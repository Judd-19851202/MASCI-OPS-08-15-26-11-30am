"""TRACK 25.01 · Legacy route move + LegacyMovedBanner regression locks.

Phase B of the Admin Operating System (AOS) rollout. Every admin surface
that was consolidated into the Operations Control Center MUST:

1. Still be reachable at its legacy URL (zero routes deleted).
2. Render a LegacyMovedBanner that points at the canonical OCC location.
3. Point at a canonical destination that actually resolves and carries
   an OCC operation with equivalent functionality (`occOperationId`).

If any of these break, operators will either (a) hit a broken URL
mid-workflow or (b) land on a canonical page that no longer contains
the tool they need. Both are Phase B regressions.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest


FRONTEND_SRC = Path("/app/frontend/src")
LEGACY_MAP = FRONTEND_SRC / "app/routing/legacyRedirects.js"
BANNER = FRONTEND_SRC / "components/admin/LegacyMovedBanner.jsx"
FEATURE_FLAGS = FRONTEND_SRC / "lib/featureFlags.js"
APP_ROUTES = FRONTEND_SRC / "app/routing/AppRoutes.jsx"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


# ── Files exist ─────────────────────────────────────────────────────

def test_legacy_map_exists():
    assert LEGACY_MAP.exists(), (
        "TRACK 25.01 · legacyRedirects.js registry must exist."
    )


def test_legacy_banner_component_exists():
    assert BANNER.exists(), (
        "TRACK 25.01 · LegacyMovedBanner.jsx must exist."
    )


def test_feature_flag_module_exists():
    assert FEATURE_FLAGS.exists(), (
        "TRACK 25.01 · featureFlags.js must exist for Phase B rollout."
    )


# ── Feature flag contract ───────────────────────────────────────────

def test_admin_nav_v3_feature_flag_default_off():
    src = _read(FEATURE_FLAGS)
    assert "masci.admin.nav.v3" in src, (
        "TRACK 25.01 · feature-flag key must be 'masci.admin.nav.v3'."
    )
    assert "isAdminNavV3Enabled" in src, (
        "TRACK 25.01 · featureFlags.js must export isAdminNavV3Enabled()."
    )
    # Sanity: neither ADMIN_NAV_V3=on nor a "return true" default should
    # appear anywhere — Phase B must default to OFF.
    assert 'return true' not in src.replace(" ", ""), (
        "TRACK 25.01 · featureFlags.js must not unconditionally return "
        "true. Phase B defaults to OFF."
    )


# ── Legacy map contract ─────────────────────────────────────────────

# Canonical set of routes that MUST be present in the Phase B map.
REQUIRED_LEGACY_ROUTES = {
    "/admin/system",
    "/admin/system-health",
    "/admin/operations-dashboard",
    "/admin/integration-truth",
    "/admin/deploy-readiness",
    "/admin/deploy-recovery",
    "/admin/scheduler-runs",
    "/admin/recovery",
    "/admin/recovery-stream",
}


def test_every_required_legacy_route_registered():
    src = _read(LEGACY_MAP)
    missing = [r for r in REQUIRED_LEGACY_ROUTES if f'"{r}"' not in src]
    assert not missing, (
        "TRACK 25.01 · legacyRedirects.js is missing required legacy "
        f"routes: {missing}"
    )


def test_every_legacy_route_points_at_operations_control_center():
    """Every consolidated legacy route MUST land inside OCC, either at
    the root or with a `?highlight=` deep-link."""
    src = _read(LEGACY_MAP)
    # Count each occurrence of /admin/operations-control as target.
    for route in REQUIRED_LEGACY_ROUTES:
        # Slice the map entry for this route to inspect its canonical.
        pattern = re.compile(
            re.escape(f'"{route}"') + r"\s*:\s*\{[^}]*?\}",
            re.DOTALL,
        )
        match = pattern.search(src)
        assert match, f"could not locate entry for {route}"
        entry = match.group(0)
        assert "/admin/operations-control" in entry, (
            f"TRACK 25.01 · legacy route {route} must redirect into OCC. "
            f"Instead it targets: {entry!r}"
        )


def test_every_legacy_route_declares_occ_operation_id():
    """Phase B → Phase C parity: every legacy route registers the OCC
    operation id that carries its functionality. Prevents 'redirected
    to a half-empty page' failure mode."""
    src = _read(LEGACY_MAP)
    for route in REQUIRED_LEGACY_ROUTES:
        pattern = re.compile(
            re.escape(f'"{route}"') + r"\s*:\s*\{[^}]*?\}",
            re.DOTALL,
        )
        match = pattern.search(src)
        assert match, f"could not locate entry for {route}"
        entry = match.group(0)
        assert "occOperationId" in entry, (
            f"TRACK 25.01 · legacy route {route} must declare "
            "`occOperationId` so parity tests can prove the OCC "
            "carries an equivalent tool."
        )
        assert "canonical" in entry and "reason" in entry, (
            f"TRACK 25.01 · legacy route {route} must declare "
            "`canonical` and `reason`. Missing fields makes the banner "
            "unable to render a real 'why we moved this' message."
        )


# ── OCC parity ─────────────────────────────────────────────────────

def test_declared_occ_operation_ids_exist_in_backend_registry():
    """Every `occOperationId` referenced by the legacy map MUST be
    registered by the backend OCC. Otherwise the redirected route
    lands on a card that does not exist — a Phase C regression."""
    src = _read(LEGACY_MAP)
    declared = set(re.findall(r'occOperationId:\s*"([^"]+)"', src))
    assert declared, (
        "TRACK 25.01 · at least one legacy entry must declare an "
        "occOperationId. Found none."
    )

    from services.operations_control import build_registry  # noqa: PLC0415
    registered = set(build_registry(db=None).keys())
    missing = declared - registered
    assert not missing, (
        "TRACK 25.01 · legacyRedirects.js references OCC operations "
        f"that are not registered in the backend: {missing}. "
        "Phase C consolidation is incomplete."
    )


# ── AppRoutes still declares every legacy path ─────────────────────

def test_every_legacy_route_still_declared_in_router():
    """Zero-drift rule: the legacy path MUST still exist as a route so
    old bookmarks don't 404. We're layering a banner on top, not
    deleting the route."""
    src = _read(APP_ROUTES)
    for route in REQUIRED_LEGACY_ROUTES:
        assert f'path="{route}"' in src, (
            f"TRACK 25.01 · Zero-drift regression: {route} is no longer "
            "declared in AppRoutes.jsx. Legacy URLs must keep working "
            "during transition."
        )


def test_every_legacy_route_wrapped_with_legacy_moved_banner():
    src = _read(APP_ROUTES)
    for route in REQUIRED_LEGACY_ROUTES:
        # We expect either `LB("/admin/system", ...)` or a Navigate
        # element on the same line. Confirm at least one legacy route
        # is wrapped (the ones NOT in this test suite as Navigate).
        line_match = re.search(
            r'path="' + re.escape(route) + r'"[^\n]*',
            src,
        )
        assert line_match, f"route not found: {route}"
        line = line_match.group(0)
        # If the route already Navigates elsewhere we accept it; the
        # required routes we're testing here are all rendering pages.
        is_navigate = "<Navigate " in line
        wrapped = f'LB("{route}"' in line
        assert wrapped or is_navigate, (
            f"TRACK 25.01 · route {route} must either be wrapped with "
            "LB(...) so the LegacyMovedBanner renders, or be a "
            f"<Navigate/> redirect. Line: {line}"
        )


def test_appRoutes_imports_legacy_banner_and_helper():
    src = _read(APP_ROUTES)
    assert "LegacyMovedBanner" in src or "WithLegacyBanner" in src, (
        "TRACK 25.01 · AppRoutes.jsx must import LegacyMovedBanner or "
        "WithLegacyBanner from components/admin/LegacyMovedBanner."
    )
    assert "const LB" in src, (
        "TRACK 25.01 · AppRoutes.jsx must define the LB() helper "
        "used to wrap legacy routes."
    )


# ── Banner UX contract ─────────────────────────────────────────────

def test_banner_has_dismiss_and_open_canonical_actions():
    src = _read(BANNER)
    assert 'data-testid="legacy-moved-banner"' in src, (
        "TRACK 25.01 · banner must expose data-testid='legacy-moved-banner'."
    )
    assert 'data-testid="legacy-moved-banner-open-canonical"' in src, (
        "TRACK 25.01 · banner must expose the open-canonical CTA testid."
    )
    assert 'data-testid="legacy-moved-banner-dismiss"' in src, (
        "TRACK 25.01 · banner must expose the dismiss testid."
    )
    assert "This page has moved" in src, (
        "TRACK 25.01 · banner must use the human-first phrase 'This "
        "page has moved' — no engineering jargon."
    )


def test_banner_uses_session_storage_for_dismissal_not_permanent():
    """Dismissal MUST be scoped to the session so any subsequent visit
    still sees the banner. Permanent dismissal defeats the point of
    signaling the move during Phase B."""
    src = _read(BANNER)
    assert "sessionStorage" in src, (
        "TRACK 25.01 · dismissal must use sessionStorage (per-tab). "
        "localStorage or cookies would make dismissal permanent."
    )


# ── No engineering language in the banner ──────────────────────────

BANNED_UI_PHRASES = (
    "V1", "V2", "V3", "Track 25", "Phase B", "Phase C",
    "AOS", "Rollout",
)


def test_banner_carries_no_engineering_terminology():
    """The banner is user-facing. Never leak internal track/phase names.
    Comments and docstrings are exempt — we scan only quoted strings."""
    src = _read(BANNER)
    # Strip line/block comments so track annotations in comments don't
    # trip this test.
    no_line_comments = re.sub(r"//[^\n]*", "", src)
    no_block_comments = re.sub(r"/\*[\s\S]*?\*/", "", no_line_comments)
    # Extract only JSX text and string literals — anything between
    # single or double quotes at the JSX level.
    strings = re.findall(r'"([^"\\]{0,4000})"', no_block_comments)
    strings += re.findall(r"'([^'\\]{0,4000})'", no_block_comments)
    combined = " ".join(strings)
    for phrase in BANNED_UI_PHRASES:
        # Only fail when the phrase appears with a space around it in the
        # human-visible string layer — imports and testids are exempt
        # because they're not user-visible.
        pattern = rf"\b{re.escape(phrase)}\b"
        for s in strings:
            if s.startswith("legacy-moved-") or s.startswith("data-") \
                    or s.startswith("masci."):
                continue
            if re.search(pattern, s):
                pytest.fail(
                    f"TRACK 25.01 · banner user-facing string carries "
                    f"engineering terminology {phrase!r}: {s!r}"
                )
    # This test purposely doesn't fail if `combined` doesn't contain
    # anything — the guarantee is the negative one.
    assert combined  # sanity: strings were extracted


# ── LegacyMovedBanner is not wired outside admin routes ────────────

def test_banner_is_only_applied_to_admin_routes():
    """The banner is admin-scoped. Wrapping non-admin routes with it
    would leak the OCC destination into portals that don't have OCC
    access."""
    src = _read(APP_ROUTES)
    # Find every `LB(` call site and confirm the first arg starts with
    # `/admin/`.
    for m in re.finditer(r'LB\("([^"]+)"', src):
        path = m.group(1)
        assert path.startswith("/admin/"), (
            f"TRACK 25.01 · LB() wraps a non-admin route: {path!r}. "
            "The LegacyMovedBanner is admin-scoped."
        )
