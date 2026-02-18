#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "${PROJECT_ROOT}/scripts/utils/podman_connection.sh"

OUT_FILE="${1:-}"
if [[ -z "${OUT_FILE}" ]]; then
    echo "Usage: capture_runtime_package_fingerprint.sh <output-file>"
    exit 1
fi

mkdir -p "$(dirname "${OUT_FILE}")"

PODMAN_CONNECTION="${PODMAN_CONNECTION:-}"
if ! PODMAN_CONNECTION="$(resolve_podman_connection "${PODMAN_CONNECTION}")"; then
    echo "❌ Unable to resolve a reachable podman connection"
    exit 1
fi

COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-janusgraph-demo}"
JUPYTER_SERVICE="${JUPYTER_SERVICE:-jupyter}"

JUPYTER_CONTAINER="$(
    podman --remote --connection "${PODMAN_CONNECTION}" ps \
        --filter "label=io.podman.compose.project=${COMPOSE_PROJECT_NAME}" \
        --filter "label=io.podman.compose.service=${JUPYTER_SERVICE}" \
        --format '{{.Names}}' | head -n 1
)"

if [[ -z "${JUPYTER_CONTAINER}" ]]; then
    JUPYTER_CONTAINER="$(
        podman --remote --connection "${PODMAN_CONNECTION}" ps --format '{{.Names}}' | \
            grep -E "^${COMPOSE_PROJECT_NAME}_${JUPYTER_SERVICE}(_[0-9]+)?$|^${JUPYTER_SERVICE}$" | head -n 1 || true
    )"
fi

if [[ -z "${JUPYTER_CONTAINER}" ]]; then
    echo "❌ Could not resolve Jupyter container for service '${JUPYTER_SERVICE}' on connection '${PODMAN_CONNECTION}'"
    podman --remote --connection "${PODMAN_CONNECTION}" ps --format '{{.Names}}' | sed 's/^/ - /' || true
    exit 1
fi

podman --remote --connection "${PODMAN_CONNECTION}" exec "${JUPYTER_CONTAINER}" bash -lc '
set -euo pipefail
if command -v conda >/dev/null 2>&1; then
  PY_CMD=(conda run --no-capture-output -n janusgraph-analysis python)
elif command -v python3 >/dev/null 2>&1; then
  PY_CMD=(python3)
else
  PY_CMD=(python)
fi
"${PY_CMD[@]}" - <<'"'"'PY'"'"'
import hashlib
import importlib.metadata as md
import platform

import numpy as np
import pandas as pd
import email_validator  # noqa: F401

arr = np.array([1, 2, 3], dtype=np.int64)
df = pd.DataFrame({"v": arr})
if int(df["v"].sum()) != 6:
    raise SystemExit("numpy/pandas ABI check failed")

def pkg_version(name: str) -> str:
    try:
        return md.version(name)
    except Exception:
        return "missing"

dist_pairs = sorted(
    (
        (d.metadata.get("Name") or "").strip().lower(),
        d.version,
    )
    for d in md.distributions()
    if d.metadata.get("Name")
)
dist_blob = "\n".join(f"{name}=={version}" for name, version in dist_pairs)
site_hash = hashlib.sha256(dist_blob.encode("utf-8")).hexdigest()
email_validator_version = pkg_version("email-validator")
pydantic_version = pkg_version("pydantic")

lines = [
    f"python={platform.python_version()}",
    f"python_implementation={platform.python_implementation()}",
    f"numpy={np.__version__}",
    f"pandas={pd.__version__}",
    f"email-validator={email_validator_version}",
    f"pydantic={pydantic_version}",
    f"site_packages_sha256={site_hash}",
]
for line in lines:
    print(line)
PY
' > "${OUT_FILE}"

if [[ ! -s "${OUT_FILE}" ]]; then
    echo "❌ Runtime package fingerprint output is empty"
    exit 1
fi

echo "✅ Runtime package fingerprint captured: ${OUT_FILE}"
