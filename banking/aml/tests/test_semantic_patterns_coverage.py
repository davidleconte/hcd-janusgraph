"""
Comprehensive Coverage Tests for detect_semantic_patterns Method

This test file implements Phase 1 of the semantic patterns coverage plan,
targeting lines 328-438 in enhanced_structuring_detection.py.

Target: Achieve 92-95% coverage through mock-based unit tests.
Current coverage: 79% → Target: 95%+

Test Strategy:
- Mock all external dependencies (JanusGraph, OpenSearch, numpy)
- Create realistic transaction data fixtures
- Test all code paths and branches
- Focus on deterministic, fast-running tests
"""

from datetime import datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch, Mock, call
from typing import Dict, Any, List

import pytest
import numpy as np

from banking.aml.enhanced_structuring_detection import (
    EnhancedStructuringDetector,
    StructuringPattern
)


# Test Fixtures
@pytest.fixture
def mock_transactions():
    """Create realistic mock transaction data."""
    return [
        {
            "tx_id": "tx-001",
            "amount": 9500.0,
            "description": "ATM Withdrawal",
            "merchant": "Bank ATM",
            "account_id": "acc-123",
            "person_id": ["person-001"],
            "person_name": ["John Doe"],
            "timestamp": 1234567890000
        },
        {
            "tx_id": "tx-002",
            "amount": 9600.0,
            "description": "ATM Withdrawal",
            "merchant": "Bank ATM",
            "account_id": "acc-456",
            "person_id": ["person-002"],
            "person_name": ["Jane Smith"],
            "timestamp": 1234567891000
        },
        {
            "tx_id": "tx-003",
            "amount": 9700.0,
            "description": "ATM Withdrawal",
            "merchant": "Bank ATM",
            "account_id": "acc-789",
            "person_id": ["person-003"],
            "person_name": ["Bob Johnson"],
            "timestamp": 1234567892000
        },
        {
            "tx_id": "tx-004",
            "amount": 5000.0,
            "description": "Different Transaction",
            "merchant": "Store",
            "account_id": "acc-999",
            "person_id": ["person-004"],
            "person_name": ["Alice Brown"],
            "timestamp": 1234567893000
        }
    ]


@pytest.fixture
def mock_embeddings():
    """Create mock embeddings for transactions."""
    # 4 transactions, 3-dimensional embeddings
    return np.array([
        [0.1, 0.2, 0.3],   # tx-001
        [0.15, 0.25, 0.35],  # tx-002 (similar to tx-001)
        [0.12, 0.22, 0.32],  # tx-003 (similar to tx-001)
        [0.8, 0.9, 0.1]    # tx-004 (different)
    ])


@pytest.fixture
def mock_similarity_matrix():
    """Create mock similarity matrix."""
    return np.array([
        [1.0, 0.95, 0.92, 0.2],   # tx-001 similar to tx-002, tx-003
        [0.95, 1.0, 0.90, 0.15],
        [0.92, 0.90, 1.0, 0.18],
        [0.2, 0.15, 0.18, 1.0]
    ])


class TestSemanticPatternsTransactionProcessing:
    """Test transaction processing and text building (lines 328-342)."""

    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    @patch("banking.aml.enhanced_structuring_detection.DriverRemoteConnection")
    @patch("banking.aml.enhanced_structuring_detection.traversal")
    def test_transaction_text_building(self, mock_trav, mock_conn, mock_embed, mock_search, mock_transactions):
        """Test transaction text building for embeddings (lines 330-341)."""
        mock_search.return_value.client.indices.exists.return_value = True
        
        # Mock graph connection and traversal
        mock_connection = MagicMock()
        mock_conn.return_value = mock_connection
        mock_g = MagicMock()
        mock_trav.return_value.with_remote.return_value = mock_g
        
        # Mock transaction query to return our test data
        mock_g.V.return_value.has_label.return_value.has.return_value.has.return_value.has.return_value.project.return_value.by.return_value.by.return_value.by.return_value.by.return_value.by.return_value.by.return_value.by.return_value.by.return_value.limit.return_value.toList.return_value = mock_transactions
        
        # Mock embedding generation
        embeddings = np.array([[0.1, 0.2], [0.1, 0.2], [0.1, 0.2], [0.8, 0.9]])
        mock_embed.return_value.encode.return_value = embeddings
        
        detector = EnhancedStructuringDetector()
        
        # Call detect_semantic_patterns
        result = detector.detect_semantic_patterns(min_cluster_size=2)
        
        # Verify embedding generation was called with transaction texts
        mock_embed.return_value.encode.assert_called_once()
        call_args = mock_embed.return_value.encode.call_args[0][0]
        
        # Verify text format: "description merchant $amount"
        assert len(call_args) == 4
        assert "ATM Withdrawal" in call_args[0]
        assert "Bank ATM" in call_args[0]
        assert "$9500.00" in call_args[0]


class TestSemanticPatternsEmbeddingGeneration:
    """Test embedding generation and similarity matrix (lines 343-350)."""

    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    @patch("banking.aml.enhanced_structuring_detection.DriverRemoteConnection")
    @patch("banking.aml.enhanced_structuring_detection.traversal")
    @patch("numpy.dot")
    def test_similarity_matrix_creation(self, mock_dot, mock_trav, mock_conn, mock_embed, mock_search, 
                                       mock_transactions, mock_embeddings, mock_similarity_matrix):
        """Test similarity matrix creation with numpy.dot (lines 348-350)."""
        mock_search.return_value.client.indices.exists.return_value = True
        
        # Mock graph connection
        mock_connection = MagicMock()
        mock_conn.return_value = mock_connection
        mock_g = MagicMock()
        mock_trav.return_value.with_remote.return_value = mock_g
        mock_g.V.return_value.has_label.return_value.has.return_value.has.return_value.has.return_value.project.return_value.by.return_value.by.return_value.by.return_value.by.return_value.by.return_value.by.return_value.by.return_value.by.return_value.limit.return_value.toList.return_value = mock_transactions
        
        # Mock embedding generation
        mock_embed.return_value.encode.return_value = mock_embeddings
        
        # Mock numpy.dot to return similarity matrix
        mock_dot.return_value = mock_similarity_matrix
        
        detector = EnhancedStructuringDetector()
        result = detector.detect_semantic_patterns(min_cluster_size=2)
        
        # Verify numpy.dot was called with embeddings and embeddings.T
        mock_dot.assert_called_once()
        call_args = mock_dot.call_args[0]
        assert len(call_args) == 2
        np.testing.assert_array_equal(call_args[0], mock_embeddings)


class TestSemanticPatternsClusterDetection:
    """Test cluster detection logic (lines 351-377)."""

    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    @patch("banking.aml.enhanced_structuring_detection.DriverRemoteConnection")
    @patch("banking.aml.enhanced_structuring_detection.traversal")
    def test_insufficient_cluster_size(self, mock_trav, mock_conn, mock_embed, mock_search, mock_transactions):
        """Test early continue when cluster size < min_cluster_size (lines 361-362)."""
        mock_search.return_value.client.indices.exists.return_value = True
        
        # Mock graph connection
        mock_connection = MagicMock()
        mock_conn.return_value = mock_connection
        mock_g = MagicMock()
        mock_trav.return_value.with_remote.return_value = mock_g
        mock_g.V.return_value.has_label.return_value.has.return_value.has.return_value.has.return_value.project.return_value.by.return_value.by.return_value.by.return_value.by.return_value.by.return_value.by.return_value.by.return_value.by.return_value.limit.return_value.toList.return_value = mock_transactions
        
        # Mock embeddings with low similarity (no clusters)
        embeddings = np.array([
            [0.1, 0.2],
            [0.5, 0.6],
            [0.9, 0.1],
            [0.2, 0.9]
        ])
        mock_embed.return_value.encode.return_value = embeddings
        
        detector = EnhancedStructuringDetector()
        
        # Call with high min_cluster_size to trigger continue
        result = detector.detect_semantic_patterns(min_similarity=0.99, min_cluster_size=10)
        
        # Should return empty list (no clusters meet size requirement)
        assert result == []

    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    @patch("banking.aml.enhanced_structuring_detection.DriverRemoteConnection")
    @patch("banking.aml.enhanced_structuring_detection.traversal")
    @patch("numpy.dot")
    def test_multiple_account_extraction(self, mock_dot, mock_trav, mock_conn, mock_embed, mock_search, mock_transactions):
        """Test account and person ID extraction from clusters (lines 367-377)."""
        mock_search.return_value.client.indices.exists.return_value = True
        
        # Mock graph connection
        mock_connection = MagicMock()
        mock_conn.return_value = mock_connection
        mock_g = MagicMock()
        mock_trav.return_value.with_remote.return_value = mock_g
        mock_g.V.return_value.has_label.return_value.has.return_value.has.return_value.has.return_value.project.return_value.by.return_value.by.return_value.by.return_value.by.return_value.by.return_value.by.return_value.by.return_value.by.return_value.limit.return_value.toList.return_value = mock_transactions
        
        # Mock embeddings with high similarity for first 3 transactions
        embeddings = np.array([
            [0.1, 0.2],
            [0.11, 0.21],
            [0.12, 0.22],
            [0.9, 0.1]
        ])
        mock_embed.return_value.encode.return_value = embeddings
        
        # Mock similarity matrix with high similarity for first 3
        similarity_matrix = np.array([
            [1.0, 0.95, 0.92, 0.2],
            [0.95, 1.0, 0.90, 0.15],
            [0.92, 0.90, 1.0, 0.18],
            [0.2, 0.15, 0.18, 1.0]
        ])
        mock_dot.return_value = similarity_matrix
        
        detector = EnhancedStructuringDetector()
        result = detector.detect_semantic_patterns(min_similarity=0.85, min_cluster_size=3)
        
        # Should detect pattern with multiple accounts
        assert len(result) > 0
        pattern = result[0]
        assert pattern.transaction_count >= 3


class TestSemanticPatternsPatternCreation:
    """Test pattern creation and risk scoring (lines 378-443)."""

    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    @patch("banking.aml.enhanced_structuring_detection.DriverRemoteConnection")
    @patch("banking.aml.enhanced_structuring_detection.traversal")
    def test_amount_below_threshold_skip(self, mock_trav, mock_conn, mock_embed, mock_search):
        """Test skip when total amount < STRUCTURING_THRESHOLD (lines 381-382)."""
        mock_search.return_value.client.indices.exists.return_value = True
        
        # Create transactions with low total amount
        low_amount_txns = [
            {
                "tx_id": f"tx-{i:03d}",
                "amount": 1000.0,  # Low amount
                "description": "Small Transaction",
                "merchant": "Store",
                "account_id": f"acc-{i:03d}",
                "person_id": [f"person-{i:03d}"],
                "person_name": [f"Person {i}"],
                "timestamp": 1234567890000 + i
            }
            for i in range(5)
        ]
        
        # Mock graph connection
        mock_connection = MagicMock()
        mock_conn.return_value = mock_connection
        mock_g = MagicMock()
        mock_trav.return_value.with_remote.return_value = mock_g
        mock_g.V.return_value.has_label.return_value.has.return_value.has.return_value.has.return_value.project.return_value.by.return_value.by.return_value.by.return_value.by.return_value.by.return_value.by.return_value.by.return_value.by.return_value.limit.return_value.toList.return_value = low_amount_txns
        
        # Mock high similarity embeddings
        embeddings = np.array([[0.1, 0.2]] * 5)
        mock_embed.return_value.encode.return_value = embeddings
        
        detector = EnhancedStructuringDetector()
        result = detector.detect_semantic_patterns(min_similarity=0.85, min_cluster_size=3)
        
        # Should return empty (total amount $5000 < $10000 threshold)
        assert result == []

    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    @patch("banking.aml.enhanced_structuring_detection.DriverRemoteConnection")
    @patch("banking.aml.enhanced_structuring_detection.traversal")
    @patch("numpy.dot")
    def test_pattern_creation_with_risk_scoring(self, mock_dot, mock_trav, mock_conn, mock_embed, mock_search):
        """Test StructuringPattern creation with risk scoring (lines 383-430)."""
        mock_search.return_value.client.indices.exists.return_value = True
        
        # Create transactions with high total amount
        high_amount_txns = [
            {
                "tx_id": f"tx-{i:03d}",
                "amount": 9500.0,  # Just below threshold
                "description": "ATM Withdrawal",
                "merchant": "Bank ATM",
                "account_id": f"acc-{i:03d}",
                "person_id": [f"person-{i:03d}"],
                "person_name": [f"Person {i}"],
                "timestamp": 1234567890000 + i
            }
            for i in range(3)
        ]
        
        # Mock graph connection
        mock_connection = MagicMock()
        mock_conn.return_value = mock_connection
        mock_g = MagicMock()
        mock_trav.return_value.with_remote.return_value = mock_g
        mock_g.V.return_value.has_label.return_value.has.return_value.has.return_value.has.return_value.project.return_value.by.return_value.by.return_value.by.return_value.by.return_value.by.return_value.by.return_value.by.return_value.by.return_value.limit.return_value.toList.return_value = high_amount_txns
        
        # Mock high similarity embeddings
        embeddings = np.array([[0.1, 0.2]] * 3)
        mock_embed.return_value.encode.return_value = embeddings
        
        # Mock similarity matrix with perfect similarity
        similarity_matrix = np.array([
            [1.0, 0.99, 0.98],
            [0.99, 1.0, 0.97],
            [0.98, 0.97, 1.0]
        ])
        mock_dot.return_value = similarity_matrix
        
        detector = EnhancedStructuringDetector()
        result = detector.detect_semantic_patterns(min_similarity=0.85, min_cluster_size=3)
        
        # Should create pattern (total $28,500 > $10,000 threshold)
        assert len(result) > 0
        pattern = result[0]
        
        # Verify pattern structure
        assert pattern.pattern_type == "semantic_similarity"
        assert pattern.transaction_count == 3
        assert pattern.total_amount == 28500.0
        assert 0.0 <= pattern.risk_score <= 1.0
        assert pattern.detection_method == "vector"
        assert len(pattern.transactions) == 3

    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    @patch("banking.aml.enhanced_structuring_detection.DriverRemoteConnection")
    @patch("banking.aml.enhanced_structuring_detection.traversal")
    @patch("numpy.dot")
    def test_person_name_list_extraction(self, mock_dot, mock_trav, mock_conn, mock_embed, mock_search):
        """Test person name extraction from list format (lines 388-393)."""
        mock_search.return_value.client.indices.exists.return_value = True
        
        # Create transactions with person_name as list
        txns_with_list_names = [
            {
                "tx_id": f"tx-{i:03d}",
                "amount": 9500.0,
                "description": "Transaction",
                "merchant": "Merchant",
                "account_id": f"acc-{i:03d}",
                "person_id": [f"person-{i:03d}"],
                "person_name": [f"Person {i}", f"Alt Name {i}"],  # List format
                "timestamp": 1234567890000 + i
            }
            for i in range(3)
        ]
        
        # Mock graph connection
        mock_connection = MagicMock()
        mock_conn.return_value = mock_connection
        mock_g = MagicMock()
        mock_trav.return_value.with_remote.return_value = mock_g
        mock_g.V.return_value.has_label.return_value.has.return_value.has.return_value.has.return_value.project.return_value.by.return_value.by.return_value.by.return_value.by.return_value.by.return_value.by.return_value.by.return_value.by.return_value.limit.return_value.toList.return_value = txns_with_list_names
        
        # Mock high similarity embeddings
        embeddings = np.array([[0.1, 0.2]] * 3)
        mock_embed.return_value.encode.return_value = embeddings
        
        # Mock similarity matrix
        similarity_matrix = np.array([
            [1.0, 0.99, 0.98],
            [0.99, 1.0, 0.97],
            [0.98, 0.97, 1.0]
        ])
        mock_dot.return_value = similarity_matrix
        
        detector = EnhancedStructuringDetector()
        result = detector.detect_semantic_patterns(min_similarity=0.85, min_cluster_size=3)
        
        # Should extract first name from list
        assert len(result) > 0
        pattern = result[0]
        assert pattern.person_name == "Person 0"

    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    @patch("banking.aml.enhanced_structuring_detection.DriverRemoteConnection")
    @patch("banking.aml.enhanced_structuring_detection.traversal")
    @patch("numpy.dot")
    def test_person_name_string_extraction(self, mock_dot, mock_trav, mock_conn, mock_embed, mock_search):
        """Test person name extraction from string format (lines 388-393)."""
        mock_search.return_value.client.indices.exists.return_value = True
        
        # Create transactions with person_name as string
        txns_with_string_names = [
            {
                "tx_id": f"tx-{i:03d}",
                "amount": 9500.0,
                "description": "Transaction",
                "merchant": "Merchant",
                "account_id": f"acc-{i:03d}",
                "person_id": [f"person-{i:03d}"],
                "person_name": f"Person {i}",  # String format (not list)
                "timestamp": 1234567890000 + i
            }
            for i in range(3)
        ]
        
        # Mock graph connection
        mock_connection = MagicMock()
        mock_conn.return_value = mock_connection
        mock_g = MagicMock()
        mock_trav.return_value.with_remote.return_value = mock_g
        mock_g.V.return_value.has_label.return_value.has.return_value.has.return_value.has.return_value.project.return_value.by.return_value.by.return_value.by.return_value.by.return_value.by.return_value.by.return_value.by.return_value.by.return_value.limit.return_value.toList.return_value = txns_with_string_names
        
        # Mock high similarity embeddings
        embeddings = np.array([[0.1, 0.2]] * 3)
        mock_embed.return_value.encode.return_value = embeddings
        
        # Mock similarity matrix
        similarity_matrix = np.array([
            [1.0, 0.99, 0.98],
            [0.99, 1.0, 0.97],
            [0.98, 0.97, 1.0]
        ])
        mock_dot.return_value = similarity_matrix
        
        detector = EnhancedStructuringDetector()
        result = detector.detect_semantic_patterns(min_similarity=0.85, min_cluster_size=3)
        
        # Should use string directly
        assert len(result) > 0
        pattern = result[0]
        assert pattern.person_name == "Person 0"


class TestSemanticPatternsClusterProcessing:
    """Test cluster processing and deduplication (lines 434-436)."""

    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    @patch("banking.aml.enhanced_structuring_detection.DriverRemoteConnection")
    @patch("banking.aml.enhanced_structuring_detection.traversal")
    @patch("numpy.dot")
    def test_processed_clusters_tracking(self, mock_dot, mock_trav, mock_conn, mock_embed, mock_search):
        """Test marking transactions as processed to avoid duplicates (lines 434-436)."""
        mock_search.return_value.client.indices.exists.return_value = True
        
        # Create overlapping transactions
        txns = [
            {
                "tx_id": f"tx-{i:03d}",
                "amount": 9500.0,
                "description": "Transaction",
                "merchant": "Merchant",
                "account_id": f"acc-{i:03d}",
                "person_id": [f"person-{i:03d}"],
                "person_name": [f"Person {i}"],
                "timestamp": 1234567890000 + i
            }
            for i in range(6)
        ]
        
        # Mock graph connection
        mock_connection = MagicMock()
        mock_conn.return_value = mock_connection
        mock_g = MagicMock()
        mock_trav.return_value.with_remote.return_value = mock_g
        mock_g.V.return_value.has_label.return_value.has.return_value.has.return_value.has.return_value.project.return_value.by.return_value.by.return_value.by.return_value.by.return_value.by.return_value.by.return_value.by.return_value.by.return_value.limit.return_value.toList.return_value = txns
        
        # Mock embeddings with two clusters: [0,1,2] and [3,4,5]
        embeddings = np.array([
            [0.1, 0.2],  # Cluster 1
            [0.11, 0.21],
            [0.12, 0.22],
            [0.8, 0.9],  # Cluster 2
            [0.81, 0.91],
            [0.82, 0.92]
        ])
        mock_embed.return_value.encode.return_value = embeddings
        
        # Mock similarity matrix with two distinct clusters
        similarity_matrix = np.array([
            [1.0, 0.95, 0.92, 0.2, 0.15, 0.18],  # Cluster 1
            [0.95, 1.0, 0.90, 0.15, 0.12, 0.14],
            [0.92, 0.90, 1.0, 0.18, 0.14, 0.16],
            [0.2, 0.15, 0.18, 1.0, 0.95, 0.92],  # Cluster 2
            [0.15, 0.12, 0.14, 0.95, 1.0, 0.90],
            [0.18, 0.14, 0.16, 0.92, 0.90, 1.0]
        ])
        mock_dot.return_value = similarity_matrix
        
        detector = EnhancedStructuringDetector()
        result = detector.detect_semantic_patterns(min_similarity=0.85, min_cluster_size=3)
        
        # Should detect 2 separate patterns (no overlap due to processed_clusters tracking)
        assert len(result) == 2


class TestSemanticPatternsEdgeCases:
    """Test edge cases and error handling."""

    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    @patch("banking.aml.enhanced_structuring_detection.DriverRemoteConnection")
    @patch("banking.aml.enhanced_structuring_detection.traversal")
    def test_empty_description_handling(self, mock_trav, mock_conn, mock_embed, mock_search):
        """Test handling of empty/null descriptions (lines 334-339)."""
        mock_search.return_value.client.indices.exists.return_value = True
        
        # Create transactions with empty descriptions
        txns_empty_desc = [
            {
                "tx_id": f"tx-{i:03d}",
                "amount": 9500.0,
                "description": None,  # Null description
                "merchant": "",  # Empty merchant
                "account_id": f"acc-{i:03d}",
                "person_id": [f"person-{i:03d}"],
                "person_name": [f"Person {i}"],
                "timestamp": 1234567890000 + i
            }
            for i in range(3)
        ]
        
        # Mock graph connection
        mock_connection = MagicMock()
        mock_conn.return_value = mock_connection
        mock_g = MagicMock()
        mock_trav.return_value.with_remote.return_value = mock_g
        mock_g.V.return_value.has_label.return_value.has.return_value.has.return_value.has.return_value.project.return_value.by.return_value.by.return_value.by.return_value.by.return_value.by.return_value.by.return_value.by.return_value.by.return_value.limit.return_value.toList.return_value = txns_empty_desc
        
        # Mock embeddings
        embeddings = np.array([[0.1, 0.2]] * 3)
        mock_embed.return_value.encode.return_value = embeddings
        
        detector = EnhancedStructuringDetector()
        
        # Should handle empty descriptions gracefully
        result = detector.detect_semantic_patterns(min_similarity=0.85, min_cluster_size=3)
        
        # Should still process (text will be " $9500.00")
        assert isinstance(result, list)

    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    @patch("banking.aml.enhanced_structuring_detection.DriverRemoteConnection")
    @patch("banking.aml.enhanced_structuring_detection.traversal")
    def test_exception_handling(self, mock_trav, mock_conn, mock_embed, mock_search):
        """Test exception handling in detect_semantic_patterns (lines 445-449)."""
        mock_search.return_value.client.indices.exists.return_value = True
        
        # Mock graph connection to raise exception
        mock_conn.side_effect = Exception("Connection error")
        
        detector = EnhancedStructuringDetector()
        
        # Should handle exception and return empty list
        result = detector.detect_semantic_patterns()
        
        assert result == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob
