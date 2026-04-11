#!/usr/bin/env python3
"""
Synthetic Identity Pattern Generator Example
============================================

Demonstrates pattern injection capabilities for fraud detection testing.

This example shows how to inject specific fraud patterns into synthetic
identities for testing detection algorithms.

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team
Date: 2026-04-11
Phase: 7.3 - Synthetic Identity Fraud Detection
"""

from banking.identity import (
    SyntheticIdentityPatternGenerator,
    PatternConfig,
    PatternType,
    BustOutDetector,
    IdentityValidator,
)


def example_1_bust_out_pattern():
    """Example 1: Inject bust-out scheme pattern."""
    print("\n" + "=" * 80)
    print("Example 1: Bust-Out Scheme Pattern Injection")
    print("=" * 80)
    
    gen = SyntheticIdentityPatternGenerator(seed=42)
    config = PatternConfig(
        pattern_type=PatternType.BUST_OUT,
        intensity=0.8,
        count=5,
        velocity_multiplier=2.5,
        utilization_target=0.95
    )
    
    identities = gen.generate_with_pattern(config)
    
    print(f"\nGenerated {len(identities)} identities with bust-out pattern")
    print("\nBust-Out Characteristics:")
    for i, identity in enumerate(identities[:3], 1):
        velocity = identity["total_credit_limit"] / identity["credit_file_age_months"]
        print(f"\n{i}. Identity: {identity['identity_id']}")
        print(f"   Pattern: {identity['pattern_injected']} (intensity: {identity['pattern_intensity']})")
        print(f"   Credit File Age: {identity['credit_file_age_months']} months")
        print(f"   Credit Limit: ${identity['total_credit_limit']:,.0f}")
        print(f"   Credit Velocity: ${velocity:,.0f}/month")
        print(f"   Utilization: {identity['credit_utilization']:.0%}")
        print(f"   Accounts: {identity['num_credit_accounts']}")


def example_2_fraud_ring_pattern():
    """Example 2: Inject fraud ring pattern."""
    print("\n" + "=" * 80)
    print("Example 2: Fraud Ring Pattern Injection")
    print("=" * 80)
    
    gen = SyntheticIdentityPatternGenerator(seed=42)
    shared_ssn = "123-45-6789"
    config = PatternConfig(
        pattern_type=PatternType.FRAUD_RING,
        intensity=1.0,
        count=5,
        ring_size=5,
        shared_ssn=shared_ssn
    )
    
    identities = gen.generate_with_pattern(config)
    
    print(f"\nGenerated {len(identities)} identities in fraud ring")
    print(f"Shared SSN: {shared_ssn}")
    print("\nRing Members:")
    for i, identity in enumerate(identities, 1):
        print(f"\n{i}. Identity: {identity['identity_id']}")
        print(f"   Ring ID: {identity['ring_id']}")
        print(f"   SSN: {identity['ssn']}")
        print(f"   Phone: {identity['phone']}")
        print(f"   Shared Attributes: {', '.join(identity['shared_attributes'])}")


def example_3_identity_theft_pattern():
    """Example 3: Inject identity theft pattern."""
    print("\n" + "=" * 80)
    print("Example 3: Identity Theft Pattern Injection")
    print("=" * 80)
    
    gen = SyntheticIdentityPatternGenerator(seed=42)
    config = PatternConfig(
        pattern_type=PatternType.IDENTITY_THEFT,
        intensity=0.9,
        count=3
    )
    
    identities = gen.generate_with_pattern(config)
    
    print(f"\nGenerated {len(identities)} identities with theft pattern")
    print("\nTheft Characteristics:")
    for i, identity in enumerate(identities, 1):
        print(f"\n{i}. Identity: {identity['identity_id']}")
        print(f"   Type: {identity['identity_type']}")
        print(f"   Stolen SSN: {identity['stolen_ssn']}")
        print(f"   Credit File Age: {identity['credit_file_age_months']} months")
        print(f"   Address Changes: {identity.get('address_changes_last_year', 0)}")
        print(f"   Utilization: {identity['credit_utilization']:.0%}")


def example_4_authorized_user_pattern():
    """Example 4: Inject authorized user abuse pattern."""
    print("\n" + "=" * 80)
    print("Example 4: Authorized User Abuse Pattern Injection")
    print("=" * 80)
    
    gen = SyntheticIdentityPatternGenerator(seed=42)
    config = PatternConfig(
        pattern_type=PatternType.AUTHORIZED_USER_ABUSE,
        intensity=0.8,
        count=3
    )
    
    identities = gen.generate_with_pattern(config)
    
    print(f"\nGenerated {len(identities)} identities with authorized user pattern")
    print("\nPiggybacking Characteristics:")
    for i, identity in enumerate(identities, 1):
        print(f"\n{i}. Identity: {identity['identity_id']}")
        print(f"   Has AU History: {identity['has_authorized_user_history']}")
        print(f"   AU Accounts: {identity['authorized_user_accounts']}")
        print(f"   Credit Score: {identity['credit_score']}")
        print(f"   Credit Tier: {identity['credit_tier']}")
        print(f"   File Age: {identity['credit_file_age_months']} months")
        print(f"   Credit Limit: ${identity['total_credit_limit']:,.0f}")


def example_5_credit_mule_pattern():
    """Example 5: Inject credit mule pattern."""
    print("\n" + "=" * 80)
    print("Example 5: Credit Mule Pattern Injection")
    print("=" * 80)
    
    gen = SyntheticIdentityPatternGenerator(seed=42)
    config = PatternConfig(
        pattern_type=PatternType.CREDIT_MULE,
        intensity=1.0,
        count=3
    )
    
    identities = gen.generate_with_pattern(config)
    
    print(f"\nGenerated {len(identities)} identities with credit mule pattern")
    print("\nMule Characteristics:")
    for i, identity in enumerate(identities, 1):
        print(f"\n{i}. Identity: {identity['identity_id']}")
        print(f"   File Age: {identity['credit_file_age_months']} months")
        print(f"   Total Accounts: {identity['num_credit_accounts']}")
        print(f"   Recent Accounts: {identity['accounts_opened_last_6_months']}")
        print(f"   Failed Applications: {identity['failed_applications_last_year']}")
        print(f"   Utilization: {identity['credit_utilization']:.0%}")
        if identity.get('rapid_account_cycling'):
            print(f"   ⚠️  Rapid account cycling detected")
        if identity.get('suspicious_transaction_patterns'):
            print(f"   ⚠️  Suspicious transaction patterns detected")


def example_6_mixed_batch():
    """Example 6: Generate mixed batch with multiple patterns."""
    print("\n" + "=" * 80)
    print("Example 6: Mixed Batch Generation")
    print("=" * 80)
    
    gen = SyntheticIdentityPatternGenerator(seed=42)
    identities = gen.generate_mixed_batch(
        total_count=100,
        pattern_distribution={
            PatternType.BUST_OUT: 0.20,
            PatternType.FRAUD_RING: 0.15,
            PatternType.IDENTITY_THEFT: 0.10,
            PatternType.AUTHORIZED_USER_ABUSE: 0.10,
            PatternType.CREDIT_MULE: 0.05,
        },
        base_intensity=0.7
    )
    
    print(f"\nGenerated {len(identities)} identities with mixed patterns")
    
    # Count patterns
    pattern_counts = {}
    for identity in identities:
        pattern = identity.get("pattern_injected", "unknown")
        pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
    
    print("\nPattern Distribution:")
    print("-" * 80)
    for pattern, count in sorted(pattern_counts.items()):
        pct = count / len(identities) * 100
        bar = "█" * int(pct / 2)
        print(f"  {pattern:25}: {count:3} ({pct:5.1f}%) {bar}")
    
    # Get summary
    summary = gen.get_pattern_summary()
    print(f"\nPattern Summary:")
    print(f"  Total Patterns Injected: {summary['total_patterns']}")
    print(f"  Total Identities: {summary['total_identities']}")


def example_7_detection_validation():
    """Example 7: Validate pattern detection."""
    print("\n" + "=" * 80)
    print("Example 7: Pattern Detection Validation")
    print("=" * 80)
    
    # Generate identities with bust-out pattern
    gen = SyntheticIdentityPatternGenerator(seed=42)
    config = PatternConfig(
        pattern_type=PatternType.BUST_OUT,
        intensity=0.9,
        count=10
    )
    identities = gen.generate_with_pattern(config)
    
    # Detect bust-out schemes
    detector = BustOutDetector()
    results = detector.detect_batch(identities)
    
    # Analyze detection accuracy
    detected_count = sum(1 for r in results if r.is_bust_out)
    detection_rate = detected_count / len(results) * 100
    
    print(f"\nGenerated {len(identities)} identities with bust-out pattern")
    print(f"Detected {detected_count} bust-out schemes")
    print(f"Detection Rate: {detection_rate:.1f}%")
    
    print("\nDetection Results:")
    print("-" * 80)
    for i, (identity, result) in enumerate(zip(identities[:5], results[:5]), 1):
        print(f"\n{i}. Identity: {identity['identity_id']}")
        print(f"   Injected Pattern: {identity['pattern_injected']}")
        print(f"   Detected as Bust-Out: {result.is_bust_out}")
        print(f"   Bust-Out Score: {result.bust_out_score}/100")
        print(f"   Risk Level: {result.risk_level}")
        print(f"   Indicators: {len(result.indicators)}")


def example_8_fraud_ring_validation():
    """Example 8: Validate fraud ring detection."""
    print("\n" + "=" * 80)
    print("Example 8: Fraud Ring Detection Validation")
    print("=" * 80)
    
    # Generate fraud ring
    gen = SyntheticIdentityPatternGenerator(seed=42)
    config = PatternConfig(
        pattern_type=PatternType.FRAUD_RING,
        intensity=1.0,
        count=5,
        ring_size=5
    )
    identities = gen.generate_with_pattern(config)
    
    # Validate identities
    validator = IdentityValidator()
    for identity in identities:
        validator.add_identity(identity)
    
    # Check for shared attributes
    print(f"\nGenerated {len(identities)} identities in fraud ring")
    print("\nShared Attribute Detection:")
    print("-" * 80)
    
    for identity in identities:
        result = validator.validate(identity["identity_id"])
        print(f"\nIdentity: {identity['identity_id']}")
        print(f"  Authenticity Score: {result.authenticity_score}/100")
        print(f"  Risk Score: {result.risk_score}/100")
        print(f"  Shared Attributes: {', '.join(result.shared_attributes) if result.shared_attributes else 'None'}")
        print(f"  Fraud Indicators: {len(result.fraud_indicators)}")
        if result.recommendations:
            print(f"  Recommendations:")
            for rec in result.recommendations[:2]:
                print(f"    - {rec}")


def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("SYNTHETIC IDENTITY PATTERN GENERATOR EXAMPLES")
    print("=" * 80)
    print("\nDemonstrating fraud pattern injection for testing detection algorithms")
    
    example_1_bust_out_pattern()
    example_2_fraud_ring_pattern()
    example_3_identity_theft_pattern()
    example_4_authorized_user_pattern()
    example_5_credit_mule_pattern()
    example_6_mixed_batch()
    example_7_detection_validation()
    example_8_fraud_ring_validation()
    
    print("\n" + "=" * 80)
    print("All examples completed successfully!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()

# Made with Bob
