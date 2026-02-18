# Codex GitHub Branch Protection Checklist: Deterministic Proof

**Date:** 2026-02-18  
**Status:** Active  
**Scope:** Repository admin action for `master` / `main`

## Objective

Require CI check `Deterministic Proof / deterministic-proof` before merge.

## UI Checklist (GitHub Web)

1. Open `Settings` -> `Branches` -> `Branch protection rules`.
2. Edit existing rules for `master` and `main` (or create if missing).
3. Enable `Require a pull request before merging`.
4. Enable `Require status checks to pass before merging`.
5. Enable `Require branches to be up to date before merging`.
6. In required checks, add exact context: `Deterministic Proof / deterministic-proof`.
7. Save rule.

## CLI Enforcement (safe merge with existing required checks)

```bash
#!/usr/bin/env bash
set -euo pipefail

OWNER="davidleconte"
REPO="hcd-janusgraph"
TARGET_CHECK="Deterministic Proof / deterministic-proof"

for BRANCH in master main; do
  if ! gh api "repos/${OWNER}/${REPO}/branches/${BRANCH}" >/dev/null 2>&1; then
    echo "skip: ${BRANCH} does not exist"
    continue
  fi

  mapfile -t CONTEXTS < <(
    gh api "repos/${OWNER}/${REPO}/branches/${BRANCH}/protection/required_status_checks" \
      --jq '.contexts[]?' 2>/dev/null || true
  )

  NEED_ADD=1
  for c in "${CONTEXTS[@]}"; do
    if [[ "${c}" == "${TARGET_CHECK}" ]]; then
      NEED_ADD=0
      break
    fi
  done
  if [[ "${NEED_ADD}" -eq 1 ]]; then
    CONTEXTS+=("${TARGET_CHECK}")
  fi

  ARGS=(--method PATCH -H "Accept: application/vnd.github+json" "repos/${OWNER}/${REPO}/branches/${BRANCH}/protection/required_status_checks" -f strict=true)
  for c in "${CONTEXTS[@]}"; do
    ARGS+=(-f "contexts[]=${c}")
  done

  gh api "${ARGS[@]}"
  echo "updated required checks for ${BRANCH}"
done
```

## Verification

```bash
for BRANCH in master main; do
  gh api "repos/davidleconte/hcd-janusgraph/branches/${BRANCH}/protection/required_status_checks" \
    --jq '{branch:"'"${BRANCH}"'", strict:.strict, contexts:.contexts}' 2>/dev/null || true
done
```

Expected: context list includes `Deterministic Proof / deterministic-proof`.
