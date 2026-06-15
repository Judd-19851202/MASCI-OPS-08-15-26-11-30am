"""TRACK 14.0-S2A · iPad Field Certification (Phases 4-11 + Amendment F)
contract regression suite.

Pins the three things that closed in this session:

  1. Phase 4 / 2A · `.field-glance-anchor` adoption on the 9 critical
     workflow page-headers (SafetyCorrectiveActions delegates via
     SafetyShell — documented exception).
  2. Phase 6A · `aria-busy` adoption on the 9 critical-workflow submit
     buttons so the global `button[aria-busy="true"]` CSS shimmer in
     index.css attaches automatically while saving.
  3. Multi-tab SSO auto-elevation (iteration_515 finding) — the four
     portal /login pages (Admin / PM / HR / Safety) MUST redirect away
     on mount when a valid same-portal token already exists in
     localStorage.

These tests run as fast static-source checks. The corresponding
runtime evidence (multi-viewport, multi-tab, throttled-network,
persona walkthroughs, stress loop) is captured in
/app/test_reports/iteration_515.json.
"""
from __future__ import annotations

from pathlib import Path

import pytest

PAGES = Path("/app/frontend/src/pages")
INDEX_CSS = Path("/app/frontend/src/index.css")


# ── Adoption: `.field-glance-anchor` on critical-workflow h1 ────


CRITICAL_GLANCE_FILES = [
    "NewDailyReport.jsx",
    "NewMeeting.jsx",
    "NewIncident.jsx",
    "NewEquipmentInspection.jsx",
    "NewQaqcInspection.jsx",
    "PublicTimeOff.jsx",
    "FieldLeadershipFormPage.jsx",
    "trench_safety/PublicExcavationForm.jsx",
]


@pytest.mark.parametrize("rel", CRITICAL_GLANCE_FILES)
def test_critical_workflow_h1_has_glance_anchor(rel: str):
    """Each critical-workflow page-header must carry the
    `.field-glance-anchor` class so a tired user can resolve
    "where am I?" in under 3 seconds (Phase 2A Glance Test)."""
    p = PAGES / rel
    src = p.read_text(encoding="utf-8")
    assert "field-glance-anchor" in src, (
        f"{rel} has no `.field-glance-anchor` on its h1 — Phase 2A Glance Test"
        f" adoption MISSING. Add the class to the top-most page heading."
    )


# ── Adoption: aria-busy on critical-workflow submit buttons ──────


CRITICAL_SUBMIT_FILES = [
    "NewDailyReport.jsx",
    "NewMeeting.jsx",
    "NewIncident.jsx",
    "NewEquipmentInspection.jsx",
    "NewQaqcInspection.jsx",
    "SafetyCorrectiveActions.jsx",
    "PublicTimeOff.jsx",
    "FieldLeadershipFormPage.jsx",
    "trench_safety/PublicExcavationForm.jsx",
]


@pytest.mark.parametrize("rel", CRITICAL_SUBMIT_FILES)
def test_critical_workflow_submit_has_aria_busy(rel: str):
    """The submit button on each critical workflow must wire
    `aria-busy={savingState}` so the global
    `button[aria-busy="true"]` shimmer rule in index.css attaches
    automatically — Phase 6A Speed Perception adoption."""
    p = PAGES / rel
    src = p.read_text(encoding="utf-8")
    assert "aria-busy=" in src, (
        f"{rel} has no `aria-busy=` on its submit button — Phase 6A "
        f"Speed Perception adoption MISSING. Add `aria-busy={{saving}}`"
        f" (or whichever in-flight flag the form uses) to the submit Button."
    )


# ── Global CSS rule: aria-busy shimmer present ───────────────────


def test_index_css_has_aria_busy_shimmer_rule():
    """The CSS shimmer that backs the aria-busy adoption above must
    exist in index.css — otherwise the adoption is decorative only."""
    css = INDEX_CSS.read_text(encoding="utf-8")
    assert 'button[aria-busy="true"]' in css, (
        "Missing `button[aria-busy=\"true\"]` shimmer rule in index.css. "
        "Add it back — Phase 6A Speed Perception depends on it."
    )
    assert "field-busy-shimmer" in css


# ── Multi-tab SSO auto-elevation (iteration_515 fix) ─────────────


SSO_AUTO_ELEVATION_CASES = [
    # (file, expected_redirect_target_substring)
    ("AdminLogin.jsx", "/admin/hub"),
    ("PmLogin.jsx", "/pm"),
    ("HrLogin.jsx", "/hr"),
    ("SafetyLogin.jsx", "/safety-portal"),
]


@pytest.mark.parametrize("rel,target", SSO_AUTO_ELEVATION_CASES)
def test_portal_login_auto_elevates_on_existing_token(rel: str, target: str):
    """Each portal /login page must include a useEffect that
    redirects to its dashboard when a same-portal token already
    exists in localStorage. This is the fix for the iteration_515
    multi-tab SSO defect.
    """
    p = PAGES / rel
    src = p.read_text(encoding="utf-8")
    # Must reference the Multi-tab SSO marker comment OR explicitly
    # check the same-portal token getter and navigate to the target.
    has_marker = "Multi-tab SSO auto-elevation" in src
    has_target_navigate = (
        f'navigate("{target}"' in src
        or f"navigate('{target}'" in src
        or f'nav("{target}"' in src
        or f"nav('{target}'" in src
    )
    assert has_marker and has_target_navigate, (
        f"{rel} missing multi-tab SSO auto-elevation hook. Add a useEffect "
        f"that calls navigate('{target}', {{replace: true}}) when the "
        f"matching portal token already exists in localStorage."
    )
