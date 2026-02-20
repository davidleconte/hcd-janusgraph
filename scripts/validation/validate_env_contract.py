#!/usr/bin/env python3
"""
Validate environment variable contract for production-secure profile.

Checks:
1. Required secure-profile variables are present in .env examples.
2. Deprecated app variable aliases are not used.
3. Unknown app-runtime variable names are not introduced.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


APP_SETTINGS_ENV_KEYS = {
    "ENVIRONMENT",
    "DEBUG",
    "JANUSGRAPH_HOST",
    "JANUSGRAPH_PORT",
    "JANUSGRAPH_USE_SSL",
    "JANUSGRAPH_CA_CERTS",
    "OPENSEARCH_HOST",
    "OPENSEARCH_PORT",
    "OPENSEARCH_USE_SSL",
    "OPENSEARCH_USERNAME",
    "OPENSEARCH_PASSWORD",
    "PULSAR_URL",
    "API_HOST",
    "API_PORT",
    "API_KEY",
    "API_JWT_SECRET",
    "API_ACCESS_TOKEN_TTL_MINUTES",
    "API_REFRESH_TOKEN_TTL_MINUTES",
    "API_USER",
    "API_USER_PASSWORD",
    "API_USER_ROLES",
    "API_USER_EMAIL",
    "AUTH_ENABLED",
    "AUTH_DEFAULT_ROLES",
    "MFA_REQUIRED_ROLES",
    "API_CORS_ORIGINS",
    "RATE_LIMIT_PER_MINUTE",
    "OTEL_SERVICE_NAME",
    "JAEGER_HOST",
    "JAEGER_PORT",
    "TRACING_ENABLED",
    "TRACING_SAMPLE_RATE",
    "LOG_LEVEL",
    "LOG_JSON",
}

PROD_REQUIRED_APP_KEYS = {
    "AUTH_ENABLED",
    "API_JWT_SECRET",
    "API_USER_PASSWORD",
    "API_USER",
    "API_USER_ROLES",
    "API_CORS_ORIGINS",
    "RATE_LIMIT_PER_MINUTE",
}

APP_PREFIXES = ("API_", "AUTH_", "MFA_", "RATE_LIMIT_", "OTEL_", "JAEGER_", "TRACING_")
APP_DIRECT_KEYS = {"ENVIRONMENT", "DEBUG", "LOG_LEVEL", "LOG_JSON"}
DEPRECATED_APP_KEYS = {"MAX_REQUESTS_PER_MINUTE"}
ALLOWED_NON_SETTINGS_KEYS = {
    "OPENSEARCH_INITIAL_ADMIN_PASSWORD",
    "GRAFANA_ADMIN_USER",
    "GRAFANA_ADMIN_PASSWORD",
    "SMTP_PASSWORD",
    "SLACK_WEBHOOK_URL",
    "COMPOSE_PROJECT_NAME",
    "PODMAN_CONNECTION",
    "PODMAN_PLATFORM",
}


def parse_env_keys(path: Path) -> set[str]:
    keys: set[str] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key = line.split("=", 1)[0].strip()
        if key.startswith("export "):
            key = key[len("export ") :].strip()
        if re.fullmatch(r"[A-Z0-9_]+", key):
            keys.add(key)
    return keys


def parse_required_compose_vars(path: Path) -> set[str]:
    content = path.read_text(encoding="utf-8")
    return set(re.findall(r"\$\{([A-Z0-9_]+):\?", content))


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate environment variable contract.")
    parser.add_argument("--env-file", default=".env.example")
    parser.add_argument("--compose-env-file", default="config/compose/.env.example")
    parser.add_argument(
        "--prod-override",
        default="config/compose/docker-compose.prod-secure.override.yml",
    )
    args = parser.parse_args()

    env_file = Path(args.env_file)
    compose_env_file = Path(args.compose_env_file)
    prod_override = Path(args.prod_override)

    missing_files = [
        str(p) for p in (env_file, compose_env_file, prod_override) if not p.exists()
    ]
    if missing_files:
        print("ERROR: missing required files:")
        for path in missing_files:
            print(f"  - {path}")
        return 1

    root_env_keys = parse_env_keys(env_file)
    compose_env_keys = parse_env_keys(compose_env_file)
    compose_required_keys = parse_required_compose_vars(prod_override)

    errors: list[str] = []

    deprecated = sorted(DEPRECATED_APP_KEYS & root_env_keys)
    if deprecated:
        errors.append(
            "Deprecated variables found in root env example: " + ", ".join(deprecated)
        )

    missing_root_required = sorted((PROD_REQUIRED_APP_KEYS | compose_required_keys) - root_env_keys)
    if missing_root_required:
        errors.append(
            "Root env example missing required prod variables: "
            + ", ".join(missing_root_required)
        )

    missing_compose_required = sorted(compose_required_keys - compose_env_keys)
    if missing_compose_required:
        errors.append(
            "Compose env example missing variables required by prod override: "
            + ", ".join(missing_compose_required)
        )

    unknown_app_keys = sorted(
        key
        for key in root_env_keys
        if (
            key.startswith(APP_PREFIXES) or key in APP_DIRECT_KEYS
        )
        and key not in APP_SETTINGS_ENV_KEYS
        and key not in ALLOWED_NON_SETTINGS_KEYS
    )
    if unknown_app_keys:
        errors.append(
            "Unknown app-runtime variables in root env example: " + ", ".join(unknown_app_keys)
        )

    if errors:
        print("ENV CONTRACT VALIDATION FAILED")
        for err in errors:
            print(f"- {err}")
        return 1

    print("ENV CONTRACT VALIDATION PASSED")
    print(f"- Root env keys parsed: {len(root_env_keys)}")
    print(f"- Compose env keys parsed: {len(compose_env_keys)}")
    print(f"- Prod override required keys: {', '.join(sorted(compose_required_keys))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
