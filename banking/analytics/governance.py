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
