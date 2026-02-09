"""
Unit Tests for TBML Detection Module
=====================================

Tests for Trade-Based Money Laundering detection algorithms including:
- Carousel fraud detection
- Over/under invoicing detection
- Shell company network detection

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
Date: 2026-02-04
"""

import pytest
from unittest.mock import Mock
from datetime import datetime, timezone
from banking.analytics.detect_tbml import (
    TBMLDetector, TBMLAlert, PriceAnomaly
)


class TestTBMLDetectorInitialization:
    """Test TBMLDetector initialization"""
    
    def test_init_default_url(self):
        """Test default JanusGraph URL"""
        detector = TBMLDetector()
        assert detector.url == "ws://localhost:18182/gremlin"
        assert detector.client is None
        assert detector.alerts == []
        
    def test_init_custom_url(self):
        """Test custom JanusGraph URL"""
        custom_url = "ws://custom-host:8182/gremlin"
        detector = TBMLDetector(url=custom_url)
        assert detector.url == custom_url
        
    def test_init_thresholds(self):
        """Test detection thresholds are set correctly"""
        detector = TBMLDetector()
        assert detector.PRICE_DEVIATION_THRESHOLD == 0.20
        assert detector.CIRCULAR_LOOP_MAX_DEPTH == 5
        assert detector.MIN_LOOP_VALUE == 50000.0


class TestCarouselFraudDetection:
    """Test carousel fraud detection methods"""
    
    def test_extract_companies_from_dict(self):
        """Test company extraction from query results"""
        detector = TBMLDetector()
        
        result = {
            'start': {'name': ['Company A']},
            'hop1': {'name': ['Company B']},
            'hop2': {'name': ['Company C']}
        }
        
        companies = detector._extract_companies(result)
        assert 'Company A' in companies
        assert 'Company B' in companies
        assert 'Company C' in companies
        
    def test_extract_companies_empty_dict(self):
        """Test company extraction with empty dict"""
        detector = TBMLDetector()
        companies = detector._extract_companies({})
        assert companies == []
        
    def test_extract_companies_non_dict(self):
        """Test company extraction with non-dict input"""
        detector = TBMLDetector()
        companies = detector._extract_companies("not a dict")
        assert companies == []
        
    def test_extract_transaction_ids(self):
        """Test transaction ID extraction"""
        detector = TBMLDetector()
        
        result = {
            'tx1': 'TX-001',
            'tx2': 'TX-002',
            'tx3': 'TX-003'
        }
        
        tx_ids = detector._extract_transaction_ids(result)
        assert 'TX-001' in tx_ids
        assert 'TX-002' in tx_ids
        assert 'TX-003' in tx_ids
        
    def test_calculate_carousel_risk_base_score(self):
        """Test carousel risk calculation with base values"""
        detector = TBMLDetector()
        
        loop = {
            'depth': 2,
            'companies': ['A', 'B'],
            'transactions': []
        }
        
        risk = detector._calculate_carousel_risk(loop)
        # Base 0.5 + depth 2 * 0.1 + 2 companies * 0.05 = 0.5 + 0.2 + 0.1 = 0.8
        assert risk >= 0.5
        assert risk <= 1.0
        
    def test_calculate_carousel_risk_high_depth(self):
        """Test carousel risk with high depth increases score"""
        detector = TBMLDetector()
        
        low_depth_loop = {'depth': 2, 'companies': ['A', 'B'], 'transactions': []}
        high_depth_loop = {'depth': 5, 'companies': ['A', 'B'], 'transactions': []}
        
        low_risk = detector._calculate_carousel_risk(low_depth_loop)
        high_risk = detector._calculate_carousel_risk(high_depth_loop)
        
        assert high_risk > low_risk


class TestInvoiceManipulationDetection:
    """Test over/under invoicing detection"""
    
    def test_check_price_anomaly_over_invoicing(self):
        """Test detection of over-invoicing"""
        detector = TBMLDetector()
        
        # Mock the market price estimation
        detector._estimate_market_price = Mock(return_value=50000.0)
        
        transaction = {
            'tx_id': 'TX-001',
            'amount': 75000.0,  # 50% over
            'description': 'gold shipment'
        }
        
        anomaly = detector._check_price_anomaly(transaction)
        
        assert anomaly is not None
        assert anomaly.direction == 'over'
        assert anomaly.deviation_percent > 0
        
    def test_check_price_anomaly_under_invoicing(self):
        """Test detection of under-invoicing"""
        detector = TBMLDetector()
        
        detector._estimate_market_price = Mock(return_value=100000.0)
        
        transaction = {
            'tx_id': 'TX-002',
            'amount': 50000.0,  # 50% under
            'description': 'electronics shipment'
        }
        
        anomaly = detector._check_price_anomaly(transaction)
        
        assert anomaly is not None
        assert anomaly.direction == 'under'
        assert anomaly.deviation_percent < 0
        
    def test_check_price_anomaly_within_threshold(self):
        """Test no anomaly when within threshold"""
        detector = TBMLDetector()
        
        detector._estimate_market_price = Mock(return_value=100000.0)
        
        transaction = {
            'tx_id': 'TX-003',
            'amount': 105000.0,  # Only 5% over, within 20% threshold
            'description': 'normal goods'
        }
        
        anomaly = detector._check_price_anomaly(transaction)
        
        assert anomaly is None
        
    def test_estimate_market_price_high_value_keywords(self):
        """Test market price estimation for high-value keywords"""
        detector = TBMLDetector()
        
        # Gold with high declared amount should suggest over-invoicing
        price = detector._estimate_market_price('gold shipment', 150000.0)
        assert price is not None
        assert price < 150000.0  # Should suggest lower market price
        
    def test_estimate_market_price_tech_keywords(self):
        """Test market price estimation for tech keywords"""
        detector = TBMLDetector()
        
        price = detector._estimate_market_price('computer equipment', 75000.0)
        assert price is not None
        
    def test_estimate_market_price_no_keyword(self):
        """Test market price estimation with no matching keywords"""
        detector = TBMLDetector()
        
        price = detector._estimate_market_price('generic item', 1000.0)
        assert price is None  # No anomaly detection without matching keywords


class TestShellCompanyDetection:
    """Test shell company network detection"""
    
    def test_calculate_shell_company_score_flagged(self):
        """Test shell company score when already flagged"""
        detector = TBMLDetector()
        
        company = {
            'is_shell': True,
            'employee_count': 10,
            'registration_date': '2020-01-01',
            'tx_count': 5,
            'country': 'US'
        }
        
        score = detector._calculate_shell_company_score(company)
        assert score >= 0.5  # Flagged adds 0.5
        
    def test_calculate_shell_company_score_low_employees(self):
        """Test shell company score with low employee count"""
        detector = TBMLDetector()
        
        company = {
            'is_shell': False,
            'employee_count': 2,  # Below threshold of 5
            'registration_date': '2020-01-01',
            'tx_count': 5,
            'country': 'US'
        }
        
        score = detector._calculate_shell_company_score(company)
        assert score >= 0.2  # Low employees adds 0.2
        
    def test_calculate_shell_company_score_offshore(self):
        """Test shell company score for offshore jurisdictions"""
        detector = TBMLDetector()
        
        company = {
            'is_shell': False,
            'employee_count': 10,
            'registration_date': '2020-01-01',
            'tx_count': 5,
            'country': 'KY'  # Cayman Islands - high risk
        }
        
        score = detector._calculate_shell_company_score(company)
        assert score >= 0.3  # Offshore adds 0.3
        
    def test_calculate_shell_company_score_multiple_factors(self):
        """Test shell company score with multiple risk factors"""
        detector = TBMLDetector()
        
        company = {
            'is_shell': True,
            'employee_count': 1,
            'registration_date': datetime.now().isoformat(),  # Recent
            'tx_count': 100,
            'country': 'VG'  # British Virgin Islands
        }
        
        score = detector._calculate_shell_company_score(company)
        assert score >= 0.8  # Multiple factors should give high score
        assert score <= 1.0
        
    def test_find_shell_networks_single_company(self):
        """Test network finding with single company (no network)"""
        detector = TBMLDetector()
        
        candidates = [
            {'company': {'name': 'Company A', 'connected_companies': 0}, 'shell_score': 0.8}
        ]
        
        networks = detector._find_shell_networks(candidates)
        assert len(networks) == 0  # Single company doesn't form a network


class TestSeverityCalculation:
    """Test severity level calculations"""
    
    def test_severity_critical(self):
        """Test critical severity for high values"""
        detector = TBMLDetector()
        
        severity = detector._calculate_severity(1500000.0)
        assert severity == 'critical'
        
    def test_severity_high(self):
        """Test high severity"""
        detector = TBMLDetector()
        
        severity = detector._calculate_severity(750000.0)
        assert severity == 'high'
        
    def test_severity_medium(self):
        """Test medium severity"""
        detector = TBMLDetector()
        
        severity = detector._calculate_severity(250000.0)
        assert severity == 'medium'
        
    def test_severity_low(self):
        """Test low severity"""
        detector = TBMLDetector()
        
        severity = detector._calculate_severity(50000.0)
        assert severity == 'low'


class TestReportGeneration:
    """Test report generation"""
    
    def test_generate_report_empty(self):
        """Test report generation with no alerts"""
        detector = TBMLDetector()
        
        report = detector.generate_report()
        
        assert 'report_date' in report
        assert report['total_alerts'] == 0
        assert report['total_value_at_risk'] == 0
        
    def test_generate_report_with_alerts(self):
        """Test report generation with alerts"""
        detector = TBMLDetector()
        
        # Add test alerts
        detector.alerts = [
            TBMLAlert(
                alert_id='TEST-001',
                alert_type='carousel',
                severity='high',
                entities=['Company A', 'Company B'],
                transactions=['TX-001'],
                total_value=500000.0,
                risk_score=0.8,
                indicators=['Test indicator'],
                timestamp=datetime.now(timezone.utc),
                details={}
            ),
            TBMLAlert(
                alert_id='TEST-002',
                alert_type='over_invoicing',
                severity='medium',
                entities=['Company C'],
                transactions=['TX-002'],
                total_value=100000.0,
                risk_score=0.6,
                indicators=['Test indicator'],
                timestamp=datetime.now(timezone.utc),
                details={}
            )
        ]
        
        report = detector.generate_report()
        
        assert report['total_alerts'] == 2
        assert report['alerts_by_type']['carousel'] == 1
        assert report['alerts_by_type']['over_invoicing'] == 1
        assert report['total_value_at_risk'] == 600000.0


class TestDataclasses:
    """Test dataclass definitions"""
    
    def test_tbml_alert_creation(self):
        """Test TBMLAlert dataclass"""
        alert = TBMLAlert(
            alert_id='TBML-001',
            alert_type='carousel',
            severity='high',
            entities=['Company A'],
            transactions=['TX-001'],
            total_value=100000.0,
            risk_score=0.8,
            indicators=['Test'],
            timestamp=datetime.now(timezone.utc),
            details={}
        )
        
        assert alert.alert_id == 'TBML-001'
        assert alert.alert_type == 'carousel'
        assert alert.severity == 'high'
        
    def test_price_anomaly_creation(self):
        """Test PriceAnomaly dataclass"""
        anomaly = PriceAnomaly(
            transaction_id='TX-001',
            declared_price=150000.0,
            market_price=100000.0,
            deviation_percent=50.0,
            direction='over',
            risk_score=0.8
        )
        
        assert anomaly.transaction_id == 'TX-001'
        assert anomaly.direction == 'over'
        assert anomaly.deviation_percent == 50.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
