# MAINTAINX INTEGRATION AUDIT

**Date:** 2026-06-04 18:05 UTC
**Mode:** READ-ONLY (no code changes, no deploys, no DB writes)
**Scope:** Inventory and certify the state of every MaintainX ↔ ForgedOps surface against the 15 capability areas requested.

---

## Executive Verdict

```
OVERALL MAINTAINX INTEGRATION:  PARTIAL  (scaffolding-grade, NOT live)

  Live API calls to MaintainX                : 0
  Configured API key (backend/.env)          : ABSENT (MAINTAINX_API_KEY unset)
  Scheduler ticks calling MaintainX           : 0
  Webhooks live                              : 0 (endpoint exists · awaiting credentials · signature stub uses HMAC-SHA256)
  Webhook signature algo (real)              : UNKNOWN (placeholder HMAC-SHA256 hex digest)
  Mapping infrastructure (Assets/Users)      : COMPLETE (CRUD + CSV + Wizard) — but no IDs populated automatically
  WO → ForgedOps surfacing UI                : PARTIAL (read endpoint + demo dataset + Operations Center counters)
  ForgedOps → MaintainX WO push (failed pre-op / DVIR / damage) | STUB ONLY
  Status sync (asset OOS ⇄ MaintainX status)  | NONE
  Maintenance history visibility              | PARTIAL (asset_holds + Operations Center + master_history)
  Parts / Labor / Attachments / Photos       | NONE (no models, no endpoints, no UI)
  PM (Preventive Maintenance) schedules      | PARTIAL (mapping field exists `maintainx.pm_schedule_id`; nothing reads/writes it)
```

The entire MaintainX integration is currently a **safe scaffold**: provider-aware data model, masked credential store, demo dataset, hardened webhook receiver that fails closed without a secret, manual CSV import, and a paste-and-preview Mappings Wizard — all stable, all auditable, none of it making outbound network calls to MaintainX.

---

## 1 · Capability-by-Capability Matrix

| # | Capability | State | Evidence (code paths) |
| --- | --- | --- | --- |
| 1 | Assets | **PARTIAL** | `asset_mappings` collection, 1:1 `equipment_master ↔ {motive, maintainx}`; CRUD at `/api/admin/integrations/asset-mappings`; CSV import (`kind="maintainx_assets"`); Mappings Wizard (`kind="maintainx_assets"`). **No outbound `GET /assets`** — `MaintainxService.sync_assets()` returns `awaiting_credentials` stub. |
| 2 | Work Orders | **PARTIAL** | Read endpoint `GET /api/integrations/maintainx/work-orders` queries `db.maintainx_work_orders` (collection exists, empty in preview). Demo dataset present (`demo_maintainx_work_orders()`). `MaintainxService.sync_work_orders()` is a stub. **No outbound `GET /work-orders`** and **no outbound `POST /work-orders`** to push from ForgedOps. |
| 3 | Preventive Maintenance | **NOT INTEGRATED** (scaffold field only) | `asset_mappings.maintainx.pm_schedule_id` field exists in the model. Nothing reads it; no PM-schedule fetch or attach endpoint exists. |
| 4 | Equipment Inspections (Pre-Op) | **PARTIAL → MaintainX = NOT INTEGRATED** | Pre-Op submissions flow through `equipment_inspections` → `operations.asset_holds` for breakdown / OOS. `MaintainxService.create_work_order_from_failed_preop(preop_id)` is a stub returning `{"ok": False, "status": "stub"}`. No actual WO is created in MaintainX. |
| 5 | DVIR | **PARTIAL → MaintainX = NOT INTEGRATED** | Live DVIR fan-out (`backend/routes/fleet_ops.py:546-643`) creates internal Shop tasks + Dispatch notifications via `lib/event_fanout`. The defect row carries `external_refs.maintainx_work_order_id: None` placeholder but is never populated. No `services/maintainx_service.create_work_order_from_dvir(...)` exists. |
| 6 | Fleet Return-to-Service | **PARTIAL → MaintainX = NOT INTEGRATED** | RTS lifecycle is fully implemented inside ForgedOps (`/api/dispatch/fleet/defects/{id}/repair` then `/clear` flow). Audit captures `rts_label="returned_to_service"`. **No callback to MaintainX** to close the linked WO or to verify the WO is closed before RTS. |
| 7 | Parts | **NOT INTEGRATED** | No `maintainx_parts` collection, no mapping table, no UI, no endpoints. |
| 8 | Labor | **NOT INTEGRATED** | No labor-time entries, no technician time-on-WO surface, no endpoints. |
| 9 | Status Synchronization | **NOT INTEGRATED** | `asset_holds.kind` & `fleet_defects.status` are ForgedOps-internal lifecycles. No bidirectional sync of WO `status` ⇄ ForgedOps `asset_hold.active` / `fleet_defects.status`. Bus exists in `events.py` reads but nothing writes back. |
| 10 | Attachments | **NOT INTEGRATED** | No attachment download/upload to MaintainX. DVIR / Pre-Op photos live in `safety_doc_storage` (R2) but are never relayed to MaintainX WO. |
| 11 | Photos | **NOT INTEGRATED** | Same as above — photos captured on DVIR / damage / pre-op stay in R2; no MaintainX `photos[]` push or pull. |
| 12 | Notifications | **PARTIAL** | Inbound: `/api/integrations/maintainx/webhook` endpoint exists (hardened, awaiting secret). Outbound: none. ForgedOps does NOT email/SMS/Slack MaintainX events; only internal Shop/Dispatch notification fan-out fires. |
| 13 | API Authentication | **AWAITING CREDENTIALS** | `integration_settings.maintainx.api_key_value` writable via `PATCH /api/admin/integrations/maintainx` (admin-strict, masked on read). `MaintainxService.is_live = enabled && api_key_value`. **No `MAINTAINX_API_KEY` set in `backend/.env`**. **No `httpx` client wired** — service has no `_client()` method. |
| 14 | Error Handling | **PARTIAL** | `integration_error_logs` collection + `write_error_log()` helper; webhook handler catches `process_webhook` exceptions and writes both `sync_log` + `error_log` rows. Test connection endpoint catches exceptions and logs them. **No retry classification (transient vs permanent), no circuit breaker.** |
| 15 | Sync Retry Logic | **NOT INTEGRATED** | No retry queue, no exponential backoff, no `pending_sync` collection, no dead-letter pattern. Failed syncs simply log + return a stub error response. |

---

## 2 · Existing Code Paths

### 2.1 Service layer

```
backend/services/maintainx_service.py        ← 80 LOC stub (placeholders for every method)
```

Defined methods (all stubs):
- `test_connection()`             → `awaiting_credentials` or `stub_live`
- `sync_assets(triggered_by)`     → `awaiting_credentials`
- `sync_users(triggered_by)`      → `awaiting_credentials`
- `sync_work_orders(triggered_by)`→ `awaiting_credentials`
- `process_webhook(raw_body, headers, test_mode)` → logs bytes; never persists
- `create_work_order_from_failed_preop(preop_id)` → `{ok: False, status: "stub"}`
- `create_work_order_from_damage_report(damage_id)` → `{ok: False, status: "stub"}`

### 2.2 Routes package

```
backend/routes/integrations/
  __init__.py            ← registers config + mappings + webhooks + events + wizard + imports/exports
  _deps.py               ← multi-role token gate (Safety / HR / Admin)
  _models.py             ← Pydantic models for AssetMapping / EmployeeMapping / Wizard
  _storage.py            ← provider list, index init, demo dataset, sync/error log helpers, signature verifier stub
  config.py              ← admin settings + test-connection + portal health card
  mappings.py            ← Asset + Employee mapping CRUD + unmapped reports
  imports_exports.py     ← CSV import / export
  wizard.py              ← paste-and-preview Mappings Wizard (preview → commit, audit-logged)
  webhooks.py            ← /api/integrations/maintainx/webhook (hardened, awaiting secret)
  events.py              ← GET /api/integrations/maintainx/work-orders (reads + demo)
  logs.py                ← read sync logs + error logs
```

### 2.3 Cross-portal surfaces

| Surface | File | Touchpoint |
| --- | --- | --- |
| Operations Center | `backend/routes/operations_center.py` | `equipment_holds` / `equipment_down` KPI tiles read `asset_holds` — these will become populated by MaintainX WO sync when live. |
| Operations panel | `backend/routes/operations.py:880-903` | `_provider("maintainx")` returns `{equipment_down, open_work_orders, overdue_pms (placeholder 0), maintenance_holds}` — currently computed from `asset_holds`. |
| Asset Profile | `frontend/src/pages/admin/AssetProfile.jsx` | `<MaintainXPlaceholder>` tab; shows mapping + "live integration coming once API is wired". |
| Master History | `backend/routes/master_history.py:170-178` | Detects `linked_maintainx_work_order_id` and labels rows "· MaintainX WO (mocked)". |
| Integration Health | `backend/routes/integration_health.py:114-124` | Probe `_probe_maintainx()` is config-only; flagged `mocked=true`. |
| Admin UI hub | `frontend/src/pages/admin/AdminIntegrationCenter.jsx` | Tabs · MaintainX provider settings, Asset/Employee mapping tables, Wizard, CSV import. |

### 2.4 Frontend

- `AdminIntegrationCenter.jsx` — full settings + mapping management UI, multiple sub-tabs, data-testid coverage.
- `AssetProfile.jsx` — MaintainX tab placeholder.
- `DispatchIntegrationsTab.jsx` — reads `/api/integrations/maintainx/work-orders` (currently empty / demo only).
- `IntegrationHealthCard.jsx` + `IntegrationEventsCard.jsx` — show provider state + recent events to Safety/HR/Admin tokens.

---

## 3 · Existing API Endpoints

### MaintainX-scoped (admin-strict unless noted)

| Method | Path | Purpose | State |
| --- | --- | --- | --- |
| GET | `/api/admin/integrations/overview` | List both providers | Live (reads `integration_settings`) |
| GET | `/api/admin/integrations/maintainx` | Get MaintainX settings | Live |
| PATCH | `/api/admin/integrations/maintainx` | Update settings (api_key, webhook_secret, demo_mode, enabled, notes) | Live |
| POST | `/api/admin/integrations/maintainx/test` | Calls `MaintainxService.test_connection()` | Stub (returns `awaiting_credentials`) |
| GET | `/api/admin/integrations/asset-mappings?provider=maintainx` | List asset mappings | Live |
| POST | `/api/admin/integrations/asset-mappings` | Create mapping | Live |
| PATCH | `/api/admin/integrations/asset-mappings/{id}` | Update mapping | Live |
| DELETE | `/api/admin/integrations/asset-mappings/{id}` | Delete mapping | Live |
| GET | `/api/admin/integrations/asset-mappings/unmapped` | Unmapped equipment | Live |
| GET | `/api/admin/integrations/employee-mappings?provider=maintainx` | List employee mappings | Live |
| POST/PATCH/DELETE | `…/employee-mappings…` | CRUD | Live |
| POST | `/api/admin/integrations/mappings/wizard/preview` | Paste-and-preview wizard | Live (read-only) |
| POST | `/api/admin/integrations/mappings/wizard/commit` | Commit mapping decisions | Live (audited) |
| GET | `/api/admin/integrations/mappings/wizard/runs[/{id}]` | Wizard audit history | Live |
| POST | `/api/admin/integrations/import-csv` (kind=`maintainx_assets`/`maintainx_users`) | Manual CSV import | Live |
| GET | `/api/admin/integrations/export-csv` | Export mappings | Live |
| GET | `/api/admin/integrations/sync-logs[?integration=maintainx]` | Read sync log | Live |
| GET | `/api/admin/integrations/error-logs[?integration=maintainx]` | Read error log | Live |
| **POST** | **`/api/integrations/maintainx/webhook`** | **Inbound webhook receiver (unauth)** | **Hardened scaffold — awaiting secret; HMAC-SHA256 placeholder algo** |
| GET | `/api/integrations/maintainx/work-orders` | Read WO list (Safety/HR/Admin gate) | Live read (table empty; demo mode injects 3 demo WOs) |
| GET | `/api/integrations/health` | Cross-portal health card | Live |
| GET | `/api/admin/integrations/health` | Admin integrations probe (includes MaintainX config check) | Live |

### MaintainX-scoped (data model only — no live integration)

| Collection | Indexed | Populated | Purpose |
| --- | --- | --- | --- |
| `db.integration_settings` | `provider` unique | YES (seeded both providers at boot) | Credentials & enable/demo flags |
| `db.asset_mappings` | `masci_equipment_id`, `maintainx.asset_id` | Manually | 1:1 equipment ↔ provider IDs |
| `db.employee_mappings` | `masci_employee_id`, `maintainx.user_id` | Manually | Employee ↔ MaintainX user |
| `db.maintainx_work_orders` | `created_at` | Empty in preview | Future cache of WO list pulled from MaintainX |
| `db.integration_sync_logs` | `started_at`, `integration` | Yes (webhook + test_connection rows) | Sync audit |
| `db.integration_error_logs` | `occurred_at`, `integration` | Yes | Error audit |
| `db.integration_wizard_runs` | `started_at`, `kind` | Yes | Mappings Wizard audit |
| `db.asset_holds` | `asset_id`, `kind`, `active` | Yes (internal use) | ForgedOps maintenance holds — **NOT** MaintainX-sourced today |
| `db.fleet_defects` | (multiple) | Yes (internal use) | DVIR / Pre-Op defects · carries `external_refs.maintainx_work_order_id` placeholder field (always `None`) |

---

## 4 · Existing Webhooks

| Webhook | Path | Auth | Behaviour today |
| --- | --- | --- | --- |
| MaintainX inbound | `POST /api/integrations/maintainx/webhook` | Unauth + `X-Maintainx-Signature` header | If `webhook_secret_value` missing AND `test_mode==False` → returns 200 `{ok:false, status:"awaiting_credentials"}` + writes sync log. If secret present → verifies via placeholder HMAC-SHA256 (real algo unknown). On valid signature → `MaintainxService.process_webhook()` (stub — logs bytes, returns `{ok:true, status:"logged_stub", stored:false}`). |

**No outbound webhook calls to MaintainX exist** (i.e. ForgedOps cannot push event notifications to MaintainX).

---

## 5 · Existing Schedulers / Sync Jobs

```bash
grep -rn "scheduler\|asyncio.create_task" backend/server.py | grep -i "maintainx"
# (no results)
```

| Job | Trigger | What it does |
| --- | --- | --- |
| ForgedOps backup scheduler | APScheduler, every ~5min | Backups only — no MaintainX call |
| Integration health probe | On-demand (`GET /api/admin/integrations/health`) | Config-only check of `MAINTAINX_API_KEY` env var |
| MaintainX asset sync | — | **NOT SCHEDULED.** Service method exists as a stub. |
| MaintainX WO sync | — | **NOT SCHEDULED.** Service method exists as a stub. |
| MaintainX user sync | — | **NOT SCHEDULED.** Service method exists as a stub. |

**No background MaintainX traffic is generated by ForgedOps today.**

---

## 6 · Existing Mappings

### Asset (equipment_master ↔ MaintainX)

Mapping doc (`db.asset_mappings`) structure for MaintainX block:

```jsonc
{
  "masci_equipment_id": "uuid",
  "masci_unit_number":  "T-12",
  "masci_equipment_name": "Truck 12",
  "masci_equipment_type": "Tractor Trailer Truck",
  "maintainx": {
    "asset_id":        "string",   // populated manually
    "location_id":     "string",
    "pm_schedule_id":  "string",   // SCAFFOLD only — no consumer
    "last_sync_at":    null,        // never set
    "mapping_status":  "Mapped" | "Unmapped"
  }
}
```

### Employee (employees ↔ MaintainX user)

```jsonc
{
  "masci_employee_id": "uuid",
  "masci_employee_name": "Tom Diesel",
  "maintainx": {
    "user_id":  "string",
    "name":     "string",
    "email":    "string",
    "role":     "string",
    "last_sync_at": null,
    "mapping_status": "Mapped" | "Unmapped"
  }
}
```

### DVIR / Fleet Defect ↔ MaintainX WO (placeholder)

`fleet_defects.external_refs.maintainx_work_order_id` — field exists, always `null`. There is no code path that ever sets it.

### Master History ↔ MaintainX WO (placeholder)

`master_history` rows can carry `linked_maintainx_work_order_id`; UI renders "· MaintainX WO (mocked)" suffix when present. Nothing populates the field.

---

## 7 · Environment & Configuration

| Key | Current value | Required for live |
| --- | --- | --- |
| `backend/.env :: MAINTAINX_API_KEY` | **UNSET** | YES |
| `backend/.env :: MAINTAINX_BASE_URL` | **UNSET** | YES |
| `integration_settings.maintainx.enabled` | `False` (seeded) | Must be `True` |
| `integration_settings.maintainx.api_key_value` | `""` (seeded) | Must be non-empty |
| `integration_settings.maintainx.webhook_secret_value` | `""` (seeded) | Required to enable real webhook verification |
| `integration_settings.maintainx.demo_mode` | `False` | OK for prod |
| `integration_settings.maintainx.test_mode` | `False` | Use during provisioning to capture provider's test pings |

---

## 8 · Risk Surface

| Risk | Status |
| --- | --- |
| Could break running app on credential entry? | No — every code path fails closed and never raises. |
| Could write to MaintainX accidentally? | No — every outbound method is a stub returning a synthetic dict. |
| Could leak credentials? | No — `settings_public_view()` masks `api_key_value` / `webhook_secret_value`, returns `*…last4` and a `_present` boolean. |
| Could swallow real WO push silently? | YES, in the sense that today's stub returns `{ok:false, status:"stub"}` to callers — admins must NOT interpret a stub success as a real WO creation. The UI surface already labels this MOCKED. |

---

## 9 · Capability Summary Table (one-line view)

| # | Capability | Verdict |
| --- | --- | --- |
| 1 | Assets | PARTIAL — mapping infra complete; **no live sync** |
| 2 | Work Orders | PARTIAL — read endpoint + demo only; **no live push or pull** |
| 3 | Preventive Maintenance | NOT INTEGRATED — scaffold field only |
| 4 | Equipment Inspections | NOT INTEGRATED at the MaintainX edge (internal flow live) |
| 5 | DVIR | NOT INTEGRATED at the MaintainX edge (internal fan-out live) |
| 6 | Fleet Return-to-Service | NOT INTEGRATED at the MaintainX edge (internal lifecycle live) |
| 7 | Parts | NOT INTEGRATED |
| 8 | Labor | NOT INTEGRATED |
| 9 | Status Synchronization | NOT INTEGRATED |
| 10 | Attachments | NOT INTEGRATED |
| 11 | Photos | NOT INTEGRATED |
| 12 | Notifications | PARTIAL (webhook receiver hardened · no outbound) |
| 13 | API Authentication | AWAITING CREDENTIALS — masked settings store + service is_live gate |
| 14 | Error Handling | PARTIAL — sync_logs + error_logs + try/except on webhook; **no retry classification** |
| 15 | Sync Retry Logic | NOT INTEGRATED |

— End of MaintainX Integration Audit —
