"""Track 19.48 · Operational Intelligence Recipient Management UI · lock test.

Run isolated:
    pytest backend/tests/test_track_19_48_recipient_management_ui.py -q
"""
from __future__ import annotations
from pathlib import Path

APP = Path("/app")
FE = APP / "frontend"
BE = APP / "backend"
MEM = APP / "memory"

PAGE = FE / "src/pages/admin/AdminOperationalIntelligenceRecipients.jsx"


# ---------------------------------------------------- Frontend integrity --
def test_recipient_page_file_exists():
    assert PAGE.exists()


def test_route_registered_and_admin_gated():
    app = (FE / "src/App.js").read_text(encoding="utf-8")
    assert "AdminOperationalIntelligenceRecipients" in app
    assert "/admin/operational-intelligence/recipients" in app
    # Route must go through the shared A(...) admin gate.
    idx = app.index("/admin/operational-intelligence/recipients")
    line_start = app.rfind("\n", 0, idx)
    line_end = app.find("\n", idx)
    line = app[line_start:line_end]
    assert "A(<AdminOperationalIntelligenceRecipients" in line, line


def test_recipient_page_wires_existing_backend_endpoints():
    text = PAGE.read_text(encoding="utf-8")
    for ep in (
        '"/operational-intelligence/recipients"',
        '"/operational-intelligence/groups"',
        '"/operational-intelligence/products"',
        '`/operational-intelligence/recipients/${editing.id}`',
        '`/operational-intelligence/recipients/${r.id}`',
    ):
        assert ep in text, f"missing endpoint wire: {ep}"


def test_recipient_page_uses_soft_deactivate_not_hard_delete():
    """The page must use api.delete for deactivation (backend soft-
    deletes) and must NEVER expose 'delete' language to the user."""
    text = PAGE.read_text(encoding="utf-8")
    # api.delete is fine (backend contract). But UI copy must say
    # "Deactivate" / "Reactivate", never "Delete".
    for banned in (
        ">Delete<",
        "'Delete'", '"Delete"',
        ">Delete recipient<",
    ):
        assert banned not in text, f"delete language leaked: {banned}"
    for required in ("Deactivate", "Reactivate"):
        assert required in text, f"missing action label: {required}"


def test_recipient_page_no_live_send_button():
    """No live-send button, no dry_run=false, no send/dispatch endpoint
    referenced from this page."""
    text = PAGE.read_text(encoding="utf-8")
    assert "dry_run" not in text or "dry_run: false" not in text
    for banned in ("dispatch?dry_run=false", "/dispatch"):
        assert banned not in text, f"live-send path leaked: {banned}"


def test_recipient_page_has_dry_run_safety_notice():
    text = PAGE.read_text(encoding="utf-8")
    assert "oi-recipients-dry-run-notice" in text
    for kw in ("Dry-run safety", "does not send email", "regulatory replay"):
        assert kw in text, f"missing safety-notice text: {kw}"


def test_recipient_page_has_required_testids():
    text = PAGE.read_text(encoding="utf-8")
    for tid in (
        "admin-operational-intelligence-recipients",
        "oi-recipients-summary-strip",
        "oi-recipients-add-btn",
        "oi-recipient-add-form",
        "oi-recipient-edit-form",
        "oi-recipients-table",
        "oi-groups-panel",
        "oi-recipients-dry-run-notice",
        "oi-recipients-governance-note",
        "oi-recipients-back-to-cockpit",
    ):
        assert tid in text, f"missing data-testid: {tid}"


def test_recipient_page_has_add_edit_deactivate_reactivate_ui():
    text = PAGE.read_text(encoding="utf-8")
    for label in ("Add recipient", "Edit", "Deactivate", "Reactivate"):
        assert label in text, f"missing action label: {label}"


def test_recipient_page_shows_no_raw_401_or_403_text():
    text = PAGE.read_text(encoding="utf-8")
    for banned in (">401<", ">403<", "Unauthorized", "Forbidden"):
        assert banned not in text, f"raw HTTP error text leaked: {banned}"


def test_recipient_form_has_all_required_fields():
    text = PAGE.read_text(encoding="utf-8")
    for tid in (
        "oi-recipient-email-input",
        "oi-recipient-display-name-input",
        "oi-recipient-role-input",
        "oi-recipient-department-input",
        "oi-recipient-digest-select",
        "oi-recipient-notes-input",
        "oi-recipient-active-checkbox",
    ):
        assert tid in text, f"form missing field: {tid}"


def test_cockpit_still_links_to_recipient_management():
    """Track 19.47 Cockpit must still expose the recipient governance
    entry and now must link to the new dedicated Recipient page."""
    text = (FE / "src/pages/admin/AdminOperationalIntelligence.jsx").read_text(
        encoding="utf-8")
    assert "oi-recipient-governance-entry" in text
    assert "/admin/operational-intelligence/recipients" in text
    assert "oi-recipients-manage-link" in text


def test_no_duplicate_recipient_system_created():
    """The recipient page must NOT introduce a new backend recipient
    module. Only the existing Track 19.45A endpoints may be consumed."""
    engine_dir = BE / "operational_intelligence"
    # There is exactly one recipients module in the engine.
    recip_files = list(engine_dir.glob("recipients*.py"))
    assert len(recip_files) == 1, [str(p) for p in recip_files]


# ---------------------------------------------------- Documentation ------
REQUIRED_DOCS = [
    "TRACK_19_48_RECIPIENT_MANAGEMENT_UI.md",
    "TRACK_19_48_PERMISSION_AND_GOVERNANCE.md",
    "TRACK_19_48_ZERO_DRIFT_MATRIX.md",
    "TRACK_19_48_QUALITY_GATE_CLOSEOUT.md",
    "TRACK_19_48_TEST_REPORT.md",
]


def test_all_track_19_48_docs_present():
    missing = [d for d in REQUIRED_DOCS if not (MEM / d).exists()]
    assert not missing, missing


def test_zero_drift_matrix_covers_all_categories():
    t = (MEM / "TRACK_19_48_ZERO_DRIFT_MATRIX.md").read_text(encoding="utf-8")
    for c in ["Schemas", "Routes", "Emails", "Scheduler",
              "Recipients", "Audit", "Rollback"]:
        assert c in t, f"ZDM missing: {c}"


def test_prd_updated():
    assert "TRACK 19.48" in (MEM / "PRD.md").read_text(encoding="utf-8")


def test_changelog_updated():
    assert "TRACK 19.48" in (MEM / "CHANGELOG.md").read_text(encoding="utf-8")
