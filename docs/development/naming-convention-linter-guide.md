# Naming Convention Linter Guide

**Version:** 1.0  
**Last Updated:** 2026-02-12  
**Status:** Active

This guide explains how to use the naming convention linter to maintain consistent file naming across the project.

---

## Table of Contents

1. [Overview](#overview)
2. [Naming Rules](#naming-rules)
3. [Usage](#usage)
4. [CI/CD Integration](#cicd-integration)
5. [Compliance Reporting](#compliance-reporting)
6. [Troubleshooting](#troubleshooting)

---

## Overview

The naming convention linter validates and enforces consistent file naming across multiple file types:

- **Documentation files** (`.md`): kebab-case
- **Python files** (`.py`): snake_case
- **YAML files** (`.yml`, `.yaml`): kebab-case
- **JSON files** (`.json`): kebab-case
- **TOML files** (`.toml`): kebab-case

### Features

- ✅ Multi-file-type support
- ✅ Automatic violation detection
- ✅ Auto-fix capability
- ✅ Git-aware operations (preserves history)
- ✅ Backup and rollback
- ✅ Compliance reporting (text, JSON, Markdown)
- ✅ Pre-commit hook integration
- ✅ CI/CD pipeline integration

---

## Naming Rules

### Documentation Files (`.md`)

**Convention:** kebab-case (lowercase with hyphens)

```bash
✅ CORRECT
user-guide.md
api-reference-v2.md
phase-8-complete.md
getting-started.md

❌ WRONG
User_Guide.md          # UPPERCASE with underscores
API_REFERENCE_V2.md    # All UPPERCASE
ApiReferenceV2.md      # PascalCase
user_guide.md          # snake_case
UserGuide.md           # PascalCase
```

**Exceptions:**
- `README.md`, `LICENSE`, `CHANGELOG.md`
- `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`
- `SECURITY.md`, `AGENTS.md`
- `QUICKSTART.md`, `FAQ.md`

### Python Files (`.py`)

**Convention:** snake_case (lowercase with underscores)

```bash
✅ CORRECT
user_service.py
api_client.py
data_generator.py
__init__.py

❌ WRONG
UserService.py         # PascalCase
user-service.py        # kebab-case
userService.py         # camelCase
```

**Exceptions:**
- `__init__.py`, `__main__.py`, `__version__.py`

### YAML Files (`.yml`, `.yaml`)

**Convention:** kebab-case (lowercase with hyphens)

```bash
✅ CORRECT
docker-compose.yml
api-config.yaml
deployment-config.yml

❌ WRONG
docker_compose.yml     # snake_case
DockerCompose.yml      # PascalCase
```

### JSON Files (`.json`)

**Convention:** kebab-case (lowercase with hyphens)

```bash
✅ CORRECT
api-config.json
package-lock.json
tsconfig.json

❌ WRONG
api_config.json        # snake_case
ApiConfig.json         # PascalCase
```

### TOML Files (`.toml`)

**Convention:** kebab-case (lowercase with hyphens)

```bash
✅ CORRECT
pyproject.toml
poetry.toml

❌ WRONG
pyproject_toml         # snake_case (no extension)
PyProject.toml         # PascalCase
```

---

## Usage

### Command Line

**Basic validation (dry-run):**

```bash
# Scan current directory
python3 scripts/validation/naming-convention-linter.py --root .

# Scan specific directory
python3 scripts/validation/naming-convention-linter.py --root docs/
```

**Auto-fix violations:**

```bash
# Fix violations with backup
python3 scripts/validation/naming-convention-linter.py --root . --fix

# Fix without backup (not recommended)
python3 scripts/validation/naming-convention-linter.py --root . --fix --no-backup
```

**Generate reports:**

```bash
# Text report (default)
python3 scripts/validation/naming-convention-linter.py --root . --format text

# JSON report
python3 scripts/validation/naming-convention-linter.py --root . --format json --output report.json

# Markdown report
python3 scripts/validation/naming-convention-linter.py --root . --format markdown --output report.md
```

**Exclude directories:**

```bash
python3 scripts/validation/naming-convention-linter.py --root . --exclude vendor archive temp
```

### Pre-commit Hook

The linter runs automatically before each commit:

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run manually on all files
pre-commit run naming-convention-linter --all-files

# Run on staged files only
pre-commit run naming-convention-linter
```

### Python API

```python
from pathlib import Path
from scripts.validation.naming_convention_linter import NamingConventionLinter

# Create linter instance
linter = NamingConventionLinter(
    root_dir=Path("."),
    exclude_dirs=["vendor", "archive"],
    auto_fix=False,
    create_backup=True
)

# Run linting
violations = linter.lint_all()

# Print violations
for violation in violations:
    print(f"❌ {violation.filepath}")
    print(f"   Rule: {violation.rule.name}")
    print(f"   Suggested: {violation.suggested_name}")

# Auto-fix violations
if violations:
    fixed_count = linter.fix_all()
    print(f"✅ Fixed {fixed_count} files")

# Generate report
report = linter.generate_report(output_format="markdown")
print(report)
```

---

## CI/CD Integration

### GitHub Actions Workflow

The linter runs automatically on:
- Pull requests (all file changes)
- Pushes to `main` or `develop` branches
- Manual workflow dispatch

**Workflow file:** `.github/workflows/naming-convention-linter.yml`

**Features:**
- Automatic violation detection
- PR comments with detailed reports
- Auto-fix capability (optional)
- Compliance reporting
- Artifact uploads (reports retained for 90 days)

### Workflow Triggers

**Automatic (on PR):**
```yaml
on:
  pull_request:
    paths:
      - '**/*.md'
      - '**/*.py'
      - '**/*.yml'
      - '**/*.yaml'
      - '**/*.json'
      - '**/*.toml'
```

**Manual (with auto-fix option):**
```bash
# Via GitHub UI: Actions → Naming Convention Linter → Run workflow
# Select "Auto-fix violations: true"
```

### Auto-fix Behavior

When violations are found in a PR:

1. **Validation job fails** - Shows violations in PR
2. **Auto-fix job runs** (if enabled) - Applies fixes automatically
3. **Commits fixes** - Creates commit with fixed files
4. **Comments on PR** - Notifies about auto-fix

**Enable auto-fix:**
- Set `fix: 'true'` in workflow dispatch
- Or uncomment auto-fix job in workflow file

---

## Compliance Reporting

### Report Formats

**Text Report:**
```bash
python3 scripts/validation/naming-convention-linter.py --root . --format text
```

Output:
```
================================================================================
NAMING CONVENTION LINTER REPORT
================================================================================
Timestamp: 2026-02-12T11:00:00
Root Directory: /path/to/project

SUMMARY
--------------------------------------------------------------------------------
Total Files Scanned: 1250
Violations Found: 15
Compliance Rate: 98.8%

VIOLATIONS BY RULE
--------------------------------------------------------------------------------
kebab-case: 10 violations
  ❌ docs/User_Guide.md
     → Suggested: user-guide.md
  ...

snake_case: 5 violations
  ❌ src/UserService.py
     → Suggested: user_service.py
  ...
```

**JSON Report:**
```bash
python3 scripts/validation/naming-convention-linter.py --root . --format json --output report.json
```

Output:
```json
{
  "timestamp": "2026-02-12T11:00:00",
  "root_directory": "/path/to/project",
  "summary": {
    "total_files": 1250,
    "violations": 15,
    "fixed": 0
  },
  "violations": [
    {
      "filepath": "docs/User_Guide.md",
      "rule": "kebab-case",
      "current_name": "User_Guide.md",
      "suggested_name": "user-guide.md",
      "severity": "error"
    }
  ]
}
```

**Markdown Report:**
```bash
python3 scripts/validation/naming-convention-linter.py --root . --format markdown --output report.md
```

Output:
```markdown
# Naming Convention Linter Report

**Timestamp:** 2026-02-12T11:00:00
**Root Directory:** `/path/to/project`

## Summary

- **Total Files Scanned:** 1250
- **Violations Found:** 15
- **Compliance Rate:** 98.8%

## Violations

| File | Rule | Suggested Fix |
|------|------|---------------|
| `docs/User_Guide.md` | kebab-case | `user-guide.md` |
```

### Compliance Metrics

**Compliance Rate Calculation:**
```
Compliance Rate = ((Total Files - Violations) / Total Files) × 100
```

**Compliance Levels:**
- 🟢 **Excellent:** ≥95% (Green badge)
- 🟡 **Good:** 85-94% (Yellow badge)
- 🔴 **Needs Improvement:** <85% (Red badge)

---

## Troubleshooting

### Common Issues

**Issue 1: Linter not found**

```bash
❌ python3: can't open file 'scripts/validation/naming-convention-linter.py'
```

**Solution:**
```bash
# Ensure you're in project root
cd /path/to/project

# Make script executable
chmod +x scripts/validation/naming-convention-linter.py
```

**Issue 2: Git mv fails**

```bash
⚠️  Cannot fix docs/old-name.md: git mv failed
```

**Solution:**
```bash
# File not tracked by git - will use regular rename
# Or add file to git first:
git add docs/old-name.md
```

**Issue 3: Target file exists**

```bash
⚠️  Cannot fix docs/Old_Name.md: docs/old-name.md already exists
```

**Solution:**
```bash
# Manually resolve conflict
# Option 1: Delete duplicate
rm docs/old-name.md

# Option 2: Rename manually
git mv docs/Old_Name.md docs/old-name-v2.md
```

**Issue 4: Pre-commit hook fails**

```bash
❌ naming-convention-linter...Failed
```

**Solution:**
```bash
# Run linter to see violations
python3 scripts/validation/naming-convention-linter.py --root .

# Fix violations
python3 scripts/validation/naming-convention-linter.py --root . --fix

# Retry commit
git commit -m "your message"
```

### Rollback Changes

If auto-fix creates issues:

```bash
# Find backup directory
ls -la .naming-linter-backups/

# Restore from backup
cp -r .naming-linter-backups/20260212_110000/* .

# Or use git to revert
git reset --hard HEAD
```

### Exclude Files

To exclude specific files or directories:

```bash
# Via command line
python3 scripts/validation/naming-convention-linter.py --root . --exclude vendor archive temp

# Via environment variable
export NAMING_LINTER_EXCLUDE="vendor,archive,temp"
python3 scripts/validation/naming-convention-linter.py --root .
```

---

## Best Practices

1. **Run before committing:**
   ```bash
   python3 scripts/validation/naming-convention-linter.py --root .
   ```

2. **Use auto-fix with caution:**
   - Always review changes before committing
   - Backups are created by default
   - Test after auto-fix

3. **Check compliance regularly:**
   ```bash
   # Weekly compliance check
   python3 scripts/validation/naming-convention-linter.py --root . --format markdown --output compliance-$(date +%Y%m%d).md
   ```

4. **Update exceptions as needed:**
   - Edit `NamingRule.exceptions` in linter script
   - Document exceptions in this guide

5. **Monitor CI/CD reports:**
   - Review PR comments
   - Check artifact reports
   - Track compliance trends

---

## References

- **Linter Script:** `scripts/validation/naming-convention-linter.py`
- **CI/CD Workflow:** `.github/workflows/naming-convention-linter.yml`
- **Pre-commit Config:** `.pre-commit-config.yaml`
- **Documentation Standards:** `docs/documentation-standards.md`

---

**Last Updated:** 2026-02-12  
**Maintained By:** DevOps Team  
**Review Frequency:** Quarterly  
**Next Review:** 2026-05-12