"""
Network Analyzer Examples
=========================

Demonstrates network analysis capabilities for fraud detection including
centrality measures, network metrics, and subgraph analysis.

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team
Date: 2026-04-11
Phase: 7.4 - Graph-Based Fraud Detection

Run: python examples/network_analyzer_example.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from banking.graph import NetworkAnalyzer
from banking.identity import SyntheticIdentityGenerator


def example_1_basic_network_analysis():
    """Example 1: Basic network analysis."""
    print("\n" + "=" * 60)
    print("Example 1: Basic Network Analysis")
    print("=" * 60)
    
    # Generate identities
    generator = SyntheticIdentityGenerator(seed=42)
    identities = generator.generate_batch(10)
    
    # Build network
    analyzer = NetworkAnalyzer()
    G = analyzer.build_network(identities)
    
    print(f"\nNetwork built:")
    print(f"  Nodes: {G.number_of_nodes()}")
    print(f"  Edges: {G.number_of_edges()}")
    
    # Get network metrics
    metrics = analyzer.get_network_metrics(G)
    print(f"\nNetwork Metrics:")
    print(f"  Density: {metrics.density:.3f}")
    print(f"  Average Clustering: {metrics.average_clustering:.3f}")
    print(f"  Connected Components: {metrics.connected_components}")
    print(f"  Largest Component: {metrics.largest_component_size} nodes")
    
    # Calculate network risk
    risk_score = metrics.get_network_risk_score()
    print(f"\nNetwork Risk Score: {risk_score:.1f}/100")


def example_2_centrality_analysis():
    """Example 2: Centrality analysis."""
    print("\n" + "=" * 60)
    print("Example 2: Centrality Analysis")
    print("=" * 60)
    
    # Generate identities with fraud ring (shared SSN)
    generator = SyntheticIdentityGenerator(seed=42)
    identities = generator.generate_batch(15)
    
    # Make some share SSN (fraud ring)
    fraud_ssn = "111-11-1111"
    for i in range(5):
        identities[i]["ssn"] = fraud_ssn
    
    # Build network
    analyzer = NetworkAnalyzer()
    G = analyzer.build_network(identities)
    
    # Calculate centrality
    centrality_metrics = analyzer.calculate_centrality(G)
    
    print(f"\nTop 5 Nodes by Degree Centrality:")
    sorted_by_degree = sorted(
        centrality_metrics.items(),
        key=lambda x: x[1].degree_centrality,
        reverse=True
    )[:5]
    
    for node_id, metrics in sorted_by_degree:
        print(f"  {node_id}:")
        print(f"    Degree: {metrics.degree_centrality:.3f}")
        print(f"    Betweenness: {metrics.betweenness_centrality:.3f}")
        print(f"    PageRank: {metrics.pagerank:.3f}")
        print(f"    Role: {metrics.get_role()}")
        print(f"    Risk Score: {metrics.get_risk_score():.1f}/100")


def example_3_fraud_ring_detection():
    """Example 3: Fraud ring detection."""
    print("\n" + "=" * 60)
    print("Example 3: Fraud Ring Detection")
    print("=" * 60)
    
    # Generate identities
    generator = SyntheticIdentityGenerator(seed=42)
    identities = generator.generate_batch(20)
    
    # Create fraud ring (5 identities sharing SSN and phone)
    fraud_ssn = "111-11-1111"
    fraud_phone = "555-1234"
    for i in range(5):
        identities[i]["ssn"] = fraud_ssn
        identities[i]["phone"] = fraud_phone
    
    # Build network
    analyzer = NetworkAnalyzer()
    G = analyzer.build_network(identities)
    
    # Get connected components (fraud rings)
    components = analyzer.get_connected_components(G)
    
    print(f"\nConnected Components (Potential Fraud Rings):")
    for i, component in enumerate(sorted(components, key=len, reverse=True), 1):
        print(f"\nComponent {i}: {len(component)} identities")
        if len(component) >= 3:  # Suspicious if 3+ identities connected
            print(f"  ⚠️  SUSPICIOUS: Large connected group")
            print(f"  Members: {', '.join(list(component)[:5])}")
            if len(component) > 5:
                print(f"  ... and {len(component) - 5} more")


def example_4_high_risk_identification():
    """Example 4: High-risk node identification."""
    print("\n" + "=" * 60)
    print("Example 4: High-Risk Node Identification")
    print("=" * 60)
    
    # Generate identities
    generator = SyntheticIdentityGenerator(seed=42)
    identities = generator.generate_batch(20)
    
    # Create fraud network
    fraud_ssn = "111-11-1111"
    for i in range(8):
        identities[i]["ssn"] = fraud_ssn
    
    # Build network
    analyzer = NetworkAnalyzer()
    G = analyzer.build_network(identities)
    
    # Identify high-risk nodes
    high_risk = analyzer.identify_high_risk_nodes(G, threshold=60.0)
    
    print(f"\nHigh-Risk Nodes (Risk Score ≥ 60):")
    print(f"Found {len(high_risk)} high-risk nodes\n")
    
    for node_id, risk_score in high_risk[:5]:
        print(f"  {node_id}: {risk_score:.1f}/100")


def example_5_shortest_path_analysis():
    """Example 5: Shortest path analysis."""
    print("\n" + "=" * 60)
    print("Example 5: Shortest Path Analysis")
    print("=" * 60)
    
    # Generate identities
    generator = SyntheticIdentityGenerator(seed=42)
    identities = generator.generate_batch(10)
    
    # Create chain: id1 -> id2 -> id3 -> id4
    identities[0]["ssn"] = "111-11-1111"
    identities[1]["ssn"] = "111-11-1111"
    identities[1]["phone"] = "555-1234"
    identities[2]["phone"] = "555-1234"
    identities[2]["address"] = "123 Main St"
    identities[3]["address"] = "123 Main St"
    
    # Build network
    analyzer = NetworkAnalyzer()
    G = analyzer.build_network(identities)
    
    # Find paths
    source = identities[0]["identity_id"]
    target = identities[3]["identity_id"]
    
    paths = analyzer.find_shortest_paths(G, source, target)
    
    print(f"\nShortest Paths from {source} to {target}:")
    if paths:
        for i, path in enumerate(paths, 1):
            print(f"\nPath {i} ({len(path)-1} hops):")
            for j, node in enumerate(path):
                if j < len(path) - 1:
                    print(f"  {node} →")
                else:
                    print(f"  {node}")
    else:
        print("  No path found")


def example_6_neighbor_analysis():
    """Example 6: Neighbor analysis."""
    print("\n" + "=" * 60)
    print("Example 6: Neighbor Analysis")
    print("=" * 60)
    
    # Generate identities
    generator = SyntheticIdentityGenerator(seed=42)
    identities = generator.generate_batch(15)
    
    # Create network with central node
    central_ssn = "111-11-1111"
    identities[0]["ssn"] = central_ssn
    for i in range(1, 6):
        identities[i]["ssn"] = central_ssn
    
    # Build network
    analyzer = NetworkAnalyzer()
    G = analyzer.build_network(identities)
    
    # Analyze neighbors
    central_node = identities[0]["identity_id"]
    
    neighbors_1 = analyzer.get_neighbors(G, central_node, depth=1)
    neighbors_2 = analyzer.get_neighbors(G, central_node, depth=2)
    
    print(f"\nNeighbor Analysis for {central_node}:")
    print(f"  Direct neighbors (depth=1): {len(neighbors_1)}")
    print(f"  Extended network (depth=2): {len(neighbors_2)}")
    
    if neighbors_1:
        print(f"\n  Direct neighbors:")
        for neighbor in list(neighbors_1)[:5]:
            print(f"    - {neighbor}")


def example_7_subgraph_extraction():
    """Example 7: Subgraph extraction."""
    print("\n" + "=" * 60)
    print("Example 7: Subgraph Extraction")
    print("=" * 60)
    
    # Generate identities
    generator = SyntheticIdentityGenerator(seed=42)
    identities = generator.generate_batch(20)
    
    # Create fraud ring
    fraud_ssn = "111-11-1111"
    fraud_ring_ids = []
    for i in range(5):
        identities[i]["ssn"] = fraud_ssn
        fraud_ring_ids.append(identities[i]["identity_id"])
    
    # Build network
    analyzer = NetworkAnalyzer()
    G = analyzer.build_network(identities)
    
    # Extract fraud ring subgraph
    subgraph = analyzer.extract_subgraph(G, set(fraud_ring_ids))
    
    print(f"\nFraud Ring Subgraph:")
    print(f"  Nodes: {subgraph.number_of_nodes()}")
    print(f"  Edges: {subgraph.number_of_edges()}")
    
    # Analyze subgraph
    sub_metrics = analyzer.get_network_metrics(subgraph)
    print(f"\n  Subgraph Metrics:")
    print(f"    Density: {sub_metrics.density:.3f}")
    print(f"    Clustering: {sub_metrics.average_clustering:.3f}")
    print(f"    Risk Score: {sub_metrics.get_network_risk_score():.1f}/100")


def example_8_comprehensive_analysis():
    """Example 8: Comprehensive network analysis."""
    print("\n" + "=" * 60)
    print("Example 8: Comprehensive Network Analysis")
    print("=" * 60)
    
    # Generate identities
    generator = SyntheticIdentityGenerator(seed=42)
    identities = generator.generate_batch(30)
    
    # Create multiple fraud patterns
    # Ring 1: Shared SSN
    for i in range(5):
        identities[i]["ssn"] = "111-11-1111"
    
    # Ring 2: Shared phone
    for i in range(5, 10):
        identities[i]["phone"] = "555-1234"
    
    # Ring 3: Shared address
    for i in range(10, 15):
        identities[i]["address"] = "123 Main St"
    
    # Build network
    analyzer = NetworkAnalyzer()
    G = analyzer.build_network(identities)
    
    # Comprehensive analysis
    print(f"\n📊 Network Overview:")
    metrics = analyzer.get_network_metrics(G)
    print(f"  Nodes: {metrics.node_count}")
    print(f"  Edges: {metrics.edge_count}")
    print(f"  Density: {metrics.density:.3f}")
    print(f"  Components: {metrics.connected_components}")
    
    # Centrality analysis
    centrality_metrics = analyzer.calculate_centrality(G)
    stats = analyzer.get_node_statistics(G, centrality_metrics)
    
    print(f"\n📈 Node Statistics:")
    print(f"  Average Risk Score: {stats['average_risk_score']:.1f}")
    print(f"  High Risk Nodes: {stats['high_risk_count']}")
    print(f"  Medium Risk Nodes: {stats['medium_risk_count']}")
    print(f"  Low Risk Nodes: {stats['low_risk_count']}")
    
    print(f"\n👥 Role Distribution:")
    for role, count in stats['role_distribution'].items():
        print(f"  {role}: {count}")
    
    # High-risk identification
    high_risk = analyzer.identify_high_risk_nodes(G, threshold=70.0)
    
    print(f"\n🚨 High-Risk Nodes (≥70):")
    for node_id, risk_score in high_risk[:3]:
        print(f"  {node_id}: {risk_score:.1f}/100")
    
    # Network risk
    network_risk = metrics.get_network_risk_score()
    print(f"\n⚠️  Overall Network Risk: {network_risk:.1f}/100")
    
    if network_risk >= 70:
        print("  Status: 🔴 HIGH RISK - Immediate investigation required")
    elif network_risk >= 40:
        print("  Status: 🟡 MEDIUM RISK - Enhanced monitoring recommended")
    else:
        print("  Status: 🟢 LOW RISK - Normal monitoring")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("NETWORK ANALYZER EXAMPLES")
    print("=" * 60)
    
    examples = [
        example_1_basic_network_analysis,
        example_2_centrality_analysis,
        example_3_fraud_ring_detection,
        example_4_high_risk_identification,
        example_5_shortest_path_analysis,
        example_6_neighbor_analysis,
        example_7_subgraph_extraction,
        example_8_comprehensive_analysis,
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\n❌ Error in {example.__name__}: {e}")
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()

# Made with Bob
