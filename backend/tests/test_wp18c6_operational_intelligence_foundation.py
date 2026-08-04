from services.project_operational_intelligence import _metric_card


def test_wp18c6_metric_card_exposes_full_governance_contract():
    card = _metric_card(
        metric_id="governed_production_rate",
        label="Governed production rate",
        definition="Accepted quantity per approved labor hour.",
        formula="approved_quantity / approved_labor_hours",
        owner="Governed Metric Engine",
        unit_label="LF/hr",
        value=12.5,
        confidence="high",
        freshness_at="2026-08-04T10:00:00+00:00",
        limitations=["Only approved actuals contribute to this KPI."],
        lineage={
            "work_block_ids": ["WB-1", "WB-2"],
            "daily_report_ids": ["DR-1"],
            "source_report_ids": ["DR-2"],
            "budget_line_ids": ["BL-1"],
            "schedule_activity_ids": ["ACT-1"],
            "rejected_candidate_ids": ["CAND-1"],
        },
        drilldown_path="/pm/operational-intelligence?metric=governed_production_rate",
    )

    assert card["version"] == "wp18c6.v1"
    assert card["calculation_timestamp"] == "2026-08-04T10:00:00+00:00"
    assert card["source_records"] == ["ACT-1", "BL-1", "CAND-1", "DR-1", "DR-2"]
    assert card["work_block_lineage"] == ["WB-1", "WB-2"]
    assert card["audit_trail"]["authority_collection"] == "project_operational_intelligence_snapshots"
    assert {row["record_type"] for row in card["supporting_evidence"]} == {
        "daily_report",
        "schedule_activity",
        "budget_line",
        "schedule_actual_candidate",
    }
    assert card["drilldown_path"].endswith("governed_production_rate")