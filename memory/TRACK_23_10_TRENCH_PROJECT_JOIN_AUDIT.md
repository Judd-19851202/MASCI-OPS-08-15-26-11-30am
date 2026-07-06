# TRACK 23.10 · TRENCH SAFETY PROJECT JOIN + COMPETENT PERSON CERTIFICATION
## Phase 1+A · Discovery & Design · NO CODE CHANGES

Verdict of design phase: **🟢 GO for Track 23.10-B (Competent Person foundation)** as the first executable sub-track. Every other sub-track depends on this foundation existing. This document does **not** modify any code, does **not** provision any UI, and does **not** fake-classify any safety source.

---

## 1 · Executive summary

Two independent gaps are on the critical path:

* **Trench data is project-aware where it originates from the Daily Report or from an active deployment; it is asset-scoped everywhere else.** The Safety Portal correctly classifies these as PARTIAL today. A shared `project_linker` service can lift asset-scoped records to LIVE **only when a high-confidence deployment link exists**. Where linkage is genuinely absent (an old hold on a stored trench box), it stays PARTIAL.
* **The Daily Report V3 has no excavation/trench section at all.** V1 captured a lightweight signal; V3 does not.
* **There is no "Competent Person" concept in the platform today.** `safety_training_records` is the canonical employee certification store (13 rows in preview) but does not include a `COMPETENT_PERSON` certification type. **`trench_safety_certifications` is misleadingly named — it is ASSET-level (box annual cert), not employee-level.**

The mandate's Final Rule (12 conditions) requires the certification foundation to exist BEFORE trench safety, Daily Report, scheduling, and Safety KPIs can consume it. Anything else is fake green.

---

## 2 · Current trench architecture (discovery)

### 2.1 Collections inventory

| Collection | Docs (preview) | Project-linked? | Notes |
|---|---:|---|---|
| `trench_excavations` | 984 | ✅ has `project_number` (via Daily Report linkage) + `competent_person_name`, `depth_ft`, `crew`, `date_of_work`, `assigned_asset_ids` | Canonical excavation-day signal; already project-aware |
| `trench_safety_deployments` | 270 | ✅ has `project_id`, `project_name`, `assigned_at`, `returned_at` | **KEY project-link table** for asset-scoped records |
| `trench_safety_assets` | 121 | ✅ has `current_project_id/name/number` (via active deployment) | Trench-box inventory; project = latest active deployment |
| `trench_safety_holds` | 1127 | ❌ asset-scoped (`asset_id`, `kind`, `is_active`, `opened_at`, `cleared_at`, `source_ref`) | PARTIAL — resolve project via active deployment at `opened_at` |
| `trench_safety_inspections` | 432 | ❌ asset-scoped (`asset_id`, `checklist`, `result`, `competent_person_confirmed`, `inspector_name`) | PARTIAL — same rule |
| `trench_safety_repairs` | 311 | ❌ asset-scoped (`asset_id`, `status`, `verified_at`, `requires_reinspection`, `reinspection_passed`) | PARTIAL · **B-04 invariant "Repair Complete ≠ Safe To Use" lives here** (`verified_at` is the only proof of safe-to-use, not `status=completed`) |
| `trench_safety_photos` | 80 | ❌ asset-scoped | Evidence link |
| `trench_safety_certifications` | 68 | ❌ **ASSET** cert (annual box cert), NOT employee | Named ambiguously; do not confuse with Competent Person |
| `trench_boxes` | 2 | n/a | Type catalog |
| `trench_safety_pulses` | 80 | n/a | Weekly leadership digest snapshots |
| `trench_safety_leadership_digests` | 9 | n/a | Weekly digest artifacts |
| `trench_safety_qr_scans` | 123 | n/a | QR-code scan log for asset lookup |
| `trench_safety_report_subscriptions` | 4 | n/a | Report subscriber list |

### 2.2 Route inventory

Existing trench routes (spot-checked): asset CRUD · deployment assign/return · hold open/clear · inspection submit · repair open/close/verify · photo upload · QR scan · report presets · leadership digest cron. All routes preserved as-is.

### 2.3 Lifecycle invariants (locked by Track 22.4B; DO NOT weaken)

* Writes to `trench_safety_holds` / `trench_safety_inspections` / `trench_safety_repairs` are **idempotent** (Track 22.4B).
* **B-04: Repair Complete ≠ Safe To Use.** A repair row can be `status="completed"` yet **NOT** safe-to-use unless `verified_at IS NOT NULL` AND `reinspection_passed IS TRUE`. Any KPI that reports "safe to use" MUST require both fields.
* Open holds remain open until an explicit `cleared_at` is set — no auto-close.

---

## 3 · Trench field matrix (CSV)

See `/app/memory/TRACK_23_10_TRENCH_FIELD_MATRIX.csv` (produced alongside this doc, 30 rows). Each row: trench field → collection key → project linkage rule → target ODS fact type → PM KPI consumer → Safety KPI consumer → PDF/email surface.

---

## 4 · Trench source classification matrix (CSV)

See `/app/memory/TRACK_23_10_TRENCH_SOURCE_CLASSIFICATION.csv` (7 rows) — one per source, with:

* Current classification (23.8)
* Linkable-via rule (deployment · daily-report ref · asset current_project)
* Post-23.10-C classification per project (LIVE / PARTIAL / MISSING)
* Confidence rule (high · medium · low)

---

## 5 · Project linkage rule (specification for `services/trench_safety/project_linker.py`)

### 5.1 Inputs
* trench record document (hold · inspection · repair · photo · deployment · excavation)

### 5.2 Resolution ladder (stop at first hit; record which rung matched)

1. **Explicit project_number on record** → `project_link_status=explicit`, confidence=high.
2. **daily_report_doc_id / report_id** → look up parent Daily Report; use its `project_number` → `inherited_from_daily_report`, high.
3. **Parent trench record** (hold's `source_ref` points to inspection · repair's parent hold · etc.) → recurse once → `inherited_from_parent_record`, high.
4. **Asset active deployment at record's date**: find `trench_safety_deployments` where `asset_id == record.asset_id` AND `assigned_at <= record.opened_at/created_at <= COALESCE(returned_at, +∞)`. If exactly ONE match → `inferred_from_assignment`, medium.
5. **Asset current project** (fallback for records without a date, e.g. `trench_safety_assets.current_project_number`): use only if `record.opened_at` is within 24h of `asset.updated_at`. Otherwise skip. → `inferred_from_current_asset`, low.
6. **Multiple candidate deployments** → `project_link_status=ambiguous`, project_number=null.
7. **No deployment ever** → `project_link_status=missing`, project_number=null.

### 5.3 Output shape (returned by `resolve_project(record) -> ProjectLinkage`)

```
{
  "project_number": "24-12" | null,
  "project_name_snapshot": "CC5744 - OXFORD RD Improvements" | null,
  "project_link_status": "explicit|inherited_from_daily_report|inherited_from_parent_record|inferred_from_assignment|inferred_from_current_asset|ambiguous|missing",
  "confidence": "high|medium|low",
  "linker_notes": "matched deployment id d123 · assigned 2026-01-04 · returned NULL"
}
```

### 5.4 Rules
* NEVER write project_number back into the source document. Linkage is derived at read time (or emitted into ODS facts; see §6).
* NEVER promote medium/low confidence to LIVE at the source-classification layer (see §7).
* NEVER fabricate a project when linkage is ambiguous.

---

## 6 · ODS trench facts (specification)

Emit into `operational_facts` (existing collection). Never touch legacy trench rows.

| Fact type | Source event | Payload (canonical) |
|---|---|---|
| `trench_inspection_fact` | On `trench_safety_inspections` insert | `asset_id · asset_label · inspection_type · result · inspector_name · competent_person_confirmed · corrective_actions_count · project_number · project_link_status · confidence` |
| `trench_hold_fact` | On `trench_safety_holds` insert or `cleared_at` update | `asset_id · kind · reason · opened_at · cleared_at · is_active · source · source_ref · project_number · project_link_status · confidence` |
| `trench_repair_fact` | On `trench_safety_repairs` insert / verify | `asset_id · status · verified_at · requires_reinspection · reinspection_passed · safe_to_use_verified (bool: `verified_at IS NOT NULL AND reinspection_passed IS TRUE`) · project_number · project_link_status · confidence` |
| `trench_verification_fact` | Emitted only when `safe_to_use_verified` transitions False → True on a repair | Same payload as `trench_repair_fact` at that moment |
| `excavation_day_fact` | On Daily Report V3 submit when `excavation_trench.work_today=true` | `project_number · report_id · date · competent_person_id · competent_person_name_snapshot · excavation_type · max_depth · max_depth_unit · excavation_count · protective_system · trench_box_id · trench_box_label_snapshot · inspection_completed · hold_issued · utilities_status · tomorrow_planned · competent_person_certification_id · competent_person_cert_valid_at_report` |

### 6.1 Rules
* All fact writes are idempotent (natural key = `source_collection + source_id + event_kind`).
* No double-counting: `excavation_day_fact` (Daily Report signal) and `trench_inspection_fact` (formal inspection) are DIFFERENT fact_types with different source → aggregator counts them separately, never adds them.
* `safe_to_use_verified` is DERIVED at fact-emit time from `verified_at IS NOT NULL AND reinspection_passed IS TRUE` — never read from `status` alone.
* Historical trench records get a **one-time backfill emitter** that computes their facts with `project_link_status` per §5. Existing records not modified.

---

## 7 · Safety KPI classification lift (specification for aggregator update)

Track 23.7 aggregator currently marks `trench_excavations` LIVE and `trench_holds` PARTIAL. Post-23.10-D:

| Source | New rule |
|---|---|
| `trench_excavations` | **LIVE** per project when at least one record has project_number; project-specific count. Already correct. |
| `trench_hold_fact` (post-linker) | **LIVE** per project when linker resolved `explicit` or `high` confidence for ≥ 1 hold in the window · **PARTIAL** if only medium/low · **MISSING · FUTURE** if none exist for the project |
| `trench_inspection_fact` | Same rule as holds |
| `trench_repair_fact` | Same rule as holds |
| `excavation_day_fact` | Always **LIVE** per project (comes from the DR itself) |
| `equipment_dvir` | Unchanged — remains **PARTIAL** (still asset-scoped) |
| `trench_holds` legacy row-level | Renamed source-status label to `trench_holds_legacy` and marked **PARTIAL** — the LIVE source is the new fact type |
| Company rollup | Company `LIVE/PARTIAL/MISSING` bucket sums per source across all active projects (existing partitioning invariant preserved). |

New KPI counters exposed by the aggregator (safety group):

* `trench_inspection_count` (already exists)
* `open_trench_holds` (new · from `trench_hold_fact.is_active=true`)
* `trench_repair_open_count` (new)
* `trench_repair_completed_count` (new)
* `trench_safe_to_use_verified_count` (new — derived)
* `unresolved_trench_safety_items` (new — sum of open holds + open repairs)
* `max_depth_observed_ft` (new — from `excavation_day_fact`)
* `protective_system_usage` (new — Counter)
* `utilities_encountered_count` (new — from `excavation_day_fact.utilities_status ∈ {known, unknown, damage_strike}`)
* `competent_person_coverage_pct` (new — % of excavation_day_facts where `competent_person_cert_valid_at_report=true`)
* `project_link_status_summary` (new — Counter of link statuses across the window)

No cost. No rates. No dollars. Preserved by the existing `_assert_no_cost` guard.

---

## 8 · Daily Report V3 excavation section (specification)

### 8.1 Section gate
* Placed after the Materials section, before the Safety section.
* Single yes/no: **"Excavation or trench work today?"** (default No).
* Collapsed by default — zero visual weight when No.

### 8.2 Fields when Yes (all required marked ⚑)

| Field | Type | Notes |
|---|---|---|
| ⚑ Competent Person | `CompetentPersonCombo` (new picker) | Uses `/api/employees/competent-persons?active=true` (§10) → only employees with an ACTIVE `COMPETENT_PERSON` certification. Shows Name · Trade · Crew · Cert expires · Certification status. Expired = disabled. Within-warning = amber inline chip. |
| Competent Person snapshot | derived | `competent_person_id · name · trade · crew · certification_id · certification_expires_at · cert_valid_at_report` |
| ⚑ Crew assigned | text (falls back to `masci_crews` inference) | Feeds scheduling |
| ⚑ Excavation type | select | trench · pit · utility crossing · structure · other |
| ⚑ Maximum depth | numeric | with unit ft/in or ft-decimal |
| Number of excavations | numeric | default 1 |
| ⚑ Protective system | select multi | trench box/shield · shoring · sloping · benching · none-under-threshold · other |
| Trench box / shield | dropdown | `trench_safety_assets` where `asset_type ∈ {box, shield}`; supports "not from inventory" custom fallback |
| ⚑ Inspection completed today | Yes/No | If No AND depth ≥ 5 ft: show inline red warning "Inspection required" + link to trench inspection form |
| Hold / stop-work issued | Yes/No | If Yes: show link to open trench hold workflow; do NOT open a hold automatically |
| ⚑ Utilities encountered | select | No · Known utility · Unknown/unmarked · Damage/strike. Damage/strike triggers inline red guidance + link to incident report |
| Tomorrow planned | Yes/No + optional notes | Feeds `scheduling_readiness.excavation_planned_tomorrow` |
| Notes | text | |
| Photos | evidence upload | linked to `excavation_day_fact` via ref |

### 8.3 Rules
* No non-excavation report becomes slower or harder — gate stays collapsed when No.
* Draft autosave includes excavation subtree.
* Restore-yesterday does NOT restore safety-critical answers (`inspection_completed`, `hold_issued`, `utilities_status`) — always reset to blank so the operator answers fresh.
* Mobile 390: all fields stack single-column; no horizontal overflow.
* If Competent Person picker is empty because no employee has an active cert → show honest empty state: *"No employees currently hold an active Competent Person certification. Contact HR/Training."* NEVER a text-input fallback for compliance-critical field.
* Section is **advisory-signal**, not a formal inspection. Formal inspection remains in the trench safety module — DR only captures the operational-day signal.

### 8.4 Persistence
Added as `daily_reports.excavation_trench = {…}` — additive, non-destructive, historical reports unaffected.

---

## 9 · PDF / Email spec

* PDF: new section "Excavation / Trench" rendered **only** when `excavation_trench.work_today=true`. Contents: Competent Person + cert-valid-at-report chip · excavation type · max depth · protective system · trench box · inspection completed · hold issued · utilities status · notes · photo thumbs. Historical reports without the field render byte-identical.
* Email: no new alert by default. Only mention trench work if: (a) hold issued, (b) utilities damage/strike, (c) inspection missing at required depth, or (d) AI summary references it. Otherwise the email stays clean.
* No cost / rate / dollar / budget content in either.

---

## 10 · Competent Person Certification Architecture (Phases A–I response)

### 10.1 Phase A · Existing training system audit

| Collection | Purpose | Owner | Suitability for cert type "COMPETENT_PERSON" |
|---|---|---|---|
| `safety_training_records` (13 · in preview) | Canonical **employee** certification/training rows. Keys: `employee_id · employee_master_id · certification_type · training_name · issued_by · completed_date · expiration_date · certificate_file_id · notes` | HR / Training Admin | **✅ THIS IS THE HOME**. Extend `certification_type` enum with `COMPETENT_PERSON` and (in Phase C) add missing fields (`issuing_organization · instructor · instructor_company · training_hours · training_standard · jurisdiction · digital_certificate · wallet_credential · verification_status · verification_status_history · suspended_at · revoked_at`) via additive migration. No new collection. |
| `safety_equipment_trainings` (34) | Sign-off style equipment topic training | Field | Not the right home — topic-level acknowledgement, not credentialed cert |
| `transport_orientation_certificates` (65) | Transport-portal specific | Transport | Domain-scoped; not a general cert |
| `training_guides` / `training_videos` | Content library | Training | Content, not credential |
| `driver_qualification_imports` | Batch import previews | HR | Ingestion tooling |
| `trench_safety_certifications` (68) | **⚠ MISNAMED** — this is trench-BOX (asset) annual certification, not employee credential | Trench safety | Leave as-is; rename disallowed (schema migration risk). Documented in field matrix so no future reader confuses them. |

### 10.2 Phase B · Certification model additions

Certification data extensions to `safety_training_records` for `certification_type="COMPETENT_PERSON"` (additive fields; existing rows unaffected):

```
issuing_organization          str
instructor                    str
instructor_company            str
training_hours                float
training_standard             "OSHA_29_CFR_1926_651"|"custom"
jurisdiction                  str (state/region)
certificate_number            str
attachments                   [file_ref]
digital_certificate           file_ref
wallet_credential             wallet ref (future)
verification_status           "active"|"expired"|"suspended"|"revoked"
verification_status_history   [{status, at, actor, reason}]
suspended_at / revoked_at     datetime
active                        bool (derived: verification_status=="active" AND today ≤ expiration_date)
```

### 10.3 Phase C · Automatic registry (no manual list)

**New service** `services/certifications/competent_person_registry.py`:

* `list_active_competent_persons(db, warning_days=30)` → returns every employee with at least one `safety_training_records` row where `certification_type="COMPETENT_PERSON"` AND `verification_status="active"` AND `expiration_date > today()`. Emits per-row `expires_in_days`, `warning=(expires_in_days ≤ warning_days)`, snapshot HR identity (via Track 23.5 normalizer).
* `resolve_active_for_employee(db, employee_id)` → latest active cert or None.
* NEVER writes. NEVER duplicates a roster. **Registry is a QUERY over `safety_training_records`, not a stored list.**
* Backfill: none — a Competent Person becomes registered the instant HR/Training creates their `safety_training_records` row.

### 10.4 Phase D · Daily Report V3 picker

`CompetentPersonCombo` (React component) hits `GET /api/employees/competent-persons?active=true` which wraps the service. Renders per-row:

```
Alec Perkins · General Laborer · Shop · Cert: ACTIVE · Expires 2027-03-15 (534 days)
Sam Cruz     · Foreman         · Concrete · Cert: WARNING (18 days) · Expires 2026-02-24
```

Expired employees are excluded server-side. Within-warning employees are selectable + display an amber chip.

### 10.5 Phase E · Trench Safety module

Trench Safety consumes the same `GET /api/employees/competent-persons?active=true` — **no separate roster**. Any place today that reads `competent_person_name` as a free-text field becomes a picker mount. Historical rows keep their existing free-text snapshot for audit — never rewritten.

### 10.6 Phase F · Scheduling readiness

`scheduling_readiness` block gains (all derivable from ODS `excavation_day_fact` + `trench_hold_fact` + registry query):

```
excavation_work_today          bool
excavation_planned_tomorrow    bool
competent_person_assigned      bool
competent_person_name          str
competent_person_cert_valid    bool
crew_signal_available          bool
trench_box_required            bool
trench_box_assigned            bool
protective_system_selected     bool
inspection_ready               bool
open_hold_blocks_work          bool
open_repair_blocks_work        bool
utility_conflict_blocks_work   bool
safety_clear_to_schedule       bool  ← AND of the four negatives + competent_person_cert_valid + inspection_ready
```

**`safety_clear_to_schedule` returns FALSE if ANY of**: open hold on any asset assigned to the project · open repair without `safe_to_use_verified=true` · unresolved utility strike incident · missing required inspection · assigned competent person's cert expired.

### 10.7 Phase G · Safety Portal dashboard additions

Existing `SafetyOperationalKpisCard` gains a `certifications` block:

```
active_competent_persons_count
expiring_within_30d_count
expired_count
upcoming_renewals_by_month
projects_missing_competent_person_coverage
```

Sourced entirely from the registry service. No new collection.

### 10.8 Phase H · ODS certification facts

Three new fact types (idempotent, project-nullable):

* `competent_person_certification_fact` — emitted on `safety_training_records` insert/update where `certification_type="COMPETENT_PERSON"`. Payload: employee_id · certification_id · verification_status · issued_at · expires_at · issuer · training_standard.
* `competent_person_assignment_fact` — emitted when a Daily Report is submitted with a competent_person_id. Payload: project_number · report_id · employee_id · certification_id · cert_valid_at_report.
* `competent_person_expiration_fact` — emitted daily by scheduler for certs expiring in ≤ 30 days. Payload: employee_id · certification_id · expires_at · days_left.

### 10.9 Phase I · Permissions

* HR-role or Training-admin only can create / modify / suspend / revoke / renew `safety_training_records` rows where `certification_type="COMPETENT_PERSON"`.
* Field users, supervisors, PM, Safety officers, Trench Safety module: **read-only** access to the registry query. Cannot self-certify.
* Existing HR/Training admin gates are already in place on `safety_training_records` writes; the new `COMPETENT_PERSON` type inherits them.
* Audit trail: every certification write logs actor + action to `verification_status_history[]` and to `db.hr_audit`.

---

## 11 · Implementation sequence (executable sub-tracks)

Every sub-track has its OWN certification bar (does not touch anything below it in the dependency graph):

### 🟢 Track 23.10-B · **COMPETENT PERSON CERTIFICATION FOUNDATION** (execute NEXT)
* Backend: extend `safety_training_records` handlers with the additive fields (§10.2). Add `services/certifications/competent_person_registry.py` (§10.3). Add `GET /api/employees/competent-persons?active=true&warning_days=30`. Add `competent_person_certification_fact` emitter on write. Permissions gate stays on existing HR/Training admin dep.
* Frontend: admin UI in Employee Lifecycle → certifications tab supports `COMPETENT_PERSON` cert type. NO change to Trench Safety, NO change to Daily Report V3, NO change to Safety KPI card in this sub-track.
* Tests: registry returns only active + non-expired · expired excluded · warning flag correct · write requires HR/Training admin token · legacy `safety_training_records` types untouched · fact emitter idempotent.
* Certification bar: registry query is the sole source of truth for who is a Competent Person; no other collection is created.

### 🟡 Track 23.10-C · **TRENCH PROJECT LINKER + ODS TRENCH FACTS**
* Depends on: 23.10-B (needs cert model for `excavation_day_fact.competent_person_certification_id`).
* Backend: `services/trench_safety/project_linker.py` (§5). New fact types emitted from existing trench routes (§6). One-time backfill migrator for historical rows (idempotent, safe to re-run).
* NO UI change. NO Daily Report change.
* Tests: 6-rung ladder resolution · `safe_to_use_verified` derivation · idempotency · B-04 invariant preserved · legacy Track 22.4B tests still pass.

### 🟡 Track 23.10-D · **SAFETY KPI TRENCH LIFT + CERT DASHBOARD BLOCK**
* Depends on: 23.10-B + 23.10-C.
* Backend: aggregator reads new ODS facts (§7) · exposes new counters · classifies sources honestly · `certifications` block (§10.7).
* Frontend: Safety Portal card renders new trench + certifications metrics. Company drilldown + per-project drilldown updated.
* Tests: `test_track_23_10_d_safety_kpi_trench_lift.py` — classification LIVE only when high-confidence · no double-count between DR signal and formal inspection · certifications counts match registry query.

### 🟡 Track 23.10-E · **DAILY REPORT V3 EXCAVATION SECTION + PDF + EMAIL + SCHEDULING READINESS**
* Depends on: 23.10-B (picker) + 23.10-C (fact emission).
* Frontend: V3 excavation gate + section (§8). `CompetentPersonCombo` picker (registry-gated). Restore-yesterday policy (§8.3). Mobile 390 verified.
* Backend: excavation_trench payload persistence · `excavation_day_fact` emit on submit · PDF renderer additions (§9) · email trigger rules (§9) · `scheduling_readiness.excavation_*` block (§10.6).
* Tests: gate collapsed when No · fields when Yes · expired-cert disabled · empty-state honest · restore-yesterday resets safety fields · PDF renders section only when work_today=true · scheduling_readiness `safety_clear_to_schedule=false` when hold/repair/utility/inspection blocker · mobile 390 no overflow.

**Sub-track order is fixed.** No sub-track ships before its dependencies.

---

## 12 · Risk register

| ID | Risk | Mitigation |
|---|---|---|
| R-01 | Extending `safety_training_records` model breaks existing 13 rows | Additive fields with defaults; existing enum values preserved; migration is a no-op for legacy rows |
| R-02 | Historical trench rows with free-text `competent_person_name` never map to a real employee | Preserve free-text snapshot verbatim on the row; new writes force picker; audit-safe |
| R-03 | Project linker inference (§5 rung 4) mis-attributes a hold to the wrong project when a box was transferred mid-day | Rule: match against the ACTIVE deployment at `opened_at`; ambiguous windows classified `ambiguous`, not LIVE |
| R-04 | Backfilling ODS facts for 984 excavations + 1127 holds + 432 inspections + 311 repairs could hit rate limits | One-time script runs offline with concurrency=8, `is_current=True` idempotency key on `(source_collection, source_id, event_kind)`; safe to re-run |
| R-05 | Cert expired mid-report → old draft references an expired cert | Picker validates on save via `resolve_active_for_employee`; draft submission blocks with clear message + prompt to re-pick |
| R-06 | Field operator with cert 1 day from expiry chooses to work anyway | Amber chip shows warning; selection allowed (not blocked) but fact carries `cert_valid_at_report=true` with `days_left` — HR gets expiration_fact daily digest |
| R-07 | B-04 invariant "Repair Complete ≠ Safe To Use" is weakened by aggregator logic | Explicit test lock: `test_track_23_10_c_repair_completed_never_implies_safe_to_use` asserts a repair with `status=completed` AND `verified_at IS NULL` produces `safe_to_use_verified=false` in the fact |
| R-08 | Scheduling reads `safety_clear_to_schedule=true` when there is a legitimate open hold on a shared asset | `scheduling_readiness` reads holds via the project_linker (§5); shared assets flagged when `project_link_status=ambiguous`; blocker returns true when ambiguity present |
| R-09 | Safety Portal double-counts an event that appears both as a Daily Report safety event and as a formal trench inspection | Different `fact_type`; aggregator emits both counters separately; documentation surfaces "operational signal vs formal inspection" distinction |
| R-10 | Competent Person concept collides with existing free-text `competent_person_confirmed` boolean in `trench_excavations` | Existing field is a self-report Yes/No; new picker adds `competent_person_id + certification_id` alongside — never rewrites the legacy bool |

---

## 13 · Files that WILL be created / modified (per sub-track)

**23.10-B**:
* NEW `backend/services/certifications/competent_person_registry.py`
* NEW `backend/tests/test_track_23_10_b_competent_person_registry.py`
* backend/routes/hr_portal.py (or new `routes/competent_person.py`) → `GET /api/employees/competent-persons`
* backend/routes/employee_lifecycle.py → certifications tab admin surface (additive fields)
* frontend/src/pages/EmployeeLifecycleCertifications.jsx (new tab under Employee Lifecycle Detail)

**23.10-C**:
* NEW `backend/services/trench_safety/project_linker.py`
* NEW `backend/services/ods_spine/trench_facts_emitter.py` (or inline in existing ingest)
* NEW `backend/scripts/backfill_track_23_10_trench_facts.py`
* NEW `backend/tests/test_track_23_10_c_trench_project_linker.py`
* No frontend changes.

**23.10-D**:
* `backend/services/operational_kpis/aggregator.py` (additive counters + classification lift)
* `frontend/src/components/SafetyOperationalKpisCard.jsx` (new trench + certifications blocks)
* NEW `backend/tests/test_track_23_10_d_safety_kpi_trench_lift.py`

**23.10-E**:
* NEW `frontend/src/components/daily-report-v3/SectionExcavationTrench.jsx`
* NEW `frontend/src/components/CompetentPersonCombo.jsx`
* `frontend/src/components/daily-report-v3/sections.jsx` (mount)
* `backend/services/ods_spine/ingest.py` (excavation_day_fact + assignment fact)
* `backend/pdf_render.py` (excavation section)
* `backend/services/email/*` (trigger rules)
* NEW `backend/tests/test_track_23_10_e_daily_report_excavation.py`

---

## 14 · Certification bar (each sub-track's Final Rule)

Each sub-track is CERTIFIED only when its own scope tests pass AND the mandate's 12 conditions relevant to that scope are satisfied. NO sub-track is certified in isolation as satisfying "Track 23.10" whole — the whole is only certified when 23.10-B/C/D/E all ship green with no fake data.

---

## 15 · Deployment recommendation for THIS design phase

**🟢 GO to review this design document.** No code changed. No safety data changed. No user impact.

Once you approve the design, the next session should execute **Track 23.10-B (Competent Person foundation)** first. Every subsequent sub-track is unblocked by 23.10-B.

**Estimated per-sub-track scope**:
* 23.10-B: ~35K tokens (backend service + endpoint + tests + admin cert UI tab)
* 23.10-C: ~40K tokens (linker + facts emitter + backfill script + tests · no UI)
* 23.10-D: ~30K tokens (aggregator lift + Safety Portal UI additions + tests)
* 23.10-E: ~45K tokens (DR V3 excavation section + picker + PDF + email + scheduling readiness + tests + screenshots)

Total: ~150K tokens across 4 sessions. Each session ships fully green regression + fully green browser proof for its scope.
