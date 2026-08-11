# PRODUCTION DEPLOYMENT CHECKLIST

Date: 2026-08-11
Status: hold until owner Save + SHA verification

## Required pre-deploy command

- Run `python3 scripts/deployment_gate.py`
- Confirm `scripts/deployment_gate.py` completes with a passing decision before any deployment event.

## Required preconditions

- Owner Save completed.
- Clean SHA identity verified against the pre-save fingerprint.
- Runtime health, frontend, backend, integration, bilingual, and trust suites green.
- Product Quality visual certification complete.

## Rollback

- Rollback immediately on login failure.
- Rollback immediately on dispatch workflow breakage.
- Rollback immediately on auth regression.
- Rollback immediately on data corruption.

## Operator safety doctrine

- No deploy with unexplained workspace artifacts.
- No deploy with hidden bypasses.
- No deploy with stale governance registers.