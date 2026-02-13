"""
Comprehensive Unit Tests for AML Structuring Detector
======================================================

Tests for AML structuring detection algorithms including:
- Transaction amount analysis
- High-volume account identification
- Structuring pattern detection
- Transaction chain analysis
- Risk scoring
- Report generation

Author: David Leconte, IBM Worldwide | Tiger-Team
Date: 2026-02-11
Week 2 Day 7: AML Structuring Detector Tests
"""

from unittest.mock import Mock, patch

import pytest

from banking.analytics.aml_structuring_detector import (
    AMLStructuringDetector,
    CTR_THRESHOLD,
    STRUCTURING_THRESHOLD,
    SUSPICIOUS_TX_COUNT,
)


# ============================================================================
# Initialization Tests
# ============================================================================


class TestAMLStructuringDetectorInitialization:
    """Test AMLStructuringDetector initialization."""

    def test_init_default_url(self):
        """Test default JanusGraph URL."""
        detector = AMLStructuringDetector()
        assert detector.url == "ws://localhost:18182/gremlin"
        assert detector.client is None
        assert detector.findings == {
            "high_risk_accounts": [],
            "suspicious_transactions": [],
            "structuring_patterns": [],
            "summary_stats": {},
        }

    def test_init_custom_url(self):
        """Test custom JanusGraph URL."""
        custom_url = "ws://custom-host:8182/gremlin"
        detector = AMLStructuringDetector(url=custom_url)
        assert detector.url == custom_url

    def test_init_findings_structure(self):
        """Test findings dictionary structure."""
        detector = AMLStructuringDetector()
        assert "high_risk_accounts" in detector.findings
        assert "suspicious_transactions" in detector.findings
        assert "structuring_patterns" in detector.findings
        assert "summary_stats" in detector.findings


# ============================================================================
# Connection Tests
# ============================================================================


class TestAMLStructuringDetectorConnection:
    """Test connection management."""

    def test_connect_success(self, mock_janusgraph_client):
        """Test successful connection."""
        detector = AMLStructuringDetector()
        
        with patch('banking.analytics.aml_structuring_detector.client.Client') as mock_client_class:
            mock_client_class.return_value = mock_janusgraph_client
            mock_janusgraph_client.submit.return_value.all.return_value.result.return_value = [1000]
            
            detector.connect()
            
            assert detector.client is not None
            mock_client_class.assert_called_once()

    def test_close_connection(self, mock_janusgraph_client):
        """Test closing connection."""
        detector = AMLStructuringDetector()
        detector.client = mock_janusgraph_client
        
        detector.close()
        
        mock_janusgraph_client.close.assert_called_once()

    def test_close_without_connection(self):
        """Test closing when no connection exists."""
        detector = AMLStructuringDetector()
        detector.close()  # Should not raise error


# ============================================================================
# Transaction Amount Analysis Tests
# ============================================================================


class TestTransactionAmountAnalysis:
    """Test transaction amount analysis."""

    def test_analyze_empty_transactions(self, mock_janusgraph_client):
        """Test analysis with no transactions."""
        detector = AMLStructuringDetector()
        detector.client = mock_janusgraph_client
        
        # Mock empty result
        mock_janusgraph_client.submit.return_value.all.return_value.result.return_value = []
        
        result = detector.analyze_transaction_amounts()
        
        assert result == {}

    def test_analyze_normal_transactions(self, mock_janusgraph_client):
        """Test analysis with normal transactions."""
        detector = AMLStructuringDetector()
        detector.client = mock_janusgraph_client
        
        # Mock normal transactions
        amounts = [5000, 3000, 2000, 1500, 1000]
        mock_janusgraph_client.submit.return_value.all.return_value.result.return_value = amounts
        
        result = detector.analyze_transaction_amounts()
        
        assert result["total_transactions"] == 5
        assert result["total_amount"] == 12500
        assert result["average_amount"] == 2500
        assert result["min_amount"] == 1000
        assert result["max_amount"] == 5000
        assert result["near_threshold_count"] == 0

    def test_analyze_suspicious_transactions(self, mock_janusgraph_client):
        """Test analysis with suspicious transactions near threshold."""
        detector = AMLStructuringDetector()
        detector.client = mock_janusgraph_client
        
        # Mock suspicious transactions (just under $10K)
        amounts = [9500, 9800, 9700, 9600, 5000]
        mock_janusgraph_client.submit.return_value.all.return_value.result.return_value = amounts
        
        result = detector.analyze_transaction_amounts()
        
        assert result["total_transactions"] == 5
        assert result["near_threshold_count"] == 4  # 4 transactions between $9.5K-$10K
        assert result["distribution"]["9k_to_10k (SUSPICIOUS)"] == 4

    def test_analyze_boundary_cases(self, mock_janusgraph_client):
        """Test analysis with boundary values."""
        detector = AMLStructuringDetector()
        detector.client = mock_janusgraph_client
        
        # Boundary cases: exactly at thresholds
        amounts = [9999.99, 10000.00, 9500.00, 9000.00]
        mock_janusgraph_client.submit.return_value.all.return_value.result.return_value = amounts
        
        result = detector.analyze_transaction_amounts()
        
        # 9999.99 and 9500.00 are in suspicious range
        assert result["near_threshold_count"] == 2
        # 9999.99, 9500.00, 9000.00 are in 9k-10k range
        assert result["distribution"]["9k_to_10k (SUSPICIOUS)"] == 3
        # 10000.00 is above threshold
        assert result["distribution"]["above_10k"] == 1

    def test_analyze_distribution_calculation(self, mock_janusgraph_client):
        """Test distribution calculation across all ranges."""
        detector = AMLStructuringDetector()
        detector.client = mock_janusgraph_client
        
        amounts = [
            500,    # under_1k
            2000,   # 1k_to_5k
            6000,   # 5k_to_9k
            9500,   # 9k_to_10k (suspicious)
            15000   # above_10k
        ]
        mock_janusgraph_client.submit.return_value.all.return_value.result.return_value = amounts
        
        result = detector.analyze_transaction_amounts()
        
        dist = result["distribution"]
        assert dist["under_1k"] == 1
        assert dist["1k_to_5k"] == 1
        assert dist["5k_to_9k"] == 1
        assert dist["9k_to_10k (SUSPICIOUS)"] == 1
        assert dist["above_10k"] == 1

    def test_analyze_stores_in_findings(self, mock_janusgraph_client):
        """Test that analysis results are stored in findings."""
        detector = AMLStructuringDetector()
        detector.client = mock_janusgraph_client
        
        amounts = [5000, 3000]
        mock_janusgraph_client.submit.return_value.all.return_value.result.return_value = amounts
        
        detector.analyze_transaction_amounts()
        
        assert "summary_stats" in detector.findings
        assert detector.findings["summary_stats"]["total_transactions"] == 2


# ============================================================================
# High-Volume Account Tests
# ============================================================================


class TestHighVolumeAccountIdentification:
    """Test high-volume account identification."""

    def test_identify_high_volume_accounts_success(self, mock_janusgraph_client):
        """Test identifying high-volume accounts."""
        detector = AMLStructuringDetector()
        detector.client = mock_janusgraph_client
        
        # Mock high-volume account data
        mock_results = [
            {"account_id": "acc-1", "sent": 15, "received": 10},
            {"account_id": "acc-2", "sent": 8, "received": 7},
            {"account_id": "acc-3", "sent": 3, "received": 2},
        ]
        mock_janusgraph_client.submit.return_value.all.return_value.result.return_value = mock_results
        
        result = detector.identify_high_volume_accounts()
        
        assert len(result) == 2  # Only accounts with total > 5
        assert result[0]["account_id"] == "acc-1"
        assert result[0]["total_transactions"] == 25
        assert result[0]["risk_level"] == "HIGH"  # > 20 transactions

    def test_identify_medium_risk_accounts(self, mock_janusgraph_client):
        """Test identifying medium-risk accounts."""
        detector = AMLStructuringDetector()
        detector.client = mock_janusgraph_client
        
        mock_results = [
            {"account_id": "acc-1", "sent": 8, "received": 7},
        ]
        mock_janusgraph_client.submit.return_value.all.return_value.result.return_value = mock_results
        
        result = detector.identify_high_volume_accounts()
        
        assert len(result) == 1
        assert result[0]["risk_level"] == "MEDIUM"  # 15 transactions (< 20)

    def test_identify_filters_low_volume(self, mock_janusgraph_client):
        """Test that low-volume accounts are filtered out."""
        detector = AMLStructuringDetector()
        detector.client = mock_janusgraph_client
        
        mock_results = [
            {"account_id": "acc-1", "sent": 2, "received": 2},  # Total = 4, should be filtered
        ]
        mock_janusgraph_client.submit.return_value.all.return_value.result.return_value = mock_results
        
        result = detector.identify_high_volume_accounts()
        
        assert len(result) == 0  # Filtered out (total <= 5)

    def test_identify_handles_exception_fallback(self, mock_janusgraph_client):
        """Test fallback query when primary query fails."""
        detector = AMLStructuringDetector()
        detector.client = mock_janusgraph_client
        
        # First call raises exception, second call succeeds
        mock_janusgraph_client.submit.side_effect = [
            Exception("Query failed"),
            Mock(all=Mock(return_value=Mock(result=Mock(return_value=[
                {"account_id": "acc-1", "sent": 10, "received": 8}
            ]))))
        ]
        
        result = detector.identify_high_volume_accounts()
        
        assert len(result) == 1
        assert result[0]["account_id"] == "acc-1"

    def test_identify_stores_in_findings(self, mock_janusgraph_client):
        """Test that results are stored in findings."""
        detector = AMLStructuringDetector()
        detector.client = mock_janusgraph_client
        
        mock_results = [{"account_id": "acc-1", "sent": 10, "received": 8}]
        mock_janusgraph_client.submit.return_value.all.return_value.result.return_value = mock_results
        
        detector.identify_high_volume_accounts()
        
        assert len(detector.findings["high_risk_accounts"]) == 1


# ============================================================================
# Structuring Pattern Detection Tests
# ============================================================================


class TestStructuringPatternDetection:
    """Test structuring pattern detection."""

    def test_detect_structuring_pattern_success(self, mock_janusgraph_client):
        """Test detecting structuring patterns."""
        detector = AMLStructuringDetector()
        detector.client = mock_janusgraph_client
        
        # Mock structuring pattern: account with multiple near-threshold transactions
        mock_results = [{"acc-1": 3}]  # 3 transactions in suspicious range
        mock_janusgraph_client.submit.return_value.all.return_value.result.return_value = mock_results
        
        result = detector.detect_structuring_patterns()
        
        assert len(result) == 1
        assert result[0]["account_id"] == "acc-1"
        assert result[0]["suspicious_tx_count"] == 3
        assert result[0]["pattern"] == "STRUCTURING"
        assert result[0]["risk_level"] == "HIGH"
        assert "SAR" in result[0]["recommendation"]

    def test_detect_no_patterns(self, mock_janusgraph_client):
        """Test when no structuring patterns are found."""
        detector = AMLStructuringDetector()
        detector.client = mock_janusgraph_client
        
        mock_janusgraph_client.submit.return_value.all.return_value.result.return_value = []
        
        result = detector.detect_structuring_patterns()
        
        assert len(result) == 0

    def test_detect_uses_fallback_on_exception(self, mock_janusgraph_client):
        """Test fallback logic when complex query fails."""
        detector = AMLStructuringDetector()
        detector.client = mock_janusgraph_client
        
        # First call (complex query) raises exception
        # Second call (get accounts) returns account list
        # Third call (count query) returns count
        call_count = [0]
        
        def side_effect_func(query):
            call_count[0] += 1
            mock_result = Mock()
            
            if call_count[0] == 1:
                # First call: complex query fails
                raise Exception("Complex query failed")
            elif call_count[0] == 2:
                # Second call: get account list
                mock_result.all.return_value.result.return_value = ["acc-1", "acc-2"]
            else:
                # Subsequent calls: count queries
                mock_result.all.return_value.result.return_value = [2]  # 2 suspicious transactions
            
            return mock_result
        
        mock_janusgraph_client.submit.side_effect = side_effect_func
        
        result = detector.detect_structuring_patterns()
        
        assert len(result) >= 1  # Should find patterns using fallback

    def test_detect_stores_in_findings(self, mock_janusgraph_client):
        """Test that patterns are stored in findings."""
        detector = AMLStructuringDetector()
        detector.client = mock_janusgraph_client
        
        mock_results = [{"acc-1": 3}]
        mock_janusgraph_client.submit.return_value.all.return_value.result.return_value = mock_results
        
        detector.detect_structuring_patterns()
        
        assert len(detector.findings["structuring_patterns"]) == 1


# ============================================================================
# Transaction Chain Analysis Tests
# ============================================================================


class TestTransactionChainAnalysis:
    """Test transaction chain analysis (layering detection)."""

    def test_analyze_chains_success(self, mock_janusgraph_client):
        """Test analyzing transaction chains."""
        detector = AMLStructuringDetector()
        detector.client = mock_janusgraph_client
        
        # Mock 2-hop transaction chains
        mock_results = [
            {"start": "acc-1", "middle": "acc-2", "end": "acc-3"},
            {"start": "acc-4", "middle": "acc-5", "end": "acc-6"},
        ]
        mock_janusgraph_client.submit.return_value.all.return_value.result.return_value = mock_results
        
        result = detector.analyze_transaction_chains()
        
        assert len(result) == 2
        assert result[0]["source"] == "acc-1"
        assert result[0]["intermediate"] == "acc-2"
        assert result[0]["destination"] == "acc-3"
        assert result[0]["hops"] == 2

    def test_analyze_chains_no_results(self, mock_janusgraph_client):
        """Test when no chains are found."""
        detector = AMLStructuringDetector()
        detector.client = mock_janusgraph_client
        
        mock_janusgraph_client.submit.return_value.all.return_value.result.return_value = []
        
        result = detector.analyze_transaction_chains()
        
        assert len(result) == 0

    def test_analyze_chains_handles_exception(self, mock_janusgraph_client):
        """Test exception handling in chain analysis."""
        detector = AMLStructuringDetector()
        detector.client = mock_janusgraph_client
        
        mock_janusgraph_client.submit.side_effect = Exception("Query failed")
        
        result = detector.analyze_transaction_chains()
        
        assert len(result) == 0  # Should return empty list on error

    def test_analyze_chains_stores_in_findings(self, mock_janusgraph_client):
        """Test that chains are stored in findings."""
        detector = AMLStructuringDetector()
        detector.client = mock_janusgraph_client
        
        mock_results = [{"start": "acc-1", "middle": "acc-2", "end": "acc-3"}]
        mock_janusgraph_client.submit.return_value.all.return_value.result.return_value = mock_results
        
        detector.analyze_transaction_chains()
        
        assert "transaction_chains" in detector.findings
        assert len(detector.findings["transaction_chains"]) == 1


# ============================================================================
# Report Generation Tests
# ============================================================================


class TestReportGeneration:
    """Test report generation."""

    def test_generate_report_empty_findings(self):
        """Test report generation with no findings."""
        detector = AMLStructuringDetector()
        
        report = detector.generate_report()
        
        # Report text doesn't include the printed header, just the content
        assert "EXECUTIVE SUMMARY" in report
        assert "RECOMMENDATIONS" in report
        assert "No immediate SAR filings required" in report

    def test_generate_report_with_findings(self):
        """Test report generation with findings."""
        detector = AMLStructuringDetector()
        
        # Populate findings
        detector.findings = {
            "summary_stats": {
                "total_transactions": 100,
                "total_amount": 500000,
                "distribution": {"9k_to_10k (SUSPICIOUS)": 5},
                "near_threshold_total": 48000,
            },
            "structuring_patterns": [
                {
                    "account_id": "acc-1",
                    "suspicious_tx_count": 3,
                    "recommendation": "File SAR",
                }
            ],
            "high_risk_accounts": [
                {"account_id": "acc-2", "total_transactions": 25}
            ],
        }
        
        report = detector.generate_report()
        
        assert "Total Transactions Analyzed: 100" in report
        assert "Structuring Patterns Found: 1" in report
        assert "High-Risk Accounts: 1" in report
        assert "STRUCTURING ALERTS" in report
        assert "File Suspicious Activity Reports" in report

    def test_generate_report_no_sar_needed(self):
        """Test report when no SAR filing is needed."""
        detector = AMLStructuringDetector()
        
        detector.findings = {
            "summary_stats": {"total_transactions": 50, "total_amount": 100000},
            "structuring_patterns": [],
            "high_risk_accounts": [],
        }
        
        report = detector.generate_report()
        
        assert "No immediate SAR filings required" in report
        assert "Continue routine monitoring" in report


# ============================================================================
# Full Analysis Tests
# ============================================================================


class TestFullAnalysis:
    """Test full analysis workflow."""

    def test_run_full_analysis_success(self, mock_janusgraph_client):
        """Test running full analysis."""
        detector = AMLStructuringDetector()
        
        with patch('banking.analytics.aml_structuring_detector.client.Client') as mock_client_class:
            mock_client_class.return_value = mock_janusgraph_client
            
            # Mock all query responses
            mock_janusgraph_client.submit.return_value.all.return_value.result.return_value = [1000]
            
            result = detector.run_full_analysis()
            
            assert "summary_stats" in result
            assert "high_risk_accounts" in result
            assert "structuring_patterns" in result
            mock_janusgraph_client.close.assert_called_once()

    def test_run_full_analysis_closes_on_exception(self, mock_janusgraph_client):
        """Test that connection is closed even on exception."""
        detector = AMLStructuringDetector()
        
        with patch('banking.analytics.aml_structuring_detector.client.Client') as mock_client_class:
            mock_client_class.return_value = mock_janusgraph_client
            mock_janusgraph_client.submit.side_effect = Exception("Query failed")
            
            with pytest.raises(Exception):
                detector.run_full_analysis()
            
            mock_janusgraph_client.close.assert_called_once()


# ============================================================================
# Property-Based Tests (using Hypothesis)
# ============================================================================


try:
    from hypothesis import given, strategies as st
    
    class TestAMLPropertyBased:
        """Property-based tests for AML detection."""
        
        @given(st.lists(st.floats(min_value=0, max_value=20000, allow_nan=False), min_size=1, max_size=100))
        def test_transaction_analysis_always_returns_valid_stats(self, amounts):
            """Test that transaction analysis always returns valid statistics."""
            from unittest.mock import Mock
            mock_client = Mock()
            detector = AMLStructuringDetector()
            detector.client = mock_client
            
            mock_client.submit.return_value.all.return_value.result.return_value = amounts
            
            result = detector.analyze_transaction_amounts()
            
            assert "total_transactions" in result
            assert "total_amount" in result
            assert "average_amount" in result
            assert "distribution" in result
            
            assert result["total_transactions"] == len(amounts)
            assert result["total_amount"] >= 0
            assert result["average_amount"] >= 0
        
        @given(st.integers(min_value=1, max_value=100))
        def test_suspicious_count_never_exceeds_total(self, total_count):
            """Test that suspicious transaction count never exceeds total."""
            from unittest.mock import Mock
            mock_client = Mock()
            detector = AMLStructuringDetector()
            detector.client = mock_client
            
            amounts = [9500] * (total_count // 2) + [5000] * (total_count - total_count // 2)
            mock_client.submit.return_value.all.return_value.result.return_value = amounts
            
            result = detector.analyze_transaction_amounts()
            
            suspicious = result["distribution"]["9k_to_10k (SUSPICIOUS)"]
            assert suspicious <= result["total_transactions"]

except ImportError:
    # Hypothesis not installed, skip property-based tests
    pass


# ============================================================================
# Edge Case Tests
# ============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_single_transaction(self, mock_janusgraph_client):
        """Test analysis with single transaction."""
        detector = AMLStructuringDetector()
        detector.client = mock_janusgraph_client
        
        mock_janusgraph_client.submit.return_value.all.return_value.result.return_value = [5000]
        
        result = detector.analyze_transaction_amounts()
        
        assert result["total_transactions"] == 1
        assert result["min_amount"] == result["max_amount"] == 5000

    def test_all_transactions_above_threshold(self, mock_janusgraph_client):
        """Test when all transactions are above CTR threshold."""
        detector = AMLStructuringDetector()
        detector.client = mock_janusgraph_client
        
        amounts = [15000, 20000, 25000]
        mock_janusgraph_client.submit.return_value.all.return_value.result.return_value = amounts
        
        result = detector.analyze_transaction_amounts()
        
        assert result["near_threshold_count"] == 0
        assert result["distribution"]["above_10k"] == 3

    def test_all_transactions_below_threshold(self, mock_janusgraph_client):
        """Test when all transactions are well below threshold."""
        detector = AMLStructuringDetector()
        detector.client = mock_janusgraph_client
        
        amounts = [1000, 2000, 3000]
        mock_janusgraph_client.submit.return_value.all.return_value.result.return_value = amounts
        
        result = detector.analyze_transaction_amounts()
        
        assert result["near_threshold_count"] == 0
        assert result["distribution"]["9k_to_10k (SUSPICIOUS)"] == 0

    def test_exact_threshold_values(self, mock_janusgraph_client):
        """Test transactions at exact threshold values."""
        detector = AMLStructuringDetector()
        detector.client = mock_janusgraph_client
        
        amounts = [
            STRUCTURING_THRESHOLD,  # Exactly at structuring threshold
            CTR_THRESHOLD,          # Exactly at CTR threshold
        ]
        mock_janusgraph_client.submit.return_value.all.return_value.result.return_value = amounts
        
        result = detector.analyze_transaction_amounts()
        
        # STRUCTURING_THRESHOLD (9500) should be in near_threshold
        # CTR_THRESHOLD (10000) should be above threshold
        assert result["near_threshold_count"] == 1
        assert result["distribution"]["above_10k"] == 1


# ============================================================================
# Constants Tests
# ============================================================================


class TestConstants:
    """Test AML constants are correctly defined."""

    def test_ctr_threshold(self):
        """Test CTR threshold is $10,000."""
        assert CTR_THRESHOLD == 10000.0

    def test_structuring_threshold(self):
        """Test structuring threshold is $9,500."""
        assert STRUCTURING_THRESHOLD == 9500.0

    def test_suspicious_tx_count(self):
        """Test suspicious transaction count threshold."""
        assert SUSPICIOUS_TX_COUNT == 3

    def test_thresholds_relationship(self):
        """Test that structuring threshold is below CTR threshold."""
        assert STRUCTURING_THRESHOLD < CTR_THRESHOLD

# Made with Bob
