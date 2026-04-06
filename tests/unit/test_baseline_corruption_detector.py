#!/usr/bin/env python3
"""
Tests for baseline corruption detection.

Tests the detect_baseline_corruption.py script with various corruption scenarios.
"""

import hashlib
import json
import tempfile
from pathlib import Path

import pytest

# Import the detector
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts" / "validation"))
from detect_baseline_corruption import BaselineCorruptionDetector


class TestBaselineCorruptionDetector:
    """Test suite for BaselineCorruptionDetector."""

    @pytest.fixture
    def clean_baseline(self, tmp_path: Path) -> Path:
        """Create a clean baseline directory."""
        baseline_dir = tmp_path / "clean_baseline"
        baseline_dir.mkdir()

        # Create notebooks
        for i in range(1, 17):
            nb_file = baseline_dir / f"notebook_{i:02d}.ipynb"
            notebook = {"cells": [{"cell_type": "code", "outputs": []}]}
            nb_file.write_text(json.dumps(notebook))

        # Create notebook report
        report = baseline_dir / "notebook-report.txt"
        report.write_text("Notebook 01: PASS\n" * 16)

        # Create status file
        status = baseline_dir / "deterministic-status.json"
        status.write_text('{"status": "success"}')

        # Create checksums
        checksums = baseline_dir / "checksums.txt"
        checksum_lines = []
        for i in range(1, 17):
            nb_file = baseline_dir / f"notebook_{i:02d}.ipynb"
            checksum = self._calculate_sha256(nb_file)
            checksum_lines.append(f"{checksum} notebook_{i:02d}.ipynb")
        checksums.write_text("\n".join(checksum_lines) + "\n")

        return baseline_dir

    def _calculate_sha256(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def test_clean_baseline_passes(self, clean_baseline: Path):
        """Test that a clean baseline passes all checks."""
        detector = BaselineCorruptionDetector(clean_baseline)
        corrupted, issues, warnings = detector.detect_corruption()

        assert not corrupted
        assert len(issues) == 0
        assert len(warnings) == 0

    def test_missing_required_file(self, clean_baseline: Path):
        """Test detection of missing required files."""
        # Remove checksums file
        (clean_baseline / "checksums.txt").unlink()

        detector = BaselineCorruptionDetector(clean_baseline)
        corrupted, issues, warnings = detector.detect_corruption()

        assert corrupted
        assert any("checksums.txt" in issue for issue in issues)

    def test_checksum_mismatch(self, clean_baseline: Path):
        """Test detection of checksum mismatches."""
        # Modify a notebook after checksums were created
        nb_file = clean_baseline / "notebook_01.ipynb"
        notebook = {"cells": [{"cell_type": "code", "outputs": ["modified"]}]}
        nb_file.write_text(json.dumps(notebook))

        detector = BaselineCorruptionDetector(clean_baseline)
        corrupted, issues, warnings = detector.detect_corruption()

        assert corrupted
        assert any("Checksum mismatch" in issue and "notebook_01.ipynb" in issue 
                   for issue in issues)

    def test_insufficient_notebooks(self, tmp_path: Path):
        """Test detection of insufficient notebook count."""
        baseline_dir = tmp_path / "baseline"
        baseline_dir.mkdir()

        # Create only 10 notebooks (less than required 16)
        for i in range(1, 11):
            nb_file = baseline_dir / f"notebook_{i:02d}.ipynb"
            nb_file.write_text('{"cells": []}')

        # Create other required files
        (baseline_dir / "notebook-report.txt").write_text("PASS\n")
        (baseline_dir / "deterministic-status.json").write_text("{}")
        (baseline_dir / "checksums.txt").write_text("a" * 64 + " file.txt\n")

        detector = BaselineCorruptionDetector(baseline_dir)
        corrupted, issues, warnings = detector.detect_corruption()

        assert corrupted
        assert any("Insufficient notebooks" in issue for issue in issues)

    def test_invalid_json_file(self, clean_baseline: Path):
        """Test detection of invalid JSON files."""
        # Corrupt the status file
        status_file = clean_baseline / "deterministic-status.json"
        status_file.write_text("not valid json {")

        detector = BaselineCorruptionDetector(clean_baseline)
        corrupted, issues, warnings = detector.detect_corruption()

        assert corrupted
        assert any("Invalid JSON" in issue and "deterministic-status.json" in issue 
                   for issue in issues)

    def test_invalid_notebook_json(self, clean_baseline: Path):
        """Test detection of invalid notebook JSON."""
        # Corrupt a notebook
        nb_file = clean_baseline / "notebook_01.ipynb"
        nb_file.write_text("not valid json")

        detector = BaselineCorruptionDetector(clean_baseline)
        corrupted, issues, warnings = detector.detect_corruption()

        assert corrupted
        assert any("Invalid JSON" in issue and "notebook_01.ipynb" in issue 
                   for issue in issues)

    def test_notebook_missing_cells(self, clean_baseline: Path):
        """Test detection of notebooks with invalid structure."""
        # Create notebook without cells
        nb_file = clean_baseline / "notebook_01.ipynb"
        nb_file.write_text('{"metadata": {}}')

        detector = BaselineCorruptionDetector(clean_baseline)
        corrupted, issues, warnings = detector.detect_corruption()

        assert corrupted
        assert any("Invalid notebook structure" in issue and "notebook_01.ipynb" in issue 
                   for issue in issues)

    def test_empty_notebook_report(self, clean_baseline: Path):
        """Test detection of empty notebook report."""
        report_file = clean_baseline / "notebook-report.txt"
        report_file.write_text("")

        detector = BaselineCorruptionDetector(clean_baseline)
        corrupted, issues, warnings = detector.detect_corruption()

        assert corrupted
        assert any("notebook-report.txt is empty" in issue for issue in issues)

    def test_unexpected_files_warning(self, clean_baseline: Path):
        """Test warning for unexpected files."""
        # Add unexpected file
        (clean_baseline / "unexpected.txt").write_text("unexpected content")

        detector = BaselineCorruptionDetector(clean_baseline)
        corrupted, issues, warnings = detector.detect_corruption()

        # Should warn but not mark as corrupted
        assert any("Unexpected file" in warning for warning in warnings)

    def test_file_referenced_in_checksums_missing(self, clean_baseline: Path):
        """Test detection of files referenced in checksums but missing."""
        # Add reference to non-existent file in checksums
        checksums_file = clean_baseline / "checksums.txt"
        with open(checksums_file, "a") as f:
            f.write("a" * 64 + " missing_file.txt\n")

        detector = BaselineCorruptionDetector(clean_baseline)
        corrupted, issues, warnings = detector.detect_corruption()

        assert corrupted
        assert any("File referenced in checksums not found" in issue 
                   for issue in issues)

    def test_report_generation(self, clean_baseline: Path):
        """Test report generation."""
        detector = BaselineCorruptionDetector(clean_baseline)
        detector.detect_corruption()
        report = detector.generate_report()

        assert "BASELINE CORRUPTION DETECTION REPORT" in report
        assert "✅ CLEAN" in report
        assert "All integrity checks passed" in report

    def test_corrupted_report_generation(self, clean_baseline: Path):
        """Test report generation for corrupted baseline."""
        # Remove required file
        (clean_baseline / "checksums.txt").unlink()

        detector = BaselineCorruptionDetector(clean_baseline)
        detector.detect_corruption()
        report = detector.generate_report()

        assert "BASELINE CORRUPTION DETECTION REPORT" in report
        assert "❌ CORRUPTED" in report
        assert "CORRUPTION ISSUES" in report

    def test_excessive_notebooks_warning(self, clean_baseline: Path):
        """Test warning for excessive notebook count."""
        # Add many extra notebooks
        for i in range(17, 30):
            nb_file = clean_baseline / f"notebook_{i:02d}.ipynb"
            nb_file.write_text('{"cells": []}')

        detector = BaselineCorruptionDetector(clean_baseline)
        corrupted, issues, warnings = detector.detect_corruption()

        assert any("Unexpected number of notebooks" in warning for warning in warnings)

    def test_notebook_report_with_errors(self, clean_baseline: Path):
        """Test warning for ERROR keywords in report."""
        report_file = clean_baseline / "notebook-report.txt"
        report_file.write_text("Notebook 01: PASS\nERROR: Something went wrong\n")

        detector = BaselineCorruptionDetector(clean_baseline)
        corrupted, issues, warnings = detector.detect_corruption()

        assert any("ERROR/EXCEPTION keywords" in warning for warning in warnings)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob
