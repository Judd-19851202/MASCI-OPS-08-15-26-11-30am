"""
tests/test_pm_staffing_completion.py — Track 14.0-PM-STAFFING-COMPLETION.

Locks the expanded staffing role model so future commits cannot:
  * remove the four new project-level roles (Project Administrator,
    Project Coordinator, QA/QC Rep, HR Rep),
  * silently merge them back into existing roles,
  * undo the safety_lead → safety_rep / dispatcher_contact →
    dispatch_rep relabels,
  * forget to translate legacy aliases at read-time,
  * remove the always-visible Team Card from PM Project Health,
  * weaken the PM self-serve permission gate.

Combine with test_project_team_assignments.py (live API CRUD) for full
coverage: this file is the *contract* lock, that file is the
*runtime* lock.
"""
from __future__ import annotations

from pathlib import Path

import pytest

REPO = Path("/app")


# ─────────────────────────────────────────────────────────────────────
# Closed-set role registry — the canonical contract
# ─────────────────────────────────────────────────────────────────────


def test_role_registry_includes_all_seventeen_roles():
    from routes.project_team_assignments import ROLE_REGISTRY
    expected = {
        "pm": "Project Manager",
        "co_pm": "Co-PM",
        "assistant_pm": "Assistant PM",
        "superintendent": "Superintendent",
        "foreman": "Foreman",
        "safety_rep": "Safety Representative",
        "project_engineer": "Project Engineer",
        "project_administrator": "Project Administrator",
        "project_coordinator": "Project Coordinator",
        "qaqc_rep": "QA/QC Representative",
        "hr_rep": "HR Representative",
        "asset_admin": "Asset Admin",
        "locate_coordinator": "811 Locate Coordinator",
        "dispatch_rep": "Dispatch Representative",
        "shop_contact": "Shop Contact",
        "executive_oversight": "Executive Oversight",
        "read_only_stakeholder": "Read-only Stakeholder",
    }
    missing = {k: v for k, v in expected.items()
               if ROLE_REGISTRY.get(k) != v}
    assert not missing, (
        f"ROLE_REGISTRY drifted from the staffing contract. "
        f"Missing / wrong-labelled keys: {missing!r}"
    )
    extra = set(ROLE_REGISTRY) - set(expected)
    assert not extra, (
        f"ROLE_REGISTRY grew unexpectedly: {extra!r}. New roles must "
        "land in this regression first to lock the contract."
    )


def test_legacy_role_aliases_translate_correctly():
    from routes.project_team_assignments import (
        LEGACY_ROLE_ALIASES, _canonical_role, ALL_ROLES,
    )
    # Aliases must point at live keys.
    for legacy, current in LEGACY_ROLE_ALIASES.items():
        assert current in ALL_ROLES, (
            f"Legacy alias {legacy!r} → {current!r} but {current!r} "
            "is not in ALL_ROLES — translation would 404."
        )
    # The two specific relabels must be aliased.
    assert LEGACY_ROLE_ALIASES.get("safety_lead") == "safety_rep"
    assert LEGACY_ROLE_ALIASES.get("dispatcher_contact") == "dispatch_rep"
    # _canonical_role passes through canonical keys unchanged.
    assert _canonical_role("safety_rep") == "safety_rep"
    assert _canonical_role("dispatch_rep") == "dispatch_rep"
    # And translates legacy keys.
    assert _canonical_role("safety_lead") == "safety_rep"
    assert _canonical_role("dispatcher_contact") == "dispatch_rep"
    # Empty / None passes through.
    assert _canonical_role(None) is None
    assert _canonical_role("") == ""


# ─────────────────────────────────────────────────────────────────────
# Permission gate — admin-only set hasn't expanded
# ─────────────────────────────────────────────────────────────────────


def test_admin_only_roles_remain_locked():
    """Only PM / Co-PM / Executive Oversight are admin-only. Everything
    else (including the 4 new roles) must be PM-assignable so a PM can
    actually run their project without filing an admin ticket."""
    from routes.project_team_assignments import (
        ADMIN_ONLY_ROLES, PM_ASSIGNABLE_ROLES, ALL_ROLES,
    )
    assert ADMIN_ONLY_ROLES == {"pm", "co_pm", "executive_oversight"}, (
        f"ADMIN_ONLY_ROLES drifted: {ADMIN_ONLY_ROLES!r}. PM staffing "
        "self-service is supposed to cover every other role."
    )
    # Every new role must be PM-assignable.
    for new_role in ("project_administrator", "project_coordinator",
                     "qaqc_rep", "hr_rep"):
        assert new_role in PM_ASSIGNABLE_ROLES, (
            f"PM cannot self-assign {new_role!r}. New role isn't wired "
            "into PM_ASSIGNABLE_ROLES."
        )
    # And the relabeled keys must also be PM-assignable.
    assert "safety_rep" in PM_ASSIGNABLE_ROLES
    assert "dispatch_rep" in PM_ASSIGNABLE_ROLES
    # Union check — nothing slipped through.
    assert PM_ASSIGNABLE_ROLES | ADMIN_ONLY_ROLES == ALL_ROLES


# ─────────────────────────────────────────────────────────────────────
# Frontend — always-visible Team Card on PM Command Center
# ─────────────────────────────────────────────────────────────────────


PM_CC = REPO / "frontend/src/pages/PmCommandCenter.jsx"


def test_pm_command_center_mounts_team_roster_card():
    """PM Command Center is the per-project "Overview" surface in the
    directive's vocabulary. It must mount the shared
    JobTeamRosterPanel inline so a PM never has to navigate to a
    separate `/team` route to see who is on the project.

    Regression locks the Team tab + the always-visible card body so
    future refactors can't silently remove the surface."""
    src = PM_CC.read_text()
    assert "JobTeamRosterPanel" in src, (
        "PmCommandCenter.jsx no longer references JobTeamRosterPanel. "
        "The always-visible Team Card has regressed — PMs will not "
        "see project staffing without a separate navigation click."
    )
    assert 'data-testid="pm-cc-team-card"' in src, (
        "Team Card test-id missing on PM Command Center. e2e cannot "
        "verify visibility."
    )
    assert 'data-testid="pm-cc-tab-team"' in src, (
        "Team tab trigger missing on PM Command Center."
    )
