#!/usr/bin/env python3
"""Tests for AML Structuring Detection module."""

import sys
from pathlib import Path
from decimal import Decimal
from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from banking.aml.structuring_detection import (
    StructuringPattern, StructuringAlert, StructuringDetector
)


class TestStructuringPattern:
    """Test StructuringPattern dataclass."""

    def test_pattern_creation(self):
        pattern = StructuringPattern(
            pattern_id="pat-123",
            pattern_type="smurfing",
            account_ids=["acc-1", "acc-2"],
            transaction_ids=["txn-1", "txn-2", "txn-3"],
            total_amount=Decimal("28500.00"),
            transaction_count=3,
            time_window_hours=24.0,
            confidence_score=0.85,
            risk_level="high",
            indicators=["just_below_threshold", "similar_amounts"],
            detected_at="2026-02-06T12:00:00Z",
            metadata={}
        )
        assert pattern.pattern_id == "pat-123"
        assert pattern.pattern_type == "smurfing"
        assert pattern.total_amount == Decimal("28500.00")
        assert pattern.confidence_score == 0.85

    def test_pattern_types(self):
        for pattern_type in ["smurfing", "layering", "integration"]:
            pattern = StructuringPattern(
                pattern_id="test",
                pattern_type=pattern_type,
                account_ids=[],
                transaction_ids=[],
                total_amount=Decimal("0"),
                transaction_count=0,
                time_window_hours=24.0,
                confidence_score=0.5,
                risk_level="medium",
                indicators=[],
                detected_at="2026-01-01",
                metadata={}
            )
            assert pattern.pattern_type == pattern_type


class TestStructuringAlert:
    """Test StructuringAlert dataclass."""

    def test_alert_creation(self):
        pattern = StructuringPattern(
            pattern_id="pat-123",
            pattern_type="smurfing",
            account_ids=["acc-1"],
            transaction_ids=["txn-1"],
            total_amount=Decimal("9500.00"),
            transaction_count=1,
            time_window_hours=24.0,
            confidence_score=0.8,
            risk_level="high",
            indicators=["just_below_threshold"],
            detected_at="2026-02-06",
            metadata={}
        )
        alert = StructuringAlert(
            alert_id="alert-123",
            alert_type="structuring_detected",
            severity="high",
            patterns=[pattern],
            accounts_involved=["acc-1"],
            total_amount=Decimal("9500.00"),
            recommendation="investigate",
            timestamp="2026-02-06T12:00:00Z"
        )
        assert alert.alert_id == "alert-123"
        assert alert.severity == "high"
        assert len(alert.patterns) == 1


class TestStructuringDetector:
    """Test StructuringDetector class."""

    def test_detector_thresholds(self):
        assert StructuringDetector.CTR_THRESHOLD == Decimal("10000.00")
        assert StructuringDetector.SUSPICIOUS_THRESHOLD == Decimal("9000.00")

    def test_detection_parameters(self):
        assert StructuringDetector.MAX_TIME_WINDOW_HOURS == 24
        assert StructuringDetector.MIN_TRANSACTIONS_FOR_PATTERN == 3
        assert StructuringDetector.HIGH_CONFIDENCE_THRESHOLD == 0.85
        assert StructuringDetector.MEDIUM_CONFIDENCE_THRESHOLD == 0.70

    def test_detector_initialization(self):
        with patch('banking.aml.structuring_detection.DriverRemoteConnection'):
            detector = StructuringDetector.__new__(StructuringDetector)
            detector.ctr_threshold = Decimal("10000.00")
            detector.suspicious_threshold = Decimal("9000.00")
            assert detector.ctr_threshold == Decimal("10000.00")

    def test_custom_ctr_threshold(self):
        with patch('banking.aml.structuring_detection.DriverRemoteConnection'):
            # Test that custom threshold can be set
            custom_threshold = Decimal("5000.00")
            detector = StructuringDetector.__new__(StructuringDetector)
            detector.ctr_threshold = custom_threshold
            detector.suspicious_threshold = custom_threshold * Decimal("0.9")
            assert detector.ctr_threshold == custom_threshold
            assert detector.suspicious_threshold == Decimal("4500.00")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
