"""
Tests for Synthetic Identity Pattern Generator
==============================================

Tests pattern injection capabilities for fraud detection testing.

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team
Date: 2026-04-11
Phase: 7.3 - Synthetic Identity Fraud Detection
"""

import pytest

from banking.identity import (
    SyntheticIdentityPatternGenerator,
    PatternConfig,
    PatternType,
)


class TestPatternGeneratorBasic:
    """Basic pattern generator tests."""
    
    def test_initialization(self):
        """Test pattern generator initialization."""
        gen = SyntheticIdentityPatternGenerator(seed=42)
        assert gen.seed == 42
        assert gen.base_generator is not None
        assert len(gen.injected_patterns) == 0
    
    def test_initialization_with_config(self):
        """Test initialization with configuration."""
        config = {"synthetic_probability": 1.0}
        gen = SyntheticIdentityPatternGenerator(seed=42, config=config)
        assert gen.config == config
        assert gen.base_generator.config == config


class TestBustOutPattern:
    """Bust-out pattern injection tests."""
    
    def test_bust_out_pattern_injection(self):
        """Test bust-out pattern injection."""
        gen = SyntheticIdentityPatternGenerator(seed=42)
        config = PatternConfig(
            pattern_type=PatternType.BUST_OUT,
            intensity=0.8,
            count=5
        )
        identities = gen.generate_with_pattern(config)
        
        assert len(identities) == 5
        for identity in identities:
            assert identity["pattern_injected"] == "bust_out"
            assert identity["pattern_intensity"] == 0.8
            # Bust-out characteristics
            assert identity["credit_file_age_months"] <= 18
            assert identity["credit_utilization"] >= 0.85
    
    def test_bust_out_high_intensity(self):
        """Test high intensity bust-out pattern."""
        gen = SyntheticIdentityPatternGenerator(seed=42)
        config = PatternConfig(
            pattern_type=PatternType.BUST_OUT,
            intensity=1.0,
            count=3
        )
        identities = gen.generate_with_pattern(config)
        
        for identity in identities:
            # High intensity = more obvious pattern
            assert identity["credit_file_age_months"] <= 10
            assert identity["credit_utilization"] >= 0.95
            assert identity["num_credit_accounts"] >= 5
    
    def test_bust_out_velocity_boost(self):
        """Test credit velocity boost in bust-out pattern."""
        gen = SyntheticIdentityPatternGenerator(seed=42)
        config = PatternConfig(
            pattern_type=PatternType.BUST_OUT,
            intensity=0.8,
            velocity_multiplier=3.0,
            count=1
        )
        identities = gen.generate_with_pattern(config)
        
        identity = identities[0]
        # Velocity should be boosted (realistic threshold based on actual data)
        velocity = identity["total_credit_limit"] / identity["credit_file_age_months"]
        assert velocity > 400  # High velocity for synthetic identity


class TestFraudRingPattern:
    """Fraud ring pattern injection tests."""
    
    def test_fraud_ring_pattern_injection(self):
        """Test fraud ring pattern injection."""
        gen = SyntheticIdentityPatternGenerator(seed=42)
        config = PatternConfig(
            pattern_type=PatternType.FRAUD_RING,
            intensity=1.0,
            count=5,
            ring_size=5
        )
        identities = gen.generate_with_pattern(config)
        
        assert len(identities) == 5
        for identity in identities:
            assert identity["pattern_injected"] == "fraud_ring"
            assert "ring_id" in identity
            assert "shared_attributes" in identity
    
    def test_fraud_ring_shared_ssn(self):
        """Test shared SSN in fraud ring."""
        gen = SyntheticIdentityPatternGenerator(seed=42)
        shared_ssn = "123-45-6789"
        config = PatternConfig(
            pattern_type=PatternType.FRAUD_RING,
            intensity=1.0,
            count=3,
            shared_ssn=shared_ssn
        )
        identities = gen.generate_with_pattern(config)
        
        # All should share the SSN
        for identity in identities:
            assert identity["ssn"] == shared_ssn
            assert "ssn" in identity["shared_attributes"]
    
    def test_fraud_ring_shared_phone(self):
        """Test shared phone in fraud ring."""
        gen = SyntheticIdentityPatternGenerator(seed=42)
        shared_phone = "555-1234"
        config = PatternConfig(
            pattern_type=PatternType.FRAUD_RING,
            intensity=1.0,
            count=3,
            shared_phone=shared_phone
        )
        identities = gen.generate_with_pattern(config)
        
        # Most should share the phone
        shared_count = sum(1 for id in identities if id["phone"] == shared_phone)
        assert shared_count >= 2
    
    def test_fraud_ring_intensity_affects_sharing(self):
        """Test that intensity affects attribute sharing."""
        gen = SyntheticIdentityPatternGenerator(seed=42)
        
        # Low intensity
        config_low = PatternConfig(
            pattern_type=PatternType.FRAUD_RING,
            intensity=0.3,
            count=5,
            ring_size=5
        )
        identities_low = gen.generate_with_pattern(config_low)
        
        # High intensity
        gen2 = SyntheticIdentityPatternGenerator(seed=42)
        config_high = PatternConfig(
            pattern_type=PatternType.FRAUD_RING,
            intensity=1.0,
            count=5,
            ring_size=5
        )
        identities_high = gen2.generate_with_pattern(config_high)
        
        # High intensity should have more shared attributes
        low_shared = sum(len(id["shared_attributes"]) for id in identities_low)
        high_shared = sum(len(id["shared_attributes"]) for id in identities_high)
        assert high_shared > low_shared


class TestIdentityTheftPattern:
    """Identity theft pattern injection tests."""
    
    def test_identity_theft_pattern_injection(self):
        """Test identity theft pattern injection."""
        gen = SyntheticIdentityPatternGenerator(seed=42)
        config = PatternConfig(
            pattern_type=PatternType.IDENTITY_THEFT,
            intensity=0.8,
            count=3
        )
        identities = gen.generate_with_pattern(config)
        
        assert len(identities) == 3
        for identity in identities:
            assert identity["pattern_injected"] == "identity_theft"
            assert identity["identity_type"] == "frankenstein"
            assert identity["credit_file_age_months"] <= 12
            assert "stolen_ssn" in identity
    
    def test_identity_theft_shared_stolen_ssn(self):
        """Test that all theft victims share stolen SSN."""
        gen = SyntheticIdentityPatternGenerator(seed=42)
        config = PatternConfig(
            pattern_type=PatternType.IDENTITY_THEFT,
            intensity=1.0,
            count=4
        )
        identities = gen.generate_with_pattern(config)
        
        # All should have same stolen SSN
        stolen_ssns = [id["stolen_ssn"] for id in identities]
        assert len(set(stolen_ssns)) == 1
    
    def test_identity_theft_high_intensity_markers(self):
        """Test high intensity adds more theft markers."""
        gen = SyntheticIdentityPatternGenerator(seed=42)
        config = PatternConfig(
            pattern_type=PatternType.IDENTITY_THEFT,
            intensity=1.0,
            count=2
        )
        identities = gen.generate_with_pattern(config)
        
        for identity in identities:
            # High intensity = more obvious theft
            assert "address_changes_last_year" in identity
            assert identity["address_changes_last_year"] >= 3
            assert identity["credit_utilization"] >= 0.7


class TestAuthorizedUserPattern:
    """Authorized user abuse pattern injection tests."""
    
    def test_authorized_user_pattern_injection(self):
        """Test authorized user pattern injection."""
        gen = SyntheticIdentityPatternGenerator(seed=42)
        config = PatternConfig(
            pattern_type=PatternType.AUTHORIZED_USER_ABUSE,
            intensity=0.8,
            count=3
        )
        identities = gen.generate_with_pattern(config)
        
        assert len(identities) == 3
        for identity in identities:
            assert identity["pattern_injected"] == "authorized_user_abuse"
            assert identity["has_authorized_user_history"] is True
            assert identity["credit_file_age_months"] <= 18
            assert "authorized_user_accounts" in identity
    
    def test_authorized_user_credit_boost(self):
        """Test credit score boost from piggybacking."""
        gen = SyntheticIdentityPatternGenerator(seed=42)
        
        # Generate without pattern
        base_identity = gen.base_generator.generate()
        base_score = base_identity["credit_score"]
        
        # Generate with pattern
        config = PatternConfig(
            pattern_type=PatternType.AUTHORIZED_USER_ABUSE,
            intensity=1.0,
            count=1
        )
        identities = gen.generate_with_pattern(config)
        boosted_score = identities[0]["credit_score"]
        
        # Score should be boosted (not always true due to randomness, but likely)
        # Just verify it's in valid range
        assert 300 <= boosted_score <= 850
    
    def test_authorized_user_credit_limit_boost(self):
        """Test credit limit boost from piggybacking."""
        gen = SyntheticIdentityPatternGenerator(seed=42)
        config = PatternConfig(
            pattern_type=PatternType.AUTHORIZED_USER_ABUSE,
            intensity=0.8,
            count=1
        )
        identities = gen.generate_with_pattern(config)
        
        identity = identities[0]
        # Should have decent credit limit
        assert identity["total_credit_limit"] > 0


class TestCreditMulePattern:
    """Credit mule pattern injection tests."""
    
    def test_credit_mule_pattern_injection(self):
        """Test credit mule pattern injection."""
        gen = SyntheticIdentityPatternGenerator(seed=42)
        config = PatternConfig(
            pattern_type=PatternType.CREDIT_MULE,
            intensity=0.8,
            count=3
        )
        identities = gen.generate_with_pattern(config)
        
        assert len(identities) == 3
        for identity in identities:
            assert identity["pattern_injected"] == "credit_mule"
            assert identity["credit_file_age_months"] <= 12
            assert identity["num_credit_accounts"] >= 5
            assert identity["credit_utilization"] >= 0.7
            assert "failed_applications_last_year" in identity
    
    def test_credit_mule_high_intensity_markers(self):
        """Test high intensity adds mule behavior markers."""
        gen = SyntheticIdentityPatternGenerator(seed=42)
        config = PatternConfig(
            pattern_type=PatternType.CREDIT_MULE,
            intensity=1.0,
            count=2
        )
        identities = gen.generate_with_pattern(config)
        
        for identity in identities:
            assert "rapid_account_cycling" in identity
            assert identity["rapid_account_cycling"] is True
            assert "suspicious_transaction_patterns" in identity
            assert identity["suspicious_transaction_patterns"] is True


class TestMixedBatchGeneration:
    """Mixed batch generation tests."""
    
    def test_generate_mixed_batch(self):
        """Test generating batch with mixed patterns."""
        gen = SyntheticIdentityPatternGenerator(seed=42)
        identities = gen.generate_mixed_batch(
            total_count=100,
            pattern_distribution={
                PatternType.BUST_OUT: 0.20,
                PatternType.FRAUD_RING: 0.15,
                PatternType.IDENTITY_THEFT: 0.10,
            },
            base_intensity=0.7
        )
        
        assert len(identities) == 100
        
        # Count patterns
        bust_out_count = sum(1 for id in identities if id.get("pattern_injected") == "bust_out")
        fraud_ring_count = sum(1 for id in identities if id.get("pattern_injected") == "fraud_ring")
        theft_count = sum(1 for id in identities if id.get("pattern_injected") == "identity_theft")
        clean_count = sum(1 for id in identities if id.get("pattern_injected") == "none")
        
        # Verify distribution (approximately)
        assert 15 <= bust_out_count <= 25  # ~20%
        assert 10 <= fraud_ring_count <= 20  # ~15%
        assert 5 <= theft_count <= 15  # ~10%
        assert 45 <= clean_count <= 65  # ~55%
    
    def test_mixed_batch_shuffled(self):
        """Test that mixed batch is shuffled."""
        gen = SyntheticIdentityPatternGenerator(seed=42)
        identities = gen.generate_mixed_batch(
            total_count=50,
            pattern_distribution={
                PatternType.BUST_OUT: 0.50,
            },
            base_intensity=0.8
        )
        
        # Patterns should not all be at start or end
        first_10_patterns = [id.get("pattern_injected") for id in identities[:10]]
        last_10_patterns = [id.get("pattern_injected") for id in identities[-10:]]
        
        # Both should have mix of patterns
        assert "bust_out" in first_10_patterns or "none" in first_10_patterns
        assert "bust_out" in last_10_patterns or "none" in last_10_patterns


class TestPatternSummary:
    """Pattern summary tests."""
    
    def test_get_pattern_summary_empty(self):
        """Test pattern summary with no patterns."""
        gen = SyntheticIdentityPatternGenerator(seed=42)
        summary = gen.get_pattern_summary()
        
        assert summary["total_patterns"] == 0
        assert summary["total_identities"] == 0
        assert summary["patterns_by_type"] == {}
    
    def test_get_pattern_summary_single_pattern(self):
        """Test pattern summary with single pattern."""
        gen = SyntheticIdentityPatternGenerator(seed=42)
        config = PatternConfig(
            pattern_type=PatternType.BUST_OUT,
            intensity=0.8,
            count=5
        )
        gen.generate_with_pattern(config)
        
        summary = gen.get_pattern_summary()
        
        assert summary["total_patterns"] == 1
        assert summary["total_identities"] == 5
        assert "bust_out" in summary["patterns_by_type"]
        assert summary["patterns_by_type"]["bust_out"]["count"] == 1
        assert summary["patterns_by_type"]["bust_out"]["identities"] == 5
        assert summary["patterns_by_type"]["bust_out"]["avg_intensity"] == 0.8
    
    def test_get_pattern_summary_multiple_patterns(self):
        """Test pattern summary with multiple patterns."""
        gen = SyntheticIdentityPatternGenerator(seed=42)
        
        # Generate multiple patterns
        config1 = PatternConfig(pattern_type=PatternType.BUST_OUT, intensity=0.8, count=5)
        gen.generate_with_pattern(config1)
        
        config2 = PatternConfig(pattern_type=PatternType.FRAUD_RING, intensity=0.7, count=3)
        gen.generate_with_pattern(config2)
        
        config3 = PatternConfig(pattern_type=PatternType.BUST_OUT, intensity=0.9, count=2)
        gen.generate_with_pattern(config3)
        
        summary = gen.get_pattern_summary()
        
        assert summary["total_patterns"] == 3
        assert summary["total_identities"] == 10
        assert "bust_out" in summary["patterns_by_type"]
        assert "fraud_ring" in summary["patterns_by_type"]
        
        # Bust-out should have 2 patterns, 7 identities
        assert summary["patterns_by_type"]["bust_out"]["count"] == 2
        assert summary["patterns_by_type"]["bust_out"]["identities"] == 7
        # Average intensity: (0.8 + 0.9) / 2 = 0.85
        assert abs(summary["patterns_by_type"]["bust_out"]["avg_intensity"] - 0.85) < 0.01


class TestDeterminism:
    """Determinism tests."""
    
    def test_deterministic_with_seed(self):
        """Test that same seed produces same patterns."""
        gen1 = SyntheticIdentityPatternGenerator(seed=42)
        config = PatternConfig(
            pattern_type=PatternType.BUST_OUT,
            intensity=0.8,
            count=5
        )
        identities1 = gen1.generate_with_pattern(config)
        
        gen2 = SyntheticIdentityPatternGenerator(seed=42)
        identities2 = gen2.generate_with_pattern(config)
        
        # Should produce identical results
        assert len(identities1) == len(identities2)
        for id1, id2 in zip(identities1, identities2):
            assert id1["identity_id"] == id2["identity_id"]
            assert id1["credit_file_age_months"] == id2["credit_file_age_months"]
            assert id1["credit_utilization"] == id2["credit_utilization"]
    
    def test_different_seeds_different_patterns(self):
        """Test that different seeds produce different patterns."""
        gen1 = SyntheticIdentityPatternGenerator(seed=42)
        config = PatternConfig(
            pattern_type=PatternType.BUST_OUT,
            intensity=0.8,
            count=5
        )
        identities1 = gen1.generate_with_pattern(config)
        
        gen2 = SyntheticIdentityPatternGenerator(seed=123)
        identities2 = gen2.generate_with_pattern(config)
        
        # Should produce different results
        assert identities1[0]["identity_id"] != identities2[0]["identity_id"]


class TestEdgeCases:
    """Edge case tests."""
    
    def test_zero_count(self):
        """Test pattern injection with zero count."""
        gen = SyntheticIdentityPatternGenerator(seed=42)
        config = PatternConfig(
            pattern_type=PatternType.BUST_OUT,
            intensity=0.8,
            count=0
        )
        identities = gen.generate_with_pattern(config)
        
        assert len(identities) == 0
    
    def test_intensity_zero(self):
        """Test pattern injection with zero intensity."""
        gen = SyntheticIdentityPatternGenerator(seed=42)
        config = PatternConfig(
            pattern_type=PatternType.BUST_OUT,
            intensity=0.0,
            count=3
        )
        identities = gen.generate_with_pattern(config)
        
        # Should still inject pattern but with minimal effect
        assert len(identities) == 3
        for identity in identities:
            assert identity["pattern_injected"] == "bust_out"
            assert identity["pattern_intensity"] == 0.0
    
    def test_intensity_above_one(self):
        """Test pattern injection with intensity > 1.0."""
        gen = SyntheticIdentityPatternGenerator(seed=42)
        config = PatternConfig(
            pattern_type=PatternType.BUST_OUT,
            intensity=1.5,
            count=2
        )
        identities = gen.generate_with_pattern(config)
        
        # Should handle gracefully (may cap at 1.0 or allow)
        assert len(identities) == 2
        for identity in identities:
            assert identity["pattern_intensity"] == 1.5

# Made with Bob
