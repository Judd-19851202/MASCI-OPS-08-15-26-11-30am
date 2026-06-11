# MOTIVE PRODUCTION ACTIVATION PLAN

**Date:** 2026-02-10
**Authority:** FORGEDOPS Execution Doctrine
**Status:** 🟡 NOT ACTIVATED · plan + gates only

Activation of the Motive telematics integration. Service-account-only changes. No JWT, sessions, RBAC, or user-data touched.

---

## 1 · Required production secrets (Emergent Manage Deployments → Secrets → System Keys)

| Key | Required | Notes |
|---|---|---|
| `MOTIVE_API_KEY` | **YES** | Customer Motive API key from your Motive dashboard. Format: long alphanumeric string. Without this, integration boots in stub mode. |
| `MOTIVE_BASE_URL` | optional | Defaults to `https://api.gomotive.com`. Set only if you use a regional/sandbox endpoint. |
| `MOTIVE_WEBHOOK_SECRET` | **YES if Motive pushes events to MASCI** | Used for HMAC verification of incoming webhook payloads. Without this, webhook ingress is rejected. |
| `MOTIVE_SYNC_EVENTS_SECONDS` | optional | Default 900 (15 min). |
| `MOTIVE_SYNC_ASSETS_SECONDS` | optional | Default 43200 (12 h). |
| `MOTIVE_SYNC_USERS_SECONDS` | optional | Default 43200 (12 h). |
| `MOTIVE_SYNC_GEOFENCES_SECONDS` | optional | Default 43200 (12 h). |
| `MOTIVE_RELIABILITY_BOOT_DELAY_S` | optional | Default 45 s (boot stagger). |
| `SCHEDULER_ENABLED` | **YES** = `true` | Already true on production. The reliability supervisor only schedules when this is true. |

**Do NOT modify:** `JWT_SECRET`, `MONGO_URL`, `DB_NAME`, `APP_ENV`.

---

## 2 · Required database records (Mongo · `masci_safety`)

Seed inside the production pod (operator action, NOT agent) once secrets are in System Keys:

| Collection | Document | Purpose |
|---|---|---|
| `integration_settings` | `{provider:"motive", enabled:true, api_key_value:"${MOTIVE_API_KEY}", webhook_secret_value:"${MOTIVE_WEBHOOK_SECRET}", base_url:"https://api.gomotive.com", last_synced_at:null, last_failed_sync_at:null, created_at:<utc>, updated_at:<utc>}` | DB-side toggle that the integration framework reads. **Without this row, `motive_service` treats Motive as disabled even if env vars are set.** |
| `asset_mappings` | populated by `sync_assets` after first successful sync | Maps Motive vehicle/device IDs → MASCI canonical asset records. Unmapped vehicles surface in the Asset Mapping Recon queue. |
| `employee_mappings` | populated by `sync_users` | Maps Motive driver IDs → MASCI employee records. |
| `motive_events` | populated by `sync_events` and webhooks | Event log. |
| `sync_logs` | written automatically by `_write_sync_log` after each sync tick | Observability — operator reads via existing Integration Center surface. |
| `integration_sync_logs` | written automatically | Reliability surface. |
| `scheduler_locks` | written automatically by the singleton scheduler | Multi-worker safety. |
| `cluster_capacity_history` | unrelated; already managed | — |

**The integration framework refuses to operate on the wrong DB:** `db_isolation_failsafe.py` already gates this.

---

## 3 · Required endpoints (must exist post-redeploy, none of these are in the current production build)

| Endpoint | Method | Auth | Purpose |
|---|---|---|---|
| `/api/integrations/motive/health` | GET | admin | Probe state: `disabled · MOCKED` until activated; `active · OK` after |
| `/api/integrations/motive/status` | GET | admin | Detailed state + last-sync timestamps |
| `/api/integrations/motive/sync` | POST | admin | Manual kick of all 4 sync ops |
| `/api/integrations/motive/assets` | GET | admin | List of Motive-side assets (read from `asset_mappings`) |
| `/api/integrations/motive/users` | GET | admin | List of Motive-side users (read from `employee_mappings`) |
| `/api/integrations/motive/events` | GET | admin | Read-only event log (already deployed) |
| `/api/integrations/motive/geofences` | GET | admin | Geofence list (already deployed) |
| `/api/integrations/motive/webhook` | POST | webhook (HMAC) | Inbound webhook receiver |
| `/api/admin/motive-reliability` | GET | admin | Reliability supervisor state · scheduler ticks |

All read-only routes are safe to ship in the mocked-default state.

---

## 4 · Scheduler behavior (already coded in `/app/backend/lib/motive_reliability.py`)

| Sync | Cadence | Env override | Failure handling |
|---|---|---|---|
| `events` | every 15 minutes | `MOTIVE_SYNC_EVENTS_SECONDS` | logs to `integration_sync_logs`, sets `last_failed_sync_at`, retries next tick |
| `assets` | every 12 hours | `MOTIVE_SYNC_ASSETS_SECONDS` | same |
| `users` | every 12 hours | `MOTIVE_SYNC_USERS_SECONDS` | same |
| `geofences` | every 12 hours | `MOTIVE_SYNC_GEOFENCES_SECONDS` | same |
| Supervisor resurrection | every 5 minutes | hard-coded | respawns any task that died with an exception |
| Boot-time staleness backfill | once, if last successful `events` sync > 30 min old | hard-coded | kicks single `events` sync at boot+`BOOT_DELAY` (default 45s) |

**Multi-worker safety:** uses the existing `scheduler_locks` singleton-lock pattern (same as backup scheduler). Only one pod runs each tick even with horizontal scaling.

**Failure alerting:** failures surface via `integration_settings.motive.last_failed_sync_at`. The Integration Health card + existing `Integration Center` UI reflect the state — no new alerting framework introduced.

---

## 5 · Webhook setup (Motive admin dashboard)

| Item | Value |
|---|---|
| Webhook URL | `https://mascidocs.com/api/integrations/motive/webhook` |
| Method | POST |
| Content-Type | `application/json` |
| Signing | HMAC-SHA256 over raw body using `MOTIVE_WEBHOOK_SECRET`. Send signature in header `X-Motive-Signature: sha256=<hex>` |
| Replay protection | Each event includes a Motive-issued `event_id`; MASCI dedupes in `motive_events` by `(provider, event_id)`. |
| Failure handling | MASCI returns 200 on duplicate/replayed events. Non-2xx triggers Motive's retry policy automatically. On signature mismatch MASCI returns 401 and does NOT persist the payload. |
| Subscribed events | At minimum: `vehicle.location_updated`, `driver.hos_status_changed`, `dvir.created`, `geofence.entered`, `geofence.exited`. Operator decides full list per Motive plan. |

---

## 6 · Data flow

```
Motive cloud
   │  webhook + REST poll
   ▼
services/motive_service.py        ← uses MOTIVE_API_KEY
   │
   ▼
Mongo: motive_events · asset_mappings · employee_mappings · sync_logs
   │
   ▼
Asset Spine (`/api/asset-spine/*`)        ← canonical asset registry
   │
   ▼
Dispatch (`/api/dispatch/*`)              ← uses asset_mappings for truck/driver identity
   │
   ▼
PM Command Center (`/api/pm/command-center/*`)
   │
   ▼
Operations Center (`/api/operations-center/*`)
   │
   ▼
Operations Map Contract (`/api/operations-map/contract`)   ← read-only, latest map state
   │
   ▼
Phase 5B Live Map UI (blocked until coverage ≥20%)
```

Every layer is read-only over the layer above. No layer mutates Motive. No fake / synthetic data is ever inserted into these collections.

---

## 7 · Motive Go/No-Go GATES (Motive MAY NOT be marked active unless EVERY gate is 🟢)

| # | Gate | Evidence required |
|---|---|---|
| 1 | `MOTIVE_API_KEY` set in production System Keys | operator screenshot of Secrets panel (key name only, value redacted) |
| 2 | API key validates against Motive | `GET /api/integrations/motive/health` returns `status: ok` AND `mocked: false` |
| 3 | `/api/integrations/motive/health` returns active/OK | as above |
| 4 | Manual sync returns successful result | `POST /api/integrations/motive/sync` → 200 with `created≥0, errors=0` |
| 5 | ≥1 Motive asset received | `GET /api/integrations/motive/assets` → array with ≥1 item OR `asset_mappings` collection has ≥1 doc with `provider:"motive"` |
| 6 | ≥1 Motive user/driver received (if drivers in Motive) | `GET /api/integrations/motive/users` → array with ≥1 item OR `employee_mappings` count ≥1 |
| 7 | `asset_mappings` rows created or unmapped queued for recon | mapping queue surfaces unmatched vehicles via `/api/asset-mapping/recon` |
| 8 | Unmapped Motive assets appear in mapping queue (NOT silently ignored) | spot-check: a fresh Motive vehicle absent from `equipment_master` shows up in the recon queue |
| 9 | System Health integrations card flips from mocked/stubbed → active/OK | `GET /api/admin/system-health` integrations card status=green AND child.motive.status=ok |
| 10 | No fake GPS / vehicle / driver data generated | grep production `motive_events.body` for fixture markers — none present |
| 11 | Preview/test data not copied into production | spot-check: no event `source: "fixture"` or `test:true` in production `motive_events` |
| 12 | Production data remains in `masci_safety` only | `/api/version.db_name = masci_safety` unchanged |

**Critical hidden gate (probe upgrade):** the current `_probe_motive` in `routes/integration_health.py` returns `mocked=true` even when the API key is present (line 134 comment: *"Configured (live probe not yet implemented)"*). To get Gate 9 to flip to green, the probe needs a live API call (e.g., `GET /v1/users/me` against Motive). This is a **30-LINE code change** scoped to `_probe_motive` only — no new features, no scope creep. Document as a pre-activation prerequisite if you want the System Health card to truthfully report `active`.

---

## 8 · Activation sequence (operator-driven, agent-monitored)

```
0. Confirm production redeploy completed (per PRODUCTION_DEPLOYMENT_GAP_CLOSEOUT_PLAN.md)
   AND post-deploy certification table all-green.
1. Operator obtains Motive API key + webhook secret from Motive dashboard.
2. Operator sets MOTIVE_API_KEY + MOTIVE_WEBHOOK_SECRET in Emergent System Keys.
3. Operator clicks "Redeploy" (mini-deploy to pick up secrets).
4. Operator opens production pod terminal, runs:
       python3 -c "from pymongo import MongoClient; import os; from datetime import datetime, timezone; \
         m=MongoClient(os.environ['MONGO_URL'])[os.environ['DB_NAME']]; \
         m.integration_settings.update_one({'provider':'motive'}, \
           {'\$set':{'enabled':True,'updated_at':datetime.now(timezone.utc).isoformat()}}, upsert=True); \
         print('motive integration_settings seeded')"
5. Operator runs manual kick: curl -X POST .../api/integrations/motive/sync (admin token).
6. Agent verifies Gates 1-12 in §7.
7. If ALL gates 🟢 → integration ACTIVE.  If ANY gate 🔴 → STOP, no fake activation.
8. Operator registers webhook in Motive dashboard.
9. Wait 60 minutes; verify scheduler ticks visible in `/api/admin/motive-reliability`.
10. Document in CHANGELOG.
```

If at any point Gate 10 or Gate 11 trips (fake data observed), HALT the integration. Never silently mask fake data.

---

## 9 · NOT activated by this plan

- MaintainX (separate workstream, similar gates required)
- FleetWatcher (blocked per OMEGA)
- Live Operations Map UI Phase 5B (blocked until Motive coverage ≥20%)
- Stripe, Twilio, FleetWatcher, additional providers

---

## 10 · References

- `/app/backend/services/motive_service.py` — live API client
- `/app/backend/lib/motive_reliability.py` — supervisor loop
- `/app/backend/routes/integration_health.py` — probe definitions
- `/app/memory/PRODUCTION_DEPLOYMENT_GAP_CLOSEOUT_PLAN.md` — prerequisite redeploy
