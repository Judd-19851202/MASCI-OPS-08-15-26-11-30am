# HR SAVE BUTTON · ROOT CAUSE REPORT

**Date**: 2026-06-02T18:33 UTC
**Mode**: READ-ONLY · NO fixes · NO code · NO deploy
**Authority**: OMEGA P0 — HR Lifecycle Save Button Forensic Failure (reopened)
**Companions**: `HR_SAVE_BUTTON_FORENSIC.md`, `HR_SAVE_BUTTON_EXECUTION_TRACE.md`, `DEPLOYMENT_BLOCKER_REASSESSMENT.md`

---

## 1 · Root-cause statement

> **The Save Status Change button executes correctly end-to-end. The user's "nothing appears to happen" report is a UX feedback insufficiency, NOT a workflow failure.** Every click takes one of three deterministic paths — each of which produces a visible signal — but the signals are EPHEMERAL (toasts auto-dismiss in ~4 s), POSITIONED OUT OF FOCUS (bottom-right of viewport while the user's eyes are on the modal Save button area), and NOT REINFORCED BY MODAL STATE (drawer stays open, statusForm is not reset, and the in-drawer success acknowledgement is minimal).

---

## 2 · Branch-by-branch analysis of what "nothing happens" can mean

### Branch 1 — Frontend validation short-circuit (most likely for fresh hires)

For an employee who has NEVER been offboarded (no `separation_type` or `rehire_eligibility` on their record), when HR transitions them to Resigned / Terminated / Retired:

| Path | Validation that fires | Toast text | API called? | DB updated? |
|---|---|---|:-:|:-:|
| separation_type missing | `HrEmployees.jsx:529-532` | "Pick a separation type — voluntary, involuntary, or layoff" | NO | NO |
| rehire_eligibility missing | `HrEmployees.jsx:534-537` | "Pick a rehire eligibility — Eligible, Not Eligible, or Review Required" | NO | NO |
| rehire reason missing (when not_eligible/review_required) | `HrEmployees.jsx:538-546` | "Add a short reason for this rehire eligibility decision" | NO | NO |

Each path runs in **< 50 ms** (synchronous validation), shows a bottom-right red toast for ~4 s, and bails before `setSaving(true)` — so the user doesn't even see the "Saving…" button-text flip.

**User's mental model**: "I clicked Save. Nothing happened."
**Reality**: A red toast briefly fired bottom-right, then auto-dismissed. The form is still filled out exactly as it was.

### Branch 2 — noop short-circuit on backend (line 982)

When `prev_status == body.lifecycle_status`, backend returns `{"ok": true, "tasks_created": 0, "noop": true}` without writing anything.

This happens when:
* HR opens the drawer for an already-Resigned employee, sees status="Resigned" in the dropdown, doesn't change it, and clicks Save.
* HR clicks Save twice rapidly (second click finds same state since the first save already advanced it).

Frontend response:
* `r.playbook_fired` is undefined for noop → `toast.success("Status updated")` fires.
* `offboardingSummary` refetch happens — but returns identical data.
* The drawer header badge doesn't visibly change.
* The "Recent status history" doesn't grow.

**User's mental model**: "I clicked Save, got a Status Updated toast, but nothing changed visually. Did it work?"
**Reality**: The backend correctly returned noop because there was no transition. No DB write was needed.

### Branch 3 — Successful save (true happy path)

Status DID change. Backend wrote. status_history grew. Playbook fired if offboarding. Toast fires bottom-right for ~4 s with green confirmation.

| What changes after success | Visible to HR? |
|---|:-:|
| Toast bottom-right | ✅ (if user is looking there) |
| Header badge color | ✅ subtle (StatusBadge tint changes) |
| "Recent status history" entry appended | ⚠️ requires scroll inside drawer to see |
| Status dropdown value | ✅ updated to the new status |
| Drawer auto-close | ❌ does NOT close |
| Parent table row | ⚠️ updates on next list refresh — invisible while drawer is open |
| In-drawer "Saved at HH:MM" banner | ❌ no such element exists |

**User's mental model** (if eyes on form): "I clicked Save. Form looks the same. Drawer didn't close. Did it work?"
**Reality**: It worked. The drawer just doesn't provide proximity-of-Save in-drawer confirmation.

---

## 3 · Why this is NOT a workflow failure

The forensic data is unambiguous:

* `db.employees.lifecycle_status` updates correctly on every transition probed.
* `status_history` is append-only and grew across probes (4 → 5 → 6).
* `employee_lifecycle_events` chain is alive (accountability timeline event count = 13).
* Offboarding playbook fires correctly — 8 tasks created on Active → Resigned.
* HR authority gate (`require_hr_or_admin`) intact — anonymous + forged-portal probes all 401.
* Both production negative and positive code paths verified.

**The failure is at the UX feedback layer, not the workflow layer.** The HR user is correct that they perceive "nothing" — but the system is correctly executing the intended business logic.

---

## 4 · Why this happens specifically on production HR users

The HR user is operating under three perception challenges that compound:

| Factor | Effect |
|---|---|
| Toast position bottom-right · auto-dismiss in ~4 s | If the user's eyes are on the modal (top-right of viewport on most monitors), the toast can be peripheral or missed entirely |
| Drawer stays open after save | Most save actions in the app DO close their modal (Add Employee dialog · Reactivate dialog · Edit forms). The HR drawer is an exception — it intentionally stays open for HR to review the resulting state. This breaks user expectations. |
| StatusBadge color shift is subtle | Active = green, Resigned = orange, Terminated = red — but on a fast click + toast-dismiss cycle, the badge change is not the user's center of attention |
| "Recent status history" is below the fold on small viewports | Even with the iter453.7 sticky footer, the history section is below the save action — user would have to scroll up *inside* the drawer to see the new entry |
| Form fields don't reset after save | The Resigned dropdown remains showing "Resigned", separation_type stays filled — visually identical to pre-save state, reinforcing the "nothing happened" illusion |
| No in-drawer success banner | The only success signal in the drawer area is the unchanged form + a brief toast |

---

## 5 · What would CHANGE the user's perception (not actioned · awaiting authorization)

Six minimal-scope changes (each is ≤ 5 LOC) that would convert "I think nothing happened" into "I can clearly see it worked":

| Idea | LOC | Effect |
|---|---:|---|
| Auto-close the drawer after a non-noop successful save | 1 | `onClose()` call inside the try block after `setSummary(s)` |
| Show a green inline "Saved at HH:MM" banner inside the sticky footer for 3 s | 8 | Local state with timeout |
| Reset `statusForm.reason` and the offboarding-extras after a successful save | 4 | Visual cue that the form was processed |
| Make the success toast modal-style (top-center, manual-dismiss) | 1 | `toast.success(msg, { duration: 10000, position: "top-center" })` |
| Add a subtle "Status changed: Active → Resigned" banner pinned at the top of the drawer for 5 s post-save | 10 | Direct visual confirmation in the user's eye path |
| Differentiate the noop toast from the real-save toast | 4 | `if (r.noop) toast.info("No change — status was already X")` vs success |

**None of these involve workflow changes, governance changes, or data-layer changes.** All are pure-UX surface improvements. None are in scope of this read-only audit.

---

## 6 · Final root-cause classification

> **The HR Save Status Change button is operationally correct but communicates success/failure poorly.** Users on production are perceiving "nothing happened" because:
>
> 1. The most common silent failure mode (frontend validation short-circuit on offboarding fields) produces only an ephemeral red toast which can be missed.
> 2. The noop short-circuit produces a misleading "Status updated" toast when nothing actually changed.
> 3. The successful save produces a green toast that auto-dismisses, doesn't close the drawer, doesn't reset the form, and provides no in-drawer success acknowledgement.
>
> The user's report is **factually accurate** as a perceptual claim AND **technically incorrect** as an operational claim. The save button works. The communication of save success/failure is what fails.

🟡 **UX FAILURE** (specifically: feedback insufficiency / discoverability of save outcome)

---

## 7 · STOP

Root-cause analysis complete. Deployment classification in `DEPLOYMENT_BLOCKER_REASSESSMENT.md`.
