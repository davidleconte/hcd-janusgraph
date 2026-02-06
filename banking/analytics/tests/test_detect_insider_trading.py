"""
Unit Tests for Insider Trading Detection Module
===============================================

Tests for Insider Trading detection algorithms including:
- Timing correlation analysis
- Coordinated trading detection
- Communication-based detection
- Network analysis

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
Date: 2026-02-04
"""

import pytest
from datetime import datetime
from banking.analytics.detect_insider_trading import (
    InsiderTradingDetector, InsiderTradingAlert, TradeCluster, CorporateEvent
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
            event_id='EVT-001',
            company_id='COMP-001',
            symbol='AAPL',
            event_type='earnings',
            announcement_date=datetime(2026, 2, 15),
            impact='positive',
            price_change_percent=15.0
        )
        
        trades = [
            {'trade_id': 'T1', 'side': 'buy', 'trade_date': datetime(2026, 2, 5)},  # In window
            {'trade_id': 'T2', 'side': 'buy', 'trade_date': datetime(2026, 2, 10)},  # In window
            {'trade_id': 'T3', 'side': 'sell', 'trade_date': datetime(2026, 2, 8)},  # Wrong side
            {'trade_id': 'T4', 'side': 'buy', 'trade_date': datetime(2026, 1, 15)},  # Too early
        ]
        
        pre_trades = detector._find_pre_announcement_trades(trades, event)
        
        assert len(pre_trades) == 2
        assert all(t['side'] == 'buy' for t in pre_trades)
        
    def test_find_pre_announcement_trades_sell_negative_impact(self):
        """Test finding sells before negative events"""
        detector = InsiderTradingDetector()
        
        event = CorporateEvent(
            event_id='EVT-002',
            company_id='COMP-001',
            symbol='TSLA',
            event_type='product_recall',
            announcement_date=datetime(2026, 2, 15),
            impact='negative',
            price_change_percent=-20.0
        )
        
        trades = [
            {'trade_id': 'T1', 'side': 'sell', 'trade_date': datetime(2026, 2, 5)},  # In window
            {'trade_id': 'T2', 'side': 'buy', 'trade_date': datetime(2026, 2, 10)},  # Wrong side
        ]
        
        pre_trades = detector._find_pre_announcement_trades(trades, event)
        
        assert len(pre_trades) == 1
        assert pre_trades[0]['side'] == 'sell'
        
    def test_calculate_timing_risk_base(self):
        """Test timing risk calculation with base values"""
        detector = InsiderTradingDetector()
        
        event = CorporateEvent(
            event_id='EVT-001',
            company_id='COMP-001',
            symbol='AAPL',
            event_type='earnings',
            announcement_date=datetime(2026, 2, 15),
            impact='positive',
            price_change_percent=5.0
        )
        
        trades = [
            {'total_value': 10000, 'trader_info': {}},
            {'total_value': 15000, 'trader_info': {}},
        ]
        
        risk = detector._calculate_timing_risk(trades, event)
        assert risk >= 0.3  # Base score
        assert risk <= 1.0
        
    def test_calculate_timing_risk_high_value(self):
        """Test timing risk with high transaction values"""
        detector = InsiderTradingDetector()
        
        event = CorporateEvent(
            event_id='EVT-001',
            company_id='COMP-001',
            symbol='AAPL',
            event_type='merger',
            announcement_date=datetime(2026, 2, 15),
            impact='positive',
            price_change_percent=25.0
        )
        
        low_value_trades = [{'total_value': 10000, 'trader_info': {}}] * 3
        high_value_trades = [{'total_value': 200000, 'trader_info': {}}] * 3
        
        low_risk = detector._calculate_timing_risk(low_value_trades, event)
        high_risk = detector._calculate_timing_risk(high_value_trades, event)
        
        assert high_risk > low_risk


class TestCoordinatedTradingDetection:
    """Test coordinated trading detection"""
    
    def test_create_cluster(self):
        """Test trade cluster creation"""
        detector = InsiderTradingDetector()
        
        trades = [
            {'trade_id': 'T1', 'trader_id': 'TR-001', 'quantity': 100, 'total_value': 10000,
             'symbol': 'AAPL', 'trade_date': datetime(2026, 2, 4, 10, 0)},
            {'trade_id': 'T2', 'trader_id': 'TR-002', 'quantity': 200, 'total_value': 20000,
             'symbol': 'AAPL', 'trade_date': datetime(2026, 2, 4, 11, 0)},
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
            trades=[{'side': 'buy'}, {'side': 'buy'}],
            symbol='AAPL',
            start_time=datetime.now(),
            end_time=datetime.now(),
            total_volume=100,
            total_value=50000,
            unique_traders={'TR-001', 'TR-002'}
        )
        
        cluster_5_traders = TradeCluster(
            trades=[{'side': 'buy'}] * 5,
            symbol='AAPL',
            start_time=datetime.now(),
            end_time=datetime.now(),
            total_volume=500,
            total_value=250000,
            unique_traders={'TR-001', 'TR-002', 'TR-003', 'TR-004', 'TR-005'}
        )
        
        risk_2 = detector._calculate_coordination_risk(cluster_2_traders)
        risk_5 = detector._calculate_coordination_risk(cluster_5_traders)
        
        assert risk_5 > risk_2
        
    def test_calculate_coordination_risk_same_side(self):
        """Test coordination risk when all trades are same side"""
        detector = InsiderTradingDetector()
        
        # All buys (coordinated)
        cluster_same = TradeCluster(
            trades=[{'side': 'buy'}, {'side': 'buy'}, {'side': 'buy'}],
            symbol='AAPL',
            start_time=datetime.now(),
            end_time=datetime.now(),
            total_volume=300,
            total_value=100000,
            unique_traders={'TR-001', 'TR-002', 'TR-003'}
        )
        
        # Mixed buys and sells (less coordinated)
        cluster_mixed = TradeCluster(
            trades=[{'side': 'buy'}, {'side': 'sell'}, {'side': 'buy'}],
            symbol='AAPL',
            start_time=datetime.now(),
            end_time=datetime.now(),
            total_volume=300,
            total_value=100000,
            unique_traders={'TR-001', 'TR-002', 'TR-003'}
        )
        
        risk_same = detector._calculate_coordination_risk(cluster_same)
        risk_mixed = detector._calculate_coordination_risk(cluster_mixed)
        
        assert risk_same > risk_mixed


class TestCommunicationDetection:
    """Test communication-based detection"""
    
    def test_is_suspicious_communication_flagged(self):
        """Test detection of flagged communication"""
        detector = InsiderTradingDetector()
        
        comm = {'contains_suspicious_keywords': [True]}
        trade = {}
        
        result = detector._is_suspicious_communication(comm, trade)
        assert result is True
        
    def test_is_suspicious_communication_keywords(self):
        """Test detection by MNPI keywords"""
        detector = InsiderTradingDetector()
        
        suspicious_comm = {'content': 'Big merger announcement coming next week', 'contains_suspicious_keywords': [False]}
        normal_comm = {'content': 'Good morning, how are you?', 'contains_suspicious_keywords': [False]}
        
        assert detector._is_suspicious_communication(suspicious_comm, {}) is True
        assert detector._is_suspicious_communication(normal_comm, {}) is False
        
    def test_calculate_communication_risk(self):
        """Test communication risk calculation"""
        detector = InsiderTradingDetector()
        
        comm_flagged = {'contains_suspicious_keywords': [True], 'is_encrypted': [False]}
        comm_normal = {'contains_suspicious_keywords': [False], 'is_encrypted': [False]}
        trade = {'total_value': [100000]}
        
        risk_flagged = detector._calculate_communication_risk(comm_flagged, trade)
        risk_normal = detector._calculate_communication_risk(comm_normal, trade)
        
        assert risk_flagged > risk_normal


class TestNetworkAnalysis:
    """Test network-based detection"""
    
    def test_calculate_network_risk_high_access(self):
        """Test network risk with high-access insider"""
        detector = InsiderTradingDetector()
        
        trades_ceo = [
            {'insider': {'job_title': ['CEO']}, 'trade': {'total_value': [100000]}},
            {'insider': {'job_title': ['CEO']}, 'trade': {'total_value': [150000]}},
        ]
        
        trades_analyst = [
            {'insider': {'job_title': ['Analyst']}, 'trade': {'total_value': [100000]}},
            {'insider': {'job_title': ['Analyst']}, 'trade': {'total_value': [150000]}},
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
        
        result = detector._parse_date('2026-02-04T10:30:00')
        
        assert result is not None
        assert result.year == 2026
        assert result.month == 2
        assert result.day == 4
        
    def test_parse_date_invalid(self):
        """Test date parsing with invalid input"""
        detector = InsiderTradingDetector()
        
        result = detector._parse_date('not a date')
        assert result is None
        
        result = detector._parse_date(None)
        assert result is None
        
    def test_calculate_severity(self):
        """Test severity calculation"""
        detector = InsiderTradingDetector()
        
        assert detector._calculate_severity(0.9) == 'critical'
        assert detector._calculate_severity(0.75) == 'high'
        assert detector._calculate_severity(0.6) == 'medium'
        assert detector._calculate_severity(0.3) == 'low'


class TestReportGeneration:
    """Test report generation"""
    
    def test_generate_report_empty(self):
        """Test report generation with no alerts"""
        detector = InsiderTradingDetector()
        
        report = detector.generate_report()
        
        assert 'report_date' in report
        assert report['total_alerts'] == 0
        assert report['total_value_at_risk'] == 0
        assert report['unique_traders'] == 0
        
    def test_generate_report_with_alerts(self):
        """Test report generation with alerts"""
        detector = InsiderTradingDetector()
        
        detector.alerts = [
            InsiderTradingAlert(
                alert_id='IT-001',
                alert_type='timing',
                severity='high',
                traders=['TR-001', 'TR-002'],
                trades=['T-001'],
                symbol='AAPL',
                total_value=500000.0,
                risk_score=0.8,
                indicators=['Test'],
                timestamp=datetime.utcnow(),
                details={}
            ),
            InsiderTradingAlert(
                alert_id='IT-002',
                alert_type='coordinated',
                severity='medium',
                traders=['TR-003'],
                trades=['T-002'],
                symbol='TSLA',
                total_value=100000.0,
                risk_score=0.6,
                indicators=['Test'],
                timestamp=datetime.utcnow(),
                details={}
            )
        ]
        
        report = detector.generate_report()
        
        assert report['total_alerts'] == 2
        assert report['alerts_by_type']['timing'] == 1
        assert report['alerts_by_type']['coordinated'] == 1
        assert report['total_value_at_risk'] == 600000.0


class TestDataclasses:
    """Test dataclass definitions"""
    
    def test_insider_trading_alert_creation(self):
        """Test InsiderTradingAlert dataclass"""
        alert = InsiderTradingAlert(
            alert_id='IT-001',
            alert_type='timing',
            severity='high',
            traders=['TR-001'],
            trades=['T-001'],
            symbol='AAPL',
            total_value=100000.0,
            risk_score=0.8,
            indicators=['Pre-announcement trading'],
            timestamp=datetime.utcnow(),
            details={}
        )
        
        assert alert.alert_id == 'IT-001'
        assert alert.alert_type == 'timing'
        assert alert.symbol == 'AAPL'
        
    def test_trade_cluster_creation(self):
        """Test TradeCluster dataclass"""
        cluster = TradeCluster(
            trades=[{'trade_id': 'T-001'}],
            symbol='AAPL',
            start_time=datetime(2026, 2, 4, 10, 0),
            end_time=datetime(2026, 2, 4, 12, 0),
            total_volume=1000,
            total_value=150000.0,
            unique_traders={'TR-001', 'TR-002'}
        )
        
        assert cluster.symbol == 'AAPL'
        assert cluster.total_volume == 1000
        assert len(cluster.unique_traders) == 2
        
    def test_corporate_event_creation(self):
        """Test CorporateEvent dataclass"""
        event = CorporateEvent(
            event_id='EVT-001',
            company_id='COMP-001',
            symbol='AAPL',
            event_type='earnings',
            announcement_date=datetime(2026, 2, 15),
            impact='positive',
            price_change_percent=12.5
        )
        
        assert event.symbol == 'AAPL'
        assert event.event_type == 'earnings'
        assert event.impact == 'positive'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
