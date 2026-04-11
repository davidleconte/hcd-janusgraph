"""
Identity Fraud Detection End-to-End Integration Tests
====================================================

Tests the complete workflow of synthetic identity fraud detection:
1. Generate synthetic identities with fraud patterns
2. Validate identity authenticity
3. Detect bust-out schemes
4. Analyze results and generate reports

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team
Date: 2026-04-11
Phase: 7.3 - Synthetic Identity Fraud Detection
"""

import pytest

from banking.identity import (
    SyntheticIdentityGenerator,
    SyntheticIdentityPatternGenerator,
    IdentityValidator,
    BustOutDetector,
    PatternConfig,
    PatternType,
)


class TestEndToEndWorkflow:
    """End-to-end workflow tests."""
    
    def test_complete_fraud_detection_pipeline(self):
        """Test complete fraud detection pipeline."""
        # Step 1: Generate synthetic identities with patterns
        pattern_gen = SyntheticIdentityPatternGenerator(seed=42)
        identities = pattern_gen.generate_mixed_batch(
            total_count=50,
            pattern_distribution={
                PatternType.BUST_OUT: 0.20,
                PatternType.FRAUD_RING: 0.15,
                PatternType.IDENTITY_THEFT: 0.10,
            },
            base_intensity=0.7
        )
        
        assert len(identities) == 50
        
        # Step 2: Validate identities
        validator = IdentityValidator()
        for identity in identities:
            validator.add_identity(identity)
        
        validation_results = []
        for identity in identities:
            result = validator.validate(identity["identity_id"])
            validation_results.append(result)
        
        assert len(validation_results) == 50
        
        # Step 3: Detect bust-out schemes
        detector = BustOutDetector()
        bust_out_results = detector.detect_batch(identities)
        
        assert len(bust_out_results) == 50
        
        # Step 4: Analyze results
        # Count fraud patterns
        pattern_counts = {}
        for identity in identities:
            pattern = identity.get("pattern_injected", "none")
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        # Count detections
        high_risk_validation = sum(1 for r in validation_results if r.risk_score >= 70)
        bust_out_detected = sum(1 for r in bust_out_results if r.is_bust_out)
        
        # Verify detection rates
        assert high_risk_validation > 0  # Should detect some high-risk identities
        assert bust_out_detected > 0  # Should detect some bust-outs
        
        # Verify pattern distribution
        assert "bust_out" in pattern_counts
        assert "fraud_ring" in pattern_counts
        assert "identity_theft" in pattern_counts
        assert "none" in pattern_counts  # Clean identities
    
    def test_bust_out_detection_accuracy(self):
        """Test bust-out detection accuracy with known patterns."""
        # Generate identities with bust-out pattern
        pattern_gen = SyntheticIdentityPatternGenerator(seed=42)
        config = PatternConfig(
            pattern_type=PatternType.BUST_OUT,
            intensity=0.9,
            count=20
        )
        bust_out_identities = pattern_gen.generate_with_pattern(config)
        
        # Generate clean identities
        clean_gen = SyntheticIdentityGenerator(seed=123, config={
            "synthetic_probability": 0.0
        })
        clean_identities = clean_gen.generate_batch(20)
        
        # Detect bust-outs
        detector = BustOutDetector()
        bust_out_results = detector.detect_batch(bust_out_identities)
        clean_results = detector.detect_batch(clean_identities)
        
        # Calculate detection rates
        bust_out_detected = sum(1 for r in bust_out_results if r.is_bust_out)
        clean_false_positives = sum(1 for r in clean_results if r.is_bust_out)
        
        # Verify accuracy
        detection_rate = bust_out_detected / len(bust_out_identities)
        false_positive_rate = clean_false_positives / len(clean_identities)
        
        assert detection_rate >= 0.70  # At least 70% detection rate
        assert false_positive_rate <= 0.20  # At most 20% false positives
    
    def test_fraud_ring_detection_accuracy(self):
        """Test fraud ring detection accuracy."""
        # Generate fraud ring
        pattern_gen = SyntheticIdentityPatternGenerator(seed=42)
        config = PatternConfig(
            pattern_type=PatternType.FRAUD_RING,
            intensity=1.0,
            count=10,
            ring_size=10
        )
        ring_identities = pattern_gen.generate_with_pattern(config)
        
        # Validate identities
        validator = IdentityValidator()
        for identity in ring_identities:
            validator.add_identity(identity)
        
        # Check for shared attributes
        high_risk_count = 0
        for identity in ring_identities:
            result = validator.validate(identity["identity_id"])
            if result.risk_score >= 70:
                high_risk_count += 1
        
        # Most should be flagged as high risk
        detection_rate = high_risk_count / len(ring_identities)
        assert detection_rate >= 0.70  # At least 70% detection
    
    def test_identity_theft_detection(self):
        """Test identity theft pattern detection."""
        # Generate identity theft pattern
        pattern_gen = SyntheticIdentityPatternGenerator(seed=42)
        config = PatternConfig(
            pattern_type=PatternType.IDENTITY_THEFT,
            intensity=0.9,
            count=10
        )
        theft_identities = pattern_gen.generate_with_pattern(config)
        
        # Validate identities
        validator = IdentityValidator()
        for identity in theft_identities:
            validator.add_identity(identity)
        
        # All should share the stolen SSN
        ssns = [id["ssn"] for id in theft_identities]
        assert len(set(ssns)) == 1  # All share same SSN
        
        # All should be flagged
        flagged_count = 0
        for identity in theft_identities:
            result = validator.validate(identity["identity_id"])
            if result.risk_score >= 50:
                flagged_count += 1
        
        assert flagged_count >= 8  # At least 80% flagged


class TestCrossModuleIntegration:
    """Cross-module integration tests."""
    
    def test_generator_validator_integration(self):
        """Test generator and validator integration."""
        # Generate identities
        gen = SyntheticIdentityGenerator(seed=42, config={
            "synthetic_probability": 0.5
        })
        identities = gen.generate_batch(20)
        
        # Validate all
        validator = IdentityValidator()
        for identity in identities:
            validator.add_identity(identity)
        
        results = [validator.validate(id["identity_id"]) for id in identities]
        
        # All should have results
        assert len(results) == 20
        assert all(r.identity_id for r in results)
        assert all(0 <= r.authenticity_score <= 100 for r in results)
        assert all(0 <= r.risk_score <= 100 for r in results)
    
    def test_generator_detector_integration(self):
        """Test generator and detector integration."""
        # Generate identities
        gen = SyntheticIdentityGenerator(seed=42, config={
            "synthetic_probability": 1.0,
            "bust_out_probability": 0.5
        })
        identities = gen.generate_batch(20)
        
        # Detect bust-outs
        detector = BustOutDetector()
        results = detector.detect_batch(identities)
        
        # All should have results
        assert len(results) == 20
        assert all(r.identity_id for r in results)
        assert all(0 <= r.bust_out_score <= 100 for r in results)
        assert all(r.risk_level in ["low", "medium", "high", "critical"] for r in results)
    
    def test_pattern_generator_all_modules(self):
        """Test pattern generator with all detection modules."""
        # Generate mixed patterns
        pattern_gen = SyntheticIdentityPatternGenerator(seed=42)
        identities = pattern_gen.generate_mixed_batch(
            total_count=30,
            pattern_distribution={
                PatternType.BUST_OUT: 0.30,
                PatternType.FRAUD_RING: 0.20,
            },
            base_intensity=0.8
        )
        
        # Validate
        validator = IdentityValidator()
        for identity in identities:
            validator.add_identity(identity)
        validation_results = [validator.validate(id["identity_id"]) for id in identities]
        
        # Detect bust-outs
        detector = BustOutDetector()
        bust_out_results = detector.detect_batch(identities)
        
        # Verify all modules processed all identities
        assert len(validation_results) == 30
        assert len(bust_out_results) == 30
        
        # Verify some detections
        high_risk_validation = sum(1 for r in validation_results if r.risk_score >= 70)
        bust_out_detected = sum(1 for r in bust_out_results if r.is_bust_out)
        
        assert high_risk_validation > 0
        assert bust_out_detected > 0


class TestDeterminismAcrossModules:
    """Test determinism across all modules."""
    
    def test_end_to_end_determinism(self):
        """Test that entire pipeline is deterministic."""
        # Run 1
        pattern_gen1 = SyntheticIdentityPatternGenerator(seed=42)
        identities1 = pattern_gen1.generate_mixed_batch(
            total_count=20,
            pattern_distribution={PatternType.BUST_OUT: 0.50},
            base_intensity=0.7
        )
        
        validator1 = IdentityValidator()
        for identity in identities1:
            validator1.add_identity(identity)
        validation1 = [validator1.validate(id["identity_id"]) for id in identities1]
        
        detector1 = BustOutDetector()
        bust_out1 = detector1.detect_batch(identities1)
        
        # Run 2
        pattern_gen2 = SyntheticIdentityPatternGenerator(seed=42)
        identities2 = pattern_gen2.generate_mixed_batch(
            total_count=20,
            pattern_distribution={PatternType.BUST_OUT: 0.50},
            base_intensity=0.7
        )
        
        validator2 = IdentityValidator()
        for identity in identities2:
            validator2.add_identity(identity)
        validation2 = [validator2.validate(id["identity_id"]) for id in identities2]
        
        detector2 = BustOutDetector()
        bust_out2 = detector2.detect_batch(identities2)
        
        # Verify identical results
        assert len(identities1) == len(identities2)
        for id1, id2 in zip(identities1, identities2):
            assert id1["identity_id"] == id2["identity_id"]
            assert id1["credit_score"] == id2["credit_score"]
        
        for v1, v2 in zip(validation1, validation2):
            assert v1.identity_id == v2.identity_id
            assert v1.authenticity_score == v2.authenticity_score
            assert v1.risk_score == v2.risk_score
        
        for b1, b2 in zip(bust_out1, bust_out2):
            assert b1.identity_id == b2.identity_id
            assert b1.bust_out_score == b2.bust_out_score
            assert b1.risk_level == b2.risk_level


class TestPerformance:
    """Performance tests."""
    
    def test_large_batch_processing(self):
        """Test processing large batch of identities."""
        # Generate 100 identities
        pattern_gen = SyntheticIdentityPatternGenerator(seed=42)
        identities = pattern_gen.generate_mixed_batch(
            total_count=100,
            pattern_distribution={
                PatternType.BUST_OUT: 0.20,
                PatternType.FRAUD_RING: 0.15,
            },
            base_intensity=0.7
        )
        
        assert len(identities) == 100
        
        # Validate all
        validator = IdentityValidator()
        for identity in identities:
            validator.add_identity(identity)
        
        validation_results = []
        for identity in identities:
            result = validator.validate(identity["identity_id"])
            validation_results.append(result)
        
        assert len(validation_results) == 100
        
        # Detect bust-outs
        detector = BustOutDetector()
        bust_out_results = detector.detect_batch(identities)
        
        assert len(bust_out_results) == 100
        
        # Get statistics
        stats = detector.get_statistics(bust_out_results)
        assert stats["total_identities"] == 100
        assert "bust_out_count" in stats
        assert "average_bust_out_score" in stats


class TestReportGeneration:
    """Report generation tests."""
    
    def test_comprehensive_fraud_report(self):
        """Test generating comprehensive fraud report."""
        # Generate identities with patterns
        pattern_gen = SyntheticIdentityPatternGenerator(seed=42)
        identities = pattern_gen.generate_mixed_batch(
            total_count=50,
            pattern_distribution={
                PatternType.BUST_OUT: 0.20,
                PatternType.FRAUD_RING: 0.15,
                PatternType.IDENTITY_THEFT: 0.10,
            },
            base_intensity=0.7
        )
        
        # Run all detections
        validator = IdentityValidator()
        for identity in identities:
            validator.add_identity(identity)
        
        validation_results = [validator.validate(id["identity_id"]) for id in identities]
        
        detector = BustOutDetector()
        bust_out_results = detector.detect_batch(identities)
        
        # Generate report data
        report = {
            "total_identities": len(identities),
            "validation": {
                "high_risk": sum(1 for r in validation_results if r.risk_score >= 70),
                "medium_risk": sum(1 for r in validation_results if 40 <= r.risk_score < 70),
                "low_risk": sum(1 for r in validation_results if r.risk_score < 40),
            },
            "bust_out": {
                "detected": sum(1 for r in bust_out_results if r.is_bust_out),
                "critical": sum(1 for r in bust_out_results if r.risk_level == "critical"),
                "high": sum(1 for r in bust_out_results if r.risk_level == "high"),
            },
            "patterns": pattern_gen.get_pattern_summary(),
        }
        
        # Verify report structure
        assert report["total_identities"] == 50
        assert "validation" in report
        assert "bust_out" in report
        assert "patterns" in report
        
        # Verify detection counts
        assert report["validation"]["high_risk"] > 0
        assert report["bust_out"]["detected"] > 0

# Made with Bob
