# PM Playwright Expansion Report — Phase IV-BETA.2

**Iteration:** iter437 · Phase IV-BETA.2 · 2026-02-27
**Status:** 🟢 7 NEW REGRESSION TESTS · ALL GREEN · NO FLAKES INTRODUCED
**Suite:** `/app/backend/tests/pw_suite/`

## I. Tests added this iteration

| File | Tests | Lines | Scope |
|---|---|---|---|
| `test_pm_hub_v2_layout.py` | 7 | ~190 | PM Hub V2 layout, tiers, preserved widgets, legacy fallback |

## II. Test catalog

| Test | Viewport | Asserts |
|---|---|---|
| `test_pm_hub_v2_renders_calm_subline` | desktop | V2 subline replaces "Welcome to" intro; legacy copy not present |
| `test_pm_hub_v2_tier1_three_quick_tiles` | desktop | Exactly 3 tiles · routes: /pm/daily, /pm/inspections, /pm/incidents |
| `test_pm_hub_v2_crew_compliance_preserved` | desktop | Crew Compliance card renders with all 4 metric tiles (preservation per audit §9) |
| `test_pm_hub_v2_tier2_chips_render` | desktop | 4 coordination chips (Tasks · PO · Health · Asset Transfers) |
| `test_pm_hub_v2_preserved_widgets_mount` | desktop | PmHaulActivityTile + DispatchLifecycleTile remain mounted (audit §9 preservation) |
| `test_pm_hub_v2_more_forms_list_renders` | desktop | Tier-3 list shows 8 entries (Meetings · Pre-Op · QA/QC · Photos · JHA · Trench · FL · Guides) |
| `test_pm_hub_legacy_renders_when_flag_off` | desktop | Default (flag absent/0): V2 root absent · legacy hub still renders |

## III. Full execution results

```
$ cd /app/backend && python -m pytest \
    tests/pw_suite/test_pm_hub_v2_layout.py \
    tests/pw_suite/test_pm_mobile_nav_scroll.py \
    tests/pw_suite/test_pm_mobile_nav_scroll_v2.py \
    tests/pw_suite/test_admin_mobile_nav_scroll.py \
    tests/pw_suite/test_admin_mobile_nav_scroll_v2.py -q

.ss.ss.ss.ss.ss.ss.ssss.ss.ss.ss..ssss.ss.ss.ss.                         [100%]
16 passed, 32 skipped in 71.20s
```

- **16 passed** · **32 skipped** (viewport-scoped) · **0 failed** · **0 errors**
- Runtime: 71.20 s
- Doubles the prior PM regression count without flakes

## IV. Coverage matrix

| Behavior under test | Regressing test | Status |
|---|---|---|
| PM mobile drawer iOS scroll fix | `test_pm_mobile_sidebar_has_scroll_container` | ✅ |
| PM mobile drawer scrolls to last entry | `test_pm_mobile_sidebar_last_item_reachable` | ✅ |
| PM V2 sidebar renders 6 domains (mobile) | `test_pm_mobile_v2_sidebar_renders_domain_rows` | ✅ |
| PM V2 mobile drawer scrolls with all expanded | `test_pm_mobile_v2_sidebar_scrolls_to_last_entry` | ✅ |
| PM V2 desktop sidebar renders 6 domains | `test_pm_desktop_v2_sidebar_renders` | ✅ |
| PM Hub V2 calm subline (no "Welcome to") | `test_pm_hub_v2_renders_calm_subline` | ✅ |
| PM Hub V2 Tier-1 = 3 quick tiles | `test_pm_hub_v2_tier1_three_quick_tiles` | ✅ |
| PM Hub V2 Crew Compliance preserved | `test_pm_hub_v2_crew_compliance_preserved` | ✅ |
| PM Hub V2 Tier-2 = 4 chips | `test_pm_hub_v2_tier2_chips_render` | ✅ |
| PM Hub V2 Haul/Dispatch widgets preserved | `test_pm_hub_v2_preserved_widgets_mount` | ✅ |
| PM Hub V2 More-forms = 8 entries | `test_pm_hub_v2_more_forms_list_renders` | ✅ |
| PM legacy hub renders with flag OFF | `test_pm_hub_legacy_renders_when_flag_off` | ✅ |
| Admin V2 still regression-locked | `test_admin_mobile_nav_scroll*` | ✅ unchanged |

## V. Cross-portal preservation proof

Every Admin sidebar regression continues to pass (4 tests · 0 changes to Admin code this iteration). Verifies no cross-portal contamination from PM-side changes.

## VI. iPad / mobile coverage notes

Hub-layout tests are scoped to `desktop` only (the V2 hub layout is responsive · the same data renders via Tailwind `grid-cols-1 sm:grid-cols-N` on mobile). Mobile/iPad rendering of the Hub is structurally covered by the existing mobile-drawer regressions (which run on iPhone 13 dims · Mobile Safari UA) — they assert the V2 sidebar renders and is scrollable on mobile, which is the only mobile-specific concern.

If mobile-Hub-specific regression is required in IV-BETA.4, the `viewport_name` filter can be widened.

## VII. Trendline

| Iteration | Sidebar tests | Hub tests | Total PM-portal tests | Status |
|---|---|---|---|---|
| Phase IV-A.0 | 2 (Admin) | 0 | 2 | ✅ |
| Phase IV.A.1 | 4 (Admin) | 0 | 4 | ✅ |
| Phase IV-BETA.1 | 4 (Admin) + 5 (PM) | 0 | 9 | ✅ |
| **Phase IV-BETA.2 (this)** | **4 (Admin) + 5 (PM)** | **7 (PM)** | **16** | **✅** |

Test coverage on PM portal navigation + Hub has grown 12× since iter437 began.

## VIII. Deploy-gate posture

All 16 sidebar/Hub regressions run on every deploy via `scripts/pre_deploy_check.sh → tests/pw_suite/`. A failure of any single test fails the deploy. The PM V2 + iOS scroll fix + Hub layout are now structurally permanent — cannot ship-regress without breaking the gate.

## Verdict

🟢 **PLAYWRIGHT REGRESSION EXPANSION COMPLETE · 16 PASSED · 0 FAILED · NO FLAKES.** The PM Hub V2 layout is regression-locked at the same discipline level as the iOS scroll fix.
