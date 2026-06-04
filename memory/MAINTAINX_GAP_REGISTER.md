# MAINTAINX GAP REGISTER & ROADMAP

**Date:** 2026-06-04 18:05 UTC
**Companion to:** `MAINTAINX_INTEGRATION_AUDIT.md`
**Mode:** READ-ONLY (no code changes, no deploys, no DB writes)

This register ranks every missing MaintainX capability against operator priority bands, with explicit attention to the five special-focus areas: Equipment Master Record · DVIR → MaintainX WO · MaintainX WO → RTS Workflow · Asset synchronization · Equipment status synchronization · Maintenance history visibility.

---

## Priority bands

```
P0 — CRITICAL  Blocks operational MaintainX use; safety-relevant; must land before "go live"
P1 — HIGH VALUE Drives day-to-day workflow efficiency; should land within the first month live
P2 — NICE-TO-HAVE  Visibility, polish, executive reporting; lands after P0+P1 stabilize
```

---

## 1 · P0 · CRITICAL GAPS

### P0-A — MaintainX API client + credential wire-up
**State today:** `MaintainxService` has no HTTP client; no `MAINTAINX_API_KEY` env wired; every sync method returns `awaiting_credentials`.
**Why P0:** Nothing else can work until this is in place.
**Capability bucket:** 13 (API Authentication)
**Work required:**
- Add `MAINTAINX_API_KEY` + `MAINTAINX_BASE_URL` to `backend/.env` (preview + production)
- Implement `_client()` returning a reused `httpx.AsyncClient` with bearer auth, 10s timeout, `User-Agent: ForgedOps/maintainx (1.0)`
- Rewrite `test_connection()` to call `GET /v1/users/me` (or equivalent canonical "whoami") and return real latency/status
- Surface API rate limits in `integration_settings.maintainx.settings` so admins can see remaining budget

### P0-B — Asset synchronization (full sync + delta sync)
**State today:** `asset_mappings.maintainx.asset_id` populated only via manual CSV / paste-wizard; `last_sync_at` never set.
**Why P0 & special focus area:** This is the foundational identity bridge — every WO push and status sync depends on a known mapping.
**Capability bucket:** 1 (Assets), special focus #4 (Asset synchronization)
**Work required:**
- Implement `MaintainxService.sync_assets()` → `GET /v1/assets?limit=…&cursor=…` paginated pull
- Upsert into `db.asset_mappings` by `maintainx.asset_id`, attempting a unit_number normalisation match into `equipment_master`; otherwise queue into a new `unmatched_maintainx_assets` review collection
- Stamp `maintainx.last_sync_at`, `mapping_status="Mapped"|"Unmatched"`
- Full sync invocation: `POST /api/admin/integrations/maintainx/sync/assets` (admin-strict, button already designable in UI)
- Delta sync invocation: identical endpoint with `?since=<iso>` parameter; only writes diff rows; logs to `integration_sync_logs`

### P0-C — Equipment status synchronization (asset_holds ⇄ MaintainX asset/WO status)
**State today:** `asset_holds` is ForgedOps-internal; nothing reads MaintainX `asset.status` or WO `status`.
**Why P0 & special focus area:** Operations Center counters (`equipment_down`, `equipment_holds`, `open_work_orders`) currently sum ForgedOps records only. The board lies to the operator if MaintainX has additional open WOs.
**Capability bucket:** 9 (Status Sync), special focus #5
**Work required:**
- On webhook event `workOrder.created` / `workOrder.statusUpdated`:
  - Resolve `maintainx.asset_id → masci_equipment_id` via `asset_mappings`
  - Upsert a row into `db.maintainx_work_orders` with `status`, `priority`, `safety_related`, `equipment_down` flags
  - If `equipment_down=True` and no matching active `asset_hold` exists, create one with `kind="maintainx_wo"`, `source_collection="maintainx_work_orders"`, `external_id=<wo.id>`
  - If WO transitions to `Done`/`Completed`, close the matching `asset_hold` and stamp `closed_by_external_ref={"maintainx_wo_id": …}`
- Reverse mirror: when a ForgedOps `asset_hold` is cleared (Dispatch RTS), call `POST /v1/work-orders/{id}/complete` if it was MaintainX-sourced
- New collection: `db.maintainx_sync_pending` (queue for retryable status writes)

### P0-D — DVIR → MaintainX Work Order push
**State today:** `MaintainxService.create_work_order_from_failed_preop()` and `create_work_order_from_damage_report()` are stubs. The DVIR fan-out at `fleet_ops.py:546-643` only creates internal Shop tasks + Dispatch notifications. `fleet_defects.external_refs.maintainx_work_order_id` is always `null`.
**Why P0 & special focus area:** This is the operator's #1 use case — a failed pre-op should result in a MaintainX WO automatically.
**Capability bucket:** 4 (Equipment Inspections), 5 (DVIR), special focus #2
**Work required:**
- Add `MaintainxService.create_work_order_from_dvir(defect_id, *, kind="oos"|"monitor")` that:
  - Resolves the truck's `maintainx.asset_id` via `asset_mappings`
  - Builds payload: title, description (defect text + category + severity), priority (`Critical` for OOS, `Medium` for monitor), `assetId`, `safetyRelated`, attached photos
  - POSTs `/v1/work-orders`
  - On success: write `fleet_defects.external_refs.maintainx_work_order_id` + `external_refs.maintainx_wo_url`; append audit row `wo_pushed_to_maintainx`
  - On failure: queue into `db.maintainx_sync_pending` with retry classification
- Plumb into `fleet_ops.py` after the existing fan-out block — guarded by `integration_settings.maintainx.enabled`
- Same pattern for `create_work_order_from_damage_report()`

### P0-E — MaintainX WO → RTS Workflow gate
**State today:** Dispatch RTS clear flow (`POST /api/dispatch/fleet/defects/{id}/clear`) requires only that ForgedOps marks `status="repaired"`. There is no requirement that the linked MaintainX WO has been closed.
**Why P0 & special focus area:** Closing a truck back to "Available" while MaintainX still shows the WO open is a compliance gap.
**Capability bucket:** 6 (Fleet RTS), special focus #3
**Work required:**
- On RTS clear: if `defect.external_refs.maintainx_work_order_id` is set, fetch `GET /v1/work-orders/{id}`; refuse the clear (`409 Conflict`) unless WO status ∈ {`Done`,`Completed`,`Cancelled`} OR caller passes `override=true` (audited)
- Optional: allow Dispatch to close the WO from ForgedOps via `POST /v1/work-orders/{id}/complete` on the same call (configurable behaviour)
- Audit captures both pre-state and post-state of the WO

### P0-F — Webhook signature verification (real algorithm)
**State today:** `verify_webhook_signature_stub()` uses placeholder HMAC-SHA256 hex digest. Real MaintainX algorithm has not been documented in code.
**Why P0:** Wrong algorithm = either everything rejects OR everything accepts (depending on direction of mismatch).
**Capability bucket:** 12 (Notifications), 13 (Auth)
**Work required:**
- Consult MaintainX webhook docs; implement `verify_webhook_signature_maintainx(secret, body, header_sig)` correctly
- Capture algo, header name, prefix (e.g. `sha256=…`), timestamp tolerance (replay window) in code comment + `integration_settings.maintainx.settings`
- Add `test_mode=True` capture into `integration_sync_logs` with raw body for the FIRST 5 test pings so operator can validate

### P0-G — Maintenance history visibility (asset profile + master history)
**State today:** `AssetProfile.jsx` has a "MaintainX" tab but renders `<MaintainXPlaceholder>`. `master_history` row labels say "(mocked)".
**Why P0 & special focus area:** Without a real history view, operators can't confirm what MaintainX knows about a unit.
**Capability bucket:** 9 (Status Sync), 14 (Error Handling), special focus #6
**Work required:**
- New endpoint `GET /api/admin/maintainx/assets/{maintainx_asset_id}/history` — proxies a cached WO list + drops mocked label
- Wire `<MaintainXAssetHistory>` component into `AssetProfile.jsx`'s MaintainX tab (renders WOs, status, cost, completed_at, link to MaintainX)
- Remove the "(mocked)" suffix in `master_history.py:178` once `linked_maintainx_work_order_id` is populated by real DVIR push (P0-D)

---

## 2 · P1 · HIGH VALUE GAPS

### P1-A — Sync retry logic + transient/permanent classification
**State today:** Failed syncs log + return; no requeue.
**Capability bucket:** 14 (Error), 15 (Retry)
**Work required:**
- New collection `db.maintainx_sync_pending {id, kind, payload, attempt, next_attempt_at, last_error, last_status_code}`
- Scheduler tick (every 60s) drains pending items with exponential backoff (1m, 5m, 30m, 2h, 12h, give-up)
- 4xx (except 408/429) → mark permanent; 5xx/408/429/network → retry
- Surface pending queue in Admin Integration Center with manual "Retry now" button

### P1-B — Preventive Maintenance schedule attachment
**State today:** `asset_mappings.maintainx.pm_schedule_id` field exists; nothing reads it.
**Capability bucket:** 3 (PM)
**Work required:**
- Pull `/v1/pm-schedules` and `/v1/assets/{id}/pm-schedules` during asset sync; cache to `db.maintainx_pm_schedules`
- Surface overdue PMs on the Asset Profile + Operations Center (`overdue_pms` counter currently `0` placeholder at `operations.py:900`)

### P1-C — Parts & Labor sync (read-only)
**State today:** No models, no endpoints.
**Capability bucket:** 7 (Parts), 8 (Labor)
**Work required:**
- `db.maintainx_parts` cache (id, name, sku, qty_on_hand, location) populated by hourly sync
- `db.maintainx_work_order_labor` cache (technician, minutes, cost) tied to local WO id
- Asset Profile + Master History display parts consumed & labor hours per closed WO

### P1-D — Photo & attachment relay (R2 → MaintainX)
**State today:** DVIR / damage / pre-op photos sit in R2; MaintainX has no copy.
**Capability bucket:** 10 (Attachments), 11 (Photos)
**Work required:**
- When pushing DVIR → WO (P0-D), follow up with `POST /v1/work-orders/{id}/attachments` per photo
- Use Cloudflare R2 pre-signed URL (already supported by `safety_doc_storage`) so we don't have to base64 the bytes through our process
- Idempotency: stamp `external_refs.attachments_pushed=[…r2_keys]` on the defect to avoid duplicates on retry

### P1-E — Outbound notifications (ForgedOps → MaintainX comments)
**State today:** None.
**Capability bucket:** 12 (Notifications)
**Work required:**
- When Dispatch leaves an RTS note or Shop logs a repair note, mirror as a MaintainX WO comment via `POST /v1/work-orders/{id}/comments`
- Audit captures both directions

### P1-F — Bidirectional user mapping live sync
**State today:** `MaintainxService.sync_users()` is a stub.
**Capability bucket:** 1 (Assets) — user side
**Work required:**
- Same pattern as P0-B but against `/v1/users`; upsert into `employee_mappings.maintainx`
- Surface "missing MaintainX user" warnings on Admin Integration Center

---

## 3 · P2 · NICE-TO-HAVE

| ID | Gap | Capability bucket | Sketch |
| --- | --- | --- | --- |
| P2-A | MaintainX KPI tile in Executive Single-Glass | 2 (WO) | Avg WO close time · open WO count · % equipment_down — added to `/admin/operations` overview |
| P2-B | Per-WO cost roll-up at job level | 7+8 | Tag WOs with `project_number` (via DVIR's truck assignment); aggregate cost by project |
| P2-C | Locations sync | 1 | Pull `/v1/locations` and surface in mapping wizard so admins don't paste IDs |
| P2-D | Webhook delivery retry status drawer | 12 | Inspector showing the last 20 inbound webhook payloads (Admin) |
| P2-E | Provider rate-limit panel | 13 | Display remaining API calls per hour and last `Retry-After` value |
| P2-F | Bulk re-sync from "Wizard run" history | 1+2 | Replay a wizard run's external IDs as a re-sync batch |
| P2-G | OOS auto-comment routing on related WOs | 9 | When a related WO closes, comment a confirmation back to the originating defect |
| P2-H | Bilingual labels in WO push payloads | 12 | Send the DVIR title bilingually (EN/ES) so Spanish-speaking techs see the right text |

---

## 4 · Special-Focus Recap Matrix

| Focus area | Audit verdict | Gap roadmap row(s) |
| --- | --- | --- |
| Equipment Master Record | Mapping infra complete; no live sync | P0-B, P0-G |
| DVIR → MaintainX Work Order | Stub only | **P0-D** (also dependencies on P0-A, P0-B) |
| MaintainX WO → RTS Workflow | No gate; ForgedOps RTS independent of WO status | **P0-E** |
| Asset synchronization | Manual only; no sync method live | **P0-B** |
| Equipment status synchronization | Bus exists but disconnected | **P0-C** (depends on P0-F webhook real algo) |
| Maintenance history visibility | Placeholder UI + mocked labels in master_history | **P0-G**, P1-C |

---

## 5 · Suggested Sequencing (no estimates, no commitment)

Operator should slot these into sprint planning. The dependency graph is:

```
P0-A (API client + creds)
   ├── P0-B (Asset sync)            ← unlocks every mapping-dependent flow
   │     └── P0-D (DVIR → WO push)
   │     └── P0-C (status sync) ─── relies on P0-F (real webhook algo)
   │           └── P0-E (RTS gate)
   │           └── P0-G (maintenance history)
   └── P0-F (webhook real algo)     ← unlocks inbound side independently
P1-A through P1-F land in any order after the P0 cluster is stable
P2 backlog landed iteratively from operator demand
```

---

## 6 · "Definition of Done" — Full MaintainX Operational Integration

ForgedOps will be considered fully operationally integrated with MaintainX when **all of the following** are true:

1. `integration_health._probe_maintainx()` returns `status=ok, mocked=false` with real latency.
2. A failed Pre-Op or OOS DVIR submitted in ForgedOps creates a MaintainX WO within 10s, and the resulting WO id is visible on the related defect and master_history row.
3. Dispatch RTS clear of a defect with a linked MaintainX WO refuses to complete unless the WO is closed (or override is audited).
4. The Operations Center `equipment_down` / `open_work_orders` / `overdue_pms` counters reflect the union of ForgedOps and MaintainX state — no MOCKED labels remain.
5. The Asset Profile MaintainX tab shows live WO history pulled directly from MaintainX, with cost, labor minutes, parts consumed, and attachments rendered.
6. Inbound webhook ping-test succeeds end-to-end with the real signature algorithm; `db.integration_sync_logs` shows ≥1 day of `status=Success` rows.
7. `db.maintainx_sync_pending` is empty (or contains only items that have not yet reached their next attempt time) for ≥24 hours.
8. `db.asset_mappings.maintainx.last_sync_at` is non-null and within the last 24 hours for ≥90% of mapped equipment.

---

## 7 · What is explicitly OUT OF SCOPE here

- We did **not** build, modify, or deploy any of the above.
- No new env keys were set.
- No credentials were requested or stored.
- No backend service was restarted.
- No code was changed.
- No database row was written.

This document is a **read-only roadmap**. Operator approval is required before any of the P0 / P1 items are scheduled into a build sprint.

— End of MaintainX Gap Register & Roadmap —
