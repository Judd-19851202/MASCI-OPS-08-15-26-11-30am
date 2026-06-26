"""TRACK 15.95 · Operations Map Phone Overflow Fix — regression.

Locks the contract that ``/operations-map`` at phone-390 viewport has
zero horizontal overflow. The original defect (PROD-15.94-BS01) was
the top-row stat banner using ``grid-template-columns: repeat(3, 1fr)``
without ``minmax(0, 1fr)`` clamps — long hint strings forced
min-content track sizes that pushed the banner past the viewport.

Static guards only. The full live overflow assertion lives in the
Track 15.86 browser smoke runtime gate.
"""
from __future__ import annotations

import os
import re


CSS_PATH = "/app/frontend/src/components/operations-map/OperationsMap.css"


def _read_css() -> str:
    with open(CSS_PATH, encoding="utf-8") as f:
        return f.read()


def test_css_file_exists():
    assert os.path.exists(CSS_PATH), f"missing CSS file: {CSS_PATH}"


def test_mobile_banner_uses_minmax_clamp():
    """The @media (max-width:900px) banner rule must use
    ``minmax(0, 1fr)`` columns so long content cannot push tracks
    past the viewport. This is the exact root cause from
    PROD-15.94-BS01."""
    src = _read_css()
    # Must include a 3-column banner using minmax(0, 1fr)
    pattern = re.compile(
        r"\.ops-map-banner\s*\{\s*grid-template-columns:\s*"
        r"repeat\(3,\s*minmax\(0,\s*1fr\)\)",
        re.MULTILINE,
    )
    assert pattern.search(src), (
        "Track 15.95 invariant violated: .ops-map-banner mobile rule "
        "must use grid-template-columns: repeat(3, minmax(0, 1fr)). "
        "The unclamped repeat(3, 1fr) form re-introduces "
        "PROD-15.94-BS01 (banner overflow on phone-390)."
    )


def test_mobile_banner_has_phone_480_collapse():
    """At <=480px the banner must collapse to 2 columns so each tile
    still fits its hint text without horizontal scroll on a 390px
    phone."""
    src = _read_css()
    pattern = re.compile(
        r"@media\s*\(\s*max-width:\s*480px\s*\)\s*\{[^}]*"
        r"\.ops-map-banner[^}]*"
        r"grid-template-columns:\s*repeat\(2,\s*minmax\(0,\s*1fr\)\)",
        re.DOTALL,
    )
    assert pattern.search(src), (
        ".ops-map-banner must collapse to 2 columns at <=480px to "
        "guarantee zero overflow at phone-390."
    )


def test_tile_has_min_width_zero_on_mobile():
    """Banner tiles must allow shrinking (min-width: 0) on mobile
    so flex/grid children honor track clamps."""
    src = _read_css()
    # The 15.95 fix block must contain this exact declaration.
    assert ".ops-map-banner .tile { min-width: 0; }" in src, (
        "Track 15.95: .ops-map-banner .tile { min-width: 0 } missing"
    )


def test_tile_text_wraps_on_mobile():
    """Long hint strings must wrap (overflow-wrap: anywhere) so
    they cannot force min-content track widths."""
    src = _read_css()
    assert ".ops-map-banner .tile .hint" in src and \
           "overflow-wrap: anywhere" in src, (
        "Track 15.95: hint text must declare overflow-wrap: anywhere"
    )


def test_track_15_83_project_card_constraints_preserved():
    """The Track 15.83 iPad bleed fix MUST remain intact — project
    cards must still have constrained min/max widths at <=1024 and
    <=640. Regression-lock the substrings."""
    src = _read_css()
    assert "@media (max-width: 1024px)" in src, "15.83 tablet rule missing"
    assert "@media (max-width: 640px)" in src, "15.83 phone rule missing"
    # The 15.83 1024 block sets project-card min/max 220/260
    assert "min-width: 220px" in src and "max-width: 260px" in src, \
        "15.83 iPad project-card constraint regressed"
    # The 15.83 640 block sets 200/240
    assert "min-width: 200px" in src and "max-width: 240px" in src, \
        "15.83 phone project-card constraint regressed"


def test_track_15_86_smoke_gate_runner_unchanged():
    """The smoke gate runner file must still exist and still
    enforce the canonical contract — no weakening to make 15.95
    pass by lowering the bar."""
    path = "/app/backend/tests/browser_smoke/run_browser_smoke.py"
    assert os.path.exists(path), "smoke runner deleted"
    src = open(path, encoding="utf-8").read()
    assert "/operations-map" in src, "smoke gate route list missing /operations-map"
    assert "/admin" in src, "smoke gate route list missing /admin"
    assert "/trench-safety" in src, "smoke gate route list missing /trench-safety"
    assert "390" in src and "768" in src and "1024" in src, \
        "smoke gate must still enforce 3 breakpoints"


def test_track_15_93_bootstrap_module_still_present():
    """Track 15.93 bootstrap must not have been touched by this
    track. Canonical module + startup hook position invariant."""
    assert os.path.exists("/app/backend/lib/system_bootstrap.py")
    server = open("/app/backend/server.py", encoding="utf-8").read()
    bs = server.find("_track_15_93_run_system_bootstrap")
    flip = server.find("_iter453_6_flip_ready_flag")
    assert bs != -1 and flip != -1
    assert bs < flip, "15.93 startup ordering disturbed"


def test_deployment_gate_includes_track_15_95():
    """The new regression file MUST be wired into the permanent
    gate list."""
    src = open("/app/scripts/deployment_gate.py", encoding="utf-8").read()
    assert "test_track_15_95_operations_map_phone_overflow.py" in src, (
        "deployment_gate.py must include the 15.95 regression file"
    )
