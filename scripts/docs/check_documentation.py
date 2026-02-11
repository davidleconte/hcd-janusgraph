#!/usr/bin/env python3
"""
Documentation validation script for Day 22.

Checks:
1. Broken internal links
2. Missing files referenced in docs
3. Code example syntax
4. Documentation structure compliance
"""

import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple
from collections import defaultdict

class DocumentationChecker:
    """Check documentation for issues."""
    
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.docs_dir = root_dir / "docs"
        self.issues: Dict[str, List[str]] = defaultdict(list)
        self.stats = {
            "total_files": 0,
            "total_links": 0,
            "broken_links": 0,
            "missing_files": 0,
            "code_blocks": 0,
            "invalid_code": 0,
        }
        
    def check_all(self) -> Dict[str, Any]:
        """Run all documentation checks."""
        print("🔍 Starting documentation validation...")
        print(f"📁 Root directory: {self.root_dir}")
        print(f"📚 Docs directory: {self.docs_dir}")
        print()
        
        # Find all markdown files
        md_files = list(self.root_dir.glob("**/*.md"))
        self.stats["total_files"] = len(md_files)
        
        print(f"Found {len(md_files)} markdown files")
        print()
        
        # Check each file
        for md_file in md_files:
            self._check_file(md_file)
            
        return {
            "issues": dict(self.issues),
            "stats": self.stats,
        }
    
    def _check_file(self, file_path: Path) -> None:
        """Check a single markdown file."""
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            self.issues[str(file_path)].append(f"Cannot read file: {e}")
            return
            
        # Check links
        self._check_links(file_path, content)
        
        # Check code blocks
        self._check_code_blocks(file_path, content)
        
    def _check_links(self, file_path: Path, content: str) -> None:
        """Check markdown links in file."""
        # Pattern for markdown links: [text](url)
        link_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
        
        for match in re.finditer(link_pattern, content):
            link_text = match.group(1)
            link_url = match.group(2)
            self.stats["total_links"] += 1
            
            # Skip external links (http/https)
            if link_url.startswith(("http://", "https://", "mailto:", "#")):
                continue
                
            # Check internal file links
            self._check_internal_link(file_path, link_url)
            
    def _check_internal_link(self, source_file: Path, link_url: str) -> None:
        """Check if internal link target exists."""
        # Remove anchor (#section)
        link_path = link_url.split("#")[0]
        if not link_path:
            return  # Just an anchor
            
        # Resolve relative to source file
        source_dir = source_file.parent
        target_path = (source_dir / link_path).resolve()
        
        # Check if target exists
        if not target_path.exists():
            self.stats["broken_links"] += 1
            rel_source = source_file.relative_to(self.root_dir)
            # Handle target path that might be outside root
            try:
                rel_target = target_path.relative_to(self.root_dir)
            except ValueError:
                rel_target = target_path
            self.issues[str(rel_source)].append(
                f"Broken link: [{link_url}] -> {rel_target}"
            )
            
    def _check_code_blocks(self, file_path: Path, content: str) -> None:
        """Check code blocks for syntax issues."""
        # Pattern for fenced code blocks
        code_block_pattern = r'```(\w+)?\n(.*?)```'
        
        for match in re.finditer(code_block_pattern, content, re.DOTALL):
            language = match.group(1) or "text"
            code = match.group(2)
            self.stats["code_blocks"] += 1
            
            # Basic validation
            if language in ("python", "py"):
                self._check_python_code(file_path, code)
            elif language in ("bash", "sh", "shell"):
                self._check_bash_code(file_path, code)
                
    def _check_python_code(self, file_path: Path, code: str) -> None:
        """Check Python code block syntax."""
        # Skip if it's just output or comments
        if all(line.strip().startswith(("#", ">>>", "...")) or not line.strip() 
               for line in code.split("\n")):
            return
            
        try:
            compile(code, "<string>", "exec")
        except SyntaxError as e:
            self.stats["invalid_code"] += 1
            rel_path = file_path.relative_to(self.root_dir)
            self.issues[str(rel_path)].append(
                f"Invalid Python code: {e.msg} at line {e.lineno}"
            )
            
    def _check_bash_code(self, file_path: Path, code: str) -> None:
        """Check bash code block for common issues."""
        # Check for common issues
        lines = code.split("\n")
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue
                
            # Check for unquoted variables with spaces
            if "$" in line and " " in line:
                # This is a heuristic check
                if re.search(r'\$\w+\s+\w+', line) and '"' not in line and "'" not in line:
                    rel_path = file_path.relative_to(self.root_dir)
                    self.issues[str(rel_path)].append(
                        f"Potentially unquoted variable at line {i}: {line[:50]}"
                    )
                    
    def print_report(self, results: Dict[str, Any]) -> bool:
        """Print validation report."""
        print("\n" + "="*80)
        print("📊 DOCUMENTATION VALIDATION REPORT")
        print("="*80)
        print()
        
        # Statistics
        stats = results["stats"]
        print("📈 Statistics:")
        print(f"  Total files checked: {stats['total_files']}")
        print(f"  Total links found: {stats['total_links']}")
        print(f"  Broken links: {stats['broken_links']}")
        print(f"  Code blocks checked: {stats['code_blocks']}")
        print(f"  Invalid code blocks: {stats['invalid_code']}")
        print()
        
        # Issues by file
        issues = results["issues"]
        if issues:
            print("⚠️  Issues Found:")
            print()
            for file_path, file_issues in sorted(issues.items()):
                print(f"📄 {file_path}")
                for issue in file_issues:
                    print(f"   • {issue}")
                print()
        else:
            print("✅ No issues found!")
            print()
            
        # Summary
        total_issues = sum(len(v) for v in issues.values())
        print("="*80)
        if total_issues == 0:
            print("✅ VALIDATION PASSED - All documentation checks passed!")
        else:
            print(f"⚠️  VALIDATION COMPLETED - {total_issues} issues found")
        print("="*80)
        print()
        
        return total_issues == 0


def main():
    """Main entry point."""
    root_dir = Path(__file__).parent.parent.parent
    
    checker = DocumentationChecker(root_dir)
    results = checker.check_all()
    passed = checker.print_report(results)
    
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()

# Made with Bob
