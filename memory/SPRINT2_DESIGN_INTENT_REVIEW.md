# SPRINT 2 · DESIGN-INTENT REVIEW

**Date**: 2026-06-02T21:55 UTC
**Authority**: OMEGA AUTHORIZATION — Sprint 2 Design-Intent Review (pre-implementation gate)
**Mode**: READ-ONLY · direct source inspection · STOP after this doc until operator approves the revised scope

---

## Headline finding · Sprint 2's premise is ALSO partially stale

Same pattern as Sprint 1: I verified each Approve/Reject surface by reading the actual JSX, not the audit register. The audit register is the **hypothesis**; the codebase is the **truth**.

| Target surface | Audit claim | Actual state |
|---|---|---|
| **PO Requests** | "Approve / Reject under dropdown menu on PO requests" | ❌ **Stale.** `PoRequests.jsx:715-747` renders Approve / Clarify / Reject as **top-level color-coded buttons** in a dedicated `po-approval-block` panel inside a side `Sheet`. CheckCircle2 / MessageSquare / XCircle icons. Explicit test ids `po-approve-btn`, `po-clarify-btn`, `po-reject-btn`. Notes textarea required. Capability-gated. |
| **Dispatch (AdminDispatch transfers + holds)** | "Approve / Reject under dropdown menu on Dispatch" | ❌ **Stale.** `admin/AdminDispatch.jsx:320-326` renders Approve as a top-level outline button with CheckCircle2 icon per row. `admin/AdminDispatch.jsx:515` renders pending-hold Approve as a top-level emerald button. Confirmation dialog ("Approve this pending hold? The asset will be marked Maintenance/Safety Hold immediately."). Test ids `dp-xfer-approve-${id}`, `dp-pending-approve-${id}`. |
| **Time-Off (HrTimeOff)** | "Time-off approval as checkbox not verb" (ITER500 DISCOVERABILITY #17) | ❌ **Stale.** `HrTimeOff.jsx:321-337` renders Approve / Deny / Need-Info as **three large color-coded buttons** (emerald · red · orange) with icons inside the HR Decision dialog. Test ids `time-off-decide-approved`, `time-off-decide-denied`, `time-off-decide-need_info`. Pay-Code field + notes field below. |
| **HR Employee Requests Queue** | n/a (implied by ITER501 #12) | ❌ **Already compliant.** `HrEmployeeRequestsQueue.jsx:334-337` renders top-level Approve button with CheckCircle2 icon, test id `hr-requests-approve-${id}`. Reject button with 5+ char reason requirement at L178-200. |
| **Asset Transfers (Receive)** | "Asset-transfer receive as checkbox not verb" (DISCOVERABILITY #18) | ❌ **Stale.** `AssetTransfers.jsx:48-49` declares Approve / Reject as state-action objects with icon (CheckCircle2 / XCircle) and `needsReason: true` for reject. The state-machine action map is the platform's standard verb pattern, not a checkbox. |

**Zero files** in `/app/frontend/src/pages/` contain a `DropdownMenuItem` referencing approve/reject (verified by grep). The audit's "Approve/Reject hidden in dropdowns" finding does not match the current codebase.

---

## Per-question answers (the 8 design-intent questions)

### Q1 · Is current action placement intentional?

**Yes.** Every Approve/Reject surface I read uses the same intentional pattern: a contextual action panel (block / dialog / sheet) that opens when the operator focuses a record, with the verb buttons rendered as top-level color-coded primary actions (emerald/red/orange) with icons, test ids, and reason-required modals where the action has irreversible consequences. This pattern is consistent across PO, Dispatch transfers, Dispatch holds, Time-Off, HR Queue, and Asset Transfers.

### Q2 · Are approval actions hidden?

**No.** None of the surfaces I read hide Approve or Reject behind a kebab, a "more" menu, or a row-action dropdown. They live in clearly-labeled action panels (e.g., `po-approval-block`) or dialogs (`HR Decision`) that the operator opens deliberately.

### Q3 · Are approval actions difficult to discover?

**No, for the listed surfaces.** The discovery path is: open record → action panel/dialog reveals → primary buttons visible. This is the textbook "explicit-action" pattern from the design-guidelines doc and matches the iter453.7 + ITER500-Rank #1 sticky-footer doctrine.

### Q4 · Are users likely to miss them?

**Unlikely.** The buttons are:
* Large (h-10 / sm-button sizing)
* Color-coded (emerald=approve · red=reject · orange/blue=intermediate)
* Icon-prefixed (CheckCircle2 / XCircle / etc.)
* Labeled in plain verbs ("Approve" / "Reject" / "Deny" / "Need Info" / "Clarify")
* Capability-gated (so approvers see them and non-approvers do not — eliminating decoy confusion)

### Q5 · Does current placement create support calls?

**No evidence in this codebase.** The support-call risk would be high if approve/reject were behind a kebab AND non-approvers saw them with a permission error — but the capability gate (`caps["po.approve"]`, `caps["po.reject"]`, etc.) means non-approvers don't see the buttons at all. Approvers see all buttons inline. The friction class "where's the button?" is structurally prevented.

### Q6 · Would promoting actions improve usability?

**No — they are already promoted.** Promoting further would either be redundant (duplicate buttons) or would force the action into the wrong context (e.g., putting Approve on the row itself before the record is reviewed could lead to accidental approvals).

### Q7 · Would promoting actions create accidental approvals?

**Yes, slightly.** If the Sprint 2 plan were to move Approve/Reject from the contextual panel to the row itself ("approve from the list without opening the record"), the action would be reachable before the operator has read the request. This is the inverse of the original concern: the **panel-anchored** pattern is doctrinally correct for irreversible decisions. Putting Approve buttons directly on row hover or in row-action menus would WEAKEN the discipline, not strengthen it.

### Q8 · What is the lowest-risk implementation pattern?

**Pattern A · No-op** — the surfaces are already at the design intent. Update the audit register and move on.

**Pattern B · Documentation-only** — Write a short doctrine note (`APPROVAL_BUTTON_DOCTRINE.md`) codifying the panel-anchored verb-button pattern so future devs don't accidentally "improve" it back into a dropdown. Zero code · ~ 30 min · prevents regression.

**Pattern C (NOT RECOMMENDED) · Add row-level quick-approve** — Would create the accidental-approval risk Q7 surfaces. Skip.

---

## Per-workflow classification

| Workflow | Classification |
|---|:-:|
| PO Requests · Approve / Clarify / Reject | 🟢 No Action Needed |
| Dispatch · transfer approval | 🟢 No Action Needed |
| Dispatch · pending-hold approval | 🟢 No Action Needed |
| Time-Off · HR Decision | 🟢 No Action Needed |
| HR Employee Requests Queue | 🟢 No Action Needed |
| Asset Transfers · approve/reject/receive | 🟢 No Action Needed |

**Six of six surfaces 🟢. Zero 🟡. Zero 🔴.**

---

## Sprint 2 verdict

# 🟢 **SPRINT 2 RETIRED BY PRIOR WORK**

Code change required: **0 lines**.
Optional one-off: Pattern B (doctrine note) · ~ 30 minutes · zero risk.
Time freed: ~ 1 week of planned engineering.

---

## Awaiting operator decision

Per the OMEGA directive: *"NO implementation. NO code changes. NO deploys."* I am stopping at the review.

Three honest options for the next sprint slot:

* **Option 1 · Move directly to a genuinely-still-valid item.** Based on this re-verification pass, candidates include: OC-005 JHP Acknowledgement Ledger (not built) · Universal undo (not built) · Sub/Vendor archive workflow (no backend `is_archived`) · verb harmonization (cosmetic platform-wide).
* **Option 2 · Authorize a Sprint 0 re-audit** — given that Sprint 1 AND Sprint 2 were both stale on first inspection, the audit register has drifted enough from reality that a 2–3 day source-direct re-audit would produce a clean register and prevent further wasted sprint-cycles. This is my most-honest recommendation.
* **Option 3 · Pick a different ITER501 sprint** (e.g., Sprint 3 Quick-Wins Sweep) — but with the same caveat: items may already be retired by prior work. Pre-validation required.

See `REVISED_ITER501_ROADMAP.md` for the updated picture.

STOP.
