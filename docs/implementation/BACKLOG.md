# Project Backlog

**Author:** David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)  
**Contact:** +33614126117  
**Date:** 2026-02-06  
**Status:** Active

## Overview

This document tracks remaining improvements and technical debt items for the HCD-JanusGraph project.

---

## P0 - Critical (Completed ✅)

| Task | Status | Notes |
|------|--------|-------|
| Remove empty directories | ✅ Done | Cleaned `notebooks/`, `.jks` |
| Add `.gitkeep` to intentional empty dirs | ✅ Done | `config/ssl/certs/`, etc. |

---

## P1 - High Priority

| Task | Status | Effort | Notes |
|------|--------|--------|-------|
| Link validation in CI | ✅ Done | 10 min | Added `markdown-link-check` to `.github/workflows/ci.yml` |
| Consolidate requirements | ✅ Done | 30 min | Migrated to `pyproject.toml` |
| Credential validation script | ✅ Done | 20 min | `scripts/validation/validate_credentials.sh` |

---

## P2 - Medium Priority

| Task | Status | Effort | Notes |
|------|--------|--------|-------|
| Archive old remediation docs | ✅ Done | 10 min | Moved pre-2026-02-04 docs |
| HCD tarball to Git LFS | 🔲 TODO | 1 hour | `hcd-1.2.3/` is 50MB+ |
| Notebook consolidation | 🔲 TODO | 2 hours | 14 notebooks → organized structure |
| Kebab-case file naming | 🔲 TODO | 2-4 hours | 162 files to rename |

---

## P3 - Future Improvements

| Task | Status | Effort | Notes |
|------|--------|--------|-------|
| mkdocs/docusaurus setup | 🔲 TODO | 4-8 hours | Searchable documentation site |
| GitHub Pages deployment | 🔲 TODO | 2 hours | Auto-deploy docs on merge |
| API documentation generation | 🔲 TODO | 4 hours | Sphinx/pdoc for Python modules |

---

## Technical Debt

| Item | Priority | Notes |
|------|----------|-------|
| `gremlinpython` pinned to <3.8.0 | Medium | Server compatibility issue with `.discard()` |
| Test timeout for full suite | Low | Run tests in batches (600s limit) |
| Some notebooks use hardcoded paths | Low | Parameterize with environment variables |

---

## Completed Recently

- 2026-02-06: Added link validation to CI pipeline
- 2026-02-06: Archived old remediation documentation
- 2026-02-06: Updated all author attributions project-wide
- 2026-02-05: Migrated to centralized `pyproject.toml`
- 2026-02-05: Fixed unit tests (port 18182, field naming)
- 2026-02-05: Full test suite passing (331 unit, 43 integration)
