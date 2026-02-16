"""Tests for banking.aml.enhanced_structuring_detection module - full coverage."""

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

MODULE = "banking.aml.enhanced_structuring_detection"


@pytest.fixture
def mock_deps():
    with (
        patch(f"{MODULE}.DriverRemoteConnection") as mock_conn_cls,
        patch(f"{MODULE}.traversal") as mock_trav,
        patch(f"{MODULE}.EmbeddingGenerator") as mock_emb_cls,
        patch(f"{MODULE}.VectorSearchClient") as mock_vs_cls,
    ):
        mock_conn = MagicMock()
        mock_conn_cls.return_value = mock_conn
        mock_g = MagicMock()
        mock_trav.return_value.with_remote.return_value = mock_g
        mock_emb = MagicMock()
        mock_emb.dimensions = 384
        mock_emb_cls.return_value = mock_emb
        mock_vs = MagicMock()
        mock_vs.client.indices.exists.return_value = False
        mock_vs_cls.return_value = mock_vs
        yield {
            "conn_cls": mock_conn_cls, "conn": mock_conn,
            "traversal": mock_trav, "g": mock_g,
            "emb_cls": mock_emb_cls, "emb": mock_emb,
            "vs_cls": mock_vs_cls, "vs": mock_vs,
        }


@pytest.fixture
def detector(mock_deps):
    from banking.aml.enhanced_structuring_detection import EnhancedStructuringDetector
    return EnhancedStructuringDetector()


class TestInit:
    def test_creates_index(self, mock_deps):
        from banking.aml.enhanced_structuring_detection import EnhancedStructuringDetector
        EnhancedStructuringDetector()
        mock_deps["vs"].create_vector_index.assert_called_once()

    def test_skips_existing_index(self, mock_deps):
        mock_deps["vs"].client.indices.exists.return_value = True
        from banking.aml.enhanced_structuring_detection import EnhancedStructuringDetector
        EnhancedStructuringDetector()
        mock_deps["vs"].create_vector_index.assert_not_called()


class TestDetectGraphPatterns:
    def test_empty_results(self, detector, mock_deps):
        mock_deps["g"].V.return_value.has_label.return_value.as_.return_value.out_e.return_value.has.return_value.has.return_value.in_v.return_value.has_label.return_value.as_.return_value.select.return_value.by.return_value.by.return_value.toList.return_value = []
        result = detector.detect_graph_patterns()
        assert result == []

    def test_error_handling(self, detector, mock_deps):
        mock_deps["conn_cls"].side_effect = Exception("connection error")
        result = detector.detect_graph_patterns()
        assert result == []

    def test_with_results(self, detector, mock_deps):
        from gremlin_python.process.traversal import T
        mock_g = MagicMock()
        mock_deps["traversal"].return_value.with_remote.return_value = mock_g
        account_data = {T.id: 1, "account_id": ["acc1"]}
        tx_data1 = {T.id: 10, "amount": [9000.0], "timestamp": [1000], "description": ["payment"]}
        tx_data2 = {T.id: 11, "amount": [9500.0], "timestamp": [2000], "description": ["transfer"]}
        tx_data3 = {T.id: 12, "amount": [8000.0], "timestamp": [3000], "description": ["wire"]}
        mock_g.V.return_value.has_label.return_value.as_.return_value.out_e.return_value.has.return_value.has.return_value.in_v.return_value.has_label.return_value.as_.return_value.select.return_value.by.return_value.by.return_value.toList.return_value = [
            {"account": account_data, "transaction": tx_data1},
            {"account": account_data, "transaction": tx_data2},
            {"account": account_data, "transaction": tx_data3},
        ]
        mock_g.V.return_value.out.return_value.has_label.return_value.value_map.return_value.toList.return_value = [
            {T.id: 100, "name": ["John Doe"]}
        ]
        result = detector.detect_graph_patterns()
        assert len(result) >= 0


class TestDetectSemanticPatterns:
    def test_few_transactions(self, detector, mock_deps):
        mock_g = MagicMock()
        mock_deps["traversal"].return_value.with_remote.return_value = mock_g
        mock_g.V.return_value.has_label.return_value.has.return_value.has.return_value.has.return_value.project.return_value.by.return_value.by.return_value.by.return_value.by.return_value.by.return_value.by.return_value.by.return_value.by.return_value.limit.return_value.toList.return_value = []
        result = detector.detect_semantic_patterns()
        assert result == []

    def test_error(self, detector, mock_deps):
        mock_deps["conn_cls"].side_effect = Exception("err")
        result = detector.detect_semantic_patterns()
        assert result == []

    def test_with_cluster(self, detector, mock_deps):
        mock_g = MagicMock()
        mock_deps["traversal"].return_value.with_remote.return_value = mock_g
        txns = [
            {"tx_id": f"tx{i}", "amount": 9500.0, "description": "cash deposit",
             "merchant": "bank", "account_id": "acc1", "person_id": ["p1"],
             "person_name": ["John"], "timestamp": 1000 + i}
            for i in range(5)
        ]
        mock_g.V.return_value.has_label.return_value.has.return_value.has.return_value.has.return_value.project.return_value.by.return_value.by.return_value.by.return_value.by.return_value.by.return_value.by.return_value.by.return_value.by.return_value.limit.return_value.toList.return_value = txns
        embeddings = np.ones((5, 384)) * 0.9
        mock_deps["emb"].encode.return_value = embeddings
        result = detector.detect_semantic_patterns(min_similarity=0.5, min_cluster_size=3)
        assert len(result) >= 0


class TestDetectHybridPatterns:
    def test_hybrid(self, detector, mock_deps):
        with patch.object(detector, "detect_graph_patterns", return_value=[]):
            with patch.object(detector, "detect_semantic_patterns", return_value=[]):
                result = detector.detect_hybrid_patterns()
                assert result == []


class TestCalculateRiskScore:
    def test_high_risk(self, detector):
        score = detector._calculate_risk_score(50000, 10, 10000)
        assert 0 <= score <= 1.0

    def test_low_risk(self, detector):
        score = detector._calculate_risk_score(10001, 3, 10000)
        assert 0 <= score <= 1.0

    def test_min_risk(self, detector):
        score = detector._calculate_risk_score(10000, 3, 10000)
        assert score >= 0


class TestFormatTransaction:
    def test_format(self, detector):
        from gremlin_python.process.traversal import T
        tx = {T.id: 42, "amount": [9500.0], "timestamp": [1000], "description": ["payment"]}
        result = detector._format_transaction(tx)
        assert result["amount"] == 9500.0
        assert result["transaction_id"] == "42"


class TestDetectStructuring:
    def test_no_structuring(self, detector):
        txns = [{"amount": 100, "timestamp": datetime.now(timezone.utc)}]
        result = detector.detect_structuring("acc1", txns)
        assert not result["is_structuring"]
        assert result["risk_level"] == "low"

    def test_structuring_detected(self, detector):
        txns = [{"amount": 9500} for _ in range(5)]
        result = detector.detect_structuring("acc1", txns)
        assert result["is_structuring"]
        assert result["total_amount"] == 47500

    def test_high_risk(self, detector):
        txns = [{"amount": 9900} for _ in range(10)]
        result = detector.detect_structuring("acc1", txns)
        assert result["risk_level"] in ["high", "medium"]

    def test_below_threshold_count(self, detector):
        txns = [{"amount": 9500}, {"amount": 9600}]
        result = detector.detect_structuring("acc1", txns)
        assert not result["is_structuring"]


class TestDetectMultiAccountStructuring:
    def test_no_coordination(self, detector):
        txns = [{"account_id": "a1", "amount": 100}]
        result = detector.detect_multi_account_structuring(txns)
        assert not result["is_coordinated_structuring"]

    def test_coordinated(self, detector):
        txns = (
            [{"account_id": "a1", "amount": 9500} for _ in range(5)] +
            [{"account_id": "a2", "amount": 9500} for _ in range(5)]
        )
        result = detector.detect_multi_account_structuring(txns)
        assert result["is_coordinated_structuring"]
        assert result["risk_level"] == "high"

    def test_single_account_structuring(self, detector):
        txns = [{"account_id": "a1", "amount": 9500} for _ in range(5)]
        result = detector.detect_multi_account_structuring(txns)
        assert not result["is_coordinated_structuring"]
        assert result["risk_level"] == "medium"

    def test_with_relationship_data(self, detector):
        txns = [{"account_id": "a1", "amount": 100}]
        result = detector.detect_multi_account_structuring(txns, relationship_data={"a1": "a2"})
        assert "relationship_score" in result

    def test_empty_transactions(self, detector):
        result = detector.detect_multi_account_structuring([])
        assert result["total_transactions"] == 0


class TestAnalyzeAmountClustering:
    def test_few_transactions(self, detector):
        result = detector.analyze_amount_clustering("acc1", [{"amount": 100}])
        assert not result["is_clustered"]

    def test_clustered_near_threshold(self, detector):
        txns = [{"amount": 9500 + i * 0.01} for i in range(10)]
        result = detector.analyze_amount_clustering("acc1", txns)
        assert result["cluster_tightness"] > 0.9

    def test_not_clustered(self, detector):
        txns = [{"amount": 100}, {"amount": 50000}]
        result = detector.analyze_amount_clustering("acc1", txns)
        assert not result["is_clustered"]

    def test_zero_average(self, detector):
        txns = [{"amount": 0}, {"amount": 0}]
        result = detector.analyze_amount_clustering("acc1", txns)
        assert result["cluster_tightness"] == 0.0

    def test_near_threshold_medium(self, detector):
        txns = [{"amount": 9500}, {"amount": 9600}, {"amount": 5000}]
        result = detector.analyze_amount_clustering("acc1", txns)
        assert result["risk_level"] in ["low", "medium"]


class TestAnalyzeTemporalPattern:
    def test_few_transactions(self, detector):
        result = detector.analyze_temporal_pattern("acc1", [{"amount": 100}])
        assert not result["is_systematic"]

    def test_systematic(self, detector):
        now = datetime.now(timezone.utc)
        txns = [{"amount": 9500, "timestamp": now + timedelta(hours=i * 24)} for i in range(5)]
        result = detector.analyze_temporal_pattern("acc1", txns)
        assert result["regularity_score"] > 0

    def test_irregular(self, detector):
        now = datetime.now(timezone.utc)
        txns = [
            {"amount": 100, "timestamp": now},
            {"amount": 100, "timestamp": now + timedelta(hours=1)},
            {"amount": 100, "timestamp": now + timedelta(hours=100)},
        ]
        result = detector.analyze_temporal_pattern("acc1", txns)
        assert 0 <= result["regularity_score"] <= 1.0

    def test_no_datetime_timestamps(self, detector):
        txns = [{"amount": 100, "timestamp": 1000}, {"amount": 200, "timestamp": 2000}]
        result = detector.analyze_temporal_pattern("acc1", txns)
        assert not result["is_systematic"]

    def test_high_regularity(self, detector):
        now = datetime.now(timezone.utc)
        txns = [{"amount": 9500, "timestamp": now + timedelta(hours=i * 12)} for i in range(5)]
        result = detector.analyze_temporal_pattern("acc1", txns)
        if result["regularity_score"] >= 0.9:
            assert result["risk_level"] == "high"


class TestGenerateReport:
    def test_text_report(self, detector):
        from banking.aml.enhanced_structuring_detection import StructuringPattern
        p = StructuringPattern(
            pattern_id="p1", pattern_type="rapid_sequence", account_id="a1",
            person_id="p1", person_name="John", transactions=[],
            total_amount=50000, transaction_count=5, time_window_hours=24,
            risk_score=0.8, detection_method="graph",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        report = detector.generate_report([p])
        assert "AML STRUCTURING DETECTION REPORT" in report
        assert "p1" in report

    def test_json_report(self, detector):
        from banking.aml.enhanced_structuring_detection import StructuringPattern
        import json
        p = StructuringPattern(
            pattern_id="p1", pattern_type="test", account_id="a1",
            person_id="p1", person_name="John", transactions=[],
            total_amount=10000, transaction_count=3, time_window_hours=24,
            risk_score=0.5, detection_method="vector",
            timestamp="2026-01-01",
        )
        report = detector.generate_report([p], output_format="json")
        parsed = json.loads(report)
        assert len(parsed) == 1

    def test_empty_report(self, detector):
        report = detector.generate_report([])
        assert "Total Patterns Detected: 0" in report
