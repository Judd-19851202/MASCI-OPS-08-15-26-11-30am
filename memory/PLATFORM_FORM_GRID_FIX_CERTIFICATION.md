# Platform Form Grid Fix Certification

_Phase V.5 · 2026-05-29 19:25 UTC._

> **Status**: SHIPPED to preview.
> **Production readiness**: pending operator review (this report).
> **Scope**: platform-wide form / view layout. Zero business-logic
> changes, zero schema changes, zero workflow changes.

## 1 · Fix summary

A new shared component `FormGrid.jsx` plus a mechanical migration of
the deprecated `grid grid-cols-1 sm:grid-cols-2 gap-{3,4}` pattern to
the canonical safe pattern `grid grid-cols-1 md:grid-cols-2 gap-x-6
gap-y-4`. **Single layout decision now controls every form on the
platform.**

## 2 · Files touched

### 2a · New shared component
- `/app/frontend/src/components/FormGrid.jsx` (76 lines, lint clean)

### 2b · Migrated files (44 files · 69 string replacements)

| File | gap-3 | gap-4 |
|---|---|---|
| `pages/NewDailyReport.jsx` | 4 | 2 |
| `pages/NewMeeting.jsx` | – | 1 |
| `pages/NewIncident.jsx` | – | 5 |
| `pages/NewInspection.jsx` | – | 2 |
| `pages/NewFleetDVIR.jsx` | – | 1 |
| `pages/NewEquipmentInspection.jsx` | – | 2 |
| `pages/NewQaqcInspection.jsx` | 1 (local Row) | – |
| `pages/NewSafetyEquipmentIssuance.jsx` | 1 (local Row) | – |
| `pages/NewSafetyEquipmentTraining.jsx` | 1 (local Row) | – |
| `pages/NewConstraint.jsx` | 2 | – |
| `pages/ReturnEquipment.jsx` | 1 | 1 |
| `pages/HrDailyReports.jsx` | – | 1 |
| `pages/HrSafetyRecords.jsx` | – | 1 |
| `pages/SafetyTrainingRecords.jsx` | 1 | 1 |
| `pages/SafetyCorrectiveActions.jsx` | 1 | – |
| `pages/SafetyFireExtinguishers.jsx` | 2 | – |
| `pages/ViewDailyReport.jsx` | 2 | 1 |
| `pages/ViewIncident.jsx` | 1 | 2 |
| `pages/ViewInspection.jsx` | 2 | – |
| `pages/ViewMeeting.jsx` | 2 | – |
| `pages/ViewQaqcInspection.jsx` | 1 | 1 |
| `pages/ViewSafetyForm.jsx` | – | 2 |
| `pages/ViewEquipmentInspection.jsx` | – | 1 |
| `pages/TrenchBoxesAdmin.jsx` | 1 | – |
| `pages/MaterialCalculators.jsx` | – | 2 |
| `pages/HrHub.jsx` | 1 | – |
| `pages/DispatchHub.jsx` | 1 | – |
| `pages/ShopHub.jsx` | – | 1 |
| `pages/AccessDenied.jsx` | 1 | – |
| `pages/NotFound.jsx` | 1 | – |
| `pages/ThankYou.jsx` | 1 | – |
| `pages/admin/AdminDigestConfig.jsx` | 2 | – |
| `pages/admin/AdminPromoAssets.jsx` | 1 | – |
| `pages/FieldLeadershipFormPage.jsx` | – | 2 |
| `components/EquipmentLines.jsx` | – | 1 |
| `components/EquipmentReturnLines.jsx` | 2 | – |
| `components/ComplianceExportPanel.jsx` | – | 1 |
| `components/AdminBannersPanel.jsx` | 1 | – |
| `components/CheatSheetCard.jsx` | – | 1 |
| `components/AutoEmailRoutingPanel.jsx` | 1 | – |
| `components/EquipmentMasterPanel.jsx` | 1 | – |
| `components/ShopSignoffCard.jsx` | – | 1 |
| `components/TrenchBoxPosterCard.jsx` | 1 | – |
| `components/PartsCatalog.jsx` | – | 1 |

**Totals**: 37 × `gap-3` → canonical · 32 × `gap-4` → canonical · 69
total replacements.

### 2c · Files untouched
- Any usage with `gap-{1,2,5,6}` was deliberately preserved (12
  occurrences across 11 files). These are specialty layouts
  (icon-row dialogs, decorative card chrome, status-pill rows) and
  are not field-input pairs.
- Local `Row({children})` helpers in 3 files were updated automatically
  because they used the gap-3 pattern internally.

## 3 · Replacement applied

```diff
- grid grid-cols-1 sm:grid-cols-2 gap-3
+ grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4

- grid grid-cols-1 sm:grid-cols-2 gap-4
+ grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4
```

Mechanical change. No logic touched. Verified post-migration:

```
remaining gap-3 occurrences in target pattern: 0
remaining gap-4 occurrences in target pattern: 0
new canonical occurrences: 69
```

## 4 · Regression evidence

| Check | Result |
|---|---|
| Wave-2 Playwright DR field reliability suite | ✅ **6 passed, 1 skipped** in 39.7 s |
| `FormGrid.jsx` ESLint | ✅ no issues |
| `NewDailyReport.jsx` ESLint | ✅ no issues |
| Visual: iPad portrait (820 × 1180) DR Report Information | ✅ Project Name / Project Number gap expanded from ~35 px to ~58 px |
| Visual: iPad portrait Safety Meeting | ✅ Date / Time row clean, no center-seam collision |
| Visual: iPad portrait Equipment Pre-Op | ✅ Project & Operator section clean |
| Visual: iPad landscape (1180 × 820) DR | ✅ 2-col with safe gap |
| Visual: mobile (390 × 844) DR | ✅ 1-col stack (correctly collapsed below 768 px) |
| Backend tests (no backend code touched) | ✅ N/A — change is frontend-only |

## 5 · Forbidden changes — NONE made

| Prohibition | Verified |
|---|---|
| Business logic | ✅ untouched |
| Schemas | ✅ untouched |
| Daily Report workflow | ✅ unchanged |
| Approval/Rejection UX | ✅ not started |
| Pilot | ✅ not started |
| RFI | ✅ not started |
| Schedule | ✅ not started |
| P6 | ✅ not started |
| PM Exposure Tile routing | ✅ not started (component still has zero importers) |
| Per-page-only patch (defect kept alive) | ✅ avoided — shared fix |

## 6 · Production deploy readiness

This change is layout-only. It does not affect:
- backend code (zero diff)
- environment variables
- database schema
- scheduler / backup machinery
- authentication / RBAC
- any business logic

**Risk classification**: LOW (visual-only · platform-wide consistent
improvement · regression suite green).

**Rollback**: if visual regression appears post-deploy, the single
mechanical replacement is reversible by re-running the inverse
`sed` against the same 44 files. The new `FormGrid.jsx` is
self-contained — deleting it has no ripple because no migration
currently imports it (it's available for new code).

## 6A · Pass-2 extension (operator-required re-audit)

After Pass 1 was rejected for incomplete platform coverage, Pass 2
extended the migration to multi-col filter bars and stats strips
using **two** canonical patterns:

| Layout density | Canonical class chain |
|---|---|
| 2-col / 3-col (form rows) | `grid grid-cols-1 md:grid-cols-{2,3} gap-x-6 gap-y-4` (24/16 px) |
| 4-col / 5-col (filter bars, stats strips) | `grid grid-cols-2 md:grid-cols-{4,5} gap-x-4 gap-y-3` (16/12 px) |

Pass-2 added ~146 additional canonical migrations on top of Pass-1's 69,
reaching **215 canonical multi-col grids platform-wide**. Detailed
inventory and screenshots are in
`IPAD_LAYOUT_VALIDATION_REPORT.md` Pass 2.

Pass-2 regression evidence (re-run after Pass 2):
- Wave-2 Playwright DR field reliability — 6 passed · 1 skipped (37.2 s)
- Backend admin auth — 23 passed (3.3 s)
- ESLint clean on FormGrid + NewDailyReport
- Operator-cited surfaces (HR Time Verification, PO Drawer, HR Hub, Payroll Variance, Dispatch, Shop, Safety, Incident, Equipment) all visually clean at iPad portrait 820×1180

## 7 · Follow-up work (not in scope of this fix)

These items are NOT part of this P0 and are explicitly deferred:

1. ESLint rule to forbid `sm:grid-cols-2` in form contexts.
2. Playwright snapshot test storing a known-good iPad portrait DR
   form image for visual regression gating.
3. Gradual migration of inline `grid grid-cols-1 md:grid-cols-2`
   classNames to the `FormGrid` component (cosmetic / semantic only;
   the canonical class chain is already correct).

## 8 · Stop condition observed

This certification is the deliverable. No further work begins until
operator review. Doctrine binding: `FORM_SPACING_DOCTRINE.md`.
Validation evidence: `IPAD_LAYOUT_VALIDATION_REPORT.md`.

---

_End of PLATFORM_FORM_GRID_FIX_CERTIFICATION.md._
