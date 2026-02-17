# Documentation Standards

**Version:** 1.0
**Last Updated:** 2026-02-07
**Status:** Active

This document defines the standards and best practices for all project documentation.

---

## Table of Contents

1. [File Naming Conventions](#file-naming-conventions)
2. [Directory Structure](#directory-structure)
3. [Document Structure](#document-structure)
4. [Writing Style](#writing-style)
5. [Markdown Formatting](#markdown-formatting)
6. [Code Examples](#code-examples)
7. [Links and References](#links-and-references)
8. [Maintenance](#maintenance)

---

## File Naming Conventions

### General Rules

**Use kebab-case for all documentation files:**

```bash
# ✅ CORRECT - Use kebab-case (lowercase with hyphens)
docs/new-feature-guide.md
docs/api-reference-v2.md
docs/user-authentication-guide.md
docs/phase-8-complete.md

# ❌ WRONG - Do not use UPPERCASE, PascalCase, or snake_case
docs/New_Feature_Guide.md      # UPPERCASE with underscores
docs/API_REFERENCE_V2.md        # All UPPERCASE
docs/ApiReferenceV2.md          # PascalCase
docs/user_guide.md              # snake_case
docs/UserGuide.md               # PascalCase
```

**Quick Reference:**

- ✅ `user-guide.md` - kebab-case (correct)
- ✅ `api-reference.md` - kebab-case (correct)
- ✅ `phase-8-complete.md` - kebab-case (correct)
- ❌ `USER_GUIDE.md` - UPPERCASE (wrong)
- ❌ `ApiReference.md` - PascalCase (wrong)
- ❌ `user_guide.md` - snake_case (wrong)

**Exceptions:**

- `README.md` - Always uppercase (standard convention)
- `LICENSE` - Always uppercase (standard convention)
- `CHANGELOG.md` - Uppercase acceptable for root-level files
- `CONTRIBUTING.md` - Uppercase acceptable for root-level files
- `CODE_OF_CONDUCT.md` - Uppercase acceptable for root-level files
- `SECURITY.md` - Uppercase acceptable for root-level files

### Specific Naming Patterns

**Guides:**

```
user-guide.md
developer-guide.md
deployment-guide.md
troubleshooting-guide.md
```

**References:**

```
api-reference.md
configuration-reference.md
command-reference.md
```

**Plans:**

```
implementation-plan.md
remediation-plan.md
migration-plan.md
```

**Reports:**

```
audit-report.md
performance-report.md
security-assessment.md
```

**Phase Documentation:**

```
phase-1-complete.md
phase-2-week-3-status.md
phase-8-implementation-guide.md
```

---

## Directory Structure

### Standard Directory Layout

```
docs/
├── README.md                   # Documentation overview
├── index.md                    # Central navigation
├── documentation-standards.md  # This file
├── [core-docs].md             # Core documentation files
├── api/                        # API documentation
│   └── README.md
├── architecture/               # Architecture decisions
│   └── README.md
├── banking/                    # Domain-specific docs
│   ├── README.md
│   ├── guides/
│   ├── architecture/
│   ├── implementation/
│   ├── planning/
│   └── setup/
├── compliance/                 # Compliance documentation
│   └── README.md
├── development/                # Development guides
│   └── README.md
├── implementation/             # Implementation tracking
│   ├── README.md
│   ├── audits/
│   ├── phases/
│   └── remediation/
├── migration/                  # Migration guides
│   └── README.md
├── operations/                 # Operations documentation
│   └── README.md
├── performance/                # Performance docs
│   └── README.md
└── archive/                    # Historical documents
    └── README.md
```

### Directory Naming Rules

1. **Use lowercase** for directory names
2. **Use hyphens** for multi-word directories (if needed)
3. **Be descriptive** but concise
4. **Group by purpose** not by format

**Examples:**

- ✅ `api/`, `architecture/`, `compliance/`
- ✅ `implementation/`, `operations/`
- ❌ `API/`, `Architecture/` (uppercase)
- ❌ `docs-api/`, `docs-arch/` (redundant prefix)

---

## Document Structure

### Required Sections

Every documentation file should include:

1. **Title** (H1) - Clear, descriptive title
2. **Metadata** - Date, version, status (if applicable)
3. **Overview/Introduction** - Brief description
4. **Table of Contents** - For documents >200 lines
5. **Main Content** - Organized with clear headings
6. **References** - Links to related documents
7. **Maintenance Info** - Last updated, review schedule

### Document Template

```markdown
# Document Title

**Date:** YYYY-MM-DD
**Version:** X.Y
**Status:** Draft | Active | Deprecated

Brief overview of the document's purpose and scope.

## Table of Contents

1. [Section 1](#section-1)
2. [Section 2](#section-2)
3. [References](#references)

---

## Section 1

Content here...

## Section 2

Content here...

---

## References

- [Related Doc 1](path/to/doc1.md)
- [Related Doc 2](path/to/doc2.md)

---

**Last Updated:** YYYY-MM-DD
**Maintained By:** Team/Person
**Review Frequency:** Monthly/Quarterly
```

### Section Hierarchy

Use proper heading hierarchy:

```markdown
# H1 - Document Title (only one per document)
## H2 - Major Sections
### H3 - Subsections
#### H4 - Sub-subsections
##### H5 - Rarely needed
###### H6 - Avoid if possible
```

---

## Writing Style

### General Principles

1. **Be Clear and Concise**
   - Use simple, direct language
   - Avoid jargon unless necessary
   - Define technical terms on first use

2. **Be Consistent**
   - Use consistent terminology
   - Follow the same structure across similar documents
   - Maintain consistent formatting

3. **Be Actionable**
   - Provide clear instructions
   - Include examples
   - Specify prerequisites

4. **Be Accurate**
   - Verify all technical details
   - Test all code examples
   - Keep information current

### Voice and Tone

- **Use active voice:** "Deploy the application" not "The application should be deployed"
- **Use present tense:** "The system connects" not "The system will connect"
- **Be direct:** "Run this command" not "You might want to run this command"
- **Be professional:** Avoid colloquialisms and humor in technical docs

### Formatting Conventions

**Commands and Code:**

```bash
# Use code blocks for commands
podman-compose -p janusgraph-demo up -d
```

**File Paths:**

- Use backticks: `path/to/file.md`
- Use relative paths when possible
- Be consistent with path separators

**Emphasis:**

- **Bold** for important terms and UI elements
- *Italic* for emphasis (use sparingly)
- `Code` for inline code, commands, and file names

---

## Markdown Formatting

### Code Blocks

Always specify the language for syntax highlighting:

````markdown
```python
def example():
    return "Hello, World!"
```

```bash
podman-compose -p janusgraph-demo up -d
```

```yaml
version: '3.8'
services:
  app:
    image: myapp:latest
```
````

### Lists

**Unordered Lists:**

```markdown
- Item 1
- Item 2
  - Sub-item 2.1
  - Sub-item 2.2
- Item 3
```

**Ordered Lists:**

```markdown
1. First step
2. Second step
3. Third step
```

**Task Lists:**

```markdown
- [x] Completed task
- [ ] Pending task
- [ ] Another pending task
```

### Tables

Use tables for structured data:

```markdown
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Data 1   | Data 2   | Data 3   |
| Data 4   | Data 5   | Data 6   |
```

**Alignment:**

```markdown
| Left | Center | Right |
|:-----|:------:|------:|
| L1   |   C1   |    R1 |
| L2   |   C2   |    R2 |
```

### Admonitions

Use blockquotes for notes, warnings, and tips:

```markdown
> **Note:** This is an informational note.

> **Warning:** This is a warning about potential issues.

> **Tip:** This is a helpful tip.
```

---

## Code Examples

### Requirements

1. **Test all examples** before including them
2. **Include context** - explain what the code does
3. **Show expected output** when relevant
4. **Handle errors** - show error handling when appropriate

### Example Format

```markdown
### Example: Creating a User

This example demonstrates how to create a new user:

```python
from banking.aml.sanctions_screening import SanctionsScreener

# Initialize the screener
screener = SanctionsScreener(opensearch_client)

# Screen an entity
result = screener.screen_entity(
    name="John Doe",
    entity_type="person",
    threshold=0.85
)

# Check results
if result.is_match:
    print(f"Match found: {result.matched_name}")
    print(f"Confidence: {result.confidence}")
```

**Expected Output:**

```
Match found: John Doe
Confidence: 0.92
```

```

---

## Links and References

### Internal Links

**Use relative paths:**
```markdown
Setup Guide (see getting-started)
[Banking Docs](banking/README.md)
[API Reference](banking/guides/api-reference.md)
```

**Link to specific sections:**

```markdown
Installation Section
[Configuration](banking/guides/user-guide.md#configuration)
```

### External Links

**Use descriptive text:**

```markdown
✅ [JanusGraph Documentation](https://docs.janusgraph.org/)
❌ [Click here](https://docs.janusgraph.org/)
```

### Cross-References

Always provide context for cross-references:

```markdown
For more information on deployment, see the [Deployment Guide](DEPLOYMENT.md).

Related documentation:
- [Architecture Overview](architecture.md)
- [Security Guidelines](SECURITY.md)
- Monitoring Setup (see operations)
```

---

## Maintenance

### Review Schedule

**Documentation Type** | **Review Frequency** | **Owner**
-----------------------|---------------------|----------
Core Documentation | Monthly | Tech Lead
API Documentation | With each release | Dev Team
Architecture Docs | Quarterly | Architects
Operations Docs | Monthly | Ops Team
Compliance Docs | Quarterly | Compliance Team

### Update Process

1. **Make Changes**
   - Update content
   - Update "Last Updated" date
   - Update version if significant changes

2. **Review**
   - Technical review for accuracy
   - Editorial review for clarity
   - Test all code examples

3. **Publish**
   - Commit changes with descriptive message
   - Update index.md if structure changed
   - Notify team of significant updates

### Deprecation

When deprecating documentation:

1. **Mark as deprecated** in the title and metadata
2. **Provide migration path** to new documentation
3. **Set removal date** (typically 6 months)
4. **Move to archive** after removal date

```markdown
# Old Feature Guide (DEPRECATED)

**Status:** Deprecated
**Deprecated Date:** 2026-01-28
**Removal Date:** 2026-07-28
**Migration:** See [New Feature Guide](new-feature-guide.md)

> **Warning:** This documentation is deprecated and will be removed on 2026-07-28.
> Please migrate to the [New Feature Guide](new-feature-guide.md).
```

---

## Checklist for New Documentation

Before publishing new documentation, verify:

- [ ] File name follows kebab-case convention
- [ ] File is in the correct directory
- [ ] Document includes required sections
- [ ] All code examples are tested
- [ ] All links are working
- [ ] Spelling and grammar checked
- [ ] Technical accuracy verified
- [ ] Cross-references added
- [ ] index.md updated (if needed)
- [ ] README.md updated (if needed)

---

## Examples

### Good Documentation Example

```markdown
# deployment-guide.md

**Date:** 2026-01-28
**Version:** 2.0
**Status:** Active

This guide provides step-by-step instructions for deploying the HCD + JanusGraph platform to production.

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 16GB RAM minimum
- 100GB disk space

## Deployment Steps

### 1. Prepare Environment

Create environment file:

```bash
cp .env.example .env
```

Edit `.env` and set:

- `CASSANDRA_PASSWORD` - Strong password
- `OPENSEARCH_PASSWORD` - Strong password

### 2. Deploy Services

```bash
cd config/compose
bash ../../scripts/deployment/deploy_full_stack.sh
```

**Expected Output:**

```
✓ Starting HCD...
✓ Starting JanusGraph...
✓ Starting OpenSearch...
✓ All services running
```

## Verification

Check service health:

```bash
podman-compose -p janusgraph-demo ps
```

All services should show "healthy" status.

## Troubleshooting

**Issue:** Services fail to start

**Solution:** Check logs:

```bash
podman-compose -p janusgraph-demo logs -f
```

## References

- Setup Guide (see Getting Started)
- Monitoring Guide (see [Operations Runbook](operations/operations-runbook.md))
- Troubleshooting (see [Operations Runbook](operations/operations-runbook.md))

---

**Last Updated:** 2026-02-07
**Maintained By:** DevOps Team
**Review Frequency:** Monthly

```

---

### Using the Enforcement Tools

**Pre-commit Hook:**

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run manually on all files
pre-commit run validate-kebab-case --all-files
```

**CI/CD Validation:**

The GitHub Actions workflow automatically runs on:
- Pull requests modifying documentation
- Pushes to `main` or `develop` branches

**Manual Validation:**

```bash
# Check for violations (dry-run)
python3 scripts/docs/apply-kebab-case.py

# Fix violations automatically
python3 scripts/docs/apply-kebab-case.py --execute

# Rollback if needed
python3 scripts/docs/apply-kebab-case.py --rollback
```

### Enforcement Workflow

```
┌─────────────────┐
│ Developer makes │
│  doc changes    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  git commit     │◄─── Pre-commit hook validates
└────────┬────────┘     (blocks if violations)
         │
         ▼
┌─────────────────┐
│   git push      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Pull Request   │◄─── CI/CD validates
└────────┬────────┘     (fails if violations)
         │
         ▼
┌─────────────────┐
│  Code Review    │◄─── Human review
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│     Merge       │
└─────────────────┘
```


## Enforcement

These standards are enforced through:

1. **Pre-commit Hooks** - Automatic validation before commits
   - Configured in `.pre-commit-config.yaml`
   - Runs `scripts/docs/apply-kebab-case.py` in dry-run mode
   - Blocks commits with naming violations

2. **CI/CD Pipeline** - Automated checks on pull requests
   - GitHub Actions workflow: `.github/workflows/validate-doc-naming.yml`
   - Runs on all documentation changes
   - Provides detailed failure reports with fix instructions

3. **Automated Remediation** - Self-service fix tool
   - Script: `scripts/docs/apply-kebab-case.py`
   - Dry-run mode: `python3 scripts/docs/apply-kebab-case.py`
   - Execute mode: `python3 scripts/docs/apply-kebab-case.py --execute`
   - Features: backup, rollback, git-aware renaming, link updates

4. **Code Review** - All documentation changes reviewed

5. **Team Training** - Regular documentation workshops

6. **AGENTS.md** - AI assistant follows these standards

---

## Placeholder Patterns and Code Auditing

### Intentional Placeholder Patterns

Documentation uses curly-brace placeholders that are **intentional template markers**, not TODOs:

| Pattern | Purpose | Example |
|---------|---------|---------|
| `{NUMBER}` | Sequential numbering | ADR-{NUMBER} |
| `{12-CHAR-ID}` | ID format specification | PER-{12-CHAR-ID} |
| `{PHONE-NUMBER}` | Redacted contact info | +1-{PHONE-NUMBER} |
| `{PLACEHOLDER}` | Generic template field | `name: {PLACEHOLDER}` |

**Why this matters**: Grep searches for `TODO|FIXME|XXX` will no longer match these intentional markers.

### Archive Directory Exclusion

When searching for actual TODOs in the codebase, **exclude archive directories**:

```bash
# Recommended: Exclude archive directories from TODO searches
grep -r "TODO\|FIXME" --include="*.py" --include="*.md" \
  --exclude-dir="archive" --exclude-dir="vendor" .

# Or use ripgrep (faster)
rg "TODO|FIXME" --type py --type md \
  --glob '!**/archive/**' --glob '!**/vendor/**'
```

**Directories to exclude from audits:**

- `docs/archive/` - Historical documents
- `docs/implementation/remediation/archive/` - Completed remediation records
- `docs/implementation/audits/archive/` - Past audit reports
- `vendor/` - Third-party code

---

## Questions?

For questions about documentation standards:

1. Check this guide first
2. Review existing documentation for examples
3. Ask in team chat
4. Open an issue for clarification

---

**Version History:**

- **1.0** (2026-01-28) - Initial version

---

**Maintained By:** Documentation Team
**Review Frequency:** Quarterly
**Next Review:** 2026-04-28
