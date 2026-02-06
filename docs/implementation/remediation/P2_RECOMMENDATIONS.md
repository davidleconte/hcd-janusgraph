# P2 Recommendations - Medium-Term Improvements

**Created:** 2026-02-06  
**Status:** Documented (Not Yet Implemented)

---

## 1. Move HCD Tarball to Git LFS or Download-on-Build

### Current State
- `vendor/hcd-1.2.3-bin.tar.gz` is 91MB in the repository
- Total vendor directory is 191MB
- This increases clone time and repository size

### Recommendations

**Option A: Git LFS (Preferred)**
```bash
# Install Git LFS
brew install git-lfs  # macOS
git lfs install

# Track large files
git lfs track "*.tar.gz"
git lfs track "vendor/**/*.tar.gz"

# Add to .gitattributes
echo "vendor/**/*.tar.gz filter=lfs diff=lfs merge=lfs -text" >> .gitattributes
```

**Option B: Download on Build**
```bash
# Add to scripts/setup/download_hcd.sh
HCD_VERSION="1.2.3"
HCD_URL="https://your-artifact-repo/hcd-${HCD_VERSION}-bin.tar.gz"

if [ ! -f "vendor/hcd-${HCD_VERSION}-bin.tar.gz" ]; then
    curl -L -o "vendor/hcd-${HCD_VERSION}-bin.tar.gz" "$HCD_URL"
fi
```

### Impact
- Reduces repository size by ~91MB
- Faster clones for new developers
- Better git performance

---

## 2. TODO Items Tracking

### Active TODOs in Production Code

| File | Line | TODO | Priority |
|------|------|------|----------|
| `scripts/deployment/archive/load_production_data.py` | ~50 | Add JanusGraph verification when graph is loaded | Low (archived) |

### Note
Most TODOs are in archived or documentation files, which is acceptable. The single production TODO is in an archived script that's not actively used.

---

## 3. Consolidate Notebook Locations

### Current State
```
banking/notebooks/       # 11 production notebooks ✅
notebooks-exploratory/   # 4 exploratory notebooks
notebooks/               # ✅ REMOVED (was empty)
```

### Recommendation
Keep current structure but document clearly:

1. **Production notebooks**: `banking/notebooks/`
   - Tested, documented, maintained
   - Part of CI/CD pipeline
   
2. **Exploratory notebooks**: `notebooks-exploratory/`
   - Development/experimentation
   - Not part of official documentation
   - Consider moving to `docs/examples/` or archiving

### Future Action
- Add README.md to `notebooks-exploratory/` explaining its purpose
- Consider archiving if not actively used

---

## Implementation Timeline

| Item | Effort | Impact | Suggested Sprint |
|------|--------|--------|------------------|
| Git LFS for HCD | 2 hours | Medium | Next sprint |
| TODO cleanup | 1 hour | Low | Backlog |
| Notebook consolidation | 2 hours | Low | Backlog |

---

**Document Status:** Active  
**Last Updated:** 2026-02-06
