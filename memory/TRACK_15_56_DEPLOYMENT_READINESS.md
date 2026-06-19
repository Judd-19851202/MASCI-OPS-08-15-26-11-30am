# TRACK 15.56 · Deployment Readiness

**Status:** 🟢 GO — fix is in preview, awaiting operator redeploy.

## What ships

Two files under `/app/.github/workflows/`:

1. `production-health-probe.yml` (already correct in preview — version drift with `main` is the root cause).
2. `production-health-probe-pr-noop.yml` (NEW in this track — PR-safe noop).

## Backend / DB impact

**Zero.** No code, no env, no schema, no migration.

## Frontend impact

**Zero.** Pure GitHub Actions configuration.

## Rollout sequence (operator)

```bash
# 1. Stage both workflow files.
git add .github/workflows/production-health-probe.yml \
        .github/workflows/production-health-probe-pr-noop.yml

# 2. Commit + push to GitHub main.
git commit -m "TRACK 15.56 — stop production-health-probe PR alert storm"
git push origin main
```

## Rollback

If anything goes wrong, simply delete the noop workflow file and `git revert` the commit. The previous "no steps" failure mode would return, but no data is at risk.

## Confidence checks performed in this track

| Check | Result |
|---|:---:|
| Real probe `on:` block contains only `schedule` + `workflow_dispatch` | ✅ |
| Job-level `if:` guard present as belt-and-suspenders | ✅ |
| Noop workflow created with `name: production-health-probe` + job `name: probe` | ✅ |
| Noop file syntax-valid YAML | ✅ (basic YAML structure correct) |
| No additional files touched in `.github/workflows/` | ✅ |
| `mascidocs.com/api/health/full` still 200 (production unaffected) | ✅ (re-checked Track 15.54) |

## Open follow-ups (operator-side, non-blocking)

1. Push the changes to GitHub `main`.
2. (Optional) Inspect repository branch-protection rules to decide whether `production-health-probe` should remain a required status check on PRs. Either keep it (noop satisfies it) or remove it (one less check to pin) — both work.
3. (Optional) Confirm no other workflows in any other branch are also referencing `pull_request` triggers for `production-health-probe`.

## GO / NO-GO

🟢 **GO.** Safe to redeploy. Frontend-zero · backend-zero · data-zero impact. Worst case if rollback needed: 30-second revert, no data loss possible.
