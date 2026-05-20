# HR Lifecycle Metadata Audit · iter284
**Status: visibility-only · NO schema changes · NO code changes · NO migrations**

## 0 · Purpose

Map the **current** state of employee lifecycle and driver qualification data so future bounded closure sequences can target the right gaps without scope drift.

This audit is NOT:
- HRIS expansion · FMCSA tooling · ELD/logbook · DOT compliance platform · telematics replacement · benefits/recruiting/applicant tracking · scheduling suite · performance management
- A redesign of the existing employee record
- A duplication of Motive (planned integration) or MaintainX (planned integration)

This audit IS:
- Evidence-based mapping of where lifecycle/qualification data currently lives, where it's missing, where notes are misused, what downstream surfaces depend on the gap.

---

## 1 · Current Employee Schema (live evidence)

### 1.1 Source of truth
`db.employees` — single canonical collection, owned by `backend/routes/employee_lifecycle.py` (iter152 / Phase C). No duplicate collection. Confirmed: HR + Field Leadership + Safety + Admin all read this collection.

### 1.2 Fields actually present on a representative live document
From a sampled live employee record (2026-05-20 snapshot):
```
created_at      crew         email           employee_id
id              is_active    name            phone
role            trade        updated_at
```
Plus (where set): `lifecycle_status`, `hire_date`, `status_history[]`, `supervisor`, `department`, `default_project_number`, `deleted_at`, `added_via`.

### 1.3 Live population counts (251 employees in db)

| Field | Documents w/ field set | Coverage |
| --- | ---: | ---: |
| `lifecycle_status` | 11 | **4.4%** |
| `hire_date` | 0 | **0%** |
| `notes` | 0 | 0% (field doesn't exist on schema) |
| `supervisor` | (varies — present on most) | — |
| `is_active` (legacy bool) | 251 | 100% |
| `deleted_at` (tombstone) | 246 active + 5 soft-deleted | 100% |

### 1.4 Status taxonomy (`ALLOWED_LIFECYCLE_STATUSES`, employee_lifecycle.py:44)
```
Pending Hire · Active · Inactive · Suspended · Terminated ·
Resigned · Retired · Seasonal · Leave of Absence
```
**9 statuses are supported.** Only 4 ever observed in live data (240 null · 6 Active · 4 Terminated · 1 Resigned). The `Seasonal` and `Leave of Absence` statuses are **infrastructure that exists but is not being used**.

### 1.5 Status history is structured (good)
Every status change appends to `status_history[]` with `{at, by, from, to, reason}`. This is **already operationally defensible** for the statuses HR is using. The gap is adoption, not structure.

### 1.6 Auto-offboarding playbook already exists (good)
On transition to `Terminated / Resigned / Retired`, the platform fans out an 8-task playbook (HR, Shop, Admin, Safety, PM) via task_service. **This is mature infrastructure that ~5 employees ever triggered.**

---

## 2 · What's MISSING (vs. user-directed required field set)

### 2.1 Employment lifecycle fields — coverage gap
| Required field | Present in schema? | Present in UI? | Live coverage |
| --- | --- | --- | ---: |
| Original Hire Date | ✅ `hire_date` (string) | ✅ edit field in HrEmployees | **0%** |
| Rehire Date | ❌ NOT in schema | ❌ NOT in UI | n/a |
| Termination Date | ❌ derived from `status_history[].at` when `to == "Terminated"` | ❌ never surfaced as own field | n/a |
| Leave Start Date | ❌ NOT in schema | ❌ status `Leave of Absence` exists w/o dates | n/a |
| Expected Return Date | ❌ NOT in schema | ❌ NOT in UI | n/a |
| Last Day Worked | ❌ NOT in schema (different from termination date) | ❌ NOT in UI | n/a |
| Employment Status enum | ✅ `lifecycle_status` 9-value enum | ✅ select in HrEmployees | 4.4% |
| Separation Type enum (voluntary / involuntary / layoff) | ❌ stored as free-text in `status_history[].reason` | ❌ no structured enum | n/a |

**Key insight**: of the 8 lifecycle fields requested, only **1 is fully wired (Employment Status)**, **1 is partially wired (hire_date — schema + UI, 0% populated)**, and **6 are entirely absent**. Of the 5 absent fields, 3 have implicit derivation paths through `status_history[]` but no first-class field.

### 2.2 Original Hire Date permanence — at risk
Schema has `hire_date` as a single mutable string field. **There is NO protection preventing it from being overwritten on rehire.** Per user directive: *"Original Hire Date must remain historically permanent."* The current schema allows trivial overwrite via `PATCH /api/hr/employees/{id}` with `{"hire_date": "2026-..."}`. **This is a structural risk, not just a coverage gap.**

### 2.3 Driver qualification fields — entirely absent
| Required field | Present in schema? | Present anywhere on platform? |
| --- | --- | --- |
| CDL Holder (flag) | ❌ | ❌ |
| Approved Company Driver (flag — DISTINCT from CDL Holder) | ❌ | ❌ |
| Driver Status (active/suspended/restricted/inactive) | ❌ | ❌ |
| CDL License Number | ❌ | ❌ structured · only as scanned PDF in legacy imports |
| CDL State | ❌ | ❌ |
| CDL Expiration Date | ❌ on employee | 🟡 trackable via `document_expirations` with `document_type="cdl_license"` but disconnected from the employee record (one row sampled · 0 currently populated for real CDLs) |
| Medical Card Expiration Date | ❌ on employee | 🟡 same — `document_type="medical_card"` available · 0 currently populated |
| Endorsements (N/H/X/T/P/S) | ❌ | ❌ |
| Air Brake / Manual Transmission restrictions | ❌ | ❌ |

### 2.4 Where CDL/medical data CURRENTLY lives
- `backend/legacy_imports.py` `DOCUMENT_TYPES` accepts `"cdl_license"` and `"medical_card"` as upload types via the OCR ingestion pipeline (iter249 Phase A — framework only · NOT activated for live promotion to employee records).
- `db.document_expirations` collection can hold CDL/medical card rows linked via `linked_employee_id`, but live data shows **0 real CDL rows and 0 real medical-card rows** — only iter151 test fixtures present (104 of 105 docs are test data; 1 real DOT Annual + 1 real OSHA 30).
- **Net effect**: the platform has the *ability* to ingest CDL/medical records as scanned documents with expiration dates, but the linkage from those documents back to a queryable "this employee is a CDL holder" flag does not exist anywhere.

---

## 3 · Where Lifecycle Data CURRENTLY Lives (tribal knowledge map)

### 3.1 Notes misuse — NOT observed in db
The `notes` field doesn't exist on the employee schema. **Tribal lifecycle data is NOT in notes** — it's worse: **it's not anywhere**. The user's directive ("currently lives in notes/tribal knowledge") describes the operational reality outside the platform (HR spreadsheets, manager memory, paper file folders) — not data hidden inside the system.

This is good news for closure: **no notes-to-structured-field migration burden** exists. Bad news: there's **no historical platform data to seed the new fields from** when implemented.

### 3.2 Where lifecycle dates leak in today
- **Hire date** → 0 records have it; HR knows it from paper files or memory
- **Termination date** → derivable from `status_history[].at` where `to == "Terminated"` (5 employees ever); never surfaced as a field
- **Leave dates** → no records · status `Leave of Absence` exists but no one has used it
- **Rehire** → no structural support; would currently overwrite the original `hire_date`

### 3.3 Surface map (where employee lifecycle data is read or displayed)

| Surface | Reads lifecycle? | Behavior |
| --- | --- | --- |
| `HrEmployees.jsx` (list + drawer) | ✅ | Status badge + hire_date in drawer · no termination date, no leave dates |
| `HrEmployeeAccountability.jsx` | ✅ | Reads `lifecycle_status` for offboarding-summary |
| `SafetyEmployeeProfiles.jsx` | (uses employee directory) | Status only |
| `HrFieldLeadership.jsx` | ✅ for active filter | Filters by `is_active` (legacy bool) |
| `routes/operations.py`, `operations_center.py` | ✅ active-only views | Filter by `is_active`, NOT lifecycle_status |
| `routes/safety_portal/training.py` | ✅ | Active-employee picker |
| `routes/master_lookup.py`, `master_where_used.py` | ✅ | Cross-collection employee references |
| `routes/admin_ops.py` | ✅ | Admin employee CRUD shadow |
| `routes/global_search.py` | ✅ | Search includes employee name |
| Tasks · CorrectiveActions · POs · DocExpirations | ✅ via `linked_employee_id` | Reference only |

**Insight**: ~10 backend surfaces read employee state, but most read the **legacy `is_active` boolean**, not `lifecycle_status`. This is the operational debt: `is_active` gets kept in sync by the lifecycle route (line 300: `_is_active_for_status`), but downstream code never learned the richer enum.

### 3.4 Dashboard / glance visibility gaps
| Operational question | Where it's answered today |
| --- | --- |
| Who is on the active roster right now? | ✅ HrEmployees list (filtered by `is_active`) |
| Who was terminated this month? | 🟡 only via `status_history` scan — no dashboard |
| Who is on leave and expected back when? | ❌ status enum exists, dates don't |
| How long has X been with the company? | ❌ 0% hire_date coverage — tenure not computable |
| Who can legally drive? | ❌ no field |
| Who is internally approved to operate company vehicles? | ❌ no field (distinct from above per user directive) |
| What CDL/medical expires in next 30/60/90? | 🟡 `document_expirations` answers it for whatever was uploaded — currently 0 real CDL rows |
| Who holds Tanker (N) endorsement? | ❌ no field |
| Who lost qualification status? | ❌ no field, no history |
| Are terminated employees still assigned equipment? | ✅ offboarding-summary surfaces this — but only after HR triggers a status change |

---

## 4 · Downstream Dependency Chains

### 4.1 Equipment / Dispatch / Fleet
- Equipment-assignment surfaces (`routes/fleet_ops.py`, `legacy_imports_equipment_checkout.py`) reference `employee_id` and `assigned_to_id` but **do not check driver qualification status** — because no such field exists.
- A terminated-but-equipment-attached employee surfaces only via the offboarding-summary (`equipment_issuances_count`). **Dispatch has no signal** that an assignee is unqualified to operate the equipment they hold.
- Fleet DVIR + visibility surfaces consume operator names but **do not validate CDL/Approved-Driver status**. Today's assumption: dispatch + foreman tribal knowledge prevents misassignment.

### 4.2 Safety / Training
- `routes/training_center.py` references training records loosely tied to employee.
- `db.document_expirations` is the **closest existing system** to CDL/medical card tracking — but the link is one-way (doc → employee), no reverse query lets "who has a current CDL?" run efficiently.

### 4.3 Tasks / Corrective Actions / POs
- All carry `linked_employee_id`. All would benefit from `lifecycle_status` filters (e.g., "open CAs against terminated employees"). Currently filterable only via custom client-side scan.

### 4.4 Motive / MaintainX integrations (planned)
- `services/motive_service.py` and `services/maintainx_service.py` are stubbed for read-only fleet data.
- **Critical alignment point**: when these integrations land, they will need an employee-side concept of "Approved Driver" to map Motive's driver list to MASCI's authoritative roster. Without the field, the integration will either invent its own driver list (bad) or operate as pure read-through display (limited).
- **This is the architectural anchor that makes "CDL Holder ≠ Approved Driver" a real distinction**: Motive can tell us who legally drives (their HOS/CDL data); MASCI must independently track who is internally approved to operate company assets. The two answers can disagree, and the operational risk is real.

---

## 5 · Existing Reusable Infrastructure (do NOT rebuild)

| Capability | File / surface | Status |
| --- | --- | --- |
| Employee CRUD + soft-delete | `routes/employee_lifecycle.py` | ✅ mature · iter152 |
| Status history with attribution | `status_history[]` array on employee doc | ✅ mature |
| Offboarding playbook (8 tasks) | `_OFFBOARDING_PLAYBOOK` | ✅ mature |
| Offboarding summary (open tasks/docs/equipment/CAs/POs) | `/api/hr/employees/{id}/offboarding-summary` | ✅ mature |
| Document expiration tracker | `routes/document_expirations.py` + `db.document_expirations` | ✅ mature · supports cdl_license + medical_card doc_types · 0% real adoption |
| Expiration threshold scanner | `document_expirations.py::_scan` | ✅ mature |
| `StatusBadge` component (frontend) | `frontend/src/components/StatusBadge.jsx` | ✅ used for lifecycle_status today |
| `EditField` inline editor (frontend) | `frontend/src/components/EditField.jsx` (used in HrEmployees drawer) | ✅ pattern reusable for new fields |
| Lifecycle status enum + active-filter logic | `_ACTIVE_STATUSES`, `_OFFBOARDING_STATUSES` constants | ✅ extension point for separation_type |
| HelpTipBlock coaching family for employee-lifecycle | `test_iter224_employee_lifecycle_helptips.py` references existing form_keys | ✅ pre-existing coaching surface |

**Implication**: a future closure for these fields should EXTEND the existing schema/UI, not replace them. The `EditField` + `StatusBadge` + `status_history[]` patterns are already operationally proven.

---

## 6 · Operational Risks Identified

1. **Original Hire Date permanence** is structurally unprotected — direct PATCH can overwrite it (Section 2.2). Real risk on rehires.
2. **96% of employees have no lifecycle_status** — the legacy `is_active` bool is doing the work of a richer enum, masking the staleness of the data.
3. **Driver qualification = tribal knowledge entirely** — neither CDL nor "Approved Driver" exist as fields. Equipment assignment surfaces have no validation hook.
4. **Motive integration has nothing to map to** — when it lands, "Approved Company Driver" must already exist on the MASCI side, or the integration becomes a bolt-on without authoritative linkage.
5. **Separation type stored as free-text reason** — not filterable, not auditable for unemployment-claim or rehire-policy patterns.
6. **No leave date pair** — `Leave of Absence` status exists with no start/end dates. The status alone is operationally useless without dates.
7. **Termination date is not a field** — derivable from `status_history`, but no surface exposes it; HR can't sort by "terminated this quarter" cheaply.

---

## 7 · Out-of-Scope Confirmations (per user directive)

Following NOT touched in this audit and explicitly NOT in scope for any iter285+ closure:
- HRIS expansion · benefits · payroll replacement · applicant tracking · recruiting · scheduling · performance management
- DOT compliance suite · FMCSA tooling · CSA management · ELD/logbook
- Telematics or fleet GPS replacement (Motive's job)
- Equipment maintenance management (MaintainX's job)
- I-9, W-4, EEO, ACA — federal compliance forms beyond what `legacy_imports` already accepts as scanned PDFs

---

## 8 · Recommended Bounded Closure Sequence (iter285+)

**The audit's job ends here.** Closure sequencing below is a proposal awaiting user gate — not a commitment.

### Proposed iter285 — Employment Lifecycle Date Structure (no driver fields yet)
Bounded to 3 atomic field additions + 1 protective rule:
1. `original_hire_date` (string · write-once · enforced server-side · NOT overwritable on PATCH)
2. `last_day_worked` (string · written on Terminated/Resigned/Retired transition · also accessible via dedicated PATCH)
3. `leave_start_date` + `expected_return_date` (string pair · validated on `Leave of Absence` status transition)
4. `separation_type` enum (`voluntary` · `involuntary` · `layoff` · null) — required when status transitions into an offboarding status
5. Derived `tenure_days` field computed at read time from `original_hire_date` (no stored value · single source of truth)

Surfaces touched: `employee_lifecycle.py` (Pydantic models + status-change handler) · `HrEmployees.jsx` drawer (read-only display + dedicated edit affordances) · regression pytest.

**Rehire handling**: do NOT introduce `rehire_dates[]` in iter285 (per user directive: *"do not implement unless audit justifies it"*). Audit position: defer — the rehire_dates question is real but better handled in a separate sequence after Section 8.1 lands and HR has live data to inform the shape.

### Proposed iter286 — Driver Qualification Foundation (separate sequence)
Bounded to the core distinction:
1. `cdl_holder` (bool · default false)
2. `approved_company_driver` (bool · default false · DOCUMENTED as distinct from cdl_holder)
3. `driver_status` enum (`active` · `suspended` · `restricted` · `inactive` · null — only meaningful when `approved_company_driver=true`)
4. `cdl_license_number` · `cdl_state` (strings · no validation beyond length/format)
5. `cdl_expiration_date` · `medical_card_expiration_date` (strings · also create matching `db.document_expirations` rows on PATCH so the existing expiration scanner picks them up)

Surfaces touched: same files as iter285 + the document-expirations linkage trigger.

### Proposed iter287 — Endorsements (separate sequence)
Single field: `endorsements` (array of canonical short codes from `{N, H, X, T, P, S}` + optional restrictions `{air_brake_restriction, manual_transmission_restriction}` as booleans). One-shot field; tone-of-MASCI emphasis on Tanker (N) per user directive.

### Proposed iter288 — Operational Dashboard Visibility (NOT compliance management)
Lightweight surface answering the operational questions from Section 3.4:
- "Active roster" filter chips (lifecycle_status x driver_status)
- "Expiring next 30/60/90 days" cards backed by existing `document_expirations` scanner — NOT a new scan engine
- Endorsement filter chips
- "Approved drivers" sub-view

**Explicit non-goals**: no compliance-management workflow · no automated CSA-style scoring · no automated suspension cascades · no Motive sync (that's a separate integration sequence).

---

## 9 · Matrix Impact (deferred — no flips made by this audit)

This audit identifies **at least 2 new candidate rows** for the maturity matrix:
- Employee Lifecycle Completeness (currently invisible · ~4% coverage)
- Driver Qualification Visibility (currently invisible · 0% coverage)

Per user governance ("Do NOT begin matrix column retirement yet — visibility over elegance"), the same principle applies in reverse: matrix row ADDITIONS should wait until closure work actually defines the dimensions, not be invented by the audit.

**Recommendation**: add the rows when iter285 lands, not before.

---

## 10 · Summary One-Liner (for ship-log)

> 251 employees · 4.4% lifecycle_status adoption · 0% hire_date coverage · 0 driver qualification fields anywhere · existing infrastructure (status_history, offboarding playbook, document_expirations) is mature and reusable · the gap is operational coverage, not architectural deficit · proposed iter285/286/287/288 sequences bound the closure work without HRIS / FMCSA drift.

---

*Generated by iter284 audit · evidence-based · visibility-only · NO code changes performed.*
