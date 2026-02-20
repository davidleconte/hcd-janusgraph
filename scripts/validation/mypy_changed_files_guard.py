#!/usr/bin/env python3
"""
Enforce "no new mypy errors" on changed first-party Python files.

Default scope:
- src/python/**/*.py
- banking/**/*.py

By default, test files are excluded from the guard.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List


INCLUDE_ROOTS = ("src/python/", "banking/")


def run(cmd: List[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=check, text=True, capture_output=True)


def ref_exists(ref: str) -> bool:
    proc = run(["git", "rev-parse", "--verify", "--quiet", ref], check=False)
    return proc.returncode == 0


def resolve_refs(base_ref: str | None, head_ref: str | None) -> tuple[str, str]:
    if head_ref:
        head = head_ref
    else:
        head = os.environ.get("GITHUB_SHA", "HEAD")

    if base_ref:
        return base_ref, head

    gh_base_ref = os.environ.get("GITHUB_BASE_REF")
    if gh_base_ref:
        candidate = f"origin/{gh_base_ref}"
        if not ref_exists(candidate):
            run(["git", "fetch", "--no-tags", "--depth", "200", "origin", gh_base_ref], check=False)
        if ref_exists(candidate):
            return candidate, head

    if ref_exists("HEAD~1"):
        return "HEAD~1", head

    raise RuntimeError(
        "Unable to resolve base ref. Provide --base-ref/--head-ref or ensure git history is available."
    )


def changed_python_files(base_ref: str, head_ref: str, include_tests: bool) -> list[str]:
    proc = run(
        ["git", "diff", "--name-only", "--diff-filter=ACMR", f"{base_ref}...{head_ref}"],
        check=False,
    )
    if proc.returncode != 0:
        proc = run(
            ["git", "diff", "--name-only", "--diff-filter=ACMR", f"{base_ref}..{head_ref}"],
            check=False,
        )
    if proc.returncode != 0:
        raise RuntimeError(
            "Unable to compute changed files for refs "
            f"{base_ref} and {head_ref}.\n{proc.stderr.strip()}"
        )

    files: list[str] = []
    for raw in proc.stdout.splitlines():
        path = raw.strip()
        if not path.endswith(".py"):
            continue
        if not path.startswith(INCLUDE_ROOTS):
            continue
        if not include_tests and "/tests/" in path:
            continue
        if Path(path).exists():
            files.append(path)
    return sorted(set(files))


def run_mypy(files: list[str]) -> int:
    if not files:
        print("No changed first-party Python files in scope; mypy changed-files guard skipped.")
        return 0

    print("Changed files in mypy scope:")
    for file_path in files:
        print(f"- {file_path}")

    cmd = ["mypy", "--ignore-missing-imports", *files]
    proc = subprocess.run(cmd, text=True)
    return proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Run mypy only on changed files.")
    parser.add_argument("--base-ref", default=None, help="Base git ref for diff.")
    parser.add_argument("--head-ref", default=None, help="Head git ref for diff.")
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="Include files under */tests/* in changed-file mypy checks.",
    )
    args = parser.parse_args()

    try:
        base_ref, head_ref = resolve_refs(args.base_ref, args.head_ref)
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        return 1

    try:
        files = changed_python_files(base_ref, head_ref, include_tests=args.include_tests)
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        return 1

    return run_mypy(files)


if __name__ == "__main__":
    raise SystemExit(main())
