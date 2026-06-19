# TRACK 15.57 · Final Remediation

**Status:** Operator action required. Code changes complete in preview; container cannot push to GitHub.

## Operator action plan (exact steps)

### Step 1 — Push Track 15.56 to GitHub `main`

**Via Emergent UI (recommended):**
1. In the Emergent UI, click the **"Save to GitHub"** button.
2. Confirm the commit description includes Track 15.56 changes.
3. Wait for the GitHub push to complete (usually seconds).
4. Refresh the GitHub `main` branch page.

**Via terminal with `gh` CLI:**
```bash
git clone https://github.com/<MASCI-org>/<MASCI-repo>.git
cd <MASCI-repo>
# Copy the two files from Emergent into the local clone (manually
# fetch the file contents via the Emergent UI or use the Emergent
# "Download" feature for the .github/workflows/ folder).
git add .github/workflows/production-health-probe.yml \
        .github/workflows/production-health-probe-pr-noop.yml
git commit -m "TRACK 15.56 — stop production-health-probe PR alert storm"
git push origin main
```

### Step 2 — Verify both files reached `main`

```bash
gh api repos/<OWNER>/<REPO>/contents/.github/workflows/production-health-probe.yml?ref=main \
  | jq -r '.content' | base64 -d | md5sum
# Expected: 890f1447cdbd0e2747da3ca473e4ad12

gh api repos/<OWNER>/<REPO>/contents/.github/workflows/production-health-probe-pr-noop.yml?ref=main \
  | jq -r '.content' | base64 -d | md5sum
# Expected: 3b4eea0dde7ea0e5eb914b2a5d056935
```

If either md5 mismatches → push didn't include the expected file content → re-do Step 1.

### Step 3 — Open a draft PR to verify noop works

1. Create a trivial branch in the GitHub repo (e.g. add a blank line to README.md).
2. Open a PR against `main`.
3. Watch the GitHub Actions tab for the PR.
4. Expected: a single check `production-health-probe / probe` reports **green** in ~3 seconds.
5. No failure email should arrive.
6. Close the PR (without merging) if it was just for verification.

### Step 4 — Verify the real probe still fires on schedule

1. Wait ≤ 15 minutes for the next cron tick.
2. Visit `https://github.com/<MASCI-org>/<MASCI-repo>/actions/workflows/production-health-probe.yml`.
3. Confirm a recent run with trigger `schedule` reports **green** (mascidocs.com is healthy).

### Step 5 — (Optional) Inspect branch protection

`https://github.com/<MASCI-org>/<MASCI-repo>/settings/branches`

- If `production-health-probe / probe` is a required check: noop satisfies it. No action.
- If you'd prefer to simplify: remove `production-health-probe` from required checks. Either choice works.

## Worst-case rollback

If anything is wrong after the push:

```bash
# Revert the commit on main
git revert <commit-sha-from-step-1>
git push origin main
```

The repo returns to the pre-Track-15.56 state. No data is at risk (this is pure GitHub Actions configuration).

## Final 7 answers

| # | Question | Answer |
|---|---|---|
| 1 | Is Track 15.56 actually on GitHub `main`? | **UNVERIFIED from this container.** The Emergent preview environment has zero git remotes configured; it cannot push to or read from GitHub. Most likely answer: NO, the fix has not been pushed yet — that's why emails persist. Operator must verify via browser or `gh` CLI. |
| 2 | Which commit contains it? | In preview/local-git: c8cc6573 (latest auto-commit). On GitHub `main`: **UNKNOWN**. Operator can determine via `git log` on their local GitHub clone. |
| 3 | Which workflow generated Run #193? | **UNVERIFIED.** Operator can determine by clicking Run #193 in the GitHub Actions tab and inspecting the "Triggered by" + workflow path fields. Most-likely: the older version of `.github/workflows/production-health-probe.yml` on `main`. |
| 4 | Why did Run #193 fail? | The job-level `if:` guard skipped all steps on the `pull_request` event, producing "this check has no steps" — which GitHub renders as Failure. |
| 5 | Why is Jaymn still receiving emails? | Track 15.56's corrected files never reached GitHub `main` because the Emergent platform's auto-commit writes to local `/app/.git` only, not to the operator's GitHub. Without a manual "Save to GitHub" push, the fix is preview-only. |
| 6 | What exact action stops the emails? | Operator must push both `.github/workflows/production-health-probe.yml` and `.github/workflows/production-health-probe-pr-noop.yml` to GitHub `main` via the Emergent "Save to GitHub" button or via `git push origin main` from a credentialed terminal. After the push, emails stop. |
| 7 | GO / NO-GO | 🟡 **GO with required operator action.** Code is correct in preview. The fix cannot take effect until the operator pushes to GitHub. |

## What this audit cannot give you

- The actual contents of GitHub `main`.
- The actual list of required checks in branch protection.
- The actual workflow that fired Run #193.
- The actual trigger payload for Run #193.

For all of those, the operator must run the verification commands above. **This is the only honest answer Track 15.57 can deliver from inside the container.**
