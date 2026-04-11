"""
Pattern Analyzer Examples
=========================

Demonstrates relationship pattern detection including shared attributes,
circular references, layering structures, and velocity patterns.

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team
Date: 2026-04-11
Phase: 7.4 - Graph-Based Fraud Detection

Examples:
    1. Shared Attribute Detection (SSN, phone, address)
    2. Circular Pattern Detection (money laundering cycles)
    3. Layering Pattern Detection (shell company networks)
    4. Velocity Pattern Detection (rapid account takeover)
    5. Comprehensive Pattern Analysis
    6. Integration with Identity Detection
    7. High-Risk Pattern Filtering
    8. Pattern-Based Investigation Workflow
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import networkx as nx
from banking.graph import PatternAnalyzer
from banking.identity import SyntheticIdentityGenerator


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def example_1_shared_attribute_detection() -> None:
    """Example 1: Detect shared attribute patterns."""
    print_section("Example 1: Shared Attribute Detection")
    
    # Create identities with shared attributes
    identities = [
        {
            "id": "person1",
            "name": "John Doe",
            "ssn": "123-45-6789",
            "phone": "555-1234",
            "address": "123 Main St",
            "email": "john@example.com",
        },
        {
            "id": "person2",
            "name": "Jane Smith",
            "ssn": "123-45-6789",  # Shared SSN (suspicious!)
            "phone": "555-5678",
            "address": "456 Oak Ave",
            "email": "jane@example.com",
        },
        {
            "id": "person3",
            "name": "Bob Johnson",
            "ssn": "987-65-4321",
            "phone": "555-1234",  # Shared phone
            "address": "123 Main St",  # Shared address
            "email": "bob@example.com",
        },
        {
            "id": "person4",
            "name": "Alice Williams",
            "ssn": "111-22-3333",
            "phone": "555-9999",
            "address": "123 Main St",  # Shared address
            "email": "alice@example.com",
        },
    ]
    
    # Detect shared attributes
    analyzer = PatternAnalyzer()
    patterns = analyzer.detect_shared_attributes(identities)
    
    print(f"Found {len(patterns)} shared attribute patterns:\n")
    
    for i, pattern in enumerate(patterns, 1):
        risk_score = pattern.get_risk_score()
        risk_level = pattern.get_risk_level()
        
        print(f"{i}. {pattern.attribute_type.upper()} Pattern:")
        print(f"   Value: {pattern.attribute_value}")
        print(f"   Entities: {pattern.entity_count}")
        print(f"   Risk Score: {risk_score:.1f}/100")
        print(f"   Risk Level: {risk_level.upper()}")
        print(f"   Entity IDs: {', '.join(sorted(pattern.entities))}")
        print()


def example_2_circular_pattern_detection() -> None:
    """Example 2: Detect circular patterns (money laundering cycles)."""
    print_section("Example 2: Circular Pattern Detection")
    
    # Create a graph with circular patterns
    G = nx.Graph()
    
    # Triangle pattern (A → B → C → A)
    G.add_edge("Account_A", "Account_B", type="transfer", value=50000.0)
    G.add_edge("Account_B", "Account_C", type="transfer", value=45000.0)
    G.add_edge("Account_C", "Account_A", type="transfer", value=40000.0)
    
    # Square pattern (D → E → F → G → D)
    G.add_edge("Account_D", "Account_E", type="transfer", value=20000.0)
    G.add_edge("Account_E", "Account_F", type="transfer", value=18000.0)
    G.add_edge("Account_F", "Account_G", type="transfer", value=16000.0)
    G.add_edge("Account_G", "Account_D", type="transfer", value=14000.0)
    
    # Detect circular patterns
    analyzer = PatternAnalyzer()
    patterns = analyzer.detect_circular_patterns(G, max_cycle_length=6)
    
    print(f"Found {len(patterns)} circular patterns:\n")
    
    for i, pattern in enumerate(patterns, 1):
        risk_score = pattern.get_risk_score()
        risk_level = pattern.get_risk_level()
        
        print(f"{i}. Cycle Length: {pattern.length}")
        print(f"   Path: {' → '.join(pattern.cycle)}")
        print(f"   Total Value: ${pattern.total_value:,.2f}")
        print(f"   Risk Score: {risk_score:.1f}/100")
        print(f"   Risk Level: {risk_level.upper()}")
        print()


def example_3_layering_pattern_detection() -> None:
    """Example 3: Detect layering patterns (shell company networks)."""
    print_section("Example 3: Layering Pattern Detection")
    
    # Create a directed graph with layering structure
    G = nx.DiGraph()
    
    # Root entity (beneficial owner)
    root = "Beneficial_Owner"
    
    # Layer 1: Holding companies
    layer1 = ["Holding_A", "Holding_B", "Holding_C"]
    for company in layer1:
        G.add_edge(root, company, type="ownership")
    
    # Layer 2: Operating companies
    layer2 = ["Operating_A1", "Operating_A2", "Operating_B1", "Operating_C1"]
    G.add_edge("Holding_A", "Operating_A1", type="ownership")
    G.add_edge("Holding_A", "Operating_A2", type="ownership")
    G.add_edge("Holding_B", "Operating_B1", type="ownership")
    G.add_edge("Holding_C", "Operating_C1", type="ownership")
    
    # Layer 3: Subsidiaries
    layer3 = ["Sub_A1_1", "Sub_A2_1", "Sub_B1_1", "Sub_C1_1"]
    G.add_edge("Operating_A1", "Sub_A1_1", type="ownership")
    G.add_edge("Operating_A2", "Sub_A2_1", type="ownership")
    G.add_edge("Operating_B1", "Sub_B1_1", type="ownership")
    G.add_edge("Operating_C1", "Sub_C1_1", type="ownership")
    
    # Detect layering patterns
    analyzer = PatternAnalyzer()
    patterns = analyzer.detect_layering_patterns(G, min_depth=3)
    
    print(f"Found {len(patterns)} layering patterns:\n")
    
    for i, pattern in enumerate(patterns, 1):
        risk_score = pattern.get_risk_score()
        risk_level = pattern.get_risk_level()
        
        print(f"{i}. Root Entity: {pattern.root_entity}")
        print(f"   Depth: {pattern.depth} layers")
        print(f"   Total Entities: {pattern.total_entities}")
        print(f"   Risk Score: {risk_score:.1f}/100")
        print(f"   Risk Level: {risk_level.upper()}")
        print(f"   Layer Structure:")
        for j, layer in enumerate(pattern.layers):
            print(f"     Layer {j}: {len(layer)} entities")
        print()


def example_4_velocity_pattern_detection() -> None:
    """Example 4: Detect velocity patterns (rapid account takeover)."""
    print_section("Example 4: Velocity Pattern Detection")
    
    # Create a graph with timestamp data
    G = nx.Graph()
    now = datetime.now()
    
    # Rapid connections (account takeover pattern)
    entity = "Compromised_Account"
    for i in range(15):
        target = f"New_Payee_{i}"
        timestamp = now + timedelta(days=i * 0.5)  # 15 connections in 7.5 days
        G.add_edge(entity, target, timestamp=timestamp, type="payment")
    
    # Normal connections (legitimate account)
    normal_entity = "Normal_Account"
    for i in range(5):
        target = f"Regular_Payee_{i}"
        timestamp = now + timedelta(days=i * 30)  # 5 connections in 150 days
        G.add_edge(normal_entity, target, timestamp=timestamp, type="payment")
    
    # Detect velocity patterns
    analyzer = PatternAnalyzer()
    patterns = analyzer.detect_velocity_patterns(
        G, time_window_days=30, min_connections=5
    )
    
    print(f"Found {len(patterns)} velocity patterns:\n")
    
    for i, pattern in enumerate(patterns, 1):
        risk_score = pattern.get_risk_score()
        risk_level = pattern.get_risk_level()
        
        print(f"{i}. Entity: {pattern.entity_id}")
        print(f"   Connections: {pattern.connection_count} in {pattern.time_window_days} days")
        print(f"   Rate: {pattern.connection_rate:.2f} connections/day")
        print(f"   Risk Score: {risk_score:.1f}/100")
        print(f"   Risk Level: {risk_level.upper()}")
        print()


def example_5_comprehensive_analysis() -> None:
    """Example 5: Comprehensive pattern analysis."""
    print_section("Example 5: Comprehensive Pattern Analysis")
    
    # Create a complex fraud network
    G = nx.Graph()
    
    # Add circular pattern
    G.add_edges_from([
        ("A", "B", {"type": "transfer", "value": 50000}),
        ("B", "C", {"type": "transfer", "value": 45000}),
        ("C", "A", {"type": "transfer", "value": 40000}),
    ])
    
    # Add velocity pattern
    now = datetime.now()
    for i in range(10):
        G.add_edge(
            "A",
            f"Target_{i}",
            timestamp=now + timedelta(days=i),
            type="payment",
        )
    
    # Create identities with shared attributes
    identities = [
        {"id": "A", "ssn": "123-45-6789", "phone": "555-1234"},
        {"id": "B", "ssn": "123-45-6789", "phone": "555-5678"},
        {"id": "C", "ssn": "987-65-4321", "phone": "555-1234"},
    ]
    
    # Perform comprehensive analysis
    analyzer = PatternAnalyzer()
    result = analyzer.analyze_patterns(G, identities)
    
    # Print summary
    summary = result.get_pattern_summary()
    print("Pattern Analysis Summary:")
    print(f"  Shared Attribute Patterns: {summary['shared_attribute_patterns']}")
    print(f"  Circular Patterns: {summary['circular_patterns']}")
    print(f"  Layering Patterns: {summary['layering_patterns']}")
    print(f"  Velocity Patterns: {summary['velocity_patterns']}")
    print(f"  Total Patterns: {summary['total_patterns']}")
    print()
    
    # Get high-risk patterns
    high_risk = result.get_high_risk_patterns(min_risk=60.0)
    print(f"High-Risk Patterns (≥60):")
    print(f"  Shared Attributes: {len(high_risk['shared_attributes'])}")
    print(f"  Circular: {len(high_risk['circular'])}")
    print(f"  Layering: {len(high_risk['layering'])}")
    print(f"  Velocity: {len(high_risk['velocity'])}")


def example_6_integration_with_identity_detection() -> None:
    """Example 6: Integration with identity detection."""
    print_section("Example 6: Integration with Identity Detection")
    
    # Generate synthetic identities
    generator = SyntheticIdentityGenerator(seed=42)
    identities = generator.generate_batch(20)
    
    print(f"Generated {len(identities)} synthetic identities")
    print()
    
    # Detect shared attribute patterns
    analyzer = PatternAnalyzer()
    patterns = analyzer.detect_shared_attributes(identities)
    
    print(f"Found {len(patterns)} shared attribute patterns")
    print()
    
    # Show high-risk patterns
    high_risk_patterns = [p for p in patterns if p.get_risk_score() >= 60.0]
    print(f"High-Risk Patterns: {len(high_risk_patterns)}")
    
    for i, pattern in enumerate(high_risk_patterns[:3], 1):
        print(f"\n{i}. {pattern.attribute_type.upper()}: {pattern.entity_count} entities")
        print(f"   Risk Score: {pattern.get_risk_score():.1f}/100")
        print(f"   Risk Level: {pattern.get_risk_level().upper()}")


def example_7_high_risk_filtering() -> None:
    """Example 7: Filter and prioritize high-risk patterns."""
    print_section("Example 7: High-Risk Pattern Filtering")
    
    # Create test data
    identities = [
        {"id": f"id{i}", "ssn": "123-45-6789"} for i in range(10)
    ]
    
    G = nx.Graph()
    G.add_edges_from([("A", "B"), ("B", "C"), ("C", "A")])
    
    # Analyze patterns
    analyzer = PatternAnalyzer()
    result = analyzer.analyze_patterns(G, identities)
    
    # Filter by risk level
    risk_thresholds = [80.0, 60.0, 40.0]
    
    for threshold in risk_thresholds:
        high_risk = result.get_high_risk_patterns(min_risk=threshold)
        total = sum(len(patterns) for patterns in high_risk.values())
        
        print(f"Patterns with risk ≥{threshold}:")
        print(f"  Total: {total}")
        for pattern_type, patterns in high_risk.items():
            if patterns:
                print(f"  {pattern_type}: {len(patterns)}")
        print()


def example_8_investigation_workflow() -> None:
    """Example 8: Pattern-based investigation workflow."""
    print_section("Example 8: Investigation Workflow")
    
    print("Step 1: Generate synthetic identities")
    generator = SyntheticIdentityGenerator(seed=42)
    identities = generator.generate_batch(30)
    print(f"  Generated {len(identities)} identities")
    print()
    
    print("Step 2: Build network from identities")
    from banking.graph import NetworkAnalyzer
    network_analyzer = NetworkAnalyzer()
    G = network_analyzer.build_network(identities)
    print(f"  Network: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    print()
    
    print("Step 3: Detect patterns")
    pattern_analyzer = PatternAnalyzer()
    result = pattern_analyzer.analyze_patterns(G, identities)
    summary = result.get_pattern_summary()
    print(f"  Found {summary['total_patterns']} total patterns")
    print()
    
    print("Step 4: Identify high-risk patterns")
    high_risk = result.get_high_risk_patterns(min_risk=60.0)
    total_high_risk = sum(len(patterns) for patterns in high_risk.values())
    print(f"  High-risk patterns: {total_high_risk}")
    print()
    
    print("Step 5: Prioritize investigation targets")
    # Get entities involved in high-risk patterns
    entities_to_investigate = set()
    
    for pattern in high_risk["shared_attributes"]:
        entities_to_investigate.update(pattern.entities)
    
    print(f"  Entities requiring investigation: {len(entities_to_investigate)}")
    print()
    
    print("Step 6: Generate investigation report")
    print("  Investigation Report:")
    print(f"    Total Identities: {len(identities)}")
    print(f"    Network Size: {G.number_of_nodes()} nodes")
    print(f"    Patterns Detected: {summary['total_patterns']}")
    print(f"    High-Risk Patterns: {total_high_risk}")
    print(f"    Investigation Targets: {len(entities_to_investigate)}")
    print()
    
    print("  Recommended Actions:")
    if total_high_risk >= 5:
        print("    - URGENT: Multiple high-risk patterns detected")
        print("    - Escalate to fraud investigation team")
        print("    - Freeze suspicious accounts")
    elif total_high_risk >= 2:
        print("    - HIGH: Significant patterns detected")
        print("    - Conduct detailed review")
        print("    - Monitor transactions closely")
    else:
        print("    - MEDIUM: Some patterns detected")
        print("    - Continue routine monitoring")


def main() -> None:
    """Run all examples."""
    print("\n" + "=" * 80)
    print("  PATTERN ANALYZER EXAMPLES")
    print("  Graph-Based Fraud Detection - Relationship Pattern Analysis")
    print("=" * 80)
    
    examples = [
        ("Shared Attribute Detection", example_1_shared_attribute_detection),
        ("Circular Pattern Detection", example_2_circular_pattern_detection),
        ("Layering Pattern Detection", example_3_layering_pattern_detection),
        ("Velocity Pattern Detection", example_4_velocity_pattern_detection),
        ("Comprehensive Analysis", example_5_comprehensive_analysis),
        ("Integration with Identity Detection", example_6_integration_with_identity_detection),
        ("High-Risk Filtering", example_7_high_risk_filtering),
        ("Investigation Workflow", example_8_investigation_workflow),
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
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()


# Made with Bob