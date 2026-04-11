"""
Synthetic Identity Generator Example
=====================================

Demonstrates how to use the SyntheticIdentityGenerator to create
synthetic identities for fraud detection testing.

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team
Date: 2026-04-11
Phase: 7.2 - Synthetic Identity Fraud Detection
"""

from banking.identity import SyntheticIdentityGenerator, IdentityType, CreditTier


def main():
    """Run synthetic identity generation examples."""
    
    print("=" * 80)
    print("Synthetic Identity Generator - Examples")
    print("=" * 80)
    print()
    
    # Example 1: Basic generation
    print("Example 1: Basic Identity Generation")
    print("-" * 80)
    gen = SyntheticIdentityGenerator(seed=42)
    identity = gen.generate()
    
    print(f"Identity ID: {identity['identity_id']}")
    print(f"Type: {identity['identity_type']}")
    print(f"Is Synthetic: {identity['is_synthetic']}")
    print(f"Name: {identity['first_name']} {identity['last_name']}")
    print(f"SSN: {identity['ssn']}")
    print(f"Credit Score: {identity['credit_score']} ({identity['credit_tier']})")
    print(f"Bust-Out Risk: {identity['bust_out_risk_score']}/100")
    print(f"Risk Indicators: {', '.join(identity['risk_indicators']) if identity['risk_indicators'] else 'None'}")
    print()
    
    # Example 2: Generate batch with high synthetic probability
    print("Example 2: Batch Generation (High Synthetic Probability)")
    print("-" * 80)
    config = {
        "synthetic_probability": 0.80,  # 80% synthetic
        "shared_ssn_probability": 0.50,
        "bust_out_probability": 0.30,
    }
    gen = SyntheticIdentityGenerator(seed=42, config=config)
    identities = gen.generate_batch(20)
    
    # Analyze the batch
    synthetic_count = sum(1 for i in identities if i["is_synthetic"])
    frankenstein_count = sum(1 for i in identities if i["identity_type"] == IdentityType.FRANKENSTEIN.value)
    shared_ssn_count = sum(1 for i in identities if "ssn" in i["shared_attributes"])
    high_risk_count = sum(1 for i in identities if i["bust_out_risk_score"] >= 70)
    
    print(f"Total Identities: {len(identities)}")
    print(f"Synthetic: {synthetic_count} ({synthetic_count/len(identities)*100:.1f}%)")
    print(f"Frankenstein Type: {frankenstein_count}")
    print(f"Shared SSN: {shared_ssn_count}")
    print(f"High Bust-Out Risk (≥70): {high_risk_count}")
    print()
    
    # Show shared attribute stats
    stats = gen.get_shared_attribute_stats()
    print("Shared Attribute Pools:")
    print(f"  - Shared SSNs: {stats['shared_ssns']}")
    print(f"  - Shared Phones: {stats['shared_phones']}")
    print(f"  - Shared Addresses: {stats['shared_addresses']}")
    print(f"  - Shared Emails: {stats['shared_emails']}")
    print()
    
    # Example 3: Detect fraud patterns
    print("Example 3: Fraud Pattern Detection")
    print("-" * 80)
    
    # Find identities with multiple shared attributes
    multi_shared = [i for i in identities if len(i["shared_attributes"]) >= 2]
    print(f"Identities with 2+ shared attributes: {len(multi_shared)}")
    
    if multi_shared:
        example = multi_shared[0]
        print(f"\nExample High-Risk Identity:")
        print(f"  ID: {example['identity_id']}")
        print(f"  Name: {example['first_name']} {example['last_name']}")
        print(f"  Shared: {', '.join(example['shared_attributes'])}")
        print(f"  Credit Utilization: {example['credit_utilization']*100:.1f}%")
        print(f"  Bust-Out Risk: {example['bust_out_risk_score']}/100")
        print(f"  Risk Indicators:")
        for indicator in example['risk_indicators']:
            print(f"    - {indicator}")
    print()
    
    # Example 4: Credit profile analysis
    print("Example 4: Credit Profile Analysis")
    print("-" * 80)
    
    # Analyze credit tiers
    tier_counts = {}
    for identity in identities:
        tier = identity["credit_tier"]
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
    
    print("Credit Tier Distribution:")
    for tier in CreditTier:
        count = tier_counts.get(tier.value, 0)
        pct = count / len(identities) * 100
        print(f"  {tier.value.capitalize():12} {count:2} ({pct:5.1f}%)")
    print()
    
    # Analyze credit file age
    avg_age = sum(i["credit_file_age_months"] for i in identities) / len(identities)
    recent_files = sum(1 for i in identities if i["credit_file_age_months"] < 12)
    
    print(f"Average Credit File Age: {avg_age:.1f} months")
    print(f"Recent Files (<12 months): {recent_files} ({recent_files/len(identities)*100:.1f}%)")
    print()
    
    # Example 5: Bust-out scheme detection
    print("Example 5: Bust-Out Scheme Detection")
    print("-" * 80)
    
    # Find potential bust-out schemes
    bust_out_candidates = [
        i for i in identities
        if i["bust_out_risk_score"] >= 70
        and i["credit_utilization"] > 0.80
        and i["credit_file_age_months"] < 24
    ]
    
    print(f"Potential Bust-Out Schemes: {len(bust_out_candidates)}")
    
    if bust_out_candidates:
        print("\nTop Bust-Out Risk Identities:")
        sorted_candidates = sorted(bust_out_candidates, key=lambda x: x["bust_out_risk_score"], reverse=True)
        for i, identity in enumerate(sorted_candidates[:3], 1):
            print(f"\n{i}. {identity['first_name']} {identity['last_name']}")
            print(f"   Risk Score: {identity['bust_out_risk_score']}/100")
            print(f"   Credit Utilization: {identity['credit_utilization']*100:.1f}%")
            print(f"   Credit File Age: {identity['credit_file_age_months']} months")
            print(f"   Total Credit Limit: ${identity['total_credit_limit']:,.2f}")
            print(f"   Shared Attributes: {', '.join(identity['shared_attributes']) if identity['shared_attributes'] else 'None'}")
    print()
    
    # Example 6: Deterministic verification
    print("Example 6: Deterministic Verification")
    print("-" * 80)
    
    # Generate with same seed
    gen1 = SyntheticIdentityGenerator(seed=999)
    identities1 = gen1.generate_batch(5)
    
    gen2 = SyntheticIdentityGenerator(seed=999)
    identities2 = gen2.generate_batch(5)
    
    # Verify identical output
    all_match = all(
        i1["identity_id"] == i2["identity_id"]
        and i1["ssn"] == i2["ssn"]
        and i1["credit_score"] == i2["credit_score"]
        for i1, i2 in zip(identities1, identities2)
    )
    
    print(f"Same seed produces identical output: {all_match}")
    print(f"First identity ID (both runs): {identities1[0]['identity_id']}")
    print(f"First SSN (both runs): {identities1[0]['ssn']}")
    print()
    
    print("=" * 80)
    print("Examples Complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()

# Made with Bob
