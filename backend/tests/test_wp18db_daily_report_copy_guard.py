from __future__ import annotations

from services.operations_control.registry import build_operations_control_plane_registry


def test_daily_report_submitted_copy_is_operator_friendly():
    template = build_operations_control_plane_registry()["templates"]["oppc.daily_report.submitted.v1"]
    body = f"{template['title_template']}\n{template['message_template']}\n{template['email_note']}"
    lowered = body.lower()
    assert 'oppc proof chain' not in lowered
    assert 'registered control-plane policy' not in lowered
    assert 'operations control plane' not in lowered


def test_daily_report_communication_intent_description_avoids_internal_jargon():
    intent = build_operations_control_plane_registry()["communication_intents"]["oppc.daily_report.notify_project_team"]
    lowered = str(intent.get('description') or '').lower()
    assert 'oppc proof chain' not in lowered
    assert 'control-plane' not in lowered