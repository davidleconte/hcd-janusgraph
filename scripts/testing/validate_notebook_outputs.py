#!/usr/bin/env python3
"""
Validate executed notebook outputs for deterministic demo quality gates.

Checks:
1) Notebook-level execution status from report TSV
2) No error outputs in any executed code cell
3) Cells with visualization calls emit rich visualization outputs
4) Cells tied to markdown "Expected Result" produce outputs
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


EXPECTED_RESULT_RE = re.compile(r"\*\*Expected Result:\*\*\s*(.+)", re.IGNORECASE)
VISUAL_TRIGGER_RE = re.compile(
    r"(plt\.show\(|fig\.show\(|iplot\(|st\.pyplot\(|st\.plotly_chart\()"
)
VISUAL_MIME_TYPES = {
    "image/png",
    "image/svg+xml",
    "text/html",
    "application/vnd.plotly.v1+json",
    "application/vnd.vega.v5+json",
    "application/vnd.vegalite.v4+json",
    "application/vnd.vegalite.v5+json",
}


@dataclass
class NotebookValidationResult:
    notebook: str
    status: str
    exit_code: int
    code_cells: int
    error_cells: int
    expected_result_cells: int
    expected_result_cells_without_output: int
    visualization_cells: int
    visualization_cells_without_output: int
    warnings: list[str]
    issues: list[str]


def _join_output_text(outputs: list[dict[str, Any]]) -> str:
    chunks: list[str] = []
    for out in outputs:
        if out.get("output_type") == "stream":
            text = out.get("text", "")
            if isinstance(text, list):
                chunks.extend(str(t) for t in text)
            else:
                chunks.append(str(text))
            continue

        data = out.get("data", {})
        if not isinstance(data, dict):
            continue
        for key in ("text/plain", "text/markdown", "text/html"):
            if key in data:
                val = data[key]
                if isinstance(val, list):
                    chunks.extend(str(v) for v in val)
                else:
                    chunks.append(str(val))
    return "\n".join(chunks).strip()


def _has_visual_output(outputs: list[dict[str, Any]]) -> bool:
    for out in outputs:
        if out.get("output_type") not in ("display_data", "execute_result"):
            continue
        data = out.get("data", {})
        if not isinstance(data, dict):
            continue
        if any(k in data for k in VISUAL_MIME_TYPES):
            return True
        text_plain = data.get("text/plain", "")
        if isinstance(text_plain, list):
            text_plain = "\n".join(str(x) for x in text_plain)
        if "Figure(" in str(text_plain):
            return True
    return False


def _has_any_output(outputs: list[dict[str, Any]]) -> bool:
    if not outputs:
        return False
    text = _join_output_text(outputs)
    if text:
        return True
    return _has_visual_output(outputs)


def _load_notebook(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_notebook(
    executed_path: Path, row: dict[str, str], strict_visual: bool
) -> NotebookValidationResult:
    notebook_name = row["notebook"]
    status = row["status"]
    exit_code = int(row["exit_code"])
    warnings: list[str] = []
    issues: list[str] = []

    if status != "PASS":
        issues.append(f"notebook status is {status}, expected PASS")
    if exit_code != 0:
        issues.append(f"exit code is {exit_code}, expected 0")

    if not executed_path.exists():
        issues.append(f"executed notebook missing: {executed_path}")
        return NotebookValidationResult(
            notebook=notebook_name,
            status=status,
            exit_code=exit_code,
            code_cells=0,
            error_cells=0,
            expected_result_cells=0,
            expected_result_cells_without_output=0,
            visualization_cells=0,
            visualization_cells_without_output=0,
            warnings=warnings,
            issues=issues,
        )

    nb = _load_notebook(executed_path)
    cells = nb.get("cells", [])

    code_cells = 0
    error_cells = 0
    expected_result_cells = 0
    expected_result_cells_without_output = 0
    visualization_cells = 0
    visualization_cells_without_output = 0

    pending_expected_result = False
    for cell in cells:
        cell_type = cell.get("cell_type", "")
        source = "".join(cell.get("source", [])) if isinstance(cell.get("source"), list) else str(cell.get("source", ""))

        if cell_type == "markdown":
            if EXPECTED_RESULT_RE.search(source):
                pending_expected_result = True
            continue

        if cell_type != "code":
            continue

        code_cells += 1
        outputs = cell.get("outputs", []) or []

        if any(out.get("output_type") == "error" for out in outputs):
            error_cells += 1
            issues.append(f"code cell {code_cells} contains error output")

        if pending_expected_result:
            expected_result_cells += 1
            if not _has_any_output(outputs):
                expected_result_cells_without_output += 1
                issues.append(
                    f"expected-result cell {code_cells} has no output"
                )
            pending_expected_result = False

        if VISUAL_TRIGGER_RE.search(source):
            visualization_cells += 1
            if not _has_visual_output(outputs):
                visualization_cells_without_output += 1
                message = f"visualization cell {code_cells} has no rich visual output"
                if strict_visual:
                    issues.append(message)
                else:
                    warnings.append(message)

    return NotebookValidationResult(
        notebook=notebook_name,
        status=status,
        exit_code=exit_code,
        code_cells=code_cells,
        error_cells=error_cells,
        expected_result_cells=expected_result_cells,
        expected_result_cells_without_output=expected_result_cells_without_output,
        visualization_cells=visualization_cells,
        visualization_cells_without_output=visualization_cells_without_output,
        warnings=warnings,
        issues=issues,
    )


def load_report(report_path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with report_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if row.get("notebook"):
                rows.append(
                    {
                        "notebook": row["notebook"],
                        "status": row["status"],
                        "exit_code": row["exit_code"],
                    }
                )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True, help="Path to notebook_run_report.tsv")
    parser.add_argument(
        "--summary",
        required=False,
        default="",
        help="Optional JSON summary output path",
    )
    parser.add_argument(
        "--strict-visual",
        action="store_true",
        help="Fail when visualization trigger cells do not emit rich outputs",
    )
    args = parser.parse_args()

    report_path = Path(args.report).resolve()
    if not report_path.exists():
        print(f"❌ Report file not found: {report_path}")
        return 1

    report_rows = load_report(report_path)
    executed_dir = report_path.parent

    results: list[NotebookValidationResult] = []
    for row in report_rows:
        stem = Path(row["notebook"]).stem
        executed_path = executed_dir / f"{stem}.executed.ipynb"
        results.append(validate_notebook(executed_path, row, args.strict_visual))

    failures = [r for r in results if r.issues]

    print("Notebook output validation summary:")
    for result in results:
        status = "PASS" if not result.issues else "FAIL"
        print(
            f" - {result.notebook}: {status} "
            f"(code_cells={result.code_cells}, error_cells={result.error_cells}, "
            f"viz_missing={result.visualization_cells_without_output}, "
            f"expected_missing={result.expected_result_cells_without_output})"
        )

    summary = {
        "status": "PASS" if not failures else "FAIL",
        "report_path": str(report_path),
        "strict_visual": args.strict_visual,
        "validated_notebooks": len(results),
        "failed_notebooks": len(failures),
        "results": [asdict(r) for r in results],
    }

    if args.summary:
        summary_path = Path(args.summary).resolve()
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        with summary_path.open("w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, sort_keys=True)

    if failures:
        print("")
        print("❌ Notebook output integrity validation failed")
        for failed in failures:
            print(f"   {failed.notebook}:")
            for issue in failed.issues:
                print(f"     - {issue}")
        return 1

    warnings = [r for r in results if r.warnings]
    if warnings:
        print("")
        print("⚠️ Notebook output validation warnings")
        for warned in warnings:
            print(f"   {warned.notebook}:")
            for warning in warned.warnings:
                print(f"     - {warning}")

    print("")
    print("✅ Notebook output integrity validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
