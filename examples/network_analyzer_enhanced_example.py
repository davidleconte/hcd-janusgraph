"""
Enhanced Network Analyzer Example
=================================

Demonstrates performance improvements with:
1. Parallel processing for centrality calculations
2. Incremental graph updates
3. Caching layer for repeated queries

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team
Date: 2026-04-11
Phase: 7.4 - Graph-Based Fraud Detection (Performance Enhancement)
"""

import time
import networkx as nx
from banking.graph.network_analyzer_enhanced import (
    NetworkAnalyzerEnhanced,
    GraphDelta,
)
from banking.identity import SyntheticIdentityGenerator


def example_parallel_processing():
    """Demonstrate parallel centrality calculation."""
    print("\n" + "="*70)
    print("Example 1: Parallel Processing for Centrality Calculations")
    print("="*70)
    
    # Create test graph
    print("\n1. Creating test graph (500 nodes)...")
    G = nx.barabasi_albert_graph(500, 3, seed=42)
    print(f"   Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    
    # Sequential processing (1 worker)
    print("\n2. Sequential processing (1 worker)...")
    analyzer_seq = NetworkAnalyzerEnhanced(max_workers=1, enable_cache=False)
    start = time.time()
    metrics_seq = analyzer_seq.calculate_centrality_parallel(G, use_cache=False)
    time_seq = time.time() - start
    print(f"   Time: {time_seq:.3f}s")
    print(f"   Nodes processed: {len(metrics_seq)}")
    
    # Parallel processing (4 workers)
    print("\n3. Parallel processing (4 workers)...")
    analyzer_par = NetworkAnalyzerEnhanced(max_workers=4, enable_cache=False)
    start = time.time()
    metrics_par = analyzer_par.calculate_centrality_parallel(G, use_cache=False)
    time_par = time.time() - start
    print(f"   Time: {time_par:.3f}s")
    print(f"   Nodes processed: {len(metrics_par)}")
    
    # Performance improvement
    speedup = time_seq / time_par if time_par > 0 else 1.0
    print(f"\n4. Performance improvement: {speedup:.2f}x faster")
    print(f"   Time saved: {(time_seq - time_par):.3f}s ({(1 - time_par/time_seq)*100:.1f}%)")


def example_incremental_updates():
    """Demonstrate incremental graph updates."""
    print("\n" + "="*70)
    print("Example 2: Incremental Graph Updates")
    print("="*70)
    
    # Create base graph
    print("\n1. Creating base graph...")
    generator = SyntheticIdentityGenerator(seed=42)
    identities = generator.generate_batch(100)
    
    from banking.graph import NetworkAnalyzer
    base_analyzer = NetworkAnalyzer()
    G = base_analyzer.build_network(identities)
    print(f"   Base graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    
    # Simulate new identities arriving
    print("\n2. Simulating new identities...")
    new_identities = generator.generate_batch(10)
    print(f"   New identities: {len(new_identities)}")
    
    # Method 1: Full rebuild
    print("\n3. Method 1: Full rebuild...")
    start = time.time()
    all_identities = identities + new_identities
    G_full = base_analyzer.build_network(all_identities)
    time_full = time.time() - start
    print(f"   Time: {time_full:.6f}s")
    print(f"   Result: {G_full.number_of_nodes()} nodes, {G_full.number_of_edges()} edges")
    
    # Method 2: Incremental update
    print("\n4. Method 2: Incremental update...")
    analyzer_enhanced = NetworkAnalyzerEnhanced()
    
    # Build delta
    new_nodes = {identity["identity_id"] for identity in new_identities}
    new_edges = []
    
    # Add edges for shared attributes (simplified)
    for new_id in new_identities:
        for old_id in identities[:5]:  # Connect to first 5 for demo
            if new_id.get("ssn") == old_id.get("ssn"):
                new_edges.append((
                    new_id["identity_id"],
                    old_id["identity_id"],
                    {"relationship": "shared_ssn", "weight": 3.0}
                ))
    
    delta = GraphDelta(
        added_nodes=new_nodes,
        removed_nodes=set(),
        added_edges=new_edges,
        removed_edges=[]
    )
    
    start = time.time()
    G_incremental = analyzer_enhanced.apply_delta(G, delta)
    time_incremental = time.time() - start
    print(f"   Time: {time_incremental:.6f}s")
    print(f"   Result: {G_incremental.number_of_nodes()} nodes, {G_incremental.number_of_edges()} edges")
    
    # Performance improvement
    speedup = time_full / time_incremental if time_incremental > 0 else 1.0
    print(f"\n5. Performance improvement: {speedup:.2f}x faster")
    print(f"   Time saved: {(time_full - time_incremental)*1000:.3f}ms")


def example_caching():
    """Demonstrate caching layer."""
    print("\n" + "="*70)
    print("Example 3: Caching Layer for Repeated Queries")
    print("="*70)
    
    # Create test graph
    print("\n1. Creating test graph...")
    G = nx.karate_club_graph()
    print(f"   Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    
    # First calculation (cache miss)
    print("\n2. First calculation (cache miss)...")
    analyzer = NetworkAnalyzerEnhanced(enable_cache=True, max_workers=2)
    start = time.time()
    metrics1 = analyzer.calculate_centrality_parallel(G, use_cache=True)
    time1 = time.time() - start
    print(f"   Time: {time1:.6f}s")
    print(f"   Cache stats: {analyzer.get_cache_stats()}")
    
    # Second calculation (cache hit - simulated)
    print("\n3. Second calculation (would be cache hit)...")
    start = time.time()
    metrics2 = analyzer.calculate_centrality_parallel(G, use_cache=True)
    time2 = time.time() - start
    print(f"   Time: {time2:.6f}s")
    print(f"   Cache stats: {analyzer.get_cache_stats()}")
    
    # Note: Actual caching requires Redis or similar in production
    print("\n4. Note: Full caching requires Redis/Memcached in production")
    print("   Current implementation shows cache infrastructure")


def example_combined_workflow():
    """Demonstrate combined workflow with all enhancements."""
    print("\n" + "="*70)
    print("Example 4: Combined Workflow (All Enhancements)")
    print("="*70)
    
    # Initialize enhanced analyzer
    print("\n1. Initializing enhanced analyzer...")
    analyzer = NetworkAnalyzerEnhanced(
        enable_cache=True,
        cache_size=128,
        max_workers=4
    )
    print("   ✓ Parallel processing enabled (4 workers)")
    print("   ✓ Caching enabled (128 entries)")
    print("   ✓ Incremental updates supported")
    
    # Create initial graph
    print("\n2. Creating initial graph...")
    generator = SyntheticIdentityGenerator(seed=42)
    identities = generator.generate_batch(50)
    
    from banking.graph import NetworkAnalyzer
    base_analyzer = NetworkAnalyzer()
    G = base_analyzer.build_network(identities)
    print(f"   Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    
    # Calculate centrality (parallel)
    print("\n3. Calculating centrality (parallel)...")
    start = time.time()
    metrics = analyzer.calculate_centrality_parallel(G)
    time_calc = time.time() - start
    print(f"   Time: {time_calc:.3f}s")
    print(f"   Top 5 high-risk nodes:")
    sorted_metrics = sorted(
        metrics.items(),
        key=lambda x: x[1].get_risk_score(),
        reverse=True
    )
    for node_id, m in sorted_metrics[:5]:
        print(f"     {node_id}: Risk={m.get_risk_score():.1f}, Role={m.get_role()}")
    
    # Simulate incremental update
    print("\n4. Simulating incremental update...")
    new_identities = generator.generate_batch(5)
    
    delta = GraphDelta(
        added_nodes={identity["identity_id"] for identity in new_identities},
        removed_nodes=set(),
        added_edges=[],
        removed_edges=[]
    )
    
    start = time.time()
    G_updated = analyzer.apply_delta(G, delta)
    time_update = time.time() - start
    print(f"   Time: {time_update:.6f}s")
    print(f"   Updated graph: {G_updated.number_of_nodes()} nodes")
    
    # Recalculate centrality (would use cache if graph unchanged)
    print("\n5. Recalculating centrality...")
    start = time.time()
    metrics_updated = analyzer.calculate_centrality_parallel(G_updated)
    time_recalc = time.time() - start
    print(f"   Time: {time_recalc:.3f}s")
    
    # Show cache statistics
    print("\n6. Cache statistics:")
    stats = analyzer.get_cache_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n7. Summary:")
    print(f"   ✓ Processed {G_updated.number_of_nodes()} nodes")
    print(f"   ✓ Parallel processing: {time_calc:.3f}s")
    print(f"   ✓ Incremental update: {time_update*1000:.3f}ms")
    print(f"   ✓ Total time: {(time_calc + time_update + time_recalc):.3f}s")


def main():
    """Run all examples."""
    print("\n" + "="*70)
    print("Enhanced Network Analyzer - Performance Examples")
    print("="*70)
    print("\nDemonstrating three key performance enhancements:")
    print("1. Parallel processing for centrality calculations")
    print("2. Incremental graph updates")
    print("3. Caching layer for repeated queries")
    
    try:
        example_parallel_processing()
        example_incremental_updates()
        example_caching()
        example_combined_workflow()
        
        print("\n" + "="*70)
        print("All examples completed successfully!")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

# Made with Bob
