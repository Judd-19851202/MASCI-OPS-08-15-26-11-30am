"""TRACK 15.82 · Dispatch Portal Layout + Roll-Off Operations.

Two-part regression lock following Track 15.81.

Part A — Dispatch Map Continuity Polish
  * `/dispatch-portal/map` route now mounts `DispatchOperationsMapPage`
    (a thin Dispatch-themed wrapper around the certified
    `OperationsMapPage`).
  * That wrapper MUST always render a `Back to Dispatch Hub` link
    pointing at `/dispatch-portal` so dispatchers never feel they left
    the Dispatch shell.
  * The Admin Console route `/operations-map` keeps the bare page —
    Admin RBAC is NOT altered.

Part B — Roll-Off Taxonomy
  * `services/asset_taxonomy.py` declares `"Roll-Off Truck"` as a
    canonical asset_type under the `Truck` class with DOT/preop/map
    behavior parity to other haul trucks.
  * `routes/pm_command_center.normalize_asset_kind` collapses every
    documented roll-off alias to the canonical key `roll_off_truck`.
  * `routes/operations_map_contract.FLEET_KINDS` includes every
    documented roll-off alias so map family classification and count
    tiles treat Roll-Off trucks as first-class fleet members.
  * Legacy crosswalks (`category` and `preop_equipment_type`) resolve
    every roll-off alias to ``("Truck", "Roll-Off Truck")``.

Existing asset types must remain unaffected.
"""
from __future__ import annotations

import re
from pathlib import Path

FRONTEND_SRC = Path("/app/frontend/src")
APP_JS = FRONTEND_SRC / "App.js"
# TRACK 22.5A · re-anchor to current routing shell.
APP_ROUTES = FRONTEND_SRC / "app" / "routing" / "AppRoutes.jsx"
DISPATCH_MAP_WRAPPER = FRONTEND_SRC / "pages/DispatchOperationsMapPage.jsx"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ─── Part A · Dispatch Map Continuity Polish ──────────────────────────


def test_dispatch_map_route_uses_dispatch_wrapper():
    """`/dispatch-portal/map` MUST render the Dispatch-themed wrapper
    (`DispatchOperationsMapPage`), not the bare `OperationsMapPage`."""
    src = (_read(APP_JS) + "\n" + _read(APP_ROUTES))
    pattern = re.compile(
        r'<Route\s+path="/dispatch-portal/map"\s+element=\{DP\('
        r'<DispatchOperationsMapPage\s*/>\)\}'
    )
    assert pattern.search(src), (
        "Track 15.82 regression: `<Route path=\"/dispatch-portal/map\" "
        "element={DP(<DispatchOperationsMapPage />)} />` is required so the "
        "Back-to-Dispatch-Hub breadcrumb always renders inside the "
        "Dispatch portal map."
    )


def test_admin_operations_map_route_keeps_bare_page():
    """`/operations-map` (Admin Console) MUST keep rendering the bare
    `OperationsMapPage` — NOT the Dispatch wrapper. The Dispatch
    breadcrumb belongs only inside Dispatch."""
    src = (_read(APP_JS) + "\n" + _read(APP_ROUTES))
    pattern = re.compile(
        r'<Route\s+path="/operations-map"\s+element=\{A\(<OperationsMapPage\s*/>\)\}'
    )
    assert pattern.search(src), (
        "Track 15.82 regression: Admin Console `/operations-map` must keep "
        "`element={A(<OperationsMapPage />)}` — do NOT swap in the Dispatch "
        "wrapper here."
    )


def test_dispatch_map_wrapper_has_back_to_hub_link():
    src = _read(DISPATCH_MAP_WRAPPER)
    # Must point at the Dispatch Hub root.
    assert 'to="/dispatch-portal"' in src, (
        "Track 15.82 regression: DispatchOperationsMapPage.jsx must "
        "include a `<Link to=\"/dispatch-portal\">` Back-to-Hub affordance."
    )
    # Must expose the canonical testid we test against in the browser.
    assert 'data-testid="dispatch-map-back-to-hub"' in src, (
        "Track 15.82 regression: DispatchOperationsMapPage.jsx must expose "
        "`data-testid=\"dispatch-map-back-to-hub\"` for browser automation."
    )
    # Must surface a Dispatch-themed breadcrumb container.
    assert 'data-testid="dispatch-map-breadcrumb"' in src, (
        "Track 15.82 regression: DispatchOperationsMapPage.jsx must expose "
        "`data-testid=\"dispatch-map-breadcrumb\"`."
    )
    # Must still mount the underlying OperationsMapPage (no map logic dup).
    assert "<OperationsMapPage" in src, (
        "Track 15.82 regression: DispatchOperationsMapPage.jsx must mount "
        "the underlying OperationsMapPage component — do not duplicate the "
        "operations map logic."
    )


def test_dispatch_map_wrapper_uses_dispatch_orange_breadcrumb():
    """Soft visual gate — breadcrumb uses the Dispatch orange palette
    (matches DispatchHub hero / DispatchMapHero borders)."""
    src = _read(DISPATCH_MAP_WRAPPER)
    assert "orange-" in src, (
        "Track 15.82 regression: DispatchOperationsMapPage.jsx breadcrumb "
        "should use Dispatch orange palette (matches DispatchHub)."
    )


# ─── Part B · Roll-Off Taxonomy ───────────────────────────────────────


def test_roll_off_truck_in_canonical_taxonomy():
    from services.asset_taxonomy import (
        ASSET_TYPES_BY_CLASS,
        VALID_ASSET_TYPES,
        behavior_for,
        is_valid_pair,
    )
    assert "Roll-Off Truck" in ASSET_TYPES_BY_CLASS["Truck"], (
        "Track 15.82: 'Roll-Off Truck' must be a canonical asset_type "
        "under the 'Truck' class."
    )
    assert "Roll-Off Truck" in VALID_ASSET_TYPES
    assert is_valid_pair("Truck", "Roll-Off Truck")
    b = behavior_for("Roll-Off Truck")
    # Same DOT/preop/insurance/map footprint as Dump Truck.
    assert b["requires_registration"] is True
    assert b["requires_insurance"] is True
    assert b["requires_pm"] is True
    assert b["requires_preop"] is True
    assert b["appears_on_map"] is True
    assert b["inspection_required"] is True
    assert b["renewal_tracking_required"] is True
    assert b["dot_required"] is True


def test_roll_off_legacy_crosswalk_category():
    from services.asset_taxonomy import classify_legacy
    # Every documented alias must resolve to ("Truck", "Roll-Off Truck")
    # via either category OR preop_equipment_type input.
    for alias in [
        "Roll-Off", "rolloff", "roll off", "Roll-Offs", "Rolloffs",
        "Roll-Off Trucks", "Rolloff Trucks", "Roll Off Trucks",
        "Container Truck", "Container Trucks",
    ]:
        out = classify_legacy(category=alias)
        assert out["asset_class"] == "Truck", f"{alias!r} → {out}"
        assert out["asset_type"] == "Roll-Off Truck", f"{alias!r} → {out}"


def test_roll_off_legacy_crosswalk_preop():
    from services.asset_taxonomy import classify_legacy
    for alias in [
        "Roll-Off", "rolloff", "roll off",
        "Roll-Off Truck", "Rolloff Truck", "Roll Off Truck",
        "Container Truck",
    ]:
        out = classify_legacy(preop_equipment_type=alias)
        assert out["asset_class"] == "Truck", f"{alias!r} → {out}"
        assert out["asset_type"] == "Roll-Off Truck", f"{alias!r} → {out}"


def test_normalize_asset_kind_collapses_roll_off_aliases():
    from routes.pm_command_center import (
        normalize_asset_kind,
        ROLL_OFF_CANONICAL,
        ROLL_OFF_DISPLAY_LABEL,
    )
    assert ROLL_OFF_CANONICAL == "roll_off_truck"
    assert ROLL_OFF_DISPLAY_LABEL == "Roll-Off Truck"
    aliases = [
        "rolloff", "roll-off", "roll off",
        "Roll-Off", "ROLLOFF", "Roll Off",
        "roll-off truck", "rolloff truck", "roll off truck",
        "Roll-Off Truck", "container truck", "Container Truck",
        "roll-offs", "rolloffs", "roll_off", "roll_off_truck",
    ]
    for a in aliases:
        out = normalize_asset_kind(a)
        assert out == ROLL_OFF_CANONICAL, (
            f"normalize_asset_kind({a!r}) returned {out!r}, expected "
            f"{ROLL_OFF_CANONICAL!r} — Track 15.82 alias regression."
        )


def test_normalize_asset_kind_preserves_existing_behavior():
    """Non-roll-off / non-road-plate values must pass through lowercased.
    This proves Track 15.82 did not change existing semantics."""
    from routes.pm_command_center import (
        normalize_asset_kind,
        ROAD_PLATE_CANONICAL,
    )
    # Road plate aliases still collapse to road_plate.
    assert normalize_asset_kind("Road Plate") == ROAD_PLATE_CANONICAL
    assert normalize_asset_kind("road plate") == ROAD_PLATE_CANONICAL
    # Untouched values pass through lowercased.
    assert normalize_asset_kind("Excavator") == "excavator"
    assert normalize_asset_kind("DUMP TRUCK") == "dump truck"
    assert normalize_asset_kind("Pickup Truck") == "pickup truck"
    assert normalize_asset_kind(None) is None
    assert normalize_asset_kind("") is None


def test_operations_map_fleet_family_recognizes_roll_off():
    """Roll-Off truck variants must land in the `fleet` family so map
    counts, filters, and marker fan-out treat them as fleet."""
    from routes.operations_map_contract import _asset_family
    aliases_lower = [
        "roll-off", "rolloff", "roll off",
        "roll-off truck", "rolloff truck", "roll off truck",
        "container truck", "container trucks", "roll_off_truck",
    ]
    for a in aliases_lower:
        fam = _asset_family(a)
        assert fam == "fleet", (
            f"_asset_family({a!r}) returned {fam!r} — Roll-Off must be "
            "classified as fleet for dispatch map visibility."
        )


def test_operations_map_existing_families_unchanged():
    """Sanity: Track 15.82 did not break existing family classification."""
    from routes.operations_map_contract import _asset_family
    assert _asset_family("dump truck") == "fleet"
    assert _asset_family("Excavator".lower()) == "heavy_equipment"
    assert _asset_family("road_plate") == "specialty:access_protection"
    assert _asset_family("light tower") == "specialty:support"
    assert _asset_family("") == "unknown"
    assert _asset_family(None) == "unknown"


def test_roll_off_marker_resolves_to_dump_truck_sprite():
    """Until a custom Roll-Off sprite ships, the V1 marker classifier
    must render Roll-Offs with the dump_truck sprite so they show on
    the map."""
    from routes.operations_map_v1 import _asset_kind_for_marker
    cases = [
        ("Roll-Off Truck", "RO-101"),
        ("rolloff truck", "RO-205"),
        ("Roll Off Truck", "RO-300"),
        ("Container Truck", "RO-1"),
        ("ROLL-OFF", "RO-99"),
    ]
    for et, un in cases:
        out = _asset_kind_for_marker(et, un)
        assert out == "dump_truck", (
            f"_asset_kind_for_marker({et!r}, {un!r}) returned {out!r} — "
            "Roll-Off should render with dump_truck sprite for map visibility."
        )


def test_roll_off_marker_does_not_steal_existing_sprites():
    from routes.operations_map_v1 import _asset_kind_for_marker
    # Existing classifications still resolve correctly.
    assert _asset_kind_for_marker("PAVER", "PV-1") == "paver"
    assert _asset_kind_for_marker("EXCAVATOR", "EXC-1") == "excavator"
    assert _asset_kind_for_marker("DUMP TRUCK", "DPT-1") == "dump_truck"
    assert _asset_kind_for_marker("WATER TRUCK", "WT-1") == "water_truck"
    assert _asset_kind_for_marker("PICKUP", "PKU-1") == "pickup"
