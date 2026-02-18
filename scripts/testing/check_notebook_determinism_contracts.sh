#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
NOTEBOOK_DETERMINISM_STRICT="${NOTEBOOK_DETERMINISM_STRICT:-0}"

python3 - "${PROJECT_ROOT}" "${NOTEBOOK_DETERMINISM_STRICT}" <<'PY'
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
strict_mode = sys.argv[2] == "1"
targets = sorted((root / "banking" / "notebooks").glob("*.ipynb")) + sorted(
    (root / "notebooks-exploratory").glob("*.ipynb")
)

hard_patterns = [
    ("datetime.now()", re.compile(r"\bdatetime\s*\.\s*now\s*\(")),
    ("datetime.utcnow()", re.compile(r"\bdatetime\s*\.\s*utcnow\s*\(")),
    ("date.today()", re.compile(r"\bdate\s*\.\s*today\s*\(")),
    ("time.time()", re.compile(r"\btime\s*\.\s*time\s*\(")),
    ("uuid.uuid4()", re.compile(r"\buuid\s*\.\s*uuid4\s*\(")),
]

warn_limit_without_order = re.compile(r"\bg\.[^\n]*\.limit\s*\(")
warn_has_order = re.compile(r"\.order\s*\(")
sample_call = re.compile(r"\.sample\s*\((?P<args>[^)]*)\)")

errors: list[str] = []
warnings: list[str] = []

for nb_path in targets:
    try:
        notebook = json.loads(nb_path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"{nb_path.relative_to(root)}: unreadable notebook ({exc})")
        continue

    for idx, cell in enumerate(notebook.get("cells", []), start=1):
        if cell.get("cell_type") != "code":
            continue
        src = "".join(cell.get("source", []))
        rel = nb_path.relative_to(root)

        for label, pattern in hard_patterns:
            if pattern.search(src):
                errors.append(f"{rel}:cell-{idx}: non-deterministic pattern `{label}`")

        for match in sample_call.finditer(src):
            args = match.group("args")
            if "random_state=" not in args.replace(" ", ""):
                errors.append(
                    f"{rel}:cell-{idx}: pandas sample() without random_state"
                )

        for line_no, line in enumerate(src.splitlines(), start=1):
            if warn_limit_without_order.search(line) and not warn_has_order.search(line):
                warnings.append(
                    f"{rel}:cell-{idx}:line-{line_no}: gremlin limit() without order() in same statement"
                )

if warnings:
    print(f"⚠️  Determinism sweep warnings: {len(warnings)}")
    for item in warnings:
        print(f"  - {item}")
else:
    print("✅ Determinism sweep warnings: 0")

if errors:
    print(f"❌ Determinism sweep errors: {len(errors)}")
    for item in errors:
        print(f"  - {item}")
    if strict_mode:
        raise SystemExit(1)
    print("ℹ️  Non-strict mode: keeping sweep as advisory to avoid breaking deterministic proof.")
else:
    print("✅ Determinism sweep errors: 0")
PY
