# DR-AUDIT-001 · DAILY REPORT FULL CONSTITUTIONAL AUDIT
**MASCI / ForgedOps Platform**
**Authorized Execution:** OMEGA Audit-Only Directive · 2026-06-08
**Status:** 🟡 Audit complete · **zero code changes performed**
**Discipline:** Evidence-only. No opinion. No build. No design. No deploy.

---

## 0 · Reader's Map

| Phase | Deliverable | Section |
|---|---|---|
| 1 | Daily Report Master Inventory | §1 |
| 2 | Field Value Matrix | §2 |
| 3 | Visibility Matrix | §3 |
| 4 | Workflow Map | §4 |
| 5 | PDF Architecture Audit (DR-PDF-001 … 020) | §5 |
| 6 | Material Movement Audit | §6 |
| 7 | Motive Mapping Matrix | §7 |
| 8 | FleetWatcher Mapping Matrix | §8 |
| 9 | MaintainX Mapping Matrix | §9 |
| 10 | Coaching Audit | §10 |
| 11 | Field Findings Report | §11 |
| 12 | Constitutional Certification (PASS/CONDITIONAL/FAIL) | §12 |
| 13 | Recommendations + Pillar gate | §13 |

---

# 1 · DAILY REPORT MASTER INVENTORY

## 1.1 · Code surface

| Layer | File | Lines | Purpose |
|---|---|---|---|
| Foreman form | `frontend/src/pages/NewDailyReport.jsx` | 2,291 | Public + admin authoring |
| Schema | `frontend/src/lib/dailyReportSchema.js` | 107 | Default shape |
| Read view | `frontend/src/pages/ViewDailyReport.jsx` | 678 | PM/Admin/Safety detail |
| Admin list | `frontend/src/pages/DailyReportsDashboard.jsx` | 228 | All reports |
| HR list/detail | `frontend/src/pages/HrDailyReports.jsx` | 422 | HR read-only |
| Safety list | `backend/routes/safety_portal/daily_reports.py` | 75 | Flagged-only Safety surface |
| CRUD | `backend/routes/daily_reports.py` | 566 | POST · GET · CSV · audit-footer (DELETE = 410 frozen) |
| Lifecycle | `backend/routes/daily_report_lifecycle.py` | 257 | OC-002 state machine + FSI kickback |
| State machine def | `backend/lib/workflow_state_machine.py` (DR block) | ≈75 | OPEN · PENDING_REVIEW · REVIEWED · CLOSED |
| PDF renderer | `backend/pdf_render.py` (`_render_daily`) | ≈300 LOC | The legal PDF emitted to PM/GC/DOT |
| Thank-You page | `frontend/src/pages/ThankYou.jsx` | 132 | Post-submit page |
| Excavation tile | `frontend/src/components/trench/DailyReportExcavationActivity.jsx` | 220 | Phase 10A-B gate |
| Field Submitter Identity | `backend/lib/field_submitter_identity.py` + `routes/field_revision.py` | — | iter452.5 kickback chain |
| Audit envelope SHA256 | `daily_reports.py` lines 150-166 + 454-484 | — | Tamper detection footer |

## 1.2 · Section / Field Master Matrix (Form, ViewDailyReport, PDF, Mongo)

Legend — `Form`/`View`/`PDF` columns: ✅ rendered · ❌ not rendered · ⚪ optional / hidden.

| Section | Field | Type | Req | Validation | Form | View | PDF | Mongo key | Notes |
|---|---|---|---|---|---|---|---|---|---|
| **01 Report Info** | `project_name` | text | ✅ | min 1 | ✅ | ✅ | ✅ | `project_name` | Auto-filled by JobPicker |
| 01 | `project_number` | text | ⚪ | — | ✅ | ✅ | ✅ | `project_number` | Auto-filled by JobPicker |
| 01 | `location` | text | ✅ | — | ✅ | ✅ | ✅ | `location` | Free text today; should pull `jobs_master.location` |
| 01 | `report_date` | date | ✅ | YYYY-MM-DD | ✅ | ✅ | ✅ | `report_date` | Auto-default today |
| 01 | `report_number` | text | ⚪ | DR-YYYYMMDD-NNN | ✅ | ✅ | ✅ | `report_number` | Server mints |
| 01 | `doc_id` | text | (sys) | DR-YYYY-NNNNN | ❌ hidden | ⚪ | ⚪ shown in footer | `doc_id` | Continuity identifier (PDF audit footer uses this) |
| 01 | `prepared_by` | text | ✅ | — | ✅ | ✅ | ✅ | `prepared_by` | Free text · F-001 gap |
| 01 | `superintendent` | text | ⚪ | — | ✅ | ✅ | ✅ | `superintendent` | Free text · F-A gap (not jobs_master-bound) |
| **02 Weather** | `weather_summary` | text | ⚪ | — | ✅ | ✅ | ✅ | `weather_summary` | Auto-filled |
| 02 | `weather_snapshots[]` | array | ⚪ | — | ✅ (background) | ❌ | ❌ | `weather_snapshots` | **Stored but invisible** |
| 02 | `gps_lat`, `gps_lng`, `gps_accuracy` | geo | ⚪ | — | ⚪ background | ❌ | ⚪ (only lat,lng in PDF) | same | accuracy stored but never rendered |
| **03 General Info** | `schedule_delays` | Yes/No | ⚪ | enum | ✅ | ✅ | ✅ | `schedule_delays` | Drives constraints gate |
| 03 | `schedule_delays_notes` | textarea | ⚪ | — | ⚪ legacy | ⚪ | ⚪ (rendered as `schedule_delay_today` key — see DR-PDF-005) | `schedule_delays_notes` | **Duplicated by `constraints[]`** post-V.2 |
| 03 | `weather_impact` | Yes/No | ⚪ | enum | ✅ | ✅ | ✅ | `weather_impact` | Drives weather constraint gate |
| 03 | `weather_impact_notes` | textarea | ⚪ | — | ⚪ | ⚪ | ⚪ | `weather_impact_notes` | Same — duplicated post-V.2 |
| 03 | `safety_incidents_today` | Yes/No | ⚪ | enum | ✅ | ✅ | ✅ | `safety_incidents_today` | Stop-the-line gate |
| 03 | `injuries_reported` | Yes/No | ⚪ | enum | ✅ | ✅ | ✅ | `injuries_reported` | Stop-the-line gate |
| 03 | `incident_notes` | textarea | gated | required if either YES | ✅ | ✅ | ✅ | `incident_notes` | Critical narrative |
| 03 | `safety_notified` | Yes/No | gated | required if incident YES | ✅ | ✅ | ✅ | `safety_notified` | Stop-the-line attestation |
| 03 | `safety_contact_person` | text | gated | — | ✅ | ✅ | ✅ | same | Free text · could resolve safety_users |
| 03 | `safety_contact_time` | time | gated | HH:MM | ✅ | ✅ | ✅ | same | — |
| 03 | `incident_report_filled` | Yes/No | gated | — | ✅ | ✅ | ✅ | same | Should cross-link `incidents` |
| 03 | `incident_report_time` | time | gated | HH:MM | ✅ | ✅ | ✅ | same | — |
| 03 | `general_notes` | textarea | ⚪ | — | ✅ | ✅ | ✅ | `general_notes` | Foreman narrative |
| 03 | `excavation_activity_today` | Yes/No | ⚪ | enforces 422 if YES + no link | ✅ | ✅ | ❌ | `excavation_activity_today` | **PDF gap — DR-PDF-014** |
| 03 | `linked_excavation_ids[]` | string[] | gated | required if excavation YES | ✅ | ✅ | ❌ | `linked_excavation_ids` | **PDF gap** |
| **04 MASCI Crews** | `masci_crews[]` rows | repeat | ⚪ | crew_count ≥ 1 soft | ✅ | ✅ | ✅ | `masci_crews` | iter250 photos + iter360 identity coaching |
| 04 (per row) | `name, trade, start_time, lunch_minutes, stop_time, hours, work_performed` | mixed | ⚪ | hours auto-calc | ✅ | ✅ | ✅ (with gross/net inline) | per row | PDF includes a gross/net math summary line |
| **05 Subs** | `subcontractors[]` rows | repeat (collapsed) | ⚪ | — | ✅ | ✅ | ✅ if any | `subcontractors` | — |
| 05 (per row) | `company, trade, foreman, count, hours, work_performed, attachment_note, photos[]` | mixed | ⚪ | — | ✅ | ✅ | ✅ + photo block | per row | iter250 sub photos |
| **06 Visitors** | `visitors[]` rows | repeat | ⚪ | — | ✅ | ✅ | ✅ if any | `visitors` | — |
| 06 (per row) | `name, company, time_in, time_out, purpose` | — | — | — | ✅ | ✅ | ✅ | — | — |
| **07 Equipment** | `equipment[]` rows | repeat | ⚪ | — | ✅ | ✅ | ✅ if any | `equipment` | Currently typed by hand — Motive M-DR-1 candidate |
| 07 (per row) | `description, hours_used, time_delivered, time_removed, notes` | — | — | — | ✅ | ✅ | ✅ | — | — |
| **08 Materials** | `materials[]` rows | repeat | ⚪ | — | ✅ | ✅ | ✅ if any | `materials` | iter250 ticket_photos |
| 08 (per row) | `description, quantity, unit, supplier, ticket_number, notes, ticket_photos[]` | — | — | — | ✅ | ✅ | ✅ + photo block | — | "Description" semantics: in-bound delivery only |
| **09 Activities** | `activities[]` rows | repeat (legacy) | ⚪ | — | ✅ | ✅ | ✅ if any | `activities` | — |
| 09 (per row) | `activity, percent_complete, station_from, station_to, notes` | — | — | — | ✅ | ✅ | ✅ | — | Legacy free-text production tracking |
| **09b Production (V.2 Wave-1B)** | `production[]` rows | repeat | ⚪ | unit ∈ closed enum | ✅ | ❌ | ❌ | `production` | 🔴 **DR-PDF-001 · DR-PDF-013 critical gap** — structured production stored but NOT on PDF and NOT on read view |
| 09b (per row) | `description, quantity, unit, custom_unit_label, station_from, station_to, notes` | — | — | server validates LF/SY/CY/TON/EA/ACRE/OTHER | ✅ | ❌ | ❌ | per row | — |
| **10 Constraints (V.2 Wave-1B)** | `constraints[]` rows | repeat | ⚪ | constraint_type ∈ 11-enum | ✅ | ❌ | ❌ | `constraints` | 🔴 **DR-PDF-002 · DR-PDF-011 critical gap** — structured constraints stored but NOT on PDF |
| 10 (per row) | `constraint_type, hours_impact, notes, may_require_rfi, may_affect_schedule` | — | — | server derives advisory flags | ✅ | ❌ | ❌ | per row | Server stamps advisory flags |
| **10 Photos** | `photos[]` | photo[] | ✅ | min 6 (`photo_min`) | ✅ | ✅ | ✅ thumbnail grid (max 24) | `photos` | R2 storage; PDF inlines via `_resolve_photo_ref` |
| 10 | `photo_min` | int | (sys) | — | ⚪ | — | — | `photo_min` (always 6) | — |
| **11 Sign-off** | `prepared_by_signature` | base64/photo://ref | ✅ | — | ✅ | ✅ | ✅ | same | iter75 R2-migrated signatures |
| 11 | `superintendent_signature` | base64/photo://ref | ⚪ | — | ✅ | ✅ | ✅ if present | same | — |
| 11 | `distribution_list[]` | email[] | ⚪ | max 20 | ✅ | ❌ visible only on form | ❌ | `distribution_list` | CC list for PM/GC/DOT |
| **System** | `id` | UUID | sys | — | ❌ | ❌ | ⚪ | `id` | — |
| sys | `doc_id` | DR-YYYY-NNNNN | sys | — | ❌ | ⚪ | ✅ in footer | `doc_id` | — |
| sys | `created_at` | ISO UTC | sys | — | ❌ | ❌ | ⚪ | `created_at` | — |
| sys | `audit_envelope_sha256` | hex | sys | — | ❌ | ❌ | ⚪ (separate endpoint) | `audit_envelope_sha256` | 🔴 **DR-PDF-008 gap** — SHA256 minted but not embedded in PDF body |
| sys | `lifecycle_state` | enum | sys | OPEN/PENDING_REVIEW/REVIEWED/CLOSED | ❌ | ✅ | ❌ | `lifecycle_state` | — |
| sys | `daily_report_links` (mirror on `trench_excavations`) | array | sys | — | ❌ | ❌ | ❌ | (on related collection) | Two-way link |
| sys | `language` | enum | sys | en/es at submit | ❌ | ⚪ | ⚪ | `language` | — |
| sys | `submitter_email_at_submit` (FSI) | email | ⚪ optional at submit | — | ❌ hidden | ❌ | ❌ | iter452.5 binding | — |
| sys | `submitter_consent_at` (FSI) | ISO | ⚪ | — | ❌ | ❌ | ❌ | iter452.5 binding | — |

**Total fields:** 47 user-visible + 9 system = **56 fields per Daily Report.**

## 1.3 · Coaching panels inventory (DR surface only)

| Panel | Component | Trigger | Estimated read time |
|---|---|---|---|
| Form header | `HelpTipBlock formKey="daily-report"` | always · with counter | 4–8 s |
| Section 04 crew | `HelpTipBlock formKey="daily-report.crew"` + iter360 identity coaching | always | 6–10 s |
| Section 07 equip | `HelpTipBlock formKey="daily-report.equipment"` | always | 4–8 s |
| Section 08 materials | `HelpTipBlock formKey="daily-report.materials"` | always | 4–8 s |
| Section 09 narrative | `HelpTipBlock formKey="daily-report.narrative"` | always | 4–8 s |
| Section 10 photos | `HelpTipBlock formKey="daily-report.photos"` | always | 4–8 s |
| Safety escalation block | red panel inside Section 03 | YES on accident OR injury | 15+ s (critical, kept) |
| Excavation "Coaching, not punishment" amber strip | `DailyReportExcavationActivity` | always | 10 s (wall of text) |
| Crew memory restore prompt | `CrewSetupRestorePrompt` | snapshot exists | 3 s |

**Cumulative happy-path coaching read-time:** ≈ 35 s. Target per `ODR_SIMPLICITY_TEST_DOCTRINE.md`: ≤ 12 s.

## 1.4 · Workflow / notification / dashboard dependencies

| Concept | Triggered by | Destination |
|---|---|---|
| Auto-email PDF | submit | PM (`jobs_master.pm_email`) + co-PMs + `distribution_list[]` |
| Photo mirror | submit | `job_photos` library (read-only mirror) |
| Excavation back-link | submit when `linked_excavation_ids[]` present | `trench_excavations.daily_report_links[]` |
| FSI binding | submit (best-effort) | `field_submitter_identity` collection |
| Lifecycle PENDING_REVIEW notification | PM/Admin transition OPEN→PENDING_REVIEW | in-app bell · `recipient_role` ∈ {admin, pm, safety} |
| Lifecycle kickback PENDING_REVIEW→OPEN | Admin only · reason ≥5 chars | FSI signed `/revise/{token}` email IF binding exists; else NO field notification |
| PM Exposure tile aggregator | reads constraint rows | `/api/daily-reports/exposure-signals` (PM hub) |
| CSV export | admin/PM | `/api/daily-reports.csv` |
| Audit footer | PDF render | `/api/daily-reports/{id}/audit-footer` (server recompute) |
| `payroll_variance` consumer | downstream | reads `masci_crews[*].hours` |
| `command_center` consumer | downstream | uses report_date + project_number |
| Draft Health tile | client telemetry events | `/admin/governance` |

---

# 2 · FIELD VALUE MATRIX

Verdicts: **KEEP · MODIFY · REMOVE · AUTO-POPULATE · INVESTIGATE**.

| Field | Verdict | Why | Pillar weight |
|---|---|---|---|
| `project_name`, `project_number` | AUTO-POPULATE (already partial via JobPicker) | jobs_master canonical | Simple |
| `location` | AUTO-POPULATE | `jobs_master.location` + GPS reverse-geocode | Simple · Trusted |
| `report_date` | KEEP (already auto) | — | — |
| `report_number` | KEEP | Server mints | — |
| `prepared_by` | MODIFY → directory ref | F-001: name collision risk | **Trusted (critical)** |
| `superintendent` | AUTO-POPULATE | F-A: not joined to `jobs_master.superintendent` | Trusted · Simple |
| `weather_summary`, `weather_snapshots` | KEEP weather_summary · INVESTIGATE removing snapshots | snapshots stored, never rendered | Simple |
| `gps_lat`, `gps_lng` | KEEP | shown on PDF | — |
| `gps_accuracy` | REMOVE | never rendered · not consumed | Simple |
| `schedule_delays` (Y/N) | KEEP (drives constraints gate) | — | — |
| `schedule_delays_notes` | REMOVE post-V.2 | replaced by `constraints[]` | Simple |
| `weather_impact` (Y/N) | KEEP (drives weather constraint) | — | — |
| `weather_impact_notes` | REMOVE post-V.2 | replaced by weather constraint row | Simple |
| `safety_incidents_today` / `injuries_reported` | KEEP | stop-the-line gate | Powerful · Trusted |
| `incident_notes` | KEEP | required narrative when YES | Trusted |
| `safety_notified`, `safety_contact_person`, `safety_contact_time`, `incident_report_filled`, `incident_report_time` | KEEP · INVESTIGATE cross-link to `incidents` | attestation chain | Powerful · Trusted |
| `general_notes` | KEEP | foreman escape valve | Powerful |
| `excavation_activity_today` + `linked_excavation_ids[]` | KEEP | Phase 10A-B 422 gate · critical | Powerful · Trusted |
| `masci_crews[]` | MODIFY → silent auto-prefill | DR-F-010 (tap currently required) | Simple |
| `masci_crews[*].name` | MODIFY → directory bind (FSI fallback) | F-001 | Trusted |
| `masci_crews[*].hours` | KEEP (auto-calc) | — | — |
| `subcontractors[]` | KEEP · MODIFY suggestions | suppliers directory pre-suggest | Simple |
| `visitors[]` | KEEP | inspector/owner visit provenance | Powerful |
| `equipment[]` | MODIFY → Motive M-DR-1 verify-only auto-discovery | Motive owns this | Simple · Trusted |
| `materials[]` | KEEP · INVESTIGATE FleetWatcher pre-fill | FW load tickets | Simple |
| `activities[]` (legacy) | KEEP (grandfathered) | coexists with production[] | — |
| `production[]` (V.2) | KEEP · 🔴 SURFACE ON PDF/VIEW | currently invisible to consumers (DR-PDF-001) | Powerful · Trusted |
| `constraints[]` (V.2) | KEEP · 🔴 SURFACE ON PDF/VIEW | currently invisible (DR-PDF-002) | Powerful · Trusted |
| `photos[]` (min 6) | KEEP | photo doctrine sacrosanct | Trusted |
| `prepared_by_signature` / `superintendent_signature` | KEEP | legal · SHA256-included | Trusted |
| `distribution_list[]` | KEEP | CC roster | Powerful |
| `audit_envelope_sha256` | KEEP · 🟡 SURFACE ON PDF | minted but not visible in PDF body (DR-PDF-008) | Trusted |
| `lifecycle_state` | KEEP | OC-002 state machine | Trusted |

---

# 3 · VISIBILITY MATRIX

| Surface | Foreman | Super | PM | Dispatch | Shop | Safety | HR | Exec |
|---|---|---|---|---|---|---|---|---|
| `/daily/submit` (authoring) | ✅ | ✅ | — | — | — | — | — | admin-only `/daily/new` |
| `/daily-reports` (list) | — | — | ✅ (PM scope) | — | — | ✅ | — | ✅ |
| `/daily/:id` (detail) | — | — | ✅ scope | — | — | ✅ flagged | — | ✅ |
| `/hr/daily-reports` | — | — | — | — | — | — | ✅ | — |
| `/safety/daily-reports` (flagged-only) | — | — | — | — | — | ✅ | — | — |
| Admin governance Draft Health tile | — | — | — | — | — | — | — | ✅ |
| PM Exposure tile (V.2 Wave-1B) | — | — | ✅ | — | — | — | — | ✅ |
| Payroll Variance consumer | — | — | ✅ | — | — | — | ✅ | ✅ |
| Lifecycle transition controls | ✅ via submit | — | ✅ PENDING | — | — | — | — | ✅ all transitions |
| PDF + audit footer | ✅ via email | ✅ | ✅ | — | — | ✅ | ✅ | ✅ |
| `/revise/{token}` (kickback) | ✅ FSI-bound only | — | — | — | — | — | — | — |
| Dispatch Board DR chip | — | — | — | ❌ no visibility | — | — | — | — |
| Shop equipment cross-reference | — | — | — | — | ❌ no visibility | — | — | — |
| Field Leadership read surface | — | — | — | — | — | — | — | ❌ no surface |

### 3.1 · Visibility gaps

- **Dispatch sees nothing** — knows where crews/trucks are; would benefit from a per-job DR-submitted chip.
- **Shop sees nothing** — owns equipment; could cross-check DR equipment rows against MaintainX OOS state.
- **Field Leadership has no DR surface today** — operates upstream of the form.
- **Production[] and constraints[] invisible to ALL consumers** (PDF + read view) — written to Mongo only.
- **Audit SHA256 invisible in PDF body** — only available via separate endpoint.

### 3.2 · Wrong visibility (information nobody uses)

- `weather_snapshots[]` granular hourly array — stored, never rendered anywhere.
- `gps_accuracy` — stored, never rendered.
- `schedule_delays_notes` / `weather_impact_notes` post-V.2 — replaced by `constraints[]`.

### 3.3 · Duplicate visibility

| Concept | Where duplicated | Recommendation |
|---|---|---|
| "Project N" indicator | JobPicker chip + Section 01 header + (legacy) StatusCard | Single canonical |
| "Crew on site today" | DR `masci_crews[]` + Dispatch board + Motive driver telemetry | DR = author, Motive = verify |
| "Equipment on site today" | DR `equipment[]` + Motive `motive_assets` GPS-on-job + MaintainX WO assignment | Motive = source-of-truth presence; DR = foreman confirms |
| "Material delivered" | DR `materials[]` + FleetWatcher load tickets | FW canonical for hauling |
| "Incident today YES" | DR `safety_incidents_today` + `incidents` collection | Two separate writes (link gap) |
| "Excavation activity today" | DR + `trench_excavations` | ✅ already two-way linked (best-in-class) |

---

# 4 · WORKFLOW MAP

## 4.1 · Lifecycle stages

```
                            ┌──────────────────────────────────────────────┐
                            │  PDF auto-email to PM / co-PM / distribution │
                            └────────────────────────▲─────────────────────┘
                                                     │ on submit
                                                     │
 CREATION ──► SUBMISSION ──► PENDING_REVIEW ──► REVIEWED ──► CLOSED
   foreman      public         PM/Admin           Admin       Admin
   @ 5:30 AM    POST           queue              decision    attestation
   on iPad     (idempotent)    bell+pm+safety               office_review_complete=true
   public                                                   payroll_inputs_verified=true
                                                                  ▲
                                            REOPEN (CLOSED→PENDING)│
                                            requires ≥5-char reason│
                                            admin-only             │

   KICKBACK (PENDING→OPEN) ─► FSI signed /revise/{token} email IF binding exists
                              else NO field notification ← F-002 gap
```

## 4.2 · Who touches what

| Stage | Touches | Why | Friction |
|---|---|---|---|
| Creation | Foreman | Authoring | 11 sections at open; ≈35 s coaching read-time |
| Submission | Foreman | One tap | Heavy-payload translate→idempotency→upload may take seconds (DR-F-013 Submit freeze) |
| PENDING_REVIEW | PM / Admin / Safety | Review queue volume | None today (bell working) |
| REVIEWED | Admin | Office decision | None |
| CLOSED | Admin | Attestation gate (2 flags) | None |
| Kickback | Admin | Send back to field | **No field-side notification when no FSI binding (F-002)** |
| Consumption | PM / Safety / HR / Exec | Read | `production[]` + `constraints[]` invisible to consumers |
| Archiving | All | Lifecycle CLOSED · DELETE = 410 frozen | Records preserved as canonical legal evidence |

## 4.3 · Friction & failure points

| Code | Friction | Severity |
|---|---|---|
| DR-FR-1 | 11 default-visible sections at 5:30 AM (11 → target 6) | MEDIUM |
| DR-FR-2 | Triple status indicator (Status Card + Section header + Submit button label) | MEDIUM |
| DR-FR-3 | Free-text prepared_by / superintendent / safety_contact_person | HIGH (Trusted) |
| DR-FR-4 | Kickback without FSI binding → no field notification | HIGH |
| DR-FR-5 | Coaching read-time ≈35 s (target ≤12 s) | MEDIUM |
| DR-FR-6 | "Use Yesterday" requires tap (silent auto-apply + undo not yet wired) | LOW |
| DR-FR-7 | `production[]` + `constraints[]` invisible to consumers | HIGH |
| DR-FR-8 | Submit chain heavier when language=es (extra translate round-trip) | MEDIUM |
| DR-FR-9 | Close Window button is silently inert (window.close ignored unless script-opened) | MEDIUM |

---

# 5 · PDF ARCHITECTURE AUDIT

The PDF emitted to the customer / PM / GC / DOT is produced by `pdf_render.py::_render_daily()` and attached to the auto-email pipeline (`server.py:11364-11410`). It is the **single legal artefact** of a Daily Report.

## 5.1 · Current PDF section order

| Section | Content | Always renders? |
|---|---|---|
| 01 · Project Information | project name, #, location, date, report#, prepared_by, superintendent, weather, GPS | ✅ |
| 02 · — | (unused — see DR-PDF-010) | n/a |
| 03 · General Information | schedule_delay_today, weather_impact, accidents, injuries, incident detail, safety escalation block | ✅ |
| 04 · MASCI Crews on Site | crew table + per-row gross/net inline · totals row | when crews present |
| 05 · Subcontractors | subs table + per-sub photo block | when subs present |
| 06 · Visitors | visitors table | when present |
| 07 · Equipment Log | equipment table | when present |
| 08 · Materials Delivered | materials table + ticket photos | when present |
| 09 · Activities Performed | activities table (5 fields: activity, % done, station from/to, notes) | when present |
| 10 · Photos | up to 24 thumbnails inline | always when ≥1 photo |
| 11 · Signatures | prepared_by + superintendent | always |

### 5.2 · Audit footer (separate API)

`GET /api/daily-reports/{id}/audit-footer` returns:
```json
{ "report_id": "...", "doc_id": "DR-2026-...", "sha256": "...", "rendered_at_utc": "...", "footer_text": "Official Record · DR-... · sha256=... · rendered ..." }
```
This is **not currently embedded in the PDF body** — only the doc_id is visible.

## 5.3 · DR-PDF-001 … 020 findings

| Code | Finding | Severity | Pillar fail |
|---|---|---|---|
| **DR-PDF-001** | `production[]` rows (V.2 Wave-1B) stored in Mongo but NOT rendered in PDF | 🔴 HIGH | Powerful · Trusted |
| **DR-PDF-002** | `constraints[]` rows (V.2 Wave-1B) stored in Mongo but NOT rendered in PDF | 🔴 HIGH | Powerful · Trusted |
| **DR-PDF-003** | No executive summary at the top — reader must scan all 11 sections to glean "what happened today" | 🟡 MEDIUM | Simple · Beautiful |
| **DR-PDF-004** | Information hierarchy is purely sequential — no "high-importance" callouts (incidents, delays, RFI signals) | 🟡 MEDIUM | Beautiful |
| **DR-PDF-005** | PDF Section 03 reads `schedule_delay_today` (singular) but the form writes `schedule_delays` (plural). Renderer key mismatch → field shows blank on PDF for many reports | 🔴 HIGH | Trusted |
| **DR-PDF-006** | No photo categorization / labels on PDF (operator can't tell crew shot vs overall vs closeout) | 🟡 MEDIUM | Powerful |
| **DR-PDF-007** | Signature block does not include date/time of signature — only the name | 🟡 MEDIUM | Trusted (legal) |
| **DR-PDF-008** | `audit_envelope_sha256` minted on save but not visible in PDF body (separate endpoint) — tamper-detection invisible to the reader | 🟡 MEDIUM | Trusted |
| **DR-PDF-009** | Weather rendered as single text line — `weather_snapshots[]` hourly granularity lost | 🟢 LOW | (data already absent) |
| **DR-PDF-010** | Section 02 number is unused (jumps from 01 → 03) — minor cosmetic | 🟢 LOW | Beautiful |
| **DR-PDF-011** | Delay/constraint reporting buried as Section 03 free-text only — structured rows with hours_impact + may_require_rfi / may_affect_schedule advisory flags absent | 🔴 HIGH | Powerful |
| **DR-PDF-012** | No per-crew total hours dashboard at top — totals only render at the bottom of the Crews table | 🟡 MEDIUM | Powerful |
| **DR-PDF-013** | Production quantity totals (TON / SY / CY rolled up) not surfaced — every load-heavy job has invisible production data | 🔴 HIGH | Powerful |
| **DR-PDF-014** | Excavation activity / linked excavation IDs not rendered on PDF — Phase 10A-B link invisible to the customer | 🔴 HIGH | Powerful · Trusted |
| **DR-PDF-015** | No lifecycle state stamp on PDF — recipient cannot tell from the PDF whether the DR is still PENDING_REVIEW or already CLOSED | 🟡 MEDIUM | Trusted |
| **DR-PDF-016** | Distribution list (CC roster) not embedded — recipient cannot see who else received the email | 🟢 LOW | Beautiful |
| **DR-PDF-017** | No bilingual support — PDF is English-only regardless of `submit_language` | 🟡 MEDIUM | Powerful |
| **DR-PDF-018** | Mobile viewing untested — a single A4-sized HTML rendered as PDF is fine but on a phone the photo grid columns may wrap awkwardly | 🟢 LOW | Beautiful |
| **DR-PDF-019** | Customer-facing executive metrics absent: total crew hours · total production qty · open incidents count · open RFI candidates | 🔴 HIGH | Powerful |
| **DR-PDF-020** | Printability — base font sizes are tight; OK on letter paper, but no print-CSS hardening test (page-break in middle of crew row possible) | 🟢 LOW | Beautiful |

### 5.4 · Severity rollup

- 🔴 HIGH: DR-PDF-001, 002, 005, 011, 013, 014, 019 (7 findings)
- 🟡 MEDIUM: DR-PDF-003, 004, 006, 007, 008, 012, 015, 017 (8 findings)
- 🟢 LOW: DR-PDF-009, 010, 016, 018, 020 (5 findings)

---

# 6 · MATERIAL MOVEMENT AUDIT

## 6.1 · Inbound material

| Material | Current handling | Status |
|---|---|---|
| Asphalt | `materials[]` row · supplier-combo · ticket_number · ticket_photos[] | ✅ adequate |
| Concrete | `materials[]` row | ✅ adequate |
| Pipe | `materials[]` row · description free-text | ✅ adequate |
| Aggregate | `materials[]` row | ✅ adequate |
| Other (steel, geotech, sand) | `materials[]` row | ✅ adequate |

**Verdict (in-bound):** existing `materials[]` shape is sufficient; the gap is volume validation (FleetWatcher cross-check).

## 6.2 · Outbound material — THE STRUCTURAL GAP

| Material | Current capture method | Capture quality |
|---|---|---|
| Dirt (unsuitable / topsoil / cut) | 🟡 inconsistent — sometimes `production[]` CY · sometimes `activities[]` notes · sometimes `materials[]` (semantically wrong — "Materials Delivered") | 🔴 INCONSISTENT |
| Unsuitable soil | same as dirt | 🔴 INCONSISTENT |
| Millings | 🟡 sometimes `production[]` TON · sometimes free-text only | 🔴 INCONSISTENT |
| Concrete demo | 🟡 sometimes `production[]` CY/EA · sometimes free-text | 🔴 INCONSISTENT |
| Trees | 🟡 sometimes `production[]` EA · usually free-text | 🔴 INCONSISTENT |
| Debris | 🟡 sometimes `production[]` TON · usually free-text | 🔴 INCONSISTENT |
| Trash | usually `general_notes` free-text | 🔴 NOT TRACKED |
| Demo materials | usually `general_notes` free-text | 🔴 NOT TRACKED |
| Truckload count | NO native capture · could come from FleetWatcher | 🔴 NO CAPTURE |
| Disposal ticket # | `materials[]` ticket_number reused (but the form labels this as "incoming") | 🟡 semantic conflict |

## 6.3 · Operational impact

- Foremen author "the same out-bound load" in three different places depending on who trained them. Production reports aggregate inconsistently.
- Owner / DOT requesting "How many CY of dirt did you haul today" requires manual reading + summing free-text — cannot be programmatically rolled up.
- FleetWatcher would canonicalize this domain entirely — see §8.

## 6.4 · Documentation only (no design proposed)

Recommendation: when FW-1 Ticket Ingest is authorized, a successor audit (DR-AUDIT-002 / FW-1 design) will determine whether to:
- (A) extend `materials[]` semantics to include direction (in/out), or
- (B) add an explicit `hauling[]` block fed by FleetWatcher.

Neither is proposed in this audit. **Both would require operator authorization and a Lock #1 review** (does this break the 9-step contract?).

---

# 7 · MOTIVE MAPPING MATRIX

Source-of-truth Motive primitives: `motive_events`, `motive_assets`, `motive_drivers`, `asset_mappings` (Motive ↔ MASCI equipment_id link). DCP-1 + DSI-1 telemetry path already field-proven.

| DR field | Motive can provide? | Classification |
|---|---|---|
| `equipment[*].description` | ✅ via `motive_assets.label` + `asset_mappings.masci_equipment_id` | **AUTO-CAPTURE CANDIDATE** |
| `equipment[*].time_delivered` | ✅ GPS geofence arrival event | **AUTO-CAPTURE CANDIDATE** |
| `equipment[*].time_removed` | ✅ GPS geofence departure event | **AUTO-CAPTURE CANDIDATE** |
| `equipment[*].hours_used` | ✅ engine-hours delta | **AUTO-CAPTURE CANDIDATE** |
| `equipment[*].notes` | ❌ operator narrative | MANUAL REQUIRED |
| `masci_crews[*].name` | 🟡 PARTIAL — Motive knows the driver, not the crew | VERIFICATION CANDIDATE (never auto-fill) |
| `masci_crews[*].start_time` | 🟡 PARTIAL — vehicle ignition-on for driver only | VERIFICATION CANDIDATE |
| `masci_crews[*].stop_time` | 🟡 PARTIAL — same | VERIFICATION CANDIDATE |
| `masci_crews[*].hours` | KEEP — foreman authority | MANUAL REQUIRED |
| `weather_summary` | Already auto via Weather API + GPS | — |
| `gps_lat`, `gps_lng` | Already auto via browser geolocation; Motive could cross-verify | — |
| `subcontractors[*]` | ❌ Motive doesn't see subs unless they're on a Motive-managed unit | MANUAL REQUIRED |
| `materials[]` | ❌ Motive isn't a delivery system (see FleetWatcher §8) | MANUAL REQUIRED |
| `excavation_activity_today` | ❌ Motive can't infer activity from equipment presence | MANUAL REQUIRED |
| `production[]` quantities | ❌ field judgement | MANUAL REQUIRED |
| `constraints[]` weather/equipment downtime | 🟡 `motive_events` (fault · idle-on) could SIGNAL | VERIFICATION CANDIDATE (signal only) |
| `safety_incidents_today` / `injuries_reported` | ❌ never automate | MANUAL REQUIRED (sacrosanct) |
| `photos[]` | ❌ field-authored | MANUAL REQUIRED |
| `signatures` | ❌ legal | MANUAL REQUIRED |

### 7.1 · Motive sprint candidates (audit-only · no build)

| Candidate | What | Pillar pass |
|---|---|---|
| M-DR-1 | Equipment auto-discovery — server queries assets within job geofence on report_date; pre-fills `equipment[]` as candidates; foreman taps to confirm | ✅✅✅✅✅ |
| M-DR-2 | Engine-hours verify — quiet "Motive: 7.2 hrs" badge under foreman-entered hours; never overwrites | ✅✅✅✅✅ |
| M-DR-3 | Equipment-fault signal — `motive_events.event_kind == 'fault'` while on job today → quiet chip "Equipment fault detected — add constraint?" | ✅✅✅✅✅ |

### 7.2 · Motive NEVER list (anti-patterns)

- Never auto-create the equipment row without foreman confirmation (breaks Trusted).
- Never use Motive driver name as `prepared_by` (driver ≠ DR author).
- Never auto-close a DR because Motive says "no equipment on site."
- Never auto-populate `masci_crews[]` from Motive (crew ≠ drivers).

---

# 8 · FLEETWATCHER MAPPING MATRIX

Source: `FWA1_FLEETWATCHER_FORENSIC_AUDIT.md` (research-only · NOT yet integrated).

| DR field | FleetWatcher can provide? | Classification |
|---|---|---|
| `materials[*].description` (asphalt mix / millings / dirt / aggregate) | ✅ load ticket carries mix/category | AUTO-CAPTURE CANDIDATE (future) |
| `materials[*].quantity` + `unit` | ✅ net tonnage / CY per ticket | AUTO-CAPTURE CANDIDATE |
| `materials[*].supplier` | ✅ plant of origin | AUTO-CAPTURE CANDIDATE |
| `materials[*].ticket_number` | ✅ FW master ticket id | AUTO-CAPTURE CANDIDATE |
| `materials[*].ticket_photos[]` | 🟡 NO — FW has digital ticket but not foreman's photo. Keep both | KEEP MANUAL ALONGSIDE |
| **Out-bound hauling** (dirt / millings / debris / trees / disposal) | ✅✅✅ FW's strongest domain | **AUTO-CAPTURE CANDIDATE** (top opportunity) |
| Truck cycle count | ✅ | AUTO-CAPTURE CANDIDATE |
| Truck load count | ✅ | AUTO-CAPTURE CANDIDATE |
| Plant activity (asphalt plant calls / silo levels) | ✅ | AUTO-CAPTURE CANDIDATE |
| Milling activity quantities | ✅ | AUTO-CAPTURE CANDIDATE |
| Export quantities (any out-bound TON / CY) | ✅ canonical | AUTO-CAPTURE CANDIDATE |
| `production[]` rows | 🟡 PARTIAL — for hauling-heavy jobs, FW totals could pre-fill a production row (foreman confirms) | VERIFICATION CANDIDATE |
| Disposal tickets | ✅ when FW captures hauler → disposal-site receipt | AUTO-CAPTURE CANDIDATE |

### 8.1 · FleetWatcher sprint candidates (audit-only)

| Candidate | What | Pillar pass |
|---|---|---|
| FW-1 Load-Ticket Ingest | Build the FW → ForgedOps ticket ingest service (P0 per OGA-1) | ✅✅✅✅✅ |
| FW-DR-1 | Pre-populate `materials[]` from today's FW tickets for matching project_number | ✅✅✅✅✅ |
| FW-DR-2 | Auto-derive a `production[]` row when FW total tonnage > 0 (foreman confirms) | ✅✅✅✅✅ |
| FW-DR-3 | New "Hauling Activity Today" gated by `hauling_today` Yes/No, pre-filled from FW | ❌ adds a 10th section → **Lock #1 violation** — DEFER unless operator amends contract |

### 8.2 · FleetWatcher missing-capture gaps (today)

- Out-bound dirt / millings / debris / trees / disposal — none of these are programmatically captured on DR today (see §6.2).
- Truck cycle metrics — none.
- Plant call-out timing — none.
- Compaction / spread rate — none.

These represent **the largest single capture-gap on the platform.** All blocked by FW-1.

---

# 9 · MAINTAINX MAPPING MATRIX

MaintainX **IS** integrated (services/maintainx_*.py + live asset sync + work-order ingestion). It is the system of record for asset registry + work orders.

| Concept | MaintainX role | DR role | Belongs where |
|---|---|---|---|
| Asset registry | ✅ canonical | DR uses descriptions | **MaintainX** |
| Work orders | ✅ canonical | DR doesn't track | **MaintainX** |
| Equipment downtime event | ✅ canonical | DR could signal "Equipment X kept down — should be excluded" | **MaintainX** + cross-link |
| Open work order on a DR equipment row | — | "Open WO: #1234 · Coolant leak" chip under the row would close the loop | **Link / read-only on DR** |
| Equipment _present on a job today_ | not Maintain's job | ✅ DR foreman authority | **Daily Report** |
| Hours used | not Maintain's job | ✅ DR (with Motive verify) | **Daily Report** |
| OOS / out-of-service flag | ✅ canonical | DR cross-check candidate | **MaintainX + signal on DR** |

### 9.1 · MaintainX sprint candidates (audit-only)

| Candidate | What | Pillar pass |
|---|---|---|
| MX-DR-1 | Read-only "Open WO" chip under each DR equipment row | ✅✅✅✅✅ |
| MX-DR-2 | Mismatch banner: "Equipment X on this DR but OOS in MaintainX" | ✅✅✅✅✅ |

### 9.2 · Never duplicate

- ❌ Never duplicate the MaintainX work-order list inside the DR.
- ❌ Never let the DR mutate MaintainX state (read-only link).
- ❌ Never let MaintainX prevent a DR from being submitted (e.g. "equipment is OOS, refusing DR" — breaks Powerful).

---

# 10 · COACHING AUDIT

| Panel | Read-time | Mobile? | Translation (es)? | Operational value | Verdict |
|---|---|---|---|---|---|
| `daily-report` header HelpTipBlock | 4–8 s | ✅ collapsible | ✅ via useT | Onboarding nudge | KEEP |
| `daily-report.crew` (iter360 identity coaching) | 6–10 s | ✅ | ✅ | High — crew identity discipline | KEEP · SIMPLIFY to 1 line |
| `daily-report.equipment` | 4–8 s | ✅ | ✅ | Marginal — equipment is self-explanatory | SIMPLIFY |
| `daily-report.materials` | 4–8 s | ✅ | ✅ | High — "tickets matter for disputes" | KEEP |
| `daily-report.narrative` | 4–8 s | ✅ | ✅ | Marginal | SIMPLIFY |
| `daily-report.photos` | 4–8 s | ✅ | ✅ | High — OSHA framing | KEEP |
| Safety escalation red block (Section 03 when YES) | 15+ s of stop-the-line copy | ✅ | ✅ | **CRITICAL** — stops submission until safety chain complete | **KEEP, do not touch** |
| `DailyReportExcavationActivity` "Coaching, not punishment" amber strip | 10 s wall of text | ✅ | ✅ | Field reports as bloat | SIMPLIFY to 1 line |
| `CrewSetupRestorePrompt` | 3 s | ✅ | ✅ | Excellent calm tier-3 confidence copy | KEEP |
| 8 × `OshaCoachingBlock` on excavation form (adjacent) | Permanent | ✅ | ✅ | Most foremen swipe past | HIDE by default · show on field-focus (Excavation directive, not DR) |

### 10.1 · Aggregate

- **Current cumulative happy-path coaching read-time:** ≈35 s
- **Doctrine target (`ODR_SIMPLICITY_TEST_DOCTRINE.md`):** ≤12 s
- **Verdicts:** KEEP × 5 · SIMPLIFY × 4 · REMOVE × 0 · EXPAND × 0

### 10.2 · Translation quality

All HelpTipBlock keys flow through `useT()` and have ES strings in `lib/i18n.js`. The `submit_language` field on each DR captures the language at submit — but the PDF renders in English regardless (DR-PDF-017 noted).

---

# 11 · FIELD FINDINGS REPORT

Codes prefixed `DR-F-***`. Where evidence is in the codebase, file/line is cited.

| Code | Finding | Severity | Evidence | Pillar fail |
|---|---|---|---|---|
| **DR-F-001** | Free-text `prepared_by` cannot reliably identify foremen with same first name | HIGH | `daily_reports.py:80-86` (no directory bind) · `DAILY_REPORT_OWNERSHIP_AUDIT.md` F2 | Trusted |
| **DR-F-002** | Kicked-back DRs may not reach the field submitter (FSI binding optional; fallback = silent) | HIGH | `daily_report_lifecycle.py:161-187` (FSI conditional) | Trusted |
| **DR-F-003** | `employees` directory has only 1 row with an email — even directory-bound prepared_by can't deliver to most | HIGH | `DAILY_REPORT_OWNERSHIP_AUDIT.md` F3 | Trusted |
| **DR-F-004** | No public-gate revision URL outside the kickback path — submitter can only duplicate | MEDIUM | `DAILY_REPORT_OWNERSHIP_AUDIT.md` F4 | Trusted |
| **DR-F-005** | 11 default-visible sections at 5:30 AM | MEDIUM | `NewDailyReport.jsx` Sections 01-11 | Simple |
| **DR-F-006** | Triple "Project / Crew / Photos / Signature / Excavation" status indicators | MEDIUM | `DAILY_REPORT_SIMPLIFICATION_AUDIT.md` §2 | Simple · Beautiful |
| **DR-F-007** | `superintendent` not auto-pulled from `jobs_master.superintendent` | LOW | `DAILY_REPORT_SIMPLIFICATION_AUDIT.md` §4 gap F-A | Trusted |
| **DR-F-008** | 8 always-visible `OshaCoachingBlock` on excavation form (foremen swipe past) | LOW | `DAILY_REPORT_SIMPLIFICATION_AUDIT.md` §6 | Simple |
| **DR-F-009** | `weather_snapshots[]` granular array stored but never rendered | LOW | `pdf_render.py` (only `weather_summary` rendered) | (data bloat) |
| **DR-F-010** | "Use Yesterday" requires tap; silent auto-apply not yet wired | LOW | `DAILY_REPORT_SIMPLIFICATION_AUDIT.md` §7 | Simple |
| **DR-F-011** | Equipment list typed by hand — Motive could pre-fill (M-DR-1) | LOW | §7 | Simple (huge upside) |
| **DR-F-012** | Dispatch / Shop / FL have no DR read surface despite operational overlap | LOW | §3 | Powerful |
| **DR-F-013 · "Submit freeze"** | Heavy-payload submit → translate→idempotency→upload chain may block UI for seconds; spinner visible but no progress; no abort | MEDIUM | `NewDailyReport.jsx:741-857` (synchronous chain) · `payloadIsHeavy` soft-warn at line 2203 only fires AFTER they hit submit-time | Simple · Trusted |
| **DR-F-014 · "File Another" works** | File Another button navigates correctly to `returnTo` (`/daily/submit`) | ✅ OK | `ThankYou.jsx:107-115` | — |
| **DR-F-015 · "Close Window" silently inert** | `<a onClick={... window.close()}>` is ignored by all major browsers unless the window was script-opened. Field crews opening via QR/email URL get a button that does nothing | MEDIUM | `ThankYou.jsx:117-126` | Trusted · Beautiful (user-facing button does nothing) |
| **DR-F-016 · Slow submission for ES users** | When `language === "es"`, an extra `translateUserInput()` LLM round-trip runs before the submit POST | MEDIUM | `NewDailyReport.jsx:749-754` | Simple |
| **DR-F-017 · Quantity unit limitations** | Closed enum {LF, SY, CY, TON, EA, ACRE, OTHER} via `custom_unit_label`. MGAL / LB / EACH not in the set — operators use OTHER + custom label | LOW | `daily_reports.py:29` · `NewDailyReport.jsx:1958-1959` | Powerful |
| **DR-F-018 · Safety Meeting PDF ordering (adjacent module)** | Out-of-scope here but the directive named it; tracked under Safety Meeting audit, not DR | (deferred) | — | — |
| **DR-F-019 · Project auto-fill concerns** | JobPicker pulls jobs_master but `superintendent` is not auto-filled (= DR-F-007). Otherwise auto-fill is functional | LOW | JobPicker module + `daily_reports.py:80-86` | Trusted |
| **DR-F-020 · Weather workflow concerns** | GPS + Weather API auto-fills `weather_summary`. `weather_snapshots[]` stored but invisible. No hour-by-hour rendering on PDF | LOW | `pdf_render.py` Section 01 · `dailyReportSchema.js` lines 25-27 | Beautiful · Powerful |
| **DR-F-021 · `schedule_delay_today` vs `schedule_delays` field mismatch** | PDF Section 03 reads key `schedule_delay_today` (singular) but form writes `schedule_delays` (plural). Many PDFs show this field blank | HIGH | `pdf_render.py:239` vs `NewDailyReport.jsx`:`set("schedule_delays", v)` | Trusted (this is DR-PDF-005 dual-listed) |
| **DR-F-022 · Production / constraints stored, invisible to consumers** | `production[]` and `constraints[]` (V.2 Wave-1B) are written to Mongo but absent from both PDF and ViewDailyReport | HIGH | `pdf_render.py::_render_daily()` · `ViewDailyReport.jsx` (no production/constraint references) | Powerful · Trusted |

### 11.1 · Field-issue reservation

The codes **DR-H1-001 / DR-H1-002 / DR-H1-003** referenced in the directive returned **zero hits** across `/app/backend`, `/app/frontend`, `/app/memory`. Recommend operator files them into `/app/memory/DR_FIELD_OBSERVATIONS_H1.md` so this audit can be re-run against them with direct evidence.

---

# 12 · CONSTITUTIONAL CERTIFICATION

Per-section evaluation: PASS · CONDITIONAL PASS · FAIL — against the 5 pillars.

| Section | Powerful | Simple | Beautiful | Trusted | Proven | Verdict |
|---|---|---|---|---|---|---|
| 01 · Project Info | ✅ | 🟡 (location free-text) | ✅ | 🟡 (superintendent not bound to jobs_master) | ✅ | **CONDITIONAL PASS** (F-007, F-019) |
| 02 · Weather | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 03 · General Info (incl. safety escalation) | ✅ | 🟡 (4 Yes/No + duplicated by `constraints[]`) | ✅ | ✅ | ✅ | **CONDITIONAL PASS** (post-V.2 dedup needed) |
| 03b · Excavation Activity gate | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** (Phase 10A-B best-in-class) |
| 04 · MASCI Crews | ✅ | 🟡 (manual roster; auto-apply tap needed) | ✅ | 🔴 (free-text crew name = F-001) | ✅ | **CONDITIONAL PASS** |
| 05 · Subcontractors | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 06 · Visitors | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 07 · Equipment | ✅ | 🟡 (manual entry; Motive auto-discovery would lift Simple) | ✅ | ✅ | ✅ | **CONDITIONAL PASS** (F-011) |
| 08 · Materials (inbound only) | ✅ | 🟡 (semantic conflict for outbound — §6) | ✅ | ✅ | ✅ | **CONDITIONAL PASS** |
| 09 · Activities (legacy) | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 09b · Production (V.2 Wave-1B) | 🔴 invisible to consumers | ✅ | ✅ | 🔴 stored but unverifiable by reader | ✅ | **FAIL** (DR-PDF-001 · DR-PDF-013 · F-022) |
| 10 · Constraints (V.2 Wave-1B) | 🔴 invisible to consumers | ✅ | ✅ | 🔴 stored but unverifiable | ✅ | **FAIL** (DR-PDF-002 · DR-PDF-011 · F-022) |
| 10 · Photos (min 6) | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 11 · Sign-Off | ✅ | ✅ | ✅ | 🟡 (no date/time on signature; SHA256 invisible in PDF body) | ✅ | **CONDITIONAL PASS** (DR-PDF-007 · DR-PDF-008) |
| Lifecycle (OC-002) | ✅ | ✅ | ✅ | 🟡 (kickback notification F-002) | ✅ | **CONDITIONAL PASS** |
| PDF emission | 🔴 production + constraint + excavation absent | 🟡 no exec summary | 🟡 sequential, no hierarchy | 🔴 schedule_delays key mismatch · SHA256 not in body | ✅ | **CONDITIONAL PASS** (7 HIGH PDF gaps) |
| Read view (`ViewDailyReport`) | 🔴 production + constraint absent | ✅ | ✅ | 🟡 | ✅ | **CONDITIONAL PASS** |
| Thank-You page | ✅ | ✅ | ✅ | 🟡 (Close Window inert — F-015) | ✅ | **CONDITIONAL PASS** |
| HR portal (read-only) | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| Safety portal (flagged-only) | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| Coaching layer | 🟡 | 🔴 (35 s vs 12 s target) | ✅ | ✅ | ✅ | **CONDITIONAL PASS** |
| FSI Tier-1 binding | ✅ | ✅ | ✅ | 🟡 (binding-optional fallback can silence kickback) | ✅ | **CONDITIONAL PASS** |
| Audit envelope SHA256 | ✅ | ✅ | ✅ | 🟡 (not embedded in PDF body) | ✅ | **CONDITIONAL PASS** |

### 12.1 · Section-level verdict rollup

- **PASS:** 8 sections
- **CONDITIONAL PASS:** 13 sections
- **FAIL:** 2 sections (Production V.2 · Constraints V.2 — both because PDF + ViewDailyReport rendering is missing)

### 12.2 · Net verdict

🟡 **CONDITIONAL PASS** — the Daily Report system passes the foundational test (Powerful · Proven on the field side) but has **two outright FAIL** sections (Production V.2 and Constraints V.2 invisibility to consumers) and 13 conditional passes that, taken together, prevent a clean 5-pillar certification.

**The Daily Report is operationally sound today, but the V.2 Wave-1B work (Production + Constraints) is currently latent — written but unread. Until those rows surface in the PDF + ViewDailyReport, the structured uplift delivers ZERO downstream value despite being collected.**

---

# 13 · RECOMMENDATIONS · PILLAR-GATED

Every recommendation explicitly passes Powerful · Simple · Beautiful · Trusted · Proven.

## 13.1 · Recommended Changes (12 items · ranked by leverage)

| # | Recommendation | Pillar pass | Leverage |
|---|---|---|---|
| **R1** | Surface `production[]` rows on PDF + ViewDailyReport (close DR-PDF-001 · DR-PDF-013 · F-022) | ✅✅✅✅✅ | 🔴 HIGHEST — closes 2 FAIL sections |
| **R2** | Surface `constraints[]` rows on PDF + ViewDailyReport (close DR-PDF-002 · DR-PDF-011 · F-022) | ✅✅✅✅✅ | 🔴 HIGHEST |
| **R3** | Fix `schedule_delay_today` ↔ `schedule_delays` key mismatch in PDF renderer (DR-PDF-005 · DR-F-021) | ✅✅✅✅✅ | 🔴 silent data corruption today |
| **R4** | Add executive summary block at PDF top (DR-PDF-003 · DR-PDF-019) | ✅✅✅✅✅ | HIGH |
| **R5** | Add PDF audit footer with embedded SHA256 + lifecycle state (DR-PDF-008 · DR-PDF-015) | ✅✅✅✅✅ | HIGH |
| **R6** | Excavation activity + linked IDs on PDF (DR-PDF-014) | ✅✅✅✅✅ | HIGH |
| **R7** | Auto-pull `superintendent` from `jobs_master.superintendent` (DR-F-007) | ✅✅✅✅✅ | LOW effort, high trust gain |
| **R8** | Silent auto-apply yesterday's crew + equipment + 5-s undo (DR-F-010) | ✅✅✅✅✅ | HIGH |
| **R9** | Bind `prepared_by` to directory ref / FSI binding (DR-F-001) | ✅✅✅✅✅ | HIGH (Trusted) |
| **R10** | Kickback notification: in-app bell to FSI-bound submitter when binding missing fall-back to admin (DR-F-002) | ✅✅✅✅✅ | HIGH |
| **R11** | Motive M-DR-1 equipment auto-discovery (verify-only) (DR-F-011) | ✅✅✅✅✅ | HIGH |
| **R12** | Replace inert "Close Window" with "Done" return-link (DR-F-015) | ✅✅✅✅✅ | LOW effort, user-facing fix |

## 13.2 · Recommended Removals

| # | Remove | Risk | Pillar |
|---|---|---|---|
| RM-1 | `weather_snapshots[]` granular array | LOW (never rendered) | Simple |
| RM-2 | `gps_accuracy` field | LOW (never rendered) | Simple |
| RM-3 | `schedule_delays_notes` (post-V.2, after one DR cycle to confirm `constraints[]` adoption) | LOW | Simple |
| RM-4 | `weather_impact_notes` (same condition) | LOW | Simple |
| RM-5 | "Coaching, not punishment" amber wall on `DailyReportExcavationActivity` → collapse to 1 line | LOW | Simple |

## 13.3 · Recommended Auto-Populations

| Field | Source | Trust gate |
|---|---|---|
| `superintendent` | `jobs_master.superintendent` | none required |
| `masci_crews[]` suggestions | last DR per project_number | foreman undo toast |
| `equipment[]` candidates | Motive `motive_assets` GPS-on-job | foreman tap-to-confirm |
| `materials[]` rows (after FW-1) | FleetWatcher load tickets | foreman tap-to-confirm |
| Equipment hours quiet verify | Motive engine-hours delta | display-only |
| `prepared_by` | FSI binding when available | foreman can override |

## 13.4 · Recommended Future Integrations

| Sprint | What | Pillar gate | Lock #1? |
|---|---|---|---|
| FW-1 | FleetWatcher Ticket Ingest (P0 per OGA-1) | ✅✅✅✅✅ | doesn't touch DR yet |
| MX-DR-1 | MaintainX Open-WO chip under DR equipment rows | ✅✅✅✅✅ | OK (additive, no new section) |
| MX-DR-2 | Shop mismatch banner (DR equipment vs MaintainX OOS) | ✅✅✅✅✅ | OK (no DR change — Shop hub surface only) |
| FW-DR-1 | Pre-populate `materials[]` from FW tickets | ✅✅✅✅✅ | OK (uses existing section) |
| FW-DR-2 | Pre-populate `production[]` from FW tonnage | ✅✅✅✅✅ | OK |
| FW-DR-3 | NEW "Hauling Activity Today" section | ❌ Lock #1 violation (10th step) | **DEFER unless operator amends contract** |

## 13.5 · Items the platform must NEVER automate

| Field | Reason |
|---|---|
| Photos | Field-authored evidence |
| Signatures | Legal weight |
| `safety_incidents_today` / `injuries_reported` Y/N | Stop-the-line gate |
| `safety_notified` / `incident_report_filled` | Attestation |
| `production[]` quantities | Foreman judgment |
| `constraints[]` rows | Foreman judgment (Motive may signal, never create) |
| `general_notes` | Narrative — automation silences the field |
| `lifecycle_state` transition to CLOSED | Two-flag attestation required (office_review_complete + payroll_inputs_verified) |
| `masci_crews[]` from Motive | Crew ≠ drivers |

---

# 14 · STOP CONDITION ACKNOWLEDGED

**This directive ends with documentation only.**

- ✅ No code modified
- ✅ No schemas changed
- ✅ No APIs changed
- ✅ No PDFs changed
- ✅ No fields added or removed
- ✅ No integrations added
- ✅ No automation added
- ✅ No deploys
- ✅ No designs proposed beyond textual recommendation

Every recommendation R1–R12 + RM-1–RM-5 + 5 future integrations remains a **proposal** awaiting your individual authorization. The path forward is yours to set.

---

# 15 · FILE EVIDENCE INDEX

Source files read for this audit (read-only):

**Backend**
- `/app/backend/routes/daily_reports.py` (566 lines)
- `/app/backend/routes/daily_report_lifecycle.py` (257 lines)
- `/app/backend/routes/safety_portal/daily_reports.py` (75 lines)
- `/app/backend/lib/workflow_state_machine.py` (DR block · lines 215-283 + OC-007 lines 287-310)
- `/app/backend/pdf_render.py` (lines 209-504 = `_render_daily`)
- `/app/backend/server.py` (lines 11364-11410 = auto-email pipeline)
- `/app/backend/services/motive_service.py`
- `/app/backend/services/maintainx_client.py`
- `/app/backend/lib/field_submitter_identity.py`
- `/app/backend/routes/field_revision.py`

**Frontend**
- `/app/frontend/src/lib/dailyReportSchema.js` (107 lines)
- `/app/frontend/src/pages/NewDailyReport.jsx` (2,291 lines)
- `/app/frontend/src/pages/ViewDailyReport.jsx` (678 lines)
- `/app/frontend/src/pages/DailyReportsDashboard.jsx` (228 lines)
- `/app/frontend/src/pages/HrDailyReports.jsx` (422 lines)
- `/app/frontend/src/pages/ThankYou.jsx` (132 lines)
- `/app/frontend/src/components/trench/DailyReportExcavationActivity.jsx` (220 lines)
- `/app/frontend/src/components/DailyReportLifecyclePanel.jsx` (66 lines)
- `/app/frontend/src/lib/i18n.js` (DR-specific keys throughout the 6,000-line dictionary)

**Doctrine / prior audits**
- `/app/memory/DAILY_REPORT_OWNERSHIP_AUDIT.md`
- `/app/memory/DAILY_REPORT_SIMPLIFICATION_AUDIT.md`
- `/app/memory/DAILY_REPORT_FIELD_SIMPLICITY_CERTIFICATION.md`
- `/app/memory/DAILY_REPORT_FIELD_TRUST_REVIEW.md`
- `/app/memory/DAILY_REPORT_EVOLUTION_PLAN.md`
- `/app/memory/PRODUCTION_TRACKING_CERTIFICATION.md`
- `/app/memory/PM_EXPOSURE_TILE_CERTIFICATION.md`
- `/app/memory/DAILY_REPORT_AUDIT_FOOTER_CERTIFICATION.md`
- `/app/memory/FWA1_FLEETWATCHER_FORENSIC_AUDIT.md`
- `/app/memory/LIVE_PRODUCTION_MAINTAINX_AUDIT.md`
- `/app/memory/OGA1_OPERATIONAL_GAP_ANALYSIS.md`
- `/app/memory/ODR_SIMPLICITY_TEST_DOCTRINE.md`
- `/app/memory/OA1_OPERATIONS_ACTIONS_CONSTITUTION.md` (terminology reference)

— Forked main agent · DR-AUDIT-001-FULL · 2026-06-08
— Audit complete. Awaiting operator directive on R1–R12.
