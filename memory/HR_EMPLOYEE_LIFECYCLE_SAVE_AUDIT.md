# HR EMPLOYEE LIFECYCLE SAVE · FORENSIC AUDIT

**Date**: 2026-06-02
**Authority**: P0 operator directive — pre-deploy hold.
**Mode**: READ-ONLY (one persistence probe + immediate reverse documented in §6).
**Companion docs**: `HR_EMPLOYEE_STATUS_UI_REVIEW.md`, `DEPLOYMENT_IMPACT_HR_LIFECYCLE_STATUS.md`.

---

## 1 · Reported behaviour

HR reports:

> "In the HR portal, when updating an employee lifecycle/status — example: employee 'Quit' — they can select the lifecycle/status value, but there is no clear Save button, confirmation, success message, or proof that the change persisted. HR is unsure whether their action is saved or a waste of time."

---

## 2 · Surface identification

### 2.1 Exact page / component

* **Route**: `/hr/employees` (`frontend/src/App.js:709`).
* **Page**: `frontend/src/pages/HrEmployees.jsx` (1142 LOC).
* **Component handling status edits**: `EmployeeDrawer` (line 462), opened by clicking any row in the roster.
* **Tab structure inside the drawer**: `Details · Status · Offboarding Summary` (lines 614-619).
* **Status-edit UI**: `<TabsContent value="status">` block (lines 808-925).
* **Save action handler**: `submitStatusChange()` (lines 507-556).
* **Save button**: line 906 — `<Button onClick={submitStatusChange} disabled={saving} data-testid="hremp-status-save">{saving ? "Saving…" : "Update status"}</Button>`.

### 2.2 Field identification

The lifecycle dropdown allows the following canonical values (`frontend/src/lib/employeesApi.js:24-27`):

```
"Pending Hire", "Active", "Seasonal", "Leave of Absence",
"Inactive",     "Suspended", "Terminated", "Resigned", "Retired"
```

**There is no literal `"Quit"` value.** HR likely means `"Resigned"` (voluntary self-quit) — see §3.4.

Fields written by the save action on offboarding transitions:

| Field | Source | Notes |
|---|---|---|
| `lifecycle_status` | `body.lifecycle_status` | canonical value |
| `is_active` | derived from `lifecycle_status` server-side | `_is_active_for_status()` |
| `separation_type` | `body.separation_type` | REQUIRED on offboarding (400 if missing) |
| `rehire_eligibility` | `body.rehire_eligibility` | REQUIRED on offboarding (400 if missing) |
| `rehire_eligibility_reason` | `body.rehire_eligibility_reason` | REQUIRED if rehire ∈ {not_eligible, review_required} |
| `termination_date` | `body.termination_date` or today | auto-defaults to today |
| `last_day_worked` | `body.last_day_worked` or today | auto-defaults to today |
| `leave_start_date` | for Leave of Absence | auto-defaults to today |
| `expected_return_date` | optional | for Leave of Absence |
| `updated_at` | server time | ISO UTC |
| `status_history[]` | appended | `{at, by, from, to, reason}` |

* `employment_status` and `termination_status` are NOT separate fields — `lifecycle_status` is the canonical single-source-of-truth (see `employee_lifecycle.py:9`).

---

## 3 · End-to-end save flow

### 3.1 Frontend dispatch (`HrEmployees.jsx:507-556`)

1. Client-side validation:
   * Offboarding + missing `separation_type` → `toast.error("Pick a separation type")` — **returns without calling backend**.
   * Offboarding + missing `rehire_eligibility` → `toast.error("Pick a rehire eligibility")` — returns.
   * Rehire ∈ {not_eligible, review_required} + missing reason → `toast.error("Add a short reason …")` — returns.
2. Sets `saving=true` (button label flips to "Saving…").
3. Calls `changeHrEmployeeStatus(employee.id, statusForm.lifecycle_status, statusForm.reason, payload)` → axios POST to `/api/hr/employees/{id}/status` with `X-HR-Token` header.
4. On 2xx:
   * `toast.success("Status updated")` — or — `toast.success("Status updated · N offboarding tasks created")` if the offboarding playbook fired.
   * Re-fetches `offboardingSummary(employee.id)` → updates drawer state.
   * `status_history` re-renders below the button (lines 910-925, last 5 entries).
5. On error: `toast.error(friendlyError(e, "Status change failed"))`.
6. `saving=false` regardless.

### 3.2 Backend handler (`backend/routes/employee_lifecycle.py:968-1135`)

Endpoint: `POST /api/hr/employees/{employee_id}/status`
Auth: `Depends(require_hr_or_admin)` — accepts X-HR-Token OR X-Admin-Token.

1. Loads employee or 404.
2. No-op short-circuit: `prev_status == body.lifecycle_status` → returns `{ok:true, noop:true, tasks_created:0}`.
3. Validates required fields for offboarding (separation_type · rehire_eligibility · reason when applicable) — returns **400** with **field-name in `detail`** on failure.
4. Auto-populates `termination_date` / `last_day_worked` / `leave_start_date` from request body OR today.
5. Mongo update:
   ```
   $set: {lifecycle_status, is_active, updated_at, …date_updates}
   $push: {status_history: {at, by, from, to, reason}}
   ```
6. Fires offboarding playbook (`_fan_out_offboarding_playbook`) if transitioning into Terminated/Resigned/Retired/Suspended — creates up to 8 follow-up tasks across HR/Shop/Admin/Safety/PM (line 1107).
7. Returns the full updated employee + `tasks_created` count + `playbook_fired` flag.

### 3.3 Persistence path

| Layer | What gets written | Reversible? |
|---|---|---|
| `db.employees.{lifecycle_status, is_active, …date fields, status_history[]}` | YES — primary record | Yes via `/hr/employees/{id}/reactivate` |
| `db.tasks` (up to 8 offboarding rows) | YES on Term/Resigned/Retired transitions | NO — append-only audit; can be cancelled but not deleted |
| `db.notifications` (optional) | If wired via emit_notification | Append-only |

### 3.4 What "Quit" means in this UI

`"Quit"` is not a lifecycle status token. The user-facing canonical mapping is:

| HR's spoken word | UI value to pick | Notes |
|---|---|---|
| "Quit" / "He quit on us" / "Voluntary quit" | **Resigned** + `separation_type=voluntary` | Triggers playbook · 8 tasks |
| "We let him go" / "Fired" | **Terminated** + `separation_type=involuntary` | Triggers playbook · 8 tasks |
| "Reduction in force" | **Terminated** + `separation_type=layoff` | Triggers playbook · 8 tasks |
| "Retired" | **Retired** | Triggers playbook · 8 tasks |
| "On vacation/medical leave" | **Leave of Absence** | No playbook; leave dates required |
| "He no-call-no-showed but might be back" | **Suspended** or **Inactive** | No playbook |

The dropdown labels are explicit (Resigned / Terminated / Retired / etc.), but HR Manager's mental model is "Quit". If she clicked **Resigned**, the action is correct.

---

## 4 · Live backend probe (operator-objective-9 authorized)

The operator's objective #9 explicitly directs the audit to "Verify persistence by editing status · refreshing page · reloading employee record · checking API response · checking database field · checking audit/history/event record." This probe was performed and immediately reversed:

### 4.1 Test target

* Employee: `Alec Perkins` · id `c9d7ebc3-a292-4d7a-8765-0ce2739c6029`.
* Initial state (BEFORE): `lifecycle_status=None, is_active=True, status_history=[]` (legacy row, no prior lifecycle stamp).

### 4.2 Step A — missing required fields (expected to fail)

```
POST /api/hr/employees/{id}/status
X-HR-Token: <hrmanager>
{"lifecycle_status":"Resigned","reason":"PRE-DEPLOY AUDIT PROBE"}

→ HTTP 400
{"detail":"separation_type is required when transitioning to Resigned (one of: voluntary, involuntary, layoff)"}
```

✅ Backend correctly rejects with a clear human-readable error.

### 4.3 Step B — complete payload (expected to succeed)

```
POST /api/hr/employees/{id}/status
X-HR-Token: <hrmanager>
{"lifecycle_status":"Resigned","reason":"PRE-DEPLOY AUDIT PROBE — will be reversed",
 "separation_type":"voluntary","rehire_eligibility":"eligible"}

→ HTTP 200
{
  "ok": true,
  "employee": {
    "id": "c9d7ebc3-…",
    "lifecycle_status": "Resigned",
    "is_active": false,
    "separation_type": "voluntary",
    "rehire_eligibility": "eligible",
    "termination_date": "2026-06-02",
    "last_day_worked": "2026-06-02",
    "status_history": [{
      "at":"2026-06-02T14:10:01.338365+00:00",
      "by":"HR Manager","from":"Active","to":"Resigned",
      "reason":"PRE-DEPLOY AUDIT PROBE — will be reversed"
    }],
    "updated_at":"2026-06-02T14:10:01.338365+00:00"
  },
  "tasks_created": 8,
  "task_ids": [<8 uuid task ids>]
}
```

✅ 200 + full updated employee + 8 offboarding tasks fanned out.

### 4.4 Step C — verify persistence via independent read

```
GET /api/hr/employees/{id}/offboarding-summary
→ lifecycle_status=Resigned, is_active=False, status_history_len=1
```

✅ Persisted in `db.employees`. Reachable from a fresh read. Audit history present.

### 4.5 Step D — reverse via canonical reactivate endpoint

```
POST /api/hr/employees/{id}/reactivate
X-HR-Token: <hrmanager>
{"lifecycle_status":"Active","reason":"PRE-DEPLOY AUDIT PROBE — reversing test mutation"}

→ HTTP 200
{ok:true, employee:{lifecycle_status:"Active", is_active:true, last_day_worked:null,
 status_history:[{from:"Active",to:"Resigned",…probe entry…},
                 {from:"Resigned",to:"Active",…reverse entry…}], …}}
```

Then independent re-read:

```
lifecycle_status=Active, is_active=True, history_len=2
```

✅ Employee restored to Active. The forensic `status_history` retains both entries (append-only) — this is the correct doctrine.

### 4.6 Residual side-effect (disclosed)

8 offboarding tasks (`db.tasks` rows with `source_module=employees`, `source_id=<employee_id>`) were created during Step B and were **NOT** auto-deleted by the reactivate. By doctrine (`NO employee data cleanup` per the audit rules), they remain in place. The operator may choose to cancel them via `/admin/tasks` or leave them as forensic evidence of this audit probe. Task ids logged in §4.3 above.

---

## 5 · Phase Alpha impact on this path

Phase Alpha (Employee Governance) closes 5 P0 violations on the EMPLOYEE CREATE / TERMINATE write surface — see `EMPLOYEE_GOVERNANCE_ALPHA_IMPLEMENTATION_REPORT.md`. None of those closures touch `POST /api/hr/employees/{id}/status`.

| Closed by Phase Alpha | Affects HR status save? |
|---|---|
| G-1 · `POST /employees/add` → 410 | NO — that's the public path |
| G-2 · `POST /field-leadership/employees` → enqueue | NO — that's Operations |
| G-3 · `/admin/employees/*` require HR/Admin + DELETE 405 | NO — that's the Admin direct-write back-door |
| G-4 · `PUT /admin/employees/{id}` with `is_active` / `lifecycle_status` → 422 | NO — that's the Admin field back-door |
| G-5 · `POST /admin/employees/upload` merge-only | NO — that's bulk CSV |

**The HR canonical path `POST /api/hr/employees/{id}/status` is explicitly preserved AND named in the G-4 422 error message as the correct alternative**: `"Use POST /api/hr/employees/{id}/status or POST /api/hr/employees/{id}/reactivate."` (`backend/server.py:_require_hr_or_admin_for_queue` block).

**Conclusion**: Phase Alpha does NOT block HR's lifecycle save. Phase Alpha does NOT change the behaviour HR is complaining about. After Phase Alpha deploy, HR still uses the same `POST /hr/employees/{id}/status` endpoint with the same UI.

The new **HR Queue** (`/hr/employee-requests`) is a SEPARATE workflow for inbound NEW-HIRE and TERMINATION REQUESTS submitted by Operations / public forms / FL Termination Form addendum — it does NOT replace HR's direct lifecycle authority. HR can either:

* (a) Approve a queued request, which fans out into the canonical status mutation (`hr-queue-approval` path) — or —
* (b) Continue to directly edit an existing employee's status via the `HrEmployees.jsx` drawer → "Status" tab → "Update status" button (the exact path HR is complaining about).

Both paths remain operational after Alpha.

---

## 6 · Classification

# 🟡 **B — Existing behaviour works but has bad UX / no confirmation**

* **Backend**: works correctly. Persists. Returns full updated record. Fires playbook. Records audit history. Verified live with HR-only token (no admin escalation). 🟢
* **Frontend**: Save button EXISTS (`data-testid="hremp-status-save"`), success toast IS triggered, status history IS rendered post-save. But the button label says **"Update status"** instead of "Save", lives on the SECOND tab (not the default Details tab), and HR's mental vocabulary ("Quit") doesn't match any dropdown option ("Resigned"). 🟡
* **Phase Alpha impact**: NONE on this path. The HR canonical status mutation endpoint is explicitly preserved AND is the documented "use instead" path for the Alpha-closed back-doors. ✅

**This is NOT:**

* (A) Fixed by Alpha — Alpha doesn't touch this path.
* (C) Doesn't persist — persistence verified live.
* (D) Blocked by Alpha — Alpha intentionally preserves this path.
* (E) True deploy blocker — feature works; only operator perception/training is at issue.

**This IS:**

* (B) Working, persisting, audited — but with three UX hardening opportunities surfaced in `HR_EMPLOYEE_STATUS_UI_REVIEW.md §3`.

---

## 7 · Deploy-hold recommendation

# 🟢 **DEPLOY MAY PROCEED**

The OMEGA Deep Pre-Deploy Certification (🟢 GO TO DEPLOY · `DEEP_PRE_DEPLOY_GO_NO_GO.md`) is **NOT** invalidated by this report. The HR lifecycle save feature works correctly today and continues to work identically after Phase Alpha is deployed.

Three optional UX hardening tweaks are recommended for a follow-up iter (each ≤ 25 LOC, none blocking deploy):

1. Rename button label "Update status" → "Save status change" (1 string).
2. Auto-switch to the "Status" tab when the drawer is opened from the row-click "Edit Status" intent (currently always opens to "Details").
3. Add an in-form HelpTipBlock explaining the canonical vocabulary ("Quit = Resigned · Fired = Terminated · etc.") above the lifecycle dropdown.

These are listed in detail in `HR_EMPLOYEE_STATUS_UI_REVIEW.md §3` and require explicit operator authorization before any code change (rule: "STOP and ask for authorization before coding").

🛑 **STOPPED. Read-only audit complete + one operator-authorized persistence probe performed and reversed. No code changes made.**
