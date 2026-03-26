"""
Graph Machine Learning for Banking Predictive Analytics
========================================================

Implements graph embedding algorithms for:
1. Fraud risk prediction from graph structure
2. Entity similarity search using learned embeddings
3. Anomaly detection through embedding space analysis
4. Community-level risk scoring

Key Algorithms:
- Node2Vec: Random walk-based graph embeddings
- Hybrid Embeddings: Combines graph + text features
- Graph Neural Networks: Future extension for GNN models

Business Use Cases:
- Predict account fraud risk before transactions
- Find similar entities for KYC clustering
- Detect anomalous subgraphs (fraud rings)
- Score customer risk from network position

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team
Date: 2026-03-23
"""

from __future__ import annotations

import logging
import random
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import numpy as np

logger = logging.getLogger(__name__)

# Try to import ML dependencies
try:
    from sklearn.cluster import DBSCAN, KMeans
    from sklearn.decomposition import PCA
    from sklearn.manifold import TSNE
    from sklearn.metrics import silhouette_score
    from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances

    _HAS_SKLEARN = True
except ImportError:
    _HAS_SKLEARN = False


class EmbeddingMethod(str, Enum):
    """Graph embedding methods."""
    NODE2VEC = "node2vec"
    DEEPWALK = "deepwalk"
    HYBRID = "hybrid"  # Graph + text embeddings


class RiskPrediction(str, Enum):
    """Risk prediction categories."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class NodeEmbedding:
    """Embedding for a graph node."""
    node_id: str
    node_label: str
    embedding: np.ndarray
    neighbors: List[str]
    degree: int
    risk_score: float = 0.0
    cluster_id: int = -1
    is_anomaly: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_label": self.node_label,
            "embedding_dim": len(self.embedding),
            "neighbors": len(self.neighbors),
            "degree": self.degree,
            "risk_score": self.risk_score,
            "cluster_id": self.cluster_id,
            "is_anomaly": self.is_anomaly
        }


@dataclass
class GraphEmbeddingResult:
    """Complete results from graph embedding process."""
    method: EmbeddingMethod
    embedding_dim: int
    node_embeddings: Dict[str, NodeEmbedding]
    clusters: Dict[int, List[str]]
    anomalies: List[str]
    risk_predictions: Dict[str, RiskPrediction]
    timestamp: datetime
    graph_stats: Dict[str, Any]
    training_metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def total_nodes(self) -> int:
        return len(self.node_embeddings)
    
    @property
    def total_clusters(self) -> int:
        return len(self.clusters)
    
    @property
    def anomaly_count(self) -> int:
        return len(self.anomalies)


class Node2Vec:
    """
    Node2Vec algorithm for graph embeddings.
    
    Uses biased random walks to generate node sequences,
    then applies Word2Vec to learn embeddings.
    
    Key Parameters:
    - p: Return parameter (controls walk backtracking)
    - q: In-out parameter (controls exploration vs. local)
    - walk_length: Length of each random walk
    - num_walks: Number of walks per node
    
    When p < 1: Walks tend to backtrack (BFS-like, local)
    When q < 1: Walks explore new areas (DFS-like, global)
    When p = q = 1: Standard random walk (DeepWalk)
    """
    
    def __init__(
        self,
        embedding_dim: int = 128,
        walk_length: int = 80,
        num_walks: int = 10,
        p: float = 1.0,
        q: float = 1.0,
        window_size: int = 10,
        min_count: int = 1,
        workers: int = 4,
        seed: int = 42,
        max_vertices: int = None
    ):
        """
        Initialize Node2Vec parameters.
        
        Args:
            embedding_dim: Dimension of output embeddings
            walk_length: Length of each random walk
            num_walks: Number of walks per node
            p: Return parameter (1.0 = neutral, <1 = local, >1 = exploration)
            q: In-out parameter (1.0 = neutral, <1 = global, >1 = local)
            window_size: Context window for Skip-gram
            min_count: Minimum node frequency
            workers: Number of parallel workers
            seed: Random seed for reproducibility
            max_vertices: Maximum vertices to embed (for memory limits)
        """
        self.embedding_dim = embedding_dim
        self.walk_length = walk_length
        self.num_walks = num_walks
        self.p = p
        self.q = q
        self.window_size = window_size
        self.min_count = min_count
        self.workers = workers
        self.seed = seed
        self.max_vertices = max_vertices
        
        # Will be populated during fit
        self.graph: Dict[str, Set[str]] = {}
        self.node_labels: Dict[str, str] = {}
        self.embeddings: Dict[str, np.ndarray] = {}
        self._alias_nodes: Dict[str, Tuple[List[int], List[float]]] = {}
        self._alias_edges: Dict[Tuple[str, str], Tuple[List[int], List[float]]] = {}
    
    def fit(self, client: Any) -> "Node2Vec":
        """
        Fit Node2Vec on a JanusGraph instance.
        
        Args:
            client: JanusGraph client with execute() method
            
        Returns:
            Self for method chaining
        """
        logger.info("Building graph structure from JanusGraph...")
        self._build_graph(client)
        
        logger.info("Generating random walks...")
        walks = self._generate_walks()
        
        logger.info("Learning embeddings from walks...")
        self._learn_embeddings(walks)
        
        logger.info(f"Node2Vec fit complete. {len(self.embeddings)} node embeddings learned.")
        return self
    
    def _build_graph(self, client: Any) -> None:
        """Build adjacency list from JanusGraph."""
        # Get all relevant vertices (with optional limit for memory efficiency)
        limit_clause = f".limit({self.max_vertices})" if self.max_vertices else ""
        vertices_query = f"""
            g.V().hasLabel('person', 'company', 'account', 'address'){limit_clause}.
            project('id', 'label').
            by(id()).
            by(label())
        """
        vertices = client.execute(vertices_query)
        
        for vertex in vertices:
            if isinstance(vertex, dict):
                vid = str(vertex.get("id", vertex.get("ID", "")))
                label = vertex.get("label", "unknown")
                self.graph[vid] = set()
                self.node_labels[vid] = label
        
        # Get edges
        edges_query = """
            g.E().hasLabel('owns_account', 'transfers_to', 'receives_from',
                           'knows', 'owns_company', 'director_of',
                           'has_address', 'used_device', 'owns_share').
            project('source', 'target').
            by(outV().id()).
            by(inV().id())
        """
        edges = client.execute(edges_query)
        
        for edge in edges:
            if isinstance(edge, dict):
                source = str(edge.get("source", edge.get("outV", "")))
                target = str(edge.get("target", edge.get("inV", "")))
                
                if source in self.graph:
                    self.graph[source].add(target)
                if target in self.graph:
                    self.graph[target].add(source)  # Undirected for embedding
        
        logger.info(f"Built graph with {len(self.graph)} nodes")
    
    def _generate_walks(self) -> List[List[str]]:
        """Generate biased random walks for all nodes."""
        walks = []
        nodes = list(self.graph.keys())
        
        random.seed(self.seed)
        
        for walk_iter in range(self.num_walks):
            random.shuffle(nodes)
            for node in nodes:
                walk = self._node2vec_walk(node)
                if len(walk) > 1:
                    walks.append(walk)
        
        logger.info(f"Generated {len(walks)} walks (avg length: {sum(len(w) for w in walks) / len(walks):.1f})")
        return walks
    
    def _node2vec_walk(self, start_node: str) -> List[str]:
        """Perform a single biased random walk."""
        walk = [start_node]
        
        while len(walk) < self.walk_length:
            cur = walk[-1]
            neighbors = list(self.graph.get(cur, set()))
            
            if not neighbors:
                break
            
            if len(walk) == 1:
                # First step: uniform random
                walk.append(random.choice(neighbors))
            else:
                # Subsequent steps: biased by p and q
                prev = walk[-2]
                next_node = self._biased_select(prev, cur, neighbors)
                walk.append(next_node)
        
        return walk
    
    def _biased_select(self, prev: str, cur: str, neighbors: List[str]) -> str:
        """Select next node with Node2Vec bias."""
        # Compute transition probabilities
        probs = []
        for neighbor in neighbors:
            if neighbor == prev:
                # Return to previous node
                prob = 1.0 / self.p
            elif neighbor in self.graph.get(prev, set()):
                # Neighbor of previous (distance 1)
                prob = 1.0
            else:
                # New node (distance 2)
                prob = 1.0 / self.q
            probs.append(prob)
        
        # Normalize and sample
        total = sum(probs)
        if total == 0:
            return random.choice(neighbors)
        
        probs = [p / total for p in probs]
        return random.choices(neighbors, weights=probs, k=1)[0]
    
    def _learn_embeddings(self, walks: List[List[str]]) -> None:
        """Learn embeddings using Skip-gram (simplified implementation)."""
        # Simplified Word2Vec using matrix factorization approximation
        # For production, would use gensim.Word2Vec
        
        # Build vocabulary
        vocab = set()
        for walk in walks:
            vocab.update(walk)
        
        vocab_list = sorted(vocab)
        vocab_size = len(vocab_list)
        node_to_idx = {node: idx for idx, node in enumerate(vocab_list)}
        
        # Build co-occurrence matrix
        cooccurrence = np.zeros((vocab_size, vocab_size))
        
        for walk in walks:
            for i, node in enumerate(walk):
                node_idx = node_to_idx[node]
                
                # Context window
                for j in range(max(0, i - self.window_size), min(len(walk), i + self.window_size + 1)):
                    if i != j:
                        context_idx = node_to_idx[walk[j]]
                        distance = abs(i - j)
                        weight = 1.0 / distance
                        cooccurrence[node_idx, context_idx] += weight
        
        # SVD for dimensionality reduction
        if vocab_size > 0:
            try:
                U, S, Vt = np.linalg.svd(cooccurrence, full_matrices=False)
                
                # Take top-k dimensions
                k = min(self.embedding_dim, vocab_size)
                embeddings_matrix = U[:, :k] * np.sqrt(S[:k])
                
                # Normalize
                norms = np.linalg.norm(embeddings_matrix, axis=1, keepdims=True)
                norms[norms == 0] = 1
                embeddings_matrix = embeddings_matrix / norms
                
                # Store embeddings
                for node, idx in node_to_idx.items():
                    self.embeddings[node] = embeddings_matrix[idx]
            except Exception as e:
                logger.warning(f"SVD failed, using random embeddings: {e}")
                np.random.seed(self.seed)
                for node in vocab_list:
                    self.embeddings[node] = np.random.randn(self.embedding_dim) * 0.1
        else:
            logger.warning("Empty vocabulary, no embeddings generated")
    
    def get_embedding(self, node_id: str) -> Optional[np.ndarray]:
        """Get embedding for a specific node."""
        return self.embeddings.get(node_id)
    
    def get_all_embeddings(self) -> Dict[str, np.ndarray]:
        """Get all node embeddings."""
        return self.embeddings


class GraphMLEngine:
    """
    Complete Graph ML engine for banking predictive analytics.
    
    Combines:
    - Graph embeddings (Node2Vec)
    - Text embeddings (existing infrastructure)
    - Risk prediction models
    - Anomaly detection
    - Clustering for entity resolution
    
    Example:
        >>> engine = GraphMLEngine(client)
        >>> results = engine.embed_graph(method=EmbeddingMethod.NODE2VEC)
        >>> predictions = engine.predict_fraud_risk()
        >>> similar = engine.find_similar_entities("person-123", k=5)
    """
    
    # Risk thresholds
    RISK_THRESHOLDS = {
        RiskPrediction.LOW: 0.3,
        RiskPrediction.MEDIUM: 0.5,
        RiskPrediction.HIGH: 0.7,
        RiskPrediction.CRITICAL: 0.85
    }
    
    def __init__(
        self,
        client: Any,
        embedding_dim: int = 128,
        seed: int = 42
    ):
        """
        Initialize Graph ML engine.
        
        Args:
            client: JanusGraph client
            embedding_dim: Dimension for graph embeddings
            seed: Random seed for reproducibility
        """
        if not _HAS_SKLEARN:
            raise ImportError(
                "GraphMLEngine requires scikit-learn. "
                "Install with: uv pip install scikit-learn"
            )
        
        self.client = client
        self.embedding_dim = embedding_dim
        self.seed = seed
        
        self._node2vec: Optional[Node2Vec] = None
        self._results: Optional[GraphEmbeddingResult] = None
    
    def embed_graph(
        self,
        method: EmbeddingMethod = EmbeddingMethod.NODE2VEC,
        walk_length: int = 80,
        num_walks: int = 10,
        p: float = 1.0,
        q: float = 1.0,
        max_vertices: int = None
    ) -> GraphEmbeddingResult:
        """
        Generate graph embeddings using specified method.
        
        Args:
            method: Embedding algorithm
            walk_length: Length of random walks (Node2Vec)
            num_walks: Walks per node (Node2Vec)
            p: Return parameter (Node2Vec)
            q: In-out parameter (Node2Vec)
            max_vertices: Maximum vertices to embed (for memory limits)
            
        Returns:
            GraphEmbeddingResult with all embeddings
        """
        logger.info(f"Embedding graph with method={method.value}...")
        
        if method == EmbeddingMethod.NODE2VEC:
            self._node2vec = Node2Vec(
                embedding_dim=self.embedding_dim,
                walk_length=walk_length,
                num_walks=num_walks,
                p=p,
                q=q,
                seed=self.seed,
                max_vertices=max_vertices
            )
            self._node2vec.fit(self.client)
            embeddings = self._node2vec.get_all_embeddings()
            node_labels = self._node2vec.node_labels
            graph = self._node2vec.graph
        else:
            raise ValueError(f"Unsupported embedding method: {method}")
        
        # Build node embedding objects
        node_embeddings = {}
        for node_id, emb in embeddings.items():
            neighbors = list(graph.get(node_id, set()))
            node_embeddings[node_id] = NodeEmbedding(
                node_id=node_id,
                node_label=node_labels.get(node_id, "unknown"),
                embedding=emb,
                neighbors=neighbors,
                degree=len(neighbors)
            )
        
        # Perform clustering
        clusters = self._cluster_embeddings(node_embeddings)
        
        # Detect anomalies
        anomalies = self._detect_anomalies(node_embeddings, clusters)
        
        # Predict fraud risk
        risk_predictions = self._predict_risk(node_embeddings, clusters, anomalies)
        
        # Build result
        self._results = GraphEmbeddingResult(
            method=method,
            embedding_dim=self.embedding_dim,
            node_embeddings=node_embeddings,
            clusters=clusters,
            anomalies=anomalies,
            risk_predictions=risk_predictions,
            timestamp=datetime.utcnow(),
            graph_stats=self._get_graph_stats(),
            training_metadata={
                "walk_length": walk_length,
                "num_walks": num_walks,
                "p": p,
                "q": q,
                "seed": self.seed
            }
        )
        
        logger.info(f"Graph embedding complete: {len(node_embeddings)} nodes, {len(clusters)} clusters, {len(anomalies)} anomalies")
        return self._results
    
    def _cluster_embeddings(
        self,
        node_embeddings: Dict[str, NodeEmbedding],
        min_cluster_size: int = 3
    ) -> Dict[int, List[str]]:
        """Cluster nodes by embedding similarity."""
        if len(node_embeddings) < min_cluster_size:
            return {0: list(node_embeddings.keys())}
        
        # Build embedding matrix
        node_ids = list(node_embeddings.keys())
        embeddings_matrix = np.array([node_embeddings[nid].embedding for nid in node_ids])
        
        # Determine optimal number of clusters
        n_samples = len(node_ids)
        max_clusters = min(n_samples // min_cluster_size, 20)
        
        if max_clusters < 2:
            return {0: node_ids}
        
        # Try different cluster counts
        best_n_clusters = 2
        best_score = -1
        
        for n_clusters in range(2, max_clusters + 1):
            kmeans = KMeans(n_clusters=n_clusters, random_state=self.seed, n_init=10)
            labels = kmeans.fit_predict(embeddings_matrix)
            
            if len(set(labels)) > 1:
                score = silhouette_score(embeddings_matrix, labels)
                if score > best_score:
                    best_score = score
                    best_n_clusters = n_clusters
        
        # Final clustering
        kmeans = KMeans(n_clusters=best_n_clusters, random_state=self.seed, n_init=10)
        labels = kmeans.fit_predict(embeddings_matrix)
        
        # Build cluster dictionary
        clusters = defaultdict(list)
        for node_id, label in zip(node_ids, labels):
            clusters[int(label)].append(node_id)
            node_embeddings[node_id].cluster_id = int(label)
        
        return dict(clusters)
    
    def _detect_anomalies(
        self,
        node_embeddings: Dict[str, NodeEmbedding],
        clusters: Dict[int, List[str]],
        eps: float = 0.5
    ) -> List[str]:
        """Detect anomalous nodes using DBSCAN on embeddings."""
        if len(node_embeddings) < 5:
            return []
        
        # Build embedding matrix
        node_ids = list(node_embeddings.keys())
        embeddings_matrix = np.array([node_embeddings[nid].embedding for nid in node_ids])
        
        # DBSCAN for anomaly detection
        dbscan = DBSCAN(eps=eps, min_samples=3)
        labels = dbscan.fit_predict(embeddings_matrix)
        
        # Points with label -1 are anomalies
        anomalies = []
        for node_id, label in zip(node_ids, labels):
            if label == -1:
                anomalies.append(node_id)
                node_embeddings[node_id].is_anomaly = True
        
        return anomalies
    
    def _predict_risk(
        self,
        node_embeddings: Dict[str, NodeEmbedding],
        clusters: Dict[int, List[str]],
        anomalies: List[str]
    ) -> Dict[str, RiskPrediction]:
        """Predict fraud risk for each node."""
        predictions = {}
        
        # Calculate cluster-level statistics
        cluster_risks = {}
        for cluster_id, node_ids in clusters.items():
            # Risk based on cluster characteristics
            cluster_size = len(node_ids)
            
            # Get average degree
            avg_degree = np.mean([node_embeddings[nid].degree for nid in node_ids])
            
            # Higher risk for:
            # - Small clusters (isolated entities)
            # - High average degree (hubs)
            risk = 0.0
            
            if cluster_size <= 3:
                risk += 0.2  # Small cluster
            
            if avg_degree > 10:
                risk += 0.15  # Hub nodes
            
            cluster_risks[cluster_id] = risk
        
        # Assign risk predictions
        for node_id, node_emb in node_embeddings.items():
            risk_score = 0.0
            
            # Base risk from cluster
            cluster_risk = cluster_risks.get(node_emb.cluster_id, 0.0)
            risk_score += cluster_risk
            
            # Anomaly bonus
            if node_emb.is_anomaly:
                risk_score += 0.3
            
            # Hub bonus
            if node_emb.degree > 15:
                risk_score += 0.2
            
            # Store risk score
            node_emb.risk_score = min(risk_score, 1.0)
            
            # Assign prediction category
            if node_emb.risk_score >= self.RISK_THRESHOLDS[RiskPrediction.CRITICAL]:
                predictions[node_id] = RiskPrediction.CRITICAL
            elif node_emb.risk_score >= self.RISK_THRESHOLDS[RiskPrediction.HIGH]:
                predictions[node_id] = RiskPrediction.HIGH
            elif node_emb.risk_score >= self.RISK_THRESHOLDS[RiskPrediction.MEDIUM]:
                predictions[node_id] = RiskPrediction.MEDIUM
            else:
                predictions[node_id] = RiskPrediction.LOW
        
        return predictions
    
    def _get_graph_stats(self) -> Dict[str, Any]:
        """Get graph statistics."""
        stats = {}
        try:
            stats["total_vertices"] = self.client.execute("g.V().count()")[0]
            stats["total_edges"] = self.client.execute("g.E().count()")[0]
        except Exception:
            pass
        return stats
    
    def find_similar_entities(
        self,
        node_id: str,
        k: int = 10,
        include_scores: bool = True
    ) -> List[Union[str, Tuple[str, float]]]:
        """
        Find similar entities using embedding cosine similarity.
        
        Args:
            node_id: Query node ID
            k: Number of similar entities to return
            include_scores: Include similarity scores in result
            
        Returns:
            List of similar node IDs (or tuples with scores)
        """
        if not self._results:
            raise ValueError("Must call embed_graph() first")
        
        query_embedding = self._results.node_embeddings.get(node_id)
        if query_embedding is None:
            logger.warning(f"Node {node_id} not found in embeddings")
            return []
        
        query_vec = query_embedding.embedding.reshape(1, -1)
        
        # Build comparison matrix
        other_ids = []
        other_vecs = []
        
        for other_id, other_emb in self._results.node_embeddings.items():
            if other_id != node_id:
                other_ids.append(other_id)
                other_vecs.append(other_emb.embedding)
        
        if not other_vecs:
            return []
        
        other_matrix = np.array(other_vecs)
        
        # Compute similarities
        similarities = cosine_similarity(query_vec, other_matrix)[0]
        
        # Get top-k
        top_indices = np.argsort(similarities)[::-1][:k]
        
        results = []
        for idx in top_indices:
            if include_scores:
                results.append((other_ids[idx], float(similarities[idx])))
            else:
                results.append(other_ids[idx])
        
        return results
    
    def get_cluster_members(self, cluster_id: int) -> List[str]:
        """Get all members of a specific cluster."""
        if not self._results:
            raise ValueError("Must call embed_graph() first")
        return self._results.clusters.get(cluster_id, [])
    
    def get_risk_summary(self) -> Dict[str, int]:
        """Get summary of risk predictions."""
        if not self._results:
            raise ValueError("Must call embed_graph() first")
        
        summary = {level.value: 0 for level in RiskPrediction}
        for prediction in self._results.risk_predictions.values():
            summary[prediction.value] += 1
        
        return summary
    
    def export_for_visualization(
        self,
        use_tsne: bool = True,
        perplexity: int = 30
    ) -> Dict[str, Any]:
        """
        Export embeddings for 2D visualization.
        
        Args:
            use_tsne: Use t-SNE for dimensionality reduction
            perplexity: t-SNE perplexity parameter
            
        Returns:
            Dict with nodes, edges, and 2D coordinates
        """
        if not self._results:
            raise ValueError("Must call embed_graph() first")
        
        # Build embedding matrix
        node_ids = list(self._results.node_embeddings.keys())
        embeddings_matrix = np.array([
            self._results.node_embeddings[nid].embedding for nid in node_ids
        ])
        
        # Dimensionality reduction
        if use_tsne and len(node_ids) > perplexity:
            reducer = TSNE(n_components=2, perplexity=perplexity, random_state=self.seed)
        else:
            reducer = PCA(n_components=2, random_state=self.seed)
        
        coords_2d = reducer.fit_transform(embeddings_matrix)
        
        # Build nodes
        nodes = []
        for i, node_id in enumerate(node_ids):
            node_emb = self._results.node_embeddings[node_id]
            nodes.append({
                "id": node_id,
                "label": node_emb.node_label,
                "x": float(coords_2d[i, 0]),
                "y": float(coords_2d[i, 1]),
                "risk_score": node_emb.risk_score,
                "risk_level": self._results.risk_predictions.get(node_id, RiskPrediction.LOW).value,
                "cluster": node_emb.cluster_id,
                "is_anomaly": node_emb.is_anomaly,
                "degree": node_emb.degree
            })
        
        # Build edges from graph
        edges = []
        if self._node2vec:
            visited = set()
            for source, targets in self._node2vec.graph.items():
                for target in targets:
                    edge_key = tuple(sorted([source, target]))
                    if edge_key not in visited:
                        visited.add(edge_key)
                        edges.append({
                            "source": source,
                            "target": target
                        })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "method": self._results.method.value,
                "embedding_dim": self.embedding_dim,
                "total_nodes": len(nodes),
                "total_clusters": self._results.total_clusters,
                "anomaly_count": self._results.anomaly_count,
                "risk_summary": self.get_risk_summary()
            }
        }


def create_graph_ml_report(
    results: GraphEmbeddingResult,
    output_format: str = "summary"
) -> str:
    """
    Create a comprehensive Graph ML report.
    
    Args:
        results: GraphEmbeddingResult from engine
        output_format: 'summary', 'detailed', or 'risk_focused'
        
    Returns:
        Formatted report string
    """
    lines = [
        "=" * 70,
        "GRAPH MACHINE LEARNING REPORT",
        f"Generated: {results.timestamp.isoformat()}",
        f"Method: {results.method.value.upper()}",
        "=" * 70,
        "",
        "EXECUTIVE SUMMARY",
        "-" * 40,
        f"Total Nodes Embedded: {results.total_nodes}",
        f"Embedding Dimension: {results.embedding_dim}",
        f"Clusters Discovered: {results.total_clusters}",
        f"Anomalies Detected: {results.anomaly_count}",
        "",
        "RISK PREDICTIONS",
        "-" * 40,
    ]
    
    # Risk summary
    risk_counts = defaultdict(int)
    for prediction in results.risk_predictions.values():
        risk_counts[prediction.value] += 1
    
    for level in ["low", "medium", "high", "critical"]:
        count = risk_counts.get(level, 0)
        pct = (count / results.total_nodes * 100) if results.total_nodes > 0 else 0
        lines.append(f"  {level.upper():10s}: {count:5d} ({pct:5.1f}%)")
    
    if output_format == "summary":
        return "\n".join(lines)
    
    # Detailed cluster analysis
    lines.extend([
        "",
        "CLUSTER ANALYSIS",
        "-" * 40,
    ])
    
    for cluster_id, members in sorted(results.clusters.items()):
        avg_risk = np.mean([
            results.node_embeddings[nid].risk_score
            for nid in members
        ]) if members else 0
        
        anomalies_in_cluster = sum(
            1 for nid in members
            if results.node_embeddings[nid].is_anomaly
        )
        
        lines.extend([
            f"\nCluster {cluster_id}:",
            f"  Members: {len(members)}",
            f"  Avg Risk Score: {avg_risk:.3f}",
            f"  Anomalies: {anomalies_in_cluster}",
        ])
    
    if output_format == "risk_focused":
        lines.extend([
            "",
            "=" * 70,
            "HIGH-RISK ENTITIES",
            "-" * 40,
        ])
        
        high_risk = [
            (nid, results.node_embeddings[nid])
            for nid, pred in results.risk_predictions.items()
            if pred in [RiskPrediction.HIGH, RiskPrediction.CRITICAL]
        ]
        
        high_risk.sort(key=lambda x: x[1].risk_score, reverse=True)
        
        for node_id, node_emb in high_risk[:20]:
            lines.append(
                f"  {node_id}: risk={node_emb.risk_score:.3f}, "
                f"degree={node_emb.degree}, cluster={node_emb.cluster_id}"
            )
    
    return "\n".join(lines)
