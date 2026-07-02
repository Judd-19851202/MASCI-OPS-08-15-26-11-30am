"""Track 19.24 · Live UI Wiring & Human Discoverability lock tests.

Locks the navigation-wiring fix that makes Historical Records Intake
reachable from the HR portal without knowing the URL.

Zero-drift: this track added ZERO backend changes and ZERO new pages —
only two sidebar items and two HR-hub tiles that already-existing
routes were entitled to.
"""
from __future__ import annotations

from pathlib import Path


SIDEBAR = Path("/app/frontend/src/components/hr/sidebar/HrSideNavV2.jsx")
HR_HUB = Path("/app/frontend/src/pages/HrHubV2.jsx")


def test_hr_sidebar_v2_lists_historical_records_intake():
    src = SIDEBAR.read_text(encoding="utf-8")
    assert '/hr/historical-records/intake' in src
    assert 'Historical Records Intake' in src


def test_hr_sidebar_v2_lists_historical_records_queue():
    src = SIDEBAR.read_text(encoding="utf-8")
    assert '/hr/historical-records/queue' in src
    assert 'Historical Records Queue' in src


def test_hr_sidebar_v2_places_them_in_compliance_and_records_group():
    src = SIDEBAR.read_text(encoding="utf-8")
    # Doctrine: legacy record uploads sit alongside training records +
    # document expirations, not under "People Operations" (which is
    # active-workforce operations).
    compliance_start = src.index('id: "compliance-records"')
    compliance_end = src.index('id: "guidance"')
    body = src[compliance_start:compliance_end]
    assert '/hr/historical-records/intake' in body
    assert '/hr/historical-records/queue' in body


def test_hr_hub_v2_has_historical_intake_destination_tile():
    src = HR_HUB.read_text(encoding="utf-8")
    assert 'data-testid="hr-hub-v2-dest-historical-intake"' in src
    assert '/hr/historical-records/intake' in src


def test_hr_hub_v2_has_historical_queue_destination_tile():
    src = HR_HUB.read_text(encoding="utf-8")
    assert 'data-testid="hr-hub-v2-dest-historical-queue"' in src
    assert '/hr/historical-records/queue' in src


def test_hr_hub_v2_destination_tiles_carry_short_descriptions():
    """Six Pillars · Simple: a first-day HR user must read the tile and
    know instantly what it does. Locks the human-readable descriptions."""
    src = HR_HUB.read_text(encoding="utf-8")
    assert 'Upload legacy files' in src
    assert 'Approve, reject, reassign' in src


def test_zero_drift_no_new_routes_added_by_this_track():
    """Track 19.24 is nav-wiring only. No new routes should appear in
    App.js beyond the ones Track 19.21b + 19.22 already added."""
    src = Path("/app/frontend/src/App.js").read_text(encoding="utf-8")
    # These four routes MUST still be here (previous tracks).
    for r in ("/hr/historical-records/intake",
              "/hr/historical-records/queue",
              "/hr/historical-records/batches",
              "/hr/historical-records/batches/:batchId"):
        assert r in src
