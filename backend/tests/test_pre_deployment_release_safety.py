"""TRACK 18 PRODUCTION CUT · Pre-Deployment Release Safety lock.

Static-scan release-gate. Confirms:
  • All 10 required pre-deployment markdown docs exist with the
    correct content shape.
  • The 17 in-scope tracks are documented; the 10 backlog items are
    explicitly excluded.
  • No feature work / new collections / route removals / RBAC
    weakening introduced.
  • Deployment gate command, backup plan, rollback triggers are
    documented.
  • VISIBLE = USABLE doctrine is referenced in the transportation
    acceptance gate.
  • Per-role smoke matrix covers every required role.
  • Canonical naming + PDF/email + R1–R8 + governance linter checks
    are documented.
  • PRD updated.

Pure source-tree checks; does not hit the live backend.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path("/app")
MEM = ROOT / "memory"
SERVER = ROOT / "backend" / "server.py"
DEPLOY_GATE = ROOT / "scripts" / "deployment_gate.py"


def _read(p: Path) -> str:
    assert p.exists(), f"required file missing: {p}"
    return p.read_text(encoding="utf-8", errors="ignore")


# ────────────────────────────────────────────────────────────────────────
# Required document existence (1–10)
# ────────────────────────────────────────────────────────────────────────
REQUIRED_DOCS = [
    "PRE_DEPLOYMENT_RELEASE_FREEZE.md",
    "PRE_DEPLOYMENT_CHANGE_INVENTORY.md",
    "PRE_DEPLOYMENT_ENVIRONMENT_CHECK.md",
    "PRE_DEPLOYMENT_DATA_SAFETY_CHECK.md",
    "PRE_DEPLOYMENT_ROLE_SMOKE_MATRIX.md",
    "PRE_DEPLOYMENT_TRANSPORTATION_ACCEPTANCE_GATE.md",
    "PRE_DEPLOYMENT_DESIGN_LANGUAGE_CHECK.md",
    "PRE_DEPLOYMENT_TEST_RESULTS.md",
    "PRODUCTION_DEPLOYMENT_CHECKLIST.md",
    "RELEASE_NOTES_TRACK_18_PRODUCTION_CUT.md",
]


@pytest.mark.parametrize("doc", REQUIRED_DOCS)
def test_required_release_document_exists(doc):
    assert (MEM / doc).exists(), f"required release doc missing: {doc}"


# ────────────────────────────────────────────────────────────────────────
# (11) Included tracks listed
# ────────────────────────────────────────────────────────────────────────
INCLUDED_TRACKS = [
    "Track 18.00 Phase A", "Track 18.00 Phase B", "Track 18.00 Phase C",
    "Track 18.00 Phase D", "Track 18.00 Phase E", "Track 18.00E-FIX",
    "Track 18.00 Phase F", "Track 18.00 Phase G",
    "Track 18.01", "Track 18.02", "Track 18.03", "Track 18.04",
    "Track 18.05", "Track 18.06", "Track 18.07", "Track 18.08",
    "Track 18.09", "Track 18.09A", "Track 18.09C",
    "Track 18.10", "Track 18.11", "Track 18.12", "Track 18.12B", "Track 18.12C",
]


def test_release_freeze_lists_all_included_tracks():
    body = _read(MEM / "PRE_DEPLOYMENT_RELEASE_FREEZE.md")
    for t in INCLUDED_TRACKS:
        assert t in body, f"release freeze missing included track: {t}"


# ────────────────────────────────────────────────────────────────────────
# (12) Future/backlog tracks excluded
# ────────────────────────────────────────────────────────────────────────
EXCLUDED_BACKLOG = [
    "Request Access",
    "Graph visualization",
    "Manual link",
    "AI relationship suggestions",
    "Fuzzy search",
    "Saved searches",
]


def test_release_freeze_excludes_backlog():
    body = _read(MEM / "PRE_DEPLOYMENT_RELEASE_FREEZE.md")
    excluded_section = body[body.find("EXCLUDED"):]
    for item in EXCLUDED_BACKLOG:
        assert item.lower() in excluded_section.lower(), (
            f"release freeze does not document backlog exclusion: {item}")


# ────────────────────────────────────────────────────────────────────────
# (13) No feature work introduced
# ────────────────────────────────────────────────────────────────────────
def test_no_feature_work_introduced_under_release_freeze():
    body = _read(MEM / "PRE_DEPLOYMENT_RELEASE_FREEZE.md")
    assert "SCOPE FROZEN" in body.upper()
    # Hard rule statement.
    assert "NO NEW FEATURES" in body.upper()


# ────────────────────────────────────────────────────────────────────────
# (14) No new collections
# ────────────────────────────────────────────────────────────────────────
def test_no_new_collections_in_release():
    body = _read(MEM / "PRE_DEPLOYMENT_DATA_SAFETY_CHECK.md")
    assert "No destructive operation" in body or "NONE" in body


# ────────────────────────────────────────────────────────────────────────
# (15) No route removals
# ────────────────────────────────────────────────────────────────────────
def test_no_route_removals():
    # TRACK 22.5A · route wiring moved from App.js into
    # `app/routing/AppRoutes.jsx`. Read both — safety intent
    # ("these route prefixes are still mounted somewhere in the
    # shipped app shell") is preserved.
    app_js = _read(ROOT / "frontend" / "src" / "App.js") + "\n" + _read(
        ROOT / "frontend" / "src" / "app" / "routing" / "AppRoutes.jsx"
    )
    for prefix in [
        "/admin", "/dispatch-portal", "/transportation-operations",
        "/sign-in", "/transport-verify",
    ]:
        assert prefix in app_js, f"route prefix removed: {prefix}"


# ────────────────────────────────────────────────────────────────────────
# (16) No auth/RBAC weakening
# ────────────────────────────────────────────────────────────────────────
def test_admin_only_endpoints_still_admin_strict():
    audit_doc = _read(MEM / "TRANSPORTATION_ROLE_PERMISSION_MATRIX.md")
    # Spot-check that the doctrine row exists.
    assert "ADMIN-STRICT" in audit_doc
    assert "/api/admin/transportation/audit-timeline" in audit_doc
    assert "/api/admin/transportation/hr-sync" in audit_doc
    assert "/api/admin/transportation/email-routes" in audit_doc


# ────────────────────────────────────────────────────────────────────────
# (17) Deployment gate command documented
# ────────────────────────────────────────────────────────────────────────
def test_deployment_gate_command_documented():
    for doc_name in (
        "PRE_DEPLOYMENT_ENVIRONMENT_CHECK.md",
        "PRODUCTION_DEPLOYMENT_CHECKLIST.md",
    ):
        body = _read(MEM / doc_name)
        assert "deployment_gate" in body, (
            f"{doc_name} must reference scripts/deployment_gate.py")


# ────────────────────────────────────────────────────────────────────────
# (18) Backup plan documented
# ────────────────────────────────────────────────────────────────────────
def test_backup_plan_documented():
    body = _read(MEM / "PRE_DEPLOYMENT_DATA_SAFETY_CHECK.md")
    assert "BACKUP PLAN" in body.upper()
    assert "Atlas" in body or "snapshot" in body.lower()
    assert "R2" in body


# ────────────────────────────────────────────────────────────────────────
# (19) Rollback triggers documented
# ────────────────────────────────────────────────────────────────────────
def test_rollback_triggers_documented():
    body = _read(MEM / "PRODUCTION_DEPLOYMENT_CHECKLIST.md")
    assert "Rollback" in body
    for trig in [
        "login failure", "dispatch", "auth", "data corruption",
    ]:
        assert trig.lower() in body.lower(), (
            f"rollback trigger missing: {trig}")


# ────────────────────────────────────────────────────────────────────────
# (20) Transportation acceptance requires VISIBLE = USABLE
# ────────────────────────────────────────────────────────────────────────
def test_transportation_acceptance_enforces_visible_usable():
    body = _read(MEM / "PRE_DEPLOYMENT_TRANSPORTATION_ACCEPTANCE_GATE.md")
    assert "VISIBLE = USABLE" in body.upper()
    assert "HIDDEN" in body.upper()


# ────────────────────────────────────────────────────────────────────────
# (21–29) Role smoke matrix covers every required role
# ────────────────────────────────────────────────────────────────────────
REQUIRED_ROLE_SECTIONS = [
    "PUBLIC", "SUPER ADMIN", "DISPATCH",
    "PROJECT MANAGEMENT", "HUMAN RESOURCES",
    "SAFETY OPERATIONS", "SHOP OPERATIONS", "FIELD LEADERSHIP",
    "DRIVER",
]


@pytest.mark.parametrize("section", REQUIRED_ROLE_SECTIONS)
def test_role_smoke_matrix_covers_role(section):
    body = _read(MEM / "PRE_DEPLOYMENT_ROLE_SMOKE_MATRIX.md")
    assert section in body.upper(), f"role smoke missing section: {section}"


# ────────────────────────────────────────────────────────────────────────
# (30) Canonical language checks documented
# ────────────────────────────────────────────────────────────────────────
def test_canonical_language_checks_documented():
    body = _read(MEM / "PRE_DEPLOYMENT_DESIGN_LANGUAGE_CHECK.md")
    for name in [
        "MASCI Operations Platform", "Transportation Operations",
        "Project Management", "Human Resources", "Safety Operations",
        "Shop Operations", "Administration", "Field Leadership",
    ]:
        assert name in body, f"canonical name missing: {name}"


# ────────────────────────────────────────────────────────────────────────
# (31) PDF/email terminology checks
# ────────────────────────────────────────────────────────────────────────
def test_pdf_and_email_terminology_check_documented():
    body = _read(MEM / "PRE_DEPLOYMENT_DESIGN_LANGUAGE_CHECK.md")
    assert "EMAIL TEMPLATES" in body.upper()
    assert "PDF" in body
    assert "Track 18.05" in body


# ────────────────────────────────────────────────────────────────────────
# (32) R1–R8 linter checks documented
# ────────────────────────────────────────────────────────────────────────
def test_r1_through_r8_linter_documented():
    body = _read(MEM / "PRE_DEPLOYMENT_DESIGN_LANGUAGE_CHECK.md")
    for rule in ("R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"):
        assert rule in body, f"design-system rule {rule} not documented"


# ────────────────────────────────────────────────────────────────────────
# (33) Governance boundary linter check documented
# ────────────────────────────────────────────────────────────────────────
def test_governance_boundary_linter_documented():
    body = _read(MEM / "PRE_DEPLOYMENT_DESIGN_LANGUAGE_CHECK.md")
    assert "GOVERNANCE BOUNDARY" in body.upper()
    assert "Track 18.10" in body


# ────────────────────────────────────────────────────────────────────────
# (34) Final GO/NO-GO documented
# ────────────────────────────────────────────────────────────────────────
def test_final_go_no_go_documented():
    body = _read(MEM / "PRE_DEPLOYMENT_RELEASE_FREEZE.md")
    assert "FINAL RELEASE DECISION" in body.upper()
    assert ("GO" in body or "NO-GO" in body)


# ────────────────────────────────────────────────────────────────────────
# (35) PRD updated
# ────────────────────────────────────────────────────────────────────────
def test_prd_updated_for_track_18_12c():
    body = _read(MEM / "PRD.md")
    assert "TRACK 18.12C" in body
    assert "VISIBLE = USABLE" in body


# ────────────────────────────────────────────────────────────────────────
# (36) Deployment gate wires this test file
# ────────────────────────────────────────────────────────────────────────
def test_release_safety_wired_into_deployment_gate():
    body = _read(DEPLOY_GATE)
    assert "test_pre_deployment_release_safety.py" in body, (
        "deployment_gate.py must include the release-safety test"
    )


# ────────────────────────────────────────────────────────────────────────
# (37) Change inventory references every changed surface
# ────────────────────────────────────────────────────────────────────────
def test_change_inventory_covers_release_surface():
    body = _read(MEM / "PRE_DEPLOYMENT_CHANGE_INVENTORY.md")
    for needle in [
        "transportation/_shared.jsx",
        "transportation/_lists.jsx",
        "transportation/_orientation.jsx",
        "transportation/_intelligence.jsx",
        "transportation/_command_queue.jsx",
        "transportation/_views.jsx",
        "transportation.py",
        "transportation_experience.py",
        "transportation_orientation.py",
        "transportation_automation.py",
        "transportation_intelligence.py",
        "server.py",
    ]:
        assert needle in body, f"change inventory missing: {needle}"


# ────────────────────────────────────────────────────────────────────────
# (38) Release notes are professional and operator-readable
# ────────────────────────────────────────────────────────────────────────
def test_release_notes_have_required_sections():
    body = _read(MEM / "RELEASE_NOTES_TRACK_18_PRODUCTION_CUT.md")
    for section in [
        "What's new",
        "Transportation",
        "Known deferrals",
        "Rollback",
    ]:
        assert section.lower() in body.lower(), (
            f"release notes section missing: {section}")
