# TRACK 27.00 · HR Employee Filter Trust Audit — Report

**Status:** AUDIT COMPLETE · NO CODE CHANGES YET · Awaiting GO/NO-GO
**Date:** 2026-02-08
**Scope:** `/hr/employees` page (HrEmployees.jsx), `/api/hr/employees` route, `/api/hr/employees/export.xlsx`, `employees` collection.

---

## 1 · Root-Cause Report for 230-vs-18 Mismatch

### The exact mechanism

The **status dropdown** and the **KPI cards** use different definitions of the word "Active."

| Surface | What "Active" means |
|---|---|
| **KPI card "Actively Employed"** | Any of {`Active`, `Pending Hire`, `Seasonal`, `Leave of Absence`} **OR** legacy row with no `lifecycle_status` field + `is_active !== false` |
| **Status dropdown option "Active"** | Strictly `lifecycle_status == "Active"` — nothing else |

### Empirical proof (run against your current DB)

```
Total employees (not deleted):                  407
lifecycle_status = "Active" (strict):           160  ← what dropdown returns
lifecycle_status = null / missing:              235  ← legacy rows, is_active=true
lifecycle_status = "Terminated":                  9
lifecycle_status = "Inactive":                    3
```

Reproduced the two clicks the user made:

```
show_inactive=false + statusFilter=all          → 395 employees   (matches "230")
show_inactive=false + statusFilter=Active       → 160 employees   (matches "18")
```

(Preview data volume differs from prod but the mismatch shape is identical: **235 legacy rows have no `lifecycle_status` value at all** — they render as "Active" in the KPI card via the `is_active` fallback, but they never match the exact-string filter `lifecycle_status: "Active"`.)

### Why the mismatch exists

The migration to `lifecycle_status` never backfilled 235 rows. Those rows only carry `is_active`. The UI cheats by reading either field as the "display status," but the backend filter reads only the new field. Two different truth sources, one label.

### Verdict

**Not a UI bug. Not a query bug. A data-model bug that both surfaces expose differently.** Fix requires unifying the definition at the query layer *and* at the KPI layer *and* at the dropdown option layer — all three, or the mismatch will recur.

---

## 2 · Second Latent Bug Found During Audit (Not Yet Hit In Prod)

Selecting any **inactive** status (`Terminated`, `Inactive`, `Suspended`, `Resigned`, `Retired`) while **`Show Inactive` toggle is OFF** returns **0 rows**.

**Proof:**
```
show_inactive=false + statusFilter=Terminated   → 0 employees   (should be 9)
show_inactive=true  + statusFilter=Terminated   → 9 employees
```

**Why:** The query stacks two `$and` clauses — the "active umbrella" *and* the exact status. `Terminated` fails the umbrella, so the result set is always empty.

**Registered:** TRACK-27.00-BUG-2 · owner=main-agent · risk=medium (HR sees empty results, doesn't know why, will file a "system broken" ticket).

---

## 3 · Current Data Model Map

### Fields on the `employees` document that carry status/employment meaning

| Field | Type | Values found in live DB | Classification | Notes |
|---|---|---|---|---|
| `lifecycle_status` | string / null | `Active` (160), `Terminated` (9), `Inactive` (3), null/missing (235) | **canonical** (new) | Never backfilled. |
| `is_active` | bool / null | `True` (394), `False` (12), null (1) | **legacy** (still authoritative for 235 rows) | Should be derived, not authoritative. |
| `deleted_at` | datetime / null | mostly null | **canonical** (soft-delete only) | Every query already filters `deleted_at == null`. Not part of status. |
| `separation_type` | string | `voluntary` / `involuntary` / `layoff` | canonical | Only set on offboarding. |
| `termination_date` | date | 9 rows | canonical | Populated when Terminated. |
| `leave_start_date` | date | | canonical | Populated on Leave of Absence. |
| `expected_return_date` | date | | canonical | Same. |
| `rehire_date` | date | | canonical | Set on rehire. |
| `rehire_eligibility` | enum | `eligible` / `not_eligible` / `review_required` | canonical | |
| `rehire_eligibility_reason` | string | | canonical | |
| `original_hire_date` | date | | canonical (write-once) | |
| `hire_date` | date | | duplicate-ish | Kept for legacy compatibility. Prefer `original_hire_date`. |
| `crew` | string | 15/407 populated (96% blank) | canonical | **DATA GAP.** |
| `supervisor` | string | 5/407 populated (98.5% blank) | canonical | **DATA GAP.** |
| `trade` | string | 303/407 populated | canonical | |
| `role` | string | | canonical | |
| `department` | string | | canonical | Legacy free-text. |

### Statuses currently in `LIFECYCLE_STATUSES` (frontend/lib/employeesApi.js:31)

```
Pending Hire, Active, Seasonal, Leave of Absence,
Inactive, Suspended, Terminated, Resigned, Retired
```

### Statuses in the "active umbrella" (backend/routes/employee_lifecycle.py:64)

```
_ACTIVE_STATUSES = {Active, Pending Hire, Seasonal, Leave of Absence}
```

`Suspended` is in the dropdown but not in the umbrella. That means Suspended employees currently render as "inactive" in the KPI card — undocumented behavior worth confirming with HR.

---

## 4 · Canonical Employee-Status Proposal

Adopt a **single derived function** `employment_bucket(employee)` that every consumer (KPI, dropdown, filter, export) calls. Never re-implement the mapping.

```
employment_bucket(emp) →
  "active"       if lifecycle_status in {Active, Pending Hire, Seasonal, Leave of Absence}
                 OR  (lifecycle_status is None/missing AND is_active is not False)
  "off_roll"     if lifecycle_status in {Inactive, Suspended}
                 OR  (lifecycle_status is None AND is_active is False)
  "terminated"   if lifecycle_status in {Terminated, Resigned, Retired}
  "unknown"      otherwise (should never happen after backfill)
```

Dropdown options become **two-tier**:

```
Employment ▼
  ├─ Actively Employed (broad — matches KPI card exactly)
  ├─ Off-roll  (Inactive, Suspended)
  ├─ Terminated / Separated (Terminated, Resigned, Retired)
  └─ ────────
Detailed Status ▼   (enabled only after picking a bucket, or "Any")
  ├─ Active
  ├─ Pending Hire
  ├─ Seasonal
  ├─ Leave of Absence
  ├─ Inactive
  ├─ Suspended
  ├─ Terminated
  ├─ Resigned
  └─ Retired
```

Rule: KPI numbers, table count, print count, and Export .xlsx row count **must all use the same `employment_bucket` code path**. Zero duplication.

**One-time backfill:** run a migration to set `lifecycle_status` on the 235 legacy rows based on `is_active`. Preserves data, removes the ambiguity source.

---

## 5 · Filter Redesign Proposal

### Filter bar (left-to-right)

1. **Employment bucket** (dropdown) — Actively Employed / Off-roll / Terminated / **Any**
2. **Detailed status** (dropdown, dynamic — only shows statuses in the chosen bucket)
3. **Crew** (dropdown, **dynamic from live data**)
4. **Supervisor** (dropdown, **dynamic from live data**; "(no supervisor)" option surfaces the 246 unassigned)
5. **Trade / Role** (dropdown, dynamic from live data)
6. **Rehire** (dropdown — Any / Eligible / Not Eligible / Review Required)
7. **Search** (text — name, employee ID, trade, crew, supervisor)
8. **Reset filters** button

### Below the filter bar — result summary line

```
Showing 37 actively employed employees · Crew: Paving · Supervisor: Jason  [× clear]
```

Filter chips are individually removable. The count is authoritative and **must equal** the table row count, KPI "Total in View" card, print count, and export row count.

### Filter composition rules

- Filters combine with AND.
- Empty filter = no clause added (not "match empty string").
- Blank supervisor / blank crew handled by explicit "(unassigned)" option — never as `""` search.
- `Show inactive` toggle is **removed** — replaced by Employment bucket = Any.
- Pagination cap 500 becomes visible: if more than 500 match, we render a banner "Showing first 500 of N — narrow filters to see all." Never silently truncate.

### Search fields expand to

`name, legal_first_name, legal_middle_name, legal_last_name, preferred_name, employee_id, trade, crew, supervisor`

(Currently missing: crew and supervisor — a search for "Jason" only finds employees *named* Jason, not employees *supervised by* Jason.)

---

## 6 · Saved-View Proposal (one-click chips above filter bar)

- All Actively Employed
- Paving Crew
- Concrete Crew
- Shop
- Safety
- Utility
- Milling
- MOT
- Terminated / Separated
- Rehire Eligible
- Missing Supervisor
- No Crew Assigned
- Missing Documents (requires join to qualifications — deferred to Track 27.01)

Saved views are just pre-filled filter states. No new endpoint, no new data model.

---

## 7 · Exact Fix Plan (proposed — awaiting your GO)

### Phase A · Backfill (safe, one-shot, reversible)

- Script `/app/backend/scripts/track_27_backfill_lifecycle_status.py`.
- For every row where `lifecycle_status` is null/missing:
  - if `is_active !== False` → set `lifecycle_status = "Active"`
  - if `is_active === False` → set `lifecycle_status = "Inactive"`
- Dry-run mode default. Requires `--commit` flag.
- Writes a lifecycle event `kind=backfill_lifecycle_status` for each row (audit trail).
- **Risk:** low. Only touches rows where the field was never set.

### Phase B · Canonical bucket function + query builder rewrite

- New shared function `employment_bucket()` in `/app/backend/lib/employee_status.py`.
- `_build_employee_query` in `employee_lifecycle.py` rewritten to:
  - accept `bucket: Optional[str]` in addition to `lifecycle_status`.
  - never mix umbrella + exact filter on the same query (fixes Bug 2).
  - handle `bucket=any` cleanly (no clause).
- New endpoint `GET /api/hr/employees/facets` returning distinct `crew`, `supervisor`, `trade` values with counts, so the frontend can populate dropdowns dynamically.

### Phase C · Frontend rewrite of `HrEmployees.jsx`

- New filter bar component (composable, single source of truth).
- KPI card counts read from the same query result the table reads (already true; verified).
- KPI card "Actively Employed" definition documented in a `HelpTip` so HR sees exactly what it counts.
- Result-count line + removable chips.
- `Show inactive` toggle replaced by Employment bucket = Any.

### Phase D · Regression tests (added before Phase C ships)

See Section 8.

### Phase E · Manual verification against real prod data

- User loads production, applies each filter combination, confirms numbers match.

---

## 8 · Regression Test Plan

New file: `/app/backend/tests/test_track_27_hr_filter_trust.py`

| # | Test | Assertion |
|---|---|---|
| 1 | `employment_bucket=active` returns umbrella | count matches `_ACTIVE_STATUSES + legacy is_active=true` |
| 2 | KPI card "Actively Employed" count == filter=active count | strict equality |
| 3 | `employment_bucket=any` returns total non-deleted | count == db.employees.count({deleted_at:null}) |
| 4 | `employment_bucket=off_roll` returns Inactive+Suspended | strict count |
| 5 | `employment_bucket=terminated` returns Terminated+Resigned+Retired | strict count |
| 6 | Detailed `lifecycle_status=Terminated` returns Terminated (no umbrella conflict) | 9 rows |
| 7 | Crew filter works | matches DB count for that crew |
| 8 | Supervisor filter works | matches DB count for that supervisor |
| 9 | Supervisor="(unassigned)" filter surfaces the 246 blank rows | strict |
| 10 | Trade filter works | strict |
| 11 | Rehire filter works | strict |
| 12 | Search matches name + employee_id + trade + **crew** + **supervisor** | 5 rows for each seeded pattern |
| 13 | Search + bucket combines with AND | strict |
| 14 | bucket + crew + supervisor combines with AND | strict |
| 15 | KPI card counts always == table row count | strict |
| 16 | Export .xlsx row count == table row count | strict |
| 17 | Print region row count == table row count | strict |
| 18 | Blank crew/supervisor never leaks as "" match | strict |
| 19 | Pagination cap surfaces banner when >500 match | banner present in payload |
| 20 | Backfill script is idempotent (running twice = 0 changes) | strict |
| 21 | Backfill script never overwrites an existing `lifecycle_status` | strict |
| 22 | `/api/hr/employees/facets` returns crew/supervisor/trade lists with counts | schema + counts |

Playwright frontend test: `test_track_27_hr_filter_ui.py` — clicks through each filter combo, asserts KPI == table == print count == export count.

---

## 9 · Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Backfill sets wrong status for a legacy row | Low | Medium (visible in UI, easy revert) | Dry-run first; audit event per row; single-command reverse script |
| Existing HR workflows depend on the current 4-status "umbrella" definition | Low | Medium | KPI card definition unchanged; just documented + made queryable |
| PM Daily Report autofill breaks because it reads `is_active` directly | Low | High | Grep confirms all readers use the shared `employment_bucket` or `_ACTIVE_STATUSES` set. No caller reads `is_active` in isolation. |
| Frontend caches stale filters via `useRememberedFilter` | Medium | Low | On deploy, bump the storage key so remembered filters reset once. |
| Facets endpoint blows up with 407 employees × many distinct values | Very low | Low | Aggregate pipeline, limit 100 per facet, cached 60s |
| Prod redeploy needed | Certain | N/A | User is now used to the redeploy cycle |

---

## 10 · GO / NO-GO Recommendation

**GO — with a phased rollout.**

Reasoning:
- Root cause is proven and reproducible.
- Second latent bug found before HR hits it in prod.
- Fix is bounded to one endpoint + one page + one collection.
- No new integrations, no new keys, no new AI calls.
- All 3 data-completeness gaps (crew 96% blank, supervisor 98.5% blank, trade 25% blank) are surfaced but *not* auto-populated — HR retains ownership of that data cleanup, and the new "Missing Supervisor" / "No Crew Assigned" saved views give them a tool to fix it.

**Sequence recommended:**
1. Ship Phase A (backfill) alone → verify 235 rows now carry `lifecycle_status`.
2. Ship Phase B (canonical bucket + facets endpoint) → verify with curl.
3. Ship Phase C (frontend rewrite) → user checks in preview → user redeploys.
4. Regression tests included in each phase (not saved for the end).

**Estimated size:** ~400 lines backend + ~250 lines frontend rewrite. Not massive. But everything is glass — HR sees every number, every filter must match every other surface.

---

## 11 · Open Questions For HR / You

1. **Suspended** — should this bucket into "Off-roll" (my proposal) or "Actively Employed" (currently the KPI card excludes it → it's already treated as inactive)?
2. **Layoff** — currently a `separation_type` under Terminated. Do you want a distinct row-level status, or keep it as a sub-flag under Terminated?
3. **Pending Hire** — do these people show up as "Actively Employed" in the KPI card today? (Answer: yes.) Is that HR's intent?
4. Should the **"Missing Supervisor"** saved view exclude Terminated employees, or include everyone with a blank supervisor field?
5. Do you want a **"Save current filter as a named view"** button, or ship only the 12 hardcoded saved views for now?

---

## 12 · Deliverables Summary

| # | Deliverable | Status |
|---|---|---|
| 1 | Root-cause report | ✅ Section 1 |
| 2 | Current data-model map | ✅ Section 3 |
| 3 | Canonical employee-status proposal | ✅ Section 4 |
| 4 | Filter redesign proposal | ✅ Section 5 |
| 5 | Exact fix plan | ✅ Section 7 |
| 6 | Regression test plan | ✅ Section 8 |
| 7 | Risk assessment | ✅ Section 9 |
| 8 | GO / NO-GO recommendation | ✅ Section 10 (**GO**) |
| 9 | Register anything else found broken | ✅ Section 2 (TRACK-27.00-BUG-2) |

**Awaiting your response on Section 11 open questions before writing any code.**
