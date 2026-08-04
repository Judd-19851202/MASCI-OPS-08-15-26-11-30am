from services.project_schedule_actuals_spine import _forecast_row, _resolve_activity


def test_wp18c5_forecast_row_keeps_baseline_current_forecast_distinct():
    baseline = {
        "activity_id": "ACT-100",
        "planned_start_date": "2026-08-01",
        "planned_finish_date": "2026-08-05",
    }
    current = {
        "activity_id": "ACT-100",
        "activity_name": "Drainage install",
        "work_package_id": "WP-1",
        "project_cost_code": "300-101",
        "planned_start_date": "2026-08-03",
        "planned_finish_date": "2026-08-07",
        "duration_days": 5,
        "status": "in_progress",
        "actual_state": {
            "status": "in_progress",
            "actual_start_date": "2026-08-04",
            "last_progress_date": "2026-08-05",
            "approved_percent_complete": 40,
        },
    }

    row = _forecast_row(current, baseline)

    assert row["baseline_start_date"] == "2026-08-01"
    assert row["current_start_date"] == "2026-08-03"
    assert row["forecast_start_date"] == "2026-08-04"
    assert row["forecast_finish_date"] >= row["current_finish_date"]
    assert row["forecast_status"] == "in_progress"


def test_wp18c5_resolve_activity_prefers_explicit_schedule_activity_id():
    activities = [
        {"activity_id": "ACT-7", "activity_name": "Paving", "project_cost_code": "300-101", "customer_pay_item_number": "400-1"},
        {"activity_id": "ACT-8", "activity_name": "Striping", "project_cost_code": "300-102", "customer_pay_item_number": "400-2"},
    ]
    block = {"schedule_activity_id": "ACT-7", "cost_code": "300-101", "customer_pay_item_number": "400-1"}

    resolution = _resolve_activity(block, activities, "2026-08-12")

    assert resolution["resolved_activity_id"] == "ACT-7"
    assert resolution["confidence"] == "high"
    assert resolution["match_basis"] == "explicit_schedule_activity_id"


def test_wp18c5_resolve_activity_stays_governed_when_ambiguous():
    activities = [
        {"activity_id": "ACT-7", "activity_name": "Paving", "project_cost_code": "300-101", "customer_pay_item_number": "400-1", "planned_start_date": "2026-08-10", "planned_finish_date": "2026-08-12"},
        {"activity_id": "ACT-8", "activity_name": "Paving phase 2", "project_cost_code": "300-101", "customer_pay_item_number": "400-1", "planned_start_date": "2026-08-10", "planned_finish_date": "2026-08-12"},
    ]
    block = {"title": "Paving", "cost_code": "300-101", "customer_pay_item_number": "400-1"}

    resolution = _resolve_activity(block, activities, "2026-08-11")

    assert resolution["resolved_activity_id"] == ""
    assert resolution["confidence"] == "review_required"
    assert resolution["alternative_activity_ids"]