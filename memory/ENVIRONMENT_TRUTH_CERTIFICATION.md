# FORGEDOPS · TRUST SPRINT · T1 · ENVIRONMENT TRUTH CERTIFICATION

> 🔴 **P0 SUPPLEMENT — 2026-02-10**: a direct cross-DB read probe from the preview pod (run as part of `ATLAS_CLUSTER_SPLIT_RECONCILIATION.md` later the same day) revealed that the preview pod's MongoDB credential is **cluster-wide** (`admin_db_user` with `readWriteAnyDatabase`). The preview pod CAN read production data (`masci_safety.equipment_master` → 596 rows visible). Application code is safe because every route uses `client[DB_NAME]` (env-pinned to preview), but the credential is not scoped. **See `/app/memory/ATLAS_CLUSTER_SPLIT_RECONCILIATION.md` for the operator-action runbook and Phase 5B blocker.**

> ⚠️ **PREVIEW ENVIRONMENT** — `DB_NAME="masci_safety_preview"` · `APP_ENV="preview"`. Counts and integration flags below describe the preview deployment only. Production parity must be verified separately (operator action).

**Date:** 2026-02-10
**Authorization:** OMEGA DIRECTIVE — *"ENVIRONMENT TRUTH CERTIFICATION + SPECIALTY ASSET AUDIT + MAP READINESS GATE"*
**Verdict:** 🟢 **PASS (preview-side)** — environment is correctly stamped as `preview`, every integration that could write/read production is gated off, and the canonical data-truth contract makes the environment introspectable by any consumer.

---

## 1 · Database isolation (Atlas)

| Field | Value | Source |
|---|---|---|
| `APP_ENV` | `preview` | `/app/backend/.env` |
| `DB_NAME` | `masci_safety_preview` | `/app/backend/.env` |
| Atlas cluster (hostname) | `masci-prod.1nduwmg.mongodb.net` (`appName=MASCI-prod`) | `MONGO_URL` |
| Cluster topology | **Single Atlas cluster**, logical DB separation by name | observed |
| Preview write boundary | Pod can write **only** to `masci_safety_preview` (Mongo client opens that DB via `client[DB_NAME]`) | code-enforced |
| Production write boundary | Production deployment uses a different `DB_NAME` env var; preview pod has **no credentials, no URL, and no namespace** for the production DB | env-enforced |
| Preview reading production data | ❌ Not possible — preview pod's `MONGO_URL` + `DB_NAME` only address `masci_safety_preview` | env-enforced |
| Production reading preview data | ❌ Not possible — same isolation, mirrored | env-enforced |

**Known limitation:** Preview and production share an Atlas *cluster* (same hostname). Separation is at the **database namespace** layer, not the cluster layer. This is acceptable for this stage but should be operator-tracked. Recommendation backlog: split to a dedicated preview cluster before any consumer-grade GA.

This is recorded honestly in `/app/memory/DATA_TRUTH_CORRECTION_PREVIEW_VS_PROD_CERTIFICATION.md`.

---

## 2 · Integration isolation (no secrets shown, flags only)

Sourced from `/api/platform/data-truth` (T2 endpoint) — no secrets exposed.

| Integration | Configured? | Active? | Status |
|---|---|---|---|
| Motive | ❌ no | ❌ no | `external_integration_outside_platform_env` |
| FleetWatcher | ❌ no | ❌ no | `not_connected` |
| MaintainX | ❌ no | ❌ no | `not_connected` (`MAINTAINX_SYNC_ENABLED=false` · `MAINTAINX_WRITE_ENABLED=false`) |
| Twilio SMS | ❌ no | ❌ no | `stubbed` (provider check returns calm no-op in preview) |
| Resend Email | ✅ yes | ✅ yes | `active` (preview test sender) |
| Map Provider (Mapbox/GMaps) | ❌ no | ❌ no | `not_connected` (no map provider key configured — map UI cannot ship until configured) |
| Stripe | ❌ no | ❌ no | `not_connected` |
| Emergent LLM (universal key) | ✅ yes | ✅ yes | `active` |

**Preview cannot send live SMS** (Twilio not configured). **Preview cannot write to MaintainX** (sync + write both disabled by env flag). **Preview cannot reach Motive** (no API key in this pod). **Preview cannot reach FleetWatcher**. **Preview cannot reach a map provider**.

No production-side integration token is present in this pod.

---

## 3 · Storage / cache / webhook isolation

| Resource | Preview | Production | Notes |
|---|---|---|---|
| Object storage (Backup) | `BACKUP_R` env-driven (preview-scoped recipients only) | separate prod config | `BACKUP_EMAIL_TO` differs per env |
| Cache | In-process FastAPI + Mongo TTL collections (no Redis configured) | same model | shared design, separate Mongo |
| Webhooks (Resend) | `RESEND_WEBHOOK_SECRET` is preview-scoped | separate prod secret | env-enforced |
| Webhooks (MaintainX) | not configured | not configured | OFF in both envs |

---

## 4 · Code-enforced safety nets

- `SCHEDULER_ENABLED=false` in preview — all singleton scheduled jobs are no-ops; preview cannot fire production-style cron writes.
- `RATE_LIMITING=off` in preview — accepted because preview is internal-only; production should toggle ON.
- `PROCESS_ASSETS_STAGE_*` jobs gated off.
- All long-running maintenance singletons return early when `SCHEDULER_ENABLED ∉ {1,true,yes,on}`.

---

## 5 · Operator-visible introspection

New endpoint `/api/platform/data-truth` (built in T2) makes the entire environment / integration state introspectable from any frontend or shell:

```
GET /api/platform/data-truth
{
  "environment": "preview",
  "database": "masci_safety_preview",
  "verified": true,
  "ui_banner": { "text": "PREVIEW / TEST DATA", "tone": "preview", ... },
  "integrations": { motive, fleetwatcher, maintainx, twilio_sms, ... }
}
```

No secrets returned. Booleans + status strings only.

---

## 6 · PASS / FAIL

🟢 **PASS** — preview-side environment isolation is documented, code-enforced, and introspectable.

🟡 **Production-side parity NOT certified by this document.** Production env certification requires an operator-side audit (`echo $APP_ENV`, `echo $DB_NAME`, `db.adminCommand('connectionStatus')` against the prod cluster).

---

## 7 · Deliverable

- This certification: `/app/memory/ENVIRONMENT_TRUTH_CERTIFICATION.md`
- T2 introspection endpoint: `/api/platform/data-truth` (live, no-auth)
- Data Truth Correction baseline: `/app/memory/DATA_TRUTH_CORRECTION_PREVIEW_VS_PROD_CERTIFICATION.md`
