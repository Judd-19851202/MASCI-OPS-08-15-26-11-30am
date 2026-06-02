# HR LIFECYCLE · ROOT CAUSE REPORT

**Date**: 2026-06-02
**Authority**: OMEGA DIRECTIVE — P0 End-to-End Forensic Certification · Phase 8
**Mode**: READ-ONLY · NO code, NO fixes, NO deploy
**Companions**: `HR_LIFECYCLE_UI_FORENSICS.md`, `HR_LIFECYCLE_PERSISTENCE_TRACE.md`, `HR_LIFECYCLE_GOVERNANCE_CERTIFICATION.md`, `HR_LIFECYCLE_RESPONSIVE_CERTIFICATION.md`, `DEPLOYMENT_BLOCKER_ASSESSMENT.md`

---

## 1 · Operator's observation, restated precisely

> The Employee Lifecycle modal **allows data entry** (status dropdown, separation type, dates, rehire eligibility, reason) but **presents no obvious way to save, submit, confirm, or complete the action**.

**Restated as a falsifiable claim**: "The save action is missing OR unreachable OR non-functional."

---

## 2 · Falsification trace

| Sub-claim | Test | Result |
|---|---|:-:|
| Save action is missing from the DOM | grep `HrEmployees.jsx` for `hremp-status-save` testid → found at **line 940** | **❌ FALSIFIED** |
| Save action is hidden by CSS | inspected computed styles (display, visibility, opacity, position, z-index, pointer-events) | **❌ FALSIFIED** |
| Save action is conditionally rendered | tracked the conditional gates — Save renders unconditionally inside `<TabsContent value="status">` | **❌ FALSIFIED** |
| Save action is disabled | `disabled={saving}` only — `saving=false` in idle state | **❌ FALSIFIED** |
| Save action is wired to a stub | `onClick={submitStatusChange}` → `axios.post('/api/hr/employees/{id}/status', body)` → real handler in `employee_lifecycle.py:968` | **❌ FALSIFIED** |
| Save action does not persist | live HR-token probe (prior audits) confirmed `db.employees`, `status_history[]`, `employee_lifecycle_events`, `tasks` all written | **❌ FALSIFIED** |
| Save action is below the scroll fold on common operator viewports | viewport math (see `HR_LIFECYCLE_RESPONSIVE_CERTIFICATION.md §3`) confirms 60-70% device-class failure | **✅ CONFIRMED** |
| Save action is inaccessible during text entry on mobile/tablet | on-screen keyboard pushes the button out of viewport; auto-scroll-into-view doesn't compensate | **✅ CONFIRMED** |

**Net**: The save action **exists, is wired, persists, audit-trails** — but is **physically out of view** for the majority of HR's device fleet during the precise step (`Reason / note` text entry) that immediately precedes the save.

---

## 3 · Exact location of defect

| Attribute | Value |
|---|---|
| **File** | `frontend/src/pages/HrEmployees.jsx` |
| **Component** | `EmployeeDrawer` (function at line 476) |
| **Sub-component** | Status `<TabsContent>` block (lines 825-960) |
| **Save Button** | Line **940-942** |
| **Scroll container** | `<div className="flex-1 overflow-y-auto px-5 py-4 text-sm">` line **637** |
| **Sheet shell** | `<SheetContent side="right" className="w-full sm:max-w-xl p-0 flex flex-col">` line **610** |

```jsx
// Line 940-942 (current production)
<Button onClick={submitStatusChange} disabled={saving} data-testid="hremp-status-save">
  {saving ? "Saving…" : "Save Status Change"}
</Button>
```

The button is correct. Its **position** within the scroll region is the defect.

---

## 4 · Failure mechanism — exact

1. Status form contents stack vertically inside `<div className="flex-1 overflow-y-auto px-5 py-4 text-sm">`.
2. The scrollable region sits below a fixed `<SheetHeader>` (~110 px) and `<TabsList>` (~40 px) — leaving `viewport_h − ~150 px` of usable scroll height.
3. The save button is the **second-to-last element** of the form (followed only by Recent Status History).
4. On laptop 1366×768 the form's full Resigned + Not Eligible variant measures ~830 px of content — exceeding the ~620 px scroll budget by ~210 px.
5. The Save button is therefore **~210 px below the fold** on the most common operator laptop class.
6. On mobile/tablet with on-screen keyboard active, the failure is amplified by ~300-360 px.
7. The Save button is **not pinned** — there is no `<SheetFooter className="sticky bottom-0">` wrapping it.
8. There is **no keyboard shortcut** (Enter, Ctrl+S) and **no `<form onSubmit>`** wrapper to provide a secondary submit path.
9. The operator's natural recovery pattern (close the drawer expecting auto-save) results in **silent dropped writes** because there is no auto-save on drawer close.

---

## 5 · Classification

| Dimension | Classification |
|---|---|
| UI Defect | ✅ YES (form-action placement / no sticky footer) |
| Workflow Defect | ❌ NO (the workflow completes correctly when invoked) |
| Persistence Defect | ❌ NO (writes persist correctly to all 4 audit surfaces) |
| Governance Defect | ❌ NO (HR-only authority gate intact; G-1..G-5 live) |
| API Defect | ❌ NO (route exists, validates, audit-trails) |
| Authentication Defect | ❌ NO (`require_hr_or_admin` gate verified) |
| Authorization Defect | ❌ NO (RBAC matrix correct) |
| Data-integrity Defect | ❌ NO (status_history append-only; lifecycle_events append-only) |
| Audit-trail Defect | ❌ NO (every transition emits `{at, by, from, to, reason}` + lifecycle event row) |
| **Deployment Blocker** | ❌ NO (deployed code is functionally correct; defect is reachability, not correctness) |

🟡 **Net classification: UX DEFECT (sub-category: form-action discoverability / responsive reachability)**

---

## 6 · Remediation envelope (NOT actioned · authorization required)

### 6.1 · Minimal fix — Sticky footer (≤ 15 LOC)

In `HrEmployees.jsx::EmployeeDrawer`, around line 940, wrap the Save button + a Cancel-equivalent close action in a sticky footer pinned to the bottom of the scrollable area:

```jsx
{/* INSIDE <TabsContent value="status">, replacing the inline button at line 940 */}
<div className="sticky bottom-0 -mx-5 -mb-4 px-5 py-3 bg-white border-t border-slate-200 z-10
                flex items-center justify-between gap-2">
  <div className="text-[10px] font-mono uppercase tracking-wider text-slate-500">
    {saving ? "Persisting status change…" : "Status change is committed on Save"}
  </div>
  <Button onClick={submitStatusChange} disabled={saving} data-testid="hremp-status-save">
    {saving ? "Saving…" : "Save Status Change"}
  </Button>
</div>
```

* Preserves existing `data-testid="hremp-status-save"` → no test breakage.
* Sticky inside the scroll region (`overflow-y-auto` parent) keeps the footer pinned without absolute positioning.
* Negative margins reverse the parent's `px-5 py-4` to make the footer span full width.
* `z-10` ensures the sticky footer overlays the textarea cursor when typing.

### 6.2 · Secondary polish (≤ 10 LOC)

| Item | LOC | Effect |
|---|---:|---|
| Wrap the status section in `<form onSubmit={(e)=>{e.preventDefault();submitStatusChange();}}>` | 2 | Enter on inputs commits (matches Add Employee dialog convention) |
| `useEffect` keyboard listener for Cmd/Ctrl+S → `submitStatusChange()` | 6 | Power-user shortcut |
| Reactivate dialog's `<DialogFooter>` already pins its buttons — pattern parity with that flow | 0 (just align) | Visual consistency |

### 6.3 · Risk assessment

| Risk | Level | Mitigation |
|---|:-:|---|
| Layout regression on Reactivate flow | LOW | Reactivate uses `<Dialog>` not `<Sheet>` — separate code path |
| Layout regression on Add Employee dialog | LOW | Add uses `<Dialog>` — already has `<DialogFooter>` |
| Layout regression on Details tab | LOW | Details tab has no Save button — `EditField` saves inline |
| Layout regression on Offboarding Summary tab | LOW | Read-only — no Save button |
| Test breakage | LOW | `hremp-status-save` preserved; no API change |
| Mobile keyboard interaction edge case | LOW | Sticky footer rides above the keyboard on iOS Safari by virtue of `overflow-y-auto` parent |
| Translation overflow | LOW | i18n strings already short ("Save Status Change") |

### 6.4 · Estimated effort

| Item | Effort |
|---|---|
| LOC to fix | **≤ 15 LOC** (sticky-footer pattern) |
| Files touched | **1** (`HrEmployees.jsx`) |
| Backend changes | **0** |
| DB migrations | **0** |
| New tests | **1 frontend Playwright** (verify Save button visible at 1366×768 without scroll) |
| Rollback complexity | **TRIVIAL** — single-component frontend change |
| Affected workflows | Status change form ONLY (Resigned, Terminated, Laid Off, Inactive, Leave of Absence, Suspended, Active reactivation NOT affected — separate flow) |

---

## 7 · Failure-chain summary

```
[Operator picks Resigned]
   → form expands (~830 px)
   → Save button sits at offset ~778 px
   → Laptop 1366×768 scroll budget ≈ 618 px
   → Save lands ~210 px below fold
   → Operator focuses Reason textarea
   → Keyboard appears (mobile/tablet) · viewport shrinks further
   → Operator types reason
   → Operator dismisses keyboard
   → Operator looks for Save · sees Reason textarea + amber playbook warning
   → Operator does NOT scroll within the modal (no visual scroll affordance)
   → Operator taps the close X
   → NO save call · NO toast · NO write
   → Lifecycle remains Active
   → Operator reports "no Save button"
```

This is the **specific, falsifiable, reproducible failure chain** identified by this audit.

---

## 8 · Final root-cause statement

> **The HR Employee Lifecycle save action exists, is correctly wired, server-authorized, and persists end-to-end with full audit trail. It fails operationally because it is positioned inline at the end of a scrollable form with no sticky footer, placing it below the viewport fold on ~60-70% of HR's device fleet — and below the on-screen keyboard during the immediately-preceding text-entry step. The defect is reachability, not correctness.**

🟡 **CLASSIFICATION: UX DEFECT — recommended polish iter `iter453.7_hr_status_sticky_footer` (≤ 15 LOC)**

---

## 9 · STOP

Root-cause phase complete. READ-ONLY directive honored. No code, no fixes, no deploy.
