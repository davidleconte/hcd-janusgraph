"""
Unit tests for alert quality governance utilities.
"""

import json
from unittest.mock import Mock, patch

from banking.analytics.governance import (
    calculate_precision_proxy,
    emit_precision_proxy_from_summary,
    emit_precision_proxy_metric,
    export_kpi_summary,
    precision_proxy_to_dict,
)


def test_calculate_precision_proxy_mixed_outcomes():
    """Precision proxy returns deterministic TP/FP counts and rounded ratio."""
    result = calculate_precision_proxy(
        predicted_positive_ids=["CUST-001", "CUST-002", "CUST-003"],
        ground_truth_positive_ids=["CUST-001", "CUST-003", "CUST-999"],
    )

    assert result.true_positives == 2
    assert result.false_positives == 1
    assert result.total_alerts == 3
    assert result.precision_proxy == 0.6667


def test_calculate_precision_proxy_no_alerts():
    """Precision proxy handles empty predicted set safely."""
    result = calculate_precision_proxy(
        predicted_positive_ids=[],
        ground_truth_positive_ids=["CUST-001"],
    )

    assert result.true_positives == 0
    assert result.false_positives == 0
    assert result.total_alerts == 0
    assert result.precision_proxy == 0.0


def test_precision_proxy_to_dict_round_trip():
    """Dataclass conversion keeps expected keys/values."""
    result = calculate_precision_proxy(
        predicted_positive_ids=["A", "B"],
        ground_truth_positive_ids=["A"],
    )
    payload = precision_proxy_to_dict(result)

    assert payload == {
        "true_positives": 1,
        "false_positives": 1,
        "total_alerts": 2,
        "precision_proxy": 0.5,
    }


def test_export_kpi_summary_writes_sorted_json(tmp_path):
    """KPI summary export writes deterministic path/content."""
    output_path = export_kpi_summary(
        scenario="sanctions",
        run_id="demo-test-run",
        metrics={"precision_proxy": 0.75, "matches_found": 3},
        base_dir=tmp_path,
    )

    assert output_path == tmp_path / "demo-test-run" / "kpi" / "sanctions_kpi_summary.json"
    assert output_path.exists()

    content = json.loads(output_path.read_text(encoding="utf-8"))
    assert content == {"matches_found": 3, "precision_proxy": 0.75}


@patch("banking.analytics.governance.get_metric")
def test_emit_precision_proxy_metric_emits_gauge_value(mock_get_metric):
    """Metric emitter writes scenario+detector labeled gauge."""
    mock_metric = Mock()
    mock_get_metric.return_value = mock_metric

    emitted = emit_precision_proxy_metric(
        scenario="sanctions",
        detector="SanctionsScreener",
        precision_proxy=0.875,
    )

    assert emitted is True
    mock_metric.labels.assert_called_once_with(
        scenario="sanctions",
        detector="SanctionsScreener",
    )
    mock_metric.labels.return_value.set.assert_called_once_with(0.875)


@patch("banking.analytics.governance.get_metric")
def test_emit_precision_proxy_from_summary_file(mock_get_metric, tmp_path):
    """Summary-file emitter loads deterministic JSON and publishes gauge."""
    mock_metric = Mock()
    mock_get_metric.return_value = mock_metric

    summary_path = tmp_path / "alert_quality_sanctions_kpi_summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "scenario": "sanctions",
                "detector": "SanctionsScreener",
                "precision_proxy": 0.91,
            }
        ),
        encoding="utf-8",
    )

    emitted = emit_precision_proxy_from_summary(summary_path)

    assert emitted is True
    mock_metric.labels.assert_called_once_with(
        scenario="sanctions",
        detector="SanctionsScreener",
    )
    mock_metric.labels.return_value.set.assert_called_once_with(0.91)
