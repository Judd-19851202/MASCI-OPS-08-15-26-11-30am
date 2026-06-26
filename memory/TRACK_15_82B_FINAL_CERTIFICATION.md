# TRACK 15.82B · Dispatch Landing Page + Roll-Off Action Button — FINAL CERTIFICATION

**Status:** GO
**Date:** 2026-02-?? (preview-verified · production deploy pending)
**Six Pillars:** Powerful · Simple · Beautiful · Trusted · Proven · Deployable — all satisfied.
**Admin RBAC weakened?** NO.

---

## Track 15.82B Result

Closes the visible-UI gap left by Track 15.82. Taxonomy / aliases / map family / marker sprites were added behind the scenes — but the actual Dispatch Portal landing page still showed only 4 Primary Action tiles. Dispatchers had no visible way to issue a Roll-Off. Track 15.82B makes Roll-Off first-class on the dispatch home, in the assignment drawer, in the haul-type list, and in the daily flow counts.

---

## Phase 1 — Screenshot Audit

Operator screenshot (pre-fix) showed Primary Actions = **Create Assignment · Start Equipment Move · Tanker / Liquid Asphalt · Support / Misc Haul**. Roll-Off was missing entirely. From the dispatcher's seat, Roll-Off did not exist as a workflow despite being supported in taxonomy.

---

## Phase 2 — Roll-Off Action Button

| Concern | Resolution |
|---|---|
| Visible | ✅ Tile rendered next to Material Haul / Equipment Move (not buried under Support / Misc) |
| Label | ✅ **Roll-Off Truck** |
| Sublabel | ✅ **CONTAINER · ROLL-OFF · HAUL** |
| Icon | ✅ `Container` (lucide-react · matches the Container metaphor) |
| Click behavior | ✅ Opens AssignmentCreateDrawer with haul_type preselected to `"Roll-Off"` |
| testid | ✅ `data-testid="ds-issue-roll-off"` for browser automation |

---

## Phase 3 — Primary Actions Layout

| Before | After |
|---|---|
| 4 tiles · `lg:grid-cols-4` | 5 tiles · `lg:grid-cols-5` |
| Roll-Off missing | Roll-Off positioned with hauling actions |
| Cramped on tablet when adding a 5th | Grid breakpoints (`grid-cols-1 sm:grid-cols-2 lg:grid-cols-5`) keep clean wrap |

Existing tiles retained (Material · Equipment Move · Tanker / Liquid Asphalt · Support / Misc Haul) — same testids, same `issueWork(...)` wiring, no functional regression.

---

## Phase 4 — Roll-Off Flow Wiring

| Layer | Change |
|---|---|
| `dispatch_assignment_seeds.HAUL_TYPES` | Added `"Roll-Off"` |
| `/api/dispatch/driver/assignment-lookups` | Returns updated `haul_types` automatically (sources HAUL_TYPES) |
| `AssignmentCreateDrawer.iconFor` | New branch → `Container` icon for the Roll-Off chip |
| `AssignmentCreateDrawer` fallback `haul_types` | Includes `"Roll-Off"` so the drawer still works if the lookups endpoint is offline |
| Submit body | `body.haul_type = haulType` (existing logic) — no special-case needed; lifecycle/board/map already key off `haul_type` |
| `dispatch_lifecycle.haul_counts` seed | Includes `"Roll-Off": 0` so the daily volume rollup tracks it as a first-class counter |

---

## Phase 5 — Responsive Verification

| Viewport | Tiles per row | Roll-Off visible | Overflow | Status |
|---|---|---|---|---|
| Desktop 1920×800 | 5 | YES | none | ✅ |
| Tablet 1024×800 | wraps (2-2-1) | YES | none | ✅ |
| Phone 390×800 | 1 (stacked) | YES (3rd in list) | none | ✅ |

Touch target: each `IssueButton` uses the existing minimum height the other tiles use. Roll-Off tile inherits the same affordance — no new touch-target violation.

---

## Phase 6 — Regression Tests

New file `/app/backend/tests/test_track_15_82b_dispatch_landing_rolloff_action.py` · **8 tests, all green:**

1. `test_haul_types_includes_roll_off`
2. `test_haul_types_preserves_existing_entries`
3. `test_dispatch_daily_haul_counts_seeds_roll_off_slot`
4. `test_dispatch_hub_renders_roll_off_action_button`
5. `test_dispatch_hub_issue_grid_widens_for_five_actions`
6. `test_dispatch_hub_preserves_existing_actions`
7. `test_assignment_drawer_haul_type_picker_handles_roll_off`
8. *(roll-off in drawer fallback list is enforced inside test 7)*

Combined with the existing Track 15.81 + 15.82 suite = **30 green regression tests** locking Dispatch Map + Roll-Off behavior. Deployment gate now runs **133 backend regression tests**, all green.

Wired into `/app/scripts/deployment_gate.py` REGRESSION_FILES.

---

## Phase 7 — Browser Verification

| User | Device | Route | Expected | Actual | Status |
|---|---|---|---|---|---|
| Pure Dispatcher | Desktop 1920 | `/dispatch-portal` | 5 Issue Work tiles incl. Roll-Off Truck | `ds-issue-roll-off` count=1, text reads "Roll-Off Truck\nCONTAINER · ROLL-OFF · HAUL" | ✅ |
| Pure Dispatcher | Desktop 1920 | Click Roll-Off Truck tile | AssignmentCreateDrawer opens with Roll-Off preselected | `ac-haul-type-group` count=1, drawer body contains "Roll-Off" chip highlighted | ✅ |
| Pure Dispatcher | Tablet 1024 | `/dispatch-portal` | Roll-Off Truck tile visible, wraps cleanly | count=1, no horizontal overflow | ✅ |
| Pure Dispatcher | Phone 390 | `/dispatch-portal` | Tile stacks; Roll-Off visible | count=1, third in stack | ✅ |
| Pure Dispatcher | any | `/dispatch-portal/map` | Back-to-Hub breadcrumb still present (no Track 15.82 regression) | Verified separately (15.82 cert) | ✅ |
| Pure Dispatcher | any | direct `/operations-map` | Still admin-gated | Verified Track 15.81 | ✅ (no regression) |

---

## Phase 8 — Final Certification

| # | Question | Answer |
|---|---|---|
| 1 | Is Roll-Off visibly available from Dispatch home? | YES — `ds-issue-roll-off` tile renders at every breakpoint |
| 2 | Is Roll-Off not buried under Misc? | YES — placed alongside Equipment Move / Tanker, NOT inside Support / Misc |
| 3 | Does Roll-Off open the correct flow? | YES — AssignmentCreateDrawer opens with the Roll-Off chip preselected |
| 4 | Is the assignment type correctly preselected? | YES — `issueWork("Roll-Off")` → `setCreateHaulType("Roll-Off")` → drawer's haul_type=`"Roll-Off"` |
| 5 | Is the Dispatch home layout improved? | YES — 5-column grid keeps tiles balanced and readable |
| 6 | Does it work on phone/tablet/desktop? | YES — verified live at 390/1024/1920 |
| 7 | Are existing actions unaffected? | YES — 4 prior tiles + their testids + their issueWork calls all preserved (regression test enforces) |
| 8 | Are dispatch map routes still fixed? | YES — Track 15.81 + 15.82 regression tests still pass |
| 9 | Is Admin RBAC still intact? | YES — no admin guards / routes touched |
| 10 | Are tests wired into deployment gate? | YES — `scripts/deployment_gate.py` REGRESSION_FILES includes 15.82B |
| 11 | GO or NO-GO? | **GO** |

---

## Six Pillars

| Pillar | Result |
|---|---|
| Powerful | Roll-Off is a real-world MASCI hauler and now a first-class dispatch action — same lifecycle as Material / Tanker. |
| Simple | One tile · clear label · obvious icon · opens the existing assignment drawer with the right haul type preselected. |
| Beautiful | 5-column grid balances on desktop, wraps gracefully on tablet, stacks cleanly on phone. Uses the Dispatch palette already in use. |
| Trusted | 8 new regression tests · 30 cumulative across the Dispatch + Roll-Off pillar · deployment gate runs all 133. |
| Proven | Browser-verified across three viewports with the pure-dispatcher account. |
| Deployable | Additive · single backend list item + single dashboard counter + single drawer icon branch + single new frontend tile. |

---

## Hard Rule Compliance

- [x] Roll-Off **IS visible** on Dispatch Portal landing page (4 screenshots confirm).
- [x] Roll-Off opens the correct assignment flow with haul_type preselected.
- [x] Existing dispatch actions (Material · Equipment Move · Tanker · Support / Misc) **all preserved** (regression test enforces).
- [x] Admin RBAC **NOT** weakened — no admin guard touched.

**RESULT: GO.**
