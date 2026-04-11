"""
Tests for BustOutDetector
==========================

Comprehensive test suite for bust-out scheme detection.

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team
Date: 2026-04-11
Phase: 7.2 - Synthetic Identity Fraud Detection
"""

import pytest

from banking.identity import (
    SyntheticIdentityGenerator,
    BustOutDetector,
    BustOutDetectionResult,
    BustOutIndicator,
)


class TestBustOutDetectorBasic:
    """Basic functionality tests."""
    
    def test_initialization(self):
        """Test detector initialization."""
        detector = BustOutDetector()
        assert detector.bust_out_threshold == 70
        assert detector.high_velocity_threshold == 5000
    
    def test_initialization_with_config(self):
        """Test detector initialization with custom config."""
        config = {
            "bust_out_threshold": 80,
            "high_velocity_threshold": 6000,
            "max_out_threshold": 0.95,
        }
        detector = BustOutDetector(config=config)
        assert detector.bust_out_threshold == 80
        assert detector.high_velocity_threshold == 6000
        assert detector.max_out_threshold == 0.95
    
    def test_detect_single_identity(self):
        """Test detecting bust-out for single identity."""
        gen = SyntheticIdentityGenerator(seed=42)
        identity = gen.generate()
        
        detector = BustOutDetector()
        result = detector.detect(identity)
        
        assert isinstance(result, BustOutDetectionResult)
        assert result.identity_id == identity["identity_id"]
        assert isinstance(result.is_bust_out, bool)
        assert 0 <= result.bust_out_score <= 100
    
    def test_detect_batch(self):
        """Test detecting bust-out for multiple identities."""
        gen = SyntheticIdentityGenerator(seed=42)
        identities = gen.generate_batch(10)
        
        detector = BustOutDetector()
        results = detector.detect_batch(identities)
        
        assert len(results) == 10
        assert all(isinstance(r, BustOutDetectionResult) for r in results)


class TestCreditVelocity:
    """Credit velocity detection tests."""
    
    def test_high_velocity_detection(self):
        """Test detection of high credit velocity."""
        gen = SyntheticIdentityGenerator(seed=42, config={
            "synthetic_probability": 1.0,
        })
        identities = gen.generate_batch(20)
        
        # Use lower threshold to ensure detection with synthetic data
        detector = BustOutDetector(config={"high_velocity_threshold": 2000})
        results = detector.detect_batch(identities)
        
        # Some should have high velocity indicators with lower threshold
        high_velocity = [r for r in results
                        if any(ind.indicator_type == "high_credit_velocity"
                              for ind in r.indicators)]
        assert len(high_velocity) > 0
    
    def test_velocity_calculation(self):
        """Test credit velocity calculation."""
        gen = SyntheticIdentityGenerator(seed=42)
        identity = gen.generate()
        
        detector = BustOutDetector()
        result = detector.detect(identity)
        
        # Velocity should be positive
        assert result.credit_velocity >= 0
        
        # Verify calculation
        expected_velocity = identity["total_credit_limit"] / max(identity["credit_file_age_months"], 1)
        assert abs(result.credit_velocity - expected_velocity) < 0.01


class TestUtilizationSpike:
    """Utilization spike detection tests."""
    
    def test_utilization_spike_detection(self):
        """Test detection of utilization spike."""
        gen = SyntheticIdentityGenerator(seed=42, config={
            "synthetic_probability": 1.0,
            "bust_out_probability": 0.80,
        })
        identities = gen.generate_batch(30)
        
        detector = BustOutDetector()
        results = detector.detect_batch(identities)
        
        # Some should have utilization spike
        spikes = [r for r in results if r.utilization_spike]
        assert len(spikes) > 5
    
    def test_high_utilization_increases_score(self):
        """Test high utilization increases bust-out score."""
        gen = SyntheticIdentityGenerator(seed=42, config={
            "synthetic_probability": 1.0,
            "bust_out_probability": 0.80,
        })
        identities = gen.generate_batch(30)
        
        detector = BustOutDetector()
        results = detector.detect_batch(identities)
        
        # High utilization should correlate with higher scores
        high_util = [r for r in results if r.utilization_spike]
        low_util = [r for r in results if not r.utilization_spike]
        
        if high_util and low_util:
            avg_high = sum(r.bust_out_score for r in high_util) / len(high_util)
            avg_low = sum(r.bust_out_score for r in low_util) / len(low_util)
            assert avg_high > avg_low


class TestBustOutScoring:
    """Bust-out scoring tests."""
    
    def test_bust_out_score_range(self):
        """Test bust-out scores are in valid range."""
        gen = SyntheticIdentityGenerator(seed=42)
        identities = gen.generate_batch(20)
        
        detector = BustOutDetector()
        results = detector.detect_batch(identities)
        
        for result in results:
            assert 0 <= result.bust_out_score <= 100
    
    def test_synthetic_increases_score(self):
        """Test synthetic identities have higher bust-out scores."""
        gen = SyntheticIdentityGenerator(seed=42)
        identities = gen.generate_batch(30)
        
        detector = BustOutDetector()
        results = detector.detect_batch(identities)
        
        # Separate by synthetic flag
        synthetic_results = [r for r in results 
                           if any(ind.indicator_type == "synthetic_identity" 
                                 for ind in r.indicators)]
        non_synthetic = [r for r in results 
                        if not any(ind.indicator_type == "synthetic_identity" 
                                  for ind in r.indicators)]
        
        if synthetic_results and non_synthetic:
            avg_synth = sum(r.bust_out_score for r in synthetic_results) / len(synthetic_results)
            avg_non = sum(r.bust_out_score for r in non_synthetic) / len(non_synthetic)
            assert avg_synth > avg_non
    
    def test_bust_out_threshold(self):
        """Test bust-out threshold determines is_bust_out flag."""
        gen = SyntheticIdentityGenerator(seed=42, config={
            "synthetic_probability": 1.0,
            "bust_out_probability": 0.80,
        })
        identities = gen.generate_batch(30)
        
        detector = BustOutDetector(config={"bust_out_threshold": 70})
        results = detector.detect_batch(identities)
        
        for result in results:
            if result.bust_out_score >= 70:
                assert result.is_bust_out
            else:
                assert not result.is_bust_out


class TestRiskLevels:
    """Risk level determination tests."""
    
    def test_risk_level_values(self):
        """Test risk levels are valid."""
        gen = SyntheticIdentityGenerator(seed=42)
        identities = gen.generate_batch(20)
        
        detector = BustOutDetector()
        results = detector.detect_batch(identities)
        
        valid_levels = ["low", "medium", "high", "critical"]
        for result in results:
            assert result.risk_level in valid_levels
    
    def test_risk_level_matches_score(self):
        """Test risk level matches bust-out score."""
        gen = SyntheticIdentityGenerator(seed=42)
        identities = gen.generate_batch(30)
        
        detector = BustOutDetector(config={"critical_score_threshold": 85})
        results = detector.detect_batch(identities)
        
        for result in results:
            if result.bust_out_score >= 85:
                assert result.risk_level == "critical"
            elif result.bust_out_score >= 70:
                assert result.risk_level == "high"
            elif result.bust_out_score >= 50:
                assert result.risk_level == "medium"
            else:
                assert result.risk_level == "low"


class TestIndicators:
    """Indicator detection tests."""
    
    def test_indicators_present(self):
        """Test indicators are detected."""
        gen = SyntheticIdentityGenerator(seed=42, config={"synthetic_probability": 1.0})
        identities = gen.generate_batch(20)
        
        detector = BustOutDetector()
        results = detector.detect_batch(identities)
        
        # All should have at least one indicator
        for result in results:
            assert len(result.indicators) > 0
    
    def test_indicator_structure(self):
        """Test indicator structure is correct."""
        gen = SyntheticIdentityGenerator(seed=42)
        identity = gen.generate()
        
        detector = BustOutDetector()
        result = detector.detect(identity)
        
        for indicator in result.indicators:
            assert isinstance(indicator, BustOutIndicator)
            assert indicator.indicator_type
            assert indicator.severity in ["low", "medium", "high", "critical"]
            assert indicator.description
            assert indicator.score >= 0
    
    def test_critical_indicators(self):
        """Test critical indicators are flagged."""
        gen = SyntheticIdentityGenerator(seed=42, config={
            "synthetic_probability": 1.0,
            "bust_out_probability": 0.80,
        })
        identities = gen.generate_batch(30)
        
        detector = BustOutDetector()
        results = detector.detect_batch(identities)
        
        # Some should have critical indicators
        critical = [r for r in results 
                   if any(ind.severity == "critical" for ind in r.indicators)]
        assert len(critical) > 5


class TestRecommendations:
    """Recommendation generation tests."""
    
    def test_recommendations_present(self):
        """Test recommendations are generated."""
        gen = SyntheticIdentityGenerator(seed=42)
        identities = gen.generate_batch(10)
        
        detector = BustOutDetector()
        results = detector.detect_batch(identities)
        
        for result in results:
            assert len(result.recommendations) > 0
    
    def test_alert_for_bust_out(self):
        """Test ALERT recommendation for bust-out."""
        gen = SyntheticIdentityGenerator(seed=42, config={
            "synthetic_probability": 1.0,
            "bust_out_probability": 0.80,
        })
        identities = gen.generate_batch(30)
        
        detector = BustOutDetector()
        results = detector.detect_batch(identities)
        
        # Bust-outs should have ALERT recommendations
        bust_outs = [r for r in results if r.is_bust_out]
        if bust_outs:
            for result in bust_outs:
                assert any("ALERT" in rec for rec in result.recommendations)
    
    def test_freeze_recommendation(self):
        """Test freeze recommendation for high-risk."""
        gen = SyntheticIdentityGenerator(seed=42, config={
            "synthetic_probability": 1.0,
            "bust_out_probability": 0.80,
        })
        identities = gen.generate_batch(30)
        
        detector = BustOutDetector()
        results = detector.detect_batch(identities)
        
        # High-risk should have freeze recommendation
        high_risk = [r for r in results if r.is_bust_out]
        if high_risk:
            assert any("Freeze" in rec or "freeze" in rec 
                      for result in high_risk 
                      for rec in result.recommendations)


class TestHighRiskIdentities:
    """High-risk identity detection tests."""
    
    def test_get_high_risk_identities(self):
        """Test getting high-risk identities."""
        gen = SyntheticIdentityGenerator(seed=42, config={
            "synthetic_probability": 1.0,
            "bust_out_probability": 0.80,
        })
        identities = gen.generate_batch(30)
        
        detector = BustOutDetector()
        high_risk = detector.get_high_risk_identities(identities, min_score=70)
        
        assert len(high_risk) > 0
        assert all(r.bust_out_score >= 70 for r in high_risk)
        # Should be sorted by score (highest first)
        if len(high_risk) >= 2:
            assert high_risk[0].bust_out_score >= high_risk[-1].bust_out_score


class TestStatistics:
    """Statistics tests."""
    
    def test_get_statistics(self):
        """Test getting detection statistics."""
        gen = SyntheticIdentityGenerator(seed=42)
        identities = gen.generate_batch(20)
        
        detector = BustOutDetector()
        results = detector.detect_batch(identities)
        stats = detector.get_statistics(results)
        
        assert stats["total_identities"] == 20
        assert "bust_out_count" in stats
        assert "bust_out_rate" in stats
        assert "average_bust_out_score" in stats
        assert "risk_level_distribution" in stats
        assert "top_indicators" in stats
        assert "average_credit_velocity" in stats
        assert "max_credit_velocity" in stats
        assert "high_utilization_count" in stats
    
    def test_statistics_with_empty_results(self):
        """Test statistics with no results."""
        detector = BustOutDetector()
        stats = detector.get_statistics([])
        
        assert stats["total_identities"] == 0
        assert stats["bust_out_count"] == 0
    
    def test_bust_out_rate_calculation(self):
        """Test bust-out rate calculation."""
        gen = SyntheticIdentityGenerator(seed=42, config={
            "synthetic_probability": 1.0,
            "bust_out_probability": 0.80,
        })
        identities = gen.generate_batch(30)
        
        detector = BustOutDetector()
        results = detector.detect_batch(identities)
        stats = detector.get_statistics(results)
        
        # Verify rate calculation
        expected_rate = stats["bust_out_count"] / stats["total_identities"]
        assert abs(stats["bust_out_rate"] - expected_rate) < 0.01


class TestEdgeCases:
    """Edge case tests."""
    
    def test_zero_credit_file_age(self):
        """Test handling of zero credit file age."""
        gen = SyntheticIdentityGenerator(seed=42)
        identity = gen.generate()
        identity["credit_file_age_months"] = 0  # Edge case
        
        detector = BustOutDetector()
        result = detector.detect(identity)
        
        # Should not crash
        assert result is not None
        assert result.credit_velocity >= 0
    
    def test_zero_credit_limit(self):
        """Test handling of zero credit limit."""
        gen = SyntheticIdentityGenerator(seed=42)
        identity = gen.generate()
        identity["total_credit_limit"] = 0  # Edge case
        
        detector = BustOutDetector()
        result = detector.detect(identity)
        
        # Should not crash
        assert result is not None
        assert result.credit_velocity == 0
    
    def test_legitimate_identity_low_score(self):
        """Test legitimate identities have low bust-out scores."""
        gen = SyntheticIdentityGenerator(seed=42, config={"synthetic_probability": 0.0})
        identities = gen.generate_batch(20)
        
        detector = BustOutDetector()
        results = detector.detect_batch(identities)
        
        # Most should have low scores
        low_scores = [r for r in results if r.bust_out_score < 50]
        assert len(low_scores) >= 15


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob
