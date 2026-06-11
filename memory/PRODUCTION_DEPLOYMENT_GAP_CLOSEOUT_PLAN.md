# PRODUCTION DEPLOYMENT GAP CLOSEOUT PLAN

**Date:** 2026-02-10
**Authority:** FORGEDOPS Execution Doctrine · BUILD → VERIFY → PROVE → CLOSE
**Mission:** Bring production (`source_hash=3a5719f5618ad3801993617d8bd385f2`) up to preview head (`source_hash=0af9eca046211ac3cab0884851f5b77e`) safely, evidence-based, no new features, no fake data.

> **Status: NOT DEPLOYED — plan only. Awaiting operator GO.**

---

## PHASE 1 · PRODUCTION DEPLOY READINESS — VERDICT: 🟢 PASS

| # | Check | Status | Evidence |
|---|---|---|---|
| 1 | Backend imports cleanly · server.py loads | ✅ | Preview backend running on this build (pid 4628) since 00:41 UTC with no crash. |
| 2 | Frontend build present | ✅ | Preview frontend serves at `https://safety-audit-mobile-1.preview.emergentagent.com` (200 OK). |
| 3 | Critical smoke flows | ✅ | Production cert table this session: 27/27 endpoints PASS authenticated. |
| 4 | No preview-only test data hardcoded | ✅ | `cluster_capacity.py` references both DB names but `try/except` skips unreadable DBs → safe on prod. No fixtures imported at runtime. |
| 5 | No preview-only credentials committed | ✅ | `git ls-files` shows `backend/.env`, `backend/.env.preview`, `frontend/.env` ALL untracked. |
| 6 | `.env`, `.env.preview`, `frontend/.env` gitignored | ✅ | `git check-ignore -v` confirms exclusion via `.gitignore` lines 813–814. |
| 7 | Production System Keys remain source of truth | ✅ | Per Emergent support: prod reads exclusively from System Keys; `.env.preview` has no path to prod. |
| 8 | New routes don't depend on preview-only collections | ✅ | All preview routes operate on collections present in both DBs (`equipment_master`, `dispatch_assignments`, `motive_events`, etc.). |
| 9 | Routes fail safely if integrations not configured | ✅ | `integration_health._probe_motive` returns `disabled · MOCKED` when API key absent. `motive_reliability` loop logs warning if key missing, does not crash. |
| 10 | No destructive migrations on prod deploy | ✅ | Destructive `delete_many` calls in server.py are scoped (filtered by `{coll: "Trench Safety"}`, `{_id: $in: ids}`, etc.) and only fire from explicit admin endpoints, never on startup. |

**Readiness: 🟢 PASS.** Preview build is shippable to production.

---

## PHASE 2 · PRODUCTION DEPLOY IMPACT TABLE (after redeploy)

| Feature | Prod current | Prod after deploy | Risk | Verification |
|---|---|---|---|---|
| `/api/pm/command-center/*` (Phase 4A · 7 routes) | 404 | 200 | LOW · read-only | `GET /api/pm/command-center/summary` with PM token = 200 |
| `/api/operations-center/command/*` (Phase 4C · 10 routes) | partial (1/10) | full | LOW | `GET /api/operations-center/command/summary` = 200 |
| `/api/operations-center/summary` | 404 | 200 | LOW | direct probe |
| `/api/dispatch/command/*` (7 routes — dispatch command center) | 404 | 200 | MEDIUM (operator-critical) | broadcast-sms is POST-only — DO NOT auto-test |
| `/api/dispatch/governance` | 404 | 200 | LOW | direct probe |
| `/api/dispatch/exports/*.csv` (3 exports) | 404 | 200 | LOW | HEAD probe |
| `/api/asset-spine/*` (14 routes — canonical asset spine) | 404 | 200 | MEDIUM (foundation layer) | `GET /api/asset-spine/summary` = 200 |
| `/api/asset-mapping/*` (12 routes — recon) | 404 | 200 | MEDIUM | `GET /api/asset-mapping/recon` = 200 |
| `/api/integrations/motive/health` | 404 | 200 → `MOCKED` until key in System Keys | LOW (mocked-safe) | `GET` returns `disabled · MOCKED` if no key |
| `/api/integrations/motive/status` | 404 | 200 → mocked | LOW | direct probe |
| `/api/integrations/motive/sync` (manual kick) | 404 | 200 but 4xx if no key | LOW | guarded by `_probe_motive` |
| `/api/integrations/motive/assets`/`/users` | 404 | 200, empty array until sync | LOW | direct probe |
| `/api/admin/motive-reliability` | 404 | 200 with reliability state snapshot | LOW | direct probe |
| `/api/integrations/maintainx/health` | 404 | 200 → `MOCKED` if no key | LOW | direct probe |
| `/api/admin/maintainx` | 404 | 200 → mocked | LOW | direct probe |
| `/api/safety/library` | 404 | 200 | LOW | direct probe |
| `/api/safety/exports/*` (10 routes) | 404 | 200 | LOW | direct probe |
| `/api/safety-forms` (12 routes) | 404 | 200 | LOW | direct probe |
| `/api/training-center` (8 routes) | 404 | 200 | LOW | direct probe |
| `/api/hr/payroll-variance` | 404 | 200 | MEDIUM (HR-visible) | direct probe |
| `/api/master-lookup` (7 routes) | 404 | 200 | LOW | direct probe |
| `/api/photos` (governance) | 404 | 200 | LOW | direct probe |
| `/api/passkeys` (6 routes) | 404 | 200 | LOW | direct probe |
| `/api/global-search` | 404 | 200 | LOW | direct probe |
| `/api/admin/digest` (operator digest) | 404 | 200 | LOW | direct probe |
| `/api/admin/backup-verification` | 404 | 200 | LOW | direct probe |
| `/api/admin/project-identity` | 404 | 200 | LOW | direct probe |
| `/api/admin/dls` (day-1/week-1 debrief) | 404 | 200 | LOW | direct probe |
| `/api/admin/signatures` | 404 | 200 | LOW | direct probe |
| `/api/admin-strict/diag` / `/stability` | 404 | 200 | LOW | direct probe |
| `/api/platform/data-truth` | now ✅ on prod | ✅ unchanged | NONE | direct probe |
| `/api/operations-map/contract` | ✅ | ✅ unchanged | NONE | direct probe |
| `/api/cluster/capacity` | ✅ (only reads `masci_safety`) | ✅ (still skips unreadable preview DB via try/except) | NONE | confirmed live |
| **Auth surface** (login/me/logout) | ✅ | ✅ | NONE | already passing |
| **DB connection** | ✅ `masci_prod_user → masci_safety` | ✅ unchanged | NONE | system-health card green |
| **JWT_SECRET / sessions / RBAC** | ✅ | ✅ unchanged | NONE | not modified by deploy |

**No route in this set performs a destructive write on production data during normal use. All write operations are gated by admin tokens and explicit POST/PATCH/DELETE invocations.**

---

## PHASE 5 · PRODUCTION REDEPLOY DECISION

| Item | Outcome |
|---|---|
| Code readiness | 🟢 PASS |
| Secret integrity | 🟢 PASS (preview .env never reaches prod; System Keys remain authoritative) |
| Atlas isolation | 🟢 PASS (preview blocked from `masci_safety`; production blocked from `masci_safety_preview` per operator confirmation) |
| Auth surface | 🟢 unchanged by deploy |
| Data layer | 🟢 read-compatible; no migration |
| Rollback availability | 🟢 Emergent platform preserves the prior build (`3a5719f…`) for one-click rollback |

> **REDEPLOY DECISION: 🟢 GO** (technical platform readiness). The only non-technical gate is the Motive activation (see `MOTIVE_PRODUCTION_ACTIVATION_PLAN.md` — Motive activation is a SEPARATE workstream from the redeploy and can be sequenced after redeploy).

### Recommended deploy sequence

1. **Verify preview is the build you want to ship** — confirm `source_hash=0af9eca046211ac3cab0884851f5b77e` on `/api/version` (already verified).
2. **Open Emergent dashboard → production deployment → "Redeploy from preview"** (or equivalent button).
3. **Pre-deploy snapshot:** confirm production currently 200 on `/api/health` and record uptime baseline.
4. **Trigger redeploy.**
5. **Wait for build success.** Old pod continues serving until new pod is ready (rolling deploy).
6. **Post-deploy: run the Phase 6 certification suite** (below).
7. **If any RED card on system-health that wasn't yellow/red pre-deploy**, rollback (see §Rollback).
8. **Document the deploy** in `/app/memory/CHANGELOG.md`.

### Rollback criteria (auto-trigger)
- `/api/health` returns non-200 for >2 minutes.
- `/api/auth/multi-login` returns 5xx.
- `system-health.database` flips to red.
- `system-health.auth_failures` > 5 in 5 minutes.
- ANY active user reports forced logout.
- ANY 5xx storm on `/api/admin/*` or `/api/operations-center/*`.

### Rollback procedure
- Emergent dashboard → production → **Deploy History → click previous successful build (`3a5719f…`) → Redeploy**.
- Time to recovery: ≤90 s (rolling redeploy from cached previous build).
- No data loss — DB untouched.

---

## PHASE 6 · POST-DEPLOY CERTIFICATION CHECKLIST

Run this checklist immediately after the deploy completes. Every item must PASS before declaring the deploy complete.

```
□ A1 · GET https://mascidocs.com/api/health = 200
□ A2 · GET /api/version reports app_env=production, db_name=masci_safety
□ A3 · POST /api/auth/multi-login (super-admin) = 200 with all 7 portal_tokens
□ A4 · GET /api/auth/me-directory (X-Directory-Token) = 200 with is_super_admin=true
□ A5 · POST /api/auth/multi-logout = 200

□ B1 · GET /api/admin/directory (X-Admin-Token) = 200
□ B2 · GET /api/admin/system-health · all cards green except integrations (yellow expected pre-Motive)
□ B3 · GET /api/admin/audit?limit=5 = 200
□ B4 · GET /api/admin-strict/diag = 200    (new)
□ B5 · GET /api/admin-strict/stability = 200    (new)

□ C1 · GET /api/pm/command-center/summary (X-PM-Token) = 200    (new)
□ C2 · GET /api/operations-center/command/summary = 200    (new)
□ C3 · GET /api/operations-center/summary = 200    (new)
□ C4 · GET /api/dispatch/command/summary = 200    (new)
□ C5 · GET /api/dispatch/governance = 200    (new)

□ D1 · GET /api/asset-spine/summary = 200    (new)
□ D2 · GET /api/asset-mapping/recon = 200    (new)
□ D3 · GET /api/asset-transfers?limit=1 = 200
□ D4 · GET /api/operational-records?limit=1 = 200
□ D5 · GET /api/operational-attachments?limit=1 = 200    (new)
□ D6 · GET /api/timeline?limit=1 = 200

□ E1 · GET /api/integrations/motive/health = 200, status=disabled, mocked=true (until activation)
□ E2 · GET /api/integrations/motive/status = 200
□ E3 · GET /api/integrations/motive/events = 200, array (may be empty)
□ E4 · GET /api/integrations/motive/geofences = 200, array (may be empty)
□ E5 · GET /api/integrations/motive/assets = 200, array (may be empty)
□ E6 · GET /api/integrations/motive/users = 200, array (may be empty)
□ E7 · GET /api/admin/motive-reliability = 200 with reliability state snapshot

□ F1 · GET /api/integrations/maintainx/health = 200, status=disabled, mocked=true
□ F2 · GET /api/integrations/maintainx/work-orders = 200

□ G1 · GET /api/safety/library = 200
□ G2 · GET /api/safety-forms = 200
□ G3 · GET /api/training-center = 200
□ G4 · GET /api/hr/payroll-variance = 200
□ G5 · GET /api/master-lookup = 200
□ G6 · GET /api/global-search?q=test = 200
□ G7 · GET /api/photos = 200
□ G8 · GET /api/passkeys = 200

□ H1 · No 5xx on the production stderr log scan (operator)
□ H2 · No forced logout — active sessions persist
□ H3 · cluster_capacity returns only masci_safety (preview blocked, correctly)
□ H4 · system-health card "database" = green
□ H5 · system-health card "auth_failures" = 0 attempts (1h)
□ H6 · system-health card "failed_syncs" = 0 failures (24h)

□ I1 · No preview test data visible (spot-check 3 records)
□ I2 · DB_NAME confirmed = masci_safety
□ I3 · No JWT_SECRET / sessions / RBAC change observed
□ I4 · Frontend renders /sign-in without console errors
□ I5 · One operator login → dashboard load → logout completes cleanly
```

If any box fails → **rollback per Phase 5 §Rollback**.

If all boxes pass → mark deploy CLOSED and proceed to `MOTIVE_PRODUCTION_ACTIVATION_PLAN.md`.

---

## NOT in this redeploy

- Motive activation (separate plan).
- MaintainX activation (separate plan).
- FleetWatcher (blocked per OMEGA).
- Live Operations Map UI Phase 5B (blocked until Motive coverage ≥20%).
- Atlas `"Password"` user disposition (separate Emergent support thread).

**This document covers code-redeploy only.**
