from services.cost_codes.oppc_confidence import build_project_confidence_score, summarize_confidence_portfolio


def test_confidence_score_is_explainable_and_canonical():
    result = build_project_confidence_score(
        {
            "today": "2026-07-28",
            "planning": {"assignment_count": 4, "ready_assignments": 4, "missing_required_counts": {}},
            "production": {"latest_report_date": "2026-07-28", "report_count_7d": 5, "production_efficiency_percent": 97.0, "actual_quantity": 150},
            "labor": {"payroll_complete": True, "flagged_rows": 0, "labor_difference_hours": 0.0},
            "variance": {"open_variances": 0, "critical_variances": 0, "recovery_required": 0},
            "resources": {"demand_foreman": 1, "supply_foreman": 1, "demand_superintendent": 1, "supply_superintendent": 1, "demand_drivers": 2, "supply_drivers": 2, "conflict_count": 0},
            "data_trust": {"source_record_count": 10, "forecast_snapshot_count": 2, "stale_inputs": []},
        }
    )
    assert result["score"] >= 90
    assert result["band"] == "high_confidence"
    assert result["governance"]["manual_forecast_fields_used"] is False
    assert any(item.startswith("planning:") for item in result["explainability"])


def test_confidence_score_penalizes_stale_and_unreconciled_inputs():
    result = build_project_confidence_score(
        {
            "today": "2026-07-28",
            "planning": {"assignment_count": 5, "ready_assignments": 2, "missing_required_counts": {"duration_days": 3}},
            "production": {"latest_report_date": "2026-07-20", "report_count_7d": 0, "production_efficiency_percent": 40.0, "actual_quantity": 5},
            "labor": {"payroll_complete": False, "flagged_rows": 3, "labor_difference_hours": 4.0},
            "variance": {"open_variances": 5, "critical_variances": 2, "recovery_required": 2},
            "resources": {"demand_foreman": 2, "supply_foreman": 1, "demand_superintendent": 2, "supply_superintendent": 0, "demand_drivers": 3, "supply_drivers": 1, "conflict_count": 2},
            "data_trust": {"source_record_count": 0, "forecast_snapshot_count": 0, "stale_inputs": ["daily_reports", "payroll"]},
        }
    )
    assert result["score"] < 60
    assert result["band"] in {"critical", "low_confidence"}
    assert "Daily production evidence is stale or missing." in result["warnings"]
    assert any(item["key"] == "labor" and item["status"] == "incomplete" for item in result["components"])


def test_portfolio_summary_rolls_up_bands():
    summary = summarize_confidence_portfolio(
        [
            {"production_confidence": {"score": 92, "band": "high_confidence"}},
            {"production_confidence": {"score": 72, "band": "watch"}},
            {"production_confidence": {"score": 48, "band": "critical"}},
        ]
    )
    assert summary["average_score"] == 70.67
    assert summary["high_confidence"] == 1
    assert summary["watch"] == 1
    assert summary["critical"] == 1