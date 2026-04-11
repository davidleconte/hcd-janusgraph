"""
Graph Visualizer Examples
=========================

Demonstrates interactive network visualization for fraud detection
including risk-based coloring, community highlighting, and fraud ring
visualization.

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team
Date: 2026-04-11
Phase: 7.4 - Graph-Based Fraud Detection

Examples:
    1. Basic Network Visualization
    2. Risk-Based Node Coloring
    3. Community-Based Visualization
    4. Fraud Ring Highlighting
    5. Custom Layout Algorithms
    6. Integration with Full Analysis Pipeline
    7. Export to Multiple Formats
    8. Interactive Investigation Dashboard
"""

import sys
from pathlib import Path
from typing import Dict, List, Set

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import networkx as nx
from banking.graph import (
    NetworkAnalyzer,
    CommunityDetector,
    PatternAnalyzer,
    GraphVisualizer,
    VisualizationConfig,
)
from banking.identity import SyntheticIdentityGenerator


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def example_1_basic_visualization() -> None:
    """Example 1: Basic network visualization."""
    print_section("Example 1: Basic Network Visualization")
    
    # Create a simple fraud network
    G = nx.Graph()
    G.add_edges_from([
        ("Account_A", "Account_B"),
        ("Account_B", "Account_C"),
        ("Account_C", "Account_D"),
        ("Account_D", "Account_A"),
        ("Account_A", "Account_E"),
    ])
    
    print(f"Network: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    
    # Create visualizer
    visualizer = GraphVisualizer()
    
    try:
        # Create visualization
        fig = visualizer.visualize(
            G,
            title="Basic Fraud Network",
            output_file=Path("output/basic_network.html"),
        )
        print("✅ Visualization created: output/basic_network.html")
        print("   Open in browser to view interactive network")
    except ImportError as e:
        print(f"⚠️  Visualization requires plotly: {e}")
        print("   Install with: pip install plotly")


def example_2_risk_based_coloring() -> None:
    """Example 2: Risk-based node coloring."""
    print_section("Example 2: Risk-Based Node Coloring")
    
    # Create network
    G = nx.Graph()
    nodes = ["A", "B", "C", "D", "E", "F"]
    G.add_nodes_from(nodes)
    G.add_edges_from([
        ("A", "B"), ("A", "C"), ("A", "D"),  # A is hub
        ("B", "C"),
        ("D", "E"), ("E", "F"),
    ])
    
    # Assign risk scores
    risk_scores = {
        "A": 85.0,  # Critical - hub node
        "B": 70.0,  # High
        "C": 55.0,  # Medium
        "D": 35.0,  # Low
        "E": 20.0,  # Low
        "F": 10.0,  # Low
    }
    
    print("Risk Scores:")
    for node, score in sorted(risk_scores.items(), key=lambda x: x[1], reverse=True):
        level = "CRITICAL" if score >= 80 else "HIGH" if score >= 60 else "MEDIUM" if score >= 40 else "LOW"
        print(f"  {node}: {score:.1f} ({level})")
    
    # Create visualizer
    visualizer = GraphVisualizer()
    
    try:
        fig = visualizer.visualize(
            G,
            risk_scores=risk_scores,
            title="Risk-Based Network Visualization",
            output_file=Path("output/risk_based_network.html"),
        )
        print("\n✅ Visualization created: output/risk_based_network.html")
        print("   Color Legend:")
        print("   - Red: Critical Risk (≥80)")
        print("   - Orange: High Risk (≥60)")
        print("   - Yellow: Medium Risk (≥40)")
        print("   - Green: Low Risk (<40)")
    except ImportError as e:
        print(f"\n⚠️  Visualization requires plotly: {e}")


def example_3_community_visualization() -> None:
    """Example 3: Community-based visualization."""
    print_section("Example 3: Community-Based Visualization")
    
    # Create network with clear communities
    G = nx.Graph()
    
    # Community 1 (fraud ring)
    G.add_edges_from([
        ("FR1_A", "FR1_B"),
        ("FR1_B", "FR1_C"),
        ("FR1_C", "FR1_A"),
    ])
    
    # Community 2 (another fraud ring)
    G.add_edges_from([
        ("FR2_A", "FR2_B"),
        ("FR2_B", "FR2_C"),
        ("FR2_C", "FR2_D"),
        ("FR2_D", "FR2_A"),
    ])
    
    # Bridge between communities
    G.add_edge("FR1_A", "FR2_A")
    
    print(f"Network: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    
    # Detect communities
    detector = CommunityDetector()
    result = detector.detect_communities(G, algorithm="louvain")
    
    print(f"\nDetected {result.num_communities} communities:")
    for comm_id, community in result.communities.items():
        print(f"  Community {comm_id}: {community.size} members")
    
    # Create visualizer
    visualizer = GraphVisualizer()
    
    try:
        fig = visualizer.visualize(
            G,
            communities=result.node_to_community,
            title="Community Detection Visualization",
            output_file=Path("output/community_network.html"),
        )
        print("\n✅ Visualization created: output/community_network.html")
        print("   Each community is shown in a different color")
    except ImportError as e:
        print(f"\n⚠️  Visualization requires plotly: {e}")


def example_4_fraud_ring_highlighting() -> None:
    """Example 4: Fraud ring highlighting."""
    print_section("Example 4: Fraud Ring Highlighting")
    
    # Create network
    G = nx.Graph()
    
    # Fraud ring 1
    fraud_ring_1 = {"FR1_A", "FR1_B", "FR1_C"}
    G.add_edges_from([
        ("FR1_A", "FR1_B"),
        ("FR1_B", "FR1_C"),
        ("FR1_C", "FR1_A"),
    ])
    
    # Fraud ring 2
    fraud_ring_2 = {"FR2_A", "FR2_B", "FR2_C", "FR2_D"}
    G.add_edges_from([
        ("FR2_A", "FR2_B"),
        ("FR2_B", "FR2_C"),
        ("FR2_C", "FR2_D"),
        ("FR2_D", "FR2_A"),
    ])
    
    # Normal accounts
    G.add_edges_from([
        ("Normal_A", "Normal_B"),
        ("Normal_B", "Normal_C"),
    ])
    
    # Assign risk scores
    risk_scores = {}
    for node in fraud_ring_1 | fraud_ring_2:
        risk_scores[node] = 80.0  # High risk
    for node in {"Normal_A", "Normal_B", "Normal_C"}:
        risk_scores[node] = 20.0  # Low risk
    
    print(f"Network: {G.number_of_nodes()} nodes")
    print(f"Fraud Ring 1: {len(fraud_ring_1)} members")
    print(f"Fraud Ring 2: {len(fraud_ring_2)} members")
    print(f"Normal Accounts: 3")
    
    # Create visualizer
    visualizer = GraphVisualizer()
    
    try:
        fig = visualizer.visualize(
            G,
            risk_scores=risk_scores,
            fraud_rings=[fraud_ring_1, fraud_ring_2],
            title="Fraud Ring Detection",
            output_file=Path("output/fraud_rings.html"),
        )
        print("\n✅ Visualization created: output/fraud_rings.html")
        print("   Fraud ring members are highlighted with:")
        print("   - Red border")
        print("   - Diamond shape")
        print("   - Warning indicator in hover text")
    except ImportError as e:
        print(f"\n⚠️  Visualization requires plotly: {e}")


def example_5_custom_layouts() -> None:
    """Example 5: Custom layout algorithms."""
    print_section("Example 5: Custom Layout Algorithms")
    
    # Create a circular network
    G = nx.Graph()
    nodes = [f"Node_{i}" for i in range(8)]
    G.add_nodes_from(nodes)
    
    # Create circular connections
    for i in range(len(nodes)):
        G.add_edge(nodes[i], nodes[(i + 1) % len(nodes)])
    
    # Add some cross connections
    G.add_edge(nodes[0], nodes[4])
    G.add_edge(nodes[2], nodes[6])
    
    risk_scores = {node: 50.0 for node in nodes}
    
    layouts = ["spring", "circular", "kamada_kawai", "spectral"]
    
    print(f"Network: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    print(f"\nTesting {len(layouts)} layout algorithms:")
    
    for layout in layouts:
        config = VisualizationConfig(layout=layout)
        visualizer = GraphVisualizer(config)
        
        try:
            fig = visualizer.visualize(
                G,
                risk_scores=risk_scores,
                title=f"Network Layout: {layout.title()}",
                output_file=Path(f"output/layout_{layout}.html"),
            )
            print(f"  ✅ {layout.title()}: output/layout_{layout}.html")
        except ImportError:
            print(f"  ⚠️  {layout.title()}: plotly required")


def example_6_full_analysis_pipeline() -> None:
    """Example 6: Integration with full analysis pipeline."""
    print_section("Example 6: Full Analysis Pipeline Integration")
    
    print("Step 1: Generate synthetic identities")
    generator = SyntheticIdentityGenerator(seed=42)
    identities = generator.generate_batch(30)
    print(f"  Generated {len(identities)} identities")
    
    print("\nStep 2: Build network")
    network_analyzer = NetworkAnalyzer()
    G = network_analyzer.build_network(identities)
    print(f"  Network: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    
    print("\nStep 3: Calculate centrality metrics")
    centrality_metrics = network_analyzer.calculate_centrality(G)
    risk_scores = {
        node_id: metrics.get_risk_score()
        for node_id, metrics in centrality_metrics.items()
    }
    print(f"  Calculated risk scores for {len(risk_scores)} nodes")
    
    print("\nStep 4: Detect communities")
    community_detector = CommunityDetector()
    community_result = community_detector.detect_communities(G)
    print(f"  Detected {community_result.num_communities} communities")
    
    print("\nStep 5: Identify fraud rings")
    fraud_rings = community_result.get_fraud_rings(min_size=3, min_risk=60.0)
    print(f"  Found {len(fraud_rings)} potential fraud rings")
    
    print("\nStep 6: Create visualization")
    visualizer = GraphVisualizer()
    
    try:
        fig = visualizer.visualize(
            G,
            risk_scores=risk_scores,
            fraud_rings=[ring.members for ring in fraud_rings],
            title="Complete Fraud Network Analysis",
            output_file=Path("output/full_analysis.html"),
        )
        print("  ✅ Visualization created: output/full_analysis.html")
        
        print("\nAnalysis Summary:")
        print(f"  Total Identities: {len(identities)}")
        print(f"  Network Nodes: {G.number_of_nodes()}")
        print(f"  Network Edges: {G.number_of_edges()}")
        print(f"  Communities: {community_result.num_communities}")
        print(f"  Fraud Rings: {len(fraud_rings)}")
        
        high_risk_nodes = [n for n, s in risk_scores.items() if s >= 60.0]
        print(f"  High-Risk Nodes: {len(high_risk_nodes)}")
    except ImportError as e:
        print(f"  ⚠️  Visualization requires plotly: {e}")


def example_7_export_formats() -> None:
    """Example 7: Export to multiple formats."""
    print_section("Example 7: Export to Multiple Formats")
    
    # Create sample network
    G = nx.Graph()
    G.add_edges_from([
        ("A", "B"), ("B", "C"), ("C", "D"),
        ("D", "A"), ("A", "C"),
    ])
    
    risk_scores = {
        "A": 80.0,
        "B": 60.0,
        "C": 40.0,
        "D": 20.0,
    }
    
    print(f"Network: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    print("\nExporting to multiple formats:")
    
    # Plotly HTML (interactive)
    visualizer = GraphVisualizer()
    
    try:
        fig = visualizer.visualize(
            G,
            risk_scores=risk_scores,
            title="Fraud Network - Interactive",
            output_file=Path("output/export_plotly.html"),
        )
        print("  ✅ Plotly HTML: output/export_plotly.html (interactive)")
    except ImportError:
        print("  ⚠️  Plotly HTML: plotly required")
    
    # PyVis HTML (alternative interactive)
    try:
        net = visualizer.create_pyvis_network(
            G,
            risk_scores=risk_scores,
            output_file=Path("output/export_pyvis.html"),
        )
        if net:
            print("  ✅ PyVis HTML: output/export_pyvis.html (interactive)")
        else:
            print("  ⚠️  PyVis HTML: pyvis required")
    except Exception as e:
        print(f"  ⚠️  PyVis HTML: {e}")
    
    print("\nFormat Comparison:")
    print("  Plotly: Best for analysis, customizable, requires plotly")
    print("  PyVis: Physics-based layout, easy to use, requires pyvis")


def example_8_investigation_dashboard() -> None:
    """Example 8: Interactive investigation dashboard."""
    print_section("Example 8: Investigation Dashboard")
    
    print("Creating comprehensive investigation dashboard...")
    
    # Generate data
    generator = SyntheticIdentityGenerator(seed=42)
    identities = generator.generate_batch(25)
    
    # Build network
    network_analyzer = NetworkAnalyzer()
    G = network_analyzer.build_network(identities)
    
    # Calculate metrics
    centrality = network_analyzer.calculate_centrality(G)
    risk_scores = {n: m.get_risk_score() for n, m in centrality.items()}
    
    # Detect communities
    detector = CommunityDetector()
    communities = detector.detect_communities(G)
    fraud_rings = communities.get_fraud_rings(min_size=3, min_risk=60.0)
    
    # Analyze patterns
    pattern_analyzer = PatternAnalyzer()
    patterns = pattern_analyzer.analyze_patterns(G, identities)
    
    print(f"\nDashboard Data:")
    print(f"  Identities: {len(identities)}")
    print(f"  Network Nodes: {G.number_of_nodes()}")
    print(f"  Network Edges: {G.number_of_edges()}")
    print(f"  Communities: {communities.num_communities}")
    print(f"  Fraud Rings: {len(fraud_rings)}")
    print(f"  Patterns Detected: {patterns.get_pattern_summary()['total_patterns']}")
    
    # Create visualization
    config = VisualizationConfig(
        width=1600,
        height=1000,
        show_labels=True,
        enable_hover=True,
    )
    visualizer = GraphVisualizer(config)
    
    try:
        fig = visualizer.visualize(
            G,
            risk_scores=risk_scores,
            fraud_rings=[ring.members for ring in fraud_rings],
            title="Fraud Investigation Dashboard",
            output_file=Path("output/investigation_dashboard.html"),
        )
        
        print("\n✅ Dashboard created: output/investigation_dashboard.html")
        print("\nDashboard Features:")
        print("  - Interactive network visualization")
        print("  - Risk-based node coloring")
        print("  - Fraud ring highlighting")
        print("  - Hover for detailed information")
        print("  - Zoom and pan controls")
        print("  - Export-ready for reports")
        
        print("\nInvestigation Workflow:")
        print("  1. Open dashboard in browser")
        print("  2. Identify high-risk nodes (red/orange)")
        print("  3. Examine fraud rings (diamond shapes)")
        print("  4. Hover for detailed metrics")
        print("  5. Export for compliance reporting")
    except ImportError as e:
        print(f"\n⚠️  Dashboard requires plotly: {e}")


def main() -> None:
    """Run all examples."""
    print("\n" + "=" * 80)
    print("  GRAPH VISUALIZER EXAMPLES")
    print("  Interactive Network Visualization for Fraud Detection")
    print("=" * 80)
    
    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    print(f"\nOutput directory: {output_dir.absolute()}")
    
    examples = [
        ("Basic Visualization", example_1_basic_visualization),
        ("Risk-Based Coloring", example_2_risk_based_coloring),
        ("Community Visualization", example_3_community_visualization),
        ("Fraud Ring Highlighting", example_4_fraud_ring_highlighting),
        ("Custom Layouts", example_5_custom_layouts),
        ("Full Analysis Pipeline", example_6_full_analysis_pipeline),
        ("Export Formats", example_7_export_formats),
        ("Investigation Dashboard", example_8_investigation_dashboard),
    ]
    
    for i, (name, func) in enumerate(examples, 1):
        try:
            func()
        except Exception as e:
            print(f"\n❌ Error in {name}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("  All examples completed!")
    print("  Check the 'output' directory for generated visualizations")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()


# Made with Bob