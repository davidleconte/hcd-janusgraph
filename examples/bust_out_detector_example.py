#!/usr/bin/env python3
"""
Bust-Out Detector Example
=========================

Demonstrates bust-out fraud detection capabilities.

Bust-out schemes follow this pattern:
1. Create synthetic identity
2. Build credit history (6-24 months)
3. Rapidly increase credit limits
4. Max out all credit simultaneously
5. Disappear (no payments, no contact)

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team
Date: 2026-04-11
Phase: 7.2 - Synthetic Identity Fraud Detection
"""

from banking.identity import (
    SyntheticIdentityGenerator,
    BustOutDetector,
)


def example_1_basic_detection():
    """Example 1: Basic bust-out detection."""
    print("\n" + "=" * 80)
    print("Example 1: Basic Bust-Out Detection")
    print("=" * 80)
    
    # Generate synthetic identities
    gen = SyntheticIdentityGenerator(seed=42, config={
        "synthetic_probability": 1.0,
        "bust_out_probability": 0.5,
    })
    identities = gen.generate_batch(5)
    
    # Detect bust-out schemes
    detector = BustOutDetector()
    
    for identity in identities:
        result = detector.detect(identity)
        
        print(f"\nIdentity: {identity['identity_id']}")
        print(f"  Type: {identity['identity_type']}")
        print(f"  Bust-Out Score: {result.bust_out_score}/100")
        print(f"  Risk Level: {result.risk_level}")
        print(f"  Is Bust-Out: {result.is_bust_out}")
        print(f"  Credit Velocity: ${result.credit_velocity:.0f}/month")
        print(f"  Utilization Spike: {result.utilization_spike}")
        print(f"  Recent Inactivity: {result.recent_inactivity}")
        
        if result.indicators:
            print(f"  Indicators ({len(result.indicators)}):")
            for ind in result.indicators[:3]:  # Show first 3
                print(f"    - [{ind.severity.upper()}] {ind.description}")


def example_2_high_risk_analysis():
    """Example 2: High-risk identity analysis."""
    print("\n" + "=" * 80)
    print("Example 2: High-Risk Identity Analysis")
    print("=" * 80)
    
    # Generate larger batch
    gen = SyntheticIdentityGenerator(seed=123, config={
        "synthetic_probability": 1.0,
        "bust_out_probability": 0.7,
    })
    identities = gen.generate_batch(20)
    
    # Find high-risk identities
    detector = BustOutDetector()
    high_risk = detector.get_high_risk_identities(identities, min_score=70)
    
    print(f"\nFound {len(high_risk)} high-risk identities (score >= 70)")
    print("\nTop 5 High-Risk Identities:")
    print("-" * 80)
    
    for i, result in enumerate(high_risk[:5], 1):
        identity = next(id for id in identities if id['identity_id'] == result.identity_id)
        print(f"\n{i}. Identity: {result.identity_id}")
        print(f"   Score: {result.bust_out_score}/100 ({result.risk_level})")
        print(f"   Credit: ${identity['total_credit_limit']:.0f} "
              f"(age: {identity['credit_file_age_months']} months)")
        print(f"   Velocity: ${result.credit_velocity:.0f}/month")
        print(f"   Utilization: {identity['credit_utilization']:.0%}")
        print(f"   Indicators: {len(result.indicators)}")
        
        if result.recommendations:
            print(f"   Recommendations:")
            for rec in result.recommendations[:2]:
                print(f"     • {rec}")


def example_3_credit_velocity_analysis():
    """Example 3: Credit velocity analysis."""
    print("\n" + "=" * 80)
    print("Example 3: Credit Velocity Analysis")
    print("=" * 80)
    
    # Generate identities with varying credit patterns
    gen = SyntheticIdentityGenerator(seed=999)
    identities = gen.generate_batch(10)
    
    # Use lower threshold to detect more cases
    detector = BustOutDetector(config={"high_velocity_threshold": 2000})
    results = detector.detect_batch(identities)
    
    # Sort by velocity
    sorted_results = sorted(results, key=lambda r: r.credit_velocity, reverse=True)
    
    print("\nCredit Velocity Rankings:")
    print("-" * 80)
    print(f"{'Rank':<6} {'Identity':<15} {'Velocity':<15} {'Age':<10} {'Limit':<15} {'Risk'}")
    print("-" * 80)
    
    for i, result in enumerate(sorted_results, 1):
        identity = next(id for id in identities if id['identity_id'] == result.identity_id)
        print(f"{i:<6} {result.identity_id:<15} "
              f"${result.credit_velocity:>8,.0f}/mo   "
              f"{identity['credit_file_age_months']:>3} mo     "
              f"${identity['total_credit_limit']:>10,.0f}   "
              f"{result.risk_level}")


def example_4_indicator_breakdown():
    """Example 4: Detailed indicator breakdown."""
    print("\n" + "=" * 80)
    print("Example 4: Detailed Indicator Breakdown")
    print("=" * 80)
    
    # Generate high-risk identity
    gen = SyntheticIdentityGenerator(seed=42, config={
        "synthetic_probability": 1.0,
        "bust_out_probability": 1.0,
    })
    identity = gen.generate()
    
    # Detect with detailed analysis
    detector = BustOutDetector()
    result = detector.detect(identity)
    
    print(f"\nIdentity: {identity['identity_id']}")
    print(f"Type: {identity['identity_type']}")
    print(f"Bust-Out Score: {result.bust_out_score}/100")
    print(f"Risk Level: {result.risk_level}")
    
    print(f"\nCredit Profile:")
    print(f"  Score: {identity['credit_score']}")
    print(f"  File Age: {identity['credit_file_age_months']} months")
    print(f"  Total Limit: ${identity['total_credit_limit']:,.0f}")
    print(f"  Utilization: {identity['credit_utilization']:.0%}")
    print(f"  Accounts: {identity['num_credit_accounts']}")
    
    print(f"\nBust-Out Metrics:")
    print(f"  Credit Velocity: ${result.credit_velocity:,.0f}/month")
    print(f"  Utilization Spike: {result.utilization_spike}")
    print(f"  Recent Inactivity: {result.recent_inactivity}")
    print(f"  Max-Out Percentage: {result.max_out_percentage:.0%}")
    
    print(f"\nIndicators ({len(result.indicators)}):")
    for ind in result.indicators:
        print(f"  [{ind.severity.upper():8}] {ind.indicator_type:30} "
              f"(+{ind.score:2} pts) - {ind.description}")
    
    print(f"\nRecommendations ({len(result.recommendations)}):")
    for i, rec in enumerate(result.recommendations, 1):
        print(f"  {i}. {rec}")


def example_5_statistics_and_reporting():
    """Example 5: Statistics and reporting."""
    print("\n" + "=" * 80)
    print("Example 5: Statistics and Reporting")
    print("=" * 80)
    
    # Generate large batch
    gen = SyntheticIdentityGenerator(seed=42, config={
        "synthetic_probability": 0.8,
        "bust_out_probability": 0.5,
    })
    identities = gen.generate_batch(50)
    
    # Detect all
    detector = BustOutDetector()
    results = detector.detect_batch(identities)
    
    # Get statistics
    stats = detector.get_statistics(results)
    
    print("\nBust-Out Detection Statistics:")
    print("-" * 80)
    print(f"Total Identities Analyzed: {stats['total_identities']}")
    print(f"Bust-Out Cases Detected: {stats['bust_out_count']} "
          f"({stats['bust_out_rate']:.1%})")
    print(f"Average Bust-Out Score: {stats['average_bust_out_score']:.1f}/100")
    
    print(f"\nRisk Level Distribution:")
    for level, count in stats['risk_level_distribution'].items():
        pct = count / stats['total_identities'] * 100
        bar = "█" * int(pct / 2)
        print(f"  {level:8}: {count:3} ({pct:5.1f}%) {bar}")
    
    print(f"\nTop Indicators:")
    for indicator, count in stats['top_indicators'][:5]:
        pct = count / stats['total_identities'] * 100
        print(f"  {indicator:30}: {count:3} ({pct:5.1f}%)")
    
    print(f"\nCredit Velocity Statistics:")
    print(f"  Average: ${stats['average_credit_velocity']:,.0f}/month")
    print(f"  Maximum: ${stats['max_credit_velocity']:,.0f}/month")
    
    print(f"\nUtilization Statistics:")
    print(f"  High Utilization (>90%): {stats['high_utilization_count']} "
          f"({stats['high_utilization_count']/stats['total_identities']:.1%})")


def example_6_comparative_analysis():
    """Example 6: Comparative analysis (synthetic vs legitimate)."""
    print("\n" + "=" * 80)
    print("Example 6: Comparative Analysis (Synthetic vs Legitimate)")
    print("=" * 80)
    
    # Generate synthetic identities
    gen_synthetic = SyntheticIdentityGenerator(seed=42, config={
        "synthetic_probability": 1.0,
        "bust_out_probability": 0.7,
    })
    synthetic_ids = gen_synthetic.generate_batch(25)
    
    # Generate legitimate identities
    gen_legit = SyntheticIdentityGenerator(seed=123, config={
        "synthetic_probability": 0.0,
    })
    legit_ids = gen_legit.generate_batch(25)
    
    # Detect both
    detector = BustOutDetector()
    synthetic_results = detector.detect_batch(synthetic_ids)
    legit_results = detector.detect_batch(legit_ids)
    
    # Compare statistics
    synthetic_stats = detector.get_statistics(synthetic_results)
    legit_stats = detector.get_statistics(legit_results)
    
    print("\nComparative Statistics:")
    print("-" * 80)
    print(f"{'Metric':<35} {'Synthetic':<20} {'Legitimate':<20}")
    print("-" * 80)
    
    print(f"{'Bust-Out Rate':<35} "
          f"{synthetic_stats['bust_out_rate']:>6.1%}              "
          f"{legit_stats['bust_out_rate']:>6.1%}")
    
    print(f"{'Average Bust-Out Score':<35} "
          f"{synthetic_stats['average_bust_out_score']:>6.1f}/100          "
          f"{legit_stats['average_bust_out_score']:>6.1f}/100")
    
    print(f"{'Average Credit Velocity':<35} "
          f"${synthetic_stats['average_credit_velocity']:>8,.0f}/mo      "
          f"${legit_stats['average_credit_velocity']:>8,.0f}/mo")
    
    print(f"{'High Utilization Rate':<35} "
          f"{synthetic_stats['high_utilization_count']/25:>6.1%}              "
          f"{legit_stats['high_utilization_count']/25:>6.1%}")
    
    print("\nRisk Level Distribution:")
    print("-" * 80)
    for level in ['low', 'medium', 'high', 'critical']:
        syn_count = synthetic_stats['risk_level_distribution'].get(level, 0)
        leg_count = legit_stats['risk_level_distribution'].get(level, 0)
        print(f"  {level.capitalize():8}: Synthetic={syn_count:2}/25 ({syn_count/25:5.1%})  "
              f"Legitimate={leg_count:2}/25 ({leg_count/25:5.1%})")


def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("BUST-OUT DETECTOR EXAMPLES")
    print("=" * 80)
    print("\nDemonstrating bust-out fraud detection capabilities")
    print("Bust-out schemes: Rapid credit building → max out → disappear")
    
    example_1_basic_detection()
    example_2_high_risk_analysis()
    example_3_credit_velocity_analysis()
    example_4_indicator_breakdown()
    example_5_statistics_and_reporting()
    example_6_comparative_analysis()
    
    print("\n" + "=" * 80)
    print("All examples completed successfully!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()

# Made with Bob
