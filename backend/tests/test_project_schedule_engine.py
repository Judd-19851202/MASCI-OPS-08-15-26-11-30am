from services.cost_codes.schedule_engine import build_schedule_snapshot, render_dot_schedule_pdf
from services.cost_codes.foundation import build_planning_lifecycle_snapshot, build_planning_readiness, build_weekly_rollover_preview


def _assignment(code, start, duration, predecessors=None):
    return {
        "code": code,
        "item_name": code,
        "schedule_start_date": start,
        "duration_days": duration,
        "predecessor_codes": predecessors or [],
    }


def test_cpm_slides_successors_when_predecessor_is_delayed():
    assignments = [
        _assignment("MILL", "2026-07-10", 4),
        _assignment("PAVE", "2026-07-12", 2, ["MILL"]),
    ]
    progress = {
        "codes": [
            {"code": "MILL", "authorized_quantity": 100, "installed_quantity": 25, "progress_percent": 25.0, "actual_start_date": "2026-07-10", "last_progress_date": "2026-07-17"},
            {"code": "PAVE", "authorized_quantity": 100, "installed_quantity": 0, "progress_percent": 0.0},
        ]
    }
    snap = build_schedule_snapshot(assignments, progress, anchor_date="2026-07-18")
    tasks = {row["code"]: row for row in snap["tasks"]}
    assert tasks["MILL"]["schedule_status"] == "delayed"
    assert tasks["PAVE"]["forecast_start_date"] > tasks["PAVE"]["baseline_start_date"]


def test_progress_percent_flows_into_task_bar_data():
    snap = build_schedule_snapshot([_assignment("CC-1", "2026-07-18", 3)], {"codes": [{"code": "CC-1", "authorized_quantity": 200, "installed_quantity": 110, "progress_percent": 55.0}]}, anchor_date="2026-07-18")
    task = snap["tasks"][0]
    assert task["progress_percent"] == 55.0
    assert task["installed_quantity"] == 110.0


def test_dot_schedule_pdf_renders_binary():
    snap = build_schedule_snapshot([_assignment("CC-1", "2026-07-18", 2)], {"codes": []}, anchor_date="2026-07-18")
    pdf = render_dot_schedule_pdf("20-07", snap)
    assert pdf.startswith(b"%PDF")


def test_planning_readiness_flags_missing_oppc_fields():
    readiness = build_planning_readiness([
        {
            "code": "CC-1",
            "item_name": "Drainage",
            "unit_of_measure": "LF",
            "authorized_quantity": 150,
            "schedule_start_date": "2026-07-18",
            "duration_days": 2,
            "schedule_phase": "",
            "planned_performer": "",
        }
    ])
    assert readiness["status"] == "needs_attention"
    assert readiness["missing_required_counts"]["planned_performer"] == 1
    assert readiness["missing_required_counts"]["schedule_phase"] == 1


def test_planning_lifecycle_promotes_ready_projects_to_publishable_state():
    readiness = build_planning_readiness([
        {
            "code": "CC-1",
            "item_name": "Drainage",
            "unit_of_measure": "LF",
            "authorized_quantity": 150,
            "schedule_start_date": "2026-07-18",
            "duration_days": 2,
            "schedule_phase": "Phase 1",
            "planned_performer": "Crew A",
        }
    ])
    lifecycle = build_planning_lifecycle_snapshot(
        planning_readiness=readiness,
        stored={"has_unpublished_changes": True},
        schedule_window={"anchor_date": "2026-07-18", "start_date": "2026-07-11", "end_date": "2026-07-25", "history_days": 7, "forecast_days": 7, "visible_days": 15},
    )
    assert lifecycle["status"] == "ready_to_publish"
    assert lifecycle["supports_publish"] is True


def test_weekly_rollover_preview_rolls_not_started_work_forward():
    readiness = build_planning_readiness([
        {
            "code": "CC-1",
            "item_name": "Drainage",
            "unit_of_measure": "LF",
            "authorized_quantity": 150,
            "schedule_start_date": "2026-07-10",
            "duration_days": 2,
            "schedule_phase": "Phase 1",
            "planned_performer": "Crew A",
        }
    ])
    preview = build_weekly_rollover_preview(
        [
            {
                "code": "CC-1",
                "item_name": "Drainage",
                "unit_of_measure": "LF",
                "authorized_quantity": 150,
                "schedule_start_date": "2026-07-10",
                "duration_days": 2,
                "schedule_phase": "Phase 1",
                "planned_performer": "Crew A",
            }
        ],
        {"codes": [{"code": "CC-1", "authorized_quantity": 150, "installed_quantity": 0, "progress_percent": 0.0}]},
        readiness,
        anchor_date="2026-07-18",
    )
    assert preview["status"] == "ready"
    assert preview["rollover_anchor_date"] == "2026-07-20"
    assert preview["actions"][0]["rule_applied"] == "roll_to_next_anchor"
    assert preview["actions"][0]["proposed_start_date"] == "2026-07-20"