from services.project_budget_authority import (
    _build_budget_row_suggestion,
    _line_kind_from_value,
    _normalize_source_row,
    _pdf_line_to_row,
)


def test_wp18c3_normalize_source_row_derives_amount_and_cost_code():
    row = _normalize_source_row(
        {
            "Pay Item": "401-1",
            "Description": "Asphalt surface course",
            "Qty": "125.5",
            "Unit": "TON",
            "Unit Price": "98.75",
        }
    )

    assert row["customer_pay_item_number"] == "401-1"
    assert row["description"] == "Asphalt surface course"
    assert row["quantity"] == 125.5
    assert row["unit"] == "TON"
    assert row["unit_price"] == 98.75
    assert row["budget_amount"] == 12393.125
    assert row["project_cost_code"] == "401-1"


def test_wp18c3_budget_row_suggestion_preserves_review_required_when_ambiguous():
    normalized = {
        "customer_pay_item_number": "",
        "description": "unknown specialty item",
        "project_cost_code": "",
        "phase_id": "",
        "work_package_id": "",
        "schedule_activity_id": "",
        "schedule_activity_name": "",
    }
    suggestion = _build_budget_row_suggestion(normalized, [], [])

    assert suggestion["confidence"] == "review_required"
    assert suggestion["enterprise_work_type_id"] == ""
    assert any("Customer pay-item number" in warning for warning in suggestion["warnings"])


def test_wp18c3_pdf_line_parser_extracts_budget_shape():
    parsed = _pdf_line_to_row("401-2 Asphalt Surface Course 120 TON 99.50 11940.00")

    assert parsed["customer pay item"] == "401-2"
    assert parsed["description"] == "Asphalt Surface Course"
    assert parsed["qty"] == "120"
    assert parsed["unit"] == "TON"


def test_wp18c3_line_kind_detects_allowance_and_reserve():
    assert _line_kind_from_value("Allowance") == "allowance"
    assert _line_kind_from_value("Management Reserve") == "management_reserve"
    assert _line_kind_from_value("Standard line") == "direct_cost"
