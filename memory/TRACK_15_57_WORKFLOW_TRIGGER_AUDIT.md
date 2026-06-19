# TRACK 15.57 · Workflow Trigger Audit

**Status:** Trigger audit performed against **preview** files only. GitHub-side files are **UNVERIFIED** (no remote credentials in container).

## Workflows that exist in preview

| File | `name:` | Triggers (`on:`) | Job `if:` guard |
|---|---|---|---|
| `.github/workflows/production-health-probe.yml` | `production-health-probe` | `schedule: cron */15 * * * *` + `workflow_dispatch: {}` | `github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'` |
| `.github/workflows/production-health-probe-pr-noop.yml` | `production-health-probe` | `pull_request: {}` | (no `if:` guard — runs every PR · single PASS step) |
| `.github/workflows/sigma3-deploy-gate.yml` | `sigma3-deploy-gate` | `push: main/master` + `workflow_dispatch` | (different check name; not implicated) |
| `.github/workflows/ci.yml` | `MASCI Hub CI Gate` | push/pull_request | (different check name; not implicated) |

## Reusable-workflow references

None. No `uses: ./.github/workflows/...` cross-references, no `workflow_call` triggers, no reusable composites.

## Why Run #193 was reported as "Triggered via pull_request · This check has no steps"

**Two possible explanations, both consistent with the operator-side report:**

### Hypothesis A — GitHub `main` has an OLDER version of `production-health-probe.yml`

This was Track 15.56's stated root cause. If the file on GitHub `main` still contains `pull_request:` in its `on:` block, then:
1. GitHub sees `pull_request:` and invokes the workflow on PR events.
2. The job-level `if:` guard (which IS present on `main`'s older version too, per Track 15.34B) rejects `pull_request`.
3. All steps are skipped.
4. GitHub renders "This check has no steps" and (depending on rendering) "Failure" or "Skipped."
5. Operator email notifications fire.

This hypothesis can be **proven true** by the operator running the verification commands in `TRACK_15_57_GITHUB_MAIN_VERIFICATION.md`.

### Hypothesis B — A required-status-check rule causes GitHub to invoke a stale check context

If GitHub repo branch-protection rules list `production-health-probe / probe` as a required check, and the workflow with that check name doesn't run on `pull_request`, GitHub will continue to wait for the check and may report it as "Failure · no steps" after a timeout. This is a known GitHub behavior with stale required-check pinning.

This hypothesis can be **proven** by the operator inspecting branch-protection rules (see `TRACK_15_57_BRANCH_PROTECTION_AUDIT.md`).

## Run #193 — exact trigger source

**Unverifiable from inside this container.** GitHub provides this information in the run's detail page (URL pattern `https://github.com/<owner>/<repo>/actions/runs/<id>`). The operator can paste Run #193's URL into the next track for definitive identification.

Likely candidates:
- The OLDER version of `production-health-probe.yml` still on `main`, fired by GitHub's pull_request event.
- OR a stale branch-protection check timeout reporting against a workflow that doesn't run on PRs.

## Verdict

Trigger audit is complete in preview. Final root cause attribution requires operator-side GitHub access. See `TRACK_15_57_FINAL_REMEDIATION.md` for the operator action sequence.
