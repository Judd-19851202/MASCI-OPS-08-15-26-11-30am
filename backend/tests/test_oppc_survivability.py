from services.cost_codes.foundation import build_forecast_snapshot_record, normalize_forecast_override
from services.cost_codes.oppc_briefings import approve_briefing, freeze_briefing
from services.cost_codes.oppc_confidence import build_confidence_snapshot_record


def test_forecast_snapshot_has_version_and_integrity_hash():
    snapshot = build_forecast_snapshot_record(
        project_number="20-07",
        schedule={
            "projected_finish_date": "2026-08-01",
            "committed_finish_date": "2026-08-03",
            "critical_path": ["PIPE"],
            "override_count": 1,
            "warnings": [],
            "hardening_summary": {"critical_activities": 1},
            "window": {"anchor_date": "2026-07-28"},
        },
        scenario_key="additional_crew",
        scenario_label="Additional Crew",
        actor_label="qa@example.com",
    )
    assert snapshot["version"] == 1
    assert len(snapshot["content_hash"]) == 64


def test_confidence_snapshot_has_version_and_integrity_hash():
    snapshot = build_confidence_snapshot_record(
        project_number="20-07",
        confidence={"score": 88, "band": "high_confidence", "status": "green", "components": [], "freshness": {}, "warnings": [], "explainability": []},
        actor_label="qa@example.com",
    )
    assert snapshot["version"] == 1
    assert len(snapshot["content_hash"]) == 64


def test_override_history_is_append_only_and_hashed():
    override = normalize_forecast_override(
        cost_code="PIPE",
        calculated_start_date="2026-07-20",
        calculated_finish_date="2026-07-25",
        adjusted_start_date="2026-07-20",
        adjusted_finish_date="2026-07-24",
        reason="Executive acceleration",
        actor_label="qa@example.com",
        actor_role="admin",
        evidence_links=["doc://directive-1"],
    )
    revised = normalize_forecast_override(
        cost_code="PIPE",
        calculated_start_date="2026-07-20",
        calculated_finish_date="2026-07-25",
        adjusted_start_date="2026-07-20",
        adjusted_finish_date="2026-07-23",
        reason="Updated executive acceleration",
        actor_label="qa@example.com",
        actor_role="admin",
        evidence_links=["doc://directive-2"],
        existing=override,
    )
    assert revised["override_id"] == override["override_id"]
    assert len(revised["history"]) == 2
    assert len(revised["content_hash"]) == 64


def test_briefing_approval_then_freeze_preserves_hash_and_status():
    doc = {
        "scope_type": "project",
        "scope_key": "20-07",
        "week_ending": "2026-07-27",
        "status": "draft",
        "sections": {"summary": {"open_variances": 1}},
        "warnings": [],
        "approval_history": [],
    }
    approved = approve_briefing(doc, actor_label="qa@example.com")
    frozen = freeze_briefing(approved, actor_label="qa@example.com")
    assert approved["status"] == "approved"
    assert frozen["status"] == "frozen"
    assert frozen["frozen"] is True
    assert len(frozen["content_hash"]) == 64