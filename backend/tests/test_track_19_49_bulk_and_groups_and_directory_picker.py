"""Track 19.49 · Bulk-import UI + Group-Membership Editor + Platform
Person Picker · lock test.

Run isolated:
    pytest backend/tests/test_track_19_49_bulk_and_groups_and_directory_picker.py -q
"""
from __future__ import annotations
from pathlib import Path

APP = Path("/app")
FE = APP / "frontend"
BE = APP / "backend"
MEM = APP / "memory"

PAGE = FE / "src/pages/admin/AdminOperationalIntelligenceRecipients.jsx"


def _page():
    return PAGE.read_text(encoding="utf-8")


# ---------------------------------------------------- Bulk import --------
def test_bulk_import_panel_present():
    t = _page()
    assert "BulkImportPanel" in t
    assert "oi-bulk-import-panel" in t
    assert "oi-recipients-bulk-btn" in t


def test_bulk_paste_mode_wires_bulk_import_endpoint():
    t = _page()
    assert "/operational-intelligence/recipients/bulk-import" in t
    assert "oi-bulk-paste-submit" in t
    assert "oi-bulk-paste-textarea" in t


def test_bulk_paste_validates_emails_and_shows_summary():
    t = _page()
    # Client-side email regex enforcement + invalid-list surfaced.
    assert "oi-bulk-parse-summary" in t
    assert "oi-bulk-invalid-list" in t
    assert "emailRe" in t


def test_bulk_import_shows_duplicate_and_inserted_counts():
    t = _page()
    for tid in ("oi-bulk-result-inserted",
                "oi-bulk-result-duplicate",
                "oi-bulk-result-errors"):
        assert tid in t, f"missing bulk-result stat: {tid}"


def test_bulk_import_has_active_toggle():
    t = _page()
    assert "oi-bulk-active-checkbox" in t


# ---------------------------------------------------- Copy from product --
def test_copy_from_product_tab_present_and_wired():
    t = _page()
    assert "oi-bulk-tab-copy" in t
    assert "oi-bulk-copy-source" in t
    assert "oi-bulk-copy-submit" in t
    # Copy path must funnel through bulk-import (single ingest endpoint).
    assert "submitCopy" in t


def test_copy_from_product_prevents_same_source_and_target():
    t = _page()
    # `filter((p) => p.product_id !== productId)` is the guard.
    assert "p.product_id !== productId" in t


# ---------------------------------------------------- Platform directory --
def test_directory_picker_tab_present():
    t = _page()
    assert "oi-bulk-tab-directory" in t
    assert "From platform directory" in t


def test_directory_picker_uses_canonical_k4_endpoint():
    """The picker must read from `/api/admin/directory/k4/users` — the
    canonical platform-user source of truth. It must NEVER read or
    mutate `/hr/employees` (which strips emails and is HR-owned)."""
    t = _page()
    assert "/admin/directory/k4/users" in t
    # No writes to HR / directory / user endpoints.
    for banned in (
        'api.post("/hr/',
        'api.post("/admin/employees',
        'api.patch("/hr/',
        'api.patch("/admin/employees',
        'api.delete("/hr/',
        'api.delete("/admin/employees',
        'api.post("/admin/directory',
        'api.patch("/admin/directory',
    ):
        assert banned not in t, f"HR / user-account mutation leaked: {banned}"


def test_directory_picker_has_search_portal_and_multiselect():
    t = _page()
    for tid in (
        "oi-directory-search-input",
        "oi-directory-portal-filter",
        "oi-directory-picker-list",
        "oi-directory-selected-count",
        "oi-directory-submit",
        "oi-directory-cancel",
    ):
        assert tid in t, f"directory picker missing testid: {tid}"


def test_directory_picker_dedupes_against_existing_recipients():
    """Rows for users already subscribed to the target product must be
    visibly marked and disabled to prevent duplicate submissions."""
    t = _page()
    assert "existingForTarget" in t
    assert "already subscribed" in t
    # Disabled checkbox when `already` is true.
    assert "disabled={already" in t


def test_directory_picker_stores_source_reference():
    """Directory-sourced rows must persist a source_reference so admins
    can trace a recipient back to its platform-user origin."""
    t = _page()
    assert "source_reference" in t
    assert "Sourced from platform directory" in t


def test_directory_picker_preserves_manual_entry_path():
    """The manual single-add form and paste-list tabs must remain
    available — platform picker is preferred, not exclusive."""
    t = _page()
    # Manual single-add form.
    assert "oi-recipient-add-form" in t
    # Paste tab.
    assert "oi-bulk-tab-paste" in t


def test_directory_picker_never_creates_platform_users_or_hr_records():
    """No POST calls to the directory or HR write paths."""
    t = _page()
    banned = [
        'api.post("/admin/directory',
        'api.post("/admin/employees',
        'api.post("/hr/employees',
        'api.post("/employees',
        'api.put("/admin/employees',
        'api.put("/hr/employees',
    ]
    for b in banned:
        assert b not in t, f"forbidden mutation: {b}"


# ---------------------------------------------------- Group create + members
def test_group_create_panel_present_and_wired():
    t = _page()
    assert "GroupCreatePanel" in t
    for tid in ("oi-group-create-panel", "oi-group-create-id",
                "oi-group-create-name", "oi-group-create-products",
                "oi-group-create-submit", "oi-groups-create-btn"):
        assert tid in t, f"missing group-create testid: {tid}"
    assert 'api.post("/operational-intelligence/groups"' in t


def test_group_member_editor_present_and_wired():
    t = _page()
    assert "GroupMemberEditor" in t
    assert "/operational-intelligence/groups/${group.group_id}/members" in t
    # Members button per row.
    assert "oi-group-members-btn-" in t


def test_group_member_editor_shows_existing_members_readonly():
    t = _page()
    assert "Current members" in t
    assert "Member removal is not yet exposed" in t


# ---------------------------------------------------- Safety / dry-run ---
def test_no_live_send_path_in_page():
    t = _page()
    for banned in ("dispatch?dry_run=false", "/dispatch",
                   'dry_run: false'):
        assert banned not in t, f"live-send leaked: {banned}"


def test_dry_run_safety_note_still_present_in_bulk_panel():
    t = _page()
    assert "oi-bulk-safety-note" in t
    for kw in ("do not send email", "do not\n          mutate HR",
               "canonical, already-authorized user emails"):
        assert kw in t.replace("<strong>", "").replace("</strong>", ""), (
            f"missing safety-note text fragment: {kw!r}")


def test_delete_language_still_absent():
    t = _page()
    for banned in (">Delete<", ">Delete recipient<"):
        assert banned not in t, f"delete language leaked: {banned}"


# ---------------------------------------------------- Documentation ------
REQUIRED_DOCS = [
    "TRACK_19_49_BULK_IMPORT_AND_GROUPS.md",
    "TRACK_19_49_PLATFORM_PERSON_PICKER.md",
    "TRACK_19_49_ZERO_DRIFT_MATRIX.md",
    "TRACK_19_49_QUALITY_GATE_CLOSEOUT.md",
    "TRACK_19_49_TEST_REPORT.md",
]


def test_all_track_19_49_docs_present():
    missing = [d for d in REQUIRED_DOCS if not (MEM / d).exists()]
    assert not missing, missing


def test_zero_drift_matrix_covers_all_categories():
    t = (MEM / "TRACK_19_49_ZERO_DRIFT_MATRIX.md").read_text(encoding="utf-8")
    for c in ["Schemas", "Routes", "Emails", "Scheduler",
              "Recipients", "Audit", "HR", "Rollback"]:
        assert c in t, f"ZDM missing: {c}"


def test_prd_updated():
    assert "TRACK 19.49" in (MEM / "PRD.md").read_text(encoding="utf-8")


def test_changelog_updated():
    assert "TRACK 19.49" in (MEM / "CHANGELOG.md").read_text(encoding="utf-8")


# ---------------------------------------------------- Regression check ---
def test_backend_recipient_engine_unchanged():
    """Track 19.49 is a pure frontend track — the backend recipient
    module must still be the single Track 19.45A file."""
    files = list((BE / "operational_intelligence").glob("recipients*.py"))
    assert len(files) == 1, [str(f) for f in files]
