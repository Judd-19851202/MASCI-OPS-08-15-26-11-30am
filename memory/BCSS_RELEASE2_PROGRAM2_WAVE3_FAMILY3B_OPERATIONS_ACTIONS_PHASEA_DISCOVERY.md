# BCSS RELEASE 2 · PROGRAM 2 · WAVE 3 · FAMILY 3B
## OPERATIONS ACTIONS — PHASE A REPOSITORY DISCOVERY

Date: 2026-07-25
Mode: READ-ONLY DISCOVERY · REPOSITORY-VERIFIED · NO IMPLEMENTATION

---

## Executive Summary

Repository evidence supports **Wave 3 Family 3B = Operations Actions** as a **real, bounded constitutional family** with a deterministic repository owner:

- **Canonical repository owner:** `/app/backend/routes/operations_actions/api.py`
- **Mount / route owner:** `register_operations_actions_routes(...)` mounted from `backend/server.py`
- **Frontend runtime owner set:**
  - `/app/frontend/src/pages/operations_actions/OperationsActions.jsx`
  - `/app/frontend/src/pages/operations_actions/OperationsActionNew.jsx`
  - `/app/frontend/src/pages/operations_actions/OperationsActionDetail.jsx`
  - shared OA components under `/app/frontend/src/components/oa/`
- **Runtime role:** cross-portal CRUD coordination layer for operational actions
- **Truth subject:** the `operations_actions` record and its internal lifecycle (`status`, `current_owner`, `notes`, `photos`, `history`)

Repository evidence also proves critical constitutional characteristics:

1. **Family 3B is mutating by design.** This is not a read-only family.
2. **Family 3B directly mutates its own owned records** in `db.operations_actions`.
3. **Family 3B is not the system of record for the external world**, but it **is** the repository owner for the coordination record it creates and mutates.
4. **Cross-portal authority is intentional** — any real portal actor may act.
5. **Trust Spine integration is incomplete / indirect** — history and notifications exist, but direct Trust Spine event production is not evidenced in the route owner.
6. **Performance ownership is mostly attributable to Family 3B** for query shape, fan-out search, payload size, and photo workflow; some latency and auth work is shared infrastructure.

### Phase B recommendation

- **GO** for a future bounded Phase B.

Reason:

- one bounded constitutional family exists
- repository owner is clear
- mutation boundary is deterministic
- API surface is deterministic
- direct frontend consumers are deterministic
- performance ownership is materially understandable, with a documented register
- adjacent families remain separable

However, Phase B should explicitly preserve the following evidence-backed tensions:

- portal-token-alone documentation/tests vs live runtime dependency on `X-Directory-Token`
- missing direct Trust Spine writes from the owner route
- missing dedicated immutable audit collection outside per-record `history`
- missing formal doctrine file referenced by code (`/app/memory/OA1_OPERATIONS_ACTIONS_CONSTITUTION.md` not present)

---

## Repository Evidence

### Primary backend files inspected

- `/app/backend/routes/operations_actions/api.py`
- `/app/backend/routes/operations_actions/__init__.py`
- `/app/backend/server.py`
- `/app/backend/lib/event_fanout.py`
- `/app/backend/session_timeout.py`
- `/app/backend/pm_auth.py`
- `/app/backend/dispatch_users.py`
- `/app/backend/safety_users.py`
- `/app/backend/routes/auth_directory_routes.py`

### Primary frontend files inspected

- `/app/frontend/src/pages/operations_actions/OperationsActions.jsx`
- `/app/frontend/src/pages/operations_actions/OperationsActionNew.jsx`
- `/app/frontend/src/pages/operations_actions/OperationsActionDetail.jsx`
- `/app/frontend/src/lib/oa.js`
- `/app/frontend/src/components/oa/OperationsActionsTile.jsx`
- `/app/frontend/src/components/oa/OwnerPicker.jsx`
- `/app/frontend/src/components/oa/PhotoUploader.jsx`
- `/app/frontend/src/components/oa/HistoryFeed.jsx`
- `/app/frontend/src/components/oa/CoachingPanel.jsx`
- `/app/frontend/src/components/oa/StatusBadge.jsx`
- `/app/frontend/src/app/routing/AppRoutes.jsx`
- `/app/frontend/src/lib/api.js`
- `/app/frontend/src/lib/portalAuthScope.js`
- `/app/frontend/src/lib/portalContext.js`
- portal hubs with OA tile:
  - `PmHub.jsx`
  - `DispatchHub.jsx`
  - `SafetyHub.jsx`
  - `ShopHub.jsx`
  - `FieldLeadershipPortalDashboard.jsx`

### Tests inspected

- `/app/backend/tests/test_oa1_operations_actions.py`
- `/app/backend/tests/test_oa1_cross_portal.py`
- `/app/backend/tests/test_track15_operational_reality.py`
- `/app/backend/tests/test_track14_discoverability_finalization.py`
- `/app/backend/tests/test_track_24_2_safe_regex_and_route_hardening.py`

### Runtime observations collected

Measured preview latencies with valid admin + directory session:

- `GET /api/operations-actions/summary` → **364.3 ms**
- `GET /api/operations-actions?limit=20` → **512.7 ms**
- `GET /api/operations-actions/owner-search?q=jaymn&limit=10` → **557.4 ms**

Index evidence from `db.operations_actions.list_indexes()`:

- `_id_`
- `oa_id_unique` on `id`
- `oa_number_unique` on `oa_number`
- `oa_status` on `status`
- `oa_owner_id` on `current_owner.id`
- `oa_job` on `job_number`
- `oa_created_desc` on `created_at desc`

---

## Family Identity

### Does Family 3B exist as a bounded family?

- **Yes**.

Repository evidence:

- `backend/routes/operations_actions/api.py` is a dedicated route owner module.
- `backend/routes/operations_actions/__init__.py` explicitly defines a separate module boundary.
- `AppRoutes.jsx` mounts a dedicated route set for `/operations-actions`, `/operations-actions/new`, and `/operations-actions/:id`.
- `oa.js` is a dedicated frontend API client wrapper.
- Dedicated backend tests exist under `test_oa1_*`.

### Constitutional classification

- **MUTATING CROSS-PORTAL OPERATIONAL COORDINATION FAMILY**

### Truth subject

The family’s owned truth subject is:

- the `operations_actions` coordination record
- its approved six-state lifecycle
- owner assignment
- notes
- photos
- append-only in-record `history`

### Important identity distinction

The module header states:

> “ForgedOps is NEVER the system of record.”

Repository interpretation:

- Family 3B is **not** the source of truth for every external operational system.
- Family 3B **is** the direct owner of the coordination record in `db.operations_actions`.

This is not a contradiction if interpreted precisely:

- external operational truth ≠ `operations_actions` truth
- the OA record itself is directly owned here

---

## Route Ownership and Backend Architecture

### Canonical route owner

- `backend/routes/operations_actions/api.py`

### Registration path

- `register_operations_actions_routes(router, db, require_actor)`
- mounted from `backend/server.py`

### Backend design

The module is structurally cohesive:

1. constants / enums
2. request models
3. helper functions
4. owner search helper
5. in-record history helper
6. assignment notification helper
7. route registration function

### Owned collection

- `db.operations_actions`

### Supporting collections / infra touched

- `db.system_counters` for OA number sequencing
- directory collections for owner search:
  - `user_directory`
  - `project_managers`
  - `dispatch_users`
  - `hr_users`
  - `safety_users`
  - `field_leadership_users`
  - `shop_users`
- `notifications` indirectly via `emit_notification(...)`
- photo storage / R2 via `photo_storage`

### Backend owner conclusion

Family 3B is **not** an aggregator. It is a mutating owner route for its own coordination record.

---

## Frontend Consumers

### Primary pages

| Route | Frontend owner | Role |
|---|---|---|
| `/operations-actions` | `OperationsActions.jsx` | list / filter / summary inbox |
| `/operations-actions/new` | `OperationsActionNew.jsx` | create action |
| `/operations-actions/:id` | `OperationsActionDetail.jsx` | read / edit / assign / status / notes / photos / history |

### Shared OA components

| Component | Role |
|---|---|
| `OperationsActionsTile.jsx` | hub badge / entry surface |
| `OwnerPicker.jsx` | cross-directory owner typeahead |
| `PhotoUploader.jsx` | upload / view / delete photo evidence |
| `HistoryFeed.jsx` | render in-record lifecycle history |
| `StatusBadge.jsx` | render approved six-state badge only |
| `CoachingPanel.jsx` | behavioral guidance / usage doctrine |

### Cross-portal discoverability evidence

The OA tile is embedded in multiple portals:

- PM
- Dispatch
- Safety
- Shop
- Field Leadership

This proves the family is intended as a **shared operational lane**, not an admin-only surface.

### Frontend auth behavior

- `oa.js` delegates to global `api`
- `api.js` attaches scoped portal auth headers
- `/operations-actions` is treated as a shared cross-portal helper path

---

## API Surface Inventory

All routes live under `/api/operations-actions`.

| Method | Endpoint | Function |
|---|---|---|
| GET | `/owner-search` | cross-directory owner typeahead |
| GET | `/summary` | badge counts + mine_open |
| GET | `/` | list + filters |
| POST | `/` | create OA |
| GET | `/{oa_id}` | read one |
| PATCH | `/{oa_id}` | edit core fields |
| POST | `/{oa_id}/assign` | assign / reassign owner |
| POST | `/{oa_id}/status` | lifecycle transition |
| POST | `/{oa_id}/notes` | append note |
| POST | `/{oa_id}/photos` | upload photo evidence |
| GET | `/{oa_id}/photos/{photo_id}/url` | presign photo read |
| DELETE | `/{oa_id}/photos/{photo_id}` | delete photo reference + best-effort storage delete |

---

## Authorization Model

### Repository-declared model

The module docstring says:

- all endpoints gate on `_require_oa_actor`
- `_require_oa_actor` accepts **ANY real portal token**
- “No portal-level write asymmetry in OA-1 by design”

### Repository-verified actor model

`_actor_to_owner(actor)` maps these actor kinds:

- admin → `user_directory`
- safety → `safety_users`
- hr → `hr_users`
- dispatch → `dispatch_users`
- pm → `project_managers`
- shop → `shop_users`
- fl / field_leadership → `field_leadership_users`

### Live runtime finding

Live preview evidence shows a material auth nuance:

- portal token **alone** returned 401 on `/api/operations-actions/summary`
- portal token **plus matching `X-Directory-Token`** returned 200 for admin, pm, dispatch, safety, shop, and fl

Root cause evidence:

- portal token validators in `pm_auth.py`, `dispatch_users.py`, `safety_users.py`, etc. all call `has_active_session_activity(...)`
- `session_timeout.py` requires a matching bound directory session when `directory_session_token_hash` exists

### Authorization contradiction

There is a repository/runtime contract tension:

| Claim | Evidence |
|---|---|
| “Any real portal token” | module docstring + cross-portal tests assume isolated token lanes |
| live runtime requirement | portal token must be paired with the bound directory session token |

### Constitutional interpretation

This is **not** a boundary collapse.

It is a **contract contradiction** between:

- route/module docs and some tests
- current session-binding runtime behavior

---

## Workflow Ownership

Family 3B owns the lifecycle workflow of the OA record itself:

- creation
- owner assignment
- status progression
- note accumulation
- photo evidence attachment
- history accumulation
- closure

What Family 3B does **not** own by repository evidence:

- broader dispatch lifecycle truth
- incident truth
- corrective action truth in other families
- external ticketing systems
- recovery / deployment / survivability workflows

---

## Command Model and Operation Inventory

### Approved lifecycle states

- `open`
- `assigned`
- `in_progress`
- `waiting`
- `completed`
- `closed`

### Command inventory

| Operation | Endpoint | Classification | Read-only or mutating | Direct mutation? | Canonical owner | Audit produced? | Idempotent? | Confirmation required? | Rollback possible? | Administrative authority | Operational authority |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Owner search | `GET /owner-search` | Read / Validate | Read-only | No | Family 3B reads shared directories | No dedicated audit row | Yes | No | N/A | None | none |
| Summary | `GET /summary` | Read | Read-only | No | Family 3B | No | Yes | No | N/A | None | none |
| List | `GET /` | Read / Validate | Read-only | No | Family 3B | No | Yes | Yes for same query | No | N/A | None | none |
| Create | `POST /` | Execute | Mutating | Yes | Family 3B | `history.created`; optional notification if owner set | No | No | No explicit rollback | Any real portal actor | creates OA record |
| Read one | `GET /{oa_id}` | Read | Read-only | No | Family 3B | No | Yes | No | N/A | None | none |
| Patch fields | `PATCH /{oa_id}` | Repair / Update | Mutating | Yes | Family 3B | `history.updated` | Effectively yes when no diffs | No | No explicit rollback | Any real portal actor | edits OA core fields |
| Assign owner | `POST /{oa_id}/assign` | Execute / Override | Mutating | Yes | Family 3B | `history.assigned` + best-effort notification | No | No | Reassign can supersede; no formal rollback | Any real portal actor | changes owner |
| Change status | `POST /{oa_id}/status` | Execute / Approve / Cancel / Archive-like close | Mutating | Yes | Family 3B | `history.status_changed`; optional note append | Same-status request returns existing doc | No | No reopen route in owner file | Any real portal actor | changes lifecycle state |
| Add note | `POST /{oa_id}/notes` | Execute / Append | Mutating | Yes | Family 3B | `history.note_added` + note row | No | No | No | Any real portal actor | adds note evidence |
| Upload photo | `POST /{oa_id}/photos` | Execute / Append evidence | Mutating | Yes | Family 3B record + shared storage infra | `history.photo_added` | No | No | Partial via delete | Any real portal actor | adds photo evidence |
| Photo URL | `GET /{oa_id}/photos/{photo_id}/url` | Read | Read-only | No | Family 3B + shared storage infra | No | Yes | No | N/A | None | none |
| Delete photo | `DELETE /{oa_id}/photos/{photo_id}` | Delete | Mutating | Yes | Family 3B record + shared storage infra | `history.photo_deleted` | Repeat after delete = 404 | Browser confirm in UI only | No restore path | Any real portal actor | removes photo ref |

---

## Command Lifecycle Mapping

### 1. Create Action

- **Trigger source:** `OperationsActionNew.jsx` → `oaApi.create(...)`
- **Validation:** Pydantic `CreatePayload`; enum validation for category + priority
- **Authorization:** `_require_oa_actor`
- **Execution:** generate id + OA number → insert into `db.operations_actions`
- **State transition:** `open` or `assigned` when owner is supplied
- **Audit generation:** `history.created`
- **Notification/event generation:** best-effort assignment notification only if owner exists
- **Completion criteria:** insert succeeds and record returned
- **Failure handling:** 422 enum issues, auth failure, DB failure
- **Retry behavior:** no explicit retry
- **Rollback capability:** none
- **Idempotency:** no

### 2. Update Core Fields

- **Trigger source:** detail page save
- **Validation:** Pydantic `UpdatePayload`, enum validation
- **Authorization:** `_require_oa_actor`
- **Execution:** compare fields → `update_one`
- **State transition:** no lifecycle transition
- **Audit generation:** `history.updated`
- **Notification/event generation:** none
- **Completion criteria:** updated doc returned
- **Failure handling:** 404 missing, 409 if closed
- **Retry behavior:** no explicit retry
- **Rollback capability:** none
- **Idempotency:** effectively yes if no diffs

### 3. Assign / Reassign Owner

- **Trigger source:** detail page owner picker
- **Validation:** `AssignPayload`, directory enum validation
- **Authorization:** `_require_oa_actor`
- **Execution:** update owner + assigned_at + last_updated_at; `open → assigned`
- **State transition:** `open → assigned` or owner-only change
- **Audit generation:** `history.assigned`
- **Notification/event generation:** `_notify_assignment(...)` → `emit_notification(...)`
- **Completion criteria:** updated doc returned and notification attempted
- **Failure handling:** 404 missing, 409 closed
- **Retry behavior:** no route-level retry; notification best-effort only
- **Rollback capability:** manual reassignment only
- **Idempotency:** no

### 4. Change Status

- **Trigger source:** detail page status buttons
- **Validation:** enum validation + transition rules
- **Authorization:** `_require_oa_actor`
- **Execution:** `update_one`
- **State transition:** among six approved statuses; `closed` is terminal in OA-1
- **Audit generation:** `history.status_changed`, optional note append
- **Notification/event generation:** none evidenced here
- **Completion criteria:** updated doc returned
- **Failure handling:** 404 missing, 409 invalid transition
- **Retry behavior:** same-status request returns existing doc
- **Rollback capability:** no reopen route
- **Idempotency:** same-status request is effectively idempotent

### 5. Add Note

- **Trigger source:** detail page note submit
- **Validation:** `NotePayload` min/max length
- **Authorization:** `_require_oa_actor`
- **Execution:** append note + history
- **State transition:** none
- **Audit generation:** `history.note_added`
- **Notification/event generation:** none
- **Completion criteria:** note returned
- **Failure handling:** 404 missing
- **Retry behavior:** none
- **Rollback capability:** none
- **Idempotency:** no

### 6. Upload Photo

- **Trigger source:** detail page photo uploader
- **Validation:** OA existence, file size, magic-byte content-type validation
- **Authorization:** `_require_oa_actor`
- **Execution:** synchronous file read → storage upload → append photo + history
- **State transition:** none
- **Audit generation:** `history.photo_added`
- **Notification/event generation:** none
- **Completion criteria:** photo metadata returned
- **Failure handling:** 404 missing OA, 413 oversize, 422 format, 503 storage not configured, 500 upload failure
- **Retry behavior:** no explicit retry
- **Rollback capability:** partial via photo delete
- **Idempotency:** no

### 7. Delete Photo

- **Trigger source:** detail page delete confirmation
- **Validation:** OA + photo existence
- **Authorization:** `_require_oa_actor`
- **Execution:** best-effort storage delete → pull photo ref → append history
- **State transition:** none
- **Audit generation:** `history.photo_deleted`
- **Notification/event generation:** none
- **Completion criteria:** `{ok: true}` returned
- **Failure handling:** 404 missing OA / photo; storage delete failure is logged and ignored
- **Retry behavior:** no explicit retry
- **Rollback capability:** none
- **Idempotency:** no formal idempotency, repeat after success becomes 404

---

## Mutation Authority Matrix

| Operation | Canonical record modified | Canonical owner | Mutation owner | Audit owner | Trust owner |
|---|---|---|---|---|---|
| Create OA | `operations_actions` doc | Family 3B | Family 3B direct | Family 3B `history` | Unknown / missing direct Trust Spine write |
| Patch fields | `operations_actions` doc | Family 3B | Family 3B direct | Family 3B `history` | Unknown / missing direct Trust Spine write |
| Assign owner | `operations_actions.current_owner`, `assigned_at`, maybe `status` | Family 3B | Family 3B direct | Family 3B `history` | Notification infra for downstream visibility; no direct Trust Spine write evidenced |
| Change status | `operations_actions.status`, `closed_at`, `notes?` | Family 3B | Family 3B direct | Family 3B `history` | Unknown / missing direct Trust Spine write |
| Add note | `operations_actions.notes` | Family 3B | Family 3B direct | Family 3B `history` | Unknown / missing direct Trust Spine write |
| Upload photo | `operations_actions.photos` + shared storage object | Family 3B record + shared storage infra | Family 3B + storage infra | Family 3B `history` | Unknown / missing direct Trust Spine write |
| Delete photo | `operations_actions.photos` + shared storage object delete attempt | Family 3B record + shared storage infra | Family 3B + storage infra | Family 3B `history` | Unknown / missing direct Trust Spine write |

### Matrix conclusion

- Family 3B mutates its own canonical coordination record directly.
- Repository evidence does **not** show Family 3B issuing a command to another canonical family in order to mutate the OA record.
- Repository evidence does **not** show orchestration across multiple canonical owners beyond:
  - owner-directory lookup reads
  - in-app notification emission on assignment
  - photo storage integration

No direct canonical ownership violation was found in the owner route itself.

---

## Audit Model

### What is definitely present

Family 3B keeps an **append-only in-record history rail**:

- `created`
- `updated`
- `assigned`
- `status_changed`
- `note_added`
- `photo_added`
- `photo_deleted`

Each entry includes:

- `id`
- `kind`
- actor via `_actor_to_owner(actor)`
- `before` / `after`
- timestamp `at`

### What is not directly evidenced

- no dedicated `admin_audit` write in the route owner
- no dedicated immutable out-of-record audit collection in the owner route
- no direct Trust Spine event insertion evidenced in the owner route

### Audit conclusion

The family has **good local auditability** via `history`, but **weaker platform-wide forensic evidence** than a dual-write design would provide.

---

## Trust Spine Integration Analysis

### Produced events — repository-evidenced

Direct Trust Spine production from `operations_actions/api.py` is **not evidenced**.

### Produced non-Trust events / indirect signals

- assignment path emits in-app notification via `emit_notification(...)`
- notification payload uses:
  - `type = oa_assignment`
  - `linked_source_module = operations_action`
  - `linked_source_record_id = oa_id`

### Consumed trust/audit signals

Repository evidence does **not** show OA routes consuming `trust_spine_events` directly.

### Missing Trust Spine evidence

For core OA mutations, the owner file does **not** show direct Trust Spine production for:

- create
- assign
- status change
- close
- note append
- photo add/delete

### Duplicate or contradictory Trust evidence

- no duplicate Trust event writer found inside the route owner
- but there is a traceability asymmetry:
  - local `history` exists
  - notification exists only for assignment
  - no direct Trust Spine row is evidenced in the route owner

### Trust conclusion

Family 3B has **local lifecycle traceability**, but **direct Trust Spine integration appears incomplete or delegated elsewhere**, and repository evidence inside the owner route is insufficient to claim full Trust Spine parity.

---

## Duplicates, Contradictions, Dead Code, Legacy, Unknown Ownership

### Repository contradictions

#### 1. Token contract contradiction

- code/comments/tests imply “any real portal token”
- live runtime requires the matching bound directory session token too

Classification:

- Owner: **shared infrastructure + Family 3B contract surface**

#### 2. Missing constitution file reference

`backend/routes/operations_actions/__init__.py` and `AppRoutes.jsx` reference:

- `/app/memory/OA1_OPERATIONS_ACTIONS_CONSTITUTION.md`

But the file is not present.

Classification:

- **dead / missing doctrine reference**

#### 3. Cross-portal test assumption tension

`test_oa1_cross_portal.py` is built around isolated portal-token lanes defeating conftest admin auto-attach.

Live runtime evidence shows the requests need the directory token as well.

Classification:

- **test/runtime contract drift**

### Duplicate implementations

- No duplicate backend owner route for the OA record was found.
- No alternate CRUD owner for `operations_actions` was found.

### Legacy code evidence

- comments note the legacy `kind=oa_assignment` notification shape was retired
- new notification path is canonicalized via `emit_notification(...)`

### Unknown ownership

- direct Trust Spine ownership for OA lifecycle events is **unknown** from the owner route
- platform-wide immutable audit ownership beyond in-record `history` is **unknown / not evidenced here**

---

## Performance & Latency Discovery

## Performance Ownership Register

| Endpoint / flow | Finding | Likely cause class | Ownership | Priority | Status |
|---|---|---|---|---|---|
| `GET /summary` | aggregate count + actor-specific count on every request | Database / repeated query work | Family 3B | Medium | Runtime observed |
| `GET /summary` | `mine_open` adds second query beyond aggregate | Database / duplicate query pass | Family 3B | Low | Repository verified |
| `GET /` | two-query list path: `count_documents` + `find` | Database | Family 3B | Medium | Repository verified |
| `GET /` | potentially large payload with full action rows (all fields except history) | Excessive payload / serialization | Family 3B | Medium | Repository verified |
| `GET /owner-search` | fan-out sequential search across 7 collections | Database / search/indexing / duplicate processing | Family 3B + shared directory families | High | Repository verified + runtime observed |
| `GET /owner-search` | no explicit parallelization across collections | Code path / blocking async sequence | Family 3B | Medium | Repository verified |
| `POST /` | OA number generation hits `system_counters` before insert | Database / sequencing | Family 3B + shared infra | Low | Repository verified |
| `POST /` and `/assign` | best-effort notification adds downstream dependency | External dependency / network | Shared infrastructure | Medium | Repository verified |
| `PATCH /{id}` / `POST /assign` / `POST /status` | read → update → read pattern | Database / duplicate query pattern | Family 3B | Medium | Repository verified |
| `POST /photos` | synchronous `await file.read()` + upload to storage | Blocking I/O / external dependency | Family 3B + shared infrastructure | High | Repository verified |
| `GET /photos/.../url` | storage presign call | External dependency / network | Shared infrastructure | Medium | Repository verified |
| Cross-portal auth on every route | repeated session-activity + directory binding validation | Authorization / shared infra | Shared infrastructure | Medium | Repository verified + runtime observed |

---

## Latency Ownership Register

| Endpoint / flow | Observed / inferred behavior | Likely root cause | Architectural / config / data / code / infra | Owner | Priority | Status |
|---|---|---|---|---|---|---|
| `GET /summary` | 364.3 ms in preview | aggregate + actor-specific count + auth binding | Code path + database + shared auth infra | Family 3B + shared infra | Medium | Runtime observed |
| `GET /` with `limit=20` | 512.7 ms in preview | count query + list query + serialization of full rows | Code path + database + payload size | Family 3B | Medium | Runtime observed |
| `GET /owner-search?q=jaymn&limit=10` | 557.4 ms in preview | 7 collection scans, dedupe, auth | Search/indexing + database + code path | Family 3B + directory-family infra | High | Runtime observed |
| `POST /` | no direct runtime measurement collected | counter increment + insert + optional notify | Database + notification infra | Family 3B + shared infra | Medium | Needs verification |
| `PATCH /{id}` | no direct runtime measurement collected | read/update/read pattern | Database + code path | Family 3B | Medium | Needs verification |
| `POST /{id}/assign` | no direct runtime measurement collected | read/update/read + notify | Database + external dependency | Family 3B + shared infra | High | Needs verification |
| `POST /{id}/status` | no direct runtime measurement collected | read/update/read + optional note append | Database + serialization | Family 3B | Medium | Needs verification |
| `POST /{id}/notes` | no direct runtime measurement collected | update with embedded arrays + history append | Database | Family 3B | Low | Needs verification |
| `POST /{id}/photos` | no direct runtime measurement collected | full file read, type detect, upload, update | Blocking I/O + external dependency + infra | Family 3B + shared infra | Critical | Repository verified |
| `GET /{id}/photos/{photo_id}/url` | no direct runtime measurement collected | storage presign call | External dependency / network | Shared infrastructure | Medium | Repository verified |
| `DELETE /{id}/photos/{photo_id}` | no direct runtime measurement collected | best-effort storage delete + DB update | External dependency + database | Family 3B + shared infra | Medium | Repository verified |

---

## Endpoint-Level Performance Readiness

| Endpoint | Repository owner | Expected SLA / target | Current observed behavior | Optimization owner | Belongs in Family 3B? |
|---|---|---|---|---|---|
| `GET /owner-search` | Family 3B route owner | No repository SLA defined | ~557 ms preview sample | Family 3B + shared directory/index owners | **Yes, primarily** |
| `GET /summary` | Family 3B route owner | No repository SLA defined | ~364 ms preview sample | Family 3B + shared auth infra | **Yes, primarily** |
| `GET /` | Family 3B route owner | No repository SLA defined | ~513 ms preview sample for 20 rows | Family 3B | **Yes** |
| `POST /` | Family 3B route owner | No repository SLA defined | not measured | Family 3B + shared notify infra | **Yes, primarily** |
| `GET /{oa_id}` | Family 3B route owner | No repository SLA defined | not measured | Family 3B | **Yes** |
| `PATCH /{oa_id}` | Family 3B route owner | No repository SLA defined | not measured | Family 3B | **Yes** |
| `POST /{oa_id}/assign` | Family 3B route owner | No repository SLA defined | not measured | Family 3B + notification infra | **Yes, primarily** |
| `POST /{oa_id}/status` | Family 3B route owner | No repository SLA defined | not measured | Family 3B | **Yes** |
| `POST /{oa_id}/notes` | Family 3B route owner | No repository SLA defined | not measured | Family 3B | **Yes** |
| `POST /{oa_id}/photos` | Family 3B route owner + shared storage | No repository SLA defined | not measured | Family 3B + storage infra | **Shared** |
| `GET /{oa_id}/photos/{photo_id}/url` | Family 3B route owner + shared storage | No repository SLA defined | not measured | Shared storage infra | **Partially** |
| `DELETE /{oa_id}/photos/{photo_id}` | Family 3B route owner + shared storage | No repository SLA defined | not measured | Family 3B + storage infra | **Shared** |

### Performance readiness conclusion

Performance ownership is sufficiently understandable for future bounded work:

- core list / summary / mutation query shape = Family 3B
- photo upload / presign / delete = Family 3B + shared storage infrastructure
- session-binding auth cost = shared auth infrastructure
- owner-search latency = Family 3B plus directory/index owners

---

## Repository Risks

1. **Auth contract drift** between doc/tests and live session-bound runtime.
2. **Missing doctrine file** referenced by code.
3. **No direct Trust Spine write evidence** for core lifecycle mutations.
4. **No dedicated immutable audit collection** evidenced in owner route.
5. **Read/update/read mutation pattern** repeated across multiple mutators.
6. **Owner search fans out sequentially across seven collections.**
7. **Photo path depends on shared storage infrastructure and blocking file read.**

---

## Constitutional Analysis

### Canonical owner

- Clear: Family 3B owns `operations_actions` CRUD lifecycle.

### Route ownership

- Clear: one route owner file.

### Mutation ownership

- Clear: Family 3B directly mutates its own canonical coordination records.

### Audit ownership

- Partially clear: Family 3B owns in-record `history`; platform-wide immutable audit ownership is not evidenced here.

### Trust ownership

- Incomplete / partially unknown: Trust Spine integration is not directly evidenced in owner routes.

### Adjacent family separation

- Preserved.

No repository evidence shows Family 3B directly mutating:

- Family 3A admin observability truth
- Family 3C operational events truth
- Family 3D asset-mapping truth

The family reads shared identity directories and uses shared notification/storage infrastructure, but retains a clear owned mutation subject.

---

## GO / NO-GO Recommendation

## GO — Family 3B is a valid bounded constitutional family for future Phase B

### Evidence basis for GO

- one repository owner exists
- API surface is deterministic
- frontend surface is deterministic
- mutation boundary is deterministic
- direct owner collection is deterministic
- adjacent family separation is preserved
- performance ownership is sufficiently understandable to produce a deterministic optimization backlog

### Required cautions for any future Phase B

Future Phase B should explicitly address, but not overreach beyond Family 3B:

1. portal-token contract drift vs live directory-bound runtime
2. missing doctrine file reference
3. Trust Spine write / audit-rail completeness
4. owner-search fan-out cost
5. photo-path storage dependency and blocking upload flow

---

## Discovery Verdict

Family 3B — Operations Actions — is **Present**, **bounded**, **mutating**, and **constitutionally separable**.

It is not a read-only family and it is not merely an admin view. It is a cross-portal operational coordination owner with direct mutation authority over the `operations_actions` record family.

Repository evidence supports advancing to a future bounded Phase B **only by explicit user authorization**.

Stop here and wait for authorization before any implementation.