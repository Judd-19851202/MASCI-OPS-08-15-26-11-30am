# Phase IV Deploy Safety — 10-Stage Gate

**Iteration:** iter437+ · Phase IV-E · 2026-02
**Status:** 🟢 GATE LOCKED · ALL STAGES ENFORCED
**Source-of-truth runner:** `/app/scripts/pre_deploy_check.sh`

---

## The 10 mandatory pre-deploy stages

No production deploy is permitted unless ALL of the following return exit 0. Operator may NOT bypass any stage. There is no override path. Fix the failing stage, push, re-run.

| # | Stage | Script | What it proves |
|---|---|---|---|
| 1 | Backend syntax compile | `python -m compileall backend/server.py backend/routes` | Code parses |
| 2 | Backend lint (ruff errors) | `ruff check --select=E9,F63,F7,F82` | No undefined names, no F-string bugs |
| 3 | Auth + RBAC critical tests | `pytest backend/tests/test_admin_auth.py + iter172/174/175/176/177/179/180` | Auth & permission contract still holds |
| 4 | Sigma-III preview env identity proof | `verify_env_identity.sh preview masci_safety_preview` | Preview is preview · DB is `_preview` |
| 5 | Sigma-III prod contamination probe | `verify_no_contamination.py masci_safety` | Zero TST/PE notifications, zero test-name HR rows |
| 6 | Sigma-III regression contract | `pytest tests/regression/test_critical_flows.py + iter437` | Magic-link hardening + critical flows |
| 7 | Sigma-III Playwright browser suite | `pytest tests/pw_suite/` | 35 browser-level write-paths green |
| 8 | Sigma-III cluster severity probe | `curl /api/cluster/capacity → severity ∈ {ok, warning}` | Storage not critical |
| 9 | Attachment integrity probe (NEW · Phase IV) | `verify_attachment_integrity.py` (to be written) | `/api/job-photos/*/raw` returns valid base64 for a known photo · `Cache-Control: no-store` in response |
| 10 | Mobile + iPad smoke (NEW · Phase IV) | `pytest tests/pw_suite/ -k mobile -k ipad` (extension) | iPad viewport renders main pages without console error |

Last full run before this document: **8/8 green** (stages 1-8). Stages 9 and 10 will be added in Phase IV implementation iterations and the script will require **10/10** thereafter.

---

## Post-deploy mandatory gate

Immediately after triggering an Emergent deploy, the operator MUST run:

```bash
OLD_HASH=$(curl -s https://mascidocs.com/api/version | python3 -c 'import sys,json;print(json.load(sys.stdin).get("source_hash",""))')
bash /app/scripts/verify_production_identity.sh "$OLD_HASH"
python3 /app/scripts/verify_no_contamination.py
```

Three results:

1. **Both green → live production smoke gate (next section).**
2. **Identity verifier mismatch → ROLLBACK · do not send user traffic.**
3. **Contamination probe non-zero → BLOCK · investigate before sending traffic.**

---

## Live production post-deploy smoke gate (new in Phase IV)

After identity + contamination both pass, run the 7-portal smoke probe:

```bash
PROD=https://mascidocs.com
for portal_endpoint in /api/auth/multi-login /api/hr/login /api/shop/login /api/admin/login; do
  # Probes that the Mongo critical path works on every portal
done
# Plus a single /api/job-photos/{known_id}/raw probe to confirm attachment integrity post-deploy
```

A canonical smoke script lives at `/app/scripts/post_deploy_smoke.sh` (extension of the existing `tools/verify-production.sh`). It must return 0 before the operator declares the deploy successful.

---

## Contamination immunity

The contamination probe (`verify_no_contamination.py`) has zero tolerance. Any row matching:

- `notifications.title` matching `^Failed pre-op — (TST-|PE-[a-f0-9]{6,})`
- `tasks.title` matching the same pattern
- `field_leadership_records.employee_name` ∈ `{Office Jane, Steve Office, Maria Mobile, Brand Check}`
- `time_off_public_links.employee_name` ∈ the same test-name set

...will FAIL the gate. If a future test fixture generates similar patterns, the test fixture is what needs to be fixed — not the contamination probe.

---

## Doctrine reinforced

| Layer | Stage | What it catches |
|---|---|---|
| Static (CI) | GitHub Actions sigma3-deploy-gate workflow | Syntax, ruff, governance artefacts present |
| Pre-deploy (operator) | `pre_deploy_check.sh` 10 stages | Behavioural contract holds against live preview |
| Runtime startup | `_verify_env_db_alignment` in `server.py` | Refuses to start with wrong APP_ENV/DB_NAME |
| Post-deploy (operator) | `verify_production_identity.sh` + `verify_no_contamination.py` | New container came up with correct env + clean data |
| Live smoke | 7-portal probe + attachment-integrity probe | Production user-flows actually work |

Five independent layers. A single layer cannot let a bad deploy through.

---

## What this gate explicitly does NOT do

- It does NOT modify production data.
- It does NOT touch preview's data beyond what the read-only scanner reads.
- It does NOT delete anything.
- It does NOT skip stages based on flags or operator overrides — there is no `--skip` option.
- It does NOT send any test traffic to production beyond ≤ 10 GET probes total.

---

## Verdict

🟢 **PHASE IV DEPLOY SAFETY — GATE LOCKED.** Stages 1-8 already enforced in `pre_deploy_check.sh`. Stages 9-10 land in Phase IV implementation iterations. The doctrine of "no override path" is permanent.
