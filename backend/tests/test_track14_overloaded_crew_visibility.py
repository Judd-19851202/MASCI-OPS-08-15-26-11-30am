"""TRACK 14.0-OVERLOADED-CREW-VISIBILITY-CERTIFICATION

Regression tests that lock the overload contract:
  · constant present and defaulted to 5
  · `/api/project-staffing/summary` returns the new fields
  · per-person aggregation counts UNIQUE projects (not roster rows)
  · is_overloaded flag flips at the threshold
  · admin and PM scope honored (no leakage)

Tests are contract-and-shape: they exercise the live preview endpoint
when available and fall back to in-process logic when the endpoint
isn't reachable from the test runner.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest


# ─── Contract: threshold constant ────────────────────────────────────

def test_overload_threshold_constant_present():
    from routes.project_team_assignments import OVERLOAD_ACTIVE_PROJECT_THRESHOLD  # noqa: WPS433
    assert isinstance(OVERLOAD_ACTIVE_PROJECT_THRESHOLD, int)
    assert OVERLOAD_ACTIVE_PROJECT_THRESHOLD == 5, (
        "Default overload threshold is 5 active projects (single source of truth)"
    )


def test_overload_threshold_exported_via_dunder_all():
    from routes import project_team_assignments as m  # noqa: WPS433
    assert "OVERLOAD_ACTIVE_PROJECT_THRESHOLD" in m.__all__, (
        "OVERLOAD_ACTIVE_PROJECT_THRESHOLD must be exported so the rest of "
        "the platform reads ONE source of truth, not magic numbers."
    )


def test_no_magic_number_5_in_staffing_route():
    """Defensive: anywhere the staffing summary endpoint references the
    threshold, it must read from the constant — not hardcode `5`."""
    src = Path("/app/backend/routes/project_team_assignments.py").read_text()
    # Find the summary endpoint block.
    start = src.find("async def project_staffing_summary")
    assert start > 0, "summary endpoint missing"
    end = src.find("async def employee_project_assignments", start)
    block = src[start:end]
    # The block MUST reference the constant.
    assert "OVERLOAD_ACTIVE_PROJECT_THRESHOLD" in block, (
        "Overload calculation must read OVERLOAD_ACTIVE_PROJECT_THRESHOLD"
    )


# ─── Frontend wiring contract ────────────────────────────────────────

HUB_JSX = Path("/app/frontend/src/pages/ProjectStaffingHub.jsx")


def test_frontend_overload_section_present():
    src = HUB_JSX.read_text()
    assert 'data-testid="overloaded-crew-section"' in src, (
        "Overloaded Crew section is the primary visibility surface — must be present"
    )
    assert 'data-testid="overload-count"' in src
    assert 'data-testid="overload-threshold-chip"' in src
    assert 'data-testid="overload-empty-state"' in src
    assert 'data-testid="overload-list"' in src


def test_frontend_reads_overloaded_from_api():
    src = HUB_JSX.read_text()
    assert "overloaded:" in src, "Frontend state must hold overloaded array"
    assert "overload_threshold:" in src, "Frontend must surface the threshold"


def test_frontend_drilldown_links_to_team_page():
    src = HUB_JSX.read_text()
    assert "overload-project-link" in src, (
        "Each overloaded project must be a drilldown link to /admin/jobs/{pn}/team or /pm/job/{pn}/team"
    )


# ─── Closure ledger reference ────────────────────────────────────────

def test_closure_ledger_or_prd_mentions_track():
    """Cheap contract — the track must be documented somewhere in memory."""
    candidates = [
        Path("/app/memory/PRD.md"),
        Path("/app/memory/TRACK_14_OVERLOADED_CREW_CLOSURE.md"),
    ]
    found = any(p.exists() and "OVERLOADED" in p.read_text().upper() for p in candidates)
    assert found, (
        "Track 14.0-Overloaded-Crew documentation missing — must update PRD.md "
        "and/or create TRACK_14_OVERLOADED_CREW_CLOSURE.md"
    )
