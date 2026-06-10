# MASTER EQUIPMENT GOVERNANCE
**FORGEDOPS Dispatch Command Center V1 · Asset Identity Contract**
**Date:** 2026-02-10 · **Status:** Architecture-locked · Audit-only · No code

> Supersedes the partial answers in `MASTER_ASSET_GOVERNANCE_ARCHITECTURE.md`
> (2026-02-10 P0.1 baseline) by enumerating **every** governance question
> the directive requires before Dispatch Command Center construction.

---

## §1 · Single Source of Truth

`equipment_master` is the **canonical** asset spine for every GPS-bearing
and field-deployed asset (trucks, trailers, semis, excavators, dozers,
loaders, pavers, mills, attachments). Reads and writes flow through the
`AssetSpine` service in `backend/services/asset_spine.py`.

Vendor mirrors (`motive_events`, `asset_mappings`,
`asset_mapping_proposals`, MaintainX, FleetWatcher) **observe, validate,
and enrich** — they NEVER create or retire canonical assets.

Lower-governance collections retained as-is:
- `equipment` — shop tools / consumables (light schema)
- `trench_safety_assets` — domain-specific (TB-01..TB-07)
- `field_leadership_equipment_catalog` — read-only field-leadership view

---

## §2 · Ownership Matrix

| Action | Admin | Fleet Mgr (planned) | Shop Mgr | Dispatcher | PM | Safety | HR | Driver |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Create asset** | ✅ | ✅ | partial (shop assets only) | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Edit identity** (model, serial, type, VIN, plate) | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Edit operational fields** (assigned project, location hints) | ✅ | ✅ | ✅ | ✅ (truck OOS only) | partial | ❌ | ❌ | ❌ |
| **Retire (deactivate)** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Reactivate** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Transfer (ownership / project / location change)** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Map to Motive / MaintainX / FleetWatcher** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **View asset profile** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | partial | partial (their own truck) |

**Enforcement points (existing):**
- `require_admin` (or `require_admin_strict`) for writes
- `require_any_portal` for reads
- `require_dispatch_or_admin` for assignment-related operational edits
- `require_shop_or_admin` for defect / repair edits

Fleet Manager role is **planned** — for V1 it is folded into Admin.

---

## §3 · Audit Trail (the trust contract)

Every mutation writes **three** rows:

| Layer | Collection | What it captures |
|---|---|---|
| 1 | `admin_audit_log` | action, actor, target_id, before, after, reason |
| 2 | `audit_events` | cross-portal lifecycle event (e.g. ASSET_RETIRED) |
| 3 | `master_history` | identity-level change (model / serial / VIN / plate) |

Plus per-document fields:
- `created_by`, `created_at`
- `updated_by`, `updated_at`
- `last_modified_by`, `last_modified_at`
- `metadata_backfilled_from`, `metadata_backfilled_at` (legacy provenance)

Per-asset visibility surface: `AssetProfile.jsx` already aggregates the
above — the Dispatch Command Center build will add the **transfer
ledger** tab using the `/api/asset-spine/assets/{id}/transfers` route
that already exists (P0.7).

---

## §4 · Duplicate Prevention

**Pre-create guard** (`AssetSpine.create_asset`):
- Rejects insert when `unit_number` or `asset_number` matches an existing
  document (raises `ValueError` → HTTP 409).

**Continuous detection** (`asset_spine_detection.detect_duplicates`):
- Runs nightly via `services/asset_spine_scheduler.py` at 02:00 UTC.
- Groups `equipment_master` rows by `vin_serial_number` (canonical),
  `serial_number`, and `unit_number`.
- Persists findings into `asset_spine_health_runs`.

**Operator surface:** `/admin/asset-spine` (Asset Spine Health dashboard)
shows duplicates with severity. Resolution = Admin retires one, keeps
the other; audit chain captures the decision.

---

## §5 · Orphan Prevention

Orphan = active asset that has shown no operational activity in 30 days.

**Detector** (`asset_spine_detection.detect_orphaned`) checks each
active asset for:
- Recent Motive event (`motive_events` within 30 d)
- Recent inspection (`equipment_inspections` within 30 d)
- Recent dispatch assignment (`dispatch_assignments` within 30 d)

If none of the three → flagged with severity=`medium`. Findings persist
in `asset_spine_health_runs.findings_summary.orphaned`.

**Resolution workflow:** Operations Center Asset Spine Health tile
links to the orphans list; Admin reviews and either retires or schedules
inspection.

---

## §6 · Assignment Tracking

**Where assignment lives:**

| Assignment kind | Source of truth | Read path |
|---|---|---|
| Asset → Driver (live haul) | `dispatch_assignments.driver_id` + `truck_id` | `/api/dispatch/assignments/board` |
| Asset → Project (active deployment) | `equipment_master.current_project_id` + `current_project_name` | `/api/asset-spine/assets/{id}` |
| Driver → Truck (shift session) | `dispatch_driver_sessions.truck_id` | `/api/dispatch/driver/sessions` |
| Driver → Employee record | `dispatch_driver_sessions.employee_id` (iter402) | same |
| Equipment → Trailer pairing | `dispatch_assignments.trailer_id` + `trailer_label` | board endpoint |

**Conflict detection:**
- Same truck on two open assignments → governance finding via
  `dispatch_governance.py`
- Same driver session on two trucks → last-driver-wins (existing logic
  in `routes/dispatch_driver.py:start_shift_route`)

---

## §7 · Transfer Tracking

`asset_transfers` ledger (append-only, exposed via
`/api/asset-spine/assets/{id}/transfers`).

**Recorded transfer types:**
- `CREATE` (write at asset creation)
- `RETIRE` (write at retirement)
- `ACTIVATE` (un-retire)
- `TRANSFER` (project / department / ownership / location change via
  `AssetSpine.transfer_asset`)

Each row carries a structured `delta { before: {...}, after: {...} }`
so the operational reason and the field-level change are reconstructable.

---

## §8 · Status Change Tracking

| Status surface | Authoritative collection | Lifecycle module |
|---|---|---|
| **Asset operational status** (ACTIVE / OOS / MAINT / RETIRED) | `equipment_master.asset_status` (canonical) + `status` (legacy mirror) | `AssetSpine.update_asset` |
| **Haul lifecycle state** (ASSIGNED → COMPLETE etc.) | `dispatch_assignments.current_state` + `state_history[]` | `dispatch_lifecycle._record_transition` |
| **Truck DVIR status** | `fleet_status.status` (available / oos / defect_open / unknown) | `routes/fleet_ops.py:_rebuild_status` |
| **Shop recovery sub-state** | `dispatch_assignments.breakdown_recovery` (acknowledged → diagnosing → waiting_on_parts → repair_active → operational_test → returned_to_service) | `routes/dispatch_continuity.py` |
| **Motive presence** | derived from `motive_events` | `routes/operational_events.py` |

Every transition writes to a corresponding state-event collection:
- `dispatch_state_events` (haul lifecycle)
- `dispatch_continuity_events` (operational exception / recovery)
- `fleet_audit` (DVIR / defect lifecycle)
- `admin_audit_log` (identity / ownership)

---

## §9 · GPS-Linked vs Non-GPS Assets

| Asset class | GPS? | Canonical | Mirror |
|---|---|---|---|
| Truck (any kind) | usually | `equipment_master` | `asset_mappings.motive_asset_id` (when mapped) |
| Trailer | rare | `equipment_master` | `asset_mappings.motive_asset_id` (when mapped) |
| Excavator / dozer / loader | sometimes (Asset Gateway) | `equipment_master` | `asset_mappings.motive_asset_id` (when mapped) |
| Paver / mill | rare | `equipment_master` | none for V1 |
| Attachment (bucket, breaker) | never | `equipment_master` (parent_id) | none |
| Light tower / portable | never | `equipment` (light schema) | none |
| Trench box | never | `trench_safety_assets` | none |

**GPS reconciliation surface:** `routes/asset_mapping_recon.py` and
`AdminAssetMapping.jsx` provide the operator workflow — approve / reject
/ reassign Motive-discovered mappings.

**Non-GPS handling:** Asset Spine treats absent `motive_asset_id` as
**valid**. The orphan detector excludes assets that have any
inspection or dispatch activity even when no Motive events exist,
preventing false alarms on light/portable assets.

---

## §10 · Permitted vs Forbidden Mutations

**Permitted via UI (Admin):**
- `POST /api/asset-spine/assets` — create
- `PATCH /api/asset-spine/assets/{id}` — update identity & operational fields
- `POST /api/asset-spine/assets/{id}/retire`
- `POST /api/asset-spine/assets/{id}/activate`
- `POST /api/asset-spine/assets/{id}/transfer`
- `POST /api/asset-spine/assets/{id}/onboarding/advance`

**Permitted via Webhook (Motive):**
- Create `motive_events` row (telemetry)
- Create `asset_mapping_proposals` row (discovery)

**Forbidden:**
- Any direct write to `equipment_master` outside `AssetSpine` service.
- Any cross-collection asset shadow record.
- Any vendor-driven write to `equipment_master.is_active` (only Admin
  can retire).

---

## §11 · Pillar Scorecard

| Pillar | Why this contract honors it |
|---|---|
| **Powerful** | Single canonical model; every portal reads the same row |
| **Simple** | Operator's mental model: "ForgedOps owns; vendors validate" |
| **Beautiful** | One `AssetProfile.jsx`; one health dashboard; one transfer ledger |
| **Trusted** | Triple-audited (admin_audit_log + audit_events + master_history); idempotent retire; admin-only undo |
| **Proven** | P0.1–P0.7 shipped 2026-02-10 with 693-asset live verification, nightly reconciler running |

---

## §12 · Gaps to Close During Dispatch Command Center V1

1. Surface the **transfer ledger** tab inside `AssetProfile.jsx` (the
   `/transfers` endpoint exists but no UI yet).
2. Add **per-asset live assignment chip** to `AssetProfile.jsx` (already
   computable from `dispatch_assignments`).
3. Wire **Asset Spine Health tile** prominently into the Operations Center
   command surface (endpoint exists; UI binding pending).

Anything outside this list is **out of scope** for V1.
