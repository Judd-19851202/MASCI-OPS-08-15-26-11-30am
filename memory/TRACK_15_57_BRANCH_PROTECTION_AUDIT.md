# TRACK 15.57 · Branch Protection Audit

**Status:** ⚠ **UNVERIFIED from inside this container.** Branch protection rules live on the GitHub repository settings page; this container has no GitHub credentials.

## What the operator can verify

### Browser (1 minute)

1. https://github.com/<MASCI-org>/<MASCI-repo>/settings/branches
2. Find the rule for the `main` branch (or default branch).
3. Inspect "Require status checks to pass before merging" → "Status checks that are required."
4. **Is `production-health-probe / probe` (or any string containing `production-health-probe`) listed?**

### Operator terminal with `GH_TOKEN` (30 seconds)

```bash
gh api repos/<OWNER>/<REPO>/branches/main/protection 2>/dev/null \
  | jq '.required_status_checks.checks // .required_status_checks.contexts'
```

## Decision tree based on operator-side result

| Result | Interpretation | Operator action |
|---|---|---|
| `production-health-probe / probe` is NOT in required checks | Track 15.56 noop is unnecessary; emails are coming from the OLDER `production-health-probe.yml` on `main`. | Push the two corrected files in preview to `main`. |
| `production-health-probe / probe` IS in required checks AND the noop workflow exists on `main` | Branch protection is being satisfied; emails should stop on next PR. If they don't, GitHub may be holding stale cached check states; close & reopen the PR or rebase. | None — wait one PR cycle. |
| `production-health-probe / probe` IS in required checks AND the noop workflow does NOT exist on `main` | Branch protection waits forever → stale "no steps" failure → email storm. | Push the noop file to `main`. |
| Branch protection itself does not require this check | The emails come from the workflow run failures (Hypothesis A in `WORKFLOW_TRIGGER_AUDIT.md`), not from required-check timeouts. | Push the corrected `production-health-probe.yml` to `main`. |

## Is GitHub requiring `production-health-probe / probe` on PRs?

**UNVERIFIED.** This question CANNOT be answered from inside the Emergent preview container.

The operator MUST inspect their own GitHub repo settings.

## Hard-rule compliance for this section

- ✅ No assumptions about GitHub state.
- ✅ No speculation about which branch protection rules exist.
- ✅ UNVERIFIED items explicitly labeled.
- ✅ Operator action paths provided for both possible answers.
