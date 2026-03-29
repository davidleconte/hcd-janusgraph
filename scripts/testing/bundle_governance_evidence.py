#!/usr/bin/env python3
"""
Bundle governance evidence artifacts for weekly audit handoff (FR-044).

This script reads the KPI trend report, emits a markdown summary, and creates
a deterministic tar.gz bundle containing key governance artifacts.
"""

from __future__ import annotations

import argparse
import json
import tarfile
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _discover_run_dirs(exports_root: Path) -> list[Path]:
    return sorted(path for path in exports_root.glob("demo-*") if path.is_dir())


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _render_summary_markdown(
    trend_report: dict[str, Any],
    trend_report_path: Path,
    latest_run_id: str | None,
) -> str:
    runs_evaluated = trend_report.get("runs_evaluated", 0)
    overall_avg = trend_report.get("overall_avg_precision_proxy")
    status_counts = trend_report.get("status_counts", {})
    run_summaries = trend_report.get("run_summaries", [])

    status_counts_str = ", ".join(
        f"{status}={count}" for status, count in sorted(status_counts.items())
    ) or "none"

    lines = [
        "# Weekly Governance Evidence Rollup",
        "",
        "## Summary",
        f"- Trend report: `{trend_report_path}`",
        f"- Latest run: `{latest_run_id or 'N/A'}`",
        f"- Runs evaluated: `{runs_evaluated}`",
        f"- Overall avg precision proxy: `{overall_avg}`",
        f"- Status counts: `{status_counts_str}`",
        "",
        "## Run Summaries",
        "",
        "| Run ID | Status | Records | Warnings | Critical | Avg Precision |",
        "|---|---|---:|---:|---:|---:|",
    ]

    for item in run_summaries:
        lines.append(
            "| {run_id} | {status} | {records} | {warnings} | {critical} | {avg} |".format(
                run_id=item.get("run_id", "unknown"),
                status=item.get("status", "UNKNOWN"),
                records=item.get("records_evaluated", 0),
                warnings=item.get("warning_count", 0),
                critical=item.get("critical_count", 0),
                avg=item.get("avg_precision_proxy"),
            )
        )

    if not run_summaries:
        lines.append("| N/A | NO_DATA | 0 | 0 | 0 | None |")

    return "\n".join(lines) + "\n"


def _collect_bundle_sources(
    trend_report_path: Path,
    summary_path: Path,
    latest_run_dir: Path | None,
) -> list[Path]:
    sources = [trend_report_path, summary_path]
    if latest_run_dir is not None:
        for name in ("kpi_drift_verdict.json", "kpi_drift.log", "kpi_trends.log", "pipeline_summary.txt"):
            candidate = latest_run_dir / name
            if candidate.is_file():
                sources.append(candidate)
    return sources


def _normalized_tar_filter(tarinfo: tarfile.TarInfo) -> tarfile.TarInfo:
    tarinfo.uid = 0
    tarinfo.gid = 0
    tarinfo.uname = "root"
    tarinfo.gname = "root"
    tarinfo.mtime = 0
    return tarinfo


def _relative_arcname(path: Path, repo_root: Path, exports_root: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(repo_root.resolve()))
    except ValueError:
        try:
            return str(resolved.relative_to(exports_root.resolve().parent))
        except ValueError:
            return path.name


def build_bundle(
    *,
    exports_root: Path,
    trend_report_path: Path,
    summary_output_path: Path,
    bundle_output_path: Path,
) -> dict[str, Any]:
    if not trend_report_path.is_file():
        raise FileNotFoundError(f"Trend report not found: {trend_report_path}")

    trend_report = _load_json(trend_report_path)
    run_dirs = _discover_run_dirs(exports_root=exports_root)
    latest_run_dir = run_dirs[-1] if run_dirs else None
    latest_run_id = latest_run_dir.name if latest_run_dir else None

    summary_output_path.parent.mkdir(parents=True, exist_ok=True)
    summary_output_path.write_text(
        _render_summary_markdown(
            trend_report=trend_report,
            trend_report_path=trend_report_path,
            latest_run_id=latest_run_id,
        ),
        encoding="utf-8",
    )

    repo_root = _repo_root()
    bundle_output_path.parent.mkdir(parents=True, exist_ok=True)
    sources = _collect_bundle_sources(
        trend_report_path=trend_report_path,
        summary_path=summary_output_path,
        latest_run_dir=latest_run_dir,
    )
    sources = sorted({path.resolve() for path in sources if path.is_file()})

    with tarfile.open(bundle_output_path, mode="w:gz", compresslevel=9) as archive:
        for source in sources:
            archive.add(
                str(source),
                arcname=_relative_arcname(
                    Path(source),
                    repo_root=repo_root,
                    exports_root=exports_root,
                ),
                filter=_normalized_tar_filter,
            )

    return {
        "latest_run_id": latest_run_id,
        "files_bundled": [
            _relative_arcname(
                Path(source),
                repo_root=repo_root,
                exports_root=exports_root,
            )
            for source in sources
        ],
        "summary_output": str(summary_output_path),
        "bundle_output": str(bundle_output_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--exports-root",
        default=str(_repo_root() / "exports"),
        help="Exports root directory containing demo-* run folders (default: <repo>/exports)",
    )
    parser.add_argument(
        "--trend-report",
        default=str(_repo_root() / "exports" / "evidence" / "governance" / "kpi_trend_report.json"),
        help="Path to KPI trend report JSON",
    )
    parser.add_argument(
        "--summary-output",
        default=str(
            _repo_root() / "exports" / "evidence" / "governance" / "weekly_governance_summary.md"
        ),
        help="Output markdown summary path",
    )
    parser.add_argument(
        "--bundle-output",
        default=str(
            _repo_root() / "exports" / "evidence" / "governance" / "governance_evidence_bundle.tar.gz"
        ),
        help="Output tar.gz bundle path",
    )
    args = parser.parse_args()

    exports_root = Path(args.exports_root).resolve()
    if not exports_root.exists():
        print(f"❌ Exports root not found: {exports_root}")
        return 1

    trend_report_path = Path(args.trend_report).resolve()
    summary_output_path = Path(args.summary_output).resolve()
    bundle_output_path = Path(args.bundle_output).resolve()

    try:
        result = build_bundle(
            exports_root=exports_root,
            trend_report_path=trend_report_path,
            summary_output_path=summary_output_path,
            bundle_output_path=bundle_output_path,
        )
    except FileNotFoundError as exc:
        print(f"❌ {exc}")
        return 1

    print(
        "Governance evidence bundle complete: "
        f"latest_run={result['latest_run_id']}, files={len(result['files_bundled'])}"
    )
    print(f"Summary: {result['summary_output']}")
    print(f"Bundle: {result['bundle_output']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
