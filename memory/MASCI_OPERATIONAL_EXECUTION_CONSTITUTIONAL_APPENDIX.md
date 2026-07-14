# MASCI Operational Execution Constitutional Appendix

## 1. Appendix Authority

This appendix is a mandatory part of the MASCI Operational Execution constitutional set.

It exists because the five core artifacts require normative catalogs to eliminate the remaining ambiguity around:
- explicit state machines
- cross-module event authority
- dashboard and executive reporting authority
- KPI authority
- notification authority
- offline, synchronization, caching, and concurrency authority

This appendix does not weaken the core artifacts.
It makes them executable as governance.

## 2. Canonical Lifecycle Catalog

### 2.1 Operational Work Lifecycle
- **States:** draft, ready, committed, in_execution, blocked, completed, cancelled, archived
- **Allowed transitions:**
  - draft → ready
  - ready → committed
  - ready → cancelled
  - committed → in_execution
  - committed → blocked
  - committed → cancelled
  - blocked → committed
  - blocked → cancelled
  - in_execution → completed
  - in_execution → blocked
  - completed → archived
  - cancelled → archived
- **Invalid transitions:** direct draft → completed, cancelled → committed, completed → draft
- **Rollback / correction rule:** readiness/commit corrections require auditable lifecycle mutation; completed/cancelled facts cannot be silently erased
- **Terminal states:** archived

### 2.2 Rolling Schedule Lifecycle
- **States:** working, reviewed, committed, published, superseded, cancelled
- **Allowed transitions:**
  - working → reviewed
  - reviewed → committed
  - committed → published
  - published → superseded
  - working/reviewed/committed → cancelled
- **Invalid transitions:** superseded → published, cancelled → committed without explicit re-creation/versioning
- **Rollback / correction rule:** schedule corrections require new version or governed state change; prior publication must remain historically visible
- **Terminal states:** superseded, cancelled

### 2.3 Daily Report Lifecycle
- **States:** local_draft, server_draft, submitted, corrected, approved, superseded
- **Allowed transitions:**
  - local_draft → server_draft
  - server_draft → submitted
  - submitted → corrected
  - submitted → approved where approval model exists
  - corrected → submitted
  - approved → superseded only through governed correction/publication rules
- **Invalid transitions:** local_draft → approved, superseded → submitted without governed copy/version path
- **Rollback / correction rule:** field truth must be preserved through version history; local continuity artifacts remain non-canonical until synchronized
- **Terminal states:** superseded only for superseded versions; latest approved/submitted version remains live source truth

### 2.4 Weekly Reconciliation Lifecycle
- **States:** draft, running, under_review, published, reopened, superseded, cancelled
- **Allowed transitions:**
  - draft → running
  - running → under_review
  - under_review → published
  - published → reopened
  - reopened → under_review
  - published → superseded
  - draft/running/under_review → cancelled
- **Invalid transitions:** cancelled → published, superseded → reopened without governed successor record
- **Rollback / correction rule:** any correction after publication must preserve prior published version
- **Terminal states:** superseded, cancelled

### 2.5 Daily Company Operations Brief Lifecycle
- **States:** draft, under_review, published, withdrawn, superseded
- **Allowed transitions:**
  - draft → under_review
  - under_review → published
  - published → withdrawn
  - published → superseded
- **Invalid transitions:** withdrawn → published without governed new version, superseded → published
- **Rollback / correction rule:** published brief corrections require successor version or governed withdrawal
- **Terminal states:** withdrawn, superseded

### 2.6 Dispatch Assignment Lifecycle
- **States:** created, assigned, en_route, on_site, completed, cancelled
- **Allowed transitions:** created → assigned → en_route → on_site → completed, with governed cancellation paths before completion
- **Invalid transitions:** completed → assigned, cancelled → en_route
- **Rollback / correction rule:** historical dispatch movement remains auditable
- **Terminal states:** completed, cancelled

### 2.7 PM Work Order Lifecycle
- **States:** draft, scheduled, active, completed, cancelled, archived
- **Allowed transitions:** draft → scheduled → active → completed → archived; draft/scheduled/active → cancelled
- **Invalid transitions:** cancelled → active without governed recreation, archived → active
- **Rollback / correction rule:** maintenance history must remain visible
- **Terminal states:** archived, cancelled

### 2.8 Notification Lifecycle
- **States:** eligible, queued, sent, failed, suppressed, expired
- **Allowed transitions:** eligible → queued → sent or failed or suppressed; queued/failed → expired by policy
- **Invalid transitions:** sent → queued without new source trigger, suppressed → sent without new eligibility event
- **Rollback / correction rule:** delivery retries preserve source trigger lineage; notifications do not mutate source truth
- **Terminal states:** sent, suppressed, expired

### 2.9 Projection / Background Job Lifecycle
- **States:** pending, running, succeeded, failed, stale, superseded
- **Allowed transitions:** pending → running → succeeded/failed; succeeded → stale/superseded; failed → pending only by governed retry rule
- **Invalid transitions:** stale → running without explicit re-queue, superseded → succeeded
- **Rollback / correction rule:** retries preserve prior failure evidence
- **Terminal states:** superseded

## 3. Canonical Cross-Module Event Map

### 3.1 Daily Report Submission Chain
Daily Report submitted
→ Daily Report source record finalized for that version
→ actual production projection refresh eligible
→ Trust Spine daily-report stage emitted
→ schedule actuals comparison eligible
→ reconciliation refresh/run eligible
→ executive brief inputs refreshed
→ dashboard refresh / stale invalidation triggered
→ governed notifications eligible

### 3.2 Schedule Publication Chain
Schedule publication committed
→ schedule publication version created
→ Trust Spine schedule-publication stage emitted
→ Daily Execution expectation views refreshed
→ reconciliation baseline refreshed
→ executive brief commitment inputs refreshed
→ schedule alerts/notifications eligible

### 3.3 Reconciliation Publication Chain
Reconciliation published
→ reconciliation publication version created
→ Trust Spine reconciliation-publication stage emitted
→ variance / recovery dashboards refreshed
→ executive brief variance inputs refreshed
→ governed escalation notifications eligible

### 3.4 Executive Brief Publication Chain
Executive brief published
→ publication version created
→ Trust Spine brief-publication stage emitted
→ executive dashboard publication surfaces refreshed
→ governed executive notifications/delivery eligible

### 3.5 Dispatch / PM / Safety / QA-QC Supporting Event Rule
Supporting domain events may update schedule readiness, reconciliation evidence, brief sections, and dashboards only through explicit declared event contracts.
No implied propagation is permitted.

## 4. Dashboard and Executive Reporting Authority Catalog

### 4.1 Dashboard Authority Rule
Every dashboard card or table must be classified as one of:
- source-backed operational view
- derived KPI view
- projection freshness / health view
- publication status view
- executive summary view

### 4.2 Dashboard Authority by Concept
- project dashboards → authority from project, staffing, and declared projections
- work dashboards → authority from Operational Work and declared projections
- schedule dashboards → authority from schedule publication versions
- daily execution dashboards → authority from Daily Reports and declared derived projections
- reconciliation dashboards → authority from reconciliation publications
- executive dashboards → authority from published brief + approved KPI definitions + declared supporting projections

### 4.3 Executive Reporting Rule
Executive reporting is a governed read/publication layer built from:
- verified source facts
- defined KPIs
- governed derived projections
- clearly separated AI narrative

Executive reporting may not invent new definitions, new truth, or new ownership.

## 5. KPI Authority Catalog

### 5.1 KPI Classes
The KPI registry must classify metrics into:
- source-direct counts
- derived operational performance KPIs
- derived quality/safety KPIs
- executive rollup KPIs

### 5.2 Mandatory Authority for Core KPI Families
- labor hours → Daily Report source facts unless another governed source explicitly owns the fact
- production quantities → Daily Report source facts and/or actual production projection formulas
- schedule adherence → schedule publication + reconciliation formulas
- constraint rate → reconciliation/safety/governed constraint formulas
- dispatch efficiency → dispatch authority formulas
- fleet uptime / equipment utilization → equipment and PM authority formulas
- QA/QC rates → QA/QC authority formulas
- incident rate → safety authority formulas

### 5.3 KPI Non-Duplication Rule
If multiple dashboards show the same KPI family, they must reference the same formula authority.

## 6. Notification Authority Catalog

### 6.1 Notification Trigger Classes
Notifications may be triggered only by:
- source lifecycle changes
- publication lifecycle changes
- reconciliation or exception lifecycle changes
- governed reminder/escalation policies

### 6.2 Notification Non-Authority Rule
Notifications are downstream delivery artifacts.
They do not create, publish, reconcile, approve, certify, or redefine operational truth.

### 6.3 Notification Deduplication Rule
Every notification class must define:
- dedupe key
- suppression rule
- retry rule
- expiry rule

## 7. Offline, Synchronization, and Continuity Authority Catalog

### 7.1 Local Continuity Rule
Local continuity artifacts are permitted for interruption-sensitive field workflows only.
They are convenience/recovery layers, not enterprise source truth.

### 7.2 Pending Synchronization Rule
Pending synchronized state must be visibly distinguishable from canonical server-accepted state.

### 7.3 Reconnect Conflict Rule
If local and server state diverge, the workflow must define whether it:
- rejects stale local mutation
- merges through governed conflict logic
- requires explicit user resolution

### 7.4 Replay Rule
Replayed submissions after reconnect must be idempotent or safely conflict-checked.

## 8. Concurrency and Cache Authority Catalog

### 8.1 Concurrency Rule
Every mutable source or publication workflow must define collision behavior for:
- simultaneous edits
- simultaneous approvals
- simultaneous publications
- worker and user mutation overlap

### 8.2 Cache Rule
Every cached surface must define:
- canonical upstream source
- freshness indicator
- invalidation trigger
- stale-display rule
- failure fallback rule

### 8.3 Mixed-Truth Prohibition
No cached or partially refreshed surface may appear fresher or more authoritative than its source proof allows.

## 9. Appendix Cross-Reference Map

This appendix is normatively referenced by:
- Constitution §15.4, §19.3, §22.14, §27
- Register Track 1 and all tracks with event, dashboard, notification, offline, sync, concurrency, and cache impact
- Role Matrix §14
- Certification Plan §35