#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "${PROJECT_ROOT}/scripts/utils/podman_connection.sh"

PODMAN_CONNECTION="${PODMAN_CONNECTION:-}"
if ! PODMAN_CONNECTION="$(resolve_podman_connection "${PODMAN_CONNECTION}")"; then
    echo "❌ Unable to resolve a reachable podman connection"
    exit 1
fi
COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-janusgraph-demo}"

ANALYTICS_SERVICE="${ANALYTICS_SERVICE:-analytics-api}"
JUPYTER_SERVICE="${JUPYTER_SERVICE:-jupyter}"

PASS_COUNT=0
FAIL_COUNT=0

pass() {
    local msg="$1"
    PASS_COUNT=$((PASS_COUNT + 1))
    echo "✅ ${msg}"
}

fail() {
    local msg="$1"
    FAIL_COUNT=$((FAIL_COUNT + 1))
    echo "❌ ${msg}"
}

load_container_list() {
    podman --remote --connection "${PODMAN_CONNECTION}" ps --format '{{.Names}}'
}

resolve_container() {
    local service_name="$1"
    local with_prefix="${COMPOSE_PROJECT_NAME}_${service_name}_1"
    local list="$2"

    if printf '%s\n' "${list}" | grep -qx "${with_prefix}"; then
        echo "${with_prefix}"
        return 0
    fi

    if printf '%s\n' "${list}" | grep -qx "${service_name}"; then
        echo "${service_name}"
        return 0
    fi

    return 1
}

check_python_modules() {
    local container_name="$1"
    local module_csv="$2"

    podman --remote --connection "${PODMAN_CONNECTION}" exec \
        -e "MODULE_CSV=${module_csv}" \
        "${container_name}" \
        bash -lc '
set -euo pipefail
PYBIN="python3"
if ! command -v "${PYBIN}" >/dev/null 2>&1; then
  PYBIN="python"
fi
if command -v conda >/dev/null 2>&1; then
  CONDA_PY="conda run -n janusgraph-analysis python"
else
  CONDA_PY=""
fi
if [[ -n "${CONDA_PY}" ]]; then
  ${CONDA_PY} - <<'"'"'PY'"'"'
import importlib.util
import os
import sys

mods = [m.strip() for m in os.environ.get("MODULE_CSV", "").split(",") if m.strip()]
missing = [m for m in mods if importlib.util.find_spec(m) is None]
if missing:
    print("Missing modules: " + ", ".join(missing))
    raise SystemExit(1)
PY
else
"${PYBIN}" - <<'"'"'PY'"'"'
import importlib.util
import os
import sys

mods = [m.strip() for m in os.environ.get("MODULE_CSV", "").split(",") if m.strip()]
missing = [m for m in mods if importlib.util.find_spec(m) is None]
if missing:
    print("Missing modules: " + ", ".join(missing))
    raise SystemExit(1)
PY
fi
'
}

main() {
    local container_list
    local analytics_container
    local jupyter_container

    if ! container_list="$(load_container_list 2>/dev/null)"; then
        echo "❌ Unable to access podman containers on connection '${PODMAN_CONNECTION}'"
        exit 1
    fi

    if ! analytics_container="$(resolve_container "${ANALYTICS_SERVICE}" "${container_list}")"; then
        echo "❌ Could not resolve analytics container for service '${ANALYTICS_SERVICE}'"
        exit 1
    fi
    pass "Resolved analytics container: ${analytics_container}"

    if ! jupyter_container="$(resolve_container "${JUPYTER_SERVICE}" "${container_list}")"; then
        echo "❌ Could not resolve jupyter container for service '${JUPYTER_SERVICE}'"
        exit 1
    fi
    pass "Resolved jupyter container: ${jupyter_container}"

    local analytics_modules
    analytics_modules="slowapi,pydantic_settings,pythonjsonlogger,jwt,banking,pyotp,qrcode,opentelemetry,opentelemetry.sdk,opentelemetry.exporter.otlp.proto.grpc.trace_exporter,opentelemetry.exporter.jaeger.thrift,opentelemetry.instrumentation.requests,requests"
    if check_python_modules "${analytics_container}" "${analytics_modules}" >/dev/null 2>&1; then
        pass "Analytics runtime python modules validated"
    else
        fail "Analytics runtime python modules check failed"
    fi

    if podman --remote --connection "${PODMAN_CONNECTION}" exec "${analytics_container}" bash -lc 'test -n "${OPENSEARCH_INITIAL_ADMIN_PASSWORD:-}"'; then
        pass "analytics-api env includes OPENSEARCH_INITIAL_ADMIN_PASSWORD"
    else
        fail "analytics-api env is missing OPENSEARCH_INITIAL_ADMIN_PASSWORD"
    fi

    if podman --remote --connection "${PODMAN_CONNECTION}" exec "${analytics_container}" bash -lc 'test -w /var/log/janusgraph'; then
        pass "analytics-api can write /var/log/janusgraph"
    else
        fail "analytics-api cannot write /var/log/janusgraph"
    fi

    local jupyter_modules
    jupyter_modules="pydantic,pydantic_settings,email_validator"
    if check_python_modules "${jupyter_container}" "${jupyter_modules}" >/dev/null 2>&1; then
        pass "Jupyter runtime python modules validated"
    else
        fail "Jupyter runtime python modules check failed"
    fi

    if podman --remote --connection "${PODMAN_CONNECTION}" exec "${jupyter_container}" bash -lc 'test -d /workspace/notebooks-exploratory && ls /workspace/notebooks-exploratory/*.ipynb >/dev/null 2>&1'; then
        pass "Jupyter exploratory notebooks mount/path validated"
    else
        fail "Jupyter exploratory notebooks mount/path missing or empty"
    fi

    echo "Runtime contract checks: pass=${PASS_COUNT} fail=${FAIL_COUNT}"
    if [[ "${FAIL_COUNT}" -gt 0 ]]; then
        exit 1
    fi
}

main "$@"
