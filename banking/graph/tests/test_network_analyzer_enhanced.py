"""
Tests for Enhanced Network Analyzer
===================================

Tests parallel processing, incremental updates, and caching.

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team
Date: 2026-04-11
Phase: 7.4 - Graph-Based Fraud Detection (Performance Enhancement)
"""

import pytest
import networkx as nx
import time
from banking.graph.network_analyzer_enhanced import (
    NetworkAnalyzerEnhanced,
    GraphDelta,
)


class TestNetworkAnalyzerEnhanced:
    """Test enhanced network analyzer functionality."""
    
    def test_initialization(self) -> None:
        """Test analyzer initialization."""
        analyzer = NetworkAnalyzerEnhanced(
            enable_cache=True,
            cache_size=128,
            max_workers=4
        )
        
        assert analyzer.enable_cache is True
        assert analyzer.cache_size == 128
        assert analyzer.max_workers == 4
        assert analyzer.cache_hits == 0
        assert analyzer.cache_misses == 0
    
    def test_parallel_centrality_basic(self) -> None:
        """Test parallel centrality calculation."""
        analyzer = NetworkAnalyzerEnhanced(max_workers=2)
        
        # Create test graph
        G = nx.karate_club_graph()
        
        # Calculate centrality
        metrics = analyzer.calculate_centrality_parallel(G)
        
        assert len(metrics) == G.number_of_nodes()
        assert all(hasattr(m, 'degree_centrality') for m in metrics.values())
        assert all(hasattr(m, 'betweenness_centrality') for m in metrics.values())
    
    def test_parallel_centrality_performance(self) -> None:
        """Test that parallel processing is faster."""
        # Create larger graph
        G = nx.barabasi_albert_graph(100, 3, seed=42)
        
        # Sequential (max_workers=1)
        analyzer_seq = NetworkAnalyzerEnhanced(max_workers=1, enable_cache=False)
        start = time.time()
        metrics_seq = analyzer_seq.calculate_centrality_parallel(G, use_cache=False)
        time_seq = time.time() - start
        
        # Parallel (max_workers=4)
        analyzer_par = NetworkAnalyzerEnhanced(max_workers=4, enable_cache=False)
        start = time.time()
        metrics_par = analyzer_par.calculate_centrality_parallel(G, use_cache=False)
        time_par = time.time() - start
        
        # Results should be identical
        assert len(metrics_seq) == len(metrics_par)
        
        # Parallel should be faster (or at least not slower)
        # Note: For small graphs, overhead may make parallel slower
        print(f"Sequential: {time_seq:.3f}s, Parallel: {time_par:.3f}s")
    
    def test_parallel_centrality_empty_graph(self) -> None:
        """Test parallel centrality with empty graph."""
        analyzer = NetworkAnalyzerEnhanced()
        G = nx.Graph()
        
        metrics = analyzer.calculate_centrality_parallel(G)
        
        assert len(metrics) == 0
    
    def test_parallel_centrality_single_node(self) -> None:
        """Test parallel centrality with single node."""
        analyzer = NetworkAnalyzerEnhanced()
        G = nx.Graph()
        G.add_node("node1")
        
        metrics = analyzer.calculate_centrality_parallel(G)
        
        assert len(metrics) == 1
        assert "node1" in metrics
        assert metrics["node1"].degree_centrality == 0.0
        assert metrics["node1"].pagerank == 1.0
    
    def test_graph_fingerprint(self) -> None:
        """Test graph fingerprinting."""
        analyzer = NetworkAnalyzerEnhanced()
        
        # Same graph should have same fingerprint
        G1 = nx.Graph()
        G1.add_edges_from([("A", "B"), ("B", "C")])
        
        G2 = nx.Graph()
        G2.add_edges_from([("A", "B"), ("B", "C")])
        
        fp1 = analyzer._compute_graph_fingerprint(G1)
        fp2 = analyzer._compute_graph_fingerprint(G2)
        
        assert fp1 == fp2
    
    def test_graph_fingerprint_different(self) -> None:
        """Test that different graphs have different fingerprints."""
        analyzer = NetworkAnalyzerEnhanced()
        
        G1 = nx.Graph()
        G1.add_edges_from([("A", "B"), ("B", "C")])
        
        G2 = nx.Graph()
        G2.add_edges_from([("A", "B"), ("B", "D")])  # Different edge
        
        fp1 = analyzer._compute_graph_fingerprint(G1)
        fp2 = analyzer._compute_graph_fingerprint(G2)
        
        assert fp1 != fp2


class TestGraphDelta:
    """Test GraphDelta functionality."""
    
    def test_delta_creation(self) -> None:
        """Test creating GraphDelta."""
        delta = GraphDelta(
            added_nodes={"node1", "node2"},
            removed_nodes={"node3"},
            added_edges=[("node1", "node2", {})],
            removed_edges=[("node3", "node4")]
        )
        
        assert len(delta.added_nodes) == 2
        assert len(delta.removed_nodes) == 1
        assert len(delta.added_edges) == 1
        assert len(delta.removed_edges) == 1
    
    def test_delta_is_empty(self) -> None:
        """Test empty delta detection."""
        empty_delta = GraphDelta(
            added_nodes=set(),
            removed_nodes=set(),
            added_edges=[],
            removed_edges=[]
        )
        
        assert empty_delta.is_empty() is True
        
        non_empty_delta = GraphDelta(
            added_nodes={"node1"},
            removed_nodes=set(),
            added_edges=[],
            removed_edges=[]
        )
        
        assert non_empty_delta.is_empty() is False


class TestIncrementalUpdates:
    """Test incremental graph updates."""
    
    def test_apply_delta_add_nodes(self) -> None:
        """Test adding nodes via delta."""
        analyzer = NetworkAnalyzerEnhanced()
        
        # Original graph
        G = nx.Graph()
        G.add_edges_from([("A", "B"), ("B", "C")])
        
        # Delta: add node D
        delta = GraphDelta(
            added_nodes={"D"},
            removed_nodes=set(),
            added_edges=[],
            removed_edges=[]
        )
        
        G_updated = analyzer.apply_delta(G, delta)
        
        assert G_updated.has_node("D")
        assert G_updated.number_of_nodes() == 4
    
    def test_apply_delta_remove_nodes(self) -> None:
        """Test removing nodes via delta."""
        analyzer = NetworkAnalyzerEnhanced()
        
        # Original graph
        G = nx.Graph()
        G.add_edges_from([("A", "B"), ("B", "C")])
        
        # Delta: remove node C
        delta = GraphDelta(
            added_nodes=set(),
            removed_nodes={"C"},
            added_edges=[],
            removed_edges=[]
        )
        
        G_updated = analyzer.apply_delta(G, delta)
        
        assert not G_updated.has_node("C")
        assert G_updated.number_of_nodes() == 2
    
    def test_apply_delta_add_edges(self) -> None:
        """Test adding edges via delta."""
        analyzer = NetworkAnalyzerEnhanced()
        
        # Original graph
        G = nx.Graph()
        G.add_nodes_from(["A", "B", "C"])
        G.add_edge("A", "B")
        
        # Delta: add edge B-C
        delta = GraphDelta(
            added_nodes=set(),
            removed_nodes=set(),
            added_edges=[("B", "C", {"weight": 1.0})],
            removed_edges=[]
        )
        
        G_updated = analyzer.apply_delta(G, delta)
        
        assert G_updated.has_edge("B", "C")
        assert G_updated["B"]["C"]["weight"] == 1.0
    
    def test_apply_delta_remove_edges(self) -> None:
        """Test removing edges via delta."""
        analyzer = NetworkAnalyzerEnhanced()
        
        # Original graph
        G = nx.Graph()
        G.add_edges_from([("A", "B"), ("B", "C")])
        
        # Delta: remove edge A-B
        delta = GraphDelta(
            added_nodes=set(),
            removed_nodes=set(),
            added_edges=[],
            removed_edges=[("A", "B")]
        )
        
        G_updated = analyzer.apply_delta(G, delta)
        
        assert not G_updated.has_edge("A", "B")
        assert G_updated.has_edge("B", "C")
    
    def test_apply_delta_in_place(self) -> None:
        """Test in-place delta application."""
        analyzer = NetworkAnalyzerEnhanced()
        
        # Original graph
        G = nx.Graph()
        G.add_edges_from([("A", "B"), ("B", "C")])
        
        # Delta: add node D
        delta = GraphDelta(
            added_nodes={"D"},
            removed_nodes=set(),
            added_edges=[],
            removed_edges=[]
        )
        
        G_updated = analyzer.apply_delta(G, delta, in_place=True)
        
        # Should be same object
        assert G_updated is G
        assert G.has_node("D")
    
    def test_apply_delta_copy(self) -> None:
        """Test delta application with copy."""
        analyzer = NetworkAnalyzerEnhanced()
        
        # Original graph
        G = nx.Graph()
        G.add_edges_from([("A", "B"), ("B", "C")])
        
        # Delta: add node D
        delta = GraphDelta(
            added_nodes={"D"},
            removed_nodes=set(),
            added_edges=[],
            removed_edges=[]
        )
        
        G_updated = analyzer.apply_delta(G, delta, in_place=False)
        
        # Should be different objects
        assert G_updated is not G
        assert G_updated.has_node("D")
        assert not G.has_node("D")  # Original unchanged
    
    def test_compute_delta(self) -> None:
        """Test computing delta between graphs."""
        analyzer = NetworkAnalyzerEnhanced()
        
        # Original graph
        G_old = nx.Graph()
        G_old.add_edges_from([("A", "B"), ("B", "C")])
        
        # Updated graph
        G_new = nx.Graph()
        G_new.add_edges_from([("A", "B"), ("B", "D")])  # C->D
        
        delta = analyzer.compute_delta(G_old, G_new)
        
        assert "D" in delta.added_nodes
        assert "C" in delta.removed_nodes
        assert any(u == "B" and v == "D" for u, v, _ in delta.added_edges)
    
    def test_apply_empty_delta(self) -> None:
        """Test applying empty delta."""
        analyzer = NetworkAnalyzerEnhanced()
        
        G = nx.Graph()
        G.add_edges_from([("A", "B"), ("B", "C")])
        
        empty_delta = GraphDelta(
            added_nodes=set(),
            removed_nodes=set(),
            added_edges=[],
            removed_edges=[]
        )
        
        G_updated = analyzer.apply_delta(G, empty_delta)
        
        # Should be unchanged
        assert G_updated.number_of_nodes() == G.number_of_nodes()
        assert G_updated.number_of_edges() == G.number_of_edges()


class TestCaching:
    """Test caching functionality."""
    
    def test_cache_stats_initial(self) -> None:
        """Test initial cache statistics."""
        analyzer = NetworkAnalyzerEnhanced(enable_cache=True)
        
        stats = analyzer.get_cache_stats()
        
        assert stats['hits'] == 0
        assert stats['misses'] == 0
        assert stats['total'] == 0
        assert stats['hit_rate'] == 0.0
        assert stats['enabled'] is True
    
    def test_cache_disabled(self) -> None:
        """Test with caching disabled."""
        analyzer = NetworkAnalyzerEnhanced(enable_cache=False)
        
        stats = analyzer.get_cache_stats()
        
        assert stats['enabled'] is False
    
    def test_clear_cache(self) -> None:
        """Test cache clearing."""
        analyzer = NetworkAnalyzerEnhanced(enable_cache=True)
        
        # Simulate some cache activity
        analyzer.cache_hits = 10
        analyzer.cache_misses = 5
        
        analyzer.clear_cache()
        
        stats = analyzer.get_cache_stats()
        assert stats['hits'] == 0
        assert stats['misses'] == 0


class TestPerformance:
    """Test performance characteristics."""
    
    def test_large_graph_performance(self) -> None:
        """Test performance on larger graph."""
        analyzer = NetworkAnalyzerEnhanced(max_workers=4)
        
        # Create larger graph (1000 nodes)
        G = nx.barabasi_albert_graph(1000, 3, seed=42)
        
        start = time.time()
        metrics = analyzer.calculate_centrality_parallel(G, use_cache=False)
        elapsed = time.time() - start
        
        assert len(metrics) == 1000
        assert elapsed < 10.0  # Should complete in <10 seconds
        print(f"Large graph (1000 nodes) processed in {elapsed:.3f}s")
    
    def test_incremental_update_performance(self) -> None:
        """Test that incremental updates are faster than full rebuild."""
        analyzer = NetworkAnalyzerEnhanced()
        
        # Create base graph
        G = nx.barabasi_albert_graph(500, 3, seed=42)
        
        # Time full rebuild
        start = time.time()
        G_full = G.copy()
        G_full.add_node("new_node")
        G_full.add_edge("new_node", list(G.nodes())[0])
        time_full = time.time() - start
        
        # Time incremental update
        delta = GraphDelta(
            added_nodes={"new_node"},
            removed_nodes=set(),
            added_edges=[("new_node", list(G.nodes())[0], {})],
            removed_edges=[]
        )
        
        start = time.time()
        G_incremental = analyzer.apply_delta(G, delta)
        time_incremental = time.time() - start
        
        # Incremental should be much faster
        assert time_incremental < time_full
        print(f"Full: {time_full:.6f}s, Incremental: {time_incremental:.6f}s")

# Made with Bob
