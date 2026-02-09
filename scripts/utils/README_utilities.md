# Utility Scripts

Python utility scripts for maintenance and automation tasks.

## Contents

| Script | Description |
|--------|-------------|
| `fix_banking_notebooks.py` | Fix and update banking notebooks (connection strings, imports) |

## Usage

All scripts require the conda environment to be active:

```bash
# Activate conda environment first
conda activate janusgraph-analysis

# Run utility script
python scripts/utilities/fix_banking_notebooks.py
```

## Adding New Utilities

When adding new utility scripts:
1. Place Python scripts in this directory
2. Add docstring with usage instructions
3. Update this README
4. Ensure script works with Python 3.11

---

**Co-Authored-By:** David Leconte <team@example.com>
