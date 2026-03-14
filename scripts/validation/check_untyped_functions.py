#!/usr/bin/env python3
"""
Check for untyped public functions in changed files.

Enforces CODEX-P0-002: No new untyped public functions.
- Public functions are those NOT starting with underscore
- Functions must have type hints for all parameters and return type

Usage:
    python scripts/validation/check_untyped_functions.py [--base-ref HEAD~1] [--head-ref HEAD]
"""

import argparse
import ast
import subprocess
import sys
from pathlib import Path
from typing import List, Optional


INCLUDE_ROOTS = ("src/python/", "banking/")
EXCLUDE_PATTERNS = ("tests/", "test_", "__pycache__", "conftest.py")


class FunctionChecker(ast.NodeVisitor):
    """AST visitor to find untyped public functions."""
    
    def __init__(self, filename: str):
        self.filename = filename
        self.violations: List[dict] = []
        self.current_class: Optional[str] = None
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._check_function(node)
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._check_function(node)
        self.generic_visit(node)
    
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class
    
    def _check_function(self, node) -> None:
        """Check if a function has proper type hints."""
        # Skip private/protected methods
        if node.name.startswith("_"):
            return
        
        # Skip if inside a test file
        if any(p in self.filename for p in EXCLUDE_PATTERNS):
            return
        
        issues = []
        
        # Check parameter annotations (skip self, cls)
        args_to_check = node.args.args
        if args_to_check and args_to_check[0].arg in ("self", "cls"):
            args_to_check = args_to_check[1:]
        
        for arg in args_to_check:
            if arg.annotation is None:
                issues.append(f"parameter '{arg.arg}' missing type hint")
        
        # Check *args annotation
        if node.args.vararg and node.args.vararg.annotation is None:
            issues.append(f"*{node.args.vararg.arg} missing type hint")
        
        # Check **kwargs annotation
        if node.args.kwarg and node.args.kwarg.annotation is None:
            issues.append(f"**{node.args.kwarg.arg} missing type hint")
        
        # Check return annotation
        if node.returns is None:
            # Allow None for __init__ and procedures that return None implicitly
            if node.name != "__init__" and not self._is_init_method(node):
                issues.append("missing return type hint")
        
        if issues:
            location = f"{self.filename}:{node.lineno}"
            func_name = f"{self.current_class}.{node.name}" if self.current_class else node.name
            self.violations.append({
                "location": location,
                "function": func_name,
                "issues": issues,
            })
    
    def _is_init_method(self, node) -> bool:
        """Check if this is an __init__ method."""
        return node.name == "__init__" and self.current_class is not None


def get_changed_files(base_ref: str, head_ref: str) -> List[str]:
    """Get list of changed Python files."""
    result = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACMR", f"{base_ref}...{head_ref}"],
        capture_output=True,
        text=True,
    )
    
    if result.returncode != 0:
        result = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=ACMR", f"{base_ref}..{head_ref}"],
            capture_output=True,
            text=True,
        )
    
    files = []
    for line in result.stdout.strip().split("\n"):
        path = line.strip()
        if not path.endswith(".py"):
            continue
        if not any(path.startswith(r) for r in INCLUDE_ROOTS):
            continue
        if any(p in path for p in EXCLUDE_PATTERNS):
            continue
        files.append(path)
    
    return files


def check_file(filepath: str) -> List[dict]:
    """Check a single file for untyped functions."""
    try:
        with open(filepath) as f:
            source = f.read()
        
        tree = ast.parse(source)
        checker = FunctionChecker(filepath)
        checker.visit(tree)
        return checker.violations
    except SyntaxError as e:
        return [{"location": filepath, "error": f"Syntax error: {e}"}]
    except FileNotFoundError:
        return []


def main():
    parser = argparse.ArgumentParser(description="Check for untyped public functions")
    parser.add_argument("--base-ref", default="HEAD~1", help="Base git ref")
    parser.add_argument("--head-ref", default="HEAD", help="Head git ref")
    parser.add_argument("--all", action="store_true", help="Check all files, not just changed")
    parser.add_argument("--baseline", type=Path, help="Baseline file to compare against")
    parser.add_argument("--update-baseline", action="store_true", help="Update baseline file")
    args = parser.parse_args()
    
    if args.all:
        # Check all Python files in scope
        files = []
        for root in INCLUDE_ROOTS:
            root_path = Path(root)
            if root_path.exists():
                files.extend(str(p) for p in root_path.rglob("*.py") 
                           if not any(x in str(p) for x in EXCLUDE_PATTERNS))
    else:
        files = get_changed_files(args.base_ref, args.head_ref)
    
    if not files:
        print("✅ No Python files to check")
        return 0
    
    print(f"🔍 Checking {len(files)} files for untyped public functions...")
    
    all_violations = []
    for filepath in files:
        violations = check_file(filepath)
        all_violations.extend(violations)
    
    if not all_violations:
        print("✅ All public functions have proper type hints")
        return 0
    
    # Format violations for comparison (no leading spaces for clean comparison)
    violation_lines = set()
    for v in all_violations:
        if "error" not in v:
            violation_lines.add(f"{v['location']}: {v['function']}()")
    
    # Update baseline mode - must come BEFORE baseline comparison
    if args.update_baseline:
        if not args.baseline:
            print("❌ --baseline required with --update-baseline")
            return 1
        with open(args.baseline, "w") as f:
            for line in sorted(violation_lines):
                f.write(line + "\n")
        print(f"📝 Updated baseline: {args.baseline} ({len(violation_lines)} functions)")
        return 0
    
    # Check against baseline if provided
    if args.baseline and args.baseline.exists():
        with open(args.baseline) as f:
            baseline_lines = set(line.strip() for line in f if line.strip())
        
        new_violations = violation_lines - baseline_lines
        
        if not new_violations:
            print(f"✅ No NEW untyped functions (baseline: {len(baseline_lines)})")
            return 0
        
        print(f"\n❌ Found {len(new_violations)} NEW untyped functions:\n")
        for v in sorted(new_violations):
            print(v)
        print(f"\n💡 Add type hints or update baseline: {args.baseline}")
        return 1
    
    # No baseline - show all violations
    print(f"\n❌ Found {len(all_violations)} functions with missing type hints:\n")
    for v in all_violations:
        if "error" in v:
            print(f"  {v['location']}: {v['error']}")
        else:
            print(f"  {v['location']}: {v['function']}()")
            for issue in v["issues"]:
                print(f"    - {issue}")
    
    print("\n💡 Add type hints to fix these violations")
    return 1


if __name__ == "__main__":
    sys.exit(main())
