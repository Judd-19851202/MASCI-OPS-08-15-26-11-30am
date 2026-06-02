# DEPLOYMENT BLOCKER ASSESSMENT — HR Lifecycle Save Path

**Date**: 2026-06-02
**Mode**: READ-ONLY.
**Companions**: `HR_LIFECYCLE_SAVEPATH_AUDIT.md`, `HR_LIFECYCLE_UI_FORENSICS.md`, `HR_LIFECYCLE_PERSISTENCE_TRACE.md`.

---

# 🟡 **FINAL CLASSIFICATION — UX DEFECT (not a deployment blocker)**

The Save action exists, is wired, is server-side authorized, and persists correctly to `db.employees + db.employee_lifecycle_events + db.tasks` with full audit trail. **The defect is purely visual reachability**: the button sits at the bottom of a scrollable form with no sticky footer, and on smaller viewports (laptop 1366×768, tablet, mobile + keyboard) it lands below the fold, making HR believe the action does not exist.

---

## 1 · Why this is NOT 🔴 a Deployment Blocker

| Criterion | Result |
|---|---|
| Does the feature work when invoked? | ✅ YES |
| Does data persist correctly? | ✅ YES |
| Are Phase Alpha protections intact? | ✅ YES (G-1..G-5 all live) |
| Is the action reachable AT ALL? | ✅ YES (by scrolling within the modal) |
| Does the deployed code expose a security defect? | ✅ NO |
| Does the deployed code expose a data-integrity defect? | ✅ NO |
| Does the deployed code expose a workflow-integrity defect? | ✅ NO |
| Production source_hash | `7a6c669f9e9212286e3850fae6a0b78e` (current target build) |

**No blocker conditions are met.** The deployed code is functionally correct. The operator's reported behaviour is reproducible only on specific viewport configurations and is resolvable with scroll.

## 2 · Why this IS 🟡 a UX Defect

| Criterion | Result |
|---|---|
| Does HR perceive the feature as missing? | 🔴 YES (per operator report) |
| Is the perception reproducible on common viewports? | 🔴 YES (laptop 1366×768, tablet, mobile + keyboard) |
| Does the perception lead to dropped writes? | 🔴 YES (HR closes drawer assuming auto-save, never clicks Save) |
| Is there a sticky-footer pattern that would fix this? | ✅ YES — standard shadcn `<SheetFooter className="sticky bottom-0">` |
| Estimated remediation scope | ≤ 15 LOC |
| Does this defect affect a P0 workflow? | ⚠️ YES — employee lifecycle is a constitutional Phase Alpha workflow |
| Severity of UX impact | MEDIUM — daily-use HR surface |
| Frequency of impact | HIGH — every employee separation/reactivation transition |

## 3 · Impact assessment per workflow

| Workflow | Affected? | Reason |
|---|---|---|
| Resigned transitions | 🔴 YES | Save below fold on small viewports |
| Terminated transitions | 🔴 YES | Same |
| Layoff transitions (Terminated + separation_type=layoff) | 🔴 YES | Same |
| Inactive transitions | 🟡 marginal | Form is shorter (no separation section) — usually visible |
| Leave of Absence transitions | 🟡 marginal | Form has 2 extra date fields but smaller than separation section |
| Rehire (via Reactivate button) | ✅ NO | Reactivation path uses a different button at a different code location (not audited here) |

## 4 · Compared to the prior ITER453.5 batch

ITER453.5 shipped **3 hardening recommendations** (REC-1, REC-2, REC-3) all of which addressed the operator's previous P0 confusion report. Each is verified live in production today:

* ✅ **REC-1** (button verb) — "Save Status Change" is the canonical label (verified in prod bundle).
* ✅ **REC-2** (badge click) — clicking the status badge opens drawer directly on Status tab (verified in prod bundle).
* ✅ **REC-3** (vocabulary HelpTip) — Employee Lifecycle Guide is present (verified in prod bundle).

The remaining issue surfaced now is **a fourth, distinct UX gap that ITER453.5 did NOT cover**: action reachability via sticky footer.

## 5 · Compared to the OMEGA Pre-Deploy 🟢 GO verdict

The current production deploy was certified 🟢 GO on the basis of:
* Phase Alpha closures verified live
* ITER453 lifecycle endpoints verified live
* ITER453.5 UX strings verified in bundle
* 50/50 pytest pass

**This UX defect did not surface in those probes because the defect is viewport-dependent and bundle-string verification does not catch it.** It would surface only via:
* Visual end-to-end testing on multiple viewport sizes
* User-acceptance testing with real HR staff
* Operator field report (which is what triggered this audit)

This is a known limitation of bundle-string + endpoint probes. It does not invalidate the prior 🟢 verdict; it surfaces a new finding requiring a targeted polish iter.

## 6 · Recommended remediation (NOT actioned · operator authorization required)

A future targeted polish iter (e.g., `iter453.7` or `iter454.x_hr_status_sticky_footer`) could:

### REC-4 · Sticky footer Save action (≤ 15 LOC)

* Refactor the Status tab's bottom section: extract the Save button (line 940) + Recent status history (line 944-959) so that the **Save button moves into a sticky `<div className="sticky bottom-0 bg-white border-t -mx-5 -mb-4 px-5 py-3 z-10">`** pinned to the bottom of the scrollable area.
* The Recent status history stays inline above the sticky region.
* No backend change.
* No new data-testid required (`hremp-status-save` is preserved).

Optional secondary additions:

* **Keyboard shortcut**: Cmd/Ctrl+S calls `submitStatusChange()` (≤ 5 LOC, attach via `useEffect` listener).
* **Form-wide `<form onSubmit>`**: wrap the status section in `<form onSubmit={(e)=>{e.preventDefault();submitStatusChange();}}>` so Enter in any input triggers Save. (≤ 5 LOC)

Total polish: ≤ 25 LOC for a complete fix.

## 7 · Operator action options

| Option | Effort | Effect |
|---|---|---|
| (a) Authorize iter453.7 sticky-footer polish (≤ 25 LOC) | next deploy cycle | Closes the defect for all viewports |
| (b) Issue an in-app announcement banner to HR explaining "scroll down within the modal to find Save Status Change" | ≤ 10 LOC | Workaround only — doesn't fix root cause |
| (c) Leave as-is (defer to a later iter) | 0 LOC now | HR continues to perceive missing Save; dropped writes possible |
| (d) Combine (a) + a one-line HR comms about the new sticky footer | preferred | Closes defect + preempts confusion |

## 8 · STOP

Audit complete. No code, no fixes, no deploy. READ-ONLY directive honored.

# 🟡 **FINAL CLASSIFICATION — UX DEFECT**

* Save action exists and persists correctly.
* Below-fold reachability on laptop/tablet/mobile + keyboard is the root cause of HR's perception.
* No deployment blocker. No defect in data path. Phase Alpha intact.
* Recommended fix: REC-4 sticky-footer pattern (≤ 15 LOC, awaiting operator authorization).
