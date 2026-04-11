"""
Tests for IdentityValidator
============================

Comprehensive test suite for identity validation and fraud detection.

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team
Date: 2026-04-11
Phase: 7.2 - Synthetic Identity Fraud Detection
"""

import pytest

from banking.identity import (
    SyntheticIdentityGenerator,
    IdentityValidator,
    ValidationResult,
    SharedAttributeCluster,
)


class TestIdentityValidatorBasic:
    """Basic functionality tests."""
    
    def test_initialization(self):
        """Test validator initialization."""
        validator = IdentityValidator()
        assert validator.min_authenticity_threshold == 70
        assert validator.max_risk_threshold == 50
    
    def test_initialization_with_config(self):
        """Test validator initialization with custom config."""
        config = {
            "min_authenticity_threshold": 80,
            "max_risk_threshold": 40,
            "shared_ssn_weight": 50,
        }
        validator = IdentityValidator(config=config)
        assert validator.min_authenticity_threshold == 80
        assert validator.max_risk_threshold == 40
        assert validator.shared_ssn_weight == 50
    
    def test_add_single_identity(self):
        """Test adding a single identity."""
        gen = SyntheticIdentityGenerator(seed=42)
        identity = gen.generate()
        
        validator = IdentityValidator()
        validator.add_identity(identity)
        
        assert len(validator._identities) == 1
        assert identity["identity_id"] in validator._identities
    
    def test_add_multiple_identities(self):
        """Test adding multiple identities."""
        gen = SyntheticIdentityGenerator(seed=42)
        identities = gen.generate_batch(10)
        
        validator = IdentityValidator()
        validator.add_identities(identities)
        
        assert len(validator._identities) == 10


class TestValidation:
    """Validation tests."""
    
    def test_validate_single_identity(self):
        """Test validating a single identity."""
        gen = SyntheticIdentityGenerator(seed=42)
        identity = gen.generate()
        
        validator = IdentityValidator()
        validator.add_identity(identity)
        
        result = validator.validate(identity["identity_id"])
        
        assert isinstance(result, ValidationResult)
        assert result.identity_id == identity["identity_id"]
        assert isinstance(result.is_authentic, bool)
        assert 0 <= result.authenticity_score <= 100
        assert 0 <= result.risk_score <= 100
    
    def test_validate_nonexistent_identity(self):
        """Test validating non-existent identity raises error."""
        validator = IdentityValidator()
        
        with pytest.raises(ValueError, match="not found"):
            validator.validate("nonexistent-id")
    
    def test_validate_all(self):
        """Test validating all identities."""
        gen = SyntheticIdentityGenerator(seed=42)
        identities = gen.generate_batch(10)
        
        validator = IdentityValidator()
        validator.add_identities(identities)
        
        results = validator.validate_all()
        
        assert len(results) == 10
        assert all(isinstance(r, ValidationResult) for r in results)
    
    def test_legitimate_identity_high_authenticity(self):
        """Test legitimate identities have high authenticity scores."""
        gen = SyntheticIdentityGenerator(seed=42, config={"synthetic_probability": 0.0})
        identities = gen.generate_batch(10)
        
        validator = IdentityValidator()
        validator.add_identities(identities)
        
        results = validator.validate_all()
        
        # All should be authentic
        assert all(r.is_authentic for r in results)
        assert all(r.authenticity_score >= 70 for r in results)
    
    def test_synthetic_identity_low_authenticity(self):
        """Test synthetic identities have low authenticity scores."""
        gen = SyntheticIdentityGenerator(seed=42, config={"synthetic_probability": 1.0})
        identities = gen.generate_batch(10)
        
        validator = IdentityValidator()
        validator.add_identities(identities)
        
        results = validator.validate_all()
        
        # Most should be flagged as not authentic
        not_authentic = [r for r in results if not r.is_authentic]
        assert len(not_authentic) >= 5  # At least half


class TestSharedAttributeDetection:
    """Shared attribute detection tests."""
    
    def test_detect_shared_ssn(self):
        """Test detection of shared SSN."""
        gen = SyntheticIdentityGenerator(seed=42, config={
            "synthetic_probability": 1.0,
            "shared_ssn_probability": 0.80,
        })
        identities = gen.generate_batch(20)
        
        validator = IdentityValidator()
        validator.add_identities(identities)
        
        # Check for shared SSN detection
        results = validator.validate_all()
        shared_ssn_count = sum(1 for r in results if "ssn" in r.shared_attributes)
        
        assert shared_ssn_count > 5  # Should have multiple shared SSNs
    
    def test_detect_shared_phone(self):
        """Test detection of shared phone."""
        gen = SyntheticIdentityGenerator(seed=42, config={
            "synthetic_probability": 1.0,
            "shared_phone_probability": 0.80,
        })
        identities = gen.generate_batch(20)
        
        validator = IdentityValidator()
        validator.add_identities(identities)
        
        results = validator.validate_all()
        shared_phone_count = sum(1 for r in results if "phone" in r.shared_attributes)
        
        assert shared_phone_count > 5
    
    def test_detect_shared_address(self):
        """Test detection of shared address."""
        gen = SyntheticIdentityGenerator(seed=42, config={
            "synthetic_probability": 1.0,
            "shared_address_probability": 0.80,
        })
        identities = gen.generate_batch(20)
        
        validator = IdentityValidator()
        validator.add_identities(identities)
        
        results = validator.validate_all()
        shared_address_count = sum(1 for r in results if "address" in r.shared_attributes)
        
        assert shared_address_count > 3
    
    def test_multiple_shared_attributes(self):
        """Test detection of multiple shared attributes."""
        gen = SyntheticIdentityGenerator(seed=42, config={
            "synthetic_probability": 1.0,
            "shared_ssn_probability": 0.80,
            "shared_phone_probability": 0.80,
            "shared_address_probability": 0.80,
        })
        identities = gen.generate_batch(30)
        
        validator = IdentityValidator()
        validator.add_identities(identities)
        
        results = validator.validate_all()
        multi_shared = [r for r in results if len(r.shared_attributes) >= 2]
        
        assert len(multi_shared) > 5


class TestSharedAttributeClusters:
    """Shared attribute cluster tests."""
    
    def test_get_shared_attribute_clusters(self):
        """Test getting shared attribute clusters."""
        gen = SyntheticIdentityGenerator(seed=42, config={
            "synthetic_probability": 1.0,
            "shared_ssn_probability": 0.70,
        })
        identities = gen.generate_batch(20)
        
        validator = IdentityValidator()
        validator.add_identities(identities)
        
        clusters = validator.get_shared_attribute_clusters()
        
        assert len(clusters) > 0
        assert all(isinstance(c, SharedAttributeCluster) for c in clusters)
    
    def test_cluster_risk_scoring(self):
        """Test cluster risk scoring based on size."""
        gen = SyntheticIdentityGenerator(seed=42, config={
            "synthetic_probability": 1.0,
            "shared_ssn_probability": 0.80,
        })
        identities = gen.generate_batch(30)
        
        validator = IdentityValidator()
        validator.add_identities(identities)
        
        clusters = validator.get_shared_attribute_clusters()
        
        # Larger clusters should have higher risk scores
        if len(clusters) >= 2:
            # Clusters are sorted by risk score (highest first)
            assert clusters[0].risk_score >= clusters[-1].risk_score
    
    def test_cluster_contains_identity_ids(self):
        """Test clusters contain correct identity IDs."""
        gen = SyntheticIdentityGenerator(seed=42, config={
            "synthetic_probability": 1.0,
            "shared_ssn_probability": 0.80,
        })
        identities = gen.generate_batch(20)
        
        validator = IdentityValidator()
        validator.add_identities(identities)
        
        clusters = validator.get_shared_attribute_clusters()
        
        for cluster in clusters:
            assert len(cluster.identity_ids) >= 2
            # All identity IDs should exist
            assert all(id in validator._identities for id in cluster.identity_ids)


class TestAuthenticityScoring:
    """Authenticity scoring tests."""
    
    def test_authenticity_score_range(self):
        """Test authenticity scores are in valid range."""
        gen = SyntheticIdentityGenerator(seed=42)
        identities = gen.generate_batch(20)
        
        validator = IdentityValidator()
        validator.add_identities(identities)
        
        results = validator.validate_all()
        
        for result in results:
            assert 0 <= result.authenticity_score <= 100
    
    def test_synthetic_lowers_authenticity(self):
        """Test synthetic flag lowers authenticity score."""
        gen = SyntheticIdentityGenerator(seed=42)
        
        # Generate one legitimate and one synthetic
        legitimate = gen.generate()
        while legitimate["is_synthetic"]:
            legitimate = gen.generate()
        
        synthetic = gen.generate()
        while not synthetic["is_synthetic"]:
            synthetic = gen.generate()
        
        validator = IdentityValidator()
        validator.add_identity(legitimate)
        validator.add_identity(synthetic)
        
        leg_result = validator.validate(legitimate["identity_id"])
        syn_result = validator.validate(synthetic["identity_id"])
        
        # Legitimate should have higher authenticity
        assert leg_result.authenticity_score > syn_result.authenticity_score
    
    def test_shared_attributes_lower_authenticity(self):
        """Test shared attributes lower authenticity score."""
        gen = SyntheticIdentityGenerator(seed=42, config={
            "synthetic_probability": 1.0,
            "shared_ssn_probability": 0.80,
        })
        identities = gen.generate_batch(20)
        
        validator = IdentityValidator()
        validator.add_identities(identities)
        
        results = validator.validate_all()
        
        # Identities with shared attributes should have lower scores
        with_shared = [r for r in results if r.shared_attributes]
        without_shared = [r for r in results if not r.shared_attributes]
        
        if with_shared and without_shared:
            avg_with = sum(r.authenticity_score for r in with_shared) / len(with_shared)
            avg_without = sum(r.authenticity_score for r in without_shared) / len(without_shared)
            assert avg_with < avg_without


class TestRiskScoring:
    """Risk scoring tests."""
    
    def test_risk_score_range(self):
        """Test risk scores are in valid range."""
        gen = SyntheticIdentityGenerator(seed=42)
        identities = gen.generate_batch(20)
        
        validator = IdentityValidator()
        validator.add_identities(identities)
        
        results = validator.validate_all()
        
        for result in results:
            assert 0 <= result.risk_score <= 100
    
    def test_shared_attributes_increase_risk(self):
        """Test shared attributes increase risk score."""
        gen = SyntheticIdentityGenerator(seed=42, config={
            "synthetic_probability": 1.0,
            "shared_ssn_probability": 0.80,
        })
        identities = gen.generate_batch(20)
        
        validator = IdentityValidator()
        validator.add_identities(identities)
        
        results = validator.validate_all()
        
        with_shared = [r for r in results if r.shared_attributes]
        without_shared = [r for r in results if not r.shared_attributes]
        
        if with_shared and without_shared:
            avg_with = sum(r.risk_score for r in with_shared) / len(with_shared)
            avg_without = sum(r.risk_score for r in without_shared) / len(without_shared)
            assert avg_with > avg_without
    
    def test_get_high_risk_identities(self):
        """Test getting high-risk identities."""
        gen = SyntheticIdentityGenerator(seed=42, config={
            "synthetic_probability": 1.0,
            "bust_out_probability": 0.80,
        })
        identities = gen.generate_batch(30)
        
        validator = IdentityValidator()
        validator.add_identities(identities)
        
        high_risk = validator.get_high_risk_identities(min_risk_score=70)
        
        assert len(high_risk) > 0
        assert all(r.risk_score >= 70 for r in high_risk)
        # Should be sorted by risk score (highest first)
        if len(high_risk) >= 2:
            assert high_risk[0].risk_score >= high_risk[-1].risk_score


class TestFraudIndicators:
    """Fraud indicator tests."""
    
    def test_fraud_indicators_present(self):
        """Test fraud indicators are identified."""
        gen = SyntheticIdentityGenerator(seed=42, config={"synthetic_probability": 1.0})
        identities = gen.generate_batch(20)
        
        validator = IdentityValidator()
        validator.add_identities(identities)
        
        results = validator.validate_all()
        
        # All synthetics should have fraud indicators
        for result in results:
            assert len(result.fraud_indicators) > 0
    
    def test_synthetic_identity_indicator(self):
        """Test synthetic identity indicator is flagged."""
        gen = SyntheticIdentityGenerator(seed=42, config={"synthetic_probability": 1.0})
        identities = gen.generate_batch(10)
        
        validator = IdentityValidator()
        validator.add_identities(identities)
        
        results = validator.validate_all()
        
        for result in results:
            # Should have synthetic_identity indicator
            assert any("synthetic_identity_" in ind for ind in result.fraud_indicators)
    
    def test_shared_ssn_indicator(self):
        """Test shared SSN indicator is flagged."""
        gen = SyntheticIdentityGenerator(seed=42, config={
            "synthetic_probability": 1.0,
            "shared_ssn_probability": 0.80,
        })
        identities = gen.generate_batch(20)
        
        validator = IdentityValidator()
        validator.add_identities(identities)
        
        results = validator.validate_all()
        
        # Some should have shared_ssn indicator
        shared_ssn_indicators = [r for r in results 
                                if any("shared_ssn" in ind for ind in r.fraud_indicators)]
        assert len(shared_ssn_indicators) > 5


class TestRecommendations:
    """Recommendation generation tests."""
    
    def test_recommendations_present(self):
        """Test recommendations are generated."""
        gen = SyntheticIdentityGenerator(seed=42)
        identities = gen.generate_batch(10)
        
        validator = IdentityValidator()
        validator.add_identities(identities)
        
        results = validator.validate_all()
        
        for result in results:
            assert len(result.recommendations) > 0
    
    def test_reject_recommendation_for_low_authenticity(self):
        """Test REJECT recommendation for low authenticity."""
        gen = SyntheticIdentityGenerator(seed=42, config={
            "synthetic_probability": 1.0,
            "shared_ssn_probability": 0.80,
        })
        identities = gen.generate_batch(20)
        
        validator = IdentityValidator()
        validator.add_identities(identities)
        
        results = validator.validate_all()
        
        # Some should have REJECT recommendation
        rejects = [r for r in results 
                  if any("REJECT" in rec for rec in r.recommendations)]
        assert len(rejects) > 0
    
    def test_high_risk_alert(self):
        """Test HIGH RISK alert for high-risk identities."""
        gen = SyntheticIdentityGenerator(seed=42, config={
            "synthetic_probability": 1.0,
            "bust_out_probability": 0.80,
        })
        identities = gen.generate_batch(30)
        
        validator = IdentityValidator()
        validator.add_identities(identities)
        
        results = validator.validate_all()
        
        # Some should have HIGH RISK recommendation
        high_risk = [r for r in results 
                    if any("HIGH RISK" in rec for rec in r.recommendations)]
        assert len(high_risk) > 0


class TestStatistics:
    """Statistics tests."""
    
    def test_get_statistics(self):
        """Test getting validation statistics."""
        gen = SyntheticIdentityGenerator(seed=42)
        identities = gen.generate_batch(20)
        
        validator = IdentityValidator()
        validator.add_identities(identities)
        
        stats = validator.get_statistics()
        
        assert stats["total_identities"] == 20
        assert "authentic_count" in stats
        assert "synthetic_count" in stats
        assert "high_risk_count" in stats
        assert "shared_ssn_clusters" in stats
    
    def test_statistics_with_empty_validator(self):
        """Test statistics with no identities."""
        validator = IdentityValidator()
        stats = validator.get_statistics()
        
        assert stats["total_identities"] == 0
        assert stats["authentic_count"] == 0
    
    def test_authenticity_rate_calculation(self):
        """Test authenticity rate calculation."""
        gen = SyntheticIdentityGenerator(seed=42, config={"synthetic_probability": 0.0})
        identities = gen.generate_batch(10)
        
        validator = IdentityValidator()
        validator.add_identities(identities)
        
        stats = validator.get_statistics()
        
        # All legitimate should have high authenticity rate
        assert stats["authenticity_rate"] >= 0.8


class TestEdgeCases:
    """Edge case tests."""
    
    def test_single_identity_validation(self):
        """Test validating a single identity."""
        gen = SyntheticIdentityGenerator(seed=42)
        identity = gen.generate()
        
        validator = IdentityValidator()
        validator.add_identity(identity)
        
        result = validator.validate(identity["identity_id"])
        
        assert result is not None
        # Single identity should have no shared attributes
        assert len(result.shared_attributes) == 0
    
    def test_empty_validator_statistics(self):
        """Test statistics on empty validator."""
        validator = IdentityValidator()
        stats = validator.get_statistics()
        
        assert stats["total_identities"] == 0
        assert stats["shared_ssn_clusters"] == 0
    
    def test_all_legitimate_identities(self):
        """Test with all legitimate identities."""
        gen = SyntheticIdentityGenerator(seed=42, config={"synthetic_probability": 0.0})
        identities = gen.generate_batch(20)
        
        validator = IdentityValidator()
        validator.add_identities(identities)
        
        results = validator.validate_all()
        
        # Most should be authentic
        authentic_count = sum(1 for r in results if r.is_authentic)
        assert authentic_count >= 15


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob
