# Deploy Checks · MASCI Platform

This directory hosts **stabilization-safe pre-deploy hooks** for the MASCI Operations Platform.

## Scope (operator-mandated · iter321)

The hooks here are intentionally narrow:
- **Anti-drift protection only.**
- **One hook = one focused check.**
- No screenshot testing, no visual diff, no giant CI, no style bureaucracy, no unrelated tests.

## Current hooks

### `run_family_contract.sh`
Runs `pytest test_platform_family_contract.py` — the single read-only invariant suite that locks the Platform Family visual contract across HR · Safety · FL · Field · Shop · QA/QC. Exits non-zero on any contract violation. ~10 lines of bash.

**Usage** — wire into your deploy pipeline before pushing to production / before mascidocs.com redeploy:

```bash
/app/.deploy_checks/run_family_contract.sh
```

Pass → safe to deploy.
Fail → fix the violation before deploying (see the failed assertion to identify which hub drifted and what anchor was missed).

## What this directory MUST NOT become

- ❌ A general-purpose CI runner
- ❌ A screenshot regression system
- ❌ A pixel-diff farm
- ❌ A style enforcement tower
- ❌ A place to put unrelated tests

Every hook added here must trace back to a specific stabilization concern. If it doesn't, it doesn't belong.
