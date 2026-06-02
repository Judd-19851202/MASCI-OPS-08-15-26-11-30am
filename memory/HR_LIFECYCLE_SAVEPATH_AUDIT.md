# HR LIFECYCLE · SAVE PATH FORENSIC AUDIT

**Date**: 2026-06-02
**Authority**: OMEGA DIRECTIVE · P0 read-only audit.
**Mode**: READ-ONLY. No code, no fixes, no deploys.
**Companions**: `HR_LIFECYCLE_UI_FORENSICS.md`, `HR_LIFECYCLE_PERSISTENCE_TRACE.md`, `DEPLOYMENT_BLOCKER_ASSESSMENT.md`.

---

## 1 · Operator-reported evidence

> "Employee Lifecycle modal allows status changes and separation information entry but presents no visible Save/Submit/Update action."

---

## 2 · Surface identification

* **Page**: `frontend/src/pages/HrEmployees.jsx` (1 176 LOC, line counts post-ITER453.5).
* **Component**: `EmployeeDrawer` (line 476).
* **Shell**: Shadcn `<Sheet>` with `<SheetContent side="right" className="w-full sm:max-w-xl p-0 flex flex-col">` (line 610).
* **Tab strip**: `Details · Status · Offboarding Summary` (lines 631-636).
* **Scroll container**: `<div className="flex-1 overflow-y-auto px-5 py-4 text-sm">` (line 637) — this IS the scrollable region.
* **Save trigger**: line **940** —
  ```jsx
  <Button onClick={submitStatusChange} disabled={saving} data-testid="hremp-status-save">
    {saving ? "Saving…" : "Save Status Change"}
  </Button>
  ```

## 3 · Inventory of every possible completion path

| Mechanism | Present? | Location | Verdict |
|---|---|---|---|
| **Save button** | ✅ YES | line 940 (`data-testid="hremp-status-save"`) | EXISTS |
| Submit button | ❌ no separate Submit | — | n/a (Save is the only commit action) |
| Update button | ❌ — legacy "Update status" was replaced by "Save Status Change" in ITER453.5 REC-1 | — | n/a |
| Confirm button | ❌ no confirm modal | — | n/a |
| **Sticky footer actions** | 🔴 **NOT PRESENT** — Save button is inline at the bottom of the scrollable form, NOT in a sticky footer | line 940 | **🔴 ABSENT** |
| Hidden actions | ❌ none | — | n/a |
| Keyboard-triggered actions | ⚠️ Enter on inputs does NOT submit; no `<form onSubmit>` wrapper around the lifecycle fields | — | NOT IMPLEMENTED |

## 4 · Modal scroll behaviour

The `<SheetContent>` is a flex-column with header (fixed top) → tabs strip (fixed) → scrollable inner content.

* `<SheetContent className="w-full sm:max-w-xl p-0 flex flex-col">` — full height of the viewport, column layout.
* `<SheetHeader className="px-5 pt-5 pb-3 border-b">` — fixed top region.
* `<Tabs className="flex-1 flex flex-col">` — takes remaining flex space.
* `<TabsList className="rounded-none border-b">` — fixed below header.
* `<div className="flex-1 overflow-y-auto px-5 py-4 text-sm">` — scrollable region (lines 637+).
* Inside this scroll region, `<TabsContent value="status" className="mt-0 space-y-3">` contains EVERY status-tab element including the Save button at line 940 and the recent-history list at line 944.

**The Save button scrolls WITH the form content.** It is NOT pinned to the visible area.

## 5 · Element ordering inside Status tab (top → bottom)

| Order | Element | Conditional? | Approx vertical height |
|---:|---|---|---:|
| 1 | `HelpTipBlock formKey="employee-lifecycle.separation"` | always | 1-3 rows |
| 2 | `HelpTip` "Employee Lifecycle Guide" (REC-3 · collapsed by default) | always | 1 row collapsed · 7 rows expanded |
| 3 | `<Label>New status</Label>` + dropdown | always | 2 rows |
| 4 | Separation Type dropdown | only if lifecycle ∈ {Terminated, Resigned, Retired} | 2 rows |
| 5 | Last Day Worked + Termination Date (sm:grid-cols-2) | same condition | 2 rows |
| 6 | Rehire Eligibility dropdown | same condition | 2 rows |
| 7 | Rehire Eligibility Reason (textarea, 2 rows) | only if rehire ∈ {not_eligible, review_required} | 3-4 rows |
| 8 | Leave Start Date + Expected Return Date | only if lifecycle = Leave of Absence | 2 rows |
| 9 | Reason / note (textarea, 3 rows) | always | 4 rows |
| 10 | Offboarding playbook warning (amber callout) | only on Terminated/Resigned/Retired *fresh* transition | 3 rows |
| 11 | **🔴 Save Status Change button** | always | 1 row |
| 12 | Recent status history list (last 5) | only when `last_status_change` exists | 1-5 rows |

When **Resigned** is selected (the operator's named scenario):

Total ≈ rows 1-3 (2-4) + rows 4-7 (8-10) + row 9 (4) + row 10 (3) + row 11 (1) = **~18-22 vertical rows** above and including the Save button.

## 6 · Viewport behaviour analysis

The `<SheetContent>` claims full viewport height. Subtracting:

| Region | Pixels (estimate) |
|---|---:|
| `SheetHeader` (title + role chip + Accountability link) | ~110 px |
| `TabsList` (3 tabs) | ~40 px |
| **Available for scrollable inner content** | viewport_height − ~150 px |

| Viewport | viewport_height | available_scroll | ~rows visible | Save button visible without scroll? |
|---|---:|---:|---:|---|
| Desktop 1920 × 1200 | 1200 | ~1050 | ~30 | ✅ Visible (form ≤ 22 rows fits) |
| Desktop 1920 × 1080 | 1080 | ~930 | ~26 | ✅ Visible (form ≤ 22 rows fits) |
| Laptop 1366 × 768 | 768 | ~620 | ~17 | 🔴 **HIDDEN below fold** when Resigned + rehire=not_eligible (form ~22 rows) |
| Tablet 1024 × 768 | 768 | ~620 | ~17 | 🔴 **HIDDEN below fold** for same scenario |
| Tablet 768 × 1024 (portrait) | 1024 | ~870 | ~24 | ⚠️ Marginal — visible if no scroll-padding, but tight |
| Mobile 414 × 896 (iPhone) | 896 | ~750 | ~21 | 🟡 **Marginal** — typically requires 1 scroll-touch to reveal |
| Mobile + on-screen keyboard | (896 − ~330 = 566) | ~420 | ~12 | 🔴 **HIDDEN** when any text field has focus |

## 7 · Off-screen / hidden / clipped audit

| Mechanism | Result |
|---|---|
| `display: none` on Save button | ❌ none |
| `visibility: hidden` | ❌ none |
| `opacity: 0` | ❌ none |
| `position: absolute; left: -9999px` | ❌ none |
| Parent `overflow: hidden` that clips Save | ❌ none (parent is `overflow-y-auto`, scrolls) |
| Conditional render that hides Save | ❌ Save renders unconditionally |
| z-index stacking | ❌ no overlay |
| `pointer-events: none` | ❌ none |
| **Below-fold by scroll position** | 🔴 **CONFIRMED** on laptop/tablet/mobile when separation section is expanded |
| Missing sticky-footer pattern | 🔴 **CONFIRMED** — the Save button is not pinned |

## 8 · Root cause

**The Save button exists, is wired correctly, and persists state when clicked. But on common operator viewports (laptop 1366×768, tablet, mobile + keyboard) the button sits BELOW THE FOLD inside a scrollable column that has no sticky footer.** HR's brain expects a sticky footer "Save / Cancel" pattern (every banking, CRM, and ATS app uses this) and gives up before scrolling further inside the modal.

Compounding factors:

1. The Reason / note textarea immediately precedes the Save button. When focused on textarea, the cursor draws attention there and the unscrolled fold sits below the textarea.
2. On mobile, the keyboard overlay covers ~330 px of vertical space, pushing the Save button out of the viewport entirely while the textarea is focused.
3. Browser autoscroll-on-focus moves the textarea into view but does NOT scroll further to expose the Save button.

## 9 · Compared to operator's evidence

| Operator claim | Verdict |
|---|---|
| "presents no visible Save/Submit/Update action" | 🟡 **PARTIALLY CONFIRMED** — Save action IS PRESENT in the DOM and is FUNCTIONAL, but is below the visible viewport on the affected resolutions. From the operator's perspective, "no visible" is accurate as a user-experience description. |
| Lifecycle changes do not persist? | ❌ **NOT CONFIRMED** — prior audits + this audit's persistence trace confirm full end-to-end save. The action just isn't reachable without scroll. |
| Hidden / missing entirely? | ❌ **NOT MISSING** — button is in the DOM, rendered, clickable, functional. |
| Conditional? | ❌ unconditional. |
| Off-screen by CSS? | ❌ off-screen by SCROLL position, not by CSS. |
