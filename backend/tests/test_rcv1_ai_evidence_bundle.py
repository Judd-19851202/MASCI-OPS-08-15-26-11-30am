from services.dr_ai.evidence import build_evidence_bundle


def test_ai_evidence_bundle_includes_full_daily_report_context_fields():
    payload = {
        "project_name": "Fixture Project",
        "project_number": "20-07",
        "report_date": "2026-07-23",
        "prepared_by": "RCV Foreman",
        "superintendent": "Jaymn Judd",
        "location": "Sanford",
        "weather_summary": "Hot and humid",
        "weather_snapshots": [{"time": "06:00", "temp_f": 82}],
        "weather_snapshot_meta": {"observation_timestamp": "2026-07-23T06:00:00-04:00"},
        "distribution_list": ["pm@example.com"],
        "schedule_delays": "Yes",
        "schedule_delays_notes": "Utility conflict",
        "weather_impact": "No",
        "safety_notes": "Trench box used",
        "safety_incidents_today": "No",
        "injuries_reported": "No",
        "incident_notes": "",
        "general_notes": "Resident access maintained",
        "notes": "Voice transcript text",
        "narrative_sections": {
            "work_completed": "Installed 120 LF of pipe",
            "follow_ups": "Await utility owner signoff",
            "tomorrow_plan": "Continue southbound run",
        },
        "cost_code_quantities": [{"cost_code": "033000", "installed_quantity": "120"}],
        "linked_excavation_ids": ["EX-1"],
        "excavation_activity_today": "Yes",
        "attachments": [{"filename": "daily_ticket.pdf"}],
        "photos": ["data:image/jpeg;base64,abc123"],
    }

    bundle = build_evidence_bundle(payload)

    assert bundle["prepared_by"] == "RCV Foreman"
    assert bundle["superintendent"] == "Jaymn Judd"
    assert bundle["weather_snapshots"][0]["temp_f"] == 82
    assert bundle["schedule_delays_notes"] == "Utility conflict"
    assert bundle["safety_notes"] == "Trench box used"
    assert bundle["notes"] == "Voice transcript text"
    assert bundle["cost_code_quantities"][0]["cost_code"] == "033000"
    assert bundle["linked_excavation_ids"] == ["EX-1"]
    assert bundle["distribution_list"] == ["pm@example.com"]
    assert bundle["photos"][0]["ref"] == "photo:0"