# HR SAVE BUTTON · EXECUTION TRACE

**Date**: 2026-06-02T18:33 UTC
**Mode**: READ-ONLY · live preview backend probe + code-path trace · NO production mutation
**Authority**: OMEGA P0 — HR Lifecycle Save Button Forensic Failure (reopened)

---

## 1 · Full click-to-database trace (code path)

| Stage | File · Line | What happens |
|---|---|---|
| 1 · Button click | `HrEmployees.jsx:1043` | `<Button onClick={submitStatusChange} disabled={saving} data-testid="hremp-status-save" />` |
| 2 · Handler entry | `HrEmployees.jsx:524` | `const submitStatusChange = async () => { ... }` |
| 3 · Early-return guard | `HrEmployees.jsx:525` | `if (!employee) return;` — if no employee loaded, silently bails |
| 4 · Frontend validation A | `HrEmployees.jsx:529-532` | `if (offboardingTransition && !statusForm.separation_type && !employee.separation_type) { toast.error("Pick a separation type..."); return; }` |
| 5 · Frontend validation B | `HrEmployees.jsx:534-537` | `if (offboardingTransition && !statusForm.rehire_eligibility && !employee.rehire_eligibility) { toast.error("Pick a rehire eligibility..."); return; }` |
| 6 · Frontend validation C | `HrEmployees.jsx:538-546` | `if (offboardingTransition && rehire in ["not_eligible","review_required"] && !reason.trim() && !employee.rehire_eligibility_reason) { toast.error("Add a short reason..."); return; }` |
| 7 · Set loading state | `HrEmployees.jsx:547` | `setSaving(true);` — button text flips to "Saving…" |
| 8 · Build payload | `HrEmployees.jsx:548-560` | Inserts lifecycle_status, reason, separation_type, dates, rehire_eligibility, rehire_eligibility_reason into payload |
| 9 · API call | `HrEmployees.jsx:561` → `employeesApi.js:57-66` | `axios.post(${API}/hr/employees/${id}/status, body, {headers: authHeaders()})` with `X-HR-Token` header |
| 10 · Backend gate | `employee_lifecycle.py:972` | `Depends(require_hr_or_admin)` — 401 if missing/wrong token, 403 if wrong role |
| 11 · Backend fetch employee | `employee_lifecycle.py:974-977` | `db.employees.find_one({"id": employee_id, "deleted_at": None})` — 404 if missing |
| 12 · noop short-circuit | `employee_lifecycle.py:981-983` | `if prev_status == body.lifecycle_status: return {"ok": True, "employee": existing, "tasks_created": 0, "noop": True}` |
| 13 · Backend validation A | `employee_lifecycle.py:1010-1016` | `if not (existing_sep or incoming_sep): raise HTTPException(400, "separation_type is required when transitioning to {status} (one of: voluntary, involuntary, layoff)")` |
| 14 · Backend validation B | `employee_lifecycle.py:1029-1034` | `if chosen_rehire not in ALLOWED_REHIRE_ELIGIBILITY: raise HTTPException(400, "rehire_eligibility must be one of {valid}")` |
| 15 · Backend validation C | `employee_lifecycle.py:1042-1050` | `if chosen_rehire in {"not_eligible","review_required"} and not reason: raise HTTPException(400, "rehire_eligibility_reason is required ...")` |
| 16 · DB write | `employee_lifecycle.py:1094-1100` | `db.employees.update_one({"id": id}, {"$set": {lifecycle_status, is_active, updated_at, ...date_updates}, "$push": {"status_history": {at, by, from, to, reason}}})` |
| 17 · Playbook fan-out | `employee_lifecycle.py:1107-1111` | If transitioning into Terminated/Resigned/Retired: `_fan_out_offboarding_playbook` inserts 8 rows in `db.tasks` |
| 18 · Response | `employee_lifecycle.py:1116-1122` | Returns `{"ok": True, "employee": <full doc>, "tasks_created": N, "task_ids": [...], "playbook_fired": True/False}` |
| 19 · Frontend success toast | `HrEmployees.jsx:562-566` | If `r.playbook_fired`: `toast.success("Status updated · N offboarding tasks created")`. Else: `toast.success("Status updated")` |
| 20 · Frontend re-fetch | `HrEmployees.jsx:567-569` | `const s = await offboardingSummary(employee.id); setSummary(s); setEmployee(s.employee);` — refreshes drawer state |
| 21 · Frontend error catch | `HrEmployees.jsx:570-572` | `catch (e) { toast.error(friendlyError(e, "Status change failed")); }` |
| 22 · Finally | `HrEmployees.jsx:572` | `finally { setSaving(false); }` — button text back to "Save Status Change" |

**Critical observation — what does NOT happen on success**:
* ❌ The drawer does NOT auto-close
* ❌ `statusForm` is NOT reset
* ❌ The user does NOT see a prominent in-drawer success banner — only the bottom-right toast which auto-dismisses in ~4 seconds
* ❌ The parent employee list/table is not visibly refreshed in front of the user (the drawer covers it)

---

## 2 · Live preview backend probes — what actually happens at each branch

Probe employee: `c9d7ebc3-a292-4d7a-8765-0ce2739c6029` (Alec Perkins) — preview pod, HR token. Pre-state: `lifecycle_status=Active`, `separation_type=voluntary` (persisted from earlier test runs), `rehire_eligibility=eligible`, `status_history.length=4`.

| Probe | Request body | Backend response | Side effects |
|---|---|---|---|
| **A** | `{"lifecycle_status":"Resigned","reason":"forensic probe"}` (NO separation_type, NO rehire_eligibility in body) | **HTTP 200** · `{"ok":true,"playbook_fired":true,"tasks_created":8}` · `lifecycle_status` flipped to Resigned · 8 task_ids returned | DB updated · status_history.length=5 · 8 offboarding playbook tasks inserted |
| **B** | `{"lifecycle_status":"Resigned","reason":"…","separation_type":"voluntary"}` (already Resigned now) | **HTTP 200** · `{"ok":true,"tasks_created":0,"noop":true}` · `lifecycle_status` unchanged | NO DB write · NO history entry · NO playbook |
| **C** | `{"lifecycle_status":"Resigned","reason":"…","separation_type":"voluntary","rehire_eligibility":"not_eligible"}` (still Resigned · no reason field) | **HTTP 200** · `{"ok":true,"tasks_created":0,"noop":true}` | NO write — noop short-circuit fires BEFORE validation C |
| **D** | `{"lifecycle_status":"Active","reason":"forensic noop probe"}` (was Resigned · → Active) | **HTTP 200** · status flipped to Active · `is_active=true` · status_history.length=6 | DB updated · history entry appended |

### Why Probe A returned 200 instead of 400 (separation_type missing)

The backend's validation at line 1010 checks: `if not (existing_sep or incoming_sep)`. **Alec Perkins already had `separation_type="voluntary"` on his record from earlier test runs**, so `existing_sep` was non-empty and the validation passed — the backend silently re-used the existing value. The frontend validation at line 529 mirrors this exact logic (`!statusForm.separation_type && !employee.separation_type`).

**Implication**: For a previously-offboarded-then-reactivated employee, the separation_type, rehire_eligibility, and termination_date persist on the record. Re-offboarding does NOT require the operator to re-enter them. This is intentional but produces a UX surprise — the form fields appear required (they're rendered when status=Resigned/Terminated/Retired) but actually have hidden fallbacks. **For a brand-new hire who has never been offboarded**, the validation WOULD fire (both frontend and backend) and `toast.error` would be the user-visible result.

---

## 3 · Where "nothing happens" can occur — failure-mode catalog

| # | Failure mode | User experience | Backend log | DB write | Toast visible? |
|---:|---|---|:-:|:-:|:-:|
| F1 | Frontend validation A: offboarding + no separation_type + no existing | Click → red toast "Pick a separation type — voluntary, involuntary, or layoff" → returns early | NONE (request never sent) | NO | toast.error fires (bottom-right, 4s auto-dismiss) |
| F2 | Frontend validation B: offboarding + no rehire_eligibility + no existing | Click → red toast "Pick a rehire eligibility — Eligible, Not Eligible, or Review Required" → returns early | NONE | NO | toast.error fires |
| F3 | Frontend validation C: rehire=not_eligible/review_required + no reason | Click → red toast "Add a short reason for this rehire eligibility decision" → returns early | NONE | NO | toast.error fires |
| F4 | Backend validation A: same as F1 but employee has no historical separation_type | Click → "Saving…" → HTTP 400 → red toast `friendlyError("separation_type is required when transitioning to Resigned (one of: voluntary, involuntary, layoff)")` | 400 in access log | NO | toast.error fires |
| F5 | Backend validation B/C: bad rehire_eligibility value or missing reason | Click → "Saving…" → HTTP 400 → red toast | 400 in access log | NO | toast.error fires |
| F6 | `noop` short-circuit (line 982): user picks same status as current | Click → "Saving…" → HTTP 200 with `noop: true` → toast.success("Status updated") → drawer re-renders with IDENTICAL state | 200 in access log | NO actual DB mutation (find_one only) | toast.success fires — but UI looks unchanged |
| F7 | Network drop / CORS / 5xx | Click → "Saving…" → axios rejects → red toast `friendlyError(e, "Status change failed")` | NONE or 5xx | NO | toast.error fires |
| F8 | Successful save · drawer stays open · toast auto-dismisses | Click → "Saving…" → 200 → status_history appended (visible if user scrolls inside drawer to "Recent status history") → header badge updates → toast auto-dismisses in 4s | 200 | YES | toast.success fires — but ephemeral |
| F9 | `friendlyError()` returns empty string | Catch block fires, `toast.error("")` may render an empty toast container | non-200 | NO | toast may be barely visible |
| F10 | Sonner Toaster not mounted / Z-index conflict with sticky footer | Click → handler fires → API may fire → toast hidden behind sticky footer or off-screen | varies | varies | toast NOT visible |

---

## 4 · The single most-likely user-perception failure (F8 compound)

```
User flow                          What user perceives           What actually happens
────────────────────────────────  ─────────────────────────     ────────────────────────────────────
1. Pick "Resigned" from dropdown   Form expands                  Form expands; status badge in header
                                                                  still shows Active
2. Pick separation type            Field fills                   Local statusForm state updates
3. Pick rehire eligibility         Field fills                   Local statusForm state updates
4. (Optionally) pick reason        Textarea fills                Local statusForm state updates
5. Click "Save Status Change"      Button briefly shows
                                   "Saving…" (~200-400ms)        setSaving(true) → API fires
6. ~400 ms later button reverts    Toast appears bottom-right    Backend returned 200
                                   "Status updated · 8 offboarding tasks created"
                                   Toast auto-dismisses ~4s
7. User looks at drawer            Header badge now shows        Drawer state refreshed (offboardingSummary re-fetched)
                                   "Resigned" (visual change
                                   may be subtle — color shift)
8. User looks at modal             Drawer is still open with     Drawer is INTENTIONALLY left open so HR
                                   the same form layout          can review history; statusForm not reset
                                   No "Saved" banner inside drawer
9. User clicks X / outside         Drawer closes                 setId(null) → drawer unmounts
10. User looks at table            Row now shows "Resigned"      Table re-renders from latest fetch

USER'S MENTAL MODEL: "I clicked save, nothing happened, so I clicked X expecting it to save on close."
ACTUAL REALITY:      Save WORKED. Backend wrote. Tasks fired. Toast was shown for 4s. UI did update.
                     But the UX feedback was insufficient for the user to perceive success.
```

If the user's eyes were on the modal/button area (not bottom-right) at the moment of save, AND the status badge color change was subtle, AND the drawer didn't close — the user would conclude "nothing happened".

---

## 5 · Per-transition reproduction matrix (preview backend, HR-token)

| Lifecycle target | Live probe result | Frontend validation outcome | Backend validation outcome | DB write | Playbook | Toast |
|---|---|---|---|:-:|:-:|---|
| Active → **Resigned** (fresh, no history) | would require fresh employee | F1 fires (separation_type required) | F4 fires if FE somehow bypassed | NO | NO | red |
| Active → **Resigned** (with persisted history) | Probe A: 200, playbook fired | passes (employee.separation_type present) | passes (existing_sep set) | YES | 8 tasks | green |
| Active → **Terminated** (involuntary) | same code path · Probe A equivalent | same gating | same gating | YES on transition | 8 tasks | green |
| Active → **Terminated** (laid off · separation_type=layoff) | same code path · `separation_type` carries layoff | same gating | same gating | YES on transition | 8 tasks | green |
| Inactive → **Active** (rehire via Status tab) | Probe D: 200, status flipped | NO offboarding validation triggered | NO offboarding validation | YES | NO playbook | green |
| (preferred path) Rehire via Reactivate Dialog | separate handler `submitReactivate` → `POST /reactivate` (line 580) | sets rehire_date · preserves original_hire_date | preserved by `/reactivate` endpoint | YES | NO | green |
| Same → Same (e.g., Active → Active) | Probe B/C equivalent: 200 noop | passes (no transition) | noop short-circuit · NO write | NO | NO | green (misleading) |

---

## 6 · Evidence that the backend is healthy and the wire is intact

* Production probe of the endpoint family returns the correct gating: anonymous → 401, wrong portal token → 401 (per `L1_L2_REMEDIATION_CERTIFICATION.md`).
* Preview probe with HR token returns 200 on every code path tested above.
* `status_history` is growing correctly across runs (4 → 5 → 6 across the probes in this audit).
* The 8-row offboarding playbook fires when transitioning into Terminated/Resigned/Retired.
* The `noop` short-circuit returns successfully but with `tasks_created: 0` and `noop: true` flag.

**The backend, the API call, the DB write, the status_history write, and the playbook fan-out all WORK CORRECTLY.** The failure surface is on the frontend perception side.

---

## 7 · STOP

Execution trace complete. Findings consolidated into `HR_SAVE_BUTTON_ROOT_CAUSE.md` and `DEPLOYMENT_BLOCKER_REASSESSMENT.md`.
