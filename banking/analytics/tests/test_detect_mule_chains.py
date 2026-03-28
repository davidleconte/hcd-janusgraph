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
