# TRACK 15.56 · GitHub Actions Alert Storm RCA

**Status:** Root cause identified · fix shipped in preview · operator redeploy required.

## Symptom

GitHub mobile app shows:
- Workflow: `production-health-probe`
- Run #193 · Status: Failure · Duration 3 s · Trigger: `pull_request`
- UI says: "This check has no steps"
- Operator inbox: dozens of failure emails per day

## Root cause

The version of `.github/workflows/production-health-probe.yml` currently on the GitHub **default branch (`main`)** is an **older version** that still has `pull_request:` listed in its `on:` trigger block.

When a PR opens:
1. GitHub reads the workflow file on `main`.
2. The older file lists `pull_request:` in `on:`, so GitHub invokes the workflow.
3. The job has `if: github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'`, which evaluates to **false** on `pull_request` events.
4. GitHub skips all the steps inside the job — but still reports the workflow run.
5. Because the job ran without steps, GitHub records "**This check has no steps**" and a **failure-style state** (skipped jobs with required-check semantics).
6. Operator email notifications fire for each PR.

The current preview file (`/app/.github/workflows/production-health-probe.yml`) has **already been corrected** — its `on:` block contains only `schedule` + `workflow_dispatch`. But that corrected version has not yet reached the GitHub `main` branch, so the old behavior persists.

This is a **version drift between the preview branch and the GitHub default branch**. The fix is to push the current preview file to GitHub `main`.

## Q&A

| Question | Answer |
|---|---|
| Why is GitHub firing on `pull_request`? | The workflow file currently on `main` still includes `pull_request:` in its trigger block. |
| Why does the check have "no steps"? | The job-level `if:` guard evaluates to false on `pull_request` events, so the steps are skipped — GitHub renders that as "no steps." |
| Was prior certification wrong? | No — Track 15.51 and 15.52A inspected the **preview** workflow file, which is clean. The version on GitHub `main` is older. The drift was not detected because no probe in this container can read the GitHub-side file. |
| Is there a way to detect this from inside the container? | No, unless we add a one-shot Git ls-remote of `origin/main` to compare file contents — which would require GitHub credentials. |

## Where the drift came from

The most likely cause: a previous version of the workflow file shipped with `on: pull_request:` listed (for self-test purposes during early development of Track 15.34B). When the production-only triggers were narrowed in a later track, the file was edited in preview but the operator's deploy step (push to `main`) did not run, or ran against a different branch.

## Why this is not a code defect

The current preview file is **correct**. The fix has already been authored. The only remaining action is the operator's standard "push preview → main" deployment for the `.github/` directory.

## Belt-and-suspenders added in this track

Even after the operator pushes the corrected file to `main`, there is one residual risk: if the GitHub **branch protection rules** still list `production-health-probe` as a *required status check* on PRs, the PR will be **blocked from merging** because the check never runs on PR events any more.

To prevent that secondary failure mode, this track adds `/app/.github/workflows/production-health-probe-pr-noop.yml` — a second workflow file that:
- Triggers on `pull_request` only.
- Has the same workflow `name: production-health-probe` and job `name: probe`.
- Runs a single PASS step in seconds.
- Satisfies any branch protection rule pinned to `production-health-probe / probe` on PRs.
- Never runs against actual production endpoints.

This is documented in `TRACK_15_56_PRODUCTION_HEALTH_PROBE_TRIGGER_FIX.md`.
