"""
Unit Tests for APP Fraud Mule-Chain Detector
============================================

Tests for additive FR-030 mule-chain analytics:
- Detector initialization and connection behavior
- Rapid-transfer chain qualification logic
- Deterministic alert ID generation
- Risk scoring boundaries
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

import pytest

from banking.analytics.detect_mule_chains import MuleChainAlert, MuleChainDetector


class TestMuleChainDetectorInitialization:
    """Test MuleChainDetector initialization and connection handling."""

    def test_init_default_url(self):
        """Test default JanusGraph URL and empty alert list."""
        detector = MuleChainDetector()
        assert detector.url == "ws://localhost:18182/gremlin"
        assert detector.client is None
        assert detector.alerts == []

    @patch("banking.analytics.detect_mule_chains.client.Client")
    def test_connect_success(self, mock_client_class):
        """Test successful connection creation."""
        detector = MuleChainDetector()
        detector.connect()

        assert detector.client is not None
        mock_client_class.assert_called_once()

    def test_close_with_client(self):
        """Test closing detector with active client."""
        detector = MuleChainDetector()
        detector.client = Mock()

        detector.close()

        detector.client.close.assert_called_once()

    def test_query_without_connection_raises(self):
        """Test _query guard when connect() has not been called."""
        detector = MuleChainDetector()

        with pytest.raises(RuntimeError, match="Not connected"):
            detector._query("g.V().count()")


class TestMuleChainAlertConstruction:
    """Test path-to-alert conversion and filtering rules."""

    @staticmethod
    def _tx(tx_id: str, amount: float, when: datetime) -> dict:
        return {
            "transaction_id": tx_id,
            "amount": amount,
            "transaction_date": when.isoformat(),
        }

    def test_build_alert_for_valid_rapid_chain(self):
        """Test valid rapid chain produces a MuleChainAlert."""
        detector = MuleChainDetector()
        base = datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)

        path = {
            "accounts": ["A-VICTIM", "A-MULE-1", "A-MULE-2", "A-CASHOUT"],
            "transactions": [
                self._tx("TX-1", 10000.0, base),
                self._tx("TX-2", 9800.0, base + timedelta(minutes=8)),
                self._tx("TX-3", 9500.0, base + timedelta(minutes=18)),
            ],
        }

        alert = detector._build_alert_from_path(path, min_hops=3, max_hop_minutes=60)

        assert isinstance(alert, MuleChainAlert)
        assert alert.victim_account_id == "A-VICTIM"
        assert alert.mule_account_ids == ["A-MULE-1", "A-MULE-2"]
        assert alert.cash_out_account_id == "A-CASHOUT"
        assert alert.hop_count == 3
        assert alert.transaction_ids == ["TX-1", "TX-2", "TX-3"]
        assert alert.total_value == pytest.approx(29300.0)
        assert alert.average_hop_minutes == pytest.approx(9.0)
        assert alert.alert_id.startswith("APP-MULE-")

    def test_build_alert_rejects_slow_hops(self):
        """Test chains with hop latency above threshold are filtered out."""
        detector = MuleChainDetector()
        base = datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)

        path = {
            "accounts": ["A1", "A2", "A3", "A4"],
            "transactions": [
                self._tx("TX-1", 1000.0, base),
                self._tx("TX-2", 900.0, base + timedelta(minutes=30)),
                self._tx("TX-3", 850.0, base + timedelta(minutes=120)),
            ],
        }

        alert = detector._build_alert_from_path(path, min_hops=3, max_hop_minutes=60)
        assert alert is None

    def test_build_alert_is_deterministic_for_same_path(self):
        """Test deterministic alert ID for identical path content."""
        detector = MuleChainDetector()
        base = datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)

        path = {
            "accounts": ["V", "M1", "M2", "C"],
            "transactions": [
                self._tx("T1", 4000.0, base),
                self._tx("T2", 3800.0, base + timedelta(minutes=5)),
                self._tx("T3", 3600.0, base + timedelta(minutes=11)),
            ],
        }

        alert_one = detector._build_alert_from_path(path, min_hops=3, max_hop_minutes=60)
        alert_two = detector._build_alert_from_path(path, min_hops=3, max_hop_minutes=60)

        assert alert_one is not None and alert_two is not None
        assert alert_one.alert_id == alert_two.alert_id


class TestMuleChainDetectorScan:
    """Test detector scan behavior with mocked query results."""

    def test_detect_mule_chains_returns_matching_alerts(self):
        """Test scan returns only qualifying chains."""
        detector = MuleChainDetector()
        base = datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)

        valid_path = {
            "accounts": ["A0", "A1", "A2", "A3"],
            "transactions": [
                {"transaction_id": "X1", "amount": 2000.0, "transaction_date": base.isoformat()},
                {
                    "transaction_id": "X2",
                    "amount": 1800.0,
                    "transaction_date": (base + timedelta(minutes=4)).isoformat(),
                },
                {
                    "transaction_id": "X3",
                    "amount": 1600.0,
                    "transaction_date": (base + timedelta(minutes=9)).isoformat(),
                },
            ],
        }
        invalid_path = {
            "accounts": ["B0", "B1", "B2", "B3"],
            "transactions": [
                {"transaction_id": "Y1", "amount": 1000.0, "transaction_date": base.isoformat()},
                {
                    "transaction_id": "Y2",
                    "amount": 900.0,
                    "transaction_date": (base + timedelta(minutes=70)).isoformat(),
                },
                {
                    "transaction_id": "Y3",
                    "amount": 800.0,
                    "transaction_date": (base + timedelta(minutes=130)).isoformat(),
                },
            ],
        }

        detector._query = Mock(return_value=[valid_path, invalid_path])

        alerts = detector.detect_mule_chains(min_hops=3, max_hop_minutes=60)

        assert len(alerts) == 1
        assert alerts[0].victim_account_id == "A0"
        assert len(detector.alerts) == 1

    def test_detect_mule_chains_handles_query_exception(self):
        """Test scan failure returns empty alert list and does not raise."""
        detector = MuleChainDetector()
        detector._query = Mock(side_effect=Exception("query failure"))

        alerts = detector.detect_mule_chains()

        assert alerts == []


class TestMuleChainRecordsAPI:
    """Test notebook-ready records API behavior and deterministic ordering."""

    def test_detect_mule_chains_as_records_schema(self):
        """Test records API emits required business evidence fields."""
        detector = MuleChainDetector()
        alert = MuleChainAlert(
            alert_id="APP-MULE-abcdef123456",
            victim_account_id="A-VICTIM",
            mule_account_ids=["A-MULE-1", "A-MULE-2"],
            cash_out_account_id="A-CASHOUT",
            transaction_ids=["TX-1", "TX-2", "TX-3"],
            hop_count=3,
            total_value=29300.0,
            average_hop_minutes=9.1234,
            risk_score=0.87654,
            indicators=["rapid hops"],
            details={"source": "unit-test"},
        )
        detector.detect_mule_chains = Mock(return_value=[alert])

        records = detector.detect_mule_chains_as_records()

        assert len(records) == 1
        record = records[0]
        assert set(record.keys()) == {
            "alert_id",
            "victim_account_id",
            "mule_account_ids",
            "cash_out_account_id",
            "hop_count",
            "total_value",
            "average_hop_minutes",
            "risk_score",
            "reason_codes",
            "rationale",
            "evidence_summary",
        }
        assert record["alert_id"] == "APP-MULE-abcdef123456"
        assert record["victim_account_id"] == "A-VICTIM"
        assert record["mule_account_ids"] == ["A-MULE-1", "A-MULE-2"]
        assert record["cash_out_account_id"] == "A-CASHOUT"
        assert record["hop_count"] == 3
        assert record["total_value"] == pytest.approx(29300.0)
        assert record["average_hop_minutes"] == pytest.approx(9.12)
        assert record["risk_score"] == pytest.approx(0.8765)
        assert record["reason_codes"] == [
            "APP_MULE_CHAIN",
            "RAPID_TRANSFER_VELOCITY",
            "MULTI_HOP_CASH_OUT_PATH",
        ]
        assert "Funds traversed 3 hops" in record["rationale"]
        assert "Victim=A-VICTIM" in record["evidence_summary"]

    def test_detect_mule_chains_as_records_deterministic_sort(self):
        """Test records are deterministically sorted by alert_id then descending risk_score."""
        detector = MuleChainDetector()
        alert_b = MuleChainAlert(
            alert_id="APP-MULE-bbbbbbbbbbbb",
            victim_account_id="V-B",
            mule_account_ids=["M-B1"],
            cash_out_account_id="C-B",
            transaction_ids=["T-B1", "T-B2", "T-B3"],
            hop_count=3,
            total_value=11000.0,
            average_hop_minutes=8.0,
            risk_score=0.7,
            indicators=[],
            details={},
        )
        alert_a_low = MuleChainAlert(
            alert_id="APP-MULE-aaaaaaaaaaaa",
            victim_account_id="V-A2",
            mule_account_ids=["M-A2"],
            cash_out_account_id="C-A2",
            transaction_ids=["T-A4", "T-A5", "T-A6"],
            hop_count=3,
            total_value=9000.0,
            average_hop_minutes=12.0,
            risk_score=0.4,
            indicators=[],
            details={},
        )
        alert_a_high = MuleChainAlert(
            alert_id="APP-MULE-aaaaaaaaaaaa",
            victim_account_id="V-A1",
            mule_account_ids=["M-A1"],
            cash_out_account_id="C-A1",
            transaction_ids=["T-A1", "T-A2", "T-A3"],
            hop_count=3,
            total_value=15000.0,
            average_hop_minutes=7.0,
            risk_score=0.9,
            indicators=[],
            details={},
        )
        detector.detect_mule_chains = Mock(return_value=[alert_b, alert_a_low, alert_a_high])

        records = detector.detect_mule_chains_as_records()

        assert [record["alert_id"] for record in records] == [
            "APP-MULE-aaaaaaaaaaaa",
            "APP-MULE-aaaaaaaaaaaa",
            "APP-MULE-bbbbbbbbbbbb",
        ]
        assert [record["risk_score"] for record in records] == [0.9, 0.4, 0.7]
