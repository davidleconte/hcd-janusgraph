# dependency-abi-compat-guard

## Purpose
Prevent and repair dependency ABI/runtime compatibility breaks.

## Trigger when
- Import-time errors mention binary/ABI mismatch.
- `numpy/pandas/sklearn` stack fails after package updates.
- PyTorch/ML ecosystem imports degrade after dependency changes.

## Workflow
1. Capture versions:
`python -c "import numpy, pandas, sklearn; ..."`
2. Detect mismatch signature:
`ValueError: numpy.dtype size changed ...`
3. Reinstall compatible pinned set in env via `uv`:
`uv pip install --force-reinstall <compatible-versions>`
4. Verify imports and targeted tests.
5. Record final versions in remediation notes.

## Outputs
- Stable import/runtime compatibility
- Version set used to restore compatibility

## Guardrails
- Use `uv` only.
- Avoid ad-hoc mixed package managers in the same env.

