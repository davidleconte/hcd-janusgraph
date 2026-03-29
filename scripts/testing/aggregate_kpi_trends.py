#!/usr/bin/env python3
"""
Aggregate KPI drift verdicts across historical demo runs (FR-043).

This script scans exports/demo-*/kpi_drift_verdict.json artifacts and emits a
deterministic trend report for governance review.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _discover_verdict_files(exports_root: Path) -> list[Path]:
    return sorted(
        path for path in exports_root.glob("demo-*/kpi_drift_verdict.json") if path.is_file()
    )


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _run_summary(run_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    records = payload.get("records", [])
    precisions = [
        parsed
        for parsed in (_safe_float(record.get("precision_proxy")) for record in records)
        if parsed is not None
    ]
    avg_precision = round(sum(precisions) / len(precisions), 4) if precisions else None

    return {
        "run_id": run_id,
        "status": str(payload.get("status", "UNKNOWN")),
        "records_evaluated": int(payload.get("records_evaluated", 0)),
        "warning_count": int(payload.get("warning_count", 0)),
        "critical_count": int(payload.get("critical_count", 0)),
        "avg_precision_proxy": avg_precision,
    }


def build_trend_report(exports_root: Path, max_runs: int | None = None) -> dict[str, Any]:
    verdict_files = _discover_verdict_files(exports_root=exports_root)
    if max_runs is not None:
        verdict_files = verdict_files[-max_runs:]

    run_summaries: list[dict[str, Any]] = []
    detector_trends: dict[str, list[dict[str, Any]]] = {}

    for verdict_file in verdict_files:
        run_id = verdict_file.parent.name
        payload = json.loads(verdict_file.read_text(encoding="utf-8"))
        run_summaries.append(_run_summary(run_id=run_id, payload=payload))

        for record in payload.get("records", []):
            scenario = str(record.get("scenario", "")).strip()
            detector = str(record.get("detector", "")).strip()
            if not scenario or not detector:
                continue

            key = f"{scenario}::{detector}"
            detector_trends.setdefault(key, []).append(
                {
                    "run_id": run_id,
                    "precision_proxy": _safe_float(record.get("precision_proxy")),
                    "severity": str(record.get("severity", "UNKNOWN")),
                }
            )

    summary_precisions = [
        value
        for value in (item.get("avg_precision_proxy") for item in run_summaries)
        if isinstance(value, float)
    ]
    overall_avg = (
        round(sum(summary_precisions) / len(summary_precisions), 4) if summary_precisions else None
    )

    status_counts: dict[str, int] = {}
    for item in run_summaries:
        status = str(item.get("status", "UNKNOWN"))
        status_counts[status] = status_counts.get(status, 0) + 1

    return {
        "status": "NO_DATA" if not run_summaries else "PASS",
        "runs_evaluated": len(run_summaries),
        "overall_avg_precision_proxy": overall_avg,
        "status_counts": dict(sorted(status_counts.items())),
        "run_summaries": run_summaries,
        "detector_trends": {key: detector_trends[key] for key in sorted(detector_trends)},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--exports-root",
        default=str(_repo_root() / "exports"),
        help="Exports root directory containing demo-* run folders (default: <repo>/exports)",
    )
    parser.add_argument(
        "--output",
        default=str(_repo_root() / "exports" / "evidence" / "governance" / "kpi_trend_report.json"),
        help="Output report file path (default: exports/evidence/governance/kpi_trend_report.json)",
    )
    parser.add_argument(
        "--max-runs",
        type=int,
        default=30,
        help="Maximum number of latest runs to include (default: 30)",
    )
    args = parser.parse_args()

    if args.max_runs <= 0:
        print("❌ Invalid --max-runs: must be > 0")
        return 1

    exports_root = Path(args.exports_root).resolve()
    if not exports_root.exists():
        print(f"❌ Exports root not found: {exports_root}")
        return 1

    report = build_trend_report(exports_root=exports_root, max_runs=args.max_runs)
    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    print(
        "KPI trend aggregation complete: "
        f"runs={report['runs_evaluated']}, overall_avg={report['overall_avg_precision_proxy']}"
    )
    print(f"Artifact: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
