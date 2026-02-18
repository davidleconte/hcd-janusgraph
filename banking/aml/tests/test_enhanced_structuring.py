"""
Unit tests for EnhancedStructuringDetector.

Tests cover:
- Initialization and configuration
- Connection management
- Graph-based pattern detection
- Vector-based semantic analysis
- Hybrid detection combining graph + vector
- Risk scoring
- Error handling
"""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

from banking.aml.enhanced_structuring_detection import (
    EnhancedStructuringDetector,
    StructuringPattern,
)


class TestEnhancedDetectorInit:
    """Test initialization."""

    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_default_init(self, mock_embed, mock_search):
        mock_search.return_value.client.indices.exists.return_value = True
        detector = EnhancedStructuringDetector()

        assert detector.graph_url == "ws://localhost:18182/gremlin"
        assert detector.STRUCTURING_THRESHOLD == 10000.0
        assert detector.RAPID_SEQUENCE_HOURS == 24
        assert detector.MIN_TRANSACTIONS == 3
        assert detector.SEMANTIC_SIMILARITY_THRESHOLD == 0.85

    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_custom_host_port(self, mock_embed, mock_search):
        mock_search.return_value.client.indices.exists.return_value = True
        detector = EnhancedStructuringDetector(
            janusgraph_host="graph.example.com",
            janusgraph_port=8182,
        )
        assert detector.graph_url == "ws://graph.example.com:8182/gremlin"

    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_custom_opensearch(self, mock_embed, mock_search):
        mock_search.return_value.client.indices.exists.return_value = True
        EnhancedStructuringDetector(
            opensearch_host="search.example.com",
            opensearch_port=9300,
            embedding_model="bert",
        )
        mock_embed.assert_called_once_with(model_name="bert")
        mock_search.assert_called_once_with(host="search.example.com", port=9300)

    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_class_constants(self, mock_embed, mock_search):
        mock_search.return_value.client.indices.exists.return_value = True
        assert EnhancedStructuringDetector.STRUCTURING_THRESHOLD == 10000.0
        assert EnhancedStructuringDetector.REPORTING_THRESHOLD == 10000.0
        assert EnhancedStructuringDetector.TIME_WINDOW_HOURS == 24


class TestEnhancedDetectorRiskScoring:
    """Test risk scoring calculation."""

    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_calculate_risk_score_basic(self, mock_embed, mock_search):
        mock_search.return_value.client.indices.exists.return_value = True
        detector = EnhancedStructuringDetector()
        score = detector._calculate_risk_score(total_amount=15000.0, tx_count=5, threshold=10000.0)
        assert 0.0 <= score <= 1.0

    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_calculate_risk_score_high_amount(self, mock_embed, mock_search):
        mock_search.return_value.client.indices.exists.return_value = True
        detector = EnhancedStructuringDetector()
        score = detector._calculate_risk_score(total_amount=50000.0, tx_count=10, threshold=10000.0)
        assert score > 0.3

    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_calculate_risk_score_minimum(self, mock_embed, mock_search):
        mock_search.return_value.client.indices.exists.return_value = True
        detector = EnhancedStructuringDetector()
        score = detector._calculate_risk_score(total_amount=10001.0, tx_count=3, threshold=10000.0)
        assert score >= 0.0

    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_calculate_risk_score_capped(self, mock_embed, mock_search):
        mock_search.return_value.client.indices.exists.return_value = True
        detector = EnhancedStructuringDetector()
        score = detector._calculate_risk_score(
            total_amount=1000000.0, tx_count=100, threshold=10000.0
        )
        assert score <= 1.0


class TestEnhancedDetectorSimpleDetection:
    """Test simple structuring detection interface."""

    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_detect_structuring_no_pattern(self, mock_embed, mock_search):
        mock_search.return_value.client.indices.exists.return_value = True
        detector = EnhancedStructuringDetector()
        transactions = [
            {"amount": 500, "timestamp": "2026-01-01T10:00:00Z", "type": "deposit"},
            {"amount": 600, "timestamp": "2026-01-01T11:00:00Z", "type": "deposit"},
        ]
        result = detector.detect_structuring("acc-1", transactions)
        assert result["is_structuring"] is False
        assert result["risk_score"] >= 0.0

    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_detect_structuring_with_pattern(self, mock_embed, mock_search):
        mock_search.return_value.client.indices.exists.return_value = True
        detector = EnhancedStructuringDetector()
        transactions = [
            {"amount": 9500, "timestamp": "2026-01-01T10:00:00Z", "type": "deposit"},
            {"amount": 9600, "timestamp": "2026-01-01T10:05:00Z", "type": "deposit"},
            {"amount": 9700, "timestamp": "2026-01-01T10:10:00Z", "type": "deposit"},
        ]
        result = detector.detect_structuring("acc-1", transactions)
        assert result["is_structuring"] is True
        assert result["total_amount"] > 10000
        assert len(result["indicators"]) > 0

    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_detect_multi_account_structuring(self, mock_embed, mock_search):
        mock_search.return_value.client.indices.exists.return_value = True
        detector = EnhancedStructuringDetector()
        transactions = [
            {"amount": 9500, "account_id": "acc-1"},
            {"amount": 9600, "account_id": "acc-1"},
            {"amount": 9700, "account_id": "acc-1"},
            {"amount": 9500, "account_id": "acc-2"},
            {"amount": 9600, "account_id": "acc-2"},
            {"amount": 9700, "account_id": "acc-2"},
        ]
        result = detector.detect_multi_account_structuring(transactions)
        assert "is_coordinated_structuring" in result
        assert "accounts_involved" in result

    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_analyze_amount_clustering(self, mock_embed, mock_search):
        mock_search.return_value.client.indices.exists.return_value = True
        detector = EnhancedStructuringDetector()
        transactions = [
            {"amount": 9500},
            {"amount": 9510},
            {"amount": 9490},
            {"amount": 9505},
        ]
        result = detector.analyze_amount_clustering("acc-1", transactions)
        assert "is_clustered" in result
        assert "cluster_tightness" in result

    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_analyze_temporal_pattern(self, mock_embed, mock_search):
        mock_search.return_value.client.indices.exists.return_value = True
        detector = EnhancedStructuringDetector()
        result = detector.analyze_temporal_pattern("acc-1", [{"amount": 100}])
        assert result["is_systematic"] is False

    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_generate_report_text(self, mock_embed, mock_search):
        mock_search.return_value.client.indices.exists.return_value = True
        detector = EnhancedStructuringDetector()
        report = detector.generate_report([], output_format="text")
        assert "AML STRUCTURING DETECTION REPORT" in report
        assert "Total Patterns Detected: 0" in report

    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_generate_report_json(self, mock_embed, mock_search):
        mock_search.return_value.client.indices.exists.return_value = True
        detector = EnhancedStructuringDetector()
        report = detector.generate_report([], output_format="json")
        import json

        parsed = json.loads(report)
        assert isinstance(parsed, list)
        assert len(parsed) == 0

    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_semantic_threshold(self, mock_embed, mock_search):
        mock_search.return_value.client.indices.exists.return_value = True
        assert EnhancedStructuringDetector.SEMANTIC_SIMILARITY_THRESHOLD == 0.85


class TestStructuringPatternDataclass:
    """Test StructuringPattern dataclass."""

    def test_pattern_creation(self):
        pattern = StructuringPattern(
            pattern_id="RAPID_123",
            pattern_type="rapid_sequence",
            account_id="acc-1",
            person_id="person-1",
            person_name="John Doe",
            transactions=[{"id": "tx-1", "amount": 9000.0}],
            total_amount=9000.0,
            transaction_count=1,
            time_window_hours=24.0,
            risk_score=0.85,
            detection_method="graph",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        assert pattern.pattern_id == "RAPID_123"
        assert pattern.pattern_type == "rapid_sequence"
        assert pattern.risk_score == 0.85
        assert pattern.detection_method == "graph"

    def test_pattern_types(self):
        for ptype in ["rapid_sequence", "amount_splitting", "semantic_similarity"]:
            pattern = StructuringPattern(
                pattern_id="TEST",
                pattern_type=ptype,
                account_id="acc-1",
                person_id="p-1",
                person_name="Test",
                transactions=[],
                total_amount=0.0,
                transaction_count=0,
                time_window_hours=24.0,
                risk_score=0.5,
                detection_method="hybrid",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            assert pattern.pattern_type == ptype

    def test_detection_methods(self):
        for method in ["graph", "vector", "hybrid"]:
            pattern = StructuringPattern(
                pattern_id="TEST",
                pattern_type="rapid_sequence",
                account_id="acc-1",
                person_id="p-1",
                person_name="Test",
                transactions=[],
                total_amount=0.0,
                transaction_count=0,
                time_window_hours=24.0,
                risk_score=0.5,
                detection_method=method,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            assert pattern.detection_method == method


class TestEnhancedDetectorAdditionalCoverage:
    """Additional tests for uncovered lines."""

    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_ensure_transaction_index_creates_when_missing(self, mock_embed, mock_search):
        mock_search.return_value.client.indices.exists.return_value = False
        EnhancedStructuringDetector()
        mock_search.return_value.create_vector_index.assert_called_once()

    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_format_transaction(self, mock_embed, mock_search):
        from gremlin_python.process.traversal import T

        mock_search.return_value.client.indices.exists.return_value = True
        detector = EnhancedStructuringDetector()
        tx_data = {
            T.id: "tx-123",
            "amount": [9500.0],
            "timestamp": [1700000000],
            "description": ["ATM deposit"],
        }
        result = detector._format_transaction(tx_data)
        assert result["transaction_id"] == "tx-123"
        assert result["amount"] == 9500.0

    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_detect_structuring_risk_levels(self, mock_embed, mock_search):
        mock_search.return_value.client.indices.exists.return_value = True
        detector = EnhancedStructuringDetector()
        txs = [
            {"amount": 9500},
            {"amount": 9600},
            {"amount": 9700},
            {"amount": 9800},
            {"amount": 9900},
        ]
        result = detector.detect_structuring("acc-1", txs)
        assert result["is_structuring"] is True
        assert result["risk_level"] in ("low", "medium", "high")
        assert result["pattern_type"] == "simple_structuring"
        assert len(result["indicators"]) >= 2

    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_detect_structuring_below_threshold_total(self, mock_embed, mock_search):
        mock_search.return_value.client.indices.exists.return_value = True
        detector = EnhancedStructuringDetector()
        txs = [{"amount": 9500}, {"amount": 400}]
        result = detector.detect_structuring("acc-1", txs)
        assert result["is_structuring"] is False

    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_multi_account_no_structuring(self, mock_embed, mock_search):
        mock_search.return_value.client.indices.exists.return_value = True
        detector = EnhancedStructuringDetector()
        txs = [
            {"amount": 100, "account_id": "acc-1"},
            {"amount": 200, "account_id": "acc-2"},
        ]
        result = detector.detect_multi_account_structuring(txs)
        assert result["is_coordinated_structuring"] is False
        assert result["risk_level"] == "low"

    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_multi_account_coordinated(self, mock_embed, mock_search):
        mock_search.return_value.client.indices.exists.return_value = True
        detector = EnhancedStructuringDetector()
        txs = [
            {"amount": 9500, "account_id": "acc-1"},
            {"amount": 9600, "account_id": "acc-1"},
            {"amount": 9700, "account_id": "acc-1"},
            {"amount": 9500, "account_id": "acc-2"},
            {"amount": 9600, "account_id": "acc-2"},
            {"amount": 9700, "account_id": "acc-2"},
        ]
        result = detector.detect_multi_account_structuring(txs)
        assert result["is_coordinated_structuring"] is True
        assert result["risk_level"] == "high"
        assert result["risk_score"] >= 0.6
        assert len(result["coordinated_accounts"]) == 2

    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_amount_clustering_insufficient_data(self, mock_embed, mock_search):
        mock_search.return_value.client.indices.exists.return_value = True
        detector = EnhancedStructuringDetector()
        result = detector.analyze_amount_clustering("acc-1", [{"amount": 100}])
        assert result["is_clustered"] is False
        assert result["cluster_size"] == 0

    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_amount_clustering_tight_cluster(self, mock_embed, mock_search):
        mock_search.return_value.client.indices.exists.return_value = True
        detector = EnhancedStructuringDetector()
        txs = [{"amount": 9500}, {"amount": 9501}, {"amount": 9499}, {"amount": 9500}]
        result = detector.analyze_amount_clustering("acc-1", txs)
        assert result["cluster_tightness"] > 0.9
        assert result["cluster_size"] >= 3
        assert "std_dev" in result

    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_amount_clustering_medium_risk(self, mock_embed, mock_search):
        mock_search.return_value.client.indices.exists.return_value = True
        detector = EnhancedStructuringDetector()
        txs = [{"amount": 9500}, {"amount": 9600}, {"amount": 5000}]
        result = detector.analyze_amount_clustering("acc-1", txs)
        assert result["risk_level"] in ("low", "medium")

    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_temporal_pattern_insufficient(self, mock_embed, mock_search):
        mock_search.return_value.client.indices.exists.return_value = True
        detector = EnhancedStructuringDetector()
        result = detector.analyze_temporal_pattern("acc-1", [])
        assert result["is_systematic"] is False

    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_temporal_pattern_systematic(self, mock_embed, mock_search):
        from datetime import timedelta

        mock_search.return_value.client.indices.exists.return_value = True
        detector = EnhancedStructuringDetector()
        base = datetime(2026, 1, 1, tzinfo=timezone.utc)
        txs = [{"amount": 9500, "timestamp": base + timedelta(hours=i * 24)} for i in range(5)]
        result = detector.analyze_temporal_pattern("acc-1", txs)
        assert "regularity_score" in result
        assert result["transaction_count"] == 5

    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_temporal_pattern_no_datetime_timestamps(self, mock_embed, mock_search):
        mock_search.return_value.client.indices.exists.return_value = True
        detector = EnhancedStructuringDetector()
        txs = [
            {"amount": 9500, "timestamp": "2026-01-01"},
            {"amount": 9600, "timestamp": "2026-01-02"},
        ]
        result = detector.analyze_temporal_pattern("acc-1", txs)
        assert result["is_systematic"] is False

    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_generate_report_with_patterns(self, mock_embed, mock_search):
        mock_search.return_value.client.indices.exists.return_value = True
        detector = EnhancedStructuringDetector()
        pattern = StructuringPattern(
            pattern_id="TEST_001",
            pattern_type="rapid_sequence",
            account_id="acc-1",
            person_id="p-1",
            person_name="Jane Doe",
            transactions=[{"id": "tx-1"}],
            total_amount=25000.0,
            transaction_count=3,
            time_window_hours=24.0,
            risk_score=0.85,
            detection_method="graph",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        report = detector.generate_report([pattern], output_format="text")
        assert "Jane Doe" in report
        assert "TEST_001" in report
        assert "$25,000.00" in report

    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_generate_report_json_with_patterns(self, mock_embed, mock_search):
        import json

        mock_search.return_value.client.indices.exists.return_value = True
        detector = EnhancedStructuringDetector()
        pattern = StructuringPattern(
            pattern_id="TEST_002",
            pattern_type="semantic_similarity",
            account_id="acc-2",
            person_id="p-2",
            person_name="John",
            transactions=[],
            total_amount=15000.0,
            transaction_count=2,
            time_window_hours=24.0,
            risk_score=0.6,
            detection_method="vector",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        report = detector.generate_report([pattern], output_format="json")
        parsed = json.loads(report)
        assert len(parsed) == 1
        assert parsed[0]["pattern_id"] == "TEST_002"

    @patch("banking.aml.enhanced_structuring_detection.traversal")
    @patch("banking.aml.enhanced_structuring_detection.DriverRemoteConnection")
    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_detect_graph_patterns_empty(self, mock_embed, mock_search, mock_conn, mock_trav):
        mock_search.return_value.client.indices.exists.return_value = True
        mock_g = Mock()
        mock_trav.return_value.with_remote.return_value = mock_g
        mock_g.V.return_value.hasLabel.return_value.as_.return_value.outE.return_value.has.return_value.has.return_value.inV.return_value.hasLabel.return_value.as_.return_value.select.return_value.by.return_value.by.return_value.toList.return_value = (
            []
        )
        detector = EnhancedStructuringDetector()
        patterns = detector.detect_graph_patterns()
        assert patterns == []

    @patch("banking.aml.enhanced_structuring_detection.traversal")
    @patch("banking.aml.enhanced_structuring_detection.DriverRemoteConnection")
    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_detect_graph_patterns_error(self, mock_embed, mock_search, mock_conn, mock_trav):
        mock_search.return_value.client.indices.exists.return_value = True
        mock_conn.side_effect = Exception("Connection refused")
        detector = EnhancedStructuringDetector()
        patterns = detector.detect_graph_patterns()
        assert patterns == []

    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_detect_hybrid_patterns(self, mock_embed, mock_search):
        mock_search.return_value.client.indices.exists.return_value = True
        detector = EnhancedStructuringDetector()
        detector.detect_graph_patterns = Mock(return_value=[])
        detector.detect_semantic_patterns = Mock(return_value=[])
        result = detector.detect_hybrid_patterns()
        assert result == []
        detector.detect_graph_patterns.assert_called_once()
        detector.detect_semantic_patterns.assert_called_once()

    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_multi_account_single_structuring(self, mock_embed, mock_search):
        mock_search.return_value.client.indices.exists.return_value = True
        detector = EnhancedStructuringDetector()
        txs = [
            {"amount": 9500, "account_id": "acc-1"},
            {"amount": 9600, "account_id": "acc-1"},
            {"amount": 9700, "account_id": "acc-1"},
            {"amount": 100, "account_id": "acc-2"},
        ]
        result = detector.detect_multi_account_structuring(txs)
        assert result["is_coordinated_structuring"] is False
        assert result["risk_level"] == "medium"


class TestDetectGraphPatternsWithResults:
    """Test detect_graph_patterns with mocked graph query results."""

    @patch("banking.aml.enhanced_structuring_detection.traversal")
    @patch("banking.aml.enhanced_structuring_detection.DriverRemoteConnection")
    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_detect_graph_patterns_with_results(
        self, mock_embed, mock_search, mock_conn, mock_trav
    ):
        from gremlin_python.process.traversal import T

        mock_search.return_value.client.indices.exists.return_value = True

        mock_g = Mock()
        mock_trav.return_value.with_remote.return_value = mock_g

        account_id = "acc-001"
        query_results = [
            {
                "account": {T.id: account_id, "account_id": ["ACC001"]},
                "transaction": {
                    T.id: "tx-1",
                    "amount": [9500.0],
                    "timestamp": [1700000000],
                    "description": ["ATM deposit"],
                },
            },
            {
                "account": {T.id: account_id, "account_id": ["ACC001"]},
                "transaction": {
                    T.id: "tx-2",
                    "amount": [9600.0],
                    "timestamp": [1700001000],
                    "description": ["ATM deposit"],
                },
            },
            {
                "account": {T.id: account_id, "account_id": ["ACC001"]},
                "transaction": {
                    T.id: "tx-3",
                    "amount": [9700.0],
                    "timestamp": [1700002000],
                    "description": ["ATM deposit"],
                },
            },
        ]

        chain = Mock()
        mock_g.V.return_value = chain
        chain.hasLabel.return_value = chain
        chain.has_label.return_value = chain
        chain.as_.return_value = chain
        chain.outE.return_value = chain
        chain.out_e.return_value = chain
        chain.has.return_value = chain
        chain.inV.return_value = chain
        chain.in_v.return_value = chain
        chain.select.return_value = chain
        chain.by.return_value = chain
        chain.toList.return_value = query_results

        person_chain = Mock()
        mock_g.V.return_value = person_chain
        person_chain.out.return_value = person_chain
        person_chain.hasLabel.return_value = person_chain
        person_chain.has_label.return_value = person_chain
        person_chain.valueMap.return_value = person_chain
        person_chain.value_map.return_value = person_chain
        person_chain.toList.return_value = [{T.id: "p-001", "name": ["John Doe"]}]

        def v_side_effect(*args, **kwargs):
            if args:
                return person_chain
            return chain

        mock_g.V.side_effect = v_side_effect

        detector = EnhancedStructuringDetector()
        patterns = detector.detect_graph_patterns(min_transactions=3)
        assert len(patterns) >= 1
        p = patterns[0]
        assert p.pattern_type == "rapid_sequence"
        assert p.detection_method == "graph"
        assert p.total_amount > 10000
        assert p.transaction_count == 3

    @patch("banking.aml.enhanced_structuring_detection.traversal")
    @patch("banking.aml.enhanced_structuring_detection.DriverRemoteConnection")
    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_detect_graph_patterns_below_min_transactions(
        self, mock_embed, mock_search, mock_conn, mock_trav
    ):
        from gremlin_python.process.traversal import T

        mock_search.return_value.client.indices.exists.return_value = True

        mock_g = Mock()
        mock_trav.return_value.with_remote.return_value = mock_g

        query_results = [
            {
                "account": {T.id: "acc-001"},
                "transaction": {
                    T.id: "tx-1",
                    "amount": [9500.0],
                    "timestamp": [1700000000],
                    "description": [""],
                },
            },
        ]

        chain = Mock()
        mock_g.V.return_value = chain
        chain.hasLabel.return_value = chain
        chain.as_.return_value = chain
        chain.outE.return_value = chain
        chain.has.return_value = chain
        chain.inV.return_value = chain
        chain.select.return_value = chain
        chain.by.return_value = chain
        chain.toList.return_value = query_results

        detector = EnhancedStructuringDetector()
        patterns = detector.detect_graph_patterns(min_transactions=3)
        assert len(patterns) == 0

    @patch("banking.aml.enhanced_structuring_detection.traversal")
    @patch("banking.aml.enhanced_structuring_detection.DriverRemoteConnection")
    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_detect_graph_patterns_total_below_threshold(
        self, mock_embed, mock_search, mock_conn, mock_trav
    ):
        from gremlin_python.process.traversal import T

        mock_search.return_value.client.indices.exists.return_value = True

        mock_g = Mock()
        mock_trav.return_value.with_remote.return_value = mock_g

        account_id = "acc-002"
        query_results = [
            {
                "account": {T.id: account_id},
                "transaction": {
                    T.id: "tx-1",
                    "amount": [1000.0],
                    "timestamp": [1700000000],
                    "description": [""],
                },
            },
            {
                "account": {T.id: account_id},
                "transaction": {
                    T.id: "tx-2",
                    "amount": [1000.0],
                    "timestamp": [1700001000],
                    "description": [""],
                },
            },
            {
                "account": {T.id: account_id},
                "transaction": {
                    T.id: "tx-3",
                    "amount": [1000.0],
                    "timestamp": [1700002000],
                    "description": [""],
                },
            },
        ]

        chain = Mock()
        mock_g.V.return_value = chain
        chain.hasLabel.return_value = chain
        chain.as_.return_value = chain
        chain.outE.return_value = chain
        chain.has.return_value = chain
        chain.inV.return_value = chain
        chain.select.return_value = chain
        chain.by.return_value = chain
        chain.toList.return_value = query_results

        detector = EnhancedStructuringDetector()
        patterns = detector.detect_graph_patterns(min_transactions=3)
        assert len(patterns) == 0


class TestDetectSemanticPatterns:
    """Test detect_semantic_patterns with mocked dependencies."""

    @patch("banking.aml.enhanced_structuring_detection.traversal")
    @patch("banking.aml.enhanced_structuring_detection.DriverRemoteConnection")
    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_detect_semantic_insufficient_transactions(
        self, mock_embed, mock_search, mock_conn, mock_trav
    ):
        mock_search.return_value.client.indices.exists.return_value = True

        mock_g = Mock()
        mock_trav.return_value.with_remote.return_value = mock_g

        chain = Mock()
        mock_g.V.return_value = chain
        chain.hasLabel.return_value = chain
        chain.has.return_value = chain
        chain.project.return_value = chain
        chain.by.return_value = chain
        chain.limit.return_value = chain
        chain.toList.return_value = [{"tx_id": "tx-1", "amount": 9500}]

        detector = EnhancedStructuringDetector()
        patterns = detector.detect_semantic_patterns(min_cluster_size=3)
        assert patterns == []

    @patch("banking.aml.enhanced_structuring_detection.traversal")
    @patch("banking.aml.enhanced_structuring_detection.DriverRemoteConnection")
    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_detect_semantic_with_cluster(self, mock_embed, mock_search, mock_conn, mock_trav):
        import numpy as np

        mock_search.return_value.client.indices.exists.return_value = True

        mock_g = Mock()
        mock_trav.return_value.with_remote.return_value = mock_g

        txns = [
            {
                "tx_id": f"tx-{i}",
                "amount": 9500 + i * 10,
                "description": "ATM deposit cash",
                "merchant": "ATM",
                "account_id": f"acc-{i % 2}",
                "person_id": [f"p-{i % 2}"],
                "person_name": [f"Person {i % 2}"],
                "timestamp": 1700000000 + i * 1000,
            }
            for i in range(5)
        ]

        chain = Mock()
        mock_g.V.return_value = chain
        chain.hasLabel.return_value = chain
        chain.has.return_value = chain
        chain.project.return_value = chain
        chain.by.return_value = chain
        chain.limit.return_value = chain
        chain.toList.return_value = txns

        embeddings = np.ones((5, 384)) * 0.5
        for i in range(5):
            embeddings[i][0] = 0.5 + i * 0.001
        mock_embed.return_value.encode.return_value = embeddings

        detector = EnhancedStructuringDetector()
        patterns = detector.detect_semantic_patterns(min_similarity=0.99, min_cluster_size=3)
        assert isinstance(patterns, list)

    @patch("banking.aml.enhanced_structuring_detection.traversal")
    @patch("banking.aml.enhanced_structuring_detection.DriverRemoteConnection")
    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_detect_semantic_error_handling(self, mock_embed, mock_search, mock_conn, mock_trav):
        mock_search.return_value.client.indices.exists.return_value = True
        mock_conn.side_effect = Exception("Connection refused")

        detector = EnhancedStructuringDetector()
        patterns = detector.detect_semantic_patterns()
        assert patterns == []


class TestDetectHybridPatternsWithResults:
    """Test hybrid detection with combined results."""

    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_hybrid_combines_and_sorts(self, mock_embed, mock_search):
        mock_search.return_value.client.indices.exists.return_value = True
        detector = EnhancedStructuringDetector()

        graph_pattern = StructuringPattern(
            pattern_id="G1",
            pattern_type="rapid_sequence",
            account_id="acc-1",
            person_id="p-1",
            person_name="Alice",
            transactions=[],
            total_amount=15000,
            transaction_count=3,
            time_window_hours=24,
            risk_score=0.5,
            detection_method="graph",
            timestamp="2026-01-01T00:00:00Z",
        )
        semantic_pattern = StructuringPattern(
            pattern_id="S1",
            pattern_type="semantic_similarity",
            account_id="acc-2",
            person_id="p-2",
            person_name="Bob",
            transactions=[],
            total_amount=20000,
            transaction_count=4,
            time_window_hours=72,
            risk_score=0.9,
            detection_method="vector",
            timestamp="2026-01-01T00:00:00Z",
        )

        detector.detect_graph_patterns = Mock(return_value=[graph_pattern])
        detector.detect_semantic_patterns = Mock(return_value=[semantic_pattern])

        result = detector.detect_hybrid_patterns()
        assert len(result) == 2
        assert result[0].risk_score >= result[1].risk_score
        assert result[0].pattern_id == "S1"


class TestAdditionalBranchCoverage:
    """Cover remaining branches."""

    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_amount_clustering_high_risk(self, mock_embed, mock_search):
        mock_search.return_value.client.indices.exists.return_value = True
        detector = EnhancedStructuringDetector()
        txs = [{"amount": 9500.00}, {"amount": 9500.01}, {"amount": 9499.99}, {"amount": 9500.00}]
        result = detector.analyze_amount_clustering("acc-1", txs)
        assert result["cluster_tightness"] > 0.95

    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_temporal_pattern_high_regularity(self, mock_embed, mock_search):
        from datetime import timedelta

        mock_search.return_value.client.indices.exists.return_value = True
        detector = EnhancedStructuringDetector()
        base = datetime(2026, 1, 1, tzinfo=timezone.utc)
        txs = [{"amount": 9500, "timestamp": base + timedelta(hours=i * 24)} for i in range(10)]
        result = detector.analyze_temporal_pattern("acc-1", txs)
        assert result["regularity_score"] >= 0.9
        assert result["is_systematic"] is True
        assert result["risk_level"] == "high"

    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_detect_structuring_high_risk_score(self, mock_embed, mock_search):
        mock_search.return_value.client.indices.exists.return_value = True
        detector = EnhancedStructuringDetector()
        txs = [{"amount": 9500 + i * 10} for i in range(20)]
        result = detector.detect_structuring("acc-1", txs)
        assert result["risk_level"] in ("medium", "high")

    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_multi_account_empty(self, mock_embed, mock_search):
        mock_search.return_value.client.indices.exists.return_value = True
        detector = EnhancedStructuringDetector()
        result = detector.detect_multi_account_structuring([])
        assert result["is_coordinated_structuring"] is False
        assert result["total_amount"] == 0
