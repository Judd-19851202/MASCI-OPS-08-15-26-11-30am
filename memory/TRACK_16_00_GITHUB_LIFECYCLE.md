# TRACK 16.00 · GitHub Repository Lifecycle Hardening

**Status:** Implemented · regression-locked · deployment gate PASS

## Problem statement

Emergent's "Save to GitHub" mechanism creates a new dated snapshot
repository every time the operator presses Save. Every snapshot
inherits the prior repo's full source tree — including
`.github/workflows/production-health-probe.yml` with its `schedule:
*/15 * * * *` cron trigger. The result was that dozens of dated
snapshot repos under `Judd-19851202/MASCI-OPS-*` /
`Judd-19851202/MASCI-Plat-*` were independently probing
`mascidocs.com` every 15 minutes, and (because of an unrelated
job-level `if:` bug fixed in Track 15.97) emitting failure-email
notifications for "This check has no steps" on every PR run.

The customer was being asked to disable workflows by hand across
every dated snapshot repo. That was an unbounded recurring chore —
unacceptable under the Six Pillars.

## Permanent fix

The workflow now **self-silences** on every repository that is not the
active production source. The gate is the GitHub repository variable
`vars.ACTIVE_PRODUCTION_SOURCE`.

### Why this works automatically

GitHub repository **variables** and **secrets** live at the repository
settings level, *not* in the source tree. They are **never copied**
when a repo is forked, cloned, or snapshotted via the GitHub API.
Therefore:

| Event | Source repo | New repo | Variable on new repo |
|---|---|---|---|
| Emergent snapshots → `MASCI-OPS-7-15-26` | has `ACTIVE_PRODUCTION_SOURCE = MASCI-OPS-7-15-26` | created | **unset** |
| Workflow runs in new snapshot | (n/a) | gate sees variable unset | **classifies as snapshot · skips all probes** |

Result: a freshly-created snapshot is operationally silent from the
instant it exists. No customer action required. Ever.

### The lifecycle-gate step

The workflow's first step (`Resolve repository lifecycle role`) always
runs on every event and reads `vars.ACTIVE_PRODUCTION_SOURCE`:

* If the variable is **unset** → emit a `::notice::` + step-summary
  explaining the repo is a snapshot/inactive. No probes run. Exit 0.
  No failure email.
* If the variable **equals `${{ github.repository }}`** → set
  `is_active=true`. All subsequent probe steps gate on this.
* If the variable **is set but doesn't match** → emit a `::notice::`
  + step-summary indicating which repo IS the active source. Exit 0.

The probe steps (`GET /api/health`, `GET /api/version`,
`GET /api/admin/deployment-readiness`) are step-gated on
`steps.lifecycle.outputs.is_active == 'true'`. They literally cannot
run on a snapshot.

### How the active production repo gets bootstrapped

The active production source repository must have its
`ACTIVE_PRODUCTION_SOURCE` variable populated **once**, in:

> **Repository settings → Secrets and variables → Actions → Variables → New repository variable**
>
> * Name: `ACTIVE_PRODUCTION_SOURCE`
> * Value: `Judd-19851202/<name-of-active-repo>` (must match `github.repository` exactly)

That's the only manual step. Emergent Support can perform this once
on initial deploy; thereafter no rotation is needed unless the active
production source itself is moved to a different repository.

If the variable is forgotten on the active repo, the active repo's
workflow self-classifies as a snapshot — the probes don't run, but
nothing breaks. The operator sees a clear `::notice::` and a
step-summary instructing them to set the variable.

### One-time backfill for snapshots that pre-date this change

Snapshots created before Track 16.00 still carry the OLD workflow
shape (with the job-level `if:` or with no lifecycle gate). They keep
emailing until those workflows are disabled. The operator can
perform the one-time cleanup in two equivalent ways:

#### Option A — Via the GitHub UI (5 minutes total)

For each `MASCI-OPS-*` / `MASCI-Plat-*` snapshot that is NOT the
active production source:

1. Repo → **Actions** tab → select `production-health-probe`.
2. **⋯** menu → **Disable workflow**.

That stops cron immediately. PRs are no longer triggered. No more
emails from that snapshot.

#### Option B — Via the lifecycle-manager CLI

```bash
# 1. Generate a GitHub PAT with `repo` + `workflow` scope.
# 2. Set the env (use Emergent secrets or a shell-local file — never paste in chat).
export GITHUB_PAT='ghp_xxxx'
export GITHUB_OWNER='Judd-19851202'
export ACTIVE_PROD_REPO='Judd-19851202/MASCI-OPS-6-25-26-10m'

# 3. Preview what would change:
python3 /app/scripts/github_lifecycle_manager.py --dry-run

# 4. If the dry-run report looks right, apply:
python3 /app/scripts/github_lifecycle_manager.py --apply
#   (add --delete-noop to also delete production-health-probe-pr-noop.yml)
#   (add --strip-required-checks to also remove obsolete required status checks
#    from branch protection — requires PAT with administration:write scope)

# 5. Revoke the PAT immediately after.
```

The CLI never prints the token, never writes it to disk, never logs
it. It refuses to touch the active production repo (read-only
verification only). It only targets repos whose name matches the
MASCI/Plat/Ops snapshot pattern.

## Acceptance criteria — locked in regression

The following invariants are now enforced by
`/app/backend/tests/test_track_16_00_github_lifecycle_hardening.py`:

* No legacy `production-health-probe-pr-noop.yml` sibling.
* Workflow `name:` is exactly `production-health-probe`.
* All three triggers present (`schedule`, `workflow_dispatch`, `pull_request`).
* **No job-level `if:` on the `probe` job** (the empty-job failure pattern).
* The first step runs unconditionally (no `if:`), and is the lifecycle resolver.
* The lifecycle gate reads `vars.ACTIVE_PRODUCTION_SOURCE`.
* Every probe step gates on `steps.lifecycle.outputs.is_active == 'true'`.
* The authenticated readiness step is double-gated: active **AND**
  non-PR **AND** secrets present.
* No hard-coded credentials in the workflow.
* No `continue-on-error: true` swallowing failures.
* The lifecycle CLI exists, is executable, parses, exposes
  `--dry-run` + `--apply`, reads the token from env only (never CLI
  flag), never prints the raw token (only `<len chars · redacted>`),
  filters on the MASCI snapshot pattern, and **never modifies the
  active production repo**.

Any future regression that re-introduces the empty-job pattern, leaks
a token, or accidentally touches the active production repo is caught
by the deployment gate before deploy.

## Platform-level note

The only piece of this lifecycle problem that **cannot** be solved
inside MASCI is Emergent's own snapshot-creation behaviour. When
Emergent creates a new dated snapshot repository, it could
additionally:

1. Set `actions: disabled` on the new repository via
   `PATCH /repos/{owner}/{repo} { has_actions: false }`, or
2. Disable each workflow individually on the snapshot.

Either would make the lifecycle bullet-proof regardless of workflow
file contents. **This is outside MASCI's reach.** The workflow
self-silencing pattern documented here is the maximum that can be
guaranteed from the application side, and it is sufficient to
eliminate the customer-facing problem.

If Emergent ever implements snapshot-side Actions-disabling, this
workflow will continue to function unchanged — the two layers compose
cleanly.
