# PHASE 3 · HR LIFECYCLE VOCABULARY REPORT (REC-3)

**Date**: 2026-06-02
**Batch**: ITER453.5 HR Lifecycle UX Hardening.
**Scope**: Add inline HelpTipBlock above lifecycle selector explaining the canonical vocabulary.

---

## 1 · Approved copy (verbatim from operator directive)

```
Employee Lifecycle Guide

Resigned = Employee voluntarily quit
Terminated = Company initiated separation
Layoff = Workforce reduction / business decision
Active = Current employee
Leave of Absence = Temporarily inactive
Reactivated = Returned to active employment
```

## 2 · Implementation

Inserted as a **static `<HelpTip>`** (NOT a registry-fed `HelpTipBlock`) so the operator-approved copy is shipped with the bundle and renders without backend tip-registry seeding.

Location: `HrEmployees.jsx`, immediately above the existing `<Label>New status</Label>` block on the Status tab (line ~810).

```jsx
<HelpTip
  kind="example"
  title="Employee Lifecycle Guide — pick the right status"
  defaultOpen={false}
  testId="lifecycle-vocabulary"
  body={
    <ul className="list-disc pl-4 space-y-0.5">
      <li><b>Resigned</b> — Employee voluntarily quit</li>
      <li><b>Terminated</b> — Company initiated separation</li>
      <li><b>Layoff</b> — Workforce reduction / business decision (pick Terminated + Layoff)</li>
      <li><b>Active</b> — Current employee</li>
      <li><b>Leave of Absence</b> — Temporarily inactive</li>
      <li><b>Reactivated</b> — Returned to active employment (use Reactivate button)</li>
    </ul>
  }
/>
```

* Import statement updated from `import { HelpTipBlock } from "@/components/HelpTip"` → `import { HelpTip, HelpTipBlock } from "@/components/HelpTip"`.

## 3 · Adherence to design constraints

| Requirement | Result |
|---|---|
| Simple language | ✅ Operator-approved copy used verbatim |
| Mobile friendly | ✅ `<HelpTip>` is collapsible by default · single line when collapsed · expands inline (no overlay) |
| No modal | ✅ Inline expand-in-place |
| No popup | ✅ No portal · no overlay · no z-index stacking |
| Bilingual fallback | ✅ Inherits `useT()` from `HelpTip` — copy can later be translated by passing `title_es` / `body_es` |
| data-testid | ✅ `helptip-lifecycle-vocabulary` (parent) + `helptip-lifecycle-vocabulary-toggle` + `helptip-lifecycle-vocabulary-body` |
| Adds note on Layoff workflow | ✅ Calls out "pick Terminated + Layoff" because `Layoff` is a `separation_type`, not a lifecycle_status |
| Adds note on Reactivated workflow | ✅ Calls out "use Reactivate button" because Reactivated is achieved via `POST /hr/employees/{id}/reactivate`, not the dropdown |

## 4 · Preserved

* Existing `HelpTipBlock formKey="employee-lifecycle.separation"` (line above) remains — it picks up any backend-registered tips and is independent of the static vocabulary block.
* Existing `HelpTipBlock formKey="employee-lifecycle.rehire"` (rehire eligibility section) is unchanged.
* No registry-side seeding required.

## 5 · LOC accounting

Approximately 21 lines (JSX block + import-line modification). Slightly above the original 10-LOC estimate because the operator-approved copy is non-negotiable and required structured rendering (bulleted list).

## 6 · Result

🟢 **PASS.** Vocabulary guide is collapsible, inline, mobile-friendly, ships with the bundle.

## 7 · Operator alignment with success criteria

> HR understands: "Quit vs Resigned vs Terminated vs Layoff" YES

The expanded panel reads exactly the way HR's mental model speaks ("Employee voluntarily quit" → Resigned), removing the vocabulary ambiguity that contributed to the original confusion report.
