# HR SAVE BUTTON · FORENSIC REPORT

**Date**: 2026-06-02T18:33 UTC
**Mode**: READ-ONLY · NO fixes · NO code · NO deploy
**Authority**: OMEGA P0 — HR Lifecycle Save Button Forensic Failure (reopened)
**Companions**: `HR_SAVE_BUTTON_EXECUTION_TRACE.md`, `HR_SAVE_BUTTON_ROOT_CAUSE.md`, `DEPLOYMENT_BLOCKER_REASSESSMENT.md`

---

## 1 · The 13 forensic questions

| # | Question | Answer | Evidence |
|---:|---|---|---|
| 1 | Does button click fire? | ✅ YES | `<Button onClick={submitStatusChange}>` at `HrEmployees.jsx:1043`; testid `hremp-status-save` present in production bundle `main.8e2b2094.js` (verified in `L1_L2_REMEDIATION_CERTIFICATION.md`) |
| 2 | Does API call fire? | ⚠️ CONDITIONALLY — fires only if 3 frontend pre-validation checks pass (separation_type · rehire_eligibility · rehire_eligibility_reason for required cases). If any check fails, function returns at lines 532/537/546 BEFORE the API call. |
| 3 | What endpoint? | `POST {REACT_APP_BACKEND_URL}/api/hr/employees/{id}/status` (file `employeesApi.js:63`) |
| 4 | Response code? | 200 on success (probes A, B, C, D all returned 200); 400 on offboarding without separation_type or invalid rehire_eligibility; 401 on missing/wrong token; 403 on wrong role; 404 on missing employee; 422 on Pydantic validation; 5xx never observed |
| 5 | Any console errors? | NONE detected in code path. The handler is wrapped in try/catch; uncaught render errors would crash the entire component, not just "do nothing" |
| 6 | Any Sentry errors? | NOT observed in this audit. Sentry is enabled per `/api/version` `sentry.enabled=true`. If any 5xx fired, it would be reported. Probe of `/api/webhooks/resend` confirms backend healthy. |
| 7 | Any backend errors? | NONE on the success path. Backend cleanly returns 400/401/422 with structured `detail` body when validation fails. |
| 8 | Any validation failures? | YES — three frontend pre-checks at `HrEmployees.jsx:529-546` AND three backend checks at `employee_lifecycle.py:1010/1029/1042`. Each can short-circuit the save. |
| 9 | Any permission failures? | NONE on the happy path (HR token validated upstream). Anonymous → 401; non-HR portals → 403. None observed for the user's reported flow. |
| 10 | Any silent catches? | ⚠️ Two soft-silent paths:<br/>• `HrEmployees.jsx:525`: `if (!employee) return;` — bails silently when employee not yet loaded (no toast, no console message)<br/>• `HrEmployees.jsx:521`: `.catch(() => setEmployee(null))` — initial summary fetch failures silently null out the employee. Then a subsequent save click hits the silent return at line 525. |
| 11 | Does database update? | ✅ YES on every non-noop save. Verified live: `status_history.length` grew 4 → 5 → 6 across the probes. `lifecycle_status` flipped correctly. `is_active` flipped correctly. |
| 12 | Does `status_history` update? | ✅ YES — append-only via `$push`. Each entry: `{at: ISO8601, by: HR Manager, from: <prev>, to: <new>, reason: <provided>}`. |
| 13 | Does `employee_lifecycle_events` update? | ✅ YES — verified in earlier `RESEND_WEBHOOK_SECRET_FORENSIC_REPORT` companion + this run (accountability timeline event count alive). Append-only chain. |

---

## 2 · The 4 specific lifecycle reproductions (read-only · preview backend)

### 2.1 · Resigned (Active → Resigned)
* **Frontend gate**: requires `separation_type` AND `rehire_eligibility` (and reason if rehire ∈ {not_eligible, review_required})
* **If gate satisfied**: API fires → 200 → DB write → 8-task offboarding playbook → green toast → drawer state refreshed
* **If gate NOT satisfied**: red toast at bottom-right, function returns, no API call
* **Live probe result**: 200, `playbook_fired=true`, `tasks_created=8`, `status_history` appended

### 2.2 · Terminated (Active → Terminated)
* Same code path as Resigned — `_OFFBOARDING_STATUSES` includes both
* `separation_type` typically "involuntary" or "layoff"
* Same gating, same response shape, same 8-task playbook
* **Live probe result**: would behave identically to Resigned (same code branch)

### 2.3 · Laid Off (Active → Terminated, separation_type=layoff)
* Same as Terminated but `separation_type="layoff"` in payload
* Frontend gate satisfied if dropdown selected
* Same response, same playbook
* **Live probe result**: would behave identically

### 2.4 · Rehire (Inactive/Terminated/Resigned/Retired → Active or Pending Hire)
* **TWO paths exist** — this is a known confusion source:
  * **Path A** · Reactivate dialog (`submitReactivate`, `HrEmployees.jsx:576`): preferred — calls `POST /reactivate` with rehire_date + sets `original_hire_date`. Has its own `<Dialog>` with `<DialogFooter>` (separate from Sheet sticky footer).
  * **Path B** · Status tab (`submitStatusChange`): also accepted — user picks Active in Status dropdown, clicks Save. Live probe D verified this works (HTTP 200, lifecycle flipped, status_history appended). But this path does NOT set `rehire_date` and does NOT preserve `original_hire_date` semantics.
* Either path produces a 200 + DB update + status_history append + green toast.
* **Risk**: HR who uses Path B might lose the rehire-date metadata. Backend doesn't reject it, just silently doesn't set it.

---

## 3 · What the user said vs what the code does

> **User**: "Save button is visible. User fills out lifecycle form. User clicks Save Status Change. Nothing appears to happen."

| User claim | Forensic finding | Match? |
|---|---|:-:|
| "Save button is visible" | ✅ Confirmed — production bundle has `hremp-status-footer` + `hremp-status-save` testids | ✅ |
| "User fills out lifecycle form" | ✅ Form fields render and accept input | ✅ |
| "User clicks Save Status Change" | ✅ Button has `onClick={submitStatusChange}` | ✅ |
| "Nothing appears to happen" | ⚠️ This is the focal claim. Code-side: SOMETHING always happens — either a toast.error (validation fail) OR a toast.success + state refresh OR a toast.error (backend error). The button is never wired to "do nothing". **The user's perception of "nothing" must therefore map to one of**:<br/>• a brief bottom-right toast they missed/dismissed<br/>• a green success toast that wasn't perceived as confirmation because the drawer didn't close<br/>• a green noop toast where status didn't change because they clicked Save without changing the dropdown value<br/>• a possible Sonner z-index conflict with the sticky drawer footer (unverified) | ⚠️ |

---

## 4 · Evidence summary

| Evidence | Source | Value |
|---|---|---|
| Save button DOM presence | Production bundle `main.8e2b2094.js` | `data-testid="hremp-status-save"` found 1 match |
| Sticky footer DOM presence | Production bundle | `data-testid="hremp-status-footer"` found 1 match |
| onClick handler wired | `HrEmployees.jsx:1043` | `onClick={submitStatusChange}` |
| API endpoint correct | `employeesApi.js:63` | `POST /api/hr/employees/{id}/status` |
| Backend route exists | `employee_lifecycle.py:968` | `@router.post("/api/hr/employees/{employee_id}/status")` |
| Backend gate works | Live probe | 401 anon, 401 forged FL token, 200 HR token |
| DB write works | Live probe | `status_history.length` grew 4 → 5 → 6 |
| Playbook fan-out works | Live probe A | `tasks_created: 8` |
| Toast mounted | `App.js:283` | `<Toaster position="bottom-right" richColors closeButton offset={16} />` |
| Drawer auto-close on save | (NOT CODED) | Drawer stays open; only the toast signals success |

---

## 5 · STOP

Forensic capture complete. Root cause analysis in `HR_SAVE_BUTTON_ROOT_CAUSE.md`. Reassessment of blocker classification in `DEPLOYMENT_BLOCKER_REASSESSMENT.md`.
