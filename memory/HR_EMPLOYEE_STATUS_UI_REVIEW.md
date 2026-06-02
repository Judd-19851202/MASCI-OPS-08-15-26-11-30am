# HR EMPLOYEE STATUS · UI REVIEW

**Date**: 2026-06-02
**Companion**: `HR_EMPLOYEE_LIFECYCLE_SAVE_AUDIT.md`, `DEPLOYMENT_IMPACT_HR_LIFECYCLE_STATUS.md`.
**Mode**: READ-ONLY.

---

## 1 · UI inventory — `/hr/employees` drawer · "Status" tab

| Element | data-testid | Behaviour | Verdict |
|---|---|---|---|
| Tab strip (`Details · Status · Offboarding Summary`) | `hremp-tab-status` | Default tab on drawer open = **Details**. HR must click "Status" tab to reach the status editor. | 🟡 hidden by default |
| Lifecycle dropdown | `hremp-status-new` | 9 canonical values from `LIFECYCLE_STATUSES` array | 🟢 functional · 🟡 no "Quit" alias |
| Separation Type dropdown (conditional · shown when status ∈ {Terminated, Resigned, Retired}) | `hremp-separation-type` | Required for save; validation enforced client-side AND server-side | 🟢 |
| Last Day Worked (date input) | `hremp-tx-last-day` | Optional; auto-defaults to today server-side | 🟢 |
| Termination Date (date input) | `hremp-tx-term-date` | Optional; auto-defaults to today server-side | 🟢 |
| Rehire Eligibility dropdown | `hremp-rehire-eligibility` | Required for save on offboarding transitions | 🟢 |
| Rehire Eligibility Reason (textarea, conditional) | `hremp-rehire-reason` | Required when rehire ∈ {not_eligible, review_required} | 🟢 |
| Leave Start Date / Expected Return Date (when status=Leave of Absence) | `hremp-tx-leave-start` / `hremp-tx-leave-return` | Optional · auto-default | 🟢 |
| Reason / note (textarea) | `hremp-status-reason` | Optional · recorded in `status_history.reason` | 🟢 |
| Offboarding-playbook warning callout | `hremp-playbook-warning` | Amber panel — "Offboarding playbook will fire · 8 follow-up tasks" — shown when transitioning into Term/Resigned/Retired | 🟢 |
| Save button | `hremp-status-save` | Label: **"Update status"** / **"Saving…"** while in-flight | 🟡 label not "Save" |
| Recent status history list | (no testid; renders inside Status tab) | Shows last 5 history entries with timestamps + from→to + reason | 🟢 |
| Success toast | (sonner toast) | `"Status updated"` or `"Status updated · 8 offboarding tasks created"` | 🟢 fires correctly |
| Error toast | (sonner toast) | `friendlyError(e, "Status change failed")` — shows server-side validation message | 🟢 fires correctly |

---

## 2 · Why HR perceives "no Save button / no confirmation"

Three independent factors compound into the perception:

### 2.1 Label mismatch

The button literally reads **"Update status"** (line 906). HR's mental model is "I picked something from a dropdown, where do I click Save?". The button is there, but the verb doesn't match the verb HR expects. This is the most likely root cause.

### 2.2 Tab visibility

The `EmployeeDrawer` opens to the **Details** tab by default (`useState("details")` on line 466). On the Details tab, the lifecycle dropdown does NOT appear — only individual editable fields (trade, role, crew, etc.). To reach the status editor, HR must:

1. Click an employee row → drawer opens to **Details**.
2. Click the **Status** tab → status dropdown + Save button + history appear.

If HR picked a value from the small lifecycle filter dropdown at the TOP of the roster page (`hremp-status-filter`, line 161), that is **NOT a save target** — it's a list-filter only, and it has no Save button by design. HR may have been clicking that and waiting for something to happen.

### 2.3 Vocabulary mismatch

There is no `"Quit"` value. HR Manager's spoken word "Quit" maps to **Resigned** + `separation_type=voluntary`. If HR was scanning the dropdown looking for "Quit", she may have given up before finding "Resigned" — or she may have clicked Resigned but is uncertain whether that's the right canonical word for what she meant.

### 2.4 What DID work for HR (verified)

* Backend status PERSISTS correctly (see `HR_EMPLOYEE_LIFECYCLE_SAVE_AUDIT.md §4`).
* If HR did press "Update status", the toast DID fire and the history DID update — but a Sonner toast can be missed on slower devices or if HR was already navigating away from the drawer.
* Server response includes `tasks_created` count which is surfaced in the toast string when > 0.

---

## 3 · Recommended UX hardening (each ≤ 25 LOC · NONE actioned this audit)

Per operator rule: "READ ONLY unless defect is confirmed and fix is under 25 LOC and directly required to make HR lifecycle save behavior clear/safe. If fix is needed: STOP and ask for authorization before coding."

**No defect was confirmed.** Three optional UX hardening recommendations are surfaced for explicit operator authorization. Each is independent and reversible.

### REC-1 · Rename "Update status" → "Save status change" (1 LOC · 1 string)

* File: `frontend/src/pages/HrEmployees.jsx:907`.
* Change: `{saving ? "Saving…" : "Update status"}` → `{saving ? "Saving…" : "Save status change"}`.
* Impact: Direct vocabulary match with HR's mental "Save" verb. Zero functional change.

### REC-2 · Auto-jump to Status tab when row's status badge was the click target (≤ 12 LOC)

* File: `frontend/src/pages/HrEmployees.jsx:232-250` (row click) + `:466` (tab default).
* Logic: when the user clicks the row's `StatusBadge`, set `tab="status"` instead of `"details"`. Currently the entire row triggers `onClick={() => setEditId(e.id)}` → drawer defaults to Details.
* Implementation sketch: pass an `initialTab` prop into `EmployeeDrawer`; have the StatusBadge wrap a separate click handler that sets it to `"status"`.
* Impact: HR clicks the badge they want to change → drawer opens on the editor that changes it.

### REC-3 · Add a HelpTipBlock above the lifecycle dropdown (≤ 10 LOC)

* File: `frontend/src/pages/HrEmployees.jsx:810` (just before the `<Label>New status</Label>`).
* Insert: `<HelpTipBlock formKey="employee-lifecycle.vocabulary" />` with content:

```
"Quit" / "voluntary self-quit" → choose **Resigned** + Voluntary
"Fired" / "let go for cause" → choose **Terminated** + Involuntary
"Reduction in force" → choose **Terminated** + Layoff
"Retired" → choose **Retired**
"On medical / paternity / vacation" → choose **Leave of Absence**
"Suspended pending investigation" → choose **Suspended**
```

* Impact: removes vocabulary ambiguity. Zero functional change.

### Combined LOC budget

| Recommendation | LOC | Risk |
|---|---|---|
| REC-1 | 1 | None |
| REC-2 | ~12 | Trivial — prop threading |
| REC-3 | ~10 | None — content-only insertion |
| **Total if all three approved** | **≤ 25** | Within the operator's 25-LOC allowance |

---

## 4 · What is NOT a defect

To prevent future confusion, the following are confirmed to **work correctly** and require no change:

* ✅ Save button is rendered on the Status tab with `data-testid="hremp-status-save"`.
* ✅ Saving state animates ("Saving…").
* ✅ Server returns 200 with full updated employee record on success.
* ✅ Server returns 400 with field-name in `detail` on missing required fields.
* ✅ Sonner success toast fires with the canonical "Status updated" copy.
* ✅ Sonner error toast fires with the server's human-readable error message.
* ✅ Status history list re-renders below the button after save (5 most recent entries).
* ✅ `OffboardingSummary` is re-fetched and the badge in the drawer header re-renders to the new status.
* ✅ The roster table's status filter re-applies (via `fetchAll()` on drawer close).
* ✅ HR-only token (`hrmanager@mascigc.com`) successfully invokes the endpoint without admin escalation — verified live in §4 of the companion audit.
* ✅ Audit / history / event record IS written (`db.employees.status_history[]` append + `db.tasks` fan-out on offboarding).

---

## 5 · UX verdict

# 🟡 **WORKING WITH IMPROVABLE UX**

The save flow is functionally complete. The reported confusion stems from three small but compounding UX gaps (label · default tab · vocabulary) that are independently addressable in ≤ 25 LOC total. **No blocker. No defect. No deploy hold required.**
