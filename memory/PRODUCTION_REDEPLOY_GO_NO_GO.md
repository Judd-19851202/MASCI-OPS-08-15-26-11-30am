# PRODUCTION REDEPLOY · GO / NO-GO

**Date:** 2026-02-10
**Decision:** **🟢 GO for code redeploy** · **🔴 NO-GO for Motive activation** (operator secrets not yet provisioned)

---

## 1 · Redeploy readiness

**🟢 GO — Production redeploy from preview head is authorized.**

Rationale (verified, not asserted):
- Preview backend build is healthy, running under `masci_preview_user` with full isolation enforced.
- Atlas cross-DB isolation proven (preview blocked from `masci_safety`).
- `admin_db_user` deleted; production runs under `masci_prod_user`.
- All 10 deploy-readiness items in `PRODUCTION_DEPLOYMENT_GAP_CLOSEOUT_PLAN.md` §Phase 1 PASS.
- No destructive migration runs at startup. All `delete_many` calls are scoped + admin-gated.
- `.env`, `.env.preview` proven gitignored. Production `MONGO_URL` lives in System Keys, not in code.
- Rollback path available: Emergent retains previous build (`3a5719f…`) for one-click revert.

Risk floor: **MEDIUM** — operator-critical dispatch + ops command center routes change from 404 → 200. Possible UI-surface regressions if frontend hard-codes a route that previously returned 404 and silently hid the panel; unlikely but to be verified by Phase 6 checklist.

---

## 2 · Motive activation readiness

**🔴 NO-GO** until:
1. `MOTIVE_API_KEY` is set in production Emergent System Keys.
2. `MOTIVE_WEBHOOK_SECRET` is set (if webhook ingress desired — strongly recommended).
3. (Recommended) `_probe_motive` in `routes/integration_health.py` is upgraded with a live API ping so System Health truthfully reports `active` vs `mocked`.
4. The 12 Motive Go/No-Go gates in `MOTIVE_PRODUCTION_ACTIVATION_PLAN.md` §7 are all 🟢 with operator-verifiable evidence.

The Motive route handlers WILL be deployed by the code-redeploy and will gracefully report `disabled · MOCKED` until the API key is in place. **It is safe to redeploy code BEFORE provisioning the Motive secrets** — that is the recommended sequence.

---

## 3 · Required operator secrets

| Key | Where | Required for |
|---|---|---|
| `MOTIVE_API_KEY` | Emergent → Manage Deployments → Secrets → System Keys (production only) | Motive activation |
| `MOTIVE_WEBHOOK_SECRET` | same | Motive webhook ingress |
| `MOTIVE_BASE_URL` | same (optional · default `https://api.gomotive.com`) | regional override |
| `MAINTAINX_API_KEY` (already in preview .env) | same | MaintainX activation (separate workstream) |
| `MAINTAINX_BASE_URL` | same | MaintainX activation |
| `MAINTAINX_SYNC_ENABLED=true` | same | MaintainX activation |
| `MAINTAINX_WRITE_ENABLED=false` | same | MaintainX safety |

**Do NOT modify:** `JWT_SECRET`, `MONGO_URL`, `DB_NAME`, `APP_ENV`. (`MONGO_URL` was rotated to `masci_prod_user` already.)

---

## 4 · Required Motive admin actions (in Motive's own dashboard)

1. Obtain a Motive API key with the minimum scopes: `read:assets`, `read:users`, `read:events`, `read:geofences` (+ `read:dvirs` if you want DVIR ingest).
2. Generate a webhook signing secret.
3. Register webhook URL: `https://mascidocs.com/api/integrations/motive/webhook`.
4. Subscribe to minimum event types: `vehicle.location_updated`, `driver.hos_status_changed`, `geofence.entered`, `geofence.exited`. Add `dvir.created` and `accident.detected` if desired.
5. Confirm Motive's IP allowlist (if any) does not block egress from MASCI's production pod.

---

## 5 · Exact next action

```
STEP 1 (operator · ~5 min): 
   • Open Emergent dashboard → production deployment.
   • Click "Redeploy" or "Promote preview to production".
   • Wait for build success and rolling restart.
   
STEP 2 (agent · ~3 min):
   • Run the Phase 6 post-deploy certification table.
   • Report PASS or FAIL per item.

STEP 3 (operator · if Phase 6 PASS): 
   • Provision Motive secrets in Emergent System Keys (see §3).
   • Click "Redeploy" once more so the pod picks up the new env-vars.

STEP 4 (agent · ~5 min):
   • Verify Motive Go/No-Go gates 1–12.
   • Report activation status: ACTIVE or NOT-ACTIVE-AND-WHY.

STEP 5 (operator · if Motive active):
   • Open Motive dashboard → register webhook URL.
   • Subscribe to the minimum event set.

STEP 6 (agent · final):
   • Verify webhook is reachable end-to-end.
   • Confirm scheduler ticks visible in /api/admin/motive-reliability.
   • File evidence document.
```

If Phase 6 fails on any item → ROLLBACK per `PRODUCTION_DEPLOYMENT_GAP_CLOSEOUT_PLAN.md` §Rollback. Do NOT proceed to Motive activation.

---

## 6 · Remaining blockers

| Blocker | Type | Owner | Fix |
|---|---|---|---|
| `MOTIVE_API_KEY` not in production System Keys | secret | operator | obtain from Motive admin, paste into Secrets panel |
| `MOTIVE_WEBHOOK_SECRET` not in production System Keys | secret | operator | generate in Motive dashboard, paste into Secrets panel |
| `_probe_motive` live-probe upgrade | code (~30 lines) | engineering | optional but recommended before flipping System Health to green |
| Atlas `"Password"` user disposition | vendor (Emergent) | Emergent support reply | awaiting support reply on ownership |
| Motive webhook URL not registered in Motive dashboard | vendor (Motive) | operator | register after activation |
| FleetWatcher activation | downstream | operator + Trust closeout | blocked per OMEGA, deferred |
| Live Operations Map UI (Phase 5B) | downstream | engineering | blocked until Motive coverage ≥20% |

---

## 7 · Final answers (per directive output format)

1. **Production redeploy readiness:** 🟢 **PASS**
2. **Motive activation readiness:** 🔴 **FAIL** (secrets not yet provisioned)
3. **Deployment GO/NO-GO:** 🟢 **GO** for code redeploy · 🔴 **NO-GO** for Motive activation
4. **Required operator secrets:** see §3
5. **Required Motive admin actions:** see §4
6. **Exact next action:** see §5 STEP 1
7. **Remaining blockers:** see §6

No deployment performed. No secrets read or written. No production touched.
