"""
Community Detector for Fraud Ring Detection
===========================================

Implements community detection algorithms for identifying fraud rings
and suspicious groups in relationship networks.

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team
Date: 2026-04-11
Phase: 7.4 - Graph-Based Fraud Detection

Key Features:
    - Louvain algorithm for community detection
    - Label propagation algorithm
    - Modularity calculation
    - Community statistics and analysis
    - Fraud ring identification and scoring

Business Value:
    - Detect organized fraud rings
    - Identify coordinated fraud activities
    - Prioritize investigation targets
    - Support compliance reporting
"""

from dataclasses import dataclass
from typing import Dict, List, Set, Tuple, Optional, Any
import networkx as nx
from collections import defaultdict, Counter
import logging

# Try to import community detection libraries
try:
    import community as community_louvain
    LOUVAIN_AVAILABLE = True
except ImportError:
    LOUVAIN_AVAILABLE = False
    logging.warning("python-louvain not available, using fallback algorithm")

logger = logging.getLogger(__name__)


@dataclass
class Community:
    """Represents a detected community (potential fraud ring)."""
    
    community_id: int
    members: Set[str]
    size: int
    density: float
    modularity_contribution: float
    
    def get_risk_score(self) -> float:
        """
        Calculate risk score for this community.
        
        Larger, denser communities are more suspicious.
        
        Returns:
            Risk score (0-100, higher = more risky)
        """
        risk_score = 0.0
        
        # Size factor (larger groups are more suspicious)
        if self.size >= 10:
            risk_score += 40
        elif self.size >= 5:
            risk_score += 30
        elif self.size >= 3:
            risk_score += 20
        else:
            risk_score += 10
        
        # Density factor (tighter connections are more suspicious)
        if self.density >= 0.7:
            risk_score += 40
        elif self.density >= 0.5:
            risk_score += 30
        elif self.density >= 0.3:
            risk_score += 20
        else:
            risk_score += 10
        
        # Modularity factor (well-defined communities are more suspicious)
        if self.modularity_contribution >= 0.3:
            risk_score += 20
        elif self.modularity_contribution >= 0.2:
            risk_score += 10
        
        return min(100.0, risk_score)
    
    def get_risk_level(self) -> str:
        """
        Get risk level classification.
        
        Returns:
            Risk level (critical, high, medium, low)
        """
        risk_score = self.get_risk_score()
        
        if risk_score >= 80:
            return "critical"
        elif risk_score >= 60:
            return "high"
        elif risk_score >= 40:
            return "medium"
        else:
            return "low"


@dataclass
class CommunityDetectionResult:
    """Results of community detection analysis."""
    
    communities: List[Community]
    total_communities: int
    modularity: float
    algorithm: str
    node_to_community: Dict[str, int] = None  # type: ignore
    
    @property
    def num_communities(self) -> int:
        """Alias for total_communities for backward compatibility."""
        return self.total_communities
    
    def get_fraud_rings(self, min_size: int = 3, min_risk: float = 60.0) -> List[Community]:
        """
        Get potential fraud rings based on size and risk.
        
        Args:
            min_size: Minimum community size
            min_risk: Minimum risk score
        
        Returns:
            List of communities meeting criteria
        """
        return [
            c for c in self.communities
            if c.size >= min_size and c.get_risk_score() >= min_risk
        ]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about detected communities.
        
        Returns:
            Dictionary of statistics
        """
        if not self.communities:
            return {
                "total_communities": 0,
                "total_members": 0,
                "average_size": 0.0,
                "largest_community": 0,
                "average_density": 0.0,
                "modularity": 0.0,
            }
        
        sizes = [c.size for c in self.communities]
        densities = [c.density for c in self.communities]
        risk_scores = [c.get_risk_score() for c in self.communities]
        
        risk_levels = Counter([c.get_risk_level() for c in self.communities])
        
        return {
            "total_communities": self.total_communities,
            "total_members": sum(sizes),
            "average_size": sum(sizes) / len(sizes),
            "largest_community": max(sizes),
            "smallest_community": min(sizes),
            "average_density": sum(densities) / len(densities),
            "modularity": self.modularity,
            "average_risk_score": sum(risk_scores) / len(risk_scores),
            "risk_level_distribution": dict(risk_levels),
            "high_risk_communities": sum(1 for c in self.communities if c.get_risk_score() >= 60),
        }


class CommunityDetector:
    """
    Community detector for fraud ring identification.
    
    Implements multiple community detection algorithms to identify
    potential fraud rings and suspicious groups in networks.
    
    Example:
        >>> detector = CommunityDetector()
        >>> result = detector.detect_communities(G, algorithm="louvain")
        >>> fraud_rings = result.get_fraud_rings(min_size=3, min_risk=60.0)
    """
    
    def __init__(self) -> None:
        """Initialize community detector."""
        self.logger = logging.getLogger(__name__)
    
    def detect_communities(
        self,
        G: nx.Graph,
        algorithm: str = "louvain",
        **kwargs: Any
    ) -> CommunityDetectionResult:
        """
        Detect communities in the network.
        
        Args:
            G: NetworkX graph
            algorithm: Algorithm to use ("louvain" or "label_propagation")
            **kwargs: Additional algorithm-specific parameters
        
        Returns:
            CommunityDetectionResult object
        """
        if G.number_of_nodes() == 0:
            return CommunityDetectionResult(
                communities=[],
                total_communities=0,
                modularity=0.0,
                algorithm=algorithm
            )
        
        if algorithm == "louvain":
            return self._detect_louvain(G, **kwargs)
        elif algorithm == "label_propagation":
            return self._detect_label_propagation(G, **kwargs)
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")
    
    def _detect_louvain(self, G: nx.Graph, **kwargs: Any) -> CommunityDetectionResult:
        """
        Detect communities using Louvain algorithm.
        
        The Louvain algorithm optimizes modularity to find communities.
        It's fast and produces high-quality results.
        """
        if LOUVAIN_AVAILABLE:
            # Use python-louvain library
            partition = community_louvain.best_partition(G, **kwargs)
        else:
            # Fallback to greedy modularity
            self.logger.warning("Using fallback greedy modularity algorithm")
            communities_gen = nx.community.greedy_modularity_communities(G)
            partition = {}
            for comm_id, community in enumerate(communities_gen):
                for node in community:
                    partition[node] = comm_id
        
        # Calculate modularity
        modularity = self._calculate_modularity(G, partition)
        
        # Build Community objects
        communities = self._build_communities(G, partition, modularity)
        
        self.logger.info(
            f"Louvain detected {len(communities)} communities "
            f"with modularity {modularity:.3f}"
        )
        
        return CommunityDetectionResult(
            communities=communities,
            total_communities=len(communities),
            modularity=modularity,
            algorithm="louvain",
            node_to_community=partition
        )
    
    def _detect_label_propagation(
        self,
        G: nx.Graph,
        **kwargs: Any
    ) -> CommunityDetectionResult:
        """
        Detect communities using label propagation algorithm.
        
        Label propagation is fast and works well for large networks.
        """
        communities_gen = nx.community.label_propagation_communities(G)
        
        # Convert to partition dictionary
        partition = {}
        for comm_id, community in enumerate(communities_gen):
            for node in community:
                partition[node] = comm_id
        
        # Calculate modularity
        modularity = self._calculate_modularity(G, partition)
        
        # Build Community objects
        communities = self._build_communities(G, partition, modularity)
        
        self.logger.info(
            f"Label propagation detected {len(communities)} communities "
            f"with modularity {modularity:.3f}"
        )
        
        return CommunityDetectionResult(
            communities=communities,
            total_communities=len(communities),
            modularity=modularity,
            algorithm="label_propagation",
            node_to_community=partition
        )
    
    def _calculate_modularity(
        self,
        G: nx.Graph,
        partition: Dict[str, int]
    ) -> float:
        """
        Calculate modularity of a partition.
        
        Modularity measures how well the network is divided into communities.
        Higher modularity (closer to 1) indicates better community structure.
        """
        if not partition:
            return 0.0
        
        # Convert partition to list of sets
        communities = defaultdict(set)
        for node, comm_id in partition.items():
            communities[comm_id].add(node)
        
        community_list = list(communities.values())
        
        try:
            modularity = nx.community.modularity(G, community_list)
            return modularity
        except (nx.NetworkXError, ZeroDivisionError):
            return 0.0
    
    def _build_communities(
        self,
        G: nx.Graph,
        partition: Dict[str, int],
        total_modularity: float
    ) -> List[Community]:
        """Build Community objects from partition."""
        # Group nodes by community
        community_members = defaultdict(set)
        for node, comm_id in partition.items():
            community_members[comm_id].add(node)
        
        communities = []
        for comm_id, members in community_members.items():
            # Extract subgraph for this community
            subgraph = G.subgraph(members)
            
            # Calculate density
            if len(members) > 1:
                density = nx.density(subgraph)
            else:
                density = 0.0
            
            # Estimate modularity contribution (simplified)
            modularity_contribution = total_modularity / len(community_members)
            
            community = Community(
                community_id=comm_id,
                members=members,
                size=len(members),
                density=density,
                modularity_contribution=modularity_contribution
            )
            
            communities.append(community)
        
        # Sort by size descending
        communities.sort(key=lambda c: c.size, reverse=True)
        
        return communities
    
    def compare_algorithms(
        self,
        G: nx.Graph
    ) -> Dict[str, CommunityDetectionResult]:
        """
        Compare multiple community detection algorithms.
        
        Args:
            G: NetworkX graph
        
        Returns:
            Dictionary mapping algorithm names to results
        """
        results = {}
        
        algorithms = ["louvain", "label_propagation"]
        
        for algorithm in algorithms:
            try:
                result = self.detect_communities(G, algorithm=algorithm)
                results[algorithm] = result
                self.logger.info(
                    f"{algorithm}: {result.total_communities} communities, "
                    f"modularity={result.modularity:.3f}"
                )
            except Exception as e:
                self.logger.error(f"Error with {algorithm}: {e}")
        
        return results
    
    def get_community_members(
        self,
        result: CommunityDetectionResult,
        community_id: int
    ) -> Optional[Set[str]]:
        """
        Get members of a specific community.
        
        Args:
            result: CommunityDetectionResult object
            community_id: Community ID
        
        Returns:
            Set of member node IDs, or None if not found
        """
        for community in result.communities:
            if community.community_id == community_id:
                return community.members
        return None
    
    def get_inter_community_edges(
        self,
        G: nx.Graph,
        result: CommunityDetectionResult
    ) -> List[Tuple[str, str, int, int]]:
        """
        Get edges that connect different communities.
        
        These edges may indicate connections between fraud rings.
        
        Args:
            G: NetworkX graph
            result: CommunityDetectionResult object
        
        Returns:
            List of (node1, node2, comm1, comm2) tuples
        """
        # Build node to community mapping
        node_to_comm = {}
        for community in result.communities:
            for node in community.members:
                node_to_comm[node] = community.community_id
        
        inter_edges = []
        for u, v in G.edges():
            comm_u = node_to_comm.get(u)
            comm_v = node_to_comm.get(v)
            
            if comm_u is not None and comm_v is not None and comm_u != comm_v:
                inter_edges.append((u, v, comm_u, comm_v))
        
        self.logger.info(f"Found {len(inter_edges)} inter-community edges")
        
        return inter_edges
    
    def merge_small_communities(
        self,
        G: nx.Graph,
        result: CommunityDetectionResult,
        min_size: int = 3
    ) -> CommunityDetectionResult:
        """
        Merge small communities into larger ones.
        
        Small communities (< min_size) are merged with their most connected neighbor.
        
        Args:
            G: NetworkX graph
            result: CommunityDetectionResult object
            min_size: Minimum community size
        
        Returns:
            New CommunityDetectionResult with merged communities
        """
        # Separate small and large communities
        large_communities = [c for c in result.communities if c.size >= min_size]
        small_communities = [c for c in result.communities if c.size < min_size]
        
        if not small_communities:
            return result
        
        # Build partition from large communities
        partition = {}
        for comm in large_communities:
            for node in comm.members:
                partition[node] = comm.community_id
        
        # Assign small community members to nearest large community
        for small_comm in small_communities:
            # Find most connected large community
            connections: Dict[int, int] = defaultdict(int)
            for node in small_comm.members:
                for neighbor in G.neighbors(node):
                    if neighbor in partition:
                        connections[partition[neighbor]] += 1
            
            if connections:
                # Assign to most connected community
                target_comm = max(connections.items(), key=lambda x: x[1])[0]
                for node in small_comm.members:
                    partition[node] = target_comm
            else:
                # No connections, keep as separate community
                for node in small_comm.members:
                    partition[node] = small_comm.community_id
        
        # Rebuild communities
        modularity = self._calculate_modularity(G, partition)
        communities = self._build_communities(G, partition, modularity)
        
        self.logger.info(
            f"Merged {len(small_communities)} small communities, "
            f"resulting in {len(communities)} total communities"
        )
        
        return CommunityDetectionResult(
            communities=communities,
            total_communities=len(communities),
            modularity=modularity,
            algorithm=f"{result.algorithm}_merged"
        )

# Made with Bob
