# TRACK 15.56 · GitHub Checks Certification

**Status:** ✅ Code changes complete in preview. Operator redeploy required for live GitHub effect.

## What the operator should verify after redeploy

| # | Action | Expected result |
|---|---|---|
| 1 | Push the two `.github/workflows/` files to GitHub `main`. | GitHub starts reading the new versions. |
| 2 | Open a draft PR against `main`. | `production-health-probe / probe` (from noop workflow) reports **green** within ~3 seconds. No emails fire. |
| 3 | Wait for the next cron tick (≤ 15 minutes). | Real `production-health-probe / probe` (from main workflow) runs on schedule, probes `mascidocs.com`, reports green (if production is up). |
| 4 | Click "Run workflow" manually on `production-health-probe` workflow. | Real probe runs on demand, reports green. |
| 5 | Inspect the workflow run for the PR. | Job: `probe` · Steps: 1 · Status: success · Duration: ~3 seconds. No "no steps" failures. |
| 6 | Send a deliberately bad probe (e.g. temporarily change `PROD_URL` secret to a nonexistent host). | Real probe fails → email fires → operator triages → revert secret. Confirms real outages still alert. |

## Items checked in preview (code review)

| Check | Result |
|---|:---:|
| `.github/workflows/production-health-probe.yml` triggers = schedule + workflow_dispatch only | ✅ |
| Same file has job-level `if:` guard | ✅ |
| New `.github/workflows/production-health-probe-pr-noop.yml` triggers only on `pull_request` | ✅ |
| Noop workflow's `name:` matches the real workflow's `name:` so branch-protection check identifiers stay consistent | ✅ |
| Noop workflow's job name (`probe`) matches the real workflow's job name | ✅ |
| Neither file references any backend code or environment variable beyond `PROD_URL` (production probe only) | ✅ |

## Phase 3 — Notification Noise Kill

After redeploy:
- **Workflow trigger:** real probe NO LONGER fires on `pull_request` because GitHub reads the corrected `on:` block. Noop fires on `pull_request` and intentionally passes. No false failures means no failure emails.
- **Required checks:** if pinned, the noop satisfies them. Operator may also un-pin the check; either path works.
- **Branch protection:** unchanged in this track; operator may inspect post-redeploy.
- **Repository notification settings:** unchanged. Operator can choose to mute "Actions" failure emails for `production-health-probe` workflow if any future runs flake — though they shouldn't.
- **Stale failed runs:** GitHub may continue to display the historical Run #193 and its predecessors as "Failure." These are immutable past-tense records and cannot be retroactively cleared. New PRs after redeploy will NOT add to this list.

## Phase 4 — Confirmations after redeploy

| # | Confirmation | How operator verifies |
|---|---|---|
| 1 | Manual workflow_dispatch passes | Click "Run workflow" in GitHub Actions UI · should complete in ≤ 30 s and report green |
| 2 | PR context does not invoke real probe | Open draft PR · observe only `probe` (noop) runs · no `verify-production.sh` invocation in logs |
| 3 | Scheduled path intact | Wait 15 min · observe one new cron-triggered run · should report green |
| 4 | Real production probes still test `mascidocs.com` | Inspect logs of a cron run · should see `tools/verify-production.sh` hitting all 5 endpoints |
| 5 | No empty "check has no steps" runs | Inspect any post-redeploy run · should always show ≥ 1 step |

## Real production outage detection — not weakened

The real `production-health-probe.yml` workflow is **unchanged in behavior** for schedule + workflow_dispatch events. It still runs `tools/verify-production.sh` against `mascidocs.com`. It still does a 30-second soak re-verify. It still emails on real failures.

The noop workflow runs ONLY on `pull_request` events and ONLY produces a single PASS step. It cannot hide a real outage because it never even tries to probe production on a PR.

## Final answers

| Q | A |
|---|---|
| Can production outages still alert? | **Yes.** The real probe is unchanged for schedule + workflow_dispatch paths. |
| Will Jaymn keep getting spammed? | **No.** Once the operator redeploys `.github/workflows/` to GitHub `main`, the PR-triggered "no steps" failures stop. |
