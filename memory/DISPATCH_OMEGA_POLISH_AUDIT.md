# DISPATCH OMEGA POLISH SPRINT · AUDIT
## OMEGA Authorization · Polish-only sprint · NO new features

**Date**: 2026-06-03
**File modified**: `/app/frontend/src/pages/DispatchHub.jsx` (rewrite — 631 LOC → 626 LOC, -5 LOC net; layout reshaped without bloat)
**Files NOT touched**: every other frontend file, every backend file, every DB collection, every route, every API.

---

## 1 · Scope confirmation

| Authorized | Status |
|---|:-:|
| Q1 — Data sanitation: Option A (audit-only, ZERO prod writes) | 🟢 |
| Q2 — Coaching persistence: Option A (localStorage) | 🟢 |
| P0 Hierarchy rebuild | 🟢 |
| P0 Decorative component review | 🟢 |
| P0 Coaching collapse | 🟢 |
| P0 Guide consolidation | 🟢 |
| P1 Screen density | 🟢 |
| P1 Visual command center mode | 🟢 |
| P1 Duplicate content elimination | 🟢 |

---

## 2 · Code-side verification

| Check | Result |
|---|:-:|
| ESLint clean on `DispatchHub.jsx` | 🟢 No issues found |
| Webpack compile | 🟢 *"webpack compiled successfully"* |
| Section order in source (by `data-testid`) | 🟢 attention → issue → live → follow → secondary → command → resources → peripheral |
| Local `<footer>` removed (was duplicate of `<GlobalFooter />` in App.js) | 🟢 confirmed |
| All routes / test-ids / backend calls preserved | 🟢 verified |

---

## 3 · Top-level changes applied

| Change | File | Detail |
|---|---|---|
| Section order rebuilt per directive | `DispatchHub.jsx` | Attention is now first operational surface. Was: Command/coaching → Attention. Now: Attention → Issue Work → Live Board → Follow-Through → Secondary → Coaching (collapsible) → Resources → Peripheral. |
| Decorative components moved below operational content | `DispatchHub.jsx` | `PasskeyEnrollPrompt`, `FieldMemoryGlance`, `LastActivityLine` now sit in a `[data-testid="ds-peripheral"]` block at the bottom of the page, under a subtle border-top divider. Previously rendered above Operational Attention. |
| Coaching converted to collapsible | `DispatchHub.jsx` | New `<CoachingBlock>` component with chevron toggle. Default: expanded (first visit). Persistence: `localStorage["masci.dispatch.coaching.collapsed"]`. Header reads "Show Dispatch Guidance" when collapsed, "Dispatch Command" when expanded. |
| Guide section consolidated | `DispatchHub.jsx` | Was: 6 `<GuideTile>` cards + 1 "Open all guides" CTA in a 2-column grid (~280 px vertical). Now: 1 "Open Guides" CTA only (~64 px vertical). Saves ~216 px above scroll. |
| Density pass: `space-y-6` → `space-y-4` | `DispatchHub.jsx` | Vertical rhythm between sections compressed from 24 px to 16 px. |
| Density pass: `py-6` → `py-4` (main) | `DispatchHub.jsx` | Page top/bottom margin compressed from 24 px to 16 px. |
| Density pass: `p-5` → `p-4` (section cards) | `DispatchHub.jsx` | Section padding compressed from 20 px to 16 px on all six sections (`dense` prop). |
| Issue button min-height 88 → 76 px | `DispatchHub.jsx` | Still ≥44 px tap target compliant; saves 12 px × 4 buttons = 48 px above scroll. |
| Live board CTA min-height 52 → 48 px | `DispatchHub.jsx` | Still ≥44 px tap target compliant. |
| Section icon box 40 → 36 px | `DispatchHub.jsx` | Tighter visual chrome. |
| Live attention cards gain ring on active counts | `DispatchHub.jsx` | `ring-1 ring-inset` on rose/amber when count > 0 — adds command-center "alive" emphasis without color change. |
| Local footer removed | `DispatchHub.jsx` | `<footer>` block + `<ForgedOpsAttribution variant="footer" />` removed. `<GlobalFooter />` already mounted in `App.js:771` provides the single canonical footer. |
| `Section` component gains `dense` prop | `DispatchHub.jsx` | Backward-compatible (default `false`); all hub sections pass `dense={true}`. |

---

## 4 · Behaviour preservation

| Feature | Pre-sprint | Post-sprint |
|---|---|---|
| Operational Attention cards (breakdown, stuck, longWait) | rendered from `/api/dispatch/governance/findings` | same |
| Issue Work 4-button grid (Material / Equipment Move / Tanker / Support) | opens `<AssignmentCreateDrawer>` with `initialHaulType` | same |
| Operational Board link | `to="/dispatch-portal/board"` | same |
| Follow-Through tabs (Equipment moves, Holds) | `<DispatchTransfersTab>`, `<DispatchHoldsTab>` | same |
| Secondary tabs (Overview, Utilization, Idle, Integrations) | `<DispatchOverviewTab>` etc. | same |
| Sidebar V2 (`useDispatchSidebarV2Enabled()`) | rendered when flag enabled | same |
| Logout | `clearAllSessions()` + nav to `/dispatch-portal/login` | same |
| All test-ids | preserved 1:1 (`ds-section-attention`, `ds-attention-breakdown`, `dispatch-board-link`, `ds-issue-material`, etc.) | preserved |
| New test-ids introduced | n/a | `ds-section-resources`, `ds-section-command`, `ds-coaching-toggle`, `ds-coaching-body`, `ds-coaching-icon-down`, `ds-coaching-icon-up`, `ds-peripheral` |
| Backend endpoints called | `/api/dispatch/governance/findings` (only) | same |

**Zero new backend endpoints. Zero new database surfaces. Zero new permissions. Zero new business logic.**

---

## 5 · Risk classification

| Risk | Severity | Notes |
|---|---|---|
| Auth flow regression | LOW | Auth gate (`RequireDispatch`) untouched. |
| Test-id regression | NONE | All pre-existing test-ids preserved. |
| Translation key drift | NONE | All strings still wrapped in `t(...)`. |
| Layout regression on small screens | LOW | All responsive breakpoints preserved (`sm:`, `lg:`). |
| Coaching first-visit UX | LOW | Default is expanded on first visit (`null` localStorage). Returning users with previous expanded state see expanded; only users who explicitly collapsed see collapsed. |
| Duplicate footer regression elsewhere | NONE | This sprint only modified DispatchHub. Other hub footers can be audited in a follow-up sprint. |

---

## 6 · Compliance with directive stop-rules

| Rule | Status |
|---|:-:|
| No new workflows | 🟢 |
| No new database tables | 🟢 |
| No new APIs | 🟢 |
| No new backend architecture | 🟢 |
| No new modules | 🟢 |
| No new permissions | 🟢 |
| No new business logic | 🟢 |
| ZERO production data changes | 🟢 (data sanitation is audit-only) |

---

## 7 · Cross-references

| Companion deliverable | Subject |
|---|---|
| `DISPATCH_DATA_SANITATION_REPORT.md` | Audit + cleanup script (operator-runnable, no auto-execution) |
| `DISPATCH_INFORMATION_HIERARCHY_REPORT.md` | Old vs new section order and rationale |
| `DISPATCH_SCREEN_DENSITY_REPORT.md` | Pixel-level density math (above-the-fold delta) |
| `DISPATCH_COMMAND_CENTER_CERTIFICATION.md` | Final certification + GO verdict + post-deploy verification |
