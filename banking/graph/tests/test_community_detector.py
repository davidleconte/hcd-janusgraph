"""
Tests for Community Detector
============================

Tests community detection algorithms for fraud ring identification.

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team
Date: 2026-04-11
Phase: 7.4 - Graph-Based Fraud Detection
"""

import pytest
import networkx as nx
from banking.graph import CommunityDetector, Community, CommunityDetectionResult


class TestCommunity:
    """Test Community dataclass."""
    
    def test_community_creation(self):
        """Test creating Community."""
        community = Community(
            community_id=1,
            members={"node1", "node2", "node3"},
            size=3,
            density=0.8,
            modularity_contribution=0.3
        )
        
        assert community.community_id == 1
        assert len(community.members) == 3
        assert community.size == 3
    
    def test_risk_score_large_dense(self):
        """Test risk score for large, dense community."""
        community = Community(
            community_id=1,
            members=set(f"node{i}" for i in range(10)),
            size=10,
            density=0.9,
            modularity_contribution=0.4
        )
        
        risk_score = community.get_risk_score()
        assert risk_score >= 80  # Should be high risk
    
    def test_risk_score_small_sparse(self):
        """Test risk score for small, sparse community."""
        community = Community(
            community_id=1,
            members={"node1", "node2"},
            size=2,
            density=0.2,
            modularity_contribution=0.1
        )
        
        risk_score = community.get_risk_score()
        assert risk_score < 50  # Should be lower risk
    
    def test_risk_level_critical(self):
        """Test critical risk level."""
        community = Community(
            community_id=1,
            members=set(f"node{i}" for i in range(15)),
            size=15,
            density=0.95,
            modularity_contribution=0.5
        )
        
        assert community.get_risk_level() == "critical"
    
    def test_risk_level_low(self):
        """Test low risk level."""
        community = Community(
            community_id=1,
            members={"node1", "node2"},
            size=2,
            density=0.1,
            modularity_contribution=0.05
        )
        
        assert community.get_risk_level() == "low"


class TestCommunityDetectionResult:
    """Test CommunityDetectionResult dataclass."""
    
    def test_result_creation(self):
        """Test creating CommunityDetectionResult."""
        communities = [
            Community(1, {"n1", "n2"}, 2, 0.5, 0.2),
            Community(2, {"n3", "n4", "n5"}, 3, 0.7, 0.3),
        ]
        
        result = CommunityDetectionResult(
            communities=communities,
            total_communities=2,
            modularity=0.5,
            algorithm="louvain"
        )
        
        assert result.total_communities == 2
        assert result.modularity == 0.5
        assert result.algorithm == "louvain"
    
    def test_get_fraud_rings(self):
        """Test getting fraud rings."""
        communities = [
            Community(1, {"n1", "n2"}, 2, 0.5, 0.2),  # Too small
            Community(2, set(f"n{i}" for i in range(5)), 5, 0.8, 0.3),  # Fraud ring
            Community(3, {"n10", "n11", "n12"}, 3, 0.3, 0.1),  # Low risk
        ]
        
        result = CommunityDetectionResult(communities, 3, 0.5, "louvain")
        fraud_rings = result.get_fraud_rings(min_size=3, min_risk=60.0)
        
        assert len(fraud_rings) == 1
        assert fraud_rings[0].community_id == 2
    
    def test_get_statistics(self):
        """Test getting statistics."""
        communities = [
            Community(1, {"n1", "n2"}, 2, 0.5, 0.2),
            Community(2, {"n3", "n4", "n5"}, 3, 0.7, 0.3),
        ]
        
        result = CommunityDetectionResult(communities, 2, 0.5, "louvain")
        stats = result.get_statistics()
        
        assert stats["total_communities"] == 2
        assert stats["total_members"] == 5
        assert stats["largest_community"] == 3
        assert "average_density" in stats
    
    def test_get_statistics_empty(self):
        """Test statistics with no communities."""
        result = CommunityDetectionResult([], 0, 0.0, "louvain")
        stats = result.get_statistics()
        
        assert stats["total_communities"] == 0
        assert stats["total_members"] == 0


class TestCommunityDetector:
    """Test CommunityDetector class."""
    
    def test_initialization(self):
        """Test CommunityDetector initialization."""
        detector = CommunityDetector()
        assert detector is not None
    
    def test_detect_communities_empty_graph(self):
        """Test detection on empty graph."""
        detector = CommunityDetector()
        G = nx.Graph()
        
        result = detector.detect_communities(G)
        
        assert result.total_communities == 0
        assert len(result.communities) == 0
    
    def test_detect_communities_single_node(self):
        """Test detection with single node."""
        detector = CommunityDetector()
        G = nx.Graph()
        G.add_node("node1")
        
        result = detector.detect_communities(G)
        
        assert result.total_communities == 1
        assert result.communities[0].size == 1
    
    def test_detect_communities_disconnected(self):
        """Test detection with disconnected components."""
        detector = CommunityDetector()
        G = nx.Graph()
        G.add_edges_from([("n1", "n2"), ("n2", "n3")])  # Component 1
        G.add_edges_from([("n4", "n5")])  # Component 2
        
        result = detector.detect_communities(G)
        
        assert result.total_communities >= 2
    
    def test_detect_communities_louvain(self):
        """Test Louvain algorithm."""
        detector = CommunityDetector()
        G = nx.karate_club_graph()  # Well-known test graph
        
        result = detector.detect_communities(G, algorithm="louvain")
        
        assert result.algorithm == "louvain"
        assert result.total_communities > 0
        assert 0 <= result.modularity <= 1
    
    def test_detect_communities_label_propagation(self):
        """Test label propagation algorithm."""
        detector = CommunityDetector()
        G = nx.karate_club_graph()
        
        result = detector.detect_communities(G, algorithm="label_propagation")
        
        assert result.algorithm == "label_propagation"
        assert result.total_communities > 0
    
    def test_detect_communities_invalid_algorithm(self):
        """Test with invalid algorithm."""
        detector = CommunityDetector()
        G = nx.Graph()
        G.add_edge("n1", "n2")
        
        with pytest.raises(ValueError):
            detector.detect_communities(G, algorithm="invalid")
    
    def test_compare_algorithms(self):
        """Test comparing algorithms."""
        detector = CommunityDetector()
        G = nx.karate_club_graph()
        
        results = detector.compare_algorithms(G)
        
        assert "louvain" in results
        assert "label_propagation" in results
        assert all(isinstance(r, CommunityDetectionResult) for r in results.values())
    
    def test_get_community_members(self):
        """Test getting community members."""
        detector = CommunityDetector()
        G = nx.Graph()
        G.add_edges_from([("n1", "n2"), ("n2", "n3")])
        
        result = detector.detect_communities(G)
        members = detector.get_community_members(result, result.communities[0].community_id)
        
        assert members is not None
        assert len(members) > 0
    
    def test_get_community_members_invalid_id(self):
        """Test getting members with invalid ID."""
        detector = CommunityDetector()
        G = nx.Graph()
        G.add_edge("n1", "n2")
        
        result = detector.detect_communities(G)
        members = detector.get_community_members(result, 999)
        
        assert members is None
    
    def test_get_inter_community_edges(self):
        """Test getting inter-community edges."""
        detector = CommunityDetector()
        G = nx.Graph()
        # Create two communities with one connecting edge
        G.add_edges_from([("n1", "n2"), ("n2", "n3")])  # Community 1
        G.add_edges_from([("n4", "n5")])  # Community 2
        G.add_edge("n3", "n4")  # Inter-community edge
        
        result = detector.detect_communities(G)
        inter_edges = detector.get_inter_community_edges(G, result)
        
        # Should have at least one inter-community edge if detected as separate
        assert isinstance(inter_edges, list)
    
    def test_merge_small_communities(self):
        """Test merging small communities."""
        detector = CommunityDetector()
        G = nx.Graph()
        # Create one large and one small community
        G.add_edges_from([("n1", "n2"), ("n2", "n3"), ("n3", "n4")])  # Large
        G.add_edge("n5", "n6")  # Small
        G.add_edge("n4", "n5")  # Connect them
        
        result = detector.detect_communities(G)
        merged = detector.merge_small_communities(G, result, min_size=3)
        
        # Should have fewer communities after merging
        assert merged.total_communities <= result.total_communities


class TestFraudRingDetection:
    """Test fraud ring detection scenarios."""
    
    def test_detect_fraud_ring_shared_ssn(self):
        """Test detecting fraud ring with shared SSN."""
        from banking.graph import NetworkAnalyzer
        from banking.identity import SyntheticIdentityGenerator
        
        # Generate identities with fraud ring
        generator = SyntheticIdentityGenerator(seed=42)
        identities = generator.generate_batch(10)
        
        # Create fraud ring (5 identities sharing SSN)
        fraud_ssn = "111-11-1111"
        for i in range(5):
            identities[i]["ssn"] = fraud_ssn
        
        # Build network
        analyzer = NetworkAnalyzer()
        G = analyzer.build_network(identities)
        
        # Detect communities
        detector = CommunityDetector()
        result = detector.detect_communities(G)
        
        # Should detect fraud ring
        fraud_rings = result.get_fraud_rings(min_size=3, min_risk=50.0)
        assert len(fraud_rings) > 0
    
    def test_multiple_fraud_rings(self):
        """Test detecting multiple fraud rings."""
        from banking.graph import NetworkAnalyzer
        from banking.identity import SyntheticIdentityGenerator
        
        # Generate identities
        generator = SyntheticIdentityGenerator(seed=42)
        identities = generator.generate_batch(15)
        
        # Create two fraud rings
        for i in range(5):
            identities[i]["ssn"] = "111-11-1111"
        for i in range(5, 10):
            identities[i]["ssn"] = "222-22-2222"
        
        # Build network
        analyzer = NetworkAnalyzer()
        G = analyzer.build_network(identities)
        
        # Detect communities
        detector = CommunityDetector()
        result = detector.detect_communities(G)
        
        # Should detect multiple communities
        assert result.total_communities >= 2


class TestDeterminism:
    """Test deterministic behavior."""
    
    def test_detection_deterministic(self):
        """Test that detection is deterministic."""
        detector1 = CommunityDetector()
        detector2 = CommunityDetector()
        
        G = nx.karate_club_graph()
        
        result1 = detector1.detect_communities(G, algorithm="louvain")
        result2 = detector2.detect_communities(G, algorithm="louvain")
        
        # Should produce same number of communities
        assert result1.total_communities == result2.total_communities


class TestEdgeCases:
    """Test edge cases."""
    
    def test_complete_graph(self):
        """Test with complete graph (all nodes connected)."""
        detector = CommunityDetector()
        G = nx.complete_graph(10)
        
        result = detector.detect_communities(G)
        
        # Complete graph should be one community
        assert result.total_communities == 1
        assert result.communities[0].density == 1.0
    
    def test_star_graph(self):
        """Test with star graph (one central node)."""
        detector = CommunityDetector()
        G = nx.star_graph(10)
        
        result = detector.detect_communities(G)
        
        # Star graph should be one community
        assert result.total_communities == 1
    
    def test_path_graph(self):
        """Test with path graph (linear chain)."""
        detector = CommunityDetector()
        G = nx.path_graph(10)
        
        result = detector.detect_communities(G)
        
        # Path graph may be split into communities
        assert result.total_communities >= 1

# Made with Bob
