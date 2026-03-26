<!--
File: .github/PULL_REQUEST_TEMPLATE.md
Created: 2026-01-28T10:31:20.789
Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
-->

## Description

Brief description of changes made in this PR.

## Type of Change

- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing functionality to break)
- [ ] Documentation update
- [ ] Refactoring
- [ ] Configuration change

## Related Issues

Closes #(issue number)

## Changes Made

- Change 1
- Change 2
- Change 3

## Testing

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed
- [ ] All tests pass locally

## Checklist

- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No breaking changes (or documented if unavoidable)
- [ ] No secrets/credentials committed
- [ ] All CI checks pass

## Determinism Acceptance Criteria (Release Gate)

- [ ] Deterministic wrapper rerun executed when required
- [ ] `exports/deterministic-status.json` exists and `exit_code=0`
- [ ] Determinism-sensitive changes include `[determinism-override]` (if applicable)
- [ ] Notebook run report shows required notebooks PASS with `error_cells=0`
- [ ] Determinism artifact verification and drift detection passed
- [ ] Evidence artifacts linked in PR (status JSON, run dir, reports/logs, canonical baseline refs)
- [ ] Reviewed against: `docs/operations/determinism-acceptance-criteria-checklist.md`

## Screenshots (if applicable)

Add screenshots here.

## Deployment Notes

Any special deployment considerations or migration steps.

---
**Reviewed by**: _______________
**Signature**: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
