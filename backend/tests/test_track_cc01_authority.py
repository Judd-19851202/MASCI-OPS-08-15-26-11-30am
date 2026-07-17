import pytest

from services.cost_codes.foundation import (
    build_legacy_cost_code_projection,
    build_ods_project_cost_code_doc,
    build_progress_snapshot,
    normalize_cost_code_actual_rows,
    normalize_job_assignment,
)
from services.ods_spine import ingest


def test_normalize_job_assignment_preserves_original_and_sets_authority_fields():
    existing = {
        "code": "CC-100",
        "item_name": "Pipe",
        "unit_of_measure": "LF",
        "bid_unit_price": 22.5,
        "target_man_hours": 1.5,
        "original_quantity": 100.0,
        "authorized_quantity": 100.0,
        "forecast_quantity": 110.0,
    }
    row = {
        "code": "CC-100",
        "item_name": "Pipe",
        "unit_of_measure": "LF",
        "authorized_quantity": 125.0,
        "forecast_quantity": 140.0,
        "planned_performer": "Crew A",
    }

    normalized = normalize_job_assignment(row, existing_assignment=existing)

    assert normalized["original_quantity"] == 100.0
    assert normalized["authorized_quantity"] == 125.0
    assert normalized["forecast_quantity"] == 140.0
    assert normalized["bid_quantity"] == 125.0
    assert normalized["planned_performer"] == "Crew A"
    assert normalized["bid_unit_price"] == 22.5


def test_normalize_cost_code_actual_rows_enforces_assignment_scope_and_evidence():
    assignments = [
        {
            "code": "CC-100",
            "item_name": "Pipe",
            "unit_of_measure": "LF",
            "sort_order": 0,
            "planned_performer": "Crew A",
            "cpm_activity_id": "CPM-1",
        }
    ]
    rows = normalize_cost_code_actual_rows(
        [
            {
                "cost_code": "CC-100",
                "installed_quantity": 8.5,
                "actual_performer": "Crew B",
                "work_area": "North",
                "location": "Sta 1+00",
                "notes": "Installed section",
                "evidence_links": "photo-1, photo-2",
            }
        ],
        assignments=assignments,
        report_location="Fallback Yard",
    )

    assert rows[0]["cost_code"] == "CC-100"
    assert rows[0]["actual_performer"] == "Crew B"
    assert rows[0]["planned_performer"] == "Crew A"
    assert rows[0]["work_area"] == "North"
    assert rows[0]["location"] == "Sta 1+00"
    assert rows[0]["evidence_links"] == ["photo-1", "photo-2"]

    with pytest.raises(ValueError):
        normalize_cost_code_actual_rows(
            [{"cost_code": "CC-999", "installed_quantity": 1}],
            assignments=assignments,
        )


def test_build_progress_snapshot_supports_authorized_quantities_and_overrun():
    assignments = [
        {
            "code": "CC-100",
            "item_name": "Pipe",
            "unit_of_measure": "LF",
            "original_quantity": 100.0,
            "authorized_quantity": 100.0,
            "forecast_quantity": 120.0,
            "planned_performer": "Crew A",
        }
    ]
    daily_rows = [{"cost_code": "CC-100", "installed_quantity": 130.0}]

    progress = build_progress_snapshot(assignments, daily_rows)
    code = progress["codes"][0]

    assert progress["overall_percent_complete"] == 130.0
    assert progress["total_authorized_quantity"] == 100.0
    assert progress["total_forecast_quantity"] == 120.0
    assert progress["total_overrun_quantity"] == 30.0
    assert progress["supports_over_100_percent"] is True
    assert code["overrun_quantity"] == 30.0
    assert code["remaining_authorized_quantity"] == -30.0
    assert code["planned_performer"] == "Crew A"
    assert "target_man_hours" not in code


def test_projection_docs_are_derived_and_financially_shielded():
    assignments = [
        {
            "code": "CC-100",
            "item_name": "Pipe",
            "unit_of_measure": "LF",
            "original_quantity": 100.0,
            "authorized_quantity": 125.0,
            "forecast_quantity": 140.0,
            "planned_performer": "Crew A",
            "bid_unit_price": 22.5,
            "target_man_hours": 1.5,
        }
    ]

    legacy = build_legacy_cost_code_projection(assignments)
    ods_doc = build_ods_project_cost_code_doc(
        project_number="ZZ-RUNTIME-CERT-2026",
        assignments=assignments,
        tenant_id="masci",
        version=3,
    )

    assert legacy == [{"code": "CC-100", "description": "Pipe", "active": True}]
    assert ods_doc["source_authority"] == "jobs_master.assigned_cost_codes"
    assert ods_doc["projection_locked"] is True
    assert ods_doc["editable"] is False
    assert ods_doc["cost_codes"][0]["planned_qty"] == 125.0
    assert "bid_unit_price" not in ods_doc["cost_codes"][0]
    assert "target_man_hours" not in ods_doc["cost_codes"][0]


def test_ods_v1_fact_builder_prefers_cost_code_actuals_without_legacy_double_count():
    report = {
        "id": "dr-1",
        "project_number": "ZZ-RUNTIME-CERT-2026",
        "report_date": "2026-07-17",
        "prepared_by": "foreman",
        "cost_code_quantities": [
            {
                "cost_code": "CC-100",
                "item_name": "Pipe",
                "unit_of_measure": "LF",
                "installed_quantity": 11.5,
                "actual_performer": "Crew B",
                "work_area": "North",
                "location": "Sta 1+00",
                "notes": "Installed beyond authorized quantity",
                "evidence_links": ["photo-1", "ticket-7"],
            }
        ],
        "activities": [
            {"cost_code": "CC-100", "activity": "Legacy row", "quantity": 999, "unit": "LF"}
        ],
    }

    facts = ingest._build_facts_from_dr_v1_report(report)
    prod = [f for f in facts if f["fact_type"] == "production_fact"]

    assert len(prod) == 1
    assert prod[0]["payload"]["entry_mode"] == "assigned_cost_code_actual"
    assert prod[0]["payload"]["quantity"] == 11.5
    assert prod[0]["payload"]["actual_performer"] == "Crew B"
    assert prod[0]["payload"]["evidence_links"] == ["photo-1", "ticket-7"]


@pytest.mark.asyncio
async def test_ods_v1_ingest_skips_synthetic_and_certification_rows(monkeypatch):
    monkeypatch.setattr(ingest, "ods_enabled", lambda: True)
    monkeypatch.setattr(ingest, "dr_v2_spine_emission_enabled", lambda: True)

    result = await ingest.ingest_dr_v1_report(
        db=None,
        report={
            "id": "dr-hidden",
            "project_number": "ZZ-RUNTIME-CERT-2026",
            "report_date": "2026-07-17",
            "synthetic_record": True,
        },
    )

    assert result["skipped"] is True
    assert result["reason"] == "excluded_from_operations"