# Codex P2 Closeout Rollback/Forward Plan

- Date: 2026-02-20
- Scope: P2 implementation and deterministic-proof closeout
- Milestone tag target: `p2-complete-2026-02-20`

## Commit Sequence

1. `a7558f9`  
   `feat(performance): add deterministic SLO baseline gate and CI enforcement`
2. `837718d`  
   `feat(perf): add startup budget gate and performance governance runbook`
3. `1a9ed38`  
   `docs(ops): implement deterministic gate alert-to-runbook mapping (P2-004)`
4. `HEAD` at closeout time  
   `docs(status): refresh deterministic proof evidence and add P2 rollback/forward plan`

## Rollback Plan

### Full rollback to pre-P2 state

Use commit `9734d93` (state before P2 implementation):

```bash
git checkout 9734d93
```

### Incremental rollback by milestone

1. Undo closeout docs only:

```bash
git revert HEAD
```

2. Undo P2-004 docs/ops mapping:

```bash
git revert 1a9ed38
```

3. Undo P2-002/P2-003 startup gate and runbook:

```bash
git revert 837718d
```

4. Undo P2-001 runtime SLO gate:

```bash
git revert a7558f9
```

## Forward Plan

To re-apply from pre-P2 (`9734d93`) in deterministic order:

```bash
git cherry-pick a7558f9
git cherry-pick 837718d
git cherry-pick 1a9ed38
git cherry-pick <closeout-commit-sha-from-git-log>
```

## Post-Operation Validation

After rollback or forward-apply, run:

```bash
PODMAN_CONNECTION=podman-wxd-root bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh \
  --status-report exports/deterministic-status.json
```

Expected deterministic verdict: `exit_code=0`, `15/15` notebook `PASS`.
