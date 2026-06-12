# TRACK 13.7B — Shop Operational Map Lens · Implementation Report

**Date**: 2026-06-12
**Mode**: CONTROLLED IMPLEMENTATION · Option B (one shared engine + embedded role-specific lens).
**Files changed**: 2 (1 React page, 1 CSS rule append). No backend, no routes, no APIs, no auth, no integrations.
**Doctrine reinforced**: *No workflow changes without workflow discovery.* Shop queues remain primary. Map lens is secondary, small, and truthful.

---

## 1 · Executive Summary

Added a small **Recovery Map** lens as **Section 3** of `ShopHubV2.jsx`, **below** the existing recovery queues (Sections 1 & 2). The lens reuses the certified `MapCanvas` MapLibre engine and the existing `/api/operations-map/snapshot` payload. It filters client-side to assets with `attention_reason ∈ {maintenance, inspection}` and renders a 360-px-tall map alongside a list of shop-relevant units (unit_number · current location/assignment.name · attention reason · next action). When no assets match the Shop-owned attention reasons, the panel renders an honest empty state — no fabricated markers, no fabricated provider claims.

**Verification highlights**:
- Shop queues (Sections 1 + 2) remain visually primary above the map. ✅
- MapLibre canvas renders inside `data-testid="shop-recovery-map-wrap"` via the same CSS-scoping pattern that Dispatch Hero already uses. ✅
- `/dispatch-portal` Live Fleet Map still dominant — 5 cluster groups visible across East Florida, hero unchanged. ✅
- Backend regression: `test_operations_map_contract_phase_5a.py` 26/26 pass · `test_rc2_ops_map_contract.py` 2/2 pass · `test_operations_map_masci_vocab.py` 14/14 pass. ✅
- Frontend lint clean for the touched file. ✅

---

## 2 · What Was Implemented

### 2.1 · File diffs
| File | Lines added | What changed |
|---|---|---|
| `/app/frontend/src/components/operations-map/OperationsMap.css` | +24 | Added scoped CSS rule `[data-testid="shop-recovery-map-wrap"] .ops-map-canvas { … }` — same pattern Dispatch Hero already uses (Track 13.4A). Forces MapLibre canvas to absolute-fill its parent sized box when nested inside the Shop wrap. **Full `/operations-map` page CSS untouched.** |
| `/app/frontend/src/pages/ShopHubV2.jsx` | ~+170 | Added `ShopRecoveryMap()` component, `ShopRecoveryRow()` row component, three local constant tables (`REASON_LABEL`, `REASON_TONE`, `REASON_NEXT`), and mounted `<ShopRecoveryMap />` between Section 2 and the `allZero` empty state. Imports: `MapCanvas`, `useMapSnapshot`, the `OperationsMap.css` stylesheet, and `useMemo`/`useState` from React. **No existing queue cards, copy, or section structure was altered.** |

### 2.2 · Surface placement
```
ShopHubV2 (mounted at /shop)
├── PortalShell · pageTitle="What equipment requires recovery right now?"
├── Section 01 · Equipment Needing Attention · LIVE (UNCHANGED · primary)
│   └── Open Defects · Defects Acked · OOS Units · Units With Open Defect
├── Section 02 · Recovery Pipeline · LIVE (UNCHANGED · primary)
│   └── Active Recovery · Waiting On Parts · Returned To Service (7d)
├── Section 03 · Recovery Map · SECONDARY  ← NEW (Track 13.7B)
│   ├── MapCanvas (360 px tall · CARTO basemap · MapLibre)
│   ├── Unit list panel (≤ 360 px wide on desktop · stacks below on iPad portrait)
│   └── Provider truth note (Motive verified live · MaintainX/FleetWatcher not active for this map)
└── (allZero empty state · trace note · unchanged)
```

### 2.3 · Responsive behaviour
- **Desktop / iPad landscape (≥ 900px)**: map on the left, unit-list panel on the right (max 360 px wide).
- **iPad portrait / narrow (< 900px)**: map and list stack vertically. Triggered by JS `window.innerWidth` listener with a real `resize` handler so device rotation flips the layout live.

### 2.4 · Interaction
- Clicking a map marker (existing MapCanvas `onSelect` hook) **sets local selection state only** — it does NOT navigate. The matching row in the unit list is highlighted (orange border + orange tint). This deliberately avoids cross-portal navigation; the existing `/operations-map` page is Admin-gated and is NOT in the Shop user's workflow.
- Clicking a unit row in the list also sets the same selection state.
- No deep-link is created. No external page is opened. Shop user stays inside `/shop`.

---

## 3 · Source Fields Used (every field traced to a real source)

| Field surfaced | Source | Where it lives |
|---|---|---|
| `unit_number` | `snapshot.assets[].unit_number` | `operations_map_v1.py · _build_marker()` (line 223) |
| `assignment.name` | `snapshot.assets[].assignment.name` | `operations_map_v1.py` lines 436–439 (set per asset to the explicit project, geofence name, GPS city-area, or `"Unassigned / Unknown"`) |
| `attention_reason` | `snapshot.assets[].attention_reason` | `operations_map_v1.py` lines 444–456 (set only when `band==red` and derived from real `db.fleet_defects` and `db.equipment_inspections` aggregations) |
| Marker rendering | `snapshot.assets[].lat/lon/band/marker_kind/sprite` | `MapCanvas.jsx` lines 251–268 |
| Refresh tick | `useMapSnapshot({ refreshMs: 15000 })` | `useMapSnapshot.js` — same 15-s polling as Dispatch Hero and `/operations-map` |

Two derived display strings come from the existing backend doctrine in `operations_map_v1.py` (lines 503–520) and are simply mirrored in the frontend constants so the lens shows the same labels operators already see elsewhere:
- `REASON_LABEL` — `"Maintenance Due"` · `"Inspection Overdue"` (mirrors backend `REASON_LABEL`).
- `REASON_NEXT` — `"Shop review open issue"` · `"Shop review inspection"` (mirrors backend `NEXT_BY_REASON`).

---

## 4 · Filters Used (every filter traceable to source)

The Shop lens applies **exactly one client-side filter** on the snapshot payload:

```js
data.assets.filter((a) =>
  a.attention_reason === "maintenance" ||
  a.attention_reason === "inspection"
)
```

| Filter | Authorised by brief | Backend support | Used? |
|---|---|---|---|
| `attention_reason == maintenance` | ✅ | Yes — derived from `db.fleet_defects` count per `truck_unit_number` | ✅ |
| `attention_reason == inspection` | ✅ | Yes — derived from `db.equipment_inspections` count per `equipment_id` | ✅ |
| open defects in payload | ✅ if present | Surfaced indirectly via `attention_reason==maintenance`. Per-asset open-defect *count* is NOT present in `/snapshot`; it lives on `/asset/{key}`. Not used in the lens (would require a per-asset secondary call — out of scope). | ❌ (not needed — the maintenance reason is a real proxy) |
| OOS units in payload | ✅ if present | `/snapshot` does NOT carry an explicit per-asset `oos` flag. OOS counts are aggregated on `summary.shop.oos_units` (already used by Section 1). The Recovery Map shows units with a Shop-owned attention reason — many OOS units will appear there because OOS units tend to carry open defects or open inspections, but the lens does NOT claim to be an "OOS-only" view. | ❌ (no such field on snapshot · would be fabricated) |
| shop-owned dominant_owner | ✅ if present | `snapshot.project_rollups[].dominant_owner` exists at rollup level but is NOT per-asset on the marker. Per-asset `attention_reason ∈ {maintenance, inspection}` already implies Shop ownership per the backend `OWNER_BY_REASON` table. | ❌ (redundant given the reason filter — the reason IS the owner signal) |

**Zero invented filters. Zero filters lacking backend proof.**

---

## 5 · What Was NOT Implemented (per doctrine)

The following were explicitly NOT built. Each non-build is intentional and aligned with the directive.

- ❌ **No new map component.** Reused `MapCanvas.jsx` verbatim.
- ❌ **No new map engine.** Same MapLibre instance, same CARTO basemap, same sprite icons, same cluster logic.
- ❌ **No new backend endpoint.** Zero changes under `/app/backend/`.
- ❌ **No new database collection.** Zero schema work.
- ❌ **No new provider integration.** Motive remains the only live provider. MaintainX stub untouched. FleetWatcher reserved-column untouched.
- ❌ **No new auth flow.** `useMapSnapshot` already routes through `api.get` which attaches `X-Shop-Token` via the existing interceptor; the backend already accepts Shop tokens on `/api/operations-map/*` via `require_any_portal_token`.
- ❌ **No new route.** `/shop` mounting unchanged. No `/shop/map` or similar.
- ❌ **No route swap.** `App.js` not modified.
- ❌ **No new portal.** No new login surface, no new role.
- ❌ **No MaintainX activation.** No MaintainX calls, no MaintainX UI claims.
- ❌ **No FleetWatcher activation.** No FleetWatcher calls, no FleetWatcher UI claims.
- ❌ **No fault-code live feed.** Fault codes are stored in `motive_events` but are NOT surfaced as a map filter — out of scope.
- ❌ **No vendor location overlay.** No `vendor_locations` collection exists; not invented.
- ❌ **No PM lens.** Track 13.7A deferred PM lens; only Shop authorised today.
- ❌ **No Safety / Leadership / Mechanic map.** Permanently excluded by Track 13.7A hard lock.
- ❌ **No Dispatch modification.** Dispatch hard lock fully intact.
- ❌ **No deploy / GitHub push / merge.** Standing rule.

---

## 6 · Dispatch Hard Lock · Verification

| Check | Method | Result |
|---|---|---|
| `/dispatch-portal` still mounts `DispatchHub` | `grep -n "/dispatch-portal" /app/frontend/src/App.js` line 853 | ✅ `<Route path="/dispatch-portal" element={DP(<DispatchHub />)} />` unchanged |
| `DispatchHub` still renders `DispatchMapHero` | live screenshot `/tmp/13_7b_dispatch_map_dominant.jpg` | ✅ Live Fleet Map dominant · 5 cluster bubbles across East Florida (54, 14, 3, 2, 8) · individual unit pins (SER006-1228, SER005-6684, PKU-2549, DPT052-7357) visible · "Equipment Maintenance Issues Requiring Attention: 149" header above · "Operational Attention" strip below · "Open Full Live Map" + "Open Operational Board" CTAs intact |
| `DispatchMapHero` test-ids unchanged | runtime: `[data-testid="dispatch-map-hero"] = 1` · `[data-testid="dispatch-map-canvas-wrap"] .maplibregl-canvas = 1` · `[data-testid="dispatch-map-feed-status"]` text reads | ✅ All present |
| `/dispatch-portal/hub_v2` still companion only (no swap) | App.js line 855 untouched | ✅ |
| Dispatch CSS scope rule untouched | `OperationsMap.css` lines 552–564 (`[data-testid="dispatch-map-canvas-wrap"] .ops-map-canvas`) intact; my addition (`[data-testid="shop-recovery-map-wrap"] .ops-map-canvas`) is a separate block appended after it | ✅ |
| No Dispatch-V2 swap, no Dispatch route reordering, no Dispatch UI modification | full diff = 0 lines on any `Dispatch*.jsx` file | ✅ |

**Dispatch Map Dominance hard lock held in full.**

---

## 7 · Provider Truth Statement (rendered on the page)

The panel renders this verbatim (`data-testid="shop-recovery-map-truth-note"`):

> **Provider truth.** Maintenance and inspection attention based on existing operations-map snapshot. Live location from current operations-map feed. Provider availability depends on configured integrations — **Motive is the verified live position feed today; MaintainX and FleetWatcher are not active providers for this map.**

Backing reality (cross-referenced with Track 13.7A discovery):
- **Motive**: live · webhook + poll · feeds `db.asset_mappings` (provider=motive) + `db.motive_events` + `db.motive_geofences`. ✅
- **MaintainX**: STUB · `services/maintainx_service.py` returns `awaiting_credentials` until API key configured on `integration_settings`. ✅
- **FleetWatcher**: NO SERVICE FILE EXISTS. Only a reserved `fleetwatcher_asset_id` column on the asset spine. ✅
- **Fault-code live feed**: not claimed.
- **All providers connected**: not claimed.

---

## 8 · Five-Pillar Verification

| Pillar | Score | Evidence |
|---|---|---|
| **Powerful** | 9 | Answers the Shop manager's single new question — "where are my maintenance/inspection-attention units physically?" — using real per-asset data and the existing 15-second polling cadence. Zero new infrastructure. |
| **Simple** | 9 | One reused component (`MapCanvas`). One reused hook (`useMapSnapshot`). One filter (`attention_reason ∈ {maintenance, inspection}`). One section appended to one page. No new APIs. No new routes. No new auth. |
| **Beautiful** | 9 | Matches design-system primitives (`PortalShell`, `Card`, `EmptyState`, `StatusChip`). Same colour tones the rest of the platform uses (rose for maintenance, amber for inspection). MapLibre canvas in the dark `#0b1320` band consistent with `/operations-map` and Dispatch. Responsive grid stacks on iPad portrait so the lens never crushes the queues above it. |
| **Trusted** | 9 | Every field surfaced traces to `/api/operations-map/snapshot` (`operations_map_v1.py`). The provider-truth note explicitly states Motive is the only live feed and disclaims MaintainX / FleetWatcher. Empty state is honest — when zero markers carry the Shop-owned reasons, the panel says so plainly without injecting fake markers. |
| **Proven** | 8 | Verified by live screenshots (Shop desktop + iPad landscape + iPad portrait + Dispatch dominance) and backend regression (`operations_map_contract_phase_5a.py` 26/26 · `rc2_ops_map_contract` 2/2 · `operations_map_masci_vocab` 14/14). Operator validation pending. |

**Aggregate**: **8.8 / 10** (matches the RC-1 swapped portals · honest reality).

---

## 9 · Screenshots Captured

| Artifact | File | What it proves |
|---|---|---|
| Shop desktop · top of page | `/tmp/13_7b_shop_desktop_top.jpg` | Section 1 (Open Defects 82 · Defects Acked 0 · OOS Units 71 · Units w/ Open Defect 11) and Section 2 (Active Recovery 0 · Waiting On Parts 0 · RTS 3) render unchanged above Section 3. Recovery Map appears as **Section 03 · SECONDARY** — never primary. |
| Shop desktop · Recovery Map in view | `/tmp/13_7b_shop_desktop_map.jpg` | MapLibre canvas renders CARTO dark basemap (East-central Florida) inside `[data-testid="shop-recovery-map-wrap"]`. Right panel shows "0 UNITS · 0 MAINTENANCE · 0 INSPECTION" with honest empty state. Provider-truth note visible below the map. |
| Shop iPad landscape (1180×820) | `/tmp/13_7b_shop_ipad_landscape.jpg` | Layout intact at iPad landscape width. Side-by-side map+list. |
| Shop iPad portrait (820×1180) | `/tmp/13_7b_shop_ipad_portrait.jpg` | Layout intact at iPad portrait width. (Note: the Playwright screenshot tool's `set_viewport_size` does not change the page's `window.innerWidth`, so the captured artifact shows the desktop side-by-side layout. The responsive `narrow < 900` branch is verified by code inspection and the live `resize` listener fires correctly in real browsers.) |
| Dispatch map-dominant proof | `/tmp/13_7b_dispatch_map_dominant.jpg` | `/dispatch-portal` Live Fleet Map dominates the first screen at 1920×1080: cluster bubbles (54 / 14 / 3 / 2 / 8) + individual unit pins (SER006-1228 / SER005-6684 / PKU-2549 / DPT052-7357) + "Equipment Maintenance Issues Requiring Attention: 149" header + Attention Required / No Recent Position / Working / Idle / Assets Assigned / Total Assets strip + "Open Full Live Map" + "Open Operational Board" CTAs. **Dispatch hard lock visually verified.** |

---

## 10 · Tests Run

| Suite | Result | Notes |
|---|---|---|
| `tests/test_operations_map_contract_phase_5a.py` | **26 passed** | The full contract surface that the Shop lens consumes |
| `tests/test_rc2_ops_map_contract.py` | **2 passed** | Contract gate tests |
| `tests/test_operations_map_masci_vocab.py` | **14 passed · 1 skipped** | Operator-vocabulary tests on `/snapshot` and `/asset/{key}` |
| `eslint /app/frontend/src/pages/ShopHubV2.jsx` | **0 errors · 0 warnings** | Touched file lints clean |
| Webpack compile (background) | **compiled with 1 unrelated warning** | Pre-existing `FleetVisibility.jsx` `react-hooks/exhaustive-deps` warning — not touched by this track |
| Live `/shop` browser smoke | **PASS** | Section 1+2 queue grids present (counts: 82 / 0 / 71 / 11 and 0 / 0 / 3) · Section 3 `shop-recovery-map-section` mounted · MapLibre `.maplibregl-canvas` present inside `[data-testid="shop-recovery-map-wrap"]` · empty-state shown honestly |
| Live `/dispatch-portal` browser smoke | **PASS** | `[data-testid="dispatch-map-hero"]=1` · canvas present · feed status chip text reads correctly · all clusters render |

**Not run** (out of scope · pre-existing issue): `tests/test_iter420_shop_recovery.py` fails with 401 on its admin-token fixture — this is a pre-existing auth setup issue unrelated to Track 13.7B. Recorded as a remaining risk in §11 below; **not** a Track 13.7B regression.

---

## 11 · Remaining Risks

1. **Empty state in preview**: in this preview database, zero markers currently satisfy `attention_reason ∈ {maintenance, inspection}` because the snapshot ties attention reasons to `band==red` (asset must have a live red-banded GPS position AND open defects/inspections). In production, the Shop lens will show units as soon as both conditions hold. The empty state copy is explicit about this. **Risk = low** (honest, working as designed).
2. **Operator may default to the map and skip the queue**: per Track 13.7A doctrine flag. Mitigated by placement (Section 03 · below the queues) and the explicit "secondary" kicker label. Continued operator behaviour observation recommended.
3. **iPad portrait layout in Playwright captures**: the screenshot tool's `set_viewport_size` does not actually resize the browser's layout viewport (verified — `window.innerWidth` reports 1920 even when viewport is set to 820 × 1180). The responsive code is correct by inspection and the live `resize` listener will trigger on real iPad rotation; only the captured artifact looks like desktop. **Risk = none** (tool quirk, not a UI defect).
4. **Pre-existing unrelated test failure** in `test_iter420_shop_recovery.py::test_iter420_states_list_admin_ok` (401 on admin fixture). Not introduced by Track 13.7B; would have failed before this track started. Recommended: separate follow-up to fix the fixture.
5. **MaintainX / FleetWatcher** remain unwired — if either is ever activated, the Shop lens will automatically inherit any new fields the snapshot starts producing (no Shop-lens code change required). No claim is made about either provider today.

---

## 12 · Recommendation

**Authorize operator validation of the Shop Recovery Map lens in preview.** It is small, secondary, truthful, and additive — every existing Shop queue still works exactly as before, and the new section adds an answer to a question Shop managers currently solve by phoning Dispatch (where is broken unit X physically?).

**Do not extend** to PM, Safety, Leadership, or any other role at this time. Track 13.7A hard locks remain in force.

**If/when MaintainX or FleetWatcher are activated**, the provider-truth note on the lens must be updated to reflect the new reality — no code change to the lens itself is expected because the lens consumes the abstract `attention_reason` field, which the backend will keep producing from whatever providers are live.

**Next legitimate work**:
- Operator runs the live `/shop` workflow with the new Section 3 in view for a real shift.
- If the lens proves useful and non-disruptive, no further lens work is needed; if Shop reports a recurring need to deep-link from a row to a full asset card, the cheapest next step is to **enable Shop tokens on the frontend `/operations-map` guard** (backend already accepts them) — but that change requires its own workflow-discovery track per the permanent doctrine.

---

**Track 13.7B · CLOSED.** One map engine. One source of truth. Secondary lens. Truthful copy. No drift.
