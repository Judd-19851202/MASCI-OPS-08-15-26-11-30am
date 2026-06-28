"""TRACK 18.07 · Design System Enforcement + Deferred Polish Closure
regression lock.

This file complements the linter (`test_track_18_07_design_system_linter.py`)
by asserting the documentation deliverables exist, the YELLOW items
are closed, the carve-outs are honored, and the deployment gate is
wired.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path("/app")
MEMORY = ROOT / "memory"
BACKEND = ROOT / "backend"
GATE = ROOT / "scripts" / "deployment_gate.py"
FRONTEND_SRC = ROOT / "frontend" / "src"

CERT = MEMORY / "TRACK_18_07_DESIGN_SYSTEM_ENFORCEMENT.md"
LINTER_RULES = MEMORY / "DESIGN_SYSTEM_LINTER_RULES.md"
DESIGN_SYSTEM = MEMORY / "OPERATIONAL_DESIGN_SYSTEM.md"
LINTER = BACKEND / "tests" / "test_track_18_07_design_system_linter.py"


# ===========================================================================
# 1–7 · Required artifacts present.
# ===========================================================================
def test_01_certification_doc_exists():
    assert CERT.exists()


def test_02_linter_rules_doc_exists():
    assert LINTER_RULES.exists()


def test_03_design_system_updated_with_audit_timeline_section():
    src = DESIGN_SYSTEM.read_text()
    assert "Audit Timeline Date Format" in src
    # All four pattern rows present.
    assert "Today · h:mm A" in src
    assert "MMM d · h:mm A" in src
    assert "MMM d, yyyy · h:mm A" in src
    assert "timezone abbreviation" in src


def test_04_linter_file_exists():
    assert LINTER.exists()


def test_05_linter_file_defines_at_least_5_rule_tests():
    """The linter ships at least one test per rule (R1–R5) plus the
    workspace-identity batch."""
    src = LINTER.read_text()
    for rule in ("test_lint_no_raw_no_data_empty_state",
                 "test_lint_no_raw_developer_error_text",
                 "test_lint_no_legacy_restricted_state_wording",
                 "test_lint_no_vague_ctas",
                 "test_lint_no_user_facing_dispatch_portal"):
        assert rule in src, f"Linter missing rule test: {rule}"


def test_06_linter_documents_allowlist():
    src = LINTER.read_text()
    assert "LINTER_ALLOWLIST" in src


def test_07_linter_documents_carve_outs_for_internal_registries():
    """Allow-list must include the documented engineering carve-outs."""
    src = LINTER.read_text()
    for f in ("lib/portalContinuity.js", "lib/returnContext.js",
              "lib/permissions.js"):
        assert f in src, f"Allow-list missing internal registry: {f}"


# ===========================================================================
# 8–17 · Yellow items closed (file-level evidence).
# ===========================================================================
def test_08_dispatch_change_password_uses_canonical():
    src = (FRONTEND_SRC / "pages" / "DispatchChangePassword.jsx").read_text()
    assert 't("Transportation Operations")' in src
    assert 't("Dispatch Portal")' not in src


def test_09_hr_change_password_uses_canonical():
    src = (FRONTEND_SRC / "pages" / "HrChangePassword.jsx").read_text()
    assert 't("Human Resources")' in src
    assert 't("HR Portal")' not in src


def test_10_hr_hub_kicker_uses_canonical():
    src = (FRONTEND_SRC / "pages" / "HrHub.jsx").read_text()
    assert 't("Human Resources")' in src


def test_11_pm_change_password_uses_canonical():
    src = (FRONTEND_SRC / "pages" / "PmChangePassword.jsx").read_text()
    assert 't("Project Management")' in src


def test_12_view_daily_report_uses_canonical():
    src = (FRONTEND_SRC / "pages" / "ViewDailyReport.jsx").read_text()
    assert 't("Project Management")' in src


def test_13_safety_change_password_uses_canonical():
    src = (FRONTEND_SRC / "pages" / "SafetyChangePassword.jsx").read_text()
    assert 't("Safety Operations")' in src


def test_14_safety_audits_uses_canonical():
    src = (FRONTEND_SRC / "pages" / "SafetyAudits.jsx").read_text()
    assert 't("Safety Operations")' in src


def test_15_safety_forms_records_uses_canonical():
    src = (FRONTEND_SRC / "pages" / "SafetyFormsRecords.jsx").read_text()
    assert 't("Safety Operations")' in src


def test_16_admin_dispatch_shell_uses_canonical():
    src = (FRONTEND_SRC / "pages" / "admin" / "AdminDispatch.jsx").read_text()
    assert 'title="Transportation Operations"' in src


def test_17_field_leadership_records_uses_canonical():
    src = (FRONTEND_SRC / "pages" / "FieldLeadershipRecords.jsx").read_text()
    assert 't("Administration")' in src


def test_18_field_leadership_view_uses_canonical():
    src = (FRONTEND_SRC / "pages" / "FieldLeadershipView.jsx").read_text()
    assert 't("Administration")' in src
    assert 't("Project Management")' in src
    assert 't("Admin Console")' not in src
    assert 't("PM Hub")' not in src


def test_19_deploy_recovery_uses_canonical():
    src = (FRONTEND_SRC / "pages" / "admin" / "DeployRecovery.jsx").read_text()
    assert ">Transportation Operations</Link>" in src
    assert ">Dispatch Portal</Link>" not in src


def test_20_intelligence_empty_state_is_operational():
    src = (FRONTEND_SRC / "pages" / "transportation" / "_intelligence.jsx").read_text()
    # Replaced "No data" with an operational empty state.
    assert ">No data<" not in src
    assert "scored yet" in src


# ===========================================================================
# 21–26 · Carve-outs preserved.
# ===========================================================================
def test_21_no_new_collections():
    src = (BACKEND / "server.py").read_text()
    assert "db.track_18_07_" not in src


def test_22_dispatch_token_alias_preserved():
    src = (BACKEND / "server.py").read_text()
    assert "X-Dispatch-Token" in src


def test_23_admin_route_prefix_preserved():
    src = (BACKEND / "routes" / "transportation_relationships.py").read_text()
    assert 'prefix="/api/admin/transportation"' in src


def test_24_dispatch_login_route_preserved():
    src = (BACKEND / "routes" / "dispatch_portal_auth.py").read_text()
    assert "/dispatch/login" in src


def test_25_rbac_admin_strict_guard_intact():
    src = (BACKEND / "routes" / "transportation_experience.py").read_text()
    assert "require_admin_dep" in src


def test_26_design_system_certification_intact():
    """Track 18.06 deliverables still in place."""
    for f in (MEMORY / "OPERATIONAL_DESIGN_SYSTEM.md",
              MEMORY / "AUTHENTICATED_WORKSPACE_DESIGN_AUDIT.md",
              MEMORY / "TRACK_18_06_OPERATIONAL_DESIGN_SYSTEM_CERTIFICATION.md"):
        assert f.exists()


# ===========================================================================
# 27–29 · Linter wiring.
# ===========================================================================
def test_27_linter_wired_into_deployment_gate():
    src = GATE.read_text()
    assert "test_track_18_07_design_system_linter.py" in src


def test_28_track_enforcement_doc_wired_into_deployment_gate():
    src = GATE.read_text()
    assert "test_track_18_07_design_system_enforcement.py" in src


def test_29_certification_declares_go():
    src = CERT.read_text()
    assert "GO" in src


# ===========================================================================
# 30 · Flake investigation documented.
# ===========================================================================
def test_30_flake_investigation_documented():
    src = CERT.read_text()
    assert "15.79E" in src or "15_79e" in src
    assert "ordering" in src.lower() or "isolation" in src.lower()
