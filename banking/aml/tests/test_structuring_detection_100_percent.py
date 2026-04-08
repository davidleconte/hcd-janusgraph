"""
100% Coverage Tests for StructuringDetector

This test file targets uncovered lines in structuring_detection.py to achieve 95%+ coverage.
Current coverage: 80% → Target: 95%+

Missing lines to cover:
- 115-119: Connection already established (early return)
- 132: Auto-connect when _g is None
- 213: Empty transactions return path in detect_smurfing
- 266-270, 272: Error handling in detect_layering
- 314-349: Error handling in detect_network_structuring
- Other edge cases in _analyze methods
"""

import sys
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

# Mock resilience module before importing StructuringDetector
mock_resilience = MagicMock()
mock_circuit_breaker = MagicMock()
mock_circuit_breaker_config = MagicMock()
mock_resilience.CircuitBreaker = mock_circuit_breaker
mock_resilience.CircuitBreakerConfig = mock_circuit_breaker_config
mock_resilience.retry_with_backoff = lambda **kwargs: lambda func: func
sys.modules['src.python.utils.resilience'] = mock_resilience

from banking.aml.structuring_detection import (
    StructuringDetector,
    StructuringPattern,
    StructuringAlert
)


class TestConnectionManagement:
    """Test connection lifecycle and edge cases."""

    def test_connect_when_already_connected(self):
        """Test connect() returns early when connection already exists (lines 115-116)."""
        detector = StructuringDetector()
        
        # Manually set connection to simulate already connected state
        mock_connection = MagicMock()
        mock_g = MagicMock()
        detector._connection = mock_connection
        detector._g = mock_g
        
        # Call connect - should return early without creating new connection
        detector.connect()
        
        # Verify connection objects unchanged
        assert detector._connection is mock_connection
        assert detector._g is mock_g

    def test_get_traversal_auto_connects(self):
        """Test _get_traversal() auto-connects when _g is None (line 132)."""
        detector = StructuringDetector()
        
        # Ensure _g is None
        detector._g = None
        detector._connection = None
        
        # Mock the connect method
        with patch.object(detector, 'connect') as mock_connect:
            mock_g = MagicMock()
            
            # Set up mock to set _g when connect is called
            def set_g():
                detector._g = mock_g
            mock_connect.side_effect = set_g
            
            # Call _get_traversal
            result = detector._get_traversal()
            
            # Verify connect was called and _g returned
            mock_connect.assert_called_once()
            assert result is mock_g


class TestDetectSmurfingEdgeCases:
    """Test edge cases in detect_smurfing method."""

    def test_detect_smurfing_insufficient_transactions(self):
        """Test detect_smurfing returns empty when < min_transactions (line 196-200)."""
        detector = StructuringDetector()
        
        # Mock graph traversal to return only 2 transactions (< 3 minimum)
        mock_g = MagicMock()
        mock_traversal = MagicMock()
        mock_traversal.toList.return_value = [
            {"id": "tx1", "amount": 9500.0, "timestamp": 1234567890000, "to_account": "acc-456"},
            {"id": "tx2", "amount": 9600.0, "timestamp": 1234567891000, "to_account": "acc-789"}
        ]
        mock_g.V.return_value.has.return_value.out_e.return_value.has.return_value.has.return_value.project.return_value.by.return_value.by.return_value.by.return_value.by.return_value = mock_traversal
        
        detector._g = mock_g
        detector._connection = MagicMock()
        
        # Call detect_smurfing with min_transactions=3
        result = detector.detect_smurfing("acc-123", time_window_hours=24, min_transactions=3)
        
        # Should return empty list (insufficient transactions)
        assert result == []

    def test_detect_smurfing_error_handling(self):
        """Test detect_smurfing error handling (lines 215-217)."""
        detector = StructuringDetector()
        
        # Mock graph traversal to raise exception
        mock_g = MagicMock()
        mock_g.V.side_effect = Exception("Graph connection error")
        detector._g = mock_g
        detector._connection = MagicMock()
        
        # Call detect_smurfing - should handle error gracefully
        result = detector.detect_smurfing("acc-123", time_window_hours=24)
        
        # Should return empty list on error
        assert result == []


class TestDetectLayeringEdgeCases:
    """Test edge cases in detect_layering method."""

    def test_detect_layering_error_handling(self):
        """Test detect_layering error handling (lines 276-278)."""
        detector = StructuringDetector()
        
        # Mock graph traversal to raise exception
        mock_g = MagicMock()
        mock_g.V.side_effect = Exception("Graph connection error")
        detector._g = mock_g
        detector._connection = MagicMock()
        
        # Call detect_layering with list of account IDs - should handle error gracefully
        result = detector.detect_layering(["acc-123", "acc-456"], time_window_hours=24)
        
        # Should return empty list on error
        assert result == []

    def test_detect_layering_no_circular_transactions(self):
        """Test detect_layering with no circular transactions found (line 265-270)."""
        detector = StructuringDetector()
        
        # Mock graph traversal to return empty circular transactions
        mock_g = MagicMock()
        mock_traversal = MagicMock()
        mock_traversal.toList.return_value = []  # No circular transactions
        mock_g.V.return_value.has.return_value.out_e.return_value.has.return_value.as_.return_value.in_v.return_value.out_e.return_value.has.return_value.where.return_value.select.return_value.project.return_value.by.return_value.by.return_value.by.return_value = mock_traversal
        
        detector._g = mock_g
        detector._connection = MagicMock()
        
        # Call detect_layering
        result = detector.detect_layering(["acc-123"], time_window_hours=24)
        
        # Should return empty list (no patterns found)
        assert result == []


class TestDetectNetworkStructuringEdgeCases:
    """Test edge cases in detect_network_structuring method."""

    def test_detect_network_structuring_error_handling(self):
        """Test detect_network_structuring error handling (lines 314-353)."""
        detector = StructuringDetector()
        
        # Mock graph traversal to raise exception
        mock_g = MagicMock()
        mock_g.V.side_effect = Exception("Graph connection error")
        detector._g = mock_g
        detector._connection = MagicMock()
        
        # Call detect_network_structuring - should handle error gracefully
        result = detector.detect_network_structuring("acc-123", time_window_hours=24)
        
        # Should return empty list on error
        assert result == []

    def test_detect_network_structuring_no_related_accounts(self):
        """Test detect_network_structuring with no related accounts (line 428)."""
        detector = StructuringDetector()
        
        # Mock graph traversal to return empty related accounts
        mock_g = MagicMock()
        mock_traversal = MagicMock()
        mock_traversal.toList.return_value = []  # No related accounts
        mock_g.V.return_value.has.return_value.out.return_value.dedup.return_value = mock_traversal
        
        detector._g = mock_g
        detector._connection = MagicMock()
        
        # Call detect_network_structuring
        result = detector.detect_network_structuring("acc-123", time_window_hours=24)
        
        # Should return empty list
        assert result == []


class TestAnalyzeMethodsEdgeCases:
    """Test edge cases in _analyze methods."""

    def test_analyze_smurfing_pattern_low_confidence(self):
        """Test _analyze_smurfing_pattern with low confidence pattern."""
        detector = StructuringDetector()
        
        # Create transactions that don't meet high confidence criteria
        transactions = [
            {"id": "tx1", "amount": 15000.0, "timestamp": 1234567890000, "to_account": "acc-456"},
            {"id": "tx2", "amount": 16000.0, "timestamp": 1234567891000, "to_account": "acc-789"},
            {"id": "tx3", "amount": 17000.0, "timestamp": 1234567892000, "to_account": "acc-012"}
        ]
        
        # Call _analyze_smurfing_pattern
        result = detector._analyze_smurfing_pattern("acc-123", transactions, 24)
        
        # Should return pattern with low confidence
        assert result is not None
        assert result.confidence_score < 0.7

    def test_analyze_layering_pattern_few_transactions(self):
        """Test _analyze_layering_pattern with few transactions."""
        detector = StructuringDetector()
        
        # Create transactions list (not chains)
        transactions = [
            {"id": "tx1", "amount": 5000.0, "timestamp": 1234567890000},
            {"id": "tx2", "amount": 5000.0, "timestamp": 1234567891000}
        ]
        
        # Call _analyze_layering_pattern
        result = detector._analyze_layering_pattern("acc-123", transactions, 24)
        
        # Should return pattern with some confidence
        assert result is not None
        assert result.pattern_type == "layering"

    def test_analyze_network_pattern_empty_transactions(self):
        """Test _analyze_network_pattern with empty transactions (line 460-461)."""
        detector = StructuringDetector()
        
        # Call with empty transactions list
        result = detector._analyze_network_pattern(["acc-123"], [], 24)
        
        # Should return None (line 461)
        assert result is None

    def test_analyze_network_pattern_multiple_accounts(self):
        """Test _analyze_network_pattern with multiple accounts."""
        detector = StructuringDetector()
        
        # Create transactions for network pattern
        transactions = [
            {"id": "tx1", "amount": 5000.0, "timestamp": 1234567890000},
            {"id": "tx2", "amount": 6000.0, "timestamp": 1234567891000},
            {"id": "tx3", "amount": 7000.0, "timestamp": 1234567892000}
        ]
        
        # Call _analyze_network_pattern with multiple accounts
        result = detector._analyze_network_pattern(["acc-123", "acc-456", "acc-789"], transactions, 24)
        
        # Should return pattern
        assert result is not None
        assert result.pattern_type == "network_structuring"
        assert len(result.account_ids) == 3


class TestGenerateAlert:
    """Test generate_alert method."""

    def test_generate_alert_empty_patterns(self):
        """Test generate_alert with empty patterns list."""
        detector = StructuringDetector()
        
        # Call with empty patterns
        result = detector.generate_alert([])
        
        # Should return None
        assert result is None

    def test_generate_alert_single_pattern(self):
        """Test generate_alert with single pattern."""
        detector = StructuringDetector()
        
        # Create a single pattern
        pattern = StructuringPattern(
            pattern_id="pat-001",
            pattern_type="smurfing",
            account_ids=["acc-123"],
            transaction_ids=["tx1", "tx2", "tx3"],
            total_amount=Decimal("27000.00"),
            transaction_count=3,
            time_window_hours=24.0,
            confidence_score=0.85,
            risk_level="critical",
            indicators=["Multiple transactions below threshold"],
            detected_at=datetime.now(timezone.utc).isoformat(),
            metadata={}
        )
        
        # Call generate_alert
        result = detector.generate_alert([pattern])
        
        # Should return alert
        assert result is not None
        assert isinstance(result, StructuringAlert)
        assert result.severity == "critical"
        assert len(result.patterns) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob
