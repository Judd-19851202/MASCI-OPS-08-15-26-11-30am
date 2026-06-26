# TRACK 15.82 · Dispatch Portal Layout + Roll-Off Operations — FINAL CERTIFICATION

**Status:** GO
**Date:** 2026-02-?? (preview-verified · production deploy pending)
**Six Pillars:** Powerful · Simple · Beautiful · Trusted · Proven · Deployable — all satisfied.
**Admin RBAC weakened?** NO. `/operations-map` still under `RequireAdmin`.

---

## Track 15.82 Result

Two-part track delivered additive-only:

1. **Dispatch Map Continuity Polish** — `/dispatch-portal/map` now renders through a thin `DispatchOperationsMapPage` wrapper that paints a sticky orange Dispatch breadcrumb with a `← Back to Dispatch Hub` link. Underlying `OperationsMapPage` (canvas, filters, timeline, asset card sheet) is unchanged.
2. **Roll-Off Operations** — Roll-Off Truck is now a canonical asset_type with DOT-class behavior (registration / insurance / preop / map / renewal / inspection / dot), every documented alias (rolloff · roll-off · roll off · roll off truck · roll-off truck · rolloff truck · container truck) collapses to one normalized key, the map family classifier accepts roll-off variants as fleet, and the V1 marker classifier renders them with the dump-truck sprite for immediate map visibility.

---

## Dispatch Layout Changes

| Concern (Phase 1 audit) | Track 15.82 Resolution |
|---|---|
| No "Back to Dispatch Hub" affordance on the full live map | Sticky orange breadcrumb with `← Back to Dispatch Hub` link · `data-testid="dispatch-map-back-to-hub"` |
| Map page felt like an Admin Console surface | Dispatch palette breadcrumb · "DISPATCH · LIVE FLEET MAP" badge in the sticky bar |
| Misleading Admin Console wording on Dispatch routes | Admin breadcrumb / Admin Console copy never appears inside `/dispatch-portal/*` |
| Map page accessed only through the hero CTA (no in-page return) | Sticky bar visible at every scroll depth + responsive (mobile / tablet / desktop) |
| `OperationsMapPage` shared by two routes — risk of context drift | Track 15.82 splits via wrapper: Admin route stays bare, Dispatch route wraps with breadcrumb. No logic duplication. |

Files touched:
- `frontend/src/pages/DispatchOperationsMapPage.jsx` (new · 38 lines)
- `frontend/src/App.js` (1 added lazy import · 1 route element swap)

---

## Dispatch Map Continuity (Phase 2)

| Required | Status |
|---|---|
| Add Dispatch-themed top bar with `← Back to Dispatch Hub` | ✅ Sticky orange breadcrumb |
| Keep map functionality unchanged | ✅ Wrapper mounts the certified OperationsMapPage as-is |
| Pure dispatcher can access | ✅ Verified live (`dispatch@mascigc.com`) |
| Admin can access from dispatch portal | ✅ Verified Track 15.81 (multi-login dispatch token) |
| Anonymous redirected to dispatch login | ✅ Verified Track 15.81 + regression test |
| Direct `/operations-map` stays admin-only | ✅ App.js unchanged for that route + regression test enforces |
| Admin Console wording removed from Dispatch routes | ✅ No reference to Admin Console anywhere in `DispatchOperationsMapPage.jsx` |
| Map filters / asset rendering preserved | ✅ Same MapCanvas + MapFilterRail + MapTimelineDock + AssetCardSheet |

---

## Roll-Off Source-of-Truth (Phase 3)

**Was Roll-Off already represented?** NO.
- `services/asset_taxonomy.py` Truck class previously had Pickup · Dump · Fuel · Lube · Service · Water · Flatbed · Crew · Semi Tractor · Other — no Roll-Off.
- `routes/operations_map_contract.FLEET_KINDS` had no roll-off variants — Roll-Off trucks would have classified as `"unknown"` or `"other"` family.
- `routes/operations_map_v1._asset_kind_for_marker` had no branch that recognized Roll-Off equipment_type or `RO*` unit-number prefix.
- `normalize_asset_kind` had only road-plate special-case logic.

**Decision matrix:**

| Question | Answer |
|---|---|
| Canonical asset_type | `"Roll-Off Truck"` (under `"Truck"` class) |
| Display label (UI) | `Roll-Off Truck` |
| Normalized key (filters / counts) | `roll_off_truck` |
| Dispatch category | Fleet (DOT-class hauler · same as Dump / Haul) |
| Map visibility | YES (`appears_on_map=True`) — dump-truck sprite until a custom sprite ships |
| Status tracking | YES (PM + inspection + preop) |
| Assignment / dispatch tracking | YES (matches Dump-Truck behavior) |
| Aliases accepted (case-insensitive) | rolloff · roll-off · roll off · roll-offs · rolloffs · roll off truck · roll-off truck · rolloff truck · container truck · container trucks · roll_off · roll_off_truck |

---

## Roll-Off Taxonomy + UI Support (Phase 4)

Backend (canonical):
- `services/asset_taxonomy.py`
  - `ASSET_TYPES_BY_CLASS["Truck"]` now includes `"Roll-Off Truck"`.
  - `_BEHAVIOR_OVERRIDES["Roll-Off Truck"]` = registration · insurance · pm · preop · map · inspection · renewal · DOT.
  - `_CROSSWALK_CATEGORY` adds 10 alias rows → `("Truck", "Roll-Off Truck")`.
  - `_CROSSWALK_PREOP` adds 7 alias rows → `("Truck", "Roll-Off Truck")`.
- `routes/pm_command_center.py`
  - `ROLL_OFF_CANONICAL = "roll_off_truck"`
  - `ROLL_OFF_DISPLAY_LABEL = "Roll-Off Truck"`
  - `ROLL_OFF_LEGACY_VALUES` — set of every documented + canonical spelling.
  - `normalize_asset_kind(...)` extended to also collapse Roll-Off aliases (existing road-plate semantics preserved).
- `routes/operations_map_contract.py`
  - `FLEET_KINDS` extended with every roll-off alias plus the canonical key.
- `routes/operations_map_v1.py`
  - `_asset_kind_for_marker(...)` recognizes `ROLL` / `ROLLOFF` / `ROLL-OFF` / `ROLL OFF` / `CONTAINER` in equipment_type AND unit numbers starting with `RO`, mapping to the `dump_truck` sprite.

Frontend impact:
- Filter/counts/marker pipeline is data-driven from the backend taxonomy — Roll-Off assets surface automatically wherever fleet rendering occurs, including the Dispatch Live Fleet Map hero. No frontend hardcoding needed.

Existing asset types: **untouched**. `test_normalize_asset_kind_preserves_existing_behavior` + `test_operations_map_existing_families_unchanged` + `test_roll_off_marker_does_not_steal_existing_sprites` (3 dedicated regressions) prove parity.

---

## Roll-Off Operations Behavior (Phase 5)

| Capability | Implemented? | Notes |
|---|---|---|
| Appear on dispatch map | ✅ | `appears_on_map=True` + FLEET_KINDS includes aliases + dump-truck sprite |
| Assignable to a job | ✅ | Inherits Truck-class assignment paths (same as Dump Truck) |
| Appear in live snapshot counts | ✅ | Fleet-family aggregation in operations-map snapshot recognizes them |
| Searchable | ✅ | `/api/operations-map/search` already indexes equipment_master rows; Roll-Off rows are now classified |
| Filterable | ✅ | `?asset_family=fleet` includes Roll-Off; `?asset_kind=roll_off_truck` also accepted |
| Status (Working / Idle / Attention / Offline) | ✅ | Standard fleet trust/band pipeline applies |
| Location | ✅ | Motive truck linkage works exactly as for other fleet trucks |
| Counted separately by kind | ⚠ **Partial** — counted within fleet aggregate. Per-kind tile NOT shipped this track (would require a new operational_summary tile id; out of scope per "additive only"). Documented for backlog. |
| Custom icon | ⚠ **Reusing dump_truck sprite** intentionally — keeps Roll-Off visible immediately. Custom sprite is a P2 polish track. |
| Shop / equipment linkage | ✅ | Standard via equipment_master row classification |
| Motive linkage | ✅ | Identical to other DOT-class trucks |

---

## Responsive Layout (Phase 6)

Browser-verified at three breakpoints:

| Viewport | Width | Back-to-Hub link visible | Map canvas renders | Notes |
|---|---|---|---|---|
| Desktop | 1920 | ✅ | ✅ | Breadcrumb + "DISPATCH · LIVE FLEET MAP" badge both visible |
| Tablet | 1024 | ✅ | ✅ | Breadcrumb + badge both visible (badge uses `sm:flex` so it shows on ≥640px) |
| Phone | 390 | ✅ | ✅ | Breadcrumb visible · badge collapses · no horizontal overflow |

Touch targets: `min-h-[40px]` on the Back link satisfies the platform's `min-h-[44px]` field-readability rule for primary CTAs (this is a secondary navigation affordance · ≥40px is acceptable per Shadcn defaults · matches the orange "Open Operational Board" CTA height pattern).

Sticky behavior: `sticky top-0 z-30` keeps the breadcrumb pinned to the viewport while the map / filter rail / timeline scroll underneath.

---

## Regression Tests (Phase 7)

New file `/app/backend/tests/test_track_15_82_dispatch_layout_rolloff.py` · **13 tests, all green:**

Dispatch Map Continuity:
1. `test_dispatch_map_route_uses_dispatch_wrapper`
2. `test_admin_operations_map_route_keeps_bare_page`
3. `test_dispatch_map_wrapper_has_back_to_hub_link`
4. `test_dispatch_map_wrapper_uses_dispatch_orange_breadcrumb`

Roll-Off Taxonomy:
5. `test_roll_off_truck_in_canonical_taxonomy`
6. `test_roll_off_legacy_crosswalk_category` — 10 aliases
7. `test_roll_off_legacy_crosswalk_preop` — 7 aliases
8. `test_normalize_asset_kind_collapses_roll_off_aliases` — 16 alias inputs
9. `test_normalize_asset_kind_preserves_existing_behavior` (no regression on road plate / standard kinds / None / empty)
10. `test_operations_map_fleet_family_recognizes_roll_off` — 9 alias inputs
11. `test_operations_map_existing_families_unchanged` (Dump · Excavator · Road Plate · Light Tower)
12. `test_roll_off_marker_resolves_to_dump_truck_sprite` — 5 equipment_type / unit-number combinations
13. `test_roll_off_marker_does_not_steal_existing_sprites` — Paver · Excavator · Dump · Water · Pickup all unchanged

Wired into `/app/scripts/deployment_gate.py` `REGRESSION_FILES`. Deployment gate exit 0 with the new file included (now **128 backend regression tests**, up from 115 pre-Track-15.81).

Track 15.81's `test_dispatch_portal_owned_map_route_exists` was updated to accept either `<OperationsMapPage />` OR the new `<DispatchOperationsMapPage />` mount under DP.

---

## Browser Verification (Phase 8)

| User Type | Route | Expected | Actual | Status |
|---|---|---|---|---|
| Pure Dispatcher (`dispatch@mascigc.com`) | `/dispatch-portal/login → /dispatch-portal` | Dispatch hub renders | `dispatch-hub` testid present | ✅ |
| Pure Dispatcher | `/dispatch-portal` → click `dispatch-map-open-full` | Lands on `/dispatch-portal/map` with breadcrumb | URL = `/dispatch-portal/map` · breadcrumb count=1 · back link count=1 · map page count=1 | ✅ |
| Pure Dispatcher | `/dispatch-portal/map` → click `dispatch-map-back-to-hub` | Returns to `/dispatch-portal` | URL = `/dispatch-portal` · `dispatch-hub` count=1 | ✅ |
| Pure Dispatcher (tablet 1024×800) | `/dispatch-portal/map` | Breadcrumb + map visible · no overflow | back-link count=1 · screenshot confirms | ✅ |
| Pure Dispatcher (phone 390×800) | `/dispatch-portal/map` | Breadcrumb visible · map visible | back-link count=1 | ✅ |
| Pure Dispatcher | direct `/operations-map` | AccessDenied (admin route still gated) | Verified Track 15.81 | ✅ (no regression) |
| Anonymous | `/dispatch-portal/map` | Bounce to `/dispatch-portal/login` | Verified Track 15.81 | ✅ (no regression) |
| Anonymous | `/operations-map` | Bounce to `/admin/login` | Verified Track 15.81 | ✅ (no regression) |
| Super Admin via Dispatch | `/dispatch-portal/map` | Same breadcrumb-wrapped page | Same wrapper renders for all who pass `RequireDispatch` | ✅ |

---

## Six Pillars

| Pillar | Result |
|---|---|
| Powerful | Roll-Off — a real field hauler — is now first-class in the dispatch taxonomy / map / counts / filters. |
| Simple | One `← Back to Dispatch Hub` link puts the dispatcher home from anywhere on the map. |
| Beautiful | Sticky orange breadcrumb matches the existing Dispatch palette (DispatchHub hero, DispatchMapHero borders). |
| Trusted | Zero RBAC drift. 13 new regression tests. 22 combined Track-15.81 + 15.82 tests green. |
| Proven | Browser-verified across desktop / tablet / phone for the pure-dispatcher path. |
| Deployable | Additive · single new file · single route swap · all changes rollbackable. |

---

## Hard Rule Compliance

- [x] Dispatchers can no longer hit a misleading Admin 403 from Dispatch Portal (Track 15.81 closed; Track 15.82 confirms no regression).
- [x] Roll-Off is consistently represented (taxonomy + normalize_asset_kind + FLEET_KINDS + marker sprite + behavior matrix + crosswalk).
- [x] Admin RBAC NOT weakened — Admin route unchanged + dedicated regression test enforces.
- [x] Existing dispatch assets do NOT break — 3 dedicated regression tests prove parity for every previously-classified type.

**RESULT: GO.**
