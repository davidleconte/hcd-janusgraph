"""
Unit tests for scripts/testing/detect_kpi_drift.py.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


def _load_module():
    module_path = Path("scripts/testing/detect_kpi_drift.py").resolve()
    module_name = "detect_kpi_drift"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_build_verdict_pass(tmp_path):
    """PASS when all precision_proxy values meet warning threshold."""
    module = _load_module()

    kpi_file = tmp_path / "sanctions_kpi.json"
    kpi_file.write_text(
        json.dumps(
            {
                "scenario": "sanctions",
                "detector": "SanctionsScreener",
                "precision_proxy": 0.95,
            }
        ),
        encoding="utf-8",
    )

    module._discover_kpi_files = lambda report_dir, project_root: [kpi_file]  # noqa: SLF001
    verdict = module.build_verdict(
        report_dir=tmp_path,
        warning_threshold=0.90,
        critical_threshold=0.80,
    )

    assert verdict["status"] == "PASS"
    assert verdict["warning_count"] == 0
    assert verdict["critical_count"] == 0
    assert verdict["records_evaluated"] == 1


def test_build_verdict_warn(tmp_path):
    """WARN when precision_proxy is below warning but above critical threshold."""
    module = _load_module()

    kpi_file = tmp_path / "aml_kpi.json"
    kpi_file.write_text(
        json.dumps(
            {
                "scenario": "aml_structuring",
                "detector": "EnhancedStructuringDetector",
                "precision_proxy": 0.85,
            }
        ),
        encoding="utf-8",
    )

    module._discover_kpi_files = lambda report_dir, project_root: [kpi_file]  # noqa: SLF001
    verdict = module.build_verdict(
        report_dir=tmp_path,
        warning_threshold=0.90,
        critical_threshold=0.80,
    )

    assert verdict["status"] == "WARN"
    assert verdict["warning_count"] == 1
    assert verdict["critical_count"] == 0
    assert verdict["records"][0]["severity"] == "WARNING"


def test_build_verdict_fail(tmp_path):
    """FAIL when precision_proxy breaches critical threshold."""
    module = _load_module()

    kpi_file = tmp_path / "fraud_kpi.json"
    kpi_file.write_text(
        json.dumps(
            {
                "scenario": "fraud_detection",
                "detector": "FraudDetector",
                "precision_proxy": 0.72,
            }
        ),
        encoding="utf-8",
    )

    module._discover_kpi_files = lambda report_dir, project_root: [kpi_file]  # noqa: SLF001
    verdict = module.build_verdict(
        report_dir=tmp_path,
        warning_threshold=0.90,
        critical_threshold=0.80,
    )

    assert verdict["status"] == "FAIL"
    assert verdict["warning_count"] == 0
    assert verdict["critical_count"] == 1
    assert verdict["records"][0]["severity"] == "CRITICAL"


def test_build_verdict_no_data(tmp_path):
    """NO_DATA when no KPI summary files are available."""
    module = _load_module()

    module._discover_kpi_files = lambda report_dir, project_root: []  # noqa: SLF001
    verdict = module.build_verdict(
        report_dir=tmp_path,
        warning_threshold=0.90,
        critical_threshold=0.80,
    )

    assert verdict["status"] == "NO_DATA"
    assert verdict["records_evaluated"] == 0
    assert verdict["warning_count"] == 0
    assert verdict["critical_count"] == 0
