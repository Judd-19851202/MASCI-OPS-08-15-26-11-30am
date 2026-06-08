# DR-AUDIT-001 · DAILY REPORT CONSTITUTIONAL AUDIT
**ForgedOps / MASCI Trench Safety & Dispatch Operations Platform**
**Filed:** 2026-06-08
**Discipline:** OMEGA · EVIDENCE-ONLY · NO CODE
**Status:** 🟡 Audit complete. **Zero feature implementation performed.** 12 actionable recommendations identified, every one routed through the 5-pillar gate.

---

## 0 · Scope Statement

This is a forensic audit of the Daily Report system. It identifies what exists, why it exists, who uses it, what is missing, what is duplicated, what can be automated (from Motive / FleetWatcher / MaintainX / jobs_master / employees), and what must never be automated. Every recommendation must pass **Powerful · Simple · Beautiful · Trusted · Proven** plus the additional question:

> **Can this information already be obtained from another system?**

Daily Report is a 9-step field contract executed under the doctrine `ODR_SIMPLICITY_TEST_DOCTRINE.md`:

> _"Would a foreman complete this on a phone, standing in mud, wearing gloves, at 5:30 PM, after a 12-hour shift?"_

Nothing in this audit can violate the 9-step lock.

---

## 1 · PHASE 1 · COMPLETE INVENTORY (Daily Report Master Inventory)

### 1.1 · Code surface inventory (evidence files)

| Layer | File | Lines |
|---|---|---|
| **Form (foreman)** | `frontend/src/pages/NewDailyReport.jsx` | 2,291 |
| **Schema / defaults** | `frontend/src/lib/dailyReportSchema.js` | 107 |
| **Detail (read)** | `frontend/src/pages/ViewDailyReport.jsx` | 678 |
| **Admin dashboard** | `frontend/src/pages/DailyReportsDashboard.jsx` | 228 |
| **HR portal view** | `frontend/src/pages/HrDailyReports.jsx` | 422 |
| **Safety portal view** | `backend/routes/safety_portal/daily_reports.py` | 75 |
| **Backend CRUD** | `backend/routes/daily_reports.py` | 566 |
| **Lifecycle state machine** | `backend/routes/daily_report_lifecycle.py` | 257 |
| **State definitions** | `backend/lib/workflow_state_machine.py` (DR block) | ≈75 |
| **Excavation tie-in** | `frontend/src/components/trench/DailyReportExcavationActivity.jsx` | 220 |
| **Field Submitter Identity (FSI)** | `backend/lib/field_submitter_identity.py` + `routes/field_revision.py` | — |
| **Audit footer / SHA256** | `backend/routes/daily_reports.py` lines 150–166, 454–484 | — |

### 1.2 · Section / Field Master Matrix

11 numbered sections in the form. Default-visible: **11**. Sections 05/06/07/08/09 collapsed but always present (`CollapseCard` pattern).

| # | Section | Field | Type | Req? | Validation | Visibility (form) | Storage | Auto-source candidate |
|---|---|---|---|---|---|---|---|---|
| 01 | Report Information | `project_name` | text | ✅ | min 1 char | always | DR doc | `jobs_master.project_name` (already on JobPicker) |
| 01 | " | `project_number` | text | ⚪ | — | always | DR doc | `jobs_master.project_number` (already on JobPicker) |
| 01 | " | `location` | text | ✅ | — | always | DR doc | `jobs_master.location` + GPS reverse-geocode |
| 01 | " | `report_date` | date | ✅ | YYYY-MM-DD | always | DR doc | `today()` (already auto-default) |
| 01 | " | `report_number` | text | ⚪ | DR-YYYYMMDD-NNN | always | DR doc | `GET /api/daily-reports/next-number` (already wired) |
| 01 | " | `prepared_by` | text (free) | ✅ | — | always | DR doc | **Last submitter on this `project_number`** (Phase 10D candidate, not auto-applied) |
| 01 | " | `superintendent` | text (free) | ⚪ | — | always | DR doc | `jobs_master.superintendent` ❌ NOT WIRED today (gap F-A) |
| 02 | Weather | `weather_summary` | text | ⚪ | — | always | DR doc | Weather API + GPS (already auto-filled) |
| 02 | " | `weather_snapshots[]` | array | ⚪ | — | always | DR doc | Weather API hourly fetch |
| 02 | " | `gps_lat`, `gps_lng`, `gps_accuracy` | geo | ⚪ | — | hidden | DR doc | Browser geolocation (already wired) |
| 03 | General Information | `schedule_delays` | Yes/No | ⚪ | enum | always | DR doc | — manual signal |
| 03 | " | `schedule_delays_notes` | textarea | ⚪ | — | conditional | DR doc | Replaced by structured `constraints[]` rows (V.2 Wave-1B) |
| 03 | " | `weather_impact` | Yes/No | ⚪ | enum | always | DR doc | Weather API delta detection |
| 03 | " | `weather_impact_notes` | textarea | ⚪ | — | conditional | DR doc | Same |
| 03 | " | `safety_incidents_today` | Yes/No | ⚪ | enum | always | DR doc | — manual signal |
| 03 | " | `injuries_reported` | Yes/No | ⚪ | enum | always | DR doc | — manual signal |
| 03 | " | `incident_notes` | textarea | ⚪ | required if either YES | conditional | DR doc | — manual narrative |
| 03 | " | `safety_notified` | Yes/No | ⚠️ gated | required if incident YES | gated | DR doc | Cross-reference with `incidents` collection |
| 03 | " | `safety_contact_person` | text | ⚠️ gated | — | gated | DR doc | `safety_users` directory (could resolve) |
| 03 | " | `safety_contact_time` | time | ⚠️ gated | HH:MM | gated | DR doc | — manual |
| 03 | " | `incident_report_filled` | Yes/No | ⚠️ gated | — | gated | DR doc | Cross-reference with `incidents` collection |
| 03 | " | `incident_report_time` | time | ⚠️ gated | — | gated | DR doc | — manual |
| 03 | " | `general_notes` | textarea | ⚪ | — | always | DR doc | — manual narrative |
| 03 | " | **`excavation_activity_today`** | Yes/No | ⚪ | **enforces linked_excavation_ids if YES** (422) | always | DR doc | Cross-reference with `trench_excavations` |
| 03 | " | `linked_excavation_ids` | string[] | ⚠️ gated | required if excavation YES | gated | DR doc | Could surface candidates by project_number |
| 04 | MASCI Crews | `masci_crews[]` | repeat block | ✅ | crew_count ≥ 1 (soft via Section 04 banner) | always | DR doc | **Last DR for same project_number** (PreviousReportSuggestions exists but requires tap) |
| 04 | " (per row) | `name, trade, start_time, lunch_minutes, stop_time, hours, work_performed` | mixed | ⚪ | hours auto-calc | per row | DR doc | `employees` directory; Motive driver in-vehicle timeline candidate |
| 05 | Subcontractors | `subcontractors[]` | repeat (collapsed) | ⚪ | — | collapsed | DR doc | Yesterday's DR; vendors directory |
| 05 | " | per row: `company, trade, foreman, count, hours, work_performed, attachment_note, photos[]` | — | — | — | — | — | `suppliers/vendors` collection |
| 06 | Visitors | `visitors[]` | repeat (collapsed) | ⚪ | — | collapsed | DR doc | — manual |
| 06 | " | per row: `name, company, time_in, time_out, purpose` | — | — | — | — | — | — |
| 07 | Equipment | `equipment[]` | repeat (collapsed) | ⚪ | — | collapsed | DR doc | **Motive `assets` ON-SITE filter by GPS** + yesterday's DR |
| 07 | " | per row: `description, hours_used, time_delivered, time_removed, notes` | — | — | — | — | — | Motive utilization · MaintainX work-order linkage |
| 08 | Materials | `materials[]` | repeat (collapsed) | ⚪ | — | collapsed | DR doc | **FleetWatcher load tickets** (future) · supplier directory |
| 08 | " | per row: `description, quantity, unit, supplier, ticket_number, notes, ticket_photos[]` | — | — | — | — | — | FleetWatcher API |
| 09 | Activity / Production Log | `activities[]` | repeat (collapsed) | ⚪ | — | collapsed | DR doc | Yesterday's DR copy-forward |
| 09 | " | per row: `activity, percent_complete, station_from, station_to, notes` | — | — | — | — | — | — |
| 09b | Production Quantities (V.2 Wave-1B) | `production[]` | repeat (collapsed) | ⚪ | unit ∈ {LF, SY, CY, TON, EA, ACRE, OTHER} | collapsed | DR doc · structured | — operator-authored |
| 09b | " | per row: `description, quantity, unit, custom_unit_label, station_from, station_to, notes` | — | — | — | — | — | — |
| 10 | Delays / Extra Work (V.2 Wave-1B) | `constraints[]` | repeat (collapsed) | ⚪ | constraint_type ∈ {11-enum} | collapsed | DR doc · structured | Weather API · Motive (equipment downtime) · FleetWatcher (trucking) |
| 10 | " | per row: `constraint_type, hours_impact, notes` + server-derived `may_require_rfi`, `may_affect_schedule` | — | — | — | — | — | — |
| 10b | Distribution List | `distribution_list[]` | email[] | ⚪ | max 20 | sign-off | DR doc | `jobs_master.pm_email` + `co_pm_emails` |
| 10 (photos) | Photos | `photos[]` | photo[] | ✅ | min 6 (`photo_min`) | always | DR doc · photo refs | Mirrored to `job_photos` library |
| 11 | Sign-Off | `prepared_by_signature` | signature | ✅ | — | always | DR doc | — manual |
| 11 | " | `superintendent_signature` | signature | ⚪ | — | always | DR doc | — manual |

### 1.3 · Hidden / system fields

| Field | Stamped by | Purpose | Pillar |
|---|---|---|---|
| `id` (UUID) | server on insert | canonical id | ✅ Trusted |
| `doc_id` (DR-YYYY-NNNNN) | `doc_ids.ensure_doc_id()` | human-readable continuity | ✅ Trusted |
| `created_at` (ISO UTC) | server | audit | ✅ Trusted |
| `audit_envelope_sha256` | server (V.2 Wave-1A) | tamper detection · PDF footer | ✅ Trusted |
| `lifecycle_state` | server (default OPEN) | OC-002 state machine | ✅ Trusted |
| `lifecycle_updated_at`, `lifecycle_pending_review_at`, `lifecycle_reviewed_at`, `lifecycle_closed_at` | server | timeline | ✅ Trusted |
| `daily_report_links` (mirror on `trench_excavations`) | server | two-way excavation linkage | ✅ Trusted |
| `language` | client | EN/ES at submit | ✅ Trusted |

### 1.4 · Related modules touched at submit

| Module | What happens | File |
|---|---|---|
| `trench_excavations` | Reverse-link stamped on every linked excavation (`daily_report_links[]`) | `daily_reports.py:286-303` |
| `job_photos` | Photos mirrored read-only to library | `daily_reports.py:304-309` |
| `auto_email` scheduler | PDF delivery queued (PM + co-PM + distribution list) | `daily_reports.py:310` |
| `field_submitter_identity` (iter452.5) | Tier-1 identity binding · supports kickback `/revise/{token}` flow | `daily_reports.py:312-332` |
| `audit_envelope_sha256` | SHA256 computed for legal continuity | `daily_reports.py:280` |
| `idempotency` | Idempotency key from `Idempotency-Key` header — preserves submit if tab reloads | `daily_reports.py:262` |
| `R2 photo_storage` | Inline base64 → R2 refs on the same write path | `daily_reports.py:186-232` |

### 1.5 · Coaching panels inventory

| Surface | Panel | Trigger |
|---|---|---|
| Form header | `HelpTipBlock formKey="daily-report"` | always · with counter |
| Section 04 | `HelpTipBlock formKey="daily-report.crew"` | always |
| Section 04 | "Crew identity linkage" coaching | iter360 · always |
| Section 03 | Safety escalation amber/red block | YES on accident OR injury |
| Section 07 | `HelpTipBlock formKey="daily-report.equipment"` | always |
| Section 08 | `HelpTipBlock formKey="daily-report.materials"` | always |
| Section 09 | `HelpTipBlock formKey="daily-report.narrative"` | always |
| Section 10 (Photos) | `HelpTipBlock formKey="daily-report.photos"` | always |
| Excavation tile | `DailyReportExcavationActivity` "Coaching, not punishment" amber strip | always (flagged in audit as bloat) |
| Restore prompt | `CrewSetupRestorePrompt` | when localStorage crew memory snapshot exists |

---

## 2 · PHASE 2 · FIELD VALUE ANALYSIS

For every field a KEEP / MODIFY / REMOVE / AUTO-POPULATE / INVESTIGATE verdict.

| Field | Verdict | Rationale | Pillars touched |
|---|---|---|---|
| `project_name` / `project_number` | **AUTO-POPULATE** (already partial) | `JobPicker` already pulls from `jobs_master`. Foreman re-types nothing today. ✅ | Simple · Trusted |
| `location` | **AUTO-POPULATE** | `jobs_master.location` + GPS reverse-geocode. Today free-text — fragility risk. | Simple · Trusted |
| `report_date` | **KEEP** (already auto) | — | — |
| `report_number` | **KEEP** | Backend mints. Foreman sees, doesn't author. | — |
| `prepared_by` | **MODIFY → directory-bound** | Free text today. Two foremen with same first name produce indistinguishable strings (DR_OWNERSHIP_AUDIT F2). | Trusted (BREAKS today) |
| `superintendent` | **AUTO-POPULATE from `jobs_master.superintendent`** | Currently NOT wired (DR_SIMPLIFICATION_AUDIT §4 gap F-A). | Trusted · Simple |
| `weather_summary` / `weather_snapshots` | **KEEP** (auto) | Weather API + GPS already populates. | — |
| `schedule_delays` (Yes/No toggle) | **MODIFY → replaced by structured `constraints[]` gate** | V.2 Wave-1B already implemented the structured rows. The Yes/No is now a duplicate signal (audit §2 duplicate flag). | Simple |
| `schedule_delays_notes` | **REMOVE** (post-V.2) | Replaced by structured constraint rows. Triple-duplicated. | Simple |
| `weather_impact` / `weather_impact_notes` | **MODIFY → consolidate** | YES + missing weather-constraint row = the only meaningful state. Free text is duplicate. | Simple |
| `safety_incidents_today` / `injuries_reported` | **KEEP** | Critical gate — drives the stop-the-line safety escalation block. Field-authored signal, irreplaceable. | Powerful · Trusted |
| `incident_notes` | **KEEP (conditional)** | Narrative-only when YES. Required. | Trusted |
| `safety_notified` / `safety_contact_person` / `safety_contact_time` / `incident_report_filled` / `incident_report_time` | **KEEP · INVESTIGATE cross-reference** | These ARE the stop-the-line block. The opportunity is to surface a real `incidents` collection link when filled. | Powerful · Trusted |
| `general_notes` | **KEEP** | Foreman's narrative escape valve. Operationally valuable. | Powerful |
| `excavation_activity_today` + `linked_excavation_ids` | **KEEP** (Phase 10A-B gate) | Hard 422 enforces the trench-safety chain. Critical. | Powerful · Trusted |
| `masci_crews[]` | **MODIFY → auto-prefill from yesterday's DR, foreman confirms** | Currently requires tap on PreviousReportSuggestions. DR_SIMPLIFICATION_AUDIT §3 calls for silent auto-apply with undo. | Simple |
| `masci_crews[*].name` | **MODIFY → directory-bound (Phase 1B candidate)** | Free text today causes payroll variance ambiguity. iter452.5 already partially addresses via FSI. | Trusted |
| `masci_crews[*].hours` | **KEEP** (auto-calc from start/lunch/stop) | Already auto-computed. | Simple · Trusted |
| `subcontractors[]` | **KEEP · MODIFY** | Field-authored. Could pre-suggest from suppliers directory + recent subs. | Simple |
| `subcontractors[*].photos[]` (sub flagger tickets) | **KEEP** | Critical for backup/dispute. | Trusted |
| `visitors[]` | **KEEP** | Inspector / DOT / owner visits — irreplaceable provenance. | Powerful |
| `equipment[]` | **MODIFY → cross-reference Motive** | **🔥 Highest auto-capture value.** Motive owns GPS + equipment + on-site geofencing. Foreman SHOULD verify, not enumerate. | Simple · Trusted · Beautiful |
| `materials[]` | **KEEP · INVESTIGATE FleetWatcher** | FleetWatcher owns load tickets / hauling / tonnage. Could pre-populate ticket rows. | Simple · Trusted |
| `activities[]` (legacy free-text) | **KEEP** (V.2 plan: gradually shift weight to `production[]`) | Coexists with `production[]`. Operator-authored narrative — has real value. | Powerful |
| `production[]` (V.2 Wave-1B) | **KEEP** | Structured, optional, doesn't break the 9-step contract. Already certified. | Powerful · Trusted |
| `constraints[]` (V.2 Wave-1B) | **KEEP** | Structured. Drives the PM exposure tile signal-only. | Powerful · Trusted |
| `photos[]` (min 6) | **KEEP** | Photo doctrine is sacrosanct. R2-backed. | Trusted |
| `prepared_by_signature` / `superintendent_signature` | **KEEP** | Legal weight. Hashed into the SHA256 audit envelope. | Trusted |
| `distribution_list[]` | **KEEP** | PM + GC + DOT + insurance email targets. | Powerful |
| `audit_envelope_sha256` | **KEEP** | Continuity + tamper detection. | Trusted |
| `lifecycle_state` | **KEEP** | OC-002 state machine. PM/Admin/Safety review queue. | Trusted |

---

## 3 · PHASE 3 · VISIBILITY MATRIX

Where each role currently sees Daily Reports:

| Surface | Foreman | Super | PM | Dispatch | Shop | Safety | HR | Exec |
|---|---|---|---|---|---|---|---|---|
| `/daily/submit` (public · authoring) | ✅ | ✅ | — | — | — | — | — | — |
| `/daily/new` (admin authoring) | — | — | — | — | — | — | — | ✅ |
| `/daily-reports` (admin listing) | — | — | ✅ (PM-scoped) | — | — | ✅ | — | ✅ |
| `/daily/:id` (read) | — | — | ✅ (PM-scoped) | — | — | ✅ (flagged-only) | — | ✅ |
| `/admin/governance` Draft Health tile | — | — | — | — | — | — | — | ✅ |
| `/hr/daily-reports` (HR read-only) | — | — | — | — | — | — | ✅ | — |
| `/safety/daily-reports` (flagged-only) | — | — | — | — | — | ✅ | — | — |
| `/pm/daily-reports/:id` (PM detail) | — | — | ✅ (their projects) | — | — | — | — | — |
| Lifecycle transition (OPEN → PENDING_REVIEW) | ✅ via submit | — | ✅ | — | — | — | — | ✅ |
| Lifecycle PENDING → REVIEWED / CLOSED | — | — | — | — | — | — | — | ✅ (admin only) |
| PDF + audit footer | ✅ via email | ✅ | ✅ | — | — | ✅ | ✅ | ✅ |
| `/admin/payroll-variance` (consumer) | — | — | ✅ | — | — | — | ✅ | ✅ |
| `/revise/{token}` (field submitter kickback) | ✅ via signed email | — | — | — | — | — | — | — |
| `daily-reports/exposure-signals` PM tile (V.2 Wave-1B · signal-only) | — | — | ✅ | — | — | — | — | ✅ |

### 3.1 · Visibility gaps identified

| Gap | Pillar | Severity |
|---|---|---|
| **Dispatch sees nothing** | Powerful | 🟡 MEDIUM — Dispatch knows where crews/trucks are; would benefit from "Was Crew X actually on Job Y today?" cross-check. |
| **Shop sees nothing** | Powerful | 🟡 MEDIUM — Shop owns equipment lifecycle; the DR equipment list is reality vs MaintainX state. A Shop view of "equipment that showed up on a DR but is OOS in MaintainX" would close the loop. |
| **Field Leadership has no DR surface today** | Powerful | 🟢 LOW — FL operates upstream of the form. No clear value. |
| **Foreman cannot re-access prior submissions without login** | Trusted | 🟡 MEDIUM — F4 of `DAILY_REPORT_OWNERSHIP_AUDIT.md`. Partially addressed by FSI `/revise/{token}` but only when kicked back. |
| **HR cannot see "labor variance" delta** | Powerful | 🟡 MEDIUM — HR can read but the variance computation lives separately. |

### 3.2 · Information nobody uses (RED — investigate removal)

| Field | Evidence of zero use |
|---|---|
| `weather_snapshots[]` granular hourly array | Stored but never rendered on detail page; never consumed by downstream. **REMOVE** candidate. |
| `gps_accuracy` | Stored; not displayed; not queried. **REMOVE**. |
| `schedule_delays_notes` post-V.2 | Replaced by `constraints[]`. Triple duplication. **REMOVE** (after one DR cycle to confirm). |
| `weather_impact_notes` post-V.2 | Same. **REMOVE**. |

### 3.3 · Information duplicated across modules

| Concept | Locations | Recommendation |
|---|---|---|
| "Crew on site today" | DR `masci_crews[]` · Dispatch board · Motive driver telemetry | **Single source** = DR + Dispatch fuse; Motive verifies (see §5) |
| "Equipment on site today" | DR `equipment[]` · Motive `assets` GPS-on-job · MaintainX work-order assignment | **Motive is the source-of-truth for presence**; DR is the foreman's confirmation |
| "Project number" | DR · jobs_master · dispatch_assignments · trench_excavations · safety_meetings · jhas · incidents | OK — common key across modules |
| "Material delivered" | DR `materials[]` · FleetWatcher load tickets | FleetWatcher is canonical for hauling. DR is the foreman's confirmation. |
| "Incident today YES" | DR `safety_incidents_today` · `incidents` collection | **Two separate writes today.** Should be linked at submit if incident report has been filed. |
| "Excavation activity today" | DR `excavation_activity_today` · `trench_excavations` | ✅ Already two-way linked (Phase 10A-B). Best-in-class. |

---

## 4 · PHASE 4 · OPERATIONAL WORKFLOW MAP

```
CREATION ──────► SUBMISSION ──────► REVIEW ──────► CONSUMPTION ──────► REPORTING ──────► ARCHIVING
   ↓                  ↓                 ↓               ↓                   ↓               ↓
foreman           public POST       PM/admin       PM (PM scope)        CSV export      lifecycle CLOSED
@ 5:30 AM         /daily-reports    via portal     Safety (flagged)     audit-footer    audit_envelope
on iPad           lifecycle=OPEN    PENDING_REVIEW HR (read-only)       SHA256          permanent
                  idempotent        →REVIEWED      Exec (governance)    PDF + email     DELETE = 410 (frozen)
                  R2 photos         →CLOSED        PM exposure tile     to PM/GC/DOT
                  FSI binding       (attestation)  Payroll variance
                                                   Job photos library
                                                   Excavation backlink
```

### 4.1 · Who enters / reviews / acts / ignores

| Person | Enters? | Reviews? | Acts on? | Ignores? |
|---|---|---|---|---|
| **Foreman** | ✅ (authors the DR) | — | — (kickback only) | — |
| **Superintendent** | ⚪ co-signs | ⚪ glances | — | — |
| **PM** | — | ✅ PENDING → REVIEWED | ✅ — payroll, RFI, schedule | — |
| **Dispatch** | — | — | — | 🔴 zero touch (gap) |
| **Shop** | — | — | — | 🔴 zero touch (gap) |
| **Safety** | — | ✅ flagged-only | ✅ — when injury/incident | other days |
| **HR** | — | ✅ read-only filters | ✅ — payroll-attestation | — |
| **Exec** | — | ✅ governance Draft Health tile | ✅ — when trust signals red | — |

### 4.2 · Friction points (evidence-based)

| Friction | Evidence | Pillar fail |
|---|---|---|
| 11 default-visible sections at form open | `NewDailyReport.jsx` Sections 01-11 + collapsed cards | Simple |
| Triple "Project / Crew / Photos / Signature / Excavation" indicators | `DAILY_REPORT_SIMPLIFICATION_AUDIT.md` §2 (Status Card + form-header + CollapseCard badge + Submit button label) | Simple · Beautiful |
| Free-text `prepared_by` (no directory binding) | `DAILY_REPORT_OWNERSHIP_AUDIT.md` F2 (same first name = identical strings) | Trusted |
| Field crew has no notification when DR is kicked back to OPEN | `DAILY_REPORT_OWNERSHIP_AUDIT.md` F1 (NO push/SMS/email today, audit-row only) | Trusted |
| Free-text `superintendent` not joined to `jobs_master.superintendent` | `DAILY_REPORT_SIMPLIFICATION_AUDIT.md` §4 gap F-A | Trusted |
| Coaching wall at top of every section ("OSHA library style") | `DAILY_REPORT_SIMPLIFICATION_AUDIT.md` §6 (8 OshaCoachingBlocks just on excavation) | Simple · Beautiful |
| Foreman must tap "Use Yesterday" to prefill | `DAILY_REPORT_SIMPLIFICATION_AUDIT.md` §7 (recommends silent auto-apply + undo) | Simple |
| `superintendent_signature` field but no `superintendent` linkage | `DAILY_REPORT_OWNERSHIP_AUDIT.md` §2 (free text only) | Trusted |
| Payroll-Variance Finalize state machine separate from DR Closed gate | `workflow_state_machine.py` lines 287-310 (OC-007 graph) | (intentional — not friction) |

---

## 5 · PHASE 5 · MOTIVE OPPORTUNITY MATRIX

Every DR field run through the question: **"Can Motive provide this automatically?"**

Sources verified:
- `services/motive_service.py` — Motive API client
- `motive_events`, `motive_assets`, `motive_drivers` collections (Source-of-truth: telemetry · live)
- `asset_mappings` collection — links Motive asset → MASCI equipment_id
- `driver_command_profile` — DCP-1 pulls Motive timeline per driver

| DR field | Motive can provide? | Classification |
|---|---|---|
| `equipment[*].description` | ✅ YES — `motive_assets.label/vin` + `asset_mappings.masci_equipment_id` | **AUTO-CAPTURE CANDIDATE** |
| `equipment[*].time_delivered` | ✅ YES — GPS arrival event when crossing job geofence | **AUTO-CAPTURE CANDIDATE** |
| `equipment[*].time_removed` | ✅ YES — GPS departure event | **AUTO-CAPTURE CANDIDATE** |
| `equipment[*].hours_used` | ✅ YES — engine-hours delta per asset (Motive Vehicle Activity API) | **AUTO-CAPTURE CANDIDATE** |
| `equipment[*].notes` | 🟡 NO — operator narrative; Motive doesn't author this | MANUAL |
| `masci_crews[*].name` | 🟡 PARTIAL — Motive driver assigned to vehicle → driver name; but **drivers ≠ crew members in general** | VERIFY ONLY (don't auto-fill) |
| `masci_crews[*].start_time` | 🟡 PARTIAL — vehicle ignition-on time at job geofence (for drivers); other crew arrivals are NOT telemetered | VERIFY ONLY |
| `masci_crews[*].stop_time` | 🟡 PARTIAL — same as above | VERIFY ONLY |
| `weather_summary` | 🟢 already from Weather API | — |
| `gps_lat/lng` | ✅ Motive `vehicle.last_known_location` available; client already wired browser geo | — |
| `subcontractors[*].count` | ❌ NO — Motive doesn't know about subs | MANUAL |
| `materials[*]` | ❌ NO — Motive isn't a delivery system | MANUAL (see FleetWatcher §6) |
| `excavation_activity_today` | ❌ NO — Motive doesn't infer activity from equipment presence | MANUAL |
| `production[]` quantities | ❌ NO | MANUAL |
| `constraints[]` (weather/equipment downtime) | 🟡 PARTIAL — `motive_events` (DVIR fault · idle-while-on) could SIGNAL equipment-down constraint | VERIFY ONLY (signal only — never auto-create constraint) |

### 5.1 · Motive auto-capture sprint candidates (NO IMPLEMENTATION — proposal only)

| Sprint | What | Pillar test |
|---|---|---|
| **M-DR-1** Equipment Auto-Discovery | When foreman opens DR, server queries `motive_assets` for assets within job geofence on `report_date`; pre-fills `equipment[]` as candidates. Foreman taps to confirm / removes. | ✅✅✅✅ — **passes all 5 pillars**. Powerful (eliminates ~6 manual entries), Simple (one tap to confirm), Beautiful (no list to type), Trusted (foreman remains the gate), Proven (DCP-1 telemetry path already field-validated). |
| **M-DR-2** Equipment Hours Verify | If foreman enters hours_used, server computes Motive engine-hours delta and surfaces a quiet badge: "Motive: 7.2 hrs" beside the foreman entry. Never overwrites. | ✅ — VERIFY ONLY semantics already validated for DSI-1. |
| **M-DR-3** Equipment-Down Constraint Signal | When `motive_events.event_kind == 'fault'` for an asset present on the DR job today, surface a quiet chip under the Delays card: "Equipment fault detected — add constraint?" Foreman decides. | ✅ — signal only, no automation. |

### 5.2 · Motive-related NEVER list (anti-patterns)

- ❌ Never AUTO-CREATE the equipment row without foreman confirmation (breaks Trusted).
- ❌ Never use Motive driver name as the `prepared_by` (breaks Trusted — driver ≠ DR author).
- ❌ Never auto-close a DR because Motive says "no equipment on site" (breaks Powerful — quiet days still need DRs).

---

## 6 · PHASE 6 · FLEETWATCHER OPPORTUNITY MATRIX

Source: `FWA1_FLEETWATCHER_FORENSIC_AUDIT.md` (research-only doctrine). FleetWatcher is **not yet integrated** with the platform.

| DR field | FleetWatcher can provide? | Classification |
|---|---|---|
| `materials[*].description` (asphalt mix, millings, dirt) | ✅ YES — FleetWatcher load tickets carry mix-design / category | AUTO-CAPTURE CANDIDATE (future) |
| `materials[*].quantity` + `unit` | ✅ YES — net tonnage / cubic yardage per ticket | AUTO-CAPTURE CANDIDATE |
| `materials[*].supplier` | ✅ YES — plant of origin | AUTO-CAPTURE CANDIDATE |
| `materials[*].ticket_number` | ✅ YES — FW master ticket id | AUTO-CAPTURE CANDIDATE |
| `materials[*].ticket_photos[]` | 🟡 NO — FW doesn't have the foreman's ticket photo, but does have the digital ticket. Foreman photo is the legal corroboration. | KEEP MANUAL ALONGSIDE |
| `production[]` for hauling-heavy jobs (TON of millings, CY of dirt) | ✅ YES — FleetWatcher computes by load count × calibrated weight | AUTO-CAPTURE CANDIDATE |
| **NEW workflow: "Dirt Hauling / Millings Hauling / Disposal"** | ✅ YES — FleetWatcher excels here. Per the directive: "Material export · Dirt hauling · Millings hauling · Concrete removal · Tree removal · Debris hauling · Disposal tracking · Truckload tracking" | **AUDIT-ONLY · sprint candidate** (see §10) |

### 6.1 · FleetWatcher opportunity rank (audit-only · NO BUILD)

| Sprint candidate | Pillar pass? |
|---|---|
| FW-1 Load-Ticket Ingest (FWA-1 flagged as P0 in OGA-1 gap analysis) | All 5 pass. **Top-ranked deferred sprint.** |
| FW-DR-1 Pre-populate `materials[]` from today's FW load tickets for matching project_number | All 5 pass. |
| FW-DR-2 Auto-derive a `production[]` row when FW total tonnage > 0 for the project (foreman confirms unit + description) | Passes Powerful + Simple but **needs Trust gate** (foreman must confirm — never silent). |
| FW-DR-3 New section "Hauling Activity Today" gated by `hauling_today` Yes/No — pre-fills from FW | **Needs operator authorization** — adds a 10th section to the 9-step contract (Lock #1 violation). **Defer unless directive amends.** |

---

## 7 · PHASE 7 · MAINTAINX OPPORTUNITY MATRIX

Source: `LIVE_PRODUCTION_MAINTAINX_AUDIT.md` + `services/maintainx_*.py`. MaintainX IS connected (lived asset sync + work-order ingestion).

| DR field | MaintainX role | Classification |
|---|---|---|
| `equipment[*].description` | MaintainX has the canonical asset registry | OK — MaintainX is system of record, DR is presence confirmation |
| `equipment[*].notes` | If equipment has an open work-order, surface "Open WO: #1234 · Coolant leak" | **LINK-CANDIDATE** — read-only signal under the row |
| `safety_incidents_today` YES | Should be linked to the `incidents` collection (already a thing), NOT to MaintainX | KEEP separate |
| New idea: **Equipment kept down (per MaintainX) but logged on DR** | Mismatch signal · admin notification | **Cross-check candidate** (audit-only) |

### 7.1 · MaintainX-related belongs-where matrix

| Concept | Belongs in | Why |
|---|---|---|
| Asset registry | MaintainX | System of record |
| Work orders | MaintainX | System of record |
| Equipment-down event | MaintainX | System of record |
| Equipment _present on a job today_ | **Daily Report (foreman confirms)** | DR is the boots-on-ground source |
| Hours used | DR (with Motive verify) | Foreman authority |
| Open work-order banner on a DR equipment row | **Cross-link · read-only** | Visibility without ownership transfer |

### 7.1.1 · MaintainX sprint candidates (audit-only)

| Sprint | Pillar pass? |
|---|---|
| MX-DR-1 Read-only "Open WO" chip under DR equipment row | ✅ all five — pure visibility, no automation |
| MX-DR-2 Mismatch banner: "Equipment X on this DR but is OOS in MaintainX" | ✅ all five — calm, signal only |

---

## 8 · PHASE 8 · PRODUCTION INTELLIGENCE AUDIT

### 8.1 · What we track today

`production[]` rows (V.2 Wave-1B, certified · `PRODUCTION_TRACKING_CERTIFICATION.md`):
- `description` (free text)
- `quantity` (number)
- `unit` ∈ {LF, SY, CY, TON, EA, ACRE, OTHER} (closed enum · server-validated)
- `custom_unit_label` (when OTHER)
- `station_from` / `station_to` (FDOT-friendly)
- `notes`

Plus the legacy `activities[]` block (free text + percent_complete).

### 8.2 · The directive's listed missing workflows

> Material export · Dirt hauling · Millings hauling · Concrete removal · Tree removal · Debris hauling · Disposal tracking · Truckload tracking

| Workflow | Today | Recommendation | Pillar pass? |
|---|---|---|---|
| Material export (out-bound asphalt/aggregate) | covered by `production[]` TON · supplemented by `materials[]` | Add FleetWatcher integration for tonnage validation | Pending FW-1 |
| Dirt hauling | `production[]` CY · no truck-load granularity | Future: FleetWatcher truckload count | Sprint FW-1 |
| Millings hauling | Same — `production[]` TON | Future: FleetWatcher | Sprint FW-1 |
| Concrete removal | `production[]` CY/EA possible | No domain-specific UX today. Existing fields adequate. | KEEP as-is |
| Tree removal | `production[]` EA possible | No domain-specific UX today. | KEEP — flag if foremen ask |
| Debris hauling | Same as millings | Future: FleetWatcher | Sprint FW-1 |
| Disposal tracking | `materials[]` ticket_number serves partially | Add `disposal_tickets[]` if SCS/DOT compliance ever required (NOT today's need) | INVESTIGATE only |
| Truckload tracking | NO native — would be FleetWatcher | Sprint FW-1 | — |

### 8.3 · Pillar verdict on adding workflows

**Every "new hauling workflow" carries one cost: a 10th step to the 9-step contract (Lock #1 violation)** unless folded under existing `materials[]` or `production[]`. Recommendation: do NOT add new top-level sections. Instead, let FW-1 ingest pre-populate `materials[]` and `production[]`. Foreman gains data, contract holds.

---

## 9 · PHASE 9 · COACHING AUDIT

Per the existing `DAILY_REPORT_COACHING_LANGUAGE.md` doctrine. Coaching panels evaluated:

| Panel | Where | Read time | Mobile? | Operational value | Verdict |
|---|---|---|---|---|---|
| `HelpTipBlock` daily-report header | Form top | 4–8 s | ✅ collapsible | Onboarding nudge | **KEEP** |
| `HelpTipBlock` daily-report.crew | Section 04 | 4–8 s | ✅ | Crew identity discipline (iter360) | **KEEP — SIMPLIFY** to 1 line |
| `HelpTipBlock` daily-report.equipment | Section 07 | 4–8 s | ✅ | Marginal — equipment is mostly self-explanatory | **SIMPLIFY** to 1 line |
| `HelpTipBlock` daily-report.materials | Section 08 | 4–8 s | ✅ | "Tickets matter for payment disputes" — high value | **KEEP** |
| `HelpTipBlock` daily-report.narrative | Section 09 | 4–8 s | ✅ | Marginal | **SIMPLIFY** |
| `HelpTipBlock` daily-report.photos | Section 10 | 4–8 s | ✅ | OSHA framing — high value | **KEEP** |
| Safety escalation red block | Section 03 (when YES) | 15+ s of stop-the-line copy | ✅ | **Critical** — stops submission until incident chain complete | **KEEP, do not touch** |
| `DailyReportExcavationActivity` "Coaching, not punishment" amber strip | Section 03 (always) | 10 s wall of text | ✅ | Wall of text · field reports it as bloat | **SIMPLIFY** — collapse into 1 line |
| 8 × `OshaCoachingBlock` on excavation form (not DR but adjacent) | Excavation form | Permanent | ✅ | Most foremen swipe past | **HIDE by default · show on field-focus** |
| `CrewSetupRestorePrompt` | Form load | 3 s | ✅ | Excellent — calm tier-3 confidence copy | **KEEP** |

### 9.1 · Coaching aggregate

- KEEP: 5 panels
- SIMPLIFY: 4 panels
- REMOVE: 0
- EXPAND: 0

Recommended global rule: **A foreman should not have to read more than 12 seconds of coaching to finish a Daily Report.** Current cumulative read-time on a happy-path day: ≈ 35 seconds. Target: ≤ 12 seconds.

---

## 10 · PHASE 10 · FIELD TEST AUDIT

### 10.1 · Field-issue codes referenced (DR-H1-001 / DR-H1-002 / DR-H1-003)

**Evidence:** A code search across `/app/backend`, `/app/frontend`, `/app/memory` returned **zero hits** for the codes `DR-H1-001`, `DR-H1-002`, `DR-H1-003`. They are not currently tracked in the codebase or memory. **Recommendation:** when the operator next captures field observations, file them under those codes in `/app/memory/DR_FIELD_OBSERVATIONS_H1.md` so this audit can be re-run against them.

### 10.2 · Field-discovered issues that ARE documented (used as substitute evidence)

Drawn from `DAILY_REPORT_OWNERSHIP_AUDIT.md`, `DAILY_REPORT_SIMPLIFICATION_AUDIT.md`, `DAILY_REPORT_FIELD_TRUST_REVIEW.md`, `OPERATIONAL_CALMNESS_AUDIT.md`:

| Code (assigned) | Issue | Severity | Pillar fail |
|---|---|---|---|
| **DR-F-001** | Free-text `prepared_by` cannot reliably identify two foremen with the same first name | HIGH | Trusted |
| **DR-F-002** | Kicked-back DRs have no field-side notification (no email/SMS/push to submitter) | HIGH | Trusted |
| **DR-F-003** | 261-row `employees` directory has only 1 row with an email — even if form captured directory selection, contact would fail for ~260/261 | HIGH | Trusted |
| **DR-F-004** | No public-gate revision URL — submitter can only create a duplicate or wait | MEDIUM | Trusted |
| **DR-F-005** | 11 default-visible sections — friction at 5:30 AM open | MEDIUM | Simple |
| **DR-F-006** | Triple "Project / Crew / Photos / Signature / Excavation" status indicators across Status Card + form header + CollapseCard | MEDIUM | Simple + Beautiful |
| **DR-F-007** | `superintendent` not auto-pulled from `jobs_master.superintendent` | LOW | Trusted |
| **DR-F-008** | 8 `OshaCoachingBlock` always-visible blocks on excavation form (foremen swipe past) | LOW | Simple |
| **DR-F-009** | `weather_snapshots[]` granular array stored but never rendered | LOW | (data bloat) |
| **DR-F-010** | "Use Yesterday" still requires a tap; auto-apply-with-undo not yet wired | LOW | Simple |
| **DR-F-011** | Equipment list mostly typed by hand — Motive could pre-fill (M-DR-1) | LOW | Simple (huge upside) |
| **DR-F-012** | No Dispatch / Shop / Field-Leadership read surface for DR data despite operational overlap | LOW | Powerful |

### 10.3 · iter452.5 closed items (already fixed · evidence only, no action)

- ✅ Field Submitter Identity Tier 1 binding (`lib/field_submitter_identity.py`) — submitter email captured at submit when supplied; orphans dead-lettered.
- ✅ Kickback `/revise/{token}` flow exists (`routes/field_revision.py`).
- ✅ Resend webhook closure (`test_iter452_5_2_resend_webhook.py`).
- 🟡 The kickback notification fires ONLY when an FSI binding exists. If submitter didn't supply email, the notification fails silently — DR-F-002 still partially open.

---

## 11 · FINAL DELIVERABLES — Recommendations Funnel

### 11.1 · Recommended Changes (RANKED · 5-pillar compliant)

| # | Recommendation | Source field(s) | Pillars passed |
|---|---|---|---|
| **R1** | **Auto-populate `superintendent` from `jobs_master.superintendent`** (Trust gap F-A — non-breaking) | `superintendent` | ✅✅✅✅✅ |
| **R2** | **Silent auto-apply yesterday's crew + equipment** on job selection, with a 5-second "Yesterday's setup applied · undo" toast (DR-F-010) | `masci_crews`, `equipment` | ✅✅✅✅✅ |
| **R3** | **Bind `prepared_by` to a person reference** (`employees` directory or FSI auth context) instead of free text. Keep free-text fallback for off-roster crews. (DR-F-001) | `prepared_by` | ✅✅✅✅ — Trusted gain offsets minor Simple cost |
| **R4** | **Show kickback notification to FSI-bound submitter through the bell** (in-app) and via FSI signed email when FSI binding exists (DR-F-002) | lifecycle PENDING_REVIEW → OPEN | ✅✅✅✅✅ |
| **R5** | **Motive M-DR-1** equipment auto-discovery on form load (foreman confirms). | `equipment[]` | ✅✅✅✅✅ |
| **R6** | **Read-only "Open WO" chip under DR equipment rows** from MaintainX (MX-DR-1). | `equipment[]` | ✅✅✅✅✅ |
| **R7** | **PM Exposure tile** — already exists (V.2 Wave-1B `daily-reports/exposure-signals`); ensure it surfaces on every PM portal landing. | exposure-signals | ✅✅✅✅✅ |
| **R8** | **Coaching simplification** — bring cumulative coaching read-time ≤12 s (currently ≈35 s). | All HelpTipBlocks | ✅✅✅✅✅ |
| **R9** | **Dispatch read-only `Daily Report Today` chip on Dispatch Board** for each active job ("✅ DR submitted" / "⏳ Pending" / "—") | lifecycle_state | ✅✅✅✅✅ |
| **R10** | **Shop mismatch banner** — when an asset is on a DR equipment row but currently OOS in MaintainX, the Shop hub shows a calm signal (MX-DR-2). | `equipment[]` × MaintainX | ✅✅✅✅✅ |

### 11.2 · Recommended Removals

| # | Remove | Rationale | Risk |
|---|---|---|---|
| RM-1 | `weather_snapshots[]` granular array (stored but never rendered) | Data bloat | LOW — keep `weather_summary` |
| RM-2 | `schedule_delays_notes` free-text post-V.2 | Replaced by structured `constraints[]` | LOW — one DR cycle to confirm |
| RM-3 | `weather_impact_notes` free-text post-V.2 | Same | LOW |
| RM-4 | "Coaching, not punishment" amber strip on `DailyReportExcavationActivity` | Wall of text · 1-line equivalent suffices | LOW |
| RM-5 | 7 always-visible OSHA coaching blocks on excavation form | Defer to focus-state | LOW |

### 11.3 · Recommended Auto-Populations

| Field | Source | Trust gate |
|---|---|---|
| `superintendent` | `jobs_master.superintendent` | none required |
| `masci_crews[]` (suggestions) | last DR per `project_number` | foreman undo toast |
| `equipment[]` (candidates) | Motive `assets` GPS-on-job | foreman tap-to-confirm |
| `materials[]` (after FW-1) | FleetWatcher load tickets | foreman tap-to-confirm |
| `prepared_by` | FSI binding when available | foreman can override |
| Equipment hours_used quiet verify | Motive engine-hours delta | display-only — never overwrites |

### 11.4 · Items the platform must NEVER automate

| Field | Why not |
|---|---|
| Photos | Field-authored evidence — must remain operator-uploaded |
| Signatures | Legal weight |
| `safety_incidents_today` / `injuries_reported` YES/NO | Stop-the-line gate |
| `safety_notified` / `incident_report_filled` | Attestation |
| `production[]` quantities | Foreman judgment |
| `constraints[]` rows | Foreman judgment (Motive may signal, never create) |
| `general_notes` | Narrative — automation would silence the field |
| Final `lifecycle_state` transitions to CLOSED | Requires attestation (office_review_complete + payroll_inputs_verified) |

---

## 12 · PILLAR COMPLIANCE REVIEW

Every recommendation R1–R10 cross-checked:

| # | Powerful | Simple | Beautiful | Trusted | Proven | Pass? |
|---|---|---|---|---|---|---|
| R1 superintendent auto-pull | ✅ | ✅ | ✅ | ✅ | ✅ existing jobs_master pattern | 🟢 |
| R2 silent crew/equipment auto-apply | ✅ | ✅ | ✅ | ✅ (undo gate) | 🟡 PreviousReportSuggestions is partially proven | 🟢 |
| R3 prepared_by directory bind | ✅ | 🟡 (one extra tap) | ✅ | ✅✅ | ✅ FSI binding proven | 🟢 |
| R4 kickback bell + email | ✅ | ✅ | ✅ | ✅ | ✅ in-app bell proven (OA-1) | 🟢 |
| R5 Motive equipment auto-discovery | ✅✅ | ✅ | ✅ | ✅ (confirm-only) | ✅ DCP-1 telemetry path proven | 🟢 |
| R6 MaintainX Open-WO chip | ✅ | ✅ | ✅ | ✅ | ✅ MX integration live | 🟢 |
| R7 PM Exposure tile surfacing | ✅ | ✅ | ✅ | ✅ | ✅ already built | 🟢 |
| R8 Coaching simplification | ✅ | ✅✅ | ✅ | ✅ | ✅ doctrine exists | 🟢 |
| R9 Dispatch DR chip | ✅ | ✅ | ✅ | ✅ | ✅ same chip pattern used elsewhere | 🟢 |
| R10 Shop mismatch banner | ✅ | ✅ | ✅ | ✅ | ✅ universal palette established | 🟢 |

**Every recommendation passes all 5 pillars.** Zero violations of the 9-step lock. Zero recommendations introduce automation forbidden by the Coaching audit. Zero recommendations transfer system-of-record from MaintainX / FleetWatcher / Motive / Vista.

---

## 13 · NEXT STEPS (operator-gated · NO BUILD)

1. **Operator review of this audit** — sign-off on R1–R10 individually.
2. **DR-AUDIT-002** (proposed): tactical breakdown of each authorized R into a build directive with explicit testid + bilingual matrices + 30-second benchmark.
3. **FW-1 Ticket Ingest** continues to be the P0 deferred sprint (recommendation: pre-requisite to R-FW-DR-1).
4. **DR field observations capture** — operator to file DR-H1-001 / DR-H1-002 / DR-H1-003 into `/app/memory/DR_FIELD_OBSERVATIONS_H1.md` so future audits can verify them directly.

---

## 14 · FILE EVIDENCE INDEX

Source files referenced in this audit (read-only · no modifications):

- `/app/backend/routes/daily_reports.py` (566 lines)
- `/app/backend/routes/daily_report_lifecycle.py` (257 lines)
- `/app/backend/routes/safety_portal/daily_reports.py` (75 lines)
- `/app/backend/lib/workflow_state_machine.py` (DR block ≈ lines 215–283)
- `/app/backend/services/motive_service.py`
- `/app/backend/services/maintainx_client.py`
- `/app/frontend/src/lib/dailyReportSchema.js` (107 lines)
- `/app/frontend/src/pages/NewDailyReport.jsx` (2,291 lines)
- `/app/frontend/src/pages/ViewDailyReport.jsx` (678 lines)
- `/app/frontend/src/pages/DailyReportsDashboard.jsx` (228 lines)
- `/app/frontend/src/pages/HrDailyReports.jsx` (422 lines)
- `/app/frontend/src/components/trench/DailyReportExcavationActivity.jsx` (220 lines)
- `/app/memory/DAILY_REPORT_OWNERSHIP_AUDIT.md`
- `/app/memory/DAILY_REPORT_SIMPLIFICATION_AUDIT.md`
- `/app/memory/DAILY_REPORT_FIELD_SIMPLICITY_CERTIFICATION.md`
- `/app/memory/DAILY_REPORT_FIELD_TRUST_REVIEW.md`
- `/app/memory/DAILY_REPORT_EVOLUTION_PLAN.md`
- `/app/memory/PRODUCTION_TRACKING_CERTIFICATION.md`
- `/app/memory/PM_EXPOSURE_TILE_CERTIFICATION.md`
- `/app/memory/FWA1_FLEETWATCHER_FORENSIC_AUDIT.md`
- `/app/memory/LIVE_PRODUCTION_MAINTAINX_AUDIT.md`
- `/app/memory/OGA1_OPERATIONAL_GAP_ANALYSIS.md`
- `/app/memory/ODR_SIMPLICITY_TEST_DOCTRINE.md` (referenced doctrine)

— Forked main agent · DR-AUDIT-001 · 2026-06-08
— ZERO code changes. Audit complete. Awaiting operator directive on R1–R10.
