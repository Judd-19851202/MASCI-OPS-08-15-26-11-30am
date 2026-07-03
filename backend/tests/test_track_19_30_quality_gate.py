"""Track 19.30 · Production Quality Gate + Operational Excellence Standard.

Lock test that enforces the existence and structural completeness of the
permanent quality gate, scoring rubric, closeout template, regression
template, pilot observation playbook, and executive demo checklist. If a
future agent removes or mutates any of these governance documents, this
lock will fail loudly and force restoration before any track can close.
"""
from pathlib import Path

MEM = Path("/app/memory")

DOCS = {
    "quality_gate": MEM / "PRODUCTION_READINESS_QUALITY_GATE.md",
    "rubric": MEM / "SIX_PILLAR_SCORING_RUBRIC.md",
    "closeout_template": MEM / "FUTURE_TRACK_CLOSEOUT_TEMPLATE.md",
    "regression_template": MEM / "REGRESSION_GATE_TEMPLATE.md",
    "pilot_playbook": MEM / "PILOT_OBSERVATION_PLAYBOOK.md",
    "demo_checklist": MEM / "EXECUTIVE_DEMO_CHECKLIST.md",
}


# ---------------------------------------------------------------------------
# Document existence


def test_all_governance_docs_present():
    missing = [name for name, path in DOCS.items() if not path.exists()]
    assert not missing, f"Missing Track 19.30 governance documents: {missing}"


def test_prd_updated_for_19_30():
    prd = (MEM / "PRD.md").read_text(encoding="utf-8")
    assert "TRACK 19.30" in prd, "PRD.md must reference TRACK 19.30"


def test_changelog_updated_for_19_30():
    changelog = (MEM / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "TRACK 19.30" in changelog, "CHANGELOG.md must reference TRACK 19.30"


# ---------------------------------------------------------------------------
# Quality Gate — required checklist categories


QUALITY_GATE_REQUIRED_CATEGORIES = [
    "Architecture reviewed",
    "Data model reviewed",
    "UI reviewed",
    "Mobile",
    "iPad",
    "Desktop",
    "Accessibility",
    "English",
    "Spanish",
    "Permissions",
    "Backend route",
    "Frontend route",
    "Payload",
    "PDF",
    "Email",
    "Notification",
    "Historical record",
    "Employee 360",
    "Incident Case",
    "Reporting",
    "Dashboard",
    "Export",
    "Trust Spine",
    "Audit event",
    "Autosave",
    "Session behavior",
    "Error states",
    "Empty states",
    "Loading states",
    "Role-based visibility",
    "Public/private boundary",
    "Regression tests",
    "Playwright smoke",
    "Documentation updated",
    "PRD updated",
    "CHANGELOG updated",
    "Rollback path documented",
    "Pilot-user validation",
    "Executive signoff",
]


def test_quality_gate_covers_all_required_categories():
    text = DOCS["quality_gate"].read_text(encoding="utf-8")
    missing = [c for c in QUALITY_GATE_REQUIRED_CATEGORIES if c not in text]
    assert not missing, f"Quality gate missing categories: {missing}"


# ---------------------------------------------------------------------------
# Rubric — six pillars + NO-GO thresholds


SIX_PILLARS = ["Powerful", "Simple", "Beautiful", "Trusted", "Proven", "Operational"]


def test_rubric_defines_all_six_pillars():
    text = DOCS["rubric"].read_text(encoding="utf-8")
    for pillar in SIX_PILLARS:
        assert pillar in text, f"Rubric missing pillar: {pillar}"


def test_rubric_defines_no_go_thresholds():
    text = DOCS["rubric"].read_text(encoding="utf-8")
    assert "NO-GO" in text
    assert "60 / 60" in text or "60/60" in text
    assert "48" in text  # pilot acceptable threshold


def test_rubric_defines_scoring_bands():
    text = DOCS["rubric"].read_text(encoding="utf-8")
    for band in ["Elite", "Production Strong", "Pilot Acceptable", "Not Acceptable"]:
        assert band in text, f"Rubric missing band: {band}"


# ---------------------------------------------------------------------------
# Closeout template — required sections


CLOSEOUT_REQUIRED_SECTIONS = [
    "TRACK",
    "STATUS",
    "EXECUTIVE VERDICT",
    "WHAT CHANGED",
    "WHY IT MATTERS",
    "SIX PILLAR SCORE",
    "ZERO-DRIFT MATRIX",
    "USER PERSONAS VERIFIED",
    "WORKFLOWS VERIFIED",
    "MOBILE",
    "BILINGUAL",
    "PERMISSIONS",
    "PDF",
    "EMAIL",
    "NOTIFICATION",
    "HISTORICAL RECORDS",
    "TRUST SPINE",
    "TESTS",
    "DOCS",
    "RISKS",
    "REMAINING DEBT",
    "ROLLBACK",
    "FINAL CALL",
]


def test_closeout_template_includes_all_sections():
    text = DOCS["closeout_template"].read_text(encoding="utf-8")
    missing = [s for s in CLOSEOUT_REQUIRED_SECTIONS if s not in text]
    assert not missing, f"Closeout template missing sections: {missing}"


def test_closeout_template_includes_zero_drift_matrix():
    text = DOCS["closeout_template"].read_text(encoding="utf-8")
    assert "ZERO-DRIFT MATRIX" in text
    # Matrix should reference the major drift categories
    for cat in [
        "Schemas",
        "Backend routes",
        "Payloads",
        "PDFs",
        "Emails",
        "Permissions",
        "Trust Spine",
        "Audit events",
    ]:
        assert cat in text, f"Zero-drift matrix missing category: {cat}"


def test_closeout_template_includes_tests_docs_rollback():
    text = DOCS["closeout_template"].read_text(encoding="utf-8")
    assert "TESTS" in text
    assert "DOCS" in text
    assert "ROLLBACK" in text


# ---------------------------------------------------------------------------
# Regression template — required categories


REGRESSION_REQUIRED = [
    "Backend unit tests",
    "Backend route contract tests",
    "Frontend build",
    "Frontend lint",
    "Playwright smoke",
    "Role permission smoke",
    "Bilingual smoke",
    "PDF smoke",
    "Email dry-run smoke",
    "Notification dry-run smoke",
    "Mobile viewport smoke",
    "iPad viewport smoke",
    "Desktop smoke",
    "Historical record smoke",
    "Audit event smoke",
    "Trust Spine smoke",
    "Rollback sanity check",
]


def test_regression_template_includes_all_categories():
    text = DOCS["regression_template"].read_text(encoding="utf-8")
    missing = [c for c in REGRESSION_REQUIRED if c not in text]
    assert not missing, f"Regression template missing categories: {missing}"


# ---------------------------------------------------------------------------
# Pilot playbook — persona coverage


PILOT_PERSONAS = [
    "Foreman",
    "Operator",
    "Driver",
    "Supervisor",
    "HR",
    "Safety",
    "PM",
    "Shop",
    "Dispatch",
    "Executive",
]


def test_pilot_playbook_covers_all_personas():
    text = DOCS["pilot_playbook"].read_text(encoding="utf-8")
    missing = [p for p in PILOT_PERSONAS if p not in text]
    assert not missing, f"Pilot playbook missing personas: {missing}"


def test_pilot_playbook_captures_friction_signals():
    text = DOCS["pilot_playbook"].read_text(encoding="utf-8")
    for signal in [
        "confusion",
        "abandoned",
        "misunderstood",
        "slow",
        "missing data",
        "bad PDFs",
        "wrong emails",
        "permission",
        "mobile",
        "Spanish",
        "training",
    ]:
        assert signal.lower() in text.lower(), f"Pilot playbook missing signal: {signal}"


# ---------------------------------------------------------------------------
# Executive demo — all major demo flows


DEMO_FLOWS = [
    "Login",
    "Daily Report",
    "Equipment Pre-Op",
    "DVIR",
    "Safety Meeting",
    "Incident",
    "HR Employee Record",
    "PM",
    "Safety",
    "Shop",
    "Executive",
    "PDF",
    "email",
    "audit",
    "Bilingual",
    "Mobile",
]


def test_executive_demo_includes_all_flows():
    text = DOCS["demo_checklist"].read_text(encoding="utf-8")
    missing = [f for f in DEMO_FLOWS if f.lower() not in text.lower()]
    assert not missing, f"Executive demo missing flows: {missing}"


def test_executive_demo_references_industry_comparison():
    text = DOCS["demo_checklist"].read_text(encoding="utf-8")
    for competitor in ["HCSS", "Procore", "Raken", "SafetyCulture", "Samsara"]:
        assert competitor in text, f"Demo checklist missing competitor: {competitor}"
