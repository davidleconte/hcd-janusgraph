"""
Identity Validator Example
===========================

Demonstrates how to use the IdentityValidator to detect synthetic identity
fraud through cross-validation and shared attribute analysis.

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team
Date: 2026-04-11
Phase: 7.2 - Synthetic Identity Fraud Detection
"""

from banking.identity import SyntheticIdentityGenerator, IdentityValidator


def main():
    """Run identity validation examples."""
    
    print("=" * 80)
    print("Identity Validator - Fraud Detection Examples")
    print("=" * 80)
    print()
    
    # Example 1: Basic validation
    print("Example 1: Basic Identity Validation")
    print("-" * 80)
    
    # Generate identities with high synthetic probability
    gen = SyntheticIdentityGenerator(seed=42, config={
        "synthetic_probability": 0.50,
        "shared_ssn_probability": 0.40,
    })
    identities = gen.generate_batch(30)
    
    # Create validator and add identities
    validator = IdentityValidator()
    validator.add_identities(identities)
    
    # Validate all identities
    results = validator.validate_all()
    
    print(f"Total Identities Validated: {len(results)}")
    authentic_count = sum(1 for r in results if r.is_authentic)
    synthetic_count = len(results) - authentic_count
    print(f"Authentic: {authentic_count} ({authentic_count/len(results)*100:.1f}%)")
    print(f"Synthetic/Suspicious: {synthetic_count} ({synthetic_count/len(results)*100:.1f}%)")
    print()
    
    # Example 2: Shared attribute detection
    print("Example 2: Shared Attribute Detection")
    print("-" * 80)
    
    clusters = validator.get_shared_attribute_clusters()
    print(f"Shared Attribute Clusters Found: {len(clusters)}")
    print()
    
    # Show top 3 clusters
    for i, cluster in enumerate(clusters[:3], 1):
        print(f"{i}. {cluster.attribute_type.upper()} Cluster")
        print(f"   Identities Sharing: {len(cluster.identity_ids)}")
        print(f"   Risk Score: {cluster.risk_score}/100")
        print(f"   Identity IDs: {', '.join(cluster.identity_ids[:3])}...")
        print()
    
    # Example 3: High-risk identity analysis
    print("Example 3: High-Risk Identity Analysis")
    print("-" * 80)
    
    high_risk = validator.get_high_risk_identities(min_risk_score=70)
    print(f"High-Risk Identities (≥70): {len(high_risk)}")
    print()
    
    if high_risk:
        print("Top 3 High-Risk Identities:")
        for i, result in enumerate(high_risk[:3], 1):
            identity = validator._identities[result.identity_id]
            print(f"\n{i}. Identity: {identity['first_name']} {identity['last_name']}")
            print(f"   ID: {result.identity_id}")
            print(f"   Authenticity Score: {result.authenticity_score}/100")
            print(f"   Risk Score: {result.risk_score}/100")
            print(f"   Shared Attributes: {', '.join(result.shared_attributes) if result.shared_attributes else 'None'}")
            print(f"   Fraud Indicators:")
            for indicator in result.fraud_indicators[:3]:
                print(f"     - {indicator}")
            print(f"   Recommendations:")
            for rec in result.recommendations[:2]:
                print(f"     - {rec}")
    print()
    
    # Example 4: Validation statistics
    print("Example 4: Validation Statistics")
    print("-" * 80)
    
    stats = validator.get_statistics()
    print(f"Total Identities: {stats['total_identities']}")
    print(f"Authentic: {stats['authentic_count']}")
    print(f"Synthetic: {stats['synthetic_count']}")
    print(f"High Risk: {stats['high_risk_count']}")
    print(f"Authenticity Rate: {stats['authenticity_rate']*100:.1f}%")
    print()
    print("Shared Attribute Clusters:")
    print(f"  - SSN Clusters: {stats['shared_ssn_clusters']}")
    print(f"  - Phone Clusters: {stats['shared_phone_clusters']}")
    print(f"  - Address Clusters: {stats['shared_address_clusters']}")
    print()
    
    # Example 5: Individual identity validation
    print("Example 5: Individual Identity Validation")
    print("-" * 80)
    
    # Pick a suspicious identity
    suspicious = [r for r in results if not r.is_authentic]
    if suspicious:
        result = suspicious[0]
        identity = validator._identities[result.identity_id]
        
        print(f"Identity: {identity['first_name']} {identity['last_name']}")
        print(f"SSN: {identity['ssn']}")
        print(f"Credit Score: {identity['credit_score']} ({identity['credit_tier']})")
        print(f"Credit File Age: {identity['credit_file_age_months']} months")
        print(f"Credit Utilization: {identity['credit_utilization']*100:.1f}%")
        print()
        print(f"Validation Result:")
        print(f"  Is Authentic: {result.is_authentic}")
        print(f"  Authenticity Score: {result.authenticity_score}/100")
        print(f"  Risk Score: {result.risk_score}/100")
        print()
        print(f"Shared Attributes: {', '.join(result.shared_attributes) if result.shared_attributes else 'None'}")
        print()
        print(f"Fraud Indicators:")
        for indicator in result.fraud_indicators:
            print(f"  - {indicator}")
        print()
        print(f"Recommendations:")
        for rec in result.recommendations:
            print(f"  - {rec}")
    print()
    
    # Example 6: Fraud ring detection
    print("Example 6: Fraud Ring Detection (Shared SSN)")
    print("-" * 80)
    
    # Find SSN clusters (potential fraud rings)
    ssn_clusters = [c for c in clusters if c.attribute_type == "ssn"]
    
    if ssn_clusters:
        print(f"Potential Fraud Rings: {len(ssn_clusters)}")
        print()
        
        # Analyze largest fraud ring
        largest_ring = max(ssn_clusters, key=lambda c: len(c.identity_ids))
        print(f"Largest Fraud Ring:")
        print(f"  Shared SSN: {largest_ring.attribute_value}")
        print(f"  Number of Identities: {len(largest_ring.identity_ids)}")
        print(f"  Risk Score: {largest_ring.risk_score}/100")
        print()
        print(f"  Identities in Ring:")
        for identity_id in largest_ring.identity_ids[:5]:
            identity = validator._identities[identity_id]
            result = validator.validate(identity_id)
            print(f"    - {identity['first_name']} {identity['last_name']}")
            print(f"      Risk: {result.risk_score}/100, Auth: {result.authenticity_score}/100")
    print()
    
    # Example 7: Comparison of legitimate vs synthetic
    print("Example 7: Legitimate vs Synthetic Comparison")
    print("-" * 80)
    
    legitimate_results = [r for r in results if r.is_authentic]
    synthetic_results = [r for r in results if not r.is_authentic]
    
    if legitimate_results and synthetic_results:
        avg_auth_legit = sum(r.authenticity_score for r in legitimate_results) / len(legitimate_results)
        avg_auth_synth = sum(r.authenticity_score for r in synthetic_results) / len(synthetic_results)
        avg_risk_legit = sum(r.risk_score for r in legitimate_results) / len(legitimate_results)
        avg_risk_synth = sum(r.risk_score for r in synthetic_results) / len(synthetic_results)
        
        print("Legitimate Identities:")
        print(f"  Count: {len(legitimate_results)}")
        print(f"  Avg Authenticity Score: {avg_auth_legit:.1f}/100")
        print(f"  Avg Risk Score: {avg_risk_legit:.1f}/100")
        print()
        print("Synthetic/Suspicious Identities:")
        print(f"  Count: {len(synthetic_results)}")
        print(f"  Avg Authenticity Score: {avg_auth_synth:.1f}/100")
        print(f"  Avg Risk Score: {avg_risk_synth:.1f}/100")
        print()
        print(f"Authenticity Score Difference: {avg_auth_legit - avg_auth_synth:.1f} points")
        print(f"Risk Score Difference: {avg_risk_synth - avg_risk_legit:.1f} points")
    print()
    
    print("=" * 80)
    print("Examples Complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()

# Made with Bob
