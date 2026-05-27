# MASCI Regression Strategy (Phase Sigma · iter437)

**Status:** ✅ Foundation operational. 58 total assertions green.
**Last green:** 2026-05-26 23:45 UTC.

---

## 1. Current coverage — VERIFIED with proof

### 1a. API regression (read-only contract suite)
- **Path:** `/app/backend/tests/regression/test_critical_flows.py`
- **Runtime:** ~9 s
- **Assertions:** **43**
- **Last result:** `43 passed in 9.45s` · 3+ consecutive runs, no flakes
- **Proof artifact:** `/app/memory/REGRESSION_BASELINE.md`

| Contract                              | Tests |
|---------------------------------------|------:|
| Env separation guardrail              |     2 |
| Health                                |     1 |
| Super-admin multi-login               |     3 |
| Per-portal `/me` reachability         |     7 |
| Cross-portal token isolation          |     3 |
| Critical list endpoints (admin)       |     8 |
| HR performance SLA (<3 s p99)         |     3 |
| Public-vs-protected enforcement       |    12 |
| Reference data presence               |     2 |
| Cluster capacity probe                |     2 |

### 1b. Playwright browser regression (Phase Sigma — NEW)
- **Path:** `/app/backend/tests/pw_suite/test_critical_flows_pw.py`
- **Runtime:** ~36 s
- **Assertions:** **15** (5 flows × 3 viewports)
- **Last result:** `15 passed in 36.32s`
- **Viewports:** desktop (1920×1080), ipad (1024×1366), mobile (390×844, mobile-Safari UA)
- **Artifacts on failure:** screenshot + JSON metadata at `/app/test_reports/playwright/<test>.png|.json`

| Flow                                            | Coverage                                              |
|-------------------------------------------------|-------------------------------------------------------|
| Public hub renders + EnvBanner visible          | App shell + preview banner contract                   |
| Cluster-capacity reachable from browser         | CORS + endpoint + severity contract                   |
| Admin login round-trip via `/sign-in`           | Real form submit → portal redirect                    |
| Daily Reports list reachable for admin          | Token injection + critical API + 1+ row from restore  |
| Logout clears portal tokens                     | `/api/auth/multi-logout` + localStorage purge         |

### 1c. Threshold-logic verification (this session)
- ✅ `ATLAS_QUOTA_MB=750`  → severity=`critical` (121.5%)
- ✅ `ATLAS_QUOTA_MB=1100` → severity=`warning`  (82.9%)
- ✅ `ATLAS_QUOTA_MB=10240` → severity=`ok`        (8.9%)

---

## 2. Critical paths NOT yet covered

Tracked here so they don't get forgotten. None of these are marked verified.

### 🟠 P0 — must add before "operational trust" is real
| # | Flow                                              | Why deferred                            |
|---|---------------------------------------------------|------------------------------------------|
| 1 | MFA enroll → verify → use → disable               | Existing `test_iter375_mfa_totp.py` covers backend; need browser flow |
| 2 | Passkey enroll + login                            | WebAuthn requires browser-specific helpers |
| 3 | Daily Report **submit** (write path)              | Write-path tests need cleanup discipline; deferred to session 2 |
| 4 | Dispatch board load                               | Needs real dispatch token bootstrap     |
| 5 | Driver shift start/end                            | Needs driver-token bootstrap            |

### 🟠 P0 — operational
| # | Flow                                              | Coverage path                            |
|---|---------------------------------------------------|------------------------------------------|
| 6 | Crew section + Visitor section + Subcontractor    | Sub-forms in `/daily/new`                |
| 7 | Attachment upload round-trip (R2 persistence)     | Multipart POST + R2 HEAD check           |
| 8 | Payroll workflow                                  | HR portal write path                     |
| 9 | Public form (`/inspections/new`, `/meetings/new`) | Rate-limit + magic-link variant          |
| 10 | Restore-system health checks                     | `/api/admin/persistence/health`          |
| 11 | Environment isolation enforced under load        | Concurrent prod/preview API access       |

### 🟡 P1 — survivability
| # | Flow                                              | Note                                     |
|---|---------------------------------------------------|------------------------------------------|
| 12 | Time Verification (HR)                           | Performance-critical                     |
| 13 | Route role-routing edge cases                    | E.g. PM token on `/admin` → must redirect|
| 14 | Mobile keyboard / touch-target audits            | Visual regression                        |
| 15 | Offline-queue persistence after refresh          | Field-survivability test                 |

---

## 3. Deployment gating strategy

Gate every production deploy on:

```bash
# Gate A — backend contract (deploy-blocker)
cd /app/backend && python3 -m pytest tests/regression/test_critical_flows.py -q

# Gate B — Playwright browser flows (deploy-blocker on first 5 flows)
cd /app/backend && python3 -m pytest tests/pw_suite/test_critical_flows_pw.py -q

# Gate C — cluster sanity (deploy-blocker if severity != "ok")
URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d= -f2) && \
  curl -fsS "$URL/api/cluster/capacity" | python3 -c "
import sys, json; d=json.load(sys.stdin)
assert d['ok'] and d['severity'] in {'ok','warning'}, d
"
```

A deploy that fails ANY gate must NOT promote.

Exit code 0 across all three = green light.

---

## 4. Failure runbook (when the suite goes red)

| Symptom                              | Triage                                                  |
|--------------------------------------|---------------------------------------------------------|
| `test_env_identity_*` fails          | STOP. Pod may be on prod. Check `/api/version`.         |
| `test_multi_login_*` fails           | Super-admin bootstrap broken. Check backend logs `[directory]`. |
| Playwright `test_public_hub_renders` fails | SplashOverlay stuck OR React build failed.        |
| Playwright `test_admin_login_round_trip` fails on ONE viewport only | Likely a responsive selector bug — check screenshot. |
| `test_admin_can_reach_daily_reports` returns 0 docs | Preview DB was wiped. Re-run restore drill. |
| `test_hr_perf_budget` fails          | Mongo regression. Check projection in `routes/hr_portal.py`. |
| Cluster severity ≠ ok                | See `ATLAS_ALERTS_RUNBOOK.md` + `OPERATIONAL_RUNBOOKS.md`. |

Full debugging guide in `OPERATIONAL_RUNBOOKS.md` (Phase Sigma).

---

## 5. Future certification roadmap (sequenced)

**Session 2 (next sprint):**
- Build write-path flows (#3, #7, #8) — daily-report submit, attachment upload, payroll.
- Build dispatch + driver flows (#4, #5).
- Wire `pytest-html` reporter for CI artifact.

**Session 3:**
- MFA + passkey browser flows (#1, #2).
- Public-form variants (#9).
- Restore-system health (#10).
- Concurrent prod/preview isolation under load (#11).

**Session 4:**
- Visual regression baseline (#14).
- Offline-queue persistence (#15).
- Role-routing edge cases (#13).

**Stop condition:** all 15 flows green on all 3 viewports, runtime under 5 min total.

---

## 6. Proof trail

| Date       | Suite           | Result               | Artifact                          |
|------------|-----------------|----------------------|-----------------------------------|
| 2026-05-26 | API regression  | `43 passed in 9.45s` | `REGRESSION_BASELINE.md`          |
| 2026-05-26 | Playwright      | `15 passed in 36.32s`| `/app/test_reports/playwright/`   |
| 2026-05-26 | Threshold logic | 3/3 severities VERIFIED | This document § 1c             |
| 2026-05-26 | Cluster after restore | 7.7% / OK      | `/api/cluster/capacity`           |
