"""
test_iter353a_ui_hr_safety_records.py — iter353a-UI regression locks

Source-level lock confirming the HR Safety Records page has write
surfaces (Add Training Record, Upload Document) + archive pattern,
and that HR delete buttons are NEVER rendered (operator policy).
"""
from pathlib import Path


def test_hr_safety_records_has_add_training_button():
    src = (Path(__file__).parent.parent.parent / "frontend" / "src"
           / "pages" / "HrSafetyRecords.jsx").read_text()
    assert 'data-testid="hr-safety-add-training-btn"' in src, (
        "iter353a-UI — HrSafetyRecords must surface an Add Training button"
    )
    assert 'data-testid="hr-safety-add-training-form"' in src, (
        "iter353a-UI — Add Training form must exist"
    )
    assert "/safety/training-records" in src, (
        "iter353a-UI — form must POST to /api/safety/training-records"
    )


def test_hr_safety_records_has_upload_document_button():
    src = (Path(__file__).parent.parent.parent / "frontend" / "src"
           / "pages" / "HrSafetyRecords.jsx").read_text()
    assert 'data-testid="hr-safety-upload-doc-btn"' in src
    assert 'data-testid="hr-safety-upload-doc-form"' in src
    assert "/safety/documents" in src


def test_hr_safety_records_uses_patch_to_archive_not_delete():
    src = (Path(__file__).parent.parent.parent / "frontend" / "src"
           / "pages" / "HrSafetyRecords.jsx").read_text()
    # archiveTraining + archiveDoc functions exist
    assert "archiveTraining" in src and "archiveDoc" in src
    # They use PATCH, not DELETE
    assert "axios.patch(`${API}/safety/training-records" in src, (
        "iter353a-UI archive must use PATCH (no hard delete)"
    )
    assert "axios.patch(`${API}/safety/documents" in src, (
        "iter353a-UI doc archive must use PATCH (no hard delete)"
    )
    # No axios.delete calls in HR Safety Records (HR has no delete authority)
    assert "axios.delete" not in src, (
        "iter353a-UI MUST NOT call axios.delete from HrSafetyRecords — "
        "HR has no hard-delete authority per operator policy"
    )


def test_hr_safety_records_surfaces_audit_attribution():
    src = (Path(__file__).parent.parent.parent / "frontend" / "src"
           / "pages" / "HrSafetyRecords.jsx").read_text()
    # The "Entered By" column + ROLE_PILL render audit attribution
    assert "Entered By" in src or "entered_by" in src.lower()
    assert "ROLE_PILL" in src
    assert "created_by_role" in src
    # Archive pill should be rendered for archived rows
    assert "ARCHIVED" in src


def test_hr_safety_records_calm_intro_strip_present():
    src = (Path(__file__).parent.parent.parent / "frontend" / "src"
           / "pages" / "HrSafetyRecords.jsx").read_text()
    assert 'data-testid="hr-safety-intro-strip"' in src
    assert "Shared HR + Safety accountability surface" in src
