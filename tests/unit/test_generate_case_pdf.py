"""
Unit tests for scripts/reporting/generate_case_pdf.py.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


def _load_module():
    module_path = Path("scripts/reporting/generate_case_pdf.py").resolve()
    module_name = "generate_case_pdf"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_generate_case_pdf_writes_valid_pdf(tmp_path):
    """PDF generator should write a deterministic single-page PDF artifact."""
    module = _load_module()

    case_data = {
        "alert_id": "ALERT-123",
        "timestamp": "2026-03-29T18:00:00Z",
        "detector": "SanctionsScreener",
        "decision": "REVIEW",
        "confidence": 0.91,
        "risk_score": 0.88,
        "victim_id": "CUST-001",
        "reason_codes": ["SANCTION_NAME_MATCH", "JURISDICTION_MATCH"],
        "evidence_summary": "Potential sanctions hit requiring analyst review.",
    }

    output_pdf = tmp_path / "alert-123.pdf"
    module.generate_case_pdf(case_data=case_data, output_pdf_path=output_pdf)

    content = output_pdf.read_bytes()
    assert output_pdf.is_file()
    assert content.startswith(b"%PDF-1.4")
    assert b"Case Evidence Report" in content
    assert b"ALERT-123" in content


def test_generate_case_pdf_from_file(tmp_path):
    """File-based wrapper should parse JSON and generate a PDF."""
    module = _load_module()

    input_json = tmp_path / "case.json"
    input_json.write_text(
        json.dumps(
            {
                "alert_id": "ALERT-456",
                "decision": "ESCALATE",
                "reason_codes": ["ENTITY_TYPE_MATCH"],
            }
        ),
        encoding="utf-8",
    )
    output_pdf = tmp_path / "case.pdf"

    module.generate_case_pdf_from_file(
        input_json_path=input_json,
        output_pdf_path=output_pdf,
        title="Regulator Evidence",
    )

    content = output_pdf.read_bytes()
    assert output_pdf.is_file()
    assert b"Regulator Evidence" in content
    assert b"ALERT-456" in content
