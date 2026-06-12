# Track 13.18 — Material Movement Ledger · Certification & Architecture

**Date:** 2026-06-12
**Mode:** SOURCE-TRUTH CERTIFICATION + ARCHITECTURE DESIGN ONLY
**Implementation:** NONE. Zero code · zero route · zero schema · zero UI.
**Doctrine:** DISCOVER → VERIFY → DOCUMENT → DECIDE → BUILD. Source-code reality wins.

---

## 1 · TL;DR

A Material Movement Ledger is **already physically distributed across five live sources** in
the codebase. There is no single `material_ledger` collection, and there should not be one
yet. The current architecture is a derived, read-only rollup (`/api/material-movement/daily/...`)
backed by:

| Source                                  | Role                                  | Truth posture                |
| --------------------------------------- | ------------------------------------- | ---------------------------- |
| `daily_reports.materials[]`             | Inbound deliveries · foreman authored | Field source truth (in)      |
| `daily_reports.outbound_materials[]`    | Outbound hauls · foreman authored     | Field source truth (out)     |
| `dispatch_assignments`                  | MASCI-controlled hauling              | Dispatch operational truth   |
| `haul_cycles`                           | Derived cycle summary                 | Dispatch completion truth    |
| `operational_attachments` (scale_ticket etc.) | Weight / ticket proof layer       | Proof truth                  |
| `odr.MaterialEvent` (inside ODR section 5.5) | Formal archive layer             | Archive / record-layer truth |
| `fleetwatcher` reserved template        | Future automated feed                 | NOT CONNECTED · null fields  |

**Verdict:** The ledger foundation exists. What is missing is **role-scoped projection +
proof-join + conflict surfacing** on top of the existing derived layer.

**Recommended next action:** **B — Build a thin Material Ledger foundation now**, but ONLY
as an additive read-only enhancement to the existing `/api/material-movement/daily/...`
endpoint. NO new collection. NO new tile. NO new UI. NO FleetWatcher. The next track
(13.19) should enrich the derived view with proof-join + verification status, leaving
PM / Dispatch / Admin role views for tracks 13.20+.

---

## 2 · Phase 1 — Source-Truth Inventory

### 2.1 Backend modules audited

| File                                                | Material role                                            |
| --------------------------------------------------- | -------------------------------------------------------- |
| `backend/routes/material_movement.py`               | **Derived rollup** — single endpoint, no persistence    |
| `backend/routes/daily_reports.py`                   | `materials[]` inbound + `outbound_materials[]` (K-MM-2) |
| `backend/routes/odr/models.py` (`MaterialEvent`)    | Formal archive layer — closed-set enums                  |
| `backend/routes/odr/enums.py`                       | `MaterialEventKind`, `MaterialUom`, `MaterialIssue`     |
| `backend/routes/operational_attachments.py`         | Proof layer — 12 attachment types incl. `scale_ticket` |
| `backend/routes/dispatch_lifecycle.py`              | `dispatch_assignments` + `haul_cycles` derivation       |
| `backend/routes/dispatch_command_center.py`         | `_fleetwatcher_template()` · NOT_CONNECTED              |
| `backend/routes/pm_command_center.py`               | `/pm/command-center/{materials,hauls}` per-project view |
| `backend/routes/operations_center_command.py`       | Company-wide hauls/materials rollup (Operations Center) |
| `backend/services/asset_spine.py`                   | Reserves `fleetwatcher_asset_id` mapping field          |
| `backend/routes/platform_data_truth.py`             | `FLEETWATCHER_API_KEY` env-flag check                   |

### 2.2 Frontend consumers audited

| File                                                              | Material role                              |
| ----------------------------------------------------------------- | ------------------------------------------ |
| `frontend/src/components/MaterialMovementTile.jsx`                | Read-only daily tile (MM-001B · E-1)       |
| `frontend/src/pages/ViewDailyReport.jsx`                          | Mounts `MaterialMovementTile`              |
| `frontend/src/pages/PmCommandCenter.jsx` (`tab=materials`)        | PM project material view                   |
| `frontend/src/components/pm/command/PmHaulsBoard.jsx`             | PM hauls board                             |
| `frontend/src/components/dispatch/command/HaulBoard.jsx`          | Dispatch company-wide haul board           |
| `frontend/src/components/dispatch/AttachmentStrip.jsx`            | Scale-ticket 4-field inputs (Track 13.14)  |
| `frontend/src/pages/DispatchCommandCenter.jsx`                    | Dispatch board (FleetWatcher templates)    |
| `frontend/src/pages/OperationsCenterCommand.jsx`                  | Ops Center hauls+materials                 |

### 2.3 Collections / schemas touching material movement

| Collection                  | Material-relevant fields                                                                                                                                                       |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `daily_reports`             | `materials[]` (description, quantity, unit, supplier, ticket_number, ticket_photos), `outbound_materials[]` (material, quantity, unit, hauler, destination, ticket_or_manifest, notes), `production[]` (NOT material movement — excluded by MM-001B-F1 doctrine), `report_date`, `project_number` |
| `dispatch_assignments`      | truck_id, driver_id, driver_name, project_number, project_name, material, source_location, destination, dropoff_location, haul_type, load_count, carrier, trailer_id, equipment_id, liquid_product, scheduled_date, state_history, assigned_at, completed_at |
| `haul_cycles`               | assignment_id, truck_id, driver, project, material, source_location, destination, haul_type, started_at, completed_at, total_seconds, wait_seconds, operating_seconds, transitions |
| `operational_attachments`   | type ∈ {scale_ticket, asphalt_ticket, tanker_BOL, fuel_receipt, delivery_receipt, load_photo, damage_photo, dump_receipt, …}, host_kind ("assignment"), host_id, weight_gross_lbs, weight_tare_lbs, weight_net_lbs, material_code, uploaded_by, uploaded_role, uploaded_at, operational_note, filename, content_type, R2 key |
| `odr_*` (MaterialEvent block) | material_event_id, work_area_id, kind ∈ {delivered, consumed, staged, returned, wasted, rejected, short}, material_code, description (localized), quantity, uom ∈ {ton, cy, lf, sf, ea, gal, other}, vendor, ticket_numbers[], photos[], issue ∈ {shortage, reject, damage, wrong_material} |

### 2.4 FleetWatcher reality check

* `FLEETWATCHER_API_KEY` env var **not configured** (per `platform_data_truth.py`).
* `_fleetwatcher_template()` returns **all None** — `ticket_number`, `tons`, `loads`,
  `cycle_time_min`, `plant`, `material`, `delivery_status`.
* `asset_spine` reserves `fleetwatcher_asset_id` mapping field — **never populated** in
  preview DB.
* No ingestion route exists. No reconciliation logic exists.
* **FleetWatcher = future only.** Track 13.18 honors this — designs ingestion shape, does
  not implement.

### 2.5 MaintainX reality check

* Stubbed `_maintainx_template()` — work-order fields only.
* **Not part of material movement.** Work-order data ≠ haul/ticket data. Out of scope.

---

## 3 · Phase 2 — Current Data Capability Map

| Data Item                  | Exists Today | Source(s)                                                  | Field name(s)                                              | Collection                | Endpoint                                                  | Frontend consumer                              | Reliability                       | Notes                                                                          |
| -------------------------- | ------------ | ---------------------------------------------------------- | ---------------------------------------------------------- | ------------------------- | --------------------------------------------------------- | ---------------------------------------------- | --------------------------------- | ------------------------------------------------------------------------------ |
| project_number             | YES          | All sources                                                | `project_number`                                           | All                       | All material endpoints                                    | All                                            | HIGH                              | Canonical join key                                                             |
| project_name               | YES          | dispatch_assignments, haul_cycles, daily_reports           | `project_name`                                             | All                       | All                                                       | All                                            | HIGH                              | —                                                                              |
| PM assignment              | PARTIAL      | Project records / role fan-out                             | (role-based)                                               | `projects` / role tokens  | role-fan-out                                              | PM Hub V2                                      | MED — role-based, not per-project | No per-project PM ownership table; fan-out by role                             |
| Co-PM assignment           | NO           | —                                                          | —                                                          | —                         | —                                                        | —                                              | —                                 | Not in current architecture                                                    |
| HR assignment              | N/A          | —                                                          | —                                                          | —                         | —                                                        | —                                              | —                                 | HR is not a material owner                                                     |
| Movement date              | YES          | daily_reports.report_date · dispatch.scheduled_date        | `report_date`, `scheduled_date`                            | daily_reports, dispatch_assignments | `/material-movement/daily/{p}/{d}`                | MaterialMovementTile, PM CC                    | HIGH                              | Two formats unified at read time                                               |
| Truck number               | YES          | dispatch_assignments, haul_cycles                          | `truck_id`                                                 | dispatch_assignments      | dispatch endpoints                                        | HaulBoard                                      | HIGH                              | No truck on Daily Report inbound rows                                          |
| Driver name                | YES          | dispatch_assignments, haul_cycles                          | `driver_id`, `driver_name`                                 | dispatch_assignments      | dispatch endpoints                                        | HaulBoard                                      | HIGH                              | —                                                                              |
| Hauler / company           | PARTIAL      | dispatch_assignments.carrier · daily_reports.outbound_materials.hauler | `carrier`, `hauler`                              | both                      | rollup                                                    | MaterialMovementTile                           | MED                               | Free-text                                                                      |
| Ticket number              | YES          | daily_reports.materials[*].ticket_number · outbound_materials[*].ticket_or_manifest · operational_attachments scale_ticket meta · ODR.MaterialEvent.ticket_numbers[] | several                                                    | several                   | rollup + ODR                                              | tile + attachment strip                        | MED                               | **No single canonical ticket field** — proof layer is the strongest            |
| Material code              | PARTIAL      | operational_attachments.material_code (Track 13.14) · ODR.MaterialEvent.material_code | `material_code`                                         | both                      | both                                                      | AttachmentStrip · ODR                          | LOW (sparse)                      | Free-text per-event today                                                      |
| Material description       | YES          | daily_reports.materials[*].description · outbound_materials[*].material · dispatch.material · ODR.MaterialEvent.description | many                                          | all                       | all                                                       | all                                            | HIGH (free-text)                  | Free-text labels                                                               |
| Gross weight (lbs)         | YES          | operational_attachments.weight_gross_lbs (Track 13.14)     | `weight_gross_lbs`                                         | operational_attachments   | attachment endpoints                                      | AttachmentStrip                                | LOW (only when entered)           | Optional structured field                                                      |
| Tare weight (lbs)          | YES          | operational_attachments.weight_tare_lbs                    | `weight_tare_lbs`                                          | operational_attachments   | attachment endpoints                                      | AttachmentStrip                                | LOW                               | Optional                                                                       |
| Net weight (lbs)           | YES          | operational_attachments.weight_net_lbs (explicit or derived gross−tare) | `weight_net_lbs`                              | operational_attachments   | attachment endpoints                                      | AttachmentStrip                                | LOW                               | Auto-computed when gross+tare provided                                         |
| Quantity                   | YES          | daily_reports.materials[*].quantity · outbound_materials[*].quantity · ODR.MaterialEvent.quantity | `quantity`                            | all                       | all                                                       | all                                            | HIGH                              | Free-numeric                                                                   |
| Unit of measure            | YES          | daily_reports rows.unit · ODR.MaterialEvent.uom (closed-set ton/cy/lf/sf/ea/gal/other) | `unit`, `uom`                                 | all                       | all                                                       | all                                            | MED                               | ODR uses closed enum; Daily Report uses free-text                              |
| Loads count                | YES          | dispatch_assignments.load_count · haul_cycles count        | `load_count`                                               | dispatch_assignments      | rollup                                                    | tile                                           | HIGH (per-assignment)             | One row = one haul                                                             |
| Haul direction (IN/OUT)    | YES          | derived from source: materials[]=IN, outbound_materials[]=OUT, dispatch=carrier-defined | (derived)                                  | derived                   | derived                                                   | tile                                           | HIGH                              | No explicit `direction` field in any collection — derived from source list     |
| Source location / plant    | YES          | dispatch_assignments.source_location · daily_reports.materials.supplier | `source_location`, `supplier`                  | both                      | both                                                      | tile, dispatch board                           | MED                               | Free-text                                                                      |
| Destination job            | YES          | dispatch_assignments.destination · dropoff_location · outbound_materials.destination | several                                       | both                      | both                                                      | tile                                           | MED                               | Free-text                                                                      |
| Daily report reference     | YES          | rollup carries `dr_id`                                     | `dr_id`                                                    | derived                   | rollup                                                    | tile                                           | HIGH                              | —                                                                              |
| ODR reference              | PARTIAL      | ODR records exist; no link from rollup yet                 | `material_event_id`                                        | ODR                       | ODR endpoints                                             | ODR consumers                                  | MED                               | **No join from rollup → ODR.MaterialEvent today**                              |
| Scale-ticket attachment    | YES          | operational_attachments where host_kind="assignment", type="scale_ticket" | `host_id`, `type`                          | operational_attachments   | `/operational-attachments?host_kind=assignment&host_id=…` | AttachmentStrip                                | HIGH                              | Hosted **on assignment only** today                                            |
| Dispatch assignment ref    | YES          | rollup carries dispatch rows                               | `id` (in `dispatch.rows[]`)                                | derived                   | rollup                                                    | tile                                           | HIGH                              | —                                                                              |
| FleetWatcher ID            | NO           | reserved field only                                        | `fleetwatcher_asset_id`                                    | asset_spine               | `_fleetwatcher_template()` (null)                         | dispatch board (chip)                          | N/A                               | Future                                                                         |
| Verification status        | NO           | —                                                          | —                                                          | —                         | —                                                        | —                                              | —                                 | **Doesn't exist** — design candidate                                           |
| Created by                 | YES          | daily_reports.prepared_by · attachments.uploaded_by · dispatch.created_by | several                                            | all                       | all                                                       | various                                        | HIGH                              | —                                                                              |
| Corrected by               | PARTIAL      | dispatch revisions (RevisionRequest)                       | `correction_reason`                                        | dispatch_assignments      | revision endpoint                                         | dispatch                                       | MED                               | Only on dispatch revisions; not on Daily Reports or attachments                |
| Source system              | YES          | implicit per-collection                                    | (collection name)                                          | all                       | all                                                       | all                                            | HIGH                              | Rollup labels its own source (`dispatch`, `incoming`, `outgoing`)              |

---

## 4 · Phase 3 — Source of Truth Analysis

Per-field, primary / secondary / proof / future / conflict-resolution:

### 4.1 Ticket number

* **Primary:** `operational_attachments` scale_ticket / asphalt_ticket / delivery_receipt metadata (the actual ticket image is the truth).
* **Secondary:** `daily_reports.materials[*].ticket_number` (foreman-typed).
* **Proof:** the uploaded attachment file (R2 binary).
* **Future:** FleetWatcher ticket_number when integrated.
* **Conflict rule:** Attachment proof wins. Daily Report number flagged for verification on mismatch. **Never overwrite the attachment.**

### 4.2 Material quantity

* **Primary:** `operational_attachments.weight_net_lbs` where present (Track 13.14 structured net).
* **Secondary:** `daily_reports.materials[*].quantity` (manual) and `outbound_materials[*].quantity`.
* **Future:** FleetWatcher ticket tons.
* **Conflict rule:** Flag mismatch when |attachment_net − reported_quantity| / reported_quantity > tolerance. Do **not** auto-overwrite. Surface as `needs_verification`.

### 4.3 Material description / code

* **Primary:** `operational_attachments.material_code` (Track 13.14) where present.
* **Secondary:** ODR.MaterialEvent.material_code (closed-set archive layer).
* **Tertiary:** Daily Report free-text description.
* **Conflict rule:** When attachment has code AND DR has description, both shown — operator may correct. No automated normalization.

### 4.4 Truck / driver

* **Primary:** `dispatch_assignments` (when MASCI-controlled haul).
* **Secondary:** `daily_reports.outbound_materials[*].hauler` for non-MASCI hauls.
* **Conflict rule:** None — DR carrier rows describe non-MASCI trucks; dispatch describes MASCI trucks. Distinct populations.

### 4.5 Movement date

* **Primary:** `daily_reports.report_date` for field-recorded rows.
* **Primary:** `dispatch_assignments.scheduled_date` for dispatched rows.
* **Conflict rule:** None — independent dimensions. Rollup joins on `(project_number, date)`.

### 4.6 Loads count

* **Primary:** `haul_cycles` rows (one per completed assignment).
* **Secondary:** `dispatch_assignments.load_count` (planned).
* **Future:** FleetWatcher load count.
* **Conflict rule:** Cycle count wins over planned count. Variance is a Dispatch-actionable signal.

### 4.7 Direction (IN / OUT)

* **Primary:** derived. `daily_reports.materials[]` = IN. `daily_reports.outbound_materials[]` = OUT. `dispatch_assignments` direction depends on `source_location → destination` semantics (carrier-defined, free-text today).
* **Conflict rule:** Direction is **derived**, not stored. Do not introduce a stored `direction` field on dispatch_assignments unless operator workflow demands it.

### 4.8 Verification status

* **Primary:** **Does not exist.** Design candidate for Track 13.19+.
* Recommendation: virtual flag in rollup output, computed at read time. Values: `unverified` / `proof_present` / `needs_review` / `verified`. NO persistence yet.

---

## 5 · Phase 4 — Role-Based Visibility Matrix

| Role             | Create movement | Attach scale ticket | View project-scoped | View company-wide | Edit/Correct | Verify/Certify | Export/Report | See missing-ticket warnings | See FleetWatcher errors (future) |
| ---------------- | --------------- | ------------------- | ------------------- | ----------------- | ------------ | -------------- | ------------- | --------------------------- | -------------------------------- |
| **PM**           | NO (read)       | NO (read)           | **YES (assigned)**  | **NO**            | NO           | NO             | Project export only | **YES (assigned)**       | NO                               |
| Co-PM            | NO              | NO                  | YES (if assigned)   | NO                | NO           | NO             | Project export only | YES                       | NO                               |
| Superintendent   | YES (via DR)    | YES                 | YES (assigned)      | NO                | YES (DR own) | NO             | NO            | YES                         | NO                               |
| Foreman          | YES (via DR)    | YES                 | YES (assigned)      | NO                | YES (DR own) | NO             | NO            | YES                         | NO                               |
| **Dispatch**     | YES (via assignment) | YES (on assignment) | YES (any project)   | **YES**           | YES (revision) | YES (operational) | YES (company) | YES                       | YES                              |
| Shop             | NO              | NO                  | NO                  | NO                | NO           | NO             | NO            | NO                          | NO                               |
| **Admin**        | NO              | NO                  | YES (read-only)     | **YES**           | NO (read)    | YES (data-quality) | YES (company export) | YES                  | YES                              |
| Leadership       | NO              | NO                  | YES (read-only)     | YES (summary)     | NO           | NO             | YES (summary) | YES (summary)               | NO                               |
| **Driver** (no-login) | NO         | YES (on own assignment via dispatch UI) | NO                  | NO                | NO           | NO             | NO            | NO                          | NO                               |
| HR               | NO              | NO                  | NO                  | NO                | NO           | NO             | NO            | NO                          | NO                               |
| Safety           | NO              | NO                  | NO                  | NO                | NO           | NO             | NO            | NO                          | NO                               |

**Hard rules enforced:** PM scope = assigned projects only · Dispatch sees company-wide
operational movement · Admin sees company-wide rollup + data quality · Driver remains
no-login · Safety / HR / Shop are not material ledger owners.

---

## 6 · Phase 5 — Existing Material Movement Module Certification

### Object: `backend/routes/material_movement.py` + `frontend/src/components/MaterialMovementTile.jsx`

| Question                              | Answer                                                                                                              |
| ------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| What does it do today?                | Single GET endpoint returning a project-day rollup: dispatch summary + incoming[] + outgoing[]. Hides on zero in UI. |
| What endpoints exist?                 | `GET /api/material-movement/daily/{project_number}/{date}` — one endpoint.                                          |
| What frontend exists?                 | `MaterialMovementTile.jsx` rendered in `ViewDailyReport.jsx` (read-only).                                            |
| What data does it store?              | **Nothing.** Pure derivation. No collection.                                                                         |
| What role owns it?                    | Same access posture as `/api/jobs` (public read by signed-in role). Not project-scoped at the endpoint level.        |
| Complete / partial / dormant / hidden? | **Partial.** Inbound + outbound + dispatch summary work; proof-join, conflict-flag, verification-status absent.     |
| Should it be the ledger backbone?     | **YES** — keep as the derived ledger backbone. Do not introduce a new collection.                                   |
| Should it remain a tile?              | YES (project-day visibility tile). Future role views layer on top of the same endpoint with new query params.       |
| Merge with attachments / scale tickets? | **JOIN, not merge.** Add an optional `?include=attachments` projection that joins `operational_attachments` on dispatch row id. |
| Leave it alone?                       | Not entirely — Phase A enhancements needed. Core shape unchanged.                                                   |

**Disposition:** **LEDGER BACKBONE.**

### Object: `odr.MaterialEvent`

| Question                              | Answer                                                                                              |
| ------------------------------------- | --------------------------------------------------------------------------------------------------- |
| What does it do today?                | Captures formal per-event material records inside ODR section 5.5 (delivered/consumed/staged/etc.). |
| Disposition                           | **SUPPORTING VIEW** — formal archive layer. Do **not** retire; do **not** promote to backbone.       |

### Object: `haul_cycles`

| Question                              | Answer                                                                                              |
| ------------------------------------- | --------------------------------------------------------------------------------------------------- |
| What does it do today?                | One row per completed dispatch_assignment — derived cycle truth (timing, transitions, wait time).    |
| Disposition                           | **SUPPORTING VIEW** — Dispatch operational summary. Read source for Dispatch company-wide ledger.    |

### Object: `operational_attachments` (scale_ticket family)

| Question                              | Answer                                                                                              |
| ------------------------------------- | --------------------------------------------------------------------------------------------------- |
| What does it do today?                | Proof file storage + structured weight/material code fields (Track 13.14).                          |
| Disposition                           | **SUPPORTING VIEW · PROOF LAYER.** Keep as proof source of truth. Do not move into ledger backbone.  |

---

## 7 · Phase 6 — Daily Report / ODR Relationship

| Question                                       | Answer                                                                                                                                                |
| ---------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| Do Daily Reports already capture material in/out? | YES — `materials[]` (inbound) + `outbound_materials[]` (outbound, K-MM-2).                                                                          |
| Do ODR records reference material movement?    | YES — `MaterialEvent` block with closed-set enums (kind/uom/issue).                                                                                   |
| Should Daily Reports write to ledger?          | **NO.** Daily Reports already are the field source truth for the ledger. The ledger reads from them, not the other way around.                       |
| Should ledger feed Daily Reports?              | **NO.** Daily Reports are field-authored. The ledger is derived. One-way read.                                                                        |
| Should ODR archive ledger snapshots?           | **NO** — ODR `MaterialEvent` is its own per-event record. It overlaps with Daily Report material rows but is authored independently (formal layer). |
| Should ODR link to ledger records?             | **OPTIONAL · future.** A read-time join (ODR.MaterialEvent ↔ Daily Report row) is possible if operator workflow demands cross-reference. Not now.    |
| What avoids duplicate entry?                   | Daily Reports remain the field entry point. ODR is authored separately by senior superintendent / PM during formal record review.                    |
| What avoids conflicting records?               | Surface both at read time with source labels (`source: daily_report`, `source: odr_material_event`). Flag quantity divergence ≥ tolerance.            |

**Doctrine:** Daily Reports stay primary field-entry. ODR stays formal record archive. Ledger
is derived view across both. No double-write, no double-entry. The ledger NEVER writes back.

---

## 8 · Phase 7 — Dispatch Relationship

| Question                                           | Answer                                                                                                                              |
| -------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| Does Dispatch currently have load/haul data?       | YES — `dispatch_assignments` + `haul_cycles`.                                                                                       |
| Does Dispatch know truck/job/material?             | YES — assignment carries truck_id, project_number, material, source/destination.                                                    |
| Should Dispatch create ledger entries?             | **YES** — by creating assignments. They already do.                                                                                 |
| Should Dispatch only view ledger entries?          | **BOTH** — they create (assignments) and view (rollup).                                                                             |
| Should Dispatch verify loads?                      | **YES** — operational verification at Dispatch level. Not accounting verification.                                                  |
| Should Dispatch see day/week/month/year rollups?   | YES — at the Dispatch Command Center level, NOT inside the Map-First canvas.                                                        |
| Should Dispatch have filters by job/material/truck/driver? | YES — but as a Dispatch Companion view, **not** inside the MapLibre surface.                                                |
| What must not disturb the map-first workflow?      | The MapLibre canvas is HARD-LOCKED. Any haul-ledger UI ships as a **separate Dispatch Companion page**, not as an overlay.          |

---

## 9 · Phase 8 — PM Relationship

| Question                                 | Answer                                                                                                                                                  |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Where should project-scoped material movement appear? | `PmProjectDetail.jsx` (per-project material panel) **and** `PmCommandCenter.jsx → tab=materials` (per-project rollup). Both routes exist today. |
| PM Hub?                                  | NO — PM Hub stays the action queue. Material rollup belongs in Project Detail / Command Center.                                                         |
| PM Project Detail?                       | **YES** — add a read-only Material Movement panel (same shape as the Operational Events panel added in Track 13.13).                                    |
| Daily Report view?                       | YES — `MaterialMovementTile` already renders there.                                                                                                     |
| ODR?                                     | OPTIONAL — ODR consumers already see their own `MaterialEvent` rows.                                                                                    |
| Separate project material page?          | **NO** — would create a dead route. Use the existing PM Command Center tab.                                                                             |
| Minimum useful PM view?                  | Per-project daily roll-up of in/out/dispatch + ticket-attachment count + missing-proof count. NO company-wide rollup ever.                              |
| Day / week / month / year?               | Day = exists. Week/month/year = future enhancement. **Day is sufficient for first cut.**                                                                 |
| Verified records only or all?            | **All**, with source labels. PMs need to see unverified records to chase proof.                                                                         |
| Missing-ticket warnings?                 | **YES** — surface missing-proof count per project-day. PM can route to attachment workflow already.                                                     |

**Hard rule:** PM sees assigned projects only. No company-wide material ledger in PM portal.

---

## 10 · Phase 9 — Admin Relationship

| Question                              | Answer                                                                                                                |
| ------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| Company-wide material rollups?        | **YES** — Admin reads across all projects.                                                                            |
| Data-quality issues?                  | **YES** — missing tickets, quantity divergences, unverified rows.                                                     |
| Missing tickets?                      | YES — count of assignments without scale_ticket attachment.                                                           |
| Export ledger?                        | **YES** — CSV export of derived ledger by date range. NO ERP integration.                                             |
| Reconcile conflicts?                  | YES — operational reconciliation only. Annotate via existing notification or attachment workflow. NO new collection.  |
| Admin Hub card later?                 | YES — likely a Material Data-Quality card on `AdminHubV2.jsx` alongside the Operations Actions card. Future track.    |
| Dedicated Admin page later?           | OPTIONAL — `/admin/material-quality` page consuming the same derived endpoint with admin-only filters. Future track.   |

**Hard rule:** Admin view is operational/data-quality/reporting only. No accounting. No
cost. No pay-app. No ERP. No vendor portal.

---

## 11 · Phase 10 — FleetWatcher Future Integration Design

**Status today:** NOT_CONNECTED · `_fleetwatcher_template()` returns all None ·
`FLEETWATCHER_API_KEY` env not set · no ingestion route.

**Future ingestion shape (design only — DO NOT BUILD):**

| FleetWatcher field    | Ledger join target                              | Confidence scoring          |
| --------------------- | ----------------------------------------------- | --------------------------- |
| ticket_number         | operational_attachments.ticket_number metadata  | match → HIGH; no match → LOW |
| truck                 | dispatch_assignments.truck_id (via asset_spine.fleetwatcher_asset_id) | mapped → HIGH; unmapped → MED |
| driver                | dispatch_assignments.driver_name                | name match → MED            |
| material              | dispatch_assignments.material (free-text)       | normalized match → MED      |
| tons (net)            | operational_attachments.weight_net_lbs          | tolerance check (±2%) → HIGH |
| load_time             | dispatch_assignments.state_history[*].at        | within window → HIGH        |
| dump_time             | dispatch_assignments.completed_at               | within window → HIGH        |
| plant / pit           | dispatch_assignments.source_location            | normalized match → MED      |
| job                   | dispatch_assignments.project_number             | exact → HIGH                |
| haul direction        | derived from plant→job direction                | high                        |
| ticket image          | new operational_attachment (type=scale_ticket) with `source_system: fleetwatcher` | injected as proof |

**Future ingestion layer:**

* New collection `fleetwatcher_tickets` (raw inbox, append-only). Polled or webhook-fed.
* Reconciliation job matches FleetWatcher tickets to existing dispatch_assignments by
  truck + date + window.
* Match writes a structured attachment with `source_system: fleetwatcher` and links to the
  assignment.
* No match → row sits in `unmatched_fleetwatcher_tickets` for Admin reconciliation queue.

**Duplicate detection:** ticket_number + truck + day uniqueness check.

**Manual correction:** Operator (Admin or Dispatch) may dismiss a FleetWatcher row or
reassign it to a different assignment. Audit row written.

**DO NOT IMPLEMENT.** FleetWatcher remains future.

---

## 12 · Phase 11 — Conflict Resolution / Data Quality

### Example: DR says 500 tons · scale tickets total 480 tons · dispatch says 24 loads · FleetWatcher (future) says 25 loads.

**Rules:**

1. **Never auto-overwrite proof records.** Attachment net weight is canonical.
2. **Flag conflicts** at read time. Do not persist a single reconciled value.
3. **Surface source labels** on every row (`source: daily_report`, `source: dispatch`, `source: attachment`, `source: odr_material_event`, `source: fleetwatcher`).
4. **Verification status (virtual, computed at read time):**
   - `proof_present` — at least one scale_ticket attachment exists for the assignment/day.
   - `needs_review` — quantity divergence ≥ tolerance OR missing attachment when expected.
   - `unverified` — no proof, no review yet.
   - `verified` — operator marked verified (future — requires new field or new collection; **defer**).
5. **Authorized correction:** today, only via existing source-level edits (Daily Report edit, dispatch revision, attachment re-upload). NO new correction UI yet.
6. **Audit trail:** preserved at source. No new audit collection.
7. **Preserve original source:** the rollup never mutates source documents.
8. **Mark verified / needs review / corrected:** virtual labels only, no persistence in this phase.

---

## 13 · Phase 12 — Proposed Ledger Data Model

**This is design only. NO collection is being created.**

The ledger is a **derived virtual document** per project-day. It already exists in
`/api/material-movement/daily/{p}/{d}` — Phase A enriches the output with the following
shape:

```jsonc
{
  "project_number": "...",
  "project_name": "...",
  "date": "YYYY-MM-DD",
  "rollup": {
    "loads_in": 0,
    "loads_out": 0,
    "tons_in": null,
    "tons_out": null,
    "trucks_seen": 0,
    "proof_present_count": 0,
    "needs_review_count": 0,
    "unverified_count": 0
  },
  "rows": [
    {
      "row_id": "<derived>",                     // hash(source_system|source_record_id)
      "direction": "IN" | "OUT" | "DISPATCH",
      "movement_date": "YYYY-MM-DD",
      "movement_time": "HH:MM" | null,
      "material_description": "...",
      "material_code": "..." | null,
      "quantity": 0 | null,
      "unit": "...",
      "weight_net_lbs": 0 | null,
      "weight_gross_lbs": 0 | null,
      "weight_tare_lbs": 0 | null,
      "ticket_number": "..." | null,
      "truck_number": "..." | null,
      "driver_name": "..." | null,
      "hauler": "..." | null,
      "source_location": "..." | null,
      "destination_location": "..." | null,

      "source_system": "daily_report" | "dispatch_assignment" | "odr_material_event" | "operational_attachment" | "fleetwatcher",
      "source_record_id": "...",
      "daily_report_id": "..." | null,
      "odr_id": "..." | null,
      "attachment_id": "..." | null,
      "dispatch_assignment_id": "..." | null,
      "fleetwatcher_ticket_id": null,

      "verification_status": "proof_present" | "needs_review" | "unverified",
      "confidence": "HIGH" | "MED" | "LOW",
      "created_by": "...",
      "corrected_by": null,
      "correction_reason": null,
      "audit_events": []
    }
  ]
}
```

| Field                       | Required now | Optional now | Future only | Source today                                                  | UI owner                      |
| --------------------------- | ------------ | ------------ | ----------- | ------------------------------------------------------------- | ----------------------------- |
| row_id                      | derived      |              |             | derived                                                       | rollup                        |
| project_number              | YES          |              |             | all sources                                                   | rollup                        |
| direction                   | YES (derived) |             |             | source list                                                   | rollup                        |
| material_code               |              | YES          |             | attachment / ODR                                              | rollup                        |
| material_description        | YES          |              |             | all sources                                                   | rollup                        |
| quantity                    |              | YES          |             | DR / ODR                                                      | rollup                        |
| weight_net_lbs              |              | YES          |             | attachment                                                    | rollup                        |
| ticket_number               |              | YES          |             | DR / attachment / ODR                                         | rollup                        |
| truck_number                |              | YES          |             | dispatch                                                      | rollup                        |
| driver_name                 |              | YES          |             | dispatch                                                      | rollup                        |
| hauler                      |              | YES          |             | dispatch.carrier · DR.hauler                                  | rollup                        |
| source_location / destination |            | YES          |             | dispatch · DR                                                 | rollup                        |
| daily_report_id             |              | YES          |             | DR                                                            | rollup                        |
| odr_id                      |              | YES          |             | ODR                                                           | rollup                        |
| attachment_id               |              | YES          |             | attachments                                                   | rollup                        |
| dispatch_assignment_id      |              | YES          |             | dispatch                                                      | rollup                        |
| fleetwatcher_ticket_id      |              |              | YES         | future                                                        | rollup                        |
| verification_status         | YES (derived) |             |             | derived from attachment presence + quantity divergence        | rollup                        |
| confidence                  | YES (derived) |             |             | derived                                                       | rollup                        |
| corrected_by / correction_reason / audit_events | |              | future      | source revisions today; no aggregation                        | future                        |

**Critical:** **No new collection.** The ledger remains derived.

---

## 14 · Phase 13 — Phased Build Plan

### Phase A — Minimum Viable Ledger Foundation · `LOWEST RISK`

* **Purpose:** Enrich the existing `/api/material-movement/daily/{p}/{d}` endpoint with proof-join + verification labels. Pure read. Zero new collection. Zero new UI.
* **Files affected:** `backend/routes/material_movement.py` (one file). Optional projection extension on `_public_attachment` output shape consumed by rollup.
* **Backend needs:**
  - Query `operational_attachments` where `host_kind="assignment"` AND `host_id ∈ dispatch row ids` AND `type ∈ {scale_ticket, asphalt_ticket, delivery_receipt, dump_receipt}`.
  - Compute `verification_status` per dispatch row (proof_present / unverified).
  - Add `rollup` counters at the top of response.
* **Frontend needs:** **NONE.** `MaterialMovementTile.jsx` is forward-compatible (extra fields ignored).
* **Risks:** Minor — additional DB read per project-day. Bounded by 500-row dispatch cap.
* **Five-pillar score:**
  - Powerful: 7/10 (proof-join is the highest-value gap)
  - Simple: 9/10 (one endpoint, one file)
  - Beautiful: 8/10 (zero UI churn)
  - Trusted: 9/10 (zero source mutation, no new collection)
  - Proven: 8/10 (existing endpoint pattern, well-tested)
* **Test requirements:** pytest extension on `material_movement.py`. Validate proof-join, counter math, empty-day behavior, attachment-but-no-dispatch behavior.
* **Rollback:** Revert single file. Zero schema delta.

### Phase B — PM Project Material View

* **Purpose:** Read-only Material panel on `PmProjectDetail.jsx` consuming Phase A's enriched endpoint. Project-scoped only.
* **Files affected:** `frontend/src/pages/PmProjectDetail.jsx` (one file).
* **Backend needs:** **NONE** (Phase A already provides the data).
* **Frontend needs:** Panel similar to the Operational Events panel from Track 13.13.
* **Risks:** Low.
* **Five-pillar:** Powerful 7 · Simple 8 · Beautiful 8 · Trusted 9 · Proven 7
* **Test requirements:** screenshot proof + empty-state proof.
* **Rollback:** Revert single file.

### Phase C — Dispatch Haul Ledger Companion

* **Purpose:** Dispatch-only company-wide haul ledger reading `haul_cycles` + dispatch_assignments + attachments. **Outside the Map canvas.**
* **Files affected:** new Dispatch companion page (probably `frontend/src/pages/DispatchHaulLedger.jsx`) + new endpoint `GET /api/dispatch/haul-ledger?from=&to=&material=&truck=&driver=&project=`.
* **Backend needs:** Read endpoint with filters. NO new collection.
* **Frontend needs:** Companion page (sidebar link in `DispatchSideNavV2.jsx`).
* **Risks:** Medium — must not encroach on the MapLibre surface. Hard lock enforced by routing.
* **Five-pillar:** Powerful 9 · Simple 7 · Beautiful 8 · Trusted 8 · Proven 7
* **Test requirements:** filter combinatorics, large-date-range pagination, map canvas non-regression.
* **Rollback:** Hide sidebar link; remove endpoint registration line.

### Phase D — Admin Data-Quality / Export View

* **Purpose:** Admin-only company-wide data-quality view + CSV export.
* **Files affected:** `frontend/src/pages/admin/AdminMaterialQuality.jsx` (new) + new endpoint `GET /api/admin/material-quality?from=&to=` + CSV export endpoint.
* **Backend needs:** Read endpoint surfacing `needs_review_count`, `unverified_count`, missing-ticket assignments. Streaming CSV.
* **Frontend needs:** Admin page + Admin Hub V2 card.
* **Risks:** Medium — large date-range query cost.
* **Five-pillar:** Powerful 9 · Simple 7 · Beautiful 7 · Trusted 9 · Proven 6
* **Test requirements:** large-range smoke test, CSV shape, role gate.
* **Rollback:** Hide Admin Hub card.

### Phase E — FleetWatcher Ingestion · `FUTURE ONLY`

* **Purpose:** Activate FleetWatcher feed when credentials + service exist.
* **Files affected:** new `backend/services/fleetwatcher_ingestion.py` + new collection `fleetwatcher_tickets`.
* **Backend needs:** webhook/poll handler, reconciliation job, unmatched queue.
* **Frontend needs:** Admin reconciliation queue UI.
* **Risks:** HIGH — external integration, credentials, rate limits, data-quality drift.
* **Five-pillar:** Powerful 10 · Simple 5 · Beautiful 7 · Trusted 6 · Proven 4
* **Blockers:** `FLEETWATCHER_API_KEY` + active FleetWatcher tenant credentials.
* **DO NOT BUILD UNTIL CREDENTIALS EXIST.**

---

## 15 · Phase 14 — What NOT to Build

The following are out of scope for the Material Movement Ledger. Repeating the hard locks:

* ❌ Full accounting / general ledger
* ❌ Cost tracking · job costing · burdened rates
* ❌ Pay application quantities
* ❌ Contract quantity tracking
* ❌ Formal change order quantities
* ❌ ERP material module
* ❌ Vendor portal
* ❌ Driver material dashboard (Driver stays no-login, no hub)
* ❌ Mechanic material view (no Mechanic Portal)
* ❌ Safety material map
* ❌ Leadership material map (no Leadership Map Lens)
* ❌ FleetWatcher fake integration / templated tons
* ❌ Auto-reconciliation without operator proof
* ❌ New `material_ledger` collection
* ❌ New `material_correction` collection
* ❌ Daily Report rewrite or schema break
* ❌ ODR rewrite
* ❌ Per-project PM ownership tables (role fan-out remains the contract)
* ❌ Verification persistence (virtual labels only in Phase A)
* ❌ Material UI inside the MapLibre canvas

---

## 16 · Phase 15 — Final Recommendation

**Chosen action: B — Build the Material Ledger foundation now (Phase A only).**

### Why B (and not F)

* The ledger foundation already exists distributed across five sources. The minimum risk
  unlock is enriching the existing derived endpoint with a proof-join + verification
  labels. Doing nothing (F) wastes the work already done by MM-001B and Track 13.14.
* Phase A is **one file** (`backend/routes/material_movement.py`), **one read endpoint
  enhancement**, **zero new collection**, **zero new UI**, **zero new schema**, **zero new
  permission model**.

### Why not C / D / E first

* C (PM project view), D (Dispatch ledger), E (Admin rollup) all depend on the enriched
  endpoint that Phase A produces. Building them first would either duplicate Phase A logic
  in each consumer or block on missing fields.

### Why not B = build everything

* Phase B–E are scoped as separate tracks. Sequencing them protects the deployment-readiness
  GREEN status and respects the 30-day operator sign-off window for portal V2 swaps.

### Recommended next track

* **Track 13.19 — Material Movement Ledger · Phase A · Proof-Join & Verification Labels.**
  Single-file backend enrichment of `/api/material-movement/daily/{p}/{d}`. Adds:
  - `rollup` counters (loads_in, loads_out, proof_present_count, needs_review_count, unverified_count)
  - Per-row `verification_status` and `confidence` virtual fields
  - Optional `attachments[]` array joined on dispatch row ids
  - **No tile change.** `MaterialMovementTile` continues to ignore extra fields.

* **Track 13.20 — Material Movement Ledger · Phase B · PM Project Material Panel.** Read-only
  panel on `PmProjectDetail.jsx`.

* **Track 13.21 — Material Movement Ledger · Phase C · Dispatch Companion Haul Ledger.**
  Companion-only, outside the MapLibre canvas.

* **Track 13.22 — Material Movement Ledger · Phase D · Admin Data-Quality + Export.**

* **Track 13.X — Material Movement Ledger · Phase E · FleetWatcher (blocked until credentials).**

---

## 17 · Required Final Response

| # | Item                                                | Value                                                                                                                                                                       |
| - | --------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1 | Track status                                        | **CLOSED.** Track 13.18 is a certification + architecture track. All 15 phases complete.                                                                                   |
| 2 | Implementation occurred                             | **NO.** Zero code change. Zero schema change. Zero route registration. Zero UI change. Zero deploy. Zero GitHub save.                                                       |
| 3 | Data sources found                                  | 5 live sources: `daily_reports.materials[]`, `daily_reports.outbound_materials[]`, `dispatch_assignments`, `haul_cycles`, `operational_attachments` (scale_ticket family), + `odr.MaterialEvent` archive layer. FleetWatcher = NOT_CONNECTED reserved template. MaintainX = out of scope. |
| 4 | Current material system status                      | **PARTIAL · LEDGER BACKBONE present.** `/api/material-movement/daily/{p}/{d}` + `MaterialMovementTile.jsx` (MM-001B · E-1) is the canonical derived view. Track 13.14 added 4 structured fields on scale_ticket attachments. ODR `MaterialEvent` is the formal archive layer. Missing: proof-join, verification status, role-scoped views. |
| 5 | Recommended architecture                            | **Derived virtual ledger** built on the existing endpoint. NO new collection. NO write-back to sources. NO FleetWatcher activation. Role-scoped projections layered on top via query params. PM = project-scoped · Dispatch = company-wide companion (outside Map) · Admin = company-wide rollup + export · Driver = no access. |
| 6 | Recommended next build                              | **Track 13.19 · Phase A** — enrich `/api/material-movement/daily/{p}/{d}` with proof-join + virtual `verification_status` + rollup counters. Single backend file. No new endpoint. No UI change. |
| 7 | What not to build                                   | New material_ledger collection · ERP/accounting/cost/pay-app · Driver material UI · Map-canvas material overlay · auto-reconciliation · FleetWatcher fake data · verification persistence yet. (See §15.) |
| 8 | Blockers                                            | None for Phase A. Phase E (FleetWatcher) blocked on `FLEETWATCHER_API_KEY` + active service credentials. Phase B–D depend on Phase A landing first. |
| 9 | Report path                                         | `/app/memory/TRACK_13_18_MATERIAL_MOVEMENT_LEDGER_CERTIFICATION_AND_ARCHITECTURE.md` (this file).                                                                          |

---

## 18 · Hard-Lock Reaffirmation (post-13.18)

* ✅ Dispatch remains Map-First (MapLibre canvas untouched).
* ✅ Driver remains no-login (no Driver Hub, no Driver material UI).
* ✅ No Mechanic Portal.
* ✅ Shop Repair Complete ≠ Returned To Service.
* ✅ One map engine.
* ✅ One source of truth — the derived endpoint, not a new physical collection.
* ✅ PMs only see assigned projects.
* ✅ Dispatch sees company-wide haul/load movement (Companion view, not Map overlay).
* ✅ Admin sees company-wide rollups.
* ✅ Daily Reports remain operational source of truth.
* ✅ ODR remains operational record archive.
* ✅ Scale Tickets remain proof / attachment layer.
* ✅ FleetWatcher = future only.
* ✅ MaintainX = not part of Material Movement.

**Track 13.18 · CLOSED. Architecture certified. Awaiting operator directive on Track 13.19.**
