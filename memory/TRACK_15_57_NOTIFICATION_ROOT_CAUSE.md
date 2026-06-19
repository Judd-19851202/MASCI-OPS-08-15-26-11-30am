# TRACK 15.57 · Notification Root Cause

**Status:** Best-effort attribution. Final attribution requires operator-side GitHub access.

## Why Jaymn is receiving dozens of emails after Track 15.56 was authored

The honest answer breaks down by the source of the emails:

### Source 1 — Workflow-run failures (most likely)

GitHub sends a failure email for any workflow run that exits non-zero on the default branch OR on a PR. If the workflow file currently on GitHub `main` is the **older version of `production-health-probe.yml`** that still includes `pull_request:` in `on:`, then every PR opened on that repo triggers:
- A workflow invocation.
- All steps skipped by the job-level `if:` guard.
- "No steps" failure state.
- Email to Jaymn.

This was Track 15.56's stated cause. It remains the highest-probability source of the email storm because:
- Track 15.56 wrote the corrected file in preview.
- The Emergent platform's auto-commits do NOT automatically push to the operator's GitHub `main`.
- Without an explicit "Save to GitHub" action by the operator, the corrected file never reaches `main`.

### Source 2 — Required-status-check timeout failures (possible)

If GitHub's branch-protection rule on `main` lists `production-health-probe / probe` as a required check, and no workflow on `main` provides that check on `pull_request` events, GitHub may report the missing check as a failure after a timeout.

This source becomes ZERO if Track 15.56's noop workflow reaches `main`. Until then, this source remains active.

### Source 3 — Stale `mascidocs.com` outage emails (very unlikely)

The real production probe runs every 15 min against `mascidocs.com`. If production were actually down, every cron tick would email Jaymn. Re-verified live in Track 15.54: `mascidocs.com/api/health/full` returns 200, and all 5 production-health-probe endpoints PASS. So production-outage emails are not the source.

### Source 4 — UptimeRobot or other external monitor (possible if configured)

If Jaymn has UptimeRobot or another external uptime monitor pointed at `/api/health/full` or any production endpoint, that monitor's emails would also feel like "GitHub email spam." Track 15.52 noted UptimeRobot was the original suspected source. The fact that GitHub mobile app shows specific Run #193 with workflow_path and trigger means **at least some of the emails ARE genuinely GitHub-Actions emails**, which rules out UptimeRobot as the sole source.

## Most likely root cause (best evidence-based attribution)

**Source 1 — workflow file on GitHub `main` is still the older version with `pull_request:` in its `on:` block.** The Emergent platform's auto-commit committed Track 15.56's fix to the local `/app/.git` only; it never reached the operator's GitHub repo because no `origin` remote is configured in this container.

This is the path with the strongest evidence:
1. Track 15.56 was authored in preview.
2. The preview file is verifiably correct (md5 `890f1447cdbd0e2747da3ca473e4ad12`).
3. The container has zero git remotes; the platform cannot have pushed to GitHub.
4. The operator's GitHub repo's `main` therefore still has the pre-Track-15.56 version of the file.
5. Every PR triggers the old workflow → "no steps" failure → email.

## Why GitHub doesn't "auto-receive" preview edits

The Emergent platform's auto-commit system writes to `/app/.git` (local). To push to the operator's GitHub repo, the operator must either:
- Use the Emergent UI's "Save to GitHub" button.
- Or, from their laptop with credentials: `cd <local-clone> && git pull && git push origin main`.

There is no automatic preview→GitHub push in the platform.

## Exact action that stops the emails

1. Operator opens the Emergent UI.
2. Clicks "Save to GitHub" (or equivalent push action).
3. Confirms the commit includes both `.github/workflows/production-health-probe.yml` and `.github/workflows/production-health-probe-pr-noop.yml`.
4. Verifies via browser: visit `https://github.com/<MASCI-org>/<MASCI-repo>/blob/main/.github/workflows/production-health-probe.yml` and confirm `on:` block contains only `schedule` + `workflow_dispatch`.

Within minutes of the push, future PRs stop triggering "no steps" failures, and the email storm stops.
