#!/usr/bin/env python3
"""
Integration tests for baseline quality calculator.

Tests the calculate_baseline_quality.py script with realistic baseline scenarios.
"""

import json
import tempfile
from pathlib import Path
from typing import Dict, List

import pytest

# Import the calculator
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts" / "validation"))
from calculate_baseline_quality import BaselineQualityCalculator


class TestBaselineQualityCalculator:
    """Test suite for BaselineQualityCalculator."""

    @pytest.fixture
    def temp_baseline_dir(self, tmp_path: Path) -> Path:
        """Create temporary baseline directory."""
        baseline_dir = tmp_path / "test_baseline"
        baseline_dir.mkdir()
        return baseline_dir

    @pytest.fixture
    def perfect_baseline(self, temp_baseline_dir: Path) -> Path:
        """Create a perfect baseline with all artifacts."""
        # Create notebook report (all pass)
        report = temp_baseline_dir / "notebook-report.txt"
        report.write_text(
            "Notebook 01: PASS\n"
            "Notebook 02: PASS\n"
            "Notebook 03: PASS\n"
            "Notebook 04: PASS\n"
            "Notebook 05: PASS\n"
            "Notebook 06: PASS\n"
            "Notebook 07: PASS\n"
            "Notebook 08: PASS\n"
            "Notebook 09: PASS\n"
            "Notebook 10: PASS\n"
            "Notebook 11: PASS\n"
            "Notebook 12: PASS\n"
            "Notebook 13: PASS\n"
            "Notebook 14: PASS\n"
            "Notebook 15: PASS\n"
            "Notebook 16: PASS\n"
        )

        # Create valid checksums (5 lines exactly)
        checksums = temp_baseline_dir / "checksums.txt"
        checksum_lines = [
            "a" * 64 + " file1.txt",
            "b" * 64 + " file2.txt",
            "c" * 64 + " file3.txt",
            "d" * 64 + " file4.txt",
            "e" * 64 + " file5.txt"
        ]
        checksums.write_text("\n".join(checksum_lines) + "\n")

        # Create status file
        status = temp_baseline_dir / "deterministic-status.json"
        status.write_text('{"status": "success"}')

        # Create 16 notebooks without errors
        for i in range(1, 17):
            nb_file = temp_baseline_dir / f"notebook_{i:02d}.ipynb"
            notebook = {
                "cells": [
                    {
                        "cell_type": "code",
                        "outputs": [
                            {"output_type": "stream", "text": ["Success"]}
                        ]
                    }
                ]
            }
            nb_file.write_text(json.dumps(notebook))

        return temp_baseline_dir

    def test_perfect_baseline_scores_100(self, perfect_baseline: Path):
        """Test that a perfect baseline scores 100/100."""
        calculator = BaselineQualityCalculator(perfect_baseline)
        score, metrics = calculator.calculate_quality_score()

        assert score == 100.0, f"Expected 100.0, got {score}"
        assert metrics["notebook_pass_rate"] == 100.0
        assert metrics["checksum_stability"] == 100.0
        assert metrics["artifact_completeness"] == 100.0
        assert metrics["error_cell_absence"] == 100.0
        assert calculator.meets_quality_threshold(score)
        assert len(calculator.issues) == 0

    def test_missing_notebook_report(self, temp_baseline_dir: Path):
        """Test handling of missing notebook report."""
        calculator = BaselineQualityCalculator(temp_baseline_dir)
        pass_rate = calculator.calculate_notebook_pass_rate()

        assert pass_rate == 0.0
        assert any("notebook-report.txt not found" in issue for issue in calculator.issues)

    def test_failed_notebooks_reduce_score(self, temp_baseline_dir: Path):
        """Test that failed notebooks reduce the score."""
        # Create report with failures
        report = temp_baseline_dir / "notebook-report.txt"
        report.write_text(
            "Notebook 01: PASS\n"
            "Notebook 02: FAIL\n"
            "Notebook 03: PASS\n"
            "Notebook 04: FAIL\n"
        )

        calculator = BaselineQualityCalculator(temp_baseline_dir)
        pass_rate = calculator.calculate_notebook_pass_rate()

        assert pass_rate == 50.0  # 2 pass, 2 fail
        assert any("2 notebook(s) failed" in issue for issue in calculator.issues)

    def test_invalid_checksum_format(self, temp_baseline_dir: Path):
        """Test handling of invalid checksum format."""
        checksums = temp_baseline_dir / "checksums.txt"
        checksums.write_text(
            "invalid checksum format\n"
            "another bad line\n"
        )

        calculator = BaselineQualityCalculator(temp_baseline_dir)
        stability = calculator.calculate_checksum_stability()

        assert stability == 0.0
        assert any("Invalid checksum file" in issue for issue in calculator.issues)

    def test_partial_checksum_validity(self, temp_baseline_dir: Path):
        """Test partial checksum validity."""
        checksums = temp_baseline_dir / "checksums.txt"
        checksum_lines = [
            "a" * 64 + " file1.txt",
            "b" * 64 + " file2.txt",
            "invalid line",
            "d" * 64 + " file4.txt",
            "e" * 64 + " file5.txt"
        ]
        checksums.write_text("\n".join(checksum_lines) + "\n")

        calculator = BaselineQualityCalculator(temp_baseline_dir)
        stability = calculator.calculate_checksum_stability()

        assert stability == 80.0  # 4 valid out of 5
        assert any("Invalid checksum line" in issue for issue in calculator.issues)

    def test_missing_artifacts(self, temp_baseline_dir: Path):
        """Test detection of missing artifacts."""
        # Only create checksums, missing others
        checksums = temp_baseline_dir / "checksums.txt"
        checksums.write_text("a" * 64 + " file.txt\n" * 5)

        calculator = BaselineQualityCalculator(temp_baseline_dir)
        completeness = calculator.calculate_artifact_completeness()

        # Should have 1/4 (checksums present, others missing, notebooks insufficient)
        assert completeness == 25.0
        assert any("Missing artifact: notebook-report.txt" in issue for issue in calculator.issues)
        assert any("Missing artifact: deterministic-status.json" in issue for issue in calculator.issues)
        assert any("Insufficient notebooks" in issue for issue in calculator.issues)

    def test_sufficient_notebooks(self, temp_baseline_dir: Path):
        """Test that 15+ notebooks are considered sufficient."""
        # Create required artifacts
        (temp_baseline_dir / "checksums.txt").write_text("a" * 64 + " file.txt\n" * 5)
        (temp_baseline_dir / "notebook-report.txt").write_text("PASS\n")
        (temp_baseline_dir / "deterministic-status.json").write_text("{}")

        # Create 15 notebooks
        for i in range(15):
            nb_file = temp_baseline_dir / f"notebook_{i:02d}.ipynb"
            nb_file.write_text('{"cells": []}')

        calculator = BaselineQualityCalculator(temp_baseline_dir)
        completeness = calculator.calculate_artifact_completeness()

        assert completeness == 100.0
        assert not any("Insufficient notebooks" in issue for issue in calculator.issues)

    def test_error_cells_detected(self, temp_baseline_dir: Path):
        """Test detection of error cells in notebooks."""
        # Create notebook with error cell
        nb_file = temp_baseline_dir / "notebook_01.ipynb"
        notebook = {
            "cells": [
                {
                    "cell_type": "code",
                    "outputs": [
                        {
                            "output_type": "error",
                            "ename": "ValueError",
                            "evalue": "Test error",
                            "traceback": ["Error traceback"]
                        }
                    ]
                }
            ]
        }
        nb_file.write_text(json.dumps(notebook))

        calculator = BaselineQualityCalculator(temp_baseline_dir)
        error_score = calculator.calculate_error_cell_absence()

        assert error_score == 90.0  # 100 - (1 * 10)
        assert any("Error cell in notebook_01.ipynb" in issue for issue in calculator.issues)

    def test_multiple_error_cells_penalty(self, temp_baseline_dir: Path):
        """Test that multiple error cells increase penalty."""
        # Create notebooks with multiple errors
        for i in range(3):
            nb_file = temp_baseline_dir / f"notebook_{i:02d}.ipynb"
            notebook = {
                "cells": [
                    {
                        "cell_type": "code",
                        "outputs": [
                            {"output_type": "error", "ename": "Error"}
                        ]
                    }
                ]
            }
            nb_file.write_text(json.dumps(notebook))

        calculator = BaselineQualityCalculator(temp_baseline_dir)
        error_score = calculator.calculate_error_cell_absence()

        assert error_score == 70.0  # 100 - (3 * 10)

    def test_no_notebooks_returns_100_for_errors(self, temp_baseline_dir: Path):
        """Test that no notebooks means no errors (100%)."""
        calculator = BaselineQualityCalculator(temp_baseline_dir)
        error_score = calculator.calculate_error_cell_absence()

        assert error_score == 100.0
        assert any("No notebooks found" in warning for warning in calculator.warnings)

    def test_weighted_score_calculation(self, temp_baseline_dir: Path):
        """Test the weighted score calculation formula."""
        # Create baseline with known component scores
        # Notebook pass rate: 100% (all pass)
        report = temp_baseline_dir / "notebook-report.txt"
        report.write_text("Notebook 01: PASS\n" * 16)

        # Checksum stability: 80% (4/5 valid)
        checksums = temp_baseline_dir / "checksums.txt"
        checksum_lines = [
            "a" * 64 + " file1.txt",
            "b" * 64 + " file2.txt",
            "invalid",
            "d" * 64 + " file4.txt",
            "e" * 64 + " file5.txt"
        ]
        checksums.write_text("\n".join(checksum_lines) + "\n")

        # Artifact completeness: 100% (all artifacts present + 15 notebooks)
        (temp_baseline_dir / "deterministic-status.json").write_text("{}")
        for i in range(15):
            (temp_baseline_dir / f"notebook_{i:02d}.ipynb").write_text('{"cells": []}')

        # Error cell absence: 90% (1 error in notebook_error.ipynb)
        nb_error = temp_baseline_dir / "notebook_error.ipynb"
        nb_error.write_text(json.dumps({
            "cells": [{
                "cell_type": "code",
                "outputs": [{"output_type": "error"}]
            }]
        }))

        calculator = BaselineQualityCalculator(temp_baseline_dir)
        score, metrics = calculator.calculate_quality_score()

        # Verify component scores
        assert metrics["notebook_pass_rate"] == 100.0
        assert metrics["checksum_stability"] == 80.0
        assert metrics["artifact_completeness"] == 100.0  # All artifacts present
        assert metrics["error_cell_absence"] == 90.0

        # Expected: 100*0.4 + 80*0.3 + 100*0.2 + 90*0.1 = 40 + 24 + 20 + 9 = 93
        expected_score = 100 * 0.40 + 80 * 0.30 + 100 * 0.20 + 90 * 0.10
        assert abs(score - expected_score) < 0.01, f"Expected {expected_score}, got {score}"

    def test_quality_threshold_check(self, temp_baseline_dir: Path):
        """Test quality threshold checking."""
        calculator = BaselineQualityCalculator(temp_baseline_dir)

        assert calculator.meets_quality_threshold(95.0)
        assert calculator.meets_quality_threshold(100.0)
        assert not calculator.meets_quality_threshold(94.9)
        assert not calculator.meets_quality_threshold(0.0)

    def test_report_generation(self, perfect_baseline: Path):
        """Test report generation."""
        calculator = BaselineQualityCalculator(perfect_baseline)
        score, metrics = calculator.calculate_quality_score()
        report = calculator.generate_report(score, metrics)

        assert "BASELINE QUALITY REPORT" in report
        assert "Overall Quality Score: 100.00/100" in report
        assert "✅ PASS" in report
        assert "Notebook Pass Rate: 100.00%" in report
        assert "Checksum Stability: 100.00%" in report
        assert "Artifact Completeness: 100.00%" in report
        assert "Error Cell Absence: 100.00%" in report

    def test_report_shows_issues(self, temp_baseline_dir: Path):
        """Test that report shows issues."""
        calculator = BaselineQualityCalculator(temp_baseline_dir)
        score, metrics = calculator.calculate_quality_score()
        report = calculator.generate_report(score, metrics)

        assert "ISSUES" in report
        assert "❌" in report
        assert "notebook-report.txt not found" in report

    def test_report_shows_warnings(self, temp_baseline_dir: Path):
        """Test that report shows warnings."""
        calculator = BaselineQualityCalculator(temp_baseline_dir)
        _ = calculator.calculate_error_cell_absence()  # Generates warning
        score, metrics = calculator.calculate_quality_score()
        report = calculator.generate_report(score, metrics)

        assert "WARNINGS" in report
        assert "⚠️" in report

    def test_invalid_json_notebook_handling(self, temp_baseline_dir: Path):
        """Test handling of invalid JSON in notebooks."""
        nb_file = temp_baseline_dir / "invalid.ipynb"
        nb_file.write_text("not valid json")

        calculator = BaselineQualityCalculator(temp_baseline_dir)
        error_score = calculator.calculate_error_cell_absence()

        # Should handle gracefully with warning
        assert error_score == 100.0  # No valid notebooks = no errors
        assert any("Error reading invalid.ipynb" in warning for warning in calculator.warnings)

    def test_empty_notebook_report(self, temp_baseline_dir: Path):
        """Test handling of empty notebook report."""
        report = temp_baseline_dir / "notebook-report.txt"
        report.write_text("")

        calculator = BaselineQualityCalculator(temp_baseline_dir)
        pass_rate = calculator.calculate_notebook_pass_rate()

        assert pass_rate == 0.0
        assert any("No notebook results found" in issue for issue in calculator.issues)

    def test_non_hex_checksum(self, temp_baseline_dir: Path):
        """Test handling of non-hexadecimal checksums."""
        checksums = temp_baseline_dir / "checksums.txt"
        checksum_lines = [
            "g" * 64 + " file1.txt",  # 'g' is not valid hex
            "b" * 64 + " file2.txt",
            "c" * 64 + " file3.txt",
            "d" * 64 + " file4.txt",
            "e" * 64 + " file5.txt"
        ]
        checksums.write_text("\n".join(checksum_lines) + "\n")

        calculator = BaselineQualityCalculator(temp_baseline_dir)
        stability = calculator.calculate_checksum_stability()

        assert stability == 80.0  # 4 valid out of 5
        assert any("Invalid checksum format" in issue for issue in calculator.issues)

    def test_below_threshold_fails_strict_mode(self, temp_baseline_dir: Path):
        """Test that below-threshold scores fail in strict mode."""
        # Create minimal baseline (will score low)
        report = temp_baseline_dir / "notebook-report.txt"
        report.write_text("Notebook 01: FAIL\n")

        calculator = BaselineQualityCalculator(temp_baseline_dir)
        score, _ = calculator.calculate_quality_score()

        assert score < 95.0
        assert not calculator.meets_quality_threshold(score)


class TestBaselineQualityCalculatorEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_exactly_15_notebooks(self, tmp_path: Path):
        """Test that exactly 15 notebooks meets threshold."""
        baseline_dir = tmp_path / "baseline"
        baseline_dir.mkdir()

        # Create required artifacts
        (baseline_dir / "checksums.txt").write_text("a" * 64 + " file.txt\n" * 5)
        (baseline_dir / "notebook-report.txt").write_text("PASS\n")
        (baseline_dir / "deterministic-status.json").write_text("{}")

        # Create exactly 15 notebooks
        for i in range(15):
            (baseline_dir / f"notebook_{i:02d}.ipynb").write_text('{"cells": []}')

        calculator = BaselineQualityCalculator(baseline_dir)
        completeness = calculator.calculate_artifact_completeness()

        assert completeness == 100.0

    def test_14_notebooks_insufficient(self, tmp_path: Path):
        """Test that 14 notebooks is insufficient."""
        baseline_dir = tmp_path / "baseline"
        baseline_dir.mkdir()

        # Create required artifacts
        (baseline_dir / "checksums.txt").write_text("a" * 64 + " file.txt\n" * 5)
        (baseline_dir / "notebook-report.txt").write_text("PASS\n")
        (baseline_dir / "deterministic-status.json").write_text("{}")

        # Create only 14 notebooks
        for i in range(14):
            (baseline_dir / f"notebook_{i:02d}.ipynb").write_text('{"cells": []}')

        calculator = BaselineQualityCalculator(baseline_dir)
        completeness = calculator.calculate_artifact_completeness()

        assert completeness == 75.0  # 3/4 (notebooks insufficient)
        assert any("Insufficient notebooks: expected ≥15, got 14" in issue 
                   for issue in calculator.issues)

    def test_score_exactly_95(self, tmp_path: Path):
        """Test boundary condition: score exactly 95.0."""
        baseline_dir = tmp_path / "baseline"
        baseline_dir.mkdir()

        calculator = BaselineQualityCalculator(baseline_dir)
        
        # Test boundary
        assert calculator.meets_quality_threshold(95.0)
        assert not calculator.meets_quality_threshold(94.999)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob
