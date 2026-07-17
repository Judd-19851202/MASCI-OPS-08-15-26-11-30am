from __future__ import annotations

from pathlib import Path


SAFETY_PATH = "/app/backend/routes/safety.py"
EQUIPMENT_PATH = "/app/backend/routes/equipment.py"
QAQC_PATH = "/app/backend/routes/qaqc.py"
DAILY_REPORT_LIFECYCLE_PATH = "/app/backend/routes/daily_report_lifecycle.py"


def test_safety_workflows_emit_bell_notifications_for_meeting_jha_incident():
    src = Path(SAFETY_PATH).read_text(encoding="utf-8")
    assert '"type": "meeting.submitted"' in src
    assert '"type": "jha.submitted"' in src
    assert '"type": "incident.created"' in src
    assert 'emit_task_and_notification(' in src


def test_inspection_deficiency_emits_safety_and_pm_notifications():
    src = Path(SAFETY_PATH).read_text(encoding="utf-8")
    assert '"type": "inspection.deficiency"' in src
    assert '"Stop-work issued · safety inspection follow-up"' in src
    assert 'event_key="inspection.pm_visibility"' in src


def test_qaqc_and_equipment_failure_emit_notifications():
    qaqc = Path(QAQC_PATH).read_text(encoding="utf-8")
    equipment = Path(EQUIPMENT_PATH).read_text(encoding="utf-8")
    assert '"type": "qaqc.deficiency"' in qaqc
    assert '"type": "preop.failed"' in equipment
    assert 'emit_task_and_notification(' in qaqc
    assert 'emit_task_and_notification(' in equipment


def test_daily_report_pending_review_emits_bell_notifications():
    src = Path(DAILY_REPORT_LIFECYCLE_PATH).read_text(encoding="utf-8")
    assert '"type": "daily_report.pending_review"' in src
    assert 'for recipient in ("admin", "pm", "safety")' in src
    assert 'emit_notification(db, {' in src