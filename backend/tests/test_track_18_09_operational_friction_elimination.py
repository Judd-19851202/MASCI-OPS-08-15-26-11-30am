"""TRACK 18.09 · Operational Friction Elimination — regression lock.

Scope:
* Lock the two micro-polish edits this track made in the frontend
  (`MasterListPanel.jsx` dynamic search placeholder + `Tasks.jsx`
  description-aware placeholder).
* Lock the audit documentation surface so the three reports
  (Operational Friction Elimination, Visual Rhythm, Information
  Hierarchy, Operator Experience) stay in lockstep with the directive.
* Verify the deferral disposition for linter rule R8 is visible in
  `test_track_18_07_design_system_linter.py` (no premature ship).
* Verify the deployment gate registers `test_track_18_09_*` so the
  Track 18 family stays cohesive.

Constraints honored:
* No new feature, no new collection, no auth/RBAC change.
* No frontend rendering tests (lint-style static assertions only).
* Every assertion targets a concrete, low-noise pattern.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path("/app")
FRONTEND_SRC = ROOT / "frontend" / "src"
MEMORY = ROOT / "memory"
SCRIPTS = ROOT / "scripts"
TESTS_DIR = ROOT / "backend" / "tests"


# =====================================================================
# Documentation surface
# =====================================================================
def test_friction_elimination_report_exists():
    p = MEMORY / "TRACK_18_09_OPERATIONAL_FRICTION_ELIMINATION.md"
    assert p.exists(), "Track 18.09 friction elimination report is missing."
    body = p.read_text()
    # The report MUST honestly disclose the R8 deferral. Track 18.10 will
    # ship R8; this track does not.
    assert "R8" in body and "deferred" in body.lower(), (
        "Track 18.09 report must disclose the R8 deferral so docs and "
        "code stay in lockstep."
    )
    # Final certification must remain the closing verdict.
    assert "The interface disappears" in body
    # Status banner must read GO.
    assert "GO" in body.splitlines()[2]


def test_visual_rhythm_report_exists():
    p = MEMORY / "TRACK_18_09_VISUAL_RHYTHM_REPORT.md"
    assert p.exists(), "Track 18.09 visual rhythm report is missing."
    body = p.read_text()
    # Every row must be 🟢 — no yellow/red leftover before certification.
    assert "🔴" not in body, "Visual rhythm report has red findings — close them before locking 18.09."
    assert "🟡" not in body, "Visual rhythm report has amber findings — close them before locking 18.09."
    assert "🟢" in body


def test_information_hierarchy_report_exists():
    p = MEMORY / "TRACK_18_09_INFORMATION_HIERARCHY_REPORT.md"
    assert p.exists(), "Track 18.09 information hierarchy report is missing."
    body = p.read_text()
    assert "5-second test" in body
    # Each of the five operator questions must be present.
    for q in (
        "Where am I",
        "What matters",
        "What changed",
        "What needs me",
        "What should I do next",
    ):
        assert q in body, f"Information hierarchy report is missing the question: {q}"


def test_operator_experience_report_exists():
    p = MEMORY / "TRACK_18_09_OPERATOR_EXPERIENCE_REPORT.md"
    assert p.exists(), "Track 18.09 operator experience report is missing."
    body = p.read_text()
    # Emotional audit anchors.
    for anchor in (
        "Confident",
        "Calm",
        "Organized",
        "Supported",
        "Never overwhelmed",
        "Never lost",
        "Never fighting the software",
    ):
        assert anchor in body, f"Operator experience report is missing the anchor: {anchor}"


# =====================================================================
# Friction-elimination edits — dynamic search placeholder
# =====================================================================
def test_master_list_panel_uses_dynamic_search_placeholder():
    """`MasterListPanel` was the last shared component with a generic
    `Search…` placeholder. It must use the existing `entitySingular`
    prop to surface what the operator is actually searching."""
    p = FRONTEND_SRC / "components" / "MasterListPanel.jsx"
    body = p.read_text()
    assert "placeholder={`Search ${entitySingular}…`}" in body, (
        "MasterListPanel.jsx must use a dynamic Search {entitySingular}… "
        "placeholder so every reuse (employees, equipment, suppliers, "
        "parts, etc.) tells the operator what to type."
    )
    # The generic baseline must be gone.
    assert 'placeholder="Search…"' not in body, (
        "MasterListPanel.jsx still ships the legacy generic 'Search…' "
        "placeholder. Replace with the dynamic entitySingular variant."
    )


def test_tasks_search_placeholder_matches_server_scope():
    """The Tasks `q` query string is server-side and searches title +
    description. The placeholder must communicate that scope."""
    p = FRONTEND_SRC / "pages" / "Tasks.jsx"
    body = p.read_text()
    assert 'placeholder="Search title or description…"' in body, (
        "pages/Tasks.jsx search placeholder must read "
        "'Search title or description…' so the operator knows what "
        "the server-side q filter actually covers."
    )
    assert 'placeholder="Search title…"' not in body, (
        "pages/Tasks.jsx still ships the title-only placeholder. Replace "
        "with the description-aware variant."
    )


# =====================================================================
# R8 deferral discipline
# =====================================================================
def test_r8_duplicate_cta_rule_is_deferred_not_shipped():
    """Track 18.09 deferred R8. The linter file must carry the
    deferral comment AND must not contain a callable
    `test_lint_no_duplicate_cta_in_card` rule yet."""
    linter = TESTS_DIR / "test_track_18_07_design_system_linter.py"
    src = linter.read_text()
    assert "R8" in src and "DEFERRED" in src.upper(), (
        "R8 deferral disposition must be documented inline in the linter "
        "file. Did Track 18.10 prematurely ship R8 without removing the "
        "deferral marker?"
    )
    assert "def test_lint_no_duplicate_cta_in_card" not in src, (
        "R8 rule shipped without the deferral being closed — coordinate "
        "with the 18.10 calibration before shipping."
    )


# =====================================================================
# Deployment gate wiring
# =====================================================================
def test_track_18_09_wired_into_deployment_gate():
    gate = SCRIPTS / "deployment_gate.py"
    src = gate.read_text()
    assert "test_track_18_09_operational_friction_elimination.py" in src, (
        "Track 18.09 lock file is not wired into "
        "scripts/deployment_gate.py — every Track 18 lock file must "
        "appear in the regression set."
    )


# =====================================================================
# Cross-link integrity — every supporting report is linked from the
# main report so the audit trail is discoverable from one entry point.
# =====================================================================
def test_main_report_links_supporting_reports():
    body = (MEMORY / "TRACK_18_09_OPERATIONAL_FRICTION_ELIMINATION.md").read_text()
    for name in (
        "TRACK_18_09_VISUAL_RHYTHM_REPORT.md",
        "TRACK_18_09_INFORMATION_HIERARCHY_REPORT.md",
        "TRACK_18_09_OPERATOR_EXPERIENCE_REPORT.md",
    ):
        assert name in body, (
            f"Main Track 18.09 report does not link supporting report: {name}"
        )
