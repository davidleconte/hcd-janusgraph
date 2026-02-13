#!/usr/bin/env python3
"""
Naming Convention Linter

Validates naming conventions across multiple file types:
- Documentation files: kebab-case
- Python files: snake_case
- YAML files: kebab-case
- Configuration files: kebab-case

Features:
- Multi-file type support
- Compliance reporting
- Auto-fix capability
- Git-aware operations
- Backup and rollback
"""

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class NamingRule:
    """Naming convention rule definition."""
    
    name: str
    pattern: str
    description: str
    file_extensions: List[str]
    exceptions: List[str] = field(default_factory=list)
    custom: bool = False  # Flag for custom/project-specific rules
    
    def matches_extension(self, filepath: Path) -> bool:
        """Check if file extension matches this rule."""
        return filepath.suffix in self.file_extensions
    
    def is_exception(self, filepath: Path) -> bool:
        """Check if file is an exception to this rule."""
        filename = filepath.name
        return any(exc in filename for exc in self.exceptions)
    
    def validate(self, filepath: Path) -> bool:
        """Validate filename against pattern."""
        if self.is_exception(filepath):
            return True
        
        filename = filepath.stem  # Without extension
        return bool(re.match(self.pattern, filename))
    
    def suggest_fix(self, filepath: Path) -> Optional[str]:
        """Suggest corrected filename."""
        if self.validate(filepath):
            return None
        
        filename = filepath.stem
        
        # Apply transformation based on rule name
        if self.name == "kebab-case":
            # Convert to kebab-case
            fixed = filename.replace("_", "-")  # snake_case to kebab-case
            fixed = re.sub(r'([a-z])([A-Z])', r'\1-\2', fixed)  # PascalCase to kebab-case
            fixed = fixed.lower()
        elif self.name == "snake_case":
            # Convert to snake_case
            fixed = filename.replace("-", "_")  # kebab-case to snake_case
            fixed = re.sub(r'([a-z])([A-Z])', r'\1_\2', fixed)  # PascalCase to snake_case
            fixed = fixed.lower()
        elif self.name == "camelCase":
            # Convert to camelCase
            parts = re.split(r'[-_]', filename)
            if parts:
                fixed = parts[0].lower() + ''.join(word.capitalize() for word in parts[1:])
            else:
                fixed = filename
        else:
            return None
        
        return f"{fixed}{filepath.suffix}"


@dataclass
class ViolationReport:
    """Naming convention violation report."""
    
    filepath: Path
    rule: NamingRule
    current_name: str
    suggested_name: Optional[str]
    severity: str = "error"  # error, warning, info
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "filepath": str(self.filepath),
            "rule": self.rule.name,
            "current_name": self.current_name,
            "suggested_name": self.suggested_name,
            "severity": self.severity,
        }


class NamingConventionLinter:
    """Multi-file-type naming convention linter."""
    
    # Define naming rules
    RULES = [
        NamingRule(
            name="kebab-case",
            pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$",
            description="Lowercase with hyphens (kebab-case)",
            file_extensions=[".md", ".yml", ".yaml", ".json", ".toml", ".sh", ".css"],
            exceptions=[
                "README", "LICENSE", "CHANGELOG", "CONTRIBUTING",
                "CODE_OF_CONDUCT", "SECURITY", "AGENTS", "QUICKSTART", "FAQ"
            ]
        ),
        NamingRule(
            name="snake_case",
            pattern=r"^[a-z0-9]+(_[a-z0-9]+)*$",
            description="Lowercase with underscores (snake_case)",
            file_extensions=[".py"],
            exceptions=["__init__", "__main__", "__version__"]
        ),
        NamingRule(
            name="camelCase",
            pattern=r"^[a-z][a-zA-Z0-9]*$",
            description="Camel case starting with lowercase (camelCase)",
            file_extensions=[".ts", ".tsx", ".js", ".jsx"],
            exceptions=[]
        ),
    ]
    
    # Custom/project-specific rules (loaded from config if exists)
    CUSTOM_RULES: List[NamingRule] = []
    
    def __init__(
        self,
        root_dir: Path,
        exclude_dirs: Optional[List[str]] = None,
        auto_fix: bool = False,
        create_backup: bool = True,
        config_file: Optional[Path] = None
    ):
        """Initialize linter."""
        self.root_dir = root_dir
        default_exclude = [
            ".git", ".venv", "venv", "node_modules", "__pycache__",
            ".pytest_cache", ".mypy_cache", ".ruff_cache",
            "vendor", "archive"
        ]
        if exclude_dirs:
            self.exclude_dirs = list(set(default_exclude + exclude_dirs))
        else:
            self.exclude_dirs = default_exclude
        self.exclude_patterns: List[str] = []
        self.auto_fix = auto_fix
        self.create_backup = create_backup
        self.violations: List[ViolationReport] = []
        self.fixed_files: List[Tuple[Path, Path]] = []
        self.backup_dir: Optional[Path] = None
        
        # Load custom rules and config from file if provided
        self.custom_rules = self._load_custom_rules(config_file)
        self._load_config(config_file)
    
    def _load_custom_rules(self, config_file: Optional[Path]) -> List[NamingRule]:
        """Load custom naming rules from configuration file."""
        if not config_file:
            # Try default config locations
            default_configs = [
                self.root_dir / ".naming-rules.json",
                self.root_dir / ".naming-rules.yml",
                self.root_dir / "config" / "naming-rules.json",
            ]
            for config in default_configs:
                if config.exists():
                    config_file = config
                    break
        
        if not config_file or not config_file.exists():
            return []
        
        try:
            import yaml
            
            if config_file.suffix == ".json":
                import json
                with open(config_file) as f:
                    config_data = json.load(f)
            elif config_file.suffix in [".yml", ".yaml"]:
                with open(config_file) as f:
                    config_data = yaml.safe_load(f)
            else:
                return []
            
            custom_rules = []
            for rule_data in config_data.get("custom_rules", []):
                rule = NamingRule(
                    name=rule_data["name"],
                    pattern=rule_data["pattern"],
                    description=rule_data.get("description", ""),
                    file_extensions=rule_data["file_extensions"],
                    exceptions=rule_data.get("exceptions", []),
                    custom=True
                )
                custom_rules.append(rule)
            
            return custom_rules
        except Exception as e:
            print(f"⚠️  Warning: Failed to load custom rules from {config_file}: {e}")
            return []
    
    def _load_config(self, config_file: Optional[Path]) -> None:
        """Load configuration from file."""
        if not config_file:
            # Try default config locations
            default_configs = [
                self.root_dir / ".naming-rules.json",
                self.root_dir / ".naming-rules.yml",
                self.root_dir / "config" / "naming-rules.json",
            ]
            for config in default_configs:
                if config.exists():
                    config_file = config
                    break
        
        if not config_file or not config_file.exists():
            return
        
        try:
            import yaml
            
            if config_file.suffix == ".json":
                import json
                with open(config_file) as f:
                    config_data = json.load(f)
            elif config_file.suffix in [".yml", ".yaml"]:
                with open(config_file) as f:
                    config_data = yaml.safe_load(f)
            else:
                return
            
            # Load exclude_dirs from config
            if "exclude_dirs" in config_data:
                self.exclude_dirs.extend(config_data["exclude_dirs"])
            
            # Load exclude_patterns from config
            if "exclude_patterns" in config_data:
                self.exclude_patterns = config_data["exclude_patterns"]
            
            print(f"📋 Loaded configuration from {config_file.name}")
            if self.custom_rules:
                print(f"📋 Loaded {len(self.custom_rules)} custom rule(s)")
                for rule in self.custom_rules:
                    print(f"   - {rule.name}: {rule.description}")
        except Exception as e:
            print(f"⚠️  Warning: Failed to load config from {config_file}: {e}")
    
    def should_exclude(self, filepath: Path) -> bool:
        """Check if file should be excluded from linting."""
        # Check if any parent directory is in exclude list
        for parent in filepath.parents:
            if parent.name in self.exclude_dirs:
                return True
        
        # Check if filename matches any exclude pattern
        from fnmatch import fnmatch
        filename = filepath.name
        for pattern in self.exclude_patterns:
            if fnmatch(filename, pattern):
                return True
        
        return False
    
    def find_files(self) -> List[Path]:
        """Find all files to lint."""
        files = []
        
        # Get all extensions we care about (including custom rules)
        extensions = set()
        for rule in self.RULES:
            extensions.update(rule.file_extensions)
        for rule in self.custom_rules:
            extensions.update(rule.file_extensions)
        
        # Find files
        for ext in extensions:
            for filepath in self.root_dir.rglob(f"*{ext}"):
                if not self.should_exclude(filepath):
                    files.append(filepath)
        
        return sorted(files)
    
    def get_rule_for_file(self, filepath: Path) -> Optional[NamingRule]:
        """Get applicable naming rule for file."""
        # Check custom rules first (higher priority)
        for rule in self.custom_rules:
            if rule.matches_extension(filepath):
                return rule
        
        # Then check standard rules
        for rule in self.RULES:
            if rule.matches_extension(filepath):
                return rule
        return None
    
    def lint_file(self, filepath: Path) -> Optional[ViolationReport]:
        """Lint a single file."""
        rule = self.get_rule_for_file(filepath)
        if not rule:
            return None
        
        if not rule.validate(filepath):
            suggested = rule.suggest_fix(filepath)
            return ViolationReport(
                filepath=filepath,
                rule=rule,
                current_name=filepath.name,
                suggested_name=suggested,
                severity="error"
            )
        
        return None
    
    def lint_all(self) -> List[ViolationReport]:
        """Lint all files."""
        files = self.find_files()
        self.violations = []
        
        for filepath in files:
            violation = self.lint_file(filepath)
            if violation:
                self.violations.append(violation)
        
        return self.violations
    
    def create_backup_dir(self) -> Path:
        """Create backup directory."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.root_dir / ".naming-linter-backups" / timestamp
        backup_dir.mkdir(parents=True, exist_ok=True)
        return backup_dir
    
    def backup_file(self, filepath: Path) -> None:
        """Backup file before modification."""
        if not self.backup_dir:
            self.backup_dir = self.create_backup_dir()
        
        # Create relative path in backup dir
        rel_path = filepath.relative_to(self.root_dir)
        backup_path = self.backup_dir / rel_path
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy file
        import shutil
        shutil.copy2(filepath, backup_path)
    
    def fix_file(self, violation: ViolationReport) -> bool:
        """Fix a single file naming violation."""
        if not violation.suggested_name:
            return False
        
        old_path = violation.filepath
        new_path = old_path.parent / violation.suggested_name
        
        # Check if target already exists
        if new_path.exists():
            print(f"⚠️  Cannot fix {old_path}: {new_path} already exists")
            return False
        
        # Backup if requested
        if self.create_backup:
            self.backup_file(old_path)
        
        # Try git mv first (preserves history)
        try:
            result = subprocess.run(
                ["git", "mv", str(old_path), str(new_path)],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                self.fixed_files.append((old_path, new_path))
                return True
        except FileNotFoundError:
            pass  # Git not available
        
        # Fall back to regular rename
        try:
            old_path.rename(new_path)
            self.fixed_files.append((old_path, new_path))
            return True
        except Exception as e:
            print(f"❌ Failed to rename {old_path}: {e}")
            return False
    
    def fix_all(self) -> int:
        """Fix all violations."""
        if not self.violations:
            return 0
        
        fixed_count = 0
        for violation in self.violations:
            if self.fix_file(violation):
                fixed_count += 1
        
        return fixed_count
    
    def generate_report(self, output_format: str = "text") -> str:
        """Generate compliance report."""
        if output_format == "json":
            return self._generate_json_report()
        elif output_format == "markdown":
            return self._generate_markdown_report()
        else:
            return self._generate_text_report()
    
    def _generate_text_report(self) -> str:
        """Generate text report."""
        lines = []
        lines.append("=" * 80)
        lines.append("NAMING CONVENTION LINTER REPORT")
        lines.append("=" * 80)
        lines.append(f"Timestamp: {datetime.now().isoformat()}")
        lines.append(f"Root Directory: {self.root_dir}")
        lines.append("")
        
        # Summary
        total_files = len(self.find_files())
        violation_count = len(self.violations)
        compliance_rate = ((total_files - violation_count) / total_files * 100) if total_files > 0 else 100
        
        lines.append("SUMMARY")
        lines.append("-" * 80)
        lines.append(f"Total Files Scanned: {total_files}")
        lines.append(f"Violations Found: {violation_count}")
        lines.append(f"Compliance Rate: {compliance_rate:.1f}%")
        lines.append("")
        
        # Violations by rule
        if self.violations:
            violations_by_rule: Dict[str, List[ViolationReport]] = {}
            for v in self.violations:
                rule_name = v.rule.name
                if rule_name not in violations_by_rule:
                    violations_by_rule[rule_name] = []
                violations_by_rule[rule_name].append(v)
            
            lines.append("VIOLATIONS BY RULE")
            lines.append("-" * 80)
            for rule_name, violations in violations_by_rule.items():
                lines.append(f"\n{rule_name}: {len(violations)} violations")
                for v in violations[:10]:  # Show first 10
                    lines.append(f"  ❌ {v.filepath}")
                    if v.suggested_name:
                        lines.append(f"     → Suggested: {v.suggested_name}")
                if len(violations) > 10:
                    lines.append(f"  ... and {len(violations) - 10} more")
        
        # Fixed files
        if self.fixed_files:
            lines.append("")
            lines.append("FIXED FILES")
            lines.append("-" * 80)
            for old_path, new_path in self.fixed_files:
                lines.append(f"✅ {old_path.name} → {new_path.name}")
        
        lines.append("")
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    def _generate_json_report(self) -> str:
        """Generate JSON report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "root_directory": str(self.root_dir),
            "summary": {
                "total_files": len(self.find_files()),
                "violations": len(self.violations),
                "fixed": len(self.fixed_files),
            },
            "violations": [v.to_dict() for v in self.violations],
            "fixed_files": [
                {"old": str(old), "new": str(new)}
                for old, new in self.fixed_files
            ],
        }
        return json.dumps(report, indent=2)
    
    def _generate_markdown_report(self) -> str:
        """Generate Markdown report."""
        lines = []
        lines.append("# Naming Convention Linter Report")
        lines.append("")
        lines.append(f"**Timestamp:** {datetime.now().isoformat()}")
        lines.append(f"**Root Directory:** `{self.root_dir}`")
        lines.append("")
        
        # Summary
        total_files = len(self.find_files())
        violation_count = len(self.violations)
        compliance_rate = ((total_files - violation_count) / total_files * 100) if total_files > 0 else 100
        
        lines.append("## Summary")
        lines.append("")
        lines.append(f"- **Total Files Scanned:** {total_files}")
        lines.append(f"- **Violations Found:** {violation_count}")
        lines.append(f"- **Compliance Rate:** {compliance_rate:.1f}%")
        lines.append("")
        
        # Violations
        if self.violations:
            lines.append("## Violations")
            lines.append("")
            lines.append("| File | Rule | Suggested Fix |")
            lines.append("|------|------|---------------|")
            for v in self.violations:
                suggested = v.suggested_name or "N/A"
                lines.append(f"| `{v.filepath}` | {v.rule.name} | `{suggested}` |")
            lines.append("")
        
        # Fixed files
        if self.fixed_files:
            lines.append("## Fixed Files")
            lines.append("")
            lines.append("| Original | New Name |")
            lines.append("|----------|----------|")
            for old_path, new_path in self.fixed_files:
                lines.append(f"| `{old_path.name}` | `{new_path.name}` |")
            lines.append("")
        
        return "\n".join(lines)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Naming Convention Linter - Validate and fix naming conventions"
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Root directory to scan (default: current directory)"
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Automatically fix violations"
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Don't create backups when fixing"
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "markdown"],
        default="text",
        help="Report format (default: text)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file for report (default: stdout)"
    )
    parser.add_argument(
        "--exclude",
        nargs="+",
        help="Additional directories to exclude"
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to custom rules configuration file (JSON or YAML)"
    )
    
    args = parser.parse_args()
    
    # Create linter
    linter = NamingConventionLinter(
        root_dir=args.root,
        exclude_dirs=args.exclude,
        auto_fix=args.fix,
        create_backup=not args.no_backup,
        config_file=args.config
    )
    
    # Show loaded custom rules
    if linter.custom_rules:
        print(f"📋 Loaded {len(linter.custom_rules)} custom rule(s)")
        for rule in linter.custom_rules:
            print(f"   - {rule.name}: {rule.description}")
    
    # Run linting
    print(f"🔍 Scanning {args.root}...")
    violations = linter.lint_all()
    
    if not violations:
        print("✅ No naming convention violations found!")
        return 0
    
    print(f"❌ Found {len(violations)} naming convention violations")
    
    # Fix if requested
    if args.fix:
        print(f"\n🔧 Fixing violations...")
        fixed_count = linter.fix_all()
        print(f"✅ Fixed {fixed_count} files")
        if linter.backup_dir:
            print(f"📦 Backups saved to: {linter.backup_dir}")
    
    # Generate report
    report = linter.generate_report(output_format=args.format)
    
    if args.output:
        args.output.write_text(report)
        print(f"\n📄 Report saved to: {args.output}")
    else:
        print("\n" + report)
    
    # Exit with error if violations found and not fixed
    if violations and not args.fix:
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
