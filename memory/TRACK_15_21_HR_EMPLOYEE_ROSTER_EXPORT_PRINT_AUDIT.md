# TRACK 15.21 — HR EMPLOYEE ROSTER EXPORT + PRINT
## READ-ONLY AUDIT (NO CODE WRITTEN)

**Operator directive:** *Audit first. Do not build first.*
**Implementation preference:** **Option C — most minimal, safest, reuse-first path.**
**Author:** E1 (Emergent main agent)
**Status:** Audit complete · awaiting operator approval before implementation.

---

## 0 · TL;DR (one screen)

| Question | Answer |
|---|---|
| Does HR roster data already exist? | **Yes.** `db.employees` collection. ~1 source of truth. |
| Is there an HR endpoint that returns it? | **Yes.** `GET /api/hr/employees` (HR + Admin gated). |
| Is there already an HR-facing roster UI? | **Yes.** `/hr/employees` → `HrEmployees.jsx` renders the table. |
| Does an export already exist? | **Yes, partially.** `GET /api/admin/employees/export` returns `.xlsx` (Admin-only, 7 columns). HR cannot reach it. |
| Does a print path already exist? | **No** on the HR roster page. (`HrTimeVerification.jsx` has the print pattern we can copy.) |
| Are SSN / DOB / salary fields stored? | **No.** None of the three exist on the schema. |
| Is .xlsx safely supported today? | **Yes.** `openpyxl==3.1.5` is already installed; `_xlsx_response()` helper already at `server.py:1537`. |
| Is reportlab/PDF already supported? | **Yes**, but PDF is **not recommended** for this feature — print-to-PDF from the browser is simpler. |
| Recommended path | **Reuse `GET /api/admin/employees/export` shape, add an HR-gated mirror `GET /api/hr/employees/export.xlsx` + browser-print stylesheet on `HrEmployees.jsx`.** No new collections, no new libraries, no new auth, no PDF engine. |

---

## 1 · Phase 1 — Inventory of employee data sources

### 1.1 Primary collection (single source of truth)

`db.employees` — used everywhere the platform asks "who is on staff."

- Created/managed by `routes/employee_lifecycle.py` (HR lifecycle CRUD).
- Soft-deleted via `deleted_at`. Default queries always filter `deleted_at: null` (`ACTIVE_FILTER` in `server.py`).
- Lifecycle status tracked via `lifecycle_status` (one of: Pending Hire, Active, Inactive, Suspended, Terminated, Resigned, Retired, Seasonal, Leave of Absence).
- "Actively employed" subset (used as the HR default view): `{Active, Pending Hire, Seasonal, Leave of Absence}`.

### 1.2 Field inventory on the employee document

Sourced from `routes/employee_lifecycle.py` (`EmployeeCreate`/`EmployeePatch` Pydantic models) and the actual document layout used by `server.py` projections.

| Field | Type | Origin |
|---|---|---|
| `id` | str (uuid) | system |
| `name` | str | HR ("Legal Name") |
| `legal_first_name`, `legal_middle_name`, `legal_last_name` | str | Track 14.0 identity split (optional / legacy still has only `name`) |
| `preferred_name` | str | HR-EMPLOYEE-002 |
| `employee_id` | str (HR ID number) | HR |
| `trade` | str | HR |
| `role` | str | HR (title) |
| `crew` | str | HR |
| `department` | str | HR |
| `supervisor` | str | HR (free-text label, not a foreign key) |
| `default_project_number` | str | HR |
| `email` | str | HR |
| `phone` | str | HR |
| `hire_date` | str (YYYY-MM-DD) | HR (legacy) |
| `original_hire_date` | str (write-once) | HR (iter285) |
| `last_day_worked` | str | HR (separation) |
| `termination_date` | str | HR (separation) |
| `leave_start_date` | str | HR (leave) |
| `expected_return_date` | str | HR (leave) |
| `separation_type` | enum: voluntary / involuntary / layoff | HR |
| `rehire_eligibility` | enum: eligible / not_eligible / review_required | HR (iter316) |
| `rehire_eligibility_reason` | free-text 500 chars | HR |
| `rehire_date` | str | HR |
| `lifecycle_status` | enum (9 values) | HR |
| `is_active` | bool (kept in sync with status) | system |
| `tenure_days` | int (derived, not stored) | system @ read |
| `display_identity` | str (derived) | system @ read |
| `cdl_holder` | bool | HR / Safety |
| `approved_company_driver` | bool | HR |
| `driver_status` | enum | HR |
| `cdl_license_number` | str | HR |
| `cdl_state` | str (2 char) | HR |
| `cdl_expiration_date` | str | HR (mirrored into document_expirations) |
| `medical_card_expiration_date` | str | HR (mirrored into document_expirations) |
| `cdl_endorsements` | list of codes | HR |
| `cdl_restrictions` | list of codes | HR |
| `status_history` | array of `{at, by, from, to, reason, kind?, …}` | system (every transition) |
| `added_via` | str | system |
| `created_at`, `updated_at`, `deleted_at` | ISO | system |

**Fields that do NOT exist on this schema (confirmed via grep across the entire backend):**
- ❌ **No `ssn`** (Social Security Number)
- ❌ **No `date_of_birth` / `dob`**
- ❌ **No `salary` / `wage` / `pay_rate`**
- ❌ **No `home_address` / `mailing_address`**
- ❌ **No `emergency_contact` / `emergency_contact_phone`**

This is the cleanest possible audit outcome — **there is no PII landmine on this collection.** Whatever HR exports cannot accidentally leak SSN/DOB/salary, because none of those values were ever stored here.

### 1.3 Secondary collections that mention employees (NOT roster sources)

The audit confirmed these are *reference* collections, not roster sources, and must **not** be mixed into the export:
- `user_directory` — portal accounts (HR, PM, Admin logins) — different population, different purpose, contains password hashes.
- `field_leadership_users` — Field Leadership login accounts only.
- `safety_training_records`, `training_track_records` — per-training rows (not roster).
- `field_leadership_records`, `incidents`, `safety_forms`, `document_expirations`, `tasks`, `corrective_actions`, `po_requests`, `project_team_assignments` — *transactional* records that reference `employee_id`.

None of these are part of the roster export scope.

---

## 2 · Phase 2 — Existing roster endpoints (read)

| Endpoint | Auth gate | Returns | Use for export? |
|---|---|---|---|
| `GET /api/hr/employees` (`routes/employee_lifecycle.py:911`) | HR or Admin (`require_hr_or_admin`) | Full employee document set, filters: `show_inactive`, `lifecycle_status`, `rehire_eligibility`, `q` | **✅ Yes — primary feed for HR export.** Returns exactly what HR sees on screen plus a couple of derived fields. |
| `GET /api/employees` (`server.py:3763`) | Public | Hardened projection: `id, name, employee_id, crew, role, trade, is_active` only | ❌ No. Public projection was hardened by OMEGA 2026-06-03; using it would lose lifecycle/supervisor/department. |
| `GET /api/admin/employees/export` (`server.py:1567`) | Admin-only (`require_admin`) | `.xlsx` with 7 columns (Name, Employee ID, Trade, Role, Crew, Email, Phone) of the active-only roster | ⚠️ Partially. **Admin-only.** HR cannot use this. The column set is also narrower than HR's screen. |
| `GET /api/admin/employees/status` (`server.py:3786`) | HR-or-Admin | Counts only | ❌ No. |
| `GET /api/admin/employees/archive` (`server.py:3806`) | HR-or-Admin | Soft-deleted rows | ❌ No (out of scope; HR asked for the active roster). |
| `GET /api/master-lookup/employees` (`routes/master_lookup.py:87`) | Mixed | Typeahead | ❌ No. |

**Observation D-21 (informational, not blocking):** `GET /api/admin/employees/export` is admin-only but the function it performs (export the active roster) is something HR explicitly needs. Two viable resolutions:
1. **Recommended (Option C):** Add a sibling HR-gated endpoint that reuses the same `_xlsx_response()` helper and the same column shape — keep the admin one untouched.
2. Alternative: Relax the admin gate to `require_hr_or_admin`. Slightly riskier because admins may have relied on the admin-only gate for compliance reporting.

---

## 3 · Phase 3 — Existing UI surface (what HR already sees on screen)

### 3.1 Route + file

- Route: **`/hr/employees`**
- File: `/app/frontend/src/pages/HrEmployees.jsx`
- API client: `/app/frontend/src/lib/employeesApi.js` → `listHrEmployees(params)`
- Sidebar entry: `HrSideNavV2.jsx`
- Gate: `isHr() || isAdmin()` (frontend); the backend gate is `require_hr_or_admin`.

### 3.2 Visible columns on the HR roster table today (HrEmployees.jsx lines 211–283)

| # | Column header | Source field(s) |
|---|---|---|
| 1 | Status | `lifecycle_status` (Active / Inactive / …) |
| 2 | Legal Name | `legal_first_name + legal_last_name` (fallback: `name`) |
| 3 | Preferred Name | `preferred_name` |
| 4 | Trade / Role | `trade` · `role` |
| 5 | Crew | `crew` |
| 6 | Supervisor | `supervisor` |
| 7 | Accountability (link) | — (per-row link, not a value) |

There is also a header strip with three summary tiles: **Actively Employed**, **Inactive / Off-roll**, **Total in View**, and a filter bar (`Show Inactive`, status, rehire-eligibility, search).

### 3.3 What is NOT currently visible but exists on the record

Visible in the row drawer (one-employee detail panel) but **not** in the main table:
- `employee_id` (HR ID number)
- `email`, `phone`
- `department`, `default_project_number`
- `hire_date`, `original_hire_date`, tenure
- All separation/leave dates and CDL/medical fields
- `status_history`, `rehire_eligibility_reason`

The current main-table column set is intentionally compact for screen readability.

---

## 4 · Phase 4 — Field sensitivity classification

Each field that *could* end up in an export, classified per operator's directive ("Sensitive data must not be blindly exported"):

| Field | Default include? | Notes / requires user decision? |
|---|---|---|
| `name` (Legal Name) | ✅ Include | — |
| `preferred_name` | ✅ Include | — |
| `employee_id` (HR ID #) | ✅ Include | — |
| `lifecycle_status` | ✅ Include | The roster is meaningless without it. |
| `trade` | ✅ Include | — |
| `role` | ✅ Include | — |
| `crew` | ✅ Include | — |
| `supervisor` | ✅ Include | — |
| `department` | ✅ Include | — |
| `default_project_number` | ✅ Include | Operational, not sensitive. |
| `hire_date` | ✅ Include | Operational. (No DOB exists, so this can't be confused with one.) |
| `original_hire_date` | ✅ Include | Tenure cornerstone. |
| `email` | ⚠️ **HR-only include** | Company email; safe within HR, but should never appear on the *Public* `/api/employees` endpoint (already hardened). Keep it on the HR-only export. |
| `phone` | ⚠️ **HR-only include** | Same as email. |
| `cdl_holder`, `approved_company_driver`, `driver_status` | ⚠️ **HR-only include** | Operationally sensitive — relevant for HR DOT compliance audits. |
| `cdl_license_number` | 🟥 **EXCLUDE by default** | Government-issued ID number. Not needed for a roster print/export. HR can still see it in the per-employee drawer. **Requires explicit operator decision** to ever include in a bulk export. |
| `cdl_state` | ⚠️ HR-only, but ✅ ok to include | Just the state code (e.g., "OR"). Not sensitive on its own. |
| `cdl_expiration_date`, `medical_card_expiration_date` | ⚠️ HR-only include | DOT compliance fields — HR explicitly needs these for expiration tracking. Useful in the export. |
| `cdl_endorsements`, `cdl_restrictions` | ⚠️ HR-only include | DOT compliance fields. |
| `separation_type` | ⚠️ HR-only include | Useful for off-roll views but never for a public print. |
| `termination_date`, `last_day_worked`, `leave_start_date`, `expected_return_date` | ⚠️ HR-only include | Lifecycle audit. Useful when `show_inactive=true`. |
| `rehire_eligibility` | ⚠️ **HR-only include** | Sensitive — judgment field (eligible / not_eligible / review_required). |
| `rehire_eligibility_reason` | 🟥 **EXCLUDE by default** | **Free-text** judgment field ("attendance pattern · policy violation · job abandonment"). **Highest leak risk** on the entire schema. Should NEVER appear in a print-the-roster output. HR can still see it in the per-employee drawer. **Requires explicit operator decision** to include. |
| `status_history` (array of `{from,to,reason,by,at,kind}`) | 🟥 **EXCLUDE by default** | Contains free-text `reason` per transition. Audit trail belongs in the drawer / accountability timeline, NOT in a bulk export row. **Requires explicit operator decision**. |
| `id` (UUID) | ❓ Optional — not useful to a human reader | Recommend omit. |
| `is_active` | ❓ Redundant with `lifecycle_status` | Recommend omit. |
| `created_at`, `updated_at`, `added_via`, `deleted_at` | 🟥 Exclude | Internal system metadata. |

**Fields needing user decision before they appear in any export:**
- 🟥 `cdl_license_number`
- 🟥 `rehire_eligibility_reason`
- 🟥 `status_history`

Everything else has a clean default (Include / HR-only Include / Exclude).

### 4.1 Recommended default column set for the roster export/print (Option C)

A small, operationally-honest column list that mirrors what HR already sees on screen, plus the contact + lifecycle dates they need for payroll/DOT/onboarding cross-checks:

1. Status (`lifecycle_status`)
2. Employee ID
3. Legal Name (`name`)
4. Preferred Name
5. Trade
6. Role
7. Crew
8. Supervisor
9. Department
10. Email
11. Phone
12. Hire Date (`hire_date` or `original_hire_date`)

This matches the existing admin export's intent (Name/ID/Trade/Role/Crew/Email/Phone) plus the four fields the HR roster screen actually shows that the admin export omits (Status, Preferred Name, Supervisor, Department) plus Hire Date for tenure reference.

**Driver-qualification block** (CDL holder, CDL state, CDL/Medical expiration, endorsements, restrictions) is recommended as an **optional second sheet** in the .xlsx labeled "Driver Qualification" so HR can use the same file for DOT reviews without forcing it into the default print layout. Decision left to operator.

---

## 5 · Phase 5 — Permission / role audit

### 5.1 Who can already reach the data?

- `GET /api/hr/employees` → **HR or Admin** via `require_hr_or_admin` (`routes/employee_lifecycle.py:904`). This is the canonical gate.
- `GET /api/admin/employees/export` → **Admin only** via `require_admin`.
- `GET /api/employees` → **Public** (hardened projection).

### 5.2 Who should be allowed to export / print?

Per operator's directive ("HR needs to print and export the employee roster"):

| Role | Allowed to export/print? | Rationale |
|---|---|---|
| **HR** | ✅ Yes | Primary user. |
| **Admin** | ✅ Yes | Already implicit — admin has HR-or-Admin clearance everywhere. |
| Safety | ❌ No (not requested) | The safety portal has its own competent-person roster surface. |
| PM / Dispatch / Shop / Field Leadership | ❌ No | None of these portals have access to the HR `/hr/employees` page today. |
| Public / unauthenticated | ❌ No | Same as today. |

**Recommended gate for the new endpoint:** `require_hr_or_admin` (already defined in `routes/employee_lifecycle.py`). No new auth code needed.

### 5.3 Audit-log of the export action?

`GET /api/hr/employees` is a hot path called every time HR opens the page; we should not audit-log every roster fetch. **But** a bulk export of names + emails + lifecycle status is a different posture — recommend a lightweight `audit_events` entry on export (mirrors patterns used elsewhere). Not strictly required by the operator request, but cheap to add (one `db.audit_events.insert_one`). Final decision = operator.

---

## 6 · Phase 6 — Export format requirements & recommended path

### 6.1 What's already available

- `openpyxl==3.1.5` — installed (`backend/requirements.txt`).
- `pandas==3.0.2` — installed (overkill; not needed).
- `reportlab==4.5.1` — installed (PDF; not needed here).
- `_xlsx_response(rows, header, filename, sheet)` — already defined at `server.py:1537`. Auto-widens columns, sets correct MIME type, sets correct `Content-Disposition`. **Pure reuse.**
- 4 existing endpoints use this helper (`/admin/employees/export`, `/admin/suppliers/export`, `/admin/equipment-master/export`, `/admin/equipment-parts/export`).
- `python-csv` (`csv` stdlib) is always available.

### 6.2 Option matrix

| Path | Lib needed | Compat | Effort | Safety | Verdict |
|---|---|---|---|---|---|
| **A. Server-side `.xlsx` via `_xlsx_response`** | None new (`openpyxl` already there) | Excel, Google Sheets, Numbers, LibreOffice | **Lowest** — one new function. | Highest — file is generated server-side, no JS deps. | ✅ **Recommended.** |
| B. Server-side `.csv` (stdlib only) | None | Excel (yes, auto-opens), Sheets, Numbers | Very low | High | Reasonable secondary download option HR can keep alongside .xlsx. |
| C. Client-side `.xlsx` via SheetJS / `xlsx` package | Adds a frontend dep | Same | Higher | Slightly riskier (relies on frontend memory; HR's iPad may be a hassle for big rosters). | ❌ Not recommended. |
| D. PDF via reportlab | None | Universal | Medium | Already supported elsewhere | ❌ Not recommended for *roster* export — operator instruction: "no PDF unless already supported and necessary." Browser print-to-PDF covers it. |

**Recommendation:** Implement **Path A** (.xlsx). Path B (.csv) can be a 5-line bonus if operator wants both. Path C and D not needed.

### 6.3 Sheet structure

- Sheet 1: "Employees" — the 12 default columns from §4.1.
- Sheet 2 (optional, HR decision): "Driver Qualification" — CDL/Medical fields. Omit by default.
- Filename: `MASCI_HR_Employee_Roster_YYYY-MM-DD.xlsx`.
- Honor the **same filters HR currently has on screen** (search query, lifecycle_status, rehire_eligibility, show_inactive). Reusing the existing `list_employees` query shape is what makes this Option-C-minimal — no new query plumbing.

---

## 7 · Phase 7 — Print requirements & recommended path

### 7.1 What's already available

- Existing pattern: **`HrTimeVerification.jsx`** has an in-page `<style>@media print { … }` block (lines ~132–280) that uses `[data-print-region]`, `[data-print-only]`, `[data-print-hide]` attribute hooks, then triggers `window.print()` on a Print button. This is the established MASCI print pattern.
- `index.css` has additional `@media print` rules.

### 7.2 Option matrix

| Path | Effort | Safety | Verdict |
|---|---|---|---|
| **A. Browser print (`window.print()`) + `@media print` stylesheet on `HrEmployees.jsx`** | Lowest. Copy the `HrTimeVerification.jsx` pattern. | Highest — no new dependencies. | ✅ **Recommended.** |
| B. Server-rendered PDF via reportlab | Medium. Existing pattern via `hr_employee_compliance_brief_pdf`. | Already in use, but unnecessary here. | ❌ Not recommended — overkill. |
| C. Client-side react-to-print package | Adds dep. | Avoidable. | ❌ Not recommended. |

**Recommendation:** **Path A.** Add a `<Button data-testid="hremp-print" onClick={() => window.print()}>` next to the existing Refresh / Add Employee bar; add a `<style>@media print { … }` block scoped to the roster page that hides everything except the table + a clean header strip ("MASCI Employee Roster · {date} · filters: …").

This is **2 small additions to one existing file**. Zero new files, zero new libraries.

### 7.3 Print output structure (recommended)

- Top header (print-only): MASCI logo / wordmark + "Employee Roster" + filter description + current date + total count.
- Table: same 7 visible columns from §3.2 (Status / Legal Name / Preferred / Trade · Role / Crew / Supervisor / Accountability omitted) → drop "Accountability" column and add "Employee ID" so the printed sheet is uniquely identifiable in a stack of paper.
- Hide: filter bar, summary tiles, search input, refresh button, add-employee button, sidebar, NotificationBell, hover-only row affordances.
- `page-break-inside: avoid` on `<tr>` (already used in `HrTimeVerification.jsx`).
- Default landscape if HR's printer driver supports it (the user picks at the print dialog; we can recommend via `@page { size: landscape; }`).

---

## 8 · Phase 8 — Risk register

| # | Risk | Severity | Mitigation under Option C |
|---|---|---|---|
| R-1 | Leaking `rehire_eligibility_reason` in a bulk export. | 🟥 High | Exclude by default (see §4). Require explicit operator decision before adding. |
| R-2 | Leaking `cdl_license_number`. | 🟥 High | Exclude by default. |
| R-3 | Leaking `status_history` (free-text reasons per transition). | 🟥 High | Exclude by default. |
| R-4 | Non-HR users reaching the new endpoint. | 🟧 Medium | Use existing `require_hr_or_admin` gate. Frontend uses `isHr() \|\| isAdmin()` exactly like the current `/hr/employees` page. |
| R-5 | Production roster size > 5000 (`docs.to_list(5000)` limit in existing admin export). | 🟨 Low | Current MASCI employee count is well under this. Keep the same 5000 cap. Reuse, don't expand. |
| R-6 | New endpoint forgetting `ACTIVE_FILTER` and pulling soft-deleted rows. | 🟨 Low | Mirror the exact filter clauses that `GET /api/hr/employees` already uses. |
| R-7 | Print stylesheet leaking debug content (e.g., focused row, hover styles) onto paper. | 🟨 Low | Scoped `@media print` block hides interactive affordances; the `HrTimeVerification.jsx` pattern already does this cleanly. |
| R-8 | A frontend export-button-spam (HR clicking many times) hammers backend with full table reads. | 🟨 Low | Add the same `Cache-Control: no-store` header used by other exports; debounce on the button if it ever becomes an issue. Out-of-scope to pre-optimize. |
| R-9 | Bot/probe hitting the new export endpoint without an HR token. | 🟨 Low | Existing 401 from `require_hr_or_admin`. Already in place — no new attack surface. |

No risks above ⬛ block; the implementation is straightforward.

---

## 9 · Phase 9 — Recommended implementation plan (Option C: minimal, safe, reuse-first)

### 9.1 Surface count (intentionally small)

- **0 new collections.**
- **0 new libraries (backend or frontend).**
- **0 new auth flows / tokens.**
- **1 new backend endpoint** (`GET /api/hr/employees/export.xlsx`).
- **1 new frontend button + scoped `@media print` block** on `HrEmployees.jsx`.

### 9.2 Backend change (≤ ~60 lines, in an existing file)

**File:** `/app/backend/routes/employee_lifecycle.py`
**Location:** Right after the existing `GET /api/hr/employees` handler (around line 966).

```python
@router.get("/api/hr/employees/export.xlsx")
async def export_hr_employees(
    actor: Dict[str, Any] = Depends(require_hr_or_admin),
    show_inactive: bool = Query(default=False),
    lifecycle_status: Optional[str] = Query(default=None),
    rehire_eligibility: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None, max_length=80),
):
    # Reuse the exact same query the on-screen roster uses so the
    # exported file == what HR sees. No divergence.
    ... build `final` clauses identical to list_employees() ...
    docs = await db.employees.find(final, {"_id": 0}).sort("name", 1).to_list(5000)
    header = [
        "Status", "Employee ID", "Legal Name", "Preferred Name",
        "Trade", "Role", "Crew", "Supervisor", "Department",
        "Email", "Phone", "Hire Date",
    ]
    rows = [[
        d.get("lifecycle_status") or "",
        d.get("employee_id") or "",
        d.get("name") or "",
        d.get("preferred_name") or "",
        d.get("trade") or "",
        d.get("role") or "",
        d.get("crew") or "",
        d.get("supervisor") or "",
        d.get("department") or "",
        d.get("email") or "",
        d.get("phone") or "",
        d.get("original_hire_date") or d.get("hire_date") or "",
    ] for d in docs]
    from server import _xlsx_response, _today_stamp   # reuse helper
    return _xlsx_response(rows, header,
                          f"MASCI_HR_Employee_Roster_{_today_stamp()}.xlsx",
                          "Employees")
```

**Why this is safe:**
- Uses `require_hr_or_admin` — same gate as the existing roster endpoint.
- Honors the same filters HR already has on screen.
- Excludes every field flagged 🟥 in §4.
- Returns `.xlsx` via the **already-tested** `_xlsx_response()` helper.
- No new collection access, no PII fields touched.

### 9.3 Frontend change (≤ ~50 lines, in an existing file)

**File:** `/app/frontend/src/pages/HrEmployees.jsx`
**Changes:**

1. **Top of file** — add two icon imports: `Printer`, `Download` from `lucide-react`.
2. **Filter bar** — add two buttons next to the existing Refresh button:
   - `<Button data-testid="hremp-print" onClick={() => window.print()}>` Print
   - `<Button data-testid="hremp-export-xlsx" onClick={exportXlsx}>` Export .xlsx
3. **`exportXlsx()`** — a small async function that:
   - Builds a `URLSearchParams` from current filter state.
   - Calls `axios.get(${API}/hr/employees/export.xlsx, { params, headers: authHeaders(), responseType: 'blob' })`.
   - Triggers a download via `URL.createObjectURL` + a hidden `<a download>`.
   - Toasts on success/failure.
4. **`@media print` block** — copy the structure from `HrTimeVerification.jsx`:
   - Hide sidebar, filter bar, search input, refresh, add-employee, sticky badges, accountability link column, hover affordances.
   - Add a print-only header at the top: "MASCI Employee Roster · {today} · {filter description}".
   - Style the table for paper (black borders, page-break-inside avoid, smaller font).

### 9.4 What is explicitly NOT being built

- ❌ No new "employee system" / collection / migration.
- ❌ No new reporting engine.
- ❌ No `xlsx`/`sheetjs`/`file-saver` npm dependency.
- ❌ No reportlab PDF for the roster (browser-print covers it).
- ❌ No bulk export of `rehire_eligibility_reason`, `cdl_license_number`, or `status_history` — those stay in the per-employee drawer.
- ❌ No exposing the export to PM / Shop / Safety / Dispatch / Field Leadership / public.

### 9.5 Testing checklist (for post-approval implementation)

Backend (`pytest` style, in `/app/backend/tests/`):
1. ✅ `GET /api/hr/employees/export.xlsx` without auth → 401.
2. ✅ With HR token → 200, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`, `Content-Disposition: attachment; filename="MASCI_HR_Employee_Roster_...xlsx"`.
3. ✅ With Admin token → 200.
4. ✅ Honors `q=` / `lifecycle_status=` / `show_inactive=` / `rehire_eligibility=`.
5. ✅ Does NOT include any of the 🟥 fields anywhere in the file body.
6. ✅ Row count matches `GET /api/hr/employees` with the same filters.
7. ✅ Soft-deleted rows are excluded.

Frontend (Playwright via `testing_agent_v3_fork`):
1. ✅ HR session reaches `/hr/employees` and sees the new Print and Export .xlsx buttons.
2. ✅ Export .xlsx button downloads a file with the expected name.
3. ✅ Print button triggers `window.print()` and the print preview shows the cleaned layout (no sidebar, no filter chrome, header strip visible).
4. ✅ Non-HR portals (PM/Shop/Safety/Dispatch/Field Leadership) cannot reach `/hr/employees` (already covered by current AccessDenied gate — regression check).

### 9.6 Effort estimate

- Backend: ~30 minutes of dev + ~15 minutes of test write.
- Frontend: ~45 minutes of dev + ~10 minutes of stylesheet tuning.
- E2E test via `testing_agent_v3_fork`: ~10 minutes.
- **Total: under 2 hours of focused work.** No new infra, no new libraries.

---

## 10 · Open decisions awaiting operator sign-off

Before implementation begins, the operator should confirm:

| # | Decision | Default if not specified |
|---|---|---|
| D-1 | The 12 default columns in §4.1 are the right set? | Use as-is. |
| D-2 | Add the optional second sheet "Driver Qualification" with CDL/Medical fields? | **Omit by default** (HR can request it later — bounded scope per Option C). |
| D-3 | Add an `audit_events` row on each export? | **Skip** (lightweight feature; operator can opt-in later). |
| D-4 | Add a .csv twin endpoint (`/api/hr/employees/export.csv`)? | **Skip** (.xlsx opens in Excel/Sheets/Numbers; operator hasn't asked for .csv). |
| D-5 | Include `rehire_eligibility` (HR-only enum, not the free-text reason) in the export? | **Include** when `show_inactive=true` is active; **omit** otherwise. |
| D-6 | Loosen `GET /api/admin/employees/export` to HR-or-Admin instead of adding the new HR endpoint? | **No** — keep the existing admin export untouched; add the new HR-gated sibling endpoint. |
| D-7 | Add a print-friendly **per-employee** profile sheet next to the roster print? | **Out of scope** — operator asked for *the roster*. |

---

## 11 · Audit conclusion

The HR Employee Roster Export + Print feature is one of the **lowest-risk, highest-reuse** asks possible on the MASCI platform:

- The data exists, in one place, under HR's existing read gate.
- The Excel exporter helper is already written and used by 4 other endpoints.
- The print pattern is already proven in `HrTimeVerification.jsx`.
- The schema does not contain SSN/DOB/salary/address/emergency-contact fields, so the "blind export" risk surface is naturally bounded.
- Three free-text/sensitive judgment fields (`rehire_eligibility_reason`, `status_history.reason`, `cdl_license_number`) are flagged for default exclusion.

**Recommended implementation:** §9 above. One new backend endpoint, one new frontend button + scoped print stylesheet. No new collections. No new libraries. No new auth flows. No PDF engine. Roughly 110 lines of code in 2 existing files.

🛑 **No code has been written.** Awaiting operator approval to proceed.
