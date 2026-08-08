from lib.governed_fixture_evidence import (
    apply_governed_fixture_markers,
    find_fixture_evidence,
    governed_fixture_markers,
    is_governed_fixture,
)


def test_employee_fixture_rule_applies_explicit_hidden_markers():
    doc = {"name": "TEST_iter152_hr_abc123", "email": "fixture@example.com"}
    evidence = find_fixture_evidence(doc, "employees")
    assert evidence
    marked = apply_governed_fixture_markers(doc, "employees")
    assert marked["synthetic_record"] is True
    assert marked["hidden_from_operations"] is True
    assert marked["truth_visibility_scope"] == "technical_audit_only"


def test_daily_report_fixture_requires_deterministic_signature_not_test_name_only():
    live_named_doc = {
        "project_name": "ES Flow Test",
        "project_number": "20-07",
        "prepared_by": "Real Foreman",
    }
    assert find_fixture_evidence(live_named_doc, "daily_reports") is None
    assert is_governed_fixture(live_named_doc, "daily_reports") is False


def test_daily_report_coord_fixture_uses_placeholder_signature():
    doc = {
        "project_name": "TEST_COORD_CLASSIFY",
        "project_number": "TEST-1",
        "photos": ["data:image/png;base64,FAKE0"],
    }
    markers = governed_fixture_markers(doc, "daily_reports")
    assert markers
    assert markers["governed_classification_source"] == "backend/tests/test_daily_reports.py"


def test_dispatch_override_fixture_uses_composite_signature():
    doc = {
        "truck_id": "override-truck-abc123",
        "driver_name": "Override Test",
        "project_number": "TEST",
    }
    assert is_governed_fixture(doc, "dispatch_assignments") is True


def test_equipment_false_positive_test_word_does_not_classify_without_fixture_signature():
    doc = {
        "operator_name": "Testing Alvarez",
        "project_name": "SR 600 Utility Phase",
        "project_number": "24-12",
        "equipment_unit": "EXC-4412",
    }
    assert find_fixture_evidence(doc, "equipment_inspections") is None
    assert is_governed_fixture(doc, "equipment_inspections") is False