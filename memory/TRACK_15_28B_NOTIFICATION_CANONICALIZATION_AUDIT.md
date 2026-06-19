# TRACK 15.28B — NOTIFICATION SYSTEM CANONICALIZATION AUDIT

**Mode:** READ-ONLY · NO CODE · NO MIGRATION · NO BACKFILL · NO DEPLOY
**Date:** 2026-02 (Track 15.28B)
**Database:** `masci_safety_preview` (preview cluster — production schema mirror)
**Snapshot:** `db.notifications` = **9,742 documents** (oldest 2026-05-15, newest 2026-06-19)
**Companion collections:** `db.tasks_notifications` (162), `db.alert_events` (1), `db.digest_runs` (9), `db.digest_settings` (1), `db.trench_safety_leadership_digests` (9)

---

## EXECUTIVE FINDING (one line)

> **The MASCI notification system cannot be trusted as of this audit.** Four schemas coexist across three collections, the read path of the production bell silently excludes 552 legacy rows that were intended to be seen, role-broadcast notifications outnumber person-targeted ones 45:1, and zero of 9,742 notifications have ever been acknowledged. The original Track 15.8A / 15.8B PM complaints are explainable and reproducible — see Q9.

**Five-Pillar Score (preliminary, evidence-based):**

| Pillar | Score | Evidence |
|---|---|---|
| Powerful | 4 / 10 | 42 distinct event types fan out, but no idempotency, no de-dupe, no ack workflow used. |
| Simple | 2 / 10 | 4 schemas, 3 collections, 6 write helpers, 5 read endpoints. |
| Beautiful | 6 / 10 | Bell UI is clean; backend is dirty. |
| Trusted | 2 / 10 | 552 legacy rows invisible to bell. 8,979 rows have NULL recipient_user_id but a `recipient_role`-only broadcast. Same event fires up to 49× per asset (TB-03). |
| Proven | 1 / 10 | 0 of 9,742 notifications ever acknowledged. Only 15.4 % have any read marker. No production trace exists for whether a PM ever opened a bell item. |

---

## Q1 — NOTIFICATION CREATION PATHS (every file, route, helper, cron)

### A. Canonical writer (TYPE schema → `db.notifications`)

| File | Function | Used by |
|---|---|---|
| `backend/routes/tasks_notifications.py:307` | `_NotificationService.fanout(db, payload)` | `notification_service` singleton |
| `backend/routes/tasks_notifications.py:203` | `_TaskService.create()` — auto-emits a `task.assigned` for every task created | every task producer |
| `backend/lib/event_fanout.py:61` | `emit_notification(db, payload)` — thin wrapper around `fanout()` | 14+ producer modules |
| `backend/lib/event_fanout.py:28` | `emit_task_and_notification(db, task=, notification=)` — emits task + optional separate notification | task producers |

### B. Producers that call `emit_notification` (canonical writers)

All paths below ultimately call `notification_service.fanout()` and insert into `db.notifications`.

| Module | Line | Type emitted |
|---|---|---|
| `backend/routes/daily_report_lifecycle.py:144` | `daily_report.pending_review` |
| `backend/routes/payroll_variance.py:340` | `payroll_variance.manual_run` |
| `backend/routes/fuel_lube.py:247` | `fuel_lube.issue_reported` + `fuel_lube.issue_reported.dispatch` |
| `backend/routes/asset_transfers.py:202,239,252,263,273` | `asset_transfer.requested|approved|in_transit|dispatch_pickup|received` |
| `backend/routes/equipment.py:265,326` | `preop.failed`, `dvir.defect`, `dvir.defect.oos` |
| `backend/routes/safety_forms.py:1199` | `safety_form.issuance.submitted`, `safety_form.training.submitted` |
| `backend/routes/trench_safety/excavations.py:535,661,884,994` | 9 distinct `trench_safety.*` types |
| `backend/routes/trench_safety/notifications.py:_fanout` | central trench-safety router (8 routing keys, role matrix) |
| `backend/routes/trench_safety/pulse.py` | trench-safety digest fanout |
| `backend/routes/fleet_ops.py:734,1737` | `dvir.*` and `fleet.defect.*` |
| `backend/routes/safety.py:462,854` | `incident.created`, `inspection.*` |
| `backend/routes/qaqc.py:275` | `qaqc.deficiency` |
| `backend/routes/jha_acknowledgements.py` | `jha.submitted` |
| `backend/routes/document_expirations.py` | `asset_doc.expired`, `document.expired`, `document.expiring` |
| `backend/routes/field_leadership.py` | `fl.submitted`, `meeting.submitted` |
| `backend/routes/po_requests.py` | `po.approval_visibility`, `po.receipt_received` |
| `backend/routes/dispatch_lifecycle.py:743` (`_fire_assignment_notification`) | `shop_assignment.*` |
| `backend/routes/project_team_assignments.py:327` (`_notify_assignment`) | `project_team_assignment` |
| `backend/routes/notify_ownership_lock_seed.py:78` | direct `db.notifications.insert_one` — test/seed |

### C. Legacy writers (KIND schema → `db.notifications`)

| File | Function | Schema written |
|---|---|---|
| `backend/routes/employee_requests.py:150` (`_notify_hr_queue_pending`) | One row PER HR user via `insert_many`. Fields: `kind=hr.employee_request`, `user_id`, `user_email`, `audience=hr`, `read`, `ts`, `url`, `link_url`, `linked_request_id`, `request_kind`. **No `type`, no `recipient_role`, no `recipient_user_id`.** | LEGACY |
| `backend/routes/operations_actions/api.py:262` (`_notify_assignment`) | Writes `kind=oa_assignment`, `user_directory`, `user_id`, `user_email`, `ref_kind`, `ref_id`, `ref_url`, `body`. **No `type`, no `recipient_role`.** | LEGACY |

### D. Yet-other writers (separate collections — invisible to bell)

| File | Collection | Schema |
|---|---|---|
| `backend/routes/pm_engine.py:422` (`_notify`) | `db.tasks_notifications` (162 rows) | `kind`, `audience_role`, `audience_id`, `unit_number`, `pm_name`, `summary` |
| `backend/phase4.py:87` (`notify_user`) | `db.notifications` (BUT older crew-hub schema: `user_id`, `kind`, `project_id`, `actor_id`, `target_kind`, `target_id`, `target_label`, `preview`, `read_at`). **Currently produces 0 rows** in this snapshot — endpoint exists, frontend no longer calls it. | DORMANT LEGACY |

### E. Cron / automation producers

| Trigger | Mechanism |
|---|---|
| `backend/lib/scheduler_runs.py` + `singleton_scheduler.py` | Calls scheduled producers in `routes/scheduled_producers_d456.py` which emit `document.expiring`, `asset_doc.expires_30d`, `cert_due_soon_*`, etc. via `emit_notification`. |
| `backend/lib/operator_digest.py` | Generates digest payloads only (no `db.notifications` writes — reads from `db.compliance_findings`). |
| Trench safety pulse (`routes/trench_safety/pulse.py`) | Periodic asset health emits. |

### F. Backfill / migration scripts (one-shot, not live)

| File | Purpose |
|---|---|
| `backend/scripts/track_15_2_backfill_leaked_pm_offboarding.py` | Backfill helper that writes and updates notifications for PM offboarding. **Not on the runtime path.** |

### Total live write call-sites: **~30 across 17 files. 4 distinct on-the-wire shapes. 3 collections.**

---

## Q2 — SOURCE OF TRUTH

| Schema | Storage | Rows | Field discriminator | Read by |
|---|---|---|---|---|
| **CANONICAL (current)** | `db.notifications` | **9,190 (94.3 %)** | has `type`, `recipient_role`, `recipient_user_id` (often null), `severity`, `read_by[]`, `acknowledged_at`, `expires_at`, `delivery{}`, `linked_*` keys | `/api/notifications` (bell), `/api/field-leadership/portal/notifications-recent` (FL), `/api/global-search`, `/api/ownership-lifecycle` |
| **LEGACY HR (kind)** | `db.notifications` | **522 (5.4 %)** | `kind=hr.employee_request`, `user_id`, `user_email`, `audience=hr`, `read`, `ts`, `url` | none on the bell · `/api/me/notifications` legacy route (dormant) |
| **LEGACY OA (kind)** | `db.notifications` | **30 (0.3 %)** | `kind=oa_assignment`, `user_directory`, `ref_*`, `body` | none on the bell |
| **PM ENGINE (kind)** | `db.tasks_notifications` | 162 | `kind`, `audience_role`, `audience_id`, `unit_number`, `pm_name`, `summary` | none — produces only |
| **CREW HUB (legacy crew)** | `db.notifications` | 0 in this snapshot | `user_id`, `kind`, `project_id`, `read_at` | `/api/me/notifications` (orphan endpoint) |

**Conclusion — Q2:**
> The **canonical schema is `type` + `recipient_role` (+ optional `recipient_user_id`)**, stored in `db.notifications`. It is the source of truth for the **read** path (the production NotificationBell only queries this shape). The legacy 552 rows in the same collection are **dual-write residue** — they were inserted by `employee_requests._notify_hr_queue_pending()` and `operations_actions._notify_assignment()` but **are not delivered by the bell**, only by the dormant `/api/me/notifications` endpoint. PM-engine writes to a separate collection (`tasks_notifications`) that has **no live reader**.

**Proof (read path):**
- `backend/routes/tasks_notifications.py:563` (`build_notif_filter`) — builds the filter from `recipient_role` + `recipient_user_id` only.
- `backend/routes/tasks_notifications.py:789` (`list_notifications`) — uses that filter.
- `frontend/src/lib/tasksApi.js:51` calls `GET /api/notifications`.
- `frontend/src/components/NotificationBell.jsx` renders `n.type`, `n.severity`, `n.link_url`, `n.read_by`. Legacy fields are never referenced.

**Simulated HR user (`hrmanager@mascigc.com`, id `152a7be6-…`):**
- 9 legacy rows target this user by `user_id` / `user_email`.
- Canonical bell filter returns **0 of those 9** — the legacy rows have no `recipient_role` and no `recipient_user_id`.
- HR user sees **662 canonical rows** (role-broadcast `recipient_role=hr` of which 100 % have `recipient_user_id=null`).

⇒ **552 legacy notifications exist in `db.notifications` that the bell will never deliver.**

---

## Q3 — CAN A SINGLE EVENT GENERATE DUPLICATE NOTIFICATIONS?

**YES. Three independent duplication mechanisms exist.**

### Mechanism 1 — Role fan-out (by design)
Every trench-safety event resolves to N rows where N = `len(ROUTING_MATRIX[type].roles)`. Example `trench_safety.asset_returned_to_service` → 3 rows (safety + shop + dispatch). HR fan-out writes 1 row **per HR user** (58 HR users in `hr_users` ⇒ 58 rows per request).

### Mechanism 2 — Producer fires more than once for the same source record (no idempotency)
`db.notifications` has **no `event_id` or `idempotency_key`**. Field presence: `event_id = 0 / 9742`, `source = 0 / 9742`, `origin = 0 / 9742`.

**Evidence — `trench_safety.asset_returned_to_service` for asset `TB-03`:**
```
{type, linked_source_record_id="TB-03"}   → 147 documents
   147 / 3 roles = 49 firings of the producer
   All 147 timestamps within 18-second windows on 2026-06-07
   recipient_role=safety alone: 49 identical rows
```

`backend/routes/trench_safety/_helpers.py:188-193` invokes `notify_asset_returned_to_service()` every time `clear_hold()` runs while no active holds remain. There is no de-dupe on (asset_id, "returned_to_service") within a window. The same physical asset coming back to service N times produces N × 3 bell rows.

### Mechanism 3 — Person-targeted producer fires multiple times
Sample: `qaqc.deficiency` for the same Phase2B inspection notified the **same `recipient_user_id` (`a558ca8d-…`)** 5 consecutive times with the identical title.

Top duplicate sets (by `type` + `linked_source_record_id`):
```
trench_safety.asset_returned_to_service · TB-03 : 147
trench_safety.asset_returned_to_service · TB-05 : 132
trench_safety.asset_returned_to_service · TB-04 : 129
trench_safety.asset_returned_to_service · TB-06 : 123
trench_safety.asset_returned_to_service · TB-02 : 105
trench_safety.asset_returned_to_service · TB-07 :  81
trench_safety.asset_returned_to_service · TB-01 :  63
task.assigned                            · ...c9d7ebc3 :  16
daily_report.pending_review              ·  7 distinct records ×  9 dupes
```

> **Verdict: duplicates are not just possible — they are pervasive and silent.**

---

## Q4 — CAN ONE USER RECEIVE NOTIFICATIONS THROUGH BOTH SCHEMAS?

**YES — for HR users only, via the dormant `/api/me/notifications` legacy endpoint.**

- Bell endpoint (`/api/notifications`) — delivers canonical rows where `recipient_role=hr` OR `recipient_user_id=<user>`.
- Legacy `/api/me/notifications` (`backend/phase4.py:243`) — filters by `{user_id: <user>}`. Returns the 552 legacy hr.employee_request rows for any HR user whose `users.id` matches the legacy `user_id`.

In practice the frontend no longer calls `/api/me/notifications`, so the dual delivery is **architecturally possible but currently unwired** in the UI. If any client (mobile shell, API client, or restored crew-hub page) hits that endpoint, the user gets a parallel feed.

**Admin actor:** admin sees `{}` filter ⇒ both schemas land in the same bell list (mixed `type` + `kind` rows). Admin users can confirm this in the bell drawer today — rows missing `n.type` are the legacy 552.

---

## Q5 — CAN NOTIFICATIONS BE CREATED THAT NO USER CAN EVER SEE?

**YES. Three classes.**

### Class A — legacy schema invisible to bell (522 + 30 = **552 rows**)

| Source | Where stored | Why invisible | Count |
|---|---|---|---|
| `employee_requests._notify_hr_queue_pending` | `db.notifications` | No `recipient_role`; bell filter rejects | 522 |
| `operations_actions._notify_assignment` | `db.notifications` | No `recipient_role`; bell filter rejects | 30 |

These are visible to **admin only** (admin filter is `{}`). To any HR/PM/Shop/Dispatch/Safety/Leadership/FL user they are unreachable through the bell.

### Class B — `db.tasks_notifications` rows (162 rows)
Written by `pm_engine._notify` (`pm_assigned`, `pm_started`, etc.). **No reader exists** in `backend/` or `frontend/`. They are write-only.

### Class C — notifications with `recipient_role` set but no users in that role
- `recipient_role=fl` → 2 rows. The `field_leadership_users` collection (31 users) **does** populate role=`field_leadership` (not `fl`) in some paths. There is intentional aliasing in `actor_role()`, but if a producer sets `recipient_role="fl"` and the actor token canonicalizes to `field_leadership`, the scope filter `{"recipient_role": {"$in": ["fl"]}}` will match — verified safe today. Listed for completeness, not a deliverability problem in this snapshot.

> **Confirmed dead rows: 552 + 162 = 714 documents (7.3 % of the universe) that no operator can see in the bell.**

---

## Q6 — CAN NOTIFICATIONS BE DELIVERED TO THE WRONG RECIPIENT?

**YES — three pathways.**

### P1 — Stale role-broadcast bleed (the Track 15.8A/15.8B complaint)
- **8,979 of 9,190 canonical rows (97.7 %) have `recipient_user_id=null`.** Routing is **purely by `recipient_role`.**
- Distribution of broadcast vs targeted:

| recipient_role | targeted (string user_id) | broadcast (null) |
|---|---|---|
| safety | 129 | **3,821** |
| pm | 63 | **1,639** |
| shop | 17 | **1,228** |
| dispatch | 0 | **1,096** |
| hr | 0 | **662** |
| (null — legacy) | 0 | **552** |
| admin | 0 | 399 |
| leadership | 0 | 87 |
| superintendent | 0 | 25 |
| asset_admin | 0 | 22 |
| fl | 2 | 0 |

- Every PM in the directory therefore sees every other PM's role-broadcast (and historical broadcasts going back to 2026-05-15 unless `actor_eligibility(actor)` filters them out by join date).
- `actor_eligibility` (`tasks_notifications.py:533`) clips by user join-date, but **all PMs share every broadcast newer than their join date** regardless of which project the notification pertains to. A PM joined on day-0 sees all 1,639 PM rows.

### P2 — Eligibility cutoff bypassed for direct addressing
Any row with `recipient_user_id = <user_id>` bypasses the eligibility cutoff (`build_notif_filter` lines 596-597). If a producer sets `recipient_user_id` to a stale UUID (re-used after an account merge), the new owner of that UUID inherits old notifications. The orphan analysis (Q7) shows 7 of 13 distinct non-null `recipient_user_id` values do not resolve in the live user collections — those rows are pinned to ghost users.

### P3 — Asset Admin OR-expansion
`build_notif_filter` (lines 581-583) appends `asset_admin` to the scope when `actor.is_asset_admin=True`. This is set in localStorage as `masci.is_asset_admin`. The Shop-Portal user-record `is_asset_admin` flag is consulted, but the flag has no server-side re-check on every request beyond token issuance. If `is_asset_admin` is set then later revoked, the local hint persists until next login and the user keeps seeing `asset_admin` notifications until the token refreshes.

### P4 — PM-engine wrong-collection writes
`pm_engine._notify(audience_role="mechanic", audience_id="<uuid>")` writes to `db.tasks_notifications`. No reader picks this up, so the mechanic **never gets the notification**. From the operator's perspective: silent under-delivery.

---

## Q7 — ORPHAN ANALYSIS (missing user / project / role / routing data)

### Cross-collection user-ID index (1,213 unique known IDs across `users`, `dispatch_users`, `employees`, `safety_users`, `hr_users`, `field_leadership_users`, `user_directory`, `shop_users`, `project_managers`, `project_team_assignments`, `suppliers`)

**Recipient_user_id orphans:** 7 of 13 distinct non-null values.

| `recipient_user_id` | Rows | Found in directory? |
|---|---|---|
| `b3d7f5a8-4dc2-42a0-a05d-331e3558dc54` | 138 | KNOWN |
| `a92c7165-7900-4b6a-a602-e82b2059fe90` | 35 | KNOWN |
| `a558ca8d-85ab-48aa-b8dc-1de0e4c20dac` | 15 | KNOWN |
| `bbbd6be6-ddba-461a-93e2-f205abe9a7f7` | 10 | KNOWN |
| `e1bb32ae-…` | 4 | KNOWN |
| `91f90906-…` | 2 | KNOWN |
| `itest-mech-{cda9ab4a,c3136cc3,b3bd3831,a6c520dd,756c235d,48f57703,bad2301c}` | 1 each | **ORPHAN** — pytest fixtures |

→ **Real-user orphan rate is 0.** The 7 orphans are integration-test residue (`itest-mech-*`). Safe to ignore as production noise but should be cleaned.

**Legacy `user_email` orphans:** 0 of 58 — every legacy email still resolves to a live user record.

### Missing routing data

| Condition | Count |
|---|---|
| `recipient_role` missing | 552 (all legacy) |
| `recipient_user_id` missing AND `user_email` missing | 8,979 |
| `recipient_role` set AND `recipient_user_id` null (intentional broadcast) | 8,979 |
| `linked_project_number` set | 2,434 of 9,742 (25 %) |
| `linked_project_number` null on non-trench non-shop types | majority |
| `link_url` resolvable | 9,742 (100 %) — see note |

> `link_url` is populated for every row, but for legacy rows it points to `/hr/employee-requests?id=<rid>` (valid) and for OA rows to `/operations-actions/<id>` (valid). For canonical rows, `_resolve_link_url` returns a route or `null`. There is no enforcement that the route exists at runtime.

### Read / Ack / Expire posture

| Posture | Rows | Note |
|---|---|---|
| `acknowledged_at` set | **0 of 9,742** | Nobody has ever acknowledged a notification in this DB. |
| `read_by` non-empty | 1,499 (15.4 %) | Read coverage is poor. |
| `expires_at` set | 9,190 (94.3 %) | TTL active on canonical schema only — legacy 552 will never expire. |
| Legacy `read=false` | 552 | All legacy rows are still "unread" but invisible. |

---

## Q8 — PER-PORTAL NOTIFICATION SURFACES

| Portal | Source(s) feeding it | Destination filter | Schema relied upon | Display location |
|---|---|---|---|---|
| **Admin** | Every producer that calls `emit_notification` + the two legacy producers | `{}` (no filter — admin sees everything) | both | `NotificationBell` header drawer on every admin route |
| **PM** | task.assigned, incident.created, asset_transfer.*, qaqc.deficiency, daily_report.pending_review, inspection.deficiency, po.receipt_received, project_team_assignment | `recipient_role=pm OR recipient_user_id=<pm.id>` AND created_at ≥ pm.created_at | canonical only | `NotificationBell` header drawer (PM portal shell) |
| **HR** | Canonical: incident.created, document.expired/expiring, payroll_variance.manual_run, hr.* (via task.assigned). **Legacy**: hr.employee_request (522 rows, **invisible**). | `recipient_role=hr` AND created_at ≥ hr_user.created_at | canonical only (legacy invisible) | `NotificationBell` header drawer |
| **Safety** | incident.created, qaqc.deficiency, jha.submitted, safety_form.*, trench_safety.* | `recipient_role=safety` AND created_at ≥ safety_user.created_at | canonical only | `NotificationBell` + Safety-portal route overrides (`/safety-portal/incidents/...`) |
| **Dispatch** | asset_transfer.*, fuel_lube.issue_reported.dispatch, dvir.defect.oos, trench_safety.* (when listed) | `recipient_role=dispatch` AND eligibility | canonical only | `NotificationBell` drawer in dispatch portal shell |
| **Shop** | asset_transfer.*, shop_assignment.*, document.expiring, trench_safety.cert_expired, asset_doc.expires_* | `recipient_role=shop` (+ `asset_admin` if `is_asset_admin=true`) | canonical only | `NotificationBell` drawer (Shop portal) |
| **Field Leadership (FL)** | fl.submitted, meeting.submitted + a read-only mirror of `pm` + `safety` | (1) `NotificationBell`: `recipient_role IN ["fl","field_leadership"]`. (2) Extra: `/api/field-leadership/portal/notifications-recent` returns `recipient_role IN ["fl","safety","pm"]` | canonical only | `NotificationBell` + dedicated FL panel |
| **Asset Admin** | document expiration, classification review, asset_doc.* | OR-extension of Shop scope when `is_asset_admin=true` | canonical only | `NotificationBell` drawer with `X-Asset-Admin: 1` header |
| **Superintendent** | none directly today (3 rows total; producers do not address `superintendent` consistently) | `recipient_role=superintendent` if actor token resolves to that role | canonical only | None observed — token typically resolves to `pm` or `field_leadership` |
| **Operations Actions (OA)** | `operations_actions._notify_assignment` writes 30 LEGACY rows | LEGACY shape — invisible to bell | legacy | Nowhere — assigned OA owners do not see them in the bell |

**Hot finding from this table:**
- The **PM Portal sees 1,639 broadcast rows + 63 targeted rows = 1,702 PM-routable notifications**, of which 0 have been acknowledged and only a fraction read. This matches the operator complaint that PMs are "drowning in irrelevant bell items".

---

## Q9 — TRACK 15.8A / 15.8B PM NOTIFICATION COMPLAINT

The original complaint (paraphrased from the handoff and the project_team_assignment / pm_offboarding sprint): "*PMs are receiving notifications about projects they are not assigned to and notifications about events that happened before they joined; PMs cannot tell why a given notification is showing up*."

### Is it now explainable? **YES, with high confidence.**

### Root causes (evidence above):

1. **Role-broadcast routing dominates.** 97.7 % of PM notifications have `recipient_user_id=null`. Every PM sees every other PM's notifications scoped only by `recipient_role=pm` and the eligibility cutoff `created_at ≥ pm.created_at`.

2. **Eligibility cutoff is a join-date filter, not a project-membership filter.** A PM who joined on 2026-05-01 sees 100 % of pm-role notifications produced after that date, including notifications about projects they are **not** a member of.

3. **No project-scope check on the read side.** `build_notif_filter` never consults `db.project_managers`, `db.project_team_assignments`, or the row's `linked_project_number`. A PM's bell is **company-wide PM bell**, not project-scoped.

4. **Producer duplication.** Asset-returned events fire repeatedly (49× for TB-03), creating multiple identical rows. While these are routed to safety/shop/dispatch (not PM), the same duplication pattern exists for `task.assigned`, `qaqc.deficiency`, and `daily_report.pending_review` rows that DO land in the PM bell (see Q3 evidence).

5. **PM-targeted notifications written to the wrong collection.** `pm_engine._notify(audience_role="mechanic", ...)` writes to `db.tasks_notifications` (no reader). Conversely, the assignee_user_id propagated by `task_service.create` (line 214) populates `recipient_user_id` only when the producer remembered to pass `assignee_user_id`. Inspecting the 599 `task.assigned` rows targeted at `recipient_role=pm`, **0 had a string `recipient_user_id`** — every PM-task was broadcast.

6. **PM-engine writes to `db.tasks_notifications` and `notify` writes to `db.notifications`** — same wording, two collections, different readers. Operators cannot reconcile what they saw vs what was logged.

7. **No idempotency, no source-event-id.** When a workflow retries (e.g., dispatch lifecycle ack), the same notification can be produced again with no de-dupe.

### Is it reproducible? **YES.**
Reproduction recipe (READ-ONLY — verified via the DB, not executed):
1. Sign in as any PM whose `created_at < 2026-06-01`.
2. Open the bell.
3. Observe 1,000+ items, most of which reference projects outside the PM's assignment list (any project that triggered a `task.assigned`, `incident.created`, `qaqc.deficiency`, `daily_report.pending_review`, or `asset_transfer.*` notification produced after the PM's join date).
4. Confirm: `recipient_user_id` is null on virtually all of them. `linked_project_number` is set on a minority (25 % across all rows; for PMs the bell has no project filter regardless).

### Why was Track 15.8B's earlier fix insufficient?
Track 15.8B added the **eligibility cutoff** (`actor_eligibility`) to suppress pre-join-date noise. That correctly filters by **time**, but the missing leg is **project membership**. The cutoff also does not de-duplicate or constrain producers that fire repeatedly.

---

## Q9-Adjacent — TRUST CHECKLIST

| Question | Answer | Evidence |
|---|---|---|
| Can every notification in the DB be explained (producer, recipient, project)? | **NO** for the 552 legacy + 162 `tasks_notifications` rows. **PARTIAL** for the 8,979 broadcast rows — recipient is "everyone in the role", which is not an explanation, it is a default. | This audit |
| Can every notification be traced from event → producer → row → reader? | **NO.** No `event_id` field; no `source_module` on most rows (only `linked_source_module`); duplicate firings have identical content. | Q3 |
| Has the system ever been acknowledged-end-to-end? | **NO.** 0 of 9,742 rows have `acknowledged_at` set. | Q7 |

---

## ARCHITECTURE MAP (text diagram)

```
                                      PRODUCERS (30+ call-sites)
                                                ▼
   ┌────────────────────────────────────────────────────────────────────┐
   │ CANONICAL PATH                                                      │
   │  emit_notification(payload)  →  _NotificationService.fanout(db, p)  │
   │  emit_task_and_notification(...) → task_service.create + fanout     │
   │  Writes: db.notifications  (type/recipient_role/recipient_user_id)  │
   └────────────────────────────────────────────────────────────────────┘
                                                ▼
   ┌────────────────────────────────────────────────────────────────────┐
   │ LEGACY-HR PATH                                                      │
   │  employee_requests._notify_hr_queue_pending()                       │
   │  Writes: db.notifications  (kind/user_id/user_email/audience)       │
   │   ⇒ INVISIBLE to /api/notifications bell                            │
   └────────────────────────────────────────────────────────────────────┘
                                                ▼
   ┌────────────────────────────────────────────────────────────────────┐
   │ LEGACY-OA PATH                                                      │
   │  operations_actions._notify_assignment()                            │
   │  Writes: db.notifications  (kind/user_directory/user_id/user_email) │
   │   ⇒ INVISIBLE to /api/notifications bell                            │
   └────────────────────────────────────────────────────────────────────┘
                                                ▼
   ┌────────────────────────────────────────────────────────────────────┐
   │ PM-ENGINE PATH                                                      │
   │  pm_engine._notify(...)                                             │
   │  Writes: db.tasks_notifications  (kind/audience_role/audience_id)   │
   │   ⇒ NO READER ANYWHERE                                              │
   └────────────────────────────────────────────────────────────────────┘
                                                ▼
   ┌────────────────────────────────────────────────────────────────────┐
   │ DORMANT-CREW PATH (phase4.notify_user)                              │
   │  Writes: db.notifications  (user_id/project_id/kind/read_at)        │
   │  Reader: GET /api/me/notifications  ← bell does NOT call this       │
   │  Current rows produced: 0 in snapshot                               │
   └────────────────────────────────────────────────────────────────────┘

                                READERS
   ─────────────────────────────────────────────────────────────────
   1. /api/notifications                       (canonical bell)
   2. /api/notifications/unread-count          (bell badge)
   3. /api/notifications/{id}/read|read-all|acknowledge
   4. /api/field-leadership/portal/notifications-recent  (FL panel)
   5. /api/me/notifications                    (legacy crew-hub, unused)
```

---

## DUPLICATE RISK ANALYSIS — SUMMARY

| Risk | Magnitude in snapshot | Mechanism | Producer cluster |
|---|---|---|---|
| Same event re-fires (no event_id) | 49× per asset on TB-03 | No idempotency key in schema | trench_safety, daily_report, task.assigned, qaqc.deficiency |
| Same record × multiple roles | 3× per trench event | `_fanout` iterates roles | trench_safety/notifications.py |
| Same record × multiple users (HR fan-out) | 1 row per HR user × N HR users (58) per request | `_notify_hr_queue_pending` insert_many | employee_requests |
| Mixed-schema duplicate | none observed (legacy and canonical do not co-write the same event) | — | — |

---

## ORPHAN RISK ANALYSIS — SUMMARY

| Class | Count | Severity |
|---|---|---|
| `recipient_user_id` points to non-existent user (real users) | 0 | NONE |
| `recipient_user_id` points to test fixtures (`itest-mech-*`) | 7 distinct (7 rows) | LOW — janitorial |
| Legacy `user_email` points to non-existent user | 0 of 58 | NONE |
| Legacy rows with no `recipient_role` AND no `recipient_user_id` | 552 | HIGH — invisible to bell |
| `tasks_notifications` rows with no reader | 162 | HIGH — silent under-delivery |
| `recipient_role` set to a value with no live users (e.g. `superintendent`) | 25 | MEDIUM — depends on portal-token aliasing |

---

## WRONG-RECIPIENT RISK ANALYSIS — SUMMARY

| Risk | Status |
|---|---|
| Role-broadcast bleed (every PM sees every PM event) | **CONFIRMED** — see Q6 P1 |
| Stale UUID re-issued after merge → wrong human inherits notifications | THEORETICAL — no merge events observed in snapshot, but the schema permits it |
| `is_asset_admin` localStorage hint outliving server-side revocation | LATENT — until next token refresh |
| pm_engine writes lost to wrong collection | **CONFIRMED** — 162 silent rows in `db.tasks_notifications` |

---

## CANONICALIZATION PLAN (read-only proposal — NOT AUTHORIZED FOR EXECUTION)

> The following is a recommendation only, scoped to be executed under a separate authorization.

1. **Freeze the schema** at the canonical shape (`type`, `recipient_role`, `recipient_user_id`, `severity`, `read_by`, `acknowledged_at`, `expires_at`, `delivery`, `linked_*`, `link_url`). No other writer may insert new shapes after the cutoff.

2. **Add immutable fields** to every new row: `event_id` (uuid), `source` (module name), `producer_version` (string), `idempotency_key` (deterministic hash of (type, source_record_id, role, recipient_user_id) within a 60 s window).

3. **Migrate 552 legacy `db.notifications` rows in place:**
   - `kind` → `type`
   - `audience` → `recipient_role`
   - `user_email` → resolve to `recipient_user_id` via `users.find_one({email})`
   - `read` (bool) → `read_by: [{user_id, role, at}]` when true
   - `url` → `link_url`
   Drop the legacy fields after dual-read verification.

4. **Migrate 162 `db.tasks_notifications` rows** into `db.notifications` with `type=pm_engine.<kind>`, `recipient_role=shop`/`mechanic`-bucket, `recipient_user_id=audience_id`. Then drop the collection.

5. **Retire `phase4.notify_user` and `/api/me/notifications`** (frontend no longer calls them).

6. **Switch producers to a single helper** (`emit_notification`) — remove direct `db.notifications.insert_one` calls in `employee_requests.py`, `operations_actions/api.py`, `pm_engine.py`, `notify_ownership_lock_seed.py`, `phase4.py`.

7. **Add project-scope filter** to the PM bell:
   - Read `db.project_team_assignments` for the actor → set of `project_numbers`.
   - Filter clause: `linked_project_number IN <set> OR linked_project_number IS NULL` (system-wide PM events still surface).

8. **Add idempotency** at write time inside `_NotificationService.fanout`: dedupe on `(type, linked_source_record_id, recipient_role, recipient_user_id)` within 60 s.

9. **Add acknowledge workflow** to the UI for `severity=Critical` so the 0 % ack rate becomes meaningful.

10. **Add a single audit log row** per fanout into `db.notification_audit` with `{event_id, ts, type, written_to: [<notification_id>...]}` so every row can be traced back to a producer call.

---

## EVIDENCE-MISSING NOTES

| Gap | What is missing |
|---|---|
| Production-vs-preview parity | This audit was run against `masci_safety_preview`. Production may have a different volume, but the **schema** is identical (same code paths). Numbers will differ; conclusions will not. |
| PM-engine reader | We could not locate any reader for `db.tasks_notifications` — claim is "no reader" based on full grep across `/app`. If a mobile or external client reads it, that needs proof. |
| Acknowledge-rate root cause | Whether 0 acks is "no Critical severity issued" vs "users never click acknowledge" requires a UI session test, deferred. |
| Aliasing of `fl` ↔ `field_leadership` | Confirmed by `actor_role()` + `_scope_filter` reading the same scope_roles list. Edge-case where a producer hard-codes `recipient_role="fl"` should be verified by a producer audit, deferred. |

---

## ABSOLUTE STATUS

- ❌ **The current system is NOT trustworthy.**
- 🔒 **No remediation has been performed.**
- 🟢 **The audit is complete; no code, no migration, no data write was executed.**
- 🟡 **Remediation plan above is a proposal only — awaiting separate authorization.**

— End of TRACK 15.28B audit —
