# BCSS RELEASE 2 · PROGRAM 2
## WAVE 3 · FAMILY 3
## ADMIN OPERATIONS
## PHASE A — CAPABILITY VERIFICATION & REPOSITORY DISCOVERY

Date: 2026-07-25

Status: DISCOVERY ONLY · READ-ONLY · NO IMPLEMENTATION

---

## Executive Summary

Repository evidence does **not** support treating “Admin Operations” as one clean constitutional family with one truth subject, one owner, and one command authority.

What the repository actually shows is a **cluster** of adjacent admin-operated surfaces:

1. **Core strict-admin operational infrastructure** in `/app/backend/routes/admin_ops.py`
   - `GET /api/admin/system-health`
   - `GET /api/admin/system-health/recent`
   - `GET /api/admin/audit-log`
   - `GET /api/admin/search`
   - `GET /api/admin/deploy-recovery`
   - `GET /api/admin/lookup`
   - This layer is **read-only**.

2. **Adjacent admin command surfaces** used from “Admin Operations” UI routes, but implemented in other bounded families:
   - `operational_events.py`
   - `asset_mapping_recon.py`
   - `operations.py`
   - `operations_actions/api.py`

3. **Adjacent admin domain landings** that are operator-facing but not owned by `admin_ops.py`
   - `AdminOperationsDashboard.jsx` (legacy route still mounted)
   - `AdminOperationsEvents.jsx`
   - `AdminAiOperations.jsx`
   - `AdminAssetMapping.jsx`
   - `/operations-actions/*`

Key discovery conclusion:

- **Core `admin_ops.py` exists and is Present**.
- It is best classified as a **strict-admin observability / operator utility surface**, not as a canonical truth owner.
- The broader “Admin Operations” umbrella is **constitutionally mixed** because it combines:
  - read-only operational observability,
  - derived-state administrative execution,
  - direct operational record mutation,
  - cross-portal command execution.

Because of that mixed authority structure, repository evidence supports:

- **GO** for future bounded hardening of the **core read-only `admin_ops.py` surface**, but
- **NO-GO** for treating the full umbrella of “Admin Operations” as one single Phase B family without first preserving the existing authority boundaries.

---

## Repository Evidence

### Primary backend files inspected

- `/app/backend/routes/admin_ops.py`
- `/app/backend/routes/operational_events.py`
- `/app/backend/routes/asset_mapping_recon.py`
- `/app/backend/routes/operations.py`
- `/app/backend/routes/operations_actions/api.py`
- `/app/backend/server.py`

### Primary frontend files inspected

- `/app/frontend/src/pages/admin/AdminOperationsDashboard.jsx`
- `/app/frontend/src/pages/admin/AdminOperationsEvents.jsx`
- `/app/frontend/src/pages/admin/AdminAiOperations.jsx`
- `/app/frontend/src/pages/admin/SystemHealth.jsx`
- `/app/frontend/src/pages/admin/AdminAuditLog.jsx`
- `/app/frontend/src/pages/admin/DeployRecovery.jsx`
- `/app/frontend/src/pages/admin/AdminAssetMapping.jsx`
- `/app/frontend/src/components/AdminGlobalSearch.jsx`
- `/app/frontend/src/components/AdminReferenceLookup.jsx`
- `/app/frontend/src/components/admin/CommandPalette.jsx`
- `/app/frontend/src/pages/operations_actions/OperationsActions.jsx`
- `/app/frontend/src/pages/operations_actions/OperationsActionNew.jsx`
- `/app/frontend/src/pages/operations_actions/OperationsActionDetail.jsx`
- `/app/frontend/src/app/routing/AppRoutes.jsx`

### Tests inspected

- `/app/backend/tests/test_iter130_admin_ops.py`
- `/app/backend/tests/test_m2_event_router.py`
- `/app/backend/tests/test_motive_data_001.py`
- `/app/backend/tests/test_iter338_admin_reference_lookup.py`
- `/app/backend/tests/test_oa1_operations_actions.py`

### Planning / constitutional references inspected

- `/app/memory/BCSS_RELEASE2_PROGRAM2_CHECKPOINT6_PHASEA_DISCOVERY.md`
- `/app/memory/BCSS_RELEASE2_PROGRAM2_CHECKPOINT4_OPERATIONAL_TRUTH_SPINE.md`
- `/app/memory/BCSS_RELEASE2_PROGRAM2_WAVE3_FAMILY2_OCC_TRUST_EVENTS_PHASEA_DISCOVERY.md`
- `/app/memory/BCSS_RELEASE2_PROGRAM2_WAVE3_FAMILY1_OCC_HEALTH_AGGREGATOR_PHASEA_DISCOVERY.md`
- `/app/memory/PRD.md`

---

## Family Identity

### Does Admin Operations already exist?

- **Yes** — but in two different senses.

#### 1. Narrow, repository-clean sense
- `backend/routes/admin_ops.py` is a real mounted backend family.
- It has dedicated frontend consumers and direct backend tests.

#### 2. Broad, operator-language sense
- “Admin Operations” also refers to several adjacent operator surfaces and command consoles outside `admin_ops.py`.
- Those surfaces do **not** share one owner or one truth subject.

### Capability classification

- **Present**

### Family classification

Repository truth supports a split view:

#### Core `admin_ops.py`
- **DERIVED CONSUMER / OPERATOR UTILITY SURFACE**

Why:
- all routes are reads
- no writes are implemented in the file
- data is aggregated, searched, normalized, or projected from other owners
- no route in the file claims global operational truth ownership

#### Broader “Admin Operations” umbrella
- **NOT A SINGLE CLEAN CONSTITUTIONAL FAMILY**

Why:
- mixed route ownership across multiple backend files
- mixed actor models
- mixed truth subjects
- mixed mutation authority
- legacy and cross-portal surfaces are included in the operator mental model but not in one route family

---

## Runtime Inventory

### Backend runtime files

#### Core Admin Operations family
- `/app/backend/routes/admin_ops.py`

#### Directly adjacent admin-operated command families surfaced by inspected UI
- `/app/backend/routes/operational_events.py`
- `/app/backend/routes/asset_mapping_recon.py`
- `/app/backend/routes/operations.py`
- `/app/backend/routes/operations_actions/api.py`

### Route registration evidence

#### Core family mount
- `/app/backend/server.py:15278-15286`
- `build_admin_ops_router(db, require_admin_strict)`
- `app.include_router(_admin_ops_router)`

This proves the core family is mounted with the **strict admin gate**.

#### Adjacent operations-actions mount
- `/app/backend/server.py:15209-15212`
- mounted through `_require_oa_actor`

### Frontend runtime files

#### Direct consumers of `admin_ops.py`
- `SystemHealth.jsx`
- `AdminAuditLog.jsx`
- `DeployRecovery.jsx`
- `AdminGlobalSearch.jsx`
- `CommandPalette.jsx`
- `AdminReferenceLookup.jsx`

#### Adjacent operations surfaces inspected for family truth
- `AdminOperationsDashboard.jsx`
- `AdminOperationsEvents.jsx`
- `AdminAiOperations.jsx`
- `AdminAssetMapping.jsx`
- `OperationsActions.jsx`
- `OperationsActionNew.jsx`
- `OperationsActionDetail.jsx`

### Route mounts in frontend

Repository-backed routes include:

- `/admin/system-health`
- `/admin/audit-log`
- `/admin/deploy-recovery`
- `/admin/operations-dashboard`
- `/admin/operations-events`
- `/admin/ai-operations`
- `/admin/asset-mapping`
- `/operations-actions`
- `/operations-actions/new`
- `/operations-actions/:id`

Important route classification findings:

- `/admin/operations-dashboard` is explicitly marked **legacy / consolidated into OCC** in routing comments and prior Checkpoint 4 discovery.
- `/admin/operations-events` is an admin page over the separate `/api/operations/events` family.
- `/admin/ai-operations` is an AI domain landing, not an operations-truth owner.
- `/operations-actions/*` is **cross-portal**, not admin-only.

---

## Backend Inventory

### Core `admin_ops.py` endpoints

The core family contains exactly these mounted endpoints:

- `GET /api/admin/system-health`
- `GET /api/admin/system-health/recent`
- `GET /api/admin/audit-log`
- `GET /api/admin/search`
- `GET /api/admin/deploy-recovery`
- `GET /api/admin/lookup`

Repository evidence from file header and route implementations confirms:

- all are admin-gated
- all are reads
- no direct writes exist in the file

### Data behavior inside `admin_ops.py`

#### `system-health`
- computes health cards from:
  - MongoDB ping
  - R2 configuration / degraded events
  - canonical archive lineage / freshness
  - recent auth-failure counts
  - integration status
  - failed-sync counts
  - active sessions
  - build version

#### `audit-log`
- merges append-only / audit-like sources from:
  - `audit_events`
  - `admin_audit`
  - `operations_events`
  - `integration_wizard_runs`

#### `search`
- searches across:
  - `equipment_master`
  - `employees`
  - `operations_events`
  - `equipment_transfers`
  - `incidents`
  - `corrective_actions`
  - `projects`

#### `deploy-recovery`
- reads build metadata, backup chain evidence, R2 status, version history
- exposes `ots_truth` and `truth_relationship` for `bcss_runtime_state_authority`

#### `lookup`
- resolves exact references across 9 record families

### Adjacent backend command families surfaced by inspected admin UI

#### `operational_events.py`
- materializes derived `operational_events` from `motive_events`, `operational_locations`, and `asset_mappings`
- also provides admin audit/dashboard reads and public/project-day views

#### `asset_mapping_recon.py`
- provides proposal scan, queue, approve/reject/reassign/bulk-approve, and audit/impact views

#### `operations.py`
- owns operational event writes, holds, assignments, and transfer mutations
- appends `operations_events`

#### `operations_actions/api.py`
- owns `operations_actions` records
- supports create, update, assign, status changes, notes, photo upload/delete, and history tracking

---

## Frontend Inventory

### Core family consumers

#### 1. System Health page
- file: `/app/frontend/src/pages/admin/SystemHealth.jsx`
- backend: `GET /api/admin/system-health`
- role: strict-admin read-only health panel

#### 2. Audit Log page
- file: `/app/frontend/src/pages/admin/AdminAuditLog.jsx`
- backend: `GET /api/admin/audit-log`
- role: strict-admin merged timeline viewer

#### 3. Deploy Recovery page
- file: `/app/frontend/src/pages/admin/DeployRecovery.jsx`
- backend: `GET /api/admin/deploy-recovery`
- role: strict-admin read-only rollback / backup playbook surface

#### 4. Admin search utilities
- files:
  - `AdminGlobalSearch.jsx`
  - `CommandPalette.jsx`
- backend: `GET /api/admin/search`

#### 5. Admin reference lookup
- file: `AdminReferenceLookup.jsx`
- mounted inside `AdminSystem.jsx`
- backend: `GET /api/admin/lookup`

### Adjacent operations-facing pages inspected for family truth

#### 1. `AdminOperationsDashboard.jsx`
- route: `/admin/operations-dashboard`
- uses:
  - `GET /api/admin/asset-mapping/coverage`
  - `GET /api/admin/operational-events/dashboard`
  - `POST /api/admin/operational-events/materialize`
  - `GET /api/admin/operational-events/audit`
- repository truth: **legacy route still mounted, but not part of core `admin_ops.py`**

#### 2. `AdminOperationsEvents.jsx`
- route: `/admin/operations-events`
- uses `GET /api/operations/events?...`
- repository truth: frontend viewer over separate operations family

#### 3. `AdminAiOperations.jsx`
- route: `/admin/ai-operations`
- uses:
  - `/api/ai/gateway/status`
  - `/api/dr-v2/meta`
  - `/api/admin/production-certification`
- repository truth: AI domain landing, not admin-ops owner

#### 4. `AdminAssetMapping.jsx`
- route: `/admin/asset-mapping`
- uses both read and mutating admin commands

#### 5. `/operations-actions/*`
- routes:
  - `/operations-actions`
  - `/operations-actions/new`
  - `/operations-actions/:id`
- repository truth: cross-portal operational coordination surface, not admin-only

---

## API Inventory

### Core Admin Operations API

| Endpoint | Method | Runtime role | Mutating? |
|---|---|---|---|
| `/api/admin/system-health` | GET | health aggregation | No |
| `/api/admin/system-health/recent` | GET | monitor history readback | No |
| `/api/admin/audit-log` | GET | merged audit timeline | No |
| `/api/admin/search` | GET | cross-collection search | No |
| `/api/admin/deploy-recovery` | GET | backup / rollback readiness probe | No |
| `/api/admin/lookup` | GET | exact reference resolution | No |

### Adjacent command APIs surfaced through inspected admin operations pages

| Endpoint family | Primary methods discovered | Runtime role |
|---|---|---|
| `/api/admin/operational-events/*` | GET, POST | derived event materialization + audit/dashboard |
| `/api/admin/asset-mapping/*` | GET, POST | mapping proposal workflow + mapping commits |
| `/api/operations/*` | GET, POST, PATCH | operational record mutation + event append |
| `/api/operations-actions/*` | GET, POST, PATCH, DELETE | cross-portal action coordination CRUD |

---

## Administrative Command Architecture

Scope note: this inventory covers the administrative actions directly evidenced by the inspected Admin Operations surfaces and their linked backend route families. It does **not** claim to be an exhaustive list of every command in the repository.

### A. Core strict-admin observability / utility actions (`admin_ops.py`)

| Action | Classification | Read-only or mutating | Changes canonical truth? | Changes derived state only? | Idempotent? | Confirmation required? | Rollback supported? | Immutable audit generated? | Specific actor attribution? | Can bypass normal workflow? | Safeguards / evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `GET /api/admin/system-health` | Read | Read-only | No | No | Yes | No | N/A | No new audit row | Access only, not action-level | No | strict-admin gate via `require_admin_strict`; tested in `test_iter130_admin_ops.py` |
| `GET /api/admin/system-health/recent` | Read | Read-only | No | No | Yes | No | N/A | No new audit row | Access only | No | strict-admin gate; reads `health_monitor_runs` only |
| `GET /api/admin/audit-log` | Read | Read-only | No | No | Yes | No | N/A | No new audit row | Access only | No | strict-admin gate; merged read over append-only sources |
| `GET /api/admin/search` | Validate / Read | Read-only | No | No | Yes | No | N/A | No new audit row | Access only | No | query validation (`min_length`, regex escaping), strict-admin gate |
| `GET /api/admin/deploy-recovery` | Read / Validate | Read-only | No | No | Yes | No | N/A | No new audit row | Access only | No | strict-admin gate; exposes bounded `ots_truth` context |
| `GET /api/admin/lookup` | Validate / Read | Read-only | No | No | Yes | No | N/A | No new audit row | Access only | No | exact-match only; strict-admin gate; no public route |

### B. Adjacent admin-operated derived-state commands

| Action | Classification | Read-only or mutating | Changes canonical truth? | Changes derived state only? | Idempotent? | Confirmation required? | Rollback supported? | Immutable audit generated? | Specific actor attribution? | Can bypass normal workflow? | Safeguards / evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `POST /api/admin/operational-events/materialize` | Execute / Reconcile | State-mutating | No repository proof of canonical truth ownership | Yes — writes `operational_events` derived rows | **Yes** by route docstring and test (`same ids`) | No | No explicit rollback found | No separate immutable admin audit found | **No explicit specific actor stored** in materialized rows | Yes — admin can repopulate derived event store on demand | admin gate; storage validation `_validate_doc`; tests prove no writes to daily reports / dispatch / motive sources |
| `GET /api/admin/operational-events/audit` | Validate / Read | Read-only | No | No | Yes | No | N/A | No new audit row | Access only | No | admin gate; computes audit answers only |
| `GET /api/admin/operational-events/dashboard` | Read | Read-only | No | No | Yes | No | N/A | No new audit row | Access only | No | admin gate; derived bucket counts only |
| `POST /api/admin/asset-mapping/scan` | Simulate / Reconcile | State-mutating | No direct canonical link commit | Yes — proposal queue only | **Mostly yes**; upsert on `truck_id`, existing verified/rejected preserved | No | No explicit rollback found | No immutable audit ledger found | **No specific actor captured** | No direct truth override; feeds operator queue | admin gate; scan does **not** auto-link; tested in `test_motive_data_001.py` |
| `GET /api/admin/asset-mapping/queue` | Read | Read-only | No | No | Yes | No | N/A | No new audit row | Access only | No | admin gate |
| `POST /api/admin/asset-mapping/{prop_id}/approve` | Approve | State-mutating | **Yes** — writes `asset_mappings.masci_equipment_id` | Also updates proposal status | Not explicitly guaranteed | No | No explicit rollback; later reassign can supersede | No immutable audit ledger found | Weak attribution only: `verified_by: "admin"` | Yes — directly commits mapping link | admin gate; proposal must exist |
| `POST /api/admin/asset-mapping/{prop_id}/reject` | Reject | State-mutating | No direct canonical link commit | Yes — proposal status only | Effectively yes on repeat result, but not explicitly guarded | No | No explicit rollback | No immutable audit ledger found | Weak attribution only: `verified_by: "admin"` | No | admin gate; proposal must exist |
| `POST /api/admin/asset-mapping/{prop_id}/reassign` | Override / Repair / Approve | State-mutating | **Yes** — manually changes chosen mapping link in `asset_mappings` | Also finalizes proposal | Not explicitly guaranteed | No | No explicit rollback; another reassign could supersede | No immutable audit ledger found | Weak attribution only: `verified_by: "admin"` | **Yes** — manual operator override of scored match | admin gate; proposal and selected mapping must exist |
| `POST /api/admin/asset-mapping/bulk-approve` | Approve / Execute | State-mutating | **Yes** — batch commits mapping links | Also updates proposal status | Not explicitly guaranteed | No | No explicit rollback | No immutable audit ledger found | Weak attribution only: `verified_by: "admin-bulk"` | Yes — batch commit path | admin gate; only HIGH-confidence proposals approved |
| `GET /api/admin/asset-mapping/coverage` | Read | Read-only | No | No | Yes | No | N/A | No new audit row | Access only | No | admin gate |
| `GET /api/admin/asset-mapping/audit` | Validate / Read | Read-only | No | No | Yes | No | N/A | No new audit row | Access only | No | admin gate |
| `GET /api/admin/asset-mapping/top-unmapped` | Read | Read-only | No | No | Yes | No | N/A | No new audit row | Access only | No | admin gate |
| `GET /api/admin/asset-mapping/impact-preview/{prop_id}` | Simulate / Read | Read-only | No | No | Yes | No | N/A | No new audit row | Access only | No | admin gate; preview only |
| `GET /api/admin/asset-mapping/operational-impact` | Read / Validate | Read-only | No | No | Yes | No | N/A | No new audit row | Access only | No | admin gate; pure derivation per docstring |

### C. Adjacent operational record-mutation commands surfaced through inspected admin operations pages

| Action | Classification | Read-only or mutating | Changes canonical truth? | Changes derived state only? | Idempotent? | Confirmation required? | Rollback supported? | Immutable audit generated? | Specific actor attribution? | Can bypass normal workflow? | Safeguards / evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `POST /api/operations/events` | Execute / Other(create) | State-mutating | Writes the `operations_events` owner store | No | No explicit idempotency | No | `PATCH` exists; no rollback concept | Append-only event row itself | Weak attribution: `created_by="admin"` in route path | Yes — direct event insertion | write gate = admin or dispatch |
| `PATCH /api/operations/events/{event_id}` | Repair / Update | State-mutating | Yes — mutates existing `operations_events` row | No | No | No | No explicit rollback | No immutable append-only shadow shown | Weak actor attribution | Yes | write gate + existence checks |
| `POST /api/operations/holds` | Execute | State-mutating | Yes — writes `asset_holds`; also appends `operations_events` | No | No explicit idempotency | No | Partial compensating path via `/release` or `/dismiss` depending on status | Yes — append event via `write_event` | Weak attribution: `created_by="admin"` / `approved_by="admin"` literals | Yes — direct hold creation | kind validation, asset existence check |
| `POST /api/operations/holds/{hold_id}/approve` | Approve | State-mutating | Yes — mutates `asset_holds` active status | No | No | No | Partial via later `/release` | Yes — append event via `write_event` | Weak attribution | Yes | status guard: only pending holds |
| `POST /api/operations/holds/{hold_id}/dismiss` | Reject | State-mutating | Yes — mutates `asset_holds` | No | No | Reason required | No explicit rollback | Yes — append event via `write_event` | Weak attribution | Yes | pending-only + reason required |
| `POST /api/operations/holds/{hold_id}/release` | Release / Restore | State-mutating | Yes — mutates `asset_holds` | No | Repeating on inactive hold returns existing state | No | N/A (this is the compensating action) | Yes — append event via `write_event` | Weak attribution | Yes | active-state guard |
| `GET /api/operations/holds` | Read | Read-only | No | No | Yes | No | N/A | No new audit row | Access only | No | any-portal read gate |
| `POST /api/operations/assignments` | Execute | State-mutating | Yes — writes `asset_assignments`; closes existing active assignments | No | No | No | Partial compensating path via `/clear` | Yes — append `asset_assigned` event | Weak attribution | Yes — direct ownership reassignment | asset existence check |
| `POST /api/operations/assignments/{asset_id}/clear` | Reset / Cancel | State-mutating | Yes — mutates active assignments | No | Repeat-safe when nothing active (`cleared: 0`) | No | N/A (this is compensating path) | Yes — append `asset_unassigned` event if modified | Weak attribution | Yes | active-assignment check |
| `POST /api/operations/transfers` | Execute / Other(create) | State-mutating | Yes — writes `transfer_requests` | No | No | No | Later decision path exists | Yes — append `dispatch_request_created` event | Weak attribution | Yes | asset existence check |
| `POST /api/operations/transfers/{xid}/decide` | Approve / Reject / Cancel / Execute | State-mutating | Yes — mutates `transfer_requests` status/history | No | No | No | Partial via later decisions depending on state | Yes — append event via `write_event` | Weak attribution | Yes | validated state transitions |

### D. Adjacent cross-portal command family (`operations_actions`)

| Action | Classification | Read-only or mutating | Changes canonical truth? | Changes derived state only? | Idempotent? | Confirmation required? | Rollback supported? | Immutable audit generated? | Specific actor attribution? | Can bypass normal workflow? | Safeguards / evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `GET /api/operations-actions/owner-search` | Read | Read-only | No | No | Yes | No | N/A | No new audit row | Access only | No | any real portal token required |
| `GET /api/operations-actions/summary` | Read | Read-only | No | No | Yes | No | N/A | No new audit row | Access only | No | any real portal token required |
| `GET /api/operations-actions` | Read | Read-only | No | No | Yes | No | N/A | No new audit row | Access only | No | enum validation on filters |
| `POST /api/operations-actions` | Other(create) | State-mutating | Yes — creates `operations_actions` row | No | No | No | No explicit rollback; record remains mutable | **Yes** — per-record `history` starts with `created` entry | **Yes** — `_actor_to_owner(actor)` captured | Yes — any portal actor can create by design | enum validation; real portal token required |
| `GET /api/operations-actions/{oa_id}` | Read | Read-only | No | No | Yes | No | N/A | No new audit row | Access only | No | existence check |
| `PATCH /api/operations-actions/{oa_id}` | Repair / Update | State-mutating | Yes — mutates owned OA record | No | No | No | No explicit rollback | **Yes** — `history` appends `updated` entry | **Yes** | Yes | closed actions blocked |
| `POST /api/operations-actions/{oa_id}/assign` | Assign / Override | State-mutating | Yes — mutates owner and possibly status | No | No | No | Later reassignment possible | **Yes** — `history` appends `assigned` entry | **Yes** | Yes | owner directory validation; closed actions blocked |
| `POST /api/operations-actions/{oa_id}/status` | Other(status transition) | State-mutating | Yes — mutates status | No | Repeat to same status returns existing doc | No | No explicit reopen path after `closed` | **Yes** — `history` appends `status_changed`; note optional | **Yes** | Yes | strict status enum; transition rules |
| `POST /api/operations-actions/{oa_id}/notes` | Other(append note) | State-mutating | Yes — mutates owned OA record | No | No | No | No | **Yes** — `history` appends `note_added` | **Yes** | No | body validation |
| `POST /api/operations-actions/{oa_id}/photos` | Other(upload evidence) | State-mutating | Yes — mutates owned OA record | No | No | No | Partial via photo delete | **Yes** — `history` appends `photo_added` | **Yes** | No | magic-byte validation; size cap; storage config required |
| `GET /api/operations-actions/{oa_id}/photos/{photo_id}/url` | Read | Read-only | No | No | Yes | No | N/A | No new audit row | Access only | No | existence checks |
| `DELETE /api/operations-actions/{oa_id}/photos/{photo_id}` | Delete | State-mutating | Yes — mutates owned OA record | No | Effectively repeat-safe after deletion becomes 404 | No | N/A | **Yes** — `history` appends `photo_deleted` | **Yes** | No | existence checks; best-effort R2 delete |

### Command architecture conclusion

Repository evidence shows four different command-quality levels:

1. **Pure read-only admin infrastructure** — `admin_ops.py`
2. **Derived-state admin execution** — operational-event materialization, asset-mapping scan
3. **Direct operational record mutation** — holds, assignments, transfers
4. **Cross-portal command ownership** — operations actions

This is exactly why the umbrella “Admin Operations” cannot be treated as one flat family without architectural drift.

---

## Truth / Workflow Architecture

### Core truth finding

Repository evidence does **not** show one canonical truth subject called “Admin Operations”.

Instead, the inspected surfaces sit across different architectural roles:

#### 1. `admin_ops.py`
- reads truth from other systems
- aggregates or projects it for operators
- owns no global operational truth subject

#### 2. `operational_events.py`
- materializes derived `operational_events`
- this is derived operational state, not raw Motive truth and not dispatch source truth

#### 3. `asset_mapping_recon.py`
- creates proposal workflow around mapping truth
- approval and reassign paths directly write `asset_mappings.masci_equipment_id`

#### 4. `operations.py`
- directly owns and mutates:
  - `asset_holds`
  - `asset_assignments`
  - `transfer_requests`
- also appends `operations_events`

#### 5. `operations_actions/api.py`
- owns `operations_actions`
- includes internal `history`, `notes`, `photos`, owner assignment, and status transitions

### Workflow separation

Repository evidence preserves these boundaries:

- **Observability utilities** are separate from **command endpoints**
- **Derived-state materialization** is separate from **source-truth mutation**
- **Cross-portal command ownership** is separate from **strict-admin infrastructure**
- **AI operations** is separate from **operational record authority**

### Architectural finding

The repository already contains authority separation by file and route family.

The constitutional risk is **not absence of boundaries**.

The constitutional risk is that the umbrella label **“Admin Operations”** can hide those boundaries and invite a future Phase B to overreach across them.

---

## Administrative Authority Separation

### Does Admin Operations administer systems?

- **Yes**.

Repository evidence:

- `system-health` administers operational visibility into runtime, DB, backup, integrations, auth failures, and build identity.
- `deploy-recovery` administers rollback / backup context.
- `audit-log` administers cross-system operator traceability.
- `search` and `lookup` administer cross-system discovery and navigation.
- adjacent admin pages trigger operational materialization and mapping decisions.

### Does Admin Operations own operational truth?

- **No, not as one unified family.**

Repository evidence shows separate owners or owner-like families:

- `admin_ops.py` is read-only
- `operations.py` owns holds / assignments / transfers
- `operations_actions/api.py` owns operations actions
- `asset_mapping_recon.py` governs mapping proposal workflow and can commit mapping links
- `operational_events.py` materializes derived event state

### Does Admin Operations issue commands to canonical owners?

- **Yes, in adjacent command surfaces.**

Examples:

- asset mapping approve / reassign writes `asset_mappings`
- holds / assignments / transfers directly mutate their own owner stores
- operations actions directly mutate `operations_actions`

### Does Admin Operations mutate canonical records directly?

- **Core `admin_ops.py`: No**
- **Broader adjacent admin-operated surfaces: Yes**

Repository-proven direct mutations include:

- `asset_mappings.masci_equipment_id`
- `asset_holds`
- `asset_assignments`
- `transfer_requests`
- `operations_actions`

### Where are the authority boundaries enforced?

Repository evidence shows boundaries enforced in these ways:

1. **File-level separation**
   - reads in `admin_ops.py`
   - materialization in `operational_events.py`
   - mapping workflow in `asset_mapping_recon.py`
   - operational command owners in `operations.py`
   - cross-portal action owner in `operations_actions/api.py`

2. **Route-level separation**
   - `/api/admin/*` strict-admin observability routes
   - `/api/admin/operational-events/*` admin execution over derived state
   - `/api/operations/*` mixed read/write operational owners
   - `/api/operations-actions/*` cross-portal CRUD owner

3. **Dependency-level separation**
   - `require_admin_strict` for core admin ops
   - `require_admin_dep` for adjacent admin-only commands
   - any-portal read gates or `_require_oa_actor` for broader operational lanes

4. **Test-level separation**
   - tests explicitly verify read-only behavior and “no unwanted writes” in materialization and scan paths

### Are there any places where administrative privilege improperly becomes truth ownership?

- **No repository proof of full architectural collapse was found.**
- **Yes, several pressure points were found.**

#### Pressure point 1 — actor attribution weakness
Multiple mutating admin paths use literal actor labels such as:

- `"admin"`
- `"admin-bulk"`

rather than a specific directory actor identity.

This appears in:

- asset mapping approval / reject / reassign / bulk approve
- holds / assignments / transfers in `operations.py`

That means administrative authority is present, but **specific human attribution is weaker than it should be**.

#### Pressure point 2 — missing immutable admin audit on some mutators
Not every mutating admin surface writes an immutable, append-only audit ledger.

Examples:

- asset mapping decision routes update status / mapping link but do not surface a dedicated immutable audit collection in the inspected file
- operational-event materialize does not record who triggered the materialization in a dedicated audit trail

#### Pressure point 3 — broad umbrella naming
The broad operator label “Admin Operations” could obscure the fact that:

- some actions are observability only
- some write derived state only
- some directly mutate authoritative records
- some are cross-portal and intentionally not admin-only

This is a constitutional scope risk, not yet a direct repository owner collision.

---

## Permissions and Access Control

### Core Admin Operations permissions

`admin_ops.py` is mounted with `require_admin_strict`.

Repository evidence proves:

- Admin token required
- PM tokens rejected on `/api/admin/*`
- denied attempts logged by strict gate

### Adjacent permissions discovered

#### `operational_events.py`
- `/api/admin/operational-events/*` uses admin gate

#### `asset_mapping_recon.py`
- `/api/admin/asset-mapping/*` uses admin gate

#### `operations.py`
- read endpoints accept any portal token
- write endpoints are admin-or-dispatch gated

#### `operations_actions/api.py`
- `_require_oa_actor` accepts **any real portal token**
- repository comment is explicit: there is **no portal-level write asymmetry in OA-1 by design**

### Permission finding

The repository does **not** use one admin-only permission model for all “Admin Operations” activity.

That is another reason the umbrella cannot be treated as one flat family.

---

## Duplicate Analysis

### Duplicate surface pressure

#### 1. `/admin/operations-dashboard`
- already marked legacy / consolidated into OCC
- still mounted
- still operator-visible

This is a direct duplicate-pressure zone.

#### 2. Search duplication
- `AdminGlobalSearch.jsx` and `CommandPalette.jsx` both consume `/api/admin/search`
- same backend search service, different UI shells

This is **consumer duplication**, not owner duplication.

#### 3. Health duplication
- `/api/admin/system-health`
- `/api/admin/occ/health`
- `/api/admin/platform-trust/validate`

These overlap in operator posture, but are not the same truth subject.

#### 4. Recovery / readiness duplication pressure
- `/api/admin/deploy-recovery`
- `/api/admin/deploy-readiness`
- `/api/admin/deployment-readiness/*` from adopted BCSS line

This is known adjacent duplication pressure, but `deploy-recovery` in `admin_ops.py` is still a read-only playbook/context probe.

#### 5. Audit duplication pressure
- `/api/admin/audit-log`
- underlying raw audit sources
- `/admin/operations-events`

The merged feed is duplicative in presentation but not in storage ownership.

### Duplicate truth ownership

- **No evidence was found that `admin_ops.py` claims truth ownership over records owned elsewhere.**
- The duplication risk is mostly:
  - operator-summary duplication
  - legacy-route duplication
  - umbrella naming duplication

---

## Existing Tests

### Core family tests

#### `/app/backend/tests/test_iter130_admin_ops.py`
Proves:

- auth gate on core admin ops routes
- response-shape stability for:
  - `system-health`
  - `audit-log`
  - `search`
  - `deploy-recovery`
- deploy-recovery read-only / idempotent shape

#### `/app/backend/tests/test_iter338_admin_reference_lookup.py`
Proves:

- `/api/admin/lookup` exists
- route is admin-gated
- 9-collection lookup map exists
- frontend lookup component is mounted in `AdminSystem`

### Adjacent command-family tests

#### `/app/backend/tests/test_m2_event_router.py`
Proves:

- `materialize` exists
- `materialize` is idempotent on repeated run
- admin gate on `/admin/operational-events/*`
- no unwanted writes to daily reports / dispatch / motive source collections during audited paths

#### `/app/backend/tests/test_motive_data_001.py`
Proves:

- scan creates proposals but does **not** auto-link
- approve links
- reject does not link
- bulk-approve is restricted by confidence
- no unwanted writes during scan / audit / coverage / queue reads

#### `/app/backend/tests/test_oa1_operations_actions.py`
Proves:

- auth required
- create / read / patch / assign / status / notes work
- status transitions validated
- photo magic-byte validation enforced
- per-record history exists

### Testing finding

The repository has **good backend coverage** for the core read-only family and several adjacent command surfaces.

The main discovery gap is **constitutional boundary clarity**, not raw route absence.

---

## Existing Documentation and Prior Constitutional Findings

### Relevant earlier findings already on record

#### Checkpoint 4
- `/admin/operations-dashboard` already recorded as **legacy**.

#### Checkpoint 6
- `/api/admin/system-health` was already identified as a mixed-subject aggregator.
- composite health / event / admin surfaces were explicitly called out as poor smallest-safe grouped adoption candidates.

#### Family 1 discovery
- Admin Operations overlap with OCC Health was already noted as high.

### Discovery continuity conclusion

This report is consistent with earlier repository truth:

- the Admin Operations umbrella is real in runtime
- but it is constitutionally mixed
- and it should not be flattened into one owner track without drift

---

## Repository Risks

1. **Umbrella family ambiguity** — “Admin Operations” names multiple distinct authority types.
2. **Legacy route pressure** — `/admin/operations-dashboard` remains mounted despite explicit consolidation comments.
3. **Weak specific actor attribution** on several mutating admin paths.
4. **Missing immutable audit evidence** on some mutating admin paths.
5. **Read-only vs command surface mixing** in operator mental model.
6. **Cross-portal mutation** in `operations_actions` is intentional but broad; it must not be mistaken for admin-only authority.
7. **Health / readiness duplication pressure** from adjacent OCC and deployment surfaces.

---

## Architectural Risks

1. A future broad Phase B could incorrectly merge:
   - admin observability utilities
   - derived-state materializers
   - authoritative operational mutators
   - AI operations monitoring
   - cross-portal task coordination

2. A future hardening pass could drift into:
   - `operations.py`
   - `operations_actions/api.py`
   - asset-mapping ownership
   - OCC health / trust families
   - deployment readiness / recovery families

3. The repository’s actual boundary discipline could be weakened if “admin privilege” is treated as equivalent to “truth ownership”.

---

## Platform Survivability Roadmap Dependency Verification

| Roadmap area | Classification | Repository evidence |
|---|---|---|
| Platform Survivability Program | **Independent mandatory later milestone** | no runtime evidence shows it as a prerequisite to complete this discovery; user-mandated sequence keeps it after Wave 3 Formal Closeout |
| Backup | **Observes** | `system-health` and `deploy-recovery` read backup freshness / recent backup evidence |
| Recovery | **Observes** | `deploy-recovery` is a playbook/context surface and links operators toward recovery tooling; it does not own recovery certification |
| Disaster Recovery | **Observes / adjacent** | recovery playbook language exists, but no DR owner route was found inside `admin_ops.py` |
| Business Continuity | **Independent** | no BC owner route or BC data model discovered in the inspected Admin Operations files |
| Rollback | **Observes** | `deploy-recovery` presents rollback playbook guidance only |
| Production Readiness Review | **Observes / adjacent** | AI Ops and deploy-adjacent pages consume certification/readiness surfaces, but core Admin Operations is not the PRR owner |
| Wave 1 Deployment | **Observes / adjacent** | deploy recovery and health surfaces provide context for deployment safety, but do not own deployment authority |

### Dependency verdict

Repository evidence does **not** show that Admin Operations Phase A discovery is blocked by the Platform Survivability Program.

However, repository evidence **does** show that several Admin Operations surfaces are adjacent to backup, recovery, rollback, and readiness concerns and must not be allowed to absorb those families’ ownership.

---

## Constitutional Family Readiness

### Is the family constitutionally complete already?

- **Core `admin_ops.py`: mostly bounded but not fully framed as a constitutional family**
- **Broad “Admin Operations” umbrella: No**

Reasons proven by repository evidence:

- no single truth subject for the umbrella
- no single canonical owner for the umbrella
- mixed permission models
- mixed mutation authority
- legacy route still present
- broad operator label spans multiple separate backend families

### Does a future Phase B appear constitutionally justified?

- **Yes — but only if Phase B is strictly narrowed.**

### What is the single bounded mission supported by repository evidence?

- **Bind and harden the core `admin_ops.py` surface as a strict-admin, read-only operational observability / utility family, while preserving explicit separation from adjacent mutating command families.**

### What future work is explicitly out of scope for such a bounded Phase B?

- `operations.py` command redesign
- `operations_actions/api.py` redesign
- asset-mapping workflow redesign
- OCC Health Aggregator changes
- OCC Trust Events changes
- deployment-readiness redesign
- recovery / backup / survivability redesign
- AI operations redesign
- cross-portal auth redesign

### Could bounded Phase B be completed under Smallest Safe Repair and Zero Drift?

- **Yes, for the core read-only family only.**

### Could the full umbrella be safely hardened as one family under Smallest Safe Repair and Zero Drift?

- **No.**

That broader move would cross existing repository authority boundaries.

---

## GO / NO-GO Recommendation for Phase B

## NO-GO — FOR A BROAD “ADMIN OPERATIONS” PHASE B AS ONE UNIFIED FAMILY

### Evidence basis for NO-GO

Repository evidence proves that the umbrella currently spans:

- strict-admin read-only observability (`admin_ops.py`)
- derived-state admin execution (`operational_events.py`, asset-mapping scan)
- direct operational mutation (`operations.py`)
- cross-portal action ownership (`operations_actions/api.py`)
- AI domain monitoring (`AdminAiOperations.jsx`)
- a legacy admin route still mounted (`/admin/operations-dashboard`)

That is too broad for one constitutional Phase B without drift.

## CONDITIONAL GO — ONLY IF PHASE B IS RE-SCOPED TO THE CORE `admin_ops.py` FAMILY

That narrower track is justified because:

- the route family exists
- it is mounted and tested
- it is already strict-admin
- it is read-only
- its direct frontend consumers are clear
- its authority boundary is narrow enough to harden without crossing into unrelated command owners

---

## Discovery Verdict

Admin Operations is **Present**, but repository evidence supports two separate truths:

1. **`admin_ops.py` is a real, bounded, strict-admin read-only family.**
2. **The broader “Admin Operations” umbrella is not one constitutional family; it is a cluster of adjacent read, derived, and mutating command surfaces.**

Therefore:

- broad Family 3 hardening as one umbrella: **NO-GO**
- narrow hardening of the core `admin_ops.py` family only: **GO, if explicitly re-scoped**

Stop here and wait for explicit authorization before any Phase B work.