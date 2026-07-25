# BCSS RELEASE 2 · PROGRAM 2
## WAVE 3 · FAMILY 2
## OCC TRUST EVENTS
## PHASE A — CAPABILITY VERIFICATION & REPOSITORY DISCOVERY

Date: 2026-07-25

Status: DISCOVERY ONLY · READ-ONLY · NO IMPLEMENTATION

---

## Executive Summary

Repository evidence confirms that **OCC Trust Events already exists** as a live backend family centered on:

- `GET /api/admin/occ/trust-events`
- runtime file: `/app/backend/routes/occ_trust_events.py`

It is constitutionally best classified as an **AGGREGATOR**.

It is **not** a canonical event owner, **not** a canonical event producer, and **not** a registered truth surface in `backend/lib/canonical_truth.py`.

The family currently operates as a **read-only composite event feed** that fans in recent evidence from:

- `admin_audit`
- `scheduler_runs`
- `operations_audit`
- legacy `/api/admin/deploy-readiness`

Repository evidence does **not** show a dedicated OCC Trust Events frontend page or route. Instead, the feed is consumed indirectly by:

- `frontend/src/pages/admin/AdminGovernanceTrust.jsx`
- `frontend/src/pages/admin/AdminIdentitySecurity.jsx`

The family is **Present** in runtime terms, but **constitutionally incomplete** in OTS terms because:

1. it has **no canonical truth registration**
2. it exposes **no explicit truth subject / owner / claim ceiling contract**
3. it has **no unified event identity model** at the aggregated feed layer
4. it performs **no feed-level deduplication, contradiction handling, or replay**
5. it still consumes the **legacy** deploy-readiness route family flagged by `BCSS-R18`

Phase B appears **constitutionally justified**, but only as a **strictly bounded hardening** of the existing aggregator contract — not as a redesign, event-platform rebuild, or new event engine.

---

## Repository Evidence

### Core runtime evidence

- Backend route file: `/app/backend/routes/occ_trust_events.py`
- Mount registration: `/app/backend/server.py:3880-3884`
- Existing backend verification: `/app/backend/tests/test_track_25_sprint_7_8_trust_events.py`

### Consumer evidence

- `frontend/src/pages/admin/AdminGovernanceTrust.jsx`
- `frontend/src/pages/admin/AdminIdentitySecurity.jsx`
- No dedicated `/admin/occ/trust-events` page route found in `frontend/src/app/routing/AppRoutes.jsx`

### Constitutional / planning evidence

- `/app/memory/BCSS_RELEASE2_PROGRAM2_CHECKPOINT6_PHASEA_DISCOVERY.md`
- `/app/memory/BCSS_RELEASE2_PROGRAM2_CHECKPOINT4_SURFACE_CLAIM_MATRIX.md`
- `/app/memory/BCSS_MASTER_IMPLEMENTATION_PROGRAM_v1.0.md`
- `/app/memory/PRD.md`

### Specific repository tensions already documented

- Checkpoint 6 discovery records `/api/admin/occ/trust-events` as a **composite trust-events feed with no BCSS canonical OTS binding yet**.
- BCSS master backlog records **`BCSS-R18`**: `OCC trust-events deployment-readiness probe path is inconsistent with actual endpoint`.

---

## Runtime Inventory

### Backend runtime files

- `/app/backend/routes/occ_trust_events.py`
- `/app/backend/server.py` (mount registration only)

### Frontend runtime files

Direct consumers:

- `/app/frontend/src/pages/admin/AdminGovernanceTrust.jsx`
- `/app/frontend/src/pages/admin/AdminIdentitySecurity.jsx`

Related but separate event/audit viewers:

- `/app/frontend/src/pages/admin/AdminAuditLog.jsx`
- `/app/frontend/src/pages/AdminSchedulerRuns.jsx`
- `/app/frontend/src/pages/admin/AdminOperationsEvents.jsx`

### Mounted routes

- Backend mounted route:
  - `GET /api/admin/occ/trust-events`

### Services

The route is a **request-time fanout aggregator** using `httpx.AsyncClient` and admin-gated header forwarding.

It directly calls:

- `/api/admin/audit?limit={limit}`
- `/api/admin/scheduler-runs?limit={limit}`
- `/api/admin/operations-control/audit?limit={limit}`
- `/api/admin/deploy-readiness`

### Background jobs

- None discovered for OCC Trust Events itself.
- The route does **not** publish or subscribe to a background queue.
- It performs on-demand read aggregation only.

### Event publishers

- None at the OCC Trust Events family layer.
- The route reads and reclassifies child events; it does not emit a new event stream.

### Event subscribers

- None discovered in pub/sub terms.
- Functionally, the family is a **polling consumer** of child read endpoints.

---

## Frontend Inventory

### Dedicated OCC Trust Events page

- **Not found**.

Repository evidence shows **no dedicated frontend page** or AppRoutes entry for `/admin/occ/trust-events`.

### Actual frontend consumption

#### 1. Governance & Trust domain landing
- File: `/app/frontend/src/pages/admin/AdminGovernanceTrust.jsx`
- Uses `/admin/occ/trust-events?limit=25`
- Derives:
  - unified-trust-events card
  - unresolved deploy blockers card

#### 2. Identity & Security domain landing
- File: `/app/frontend/src/pages/admin/AdminIdentitySecurity.jsx`
- Uses `/admin/occ/trust-events?limit=25`
- Derives:
  - recent auth failures card

### Frontend classification

OCC Trust Events is currently a **backend feed consumed by domain cards**, not a standalone operator console.

---

## API Inventory

### Family API

- `GET /api/admin/occ/trust-events`
  - query param: `limit` (default `25` in route)
  - admin-gated

### Response envelope

The route returns:

- `generated_at`
- `counts`
- `by_kind`
- `auth_failures_in_window`
- `unresolved_blockers`
- `events`
- `probe_errors`

### Child APIs consumed

- `GET /api/admin/audit?limit={limit}`
- `GET /api/admin/scheduler-runs?limit={limit}`
- `GET /api/admin/operations-control/audit?limit={limit}`
- `GET /api/admin/deploy-readiness`

### Repository conflict in the route contract

The route docstring states that the feed composes a **governance findings snapshot**, but the implemented `asyncio.gather(...)` in `occ_trust_events.py` does **not** call any governance endpoint.

This is a **repository truth conflict** between declared purpose and runtime implementation.

---

## Data Inventory

### Direct data access by OCC Trust Events

- **None**. The route does not query Mongo directly.

### Indirect data sources via child routes / child collections

#### 1. `admin_audit`
- surfaced through `/api/admin/audit`
- TTL evidence in `server.py` keeps `admin_audit.at` for 365 days

#### 2. `scheduler_runs`
- surfaced through `/api/admin/scheduler-runs`
- explicit collection + unique slot dedup + TTL 90 days in `backend/lib/scheduler_runs.py`

#### 3. `operations_audit`
- surfaced through `/api/admin/operations-control/audit`
- append-only by convention in `backend/services/operations_control/audit.py`

#### 4. legacy deploy-readiness evidence
- surfaced through `/api/admin/deploy-readiness`
- that route itself reads many operational collections and integration signals
- OCC Trust Events consumes only the returned blocker/warning summary, not the underlying collections directly

### Database collections / tables implicated by family behavior

Direct: none

Indirect, repository-proven:

- `admin_audit`
- `scheduler_runs`
- `operations_audit`
- plus whatever collections the legacy deploy-readiness route inspects internally

### Event persistence

- OCC Trust Events itself does **not** persist a unified feed collection.
- It materializes the feed fresh on each request.

---

## Event Architecture Inventory

### What constitutes a Trust Event?

Repository evidence shows that a Trust Event in this family is **not a canonical event class**. It is a **normalized envelope** built from one of four child-source record types:

1. admin audit row → `_classify_audit(...)`
2. scheduler run row → `_from_scheduler(...)`
3. OCC operations audit row → `_from_ops_audit(...)`
4. deploy readiness blocker/warning → `_from_deploy_blocker(...)`

### Event schema(s)

Unified OCC Trust Events envelope per item:

```json
{
  "ts": "ISO string or null",
  "kind": "audit | auth | deploy | scheduler | ops_audit | deploy_blocker",
  "severity": "info | warning | critical",
  "summary": "human-readable summary",
  "source_endpoint": "child API route",
  "evidence": { "child-source subset" }
}
```

### Event lifecycle

- No independent OCC Trust Events lifecycle was found.
- The family only transforms existing child events into a recent merged feed.

### Event persistence

- No dedicated OCC Trust Events collection exists.
- Persistence lives only in upstream ledgers / child collections.

### Event retention

Repository-proven upstream retention examples:

- `admin_audit`: 365-day TTL (`server.py`)
- `scheduler_runs`: 90-day TTL (`backend/lib/scheduler_runs.py`)
- `operations_audit`: no TTL discovered; append-only by convention
- `trust_spine_events`: append-only indexes discovered; no TTL discovered in the inspected spine file

### Event replay capability

- No OCC Trust Events replay capability exists.
- The family supports **historical readback only insofar as upstream sources retain rows**.

### Event ordering guarantees

- The route sorts `events` newest-first by raw `ts` string.
- Items without `ts` fall to the end.
- No cross-source transactional ordering guarantee was found.
- No explicit stable tie-breaker was found for equal timestamps.

### Event deduplication

- **No feed-level deduplication exists** in OCC Trust Events.
- Upstream `scheduler_runs` has its own unique-slot dedup.
- Upstream `operations_audit` has unique `action_id`.
- The aggregator itself can surface overlapping facts from multiple child systems.

### Event correlation

- No top-level `correlation_id` field exists in OCC Trust Events items.
- No top-level `record_id`, `event_id`, or `causation_id` exists.
- Correlation, if any, is source-specific and buried inside child evidence or absent.

### Event audit evidence

- The route exposes child evidence subsets in `evidence`.
- It does not create a new append-only audit chain of its own.

### Unknown handling

- Child-probe failures are surfaced through `probe_errors`.
- Partial fan-in is allowed; failed probes do not block the whole response.

### Contradiction handling

- No explicit contradiction model was found.
- No duplicate/contradictory event detection exists at the feed layer.

---

## Constitutional Event Spine Verification

### Does the repository already define a canonical event model?

**Yes — but not for OCC Trust Events itself.**

Repository evidence shows a canonical lifecycle event model in:

- `/app/backend/lib/trust_spine.py`
- collection: `trust_spine_events`

That model is canonical for **workflow lifecycle truth**, not for the OCC Trust Events aggregate feed.

### Canonical Trust Event schema (existing in repository)

`trust_spine_events` minimum contract in `backend/lib/trust_spine.py` includes:

- `ts`
- `workflow`
- `stage`
- `correlation_id`
- `record_id`
- `project_number`
- `module`
- `status`
- optional `duration_ms`
- optional `failure_reason`
- optional `remediation`

### Event identity model

- `trust_spine_events` does **not** expose a dedicated `event_id` field in the inspected file.
- Identity is effectively row-level plus `correlation_id` + `stage` + `ts` + `record_id`.

### Event ID generation

- No dedicated canonical `event_id` generator was found in `trust_spine.py`.
- A canonical **correlation** generator exists via `new_correlation_id()`.

### Correlation IDs

- Implemented in `trust_spine.py`.
- Generated as `cid-<uuid4hex>` via `new_correlation_id()`.
- Propagated through workflow lifecycle events.

### Causation IDs

- **Not implemented** in the inspected Trust Spine model.

### Event timestamps

- Implemented as ISO UTC `ts` values.

### Event ordering guarantees

- Expected-stage ordering exists as a **contract**, not as a hard total-order guarantee.
- Indexes support retrieval by workflow / status / stage / timestamp.

### Event immutability

- `trust_spine_events` is append-only by repository contract.

### Replay capability

- Historical readback exists.
- No canonical replay engine was found in the Trust Spine event model itself.

### Deduplication strategy

- No generic trust-spine event dedup layer was found.
- Some workflows use stable correlation semantics; scheduler dedup exists in a separate family.

### Audit chain preservation

- `audit_written` is a canonical stage in the Trust Spine lifecycle.

### OCC Trust Events relationship to that canonical event spine

- OCC Trust Events does **not** emit `trust_spine_events`.
- OCC Trust Events does **not** consume `trust_spine_events` directly.
- OCC Trust Events is **not** currently bound to the repository’s canonical lifecycle event model.

---

## Truth Subject

### Canonical Truth Subject

- **No canonical truth subject registration found** for OCC Trust Events.

### Effective runtime subject

Repository behavior indicates an effective runtime subject of:

- **recent composite operational trust-event feed**

But this subject is **not formally registered** in `canonical_truth.py`.

### Evidence

- Checkpoint 6 discovery explicitly records `/api/admin/occ/trust-events` as a **composite trust-events feed (no BCSS canonical OTS binding yet)**.

---

## Canonical Owner

- **No canonical owner registration found** for OCC Trust Events.

The route is implemented in:

- `backend/routes/occ_trust_events.py`

but repository evidence does **not** elevate this file or route to canonical ownership.

### Upstream owners actually supplying evidence

Repository-proven upstream source families include:

- `admin_audit` / auth-directory audit path
- `scheduler_runs`
- `operations_audit`
- legacy deploy-readiness route family

OCC Trust Events itself is therefore an **aggregator over upstream evidence owners / evidence publishers**, not a canonical owner.

---

## Canonical Owner Route

- **No canonical owner route found** for OCC Trust Events.

Important distinction:

- mounted runtime route: `/api/admin/occ/trust-events`
- canonical owner route: **not registered / not present**

---

## Family Classification

### Capability Classification

- **Present**

### Family Classification

- **AGGREGATOR**

### Justification

Repository evidence shows the family:

- fans in multiple child sources
- creates no new authoritative source of truth
- publishes no canonical truth relationship contract
- forwards admin credentials and returns a read-only merged feed

It is not best classified as OWNER, because no ownership registration exists.

It is not best classified as DERIVED CONSUMER alone, because its primary runtime behavior is **multi-source event aggregation**.

---

## Claim Ceiling

- **No explicit claim ceiling is implemented in the family today.**

Repository evidence from Checkpoint 6 marks this route as:

- **Undefined in OTS terms**
- **No OTS bound contract**

Therefore the repository truth is:

- current runtime feed exists
- constitutional claim ceiling is **unbound / unstated** in code
- any stronger “canonical” event claim would exceed current repository evidence

---

## Consumer Relationships

### Upstream dependencies

Direct runtime dependencies:

- `/api/admin/audit`
- `/api/admin/scheduler-runs`
- `/api/admin/operations-control/audit`
- `/api/admin/deploy-readiness`

### Downstream consumers

Runtime UI consumers:

- `AdminGovernanceTrust.jsx`
- `AdminIdentitySecurity.jsx`

Verification / docs consumers:

- `test_track_25_sprint_7_8_trust_events.py`
- PRD references
- Checkpoint discovery documents

### Consumer relationships by topic

#### Trust Spine
- No direct runtime dependency discovered.
- Indirect adjacency exists because deployment / certification families elsewhere rely on `trust_spine_events`.

#### Operations Trust Center
- No direct runtime consumption by OCC Trust Events discovered.
- Both belong to adjacent operator-truth space but remain separate families.

#### OCC Health Aggregator
- Separate family.
- OCC Health Aggregator does not consume OCC Trust Events directly in its inspected route file.

#### Platform Attestation
- No direct runtime dependency discovered.

#### Deployment Certification / readiness surfaces
- Direct dependency discovered through `/api/admin/deploy-readiness`.

#### Admin Operations / audit systems
- Direct dependency discovered through `/api/admin/audit` and `/api/admin/operations-control/audit`.

#### Notification systems
- Indirect only.
- Scheduler history and deploy/admin audit rows may reflect notification-related activity, but OCC Trust Events is not a notification engine.

#### Audit systems
- Direct consumer of audit evidence.

---

## Operations Trust Spine Relationship

Repository evidence classifies OCC Trust Events in relation to the broader architecture as:

- **Not** a Canonical Event Producer
- **Yes** an Event Consumer
- **Yes** an Event Aggregator
- **Yes** an Event Observer
- **Partially** a Derived Consumer (it derives summary counts and auth-failure/blocker rollups from child evidence)

### Relationship map

| Relationship | Repository truth |
|---|---|
| Primary runtime role | Event Consumer + Event Aggregator + Event Observer |
| Canonical event producer? | No |
| Upstream owner(s) | Source-specific; no single OCC Trust Events owner registered |
| Downstream consumers | `AdminGovernanceTrust`, `AdminIdentitySecurity` |
| Truth subject consumed | admin audit/auth activity, scheduler execution history, OCC operations audit, deploy-readiness blocker summaries |
| Claim ceiling | not declared in code / not OTS-bound |
| Duplicate event ownership exists? | No single canonical owner claimed; duplicate aggregation pressure exists |

### Duplicate event ownership

- No direct duplicate canonical ownership was found because OCC Trust Events has **no canonical owner registration**.
- However, duplicate **aggregation and summary** pressure is real because the same underlying realities are also surfaced elsewhere.

---

## Duplicate Analysis

### Duplicate event engines

- No separate OCC Trust Events event-writing engine found.
- The family only aggregates existing child feeds.

### Duplicate notification engines

- None found in this family.
- It surfaces notification-adjacent evidence indirectly only.

### Duplicate audit / event stores

- OCC Trust Events does **not** create a new store.
- It reuses and summarizes existing stores.

### Duplicate routing

- Yes, at the summary/consumer layer.
- Related realities are also visible through:
  - `/api/admin/audit`
  - `/api/admin/scheduler-runs`
  - `/api/admin/operations-control/audit`
  - `/api/admin/deploy-readiness`
  - `AdminAuditLog.jsx`
  - `AdminSchedulerRuns.jsx`

### Duplicate truth ownership

- No OCC Trust Events canonical truth ownership exists.
- The constitutional risk is **absence of ownership binding**, not owner duplication inside the route itself.

### Duplicate aggregation

- Yes.
- Checkpoint 6 already documented `/api/admin/occ/trust-events` as duplicating blocker/auth-failure summaries that appear elsewhere.

---

## Existing Tests

### Backend

- `/app/backend/tests/test_track_25_sprint_7_8_trust_events.py`

Covered behaviors:

- endpoint reachability
- auth gate
- response envelope shape
- event item shape
- deploy event classification presence

### Frontend

- No dedicated OCC Trust Events frontend test was discovered.

### Gaps in discovered test coverage

No discovered tests assert:

- canonical owner / truth subject metadata (none exists)
- feed-level deduplication
- contradiction handling
- event identity model
- event replay guarantees
- dedicated frontend route behavior (none exists)

---

## Existing Documentation

### Existing constitutional / planning references

- `/app/memory/BCSS_RELEASE2_PROGRAM2_CHECKPOINT6_PHASEA_DISCOVERY.md`
- `/app/memory/BCSS_RELEASE2_PROGRAM2_CHECKPOINT4_SURFACE_CLAIM_MATRIX.md`
- `/app/memory/BCSS_MASTER_IMPLEMENTATION_PROGRAM_v1.0.md`
- `/app/memory/PRD.md`
- `/app/memory/BCSS_RELEASE1_PROGRAM1_CHECKPOINT1_CANONICAL_OWNERSHIP_AND_REGISTRATION.md`

### Existing family-specific observations already recorded elsewhere

- no BCSS canonical OTS binding yet
- composite fan-in over audit / scheduler / deploy blockers / ops audit
- duplicate summary pressure
- open backlog item `BCSS-R18`

### Existing memory artifact for this exact family

- None found before this discovery report.

---

## Repository Risks

1. **No canonical truth registration** for the family.
2. **No explicit truth subject / owner / claim ceiling contract**.
3. Route docstring calls the feed **“canonical”** while the repository does not register it as canonical.
4. Route docstring mentions **governance findings snapshot**, but runtime implementation does not fetch governance summary.
5. Family consumes **legacy `/api/admin/deploy-readiness`** rather than an already-adopted canonical deployment-readiness family.
6. Feed-level event identity is weak:
   - no `event_id`
   - no top-level `correlation_id`
   - no `causation_id`
7. No feed-level deduplication.
8. No feed-level contradiction handling.
9. No feed persistence / replay layer.
10. Internal base env var is named `OCC_HEALTH_INTERNAL_BASE`, which is semantically shared with another OCC family rather than dedicated to trust events.

---

## Architectural Risks

1. **Mixed-subject aggregation** across audit, scheduler, deployment, and OCC operations evidence.
2. **No single upstream canonical owner** for the aggregate feed.
3. **Duplicate operator summaries** in Governance, Identity, Audit, Scheduler, and deploy-readiness surfaces.
4. **Legacy dependency pressure** from the deploy-readiness family.
5. **No clean event-spine binding** between OCC Trust Events and the existing `trust_spine_events` canonical lifecycle model.
6. A future broad Phase B could drift into:
   - deployment readiness ownership
   - notification systems
   - audit platform redesign
   - broader event-model redesign

---

## Capability Classification

### Does OCC Trust Events already exist?

- **Yes**.

### Capability classification

- **Present**

### Why not Partial / Planned / External / Not Applicable?

- The route is mounted and tested.
- It has active frontend consumers.
- It returns live runtime data today.
- The incompleteness is **constitutional binding and architecture discipline**, not basic runtime absence.

---

## GO / NO-GO Recommendation for Phase B

## GO — BUT ONLY AS A NARROW AGGREGATOR HARDENING TRACK

### GO basis

Repository evidence justifies a bounded Phase B because the family:

- already exists in runtime
- has active downstream consumers
- lacks constitutional owner / truth / claim binding
- carries known duplicate-summary and legacy-dependency pressure
- has an already-open backlog item (`BCSS-R18`)

### Strict constitutional boundary for any future Phase B

Any future Phase B must remain limited to the **existing OCC Trust Events family** and its current direct consumers.

### Explicit NO-GO for broader work

Phase B should **not** expand into:

- Trust Spine redesign
- deploy-readiness family redesign
- backup / recovery / DR / BC work
- OCC Health Aggregator changes
- notification engine changes
- new persistence / replay engine creation
- full event-platform redesign

---

## Roadmap Dependency Verification

Repository truth only:

| Roadmap area | Classification | Repository evidence |
|---|---|---|
| Platform Survivability Program | **Independent** | no direct runtime dependency discovered |
| Backup | **Observes** | may surface backup/deploy-related facts indirectly through admin audit or deploy-readiness summaries; no direct backup route consumed |
| Recovery | **Observes** | may surface recovery-adjacent facts indirectly through audit/readiness evidence; no direct recovery route consumed |
| Disaster Recovery | **Independent** | no direct DR route or DR collection dependency discovered |
| Business Continuity | **Independent** | no BC route or BC data dependency discovered |
| Rollback | **Observes** | deploy-readiness / audit evidence may mention rollback or operator action history, but no direct rollback route consumed |
| Production Readiness Review | **Observes** | consumes legacy deploy-readiness blocker summaries, but is not a PRR owner |
| Wave 1 Deployment | **Observes** | surfaces deployment-related blockers / audit facts, but is not a deployment owner |

### Dependency verdict

The family is **not blocked by Platform Survivability Program as a runtime prerequisite**, but it does have adjacency to deployment/readiness evidence through the legacy deploy-readiness path.

---

## Constitutional Family Readiness

### Is this family constitutionally complete already?

- **No.**

Reasons proven by repository evidence:

- no canonical truth registration
- no canonical owner route
- no explicit claim ceiling
- no canonical event identity model at the aggregate feed layer
- unresolved legacy deploy-readiness dependency pressure

### Does Phase B appear constitutionally justified?

- **Yes.**

### If Phase B is justified, what is the single bounded mission?

- **Bind and harden the existing OCC Trust Events route as a non-owning read-only event aggregator, making its source boundaries, ownership absence, event-model limits, and legacy dependency usage explicit without creating a new event engine or new truth source.**

### What work is explicitly out of scope for Phase B?

- OCC Health Aggregator
- Platform Survivability Program
- Backup
- Recovery
- Disaster Recovery
- Business Continuity
- Rollback
- Production Readiness Review
- Wave 1 Deployment
- Trust Spine redesign
- Deploy-readiness redesign
- New persistence / replay system
- New canonical event model design
- Notification engine redesign

### Could Phase B be completed using the Smallest Safe Repair principle?

- **Yes, if and only if it stays bounded to the existing route, its current direct frontend consumers, and focused verification of the current aggregate contract.**

---

## Discovery Verdict

OCC Trust Events is **Present** and constitutionally classifies as an **AGGREGATOR**.

It is already active in runtime, but it is **not constitutionally complete**:

- no canonical owner registration
- no canonical truth subject binding
- no canonical owner route
- no explicit claim ceiling
- no unified event identity at the feed layer
- no contradiction / dedup / replay model at the feed layer

The repository supports a future **bounded Phase B hardening track**, but discovery does **not** support redesign, platform-wide event architecture expansion, or adjacent family work.

Stop here and wait for explicit authorization before any implementation.