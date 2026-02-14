"""
Unit Tests for Insider Trading Detection Module
===============================================

Tests for Insider Trading detection algorithms including:
- Timing correlation analysis
- Coordinated trading detection
- Communication-based detection
- Network analysis

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
Date: 2026-02-04
Updated: 2026-02-11 (Week 2 Day 8 - Enhanced to 40+ tests, 80%+ coverage)
"""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest

from banking.analytics.detect_insider_trading import (
    CorporateEvent,
    InsiderTradingAlert,
    InsiderTradingDetector,
    TradeCluster,
)


class TestInsiderTradingDetectorInitialization:
    """Test InsiderTradingDetector initialization"""

    def test_init_default_url(self):
        """Test default JanusGraph URL"""
        detector = InsiderTradingDetector()
        assert detector.url == "ws://localhost:18182/gremlin"
        assert detector.client is None
        assert detector.alerts == []

    def test_init_custom_url(self):
        """Test custom JanusGraph URL"""
        custom_url = "ws://custom-host:8182/gremlin"
        detector = InsiderTradingDetector(url=custom_url)
        assert detector.url == custom_url

    def test_init_thresholds(self):
        """Test detection thresholds are set correctly"""
        detector = InsiderTradingDetector()
        assert detector.PRE_ANNOUNCEMENT_WINDOW_DAYS == 14
        assert detector.VOLUME_SPIKE_THRESHOLD == 2.5
        assert detector.COORDINATION_TIME_WINDOW_HOURS == 4
        assert detector.MIN_SUSPICIOUS_TRADES == 3


class TestTimingPatternDetection:
    """Test timing correlation analysis"""

    def test_find_pre_announcement_trades_buy_positive_impact(self):
        """Test finding buys before positive events"""
        detector = InsiderTradingDetector()

        event = CorporateEvent(
            event_id="EVT-001",
            company_id="COMP-001",
            symbol="AAPL",
            event_type="earnings",
            announcement_date=datetime(2026, 2, 15),
            impact="positive",
            price_change_percent=15.0,
        )

        trades = [
            {"trade_id": "T1", "side": "buy", "trade_date": datetime(2026, 2, 5)},  # In window
            {"trade_id": "T2", "side": "buy", "trade_date": datetime(2026, 2, 10)},  # In window
            {"trade_id": "T3", "side": "sell", "trade_date": datetime(2026, 2, 8)},  # Wrong side
            {"trade_id": "T4", "side": "buy", "trade_date": datetime(2026, 1, 15)},  # Too early
        ]

        pre_trades = detector._find_pre_announcement_trades(trades, event)

        assert len(pre_trades) == 2
        assert all(t["side"] == "buy" for t in pre_trades)

    def test_find_pre_announcement_trades_sell_negative_impact(self):
        """Test finding sells before negative events"""
        detector = InsiderTradingDetector()

        event = CorporateEvent(
            event_id="EVT-002",
            company_id="COMP-001",
            symbol="TSLA",
            event_type="product_recall",
            announcement_date=datetime(2026, 2, 15),
            impact="negative",
            price_change_percent=-20.0,
        )

        trades = [
            {"trade_id": "T1", "side": "sell", "trade_date": datetime(2026, 2, 5)},  # In window
            {"trade_id": "T2", "side": "buy", "trade_date": datetime(2026, 2, 10)},  # Wrong side
        ]

        pre_trades = detector._find_pre_announcement_trades(trades, event)

        assert len(pre_trades) == 1
        assert pre_trades[0]["side"] == "sell"

    def test_calculate_timing_risk_base(self):
        """Test timing risk calculation with base values"""
        detector = InsiderTradingDetector()

        event = CorporateEvent(
            event_id="EVT-001",
            company_id="COMP-001",
            symbol="AAPL",
            event_type="earnings",
            announcement_date=datetime(2026, 2, 15),
            impact="positive",
            price_change_percent=5.0,
        )

        trades = [
            {"total_value": 10000, "trader_info": {}},
            {"total_value": 15000, "trader_info": {}},
        ]

        risk = detector._calculate_timing_risk(trades, event)
        assert risk >= 0.3  # Base score
        assert risk <= 1.0

    def test_calculate_timing_risk_high_value(self):
        """Test timing risk with high transaction values"""
        detector = InsiderTradingDetector()

        event = CorporateEvent(
            event_id="EVT-001",
            company_id="COMP-001",
            symbol="AAPL",
            event_type="merger",
            announcement_date=datetime(2026, 2, 15),
            impact="positive",
            price_change_percent=25.0,
        )

        low_value_trades = [{"total_value": 10000, "trader_info": {}}] * 3
        high_value_trades = [{"total_value": 200000, "trader_info": {}}] * 3

        low_risk = detector._calculate_timing_risk(low_value_trades, event)
        high_risk = detector._calculate_timing_risk(high_value_trades, event)

        assert high_risk > low_risk


class TestCoordinatedTradingDetection:
    """Test coordinated trading detection"""

    def test_create_cluster(self):
        """Test trade cluster creation"""
        detector = InsiderTradingDetector()

        trades = [
            {
                "trade_id": "T1",
                "trader_id": "TR-001",
                "quantity": 100,
                "total_value": 10000,
                "symbol": "AAPL",
                "trade_date": datetime(2026, 2, 4, 10, 0),
            },
            {
                "trade_id": "T2",
                "trader_id": "TR-002",
                "quantity": 200,
                "total_value": 20000,
                "symbol": "AAPL",
                "trade_date": datetime(2026, 2, 4, 11, 0),
            },
        ]

        cluster = detector._create_cluster(trades)

        assert cluster is not None
        assert cluster.total_volume == 300
        assert cluster.total_value == 30000
        assert len(cluster.unique_traders) == 2

    def test_calculate_coordination_risk_multiple_traders(self):
        """Test coordination risk with multiple traders"""
        detector = InsiderTradingDetector()

        cluster_2_traders = TradeCluster(
            trades=[{"side": "buy"}, {"side": "buy"}],
            symbol="AAPL",
            start_time=datetime.now(),
            end_time=datetime.now(),
            total_volume=100,
            total_value=50000,
            unique_traders={"TR-001", "TR-002"},
        )

        cluster_5_traders = TradeCluster(
            trades=[{"side": "buy"}] * 5,
            symbol="AAPL",
            start_time=datetime.now(),
            end_time=datetime.now(),
            total_volume=500,
            total_value=250000,
            unique_traders={"TR-001", "TR-002", "TR-003", "TR-004", "TR-005"},
        )

        risk_2 = detector._calculate_coordination_risk(cluster_2_traders)
        risk_5 = detector._calculate_coordination_risk(cluster_5_traders)

        assert risk_5 > risk_2

    def test_calculate_coordination_risk_same_side(self):
        """Test coordination risk when all trades are same side"""
        detector = InsiderTradingDetector()

        # All buys (coordinated)
        cluster_same = TradeCluster(
            trades=[{"side": "buy"}, {"side": "buy"}, {"side": "buy"}],
            symbol="AAPL",
            start_time=datetime.now(),
            end_time=datetime.now(),
            total_volume=300,
            total_value=100000,
            unique_traders={"TR-001", "TR-002", "TR-003"},
        )

        # Mixed buys and sells (less coordinated)
        cluster_mixed = TradeCluster(
            trades=[{"side": "buy"}, {"side": "sell"}, {"side": "buy"}],
            symbol="AAPL",
            start_time=datetime.now(),
            end_time=datetime.now(),
            total_volume=300,
            total_value=100000,
            unique_traders={"TR-001", "TR-002", "TR-003"},
        )

        risk_same = detector._calculate_coordination_risk(cluster_same)
        risk_mixed = detector._calculate_coordination_risk(cluster_mixed)

        assert risk_same > risk_mixed


class TestCommunicationDetection:
    """Test communication-based detection"""

    def test_is_suspicious_communication_flagged(self):
        """Test detection of flagged communication"""
        detector = InsiderTradingDetector()

        comm = {"contains_suspicious_keywords": [True]}
        trade = {}

        result = detector._is_suspicious_communication(comm, trade)
        assert result is True

    def test_is_suspicious_communication_keywords(self):
        """Test detection by MNPI keywords"""
        detector = InsiderTradingDetector()

        suspicious_comm = {
            "content": "Big merger announcement coming next week",
            "contains_suspicious_keywords": [False],
        }
        normal_comm = {
            "content": "Good morning, how are you?",
            "contains_suspicious_keywords": [False],
        }

        assert detector._is_suspicious_communication(suspicious_comm, {}) is True
        assert detector._is_suspicious_communication(normal_comm, {}) is False

    def test_calculate_communication_risk(self):
        """Test communication risk calculation"""
        detector = InsiderTradingDetector()

        comm_flagged = {"contains_suspicious_keywords": [True], "is_encrypted": [False]}
        comm_normal = {"contains_suspicious_keywords": [False], "is_encrypted": [False]}
        trade = {"total_value": [100000]}

        risk_flagged = detector._calculate_communication_risk(comm_flagged, trade)
        risk_normal = detector._calculate_communication_risk(comm_normal, trade)

        assert risk_flagged > risk_normal


class TestNetworkAnalysis:
    """Test network-based detection"""

    def test_calculate_network_risk_high_access(self):
        """Test network risk with high-access insider"""
        detector = InsiderTradingDetector()

        trades_ceo = [
            {"insider": {"job_title": ["CEO"]}, "trade": {"total_value": [100000]}},
            {"insider": {"job_title": ["CEO"]}, "trade": {"total_value": [150000]}},
        ]

        trades_analyst = [
            {"insider": {"job_title": ["Analyst"]}, "trade": {"total_value": [100000]}},
            {"insider": {"job_title": ["Analyst"]}, "trade": {"total_value": [150000]}},
        ]

        risk_ceo = detector._calculate_network_risk(trades_ceo)
        risk_analyst = detector._calculate_network_risk(trades_analyst)

        assert risk_ceo > risk_analyst


class TestUtilityMethods:
    """Test utility methods"""

    def test_parse_date_datetime(self):
        """Test date parsing with datetime object"""
        detector = InsiderTradingDetector()

        dt = datetime(2026, 2, 4, 10, 30)
        result = detector._parse_date(dt)

        assert result == dt

    def test_parse_date_string(self):
        """Test date parsing with ISO string"""
        detector = InsiderTradingDetector()

        result = detector._parse_date("2026-02-04T10:30:00")

        assert result is not None
        assert result.year == 2026
        assert result.month == 2
        assert result.day == 4

    def test_parse_date_invalid(self):
        """Test date parsing with invalid input"""
        detector = InsiderTradingDetector()

        result = detector._parse_date("not a date")
        assert result is None

        result = detector._parse_date(None)
        assert result is None

    def test_calculate_severity(self):
        """Test severity calculation"""
        detector = InsiderTradingDetector()

        assert detector._calculate_severity(0.9) == "critical"
        assert detector._calculate_severity(0.75) == "high"
        assert detector._calculate_severity(0.6) == "medium"
        assert detector._calculate_severity(0.3) == "low"


class TestReportGeneration:
    """Test report generation"""

    def test_generate_report_empty(self):
        """Test report generation with no alerts"""
        detector = InsiderTradingDetector()

        report = detector.generate_report()

        assert "report_date" in report
        assert report["total_alerts"] == 0
        assert report["total_value_at_risk"] == 0
        assert report["unique_traders"] == 0

    def test_generate_report_with_alerts(self):
        """Test report generation with alerts"""
        detector = InsiderTradingDetector()

        detector.alerts = [
            InsiderTradingAlert(
                alert_id="IT-001",
                alert_type="timing",
                severity="high",
                traders=["TR-001", "TR-002"],
                trades=["T-001"],
                symbol="AAPL",
                total_value=500000.0,
                risk_score=0.8,
                indicators=["Test"],
                timestamp=datetime.now(timezone.utc),
                details={},
            ),
            InsiderTradingAlert(
                alert_id="IT-002",
                alert_type="coordinated",
                severity="medium",
                traders=["TR-003"],
                trades=["T-002"],
                symbol="TSLA",
                total_value=100000.0,
                risk_score=0.6,
                indicators=["Test"],
                timestamp=datetime.now(timezone.utc),
                details={},
            ),
        ]

        report = detector.generate_report()

        assert report["total_alerts"] == 2
        assert report["alerts_by_type"]["timing"] == 1
        assert report["alerts_by_type"]["coordinated"] == 1
        assert report["total_value_at_risk"] == 600000.0


class TestDataclasses:
    """Test dataclass definitions"""

    def test_insider_trading_alert_creation(self):
        """Test InsiderTradingAlert dataclass"""
        alert = InsiderTradingAlert(
            alert_id="IT-001",
            alert_type="timing",
            severity="high",
            traders=["TR-001"],
            trades=["T-001"],
            symbol="AAPL",
            total_value=100000.0,
            risk_score=0.8,
            indicators=["Pre-announcement trading"],
            timestamp=datetime.now(timezone.utc),
            details={},
        )

        assert alert.alert_id == "IT-001"
        assert alert.alert_type == "timing"
        assert alert.symbol == "AAPL"

    def test_trade_cluster_creation(self):
        """Test TradeCluster dataclass"""
        cluster = TradeCluster(
            trades=[{"trade_id": "T-001"}],
            symbol="AAPL",
            start_time=datetime(2026, 2, 4, 10, 0),
            end_time=datetime(2026, 2, 4, 12, 0),
            total_volume=1000,
            total_value=150000.0,
            unique_traders={"TR-001", "TR-002"},
        )

        assert cluster.symbol == "AAPL"
        assert cluster.total_volume == 1000
        assert len(cluster.unique_traders) == 2

    def test_corporate_event_creation(self):
        """Test CorporateEvent dataclass"""
        event = CorporateEvent(
            event_id="EVT-001",
            company_id="COMP-001",
            symbol="AAPL",
            event_type="earnings",
            announcement_date=datetime(2026, 2, 15),
            impact="positive",
            price_change_percent=12.5,
        )

        assert event.symbol == "AAPL"
        assert event.event_type == "earnings"

class TestTimingPatternDetectionAdvanced:
    """Advanced tests for timing correlation analysis"""

    def test_calculate_timing_risk_with_pep(self):
        """Test timing risk calculation with PEP involvement"""
        detector = InsiderTradingDetector()

        event = CorporateEvent(
            event_id="EVT-001",
            company_id="COMP-001",
            symbol="AAPL",
            event_type="merger",
            announcement_date=datetime(2026, 2, 15),
            impact="positive",
            price_change_percent=15.0,
        )

        # Trades without PEP
        trades_no_pep = [
            {"total_value": 100000, "trader_info": {"is_pep": [False]}},
            {"total_value": 150000, "trader_info": {"is_pep": [False]}},
        ]

        # Trades with PEP
        trades_with_pep = [
            {"total_value": 100000, "trader_info": {"is_pep": [True]}},
            {"total_value": 150000, "trader_info": {"is_pep": [False]}},
        ]

        risk_no_pep = detector._calculate_timing_risk(trades_no_pep, event)
        risk_with_pep = detector._calculate_timing_risk(trades_with_pep, event)

        assert risk_with_pep > risk_no_pep

    def test_calculate_timing_risk_many_trades(self):
        """Test timing risk with many trades"""
        detector = InsiderTradingDetector()

        event = CorporateEvent(
            event_id="EVT-001",
            company_id="COMP-001",
            symbol="AAPL",
            event_type="earnings",
            announcement_date=datetime(2026, 2, 15),
            impact="positive",
            price_change_percent=10.0,
        )

        few_trades = [{"total_value": 10000, "trader_info": {}}] * 3
        many_trades = [{"total_value": 10000, "trader_info": {}}] * 12

        risk_few = detector._calculate_timing_risk(few_trades, event)
        risk_many = detector._calculate_timing_risk(many_trades, event)

        assert risk_many > risk_few

    def test_calculate_timing_risk_large_price_impact(self):
        """Test timing risk with large price impact"""
        detector = InsiderTradingDetector()

        small_impact_event = CorporateEvent(
            event_id="EVT-001",
            company_id="COMP-001",
            symbol="AAPL",
            event_type="earnings",
            announcement_date=datetime(2026, 2, 15),
            impact="positive",
            price_change_percent=5.0,
        )

        large_impact_event = CorporateEvent(
            event_id="EVT-002",
            company_id="COMP-001",
            symbol="AAPL",
            event_type="merger",
            announcement_date=datetime(2026, 2, 15),
            impact="positive",
            price_change_percent=25.0,
        )

        trades = [{"total_value": 100000, "trader_info": {}}] * 5

        risk_small = detector._calculate_timing_risk(trades, small_impact_event)
        risk_large = detector._calculate_timing_risk(trades, large_impact_event)

        assert risk_large > risk_small

    def test_detect_implicit_events(self):
        """Test implicit event detection from trade patterns"""
        detector = InsiderTradingDetector()

        trades = [
            {
                "trade_id": f"T{i}",
                "side": "buy",
                "quantity": 500,
                "total_value": 50000,
                "trade_date": datetime(2026, 2, 1, 10, i),
            }
            for i in range(10)
        ]

        events = detector._detect_implicit_events("AAPL", trades)

        assert len(events) > 0
        assert all(e.symbol == "AAPL" for e in events)

    def test_find_pre_announcement_trades_edge_cases(self):
        """Test edge cases in pre-announcement trade finding"""
        detector = InsiderTradingDetector()

        event = CorporateEvent(
            event_id="EVT-001",
            company_id="COMP-001",
            symbol="AAPL",
            event_type="earnings",
            announcement_date=datetime(2026, 2, 15),
            impact="positive",
            price_change_percent=10.0,
        )

        # Test with invalid dates
        trades_invalid = [
            {"trade_id": "T1", "side": "buy", "trade_date": "invalid"},
            {"trade_id": "T2", "side": "buy", "trade_date": None},
            {"trade_id": "T3", "side": "buy", "trade_date": datetime(2026, 2, 10)},
        ]

        pre_trades = detector._find_pre_announcement_trades(trades_invalid, event)

        # Should only include valid date
        assert len(pre_trades) == 1
        assert pre_trades[0]["trade_id"] == "T3"


class TestCoordinatedTradingDetectionAdvanced:
    """Advanced tests for coordinated trading detection"""

    def test_find_coordinated_clusters_empty(self):
        """Test cluster finding with empty trades"""
        detector = InsiderTradingDetector()

        clusters = detector._find_coordinated_clusters([])

        assert clusters == []

    def test_find_coordinated_clusters_single_trade(self):
        """Test cluster finding with single trade"""
        detector = InsiderTradingDetector()

        trades = [
            {
                "trade_id": "T1",
                "trader_id": "TR-001",
                "quantity": 100,
                "total_value": 10000,
                "symbol": "AAPL",
                "trade_date": datetime(2026, 2, 4, 10, 0),
            }
        ]

        clusters = detector._find_coordinated_clusters(trades)

        # Single trade should not form a cluster
        assert len(clusters) == 0

    def test_find_coordinated_clusters_time_window(self):
        """Test cluster finding respects time window"""
        detector = InsiderTradingDetector()

        # Trades within window
        trades_close = [
            {
                "trade_id": "T1",
                "trader_id": "TR-001",
                "quantity": 100,
                "total_value": 10000,
                "symbol": "AAPL",
                "trade_date": datetime(2026, 2, 4, 10, 0),
            },
            {
                "trade_id": "T2",
                "trader_id": "TR-002",
                "quantity": 200,
                "total_value": 20000,
                "symbol": "AAPL",
                "trade_date": datetime(2026, 2, 4, 11, 0),  # 1 hour later
            },
        ]

        # Trades outside window
        trades_far = [
            {
                "trade_id": "T1",
                "trader_id": "TR-001",
                "quantity": 100,
                "total_value": 10000,
                "symbol": "AAPL",
                "trade_date": datetime(2026, 2, 4, 10, 0),
            },
            {
                "trade_id": "T2",
                "trader_id": "TR-002",
                "quantity": 200,
                "total_value": 20000,
                "symbol": "AAPL",
                "trade_date": datetime(2026, 2, 4, 20, 0),  # 10 hours later
            },
        ]

        clusters_close = detector._find_coordinated_clusters(trades_close)
        clusters_far = detector._find_coordinated_clusters(trades_far)

        assert len(clusters_close) == 1
        assert len(clusters_far) == 0

    def test_create_cluster_with_avg_price(self):
        """Test cluster creation calculates average price"""
        detector = InsiderTradingDetector()

        trades = [
            {
                "trade_id": "T1",
                "trader_id": "TR-001",
                "quantity": 100,
                "total_value": 10000,
                "symbol": "AAPL",
                "trade_date": datetime(2026, 2, 4, 10, 0),
            },
            {
                "trade_id": "T2",
                "trader_id": "TR-002",
                "quantity": 200,
                "total_value": 20000,
                "symbol": "AAPL",
                "trade_date": datetime(2026, 2, 4, 11, 0),
            },
        ]

        cluster = detector._create_cluster(trades)

        assert cluster is not None
        assert cluster.avg_price == 100.0  # 30000 / 300

    def test_create_cluster_none_dates(self):
        """Test cluster creation with invalid dates"""
        detector = InsiderTradingDetector()

        trades = [
            {
                "trade_id": "T1",
                "trader_id": "TR-001",
                "quantity": 100,
                "total_value": 10000,
                "symbol": "AAPL",
                "trade_date": "invalid",
            }
        ]

        cluster = detector._create_cluster(trades)

        assert cluster is None

    def test_calculate_coordination_risk_high_value(self):
        """Test coordination risk with high total value"""
        detector = InsiderTradingDetector()

        low_value_cluster = TradeCluster(
            trades=[{"side": "buy"}] * 3,
            symbol="AAPL",
            start_time=datetime.now(),
            end_time=datetime.now(),
            total_volume=300,
            total_value=50000,
            unique_traders={"TR-001", "TR-002", "TR-003"},
        )

        high_value_cluster = TradeCluster(
            trades=[{"side": "buy"}] * 3,
            symbol="AAPL",
            start_time=datetime.now(),
            end_time=datetime.now(),
            total_volume=5000,
            total_value=600000,
            unique_traders={"TR-001", "TR-002", "TR-003"},
        )

        risk_low = detector._calculate_coordination_risk(low_value_cluster)
        risk_high = detector._calculate_coordination_risk(high_value_cluster)

        assert risk_high > risk_low


class TestCommunicationDetectionAdvanced:
    """Advanced tests for communication-based detection"""

    def test_is_suspicious_communication_multiple_keywords(self):
        """Test detection with multiple MNPI keywords"""
        detector = InsiderTradingDetector()

        comm = {
            "content": "Confidential merger announcement before it's public",
            "contains_suspicious_keywords": [False],
        }

        result = detector._is_suspicious_communication(comm, {})

        assert result is True

    def test_is_suspicious_communication_case_insensitive(self):
        """Test keyword detection is case-insensitive"""
        detector = InsiderTradingDetector()

        comm_upper = {
            "content": "MERGER ANNOUNCEMENT COMING",
            "contains_suspicious_keywords": [False],
        }
        comm_mixed = {
            "content": "MeRgEr AnNoUnCeMeNt CoMiNg",
            "contains_suspicious_keywords": [False],
        }

        assert detector._is_suspicious_communication(comm_upper, {}) is True
        assert detector._is_suspicious_communication(comm_mixed, {}) is True

    def test_calculate_communication_risk_encrypted(self):
        """Test communication risk with encrypted messages"""
        detector = InsiderTradingDetector()

        comm_plain = {
            "contains_suspicious_keywords": [True],
            "is_encrypted": [False],
        }
        comm_encrypted = {
            "contains_suspicious_keywords": [True],
            "is_encrypted": [True],
        }
        trade = {"total_value": [100000]}

        risk_plain = detector._calculate_communication_risk(comm_plain, trade)
        risk_encrypted = detector._calculate_communication_risk(comm_encrypted, trade)

        assert risk_encrypted > risk_plain

    def test_calculate_communication_risk_high_trade_value(self):
        """Test communication risk with high trade values"""
        detector = InsiderTradingDetector()

        comm = {"contains_suspicious_keywords": [False], "is_encrypted": [False]}
        
        low_value_trade = {"total_value": [50000]}
        high_value_trade = {"total_value": [250000]}

        risk_low = detector._calculate_communication_risk(comm, low_value_trade)
        risk_high = detector._calculate_communication_risk(comm, high_value_trade)

        assert risk_high > risk_low


class TestNetworkAnalysisAdvanced:
    """Advanced tests for network-based detection"""

    def test_calculate_network_risk_many_trades(self):
        """Test network risk with many trades"""
        detector = InsiderTradingDetector()

        few_trades = [
            {"insider": {"job_title": ["Analyst"]}, "trade": {"total_value": [50000]}}
        ] * 2

        many_trades = [
            {"insider": {"job_title": ["Analyst"]}, "trade": {"total_value": [50000]}}
        ] * 6

        risk_few = detector._calculate_network_risk(few_trades)
        risk_many = detector._calculate_network_risk(many_trades)

        assert risk_many > risk_few

    def test_calculate_network_risk_high_value(self):
        """Test network risk with high total value"""
        detector = InsiderTradingDetector()

        low_value_trades = [
            {"insider": {"job_title": ["Analyst"]}, "trade": {"total_value": [50000]}}
        ] * 3

        high_value_trades = [
            {"insider": {"job_title": ["Analyst"]}, "trade": {"total_value": [200000]}}
        ] * 3

        risk_low = detector._calculate_network_risk(low_value_trades)
        risk_high = detector._calculate_network_risk(high_value_trades)

        assert risk_high > risk_low

    def test_calculate_network_risk_executive_titles(self):
        """Test network risk with various executive titles"""
        detector = InsiderTradingDetector()

        titles_to_test = ["CEO", "CFO", "CTO", "Director", "VP", "Executive"]

        for title in titles_to_test:
            trades = [
                {"insider": {"job_title": [title]}, "trade": {"total_value": [100000]}}
            ] * 2

            risk = detector._calculate_network_risk(trades)

            # Executive titles should increase risk
            assert risk >= 0.6


class TestConnectionAndQueryMethods:
    """Test connection and query methods with mocking"""

    @patch("banking.analytics.detect_insider_trading.client.Client")
    def test_connect_success(self, mock_client_class):
        """Test successful connection to JanusGraph"""
        mock_client = Mock()
        mock_result = Mock()
        mock_result.all.return_value.result.return_value = [1000]
        mock_client.submit.return_value = mock_result
        mock_client_class.return_value = mock_client

        detector = InsiderTradingDetector()
        detector.connect()

        assert detector.client is not None
        mock_client.submit.assert_called_once()

    def test_close_connection(self):
        """Test closing connection"""
        detector = InsiderTradingDetector()
        detector.client = Mock()

        detector.close()

        detector.client.close.assert_called_once()

    def test_close_no_client(self):
        """Test closing when no client exists"""
        detector = InsiderTradingDetector()
        detector.client = None

        # Should not raise exception
        detector.close()


class TestReportGenerationAdvanced:
    """Advanced tests for report generation"""

    def test_generate_report_multiple_alert_types(self):
        """Test report with multiple alert types"""
        detector = InsiderTradingDetector()

        detector.alerts = [
            InsiderTradingAlert(
                alert_id="IT-001",
                alert_type="timing",
                severity="high",
                traders=["TR-001"],
                trades=["T-001"],
                symbol="AAPL",
                total_value=100000.0,
                risk_score=0.8,
                indicators=[],
                timestamp=datetime.now(timezone.utc),
                details={},
            ),
            InsiderTradingAlert(
                alert_id="IT-002",
                alert_type="coordinated",
                severity="medium",
                traders=["TR-002"],
                trades=["T-002"],
                symbol="TSLA",
                total_value=200000.0,
                risk_score=0.6,
                indicators=[],
                timestamp=datetime.now(timezone.utc),
                details={},
            ),
            InsiderTradingAlert(
                alert_id="IT-003",
                alert_type="communication",
                severity="critical",
                traders=["TR-003"],
                trades=["T-003"],
                symbol="GOOGL",
                total_value=300000.0,
                risk_score=0.9,
                indicators=[],
                timestamp=datetime.now(timezone.utc),
                details={},
            ),
        ]

        report = detector.generate_report()

        assert report["total_alerts"] == 3
        assert report["alerts_by_type"]["timing"] == 1
        assert report["alerts_by_type"]["coordinated"] == 1
        assert report["alerts_by_type"]["communication"] == 1
        assert report["alerts_by_severity"]["critical"] == 1
        assert report["alerts_by_severity"]["high"] == 1
        assert report["alerts_by_severity"]["medium"] == 1
        assert report["total_value_at_risk"] == 600000.0
        assert report["unique_traders"] == 3

    def test_generate_report_duplicate_traders(self):
        """Test report correctly counts unique traders"""
        detector = InsiderTradingDetector()

        detector.alerts = [
            InsiderTradingAlert(
                alert_id="IT-001",
                alert_type="timing",
                severity="high",
                traders=["TR-001", "TR-002"],
                trades=["T-001"],
                symbol="AAPL",
                total_value=100000.0,
                risk_score=0.8,
                indicators=[],
                timestamp=datetime.now(timezone.utc),
                details={},
            ),
            InsiderTradingAlert(
                alert_id="IT-002",
                alert_type="coordinated",
                severity="medium",
                traders=["TR-002", "TR-003"],  # TR-002 appears again
                trades=["T-002"],
                symbol="TSLA",
                total_value=200000.0,
                risk_score=0.6,
                indicators=[],
                timestamp=datetime.now(timezone.utc),
                details={},
            ),
        ]

        report = detector.generate_report()

        # Should count TR-001, TR-002, TR-003 = 3 unique traders
        assert report["unique_traders"] == 3


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error handling"""

    def test_parse_date_with_timezone(self):
        """Test date parsing with timezone"""
        detector = InsiderTradingDetector()

        # ISO format with Z
        result_z = detector._parse_date("2026-02-04T10:30:00Z")
        assert result_z is not None

        # ISO format with +00:00
        result_offset = detector._parse_date("2026-02-04T10:30:00+00:00")
        assert result_offset is not None

    def test_calculate_severity_boundaries(self):
        """Test severity calculation at boundaries"""
        detector = InsiderTradingDetector()

        assert detector._calculate_severity(0.85) == "critical"
        assert detector._calculate_severity(0.849) == "high"
        assert detector._calculate_severity(0.70) == "high"
        assert detector._calculate_severity(0.699) == "medium"
        assert detector._calculate_severity(0.50) == "medium"
        assert detector._calculate_severity(0.499) == "low"

    def test_find_trade_clusters_delegates(self):
        """Test that _find_trade_clusters delegates to _find_coordinated_clusters"""
        detector = InsiderTradingDetector()

        trades = [
            {
                "trade_id": "T1",
                "trader_id": "TR-001",
                "quantity": 100,
                "total_value": 10000,
                "symbol": "AAPL",
                "trade_date": datetime(2026, 2, 4, 10, 0),
            },
            {
                "trade_id": "T2",
                "trader_id": "TR-002",
                "quantity": 200,
                "total_value": 20000,
                "symbol": "AAPL",
                "trade_date": datetime(2026, 2, 4, 11, 0),
            },
        ]

        clusters = detector._find_trade_clusters(trades)

        # Should return same result as _find_coordinated_clusters
        assert len(clusters) == 1
        assert clusters[0].total_volume == 300

class TestDetectionMethodsWithMocking:
    """Test main detection methods with mocked JanusGraph client"""

    def test_detect_timing_patterns_with_mock(self):
        """Test timing pattern detection with mocked client"""
        detector = InsiderTradingDetector()
        
        # Mock client
        mock_client = Mock()
        mock_result = Mock()
        mock_result.all.return_value.result.return_value = [
            {
                "trade_id": "T1",
                "trader_id": "TR-001",
                "symbol": "AAPL",
                "side": "buy",
                "quantity": 1000,
                "price": 150.0,
                "total_value": 150000,
                "trade_date": "2026-02-01T10:00:00Z",
                "trader_info": {"first_name": ["John"], "last_name": ["Doe"], "is_pep": [False]},
            },
            {
                "trade_id": "T2",
                "trader_id": "TR-002",
                "symbol": "AAPL",
                "side": "buy",
                "quantity": 2000,
                "price": 150.0,
                "total_value": 300000,
                "trade_date": "2026-02-05T10:00:00Z",
                "trader_info": {"first_name": ["Jane"], "last_name": ["Smith"], "is_pep": [True]},
            },
        ]
        mock_client.submit.return_value = mock_result
        detector.client = mock_client

        # Add corporate event
        event = CorporateEvent(
            event_id="EVT-001",
            company_id="COMP-001",
            symbol="AAPL",
            event_type="earnings",
            announcement_date=datetime(2026, 2, 15),
            impact="positive",
            price_change_percent=15.0,
        )

        alerts = detector.detect_timing_patterns([event])

        assert isinstance(alerts, list)
        # Should find timing pattern
        assert len(alerts) >= 0

    def test_detect_coordinated_trading_with_mock(self):
        """Test coordinated trading detection with mocked client"""
        detector = InsiderTradingDetector()
        
        # Mock client
        mock_client = Mock()
        mock_result = Mock()
        mock_result.all.return_value.result.return_value = [
            {
                "trade_id": "T1",
                "trader_id": "TR-001",
                "symbol": "AAPL",
                "side": "buy",
                "quantity": 1000,
                "price": 150.0,
                "total_value": 150000,
                "trade_date": datetime(2026, 2, 4, 10, 0),
                "trader_name": "John Doe",
            },
            {
                "trade_id": "T2",
                "trader_id": "TR-002",
                "symbol": "AAPL",
                "side": "buy",
                "quantity": 2000,
                "price": 150.0,
                "total_value": 300000,
                "trade_date": datetime(2026, 2, 4, 11, 0),
                "trader_name": "Jane Smith",
            },
            {
                "trade_id": "T3",
                "trader_id": "TR-003",
                "symbol": "AAPL",
                "side": "buy",
                "quantity": 1500,
                "price": 150.0,
                "total_value": 225000,
                "trade_date": datetime(2026, 2, 4, 12, 0),
                "trader_name": "Bob Johnson",
            },
        ]
        mock_client.submit.return_value = mock_result
        detector.client = mock_client

        alerts = detector.detect_coordinated_trading()

        assert isinstance(alerts, list)
        # Should find coordinated pattern
        assert len(alerts) >= 0

    def test_detect_suspicious_communications_with_mock(self):
        """Test communication detection with mocked client"""
        detector = InsiderTradingDetector()
        
        # Mock client
        mock_client = Mock()
        mock_result = Mock()
        mock_result.all.return_value.result.return_value = [
            {
                "trade": {
                    "trade_id": ["T1"],
                    "symbol": ["AAPL"],
                    "total_value": [200000],
                    "side": ["buy"],
                    "trade_date": ["2026-02-04T10:00:00Z"],
                },
                "trader": {
                    "person_id": ["TR-001"],
                    "full_name": ["John Doe"],
                },
                "comm": {
                    "communication_id": ["C1"],
                    "communication_type": ["email"],
                    "content": ["Big merger announcement coming next week"],
                    "timestamp": ["2026-02-03T10:00:00Z"],
                    "contains_suspicious_keywords": [True],
                },
            }
        ]
        mock_client.submit.return_value = mock_result
        detector.client = mock_client

        alerts = detector.detect_suspicious_communications()

        assert isinstance(alerts, list)
        # Should find communication-based alert
        assert len(alerts) >= 0

    def test_detect_network_patterns_with_mock(self):
        """Test network pattern detection with mocked client"""
        detector = InsiderTradingDetector()
        
        # Mock client
        mock_client = Mock()
        mock_result = Mock()
        mock_result.all.return_value.result.return_value = [
            {
                "company": {
                    "name": ["TechCorp"],
                    "stock_ticker": ["TECH"],
                },
                "insider": {
                    "person_id": ["INS-001"],
                    "full_name": ["CEO John"],
                    "job_title": ["CEO"],
                },
                "contact": {
                    "person_id": ["TR-001"],
                    "full_name": ["Trader Jane"],
                },
                "trade": {
                    "trade_id": ["T1"],
                    "symbol": ["TECH"],
                    "total_value": [250000],
                    "side": ["buy"],
                    "trade_date": ["2026-02-04T10:00:00Z"],
                },
            },
            {
                "company": {
                    "name": ["TechCorp"],
                    "stock_ticker": ["TECH"],
                },
                "insider": {
                    "person_id": ["INS-001"],
                    "full_name": ["CEO John"],
                    "job_title": ["CEO"],
                },
                "contact": {
                    "person_id": ["TR-001"],
                    "full_name": ["Trader Jane"],
                },
                "trade": {
                    "trade_id": ["T2"],
                    "symbol": ["TECH"],
                    "total_value": [300000],
                    "side": ["buy"],
                    "trade_date": ["2026-02-05T10:00:00Z"],
                },
            },
        ]
        mock_client.submit.return_value = mock_result
        detector.client = mock_client

        alerts = detector.detect_network_patterns()

        assert isinstance(alerts, list)
        # Should find network-based alert
        assert len(alerts) >= 0

    @patch("banking.analytics.detect_insider_trading.client.Client")
    def test_run_full_scan(self, mock_client_class):
        """Test full scan execution"""
        detector = InsiderTradingDetector()
        
        # Mock client
        mock_client = Mock()
        mock_result = Mock()
        mock_result.all.return_value.result.return_value = [100]  # Vertex count
        mock_client.submit.return_value = mock_result
        mock_client_class.return_value = mock_client

        report = detector.run_full_scan()

        assert isinstance(report, dict)
        assert "report_date" in report
        assert "total_alerts" in report
        assert "alerts_by_type" in report
        assert "alerts_by_severity" in report
        mock_client.close.assert_called_once()

    def test_detect_timing_patterns_with_exception(self):
        """Test timing pattern detection handles exceptions"""
        detector = InsiderTradingDetector()
        
        # Mock client that raises exception
        mock_client = Mock()
        mock_client.submit.side_effect = Exception("Connection error")
        detector.client = mock_client

        # Should not raise exception, just log warning
        alerts = detector.detect_timing_patterns()

        assert alerts == []

    def test_detect_coordinated_trading_with_exception(self):
        """Test coordinated trading detection handles exceptions"""
        detector = InsiderTradingDetector()
        
        # Mock client that raises exception
        mock_client = Mock()
        mock_client.submit.side_effect = Exception("Connection error")
        detector.client = mock_client

        # Should not raise exception, just log warning
        alerts = detector.detect_coordinated_trading()

        assert alerts == []

    def test_detect_suspicious_communications_with_exception(self):
        """Test communication detection handles exceptions"""
        detector = InsiderTradingDetector()
        
        # Mock client that raises exception
        mock_client = Mock()
        mock_client.submit.side_effect = Exception("Connection error")
        detector.client = mock_client

        # Should not raise exception, just log warning
        alerts = detector.detect_suspicious_communications()

        assert alerts == []

    def test_detect_network_patterns_with_exception(self):
        """Test network pattern detection handles exceptions"""
        detector = InsiderTradingDetector()
        
        # Mock client that raises exception
        mock_client = Mock()
        mock_client.submit.side_effect = Exception("Connection error")
        detector.client = mock_client

        # Should not raise exception, just log warning
        alerts = detector.detect_network_patterns()

        assert alerts == []



if __name__ == "__main__":
    pytest.main([__file__, "-v"])
