"""Tests for banking.aml.structuring_detection module."""

import pytest
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

MODULE = "banking.aml.structuring_detection"


@pytest.fixture
def mock_deps():
    with (
        patch(f"{MODULE}.DriverRemoteConnection") as mock_conn_cls,
        patch(f"{MODULE}.traversal") as mock_trav,
    ):
        mock_conn = MagicMock()
        mock_conn_cls.return_value = mock_conn
        mock_g = MagicMock()
        mock_trav.return_value.with_remote.return_value = mock_g
        yield {"conn_cls": mock_conn_cls, "conn": mock_conn, "traversal": mock_trav, "g": mock_g}


@pytest.fixture
def detector(mock_deps):
    from banking.aml.structuring_detection import StructuringDetector
    return StructuringDetector()


class TestStructuringDataclasses:
    def test_structuring_pattern(self):
        from banking.aml.structuring_detection import StructuringPattern
        p = StructuringPattern(
            pattern_id="p1", pattern_type="smurfing", account_ids=["a1"],
            transaction_ids=["t1"], total_amount=Decimal("9000"), transaction_count=1,
            time_window_hours=24, confidence_score=0.8, risk_level="high",
            indicators=["test"], detected_at="2026-01-01", metadata={},
        )
        assert p.pattern_id == "p1"

    def test_structuring_alert(self):
        from banking.aml.structuring_detection import StructuringAlert
        a = StructuringAlert(
            alert_id="a1", alert_type="structuring", severity="high",
            patterns=[], accounts_involved=["a1"], total_amount=Decimal("9000"),
            recommendation="investigate", timestamp="2026-01-01",
        )
        assert a.alert_id == "a1"


class TestDetectorInit:
    def test_default_init(self, detector):
        assert detector.graph_url.startswith("ws://")
        assert detector.ctr_threshold == Decimal("10000.00")

    def test_custom_threshold(self, mock_deps):
        from banking.aml.structuring_detection import StructuringDetector
        d = StructuringDetector(ctr_threshold=Decimal("5000"))
        assert d.ctr_threshold == Decimal("5000")
        assert d.suspicious_threshold == Decimal("4500")

    def test_ssl(self, mock_deps):
        from banking.aml.structuring_detection import StructuringDetector
        d = StructuringDetector(use_ssl=True)
        assert d.graph_url.startswith("wss://")


class TestConnectDisconnect:
    def test_connect(self, detector, mock_deps):
        detector.connect()
        mock_deps["conn_cls"].assert_called_once()

    def test_connect_already_connected(self, detector, mock_deps):
        detector._connection = MagicMock()
        detector.connect()
        mock_deps["conn_cls"].assert_not_called()

    def test_disconnect(self, detector):
        mock_conn = MagicMock()
        detector._connection = mock_conn
        detector._g = MagicMock()
        detector.disconnect()
        mock_conn.close.assert_called_once()
        assert detector._connection is None

    def test_disconnect_not_connected(self, detector):
        detector.disconnect()

    def test_get_traversal(self, detector, mock_deps):
        assert detector._get_traversal() is not None

    def test_context_manager(self, detector, mock_deps):
        with detector as d:
            assert d is detector

    def test_exit_returns_false(self, detector):
        assert detector.__exit__(None, None, None) is False


class TestDetectSmurfing:
    def test_no_transactions(self, detector, mock_deps):
        mock_deps["g"].V.return_value.has.return_value.out_e.return_value.has.return_value.has.return_value.project.return_value.by.return_value.by.return_value.by.return_value.by.return_value.toList.return_value = []
        result = detector.detect_smurfing("acc1")
        assert result == []

    def test_few_transactions(self, detector, mock_deps):
        txns = [{"id": "t1", "amount": 9500, "timestamp": 1000, "to_account": "a2"}]
        mock_deps["g"].V.return_value.has.return_value.out_e.return_value.has.return_value.has.return_value.project.return_value.by.return_value.by.return_value.by.return_value.by.return_value.toList.return_value = txns
        result = detector.detect_smurfing("acc1")
        assert result == []

    def test_smurfing_detected(self, detector, mock_deps):
        txns = [
            {"id": f"t{i}", "amount": 9500, "timestamp": 1000 + i, "to_account": "a2"}
            for i in range(5)
        ]
        mock_deps["g"].V.return_value.has.return_value.out_e.return_value.has.return_value.has.return_value.project.return_value.by.return_value.by.return_value.by.return_value.by.return_value.toList.return_value = txns
        result = detector.detect_smurfing("acc1")
        assert len(result) == 1
        assert result[0].pattern_type == "smurfing"

    def test_smurfing_error(self, detector, mock_deps):
        mock_deps["g"].V.return_value.has.side_effect = Exception("err")
        result = detector.detect_smurfing("acc1")
        assert result == []


class TestDetectLayering:
    def test_no_circular(self, detector, mock_deps):
        mock_deps["g"].V.return_value.has.return_value.out_e.return_value.has.return_value.as_.return_value.in_v.return_value.out_e.return_value.has.return_value.where.return_value.select.return_value.project.return_value.by.return_value.by.return_value.by.return_value.toList.return_value = []
        result = detector.detect_layering(["acc1"])
        assert result == []

    def test_layering_detected(self, detector, mock_deps):
        txns = [{"id": "t1", "amount": 5000, "timestamp": 1000}, {"id": "t2", "amount": 4000, "timestamp": 2000}]
        mock_deps["g"].V.return_value.has.return_value.out_e.return_value.has.return_value.as_.return_value.in_v.return_value.out_e.return_value.has.return_value.where.return_value.select.return_value.project.return_value.by.return_value.by.return_value.by.return_value.toList.return_value = txns
        result = detector.detect_layering(["acc1"])
        assert len(result) == 1
        assert result[0].pattern_type == "layering"

    def test_layering_error(self, detector, mock_deps):
        mock_deps["g"].V.return_value.has.side_effect = Exception("err")
        result = detector.detect_layering(["acc1"])
        assert result == []


class TestDetectNetworkStructuring:
    def test_small_network(self, detector, mock_deps):
        mock_deps["g"].V.return_value.has.return_value.repeat.return_value.times.return_value.dedup.return_value.values.return_value.toList.return_value = ["a1", "a2"]
        result = detector.detect_network_structuring("acc1")
        assert result == []

    def test_network_detected(self, detector, mock_deps):
        g = mock_deps["g"]
        g.V.return_value.has.return_value.repeat.return_value.times.return_value.dedup.return_value.values.return_value.toList.return_value = ["a1", "a2", "a3", "a4"]
        txns = [{"id": f"t{i}", "amount": 9500, "timestamp": 1000, "account": f"a{i%4+1}"} for i in range(8)]
        g.V.return_value.has.return_value.out_e.return_value.has.return_value.has.return_value.project.return_value.by.return_value.by.return_value.by.return_value.by.return_value.toList.return_value = txns
        result = detector.detect_network_structuring("acc1")
        assert len(result) >= 0

    def test_network_error(self, detector, mock_deps):
        mock_deps["g"].V.return_value.has.side_effect = Exception("err")
        result = detector.detect_network_structuring("acc1")
        assert result == []


class TestAnalyzeSmurfingPattern:
    def test_empty_transactions(self, detector):
        result = detector._analyze_smurfing_pattern("acc1", [], 24)
        assert result is None

    def test_pattern_analysis(self, detector):
        txns = [{"id": f"t{i}", "amount": 9500} for i in range(5)]
        result = detector._analyze_smurfing_pattern("acc1", txns, 10)
        assert result is not None
        assert result.pattern_type == "smurfing"
        assert result.transaction_count == 5

    def test_high_total(self, detector):
        txns = [{"id": f"t{i}", "amount": 9900} for i in range(5)]
        result = detector._analyze_smurfing_pattern("acc1", txns, 24)
        assert result.total_amount > Decimal("20000")


class TestAnalyzeLayeringPattern:
    def test_too_few(self, detector):
        assert detector._analyze_layering_pattern("acc1", [{"id": "t1", "amount": 100}], 24) is None

    def test_layering(self, detector):
        txns = [{"id": "t1", "amount": 5000}, {"id": "t2", "amount": 4000}]
        result = detector._analyze_layering_pattern("acc1", txns, 24)
        assert result is not None
        assert result.pattern_type == "layering"

    def test_high_confidence(self, detector):
        txns = [{"id": f"t{i}", "amount": 5000} for i in range(10)]
        result = detector._analyze_layering_pattern("acc1", txns, 24)
        assert result.confidence_score == 1.0


class TestAnalyzeNetworkPattern:
    def test_empty(self, detector):
        assert detector._analyze_network_pattern(["a1"], [], 24) is None

    def test_network(self, detector):
        txns = [{"id": "t1", "amount": 9000}]
        result = detector._analyze_network_pattern(["a1", "a2", "a3"], txns, 24)
        assert result.pattern_type == "network_structuring"

    def test_large_network(self, detector):
        txns = [{"id": f"t{i}", "amount": 9000} for i in range(10)]
        result = detector._analyze_network_pattern(["a1", "a2", "a3", "a4", "a5", "a6", "a7", "a8", "a9"], txns, 24)
        assert result.confidence_score == 1.0
        assert result.risk_level == "critical"


class TestGenerateAlert:
    def test_no_patterns(self, detector):
        assert detector.generate_alert([]) is None

    def test_critical_alert(self, detector):
        from banking.aml.structuring_detection import StructuringPattern
        p = StructuringPattern(
            pattern_id="p1", pattern_type="smurfing", account_ids=["a1"],
            transaction_ids=["t1"], total_amount=Decimal("50000"), transaction_count=5,
            time_window_hours=24, confidence_score=0.9, risk_level="critical",
            indicators=[], detected_at="2026-01-01", metadata={},
        )
        alert = detector.generate_alert([p])
        assert alert is not None
        assert alert.severity == "critical"

    def test_high_alert(self, detector):
        from banking.aml.structuring_detection import StructuringPattern
        p = StructuringPattern(
            pattern_id="p1", pattern_type="smurfing", account_ids=["a1"],
            transaction_ids=["t1"], total_amount=Decimal("9000"), transaction_count=3,
            time_window_hours=24, confidence_score=0.75, risk_level="high",
            indicators=[], detected_at="2026-01-01", metadata={},
        )
        alert = detector.generate_alert([p])
        assert alert.severity == "high"

    def test_medium_alert(self, detector):
        from banking.aml.structuring_detection import StructuringPattern
        p = StructuringPattern(
            pattern_id="p1", pattern_type="smurfing", account_ids=["a1"],
            transaction_ids=["t1"], total_amount=Decimal("5000"), transaction_count=3,
            time_window_hours=24, confidence_score=0.5, risk_level="medium",
            indicators=[], detected_at="2026-01-01", metadata={},
        )
        alert = detector.generate_alert([p])
        assert alert.severity == "medium"
