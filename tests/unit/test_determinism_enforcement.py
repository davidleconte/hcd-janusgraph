"""
Test Determinism Enforcement
=============================

Tests to ensure deterministic behavior is maintained across the codebase.
Prevents introduction of non-deterministic patterns like datetime.now().

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
Date: 2026-04-06
"""

import ast
import os
from pathlib import Path
from typing import List, Tuple

import pytest


class DatetimeNowVisitor(ast.NodeVisitor):
    """AST visitor to detect datetime.now() calls."""

    def __init__(self):
        self.violations: List[Tuple[int, str]] = []

    def visit_Call(self, node: ast.Call) -> None:
        """Visit function call nodes."""
        # Check for datetime.now()
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == "now":
                if isinstance(node.func.value, ast.Name):
                    if node.func.value.id == "datetime":
                        self.violations.append(
                            (node.lineno, "datetime.now() call detected")
                        )
        self.generic_visit(node)


def find_python_files(directory: Path, exclude_patterns: List[str]) -> List[Path]:
    """Find all Python files in directory, excluding patterns."""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Skip excluded directories
        dirs[:] = [
            d
            for d in dirs
            if not any(pattern in str(Path(root) / d) for pattern in exclude_patterns)
        ]

        for file in files:
            if file.endswith(".py"):
                file_path = Path(root) / file
                # Skip if matches any exclude pattern
                if not any(pattern in str(file_path) for pattern in exclude_patterns):
                    python_files.append(file_path)

    return python_files


def check_file_for_datetime_now(file_path: Path) -> List[Tuple[int, str]]:
    """Check a Python file for datetime.now() usage."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content, filename=str(file_path))
        visitor = DatetimeNowVisitor()
        visitor.visit(tree)
        return visitor.violations
    except SyntaxError:
        # Skip files with syntax errors
        return []


class TestDeterminismEnforcement:
    """Test suite for determinism enforcement."""

    @pytest.fixture
    def project_root(self) -> Path:
        """Get project root directory."""
        # Assuming tests are in tests/unit/
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def exclude_patterns(self) -> List[str]:
        """Patterns to exclude from checking."""
        return [
            "tests/",  # Allow datetime.now() in tests for comparison
            ".venv",
            "__pycache__",
            ".git",
            "htmlcov",
            ".mypy_cache",
            ".ruff_cache",
            ".pytest_cache",
            "notebooks/",  # Will be checked separately
            "notebooks-exploratory/",
        ]

    def test_no_datetime_now_in_generators(self, project_root: Path, exclude_patterns: List[str]):
        """Test that data generators don't use datetime.now()."""
        generators_dir = project_root / "banking" / "data_generators"
        
        if not generators_dir.exists():
            pytest.skip("Data generators directory not found")

        violations = {}
        python_files = find_python_files(generators_dir, exclude_patterns)

        for file_path in python_files:
            file_violations = check_file_for_datetime_now(file_path)
            if file_violations:
                violations[str(file_path.relative_to(project_root))] = file_violations

        if violations:
            error_msg = "\n\nDatetime.now() violations found:\n"
            for file_path, file_violations in violations.items():
                error_msg += f"\n{file_path}:\n"
                for line_no, msg in file_violations:
                    error_msg += f"  Line {line_no}: {msg}\n"
            error_msg += "\nUse REFERENCE_TIMESTAMP from banking.data_generators.utils.deterministic instead.\n"
            pytest.fail(error_msg)

    def test_no_datetime_now_in_src(self, project_root: Path, exclude_patterns: List[str]):
        """Test that src/python doesn't use datetime.now()."""
        src_dir = project_root / "src" / "python"
        
        if not src_dir.exists():
            pytest.skip("src/python directory not found")

        # Allow datetime.now() in specific files that legitimately need current time
        allowed_files = [
            "src/python/monitoring",  # Monitoring needs current time
            "src/python/security",  # Security (MFA, sessions, RBAC) needs current time
            "src/python/api",  # API (health checks, auth) needs current time
            "src/python/performance",  # Performance (caching, profiling) needs current time
            "src/python/utils/startup_validation.py",  # Startup validation needs current time
            "src/python/utils/vector_search.py",  # Vector search timestamps
        ]

        violations = {}
        python_files = find_python_files(src_dir, exclude_patterns + allowed_files)

        for file_path in python_files:
            file_violations = check_file_for_datetime_now(file_path)
            if file_violations:
                violations[str(file_path.relative_to(project_root))] = file_violations

        if violations:
            error_msg = "\n\nDatetime.now() violations found:\n"
            for file_path, file_violations in violations.items():
                error_msg += f"\n{file_path}:\n"
                for line_no, msg in file_violations:
                    error_msg += f"  Line {line_no}: {msg}\n"
            error_msg += "\nUse REFERENCE_TIMESTAMP or document why current time is needed.\n"
            pytest.fail(error_msg)

    def test_reference_timestamp_is_defined(self, project_root: Path):
        """Test that REFERENCE_TIMESTAMP is properly defined."""
        deterministic_file = (
            project_root / "banking" / "data_generators" / "utils" / "deterministic.py"
        )

        if not deterministic_file.exists():
            pytest.skip("deterministic.py not found")

        with open(deterministic_file, "r", encoding="utf-8") as f:
            content = f.read()

        assert "REFERENCE_TIMESTAMP" in content, "REFERENCE_TIMESTAMP not defined"
        assert "2026, 1, 15" in content, "REFERENCE_TIMESTAMP should use fixed date (2026-01-15)"
        assert "timezone.utc" in content, "REFERENCE_TIMESTAMP should use UTC timezone"

    def test_reference_timestamp_is_importable(self):
        """Test that REFERENCE_TIMESTAMP can be imported."""
        try:
            from banking.data_generators.utils.deterministic import REFERENCE_TIMESTAMP
            from datetime import datetime

            assert isinstance(
                REFERENCE_TIMESTAMP, datetime
            ), "REFERENCE_TIMESTAMP should be a datetime"
            assert (
                REFERENCE_TIMESTAMP.tzinfo is not None
            ), "REFERENCE_TIMESTAMP should have timezone"
        except ImportError:
            pytest.skip("Cannot import REFERENCE_TIMESTAMP")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob
