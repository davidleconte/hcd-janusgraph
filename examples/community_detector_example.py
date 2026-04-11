"""
Community Detector Examples
===========================

Demonstrates community detection for fraud ring identification.

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team
Date: 2026-04-11
Phase: 7.4 - Graph-Based Fraud Detection

Run: python examples/community_detector_example.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from banking.graph import NetworkAnalyzer, CommunityDetector
from banking.identity import SyntheticIdentityGenerator


def example_1_basic_community_detection():
    """Example 1: Basic community detection."""
    print("\n" + "=" * 60)
    print("Example 1: Basic Community Detection")
    print("=" * 60)
    
    # Generate identities with fraud rings
    generator = SyntheticIdentityGenerator(seed=42)
    identities = generator.generate_batch(20)
    
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
    result = detector.detect_communities(G, algorithm="louvain")
    
    print(f"\nCommunity Detection Results:")
    print(f"  Algorithm: {result.algorithm}")
    print(f"  Total Communities: {result.total_communities}")
    print(f"  Modularity: {result.modularity:.3f}")
    
    print(f"\nTop 5 Communities by Size:")
    for i, community in enumerate(result.communities[:5], 1):
        print(f"\n  Community {i}:")
        print(f"    Size: {community.size} members")
        print(f"    Density: {community.density:.3f}")
        print(f"    Risk Score: {community.get_risk_score():.1f}/100")
        print(f"    Risk Level: {community.get_risk_level()}")


def example_2_fraud_ring_identification():
    """Example 2: Fraud ring identification."""
    print("\n" + "=" * 60)
    print("Example 2: Fraud Ring Identification")
    print("=" * 60)
    
    # Generate identities
    generator = SyntheticIdentityGenerator(seed=42)
    identities = generator.generate_batch(30)
    
    # Create multiple fraud rings
    for i in range(5):
        identities[i]["ssn"] = "111-11-1111"
        identities[i]["phone"] = "555-1234"
    
    for i in range(5, 10):
        identities[i]["ssn"] = "222-22-2222"
    
    for i in range(10, 15):
        identities[i]["address"] = "123 Main St"
    
    # Build network
    analyzer = NetworkAnalyzer()
    G = analyzer.build_network(identities)
    
    # Detect communities
    detector = CommunityDetector()
    result = detector.detect_communities(G)
    
    # Get fraud rings
    fraud_rings = result.get_fraud_rings(min_size=3, min_risk=60.0)
    
    print(f"\nFraud Ring Detection:")
    print(f"  Total Communities: {result.total_communities}")
    print(f"  Potential Fraud Rings: {len(fraud_rings)}")
    
    for i, ring in enumerate(fraud_rings, 1):
        print(f"\n  Fraud Ring {i}:")
        print(f"    Size: {ring.size} members")
        print(f"    Density: {ring.density:.3f}")
        print(f"    Risk Score: {ring.get_risk_score():.1f}/100")
        print(f"    Risk Level: {ring.get_risk_level()}")
        print(f"    Members: {', '.join(list(ring.members)[:5])}")
        if ring.size > 5:
            print(f"    ... and {ring.size - 5} more")


def example_3_algorithm_comparison():
    """Example 3: Algorithm comparison."""
    print("\n" + "=" * 60)
    print("Example 3: Algorithm Comparison")
    print("=" * 60)
    
    # Generate identities
    generator = SyntheticIdentityGenerator(seed=42)
    identities = generator.generate_batch(25)
    
    # Create fraud ring
    for i in range(8):
        identities[i]["ssn"] = "111-11-1111"
    
    # Build network
    analyzer = NetworkAnalyzer()
    G = analyzer.build_network(identities)
    
    # Compare algorithms
    detector = CommunityDetector()
    results = detector.compare_algorithms(G)
    
    print(f"\nAlgorithm Comparison:")
    for algorithm, result in results.items():
        print(f"\n  {algorithm.upper()}:")
        print(f"    Communities: {result.total_communities}")
        print(f"    Modularity: {result.modularity:.3f}")
        print(f"    Largest Community: {result.communities[0].size if result.communities else 0}")
        
        fraud_rings = result.get_fraud_rings(min_size=3, min_risk=60.0)
        print(f"    Fraud Rings Detected: {len(fraud_rings)}")


def example_4_community_statistics():
    """Example 4: Community statistics."""
    print("\n" + "=" * 60)
    print("Example 4: Community Statistics")
    print("=" * 60)
    
    # Generate identities
    generator = SyntheticIdentityGenerator(seed=42)
    identities = generator.generate_batch(30)
    
    # Create varied communities
    for i in range(10):
        identities[i]["ssn"] = "111-11-1111"
    for i in range(10, 15):
        identities[i]["ssn"] = "222-22-2222"
    
    # Build network
    analyzer = NetworkAnalyzer()
    G = analyzer.build_network(identities)
    
    # Detect communities
    detector = CommunityDetector()
    result = detector.detect_communities(G)
    
    # Get statistics
    stats = result.get_statistics()
    
    print(f"\nCommunity Statistics:")
    print(f"  Total Communities: {stats['total_communities']}")
    print(f"  Total Members: {stats['total_members']}")
    print(f"  Average Size: {stats['average_size']:.1f}")
    print(f"  Largest Community: {stats['largest_community']}")
    print(f"  Smallest Community: {stats['smallest_community']}")
    print(f"  Average Density: {stats['average_density']:.3f}")
    print(f"  Modularity: {stats['modularity']:.3f}")
    print(f"  Average Risk Score: {stats['average_risk_score']:.1f}")
    print(f"  High Risk Communities: {stats['high_risk_communities']}")
    
    print(f"\n  Risk Level Distribution:")
    for level, count in stats['risk_level_distribution'].items():
        print(f"    {level}: {count}")


def example_5_inter_community_connections():
    """Example 5: Inter-community connections."""
    print("\n" + "=" * 60)
    print("Example 5: Inter-Community Connections")
    print("=" * 60)
    
    # Generate identities
    generator = SyntheticIdentityGenerator(seed=42)
    identities = generator.generate_batch(20)
    
    # Create two fraud rings
    for i in range(5):
        identities[i]["ssn"] = "111-11-1111"
    for i in range(5, 10):
        identities[i]["ssn"] = "222-22-2222"
    
    # Add connection between rings
    identities[4]["phone"] = "555-1234"
    identities[5]["phone"] = "555-1234"
    
    # Build network
    analyzer = NetworkAnalyzer()
    G = analyzer.build_network(identities)
    
    # Detect communities
    detector = CommunityDetector()
    result = detector.detect_communities(G)
    
    # Get inter-community edges
    inter_edges = detector.get_inter_community_edges(G, result)
    
    print(f"\nInter-Community Analysis:")
    print(f"  Total Communities: {result.total_communities}")
    print(f"  Inter-Community Edges: {len(inter_edges)}")
    
    if inter_edges:
        print(f"\n  Connections Between Communities:")
        for node1, node2, comm1, comm2 in inter_edges[:5]:
            print(f"    {node1} (Community {comm1}) ↔ {node2} (Community {comm2})")


def example_6_small_community_merging():
    """Example 6: Small community merging."""
    print("\n" + "=" * 60)
    print("Example 6: Small Community Merging")
    print("=" * 60)
    
    # Generate identities
    generator = SyntheticIdentityGenerator(seed=42)
    identities = generator.generate_batch(25)
    
    # Create one large and several small communities
    for i in range(10):
        identities[i]["ssn"] = "111-11-1111"
    
    identities[10]["ssn"] = "222-22-2222"
    identities[11]["ssn"] = "222-22-2222"
    
    identities[12]["ssn"] = "333-33-3333"
    identities[13]["ssn"] = "333-33-3333"
    
    # Build network
    analyzer = NetworkAnalyzer()
    G = analyzer.build_network(identities)
    
    # Detect communities
    detector = CommunityDetector()
    result = detector.detect_communities(G)
    
    print(f"\nBefore Merging:")
    print(f"  Total Communities: {result.total_communities}")
    print(f"  Community Sizes: {[c.size for c in result.communities]}")
    
    # Merge small communities
    merged = detector.merge_small_communities(G, result, min_size=3)
    
    print(f"\nAfter Merging (min_size=3):")
    print(f"  Total Communities: {merged.total_communities}")
    print(f"  Community Sizes: {[c.size for c in merged.communities]}")
    print(f"  Modularity Change: {result.modularity:.3f} → {merged.modularity:.3f}")


def example_7_comprehensive_analysis():
    """Example 7: Comprehensive fraud ring analysis."""
    print("\n" + "=" * 60)
    print("Example 7: Comprehensive Fraud Ring Analysis")
    print("=" * 60)
    
    # Generate identities
    generator = SyntheticIdentityGenerator(seed=42)
    identities = generator.generate_batch(40)
    
    # Create multiple fraud patterns
    # Ring 1: Large, high-risk
    for i in range(12):
        identities[i]["ssn"] = "111-11-1111"
        identities[i]["phone"] = "555-1234"
    
    # Ring 2: Medium, medium-risk
    for i in range(12, 18):
        identities[i]["ssn"] = "222-22-2222"
    
    # Ring 3: Small, low-risk
    for i in range(18, 21):
        identities[i]["address"] = "123 Main St"
    
    # Build network
    analyzer = NetworkAnalyzer()
    G = analyzer.build_network(identities)
    
    # Detect communities
    detector = CommunityDetector()
    result = detector.detect_communities(G)
    
    print(f"\n📊 Network Overview:")
    print(f"  Nodes: {G.number_of_nodes()}")
    print(f"  Edges: {G.number_of_edges()}")
    print(f"  Communities: {result.total_communities}")
    print(f"  Modularity: {result.modularity:.3f}")
    
    # Statistics
    stats = result.get_statistics()
    print(f"\n📈 Community Statistics:")
    print(f"  Average Size: {stats['average_size']:.1f}")
    print(f"  Average Density: {stats['average_density']:.3f}")
    print(f"  Average Risk: {stats['average_risk_score']:.1f}/100")
    
    # Fraud rings
    fraud_rings = result.get_fraud_rings(min_size=3, min_risk=60.0)
    print(f"\n🚨 Fraud Ring Detection:")
    print(f"  High-Risk Rings: {len(fraud_rings)}")
    
    for i, ring in enumerate(fraud_rings, 1):
        print(f"\n  Ring {i}:")
        print(f"    Size: {ring.size} members")
        print(f"    Density: {ring.density:.3f}")
        print(f"    Risk: {ring.get_risk_score():.1f}/100")
        print(f"    Level: {ring.get_risk_level().upper()}")
        
        if ring.get_risk_level() == "critical":
            print(f"    ⚠️  CRITICAL - Immediate investigation required")
        elif ring.get_risk_level() == "high":
            print(f"    ⚠️  HIGH - Priority investigation")
    
    # Risk distribution
    print(f"\n📊 Risk Distribution:")
    for level, count in stats['risk_level_distribution'].items():
        print(f"  {level.upper()}: {count} communities")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("COMMUNITY DETECTOR EXAMPLES")
    print("=" * 60)
    
    examples = [
        example_1_basic_community_detection,
        example_2_fraud_ring_identification,
        example_3_algorithm_comparison,
        example_4_community_statistics,
        example_5_inter_community_connections,
        example_6_small_community_merging,
        example_7_comprehensive_analysis,
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
