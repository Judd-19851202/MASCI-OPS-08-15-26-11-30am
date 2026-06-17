# TRACK 15.9A — HR DAILY REPORT OPERATIONAL AUDIT

**Date:** 2026-06-17
**Source of truth:** post-iter332 + Track 15.9 + Track 15.9A code

This audit is the prerequisite for the Track 15.9A certification. It captures the state of the HR Daily Reports surface immediately AFTER the Track 15.9A hardening was applied.

---

## 1. Routes

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `GET` | `/api/hr/daily-reports` | `require_hr_user` (X-HR-Token only) | List Daily Reports company-wide with 10 filters + PM-of-record + Superintendent enrichment. |
| `GET` | `/api/hr/daily-reports/{id}` | `require_hr_user` | Read-only detail with `distribution_list` excluded + PM-of-record enrichment. |
| `GET` | `/api/hr/employee-accountability?employee=<name>` | `require_hr_user` | Workforce intelligence — unions field_leadership_records + safety_training_records + training_track_records + safety_forms + outstanding equipment lines for one employee. |

**No POST, PUT, PATCH, or DELETE under `/api/hr/daily-reports`.** Asserted by `test_no_hr_write_endpoints_on_daily_reports` and `test_no_pm_workflow_endpoints_under_hr_namespace`.

## 2. Permissions

- **Resolver:** `make_require_hr_user(db)` in `routes/hr_portal_deps.py`.
- **Header inspected:** only `X-HR-Token`. Never `X-Admin-Token`, `X-PM-Token`, `X-Safety-Token`, `X-Dispatch-Token`, `X-Field-Leadership-Token`, or `Authorization`.
- **Fall-through:** none. If `X-HR-Token` is missing or invalid → HTTP 401.
- **Asserted by:** `test_require_hr_user_rejects_all_other_tokens` (Track 15.9), 13 `iter373_hr_user_parity` tests.

## 3. API behavior

### `GET /api/hr/daily-reports` (list)
Query parameters:
| # | Param | Type | Effect |
|---|---|---|---|
| 1 | `date_from` | ISO date | `$gte` on `report_date` |
| 2 | `date_to` | ISO date | `$lte` on `report_date` |
| 3 | `project` | regex needle | `$or` on `project_name` + `project_number` |
| 4 | `pm` (NEW) | regex needle | Pre-resolves matching `project_number`s via `projects.{pm_name, pm_email}` then narrows DR match |
| 5 | `superintendent` (NEW) | regex needle | regex on `superintendent` (DR doc top-level) |
| 6 | `foreman` (NEW) | regex needle | regex on `masci_crews.foreman` (nested) |
| 7 | `employee` | regex needle | regex on `masci_crews.members.name` (nested) |
| 8 | `subcontractor` | regex needle | regex on `subcontractors.name` (nested) |
| 9 | `vendor` | regex needle | regex on `visitors.name` (nested) |
| 10 | `report_number` | regex needle | regex on `report_number` |
| — | `limit` | int | default 200, capped at 500 |

Response shape (per item):
```json
{
  "id": "uuid",
  "report_number": "DR-2026-00001",
  "report_date": "2026-06-17",
  "project_name": "Project Alpha",
  "project_number": "26-07",
  "pm_name": "Jane Doe",          // NEW (Track 15.9A)
  "pm_email": "jane@masci.com",   // NEW (Track 15.9A)
  "superintendent": "Bob Smith",  // NEW (Track 15.9A)
  "prepared_by": "Carl Foreman",
  "location": "1234 Main St",
  "weather_summary": "Clear, 72°F",
  "created_at": "ISO-8601",
  "photo_count": 12,
  "crew_count": 3,
  "sub_count": 1,
  "visitor_count": 2
}
```

### `GET /api/hr/daily-reports/{id}` (detail)
Returns the full DR document with:
- **EXCLUDED:** `distribution_list` (Track 15.9 hardening).
- **ENRICHED:** `pm_name` + `pm_email` looked up from `projects` collection (Track 15.9A).

## 4. Collections touched

| Collection | Verb | Purpose |
|---|---|---|
| `daily_reports` | `find_one` + `aggregate` | Single canonical source for DRs. |
| `projects` | `find` + `find_one` | PM-of-record lookup (project_number → pm_name + pm_email). |
| `field_leadership_records`, `safety_training_records`, `training_track_records`, `safety_forms`, `equipment_outstanding` | `find` (read-only) | Workforce intelligence aggregator on the employee-accountability endpoint. |

**No write to any collection from `/hr/daily-reports/*`.** Pure read-only.

## 5. Filter completeness audit

Compared to operator mandate ("HR can filter by: Date · Project Number · Project Name · PM · Superintendent · Foreman · Employee · Vendor · Subcontractor"):

| Operator filter | Implemented | Where |
|---|---|---|
| Date (from/to) | ✅ | `date_from` + `date_to` |
| Project Number | ✅ | `project` (matches both name + number) |
| Project Name | ✅ | `project` (matches both name + number) |
| PM | ✅ NEW (15.9A) | `pm` (pre-resolved via `projects` collection) |
| Superintendent | ✅ NEW (15.9A) | `superintendent` (DR top-level) |
| Foreman | ✅ NEW (15.9A) | `foreman` (nested `masci_crews.foreman`) |
| Employee | ✅ | `employee` (nested `masci_crews.members.name`) |
| Vendor | ✅ | `vendor` (nested `visitors.name`) |
| Subcontractor | ✅ | `subcontractor` (nested `subcontractors.name`) |
| **bonus** | Report number | ✅ | `report_number` (regex) |

**Filter completeness: 10/10 operator-mandated filters + 1 bonus. No PM filter gap. No Superintendent gap. No Foreman gap.**

## 6. Search behavior

All filters use case-insensitive partial regex (`{"$regex": needle, "$options": "i"}`). PM search resolves through the `projects` collection so HR finds reports by:

- Typing the PM's first or last name → matches `projects.pm_name` (case-insensitive partial)
- Typing the PM's email or partial domain → matches `projects.pm_email`

Same is true for all other regex filters (project, super, foreman, employee, sub, vendor, report number).

## 7. List view

- **Page:** `/app/frontend/src/pages/HrDailyReports.jsx`
- **Layout shell:** `PortalShell` + `HrSideNavV2` (same as other HR pages).
- **KPI strip:** 4 cards (Reports, Crews, Subs, Visitors) reflecting current filtered set.
- **Filter grid:** 1-col / 2-col / 4-col responsive (`grid-cols-1 sm:grid-cols-2 lg:grid-cols-4`).
- **Table columns:** Date · Report # · Project · **PM (NEW)** · **Superintendent (NEW)** · Prepared by · Crews · Subs · Visitors · `Open →`.
- **Empty state:** lucide Filter icon + italic copy.
- **Loader:** lucide Loader2 spinning.
- **No edit/approve/delete/PDF/email buttons.**

## 8. Detail view

- **Page:** same file, exported as `HrDailyReportDetail`.
- **Mount:** `/hr/daily-reports/:id`.
- **Header:**
  - Kicker: `Daily Report · Read-only`
  - Title: project name
  - Sub-line: report date · project number · location · prepared-by
  - **NEW (15.9A):** identity strip showing `Project Manager` (name + email) and `Superintendent` (name).
- **Sections (conditional):** Weather · MASCI Crews · Subcontractors · Visitors/Vendors · Narrative · Photos.
- **Read-only banner:** `hr-dr-readonly-notice`.
- **No write controls.**

## 9. KPI calculations

| KPI | Formula | Scope |
|---|---|---|
| `Reports` | `items.length` | **Filtered set** (current search) |
| `Crews` | `Σ items[i].crew_count` | Filtered set |
| `Subs` | `Σ items[i].sub_count` | Filtered set |
| `Visitors` | `Σ items[i].visitor_count` | Filtered set |

**KPI logic is "filtered set" semantics** — reflects the rows currently visible based on filters. The total-records-shown footer (`{items.length} of {totals.count} records shown`) makes that explicit. Operator can clear filters to see company-wide totals.

Note: KPIs do NOT recompute against a separate company-wide aggregate. The page is read-only and filter-driven; KPI consistency with the visible table is the trustworthy semantic.

## 10. Pagination & sorting

- **Sort:** `{"report_date": -1, "created_at": -1}` (newest first, deterministic tie-break).
- **Limit:** default 200, capped at 500.
- **No client-side pagination.** Single fetch per filter change.
- **Total-records-shown indicator** in the footer.

## 11. Mobile rendering

- **Filter grid:** `grid-cols-1` on mobile (one column, full-width inputs), `sm:grid-cols-2` at ≥640px, `lg:grid-cols-4` at ≥1024px.
- **KPI strip:** `grid-cols-1 sm:grid-cols-2` — wraps to 2-up on small screens.
- **Table:** `overflow-x-auto` wrapper to handle horizontal scroll gracefully on narrow viewports (10 columns total).
- **Detail view:** all sections collapse to single column on mobile.

## 12. iPad rendering

- **Portrait (768×1024):** filter grid renders 2 columns (sm breakpoint), KPI strip 2 columns, table scrolls horizontally (10 columns is wide).
- **Landscape (1024×768):** filter grid renders 4 columns (lg breakpoint), KPI strip 2 columns side-by-side, table fits comfortably.
- **No horizontal scroll on the page** (only inside the table wrapper, which is intentional).

## 13. Empty states

| Surface | Empty content |
|---|---|
| List page (no filter matches) | `Filter` icon + italic: "No daily reports match these filters. Try a wider date range or clear all filters to see everything on file." |
| Detail page (id not found) | italic: "Report not found." |
| Detail page (HR session expired) | toast: "Your HR session expired. Please sign in again." |
| Detail page (transient API failure) | toast: "That report is temporarily unavailable. Try again in a moment." |
| List page (transient API failure) | toast: "Daily Reports temporarily unavailable. Try again in a moment." |

iter339 calm-error semantics (`operationalError` sanitizer) used throughout.

## 14. Error states

| Failure mode | Behavior | Test |
|---|---|---|
| Missing/invalid HR token | 401 from API; toast + redirect on FE | `test_hr_dr_routes_gated_by_require_hr_user_only`, `test_require_hr_user_rejects_all_other_tokens` |
| Report not found | 404 from API; "Report not found." rendered on FE | n/a (handled implicitly) |
| Transient DB outage | toast with calm fallback string | `test_iter339_*` (5 tests) |
| Session expired mid-page | toast with localized "session expired" string | iter339 |

---

## 15. Audit completeness verification

| Item | Source |
|---|---|
| Routes enumerated | ✅ `routes/hr_portal.py` lines 340-470 |
| Permissions identified | ✅ `routes/hr_portal_deps.py` lines 42-66 |
| APIs documented | ✅ §3 |
| Queries documented | ✅ §3, §5 |
| Collections documented | ✅ §4 |
| Filters certified | ✅ §5 — 10/10 + 1 |
| Search behavior documented | ✅ §6 |
| Detail view documented | ✅ §8 |
| KPI calculations documented | ✅ §9 |
| Pagination documented | ✅ §10 |
| Sorting documented | ✅ §10 |
| Mobile rendering documented | ✅ §11 |
| iPad rendering documented | ✅ §12 |
| Empty states documented | ✅ §13 |
| Error states documented | ✅ §14 |

**Audit complete. Ready for certification (see `TRACK_15_9A_HR_DAILY_REPORT_OPERATIONAL_CERTIFICATION.md`).**
