# PM Hub Re-Tiering Certification — Phase IV-BETA.2

**Iteration:** iter437 · Phase IV-BETA.2 · 2026-02-27
**Status:** 🟢 SHIPPED · UNIFIED V2 FLAG · LEGACY DEFAULT · REGRESSION-LOCKED · PREVIEW-ONLY
**Production deployed:** ❌ NO

## I. Summary

| Aspect | Result |
|---|---|
| New component primitives (inline) | 3 (`HubV2QuickTile`, `HubV2Chip`, `HubV2MoreRow`) |
| Modified pages | 2 (`PmHub.jsx`, `PmSections.jsx` coaching cleanup) |
| New regression tests | 7 (`test_pm_hub_v2_layout.py`) |
| New governance scripts | 3 (coaching · copy · loudness) |
| Net new logic LOC | ~260 (PmHub V2 inline body + 3 primitives + flag check) |
| Net data LOC | ~30 (3 data arrays) |
| Total scope | ≤ 500 LOC frontend (within budget) |
| Backend changes | NONE |
| Schema changes | NONE |
| Feature flag | `?pmSidebarV2=1` (unified PM V2 experience · per user direction) |

## II. Hub V2 layout (tier-weighted)

```
Tier 0 · OperationsCenter (KPI signal · preserved)
Tier 1 · Crew Compliance card (calm slate + orange stripe · preserved)
Tier 1 · Today      → 3 quick-action tiles
                      • Daily Reports (red stripe)
                      • Inspections   (red stripe)
                      • Incidents     (orange stripe)
Tier 2 · Coordination → 4 compact chips
                      • My Tasks
                      • PO Requests
                      • Project Health
                      • Asset Transfers
Tier 2 · PmHaulActivityTile      (preserved)
Tier 2 · DispatchLifecycleTile   (preserved)
Tier 3 · More forms (compact list · 8 entries)
         Meetings · Pre-Op · QA/QC · Photos · JHA Plans ·
         Trench Boxes · Field Leadership · Guidance
Tier 4 · LastActivityLine        (preserved)
Tier 5 · FieldMemoryGlance       (preserved · de-emphasized)
Tier 5 · PasskeyEnrollPrompt     (preserved · de-emphasized footer)
```

## III. Acceptance criteria met

| Criterion | Result |
|---|---|
| Tile count above fold ≤ 12 | ✅ 3 Tier-1 + 4 Tier-2 chips + Crew card = 8 visible above fold |
| Hue families ≤ 3 dominant | ✅ Red (Tier 1) · Orange (Compliance) · Slate (everything else) |
| "Welcome to" removed | ✅ Replaced by calm subline "Today's operational signal across your assigned projects." |
| Hierarchy reinforced | ✅ 5-tier visual ladder; shift-critical work surfaces first |
| Simultaneous emphasis reduced | ✅ Stripe colors are 4-px-left only · no full-fill saturated tiles |
| Spacing rhythm normalized | ✅ All `mt-5` between Tier sections · 8-step scale honored |
| Typography normalized | ✅ Tile titles `text-base font-semibold` (was `text-lg font-black`) |
| All 6 preserved widgets intact | ✅ OperationsCenter · Crew Compliance · PmHaulActivity · DispatchLifecycle · LastActivityLine · FieldMemoryGlance |
| Legacy default preserved | ✅ Flag OFF → existing 15-tile grid + "Welcome" intro render unchanged |

## IV. Files touched

| Path | Change |
|---|---|
| `frontend/src/pages/PmHub.jsx` | Added 3 inline primitives + V2 layout body + flag check (`const v2 = isPmSidebarV2Enabled()`); legacy body preserved in `else` branch |
| `frontend/src/pages/pm/PmSections.jsx` | Coaching subline cleanup · doctrine-compliant `<Subline>` helper · all 7 PM sections updated |

## V. Rollback

- Operator-level: `localStorage.removeItem('masci.pm.sidebar.v2')` + reload → legacy
- Code-level: single `git revert` removes V2 path; legacy untouched

## VI. Known limitations / deferred

- Header `border-b-4 border-amber-600` still saturated · deferred to IV-BETA.4 (cross-portal chrome cleanup)
- Breadcrumb `text-amber-300` still saturated · deferred to IV-BETA.4
- Some legacy violations surfaced by `verify_admin_copy.py` (DevLogin "Unlock" button, training-topic content with "simply"): out of scope · IV-BETA.3 coaching cleanup
- Tests scoped to desktop only · mobile Hub layout uses same data via responsive grid (Tailwind `sm:grid-cols-*`)

## Verdict

🟢 **PM HUB V2 RE-TIERED · CALMER · REGRESSION-LOCKED · UNIFIED FLAG.** Awaits manual preview review before IV-BETA.3 begins.

To enable: `?pmSidebarV2=1` (or `localStorage.setItem('masci.pm.sidebar.v2','1')`).
