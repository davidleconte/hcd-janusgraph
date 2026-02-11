#!/usr/bin/env python3
"""
Analyze documentation issues and categorize them by severity and type.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Set
from collections import defaultdict

class IssueAnalyzer:
    """Analyze and categorize documentation issues."""
    
    def __init__(self, report_file: Path):
        self.report_file = report_file
        self.issues_by_type: Dict[str, List[str]] = defaultdict(list)
        self.issues_by_severity: Dict[str, List[str]] = defaultdict(list)
        self.files_with_issues: Set[str] = set()
        
    def analyze(self) -> Dict[str, Any]:
        """Analyze the validation report."""
        content = self.report_file.read_text()
        
        # Parse issues from report
        current_file = None
        for line in content.split("\n"):
            if line.startswith("📄 "):
                current_file = line[3:].strip()
                self.files_with_issues.add(current_file)
            elif line.startswith("   • "):
                issue = line[5:].strip()
                if current_file:
                    self._categorize_issue(current_file, issue)
                    
        return self._generate_report()
        
    def _categorize_issue(self, file_path: str, issue: str) -> None:
        """Categorize an issue by type and severity."""
        # Determine issue type
        if "Broken link:" in issue:
            issue_type = "broken_link"
            severity = self._assess_link_severity(file_path, issue)
        elif "Invalid Python code:" in issue:
            issue_type = "invalid_code"
            severity = self._assess_code_severity(file_path, issue)
        elif "Potentially unquoted variable" in issue:
            issue_type = "bash_warning"
            severity = "low"
        else:
            issue_type = "other"
            severity = "low"
            
        self.issues_by_type[issue_type].append(f"{file_path}: {issue}")
        self.issues_by_severity[severity].append(f"{file_path}: {issue}")
        
    def _assess_link_severity(self, file_path: str, issue: str) -> str:
        """Assess severity of broken link."""
        # Critical: Main documentation files
        if any(x in file_path for x in ["README.md", "QUICKSTART.md", "AGENTS.md"]):
            return "critical"
            
        # High: User-facing guides
        if any(x in file_path for x in ["guides/", "banking/", "operations/"]):
            return "high"
            
        # Medium: Implementation docs
        if "implementation/" in file_path:
            return "medium"
            
        # Low: Archive, vendor, .venv
        if any(x in file_path for x in ["archive/", "vendor/", ".venv/", ".bob/"]):
            return "low"
            
        return "medium"
        
    def _assess_code_severity(self, file_path: str, issue: str) -> str:
        """Assess severity of invalid code."""
        # Low: Most code examples are illustrative
        # Critical only if it's in actual code files (not docs)
        if file_path.endswith(".py"):
            return "critical"
            
        # Low: Documentation code examples
        # Many are pseudo-code or partial examples
        if any(x in issue for x in ["unexpected indent", "invalid character"]):
            return "low"
            
        return "low"
        
    def _generate_report(self) -> Dict[str, Any]:
        """Generate analysis report."""
        return {
            "summary": {
                "total_files_with_issues": len(self.files_with_issues),
                "total_issues": sum(len(v) for v in self.issues_by_type.values()),
                "by_type": {k: len(v) for k, v in self.issues_by_type.items()},
                "by_severity": {k: len(v) for k, v in self.issues_by_severity.items()},
            },
            "issues_by_type": dict(self.issues_by_type),
            "issues_by_severity": dict(self.issues_by_severity),
        }
        
    def print_report(self, results: Dict[str, Any]) -> None:
        """Print analysis report."""
        print("\n" + "="*80)
        print("📊 DOCUMENTATION ISSUES ANALYSIS")
        print("="*80)
        print()
        
        summary = results["summary"]
        
        print("📈 Summary:")
        print(f"  Files with issues: {summary['total_files_with_issues']}")
        print(f"  Total issues: {summary['total_issues']}")
        print()
        
        print("📋 By Type:")
        for issue_type, count in sorted(summary["by_type"].items(), key=lambda x: -x[1]):
            print(f"  {issue_type:20s}: {count:4d}")
        print()
        
        print("⚠️  By Severity:")
        severity_order = ["critical", "high", "medium", "low"]
        for severity in severity_order:
            count = summary["by_severity"].get(severity, 0)
            if count > 0:
                emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}[severity]
                print(f"  {emoji} {severity.capitalize():10s}: {count:4d}")
        print()
        
        # Show critical issues
        critical = results["issues_by_severity"].get("critical", [])
        if critical:
            print("🔴 CRITICAL Issues (Must Fix):")
            for issue in critical[:10]:  # Show first 10
                print(f"  • {issue}")
            if len(critical) > 10:
                print(f"  ... and {len(critical) - 10} more")
            print()
            
        # Show high priority issues
        high = results["issues_by_severity"].get("high", [])
        if high:
            print("🟠 HIGH Priority Issues (Should Fix):")
            for issue in high[:10]:  # Show first 10
                print(f"  • {issue}")
            if len(high) > 10:
                print(f"  ... and {len(high) - 10} more")
            print()
            
        print("="*80)
        print()


def main():
    """Main entry point."""
    root_dir = Path(__file__).parent.parent.parent
    report_file = root_dir / "docs_validation_report.txt"
    
    if not report_file.exists():
        print(f"❌ Report file not found: {report_file}")
        return 1
        
    analyzer = IssueAnalyzer(report_file)
    results = analyzer.analyze()
    analyzer.print_report(results)
    
    # Save detailed results
    output_file = root_dir / "docs_issues_analysis.json"
    output_file.write_text(json.dumps(results, indent=2))
    print(f"💾 Detailed analysis saved to: {output_file}")
    print()
    
    return 0


if __name__ == "__main__":
    exit(main())

# Made with Bob
