"""
Tests for SyntheticIdentityGenerator
=====================================

Comprehensive test suite for synthetic identity generation.

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team
Date: 2026-04-11
Phase: 7.2 - Synthetic Identity Fraud Detection
"""

import pytest
from decimal import Decimal

from banking.identity import (
    SyntheticIdentityGenerator,
    IdentityType,
    CreditTier,
)


class TestSyntheticIdentityGeneratorBasic:
    """Basic functionality tests."""
    
    def test_initialization(self):
        """Test generator initialization."""
        gen = SyntheticIdentityGenerator(seed=42)
        assert gen.seed == 42
        assert gen.synthetic_probability == 0.10
        assert gen.shared_ssn_probability == 0.30
    
    def test_initialization_with_config(self):
        """Test generator initialization with custom config."""
        config = {
            "synthetic_probability": 0.50,
            "shared_ssn_probability": 0.40,
            "bust_out_probability": 0.20,
        }
        gen = SyntheticIdentityGenerator(seed=42, config=config)
        assert gen.synthetic_probability == 0.50
        assert gen.shared_ssn_probability == 0.40
        assert gen.bust_out_probability == 0.20
    
    def test_generate_single_identity(self):
        """Test generating a single identity."""
        gen = SyntheticIdentityGenerator(seed=42)
        identity = gen.generate()
        
        # Check required fields
        assert "identity_id" in identity
        assert "identity_type" in identity
        assert "is_synthetic" in identity
        assert "ssn" in identity
        assert "first_name" in identity
        assert "last_name" in identity
        assert "date_of_birth" in identity
        assert "phone" in identity
        assert "email" in identity
        assert "address" in identity
        assert "credit_score" in identity
        assert "created_at" in identity
    
    def test_generate_batch(self):
        """Test batch generation."""
        gen = SyntheticIdentityGenerator(seed=42)
        identities = gen.generate_batch(10)
        
        assert len(identities) == 10
        assert all("identity_id" in i for i in identities)
        
        # Check unique IDs
        ids = [i["identity_id"] for i in identities]
        assert len(ids) == len(set(ids))


class TestDeterminism:
    """Determinism tests - CRITICAL for reproducibility."""
    
    def test_deterministic_generation(self):
        """Test that same seed produces identical output."""
        seed = 42
        
        gen1 = SyntheticIdentityGenerator(seed=seed)
        identities1 = gen1.generate_batch(20)
        
        gen2 = SyntheticIdentityGenerator(seed=seed)
        identities2 = gen2.generate_batch(20)
        
        # Compare all identities
        for i1, i2 in zip(identities1, identities2):
            assert i1["identity_id"] == i2["identity_id"]
            assert i1["ssn"] == i2["ssn"]
            assert i1["first_name"] == i2["first_name"]
            assert i1["last_name"] == i2["last_name"]
            assert i1["credit_score"] == i2["credit_score"]
            assert i1["is_synthetic"] == i2["is_synthetic"]
    
    def test_different_seeds_produce_different_output(self):
        """Test that different seeds produce different output."""
        gen1 = SyntheticIdentityGenerator(seed=42)
        identity1 = gen1.generate()
        
        gen2 = SyntheticIdentityGenerator(seed=123)
        identity2 = gen2.generate()
        
        # Should be different
        assert identity1["identity_id"] != identity2["identity_id"]
        assert identity1["ssn"] != identity2["ssn"]
    
    def test_no_datetime_now_usage(self):
        """Test that REFERENCE_TIMESTAMP is used, not datetime.now()."""
        gen = SyntheticIdentityGenerator(seed=42)
        identity1 = gen.generate()
        identity2 = gen.generate()
        
        # Both should use REFERENCE_TIMESTAMP
        assert identity1["created_at"] == identity2["created_at"]


class TestIdentityTypes:
    """Test different identity types."""
    
    def test_identity_type_values(self):
        """Test that identity types are valid."""
        gen = SyntheticIdentityGenerator(seed=42, config={"synthetic_probability": 1.0})
        identities = gen.generate_batch(50)
        
        valid_types = [t.value for t in IdentityType]
        for identity in identities:
            assert identity["identity_type"] in valid_types
    
    def test_synthetic_flag_consistency(self):
        """Test that is_synthetic flag matches identity type."""
        gen = SyntheticIdentityGenerator(seed=42)
        identities = gen.generate_batch(100)
        
        for identity in identities:
            if identity["identity_type"] == IdentityType.LEGITIMATE.value:
                assert identity["is_synthetic"] is False
            else:
                assert identity["is_synthetic"] is True
    
    def test_frankenstein_most_common(self):
        """Test that Frankenstein is most common synthetic type."""
        gen = SyntheticIdentityGenerator(seed=42, config={"synthetic_probability": 1.0})
        identities = gen.generate_batch(100)
        
        type_counts = {}
        for identity in identities:
            itype = identity["identity_type"]
            type_counts[itype] = type_counts.get(itype, 0) + 1
        
        # Frankenstein should be most common (80% weight)
        assert type_counts.get(IdentityType.FRANKENSTEIN.value, 0) > 50


class TestSSNGeneration:
    """Test SSN generation and sharing."""
    
    def test_ssn_format(self):
        """Test SSN format is correct."""
        gen = SyntheticIdentityGenerator(seed=42)
        identity = gen.generate()
        
        ssn = identity["ssn"]
        assert ssn.startswith("987-65-")
        assert len(ssn) == 11  # XXX-XX-XXXX
    
    def test_shared_ssn_detection(self):
        """Test that shared SSNs are detected."""
        gen = SyntheticIdentityGenerator(seed=42, config={
            "synthetic_probability": 1.0,
            "shared_ssn_probability": 0.80,
        })
        identities = gen.generate_batch(20)
        
        # Count identities with shared SSN
        shared_count = sum(1 for i in identities if "ssn" in i["shared_attributes"])
        assert shared_count > 5  # Should have multiple shared SSNs
    
    def test_shared_ssn_stats(self):
        """Test shared attribute statistics."""
        gen = SyntheticIdentityGenerator(seed=42, config={
            "synthetic_probability": 1.0,
            "shared_ssn_probability": 0.50,
        })
        gen.generate_batch(30)
        
        stats = gen.get_shared_attribute_stats()
        assert stats["shared_ssns"] > 0


class TestCreditProfile:
    """Test credit profile generation."""
    
    def test_credit_score_range(self):
        """Test credit scores are in valid range."""
        gen = SyntheticIdentityGenerator(seed=42)
        identities = gen.generate_batch(50)
        
        for identity in identities:
            score = identity["credit_score"]
            assert 300 <= score <= 850
    
    def test_credit_tier_consistency(self):
        """Test credit tier matches score."""
        gen = SyntheticIdentityGenerator(seed=42)
        identities = gen.generate_batch(50)
        
        for identity in identities:
            score = identity["credit_score"]
            tier = identity["credit_tier"]
            
            if score >= 750:
                assert tier == CreditTier.EXCELLENT.value
            elif score >= 700:
                assert tier == CreditTier.GOOD.value
            elif score >= 650:
                assert tier == CreditTier.FAIR.value
            elif score >= 600:
                assert tier == CreditTier.POOR.value
            else:
                assert tier == CreditTier.BAD.value
    
    def test_credit_utilization_range(self):
        """Test credit utilization is in valid range."""
        gen = SyntheticIdentityGenerator(seed=42)
        identities = gen.generate_batch(50)
        
        for identity in identities:
            utilization = identity["credit_utilization"]
            assert 0.0 <= utilization <= 1.0
    
    def test_synthetic_credit_patterns(self):
        """Test synthetic identities have expected credit patterns."""
        gen = SyntheticIdentityGenerator(seed=42, config={"synthetic_probability": 1.0})
        identities = gen.generate_batch(50)
        
        # Synthetics should have newer credit files
        avg_age = sum(i["credit_file_age_months"] for i in identities) / len(identities)
        assert avg_age < 48  # Less than 4 years on average
        
        # Some should have authorized user history
        au_count = sum(1 for i in identities if i["has_authorized_user_history"])
        assert au_count > 10  # At least 20%


class TestSharedAttributes:
    """Test shared attribute detection."""
    
    def test_shared_phone_detection(self):
        """Test shared phone detection."""
        gen = SyntheticIdentityGenerator(seed=42, config={
            "synthetic_probability": 1.0,
            "shared_phone_probability": 0.70,
        })
        identities = gen.generate_batch(20)
        
        shared_count = sum(1 for i in identities if "phone" in i["shared_attributes"])
        assert shared_count > 5
    
    def test_shared_address_detection(self):
        """Test shared address detection."""
        gen = SyntheticIdentityGenerator(seed=42, config={
            "synthetic_probability": 1.0,
            "shared_address_probability": 0.60,
        })
        identities = gen.generate_batch(20)
        
        shared_count = sum(1 for i in identities if "address" in i["shared_attributes"])
        assert shared_count > 3
    
    def test_multiple_shared_attributes(self):
        """Test identities can have multiple shared attributes."""
        gen = SyntheticIdentityGenerator(seed=42, config={
            "synthetic_probability": 1.0,
            "shared_ssn_probability": 0.80,
            "shared_phone_probability": 0.80,
            "shared_address_probability": 0.80,
        })
        identities = gen.generate_batch(30)
        
        # Some should have multiple shared attributes
        multi_shared = [i for i in identities if len(i["shared_attributes"]) >= 2]
        assert len(multi_shared) > 5


class TestBustOutRisk:
    """Test bust-out risk scoring."""
    
    def test_bust_out_risk_range(self):
        """Test bust-out risk is in valid range."""
        gen = SyntheticIdentityGenerator(seed=42)
        identities = gen.generate_batch(50)
        
        for identity in identities:
            risk = identity["bust_out_risk_score"]
            assert 0 <= risk <= 100
    
    def test_legitimate_identities_low_risk(self):
        """Test legitimate identities have low bust-out risk."""
        gen = SyntheticIdentityGenerator(seed=42, config={"synthetic_probability": 0.0})
        identities = gen.generate_batch(20)
        
        for identity in identities:
            assert identity["bust_out_risk_score"] == 0
    
    def test_high_utilization_increases_risk(self):
        """Test high credit utilization increases bust-out risk."""
        gen = SyntheticIdentityGenerator(seed=42, config={
            "synthetic_probability": 1.0,
            "bust_out_probability": 0.80,
        })
        identities = gen.generate_batch(50)
        
        # High utilization identities should have higher risk
        high_util = [i for i in identities if i["credit_utilization"] > 0.80]
        if high_util:
            avg_risk = sum(i["bust_out_risk_score"] for i in high_util) / len(high_util)
            assert avg_risk > 40


class TestRiskIndicators:
    """Test risk indicator identification."""
    
    def test_risk_indicators_present(self):
        """Test risk indicators are identified."""
        gen = SyntheticIdentityGenerator(seed=42, config={"synthetic_probability": 1.0})
        identities = gen.generate_batch(50)
        
        # All synthetics should have at least one risk indicator
        for identity in identities:
            if identity["is_synthetic"]:
                assert len(identity["risk_indicators"]) > 0
    
    def test_synthetic_identity_indicator(self):
        """Test synthetic identity type is flagged."""
        gen = SyntheticIdentityGenerator(seed=42, config={"synthetic_probability": 1.0})
        identities = gen.generate_batch(20)
        
        for identity in identities:
            indicators = identity["risk_indicators"]
            # Should have synthetic_identity_* indicator
            assert any("synthetic_identity_" in ind for ind in indicators)
    
    def test_shared_attributes_indicator(self):
        """Test shared attributes are flagged."""
        gen = SyntheticIdentityGenerator(seed=42, config={
            "synthetic_probability": 1.0,
            "shared_ssn_probability": 0.80,
        })
        identities = gen.generate_batch(30)
        
        # Some should have shared_attributes indicator
        shared_indicators = [i for i in identities 
                           if any("shared_attributes_" in ind for ind in i["risk_indicators"])]
        assert len(shared_indicators) > 10
    
    def test_high_bust_out_risk_indicator(self):
        """Test high bust-out risk is flagged."""
        gen = SyntheticIdentityGenerator(seed=42, config={
            "synthetic_probability": 1.0,
            "bust_out_probability": 0.80,
        })
        identities = gen.generate_batch(50)
        
        # Some should have bust-out risk indicator
        bust_out_indicators = [i for i in identities 
                             if any("bust_out_risk" in ind for ind in i["risk_indicators"])]
        assert len(bust_out_indicators) > 10


class TestAddressGeneration:
    """Test address generation."""
    
    def test_address_structure(self):
        """Test address has required fields."""
        gen = SyntheticIdentityGenerator(seed=42)
        identity = gen.generate()
        
        address = identity["address"]
        assert "street" in address
        assert "city" in address
        assert "state" in address
        assert "zip_code" in address
    
    def test_address_values_not_empty(self):
        """Test address fields are not empty."""
        gen = SyntheticIdentityGenerator(seed=42)
        identity = gen.generate()
        
        address = identity["address"]
        assert len(address["street"]) > 0
        assert len(address["city"]) > 0
        assert len(address["state"]) > 0
        assert len(address["zip_code"]) > 0


class TestStatistics:
    """Test generator statistics."""
    
    def test_get_statistics(self):
        """Test statistics retrieval."""
        gen = SyntheticIdentityGenerator(seed=42)
        gen.generate_batch(10)
        
        stats = gen.get_statistics()
        assert stats["generated_count"] == 10
        assert stats["seed"] == 42
    
    def test_shared_attribute_stats(self):
        """Test shared attribute statistics."""
        gen = SyntheticIdentityGenerator(seed=42, config={
            "synthetic_probability": 1.0,
            "shared_ssn_probability": 0.50,
            "shared_phone_probability": 0.50,
        })
        gen.generate_batch(30)
        
        stats = gen.get_shared_attribute_stats()
        assert "shared_ssns" in stats
        assert "shared_phones" in stats
        assert "shared_addresses" in stats
        assert "shared_emails" in stats


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_zero_synthetic_probability(self):
        """Test with zero synthetic probability."""
        gen = SyntheticIdentityGenerator(seed=42, config={"synthetic_probability": 0.0})
        identities = gen.generate_batch(20)
        
        # All should be legitimate
        assert all(not i["is_synthetic"] for i in identities)
        assert all(i["identity_type"] == IdentityType.LEGITIMATE.value for i in identities)
    
    def test_full_synthetic_probability(self):
        """Test with 100% synthetic probability."""
        gen = SyntheticIdentityGenerator(seed=42, config={"synthetic_probability": 1.0})
        identities = gen.generate_batch(20)
        
        # All should be synthetic
        assert all(i["is_synthetic"] for i in identities)
        assert all(i["identity_type"] != IdentityType.LEGITIMATE.value for i in identities)
    
    def test_single_identity_generation(self):
        """Test generating just one identity."""
        gen = SyntheticIdentityGenerator(seed=42)
        identity = gen.generate()
        
        assert identity is not None
        assert "identity_id" in identity


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob
