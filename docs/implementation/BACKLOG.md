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

## P2 - Medium Priority (All Complete ✅)

| Task | Status | Effort | Notes |
|------|--------|--------|-------|
| Archive old remediation docs | ✅ Done | 10 min | Moved pre-2026-02-04 docs |
| HCD tarball to Git LFS | ✅ Done | 10 min | `.gitattributes` configured for `vendor/*.tar.gz` |
| Notebook consolidation | ✅ Done | 30 min | Created `notebooks/README.md` unified index |
| Kebab-case file naming | ✅ Done | 1 hour | 41 files renamed, links updated |

---

## P3 - Future Improvements (All Complete ✅)

| Task | Status | Effort | Notes |
|------|--------|--------|-------|
| mkdocs setup | ✅ Done | 2 hours | `mkdocs.yml` + Material theme + Mermaid |
| GitHub Pages deployment | ✅ Done | 30 min | `.github/workflows/docs.yml` - PASSING ✅ |
| API documentation generation | ✅ Done | 20 min | `scripts/docs/generate_api_docs.sh` (pdoc) |

---

## Technical Debt (Remaining)

| Item | Priority | Notes |
|------|----------|-------|
| `gremlinpython` pinned to <3.8.0 | Medium | Server compatibility issue with `.discard()` |
| Test timeout for full suite | Low | Run tests in batches (600s limit) |
| Some notebooks use hardcoded paths | Low | Parameterize with environment variables |
| mkdocs warnings (371) | Low | Broken anchors in docs - cosmetic only |

---

## Completed Recently

- 2026-02-06: Fixed GitHub Actions docs workflow - now passing ✅
- 2026-02-06: Added mkdocs Material theme with Mermaid support
- 2026-02-06: Renamed 41 docs files to kebab-case
- 2026-02-06: Created unified notebooks index
- 2026-02-06: Added API docs generation script (pdoc)
- 2026-02-06: Added link validation to CI pipeline
- 2026-02-06: Archived old remediation documentation
- 2026-02-06: Updated all author attributions project-wide
- 2026-02-05: Migrated to centralized `pyproject.toml`
- 2026-02-05: Fixed unit tests (port 18182, field naming)
- 2026-02-05: Full test suite passing (331 unit, 43 integration)
