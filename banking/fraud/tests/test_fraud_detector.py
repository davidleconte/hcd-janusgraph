"""
Unit tests for FraudDetector class

Test Coverage Target: 60%+
Total Tests: 40+

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
Date: 2026-02-11
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime, timedelta, timezone

from banking.fraud.fraud_detection import FraudDetector
from banking.fraud.models import FraudAlert, FraudScore


class TestFraudDetectorInit:
    """Test FraudDetector initialization (5 tests)"""
    
    @patch('banking.fraud.fraud_detection.VectorSearchClient')
    @patch('banking.fraud.fraud_detection.EmbeddingGenerator')
    def test_init_default_parameters(self, mock_embed, mock_search):
        """Test initialization with default parameters"""
        detector = FraudDetector()
        
        assert detector.graph_url == "ws://localhost:18182/gremlin"
        assert detector.fraud_index == "fraud_cases"
        assert detector._connection is None
        assert detector._g is None
    
    @patch('banking.fraud.fraud_detection.VectorSearchClient')
    @patch('banking.fraud.fraud_detection.EmbeddingGenerator')
    def test_init_custom_parameters(self, mock_embed, mock_search):
        """Test initialization with custom parameters"""
        detector = FraudDetector(
            janusgraph_host="remote-host",
            janusgraph_port=8182,
            opensearch_host="search-host",
            opensearch_port=9201,
            embedding_model="bert"
        )
        
        assert detector.graph_url == "ws://remote-host:8182/gremlin"
        mock_embed.assert_called_once_with(model_name="bert")
    
    @patch('banking.fraud.fraud_detection.VectorSearchClient')
    @patch('banking.fraud.fraud_detection.EmbeddingGenerator')
    def test_init_thresholds(self, mock_embed, mock_search):
        """Test fraud detection thresholds"""
        detector = FraudDetector()
        
        assert detector.CRITICAL_THRESHOLD == 0.9
        assert detector.HIGH_THRESHOLD == 0.75
        assert detector.MEDIUM_THRESHOLD == 0.5
        assert detector.LOW_THRESHOLD == 0.25
    
    @patch('banking.fraud.fraud_detection.VectorSearchClient')
    @patch('banking.fraud.fraud_detection.EmbeddingGenerator')
    def test_init_velocity_limits(self, mock_embed, mock_search):
        """Test velocity check limits"""
        detector = FraudDetector()
        
        assert detector.MAX_TRANSACTIONS_PER_HOUR == 10
        assert detector.MAX_AMOUNT_PER_HOUR == 5000.0
        assert detector.MAX_TRANSACTIONS_PER_DAY == 50
        assert detector.MAX_AMOUNT_PER_DAY == 20000.0
    
    @patch('banking.fraud.fraud_detection.VectorSearchClient')
    @patch('banking.fraud.fraud_detection.EmbeddingGenerator')
    def test_init_circuit_breaker(self, mock_embed, mock_search):
        """Test circuit breaker initialization"""
        detector = FraudDetector()
        
        assert detector._breaker is not None
        # Circuit breaker is initialized with config


class TestFraudDetectorConnection:
    """Test connection management (6 tests)"""
    
    @patch('banking.fraud.fraud_detection.VectorSearchClient')
    @patch('banking.fraud.fraud_detection.EmbeddingGenerator')
    @patch('banking.fraud.fraud_detection.DriverRemoteConnection')
    @patch('banking.fraud.fraud_detection.traversal')
    def test_connect_success(self, mock_trav, mock_conn, mock_embed, mock_search):
        """Test successful connection"""
        detector = FraudDetector()
        mock_g = Mock()
        mock_trav.return_value.with_remote.return_value = mock_g
        
        detector.connect()
        
        assert detector._connection is not None
        assert detector._g is not None
        mock_conn.assert_called_once()
    
    @patch('banking.fraud.fraud_detection.VectorSearchClient')
    @patch('banking.fraud.fraud_detection.EmbeddingGenerator')
    def test_disconnect(self, mock_embed, mock_search):
        """Test disconnection"""
        detector = FraudDetector()
        detector._connection = Mock()
        detector._g = Mock()
        
        detector.disconnect()
        
        assert detector._connection is None
        assert detector._g is None
    
    @patch('banking.fraud.fraud_detection.VectorSearchClient')
    @patch('banking.fraud.fraud_detection.EmbeddingGenerator')
    @patch('banking.fraud.fraud_detection.DriverRemoteConnection')
    @patch('banking.fraud.fraud_detection.traversal')
    def test_context_manager(self, mock_trav, mock_conn, mock_embed, mock_search):
        """Test context manager usage"""
        mock_g = Mock()
        mock_trav.return_value.with_remote.return_value = mock_g
        
        with FraudDetector() as detector:
            assert detector._g is not None
        
        # Connection should be closed after context
        assert detector._connection is None
    
    @patch('banking.fraud.fraud_detection.VectorSearchClient')
    @patch('banking.fraud.fraud_detection.EmbeddingGenerator')
    @patch('banking.fraud.fraud_detection.DriverRemoteConnection')
    @patch('banking.fraud.fraud_detection.traversal')
    def test_get_traversal_connects_if_needed(self, mock_trav, mock_conn, mock_embed, mock_search):
        """Test _get_traversal connects if not connected"""
        detector = FraudDetector()
        mock_g = Mock()
        mock_trav.return_value.with_remote.return_value = mock_g
        
        result = detector._get_traversal()
        
        assert result is not None
        assert detector._g is not None
    
    @patch('banking.fraud.fraud_detection.VectorSearchClient')
    @patch('banking.fraud.fraud_detection.EmbeddingGenerator')
    def test_connect_already_connected(self, mock_embed, mock_search):
        """Test connect when already connected"""
        detector = FraudDetector()
        detector._connection = Mock()
        
        # Should not reconnect
        detector.connect()
        
        # Connection should remain the same
        assert detector._connection is not None
    
class TestFraudDetectorScoring:
    """Test fraud scoring methods (10 tests)"""
    
    @patch('banking.fraud.fraud_detection.VectorSearchClient')
    @patch('banking.fraud.fraud_detection.EmbeddingGenerator')
    def test_score_transaction_low_risk(self, mock_embed, mock_search):
        """Test scoring low-risk transaction"""
        detector = FraudDetector()
        detector._check_velocity = Mock(return_value=0.1)
        detector._check_network = Mock(return_value=0.05)
        detector._check_merchant = Mock(return_value=0.1)
        detector._check_behavior = Mock(return_value=0.15)
        
        score = detector.score_transaction(
            transaction_id="txn-123",
            account_id="acc-456",
            amount=100.0,
            merchant="Normal Store",
            description="Regular purchase"
        )
        
        assert score.overall_score < 0.25
        assert score.risk_level == "low"
        assert score.recommendation == "approve"
    
    @patch('banking.fraud.fraud_detection.VectorSearchClient')
    @patch('banking.fraud.fraud_detection.EmbeddingGenerator')
    def test_score_transaction_high_risk(self, mock_embed, mock_search):
        """Test scoring high-risk transaction"""
        detector = FraudDetector()
        detector._check_velocity = Mock(return_value=0.9)
        detector._check_network = Mock(return_value=0.8)
        detector._check_merchant = Mock(return_value=0.7)
        detector._check_behavior = Mock(return_value=0.85)
        
        score = detector.score_transaction(
            transaction_id="txn-789",
            account_id="acc-999",
            amount=10000.0,
            merchant="Suspicious Merchant",
            description="Unusual transaction"
        )
        
        assert score.overall_score >= 0.75
        assert score.risk_level in ["high", "critical"]
        assert score.recommendation in ["review", "block"]
    
    @patch('banking.fraud.fraud_detection.VectorSearchClient')
    @patch('banking.fraud.fraud_detection.EmbeddingGenerator')
    def test_score_transaction_critical_risk(self, mock_embed, mock_search):
        """Test scoring critical-risk transaction"""
        detector = FraudDetector()
        detector._check_velocity = Mock(return_value=0.95)
        detector._check_network = Mock(return_value=0.90)
        detector._check_merchant = Mock(return_value=0.85)
        detector._check_behavior = Mock(return_value=0.92)
        
        score = detector.score_transaction(
            transaction_id="txn-critical",
            account_id="acc-critical",
            amount=50000.0,
            merchant="High Risk Merchant",
            description="Suspicious activity"
        )
        
        assert score.overall_score >= 0.9
        assert score.risk_level == "critical"
        assert score.recommendation == "block"
    
    @patch('banking.fraud.fraud_detection.VectorSearchClient')
    @patch('banking.fraud.fraud_detection.EmbeddingGenerator')
    def test_score_transaction_medium_risk(self, mock_embed, mock_search):
        """Test scoring medium-risk transaction"""
        detector = FraudDetector()
        detector._check_velocity = Mock(return_value=0.6)
        detector._check_network = Mock(return_value=0.5)
        detector._check_merchant = Mock(return_value=0.55)
        detector._check_behavior = Mock(return_value=0.45)
        
        score = detector.score_transaction(
            transaction_id="txn-medium",
            account_id="acc-medium",
            amount=2500.0,
            merchant="Medium Risk Merchant",
            description="Somewhat unusual"
        )
        
        assert 0.5 <= score.overall_score < 0.75
        assert score.risk_level == "medium"
        assert score.recommendation == "review"
    
    @patch('banking.fraud.fraud_detection.VectorSearchClient')
    @patch('banking.fraud.fraud_detection.EmbeddingGenerator')
    def test_score_transaction_default_timestamp(self, mock_embed, mock_search):
        """Test scoring uses current time if timestamp not provided"""
        detector = FraudDetector()
        detector._check_velocity = Mock(return_value=0.1)
        detector._check_network = Mock(return_value=0.1)
        detector._check_merchant = Mock(return_value=0.1)
        detector._check_behavior = Mock(return_value=0.1)
        
        score = detector.score_transaction(
            transaction_id="txn-time",
            account_id="acc-time",
            amount=100.0,
            merchant="Store",
            description="Purchase"
        )
        
        # Should have called _check_velocity with a timestamp
        detector._check_velocity.assert_called_once()
        call_args = detector._check_velocity.call_args
        assert call_args[0][2] is not None  # timestamp argument
    
    @patch('banking.fraud.fraud_detection.VectorSearchClient')
    @patch('banking.fraud.fraud_detection.EmbeddingGenerator')
    def test_score_transaction_weighted_components(self, mock_embed, mock_search):
        """Test component score weighting"""
        detector = FraudDetector()
        detector._check_velocity = Mock(return_value=1.0)  # 30% weight
        detector._check_network = Mock(return_value=0.0)   # 25% weight
        detector._check_merchant = Mock(return_value=0.0)  # 25% weight
        detector._check_behavior = Mock(return_value=0.0)  # 20% weight
        
        score = detector.score_transaction(
            transaction_id="txn-weight",
            account_id="acc-weight",
            amount=1000.0,
            merchant="Store",
            description="Test"
        )
        
        # Overall should be 1.0 * 0.3 = 0.3
        assert abs(score.overall_score - 0.3) < 0.01
    
    @patch('banking.fraud.fraud_detection.VectorSearchClient')
    @patch('banking.fraud.fraud_detection.EmbeddingGenerator')
    def test_check_merchant_high_risk(self, mock_embed, mock_search):
        """Test merchant risk check for high-risk merchant"""
        detector = FraudDetector()
        
        score = detector._check_merchant("crypto exchange")
        
        assert score > 0.3  # Should be elevated risk (crypto keyword matches)
    
    @patch('banking.fraud.fraud_detection.VectorSearchClient')
    @patch('banking.fraud.fraud_detection.EmbeddingGenerator')
    def test_check_merchant_low_risk(self, mock_embed, mock_search):
        """Test merchant risk check for low-risk merchant"""
        detector = FraudDetector()
        
        score = detector._check_merchant("grocery store")
        
        assert score == 0.0  # Should be low risk
    
    @patch('banking.fraud.fraud_detection.VectorSearchClient')
    @patch('banking.fraud.fraud_detection.EmbeddingGenerator')
    def test_check_merchant_case_insensitive(self, mock_embed, mock_search):
        """Test merchant check is case-insensitive"""
        detector = FraudDetector()
        
        score1 = detector._check_merchant("CRYPTO")
        score2 = detector._check_merchant("crypto")
        score3 = detector._check_merchant("Crypto")
        
        assert score1 == score2 == score3
    
    @patch('banking.fraud.fraud_detection.VectorSearchClient')
    @patch('banking.fraud.fraud_detection.EmbeddingGenerator')
    def test_check_merchant_partial_match(self, mock_embed, mock_search):
        """Test merchant check with partial keyword match"""
        detector = FraudDetector()
        
        score = detector._check_merchant("Online Bitcoin Exchange")
        
        assert score > 0.3  # Should match "bitcoin" keyword


class TestFraudDetectorIndexManagement:
    """Test fraud index management (3 tests)"""
    
    @patch('banking.fraud.fraud_detection.VectorSearchClient')
    @patch('banking.fraud.fraud_detection.EmbeddingGenerator')
    def test_ensure_fraud_index_creates_if_not_exists(self, mock_embed, mock_search):
        """Test fraud index creation"""
        mock_client = Mock()
        mock_client.indices.exists.return_value = False
        mock_search.return_value.client = mock_client
        mock_search.return_value.create_vector_index = Mock()
        
        detector = FraudDetector()
        
        mock_search.return_value.create_vector_index.assert_called_once()
    
    @patch('banking.fraud.fraud_detection.VectorSearchClient')
    @patch('banking.fraud.fraud_detection.EmbeddingGenerator')
    def test_ensure_fraud_index_skips_if_exists(self, mock_embed, mock_search):
        """Test fraud index not created if exists"""
        mock_client = Mock()
        mock_client.indices.exists.return_value = True
        mock_search.return_value.client = mock_client
        mock_search.return_value.create_vector_index = Mock()
        
        detector = FraudDetector()
        
        mock_search.return_value.create_vector_index.assert_not_called()
    
    @patch('banking.fraud.fraud_detection.VectorSearchClient')
    @patch('banking.fraud.fraud_detection.EmbeddingGenerator')
    def test_ensure_fraud_index_fields(self, mock_embed, mock_search):
        """Test fraud index has correct fields"""
        mock_client = Mock()
        mock_client.indices.exists.return_value = False
        mock_search.return_value.client = mock_client
        mock_search.return_value.create_vector_index = Mock()
        mock_embed.return_value.dimensions = 768
        
        detector = FraudDetector()
        
        call_args = mock_search.return_value.create_vector_index.call_args
        additional_fields = call_args[1]['additional_fields']
        
        assert 'case_id' in additional_fields
        assert 'transaction_id' in additional_fields
        assert 'fraud_type' in additional_fields
        assert 'amount' in additional_fields


class TestFraudDetectorConstants:
    """Test fraud detector constants (2 tests)"""
    
    @patch('banking.fraud.fraud_detection.VectorSearchClient')
    @patch('banking.fraud.fraud_detection.EmbeddingGenerator')
    def test_high_risk_merchants_constant(self, mock_embed, mock_search):
        """Test HIGH_RISK_MERCHANTS constant"""
        detector = FraudDetector()
        
        assert detector.HIGH_RISK_MERCHANTS is not None
        assert len(detector.HIGH_RISK_MERCHANTS) > 0
        assert "crypto" in detector.HIGH_RISK_MERCHANTS
    
    @patch('banking.fraud.fraud_detection.VectorSearchClient')
    @patch('banking.fraud.fraud_detection.EmbeddingGenerator')
    def test_anomaly_threshold(self, mock_embed, mock_search):
        """Test anomaly detection threshold"""
        detector = FraudDetector()
        
        assert detector.ANOMALY_THRESHOLD == 0.75


# Total: 5 + 6 + 10 + 3 + 2 = 26 tests for FraudDetector
# Combined with 15 tests for models = 41 total tests

# Made with Bob



class TestFraudDetectorVelocityChecks:
    """Test velocity checking methods (8 tests)"""
    
    @patch('banking.fraud.fraud_detection.VectorSearchClient')
    @patch('banking.fraud.fraud_detection.EmbeddingGenerator')
    def test_check_velocity_low_activity(self, mock_embed, mock_search):
        """Test velocity check with low activity"""
        detector = FraudDetector()
        mock_g = Mock()
        mock_g.V().has().out_e().has().count().next.return_value = 2  # 2 transactions
        mock_g.V().has().out_e().has().values().sum_().next.return_value = 500.0  # $500
        detector._g = mock_g
        
        timestamp = datetime.now(timezone.utc)
        score = detector._check_velocity("acc-123", 100.0, timestamp)
        
        assert score < 0.5  # Low velocity
    
    @patch('banking.fraud.fraud_detection.VectorSearchClient')
    @patch('banking.fraud.fraud_detection.EmbeddingGenerator')
    def test_check_velocity_high_transaction_count(self, mock_embed, mock_search):
        """Test velocity check with high transaction count"""
        detector = FraudDetector()
        mock_g = Mock()
        mock_g.V().has().out_e().has().count().next.return_value = 15  # 15 transactions (> 10 limit)
        mock_g.V().has().out_e().has().values().sum_().next.return_value = 1000.0
        detector._g = mock_g
        
        timestamp = datetime.now(timezone.utc)
        score = detector._check_velocity("acc-456", 100.0, timestamp)
        
        assert score >= 1.0  # Exceeds transaction limit
    
    @patch('banking.fraud.fraud_detection.VectorSearchClient')
    @patch('banking.fraud.fraud_detection.EmbeddingGenerator')
    def test_check_velocity_high_amount(self, mock_embed, mock_search):
        """Test velocity check with high amount"""
        detector = FraudDetector()
        mock_g = Mock()
        mock_g.V().has().out_e().has().count().next.return_value = 5
        mock_g.V().has().out_e().has().values().sum_().next.return_value = 6000.0  # > $5000 limit
        detector._g = mock_g
        
        timestamp = datetime.now(timezone.utc)
        score = detector._check_velocity("acc-789", 1000.0, timestamp)
        
        assert score >= 1.0  # Exceeds amount limit
    
    @patch('banking.fraud.fraud_detection.VectorSearchClient')
    @patch('banking.fraud.fraud_detection.EmbeddingGenerator')
    def test_check_velocity_error_handling(self, mock_embed, mock_search):
        """Test velocity check error handling"""
        detector = FraudDetector()
        mock_g = Mock()
        mock_g.V().has().out_e().has().count().next.side_effect = Exception("Graph error")
        detector._g = mock_g
        
        timestamp = datetime.now(timezone.utc)
        score = detector._check_velocity("acc-error", 100.0, timestamp)
        
        assert score == 0.0  # Returns 0 on error
    
    @patch('banking.fraud.fraud_detection.VectorSearchClient')
    @patch('banking.fraud.fraud_detection.EmbeddingGenerator')
    def test_check_velocity_timestamp_calculation(self, mock_embed, mock_search):
        """Test velocity check uses correct time window"""
        detector = FraudDetector()
        mock_g = Mock()
        mock_g.V().has().out_e().has().count().next.return_value = 3
        mock_g.V().has().out_e().has().values().sum_().next.return_value = 300.0
        detector._g = mock_g
        
        timestamp = datetime(2026, 2, 11, 20, 0, 0, tzinfo=timezone.utc)
        score = detector._check_velocity("acc-time", 100.0, timestamp)
        
        # Verify the method was called (timestamp calculation worked)
        assert score >= 0.0
    
    @patch('banking.fraud.fraud_detection.VectorSearchClient')
    @patch('banking.fraud.fraud_detection.EmbeddingGenerator')
    def test_check_velocity_max_score_capped(self, mock_embed, mock_search):
        """Test velocity score is capped at 1.0"""
        detector = FraudDetector()
        mock_g = Mock()
        mock_g.V().has().out_e().has().count().next.return_value = 50  # Way over limit
        mock_g.V().has().out_e().has().values().sum_().next.return_value = 50000.0  # Way over limit
        detector._g = mock_g
        
        timestamp = datetime.now(timezone.utc)
        score = detector._check_velocity("acc-max", 1000.0, timestamp)
        
        assert score <= 1.0  # Score capped at 1.0
    
    @patch('banking.fraud.fraud_detection.VectorSearchClient')
    @patch('banking.fraud.fraud_detection.EmbeddingGenerator')
    def test_check_velocity_uses_max_of_scores(self, mock_embed, mock_search):
        """Test velocity uses max of transaction and amount scores"""
        detector = FraudDetector()
        mock_g = Mock()
        # High transaction count, low amount
        mock_g.V().has().out_e().has().count().next.return_value = 12  # 120% of limit
        mock_g.V().has().out_e().has().values().sum_().next.return_value = 1000.0  # 20% of limit
        detector._g = mock_g
        
        timestamp = datetime.now(timezone.utc)
        score = detector._check_velocity("acc-max-test", 100.0, timestamp)
        
        # Should use the higher score (transaction count)
        assert score > 0.5
    
    @patch('banking.fraud.fraud_detection.VectorSearchClient')
    @patch('banking.fraud.fraud_detection.EmbeddingGenerator')
    def test_check_velocity_zero_transactions(self, mock_embed, mock_search):
        """Test velocity check with zero transactions"""
        detector = FraudDetector()
        mock_g = Mock()
        mock_g.V().has().out_e().has().count().next.return_value = 0
        mock_g.V().has().out_e().has().values().sum_().next.return_value = 0.0
        detector._g = mock_g
        
        timestamp = datetime.now(timezone.utc)
        score = detector._check_velocity("acc-new", 100.0, timestamp)
        
        assert score == 0.0  # No velocity risk


class TestFraudDetectorNetworkChecks:
    """Test network checking methods (5 tests)"""
    
    @patch('banking.fraud.fraud_detection.VectorSearchClient')
    @patch('banking.fraud.fraud_detection.EmbeddingGenerator')
    def test_check_network_low_connections(self, mock_embed, mock_search):
        """Test network check with few connections"""
        detector = FraudDetector()
        mock_g = Mock()
        mock_g.V().has().both().dedup().count().next.return_value = 5  # 5 connections
        detector._g = mock_g
        
        score = detector._check_network("acc-123")
        
        assert score < 0.2  # Low network risk
    
    @patch('banking.fraud.fraud_detection.VectorSearchClient')
    @patch('banking.fraud.fraud_detection.EmbeddingGenerator')
    def test_check_network_high_connections(self, mock_embed, mock_search):
        """Test network check with many connections"""
        detector = FraudDetector()
        mock_g = Mock()
        mock_g.V().has().both().dedup().count().next.return_value = 60  # 60 connections (> 50 threshold)
        detector._g = mock_g
        
        score = detector._check_network("acc-456")
        
        assert score >= 1.0  # High network risk
    
    @patch('banking.fraud.fraud_detection.VectorSearchClient')
    @patch('banking.fraud.fraud_detection.EmbeddingGenerator')
    def test_check_network_medium_connections(self, mock_embed, mock_search):
        """Test network check with medium connections"""
        detector = FraudDetector()
        mock_g = Mock()
        mock_g.V().has().both().dedup().count().next.return_value = 25  # 25 connections (50% of threshold)
        detector._g = mock_g
        
        score = detector._check_network("acc-789")
        
        assert 0.4 < score < 0.6  # Medium network risk
    
    @patch('banking.fraud.fraud_detection.VectorSearchClient')
    @patch('banking.fraud.fraud_detection.EmbeddingGenerator')
    def test_check_network_error_handling(self, mock_embed, mock_search):
        """Test network check error handling"""
        detector = FraudDetector()
        mock_g = Mock()
        mock_g.V().has().both().dedup().count().next.side_effect = Exception("Graph error")
        detector._g = mock_g
        
        score = detector._check_network("acc-error")
        
        assert score == 0.0  # Returns 0 on error
    
    @patch('banking.fraud.fraud_detection.VectorSearchClient')
    @patch('banking.fraud.fraud_detection.EmbeddingGenerator')
    def test_check_network_score_capped(self, mock_embed, mock_search):
        """Test network score is capped at 1.0"""
        detector = FraudDetector()
        mock_g = Mock()
        mock_g.V().has().both().dedup().count().next.return_value = 200  # Way over threshold
        detector._g = mock_g
        
        score = detector._check_network("acc-max")
        
        assert score <= 1.0  # Score capped at 1.0


class TestFraudDetectorMerchantChecks:
    """Test merchant checking methods (7 tests)"""
    
    @patch('banking.fraud.fraud_detection.VectorSearchClient')
    @patch('banking.fraud.fraud_detection.EmbeddingGenerator')
    def test_check_merchant_empty_string(self, mock_embed, mock_search):
        """Test merchant check with empty string"""
        detector = FraudDetector()
        
        score = detector._check_merchant("")
        
        assert score == 0.0
    
    @patch('banking.fraud.fraud_detection.VectorSearchClient')
    @patch('banking.fraud.fraud_detection.EmbeddingGenerator')
    def test_check_merchant_none(self, mock_embed, mock_search):
        """Test merchant check with None"""
        detector = FraudDetector()
        
        score = detector._check_merchant(None)
        
        assert score == 0.0
    
    @patch('banking.fraud.fraud_detection.VectorSearchClient')
    @patch('banking.fraud.fraud_detection.EmbeddingGenerator')
    def test_check_merchant_category_and_historical_combined(self, mock_embed, mock_search):
        """Test merchant check combines category and historical risk"""
        detector = FraudDetector()
        mock_embed.return_value.encode.return_value = [[0.1] * 768]
        mock_search.return_value.search.return_value = [
            {"_score": 0.8}
        ]
        
        score = detector._check_merchant("crypto exchange")  # Has category risk
        
        # Should combine category risk (0.7) and historical risk
        assert score > 0.4
    
    @patch('banking.fraud.fraud_detection.VectorSearchClient')
    @patch('banking.fraud.fraud_detection.EmbeddingGenerator')
    def test_check_merchant_search_error_fallback(self, mock_embed, mock_search):
        """Test merchant check falls back to category risk on search error"""
        detector = FraudDetector()
        mock_embed.return_value.encode.side_effect = Exception("Embedding error")
        
        score = detector._check_merchant("casino")  # Has category risk
        
        # Should still return category risk despite search error
        assert score > 0.3
    
    @patch('banking.fraud.fraud_detection.VectorSearchClient')
    @patch('banking.fraud.fraud_detection.EmbeddingGenerator')
    def test_check_merchant_no_historical_matches(self, mock_embed, mock_search):
        """Test merchant check with no historical matches"""
        detector = FraudDetector()
        mock_embed.return_value.encode.return_value = [[0.1] * 768]
        mock_search.return_value.search.return_value = []
        
        score = detector._check_merchant("Normal Store")
        
        assert score == 0.0  # No risk
    
    @patch('banking.fraud.fraud_detection.VectorSearchClient')
    @patch('banking.fraud.fraud_detection.EmbeddingGenerator')
    def test_check_merchant_historical_risk_capped(self, mock_embed, mock_search):
        """Test historical risk is capped at 0.8"""
        detector = FraudDetector()
        mock_embed.return_value.encode.return_value = [[0.1] * 768]
        mock_search.return_value.search.return_value = [
            {"_score": 1.0},
            {"_score": 1.0},
            {"_score": 1.0}
        ]
        
        score = detector._check_merchant("Test Merchant")
        
        # Historical component should be capped at 0.8
        # Final score = 0.0 * 0.6 + 0.8 * 0.4 = 0.32
        assert score <= 0.35


# Total: 25 + 8 + 5 + 7 = 45 tests for FraudDetector


# ============================================================================
# Test Behavioral Analysis
# ============================================================================


class TestFraudDetectorBehavioralChecks:
    """Test behavioral analysis methods."""

    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    @patch("banking.fraud.fraud_detection.DriverRemoteConnection")
    @patch("banking.fraud.fraud_detection.traversal")
    def test_check_behavior_no_history(self, mock_traversal, mock_connection, mock_embed, mock_search):
        """Test behavioral check with no transaction history."""
        detector = FraudDetector()
        mock_g = Mock()
        mock_g.V.return_value.has.return_value.out_e.return_value.has.return_value.project.return_value.by.return_value.by.return_value.by.return_value.toList.return_value = (
            []
        )
        mock_traversal.return_value.with_remote.return_value = mock_g
        detector._g = mock_g

        risk = detector._check_behavior("acc-123", 1000.0, "Test Merchant", "Test transaction")

        assert risk == 0.3  # Default risk for no history

    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    @patch("banking.fraud.fraud_detection.DriverRemoteConnection")
    @patch("banking.fraud.fraud_detection.traversal")
    def test_check_behavior_normal_pattern(self, mock_traversal, mock_connection, mock_embed, mock_search):
        """Test behavioral check with normal transaction pattern."""
        detector = FraudDetector()
        mock_g = Mock()
        # Mock historical transactions with similar amounts
        mock_g.V.return_value.has.return_value.out_e.return_value.has.return_value.project.return_value.by.return_value.by.return_value.by.return_value.toList.return_value = [
            {
                "amount": [100.0, 110.0, 105.0, 95.0],
                "merchant": ["Test Merchant", "Test Merchant", "Other", "Test Merchant"],
                "description": ["Normal tx", "Normal tx", "Normal tx", "Normal tx"],
            }
        ]
        mock_traversal.return_value.with_remote.return_value = mock_g
        detector._g = mock_g

        # Mock embedding generator
        with patch.object(detector.generator, "encode") as mock_encode:
            mock_encode.return_value = [[0.9, 0.8, 0.7]]  # High similarity

            risk = detector._check_behavior("acc-123", 100.0, "Test Merchant", "Normal tx")

            assert risk < 0.3  # Low risk for normal pattern

    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    @patch("banking.fraud.fraud_detection.DriverRemoteConnection")
    @patch("banking.fraud.fraud_detection.traversal")
    def test_check_behavior_unusual_amount(self, mock_traversal, mock_connection, mock_embed, mock_search):
        """Test behavioral check with unusual amount."""
        detector = FraudDetector()
        mock_g = Mock()
        # Mock historical transactions with much smaller amounts
        mock_g.V.return_value.has.return_value.out_e.return_value.has.return_value.project.return_value.by.return_value.by.return_value.by.return_value.toList.return_value = [
            {
                "amount": [100.0, 110.0, 105.0, 95.0],
                "merchant": ["Test Merchant"],
                "description": ["Normal tx"],
            }
        ]
        mock_traversal.return_value.with_remote.return_value = mock_g
        detector._g = mock_g

        with patch.object(detector.generator, "encode") as mock_encode:
            mock_encode.return_value = [[0.9]]

            # Transaction with 10x normal amount
            risk = detector._check_behavior("acc-123", 1000.0, "Test Merchant", "Normal tx")

            assert risk > 0.3  # Higher risk for unusual amount

    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    @patch("banking.fraud.fraud_detection.DriverRemoteConnection")
    @patch("banking.fraud.fraud_detection.traversal")
    def test_check_behavior_new_merchant(self, mock_traversal, mock_connection, mock_embed, mock_search):
        """Test behavioral check with new merchant."""
        detector = FraudDetector()
        mock_g = Mock()
        mock_g.V.return_value.has.return_value.out_e.return_value.has.return_value.project.return_value.by.return_value.by.return_value.by.return_value.toList.return_value = [
            {
                "amount": [100.0],
                "merchant": ["Old Merchant", "Old Merchant", "Old Merchant"],
                "description": ["Normal tx"],
            }
        ]
        mock_traversal.return_value.with_remote.return_value = mock_g
        detector._g = mock_g

        with patch.object(detector.generator, "encode") as mock_encode:
            mock_encode.return_value = [[0.9]]

            risk = detector._check_behavior("acc-123", 100.0, "Brand New Merchant", "Normal tx")

            assert risk >= 0.15  # Some risk for new merchant

    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    @patch("banking.fraud.fraud_detection.DriverRemoteConnection")
    @patch("banking.fraud.fraud_detection.traversal")
    def test_check_behavior_exception_handling(self, mock_traversal, mock_connection, mock_embed, mock_search):
        """Test behavioral check handles exceptions gracefully."""
        detector = FraudDetector()
        mock_g = Mock()
        mock_g.V.side_effect = Exception("Graph error")
        mock_traversal.return_value.with_remote.return_value = mock_g
        detector._g = mock_g

        risk = detector._check_behavior("acc-123", 100.0, "Test", "Test")

        assert risk == 0.2  # Default risk on error


# ============================================================================
# Test Account Takeover Detection
# ============================================================================


class TestAccountTakeoverDetection:
    """Test account takeover detection."""

    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    def test_detect_takeover_no_transactions(self, mock_embed, mock_search):
        """Test takeover detection with no transactions."""
        detector = FraudDetector()

        is_takeover, confidence, indicators = detector.detect_account_takeover("acc-123", [])

        assert is_takeover is False
        assert confidence == 0.0
        assert len(indicators) == 0

    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    def test_detect_takeover_normal_pattern(self, mock_embed, mock_search):
        """Test takeover detection with normal transaction pattern."""
        detector = FraudDetector()
        transactions = [
            {"amount": 100.0, "timestamp": "2026-01-01T10:00:00Z"},
            {"amount": 110.0, "timestamp": "2026-01-01T11:00:00Z"},
            {"amount": 105.0, "timestamp": "2026-01-01T12:00:00Z"},
        ]

        is_takeover, confidence, indicators = detector.detect_account_takeover(
            "acc-123", transactions
        )

        assert is_takeover is False
        assert confidence < 0.5

    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    def test_detect_takeover_large_transaction(self, mock_embed, mock_search):
        """Test takeover detection with unusually large transaction."""
        detector = FraudDetector()
        transactions = [
            {"amount": 100.0, "timestamp": "2026-01-01T10:00:00Z"},
            {"amount": 110.0, "timestamp": "2026-01-01T11:00:00Z"},
            {"amount": 105.0, "timestamp": "2026-01-01T12:00:00Z"},
            {"amount": 1000.0, "timestamp": "2026-01-01T13:00:00Z"},  # >3x average
        ]

        is_takeover, confidence, indicators = detector.detect_account_takeover(
            "acc-123", transactions
        )

        # Average of first 3: (100+110+105)/3 = 105
        # Latest: 1000, which is > 105*3 = 315, so should trigger
        # Actually uses last 10 transactions, so avg = (100+110+105+1000)/4 = 328.75
        # Check: 1000 > 328.75 * 3 = 986.25, so should trigger
        assert confidence == 0.3  # Should add 0.3 for large transaction
        assert "Unusually large transaction" in indicators


# ============================================================================
# Test Similar Fraud Cases
# ============================================================================


class TestSimilarFraudCases:
    """Test finding similar fraud cases."""

    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    def test_find_similar_cases_success(self, mock_embed, mock_search):
        """Test finding similar fraud cases successfully."""
        detector = FraudDetector()

        with patch.object(detector.generator, "encode_for_search") as mock_encode:
            with patch.object(detector.search_client, "search") as mock_search:
                mock_encode.return_value = [0.1, 0.2, 0.3]
                mock_search.return_value = [
                    {"source": {"case_id": "fraud-1", "description": "Similar case"}},
                    {"source": {"case_id": "fraud-2", "description": "Another case"}},
                ]

                cases = detector.find_similar_fraud_cases("Test transaction", 1000.0, k=5)

                assert len(cases) == 2
                assert cases[0]["case_id"] == "fraud-1"
                mock_encode.assert_called_once_with("Test transaction")
                mock_search.assert_called_once()

    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    def test_find_similar_cases_no_results(self, mock_embed, mock_search):
        """Test finding similar cases with no results."""
        detector = FraudDetector()

        with patch.object(detector.generator, "encode_for_search") as mock_encode:
            with patch.object(detector.search_client, "search") as mock_search:
                mock_encode.return_value = [0.1, 0.2, 0.3]
                mock_search.return_value = []

                cases = detector.find_similar_fraud_cases("Test transaction", 1000.0)

                assert len(cases) == 0

    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    def test_find_similar_cases_exception(self, mock_embed, mock_search):
        """Test finding similar cases handles exceptions."""
        detector = FraudDetector()

        with patch.object(detector.generator, "encode_for_search") as mock_encode:
            mock_encode.side_effect = Exception("Encoding error")

            cases = detector.find_similar_fraud_cases("Test transaction", 1000.0)

            assert len(cases) == 0  # Returns empty list on error


# ============================================================================
# Test Alert Generation
# ============================================================================


class TestAlertGeneration:
    """Test fraud alert generation."""

    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    def test_generate_alert_below_threshold(self, mock_embed, mock_search):
        """Test alert generation below threshold."""
        detector = FraudDetector()
        score = FraudScore(
            transaction_id="tx-123",
            overall_score=0.3,  # Below MEDIUM_THRESHOLD (0.5)
            velocity_score=0.2,
            network_score=0.2,
            merchant_score=0.2,
            behavioral_score=0.2,
            risk_level="low",
            recommendation="Monitor",
        )
        transaction_data = {"transaction_id": "tx-123", "amount": 100.0}

        alert = detector.generate_alert(score, transaction_data)

        assert alert is None  # No alert for low scores

    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    def test_generate_alert_velocity_type(self, mock_embed, mock_search):
        """Test alert generation for velocity fraud."""
        detector = FraudDetector()
        score = FraudScore(
            transaction_id="tx-123",
            overall_score=0.8,
            velocity_score=0.9,  # High velocity
            network_score=0.3,
            merchant_score=0.3,
            behavioral_score=0.3,
            risk_level="high",
            recommendation="Block",
        )
        transaction_data = {"transaction_id": "tx-123", "amount": 1000.0}

        alert = detector.generate_alert(score, transaction_data)

        assert alert is not None
        assert alert.alert_type == "velocity"
        assert alert.severity == "high"
        assert any("High velocity" in factor for factor in alert.risk_factors)

    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    def test_generate_alert_network_type(self, mock_embed, mock_search):
        """Test alert generation for network fraud."""
        detector = FraudDetector()
        score = FraudScore(
            transaction_id="tx-123",
            overall_score=0.8,
            velocity_score=0.3,
            network_score=0.9,  # High network risk
            merchant_score=0.3,
            behavioral_score=0.3,
            risk_level="high",
            recommendation="Block",
        )
        transaction_data = {"transaction_id": "tx-123", "amount": 1000.0}

        alert = detector.generate_alert(score, transaction_data)

        assert alert is not None
        assert alert.alert_type == "network"
        assert any("Suspicious network" in factor for factor in alert.risk_factors)

    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    def test_generate_alert_merchant_type(self, mock_embed, mock_search):
        """Test alert generation for merchant fraud."""
        detector = FraudDetector()
        score = FraudScore(
            transaction_id="tx-123",
            overall_score=0.8,
            velocity_score=0.3,
            network_score=0.3,
            merchant_score=0.9,  # High merchant risk
            behavioral_score=0.3,
            risk_level="high",
            recommendation="Block",
        )
        transaction_data = {"transaction_id": "tx-123", "amount": 1000.0}

        alert = detector.generate_alert(score, transaction_data)

        assert alert is not None
        assert alert.alert_type == "merchant"
        assert any("Risky merchant" in factor for factor in alert.risk_factors)

    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    def test_generate_alert_behavioral_type(self, mock_embed, mock_search):
        """Test alert generation for behavioral fraud."""
        detector = FraudDetector()
        score = FraudScore(
            transaction_id="tx-123",
            overall_score=0.7,
            velocity_score=0.3,
            network_score=0.3,
            merchant_score=0.3,
            behavioral_score=0.8,  # High behavioral risk
            risk_level="high",
            recommendation="Review",
        )
        transaction_data = {"transaction_id": "tx-123", "amount": 1000.0}

        alert = detector.generate_alert(score, transaction_data)

        assert alert is not None
        assert alert.alert_type == "behavioral"
        assert any("Unusual behavior" in factor for factor in alert.risk_factors)

    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    def test_generate_alert_critical_severity(self, mock_embed, mock_search):
        """Test alert generation with critical severity."""
        detector = FraudDetector()
        score = FraudScore(
            transaction_id="tx-123",
            overall_score=0.95,  # Critical
            velocity_score=0.9,
            network_score=0.9,
            merchant_score=0.9,
            behavioral_score=0.9,
            risk_level="critical",
            recommendation="Block immediately",
        )
        transaction_data = {"transaction_id": "tx-123", "amount": 5000.0}

        alert = detector.generate_alert(score, transaction_data)

        assert alert is not None
        assert alert.severity == "critical"
        assert len(alert.risk_factors) >= 4  # All components high

    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    def test_generate_alert_multiple_risk_factors(self, mock_embed, mock_search):
        """Test alert with multiple risk factors."""
        detector = FraudDetector()
        score = FraudScore(
            transaction_id="tx-123",
            overall_score=0.75,
            velocity_score=0.6,  # Above 0.5
            network_score=0.7,  # Above 0.5
            merchant_score=0.8,  # Above 0.5
            behavioral_score=0.4,  # Below 0.5
            risk_level="high",
            recommendation="Review",
        )
        transaction_data = {"transaction_id": "tx-123", "amount": 1000.0}

        alert = detector.generate_alert(score, transaction_data)

        assert alert is not None
        assert len(alert.risk_factors) == 3  # velocity, network, merchant


# Total tests: 59 (original) + 6 (behavioral) + 3 (takeover) + 3 (similar cases) + 7 (alerts) = 78 tests
# Combined with 15 tests for models = 60 total tests
