# MOTIVE RECONCILIATION WORKFLOW
**FORGEDOPS Dispatch Command Center V1 · Audit-Only · 2026-02-10**
**Status:** Architecture-locked · No code

> **Operator doctrine (preserved from `MOTIVE_INTEGRATION_STRATEGY.md`):**
> "Validate, don't surveil." Motive is a **GPS validator and discovery
> feed** — it never creates, retires, or owns an asset. ForgedOps owns
> identity; Motive observes presence.
>
> **Operational reality:** GPS units are installed in trucks/equipment
> **before** field deployment. Therefore, Motive will frequently see a
> new asset BEFORE anyone manually adds it to `equipment_master`. The
> system must surface this without ever creating ghost / shadow rows.

---

## §1 · The Three Reconciliation Buckets

| Bucket | Operational meaning | Source collections |
|---|---|---|
| **A** — In Asset Spine, NOT in Motive | Asset exists operationally but no GPS yet (or GPS dead / out of range) | `equipment_master` rows with no `asset_mappings` row |
| **B** — In Motive, NOT in Asset Spine | GPS device installed; operator hasn't entered the asset yet (or no one approved the mapping) | `motive_events` / Motive `/v3/vehicle_locations` / `/v1/assets` returning a vehicle/asset_id that has no `asset_mappings` row |
| **C** — In both (mapped) | Healthy state | `asset_mappings` row joining `equipment_master.id` ↔ `motive.vehicle_id` or `motive.asset_id` |

Coverage % is computed by `asset_mapping_recon.coverage` and surfaced
through:
- `/api/asset-spine/health` (`motive_coverage_pct`)
- `/api/admin/asset-mapping/coverage`
- `/api/operations-center/asset-spine-tile`

Today's coverage on the MASCI dataset: **31.4%** (693 assets total · 191
mapped · 418 unmapped · 4 duplicates · 208 unsynced) — verified
2026-02-10.

---

## §2 · Bucket A — In Asset Spine, NOT in Motive

### When does this happen?
1. Asset added by Admin before GPS install (e.g. attachments, non-GPS
   equipment).
2. GPS device disconnected / battery dead / out of cell range.
3. Asset retired but Motive mapping deleted.

### Detection
- `services/asset_spine_detection.py:detect_unsynced(db)` — runs nightly
  via `asset_spine_scheduler.py`.
- Returns severity = `low`.

### Workflow
```
Nightly scan runs at 02:00 UTC
   ↓
Findings persisted to asset_spine_health_runs.findings_summary.unsynced
   ↓
Admin dashboard /admin/asset-spine surfaces the count
   ↓
Operator either:
   a. Marks "no GPS expected" (asset stays unsynced — non-GPS equipment)
   b. Investigates GPS hardware (Motive provisioning issue)
   c. Approves a queued mapping (if motive events arriving)
```

### Decision logic
- **Non-GPS class** (attachments, light towers, portables) → expected;
  no action.
- **GPS-class** (truck / trailer / heavy equipment) → operational alert:
  Shop must investigate hardware.

---

## §3 · Bucket B — In Motive, NOT in Asset Spine

### When does this happen?
**This is the most operationally important case.** New equipment
arrives at the yard with a Motive Asset Gateway or ELD already
installed. Motive starts emitting events the moment the device powers
on — typically hours or days before Admin enters the row.

### Detection
- Motive webhook fires when a new vehicle/asset id is observed.
- `motive_service.sync_assets` upserts an `asset_mappings` row with a
  placeholder `masci_equipment_id=None` (when truly new).
- Discovery is also surfaced through `asset_mapping_proposals`
  (existing collection; queued for Admin review).

### Workflow
```
Motive sees a new vehicle_id or asset_id
   ↓
services/motive_service.py:sync_assets writes to asset_mappings
(provider="motive", motive.vehicle_id=… , masci_equipment_id=null,
 status="proposed")
   ↓
asset_mapping_proposals row created (or updated)
   ↓
Admin opens /admin/asset-mapping (AdminAssetMapping.jsx)
   ↓
Operator chooses one:
   ① APPROVE → match to existing equipment_master row
       └ writes asset_mappings.masci_equipment_id
       └ admin_audit_log + audit_events entries
   ② REASSIGN → existing mapping was wrong; rebind to a different equipment_master
   ③ REJECT → "not ours" / lease asset / temporary rental
       └ asset_mappings marked rejected_at; never appears again
   ④ CREATE-AND-MAP → Admin creates a new equipment_master row via
       /api/asset-spine/assets and immediately binds the proposal to it
       (this is the recommended path for genuinely new equipment)
```

### Visibility & cadence
- `/api/admin/asset-mapping/queue` lists proposals for the Admin UI.
- Operations Center "Asset Spine Health" tile counts unmapped Motive
  vehicles (`mapping_queue_depth`).
- Nightly digest (P0.2 reconciler) refreshes the queue and emits a
  finding row.

### Doctrine guard
**Never auto-create** an `equipment_master` row from a Motive event.
The operator must explicitly approve. This preserves the audit chain
and prevents lease/rental/sub-contractor trucks from being silently
absorbed into the fleet.

---

## §4 · Bucket C — In Both (the healthy state)

```
equipment_master.id ↔ asset_mappings.masci_equipment_id
                     ↔ asset_mappings.motive.vehicle_id (or motive.asset_id)
```

Reconciliation continuously verifies the mapping is consistent. If an
asset is retired in Asset Spine but Motive events keep arriving:
- `detect_retired_but_active` fires (severity `high`).
- Admin must decide: re-activate the asset (Motive sees it because it's
  still in the yard) **or** un-map (asset was sold / scrapped / lease
  ended).

---

## §5 · Lifecycle Decision Trees

### 5.1 · New asset appears in Motive
```
Motive emits vehicle_id=ABCD123
   ↓
sync_assets writes asset_mappings(provider=motive, motive.vehicle_id=ABCD123,
                                    masci_equipment_id=null, status=proposed)
   ↓
asset_mapping_proposals row exists
   ↓
[Admin reviews]
   ├─ Match found  → APPROVE: mapping resolved
   ├─ Net-new asset → CREATE-AND-MAP: Admin runs POST /api/asset-spine/assets,
   │                  then approves the proposal → mapping resolved
   ├─ Wrong → REASSIGN to correct asset_id
   └─ Not ours → REJECT
```

### 5.2 · New truck appears in Motive
Same as §5.1. The taxonomy mirror is set on create:
`asset_type=truck`, `asset_category="Dump Trucks"` (or similar; one of
the seeded truck categories).

### 5.3 · New trailer appears in Motive
Same as §5.1. `asset_category="Trailers"`. Trailers often share a Motive
asset_id under their towing truck — the operator's job at REASSIGN time
is to correctly bind the trailer (not the truck) to the trailer mapping.

### 5.4 · New equipment (excavator / dozer / loader) appears in Motive
Motive's `/v1/assets` endpoint (Asset Gateway) returns this. `sync_assets`
sets `asset_kind="equipment"`. The proposal carries make/model/year so
the Admin can match against an existing `equipment_master` row.

### 5.5 · Asset exists in Motive but not in ForgedOps (pure orphan in Motive)
- Admin chooses CREATE-AND-MAP (most common — yard truck not yet
  entered).
- Admin chooses REJECT (lease return / sub-contractor truck).

### 5.6 · Asset exists in ForgedOps but not in Motive
- `detect_unsynced` flags it (severity `low`).
- Admin chooses one of three:
  1. Wait — GPS not yet installed (expected for new portable).
  2. Investigate — should be GPS-bearing; Shop ticket opened.
  3. Mark non-GPS — operator flag (not yet modeled; V2 feature).

---

## §6 · Operational SLAs (proposed)

| Bucket | Target time-to-resolve |
|---|---|
| Bucket B — Motive proposal for a GPS-class asset | **24 h** from first event |
| Bucket A — GPS-class asset unsynced > 14 d | **investigate** |
| Duplicates (any cause) | **48 h** |
| Retired-but-active (Motive still emitting) | **24 h** |

Reconciler runs nightly; counts persist into `asset_spine_health_runs`
so SLA trends are reconstructable later.

---

## §7 · Where This Surfaces

| Surface | Endpoint | UI |
|---|---|---|
| Live coverage % | `/api/asset-spine/health` → `motive_coverage_pct` | `/admin/asset-spine` health dashboard |
| Live queue depth | `/api/admin/asset-mapping/queue` | `/admin/asset-mapping` |
| Nightly digest | `asset_spine_health_runs` rows | `/admin/asset-spine/runs` (existing) |
| OC tile | `/api/operations-center/asset-spine-tile` | Operations Center board (V1 will pin this) |
| Per-asset reconciliation status | `/api/asset-spine/assets/{id}/profile` → `integration_status.motive` | `AssetProfile.jsx` (existing) |

---

## §8 · STOP Condition (no scope creep)

V1 Dispatch Command Center will **consume** the reconciliation outputs
but will **not** rebuild the reconciliation engine. The engine is
already shipped (P0.1–P0.7). The only Dispatch-side change:
- Asset Spine Health tile becomes a first-class tile on Operations
  Center board.
- AssignmentCreateDrawer truck picker filters out Motive-rejected
  proposals (visual clarity — does not change reconciliation).

Everything else stays in the Admin Reconciliation Center.
