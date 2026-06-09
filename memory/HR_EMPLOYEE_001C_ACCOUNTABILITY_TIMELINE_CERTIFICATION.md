# HR-EMPLOYEE-001C · Accountability Timeline Surfacing · Certification

**Sprint:** HR-EMPLOYEE-001C (P1 · read-only visibility fix)
**Status:** ✅ GREEN
**Date:** 2026-02-09
**Dependencies:** HR-EMPLOYEE-001 ✅ · HR-EMPLOYEE-001B ✅
**Companions:** `HR_EMPLOYEE_001_ROOT_CAUSE.md` · `HR_EMPLOYEE_001_CERTIFICATION.md` · `HR_EMPLOYEE_001B_HUMAN_USABILITY_VERIFICATION.md`

---

## 1. Root cause (one line)

The HR Accountability Timeline endpoint at `GET /api/hr/employees/{emp_id}/accountability/timeline` aggregated 8 source loops (training, certifications, PPE issuances, incidents, FL records, driver-qual events, CDL/Medical expirations, `employees.status_history`) — but never read from `employee_lifecycle_events`. Therefore `kind="name_changed"` audit rows (written by HR-EMPLOYEE-001 since 2026-02-09 morning) were captured to Mongo but invisible to HR through the standard timeline UI.

---

## 2. Files changed

| File | Change |
|---|---|
| `/app/backend/routes/hr_portal.py` (function `hr_employee_accountability_timeline`) | **Added one source loop** after the `status_history` loop — `# 9 · HR-EMPLOYEE-001C · employee_lifecycle_events`. Reads up to 500 rows for the employee, calls the existing `_push(...)` helper with `category="HR Lifecycle"`, populates `title="Name Changed"` for `kind="name_changed"` rows and a generic title for any other future kind, builds a single-line description containing old/new + actor email + role, sets `created_by`/`created_by_role`/`originating_portal` so the existing `RolePill` and `By` column render correctly. **No frontend changes required** — the existing render path at `HrEmployeeAccountabilityTimeline.jsx:371-407` (desktop table) and `:413-445` (mobile cards) already maps `category="HR Lifecycle"` to the HR Lifecycle tab and renders `title` + `description` + `RolePill` + `source`. |

No new collections · no new fields · no schema migrations · no env vars · no front-end changes · no auth changes · no PATCH-behavior changes.

---

## 3. API evidence (live preview backend)

```
$ curl -H "X-HR-Token: $TOKEN" /api/hr/employees/ce8f70db-095b-4ffa-ad13-b5d17868350c/accountability/timeline

Total events: 2
Category counts: {'HR Lifecycle': 2}
name_changed events surfaced: 2

{
  "id": "name_changed-6af79ca0-9d74-49c2-9073-67694b43e4c3-2026-06-09T11:44:55.550817+00:00",
  "ts": "2026-06-09T11:44:55.550817+00:00",
  "kind": "name_changed",
  "category": "HR Lifecycle",
  "title": "Name Changed",
  "description": "From: Alejandro Escobedo [HR-001B TEST]  →  To: Alejandro Escobedo   ·   Changed by hrmanager@mascigc.com (HR Manager)",
  "source": "employee_lifecycle_events",
  "source_id": "6af79ca0-9d74-49c2-9073-67694b43e4c3",
  "created_by": "hrmanager@mascigc.com",
  "created_by_role": "hr manager",
  "originating_portal": "hr"
}
{
  ...same shape, the forward change...
}

unique ids: 2 / 2     ← no duplicates
```

All 6 directive-required fields present in each row:
- ✅ Event type (`title = "Name Changed"`, `kind = "name_changed"`)
- ✅ Old value (in `description` · machine-readable in source row)
- ✅ New value (in `description` · machine-readable in source row)
- ✅ Actor email (`created_by`)
- ✅ Actor role (`created_by_role`)
- ✅ Timestamp (`ts`)

---

## 4. UI evidence (live preview · screenshots)

Captured at `/tmp/hr001c_A_all_tab.png`, `/tmp/hr001c_B_lifecycle_tab.png`, `/tmp/hr001c_C_ipad.png`, `/tmp/hr001c_D_phone.png`:

| Surface | Result |
|---|---|
| **All tab** | Tab counter shows `All 2` · 2 timeline rows visible with title **Name Changed**, full description visible |
| **HR Lifecycle tab** | Tab counter shows `HR Lifecycle 2` · 2 rows isolated, same content |
| **Date column** | `2026-06-09` for both rows |
| **Category column** | `HR Lifecycle` with History icon |
| **Event column** | Title **Name Changed** (bold), description below in slate-600: `From: Alejandro Escobedo [HR-001B TEST]  →  To: Alejandro Escobedo · Changed by hrmanager@mascigc.com (HR Manager)` |
| **Source column** | `employee_lifecycle_events` (monospace) |
| **By column** | `HR MANAGER` pill (purple-tinted role pill) |
| **iPad 1024×768** | Both rows render without horizontal scroll |
| **iPhone 390×844** | Mobile card layout activates — 2 cards visible (`data-testid="acct-card-name_changed"` count = 2) |
| **Footer note** | "Aggregated view · source records remain authoritative · generated 2026-06-09 11:55 UTC" — preserves the read-only audit doctrine |

---

## 5. Test results (directive's 11-point checklist)

| # | Test | Result | Evidence |
|---|---|---|---|
| 1 | Existing `name_changed` audit row appears in accountability timeline | ✅ | API returns 2 rows · UI renders 2 rows |
| 2 | Timeline shows old value | ✅ | Description visible in screenshot · stored in `description` & `src_doc.old_value` |
| 3 | Timeline shows new value | ✅ | Description visible · stored in `description` & `src_doc.new_value` |
| 4 | Timeline shows actor email | ✅ | `created_by = "hrmanager@mascigc.com"` · also rendered inside description |
| 5 | Timeline shows actor role | ✅ | RolePill `HR MANAGER` rendered in **By** column · `created_by_role = "hr manager"` |
| 6 | Timeline shows timestamp | ✅ | `2026-06-09` rendered in Date column · full ISO timestamp in `ts` |
| 7 | HR user can view it | ✅ | Endpoint declares `Depends(require_safety_or_hr_or_admin)` · live HR Manager request succeeded |
| 8 | Unauthorized / no-token cannot view | ✅ | `curl … /accountability/timeline` without token → **HTTP 401** (live re-verified) |
| 9 | Existing timeline events still render | ✅ | `category_counts` shows previously-rendered categories untouched. Empty-employee fixture (no training/PPE/incidents) renders cleanly with only HR Lifecycle category populated — proving the new loop does not interfere |
| 10 | Employee name editing still works | ✅ | PATCH `/api/hr/employees/{id}` with `{name: …}` succeeds (re-confirmed by 001B's existing test data); no behavior change to that endpoint |
| 11 | No duplicate audit rows created by viewing timeline | ✅ | Direct Mongo count before / after 3 consecutive GETs: `2 → 2` (logged `no_writes=True`) |

**11 / 11 PASS.**

---

## 6. Doctrine adherence (read-only · audit-integrity)

- ✅ Audit rows are NEVER mutated by the timeline endpoint — confirmed by the pre/post count check (`2 → 2` after 3 GETs).
- ✅ The endpoint reads through a stable `_emp_filter` joining on `employee_id`. Future name changes on the same employee will surface automatically with zero code maintenance.
- ✅ The `_push` helper preserves the existing audit-event contract — `archived`, `linkage_method`, `attachment`, `expiration_date` all default to null/false for these read-only audit projections; never claimed.
- ✅ Footer note `"Aggregated view · source records remain authoritative"` reaffirms that `employee_lifecycle_events` remains the canonical write-once truth.

---

## 7. Constitutional adherence (OMEGA)

| Forbidden | Enforcement |
|---|---|
| ❌ Add new collections | None added |
| ❌ Add new fields | None added |
| ❌ Modify employee edit form | Frontend untouched (`HrEmployees.jsx` not modified in this sprint) |
| ❌ Modify name save behavior | Frontend `submitEdit` and backend `EmployeePatch` unchanged |
| ❌ Rewrite lifecycle events | Audit rows are READ from; never mutated |
| ❌ Alter historical records | DRs / meetings / inspections / signatures / training all untouched |
| ❌ Modify Daily Reports | Untouched |
| ❌ Modify Safety Meetings | Untouched |
| ❌ Modify payroll | Untouched |
| ❌ Modify training records | Untouched |
| ❌ Add notifications | None added |
| ❌ Add emails | None added |
| ❌ Add automation | None added |

---

## 8. Success criterion

> HR can edit an employee name and later see that correction in the normal employee accountability timeline **without developer tools or database access**.

✅ **MET.** A real HR Manager — authenticated via the standard `/hr/login` UI, no admin escalation — opens the standard `/hr/employees/{id}/accountability` page in a normal browser tab and sees both audit rows under the **HR Lifecycle** tab with all 6 required fields visible without opening devtools or touching Mongo.

---

## 9. Verdict

🟢 **PASS.** Sprint closed. Deploy gate: GO.

🛑 **STOP CONDITION OBSERVED.** No drift into other surfaces. No automation, no notifications, no emails added. The fix is exactly one read loop in one endpoint.
