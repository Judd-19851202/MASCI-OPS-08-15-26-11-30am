from services.cost_codes.schedule_engine import build_schedule_snapshot, render_dot_schedule_pdf


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