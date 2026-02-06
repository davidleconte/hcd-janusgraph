#!/usr/bin/env python3
"""
Documentation Coverage Analyzer

Analyzes documentation coverage for Python modules by checking:
1. Module-level docstrings
2. Class docstrings
3. Function/method docstrings
4. Public API documentation

Usage:
    python scripts/docs/doc_coverage.py --report
    python scripts/docs/doc_coverage.py --json output.json
    python scripts/docs/doc_coverage.py --threshold 80
"""

import argparse
import ast
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class DocCoverageResult:
    """Result of documentation coverage analysis for a single file."""
    file_path: str
    total_items: int = 0
    documented_items: int = 0
    missing_docs: List[str] = field(default_factory=list)
    
    @property
    def coverage_percent(self) -> float:
        if self.total_items == 0:
            return 100.0
        return (self.documented_items / self.total_items) * 100


class DocCoverageAnalyzer(ast.NodeVisitor):
    """AST visitor that analyzes documentation coverage."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.result = DocCoverageResult(file_path=file_path)
        self.current_class: Optional[str] = None
    
    def _has_docstring(self, node: ast.AST) -> bool:
        """Check if a node has a docstring."""
        if not hasattr(node, 'body') or not node.body:
            return False
        first = node.body[0]
        return (
            isinstance(first, ast.Expr) and
            isinstance(first.value, (ast.Str, ast.Constant))
        )
    
    def _is_public(self, name: str) -> bool:
        """Check if a name represents a public API."""
        return not name.startswith('_')
    
    def visit_Module(self, node: ast.Module) -> None:
        """Check module-level docstring."""
        self.result.total_items += 1
        if self._has_docstring(node):
            self.result.documented_items += 1
        else:
            self.result.missing_docs.append(f"Module: {self.file_path}")
        self.generic_visit(node)
    
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Check class docstring."""
        if self._is_public(node.name):
            self.result.total_items += 1
            if self._has_docstring(node):
                self.result.documented_items += 1
            else:
                self.result.missing_docs.append(f"Class: {node.name}")
        
        # Track current class for method analysis
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Check function/method docstring."""
        self._check_function(node)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Check async function docstring."""
        self._check_function(node)
    
    def _check_function(self, node) -> None:
        """Check function or method docstring."""
        if self._is_public(node.name):
            self.result.total_items += 1
            if self._has_docstring(node):
                self.result.documented_items += 1
            else:
                if self.current_class:
                    self.result.missing_docs.append(
                        f"Method: {self.current_class}.{node.name}"
                    )
                else:
                    self.result.missing_docs.append(f"Function: {node.name}")
        self.generic_visit(node)


def analyze_file(file_path: Path) -> Optional[DocCoverageResult]:
    """Analyze a single Python file for documentation coverage."""
    try:
        source = file_path.read_text(encoding='utf-8')
        tree = ast.parse(source)
        analyzer = DocCoverageAnalyzer(str(file_path))
        analyzer.visit(tree)
        return analyzer.result
    except SyntaxError as e:
        print(f"Syntax error in {file_path}: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error analyzing {file_path}: {e}", file=sys.stderr)
        return None


def analyze_directory(
    directory: Path,
    exclude_patterns: List[str] = None
) -> List[DocCoverageResult]:
    """Analyze all Python files in a directory."""
    exclude_patterns = exclude_patterns or [
        '__pycache__', '.git', 'node_modules', 'venv', '.venv',
        'hcd-1.2.3', 'archive', 'tests'
    ]
    
    results = []
    for py_file in directory.rglob('*.py'):
        # Skip excluded patterns
        if any(pattern in str(py_file) for pattern in exclude_patterns):
            continue
        
        result = analyze_file(py_file)
        if result:
            results.append(result)
    
    return results


def generate_report(results: List[DocCoverageResult]) -> Dict:
    """Generate a coverage report from results."""
    total_items = sum(r.total_items for r in results)
    documented_items = sum(r.documented_items for r in results)
    
    overall_coverage = (documented_items / total_items * 100) if total_items > 0 else 100.0
    
    # Find files with lowest coverage
    sorted_results = sorted(results, key=lambda r: r.coverage_percent)
    lowest_coverage = [
        {
            'file': r.file_path,
            'coverage': round(r.coverage_percent, 1),
            'missing': len(r.missing_docs)
        }
        for r in sorted_results[:10]
    ]
    
    # Collect all missing docs
    all_missing = []
    for r in results:
        for item in r.missing_docs[:5]:  # Limit per file
            all_missing.append({
                'file': r.file_path,
                'item': item
            })
    
    return {
        'summary': {
            'total_files': len(results),
            'total_items': total_items,
            'documented_items': documented_items,
            'overall_coverage': round(overall_coverage, 1)
        },
        'lowest_coverage_files': lowest_coverage,
        'sample_missing_docs': all_missing[:20]
    }


def print_report(report: Dict) -> None:
    """Print a human-readable coverage report."""
    summary = report['summary']
    
    print("\n" + "=" * 60)
    print("DOCUMENTATION COVERAGE REPORT")
    print("=" * 60)
    
    print(f"\n📊 Summary:")
    print(f"   Files analyzed: {summary['total_files']}")
    print(f"   Total items: {summary['total_items']}")
    print(f"   Documented: {summary['documented_items']}")
    print(f"   Coverage: {summary['overall_coverage']}%")
    
    # Coverage bar
    filled = int(summary['overall_coverage'] / 5)
    bar = '█' * filled + '░' * (20 - filled)
    print(f"\n   [{bar}] {summary['overall_coverage']}%")
    
    print(f"\n📉 Lowest Coverage Files:")
    for item in report['lowest_coverage_files']:
        print(f"   {item['coverage']:5.1f}% | {item['file']}")
    
    if report['sample_missing_docs']:
        print(f"\n📝 Sample Missing Documentation:")
        for item in report['sample_missing_docs'][:10]:
            print(f"   - {item['item']}")
            print(f"     in {item['file']}")
    
    print("\n" + "=" * 60)
    
    # Return exit code based on coverage
    return 0 if summary['overall_coverage'] >= 80 else 1


def main():
    parser = argparse.ArgumentParser(description='Analyze documentation coverage')
    parser.add_argument('--report', action='store_true', help='Print coverage report')
    parser.add_argument('--json', type=str, help='Output JSON report to file')
    parser.add_argument('--threshold', type=float, default=80.0,
                       help='Minimum coverage threshold (default: 80)')
    parser.add_argument('--path', type=str, default='.',
                       help='Path to analyze (default: current directory)')
    
    args = parser.parse_args()
    
    # Find project directories to analyze
    base_path = Path(args.path)
    source_dirs = [
        base_path / 'src' / 'python',
        base_path / 'banking',
    ]
    
    all_results = []
    for source_dir in source_dirs:
        if source_dir.exists():
            results = analyze_directory(source_dir)
            all_results.extend(results)
    
    if not all_results:
        print("No Python files found to analyze", file=sys.stderr)
        sys.exit(1)
    
    report = generate_report(all_results)
    
    if args.json:
        with open(args.json, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Report written to {args.json}")
    
    if args.report or not args.json:
        exit_code = print_report(report)
        
        # Check threshold
        if report['summary']['overall_coverage'] < args.threshold:
            print(f"\n⚠️  Coverage {report['summary']['overall_coverage']}% "
                  f"is below threshold {args.threshold}%")
            sys.exit(1)
        else:
            print(f"\n✅ Coverage meets threshold ({args.threshold}%)")
            sys.exit(exit_code)


if __name__ == '__main__':
    main()
