from services.project_controls_authority import (
    _derive_lifecycle_from_job,
    _suggest_work_type,
    derive_work_blocks_from_report,
)


def test_wp18c2_derive_work_blocks_from_cost_rows_keeps_resource_links():
    report = {
        "id": "dr-001",
        "project_number": "24-01",
        "location": "Mainline",
        "cost_code_quantities": [
            {
                "cost_code": "300-101",
                "item_name": "Surface asphalt",
                "installed_quantity": 125,
                "unit_of_measure": "TON",
                "cpm_activity_id": "ACT-7",
                "cpm_activity_name": "Paving",
            }
        ],
        "masci_crews": [{"employee_id": "E1", "name": "Worker One", "hours": 8, "cost_code": "300-101"}],
        "equipment": [{"equipment_id": "EQ-1", "description": "Paver", "hours_used": 6, "cost_code": "300-101"}],
        "materials": [{"description": "Asphalt", "quantity": 125, "unit": "TON", "cost_code": "300-101"}],
        "subcontractors": [],
        "constraints": [],
        "photos": ["photo-a"],
    }

    blocks = derive_work_blocks_from_report(report)

    assert len(blocks) == 1
    block = blocks[0]
    assert block["cost_code"] == "300-101"
    assert block["installed_quantity"] == 125
    assert block["schedule_activity_id"] == "ACT-7"
    assert len(block["labor_entries"]) == 1
    assert len(block["equipment_entries"]) == 1
    assert len(block["material_entries"]) == 1


def test_wp18c2_suggest_work_type_matches_keywords():
    work_types = [
        {"work_type_id": "work-type:asphalt", "name": "Asphalt", "code": "ASPHALT", "keywords": ["asphalt", "pave"]},
        {"work_type_id": "work-type:drainage", "name": "Drainage", "code": "DRAINAGE", "keywords": ["pipe", "storm"]},
    ]
    pay_item = {"customer_pay_item_number": "400-2", "description": "Asphalt surface course"}

    suggestion = _suggest_work_type(pay_item, work_types)

    assert suggestion["primary_work_type_id"] == "work-type:asphalt"
    assert suggestion["confidence"] in {"medium", "high"}


def test_wp18c2_derive_lifecycle_prefers_archive_signal():
    state, notes = _derive_lifecycle_from_job({"project_number": "24-02", "active": False, "archived": True})

    assert state == "Archived"
    assert any("archive" in note.lower() for note in notes)
