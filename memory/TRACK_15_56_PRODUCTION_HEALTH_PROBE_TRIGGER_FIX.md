# TRACK 15.56 · Production Health Probe Trigger Fix

**Status:** ✅ Fix shipped to preview · operator must redeploy `.github/` to GitHub `main`.

## Files involved

### `.github/workflows/production-health-probe.yml` (real probe · already clean in preview)

```yaml
on:
  schedule:
    - cron: "*/15 * * * *"   # every 15 minutes
  workflow_dispatch: {}      # manual "Run workflow" button

jobs:
  probe:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    if: github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'
    steps:
      - uses: actions/checkout@v4
      - name: Run verify-production.sh
        env:
          PROD_URL: ${{ secrets.PROD_URL || 'https://mascidocs.com' }}
          SOAK_SECONDS: "30"
        run: |
          chmod +x ./tools/verify-production.sh
          ./tools/verify-production.sh 2>&1 | tee /tmp/probe.log
          exit "${PIPESTATUS[0]}"
      - if: failure()
        run: |
          # publish failure summary to GITHUB_STEP_SUMMARY
          ...
```

Key properties:
- Triggers: `schedule` + `workflow_dispatch` ONLY. No `pull_request`. No `push`.
- Job-level `if:` guard rejects any event other than schedule or manual dispatch (belt-and-suspenders).
- Real production probes only fire on the cron tick or when manually invoked.

### `.github/workflows/production-health-probe-pr-noop.yml` (NEW · PR-safe noop)

Created in this track. Properties:
- Triggers: `pull_request` ONLY.
- Has the same `name: production-health-probe` and job `name: probe` so any branch protection rule pinned to `production-health-probe / probe` finds a passing run on PRs.
- Single PASS step — no real production probe is fired.
- Times out in 1 minute.

## Operator redeploy required

These changes live in the preview branch. The operator must push the `.github/workflows/` directory to GitHub `main` for the fix to take effect.

```bash
# Suggested steps for the operator
git add .github/workflows/production-health-probe.yml \
        .github/workflows/production-health-probe-pr-noop.yml
git commit -m "TRACK 15.56 — stop production-health-probe PR alert storm"
git push origin main
```

After the push:
- GitHub will use the new version of `production-health-probe.yml` for `schedule` + `workflow_dispatch` events.
- GitHub will use the new `production-health-probe-pr-noop.yml` for `pull_request` events.
- The "Failure · 3s · no steps" failure mode disappears.
- Email storm stops.

## Branch protection follow-up (operator choice)

If `production-health-probe` is currently listed as a **required status check** for PRs:
- After the fix is deployed, GitHub will get a PASS from the noop workflow on every PR.
- No branch-protection-rule change is strictly required.
- Optional: simplify by removing `production-health-probe` from required-check list. Either choice works.

If `production-health-probe` is NOT a required status check:
- The noop is harmless overhead (runs in ~3 seconds per PR).
- Optional: delete the noop file. Either choice works.

## Hard-rule compliance

| Rule | Status |
|---|:---:|
| Remove `pull_request` from real probe | ✅ (already removed in preview · waiting on redeploy) |
| Remove `push` from real probe | ✅ |
| Keep only `schedule` + `workflow_dispatch` | ✅ |
| Job-level guard `if: github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'` | ✅ |
| PR-safe noop check to satisfy branch protection | ✅ (added in this track) |
| Do not let production probe fail PRs | ✅ |

## Smallest safe fix

Two file deltas:
1. (Already done) `.github/workflows/production-health-probe.yml` triggers narrowed to `schedule` + `workflow_dispatch`.
2. (This track) `.github/workflows/production-health-probe-pr-noop.yml` created.

No backend code, no env vars, no schema, no other workflow files touched.
