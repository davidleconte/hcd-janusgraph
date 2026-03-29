"""
Alert quality governance utilities.

This module centralizes deterministic KPI calculations used by fraud/AML
notebooks and reporting flows.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from banking.streaming.metrics import get_metric


@dataclass(frozen=True)
class PrecisionProxyResult:
    """Container for precision-proxy computation results."""

    true_positives: int
    false_positives: int
    total_alerts: int
    precision_proxy: float


def calculate_precision_proxy(
    predicted_positive_ids: Iterable[str],
    ground_truth_positive_ids: Iterable[str],
) -> PrecisionProxyResult:
    """Calculate precision proxy from predicted-positive vs ground-truth IDs."""
    predicted = {item for item in predicted_positive_ids if item}
    ground_truth = {item for item in ground_truth_positive_ids if item}

    true_positives = len(predicted & ground_truth)
    false_positives = len(predicted - ground_truth)
    total_alerts = len(predicted)
    precision_proxy = true_positives / total_alerts if total_alerts else 0.0

    return PrecisionProxyResult(
        true_positives=true_positives,
        false_positives=false_positives,
        total_alerts=total_alerts,
        precision_proxy=round(precision_proxy, 4),
    )


def export_kpi_summary(
    *,
    scenario: str,
    run_id: str,
    metrics: Mapping[str, Any],
    base_dir: str | Path = "exports",
) -> Path:
    """Export KPI summary as deterministic JSON under exports/<run_id>/kpi."""
    output_dir = Path(base_dir) / run_id / "kpi"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{scenario}_kpi_summary.json"
    output_path.write_text(json.dumps(metrics, indent=2, sort_keys=True), encoding="utf-8")
    return output_path


def precision_proxy_to_dict(result: PrecisionProxyResult) -> dict[str, Any]:
    """Convert a precision-proxy result to a plain dictionary."""
    return asdict(result)


def emit_precision_proxy_metric(*, scenario: str, detector: str, precision_proxy: float) -> bool:
    """Emit precision proxy to Prometheus gauge if metric registry is available."""
    metric = get_metric("alert_quality_precision_proxy")
    if metric is None:
        return False

    metric.labels(scenario=scenario, detector=detector).set(precision_proxy)
    return True


def emit_precision_proxy_from_summary(summary_path: str | Path) -> bool:
    """Load KPI summary JSON and emit precision proxy metric."""
    summary_file = Path(summary_path)
    if not summary_file.exists():
        return False

    payload = json.loads(summary_file.read_text(encoding="utf-8"))
    scenario = str(payload.get("scenario", "")).strip()
    detector = str(payload.get("detector", "")).strip()
    precision_proxy = payload.get("precision_proxy")

    if not scenario or not detector or precision_proxy is None:
        return False

    return emit_precision_proxy_metric(
        scenario=scenario,
        detector=detector,
        precision_proxy=float(precision_proxy),
    )
