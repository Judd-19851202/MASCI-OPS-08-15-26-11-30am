# TRACK 15.57 · GitHub Main Verification

**Status:** ⚠ **UNVERIFIABLE from inside this container.** Direct inspection of GitHub `main` is not possible.

## Why this is the honest answer

This container has **no `origin` remote configured**:

```
$ git remote -v
(no output — zero remotes)

$ git ls-remote --heads origin
fatal: 'origin' does not appear to be a git repository
```

The Emergent platform commits to a **local-only** `/app/.git`. Pushing to the operator's GitHub repo is performed via the Emergent UI's "Save to GitHub" button — a manual action by the operator, NOT an automatic platform behavior.

This means:
- I cannot read the file contents on GitHub `main`.
- I cannot read the list of commits on GitHub `main`.
- I cannot read GitHub-side branch-protection rules.
- I cannot directly verify whether Track 15.56's changes ever reached GitHub.

Anyone certifying that "the fix is on `main`" without a GitHub-side check is certifying by inference, which violates Track 15.57's hard-rule "no certification by inference."

## What CAN be verified from this container

| # | Item | Evidence |
|---|---|---|
| 1 | The corrected file `production-health-probe.yml` exists in preview | `grep -nE "^on:" /app/.github/workflows/production-health-probe.yml` → only `schedule` and `workflow_dispatch` listed. No `pull_request`, no `push`. |
| 2 | The new file `production-health-probe-pr-noop.yml` exists in preview | Live file present; `name: production-health-probe` and job `name: probe`. |
| 3 | File hashes for operator-side comparison | `production-health-probe.yml` md5 = `890f1447cdbd0e2747da3ca473e4ad12`<br>`production-health-probe-pr-noop.yml` md5 = `3b4eea0dde7ea0e5eb914b2a5d056935` |
| 4 | Local commits touched these files | c8cc6573 (latest), caddbed3, e1801404 — all Emergent platform auto-commits to LOCAL git, NOT pushed to GitHub by the platform |

## What the operator must verify manually

The operator has two ways to settle the question:

### Option A — Browser (30 seconds)

1. Open https://github.com/<MASCI-org>/<MASCI-repo>/blob/main/.github/workflows/production-health-probe.yml
2. Confirm the `on:` block contains ONLY `schedule` and `workflow_dispatch`. **If it still contains `pull_request:`, Track 15.56 has not reached `main` yet.**
3. Open https://github.com/<MASCI-org>/<MASCI-repo>/blob/main/.github/workflows/production-health-probe-pr-noop.yml — confirm the file exists. **If 404, Track 15.56 has not reached `main`.**

### Option B — Operator terminal with `GH_TOKEN` (1 minute)

```bash
# Confirm production-health-probe.yml on main has NO pull_request trigger
gh api repos/<OWNER>/<REPO>/contents/.github/workflows/production-health-probe.yml?ref=main \
  | jq -r '.content' | base64 -d | grep -E "^on:|pull_request|push:|schedule|workflow_dispatch"

# Confirm production-health-probe-pr-noop.yml exists on main
gh api repos/<OWNER>/<REPO>/contents/.github/workflows/production-health-probe-pr-noop.yml?ref=main \
  | jq -r '.sha'
# Should print a SHA. If "404 Not Found", file is missing.

# Compare md5s
gh api repos/<OWNER>/<REPO>/contents/.github/workflows/production-health-probe.yml?ref=main \
  | jq -r '.content' | base64 -d | md5sum
# Expected: 890f1447cdbd0e2747da3ca473e4ad12

gh api repos/<OWNER>/<REPO>/contents/.github/workflows/production-health-probe-pr-noop.yml?ref=main \
  | jq -r '.content' | base64 -d | md5sum
# Expected: 3b4eea0dde7ea0e5eb914b2a5d056935
```

If both md5s match, GitHub `main` matches preview and Track 15.56 is live.
If either md5 differs (or file is 404), Track 15.56 has **not** reached `main`.

## Most likely scenario (evidence-based reasoning, not certification)

Given that Jaymn is **still receiving failure emails after Track 15.56 was authored**:
- It is **highly likely** the operator never clicked "Save to GitHub" after Track 15.56 was authored, OR
- "Save to GitHub" was invoked but the operator's GitHub repo's `main` branch is protected and the platform's PR/merge step is still pending, OR
- The platform sync excluded `.github/workflows/` from its push (some Emergent configurations skip top-level dotfiles).

Without the operator's GitHub credentials we cannot evidence which of these is true.

## Conclusion

**Track 15.56 is verifiably correct in preview** (md5 hashes captured above; file contents inspected directly).
**Track 15.56's GitHub-main status is UNVERIFIED** from this container.
**The operator must run one of the two verification options above** to determine GitHub-side truth.

If GitHub-main does NOT match, the operator must explicitly push these two files to GitHub `main` (Emergent "Save to GitHub" or `git push origin main` from their laptop).
