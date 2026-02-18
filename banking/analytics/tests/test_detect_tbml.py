"""
Unit Tests for TBML Detection Module
=====================================

Tests for Trade-Based Money Laundering detection algorithms including:
- Carousel fraud detection
- Over/under invoicing detection
- Shell company network detection

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
Date: 2026-02-04
Updated: 2026-02-11 (Week 2 Day 9 - Enhanced to 45+ tests, 80%+ coverage)
"""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest

from banking.analytics.detect_tbml import PriceAnomaly, TBMLAlert, TBMLDetector


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
            "start": {"name": ["Company A"]},
            "hop1": {"name": ["Company B"]},
            "hop2": {"name": ["Company C"]},
        }

        companies = detector._extract_companies(result)
        assert "Company A" in companies
        assert "Company B" in companies
        assert "Company C" in companies

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

        result = {"tx1": "TX-001", "tx2": "TX-002", "tx3": "TX-003"}

        tx_ids = detector._extract_transaction_ids(result)
        assert "TX-001" in tx_ids
        assert "TX-002" in tx_ids
        assert "TX-003" in tx_ids

    def test_calculate_carousel_risk_base_score(self):
        """Test carousel risk calculation with base values"""
        detector = TBMLDetector()

        loop = {"depth": 2, "companies": ["A", "B"], "transactions": []}

        risk = detector._calculate_carousel_risk(loop)
        # Base 0.5 + depth 2 * 0.1 + 2 companies * 0.05 = 0.5 + 0.2 + 0.1 = 0.8
        assert risk >= 0.5
        assert risk <= 1.0

    def test_calculate_carousel_risk_high_depth(self):
        """Test carousel risk with high depth increases score"""
        detector = TBMLDetector()

        low_depth_loop = {"depth": 2, "companies": ["A", "B"], "transactions": []}
        high_depth_loop = {"depth": 5, "companies": ["A", "B"], "transactions": []}

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
            "tx_id": "TX-001",
            "amount": 75000.0,  # 50% over
            "description": "gold shipment",
        }

        anomaly = detector._check_price_anomaly(transaction)

        assert anomaly is not None
        assert anomaly.direction == "over"
        assert anomaly.deviation_percent > 0

    def test_check_price_anomaly_under_invoicing(self):
        """Test detection of under-invoicing"""
        detector = TBMLDetector()

        detector._estimate_market_price = Mock(return_value=100000.0)

        transaction = {
            "tx_id": "TX-002",
            "amount": 50000.0,  # 50% under
            "description": "electronics shipment",
        }

        anomaly = detector._check_price_anomaly(transaction)

        assert anomaly is not None
        assert anomaly.direction == "under"
        assert anomaly.deviation_percent < 0

    def test_check_price_anomaly_within_threshold(self):
        """Test no anomaly when within threshold"""
        detector = TBMLDetector()

        detector._estimate_market_price = Mock(return_value=100000.0)

        transaction = {
            "tx_id": "TX-003",
            "amount": 105000.0,  # Only 5% over, within 20% threshold
            "description": "normal goods",
        }

        anomaly = detector._check_price_anomaly(transaction)

        assert anomaly is None

    def test_estimate_market_price_high_value_keywords(self):
        """Test market price estimation for high-value keywords"""
        detector = TBMLDetector()

        # Gold with high declared amount should suggest over-invoicing
        price = detector._estimate_market_price("gold shipment", 150000.0)
        assert price is not None
        assert price < 150000.0  # Should suggest lower market price

    def test_estimate_market_price_tech_keywords(self):
        """Test market price estimation for tech keywords"""
        detector = TBMLDetector()

        price = detector._estimate_market_price("computer equipment", 75000.0)
        assert price is not None

    def test_estimate_market_price_no_keyword(self):
        """Test market price estimation with no matching keywords"""
        detector = TBMLDetector()

        price = detector._estimate_market_price("generic item", 1000.0)
        assert price is None  # No anomaly detection without matching keywords


class TestShellCompanyDetection:
    """Test shell company network detection"""

    def test_calculate_shell_company_score_flagged(self):
        """Test shell company score when already flagged"""
        detector = TBMLDetector()

        company = {
            "is_shell": True,
            "employee_count": 10,
            "registration_date": "2020-01-01",
            "tx_count": 5,
            "country": "US",
        }

        score = detector._calculate_shell_company_score(company)
        assert score >= 0.5  # Flagged adds 0.5

    def test_calculate_shell_company_score_low_employees(self):
        """Test shell company score with low employee count"""
        detector = TBMLDetector()

        company = {
            "is_shell": False,
            "employee_count": 2,  # Below threshold of 5
            "registration_date": "2020-01-01",
            "tx_count": 5,
            "country": "US",
        }

        score = detector._calculate_shell_company_score(company)
        assert score >= 0.2  # Low employees adds 0.2

    def test_calculate_shell_company_score_offshore(self):
        """Test shell company score for offshore jurisdictions"""
        detector = TBMLDetector()

        company = {
            "is_shell": False,
            "employee_count": 10,
            "registration_date": "2020-01-01",
            "tx_count": 5,
            "country": "KY",  # Cayman Islands - high risk
        }

        score = detector._calculate_shell_company_score(company)
        assert score >= 0.3  # Offshore adds 0.3

    def test_calculate_shell_company_score_multiple_factors(self):
        """Test shell company score with multiple risk factors"""
        detector = TBMLDetector()

        company = {
            "is_shell": True,
            "employee_count": 1,
            "registration_date": datetime.now().isoformat(),  # Recent
            "tx_count": 100,
            "country": "VG",  # British Virgin Islands
        }

        score = detector._calculate_shell_company_score(company)
        assert score >= 0.8  # Multiple factors should give high score
        assert score <= 1.0

    def test_find_shell_networks_single_company(self):
        """Test network finding with single company (no network)"""
        detector = TBMLDetector()

        candidates = [
            {"company": {"name": "Company A", "connected_companies": 0}, "shell_score": 0.8}
        ]

        networks = detector._find_shell_networks(candidates)
        assert len(networks) == 0  # Single company doesn't form a network


class TestSeverityCalculation:
    """Test severity level calculations"""

    def test_severity_critical(self):
        """Test critical severity for high values"""
        detector = TBMLDetector()

        severity = detector._calculate_severity(1500000.0)
        assert severity == "critical"

    def test_severity_high(self):
        """Test high severity"""
        detector = TBMLDetector()

        severity = detector._calculate_severity(750000.0)
        assert severity == "high"

    def test_severity_medium(self):
        """Test medium severity"""
        detector = TBMLDetector()

        severity = detector._calculate_severity(250000.0)
        assert severity == "medium"

    def test_severity_low(self):
        """Test low severity"""
        detector = TBMLDetector()

        severity = detector._calculate_severity(50000.0)
        assert severity == "low"


class TestReportGeneration:
    """Test report generation"""

    def test_generate_report_empty(self):
        """Test report generation with no alerts"""
        detector = TBMLDetector()

        report = detector.generate_report()

        assert "report_date" in report
        assert report["total_alerts"] == 0
        assert report["total_value_at_risk"] == 0

    def test_generate_report_with_alerts(self):
        """Test report generation with alerts"""
        detector = TBMLDetector()

        # Add test alerts
        detector.alerts = [
            TBMLAlert(
                alert_id="TEST-001",
                alert_type="carousel",
                severity="high",
                entities=["Company A", "Company B"],
                transactions=["TX-001"],
                total_value=500000.0,
                risk_score=0.8,
                indicators=["Test indicator"],
                timestamp=datetime.now(timezone.utc),
                details={},
            ),
            TBMLAlert(
                alert_id="TEST-002",
                alert_type="over_invoicing",
                severity="medium",
                entities=["Company C"],
                transactions=["TX-002"],
                total_value=100000.0,
                risk_score=0.6,
                indicators=["Test indicator"],
                timestamp=datetime.now(timezone.utc),
                details={},
            ),
        ]

        report = detector.generate_report()

        assert report["total_alerts"] == 2
        assert report["alerts_by_type"]["carousel"] == 1
        assert report["alerts_by_type"]["over_invoicing"] == 1
        assert report["total_value_at_risk"] == 600000.0


class TestDataclasses:
    """Test dataclass definitions"""

    def test_tbml_alert_creation(self):
        """Test TBMLAlert dataclass"""
        alert = TBMLAlert(
            alert_id="TBML-001",
            alert_type="carousel",
            severity="high",
            entities=["Company A"],
            transactions=["TX-001"],
            total_value=100000.0,
            risk_score=0.8,
            indicators=["Test"],
            timestamp=datetime.now(timezone.utc),
            details={},
        )

        assert alert.alert_id == "TBML-001"
        assert alert.alert_type == "carousel"
        assert alert.severity == "high"

    def test_price_anomaly_creation(self):
        """Test PriceAnomaly dataclass"""
        anomaly = PriceAnomaly(
            transaction_id="TX-001",
            declared_price=150000.0,
            market_price=100000.0,
            deviation_percent=50.0,
            direction="over",
            risk_score=0.8,
        )

        assert anomaly.transaction_id == "TX-001"
        assert anomaly.direction == "over"
        assert anomaly.deviation_percent == 50.0


class TestCarouselFraudDetectionAdvanced:
    """Advanced tests for carousel fraud detection"""

    def test_calculate_carousel_risk_high_value(self):
        """Test carousel risk with high transaction value"""
        detector = TBMLDetector()

        low_value_loop = {
            "depth": 3,
            "companies": ["A", "B", "C"],
            "transactions": [{"amount": 50000}],
        }
        high_value_loop = {
            "depth": 3,
            "companies": ["A", "B", "C"],
            "transactions": [{"amount": 600000}],
        }

        low_risk = detector._calculate_carousel_risk(low_value_loop)
        high_risk = detector._calculate_carousel_risk(high_value_loop)

        assert high_risk > low_risk

    def test_calculate_carousel_risk_many_companies(self):
        """Test carousel risk with many companies"""
        detector = TBMLDetector()

        few_companies_loop = {
            "depth": 3,
            "companies": ["A", "B"],
            "transactions": [{"amount": 100000}],
        }
        many_companies_loop = {
            "depth": 3,
            "companies": ["A", "B", "C", "D", "E"],
            "transactions": [{"amount": 100000}],
        }

        few_risk = detector._calculate_carousel_risk(few_companies_loop)
        many_risk = detector._calculate_carousel_risk(many_companies_loop)

        assert many_risk > few_risk

    def test_calculate_carousel_risk_capped_at_one(self):
        """Test carousel risk is capped at 1.0"""
        detector = TBMLDetector()

        extreme_loop = {
            "depth": 5,
            "companies": ["A", "B", "C", "D", "E", "F", "G", "H"],
            "transactions": [{"amount": 2000000}],
        }

        risk = detector._calculate_carousel_risk(extreme_loop)
        assert risk <= 1.0

    def test_extract_companies_with_string_names(self):
        """Test company extraction with string names (not lists)"""
        detector = TBMLDetector()

        result = {
            "start": {"name": "Company A"},  # String, not list
            "hop1": {"name": "Company B"},
        }

        companies = detector._extract_companies(result)
        assert "Company A" in companies
        assert "Company B" in companies

    def test_extract_transaction_ids_non_dict(self):
        """Test transaction ID extraction with non-dict input"""
        detector = TBMLDetector()

        tx_ids = detector._extract_transaction_ids("not a dict")
        assert tx_ids == []


class TestInvoiceManipulationDetectionAdvanced:
    """Advanced tests for invoice manipulation detection"""

    def test_check_price_anomaly_no_market_price(self):
        """Test anomaly check when no market price available"""
        detector = TBMLDetector()

        detector._estimate_market_price = Mock(return_value=None)

        transaction = {
            "tx_id": "TX-001",
            "amount": 100000.0,
            "description": "unknown item",
        }

        anomaly = detector._check_price_anomaly(transaction)
        assert anomaly is None

    def test_check_price_anomaly_zero_market_price(self):
        """Test anomaly check with zero market price"""
        detector = TBMLDetector()

        detector._estimate_market_price = Mock(return_value=0)

        transaction = {
            "tx_id": "TX-001",
            "amount": 100000.0,
            "description": "test item",
        }

        anomaly = detector._check_price_anomaly(transaction)
        assert anomaly is None

    def test_check_price_anomaly_risk_score_calculation(self):
        """Test risk score calculation for price anomalies"""
        detector = TBMLDetector()

        detector._estimate_market_price = Mock(return_value=100000.0)

        # 100% deviation
        transaction = {
            "tx_id": "TX-001",
            "amount": 200000.0,
            "description": "test item",
        }

        anomaly = detector._check_price_anomaly(transaction)
        assert anomaly is not None
        assert anomaly.risk_score <= 1.0  # Should be capped

    def test_estimate_market_price_low_value(self):
        """Test market price estimation with low declared value"""
        detector = TBMLDetector()

        # Low value shouldn't trigger estimation
        price = detector._estimate_market_price("gold shipment", 50000.0)
        assert price is None

    def test_estimate_market_price_multiple_keywords(self):
        """Test market price estimation with multiple keywords"""
        detector = TBMLDetector()

        # Should match first keyword
        price = detector._estimate_market_price("luxury gold jewelry", 200000.0)
        assert price is not None

    def test_check_price_anomaly_exact_threshold(self):
        """Test anomaly detection at exact threshold"""
        detector = TBMLDetector()

        detector._estimate_market_price = Mock(return_value=100000.0)

        # Exactly 20% deviation (at threshold)
        transaction = {
            "tx_id": "TX-001",
            "amount": 120000.0,
            "description": "test item",
        }

        anomaly = detector._check_price_anomaly(transaction)
        assert anomaly is None  # Should not trigger at exact threshold


class TestShellCompanyDetectionAdvanced:
    """Advanced tests for shell company detection"""

    def test_calculate_shell_company_score_recent_incorporation(self):
        """Test shell company score with recent incorporation"""
        detector = TBMLDetector()

        # Very recent incorporation
        recent_date = datetime.now().isoformat()

        company = {
            "is_shell": False,
            "employee_count": 10,
            "registration_date": recent_date,
            "tx_count": 5,
            "country": "US",
        }

        score = detector._calculate_shell_company_score(company)
        assert score >= 0.2  # Recent incorporation adds 0.2

    def test_calculate_shell_company_score_high_tx_ratio(self):
        """Test shell company score with high transaction ratio"""
        detector = TBMLDetector()

        company = {
            "is_shell": False,
            "employee_count": 5,
            "registration_date": "2020-01-01",
            "tx_count": 100,  # 20 tx per employee (> 10 threshold)
            "country": "US",
        }

        score = detector._calculate_shell_company_score(company)
        assert score >= 0.2  # High ratio adds 0.2

    def test_calculate_shell_company_score_invalid_date(self):
        """Test shell company score with invalid registration date"""
        detector = TBMLDetector()

        company = {
            "is_shell": False,
            "employee_count": 10,
            "registration_date": "invalid-date",
            "tx_count": 5,
            "country": "US",
        }

        # Should not crash, just skip date check
        score = detector._calculate_shell_company_score(company)
        assert score >= 0.0

    def test_calculate_shell_company_score_all_high_risk_countries(self):
        """Test shell company score for all high-risk jurisdictions"""
        detector = TBMLDetector()

        high_risk_countries = ["KY", "VG", "PA", "BZ", "SC", "MU"]

        for country in high_risk_countries:
            company = {
                "is_shell": False,
                "employee_count": 10,
                "registration_date": "2020-01-01",
                "tx_count": 5,
                "country": country,
            }

            score = detector._calculate_shell_company_score(company)
            assert score >= 0.3  # Each should add 0.3

    def test_find_shell_networks_multiple_networks(self):
        """Test finding multiple separate networks"""
        detector = TBMLDetector()

        candidates = [
            {"company": {"name": "Company A", "connected_companies": 1}, "shell_score": 0.8},
            {"company": {"name": "Company B", "connected_companies": 1}, "shell_score": 0.7},
            {"company": {"name": "Company C", "connected_companies": 1}, "shell_score": 0.9},
            {"company": {"name": "Company D", "connected_companies": 1}, "shell_score": 0.6},
        ]

        networks = detector._find_shell_networks(candidates)
        assert len(networks) >= 1  # Should find at least one network

    def test_calculate_shell_company_score_zero_employees(self):
        """Test shell company score with zero employees"""
        detector = TBMLDetector()

        company = {
            "is_shell": False,
            "employee_count": 0,
            "registration_date": "2020-01-01",
            "tx_count": 50,
            "country": "US",
        }

        score = detector._calculate_shell_company_score(company)
        assert score >= 0.2  # Zero employees should trigger low employee check


class TestConnectionAndQueryMethods:
    """Test connection and query methods with mocking"""

    @patch("banking.analytics.detect_tbml.client.Client")
    def test_connect_success(self, mock_client_class):
        """Test successful connection to JanusGraph"""
        mock_client = Mock()
        mock_result = Mock()
        mock_result.all.return_value.result.return_value = [1000]
        mock_client.submit.return_value = mock_result
        mock_client_class.return_value = mock_client

        detector = TBMLDetector()
        detector.connect()

        assert detector.client is not None
        mock_client.submit.assert_called_once()

    def test_close_connection(self):
        """Test closing connection"""
        detector = TBMLDetector()
        detector.client = Mock()

        detector.close()

        detector.client.close.assert_called_once()

    def test_close_no_client(self):
        """Test closing when no client exists"""
        detector = TBMLDetector()
        detector.client = None

        # Should not raise exception
        detector.close()


class TestDetectionMethodsWithMocking:
    """Test main detection methods with mocked JanusGraph client"""

    def test_detect_carousel_fraud_with_mock(self):
        """Test carousel fraud detection with mocked client"""
        detector = TBMLDetector()

        # Mock client
        mock_client = Mock()
        mock_result = Mock()
        mock_result.all.return_value.result.return_value = []
        mock_client.submit.return_value = mock_result
        detector.client = mock_client

        alerts = detector.detect_carousel_fraud(max_depth=3)

        assert isinstance(alerts, list)
        # Should query for multiple depths
        assert mock_client.submit.call_count >= 2

    def test_detect_invoice_manipulation_with_mock(self):
        """Test invoice manipulation detection with mocked client"""
        detector = TBMLDetector()

        # Mock client
        mock_client = Mock()
        mock_result = Mock()
        mock_result.all.return_value.result.return_value = [
            {
                "tx_id": "TX-001",
                "amount": 150000,
                "description": "gold shipment",
                "currency": "USD",
                "from_company": "Company A",
                "to_company": "Company B",
            }
        ]
        mock_client.submit.return_value = mock_result
        detector.client = mock_client

        anomalies, alerts = detector.detect_invoice_manipulation()

        assert isinstance(anomalies, list)
        assert isinstance(alerts, list)

    def test_detect_shell_company_networks_with_mock(self):
        """Test shell company network detection with mocked client"""
        detector = TBMLDetector()

        # Mock client
        mock_client = Mock()
        mock_result = Mock()
        mock_result.all.return_value.result.return_value = [
            {
                "id": "C1",
                "name": "Shell Corp A",
                "employee_count": 2,
                "registration_date": datetime.now().isoformat(),
                "is_shell": True,
                "country": "KY",
                "tx_count": 50,
                "tx_total": 500000,
                "connected_companies": 2,
            }
        ]
        mock_client.submit.return_value = mock_result
        detector.client = mock_client

        alerts = detector.detect_shell_company_networks()

        assert isinstance(alerts, list)

    @patch("banking.analytics.detect_tbml.client.Client")
    def test_run_full_scan(self, mock_client_class):
        """Test full scan execution"""
        detector = TBMLDetector()

        # Mock client
        mock_client = Mock()
        mock_result = Mock()
        mock_result.all.return_value.result.return_value = [100]
        mock_client.submit.return_value = mock_result
        mock_client_class.return_value = mock_client

        report = detector.run_full_scan()

        assert isinstance(report, dict)
        assert "report_date" in report
        assert "total_alerts" in report
        mock_client.close.assert_called_once()

    def test_detect_carousel_fraud_with_exception(self):
        """Test carousel fraud detection handles exceptions"""
        detector = TBMLDetector()

        # Mock client that raises exception
        mock_client = Mock()
        mock_client.submit.side_effect = Exception("Connection error")
        detector.client = mock_client

        # Should not raise exception, just log warning
        alerts = detector.detect_carousel_fraud()

        assert alerts == []

    def test_detect_invoice_manipulation_with_exception(self):
        """Test invoice manipulation detection handles exceptions"""
        detector = TBMLDetector()

        # Mock client that raises exception
        mock_client = Mock()
        mock_client.submit.side_effect = Exception("Connection error")
        detector.client = mock_client

        # Should not raise exception, just log warning
        anomalies, alerts = detector.detect_invoice_manipulation()

        assert anomalies == []
        assert alerts == []

    def test_detect_shell_company_networks_with_exception(self):
        """Test shell company detection handles exceptions"""
        detector = TBMLDetector()

        # Mock client that raises exception
        mock_client = Mock()
        mock_client.submit.side_effect = Exception("Connection error")
        detector.client = mock_client

        # Should not raise exception, just log warning
        alerts = detector.detect_shell_company_networks()

        assert alerts == []


class TestSeverityCalculationAdvanced:
    """Advanced tests for severity calculation"""

    def test_severity_boundaries(self):
        """Test severity calculation at boundaries"""
        detector = TBMLDetector()

        assert detector._calculate_severity(1000000) == "critical"
        assert detector._calculate_severity(999999) == "high"
        assert detector._calculate_severity(500000) == "high"
        assert detector._calculate_severity(499999) == "medium"
        assert detector._calculate_severity(100000) == "medium"
        assert detector._calculate_severity(99999) == "low"


class TestReportGenerationAdvanced:
    """Advanced tests for report generation"""

    def test_generate_report_multiple_alert_types(self):
        """Test report with multiple alert types"""
        detector = TBMLDetector()

        detector.alerts = [
            TBMLAlert(
                alert_id="TEST-001",
                alert_type="carousel",
                severity="high",
                entities=["A"],
                transactions=["T1"],
                total_value=500000.0,
                risk_score=0.8,
                indicators=[],
                timestamp=datetime.now(timezone.utc),
                details={},
            ),
            TBMLAlert(
                alert_id="TEST-002",
                alert_type="over_invoicing",
                severity="medium",
                entities=["B"],
                transactions=["T2"],
                total_value=200000.0,
                risk_score=0.6,
                indicators=[],
                timestamp=datetime.now(timezone.utc),
                details={},
            ),
            TBMLAlert(
                alert_id="TEST-003",
                alert_type="under_invoicing",
                severity="low",
                entities=["C"],
                transactions=["T3"],
                total_value=50000.0,
                risk_score=0.4,
                indicators=[],
                timestamp=datetime.now(timezone.utc),
                details={},
            ),
            TBMLAlert(
                alert_id="TEST-004",
                alert_type="shell_network",
                severity="critical",
                entities=["D", "E"],
                transactions=[],
                total_value=1500000.0,
                risk_score=0.9,
                indicators=[],
                timestamp=datetime.now(timezone.utc),
                details={},
            ),
        ]

        report = detector.generate_report()

        assert report["total_alerts"] == 4
        assert report["alerts_by_type"]["carousel"] == 1
        assert report["alerts_by_type"]["over_invoicing"] == 1
        assert report["alerts_by_type"]["under_invoicing"] == 1
        assert report["alerts_by_type"]["shell_network"] == 1
        assert report["alerts_by_severity"]["critical"] == 1
        assert report["alerts_by_severity"]["high"] == 1
        assert report["alerts_by_severity"]["medium"] == 1
        assert report["alerts_by_severity"]["low"] == 1
        assert report["total_value_at_risk"] == 2250000.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
