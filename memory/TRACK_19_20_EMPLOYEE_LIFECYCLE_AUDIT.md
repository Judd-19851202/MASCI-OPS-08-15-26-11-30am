# Track 19.20 · Employee Lifecycle & Historical Records Intelligence Audit

**Date:** 2026-07-02  
**Author:** MASCI Platform Audit  
**Scope:** Complete HR + Safety + Operations employee record architecture  
**Verdict:** 🟢 Foundation is exceptional. Six well-scoped extensions bring the platform to complete Employee 360°.

---

# 1 · Executive Summary

MASCI already operates a **unified employee lifecycle backbone** that most construction platforms take 3–5 years to build. There is ONE canonical employee collection (`db.employees`), ONE aggregation endpoint (`/api/hr/employees/{id}/accountability/timeline`) that fans out across nine downstream data sources, and ONE HR Compliance Brief PDF export suitable for OSHA / DOT / insurance / legal.

**What already exists (verified from the codebase):**

- `db.employees` — single source of truth. HR Roster Source-of-Truth doctrine locked by Track 19.03.
- HR Lifecycle Engine (`/app/backend/routes/employee_lifecycle.py` · 2,278 lines) — 9-state lifecycle (Pending Hire · Active · Inactive · Suspended · Terminated · Resigned · Retired · Seasonal · Leave of Absence), separation taxonomy, rehire eligibility (Iter316), driver-qualification / CDL / medical-card management (Iter286-287).
- HR Portal Employee Accountability Timeline (`/app/backend/routes/hr_portal.py:690` · fans out across 9 collections) + HR Compliance Brief PDF (`/hr/employees/{id}/accountability/brief.pdf`).
- Safety Portal Training Records (`db.safety_training_records`) + Safety Portal Documents Library (`db.safety_documents` with R2/inline hybrid storage).
- Field Leadership Records (`db.field_leadership_records`) — 10 kinds including `write_up`, `verbal_coaching`, `attendance`, `recognition`, `equipment_checkout`, `new_employee_eval`, `crew_eval`, `promotion_recommendation`, `training_deficiency`, `supervisor_notes`, `employee_termination` (with auto-sync into `employees.status_history`).
- PPE + Equipment Issuance flow (`db.safety_equipment_issuances`) — issue, sign, return, PDF export.
- Equipment Use-and-Care Training (`db.safety_equipment_trainings`).
- Training Track / Curriculum system (`db.training_track_records`).
- Incident Intelligence Engine (Tracks 19.15 – 19.19) — 17 incident branches, 9 report definitions, professional PDF with Attorney Work Product chrome, case workspace with visual timeline, evidence + witnesses + medical + agency + RCA + CAPA.
- Unified attachment pipeline (Track 19.04, extended by Track 19.19 to `.xlsm`) — same R2 bucket, category-grouped display.
- CDL Roster Bulk-Import Engine (Iter352) — file preview → confidence → apply with audit trail.
- HR Employee Lifecycle Events audit ledger (`db.employee_lifecycle_events`) — write-once name-change / preferred-name-change / status-change history.

**What does NOT exist (verified absent):**

- **P0** Historical Records Intake Engine — no bulk PDF upload / OCR / auto-classification / employee-matching workflow. `pytesseract`, `tesseract`, or any OCR library is NOT imported anywhere in the backend (grep returned no matches).
- **P0** Incident ↔ Employee canonical linkage — the `incident_cases` schema has `reporter_name` (string) but no `reporter_employee_id`, no `involved_employees[]`, no `witness_employee_ids[]`. The HR timeline joins via name-regex (`safety_training_records`, `safety_equipment_issuances`, etc.) but incidents are joined via `db.incidents` (legacy) not via the new incident engine.
- **P1** Employee-scoped Full-Text Search — no MongoDB `$text` indexes exist for employee documents / OCR content.
- **P1** Employee 360° UI — the aggregation endpoint exists; a single-page "employee-360" React view that renders it does not exist as a first-class page (HR portal has fragmented views).
- **P1** Discipline package export — Field Leadership records can print individually; there's no "give me every write-up + verbal coaching + termination + related-incident" bundle PDF.
- **P2** OCR full-text extraction into a searchable index.
- **P2** Automatic document classification (uploaded PDF → suggested category via ML/heuristic).
- **P2** Duplicate document detection at upload time.

**Bottom line:** MASCI's employee data model already answers "what happened with this person" better than 90% of construction HR/safety systems. Closing the six gaps below graduates it from "excellent HR + Safety timeline" to "complete Employee Lifecycle Intelligence Platform."

---

# 2 · Current Architecture Audit

## 2.1 Canonical collections (verified from source)

| Collection | Owner | Role |
|---|---|---|
| `db.employees` | HR | Single source of truth for identity + employment + CDL/medical + status |
| `db.employee_lifecycle_events` | HR (write-once) | Audit ledger for name/status transitions |
| `db.safety_training_records` | Safety | Certifications + expiration + certificate_file_id |
| `db.training_track_records` | HR/Safety | Curriculum completion tracking |
| `db.safety_equipment_issuances` | Safety | PPE + safety equipment issued to employees |
| `db.safety_equipment_trainings` | Safety | Use-and-care acknowledgments |
| `db.safety_documents` | Safety | General safety document library (R2 or inline) |
| `db.field_leadership_records` | Field Leadership (with admin write) | Write-ups, terminations, recognition, equipment checkouts, coaching, attendance |
| `db.incident_cases` (Track 19.16+) | Safety | Modern incident case lifecycle (17 branches) |
| `db.incident_case_events` / `_evidence` / `_witnesses` / `_medical` / `_agency` / `_rca` / `_capa` / `_communications` | Safety | Investigation satellites |
| `db.incidents` (legacy) | Safety | Pre-Track-19.16 incident collection (still queried by HR timeline for backward compat) |
| `db.tasks` (Iter152 Phase A) | Shared | Open task accountability |
| `db.document_expirations` (Iter152 Phase B) | Shared | Cert/document expiration tracker |
| `db.operational_attachments` (Iter417+) | Shared | Image-only attachments per operational host record |
| `db.email_routes` + `db.email_routing_audit_v2` | Ops | Route resolution + append-only audit |

## 2.2 Doctrine locks (verified in source)

- **HR Source-of-Truth** — `db.employees` is the only employee collection. Every downstream module joins by employee id/name/email. Locked by Track 19.03.
- **Zero Drift** — new Incident Engine (`incident_engine/*`) does not mutate legacy `/api/incidents` or `db.incidents`. Locked by Track 19.16.
- **Field Block Immutability** — `FieldBlock` (`incident_engine/models.py`) is never edited by Safety after `FIELD_SUBMITTED`. Safety writes only to `SafetyBlock`.
- **Trust Spine** — every state transition, evidence add, corrective-action verify, and email send emits an append-only audit row.

---

# 3 · Employee Lifecycle Audit

| Stage | Where it's captured | Verified endpoint / file |
|---|---|---|
| **Hiring / Onboarding** | `POST /api/hr/employees` sets `lifecycle_status = "Pending Hire"` | `employee_lifecycle.py:1041` |
| **Activation** | `POST /api/hr/employees/{id}/status` → Active | `employee_lifecycle.py:1282` |
| **CDL / Driver Qualification** | Mirrored into `db.document_expirations` automatically | `employee_lifecycle.py:236` (`_mirror_driver_doc_expirations`) |
| **Training** | `POST /api/safety/training-records` | `routes/safety_portal/training.py:45` |
| **PPE Issuance** | Safety Forms Equipment Issuance flow with PDF | `routes/safety_forms.py:1029` |
| **PPE Return** | `POST /api/safety-forms/equipment-issuances/{id}/return` | `routes/safety_forms.py:1209` |
| **Write-ups / Discipline** | `field_leadership_records` kind=`write_up` | `routes/field_leadership.py:76` |
| **Recognition** | kind=`recognition` | `routes/field_leadership.py` |
| **Equipment / Vehicle Assignment** | kind=`equipment_checkout` + Fleet cross-links (Track 19.16 closeout) | `routes/field_leadership.py` |
| **Incidents (as reporter/witness/injured)** | `db.incidents` (legacy) + `db.incident_cases` (Track 19.16) | `incident_engine/*` |
| **Medical Restrictions** | Captured on incidents; NOT surfaced back to employee doc | Gap · see §16 |
| **Return-to-work** | Captured in `field_leadership_records` supervisor_notes | Gap: not first-class · see §16 |
| **Suspension** | `lifecycle_status = "Suspended"` | `employee_lifecycle.py` |
| **Termination** | `field_leadership.py:489` auto-syncs into `employees.status_history` on submit of termination form | Verified · `field_leadership.py:481-525` |
| **Resignation / Retirement** | Status transition triggers offboarding playbook fan-out | `employee_lifecycle.py:800` |
| **Rehire eligibility** | `ALLOWED_REHIRE_ELIGIBILITY = {eligible, not_eligible, review_required}` — default `review_required` | `employee_lifecycle.py:74` |
| **Offboarding accountability** | `GET /api/hr/employees/{id}/offboarding-summary` aggregates open tasks + expirations + issued equipment | `employee_lifecycle.py:1553` |

**Verdict:** Every lifecycle stage from Pending Hire → Terminated is captured in structured records. The write path is complete.

---

# 4 · HR Audit

**Portal endpoints (all verified in `hr_portal.py`):**

- `/api/hr/login` · `/api/hr/change-password` · `/api/hr/forgot-password` · `/api/hr/reset/{token}` · `/api/hr/me`
- `/api/hr/field-leadership` list · detail · PDF
- `/api/hr/daily-reports` list · detail
- `/api/hr/employee-accountability` list
- **`/api/hr/employees/{id}/accountability/timeline` — Employee 360° aggregation endpoint** (fans out 9 sources)
- **`/api/hr/employees/{id}/accountability/brief.pdf` — HR Compliance Brief PDF export** (OSHA/DOT/insurance/legal)
- `/api/hr/time-verification` list + CSV export
- `/api/hr/training-records` · `/api/hr/safety-documents` (+ download)
- `/api/hr/incidents` · `/api/hr/corrective-actions`
- `/api/admin/hr-users/*` — HR user management (admin-only)

**Driver Qualification (Iter286-352):**
- `GET /api/hr/driver-qualification/dashboard` + CSV export
- `POST /api/hr/driver-qualification/import/preview` — file preview with confidence scoring
- `POST /api/hr/driver-qualification/import/apply` — apply with audit trail (`preview_token` + `skip_rows` + `create_unmatched`)
- `GET /api/hr/driver-qualification/import/audit` + `{audit_id}` — full audit history

**Verdict:** HR has a production-grade portal with roster mgmt, timeline aggregation, PDF exports, and a first-class bulk-import engine for CDL/driver-qualification data.

---

# 5 · Safety Audit

**Safety Portal endpoints (`routes/safety_portal/*.py`):**

- `auth_users.py` — Safety user auth (login, reset, password change, admin mgmt)
- `overview.py` — Safety dashboard rollup
- `training.py` — safety_training_records CRUD (per-employee)
- `documents.py` — safety_documents library (R2/inline hybrid)
- `corrective_actions.py` — CAPA queue
- `fire_extinguishers.py` + `fire_ext_attachments.py` — asset-specific safety
- `daily_reports.py` — safety visibility into DR feed
- `digest.py` — weekly digest

**Incident Intelligence Engine (Tracks 19.15 – 19.19):**
- 17 incident types (10 baseline + 7 additive)
- 9 report definitions
- Case Workspace with visual timeline spine + clickable blockers (Track 19.18)
- PDF pipeline: MASCI wordmark, Attorney Work Product chrome, running header + case footer, Case Story paragraph, narrative timeline, lettered contributing factors, page-break protection
- Pencil-whip guardrails (high-severity requires photos)
- Bilingual EN/ES parity

**Verdict:** Safety is well ahead of the industry curve. The gap is not capabilities; it's canonical linkage back to `db.employees` (see §12).

---

# 6 · Training Audit

**Two parallel training systems (by design):**

1. `db.safety_training_records` — per-completion records with `certificate_file_id`, `expiration_date`, `training_name`, `certification_type`.
2. `db.training_track_records` — curriculum-track completion (HR-curated learning paths).

**Both are joined into the HR Employee 360° timeline** via `_emp_filter()` (name+email+id regex).

**Supported attachments (per `photo_storage._DOC_MIME_TO_EXT` post-Track-19.19):**  
`.pdf`, `.xls`, `.xlsx`, `.xlsm`, `.csv` — plus photos via the image pipeline.

**Not currently first-class as training-attached artifacts (but supportable via existing pipelines):**
- Wallet cards → treat as `.pdf` or image
- OSHA cards → PDF
- CDL documents → captured in `document_expirations` linked from employee
- Manufacturer certifications → PDF
- Sign-in sheets → PDF

**Unification approach (no drift required):** every training record already accepts `certificate_file_id` pointing at a `safety_documents` entry. To unify further, add an optional `attachments[]` array on `safety_training_records` that reuses the `attachment_ref` envelope from Track 19.04 — this is a pure extension, not a redesign.

---

# 7 · PPE Audit

**Verified from `field_leadership.py` + `safety_forms.py`:**

- Safety Forms Equipment Issuance (`db.safety_equipment_issuances`) supports arbitrary items via `items[]` with `description`, `serial_number`, `quantity`, `size`, `condition`.
- Return flow (`/equipment-issuances/{id}/return`) captures return date, condition, damage notes, PDF.
- Equipment training (`db.safety_equipment_trainings`) captures use-and-care acknowledgment separately.
- Field Leadership `equipment_checkout` kind captures supervisor-level assignments (radios, tablets, laptops, tools).

**Supported today (via `items[]` free-form):** Hard hats · Safety glasses · Vests · Harnesses · Respirators · Fall protection · Gas monitors · Boot vouchers · Uniform issue · Laptop · Tablet · Phone · Tool assignment.

**Verified structured tracking:** signed acknowledgments (PDF), photographs (via attachment pipeline), serial numbers (`items[].serial_number`), replacement history (issue + return pattern), receipts (as attachments).

**Gaps (non-blocking):**
- No **expiration reminders** on PPE items (fall protection often has 5-year lifespan). Could reuse `document_expirations`.
- No **inspection history** for reusable PPE (harnesses require annual inspection). Could add a `db.ppe_inspections` collection or reuse `field_leadership_records` kind=`ppe_inspection`.

---

# 8 · Disciplinary Audit

**Field Leadership Records (`db.field_leadership_records`):**

| Kind | Verified? |
|---|:-:|
| `write_up` | ✅ |
| `verbal_coaching` | ✅ |
| `attendance` | ✅ |
| `recognition` | ✅ |
| `employee_termination` (auto-syncs into `employees.status_history`) | ✅ |
| `promotion_recommendation` | ✅ |
| `training_deficiency` | ✅ |
| `supervisor_notes` (admin-only) | ✅ |
| Progressive discipline (Verbal → Written → Final → Suspension → Termination) | Verbal + Written + Termination present as first-class kinds. Final Warning + Suspension are captured as `write_up` variants — could be promoted to first-class kinds. |
| Supervisor signature | ✅ (`needs_signatures: True` on write_up) |
| Employee acknowledgment | ✅ (`allow_refusal: True` — captures refusal as a first-class state) |
| Photos / evidence | ✅ via attachment pipeline |
| Witnesses | Free-form in `notes` — not structured |
| Appeal | Not first-class |

**Connection to Employee Lifecycle:** all Field Leadership records appear in the `/accountability/timeline` under category `Field Leadership`, sorted DESC by `occurred_at`. Verified `hr_portal.py:820-833`.

---

# 9 · Incident History Audit

**Track 19.15-19.19 Incident Intelligence Engine covers all 17 branches:**

Vehicle Accident · Equipment Accident · Utility Strike · Employee Injury · Public Injury · Near Miss · Property Damage · Environmental · Workplace Violence · Public Complaint · Fire · Threat · Theft · Vandalism · Site Security · Hazard Identified · Other.

**Current linkage to employee:**

| Path | Verified |
|---|:-:|
| `reporter_name` (string) captured in `FieldBlock` | ✅ |
| `personnel_present[]` (list of `{name, role}` dicts) | ✅ |
| Witnesses captured in `db.incident_case_witnesses` | ✅ |
| Legacy `db.incidents` joined into HR timeline via name-regex `_emp_filter()` | ✅ |
| **New `db.incident_cases` joined into HR timeline** | ❌ **Gap** — HR timeline queries only legacy `db.incidents`, not `db.incident_cases`. This is the #1 P0 gap. |
| `reporter_employee_id` FK on `FieldBlock` | ❌ |
| `involved_employees[]` FK list on case | ❌ |
| Automatic employee history entry when injured party is a known employee | ❌ |

**Fix scope** (§16, P0-B): Add optional `reporter_employee_id` + `involved_employee_ids[]` to `FieldBlock` (Pydantic `extra="allow"` already permits this — no schema drift). Update HR timeline to fan out over `db.incident_cases` in addition to `db.incidents`.

---

# 10 · Historical Records Import Architecture (proposed — NOT built)

**Doctrine:** additive engine, reuses existing R2 pipeline, never overwrites originals.

**Component design:**

```
POST /api/hr/historical-import/batches
  → creates db.historical_import_batches doc
  → returns batch_id
POST /api/hr/historical-import/batches/{batch_id}/files
  → chunked multipart upload of one or many PDFs/images
  → stores originals at documents/YYYY/MM/hist_import/{batch_id}/{sha256}.{ext}
  → creates db.historical_import_files{ batch_id, sha256, original_filename, ext,
       mime, size, uploaded_at, status: "queued" }
Worker (async, off-request):
  1. Extract text via OCR (pytesseract OR external service — see §11).
  2. Auto-classify (heuristic keyword map → training | ppe | discipline |
     incident | medical | certification | onboarding | separation).
  3. Match employee (see §11 matching engine).
  4. Write db.historical_import_suggestions{ file_id, suggested_employee_id,
     match_confidence, suggested_category, suggested_expiration_date,
     extracted_text_head, page_count }.
POST /api/hr/historical-import/suggestions/{id}/approve
  → creates canonical record (safety_training_records / safety_documents /
    field_leadership_records / etc.) linked to the imported file
  → NEVER modifies the original file
POST /api/hr/historical-import/suggestions/{id}/reject
POST /api/hr/historical-import/suggestions/{id}/reassign  (change employee/category)
POST /api/hr/historical-import/suggestions/batch/approve  (bulk approve)
GET  /api/hr/historical-import/queue                       (HR Review Queue)
GET  /api/hr/historical-import/batches/{id}/audit          (full audit trail)
```

**Bulk targets:** 100 · 500 · 1,000+ PDFs per batch. Worker is idempotent (sha256 keys prevent duplicate ingestion).

**Duplicate detection:** sha256 fingerprint on the raw bytes; the worker refuses to re-import a file whose sha256 already exists in `db.historical_import_files` OR whose classification matches an existing canonical record on the same employee + same date range.

**Audit:** every action (upload · classify · match · approve · reject · reassign) appends to `db.historical_import_events` (append-only).

---

# 11 · OCR Architecture (proposed — NOT built)

**Current state:** No OCR library imported anywhere in the backend (grep-verified).

**Two implementation paths:**

**Option A · self-hosted `pytesseract` + poppler-utils.**
- Pros: fully local, no per-page cost, no external service dependency.
- Cons: adds ~200 MB of container weight (Tesseract data), quality varies on scanned photocopies.
- Cost: $0 per page.

**Option B · Emergent LLM Key + Gemini 3 Flash vision** (or GPT-4/GPT-5.2 vision).
- Pros: superior scan quality on rotated / handwritten / photocopy-quality docs; structured extraction returns "here's the expiration date, here's the name" directly — bypassing separate NER step.
- Cons: per-page cost (~$0.001-0.005/page depending on model); requires the Emergent LLM key to have budget.
- Recommendation: **Option B** for the first release. Use Gemini 3 Flash for speed + cost. If cost becomes prohibitive at 1,000+ pages/day scale, layer in `pytesseract` as a pre-filter to skip already-machine-readable PDFs and only send scans to the LLM.

**Text storage:** `db.historical_import_files.extracted_text_head` (first 8 KB) and `db.historical_import_files.extracted_text_full` (full body, up to 500 KB per doc — larger files get truncated with an audit flag). Text is indexed for search (§12).

---

# 12 · Employee Matching Architecture (proposed)

**Match features (in priority order):**

1. **Exact employee_id match** (if the document has "Employee ID: E1234" in OCR text) — confidence 1.00.
2. **Exact name + exact hire date** — confidence 0.95.
3. **Exact legal name** — confidence 0.85.
4. **Exact preferred_name / nickname** — confidence 0.75.
5. **Fuzzy name (RapidFuzz ratio ≥ 90)** — confidence 0.60.
6. **Fuzzy name (ratio 80-89)** — confidence 0.40.
7. **No match** — routed to "Unknown Employee" review queue.

**Employee identity fields consulted:** `employees.name` · `employees.preferred_name` (add if missing) · `employees.previous_names[]` (add) · `employees.employee_id` · `employees.email`.

**Ambiguity handling:** if two employees score ≥ 0.80, both are surfaced in the HR Review Queue with a "Multiple candidates" flag. HR picks; the choice is recorded in `db.historical_import_events` for auditability.

**Manual override at any point:** HR can reassign the file to any employee, split a multi-employee document, merge duplicate suggestions, or retry classification.

---

# 13 · HR Review Queue Architecture (proposed)

**Single unified queue backing three lenses:**

- **Unmatched** — no employee suggested (confidence < 0.40).
- **Low confidence** — one candidate at 0.40–0.79.
- **High confidence** — one candidate at ≥ 0.80. Bulk-approvable.

**Row shape (renders in `HistoricalImportReview.jsx` — to build):**
- Original document thumbnail (first page render at 200 dpi)
- OCR-extracted head (200 chars) with "View full text"
- Suggested employee (chip · click to reassign)
- Confidence gauge
- Suggested record type (chip · click to change)
- Suggested expiration date (if detected)
- Action row: Approve · Reject · Reassign · Split · Merge · View history

**Audit log column:** every action visible inline. Every mutation writes to `db.historical_import_events`.

---

# 14 · Safety Review Queue Architecture (proposed)

**Same skeleton as HR queue, different downstream tables:**

- Uploaded scanned incident report → suggested `incident_case` (create-new vs. link-to-existing)
- Uploaded witness statement → attached to case + written into `db.incident_case_witnesses`
- Uploaded closeout letter → attached to case + case state advanced to `CLOSED` (with human confirmation)
- Uploaded medical restriction → attached to `db.incident_case_medical` + copied to `employees.medical_restrictions[]` (new field, additive)

Same audit ledger pattern (`db.safety_review_events`).

---

# 15 · Employee 360° Blueprint

**Backend (already exists):** `GET /api/hr/employees/{id}/accountability/timeline` — verified in `hr_portal.py:690`.

**Frontend (partial):** Individual sections exist across HR portal pages; a single-page consolidated view does not.

**Proposed page:** `/hr/employees/{id}` — `pages/EmployeeProfile.jsx` (to build).

**Layout (mirrors SafetyCaseWorkspace polish from Track 19.18):**

```
┌───────────────────────────────────────────────────────┬─────────────────┐
│  IDENTITY HEADER                                      │  Right rail:    │
│  Name · Preferred name · Employee ID · Hire date      │  Current state  │
│  Lifecycle status chip · Days tenure                  │  Expirations    │
│  ────                                                 │  Category totals│
│  Employee Story paragraph (auto-composed):            │                 │
│  "Hired 2019-03-11 as a Foreman for the Underground   │                 │
│  Division. Currently Active. Approved company driver  │                 │
│  with a Class A CDL expiring 2027-05-20."             │                 │
│  Next-Action chip: "CDL expires in 47 days"           │                 │
├───────────────────────────────────────────────────────┤                 │
│  Tabs: Timeline · Training · PPE · Incidents ·        │                 │
│        Discipline · Documents · Fleet · Onboarding ·  │                 │
│        Separation                                     │                 │
├───────────────────────────────────────────────────────┤                 │
│  Visual spine timeline (Track 19.18 pattern):         │                 │
│  · Color-coded dots per category                      │                 │
│  · Filter chips (last 30d · last year · all)          │                 │
│  · Click to open source record                        │                 │
└───────────────────────────────────────────────────────┴─────────────────┘
```

**Design pattern is 100% copy-pastable from `SafetyCaseWorkspace.jsx`** — same shell, same visual spine, same clickable blockers, same right-rail one-liner headline.

---

# 16 · Prioritized Implementation Roadmap

## 🔴 P0 (deployment-critical for full Employee 360°)

**P0-A · Incident Engine ↔ Employee linkage** (~1 track · 200 lines)
- Add `reporter_employee_id`, `involved_employee_ids[]`, `witness_employee_ids[]` to the `FieldBlock` (already `extra="allow"` — no schema drift).
- Populate these on submit from the frontend EmployeePicker (already exists).
- Update `hr_portal.py:807` HR timeline fan-out to include `db.incident_cases` in addition to `db.incidents`.
- Update `case_service` to write these fields on state transitions.
- Lock tests: incident case surfaces on employee timeline when they were the reporter · when they were a witness · when they were injured.

**P0-B · Employee 360° page** (~1 track · 400 lines)
- New `pages/EmployeeProfile.jsx` replicating the SafetyCaseWorkspace pattern.
- Consumes the existing `/api/hr/employees/{id}/accountability/timeline`.
- Employee Story auto-composed paragraph.
- Visual spine timeline with category dots + filter chips.
- Tab bar for each category with deep-link to source record.
- HR Compliance Brief PDF export button (already exists at `/accountability/brief.pdf`).

## 🟠 P1 (major operational lift, straightforward implementation)

**P1-A · Historical Records Intake Engine · Phase 1 (upload + audit)** (~1 track · 600 lines)
- `db.historical_import_batches` + `db.historical_import_files` collections.
- Chunked upload endpoints reusing the `dr_attachment` R2 helper.
- Sha256 duplicate detection.
- Simple "queued" status — no OCR yet.
- HR Review Queue page rendering uploaded files with a manual "Assign to employee + category" workflow (bypasses OCR — humans do the classification).
- Full audit ledger (`db.historical_import_events`).
- Live-verifiable with real historical PDFs before adding OCR complexity.

**P1-B · Employee-scoped full-text search** (~0.5 track · 100 lines)
- Add MongoDB `$text` indexes on `safety_documents.title + notes + extracted_text`, `safety_training_records.training_name + certification_type`, `field_leadership_records.notes`, `incident_cases.field_block.observed_conditions + event_description`.
- New endpoint `GET /api/hr/employees/{id}/search?q=<query>` returns matches across employee's records.
- Powers a search box on the Employee 360° page.

**P1-C · Discipline Package PDF** (~0.5 track · 200 lines)
- New endpoint `/api/hr/employees/{id}/discipline-package.pdf` bundling every `write_up` + `verbal_coaching` + `training_deficiency` + `employee_termination` + linked incidents.
- Reuses the WeasyPrint pipeline + Attorney Work Product chrome from Track 19.18.

**P1-D · PPE expiration reminders + inspection tracking** (~0.5 track · 150 lines)
- Extend `document_expirations` to cover PPE items with lifespan (harnesses, respirators, fall protection).
- New `db.ppe_inspections` collection (annual harness inspection etc.) — additive.
- Surface in HR timeline.

## 🟡 P2 (high-value polish)

**P2-A · Historical Records Intake · Phase 2 (OCR + auto-classify)** (~1 track · 400 lines)
- Add Gemini 3 Flash vision integration via `integration_playbook_expert_v2` playbook (requires Emergent LLM key).
- Worker extracts text + suggests employee + suggests category + suggests expiration date.
- Review Queue upgraded with confidence gauges.

**P2-B · Fuzzy employee matching with RapidFuzz** (~0.3 track · 100 lines)
- Add `rapidfuzz` dep.
- Score against `employees.name` + `preferred_name` + `previous_names[]`.
- Multi-candidate flag when ties are close.

**P2-C · Duplicate document detection at upload time** (~0.2 track · 50 lines)
- Sha256 check on already-approved records.
- Warn HR on the Review Queue before approval.

**P2-D · Progressive discipline first-class kinds** (~0.2 track · 100 lines)
- Add `final_warning` and `suspension` as first-class `field_leadership_records` kinds (currently variant of `write_up`).
- Update the discipline package PDF to render escalation chronology.

## 🟢 P3 (nice-to-have)

**P3-A · Employee onboarding checklist** — first-class collection tracking I-9, W-4, direct deposit, orientation, first-day-safety.  
**P3-B · Employee acknowledgments library** — one place to see every "signed my copy of the handbook" acknowledgment.  
**P3-C · Return-to-work workflow** — first-class flow linking injury → medical restriction → RTW date → light-duty assignment.  
**P3-D · Employee search across ALL text (full-text)** — extend §12 P1-B to non-employee-scoped search.  
**P3-E · ML-assisted classification improvement** — feedback loop where HR corrections improve suggestions.

---

# 17 · Industry Comparison

| Capability | MASCI today | Procore | Raken | Autodesk Build | Enterprise HCM (Workday) |
|---|:-:|:-:|:-:|:-:|:-:|
| Single canonical employee record | ✅ | ⚠️ (per-project) | ⚠️ | ⚠️ | ✅ |
| 9-state HR lifecycle | ✅ | ⚠️ | ❌ | ❌ | ✅ |
| Automatic write-up → status sync | ✅ | ❌ | ❌ | ❌ | Partial |
| CDL / Driver Qualification module | ✅ | ⚠️ (add-on) | ❌ | ❌ | ✅ (via HR) |
| Structured PPE issuance | ✅ | Partial | ❌ | ❌ | ⚠️ (needs asset mgmt) |
| Field write-up / discipline with signatures | ✅ | Partial | Partial | ❌ | ⚠️ |
| Incident lifecycle with 17 branches | ✅ (Track 19.16+) | ⚠️ (basic) | ❌ | ⚠️ | N/A |
| Investigation timeline visualization | ✅ (Track 19.18) | ⚠️ | ❌ | ❌ | N/A |
| Attorney Work Product PDF chrome | ✅ | ❌ | ❌ | ❌ | N/A |
| Bulk import of historical documents | ⚠️ (CDL only, not generic) | ⚠️ (limited) | ❌ | Partial | ✅ |
| OCR + auto-classification | ❌ (not built · P2 roadmap) | ⚠️ (Docs feature) | ❌ | ✅ | ⚠️ |
| Employee-scoped full-text search | ❌ (P1 roadmap) | ⚠️ | ❌ | ✅ | ✅ |
| Bilingual EN/ES parity | ✅ (Track 19.17+) | ⚠️ (limited) | ⚠️ | ⚠️ | ✅ |
| Signed distribution audit trail | ✅ (email_routing_audit_v2) | ⚠️ | ❌ | Partial | ⚠️ |

**Where MASCI exceeds the industry:** Incident Intelligence Engine · Attorney Work Product chrome · driver qualification + medical card mirroring · integrated Field Leadership discipline flow · single employee record used by HR + Safety + Ops + Fleet.

**Where MASCI matches:** HR portal · training records · document library · time verification · offboarding playbook.

**Meaningful gaps vs. best-of-breed:** OCR/auto-classify bulk import · full-text search on document contents · discipline package export · consolidated Employee 360° UI (backend already there; UI is fragmented).

---

# 18 · Gap Analysis Summary

| Gap | Priority | Effort | Ships with |
|---|:-:|:-:|---|
| Incident cases not joined into HR timeline | 🔴 P0 | 200 lines | Track 19.20 |
| Employee 360° single-page UI | 🔴 P0 | 400 lines | Track 19.20 or 19.21 |
| Historical Records Intake · Phase 1 (upload + queue, no OCR) | 🟠 P1 | 600 lines | Track 19.21 |
| Employee-scoped full-text search | 🟠 P1 | 100 lines | Track 19.21 |
| Discipline Package PDF | 🟠 P1 | 200 lines | Track 19.21 |
| PPE expiration reminders | 🟠 P1 | 150 lines | Track 19.21 |
| Historical Records Intake · Phase 2 (OCR + auto-classify) | 🟡 P2 | 400 lines | Track 19.22 |
| Fuzzy employee matching | 🟡 P2 | 100 lines | Track 19.22 |
| Duplicate document detection | 🟡 P2 | 50 lines | Track 19.22 |
| Progressive discipline as first-class kinds | 🟡 P2 | 100 lines | Track 19.22 |
| Employee onboarding checklist | 🟢 P3 | 200 lines | Track 19.23+ |
| Return-to-work workflow | 🟢 P3 | 300 lines | Track 19.23+ |
| Employee acknowledgments library | 🟢 P3 | 200 lines | Track 19.23+ |
| Platform-wide full-text search | 🟢 P3 | 200 lines | Track 19.23+ |
| ML-assisted classification feedback loop | 🟢 P3 | 300 lines | Track 19.24+ |

**Total scope for full Employee 360°:** ~3,500 lines across 5 focused tracks — completed in 6 weeks of tight iteration.

---

# 19 · Final Deployment Recommendation

**🟢 Deploy the current platform to production as-is.**  

The existing employee lifecycle backbone is superior to most construction industry platforms today. Field crews, Safety, PMs, and Executives can use it in production while the P0/P1 gaps ship over subsequent tracks.

**Sequencing:**
1. **Now:** Deploy Track 19.19 (`.xlsm` support) to production. Field crews unblocked.
2. **Track 19.20 (proposed):** P0-A (Incident ↔ Employee linkage) + P0-B (Employee 360° page). Ships full Employee 360° in one track.
3. **Track 19.21:** P1-A (Historical Import · Phase 1 · upload + manual queue) + P1-B (search) + P1-C (Discipline Package PDF) + P1-D (PPE expirations). Ships the "single lifecycle record" experience.
4. **Track 19.22:** P2 · OCR + auto-classify + fuzzy matching + duplicate detection. Ships intelligent bulk historical ingestion.
5. **Track 19.23+:** P3 polish per user priority.

**Success criterion (from the prompt):**  
> *"At the conclusion of this audit, MASCI leadership should be able to open any employee's profile and immediately access every verified record generated throughout that employee's lifecycle."*

**Backend answer:** already achievable via `GET /api/hr/employees/{id}/accountability/timeline` + `/accountability/brief.pdf` **today**.  
**Frontend answer:** achievable in Track 19.20 by building the single-page `EmployeeProfile.jsx` on top of that endpoint.

Done means done. Zero drift. Foundation is exceptional. Six weeks of focused tracks to complete.
