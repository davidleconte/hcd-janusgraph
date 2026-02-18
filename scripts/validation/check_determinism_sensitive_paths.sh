#!/usr/bin/env bash
set -euo pipefail

OVERRIDE_TOKEN="[determinism-override]"
ALLOW_OVERRIDE="${ALLOW_DETERMINISM_SENSITIVE_CHANGES:-0}"

PROTECTED_PATTERNS=(
  "requirements.lock.txt"
  "environment.yml"
  "config/compose/docker-compose.full.yml"
  "banking/streaming/events.py"
  "scripts/testing/run_demo_pipeline_repeatable.sh"
  "scripts/testing/run_notebooks_live_repeatable.sh"
  "scripts/testing/check_runtime_contracts.sh"
  "scripts/testing/capture_runtime_package_fingerprint.sh"
  "scripts/testing/check_notebook_determinism_contracts.sh"
  "scripts/testing/collect_run_manifest.sh"
  "scripts/testing/verify_deterministic_artifacts.sh"
  "notebooks/*.ipynb"
  "notebooks/*/*.ipynb"
  "notebooks/*/*/*.ipynb"
  "notebooks-exploratory/*.ipynb"
  "notebooks-exploratory/*/*.ipynb"
  "notebooks-exploratory/*/*/*.ipynb"
)

resolve_base_ref() {
  if [[ -n "${GITHUB_BASE_REF:-}" ]]; then
    git fetch --no-tags --depth=1 origin "${GITHUB_BASE_REF}:${GITHUB_BASE_REF}" >/dev/null 2>&1 || true
    if git rev-parse --verify "${GITHUB_BASE_REF}" >/dev/null 2>&1; then
      git merge-base "${GITHUB_BASE_REF}" HEAD
      return 0
    fi
  fi

  if git rev-parse --verify HEAD~1 >/dev/null 2>&1; then
    echo "HEAD~1"
    return 0
  fi

  return 1
}

if ! BASE_REF="$(resolve_base_ref)"; then
  echo "No base ref available; skipping determinism-sensitive path guard."
  exit 0
fi

mapfile -t CHANGED_FILES < <(git diff --name-only "${BASE_REF}" HEAD)

if [[ ${#CHANGED_FILES[@]} -eq 0 ]]; then
  echo "No changed files detected."
  exit 0
fi

FLAGGED=()
for file in "${CHANGED_FILES[@]}"; do
  for pattern in "${PROTECTED_PATTERNS[@]}"; do
    if [[ "${file}" == ${pattern} ]]; then
      FLAGGED+=("${file}")
      break
    fi
  done
done

if [[ ${#FLAGGED[@]} -eq 0 ]]; then
  echo "No determinism-sensitive paths changed."
  exit 0
fi

LATEST_MESSAGE="$(git log -1 --pretty=%B || true)"
if [[ "${ALLOW_OVERRIDE}" == "1" ]] || grep -Fqi "${OVERRIDE_TOKEN}" <<<"${LATEST_MESSAGE}"; then
  echo "Override accepted for determinism-sensitive path changes."
  printf 'Protected files changed:\n'
  printf '  - %s\n' "${FLAGGED[@]}"
  exit 0
fi

echo "::error::Determinism-sensitive paths were modified without explicit override."
printf 'Blocked files:\n'
printf '  - %s\n' "${FLAGGED[@]}"
echo "Use ${OVERRIDE_TOKEN} in commit message and request explicit reviewer approval."
exit 1
