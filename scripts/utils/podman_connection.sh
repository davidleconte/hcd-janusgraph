#!/usr/bin/env bash
set -euo pipefail

# Resolve a working podman remote connection name.
#
# Resolution order:
#  1. Explicit argument (if provided and reachable)
#  2. Environment PODMAN_CONNECTION (if set and reachable)
#  3. Common local defaults (podman-machine-default, podman-wxd variants)
#  4. Any connections returned by `podman system connection list`.
resolve_podman_connection() {
  local requested
  local -a candidates=()
  local candidate

  requested="${1:-${PODMAN_CONNECTION:-}}"

  if [[ -n "$requested" ]]; then
    candidates+=("$requested")
  fi

  candidates+=(
    "podman-machine-default"
    "podman-machine-default-root"
    "podman-wxd"
    "podman-wxd-root"
  )

  while IFS= read -r candidate; do
    if [[ -z "$candidate" ]]; then
      continue
    fi
    candidates+=( "$candidate" )
  done < <(podman system connection list --format '{{.Name}}' 2>/dev/null || true)

  # Deduplicate while preserving order.
  local -a unique_candidates=()
  local seen=false
  local seen_candidate
  for candidate in "${candidates[@]}"; do
    seen=false
    for seen_candidate in "${unique_candidates[@]}"; do
      if [[ "$seen_candidate" == "$candidate" ]]; then
        seen=true
        break
      fi
    done
    if [[ "$seen" == false ]]; then
      unique_candidates+=( "$candidate" )
    fi
  done

  for candidate in "${unique_candidates[@]}"; do
    if podman --remote --connection "$candidate" ps >/dev/null 2>&1; then
      echo "$candidate"
      return 0
    fi
  done

  echo "❌ No reachable Podman remote connection found." >&2
  if ! podman system connection list >/dev/null 2>&1; then
    echo "   Could not read podman connections." >&2
  else
    echo "   Available connections:" >&2
    while IFS= read -r candidate; do
      echo "   - $candidate" >&2
    done < <(podman system connection list --format '{{.Name}}' 2>/dev/null)
  fi
  return 1
}
