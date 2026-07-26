# BCSS Release 2 · Program 2 · Wave 3 · Family 3D
# Asset Mapping & Reconciliation — Phase A Repository Discovery

## Executive Discovery Result
**Discovery result:** the repository does **not** support one single, cleanly bounded Family 3D named “Asset Mapping & Reconciliation” as originally hypothesized.

Repository evidence shows **two distinct candidate responsibilities** inside the broader asset-identity space:

1. **Canonical Asset Spine / Asset Registry / Asset Lifecycle ownership**
   - centered on `/app/backend/routes/asset_spine.py`
   - canonical store: `equipment_master`
   - owns canonical asset records, asset identity projection, lifecycle mutation, onboarding, transfer history, taxonomy, and health detection

2. **Source-to-canonical external mapping and operator reconciliation**
   - split across:
     - `/app/backend/routes/integrations/mappings.py`
     - `/app/backend/routes/asset_mapping_recon.py`
     - `/app/backend/services/maintainx_asset_sync.py`
   - stores: `asset_mappings`, `asset_mapping_proposals`, `maintainx_dryrun_reports`
   - owns provider-link CRUD, queue-based Motive dispatch-truck reconciliation, and read-first MaintainX dry-run matching

These two responsibilities are related, but **not singularly owned by one backend family boundary**. The repository therefore supports **Outcome C — Family 3D Must Be Split**.

The strongest repository-backed constitutional reading is:
- canonical asset identity and lifecycle belong to an **Asset Spine** family
- source-system mapping / reconciliation belongs to a separate **Integration Mapping & Reconciliation** family or subfamily
- the existing “Family 3D” hypothesis is too broad to authorize Phase B as one bounded implementation without forcing adjacent-system redesign

## Scope and Constitutional Boundary
- This task was executed as **strict read-only repository discovery**.
- No application code, tests, data, schemas, PRD, ROADMAP, CHANGELOG, deployment, or survivability files were modified.
- The **only permitted artifact** created by this task is:
  - `/app/memory/BCSS_RELEASE2_PROGRAM2_WAVE3_FAMILY3D_ASSET_MAPPING_RECONCILIATION_PHASEA_DISCOVERY.md`

Phase A constitutional boundary evaluated here:
- whether a real repository-backed family exists for asset identity mapping and reconciliation
- whether its ownership is singular or split
- whether its persistent stores, mutation authority, and consumer boundaries are sufficiently bounded for Phase B

Explicitly preserved adjacent families:
- Family 3A — Core Admin Operations
- Family 3B — Operations Actions
- Family 3C — Operational Events

## Repository Coverage

### Backend routes reviewed
- `/app/backend/routes/asset_mapping_recon.py`
- `/app/backend/routes/asset_spine.py`
- `/app/backend/routes/integrations/mappings.py`
- `/app/backend/routes/integrations/maintainx_p0.py`
- `/app/backend/routes/asset_care.py`
- `/app/backend/routes/asset_documents.py`
- `/app/backend/routes/asset_admin_settings.py`
- `/app/backend/routes/project_identity_governance.py`
- `/app/backend/routes/operations_map_contract.py`
- `/app/backend/routes/dispatch_command_center.py`
- `/app/backend/routes/operations_center.py`

### Backend services reviewed
- `/app/backend/services/asset_spine.py`
- `/app/backend/services/asset_spine_detection.py`
- `/app/backend/services/asset_spine_scheduler.py`
- `/app/backend/services/asset_taxonomy.py`
- `/app/backend/services/maintainx_asset_sync.py`
- `/app/backend/services/inspection_classification.py`

### Route registration / server wiring reviewed
- `/app/backend/server.py`
- `/app/backend/routes/integrations/__init__.py`

### Frontend consumers reviewed
- `/app/frontend/src/pages/admin/AdminAssetMapping.jsx`
- `/app/frontend/src/pages/admin/AdminAssetSpineHealth.jsx`
- `/app/frontend/src/pages/admin/AdminAssetAdmin.jsx`
- `/app/frontend/src/pages/admin/AssetProfile.jsx`
- `/app/frontend/src/pages/admin/AdminIntegrationCenter.jsx`
- `/app/frontend/src/pages/AdminAssetThread.jsx`
- `/app/frontend/src/components/asset/AddAssetDialog.jsx`
- `/app/frontend/src/components/dispatch/command/FleetBoard.jsx`
- `/app/frontend/src/app/routing/AppRoutes.jsx`

### Tests and scripts reviewed
- `/app/backend/tests/test_asset_spine_p0_1.py`
- `/app/backend/tests/test_motive_data_001.py`
- `/app/backend/tests/test_motive_data_003.py`
- `/app/backend/tests/test_track_13_31b_d2_asset_admin_ui.py`
- `/app/backend/tests/test_track_13_31b_d7_asset_admin_operational_completion.py`
- `/app/backend/tests/test_track_13_33abc_asset_care.py`
- `/app/backend/tests/test_maintainx_p0_read_first.py`
- `/app/backend/tests/test_track_19_61_asset_thread_promotion.py`
- `/app/backend/scripts/track_15_73_slice1_equipment_audit.py`
- `/app/backend/scripts/track_15_73_slice1_resolver_regression.py`

### Safe runtime evidence gathered
- unauthenticated GETs to candidate endpoints returned `401`, confirming auth gates exist on reviewed asset admin surfaces
- non-mutating collection counts were read for:
  - `equipment_master` = 766
  - `asset_mappings` = 192
  - `asset_mapping_proposals` = 0
  - `asset_spine_health_runs` = 29
  - `asset_transfers` = 138
  - `asset_onboarding_steps` = 0
  - `project_identity_conflicts` = 1243
  - `asset_required_doc_overrides` = 2

### Coverage limitations
- no destructive routes were invoked
- no operator mutation flows were executed
- missing memory documents referenced by code comments could not be reviewed because they are absent from the repository

## Candidate Canonical Owners

### Candidate A — Asset Spine
- **File:** `/app/backend/routes/asset_spine.py`
- **Service:** `/app/backend/services/asset_spine.py`
- **Primary store:** `equipment_master`
- **Supporting stores:** `asset_transfers`, `asset_onboarding_steps`, `asset_spine_health_runs`, `admin_audit_log`, `audit_events`
- **Observed authority:** canonical asset create / update / retire / activate / transfer / onboarding progression / taxonomy review / canonical read projection
- **Repository claim strength:** very strong

### Candidate B — Asset Mapping Reconciliation (dispatch ⇄ Motive proposal queue)
- **File:** `/app/backend/routes/asset_mapping_recon.py`
- **Primary store:** `asset_mapping_proposals`
- **Mutates:** `asset_mappings.masci_equipment_id` on operator approval
- **Observed authority:** queue-based proposal generation and operator approval for unresolved dispatch truck links
- **Repository claim strength:** moderate but narrow

### Candidate C — Integration Center Asset Mappings CRUD
- **File:** `/app/backend/routes/integrations/mappings.py`
- **Primary store:** `asset_mappings`
- **Observed authority:** direct asset mapping CRUD for Motive + MaintainX identifiers linked to canonical `equipment_master` rows
- **Repository claim strength:** very strong for provider-link ownership

### Candidate D — MaintainX read-first reconciliation
- **Files:**
  - `/app/backend/routes/integrations/maintainx_p0.py`
  - `/app/backend/services/maintainx_asset_sync.py`
- **Primary store:** `maintainx_dryrun_reports` only when explicitly saved
- **Observed authority:** read-first matching, duplicate-risk analysis, dry-run reporting
- **Repository claim strength:** moderate for reconciliation intelligence, weak for canonical mutation ownership

### Discovery conclusion on candidate owners
No single candidate owns the entire hypothesis. The repository evidences **split ownership**:
- canonical asset identity owner = Asset Spine
- external-provider mapping owner = Integration Center asset mappings
- operational dispatch mapping cleanup owner = asset_mapping_recon queue
- MaintainX reconciliation owner = dry-run integration diagnostic surface

## Route and Registration Map

### Asset mapping reconciliation routes
**Registered in `server.py`:**
- `from routes.asset_mapping_recon import build_asset_mapping_router`
- mounted as `/api/admin/asset-mapping/*`

**Observed endpoints in `/app/backend/routes/asset_mapping_recon.py`:**
- `POST /api/admin/asset-mapping/scan`
- `GET /api/admin/asset-mapping/queue`
- `POST /api/admin/asset-mapping/{prop_id}/approve`
- `POST /api/admin/asset-mapping/{prop_id}/reject`
- `POST /api/admin/asset-mapping/{prop_id}/reassign`
- `POST /api/admin/asset-mapping/bulk-approve`
- `GET /api/admin/asset-mapping/coverage`
- `GET /api/admin/asset-mapping/audit`
- `GET /api/admin/asset-mapping/top-unmapped`
- `GET /api/admin/asset-mapping/impact-preview/{prop_id}`
- `GET /api/admin/asset-mapping/operational-impact`
- `GET /api/admin/executive-summary`

### Asset Spine routes
**Registered in `server.py`:**
- `register_asset_spine_routes(app, db, require_admin, _require_any_portal_token)`

**Observed endpoint families in `/app/backend/routes/asset_spine.py`:**
- canonical assets list / detail / profile
- universal asset resolver
- create / patch / retire / activate / transfer
- onboarding advance / status
- health / scan / runs
- taxonomy registry / classify preview / by-unit resolver / review-needed / apply-legacy-crosswalk

### Integration Center mapping routes
**Registered via `/app/backend/routes/integrations/__init__.py`:**
- `register_mapping_routes(api_router, db, require_admin)`

**Observed asset-specific endpoints:**
- `GET /api/admin/integrations/asset-mappings`
- `POST /api/admin/integrations/asset-mappings`
- `PATCH /api/admin/integrations/asset-mappings/{id}`
- `DELETE /api/admin/integrations/asset-mappings/{id}`
- `GET /api/admin/integrations/asset-mappings/unmapped`

### MaintainX dry-run reconciliation routes
**Registered via Integration Center:**
- `GET /api/admin/maintainx/p0/config`
- `POST /api/admin/maintainx/p0/test`
- `POST /api/admin/maintainx/p0/dryrun`
- `GET /api/admin/maintainx/p0/dryrun-reports`
- `GET /api/admin/maintainx/p0/dryrun-reports/{id}`

### Related but non-owner routes
- `/api/asset-care/*` in `asset_care.py` — read-only readiness / alert surfaces
- `/api/asset-spine/assets/{id}/documents*` in `asset_documents.py` — asset document lane over shared attachment storage
- `/api/admin/project-identity/*` in `project_identity_governance.py` — project identity governance, not asset identity governance

## Data Stores and Schemas

### `equipment_master`
- strongest repository-backed canonical asset store
- used by Asset Spine service as the **single source-of-truth collection**
- supports canonical identity fields, taxonomy, lifecycle status, ownership, document mirror fields, and external IDs

### `asset_mappings`
- provider-link crosswalk store
- used by Integration Center mapping CRUD
- also consumed by `asset_mapping_recon.py`, `asset_spine.py`, `asset_spine_detection.py`, `maintainx_asset_sync.py`, and Operational Events / verification-adjacent consumers
- holds `masci_equipment_id` plus nested provider-specific subdocs (`motive`, `maintainx`)

### `asset_mapping_proposals`
- operator-facing proposal queue
- created and maintained by `asset_mapping_recon.py`
- statuses evidenced: `Imported`, `Matched`, `Verified`, `Rejected`
- runtime count observed: `0`

### `asset_spine_health_runs`
- read-only detector run log for Asset Spine health scans
- written by `AssetSpine.scan_health()`
- runtime count observed: `29`

### `asset_transfers`
- transfer / retire provenance ledger for Asset Spine lifecycle events
- runtime count observed: `138`

### `asset_onboarding_steps`
- onboarding history store
- mirrored latest onboarding state also lives in `equipment_master.onboarding`
- runtime count observed: `0`

### `maintainx_dryrun_reports`
- read-first audit/report store for MaintainX dry-run reconciliation
- only written when caller explicitly sets `save=true`

### `asset_required_doc_overrides`
- small configuration store for required-document overrides
- runtime count observed: `2`
- belongs to asset admin/readiness configuration, not core mapping ownership

### `project_identity_conflicts`
- runtime count observed: `1243`
- belongs to project identity governance, not asset mapping identity, despite being surfaced in Asset Spine Health UI

### Audit / evidence stores touched by asset systems
- `admin_audit_log`
- `audit_events`

### Schema posture conclusion
The repository does not implement one unified “asset reconciliation store.” It implements:
- canonical asset registry store
- provider crosswalk store
- proposal queue store
- dry-run report store
- health-run store
- transfer lineage store

This is a structural argument against a single undifferentiated Family 3D.

## Asset Domain Inventory

### Canonical heavy/mobile assets
- source store: `equipment_master`
- asset domains evidenced through taxonomy and UI comments:
  - heavy equipment
  - trucks
  - trailers
  - trench safety assets
  - GPS / machine control
  - survey equipment
  - technology equipment
  - fire protection fallback lane via `fire_extinguishers` in resolver bridge

### Telematics-linked assets
- Motive vehicle / asset IDs in `asset_mappings`, `equipment_master`, and Motive consumers
- FleetWatcher asset IDs present in Asset Spine canonical fields and admin UI
- MaintainX asset IDs present in Asset Spine canonical fields and mapping CRUD / dry-run matching

### Assignment-related asset domains
- dispatch truck identities through `dispatch_assignments.truck_id`
- current project and location identity in `equipment_master`
- asset transfer lineage in `asset_transfers`

### Domain conclusion
Not all asset domains share one lifecycle:
- registry/lifecycle domains are owned by Asset Spine
- provider-link / external-source domains are owned by mapping + integration layers
- dispatch-truck reconciliation is a narrower operational reconciliation lane

## Source-System Inventory

| Source | Source Type | Integration Point | Identifiers Supplied | Repository Role |
|---|---|---|---|---|
| Internal canonical asset admin | internal canonical | `asset_spine.py`, `AdminAssetAdmin.jsx`, `AddAssetDialog.jsx` | `id`, `asset_id`, `unit_number`, taxonomy, lifecycle fields | canonical registry owner |
| Motive | external telematics | `asset_mappings`, `motive_service.py`, `asset_mapping_recon.py`, `asset_spine_detection.py`, Family 3C consumers | `vehicle_id`, `asset_id`, VIN, name, make/model/year | external reference / telemetry source |
| MaintainX | external maintenance | `integrations/mappings.py`, `maintainx_asset_sync.py`, `maintainx_p0.py` | `maintainx.asset_id`, unit number, serial, VIN, make/model/year | external source for matching + dry-run reconciliation |
| FleetWatcher | external/provider placeholder | Asset Spine canonical fields + admin UI only | `fleetwatcher_asset_id` | referenced as mapping field; no deep connector evidence reviewed here |
| Dispatch assignments | internal operational reference source | `asset_mapping_recon.py`, dispatch/operations center consumers | `truck_id`, `asset_id`, project refs | operational reference requiring reconciliation |
| Equipment inspections / DVIR | internal downstream operational record | `inspection_classification.py`, `asset_spine.py`, resolver regression script | `equipment_unit`, `asset_id`, classification context | downstream consumer / identity test surface |
| Operational Events | internal canonical event family | `operational_events`, `asset_mapping_recon.py`, `asset_spine` consumers | actor-linked project presence | dependent consumer/enrichment surface, not asset owner |

### Source authority determination
- canonical asset registry authority: `equipment_master`
- provider crosswalk authority: `asset_mappings`
- dispatch-truck mismatch triage authority: `asset_mapping_proposals`
- MaintainX reconciliation authority: dry-run diagnostic only, not canonical mutation

## Identifier Inventory

### Canonical internal identifiers
- `equipment_master.id`
- `equipment_master.asset_id`
- `equipment_master.unit_number`
- `equipment_master.asset_number`

### External/provider identifiers
- `motive_vehicle_id`
- `motive_asset_id`
- `maintainx_asset_id`
- `fleetwatcher_asset_id`
- `gps_device_id`

### Descriptive/secondary identifiers
- `serial_number`
- `vin`
- `vin_serial_number`
- `license_plate`
- `display_label` / `label` / `asset_name`
- dispatch `truck_id`

### Identifier origin and behavior
- `equipment_master.id` behaves as the strongest canonical identity key across Asset Spine CRUD, transfer ledger, onboarding, and profile reads
- `unit_number` is heavily reused as operator-facing asset reference and search token
- `asset_mappings.masci_equipment_id` links external provider rows back to canonical asset identity
- Asset Spine universal resolver probes `id`, `asset_id`, `unit_number`, `asset_number`, `serial_number`, and `vin`
- MaintainX dry-run matching normalizes unit, serial, and VIN aggressively for duplicate-risk classification
- `asset_mapping_recon.py` uses `dispatch_assignments.truck_id` as a reconciliation key even though that field is operational, not canonical

### Identifier risk
The repository supports **multiple valid lookup identifiers**, but this increases the chance of split-family confusion if registry identity and provider mapping are treated as one single family.

## Identity-Integrity Analysis

### Repository-backed identity chain
**Source identity → matching → canonical identity → references → audit → downstream use**

1. Canonical asset identity is centered on `equipment_master.id`
2. Asset Spine projects canonical fields from `equipment_master`
3. External IDs may live in two places:
   - directly on `equipment_master` (`motive_vehicle_id`, `maintainx_asset_id`, etc.)
   - indirectly in `asset_mappings`
4. Downstream consumers frequently use:
   - `asset_id`
   - `unit_number`
   - `masci_equipment_id`
   - `truck_id`
5. Audit for canonical asset mutations exists through `admin_audit_log` and `audit_events`
6. Transfer lineage persists in `asset_transfers`
7. Onboarding history persists in `asset_onboarding_steps`

### Stable identity support
- **Strongly evidenced:** stable canonical identity for Asset Spine record lifecycle
- **Partially evidenced:** alias retention via resolver support for multiple identifiers
- **Weakly evidenced:** merge history / split history for duplicate canonical assets — not found
- **Not evidenced:** a unified lineage model tying provider-link changes, proposal approvals, and canonical asset mutations together under one immutable chain

### Identity-fork risk
Because provider IDs appear both:
- embedded on `equipment_master`, and
- in `asset_mappings`

the repository has **dual reference surfaces** for external identity. This is a major reason the hypothesis cannot be certified as one family without narrowing or splitting.

## Mapping Architecture

### Mapping store
`asset_mappings` is the primary crosswalk store.

### Direct mapping architecture
In `/app/backend/routes/integrations/mappings.py`:
- mapping docs reference `masci_equipment_id`
- provider subdocs hold nested Motive and MaintainX identifiers
- create route denormalizes display fields from `equipment_master`
- 1:1 enforcement exists at create time for `masci_equipment_id`
- update route restamps `mapping_status`
- delete route removes mapping rows entirely

### Proposal-based mapping architecture
In `/app/backend/routes/asset_mapping_recon.py`:
- `dispatch_assignments.truck_id` values are scanned
- candidate Motive links are scored against `asset_mappings` rows + sampled `equipment_master`
- proposals are persisted to `asset_mapping_proposals`
- operator approval writes back to `asset_mappings.masci_equipment_id`

### Read-first reconciliation architecture
In `/app/backend/services/maintainx_asset_sync.py`:
- MaintainX assets are normalized
- compared against existing mapping rows and `equipment_master`
- classified into deterministic buckets
- optionally saved as a dry-run report
- explicitly does **not** mutate `equipment_master` or `asset_mappings`

### Mapping method classification
- Integration Center asset mapping CRUD: **manual / imported / operator-authored**
- Motive proposal queue: **rule-based deterministic + fuzzy fallback + operator approval**
- MaintainX dry-run: **read-first deterministic + heuristic classification**

## Reconciliation Architecture

### Reconciliation meaning in repository reality
“Reconciliation” is **not one thing**. At least three distinct meanings exist:

1. **Dispatch truck identity closure**
   - `dispatch_assignments.truck_id` → `asset_mappings.masci_equipment_id` → Motive IDs

2. **External-provider asset matching**
   - MaintainX asset records → canonical `equipment_master`

3. **Fleet health / duplicate / unsynced detection**
   - duplicate VIN/serial/unit checks
   - retired-but-active checks
   - orphaned/no-signal checks
   - unmapped active asset checks

### Reconciliation triggers
- operator-initiated scan (`/admin/asset-mapping/scan`)
- admin dry-run (`/admin/maintainx/p0/dryrun`)
- scheduler-driven health scan (`asset_spine_nightly_loop`)
- on-demand Asset Spine health scan

### Reconciliation persisted outputs
- `asset_mapping_proposals`
- `maintainx_dryrun_reports` (optional)
- `asset_spine_health_runs`
- `asset_mappings` updates after operator approval

### Reconciliation conclusion
The repository supports **multiple reconciliation engines**, each bounded differently. This is the core evidence for **split outcome**.

## Canonical Ownership Analysis

### Canonical asset owner
**Owner:** Asset Spine (`routes/asset_spine.py` + `services/asset_spine.py`)

Evidence:
- code comments explicitly state `equipment_master` is the single source-of-truth collection
- Asset Spine handles create/update/retire/activate/transfer/onboarding
- Asset Spine projects the canonical asset view for readers
- scripts and UI comments explicitly call `equipment_master` authoritative

### Canonical provider-link owner
**Owner:** Integration Center asset mapping CRUD (`routes/integrations/mappings.py`)

Evidence:
- explicit create/update/delete endpoints on `asset_mappings`
- 1:1 enforcement at mapping creation
- denormalized asset display fields pulled from canonical master at write time

### Canonical operator queue owner for dispatch-truck reconciliation
**Owner:** `routes/asset_mapping_recon.py`

Evidence:
- builds proposal queue in `asset_mapping_proposals`
- approves/rejects/reassigns proposals
- mutates `asset_mappings.masci_equipment_id` when operator approves

### Ownership classification
- asset registry ownership: **singular**
- mapping reconciliation ownership: **distributed intentionally, but constitutionally fragmented**
- broad Family 3D ownership: **unresolved as one family**

## Source-to-Canonical Matrix

| Source | Source Identifier | Normalization Path | Canonical Asset Store | Mapping Store | Conflict Rule | Downstream Consumers |
|---|---|---|---|---|---|---|
| Internal asset admin | `asset_number`, `unit_number`, canonical fields | Asset Spine create/update | `equipment_master` | optional `asset_mappings` later | uniqueness on create by unit/asset number | Asset Admin UI, Asset Profile, Asset Thread, readiness, docs |
| Dispatch assignments | `truck_id` | `asset_mapping_recon.score_match()` + proposal queue | indirectly `equipment_master` via proposal evidence | `asset_mapping_proposals` → `asset_mappings` on approval | operator approval required | verification-adjacent trust surfaces, dispatch visibility |
| Motive mapping rows | `motive.vehicle_id`, `motive.asset_id`, provider metadata | Integration Center CRUD or proposal approval | linked to `equipment_master` by `masci_equipment_id` | `asset_mappings` | duplicate mapping samples flagged in audit, no unified trust chain | Operational Events enrichment, Asset Spine profile, FleetBoard |
| MaintainX assets | `maintainx_asset_id`, unit, VIN, serial | `maintainx_asset_sync.run_asset_dryrun()` | matched against `equipment_master` only | existing `asset_mappings` consulted, `maintainx_dryrun_reports` optional | duplicate-risk and conflict buckets | Integration Center P0 reports |
| Inspection / pre-op inputs | `equipment_unit` | `asset-spine/taxonomy/by-unit/{u}` resolver | `equipment_master` | none directly | not_found vs unit_number vs display_label_strip | inspection classification, resolver regression scripts |

## Constitutional Ownership Matrix

| Capability | Canonical Owner | Store | Mutation Owner | Read Consumers | Audit Owner | Trust Owner | Notification Owner | Status |
|---|---|---|---|---|---|---|---|---|
| Canonical asset registry | Asset Spine | `equipment_master` | Asset Spine | Asset Admin, Asset Profile, Asset Thread, readiness, dispatch/ops visibility | `admin_audit_log` + `audit_events` | absent/unclear | absent | implemented |
| Asset lifecycle transfer history | Asset Spine | `asset_transfers` | Asset Spine | Asset Profile, `/asset-transfers` UI | Asset Spine + transfer rows | absent/unclear | absent | implemented |
| Asset onboarding history | Asset Spine | `asset_onboarding_steps` + mirror in `equipment_master.onboarding` | Asset Spine | onboarding readers | Asset Spine audit | absent/unclear | absent | implemented but sparse in runtime |
| Asset taxonomy normalization | Asset Spine + `asset_taxonomy.py` | `equipment_master` | Asset Spine admin routes | taxonomy endpoints, inspections, AdminAssetAdmin | Asset Spine audit on canonical writes | absent/unclear | absent | implemented |
| Asset health detection | Asset Spine detectors | `asset_spine_health_runs` | Asset Spine scan route / scheduler | AdminAssetSpineHealth | persisted scan runs | absent | absent | implemented |
| Provider link CRUD | Integration Center mappings | `asset_mappings` | Integration Center mapping routes | AdminIntegrationCenter, Asset Spine profile, ops/dispatch readers | limited / unclear | absent/unclear | absent | implemented |
| Dispatch truck mapping proposals | Asset Mapping Recon | `asset_mapping_proposals` | Asset Mapping Recon | AdminAssetMapping, Executive Summary | queue row timestamps only | absent | absent | implemented |
| MaintainX read-first dry-run reconciliation | MaintainX P0 | `maintainx_dryrun_reports` only if saved | MaintainX P0 route | MaintainxP0Tab / admin reports | report collection | absent | absent | implemented |
| Asset readiness / renewal surfacing | Asset Care | no dedicated new store; reads existing | read-only | AdminAssetAdmin/readiness | none beyond source records | absent | static/deferred matrix only | implemented |

## Mutation Matrix

| Mutation | Route/Function | Auth | Validation | Persistence | Audit | Trust | Notification | Idempotency | Atomicity |
|---|---|---|---|---|---|---|---|---|---|
| Create canonical asset | `POST /api/asset-spine/assets` → `AssetSpine.create_asset()` | admin | unit/asset number uniqueness; required asset_number | `equipment_master` | `admin_audit_log`, `audit_events` | not evidenced | none | not idempotent on repeated create | single-row write |
| Update canonical asset | `PATCH /api/asset-spine/assets/{id}` → `update_asset()` | admin | legal-key allowlist | `equipment_master` | `admin_audit_log`, `audit_events` | not evidenced | none | patch-style, not token-idempotent | single-row write |
| Retire asset | `POST /api/asset-spine/assets/{id}/retire` | admin | existing asset check | `equipment_master` + `asset_transfers` | Asset Spine audit | not evidenced | none | effectively repeat-safe once retired | multi-write, best-effort |
| Activate asset | `POST /api/asset-spine/assets/{id}/activate` | admin | existing asset check | `equipment_master` | Asset Spine audit | not evidenced | none | repeat-safe enough | single-row write |
| Transfer asset | `POST /api/asset-spine/assets/{id}/transfer` | admin | non-empty delta required | `equipment_master` + `asset_transfers` | Asset Spine audit | not evidenced | none | not explicitly idempotent | multi-write, best-effort |
| Advance onboarding | `POST /api/asset-spine/assets/{id}/onboarding/advance` | admin | step allowlist | `asset_onboarding_steps` + `equipment_master.onboarding` mirror | Asset Spine audit | not evidenced | none | partially idempotent by overwrite semantics, not guaranteed | multi-write, best-effort |
| Create asset mapping | `POST /api/admin/integrations/asset-mappings` | admin | canonical asset existence + one mapping per master row | `asset_mappings` | not evidenced in reviewed code | absent | none | create-only, 409 on duplicate | single-row write |
| Update asset mapping | `PATCH /api/admin/integrations/asset-mappings/{id}` | admin | existing row check | `asset_mappings` | not evidenced | absent | none | patch-style | single-row write + status restamp |
| Delete asset mapping | `DELETE /api/admin/integrations/asset-mappings/{id}` | admin | existing row check | `asset_mappings` delete | not evidenced | absent | none | destructive | single-row delete |
| Build proposal queue | `POST /api/admin/asset-mapping/scan` | admin | pure scan/scoring | `asset_mapping_proposals` | queue timestamps only | absent | none | intended idempotent by truck_id reuse | many independent writes |
| Approve proposal | `POST /api/admin/asset-mapping/{id}/approve` | admin | proposal exists | `asset_mappings` update + proposal status update | minimal row metadata only | absent | none | repeat-ish but not explicitly guarded | multi-write |
| Reject proposal | `POST /api/admin/asset-mapping/{id}/reject` | admin | proposal exists | proposal status update | minimal row metadata only | absent | none | repeat-ish | single-row write |
| Reassign proposal | `POST /api/admin/asset-mapping/{id}/reassign` | admin | proposal + mapping exists | `asset_mappings` update + proposal update | minimal row metadata only | absent | none | not explicitly idempotent | multi-write |
| MaintainX dry-run save | `POST /api/admin/maintainx/p0/dryrun?save=true` | admin | config / connectivity / report generation | `maintainx_dryrun_reports` only | report row itself | absent | none | effectively new report per run | single-row insert |

## Authentication and Authorization

### Asset Spine auth
- read endpoints depend on `require_any_portal_dep`
- mutation endpoints depend on `require_admin_dep`
- safe runtime probe returned `401` for unauthenticated `/asset-spine/*` endpoints

### Asset Mapping Recon auth
- all routes depend on `require_admin_dep`
- safe runtime probe returned `401` for unauthenticated `/admin/asset-mapping/queue`

### Integration Center asset mapping auth
- admin-only via `require_admin`

### Asset Care auth
- read-only routes gated by `require_admin_or_asset_admin_dep` when available; fallback to admin gate otherwise

### Auth contradiction note
Tests across the repository still show a mix of legacy `POST /api/admin/login` and newer `POST /api/auth/multi-login` patterns for admin token acquisition. This is an auth-contract consistency concern, but it belongs to shared auth governance, not uniquely to the Family 3D candidate.

## Lifecycle Analysis

### Canonical asset lifecycle (repository-backed)
Observed lifecycle from Asset Spine:

Create → Update → Transfer / Onboarding → Read profile → Retire / Activate → Preserve history

Persisted checkpoints:
- canonical row in `equipment_master`
- audit in `admin_audit_log` and `audit_events`
- transfer lineage in `asset_transfers`
- onboarding lineage in `asset_onboarding_steps`

### Mapping proposal lifecycle
Observed lifecycle from `asset_mapping_recon.py`:

Dispatch truck discovered → score against Motive-linked mapping rows → proposal persisted in `asset_mapping_proposals` → operator approve/reject/reassign → `asset_mappings.masci_equipment_id` updated (approve/reassign only)

### MaintainX reconciliation lifecycle
Observed lifecycle from `maintainx_asset_sync.py`:

Pull external assets → normalize → classify → duplicate-risk analysis → produce report → optionally persist `maintainx_dryrun_reports`

### Lifecycle break conclusion
These are **three distinct lifecycles**, not one unified family lifecycle. Phase B as one family would require choosing which lifecycle is actually in-scope.

## Failure Semantics

### Asset Spine
- canonical mutations attempt audit writes best-effort
- transfer and onboarding lineage inserts are wrapped in try/except warnings, so canonical state may succeed while lineage insert fails
- health scan persists run rows best-effort

### Asset Mapping Recon
- scan is idempotent by proposal reuse on `truck_id`
- proposals in terminal statuses `Verified` / `Rejected` are preserved on rescans
- approval path updates `asset_mappings` and then proposal status; no transaction evidence found

### MaintainX dry-run
- explicit doctrine: never raises externally; errors collected into report dict
- no writes to canonical stores
- optional report persistence only

### Failure semantic conclusion
Failure semantics are **family-specific by subsystem**, not unified across the broad hypothesis.

## Idempotency and Concurrency

### Idempotent / retry-safe evidence
- `asset_mapping_recon.scan()` reuses existing proposal rows by `truck_id`
- MaintainX dry-run is read-first and safe when `save_report=False`
- retired/active toggles are largely repeat-safe at state level

### Concurrency / atomicity gaps
- no transaction evidence found for multi-write asset transfer / retire / onboarding operations
- no transaction evidence found for proposal approval updating both `asset_mappings` and `asset_mapping_proposals`
- no lock / compare-and-set semantics found for mapping conflict resolution in candidate family files

### Classification
- canonical asset registry: partially concurrency-safe but not transactionally unified
- provider mapping reconciliation: partially idempotent, not transactionally unified

## Audit Integrity

### Strongest audit evidence
- Asset Spine explicitly writes to `admin_audit_log` and `audit_events`
- before/after snapshots preserved for asset create/update/transfer/retire/activate
- transfer history has its own lineage rows

### Partial audit evidence
- `asset_mapping_recon.py` records `verified_at`, `verified_by`, and timestamps in proposal rows, but no append-only audit trail was evidenced
- `integrations/mappings.py` did not show append-only audit writes in the reviewed code
- MaintainX dry-run audit is the saved report row itself, not a trust-style immutable mutation ledger

### Audit classification
- Asset Spine canonical mutations: **partial to strong**
- mapping reconciliation approvals: **partial**
- provider mapping CRUD: **unclear / partial**

## Trust Spine Participation

### Evidence found
- No explicit `trust_spine` imports or Trust Spine workflow emissions were found in:
  - `asset_spine.py`
  - `asset_mapping_recon.py`
  - `integrations/mappings.py`
  - `maintainx_asset_sync.py`
  - `asset_care.py`

### Determination
Family 3D candidate workflows do **not** show repository-evidenced Trust Spine participation in the reviewed files.

### Constitutional consequence
This is not a discovery-time repair target, but it is a Phase B boundary concern if any future candidate family requires Trust participation for its mutation flows.

## Notification Participation

### Evidence found
- `asset_care.py` exposes a static `/notifications-matrix` with explicit delivery posture notes
- matrix comments state dashboard is live, but in-app/email/SMS delivery is deferred or out of scope
- no active notification emission path was evidenced in mapping/reconciliation owner files

### Determination
- canonical asset reconciliation and provider mapping candidate systems do **not** currently evidence active notification sequencing ownership
- notification behavior is mostly absent or documentation-only in reviewed candidate files

## Family 3C Operational Events Boundary

**Family 3C owns:** canonical normalized operational presence events in `operational_events`, derived from raw telemetry and verified locations.

**Candidate Family 3D space owns:** canonical asset identity and/or provider-link reconciliation, depending on which candidate subfamily is selected.

**Integration boundary evidenced in repository:**
- Asset Mapping Recon uses `operational_events` only indirectly in impact/trust-style projections (`operational-impact`, `executive-summary`)
- Asset Spine Health and profile views consult mapping and event-adjacent telemetry, but do not own operational event materialization
- Family 3C may depend on `asset_mappings` and `equipment_master` to enrich asset identity, but it remains the event owner

### Boundary determination
The boundary is clear **only if** Family 3D is narrowed or split:
- Family 3C = event truth
- Asset registry/mapping family = asset identity truth
- integration = lookup/enrichment only

## Family 3B Operations Actions Boundary

### Evidence found
- `project_identity_governance.py` scans `operations_actions` for project identity drift, but does not own operations action mutation
- no reviewed asset mapping/reconciliation files created canonical Operations Actions rows
- `asset_mapping_recon.py` surfaces “operational impact” and “executive summary,” but not command creation

### Boundary determination
Family 3B remains canonical command ownership. Candidate Family 3D space does not evidence an independent action engine.

## Family 3A Core Admin Boundary

### Evidence found
- `AdminAssetSpineHealth.jsx`, `AdminAssetMapping.jsx`, and `AdminIntegrationCenter.jsx` expose read-only visibility / operator review surfaces
- `asset_care.py` is an observability and readiness surface over existing records

### Boundary determination
Read-only admin observability remains adjacent to Family 3A-style responsibilities. A future Family 3D must not absorb generic health visibility ownership.

## Frontend Consumer Inventory

### Direct mapping/reconciliation consumers
- `AdminAssetMapping.jsx`
  - reads `/admin/asset-mapping/queue`, `/coverage`, `/audit`, `/top-unmapped`, `/operational-impact`, `/admin/executive-summary`
  - mutation-capable via approve/reject/reassign/bulk-approve actions

- `AdminIntegrationCenter.jsx`
  - reads/writes `/admin/integrations/asset-mappings`
  - presents master asset mapping CRUD plus MaintainX/Motive integration context

- `AdminAssetSpineHealth.jsx`
  - reads `/asset-spine/health` and `/asset-spine/health/runs`
  - can trigger `/asset-spine/health/scan`
  - pure health/detection posture

- `AdminAssetAdmin.jsx`
  - canonical asset administration surface over Asset Spine and read-only readiness/doc surfaces

- `AssetProfile.jsx`
  - canonical per-asset view reading `/asset-spine/assets/{id}` and `/asset-spine/taxonomy`
  - admin edit lane includes external IDs in canonical asset record fields

- `AdminAssetThread.jsx`
  - uses `/asset-spine/resolve` and canonical asset profile/timeline surfaces

- `FleetBoard.jsx`
  - links unmapped or not-in-spine rows to `/admin/asset-mapping`
  - treats mapping and canonical profile as distinct destinations

### Consumer conclusion
Frontend consumers already encode the split:
- asset mapping queue UI
- asset registry/admin UI
- integration center mapping CRUD UI
- health/detection UI

This is further evidence against one single broad family.

## Status-Model Analysis

### Asset mapping proposal statuses
- `Imported`
- `Matched`
- `Verified`
- `Rejected`

### Asset readiness statuses
- `Ready`
- `Warning`
- `Not Ready`
- `Needs Review`

### Asset lifecycle statuses
- examples evidenced in UI/service: `active`, `inactive`, `pending_delivery`, `sold`, `retired`, `disposed`
  and uppercase storage variants like `ACTIVE`, `RETIRED`

### MaintainX dry-run classification buckets
- `exact_match`
- `probable_match`
- `possible_duplicate`
- `conflict`
- `missing_in_masci`
- `missing_in_maintainx`

### Status conclusion
The repository contains **multiple distinct status engines** for different responsibilities. That supports a split outcome, not one family.

## Duplicate-System Analysis

### Suspected duplicate or parallel systems
1. **External ID linkage exists in two places**
   - embedded in `equipment_master`
   - stored in `asset_mappings`
   - classification: **conflicting / overlapping ownership risk**

2. **Multiple reconciliation surfaces**
   - `asset_mapping_recon.py`
   - `integrations/mappings.py`
   - `maintainx_asset_sync.py`
   - `asset_spine_detection.py`
   - classification: **valid specialization but constitutionally split**

3. **Health UI exposes project identity conflicts**
   - `AdminAssetSpineHealth.jsx` surfaces `project_identity_conflicts`
   - classification: **adjacent observability coupling**, not asset-identity ownership

### Duplicate-system determination
The repository does not have one prohibited duplicate canonical asset registry, but it **does** have multiple specialized mapping/reconciliation engines. That is the central blocker to Outcome A.

## Legacy and Dead-Code Analysis

### Legacy / absent doc references
- `server.py`, `services/asset_spine.py`, and `AdminAssetSpineHealth.jsx` reference `/app/memory/MASTER_ASSET_GOVERNANCE_ARCHITECTURE.md`
- `AdminAssetMapping.jsx` and tests reference `/app/memory/MOTIVE_DAY1_ACTIVATION_RUNBOOK.md`
- both files are absent in the current repository snapshot reviewed here

### Likely live-but-transitional code
- `taxonomy/apply-legacy-crosswalk` in Asset Spine suggests legacy normalization migration logic still exists as an operator helper
- MaintainX P0 routes are explicitly framed as read-first P0/P0-B diagnostic surfaces, suggesting transitional pre-write maturity

### Dead-code conclusion
No decisive dead route was proven, but missing referenced docs and P0 transitional comments show documentation and maturity drift.

## Performance Ownership Register

| Flow | Observed Repository Shape | Likely Owner | Classification |
|---|---|---|---|
| `/admin/asset-mapping/scan` | loads dispatch distincts, all motive mappings, samples equipment master, nested scoring loop | Asset Mapping Recon | Family 3D candidate-owned if dispatch mapping queue is scoped in |
| `/admin/asset-mapping/top-unmapped` | aggregation + per-row proposal lookup | Asset Mapping Recon | Family 3D candidate-owned |
| `/admin/asset-mapping/operational-impact` | repeated counts + per-dispatch mapping lookup + operational_events lookups | Asset Mapping Recon + Family 3C dependency | mixed ownership |
| `/asset-spine/health` / `/health/scan` | multi-collection counts and detector fan-out | Asset Spine | Family 3D candidate-owned if registry family selected |
| `/asset-spine/assets?search=` | regex search over equipment_master fields | Asset Spine | Family 3D candidate-owned |
| MaintainX dry-run | external pagination + full MASCI load + classification pass | MaintainX P0 | external integration + candidate family-owned diagnostic layer |
| Asset Care summary/readiness | cross-collection advisory aggregation | Asset Care | adjacent/read-model ownership, not core mapping engine |

### Performance conclusion
Performance ownership is already fragmented along subsystem boundaries, matching the architectural split.

## Latency Register

### Safe runtime evidence
Only safe unauthenticated probe results were gathered:
- `/asset-spine/health` → `401`
- `/admin/asset-mapping/queue` → `401`
- `/asset-spine/assets?limit=1` → `401`
- `/operations-center/asset-spine-tile` → `401`

### What this proves
- endpoints exist and are gated
- no non-mutating authenticated latency sample was taken in this discovery phase

### Honest limitation
Average / median / p95 / worst endpoint latency for candidate Family 3D flows could not be safely measured here without authenticated live probing beyond the bounded needs of documentation-only discovery.

## External Integration Analysis

### Motive
- integrated through `asset_mappings`, `motive_service.py`, dispatch-facing surfaces, and Family 3C event consumers
- asset mapping queue specifically reconciles dispatch truck references to Motive-linked mappings

### MaintainX
- integrated through:
  - Integration Center mapping CRUD
  - `maintainx_asset_sync.py` read-first dry-run pipeline
  - `maintainx_p0.py` admin routes
- explicit doctrine: no writes to MaintainX, no writes to canonical asset store during dry-run

### FleetWatcher
- present mainly as identifier field (`fleetwatcher_asset_id`) in Asset Spine canonical records and admin UI references
- no deeper connector module was evidenced in the reviewed discovery set

### External integration conclusion
External integration ownership is another sign that the repository is split between canonical registry and provider-link / reconciliation surfaces.

## Survivability Dependencies

If a future Platform Survivability Program later protects this domain, the following would require preservation and restoration ordering:

1. `equipment_master` canonical asset rows
2. `asset_mappings` provider crosswalks
3. `asset_transfers` lineage
4. `asset_onboarding_steps` history
5. `asset_mapping_proposals` operator queue state
6. `asset_spine_health_runs` health evidence
7. `admin_audit_log` and `audit_events` asset mutation evidence
8. `maintainx_dryrun_reports` only if retained as meaningful operator evidence

### Restoration-order dependency
- canonical `equipment_master` should restore before provider crosswalks
- provider crosswalks should restore before event or dispatch surfaces that enrich from them
- audit/lineage stores should restore with canonical IDs intact

## Documentation Consistency

### Consistent repository claims
- Asset Spine comments repeatedly state `equipment_master` is canonical
- Integration Center comments repeatedly state `asset_mappings` should not duplicate `equipment_master`
- Asset Mapping Recon comments repeatedly state it is a queue-driven data-quality layer, not an auto-link engine

### Inconsistent or missing documentation
- code and UI reference `/app/memory/MASTER_ASSET_GOVERNANCE_ARCHITECTURE.md`, but the file is absent
- code/UI/tests reference `MOTIVE_DAY1_ACTIVATION_RUNBOOK.md`, but the file is absent
- broader “Asset Mapping & Reconciliation” is not documented as one clean family boundary; instead comments describe several narrower subsystems

## Repository Contradictions

1. **Single-source-of-truth language vs dual external-ID surfaces**
   - Asset Spine doctrine says `equipment_master` is the single source-of-truth.
   - Integration mapping and reconciliation logic still rely on separate `asset_mappings` as the provider crosswalk source.
   - This is not inherently invalid, but it contradicts a simplistic reading that all asset identity lives in one store.

2. **Missing governance docs referenced as doctrine**
   - `/app/memory/MASTER_ASSET_GOVERNANCE_ARCHITECTURE.md` is referenced in code comments and UI, but absent.
   - `/app/memory/MOTIVE_DAY1_ACTIVATION_RUNBOOK.md` is referenced in UI/tests, but absent.
   - These are live repository contradictions between code comments/tests and available documentation.

3. **Project-identity conflicts surfaced in asset health UI**
   - `AdminAssetSpineHealth.jsx` displays `project_identity_conflicts` as part of spine reconciliation posture.
   - The actual owner is `project_identity_governance.py`, which is project-domain detection, not asset-domain mapping.
   - This is a boundary-blur contradiction in observability presentation.

## Remaining Unknowns

1. Whether the missing `MASTER_ASSET_GOVERNANCE_ARCHITECTURE.md` would have declared a constitutional split already.
2. Whether `fleetwatcher_asset_id` has a deeper live connector path elsewhere beyond field storage and UI references.
3. Whether provider ID fields on `equipment_master` are intended to supersede `asset_mappings` over time or coexist permanently.
4. Whether any unreviewed background jobs outside the discovery slice mutate `asset_mappings` or `equipment_master` in ways not visible from the primary route/service owners.
5. Whether future authenticated live latency traces would reveal one subsystem as the dominant owner of the hypothesis.

## Constitutional Risks

### Critical
1. **Broad Family 3D would conflate canonical registry ownership with provider-link reconciliation ownership**
   - evidence: Asset Spine, Integration mappings, Mapping Recon, and MaintainX dry-run all own different mutation/reporting surfaces
   - constitutional owner: unresolved / split
   - consequence: Phase B would force adjacent-system redesign and boundary drift
   - Phase B blocker: **Yes**
   - Wave 3 closeout blocker: **Yes, until family is split/narrowed/merged correctly**
   - Platform Survivability blocker: No
   - PRR blocker: indirect only
   - Deployment blocker: indirect only

### High
2. **Dual external-ID storage model creates identity ambiguity**
   - evidence: provider IDs appear on `equipment_master` and via `asset_mappings`
   - owner: split between Asset Spine and Integration mappings
   - consequence: unclear field authority and reference continuity risk
   - Phase B blocker: **Yes for one-family authorization**

3. **Trust Spine participation is not evidenced for candidate mutation flows**
   - evidence: no Trust imports or stage emissions in reviewed candidate files
   - owner: candidate family files / trust governance gap
   - consequence: future Phase B would need trust-boundary clarification
   - Phase B blocker: **Yes for any mutation-heavy family certification**

### Medium
4. **Append-only audit coverage is uneven across candidate subsystems**
   - evidence: strong audit in Asset Spine, weaker/unclear in mapping CRUD and proposal approval
   - owner: split
   - consequence: inconsistent evidence chain for reconciliation decisions
   - Phase B blocker: maybe, depending on narrowed family

5. **Missing doctrine/runbook files reduce discovery certainty**
   - evidence: absent referenced memory docs
   - owner: documentation governance
   - consequence: repository claims cannot be fully reconciled to design docs
   - Phase B blocker: not alone, but contributes to NO-GO for Outcome A

### Low
6. **Legacy auth test patterns still mixed across old admin-login and multi-login**
   - evidence: reviewed tests show both patterns
   - owner: shared auth governance
   - consequence: test/doc drift, not unique to asset family
   - Phase B blocker: no, as a family-discovery outcome

## Discovery Confidence
**Moderate**

### Repository coverage
- High coverage on the strongest candidate owners: Asset Spine, Asset Mapping Recon, Integration mappings, MaintainX dry-run, Asset Care, server wiring, and direct admin UIs.

### Route coverage
- High for primary asset routes and mapping routes.
- Moderate for all possible background jobs and provider-specific connectors outside the main slice.

### Model/store coverage
- High for `equipment_master`, `asset_mappings`, `asset_mapping_proposals`, `asset_spine_health_runs`, `asset_transfers`, `asset_onboarding_steps`, `maintainx_dryrun_reports`, `asset_required_doc_overrides`.

### Frontend-consumer coverage
- High for direct admin consumers.
- Moderate for every indirect downstream consumer across the whole platform.

### Test coverage
- Moderate to high: multiple repository tests and scripts explicitly support Asset Spine, mapping, resolver, and dry-run claims.

### Documentation consistency
- Moderate at best because core referenced governance/runbook docs are absent.

### Runtime evidence where safely available
- Limited but real: store counts and auth-gate probes were gathered safely.

### Unresolved unknowns
- fleetwatcher depth, dual-ID intended authority, and missing doctrine docs remain unresolved.

### Assumptions that could not be verified
- whether missing docs would formally split the family already
- whether provider IDs on canonical rows are transitional or final constitutional design

## Required Family Classification
**Outcome C — Family 3D Must Be Split**

Repository evidence does not support one single bounded family named “Asset Mapping & Reconciliation.”

The repository instead contains at least two distinct constitutional responsibilities:

1. **Canonical Asset Spine / Asset Registry / Asset Lifecycle**
   - owner: `routes/asset_spine.py` + `services/asset_spine.py`
   - store: `equipment_master`

2. **External Mapping & Reconciliation**
   - owners split across:
     - `routes/integrations/mappings.py`
     - `routes/asset_mapping_recon.py`
     - `services/maintainx_asset_sync.py`
   - stores: `asset_mappings`, `asset_mapping_proposals`, `maintainx_dryrun_reports`

This split is already encoded in route registration, stores, UI surfaces, and tests.

## GO / NO-GO Recommendation
**NO-GO** for Phase B **as a single Family 3D “Asset Mapping & Reconciliation” implementation**.

Direct answers to the governing standard:

- **Does a real bounded family exist?**
  - Not as one single broad family.

- **Is canonical ownership deterministic?**
  - Yes for canonical asset registry (`equipment_master` / Asset Spine).
  - No for the full broad hypothesis, because mapping and reconciliation ownership is split.

- **Is mutation ownership clear?**
  - Clear only after splitting:
    - Asset Spine mutations for canonical assets
    - Integration / proposal mutations for provider mapping

- **Are persistent stores understood?**
  - Yes, but they are multiple and subsystem-specific.

- **Are mapping and reconciliation boundaries understood?**
  - Yes, and that understanding proves the hypothesis is too broad.

- **Is identity ownership clear?**
  - Canonical internal identity: yes.
  - External/provider identity ownership: split/overlapping.

- **Can Phase B be bounded without adjacent-family redesign?**
  - Not under one broad Family 3D label.

Therefore the repository supports a **successful discovery outcome of split classification**, not authorization for a single unified Phase B.

## Recommended Phase B Boundary — Scope Only
If further work is authorized later, the repository evidence supports **separate bounded scopes**, not one combined family:

### Possible bounded scope A — Canonical Asset Spine
- canonical asset registry only
- `equipment_master`
- asset lifecycle, taxonomy, transfer lineage, onboarding, health detection
- direct consumers: Asset Admin, Asset Profile, Asset Thread, Asset Spine Health, Asset Care read surfaces

### Possible bounded scope B — External Asset Mapping & Reconciliation
- provider crosswalks and operator reconciliation only
- `asset_mappings`, `asset_mapping_proposals`, `maintainx_dryrun_reports`
- direct consumers: AdminIntegrationCenter, AdminAssetMapping, MaintainX P0 surfaces

### Explicitly out of scope for either boundary unless separately authorized
- Family 3A read-only admin operations ownership
- Family 3B operations command ownership
- Family 3C operational event ownership
- project identity governance (`project_identity_conflicts`)
- shared auth redesign
- survivability implementation
- deployment / PRR work
