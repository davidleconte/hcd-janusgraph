#!/usr/bin/env python3
"""
Generate deterministic regulator-ready PDF reports from case evidence JSON (FR-045).
"""

from __future__ import annotations

import argparse
import json
import textwrap
from pathlib import Path
from typing import Any

LINES_PER_PAGE = 48


def _escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _object_bytes(index: int, payload: bytes) -> bytes:
    return f"{index} 0 obj\n".encode("utf-8") + payload + b"\nendobj\n"


def _build_page_stream(lines: list[str]) -> bytes:
    escaped_lines = [_escape_pdf_text(line) for line in lines]
    stream_lines = ["BT", "/F1 11 Tf", "50 790 Td", "14 TL"]
    for line in escaped_lines:
        stream_lines.append(f"({line}) Tj")
        stream_lines.append("T*")
    stream_lines.append("ET")
    return "\n".join(stream_lines).encode("utf-8")


def _chunk_lines(lines: list[str], chunk_size: int) -> list[list[str]]:
    if not lines:
        return [[]]
    return [lines[index : index + chunk_size] for index in range(0, len(lines), chunk_size)]


def _build_pdf_bytes(lines: list[str]) -> bytes:
    pages = _chunk_lines(lines, LINES_PER_PAGE)
    page_count = len(pages)

    font_object_index = 3 + (2 * page_count)
    page_kids = " ".join(f"{3 + (2 * page_idx)} 0 R" for page_idx in range(page_count))

    objects: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        f"<< /Type /Pages /Kids [{page_kids}] /Count {page_count} >>".encode("utf-8"),
    ]

    for page_idx, page_lines in enumerate(pages):
        page_object_index = 3 + (2 * page_idx)
        content_object_index = page_object_index + 1
        stream_content = _build_page_stream(page_lines)

        page_object = (
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Contents {content_object_index} 0 R "
            f"/Resources << /Font << /F1 {font_object_index} 0 R >> >> >>"
        ).encode("utf-8")

        content_object = (
            b"<< /Length "
            + str(len(stream_content)).encode("utf-8")
            + b" >>\nstream\n"
            + stream_content
            + b"\nendstream"
        )

        objects.extend([page_object, content_object])

    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    header = b"%PDF-1.4\n"
    body = b""
    offsets = [0]
    current_offset = len(header)

    for idx, obj in enumerate(objects, start=1):
        obj_bytes = _object_bytes(idx, obj)
        offsets.append(current_offset)
        body += obj_bytes
        current_offset += len(obj_bytes)

    xref_offset = len(header) + len(body)
    xref = [f"xref\n0 {len(objects) + 1}\n", "0000000000 65535 f \n"]
    for offset in offsets[1:]:
        xref.append(f"{offset:010d} 00000 n \n")
    xref_bytes = "".join(xref).encode("utf-8")

    trailer = (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode(
            "utf-8"
        )
    )
    return header + body + xref_bytes + trailer


def _render_case_lines(case_data: dict[str, Any], title: str) -> list[str]:
    lines: list[str] = [title, ""]
    ordered_keys = [
        "alert_id",
        "timestamp",
        "detector",
        "decision",
        "confidence",
        "risk_score",
        "victim_id",
    ]

    for key in ordered_keys:
        if key in case_data:
            lines.append(f"{key}: {case_data[key]}")

    if "reason_codes" in case_data:
        lines.append("reason_codes:")
        reason_codes = case_data.get("reason_codes", [])
        if isinstance(reason_codes, list):
            for item in reason_codes:
                lines.append(f"  - {item}")
        else:
            lines.append(f"  - {reason_codes}")

    if "evidence_summary" in case_data:
        lines.append("")
        lines.append("evidence_summary:")
        summary = str(case_data["evidence_summary"])
        for wrapped in textwrap.wrap(summary, width=90) or [""]:
            lines.append(f"  {wrapped}")

    remaining = sorted(k for k in case_data if k not in set(ordered_keys + ["reason_codes", "evidence_summary"]))
    if remaining:
        lines.append("")
        lines.append("additional_fields:")
        for key in remaining:
            value = case_data[key]
            rendered = json.dumps(value, sort_keys=True) if isinstance(value, (dict, list)) else str(value)
            for wrapped in textwrap.wrap(f"{key}: {rendered}", width=90) or [""]:
                lines.append(f"  {wrapped}")

    return lines


def generate_case_pdf(case_data: dict[str, Any], output_pdf_path: Path, title: str = "Case Evidence Report") -> Path:
    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    lines = _render_case_lines(case_data=case_data, title=title)
    output_pdf_path.write_bytes(_build_pdf_bytes(lines))
    return output_pdf_path


def generate_case_pdf_from_file(input_json_path: Path, output_pdf_path: Path, title: str = "Case Evidence Report") -> Path:
    payload = json.loads(input_json_path.read_text(encoding="utf-8"))
    return generate_case_pdf(case_data=payload, output_pdf_path=output_pdf_path, title=title)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-json", required=True, help="Path to case evidence JSON file")
    parser.add_argument("--output-pdf", required=True, help="Path to output PDF file")
    parser.add_argument("--title", default="Case Evidence Report", help="PDF report title")
    args = parser.parse_args()

    input_json_path = Path(args.input_json).resolve()
    output_pdf_path = Path(args.output_pdf).resolve()

    if not input_json_path.is_file():
        print(f"❌ Input JSON not found: {input_json_path}")
        return 1

    generate_case_pdf_from_file(
        input_json_path=input_json_path,
        output_pdf_path=output_pdf_path,
        title=args.title,
    )
    print(f"PDF generated: {output_pdf_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
