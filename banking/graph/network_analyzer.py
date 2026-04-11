"""
Network Analyzer for Graph-Based Fraud Detection
================================================

Implements network analysis algorithms for detecting fraud patterns in
relationship networks, including centrality measures, network metrics,
and subgraph analysis.

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team
Date: 2026-04-11
Phase: 7.4 - Graph-Based Fraud Detection

Key Features:
    - Centrality measures (degree, betweenness, closeness, PageRank)
    - Network metrics (density, clustering coefficient, diameter)
    - Shortest path analysis
    - Connected components
    - Subgraph extraction
    - Risk scoring based on network position

Business Value:
    - Identify key players in fraud networks
    - Detect bridge entities (money mules)
    - Find central coordinators
    - Analyze network structure
    - Support investigation workflows
"""

from dataclasses import dataclass
from typing import Dict, List, Set, Tuple, Optional, Any
import networkx as nx
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class CentralityMetrics:
    """Centrality metrics for a node in the network."""
    
    node_id: str
    degree_centrality: float
    betweenness_centrality: float
    closeness_centrality: float
    pagerank: float
    eigenvector_centrality: float
    
    def get_risk_score(self) -> float:
        """
        Calculate risk score based on centrality metrics.
        
        High centrality often indicates key players in fraud networks.
        
        Returns:
            Risk score (0-100, higher = more risky)
        """
        # Weighted combination of centrality measures (already scaled 0-100)
        risk_score = (
            self.degree_centrality * 20 +
            self.betweenness_centrality * 30 +
            self.closeness_centrality * 20 +
            self.pagerank * 20 +
            self.eigenvector_centrality * 10
        )
        return min(100.0, risk_score)
    
    def get_role(self) -> str:
        """
        Determine likely role in network based on centrality.
        
        Returns:
            Role description (coordinator, bridge, peripheral, isolated)
        """
        if self.betweenness_centrality > 0.5:
            return "bridge"  # Money mule, intermediary
        elif self.degree_centrality > 0.5:
            return "coordinator"  # Fraud ring leader
        elif self.closeness_centrality > 0.5:
            return "central"  # Central player
        elif self.degree_centrality < 0.1:
            return "peripheral"  # Edge player
        else:
            return "member"  # Regular member


@dataclass
class NetworkMetrics:
    """Overall network metrics."""
    
    node_count: int
    edge_count: int
    density: float
    average_clustering: float
    diameter: Optional[int]
    average_path_length: Optional[float]
    connected_components: int
    largest_component_size: int
    
    def get_network_risk_score(self) -> float:
        """
        Calculate overall network risk score.
        
        Dense, tightly connected networks with high clustering
        are more suspicious.
        
        Returns:
            Risk score (0-100, higher = more risky)
        """
        risk_score = 0.0
        
        # High density indicates tight connections
        if self.density > 0.3:
            risk_score += 30
        elif self.density > 0.2:
            risk_score += 20
        elif self.density > 0.1:
            risk_score += 10
        
        # High clustering indicates fraud rings
        if self.average_clustering > 0.5:
            risk_score += 30
        elif self.average_clustering > 0.3:
            risk_score += 20
        elif self.average_clustering > 0.1:
            risk_score += 10
        
        # Small diameter indicates tight network
        if self.diameter and self.diameter < 3:
            risk_score += 20
        elif self.diameter and self.diameter < 5:
            risk_score += 10
        
        # Multiple components may indicate multiple fraud rings
        if self.connected_components > 1:
            risk_score += 20
        
        return min(100.0, risk_score)


class NetworkAnalyzer:
    """
    Network analyzer for graph-based fraud detection.
    
    Provides comprehensive network analysis capabilities including
    centrality measures, network metrics, and subgraph analysis.
    
    Example:
        >>> analyzer = NetworkAnalyzer()
        >>> network = analyzer.build_network(identities)
        >>> metrics = analyzer.calculate_centrality(network)
        >>> network_stats = analyzer.get_network_metrics(network)
    """
    
    def __init__(self) -> None:
        """Initialize network analyzer."""
        self.logger = logging.getLogger(__name__)
    
    def build_network(
        self,
        identities: List[Dict[str, Any]],
        include_shared_attributes: bool = True
    ) -> nx.Graph:
        """
        Build network graph from identities.
        
        Creates nodes for each identity and edges for relationships
        (shared attributes, transactions, etc.).
        
        Args:
            identities: List of identity dictionaries
            include_shared_attributes: Whether to create edges for shared attributes
        
        Returns:
            NetworkX graph
        """
        G = nx.Graph()
        
        # Add nodes
        for identity in identities:
            G.add_node(
                identity["identity_id"],
                **{k: v for k, v in identity.items() if k != "identity_id"}
            )
        
        # Add edges for shared attributes
        if include_shared_attributes:
            self._add_shared_attribute_edges(G, identities)
        
        self.logger.info(
            f"Built network with {G.number_of_nodes()} nodes "
            f"and {G.number_of_edges()} edges"
        )
        
        return G
    
    def _add_shared_attribute_edges(
        self,
        G: nx.Graph,
        identities: List[Dict[str, Any]]
    ) -> None:
        """Add edges for shared attributes (SSN, phone, address)."""
        # Index by shared attributes
        ssn_index: Dict[str, List[str]] = defaultdict(list)
        phone_index: Dict[str, List[str]] = defaultdict(list)
        address_index: Dict[str, List[str]] = defaultdict(list)
        
        for identity in identities:
            identity_id = identity["identity_id"]
            
            if "ssn" in identity:
                ssn_index[identity["ssn"]].append(identity_id)
            if "phone" in identity:
                phone_index[identity["phone"]].append(identity_id)
            if "address" in identity:
                # Convert address dict to string for use as dict key
                address = identity["address"]
                if isinstance(address, dict):
                    address_str = f"{address.get('street', '')}, {address.get('city', '')}, {address.get('state', '')} {address.get('zip', '')}"
                else:
                    address_str = str(address)
                address_index[address_str].append(identity_id)
        
        # Add edges for shared SSN
        for ssn, ids in ssn_index.items():
            if len(ids) > 1:
                for i in range(len(ids)):
                    for j in range(i + 1, len(ids)):
                        G.add_edge(
                            ids[i], ids[j],
                            relationship="shared_ssn",
                            weight=3.0  # High weight for SSN sharing
                        )
        
        # Add edges for shared phone
        for phone, ids in phone_index.items():
            if len(ids) > 1:
                for i in range(len(ids)):
                    for j in range(i + 1, len(ids)):
                        if not G.has_edge(ids[i], ids[j]):
                            G.add_edge(
                                ids[i], ids[j],
                                relationship="shared_phone",
                                weight=2.0
                            )
        
        # Add edges for shared address
        for address, ids in address_index.items():
            if len(ids) > 1:
                for i in range(len(ids)):
                    for j in range(i + 1, len(ids)):
                        if not G.has_edge(ids[i], ids[j]):
                            G.add_edge(
                                ids[i], ids[j],
                                relationship="shared_address",
                                weight=1.5
                            )
    
    def calculate_centrality(self, G: nx.Graph) -> Dict[str, CentralityMetrics]:
        """
        Calculate centrality metrics for all nodes.
        
        Args:
            G: NetworkX graph
        
        Returns:
            Dictionary mapping node IDs to CentralityMetrics
        """
        if G.number_of_nodes() == 0:
            return {}
        
        # Special case: single node graph
        if G.number_of_nodes() == 1:
            node = list(G.nodes())[0]
            return {
                node: CentralityMetrics(
                    node_id=node,
                    degree_centrality=0.0,
                    betweenness_centrality=0.0,
                    closeness_centrality=0.0,
                    pagerank=1.0,  # Single node gets all PageRank
                    eigenvector_centrality=0.0
                )
            }
        
        # Calculate all centrality measures
        degree_cent = nx.degree_centrality(G)
        betweenness_cent = nx.betweenness_centrality(G)
        closeness_cent = nx.closeness_centrality(G)
        pagerank = nx.pagerank(G)
        
        # Eigenvector centrality (may fail for disconnected graphs)
        try:
            eigenvector_cent = nx.eigenvector_centrality(G, max_iter=1000)
        except (nx.PowerIterationFailedConvergence, nx.NetworkXError):
            eigenvector_cent = {node: 0.0 for node in G.nodes()}
        
        # Combine into CentralityMetrics objects
        metrics = {}
        for node in G.nodes():
            metrics[node] = CentralityMetrics(
                node_id=node,
                degree_centrality=degree_cent[node],
                betweenness_centrality=betweenness_cent[node],
                closeness_centrality=closeness_cent[node],
                pagerank=pagerank[node],
                eigenvector_centrality=eigenvector_cent[node]
            )
        
        self.logger.info(f"Calculated centrality for {len(metrics)} nodes")
        
        return metrics
    
    def get_network_metrics(self, G: nx.Graph) -> NetworkMetrics:
        """
        Calculate overall network metrics.
        
        Args:
            G: NetworkX graph
        
        Returns:
            NetworkMetrics object
        """
        if G.number_of_nodes() == 0:
            return NetworkMetrics(
                node_count=0,
                edge_count=0,
                density=0.0,
                average_clustering=0.0,
                diameter=None,
                average_path_length=None,
                connected_components=0,
                largest_component_size=0
            )
        
        # Basic metrics
        node_count = G.number_of_nodes()
        edge_count = G.number_of_edges()
        density = nx.density(G)
        average_clustering = nx.average_clustering(G)
        
        # Connected components
        components = list(nx.connected_components(G))
        connected_components = len(components)
        largest_component_size = max(len(c) for c in components) if components else 0
        
        # Diameter and average path length (only for connected graphs)
        diameter = None
        average_path_length = None
        
        if nx.is_connected(G):
            try:
                diameter = nx.diameter(G)
                average_path_length = nx.average_shortest_path_length(G)
            except nx.NetworkXError:
                pass
        
        return NetworkMetrics(
            node_count=node_count,
            edge_count=edge_count,
            density=density,
            average_clustering=average_clustering,
            diameter=diameter,
            average_path_length=average_path_length,
            connected_components=connected_components,
            largest_component_size=largest_component_size
        )
    
    def find_shortest_paths(
        self,
        G: nx.Graph,
        source: str,
        target: str
    ) -> List[List[str]]:
        """
        Find all shortest paths between two nodes.
        
        Args:
            G: NetworkX graph
            source: Source node ID
            target: Target node ID
        
        Returns:
            List of paths (each path is a list of node IDs)
        """
        try:
            paths = list(nx.all_shortest_paths(G, source, target))
            self.logger.info(
                f"Found {len(paths)} shortest paths from {source} to {target}"
            )
            return paths
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            self.logger.warning(f"No path found from {source} to {target}")
            return []
    
    def get_connected_components(self, G: nx.Graph) -> List[Set[str]]:
        """
        Get all connected components in the graph.
        
        Args:
            G: NetworkX graph
        
        Returns:
            List of sets, each containing node IDs in a component
        """
        components = list(nx.connected_components(G))
        self.logger.info(f"Found {len(components)} connected components")
        return components
    
    def extract_subgraph(
        self,
        G: nx.Graph,
        nodes: Set[str]
    ) -> nx.Graph:
        """
        Extract subgraph containing specified nodes.
        
        Args:
            G: NetworkX graph
            nodes: Set of node IDs to include
        
        Returns:
            Subgraph containing only specified nodes
        """
        subgraph = G.subgraph(nodes).copy()
        self.logger.info(
            f"Extracted subgraph with {subgraph.number_of_nodes()} nodes "
            f"and {subgraph.number_of_edges()} edges"
        )
        return subgraph
    
    def get_neighbors(
        self,
        G: nx.Graph,
        node: str,
        depth: int = 1
    ) -> Set[str]:
        """
        Get all neighbors within specified depth.
        
        Args:
            G: NetworkX graph
            node: Node ID
            depth: Maximum distance (1 = direct neighbors, 2 = neighbors of neighbors, etc.)
        
        Returns:
            Set of neighbor node IDs
        """
        if node not in G:
            return set()
        
        neighbors = {node}
        current_level = {node}
        
        for _ in range(depth):
            next_level = set()
            for n in current_level:
                next_level.update(G.neighbors(n))
            neighbors.update(next_level)
            current_level = next_level
        
        neighbors.remove(node)  # Remove the source node itself
        
        self.logger.info(
            f"Found {len(neighbors)} neighbors within depth {depth} of {node}"
        )
        
        return neighbors
    
    def identify_high_risk_nodes(
        self,
        G: nx.Graph,
        threshold: float = 70.0
    ) -> List[Tuple[str, float]]:
        """
        Identify high-risk nodes based on centrality.
        
        Args:
            G: NetworkX graph
            threshold: Risk score threshold (0-100)
        
        Returns:
            List of (node_id, risk_score) tuples, sorted by risk score descending
        """
        centrality_metrics = self.calculate_centrality(G)
        
        high_risk = [
            (node_id, metrics.get_risk_score())
            for node_id, metrics in centrality_metrics.items()
            if metrics.get_risk_score() >= threshold
        ]
        
        # Sort by risk score descending
        high_risk.sort(key=lambda x: x[1], reverse=True)
        
        self.logger.info(
            f"Identified {len(high_risk)} high-risk nodes "
            f"(threshold: {threshold})"
        )
        
        return high_risk
    
    def get_node_statistics(
        self,
        G: nx.Graph,
        centrality_metrics: Dict[str, CentralityMetrics]
    ) -> Dict[str, Any]:
        """
        Get comprehensive statistics about nodes.
        
        Args:
            G: NetworkX graph
            centrality_metrics: Centrality metrics for all nodes
        
        Returns:
            Dictionary of statistics
        """
        if not centrality_metrics:
            return {}
        
        risk_scores = [m.get_risk_score() for m in centrality_metrics.values()]
        roles = [m.get_role() for m in centrality_metrics.values()]
        
        role_counts: Dict[str, int] = {}
        for role in roles:
            role_counts[role] = role_counts.get(role, 0) + 1
        
        return {
            "total_nodes": len(centrality_metrics),
            "average_risk_score": sum(risk_scores) / len(risk_scores),
            "max_risk_score": max(risk_scores),
            "min_risk_score": min(risk_scores),
            "high_risk_count": sum(1 for s in risk_scores if s >= 70),
            "medium_risk_count": sum(1 for s in risk_scores if 40 <= s < 70),
            "low_risk_count": sum(1 for s in risk_scores if s < 40),
            "role_distribution": role_counts,
        }

# Made with Bob
