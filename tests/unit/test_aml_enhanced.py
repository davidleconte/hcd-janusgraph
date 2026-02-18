"""
Tests for AML Enhanced Structuring Detection module.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from banking.aml.enhanced_structuring_detection import (
    EnhancedStructuringDetector,
    StructuringPattern,
)


@pytest.fixture
def mock_dependencies():
    with (
        patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator") as mock_eg,
        patch("banking.aml.enhanced_structuring_detection.VectorSearchClient") as mock_vs,
        patch("banking.aml.enhanced_structuring_detection.DriverRemoteConnection") as mock_conn,
        patch("banking.aml.enhanced_structuring_detection.traversal") as mock_trav,
    ):
        mock_eg_inst = MagicMock()
        mock_eg_inst.dimensions = 384
        mock_eg.return_value = mock_eg_inst

        mock_vs_inst = MagicMock()
        mock_vs_inst.client.indices.exists.return_value = True
        mock_vs.return_value = mock_vs_inst

        yield {
            "embedding_generator": mock_eg,
            "embedding_instance": mock_eg_inst,
            "vector_search": mock_vs,
            "vector_instance": mock_vs_inst,
            "connection": mock_conn,
            "traversal": mock_trav,
        }


@pytest.fixture
def detector(mock_dependencies):
    return EnhancedStructuringDetector(
        janusgraph_host="localhost",
        janusgraph_port=18182,
        opensearch_host="localhost",
        opensearch_port=9200,
    )


class TestStructuringPatternDataclass:
    def test_create_pattern(self):
        pattern = StructuringPattern(
            pattern_id="P001",
            pattern_type="rapid_sequence",
            account_id="ACC-1",
            person_id="PER-1",
            person_name="John Doe",
            transactions=[{"id": "t1", "amount": 9000}],
            total_amount=9000.0,
            transaction_count=1,
            time_window_hours=24.0,
            risk_score=0.85,
            detection_method="graph",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        assert pattern.pattern_id == "P001"
        assert pattern.risk_score == 0.85


class TestEnhancedDetectorInit:
    def test_initialization(self, mock_dependencies):
        detector = EnhancedStructuringDetector()
        assert detector.graph_url == "ws://localhost:18182/gremlin"

    def test_creates_index_if_not_exists(self, mock_dependencies):
        mock_dependencies["vector_instance"].client.indices.exists.return_value = False
        detector = EnhancedStructuringDetector()
        mock_dependencies["vector_instance"].create_vector_index.assert_called_once()


class TestDetectGraphPatterns:
    def test_detect_graph_patterns_empty(self, detector, mock_dependencies):
        mock_g = MagicMock()
        mock_g.V.return_value.has_label.return_value.as_.return_value.out_e.return_value.has.return_value.has.return_value.in_v.return_value.has_label.return_value.as_.return_value.select.return_value.by.return_value.by.return_value.toList.return_value = (
            []
        )
        mock_dependencies["traversal"].return_value.with_remote.return_value = mock_g
        patterns = detector.detect_graph_patterns()
        assert patterns == []

    def test_detect_graph_patterns_error(self, detector, mock_dependencies):
        mock_dependencies["connection"].side_effect = Exception("Connection failed")
        patterns = detector.detect_graph_patterns()
        assert patterns == []


class TestDetectSemanticPatterns:
    def test_detect_semantic_patterns_no_results(self, detector, mock_dependencies):
        mock_dependencies["vector_instance"].search.return_value = []
        patterns = detector.detect_semantic_patterns()
        assert patterns == []


class TestHybridDetection:
    def test_detect_all_patterns(self, detector, mock_dependencies):
        mock_g = MagicMock()
        mock_g.V.return_value.has_label.return_value.as_.return_value.out_e.return_value.has.return_value.has.return_value.in_v.return_value.has_label.return_value.as_.return_value.select.return_value.by.return_value.by.return_value.toList.return_value = (
            []
        )
        mock_dependencies["traversal"].return_value.with_remote.return_value = mock_g
        mock_dependencies["vector_instance"].search.return_value = []

        if hasattr(detector, "detect_all_patterns"):
            patterns = detector.detect_all_patterns()
            assert isinstance(patterns, list)


class TestRiskScoreCalculation:
    def test_calculate_risk_score(self, detector):
        if hasattr(detector, "_calculate_risk_score"):
            score = detector._calculate_risk_score(total_amount=25000, tx_count=5, threshold=10000)
            assert 0 <= score <= 1


class TestFormatTransaction:
    def test_format_transaction(self, detector):
        if hasattr(detector, "_format_transaction"):
            tx = {"amount": [5000], "timestamp": [1234567890]}
            result = detector._format_transaction(tx)
            assert isinstance(result, dict)
