"""
Unit tests for scripts/testing/aggregate_kpi_trends.py.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


def _load_module():
    module_path = Path("scripts/testing/aggregate_kpi_trends.py").resolve()
    module_name = "aggregate_kpi_trends"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _write_verdict(
    exports_root: Path,
    run_id: str,
    *,
    status: str,
    records: list[dict[str, object]],
    warning_count: int = 0,
    critical_count: int = 0,
) -> None:
    run_dir = exports_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": status,
        "records_evaluated": len(records),
        "warning_count": warning_count,
        "critical_count": critical_count,
        "records": records,
    }
    (run_dir / "kpi_drift_verdict.json").write_text(json.dumps(payload), encoding="utf-8")


def test_build_trend_report_no_data(tmp_path):
    """NO_DATA when no historical KPI verdicts exist."""
    module = _load_module()

    report = module.build_trend_report(exports_root=tmp_path, max_runs=30)

    assert report["status"] == "NO_DATA"
    assert report["runs_evaluated"] == 0
    assert report["overall_avg_precision_proxy"] is None
    assert report["status_counts"] == {}
    assert report["run_summaries"] == []
    assert report["detector_trends"] == {}


def test_build_trend_report_aggregates_latest_runs(tmp_path):
    """Aggregate historical verdicts and respect max_runs limit on latest runs."""
    module = _load_module()

    _write_verdict(
        tmp_path,
        "demo-20260329T090000Z",
        status="PASS",
        records=[{"scenario": "sanctions", "detector": "SanctionsScreener", "precision_proxy": 0.95}],
    )
    _write_verdict(
        tmp_path,
        "demo-20260329T100000Z",
        status="WARN",
        warning_count=1,
        records=[{"scenario": "sanctions", "detector": "SanctionsScreener", "precision_proxy": 0.85}],
    )
    _write_verdict(
        tmp_path,
        "demo-20260329T110000Z",
        status="FAIL",
        critical_count=1,
        records=[{"scenario": "sanctions", "detector": "SanctionsScreener", "precision_proxy": 0.70}],
    )

    report = module.build_trend_report(exports_root=tmp_path, max_runs=2)

    assert report["status"] == "PASS"
    assert report["runs_evaluated"] == 2
    assert report["status_counts"] == {"FAIL": 1, "WARN": 1}
    assert report["overall_avg_precision_proxy"] == 0.775
    assert [item["run_id"] for item in report["run_summaries"]] == [
        "demo-20260329T100000Z",
        "demo-20260329T110000Z",
    ]

    trend_key = "sanctions::SanctionsScreener"
    assert trend_key in report["detector_trends"]
    assert [item["run_id"] for item in report["detector_trends"][trend_key]] == [
        "demo-20260329T100000Z",
        "demo-20260329T110000Z",
    ]


def test_build_trend_report_ignores_invalid_precision_values(tmp_path):
    """Non-numeric precision values are ignored in average calculations."""
    module = _load_module()

    _write_verdict(
        tmp_path,
        "demo-20260329T120000Z",
        status="PASS",
        records=[
            {"scenario": "sanctions", "detector": "SanctionsScreener", "precision_proxy": "0.90"},
            {"scenario": "sanctions", "detector": "SanctionsScreener", "precision_proxy": "not-a-number"},
        ],
    )

    report = module.build_trend_report(exports_root=tmp_path, max_runs=30)

    assert report["runs_evaluated"] == 1
    assert report["overall_avg_precision_proxy"] == 0.9
    trend_key = "sanctions::SanctionsScreener"
    assert report["detector_trends"][trend_key][0]["precision_proxy"] == 0.9
    assert report["detector_trends"][trend_key][1]["precision_proxy"] is None
