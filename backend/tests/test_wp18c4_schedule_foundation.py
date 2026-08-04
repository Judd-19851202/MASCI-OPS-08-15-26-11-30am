from services.project_schedule_authority import (
    _assignment_projection,
    _selected_payload_for_row,
)


def test_wp18c4_selected_payload_preserves_structured_planned_refs():
    row = {
        "normalized": {},
        "suggestion": {},
        "selected": {
            "planned_crew_ids": [{"crew_id": "crew-1", "label": "Crew Alpha"}],
            "planned_employee_ids": [{"employee_id": "emp-1", "label": "Jose Alvarez"}],
            "planned_equipment_ids": [{"equipment_id": "eq-7", "label": "Excavator 7"}],
            "planned_materials": [{"material_id": "mat-1", "description": "Pipe", "quantity": 12, "unit": "LF"}],
            "planned_vendor_refs": [{"vendor_id": "ven-1", "vendor_name": "Acme Supply"}],
            "planned_subcontractor_refs": [{"vendor_id": "sub-9", "subcontractor_name": "Delta Civil"}],
            "planned_constraints": [{"constraint_id": "con-1", "category": "weather", "title": "Weather hold", "status": "planned", "notes": "Rain risk"}],
            "planned_production_quantity": 44,
            "planned_hours": 18,
        },
    }

    selected = _selected_payload_for_row(row, {})

    assert selected["planned_crew_ids"] == [{"crew_id": "crew-1", "label": "Crew Alpha"}]
    assert selected["planned_employee_ids"] == [{"employee_id": "emp-1", "label": "Jose Alvarez"}]
    assert selected["planned_equipment_ids"] == [{"equipment_id": "eq-7", "label": "Excavator 7"}]
    assert selected["planned_materials"] == [{"material_id": "mat-1", "description": "Pipe", "quantity": 12.0, "unit": "LF"}]
    assert selected["planned_vendor_refs"] == [{"vendor_id": "ven-1", "vendor_name": "Acme Supply"}]
    assert selected["planned_subcontractor_refs"] == [{"vendor_id": "sub-9", "subcontractor_name": "Delta Civil"}]
    assert selected["planned_constraints"] == [{"constraint_id": "con-1", "category": "weather", "title": "Weather hold", "status": "planned", "notes": "Rain risk"}]
    assert selected["planned_production_quantity"] == 44.0
    assert selected["planned_hours"] == 18.0


def test_wp18c4_assignment_projection_uses_nested_planned_assignment_values():
    activity = {
        "activity_id": "ACT-100",
        "activity_name": "Install drainage pipe",
        "project_cost_code": "300-1",
        "phase_id": "PH-1",
        "work_package_id": "WP-1",
        "budget_line_id": "BL-1",
        "customer_pay_item_number": "401-2",
        "enterprise_work_type_id": "work-type:pipe",
        "planned_start_date": "2026-08-03",
        "duration_days": 3,
        "owner": "",
        "planned_assignments": {
            "planned_crew_ids": [{"crew_id": "crew-1", "label": "Crew Alpha"}],
            "planned_employee_ids": [{"employee_id": "emp-1", "label": "Jose Alvarez"}],
            "planned_equipment_ids": [{"equipment_id": "eq-7", "label": "Excavator 7"}],
            "planned_materials": [{"material_id": "mat-1", "description": "Pipe", "quantity": 10, "unit": "LF"}],
            "planned_vendor_refs": [{"vendor_id": "ven-1", "vendor_name": "Acme Supply"}],
            "planned_subcontractor_refs": [{"vendor_id": "sub-9", "subcontractor_name": "Delta Civil"}],
            "planned_production_quantity": 25,
            "planned_hours": 16,
            "planned_constraints": [{"constraint_id": "con-1", "category": "weather", "title": "Weather hold", "status": "planned", "notes": "Rain risk"}],
        },
    }

    assignment = _assignment_projection(activity)

    assert assignment["authorized_quantity"] == 25.0
    assert assignment["original_quantity"] == 25.0
    assert assignment["forecast_quantity"] == 25.0
    assert assignment["planned_hours"] == 16.0
    assert assignment["resource_demand"]["labor_hours"] == 16.0
    assert assignment["planned_performer"] == "Crew Alpha"
    assert assignment["planned_materials"] == ["Pipe"]
    assert assignment["planned_vendor_refs"] == ["Acme Supply"]
    assert assignment["planned_subcontractor_refs"] == ["Delta Civil"]
    assert assignment["planned_constraints"] == ["Weather hold"]