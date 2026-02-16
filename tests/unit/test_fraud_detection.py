"""Tests for banking.fraud.fraud_detection module."""

import numpy as np
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

from banking.fraud.models import FraudAlert, FraudScore, HIGH_RISK_MERCHANTS


MODULE = "banking.fraud.fraud_detection"


@pytest.fixture
def mock_deps():
    with (
        patch(f"{MODULE}.DriverRemoteConnection") as mock_conn_cls,
        patch(f"{MODULE}.traversal") as mock_trav,
        patch(f"{MODULE}.EmbeddingGenerator") as mock_emb_cls,
        patch(f"{MODULE}.VectorSearchClient") as mock_vs_cls,
    ):
        mock_conn = MagicMock()
        mock_conn_cls.return_value = mock_conn

        mock_g = MagicMock()
        mock_trav.return_value.with_remote.return_value = mock_g

        mock_emb = MagicMock()
        mock_emb.dimensions = 384
        mock_emb_cls.return_value = mock_emb

        mock_vs = MagicMock()
        mock_vs.client.indices.exists.return_value = False
        mock_vs_cls.return_value = mock_vs

        yield {
            "conn_cls": mock_conn_cls,
            "conn": mock_conn,
            "traversal": mock_trav,
            "g": mock_g,
            "emb_cls": mock_emb_cls,
            "emb": mock_emb,
            "vs_cls": mock_vs_cls,
            "vs": mock_vs,
        }


@pytest.fixture
def detector(mock_deps):
    from banking.fraud.fraud_detection import FraudDetector
    return FraudDetector()


class TestFraudDetectorInit:
    def test_init_creates_index(self, mock_deps):
        from banking.fraud.fraud_detection import FraudDetector
        FraudDetector()
        mock_deps["vs"].create_vector_index.assert_called_once()

    def test_init_skips_existing_index(self, mock_deps):
        mock_deps["vs"].client.indices.exists.return_value = True
        from banking.fraud.fraud_detection import FraudDetector
        FraudDetector()
        mock_deps["vs"].create_vector_index.assert_not_called()

    def test_init_ssl(self, mock_deps):
        from banking.fraud.fraud_detection import FraudDetector
        d = FraudDetector(use_ssl=True)
        assert d.graph_url.startswith("wss://")

    def test_init_no_ssl(self, detector):
        assert detector.graph_url.startswith("ws://")


class TestConnectDisconnect:
    def test_connect(self, detector, mock_deps):
        detector.connect()
        mock_deps["conn_cls"].assert_called_once()
        assert detector._connection is not None

    def test_connect_already_connected(self, detector, mock_deps):
        detector._connection = MagicMock()
        detector.connect()
        mock_deps["conn_cls"].assert_not_called()

    def test_connect_circuit_breaker_open(self, detector):
        with patch.object(type(detector._breaker), "state", new_callable=lambda: property(lambda self: MagicMock(value="open"))):
            with pytest.raises(ConnectionError):
                detector.connect()

    def test_disconnect(self, detector):
        mock_conn = MagicMock()
        detector._connection = mock_conn
        detector._g = MagicMock()
        detector.disconnect()
        mock_conn.close.assert_called_once()
        assert detector._connection is None
        assert detector._g is None

    def test_disconnect_when_not_connected(self, detector):
        detector.disconnect()

    def test_get_traversal_connects(self, detector, mock_deps):
        result = detector._get_traversal()
        assert result is not None

    def test_context_manager(self, detector, mock_deps):
        with detector as d:
            assert d is detector
        assert detector._connection is None

    def test_exit_returns_false(self, detector, mock_deps):
        assert detector.__exit__(None, None, None) is False


class TestScoreTransaction:
    def test_score_low_risk(self, detector, mock_deps):
        g = mock_deps["g"]
        g.V.return_value.has.return_value.out_e.return_value.has.return_value.count.return_value.next.return_value = 0
        g.V.return_value.has.return_value.out_e.return_value.has.return_value.values.return_value.sum_.return_value.next.return_value = 0
        g.V.return_value.has.return_value.both.return_value.dedup.return_value.count.return_value.next.return_value = 0
        g.V.return_value.has.return_value.out_e.return_value.has.return_value.project.return_value.by.return_value.by.return_value.by.return_value.toList.return_value = []
        mock_deps["emb"].encode.return_value = [np.zeros(384)]
        mock_deps["vs"].search.return_value = []

        score = detector.score_transaction("tx1", "acc1", 50.0, "grocery store", "weekly groceries")
        assert isinstance(score, FraudScore)
        assert score.risk_level == "low"
        assert score.recommendation == "approve"

    def test_score_with_timestamp(self, detector, mock_deps):
        g = mock_deps["g"]
        g.V.return_value.has.return_value.out_e.return_value.has.return_value.count.return_value.next.return_value = 0
        g.V.return_value.has.return_value.out_e.return_value.has.return_value.values.return_value.sum_.return_value.next.return_value = 0
        g.V.return_value.has.return_value.both.return_value.dedup.return_value.count.return_value.next.return_value = 0
        g.V.return_value.has.return_value.out_e.return_value.has.return_value.project.return_value.by.return_value.by.return_value.by.return_value.toList.return_value = []
        mock_deps["emb"].encode.return_value = [np.zeros(384)]
        mock_deps["vs"].search.return_value = []

        ts = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        score = detector.score_transaction("tx2", "acc1", 50.0, "store", "desc", timestamp=ts)
        assert score.transaction_id == "tx2"

    def test_score_critical(self, detector, mock_deps):
        g = mock_deps["g"]
        g.V.return_value.has.return_value.out_e.return_value.has.return_value.count.return_value.next.return_value = 20
        g.V.return_value.has.return_value.out_e.return_value.has.return_value.values.return_value.sum_.return_value.next.return_value = 10000
        g.V.return_value.has.return_value.both.return_value.dedup.return_value.count.return_value.next.return_value = 100
        g.V.return_value.has.return_value.out_e.return_value.has.return_value.project.return_value.by.return_value.by.return_value.by.return_value.toList.return_value = []
        mock_deps["emb"].encode.return_value = [np.zeros(384)]
        mock_deps["vs"].search.return_value = []

        score = detector.score_transaction("tx3", "acc1", 9999, "crypto exchange", "buy bitcoin")
        assert score.overall_score >= 0.5


class TestCheckVelocity:
    def test_velocity_error(self, detector, mock_deps):
        mock_deps["g"].V.return_value.has.side_effect = Exception("err")
        result = detector._check_velocity("acc1", 100.0, datetime.now(timezone.utc))
        assert result == 0.0

    def test_velocity_high(self, detector, mock_deps):
        g = mock_deps["g"]
        g.V.return_value.has.return_value.out_e.return_value.has.return_value.count.return_value.next.return_value = 15
        g.V.return_value.has.return_value.out_e.return_value.has.return_value.values.return_value.sum_.return_value.next.return_value = 8000
        result = detector._check_velocity("acc1", 100.0, datetime.now(timezone.utc))
        assert result == 1.0


class TestCheckNetwork:
    def test_network_low(self, detector, mock_deps):
        mock_deps["g"].V.return_value.has.return_value.both.return_value.dedup.return_value.count.return_value.next.return_value = 5
        assert detector._check_network("acc1") == pytest.approx(0.1)

    def test_network_error(self, detector, mock_deps):
        mock_deps["g"].V.return_value.has.side_effect = Exception("err")
        assert detector._check_network("acc1") == 0.0


class TestCheckMerchant:
    def test_empty_merchant(self, detector):
        assert detector._check_merchant("") == 0.0

    def test_high_risk_merchant(self, detector, mock_deps):
        mock_deps["emb"].encode.return_value = [np.zeros(384)]
        mock_deps["vs"].search.return_value = []
        result = detector._check_merchant("Crypto Exchange")
        assert result > 0

    def test_merchant_with_history(self, detector, mock_deps):
        mock_deps["emb"].encode.return_value = [np.zeros(384)]
        mock_deps["vs"].search.return_value = [{"_score": 0.8}, {"_score": 0.7}]
        result = detector._check_merchant("suspicious store")
        assert result > 0

    def test_merchant_search_error(self, detector, mock_deps):
        mock_deps["emb"].encode.side_effect = Exception("err")
        assert detector._check_merchant("some merchant") == 0.0


class TestCheckBehavior:
    def test_no_history(self, detector, mock_deps):
        mock_deps["g"].V.return_value.has.return_value.out_e.return_value.has.return_value.project.return_value.by.return_value.by.return_value.by.return_value.toList.return_value = []
        assert detector._check_behavior("acc1", 100.0, "store", "desc") == 0.3

    def test_with_history(self, detector, mock_deps):
        txns = [{"amount": [100.0, 200.0, 150.0], "merchant": ["store A", "store B"], "description": ["food", "gas"]}]
        mock_deps["g"].V.return_value.has.return_value.out_e.return_value.has.return_value.project.return_value.by.return_value.by.return_value.by.return_value.toList.return_value = txns
        mock_deps["emb"].encode.return_value = np.array([[0.1] * 384, [0.2] * 384])
        result = detector._check_behavior("acc1", 10000.0, "new merchant", "unusual purchase")
        assert 0 <= result <= 1.0

    def test_zero_std(self, detector, mock_deps):
        txns = [{"amount": [100.0, 100.0], "merchant": [], "description": []}]
        mock_deps["g"].V.return_value.has.return_value.out_e.return_value.has.return_value.project.return_value.by.return_value.by.return_value.by.return_value.toList.return_value = txns
        result = detector._check_behavior("acc1", 200.0, "", "")
        assert result > 0

    def test_same_amount_zero_std(self, detector, mock_deps):
        txns = [{"amount": [100.0, 100.0], "merchant": [], "description": []}]
        mock_deps["g"].V.return_value.has.return_value.out_e.return_value.has.return_value.project.return_value.by.return_value.by.return_value.by.return_value.toList.return_value = txns
        result = detector._check_behavior("acc1", 100.0, "", "")
        assert 0 <= result <= 1.0

    def test_behavior_error(self, detector, mock_deps):
        mock_deps["g"].V.return_value.has.side_effect = Exception("err")
        assert detector._check_behavior("acc1", 100.0, "m", "d") == 0.2

    def test_semantic_low_similarity(self, detector, mock_deps):
        txns = [{"amount": [100.0], "merchant": ["store"], "description": ["old desc"]}]
        mock_deps["g"].V.return_value.has.return_value.out_e.return_value.has.return_value.project.return_value.by.return_value.by.return_value.by.return_value.toList.return_value = txns
        mock_deps["emb"].encode.side_effect = [np.array([[0.1] * 384]), np.array([[0.9] * 384])]
        result = detector._check_behavior("acc1", 100.0, "store", "new desc")
        assert 0 <= result <= 1.0

    def test_semantic_error(self, detector, mock_deps):
        txns = [{"amount": [100.0], "merchant": ["store"], "description": ["old desc"]}]
        mock_deps["g"].V.return_value.has.return_value.out_e.return_value.has.return_value.project.return_value.by.return_value.by.return_value.by.return_value.toList.return_value = txns
        mock_deps["emb"].encode.side_effect = Exception("encode fail")
        result = detector._check_behavior("acc1", 100.0, "store", "new desc")
        assert 0 <= result <= 1.0

    def test_merchant_frequency_zero(self, detector, mock_deps):
        merchants = ["store A"] * 100
        txns = [{"amount": [100.0] * 100, "merchant": merchants, "description": []}]
        mock_deps["g"].V.return_value.has.return_value.out_e.return_value.has.return_value.project.return_value.by.return_value.by.return_value.by.return_value.toList.return_value = txns
        result = detector._check_behavior("acc1", 100.0, "rare merchant", "")
        assert result > 0

    def test_merchant_frequency_low(self, detector, mock_deps):
        merchants = ["store A"] * 98 + ["rare"] * 2
        txns = [{"amount": [100.0] * 100, "merchant": merchants, "description": []}]
        mock_deps["g"].V.return_value.has.return_value.out_e.return_value.has.return_value.project.return_value.by.return_value.by.return_value.by.return_value.toList.return_value = txns
        result = detector._check_behavior("acc1", 100.0, "rare", "")
        assert 0 <= result <= 1.0


class TestDetectAccountTakeover:
    def test_no_transactions(self, detector):
        is_takeover, conf, indicators = detector.detect_account_takeover("acc1", [])
        assert not is_takeover
        assert conf == 0.0

    def test_normal_transactions(self, detector):
        txns = [{"amount": 100.0} for _ in range(10)]
        is_takeover, conf, indicators = detector.detect_account_takeover("acc1", txns)
        assert not is_takeover

    def test_suspicious_amount(self, detector):
        txns = [{"amount": 100.0} for _ in range(10)]
        txns.append({"amount": 500.0})
        is_takeover, conf, indicators = detector.detect_account_takeover("acc1", txns)
        assert "Unusually large transaction" in indicators


class TestFindSimilarFraudCases:
    def test_find_similar(self, detector, mock_deps):
        mock_deps["emb"].encode_for_search.return_value = np.zeros(384)
        mock_deps["vs"].search.return_value = [{"source": {"case_id": "c1"}}, {"source": {"case_id": "c2"}}]
        result = detector.find_similar_fraud_cases("suspicious tx", 5000.0)
        assert len(result) == 2

    def test_find_similar_error(self, detector, mock_deps):
        mock_deps["emb"].encode_for_search.side_effect = Exception("err")
        assert detector.find_similar_fraud_cases("desc", 100.0) == []


class TestGenerateAlert:
    def test_no_alert_low_score(self, detector, mock_deps):
        score = FraudScore("tx1", 0.1, 0.1, 0.1, 0.1, 0.1, "low", "approve")
        assert detector.generate_alert(score, {"description": "", "amount": 0}) is None

    def test_velocity_alert(self, detector, mock_deps):
        mock_deps["emb"].encode_for_search.return_value = np.zeros(384)
        mock_deps["vs"].search.return_value = []
        score = FraudScore("tx1", 0.8, 0.8, 0.3, 0.3, 0.3, "high", "review")
        alert = detector.generate_alert(score, {"description": "test", "amount": 5000, "account_id": "a1"})
        assert isinstance(alert, FraudAlert)
        assert alert.alert_type == "velocity"

    def test_network_alert(self, detector, mock_deps):
        mock_deps["emb"].encode_for_search.return_value = np.zeros(384)
        mock_deps["vs"].search.return_value = []
        score = FraudScore("tx1", 0.8, 0.3, 0.8, 0.3, 0.3, "high", "review")
        alert = detector.generate_alert(score, {"description": "", "amount": 0})
        assert alert.alert_type == "network"

    def test_merchant_alert(self, detector, mock_deps):
        mock_deps["emb"].encode_for_search.return_value = np.zeros(384)
        mock_deps["vs"].search.return_value = []
        score = FraudScore("tx1", 0.8, 0.3, 0.3, 0.8, 0.3, "high", "review")
        alert = detector.generate_alert(score, {"description": "", "amount": 0})
        assert alert.alert_type == "merchant"

    def test_behavioral_alert(self, detector, mock_deps):
        mock_deps["emb"].encode_for_search.return_value = np.zeros(384)
        mock_deps["vs"].search.return_value = []
        score = FraudScore("tx1", 0.6, 0.3, 0.3, 0.3, 0.8, "medium", "review")
        alert = detector.generate_alert(score, {"description": "", "amount": 0})
        assert alert.alert_type == "behavioral"

    def test_alert_all_risk_factors(self, detector, mock_deps):
        mock_deps["emb"].encode_for_search.return_value = np.zeros(384)
        mock_deps["vs"].search.return_value = []
        score = FraudScore("tx1", 0.9, 0.8, 0.8, 0.8, 0.8, "critical", "block")
        alert = detector.generate_alert(score, {"description": "", "amount": 0})
        assert len(alert.risk_factors) == 4
