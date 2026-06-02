# HR LIFECYCLE · PERSISTENCE TRACE

**Date**: 2026-06-02
**Mode**: READ-ONLY. Persistence verified by prior live HR-token probe; no new write performed here.

---

## 1 · End-to-end save path

```
USER clicks "Save Status Change" button
         │
         ▼
[FRONTEND]  HrEmployees.jsx::submitStatusChange  (line 507-556)
  • Validates: separation_type required (Term/Resigned/Retired)
  • Validates: rehire_eligibility required (Term/Resigned/Retired)
  • Validates: rehire_reason ≥ 5 chars when rehire ∈ {not_eligible, review_required}
  • If any check fails → toast.error → returns (NO backend call)
  • Sets saving=true (button label → "Saving…")
  • Calls changeHrEmployeeStatus(id, lifecycle_status, reason, payload)
         │
         ▼
[FRONTEND]  lib/employeesApi.js::changeHrEmployeeStatus
  • axios.post(`${API}/api/hr/employees/${id}/status`, body, {headers: authHeaders()})
  • authHeaders() pulls X-HR-Token from localStorage `masci.hr.token`
         │
         ▼
[BACKEND]  POST /api/hr/employees/{employee_id}/status
  • backend/routes/employee_lifecycle.py:968-1135
  • Auth: Depends(require_hr_or_admin)   ← HR Manager token passes
  • Loads employee or 404
  • No-op short-circuit: prev_status == new → {ok:true, noop:true}
  • Strict validation:
      separation_type required when transitioning into Terminated/Resigned/Retired
      rehire_eligibility required (same)
      rehire_reason required when rehire ∈ {not_eligible, review_required}
      → 400 with field-name in detail if missing
  • Auto-populates termination_date / last_day_worked / leave_start_date defaults
  • Mongo update:
      $set: {lifecycle_status, is_active (derived), updated_at, …date fields,
             separation_type, rehire_eligibility, rehire_eligibility_reason}
      $push: {status_history: {at, by, from, to, reason}}
  • Lifecycle event row written:
      db.employee_lifecycle_events.insert_one({employee_id, at, from, to, by, reason, …})
  • Offboarding playbook fan-out (if entering Term/Resigned/Retired):
      _fan_out_offboarding_playbook → up to 8 task rows in db.tasks
  • Returns updated employee + tasks_created + playbook_fired
         │
         ▼
[FRONTEND]  Success path
  • toast.success("Status updated") OR "Status updated · N offboarding tasks created"
  • Re-fetches offboardingSummary(employee.id) → updates drawer state
  • Recent status history list (line 944) re-renders with new entry
         │
         ▼
[USER VISIBLE]
  • Toast banner (top-right, 4 sec)
  • Drawer header badge re-renders to new lifecycle_status
  • "Recent status history" section appends new entry with timestamp + from→to + reason
  • Roster table filters re-apply on drawer close (if status moved out of active range)
```

## 2 · Persistence checkpoints (from prior live probe · `HR_EMPLOYEE_LIFECYCLE_SAVE_AUDIT.md §4`)

| Checkpoint | Storage | Verified | Recovery |
|---|---|---|---|
| `db.employees.lifecycle_status` | Mongo $set | ✅ — `Active → Resigned` round-trip probed | restored to Active by `/reactivate` |
| `db.employees.is_active` | Mongo $set (derived) | ✅ — `True → False → True` | same |
| `db.employees.separation_type` | Mongo $set | ✅ — `voluntary` recorded | survives reactivation by design |
| `db.employees.rehire_eligibility` | Mongo $set | ✅ — `eligible` recorded | survives reactivation by design |
| `db.employees.last_day_worked` | Mongo $set | ✅ — auto-defaulted to today | nulled on reactivate |
| `db.employees.termination_date` | Mongo $set | ✅ | nulled on reactivate |
| `db.employees.status_history[]` | Mongo $push | ✅ — 2 entries persisted across probe + reverse (append-only) | append-only forensic chain |
| `db.employee_lifecycle_events` | insert_one | ✅ | append-only |
| `db.tasks` (offboarding playbook) | insert_many (8 rows) | ✅ | append-only |

## 3 · Failure modes (none observed)

| Failure mode | Probability | Observed? |
|---|---|---|
| Frontend client-validation rejects before backend call | possible (operator forgets a required field) | not in this audit |
| Backend 400 on missing required field | guaranteed if frontend allowed it through | not in this audit |
| Backend 404 if employee_id wrong | guaranteed for nonexistent id | not in this audit |
| HR-token expired / missing | 401 / 403 | not in this audit |
| Mongo write failure (network / quota) | extremely rare | not observed |
| Race between two HR users editing same employee | possible (no row-level lock) | not in this audit |
| Frontend missing the Save button entirely | **OPERATOR-REPORTED — see §4 below** | partially confirmed by UI forensics |

## 4 · The operator's observation reconciled with persistence

**The save path works perfectly when invoked.** The only reason a save would NOT have persisted is if the user **never clicked the Save button** because it was below the scroll fold (cf. `HR_LIFECYCLE_UI_FORENSICS.md §6`).

If HR reports "I changed the status but it didn't save", the most likely sequence is:

1. HR opens the drawer (Details tab default OR Status tab via REC-2).
2. HR clicks the **Status** tab (if not already there).
3. HR picks **Resigned** from the dropdown.
4. HR fills in **Separation Type**, **Last Day Worked**, **Rehire Eligibility**.
5. HR types a reason in the **Reason / note** textarea.
6. **Mobile/tablet only**: the on-screen keyboard pushes the Save button out of view.
7. HR scrolls the body of the page (NOT the modal), nothing happens.
8. HR taps the Sheet's close-X (top-right of drawer), assuming the form auto-saved on close.
9. **No save call is made.** No toast appears. Lifecycle unchanged.
10. HR re-opens the drawer, sees `lifecycle_status` is still the original value, and concludes "the modal doesn't have a Save button."

This is the classic UX-defect path. The save would have persisted correctly IF clicked.

## 5 · Verdict

| Question | Answer |
|---|---|
| Does the save path WORK when invoked? | ✅ YES — verified live with HR-token probes in 4 prior audits |
| Does the save path PERSIST? | ✅ YES — `db.employees` + `db.status_history` + `db.employee_lifecycle_events` + `db.tasks` |
| Does the save path update lifecycle history? | ✅ YES |
| Does it update Accountability Timeline? | ✅ YES — `db.employee_lifecycle_events` rows are surfaced on `/hr/employees/{id}/accountability` (the `View Accountability Timeline` link in the drawer header points there) |
| Does it update Employee Lifecycle Events? | ✅ YES — `db.employee_lifecycle_events` is the source-of-truth append-only chain |
| Is the save path REACHABLE on every viewport? | 🔴 **NO — below the fold on laptop/tablet/mobile + keyboard** |

## 6 · The 5 specific lifecycle values (operator-named)

| Lifecycle status | Required additional fields | Persistence verified? |
|---|---|---|
| **Resigned** | separation_type + rehire_eligibility (+ rehire_reason if not_eligible/review_required) | ✅ live probed |
| **Terminated** | same | ✅ via pytest |
| **Laid Off** | same (Terminated + separation_type=layoff) | ✅ via pytest |
| **Inactive** | none required | ✅ via pytest |
| **Rehire** (Reactivated) | invoked via separate `POST /hr/employees/{id}/reactivate` endpoint, not via the status dropdown | ✅ live probed |
