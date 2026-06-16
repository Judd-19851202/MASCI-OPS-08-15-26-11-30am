"""TRACK 14.0-PLATFORM-DISCOVERABILITY · Wave B regression tests.

Locks the 5 new global-search probes against drift:
  · daily_reports
  · meetings
  · inspections
  · trench_assets
  · jha_plans

Also asserts role-aware visibility — Safety must NOT see daily_reports,
HR / leadership must NOT see trench_assets, etc.

All tests are read-only and pointed at the preview backend via the
shared REACT_APP_BACKEND_URL the rest of the suite uses.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Set

import pytest

# Import the static constants directly — this is a contract lock, not
# an HTTP test, so we don't need a live cluster to assert structure.
from routes.global_search import (  # noqa: E402
    ALL_KINDS,
    KIND_LABELS,
    KIND_VISIBILITY,
)


# ─── Contract: 5 Wave B kinds present ───────────────────────────────

WAVE_B_KINDS = {
    "daily_reports",
    "meetings",
    "inspections",
    "trench_assets",
    "jha_plans",
}


def test_wave_b_kinds_present_in_all_kinds():
    assert WAVE_B_KINDS.issubset(set(ALL_KINDS)), (
        f"Missing Wave B kinds in ALL_KINDS: {WAVE_B_KINDS - set(ALL_KINDS)}"
    )


def test_wave_b_kinds_have_labels():
    for k in WAVE_B_KINDS:
        assert k in KIND_LABELS, f"Missing label for new kind {k!r}"
        assert KIND_LABELS[k], f"Empty label for kind {k!r}"


# ─── Contract: role-aware visibility map ─────────────────────────────

def test_admin_sees_all_wave_b_kinds():
    admin_kinds: Set[str] = set(KIND_VISIBILITY["admin"])
    assert WAVE_B_KINDS.issubset(admin_kinds), (
        "Admin should see every Wave B kind. Missing: "
        f"{WAVE_B_KINDS - admin_kinds}"
    )


def test_safety_visibility_matches_http_gate():
    """Safety reads /api/inspections, /api/meetings, /api/jhas via
    `_read_gate` and /api/trench-safety/assets via the public bridge —
    but does NOT have HTTP access to /api/daily-reports (admin-only
    via require_admin). The search-visibility map must mirror this."""
    safety = set(KIND_VISIBILITY["safety"])
    for k in ("meetings", "inspections", "jha_plans", "trench_assets"):
        assert k in safety, f"Safety should see {k!r} in global search"
    assert "daily_reports" not in safety, (
        "Safety must NOT see daily_reports in search — no HTTP read access"
    )


def test_pm_visibility_includes_pm_scoped_kinds():
    pm = set(KIND_VISIBILITY["pm"])
    # PM has /api/daily-reports + /api/meetings + /api/inspections +
    # /api/jhas access via require_admin's PM-token branch, all
    # PM-scoped via compute_pm_scope.
    for k in ("daily_reports", "meetings", "inspections", "jha_plans"):
        assert k in pm, f"PM should see {k!r} (PM-scoped)"
    # PM does NOT search trench assets — assets are cross-project
    # and would leak across PM scope without a dedicated filter.
    assert "trench_assets" not in pm, "PM should not search trench assets (cross-project)"


def test_hr_visibility_for_daily_reports_only():
    hr = set(KIND_VISIBILITY["hr"])
    # HR has /hr/daily-reports portal page → daily_reports searchable
    assert "daily_reports" in hr, "HR should see daily_reports (HR portal page exists)"
    # HR has no read access to meetings/inspections/jhas/trench-assets
    for k in ("meetings", "inspections", "jha_plans", "trench_assets"):
        assert k not in hr, f"HR should NOT see {k!r} (no HTTP read access)"


def test_shop_sees_trench_assets_only():
    shop = set(KIND_VISIBILITY["shop"])
    assert "trench_assets" in shop, "Shop runs the repair queue — must search trench assets"
    for k in ("daily_reports", "meetings", "inspections", "jha_plans"):
        assert k not in shop, f"Shop should NOT see {k!r} in search"


def test_dispatch_and_leadership_unchanged():
    """Dispatch and Field Leadership were intentionally NOT given any
    Wave B kinds — their search surface stays narrow."""
    dispatch = set(KIND_VISIBILITY["dispatch"])
    leadership = set(KIND_VISIBILITY["leadership"])
    for k in WAVE_B_KINDS:
        assert k not in dispatch, f"Dispatch should not get {k!r}"
        assert k not in leadership, f"Leadership should not get {k!r}"


# ─── Contract: Safety portal routes exist in App.js ──────────────────

APP_JS = Path(__file__).resolve().parents[2] / "frontend" / "src" / "App.js"


def test_safety_portal_meetings_route_present():
    src = APP_JS.read_text()
    assert 'path="/safety-portal/meetings"' in src, (
        "TRACK 14.0-DISCOVERABILITY Wave A fix removed: /safety-portal/meetings route missing"
    )
    # Must be SF-guarded
    line = next(ln for ln in src.split("\n") if 'path="/safety-portal/meetings"' in ln)
    assert "SF(" in line, "/safety-portal/meetings must be safety-guarded (SF wrapper)"


def test_safety_portal_inspections_route_present():
    src = APP_JS.read_text()
    assert 'path="/safety-portal/inspections"' in src, (
        "TRACK 14.0-DISCOVERABILITY Wave B regression: /safety-portal/inspections route missing"
    )
    line = next(ln for ln in src.split("\n") if 'path="/safety-portal/inspections"' in ln and ":id" not in ln)
    assert "SF(" in line, "/safety-portal/inspections must be SF-guarded"


def test_safety_portal_jha_plans_route_present():
    src = APP_JS.read_text()
    assert 'path="/safety-portal/jha-plans"' in src, (
        "TRACK 14.0-DISCOVERABILITY Wave B regression: /safety-portal/jha-plans route missing"
    )
    line = next(ln for ln in src.split("\n") if 'path="/safety-portal/jha-plans"' in ln)
    assert "SF(" in line, "/safety-portal/jha-plans must be SF-guarded"


def test_admin_daily_reports_redirect_targets_admin_daily():
    """Wave A D-FIX-2 lock: /admin/daily-reports must redirect to
    /admin/daily, NOT /hr/daily-reports (which 403'd admins)."""
    src = APP_JS.read_text()
    line = next(
        (ln for ln in src.split("\n") if 'path="/admin/daily-reports"' in ln),
        None,
    )
    assert line, "/admin/daily-reports redirect missing"
    assert 'to="/admin/daily"' in line, (
        "/admin/daily-reports must redirect to /admin/daily (Wave A D-FIX-2)"
    )
    assert "/hr/daily-reports" not in line, (
        "Regression: /admin/daily-reports must NOT redirect to /hr/daily-reports"
    )
