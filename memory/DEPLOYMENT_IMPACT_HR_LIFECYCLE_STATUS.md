# DEPLOYMENT IMPACT · HR LIFECYCLE STATUS

**Date**: 2026-06-02
**Companion**: `HR_EMPLOYEE_LIFECYCLE_SAVE_AUDIT.md`, `HR_EMPLOYEE_STATUS_UI_REVIEW.md`.
**Mode**: READ-ONLY.

---

## 1 · Impact on the pending OMEGA Pre-Deploy 🟢 GO verdict

| Question | Answer |
|---|---|
| Does this audit reveal a deploy blocker? | **NO.** |
| Does this audit invalidate the prior `DEEP_PRE_DEPLOY_GO_NO_GO.md` 🟢 GO verdict? | **NO.** |
| Does this audit require a code change before deploy? | **NO.** |
| Does this audit identify a security defect? | **NO.** |
| Does this audit identify a data-integrity defect? | **NO.** |
| Does this audit identify a workflow-integrity defect? | **NO.** |
| Does this audit identify a UX clarity gap that the operator may wish to address? | **YES — 3 hardening items, each ≤ 25 LOC, all optional.** |

---

## 2 · Per-system impact

| Downstream system | State before audit | State after audit |
|---|---|---|
| `db.employees` write surface | HR canonical path `/hr/employees/{id}/status` works correctly | Unchanged. One probe row + reverse documented. |
| `db.tasks` (offboarding playbook) | Working. 8 tasks per offboarding transition. | Unchanged. 8 probe tasks left intact per "NO employee data cleanup" rule (operator may cancel via `/admin/tasks`). |
| HR portal `/hr/employees` page | Working. Save flow operational. | Unchanged. UX-only recommendations in `HR_EMPLOYEE_STATUS_UI_REVIEW.md §3`. |
| Phase Alpha closures (G-1..G-5) | Live in preview | Unchanged. HR canonical status endpoint is EXPLICITLY preserved (Alpha 422 error message points to it as the "use instead"). |
| HR Queue (`/hr/employee-requests`) | Working. Pending=13 · approved=8 · rejected=8. | Unchanged. Queue is for INBOUND requests from Operations/public/FL Termination Form — not a replacement for HR's direct lifecycle authority. |
| Audit / history chain | `status_history[]` append-only · employee_lifecycle_events for queue-approval path | Unchanged. Both probe events (Active→Resigned, Resigned→Active) recorded in history; forensic chain preserved. |

---

## 3 · Phase Alpha re-confirmation

The pending Employee Governance Phase Alpha deploy:

* **Does NOT block** `POST /api/hr/employees/{id}/status` (HR-authority direct mutation).
* **Does NOT block** `POST /api/hr/employees/{id}/reactivate` (HR-authority restoration).
* **Does NOT replace** the HR direct-edit drawer.

It closes 5 separate back-doors (G-1 public · G-2 Operations · G-3 admin direct · G-4 PUT back-door · G-5 destructive upload) and exposes a new HR-only **inbound request queue** at `/hr/employee-requests` for submissions originating outside the HR portal.

**HR's daily workflow on `/hr/employees` is unchanged by Alpha.** After deploy:

* HR continues to manage employee lifecycle the same way: roster → row → drawer → Status tab → dropdown → "Update status".
* HR additionally gains a queue review surface for requests originated by Operations / FL Termination forms / public field forms.

---

## 4 · Classification matrix (operator's 5 options)

| Option | Definition | Match? |
|---|---|---|
| **A** | Fixed by pending Employee Governance Alpha deploy | ❌ Alpha does not touch this path |
| **B** | **Existing behavior works but has bad UX / no confirmation** | ✅ **YES — confirmed** |
| **C** | Existing behavior does not persist | ❌ Persistence verified live |
| **D** | Existing behavior is intentionally blocked by Alpha and must be replaced with HR Queue / lifecycle transition | ❌ Alpha intentionally preserves this path |
| **E** | True blocker before deploy | ❌ Feature works |

# Final classification: 🟡 **B**

---

## 5 · Deploy authorization recommendation

# 🟢 **DEPLOY MAY PROCEED**

The pending production deploy (Employee Governance Phase Alpha + ITER453 + ITER452.5.2) is not affected by this audit. No code, data, permission, or configuration change is required before deploy.

Three optional UX hardening recommendations (REC-1, REC-2, REC-3 in `HR_EMPLOYEE_STATUS_UI_REVIEW.md §3`) totaling ≤ 25 LOC are deferred to a future operator-authorized polish iter (e.g., `iter454.x_hr_status_ux_polish`).

---

## 6 · Recommended communication to HR

If the HR Manager's perception report is escalated, a concise reply is:

> Your status changes ARE being saved. The save button is on the **Status tab** of the employee drawer (the second tab — you may currently be looking on the Details tab). The button is labelled **"Update status"** — clicking it persists the change, fires a success toast, and refreshes the status-history list below the button.
>
> The platform uses **"Resigned"** for voluntary self-quits — there is no separate "Quit" label. If you intend "Employee quit on his own", pick **Resigned** + **Voluntary** in the separation-type dropdown.
>
> We've verified the save flow end-to-end with your HR account. Backend confirms 200 OK · employee record updated · 8 offboarding follow-up tasks created · audit history written. Your work is not wasted; the persistence is real.
>
> We will optionally rename the button to "Save status change", auto-open the drawer on the Status tab when you click the status badge, and add an inline help panel clarifying the Quit→Resigned vocabulary. Those changes are queued for your authorization (each is one-line-to-twelve-line scope).

---

## 7 · Audit residual disclosure

Per the rule "NO employee data cleanup", the following residuals from the operator-objective-9 persistence probe remain in the preview database:

* Employee `Alec Perkins` (`c9d7ebc3-a292-4d7a-8765-0ce2739c6029`) has 2 entries in `status_history[]` (Active→Resigned probe + Resigned→Active reverse). Current state is Active. Forensic chain preserved.
* 8 offboarding tasks in `db.tasks` linked to that employee + the probe event. Task IDs are logged in `HR_EMPLOYEE_LIFECYCLE_SAVE_AUDIT.md §4.3`.
* `separation_type=voluntary` and `rehire_eligibility=eligible` remain on the employee record (these are immutable lifecycle-stamp fields kept across reactivations by design).

The operator may cancel the 8 probe tasks via `/admin/tasks` if desired. The status-history entries are append-only and cannot be removed without violating audit doctrine — they remain as evidence of the probe.

🛑 **STOPPED. Read-only audit complete + one operator-authorized persistence probe performed and reversed. No code changes. No deploy hold required.**
