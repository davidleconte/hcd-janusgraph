#!/usr/bin/env python3
"""
Detect KPI drift for alert-quality governance artifacts (FR-042).

This script scans KPI summary JSON files and emits a deterministic verdict
artifact describing whether precision_proxy metrics drift below configured
thresholds.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class KPIDriftRecord:
    scenario: str
    detector: str
    precision_proxy: float
    warning_threshold: float
    critical_threshold: float
    severity: str
    source_file: str


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _discover_kpi_files(report_dir: Path, project_root: Path) -> list[Path]:
    candidates: list[Path] = []

    # Per-run artifacts if present.
    candidates.extend(sorted((report_dir / "evidence").glob("**/kpi/*.json")))
    # Global evidence artifacts emitted by notebooks (current pattern).
    candidates.extend(sorted((project_root / "exports" / "evidence").glob("**/kpi/*.json")))

    deduped: list[Path] = []
    seen: set[str] = set()
    for path in candidates:
        key = str(path.resolve())
        if key not in seen and path.is_file():
            deduped.append(path)
            seen.add(key)
    return deduped


def _classify_severity(
    precision_proxy: float,
    warning_threshold: float,
    critical_threshold: float,
) -> str:
    if precision_proxy < critical_threshold:
        return "CRITICAL"
    if precision_proxy < warning_threshold:
        return "WARNING"
    return "OK"


def _load_record(
    kpi_path: Path,
    warning_threshold: float,
    critical_threshold: float,
) -> KPIDriftRecord | None:
    payload = json.loads(kpi_path.read_text(encoding="utf-8"))
    scenario = str(payload.get("scenario", "")).strip()
    detector = str(payload.get("detector", "")).strip()
    precision_proxy_raw = payload.get("precision_proxy")

    if not scenario or not detector or precision_proxy_raw is None:
        return None

    precision_proxy = float(precision_proxy_raw)
    severity = _classify_severity(
        precision_proxy=precision_proxy,
        warning_threshold=warning_threshold,
        critical_threshold=critical_threshold,
    )

    return KPIDriftRecord(
        scenario=scenario,
        detector=detector,
        precision_proxy=round(precision_proxy, 4),
        warning_threshold=warning_threshold,
        critical_threshold=critical_threshold,
        severity=severity,
        source_file=str(kpi_path),
    )


def build_verdict(
    report_dir: Path,
    warning_threshold: float,
    critical_threshold: float,
) -> dict[str, Any]:
    project_root = _repo_root()
    kpi_files = _discover_kpi_files(report_dir=report_dir, project_root=project_root)

    records: list[KPIDriftRecord] = []
    for path in kpi_files:
        record = _load_record(
            kpi_path=path,
            warning_threshold=warning_threshold,
            critical_threshold=critical_threshold,
        )
        if record is not None:
            records.append(record)

    records_sorted = sorted(records, key=lambda r: (r.severity, r.scenario, r.detector, r.source_file))
    critical = [r for r in records_sorted if r.severity == "CRITICAL"]
    warning = [r for r in records_sorted if r.severity == "WARNING"]

    if not records_sorted:
        status = "NO_DATA"
    elif critical:
        status = "FAIL"
    elif warning:
        status = "WARN"
    else:
        status = "PASS"

    return {
        "status": status,
        "warning_threshold": warning_threshold,
        "critical_threshold": critical_threshold,
        "total_kpi_files_scanned": len(kpi_files),
        "records_evaluated": len(records_sorted),
        "critical_count": len(critical),
        "warning_count": len(warning),
        "records": [asdict(item) for item in records_sorted],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report_dir", help="Run report directory (e.g., exports/demo-<run_id>)")
    parser.add_argument(
        "--warning-threshold",
        type=float,
        default=0.90,
        help="Precision proxy warning threshold (default: 0.90)",
    )
    parser.add_argument(
        "--critical-threshold",
        type=float,
        default=0.80,
        help="Precision proxy critical/fail threshold (default: 0.80)",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Optional output file path (default: <report_dir>/kpi_drift_verdict.json)",
    )
    parser.add_argument(
        "--enforce",
        action="store_true",
        help="Return non-zero when status=FAIL (default: report-only mode)",
    )
    args = parser.parse_args()

    report_dir = Path(args.report_dir).resolve()
    if not report_dir.exists():
        print(f"❌ Report directory not found: {report_dir}")
        return 1

    if args.warning_threshold <= args.critical_threshold:
        print("❌ Invalid thresholds: warning-threshold must be greater than critical-threshold")
        return 1

    verdict = build_verdict(
        report_dir=report_dir,
        warning_threshold=args.warning_threshold,
        critical_threshold=args.critical_threshold,
    )

    output_path = Path(args.output).resolve() if args.output else report_dir / "kpi_drift_verdict.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(verdict, indent=2, sort_keys=True), encoding="utf-8")

    status = verdict["status"]
    print(
        f"KPI drift verdict: {status} "
        f"(evaluated={verdict['records_evaluated']}, warnings={verdict['warning_count']}, critical={verdict['critical_count']})"
    )
    print(f"Artifact: {output_path}")

    if status == "FAIL":
        print("❌ KPI drift critical threshold breach detected")
        if args.enforce:
            return 1
        print("ℹ️ Report-only mode: continuing without non-zero exit")
        return 0
    if status == "WARN":
        print("⚠️ KPI drift warning threshold breach detected")
        return 0
    if status == "NO_DATA":
        print("ℹ️ No KPI summaries found; verdict recorded as NO_DATA")
        return 0

    print("✅ KPI drift checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
