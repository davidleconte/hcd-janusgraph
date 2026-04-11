"""
Tests for Network Analyzer
==========================

Tests network analysis algorithms including centrality measures,
network metrics, and subgraph analysis.

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team
Date: 2026-04-11
Phase: 7.4 - Graph-Based Fraud Detection
"""

import pytest
import networkx as nx
from banking.graph import NetworkAnalyzer, NetworkMetrics, CentralityMetrics


class TestCentralityMetrics:
    """Test CentralityMetrics dataclass."""
    
    def test_centrality_metrics_creation(self):
        """Test creating CentralityMetrics."""
        metrics = CentralityMetrics(
            node_id="node1",
            degree_centrality=0.5,
            betweenness_centrality=0.3,
            closeness_centrality=0.4,
            pagerank=0.2,
            eigenvector_centrality=0.1
        )
        
        assert metrics.node_id == "node1"
        assert metrics.degree_centrality == 0.5
        assert metrics.betweenness_centrality == 0.3
    
    def test_risk_score_calculation(self):
        """Test risk score calculation."""
        metrics = CentralityMetrics(
            node_id="node1",
            degree_centrality=0.8,
            betweenness_centrality=0.7,
            closeness_centrality=0.6,
            pagerank=0.5,
            eigenvector_centrality=0.4
        )
        
        risk_score = metrics.get_risk_score()
        assert 0 <= risk_score <= 100
        assert risk_score > 50  # High centrality should give high risk
    
    def test_risk_score_low_centrality(self):
        """Test risk score with low centrality."""
        metrics = CentralityMetrics(
            node_id="node1",
            degree_centrality=0.1,
            betweenness_centrality=0.1,
            closeness_centrality=0.1,
            pagerank=0.1,
            eigenvector_centrality=0.1
        )
        
        risk_score = metrics.get_risk_score()
        assert risk_score < 30  # Low centrality should give low risk
    
    def test_role_determination_bridge(self):
        """Test role determination for bridge nodes."""
        metrics = CentralityMetrics(
            node_id="node1",
            degree_centrality=0.3,
            betweenness_centrality=0.8,  # High betweenness
            closeness_centrality=0.3,
            pagerank=0.2,
            eigenvector_centrality=0.1
        )
        
        assert metrics.get_role() == "bridge"
    
    def test_role_determination_coordinator(self):
        """Test role determination for coordinator nodes."""
        metrics = CentralityMetrics(
            node_id="node1",
            degree_centrality=0.8,  # High degree
            betweenness_centrality=0.3,
            closeness_centrality=0.3,
            pagerank=0.2,
            eigenvector_centrality=0.1
        )
        
        assert metrics.get_role() == "coordinator"
    
    def test_role_determination_peripheral(self):
        """Test role determination for peripheral nodes."""
        metrics = CentralityMetrics(
            node_id="node1",
            degree_centrality=0.05,  # Very low degree
            betweenness_centrality=0.1,
            closeness_centrality=0.1,
            pagerank=0.1,
            eigenvector_centrality=0.1
        )
        
        assert metrics.get_role() == "peripheral"


class TestNetworkMetrics:
    """Test NetworkMetrics dataclass."""
    
    def test_network_metrics_creation(self):
        """Test creating NetworkMetrics."""
        metrics = NetworkMetrics(
            node_count=10,
            edge_count=20,
            density=0.4,
            average_clustering=0.5,
            diameter=3,
            average_path_length=2.5,
            connected_components=1,
            largest_component_size=10
        )
        
        assert metrics.node_count == 10
        assert metrics.edge_count == 20
        assert metrics.density == 0.4
    
    def test_network_risk_score_high_density(self):
        """Test network risk score with high density."""
        metrics = NetworkMetrics(
            node_count=10,
            edge_count=30,
            density=0.8,  # High density
            average_clustering=0.7,  # High clustering
            diameter=2,  # Small diameter
            average_path_length=1.5,
            connected_components=1,
            largest_component_size=10
        )
        
        risk_score = metrics.get_network_risk_score()
        assert risk_score >= 70  # Should be high risk
    
    def test_network_risk_score_low_density(self):
        """Test network risk score with low density."""
        metrics = NetworkMetrics(
            node_count=10,
            edge_count=5,
            density=0.05,  # Low density
            average_clustering=0.1,  # Low clustering
            diameter=5,  # Large diameter
            average_path_length=3.5,
            connected_components=3,
            largest_component_size=5
        )
        
        risk_score = metrics.get_network_risk_score()
        assert risk_score < 50  # Should be lower risk


class TestNetworkAnalyzer:
    """Test NetworkAnalyzer class."""
    
    def test_initialization(self):
        """Test NetworkAnalyzer initialization."""
        analyzer = NetworkAnalyzer()
        assert analyzer is not None
    
    def test_build_network_basic(self):
        """Test building basic network."""
        analyzer = NetworkAnalyzer()
        identities = [
            {"identity_id": "id1", "name": "Alice", "ssn": "111-11-1111"},
            {"identity_id": "id2", "name": "Bob", "ssn": "222-22-2222"},
            {"identity_id": "id3", "name": "Charlie", "ssn": "333-33-3333"},
        ]
        
        G = analyzer.build_network(identities, include_shared_attributes=False)
        
        assert G.number_of_nodes() == 3
        assert G.number_of_edges() == 0  # No shared attributes
    
    def test_build_network_with_shared_ssn(self):
        """Test building network with shared SSN."""
        analyzer = NetworkAnalyzer()
        identities = [
            {"identity_id": "id1", "name": "Alice", "ssn": "111-11-1111"},
            {"identity_id": "id2", "name": "Bob", "ssn": "111-11-1111"},  # Same SSN
            {"identity_id": "id3", "name": "Charlie", "ssn": "333-33-3333"},
        ]
        
        G = analyzer.build_network(identities, include_shared_attributes=True)
        
        assert G.number_of_nodes() == 3
        assert G.number_of_edges() == 1  # id1-id2 share SSN
        assert G.has_edge("id1", "id2")
    
    def test_build_network_with_shared_phone(self):
        """Test building network with shared phone."""
        analyzer = NetworkAnalyzer()
        identities = [
            {"identity_id": "id1", "phone": "555-1234"},
            {"identity_id": "id2", "phone": "555-1234"},  # Same phone
            {"identity_id": "id3", "phone": "555-5678"},
        ]
        
        G = analyzer.build_network(identities, include_shared_attributes=True)
        
        assert G.number_of_nodes() == 3
        assert G.number_of_edges() == 1  # id1-id2 share phone
    
    def test_build_network_with_shared_address(self):
        """Test building network with shared address."""
        analyzer = NetworkAnalyzer()
        identities = [
            {"identity_id": "id1", "address": "123 Main St"},
            {"identity_id": "id2", "address": "123 Main St"},  # Same address
            {"identity_id": "id3", "address": "456 Oak Ave"},
        ]
        
        G = analyzer.build_network(identities, include_shared_attributes=True)
        
        assert G.number_of_nodes() == 3
        assert G.number_of_edges() == 1  # id1-id2 share address
    
    def test_build_network_fraud_ring(self):
        """Test building network with fraud ring (multiple shared attributes)."""
        analyzer = NetworkAnalyzer()
        identities = [
            {"identity_id": "id1", "ssn": "111-11-1111", "phone": "555-1234"},
            {"identity_id": "id2", "ssn": "111-11-1111", "phone": "555-1234"},
            {"identity_id": "id3", "ssn": "111-11-1111", "phone": "555-5678"},
        ]
        
        G = analyzer.build_network(identities, include_shared_attributes=True)
        
        assert G.number_of_nodes() == 3
        # All share SSN, so should have edges between all pairs
        assert G.number_of_edges() == 3
    
    def test_calculate_centrality_empty_graph(self):
        """Test centrality calculation on empty graph."""
        analyzer = NetworkAnalyzer()
        G = nx.Graph()
        
        metrics = analyzer.calculate_centrality(G)
        
        assert len(metrics) == 0
    
    def test_calculate_centrality_single_node(self):
        """Test centrality calculation with single node."""
        analyzer = NetworkAnalyzer()
        G = nx.Graph()
        G.add_node("node1")
        
        metrics = analyzer.calculate_centrality(G)
        
        assert len(metrics) == 1
        assert "node1" in metrics
        assert metrics["node1"].degree_centrality == 0.0
    
    def test_calculate_centrality_star_network(self):
        """Test centrality calculation on star network."""
        analyzer = NetworkAnalyzer()
        G = nx.star_graph(5)  # 1 central node, 5 peripheral nodes
        
        metrics = analyzer.calculate_centrality(G)
        
        assert len(metrics) == 6
        # Central node (0) should have highest centrality
        assert metrics[0].degree_centrality > metrics[1].degree_centrality
        assert metrics[0].betweenness_centrality > metrics[1].betweenness_centrality
    
    def test_get_network_metrics_empty_graph(self):
        """Test network metrics on empty graph."""
        analyzer = NetworkAnalyzer()
        G = nx.Graph()
        
        metrics = analyzer.get_network_metrics(G)
        
        assert metrics.node_count == 0
        assert metrics.edge_count == 0
        assert metrics.density == 0.0
    
    def test_get_network_metrics_complete_graph(self):
        """Test network metrics on complete graph."""
        analyzer = NetworkAnalyzer()
        G = nx.complete_graph(5)  # All nodes connected
        
        metrics = analyzer.get_network_metrics(G)
        
        assert metrics.node_count == 5
        assert metrics.edge_count == 10  # n*(n-1)/2 = 5*4/2 = 10
        assert metrics.density == 1.0  # Complete graph has density 1
        assert metrics.connected_components == 1
    
    def test_get_network_metrics_disconnected_graph(self):
        """Test network metrics on disconnected graph."""
        analyzer = NetworkAnalyzer()
        G = nx.Graph()
        G.add_edges_from([(1, 2), (2, 3)])  # Component 1
        G.add_edges_from([(4, 5)])  # Component 2
        
        metrics = analyzer.get_network_metrics(G)
        
        assert metrics.node_count == 5
        assert metrics.connected_components == 2
        assert metrics.largest_component_size == 3
    
    def test_find_shortest_paths_connected(self):
        """Test finding shortest paths in connected graph."""
        analyzer = NetworkAnalyzer()
        G = nx.path_graph(5)  # Linear path: 0-1-2-3-4
        
        paths = analyzer.find_shortest_paths(G, 0, 4)
        
        assert len(paths) == 1
        assert paths[0] == [0, 1, 2, 3, 4]
    
    def test_find_shortest_paths_multiple(self):
        """Test finding multiple shortest paths."""
        analyzer = NetworkAnalyzer()
        G = nx.Graph()
        G.add_edges_from([(0, 1), (0, 2), (1, 3), (2, 3)])  # Diamond shape
        
        paths = analyzer.find_shortest_paths(G, 0, 3)
        
        assert len(paths) == 2  # Two paths of length 2
    
    def test_find_shortest_paths_no_path(self):
        """Test finding paths when no path exists."""
        analyzer = NetworkAnalyzer()
        G = nx.Graph()
        G.add_node(0)
        G.add_node(1)  # Disconnected nodes
        
        paths = analyzer.find_shortest_paths(G, 0, 1)
        
        assert len(paths) == 0
    
    def test_get_connected_components(self):
        """Test getting connected components."""
        analyzer = NetworkAnalyzer()
        G = nx.Graph()
        G.add_edges_from([(1, 2), (2, 3)])  # Component 1
        G.add_edges_from([(4, 5)])  # Component 2
        G.add_node(6)  # Component 3 (isolated)
        
        components = analyzer.get_connected_components(G)
        
        assert len(components) == 3
        component_sizes = sorted([len(c) for c in components])
        assert component_sizes == [1, 2, 3]
    
    def test_extract_subgraph(self):
        """Test extracting subgraph."""
        analyzer = NetworkAnalyzer()
        G = nx.complete_graph(5)
        
        subgraph = analyzer.extract_subgraph(G, {0, 1, 2})
        
        assert subgraph.number_of_nodes() == 3
        assert subgraph.number_of_edges() == 3  # Complete graph on 3 nodes
    
    def test_get_neighbors_depth_1(self):
        """Test getting neighbors at depth 1."""
        analyzer = NetworkAnalyzer()
        G = nx.path_graph(5)  # 0-1-2-3-4
        
        neighbors = analyzer.get_neighbors(G, 2, depth=1)
        
        assert neighbors == {1, 3}
    
    def test_get_neighbors_depth_2(self):
        """Test getting neighbors at depth 2."""
        analyzer = NetworkAnalyzer()
        G = nx.path_graph(5)  # 0-1-2-3-4
        
        neighbors = analyzer.get_neighbors(G, 2, depth=2)
        
        assert neighbors == {0, 1, 3, 4}
    
    def test_get_neighbors_nonexistent_node(self):
        """Test getting neighbors of nonexistent node."""
        analyzer = NetworkAnalyzer()
        G = nx.Graph()
        G.add_node(1)
        
        neighbors = analyzer.get_neighbors(G, 999, depth=1)
        
        assert len(neighbors) == 0
    
    def test_identify_high_risk_nodes(self):
        """Test identifying high-risk nodes."""
        analyzer = NetworkAnalyzer()
        G = nx.star_graph(5)  # Central node should be high risk
        
        high_risk = analyzer.identify_high_risk_nodes(G, threshold=50.0)
        
        assert len(high_risk) > 0
        # Central node (0) should be in high risk list
        high_risk_ids = [node_id for node_id, _ in high_risk]
        assert 0 in high_risk_ids
    
    def test_identify_high_risk_nodes_empty_graph(self):
        """Test identifying high-risk nodes in empty graph."""
        analyzer = NetworkAnalyzer()
        G = nx.Graph()
        
        high_risk = analyzer.identify_high_risk_nodes(G, threshold=50.0)
        
        assert len(high_risk) == 0
    
    def test_get_node_statistics(self):
        """Test getting node statistics."""
        analyzer = NetworkAnalyzer()
        G = nx.star_graph(5)
        centrality_metrics = analyzer.calculate_centrality(G)
        
        stats = analyzer.get_node_statistics(G, centrality_metrics)
        
        assert stats["total_nodes"] == 6
        assert "average_risk_score" in stats
        assert "role_distribution" in stats
        assert stats["high_risk_count"] >= 0
    
    def test_get_node_statistics_empty(self):
        """Test getting node statistics with empty metrics."""
        analyzer = NetworkAnalyzer()
        G = nx.Graph()
        
        stats = analyzer.get_node_statistics(G, {})
        
        assert stats == {}


class TestDeterminism:
    """Test deterministic behavior."""
    
    def test_build_network_deterministic(self):
        """Test that network building is deterministic."""
        analyzer1 = NetworkAnalyzer()
        analyzer2 = NetworkAnalyzer()
        
        identities = [
            {"identity_id": "id1", "ssn": "111-11-1111"},
            {"identity_id": "id2", "ssn": "111-11-1111"},
            {"identity_id": "id3", "ssn": "222-22-2222"},
        ]
        
        G1 = analyzer1.build_network(identities)
        G2 = analyzer2.build_network(identities)
        
        assert G1.number_of_nodes() == G2.number_of_nodes()
        assert G1.number_of_edges() == G2.number_of_edges()
    
    def test_centrality_calculation_deterministic(self):
        """Test that centrality calculation is deterministic."""
        analyzer = NetworkAnalyzer()
        G = nx.star_graph(5)
        
        metrics1 = analyzer.calculate_centrality(G)
        metrics2 = analyzer.calculate_centrality(G)
        
        for node in G.nodes():
            assert metrics1[node].degree_centrality == metrics2[node].degree_centrality
            assert metrics1[node].pagerank == pytest.approx(metrics2[node].pagerank)


class TestEdgeCases:
    """Test edge cases."""
    
    def test_single_node_network(self):
        """Test network with single node."""
        analyzer = NetworkAnalyzer()
        identities = [{"identity_id": "id1"}]
        
        G = analyzer.build_network(identities)
        metrics = analyzer.get_network_metrics(G)
        
        assert metrics.node_count == 1
        assert metrics.edge_count == 0
        assert metrics.density == 0.0
    
    def test_large_fraud_ring(self):
        """Test large fraud ring (all sharing SSN)."""
        analyzer = NetworkAnalyzer()
        identities = [
            {"identity_id": f"id{i}", "ssn": "111-11-1111"}
            for i in range(10)
        ]
        
        G = analyzer.build_network(identities)
        
        assert G.number_of_nodes() == 10
        # Complete graph: n*(n-1)/2 = 10*9/2 = 45 edges
        assert G.number_of_edges() == 45
    
    def test_disconnected_components(self):
        """Test network with multiple disconnected components."""
        analyzer = NetworkAnalyzer()
        identities = [
            {"identity_id": "id1", "ssn": "111-11-1111"},
            {"identity_id": "id2", "ssn": "111-11-1111"},
            {"identity_id": "id3", "ssn": "222-22-2222"},
            {"identity_id": "id4", "ssn": "222-22-2222"},
            {"identity_id": "id5", "ssn": "333-33-3333"},  # Isolated
        ]
        
        G = analyzer.build_network(identities)
        components = analyzer.get_connected_components(G)
        
        assert len(components) == 3  # 3 separate components

# Made with Bob
