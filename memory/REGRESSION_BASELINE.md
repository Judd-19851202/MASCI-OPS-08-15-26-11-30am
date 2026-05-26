# MASCI Operational Certification — Regression Baseline

**Locked:** 2026-05-26 (P0 directive · Operational Certification phase)
**Suite path:** `/app/backend/tests/regression/test_critical_flows.py`
**Target pod:** `safety-audit-mobile-1.preview.emergentagent.com`
**Database under test:** `masci_safety_preview` · `APP_ENV=preview`
**Production database (`masci_safety`):** UNTOUCHED — suite refuses to run unless `app_env=preview` and `db_name` ends in `_preview` (enforced by `conftest.env_identity`).

---

## 1. Result — GREEN

```
41 passed in 9.30s   (run 1)
41 passed in 9.00s   (run 2)
41 passed in 9.13s   (run 3)
```

Three consecutive runs, no flakes. Zero skipped, zero xfails.

---

## 2. Coverage Map (41 assertions across 9 contracts)

| # | Contract                              | Tests | Notes                                                              |
|---|---------------------------------------|-------|--------------------------------------------------------------------|
| 1 | Environment separation guardrail      | 2     | `/api/version` must report `app_env=preview` + `db_name=*_preview` |
| 2 | Service health                        | 1     | `/api/health` returns `{ok:true, service:"masci-hub"}`             |
| 3 | Super-admin multi-login               | 3     | 7 portal tokens minted, super-admin flags correct, session token   |
| 4 | Per-portal `/me` reachability         | 7     | admin · pm · shop · hr · safety · dispatch · field-leadership      |
| 5 | Cross-portal token isolation          | 3     | HR≠Admin · PM≠HR · random token rejected                           |
| 6 | Critical list endpoints (admin)       | 8     | jobs, daily-reports, incidents, meetings, inspections, JHAs, EI×2  |
| 7 | HR performance SLA (`<3s` p99)        | 3     | time-verification · driver-qual · training-records                 |
| 8 | Public-vs-protected enforcement       | 12    | Every protected list returns 401 without a token                   |
| 9 | Reference data presence               | 2     | `/api/employees` ≥10 · `/api/admin/jobs` is a list                 |

---

## 3. Performance Snapshot — 2026-05-26

All values are **wall-clock** against the live preview pod (3 consecutive curls):

| Endpoint                                          | t1 (ms) | t2 (ms) | t3 (ms) | Budget |
|---------------------------------------------------|--------:|--------:|--------:|-------:|
| `/api/health`                                     |     127 |      88 |     104 |  1 000 |
| `/api/version`                                    |     101 |     102 |     101 |  1 000 |
| `/api/admin/jobs`                                 |     323 |     335 |     315 |  3 000 |
| `/api/daily-reports`                              |     228 |     217 |     248 |  3 000 |
| `/api/hr/time-verification`                       |     283 |     260 |     277 |  3 000 |
| `/api/hr/driver-qualification/dashboard`          |     449 |     455 |     455 |  3 000 |
| `/api/hr/training-records`                        |     283 |     339 |     283 |  3 000 |
| `/api/employees`                                  |     720 |     692 |     716 |  3 000 |

Handoff reported HR endpoints used to take **10 000+ ms** (timeouts). After the projection fixes in `routes/hr_portal.py`, the p99 is now **<500 ms** — a **~20×** improvement.

---

## 4. Guardrails Verified

1. **DB crossover impossible from suite.** `conftest.env_identity` fails the run if the pod is not on `*_preview`. Even if someone redeploys this code into prod, pytest will refuse with `returncode=3` before any HTTP call.
2. **No write path is exercised.** Every assertion is read-only — the suite cannot leave artifacts in the preview DB and cannot corrupt the upcoming restore drill.
3. **Cross-portal HMAC isolation enforced.** HR/PM tokens cannot be substituted into another portal's header; all three negative-path tests return 401.
4. **Auth enforcement on every protected list.** 12 endpoints all return 401 without a token (no silent admin fallback).

---

## 5. How to run

```bash
# From anywhere
cd /app/backend && python3 -m pytest tests/regression/test_critical_flows.py -v

# Quick green-bar check
cd /app/backend && python3 -m pytest tests/regression/test_critical_flows.py -q
```

Pre-requisite env (already present in `/app/backend/.env`):

```
APP_ENV=preview
DB_NAME=masci_safety_preview
SUPER_ADMIN_EMAIL=jaymn.judd@mascigc.com
SUPER_ADMIN_BOOTSTRAP_PASSWORD=Maddix123!
```

`REACT_APP_BACKEND_URL` is read from `/app/frontend/.env`.

The super-admin row in `user_directory` is **idempotently bootstrapped** by the backend at startup (`_bootstrap_user_directory()` in `server.py`), so the suite can run even against a freshly-restored empty preview DB.

---

## 6. What's intentionally NOT covered (deferred to next phase)

| Gap                                              | Reason                                                   | Owner / Next Phase |
|--------------------------------------------------|----------------------------------------------------------|---------------------|
| Write paths (create/update/delete)               | Code freeze — no contamination during certification      | Phase 2 of suite    |
| Frontend route smoke tests                       | Playwright not yet wired                                 | Playwright phase    |
| Photo / R2 attachment integrity                  | Requires real restored data                              | Post-restore drill  |
| Role access matrix (12 roles × N endpoints)      | Separate role-cert sweep                                 | Role Cert phase     |
| Backup manifest hash checks                      | Belongs in restore-drill harness                         | Restore drill       |
| MFA enroll/verify round-trip                     | Existing `test_iter375_mfa_totp.py` covers it            | Already covered     |

---

## 7. Failure runbook

If this suite ever goes red, follow this triage:

1. **`test_env_identity_*` fails** → STOP. The pod may have been pointed at prod. Check `/api/version` and `/app/backend/.env`. Do NOT continue with any other recovery action until this is green.
2. **`test_multi_login_*` fails** → super-admin bootstrap broken. Check backend logs for `[directory]` lines and `SUPER_ADMIN_*` env vars.
3. **`test_portal_me_*` fails** → multi-login mints a token that the portal's auth gate rejects. Likely cause: portal HMAC secret rotated without restart or `ADMIN_SESSION_EPOCH` was bumped without a fresh login.
4. **`test_hr_perf_budget` fails** → DB regression. Check whether projection (excluding base64 fields) was reverted in `routes/hr_portal.py` and whether Atlas latency spiked.
5. **`test_no_auth_protected_endpoints_401` fails** → an auth gate was removed. Treat as **P0 security incident**.
6. **`test_cross_portal_*` fails** → token isolation broken. Treat as **P0 security incident**.
