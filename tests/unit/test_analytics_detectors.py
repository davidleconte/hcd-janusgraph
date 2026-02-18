"""Tests for banking.analytics modules using mocks."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from banking.analytics.aml_structuring_detector import (
    CTR_THRESHOLD,
    STRUCTURING_THRESHOLD,
    SUSPICIOUS_TX_COUNT,
    AMLStructuringDetector,
)
from banking.analytics.detect_insider_trading import (
    CorporateEvent,
    InsiderTradingAlert,
    InsiderTradingDetector,
    TradeCluster,
)
from banking.analytics.detect_tbml import (
    PriceAnomaly,
    TBMLAlert,
    TBMLDetector,
)


class TestAMLStructuringDetectorInit:
    def test_init_default(self):
        detector = AMLStructuringDetector()
        assert detector.url == "ws://localhost:18182/gremlin"
        assert detector.client is None
        assert "high_risk_accounts" in detector.findings
        assert "suspicious_transactions" in detector.findings

    def test_init_custom_url(self):
        detector = AMLStructuringDetector(url="ws://custom:8182/gremlin")
        assert detector.url == "ws://custom:8182/gremlin"

    def test_close_no_client(self):
        detector = AMLStructuringDetector()
        detector.close()

    def test_close_with_client(self):
        detector = AMLStructuringDetector()
        detector.client = MagicMock()
        detector.close()
        detector.client.close.assert_called_once()

    def test_connect(self):
        detector = AMLStructuringDetector()
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.all.return_value.result.return_value = [100]
        mock_client.submit.return_value = mock_result
        with patch(
            "banking.analytics.aml_structuring_detector.client.Client", return_value=mock_client
        ):
            detector.connect()
        assert detector.client is not None

    def test_query(self):
        detector = AMLStructuringDetector()
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.all.return_value.result.return_value = [42]
        mock_client.submit.return_value = mock_result
        detector.client = mock_client
        result = detector._query("g.V().count()")
        assert result == [42]

    def test_analyze_transaction_amounts_empty(self):
        detector = AMLStructuringDetector()
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.all.return_value.result.return_value = []
        mock_client.submit.return_value = mock_result
        detector.client = mock_client
        result = detector.analyze_transaction_amounts()
        assert result == {}

    def test_analyze_transaction_amounts_with_data(self):
        detector = AMLStructuringDetector()
        amounts = [500, 1500, 5500, 9500, 9800, 15000, 200, 8000, 9999, 3000]
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.all.return_value.result.return_value = amounts
        mock_client.submit.return_value = mock_result
        detector.client = mock_client
        result = detector.analyze_transaction_amounts()
        assert result["total_transactions"] == 10
        assert result["total_amount"] == sum(amounts)
        assert result["near_threshold_count"] >= 2
        assert "distribution" in result

    def test_identify_high_volume_accounts(self):
        detector = AMLStructuringDetector()
        mock_results = [
            {"account_id": "ACC-001", "sent": 15, "received": 10},
            {"account_id": "ACC-002", "sent": 3, "received": 2},
            {"account_id": "ACC-003", "sent": 25, "received": 5},
        ]
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.all.return_value.result.return_value = mock_results
        mock_client.submit.return_value = mock_result
        detector.client = mock_client
        result = detector.identify_high_volume_accounts()
        assert len(result) >= 1
        high_risk = [r for r in result if r["risk_level"] == "HIGH"]
        assert len(high_risk) >= 1

    def test_detect_structuring_patterns(self):
        detector = AMLStructuringDetector()
        mock_results = [{"ACC-001": 5, "ACC-002": 3}]
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.all.return_value.result.return_value = mock_results
        mock_client.submit.return_value = mock_result
        detector.client = mock_client
        result = detector.detect_structuring_patterns()
        assert len(result) >= 1
        assert result[0]["pattern"] == "STRUCTURING"


class TestAMLConstants:
    def test_ctr_threshold(self):
        assert CTR_THRESHOLD == 10000.0

    def test_structuring_threshold(self):
        assert STRUCTURING_THRESHOLD == 9500.0

    def test_suspicious_tx_count(self):
        assert SUSPICIOUS_TX_COUNT == 3


class TestInsiderTradingDetectorInit:
    def test_init_default(self):
        detector = InsiderTradingDetector()
        assert detector.url == "ws://localhost:18182/gremlin"
        assert detector.client is None
        assert detector.alerts == []
        assert detector.corporate_events == {}

    def test_init_custom_url(self):
        detector = InsiderTradingDetector(url="ws://custom:8182/gremlin")
        assert detector.url == "ws://custom:8182/gremlin"

    def test_thresholds(self):
        assert InsiderTradingDetector.PRE_ANNOUNCEMENT_WINDOW_DAYS == 14
        assert InsiderTradingDetector.VOLUME_SPIKE_THRESHOLD == 2.5
        assert InsiderTradingDetector.PRICE_MOVEMENT_THRESHOLD == 0.05
        assert InsiderTradingDetector.COORDINATION_TIME_WINDOW_HOURS == 4
        assert InsiderTradingDetector.MIN_SUSPICIOUS_TRADES == 3

    def test_close_no_client(self):
        detector = InsiderTradingDetector()
        detector.close()

    def test_close_with_client(self):
        detector = InsiderTradingDetector()
        detector.client = MagicMock()
        detector.close()
        detector.client.close.assert_called_once()

    def test_connect(self):
        detector = InsiderTradingDetector()
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.all.return_value.result.return_value = [50]
        mock_client.submit.return_value = mock_result
        with patch(
            "banking.analytics.detect_insider_trading.client.Client", return_value=mock_client
        ):
            detector.connect()
        assert detector.client is not None

    def test_detect_timing_patterns_no_events(self):
        detector = InsiderTradingDetector()
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.all.return_value.result.return_value = []
        mock_client.submit.return_value = mock_result
        detector.client = mock_client
        alerts = detector.detect_timing_patterns()
        assert isinstance(alerts, list)

    def test_detect_timing_patterns_with_events(self):
        detector = InsiderTradingDetector()
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.all.return_value.result.return_value = [
            {
                "trade_id": "T-1",
                "trader_id": "P-1",
                "symbol": "ACME",
                "side": "buy",
                "quantity": 1000,
                "price": 50.0,
                "total_value": 50000.0,
                "trade_date": "2026-01-10",
                "trader_info": {},
            },
            {
                "trade_id": "T-2",
                "trader_id": "P-2",
                "symbol": "ACME",
                "side": "buy",
                "quantity": 500,
                "price": 51.0,
                "total_value": 25500.0,
                "trade_date": "2026-01-11",
                "trader_info": {},
            },
            {
                "trade_id": "T-3",
                "trader_id": "P-1",
                "symbol": "ACME",
                "side": "buy",
                "quantity": 800,
                "price": 49.0,
                "total_value": 39200.0,
                "trade_date": "2026-01-12",
                "trader_info": {},
            },
        ]
        mock_client.submit.return_value = mock_result
        detector.client = mock_client
        events = [
            CorporateEvent(
                event_id="E-1",
                company_id="C-1",
                symbol="ACME",
                event_type="earnings",
                announcement_date=datetime(2026, 1, 20, tzinfo=timezone.utc),
                impact="positive",
                price_change_percent=15.0,
            )
        ]
        alerts = detector.detect_timing_patterns(corporate_events=events)
        assert isinstance(alerts, list)


class TestInsiderTradingAlert:
    def test_creation(self):
        alert = InsiderTradingAlert(
            alert_id="IT-001",
            alert_type="timing",
            severity="high",
            traders=["P-1", "P-2"],
            trades=["T-1", "T-2"],
            symbol="ACME",
            total_value=75000.0,
            risk_score=0.85,
            indicators=["pre-announcement trading"],
            timestamp=datetime.now(timezone.utc),
            details={},
        )
        assert alert.alert_id == "IT-001"
        assert alert.risk_score == 0.85
        assert len(alert.traders) == 2


class TestTradeCluster:
    def test_creation(self):
        cluster = TradeCluster(
            trades=[{"id": "T-1"}],
            symbol="ACME",
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            total_volume=1000,
            total_value=50000.0,
        )
        assert cluster.symbol == "ACME"
        assert cluster.total_volume == 1000


class TestCorporateEvent:
    def test_creation(self):
        event = CorporateEvent(
            event_id="E-1",
            company_id="C-1",
            symbol="ACME",
            event_type="earnings",
            announcement_date=datetime.now(timezone.utc),
            impact="positive",
            price_change_percent=10.0,
        )
        assert event.symbol == "ACME"
        assert event.impact == "positive"


class TestTBMLDetectorInit:
    def test_init_default(self):
        detector = TBMLDetector()
        assert detector.url == "ws://localhost:18182/gremlin"
        assert detector.client is None
        assert detector.alerts == []
        assert detector.market_prices == {}

    def test_thresholds(self):
        assert TBMLDetector.PRICE_DEVIATION_THRESHOLD == 0.20
        assert TBMLDetector.CIRCULAR_LOOP_MAX_DEPTH == 5
        assert TBMLDetector.MIN_LOOP_VALUE == 50000.0

    def test_shell_company_indicators(self):
        indicators = TBMLDetector.SHELL_COMPANY_INDICATORS
        assert "low_employees" in indicators
        assert "recent_incorporation_days" in indicators

    def test_close_no_client(self):
        detector = TBMLDetector()
        detector.close()

    def test_close_with_client(self):
        detector = TBMLDetector()
        detector.client = MagicMock()
        detector.close()
        detector.client.close.assert_called_once()

    def test_connect(self):
        detector = TBMLDetector()
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.all.return_value.result.return_value = [200]
        mock_client.submit.return_value = mock_result
        with patch("banking.analytics.detect_tbml.client.Client", return_value=mock_client):
            detector.connect()
        assert detector.client is not None

    def test_detect_carousel_fraud_empty(self):
        detector = TBMLDetector()
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.all.return_value.result.return_value = []
        mock_client.submit.return_value = mock_result
        detector.client = mock_client
        alerts = detector.detect_carousel_fraud(max_depth=3)
        assert isinstance(alerts, list)

    def test_extract_companies_dict(self):
        detector = TBMLDetector()
        result = {"start": {"name": ["CompanyA"]}, "mid": {"name": ["CompanyB"]}}
        companies = detector._extract_companies(result)
        assert "CompanyA" in companies
        assert "CompanyB" in companies

    def test_extract_companies_non_dict(self):
        detector = TBMLDetector()
        assert detector._extract_companies("not a dict") == []

    def test_extract_transaction_ids_dict(self):
        detector = TBMLDetector()
        result = {"tx1": "T-001", "tx2": "T-002"}
        tx_ids = detector._extract_transaction_ids(result)
        assert "T-001" in tx_ids
        assert "T-002" in tx_ids

    def test_extract_transaction_ids_non_dict(self):
        detector = TBMLDetector()
        assert detector._extract_transaction_ids([]) == []

    def test_calculate_carousel_risk(self):
        detector = TBMLDetector()
        loop = {"depth": 3, "companies": ["A", "B", "C"], "transactions": [{"amount": 100000}]}
        risk = detector._calculate_carousel_risk(loop)
        assert isinstance(risk, float)
        assert 0.0 <= risk <= 1.0


class TestTBMLAlert:
    def test_creation(self):
        alert = TBMLAlert(
            alert_id="TBML-001",
            alert_type="carousel",
            severity="high",
            entities=["C-1", "C-2"],
            transactions=["T-1"],
            total_value=100000.0,
            risk_score=0.9,
            indicators=["circular trading"],
            timestamp=datetime.now(timezone.utc),
            details={},
        )
        assert alert.alert_type == "carousel"
        assert alert.total_value == 100000.0


class TestPriceAnomaly:
    def test_creation(self):
        anomaly = PriceAnomaly(
            transaction_id="T-1",
            declared_price=100.0,
            market_price=50.0,
            deviation_percent=100.0,
            direction="over",
            risk_score=0.95,
        )
        assert anomaly.direction == "over"
        assert anomaly.deviation_percent == 100.0
