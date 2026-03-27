"""Unit tests for Graph ML visualization safety behavior."""

from datetime import datetime, timezone

import numpy as np
import pytest

from banking.analytics.graph_ml import (
    EmbeddingMethod,
    GraphEmbeddingResult,
    GraphMLEngine,
    NodeEmbedding,
    RiskPrediction,
    _HAS_SKLEARN,
)

pytestmark = pytest.mark.skipif(not _HAS_SKLEARN, reason="scikit-learn is required for Graph ML tests")


def test_export_for_visualization_marks_missing_risk_predictions_as_unknown() -> None:
    """Nodes without risk predictions must be exported as 'unknown', not silently LOW."""
    node_1 = NodeEmbedding(
        node_id="n1",
        node_label="person",
        embedding=np.array([0.1, 0.2, 0.3, 0.4]),
        neighbors=["n2"],
        degree=1,
        risk_score=0.1,
        cluster_id=0,
        is_anomaly=False,
    )
    node_2 = NodeEmbedding(
        node_id="n2",
        node_label="account",
        embedding=np.array([0.2, 0.1, 0.4, 0.3]),
        neighbors=["n1"],
        degree=1,
        risk_score=0.6,
        cluster_id=0,
        is_anomaly=False,
    )

    results = GraphEmbeddingResult(
        method=EmbeddingMethod.NODE2VEC,
        embedding_dim=4,
        node_embeddings={"n1": node_1, "n2": node_2},
        clusters={0: ["n1", "n2"]},
        anomalies=[],
        risk_predictions={"n1": RiskPrediction.LOW},
        timestamp=datetime.now(timezone.utc),
        graph_stats={},
        training_metadata={},
    )

    engine = GraphMLEngine.__new__(GraphMLEngine)
    engine.seed = 42
    engine.embedding_dim = 4
    engine._results = results
    engine._node2vec = None

    exported = engine.export_for_visualization(use_tsne=False)
    risk_by_node = {node["id"]: node["risk_level"] for node in exported["nodes"]}

    assert risk_by_node["n1"] == "low"
    assert risk_by_node["n2"] == "unknown"
