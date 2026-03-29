"""
Unit tests for scripts/testing/bundle_governance_evidence.py.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import tarfile
from pathlib import Path


def _load_module():
    module_path = Path("scripts/testing/bundle_governance_evidence.py").resolve()
    module_name = "bundle_governance_evidence"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_build_bundle_creates_summary_and_bundle(tmp_path):
    """Build bundle should emit markdown summary and tar.gz artifact."""
    module = _load_module()

    exports_root = tmp_path / "exports"
    latest_run_dir = exports_root / "demo-20260329T120000Z"
    latest_run_dir.mkdir(parents=True, exist_ok=True)
    _write_json(
        latest_run_dir / "kpi_drift_verdict.json",
        {
            "status": "FAIL",
            "records_evaluated": 1,
            "warning_count": 0,
            "critical_count": 1,
            "records": [
                {"scenario": "sanctions", "detector": "SanctionsScreener", "precision_proxy": 0.6667}
            ],
        },
    )
    (latest_run_dir / "kpi_drift.log").write_text("drift log\n", encoding="utf-8")
    (latest_run_dir / "kpi_trends.log").write_text("trend log\n", encoding="utf-8")
    (latest_run_dir / "pipeline_summary.txt").write_text("summary\n", encoding="utf-8")

    trend_report = exports_root / "evidence" / "governance" / "kpi_trend_report.json"
    _write_json(
        trend_report,
        {
            "runs_evaluated": 1,
            "overall_avg_precision_proxy": 0.6667,
            "status_counts": {"FAIL": 1},
            "run_summaries": [
                {
                    "run_id": "demo-20260329T120000Z",
                    "status": "FAIL",
                    "records_evaluated": 1,
                    "warning_count": 0,
                    "critical_count": 1,
                    "avg_precision_proxy": 0.6667,
                }
            ],
        },
    )

    summary_output = exports_root / "evidence" / "governance" / "weekly_governance_summary.md"
    bundle_output = exports_root / "evidence" / "governance" / "governance_evidence_bundle.tar.gz"

    result = module.build_bundle(
        exports_root=exports_root,
        trend_report_path=trend_report,
        summary_output_path=summary_output,
        bundle_output_path=bundle_output,
    )

    assert result["latest_run_id"] == "demo-20260329T120000Z"
    assert summary_output.is_file()
    assert bundle_output.is_file()

    summary_text = summary_output.read_text(encoding="utf-8")
    assert "# Weekly Governance Evidence Rollup" in summary_text
    assert "demo-20260329T120000Z" in summary_text
    assert "0.6667" in summary_text

    with tarfile.open(bundle_output, "r:gz") as archive:
        names = sorted(archive.getnames())
    assert any(name.endswith("kpi_trend_report.json") for name in names)
    assert any(name.endswith("weekly_governance_summary.md") for name in names)
    assert any(name.endswith("demo-20260329T120000Z/kpi_drift_verdict.json") for name in names)


def test_build_bundle_missing_trend_report_raises(tmp_path):
    """Missing trend report should raise FileNotFoundError."""
    module = _load_module()

    exports_root = tmp_path / "exports"
    exports_root.mkdir(parents=True, exist_ok=True)

    missing_trend = exports_root / "evidence" / "governance" / "kpi_trend_report.json"
    summary_output = exports_root / "evidence" / "governance" / "weekly_governance_summary.md"
    bundle_output = exports_root / "evidence" / "governance" / "governance_evidence_bundle.tar.gz"

    try:
        module.build_bundle(
            exports_root=exports_root,
            trend_report_path=missing_trend,
            summary_output_path=summary_output,
            bundle_output_path=bundle_output,
        )
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("Expected FileNotFoundError for missing trend report")


def test_render_summary_markdown_no_data_row():
    """Summary markdown renders NO_DATA fallback row when no run summaries are present."""
    module = _load_module()

    markdown = module._render_summary_markdown(  # noqa: SLF001
        trend_report={
            "runs_evaluated": 0,
            "overall_avg_precision_proxy": None,
            "status_counts": {},
            "run_summaries": [],
        },
        trend_report_path=Path("exports/evidence/governance/kpi_trend_report.json"),
        latest_run_id=None,
    )

    assert "| N/A | NO_DATA | 0 | 0 | 0 | None |" in markdown
