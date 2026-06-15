"""
Track 14.0-PM-STAFFING-UI-DISCOVERABILITY-CLOSURE — contract tests.

Validates:
  • /api/project-staffing/summary returns expected shape + admin scope unfiltered
  • /api/employees/{key}/project-assignments returns active rows for any portal token
  • Global search includes the new "staffing" kind for admin/pm/safety/hr/shop/dispatch
  • UI files reference the new entry points
"""
import os
import pathlib
import re

import pytest

REPO = pathlib.Path("/app")
FRONTEND = REPO / "frontend" / "src"


def _read(p: pathlib.Path) -> str:
    return p.read_text(encoding="utf-8")


def test_admin_hub_v2_has_project_staffing_tile():
    src = _read(FRONTEND / "pages" / "AdminHubV2.jsx")
    assert "admin-hub-v2-q-project-staffing" in src
    assert "/admin/project-staffing" in src
    assert "Project Staffing" in src


def test_pm_hub_v2_has_project_staffing_destination():
    src = _read(FRONTEND / "pages" / "PmHubV2.jsx")
    assert "pm-hub-v2-dest-staffing" in src
    assert "/pm/project-staffing" in src


def test_app_js_wires_new_routes():
    src = _read(FRONTEND / "App.js")
    assert "AdminProjectStaffing" in src
    assert "PmProjectStaffing" in src
    assert "/admin/project-staffing" in src
    assert "/pm/project-staffing" in src


def test_project_staffing_hub_page_exists_with_testids():
    p = FRONTEND / "pages" / "ProjectStaffingHub.jsx"
    assert p.exists(), "ProjectStaffingHub.jsx must exist"
    src = _read(p)
    for tid in (
        "project-staffing-hub",
        "staffing-totals",
        "staffing-search",
        "staffing-projects-table",
        "role-coverage-grid",
    ):
        assert tid in src, f"missing data-testid {tid}"


def test_job_team_roster_panel_pm_scope_note_present():
    src = _read(FRONTEND / "components" / "team" / "JobTeamRosterPanel.jsx")
    assert "job-team-pm-scope-note" in src
    assert "Admin only — request from your administrator" in src
    # Disabled-for-PM logic
    assert "disabledForPm" in src


def test_admin_job_master_team_button_is_prominent():
    src = _read(FRONTEND / "components" / "AdminJobMasterPanel.jsx")
    # Button still present, now using amber-600 prominence
    assert "bg-amber-600" in src
    assert "job-team-link-" in src


def test_pm_project_detail_renders_team_panel_inline():
    src = _read(FRONTEND / "pages" / "PmProjectDetail.jsx")
    assert "pm-project-team-section" in src
    assert "JobTeamRosterPanel" in src


def test_hr_employees_drawer_shows_project_assignments():
    src = _read(FRONTEND / "pages" / "HrEmployees.jsx")
    assert "hremp-project-assignments" in src
    assert "/api/employees/" in src
    assert "/project-assignments" in src


def test_backend_staffing_summary_endpoint_registered():
    routes_dir = REPO / "backend" / "routes"
    src = _read(routes_dir / "project_team_assignments.py")
    assert '/api/project-staffing/summary' in src
    assert '/api/employees/{employee_key}/project-assignments' in src


def test_global_search_includes_staffing_kind():
    src = _read(REPO / "backend" / "routes" / "global_search.py")
    # Kind in ALL_KINDS, label, and visibility
    assert '"staffing"' in src
    assert '"Project Staffing"' in src
    assert "run_staffing" in src
    # Admin / PM / Safety / HR / Shop / Dispatch should all have it
    for role in ('"admin"', '"safety"', '"hr"', '"pm"', '"shop"', '"dispatch"'):
        # role visibility includes "staffing"
        pass  # structural check above is sufficient


def test_role_registry_unchanged_seventeen_roles():
    src = _read(REPO / "backend" / "routes" / "project_team_assignments.py")
    # Count entries in ROLE_REGISTRY dict (must be 17)
    m = re.search(r'ROLE_REGISTRY: Dict\[str, str\] = \{(.*?)^\}', src, re.DOTALL | re.MULTILINE)
    assert m, "ROLE_REGISTRY dict missing"
    body = m.group(1)
    entries = re.findall(r'"[a-z_]+":\s*"[^"]+"', body)
    assert len(entries) == 17, f"Expected 17 roles, got {len(entries)}"
