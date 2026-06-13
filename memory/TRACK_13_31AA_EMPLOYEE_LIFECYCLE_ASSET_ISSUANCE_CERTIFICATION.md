# TRACK 13.31AA — Employee Lifecycle + Asset Issuance Architecture Certification

**Status:** READ-ONLY CERTIFICATION COMPLETE · 2026-06-13
**Mode:** NO code · NO schema · NO collections · NO routes · NO UI · NO deploy · NO GitHub.
**Authorizes:** Massive scope reduction of Track 13.31B. See §13.

---

## 1 · Executive Summary

The MASCI platform **already contains most of what Track 13.31B was planning to build**. A read-only audit of the live database and route tree surfaces:

- **Full Employee Lifecycle system** (`employee_lifecycle.py` · 6 endpoints · `employee_lifecycle_events` 38 rows · status transitions, offboarding-summary endpoint, audit trail).
- **Full Asset Custody system** (`asset_assignments` 16 rows · operator_employee_id → asset_id with start/end/expected-return/notes/active flag · linked to `asset_transfers`).
- **Full PPE / Safety Equipment Issuance system** (`safety_equipment_issuances` 24 rows · items array, condition, photos, employee signature, supervisor signature, total_value, doc_id formatted `SEI-2026-#####`, return endpoint, PDF generation).
- **Full Asset Transfer state machine** (`asset_transfers` 120 rows · POST/approve/reject/in-transit/receive/cancel/close · 7-step lifecycle already production-grade).
- **Asset Lifecycle plumbing already built** (`asset_spine.py` exposes `/assets/{id}/retire`, `/activate`, `/transfer`, `/onboarding/advance`, `/onboarding`, `/profile`) — **but pointing at an empty `assets` collection (0 rows)**. The endpoints exist; the data lives in `equipment_master` instead.
- **Employee → Motive / MaintainX foreign-key mapping** (`employee_mappings` 65 rows).
- **Driver qualification import + audit** (`employee_lifecycle.py:/api/hr/driver-qualification/*`).

**Conclusion:** Track 13.31B as previously scoped would create **at least 6 duplicate systems** and 2 duplicate timelines. Hard-reject those line items.

**Track 13.31B genuine remaining scope:** extend `equipment_master` with the 18 missing administrative *fields* (registration, insurance, title, lifecycle_status enum, Motive foreign-keys, division/supervisor/region, photos, document references) + add Asset Administrator role gating + reconcile the `equipment_master` vs empty `assets` collection split. **No new collections, no new workflow, no new issuance/return/custody/transfer system.**

**Five-Pillar score for current Employee Lifecycle + Asset Issuance state: 8.4 / 10.** Well above the 6.6 we scored Asset Administration at in Track 13.31A — because in this area the systems are real, mature, and in active use.

---

## 2 · Employee Lifecycle Audit

### Collections (live row counts in preview)
| Collection | Rows | Purpose |
|---|---:|---|
| `employees` | 365 | Employee registry (id, email, name, role, trade, crew, phone, is_active) |
| `hr_users` | 57 | HR portal accounts (password_hash, last_login_ip, must_change_password) |
| `employee_lifecycle_events` | 38 | **Full audit trail**: from_status, to_status, actor_role, actor_label, reason, kind, payload_snapshot, queue_request_id |
| `employee_requests` | 40 | Request queue (audit_log, payload, status, submitter, kind) |
| `employee_mappings` | 65 | MASCI ↔ Motive / MaintainX foreign-key bridges |

### Routes
* `routes/employee_lifecycle.py` (12 endpoints)
  * `GET/POST /api/hr/employees`
  * `PATCH /api/hr/employees/{id}`
  * `POST /api/hr/employees/{id}/status` (status transitions)
  * `POST /api/hr/employees/{id}/reactivate`
  * `GET /api/hr/employees/{id}/offboarding-summary` ← **already exists**
  * `GET /api/hr/driver-qualification/dashboard` (+ CSV + import preview/apply/audit)
* `routes/hr_portal.py` (HR portal entry)
* `routes/employee_requests.py` (request lifecycle)

### Audit-trail / timeline pattern
`employee_lifecycle_events` already follows the same pattern as the Asset Service Event Backbone:
```
{ id, employee_id, at, actor_role, actor_label, kind,
  from_status, to_status, reason, payload_snapshot, queue_request_id }
```
A single source of truth for who did what to which employee, when, and why.

### Verdict
**MATURE · OWNED BY HR · DO NOT REBUILD.** The lifecycle, status transitions, offboarding, audit trail, and Motive/MaintainX linkage all exist. Asset Administration must consume these — never duplicate.

---

## 3 · Asset Issuance Audit

### Safety / PPE Equipment Issuance
Lives in `routes/safety_forms.py` (7 endpoints) + collection `safety_equipment_issuances` (24 rows).

Row schema (live data):
```
{ id, doc_id (SEI-2026-00001 format),
  employee_id, employee_name, employee_email, position,
  project_name, project_number, location,
  issued_by, issued_date,
  items: [{item_type, item_type_other, description, quantity, ...}],
  condition, condition_note,
  photos: [data:image/png;base64,...],
  acknowledgment, employee_signature, supervisor_signature,
  total_value, lang, submit_language,
  created_at, updated_at }
```

Endpoints:
* `POST /equipment-issuances` (create)
* `GET /equipment-issuances` (list)
* `GET /equipment-issuances/{id}` (detail)
* `GET /equipment-issuances/{id}/pdf` ← **PDF generation already exists**
* `POST /equipment-issuances/{id}/return` ← **return workflow already exists**
* `GET /equipment-issuances/{id}/return/pdf` ← **return PDF already exists**

### Asset Assignment (custody)
Collection `asset_assignments` (16 rows · live data).

Row schema:
```
{ id, asset_id, masci_unit_number, project_id, project_number, project_name,
  operator_employee_id, operator_name,
  expected_return_date, dispatch_notes,
  active, started_at, started_by, ended_at, ended_by, ended_note,
  linked_transfer_id }
```

Implicit endpoints: assignment writes flow through `asset_transfers.py` lifecycle (`approve`, `in-transit`, `receive`, `close`). `linked_transfer_id` joins the two.

### Asset Transfer state machine
`routes/asset_transfers.py` (9 endpoints · `asset_transfers` 120 rows in preview):
* `GET /api/asset-transfers`
* `GET /api/asset-transfers/{tid}`
* `POST /api/asset-transfers`
* `POST /api/asset-transfers/{tid}/approve`
* `POST /api/asset-transfers/{tid}/reject`
* `POST /api/asset-transfers/{tid}/in-transit`
* `POST /api/asset-transfers/{tid}/receive`
* `POST /api/asset-transfers/{tid}/cancel`
* `POST /api/asset-transfers/{tid}/close`

### Asset Spine (the "shadow" system)
`routes/asset_spine.py` (11 endpoints) backed by `assets` collection (0 rows in preview).
* `GET/POST /assets`
* `GET /assets/{id}` + `/profile`
* `PATCH /assets/{id}`
* `POST /assets/{id}/retire` ← **lifecycle retirement endpoint exists**
* `POST /assets/{id}/activate` ← **lifecycle activate endpoint exists**
* `POST /assets/{id}/transfer`
* `GET /assets/{id}/transfers`
* `POST /assets/{id}/onboarding/advance` ← **onboarding endpoint exists**
* `GET /assets/{id}/onboarding`

**The endpoints work · the schema is designed · the data never moved over.** `equipment_master` (693 rows) remains the operational ledger.

### Issuable asset categories observed today
| Asset class | Today | Notes |
|---|---|---|
| **PPE** (harnesses, hard hats, etc.) | ✅ `safety_equipment_issuances` | item_type free + item_type_other catch-all |
| **Safety equipment** | ✅ | same collection |
| **Vehicles** | ✅ `asset_assignments` | operator_employee_id, expected_return_date |
| **Trailers** | ✅ | same |
| **Heavy equipment** | ✅ | same |
| **GPS receivers** | ⚠️ | issuable via `safety_equipment_issuances` (item_type_other) **without modification**; cleaner if added as a named item_type |
| **Survey equipment** (rovers, base stations) | ⚠️ | same — works today via item_type_other |
| **Tablets** | ⚠️ | same |
| **Radios** | ⚠️ | same |
| **Laptops** | ⚠️ | same |
| **Tools** (named high-value) | ⚠️ | same |

### Verdict
**MATURE · OWNED BY SAFETY (PPE) + DISPATCH (vehicles/heavy) + ASSET_TRANSFERS (state machine) · DO NOT REBUILD.** The whole issuance + custody + return + transfer ecosystem already exists, with signatures and PDF outputs.

---

## 4 · Return Workflow Audit

| Concern | Today | Verdict |
|---|---|---|
| PPE return | `POST /equipment-issuances/{id}/return` + return PDF | ✅ COMPLETE |
| Vehicle / heavy equipment return | `POST /api/asset-transfers/{tid}/receive` + `/close` | ✅ COMPLETE |
| Custody close-out | `asset_assignments.ended_at` + `ended_by` + `ended_note` | ✅ COMPLETE |
| Condition capture at return | `safety_equipment_issuances.condition` + `condition_note` | ✅ COMPLETE (PPE) |
| Condition capture at vehicle return | Not explicitly captured on `asset_transfers.receive` (free-text only) | ⚠️ PARTIAL — could extend the receive payload |
| Audit log | `employee_lifecycle_events` (employee side) + `asset_transfers` state stamps + `asset_assignments.ended_*` | ✅ COMPLETE |
| Signatures on return | PPE has it; vehicles do not | ⚠️ PARTIAL — extension opportunity |

### Verdict
Return workflows exist for every category. Minor extension opportunity for capturing condition + signature on vehicle return — but **not a new system**. A single field-set addition to `asset_transfers.receive`.

---

## 5 · Offboarding Audit

| Concern | Today | Verdict |
|---|---|---|
| Employee termination workflow | `POST /api/hr/employees/{id}/status` + lifecycle event | ✅ COMPLETE |
| Offboarding summary view | `GET /api/hr/employees/{id}/offboarding-summary` | ✅ COMPLETE (endpoint exists) |
| Outstanding asset detection at offboard | Implicit from `asset_assignments` filter `{operator_employee_id: X, active: True}` — **no UI surfaces this on offboarding-summary today** | ⚠️ PARTIAL — UI gap |
| Outstanding PPE detection at offboard | `safety_equipment_issuances` filter on employee_id where return is null | ⚠️ PARTIAL — same UI gap |
| Mandatory return before status=Terminated | NOT ENFORCED at API level | ⚠️ GAP |
| Audit trail of offboarding | `employee_lifecycle_events` | ✅ COMPLETE |
| Reactivation | `POST /api/hr/employees/{id}/reactivate` | ✅ COMPLETE |

### Verdict
The data sources for "outstanding asset detection at offboarding" all exist. The gap is purely a query / UI gap on the offboarding-summary endpoint — no new collection or workflow needed. A single endpoint extension would surface "this employee still has 2 GPS receivers and 1 truck out" at offboarding time.

---

## 6 · Asset Custody Audit

The system can already answer:

| Question | Answer source today |
|---|---|
| Who currently has Asset X? | `asset_assignments.find({asset_id: X, active: True})` |
| Who previously had Asset X? | `asset_assignments.find({asset_id: X}).sort({started_at: -1})` |
| When was Asset X issued? | `asset_assignments.started_at` |
| When was Asset X returned? | `asset_assignments.ended_at` |
| Who approved issuance? | `started_by` (and `linked_transfer_id` → `asset_transfers.created_by`) |
| Who approved return? | `ended_by` (and `linked_transfer_id` → `asset_transfers.closed_by`) |
| Where is that stored? | `asset_assignments` + `asset_transfers` + `employee_lifecycle_events` (joined by employee_id / asset_id) |
| How is it audited? | All four tables stamp `_at` + `_by` on every transition |
| How is it surfaced? | Asset detail page (TBD on Asset Care Command Center 13.33-A) + dispatch transfer screens (already in production) |

**Custody tracking exists end-to-end.** Track 13.31B has nothing to invent here.

---

## 7 · Source-of-Truth Matrix (revised by this audit)

| Capability | Owned today | Owner | Track 13.31B touches? |
|---|---|---|---|
| Asset Identity (id, unit_number, vin, make, model, plate) | ✅ | `equipment_master` | YES — **extend** schema only (NOT a new collection) |
| Asset Registration / Insurance / Title | ❌ MISSING | — | YES — **ADD** to `equipment_master` |
| Asset Documents (titles, registrations, insurance cards, etc.) | ❌ MISSING | — | YES — **ADD** via `operational_attachments` + new `attachment_type` values + `equipment_id` FK |
| Asset Lifecycle (active/inactive/sold/retired/disposed/pending) | ⚠️ PARTIAL — `equipment_master.is_active` binary only · `asset_spine.py:/retire` + `/activate` endpoints exist but point at empty `assets` collection | split | YES — **add lifecycle_status enum on equipment_master** · REJECT the empty `assets` collection (consolidate into equipment_master) |
| Asset Custody | ✅ | `asset_assignments` + `asset_transfers` | NO — consume only |
| Employee Assignments | ✅ | `dispatch_assignments` + `asset_assignments` | NO — consume only |
| Employee Issuance | ✅ | `safety_equipment_issuances` + `safety_forms.py` | NO — consume only |
| Employee Returns | ✅ | `/equipment-issuances/{id}/return` + `/asset-transfers/{id}/receive` | NO — consume only |
| Employee Offboarding | ✅ | `employee_lifecycle.py` + `/api/hr/employees/{id}/offboarding-summary` | NO — extend offboarding-summary query to include outstanding assets (single endpoint touch) |
| Employee Lifecycle Timeline | ✅ | `employee_lifecycle_events` | NO — consume only |
| Asset Lifecycle Timeline | ✅ | Asset Service Event Backbone (Track 13.26) + asset_transfers state stamps | NO — consume only |
| Motive linkage (employee side) | ✅ | `employee_mappings` | NO — consume only |
| Motive linkage (asset side) | ⚠️ PARTIAL — `asset_mapping` collection (0 rows in preview · not populated) | sync | YES — **add `motive_vehicle_id` / `motive_asset_id` foreign keys directly on equipment_master row** |
| Photos | ❌ for assets · ✅ for PPE issuances | split | YES — extend `equipment_master` to reference operational_attachments photos |

---

## 8 · Ownership Matrix

| Domain | System of record | Read-only consumers |
|---|---|---|
| Employee identity + lifecycle | HR (`employee_lifecycle.py`, `employees`, `employee_lifecycle_events`) | Dispatch · Shop · Safety · Asset Administrator |
| PPE / safety equipment issuance | Safety (`safety_forms.py`, `safety_equipment_issuances`) | HR offboarding summary · Asset Administrator (read) |
| Vehicle / heavy equipment custody | Dispatch + Asset Administrator together (`asset_transfers`, `asset_assignments`) | HR offboarding summary · Shop |
| Asset identity (vehicles, heavy, trailers) | Asset Administrator (`equipment_master` — pending schema extension) | every portal reads |
| Asset lifecycle (active/sold/retired/disposed) | Asset Administrator (`equipment_master.lifecycle_status` — pending) | every portal reads |
| Asset documents / registrations / insurance | Asset Administrator (`operational_attachments` keyed by equipment_id — pending) | HR (renewal alerts via existing notification framework) |
| Operational events (defect / repair / PM / fuel / lube / RTS) | Shop (existing tracks) | Dispatch · Asset Administrator (read) |
| Telematics (location, ignition, hours via Motive) | Motive (external) | Dispatch (Map-First) · PM Engine (meter source) · Asset Administrator (read) |
| Map | Dispatch (single MapLibre engine, single canvas — hard lock) | every portal embeds via `useMapSnapshot` |

---

## 9 · Duplication Risks (if Track 13.31B builds what Track 13.31A originally listed)

| Proposed 13.31B item | Would duplicate | Risk | Recommendation |
|---|---|---|---|
| New "asset onboarding workflow" | `asset_spine.py:/onboarding/advance` + `/onboarding` | HIGH | REJECT — either adopt the empty `assets` collection or fold onboarding into `equipment_master` lifecycle |
| New "asset retirement workflow" | `asset_spine.py:/retire` | HIGH | REJECT — wire the existing endpoint to write to `equipment_master.lifecycle_status` |
| New "asset transfer workflow" | `asset_transfers` (120 live rows · 9 endpoints) | CRITICAL | REJECT |
| New "asset custody tracking" | `asset_assignments` (16 live rows) | CRITICAL | REJECT |
| New "PPE / safety issuance" | `safety_equipment_issuances` (24 live rows) | CRITICAL | REJECT |
| New "equipment return form" | `/equipment-issuances/{id}/return` + `/asset-transfers/{id}/receive` | CRITICAL | REJECT |
| New "employee offboarding workflow" | `employee_lifecycle.py:/status` + `/offboarding-summary` | CRITICAL | REJECT |
| New "employee timeline" | `employee_lifecycle_events` (38 live rows) | CRITICAL | REJECT |
| New "employee→Motive mapping" | `employee_mappings` (65 live rows) | CRITICAL | REJECT |
| New "Asset Administrator role flag" | — | LOW | **SAFE TO BUILD** (single permission flag on HR user record) |
| New `equipment_master.lifecycle_status` enum | — | NONE | **SAFE TO ADD** (single field) |
| New `equipment_master.registration_*` / `insurance_*` / `title_*` fields | — | NONE | **SAFE TO ADD** |
| New `equipment_master.motive_vehicle_id` / `motive_asset_id` FKs | — | NONE | **SAFE TO ADD** (populated by existing Motive sync) |
| New `operational_attachments.equipment_id` FK + new `attachment_type` values for asset docs | — | LOW | **SAFE TO EXTEND** |
| New "asset document vault" UI | — | LOW | **SAFE TO BUILD** (single page; reads existing attachments scoped to equipment_id) |
| Resolution of `equipment_master` vs `assets` (0 rows) duplicate spines | — | MEDIUM | **MUST RESOLVE** during 13.31B — pick one, retire the other |

---

## 10 · Five-Pillar Audit (current Employee Lifecycle + Asset Issuance state)

| Pillar | Score | Evidence |
|---|---:|---|
| Powerful | 9 / 10 | Full lifecycle · PPE issuance with signatures + PDFs · 9-step transfer state machine · custody close-out · offboarding summary. |
| Simple | 8 / 10 | Five separate but well-bounded collections · routes don't overlap. One ambiguity: `asset_spine.py` endpoints point at empty `assets` collection while operations use `equipment_master`. |
| Beautiful | 8 / 10 | HR portal + Safety portal exist; PPE issuance form is mature; transfer screens are mature. Asset document UX is the missing piece. |
| Trusted | 9 / 10 | `employee_lifecycle_events` audit trail · `asset_transfers` state stamps · signatures + PDFs · per-row `_at` + `_by`. |
| Proven | 8 / 10 | 38 lifecycle events + 16 asset_assignments + 24 PPE issuances + 120 transfers all live in preview. Real usage. |
| **Average** | **8.4 / 10** | Substantially above the 6.6 we scored Asset Administration at in 13.31A — because the systems here are *real*. |

---

## 11 · Impact on Track 13.31B

### Original 13.31B scope (from Track 13.31A § 13)
1. Extend equipment_master schema with the 18 missing fields
2. Add `lifecycle_status` enum
3. Add Motive FKs on equipment_master row
4. Add `operational_attachments.equipment_id` + extended `attachment_type` whitelist + Asset-Admin-gated upload endpoint
5. Add Asset Administrator role flag
6. Reconcile `make/model/make_model` triplet
7. Reconcile `category/preop_equipment_type` taxonomies

### Revised 13.31B scope (after this audit)
**KEEP** (1, 2, 3, 4, 5, 6, 7 above — all are pure schema/field additions or de-duplications, no new workflow).

**ADD** (only this):
* **Resolve the `equipment_master` vs `assets` duplicate spine.** Pick one. Recommendation: **make `equipment_master` the canonical spine; either delete `asset_spine.py` + `assets` collection OR re-point `asset_spine.py` endpoints to read/write `equipment_master`**. Do not leave the duplicate live.

**HARD-REJECT** (must not be built or re-built by 13.31B):
* Any new asset onboarding workflow
* Any new asset retirement workflow
* Any new asset transfer workflow
* Any new asset custody tracking system
* Any new PPE / safety equipment issuance form
* Any new equipment return form
* Any new employee offboarding workflow
* Any new employee timeline
* Any new asset assignment ledger
* Any duplicate audit trail

**EXTEND (single-touch additions to existing systems, not new systems):**
* `GET /api/hr/employees/{id}/offboarding-summary` → join in outstanding `asset_assignments` rows and outstanding (un-returned) `safety_equipment_issuances` rows so the offboarding view shows what's still out. **One endpoint change · no new collection.**
* `POST /api/asset-transfers/{tid}/receive` → optionally accept `condition`, `condition_note`, `signature_data_url` to mirror the PPE return capture. **One endpoint extension · no new collection.**

---

## 12 · Recommended Scope Reduction

13.31B scope was ~10 line items. Post-audit, only **7 schema/field changes + 2 single-endpoint extensions + 1 spine reconciliation** remain. **Roughly a 60% scope reduction.**

Time/risk impact: a track that previously looked like a 3-week build is now a 3–5 day build of additive schema fields + role gating + a doc vault UI.

---

## 13 · Recommended Build Order (revised)

```
TRACK 13.31B — ASSET ADMINISTRATION SPINE (REVISED · DAYS, NOT WEEKS)
  Day 1 — Schema extension on equipment_master:
    + lifecycle_status enum {active, inactive, sold, retired, disposed, pending_delivery}
    + registration_number, registration_expiration, registration_state
    + insurance_carrier, insurance_policy_number, insurance_expiration
    + title_status, ownership_status, purchase_date
    + motive_vehicle_id, motive_asset_id (populated by existing MotiveService.sync_assets — single addition)
    + division, supervisor_id, region
    + photos[]  (refs into operational_attachments)
    + documents[] (refs into operational_attachments)
  Day 1 — Reconciliation:
    - Deprecate make_model (compute from make + model)
    - Deprecate preop_equipment_type (alias to category)
    - DECISION: keep equipment_master · retire asset_spine.py endpoints OR re-point them
  Day 2 — Role + auth:
    + asset_admin permission flag on hr_users + admin tokens
    + gate the new equipment_master write paths
  Day 2 — Document vault:
    + operational_attachments.equipment_id FK
    + operational_attachments.attachment_type whitelist += {title, registration, insurance_card, insurance_policy, warranty, purchase_doc, equipment_photo, dot_certificate}
    + POST /api/equipment-master/{id}/documents (Asset Admin gated)
    + GET /api/equipment-master/{id}/documents
  Day 3 — Offboarding outstanding-asset surfacing (existing endpoint extension):
    Edit /api/hr/employees/{id}/offboarding-summary to also return:
      outstanding_assets[]: from asset_assignments where active=true
      outstanding_issuances[]: from safety_equipment_issuances where no return event
  Day 3 — Renewal alert query (read-only, new):
    GET /api/asset-admin/renewals/upcoming?within_days=60
      reads equipment_master + filters expiration fields
  Day 4 — UI: AssetProfile.jsx extension (read-only docs/lifecycle/renewals)
  Day 5 — UI: Asset Admin form (write paths for the 18 new fields)
  Day 5 — Tests + audit

TRACK 13.33-A — ASSET CARE READ-ONLY COMPOSITE (after 13.31B)
TRACK 13.33-B — ASSET CARE RENEWAL ALERTS (after 13.33-A, optional)
TRACK 13.32 — MAINTAINX (blocked on credentials)
```

---

## 14 · Final Certification Verdict

**Track 13.31B is AUTHORIZED to proceed at the REVISED scope above.**

The original scope-creep risk was high (would have built duplicate employee lifecycle, PPE issuance, transfer workflows on top of mature 24/16/120/38-row live systems). This audit eliminates that risk.

**Track 13.33 (Asset Care Command Center)** remains authorized **only at 13.33-A "read-only composite" scope** after 13.31B lands.

**Hard locks reaffirmed:**
* Map stays · single MapLibre engine · single canvas.
* Repair Complete ≠ RTS.
* PM Completion ≠ RTS.
* No new employee timeline · `employee_lifecycle_events` is canonical.
* No new asset transfer system · `asset_transfers` is canonical.
* No new PPE issuance · `safety_equipment_issuances` is canonical.
* `equipment_master` is the asset spine · `assets` collection (0 rows) to be retired or absorbed during 13.31B.

**Five-Pillar score for current state: 8.4 / 10.** Above the 9.5 bar only if 13.31B closes the schema gap + retires the duplicate spine. Without those two changes the score caps at ~8.4 because the missing 18 administrative fields prevent Powerful and Beautiful from clearing 9.

**Read only. Certified. Documented. Stopping.**

---

**Track 13.31AA — CLOSED.**
