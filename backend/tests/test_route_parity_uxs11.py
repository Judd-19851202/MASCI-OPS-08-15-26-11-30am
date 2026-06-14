"""
tests/test_route_parity_uxs11.py — Track 14.0-UXS-11 Platform Route
Parity Certification.

Pins the four user-evidenced drift routes to the shared PortalShell
chrome so future PRs cannot silently revert them to inline / ad-hoc
shells. Each guard is a static-analysis assertion — no live API
traffic — so they run anywhere.

Routes pinned (per the user's live-preview screenshots, 2026-02-14):
  * /project-health        → ProjectHealth.jsx     (PM portal)
  * /asset-transfers       → AssetTransfers.jsx    (PM portal)
  * /admin/jha-plans       → JhaPlansAdmin.jsx     (Safety portal)
  * /admin/trench-boxes    → TrenchBoxesAdmin.jsx  (Admin portal)

Closure ledger:
/app/memory/TRACK_14_0_UXS_11_PLATFORM_ROUTE_PARITY_CERTIFICATION_CLOSURE.md
"""
from __future__ import annotations

from pathlib import Path

import pytest

REPO = Path("/app")

EVIDENCE_ROUTES = {
    "ProjectHealth.jsx":           ("PmSideNavV2",     "PM Portal"),
    "AssetTransfers.jsx":          ("PmSideNavV2",     "PM Portal"),
    "JhaPlansAdmin.jsx":           ("SafetySideNavV2", "Safety Portal"),
    "TrenchBoxesAdmin.jsx":        ("AdminSideNavV2", "Admin"),
    "PoRequests.jsx":              ("PmSideNavV2",     "PM Portal"),
    # Sweep A (PM Portal + Safety dashboards · 2026-02-14 batch 2)
    "DailyReportsDashboard.jsx":   ("PmSideNavV2",     "PM Portal"),
    "IncidentsDashboard.jsx":      ("SafetySideNavV2", "Safety Portal"),
    "MeetingsDashboard.jsx":       ("SafetySideNavV2", "Safety Portal"),
    "DocumentExpirations.jsx":     ("HrSideNavV2",     "HR Portal"),
    "Tasks.jsx":                   ("AdminSideNavV2",  "Admin"),
    # Sweep A continuation (batch 3 · 2026-02-14)
    "PmQaqcList.jsx":              ("PmSideNavV2",     "PM Portal"),
    "HrEmployees.jsx":             ("HrSideNavV2",     "HR Portal"),
}


@pytest.mark.parametrize("page,expected", list(EVIDENCE_ROUTES.items()))
def test_evidence_route_uses_portal_shell(page, expected):
    """The 4 user-evidenced drift routes MUST render inside
    PortalShell with the correct domain sidebar. Without this they
    revert to inline / ad-hoc shells and the "leaves one application
    and enters another" defect this track exists to prevent comes
    back."""
    sidebar_name, portal_label = expected
    text = (REPO / "frontend/src/pages" / page).read_text()
    assert "import { PortalShell } from \"@/design-system\"" in text, (
        f"{page} no longer imports PortalShell. Route parity broken — "
        "the page will render without the unified MASCI chrome."
    )
    assert sidebar_name in text, (
        f"{page} no longer imports {sidebar_name}. Route parity broken "
        "— sidebar missing on this deep page."
    )
    assert "<PortalShell" in text, (
        f"{page} no longer wraps its return in <PortalShell>. Route "
        "parity broken — header / sidebar / blueprint-bg missing."
    )
    assert f"portalRole=\"{portal_label}" in text, (
        f"{page} portalRole no longer mentions the expected portal "
        f"label '{portal_label}'. Users will not see correct portal "
        "identity in the top chrome."
    )
    assert "sideNav={" in text, (
        f"{page} no longer passes a sideNav prop to PortalShell. "
        "Sidebar gone — drift returns."
    )


@pytest.mark.parametrize("page", list(EVIDENCE_ROUTES.keys()))
def test_evidence_route_does_not_import_legacy_chrome(page):
    """The 4 evidenced pages must not re-import the legacy
    `MasciLogo` / `HubBackLink` chrome components. PortalShell
    already provides the brand-bar + back-navigation, and re-introducing
    the legacy components creates the "two applications stitched
    together" defect that landed each of these routes on the user's
    drift list to begin with."""
    text = (REPO / "frontend/src/pages" / page).read_text()
    legacy_markers = [
        'from "@/components/MasciLogo"',
        'from "@/components/HubBackLink"',
    ]
    leaks = [m for m in legacy_markers if m in text]
    assert not leaks, (
        f"{page} re-introduced legacy chrome imports: {leaks!r}. "
        "PortalShell already renders the brand-bar; remove the "
        "duplicates or route drift returns."
    )
