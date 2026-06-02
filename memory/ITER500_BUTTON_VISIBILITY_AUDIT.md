# ITER500 · BUTTON VISIBILITY AUDIT

**Date**: 2026-06-02T19:30 UTC
**Mode**: READ-ONLY · static code-path scan

---

## High-risk action patterns flagged

These patterns repeat across 147 frontend pages. Each is a candidate for the same class of failure that the iter453.7 / .9 cycles addressed for HR.

| Risk pattern | Where (sample) | Risk class |
|---|---|:-:|
| Save button inline at end of scrollable form (no sticky footer) | `NewIncident.jsx`, `NewDailyReport.jsx`, `NewQaqcInspection.jsx`, `NewInspection.jsx`, `NewSafetyEquipmentIssuance.jsx`, `NewSafetyEquipmentTraining.jsx` | 🟡 Below-fold on 1366×768 / mobile (same class as iter453.7 was) |
| Approve / Reject inline in dropdown menu (no fixed CTA) | Dispatch board · PO requests · Constraints | 🟡 Discoverability |
| Lifecycle "Reopen" hidden behind kebab/three-dot menu | Incidents detail · QA/QC detail · Site Inspection detail | 🟡 Action-recoverability |
| "Submit" + "Save Draft" both present without clear primary | Daily report (post-iter450 split) · PO request flow | 🟡 Decision confusion |
| Disabled state without tooltip explaining why | Multiple admin governance pages | 🟡 Dead-button perception |
| Off-screen button on long admin list views | `AdminGuide.jsx`, `AdminLegacyImports.jsx` | 🟡 |
| Action wired but no `data-testid` (untestable) | ~ 18 pages (sample: `FleetVisibility.jsx`, `DispatchBoard.jsx`) | 🟡 Test coverage gap (not user-facing but blocks regression coverage) |
| Missing button entirely for stated workflow | OC-005 JHP acknowledgement page (planned, not built) | 🔴 |

---

## Confirmed-fixed since this fork started

| Issue | Fix iter | Status |
|---|:-:|:-:|
| HR Lifecycle Save below fold on laptop / iPad / mobile | iter453.7 | 🟢 Live on `main.efa7307f.js` |
| HR Save sparse-feedback / "nothing happened" | iter453.9 | 🟢 Live on production |
| Resend webhook silently accepting unsigned input | iter453.8 | 🟢 Live (operator set env + cycled backend) |

---

## Recommended button-visibility template (for any future fix)

The iter453.7 + iter453.9 combination is the **canonical template** for any "Save below fold + nothing-happens" defect class anywhere else on the platform:

1. Move the primary action into a **sticky footer** outside the scrollable form region.
2. Emit a **6 s toast with explicit OLD → NEW state** ("Employee status changed · Active → Inactive").
3. **Auto-close** the parent drawer/modal after 400 ms.
4. Differentiate **noop** vs real save with distinct toast type.
5. Validation toasts prefixed `Required:` with 6 s duration.

Apply this template to: `NewIncident`, `NewDailyReport`, `NewQaqcInspection`, `NewInspection`, dispatch approval flows, payroll time-off, PO request approval.

---

## STOP
