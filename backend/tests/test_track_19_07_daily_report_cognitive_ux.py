"""Track 19.07 · Daily Report UX Simplification & Cognitive Architecture — Lock Test.

Every assertion enforces ONE property:
* zero backend/schema/route drift, AND
* the cognitive-redundancy fix (NarrativeWorkflow collapsed behind
  "Additional context (rarely needed)" affordance), AND
* the six cognitive checkpoints present on the redesigned bands.
"""
from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND = REPO_ROOT / "frontend"
BACKEND = REPO_ROOT / "backend"
MEMORY = REPO_ROOT / "memory"

_UI = (FRONTEND / "src/pages/NewDailyReport.jsx").read_text(encoding="utf-8")


# --- reports & PRD ---

def test_track_19_07_reports_exist():
    for name in [
        "TRACK_19_07_COGNITIVE_UX_AUDIT.md",
        "TRACK_19_07_INFORMATION_ARCHITECTURE.md",
        "TRACK_19_07_UI_CHANGE_MAP.md",
        "TRACK_19_07_EXECUTIVE_SUMMARY.md",
        "TRACK_19_07_TEST_REPORT.md",
    ]:
        p = MEMORY / name
        assert p.exists(), f"missing 19.07 report: {name}"
        assert len(p.read_text(encoding="utf-8")) > 300


def test_prd_updated_for_19_07():
    prd = (MEMORY / "PRD.md").read_text(encoding="utf-8")
    assert "TRACK 19.07" in prd or "Track 19.07" in prd


# --- Zero backend drift (schema + routes) ---

_SCHEMA_KEYS = [
    "project_name:", "project_number:", "location:", "report_date:",
    "report_number:", "prepared_by:", "superintendent:",
    "weather_summary:", "weather_snapshots:", "weather_impact:",
    "schedule_delays:", "safety_incidents_today:", "injuries_reported:",
    "incident_notes:", "safety_notified:", "safety_contact_person:",
    "safety_contact_time:", "incident_report_filled:", "incident_report_time:",
    "general_notes:", "masci_crews:", "subcontractors:", "visitors:",
    "equipment:", "materials:", "activities:", "outbound_materials:",
    "production:", "constraints:", "photos:", "narrative_sections:",
    "photo_captions:", "prepared_by_signature:", "superintendent_signature:",
    "distribution_list:", "attachments:",
]


def test_no_schema_keys_removed_or_renamed_in_19_07():
    src = (BACKEND / "routes/daily_reports.py").read_text(encoding="utf-8")
    for k in _SCHEMA_KEYS:
        assert k in src


def test_daily_report_routes_intact_after_19_07():
    src = (BACKEND / "routes/daily_reports.py").read_text(encoding="utf-8")
    for path in [
        '"/daily-reports"', '"/daily-reports.csv"',
        '"/daily-reports/next-number"', 'audit-footer',
    ]:
        assert path in src


def test_attachment_and_recent_context_endpoints_intact():
    src = (BACKEND / "server.py").read_text(encoding="utf-8")
    assert "/daily-reports/attachments/upload" in src
    assert "/jobs/{project_number}/recent-context" in src


# --- Cognitive redundancy fix ---

def test_narrative_workflow_collapsed_behind_additional_context():
    assert 'data-testid="dr-narrative-additional-context"' in _UI
    assert '<details' in _UI
    assert "Additional context (rarely needed)" in _UI


def test_tell_the_story_of_the_day_label_removed():
    # The confusing "Tell the story of the day" prompt is replaced by
    # a single optional operational-notes field with clearer intent.
    assert "Tell the story of the day" not in _UI


def test_operational_notes_replaces_general_notes_label():
    assert "Operational notes (optional)" in _UI
    # The new microcopy makes the intent explicit — not another log.
    assert "isn't already captured" in _UI


def test_narrative_sections_schema_key_still_bound_in_ui():
    # The persisted schema key remains reachable from the UI so
    # existing drafts + historical DRs are never lost.
    assert '"narrative_sections"' in _UI
    assert "NarrativeWorkflow" in _UI


# --- Six cognitive checkpoints present ---

def test_six_cognitive_checkpoints_present():
    for checkpoint in [
        'data-cognitive-checkpoint="who-was-there"',
        'data-cognitive-checkpoint="what-got-done"',
        'data-cognitive-checkpoint="what-impacted-today"',
        'data-cognitive-checkpoint="what-moved"',
        'data-cognitive-checkpoint="was-the-job-safe"',
        'data-cognitive-checkpoint="what-happens-next"',
    ]:
        assert checkpoint in _UI


def test_six_cognitive_labels_render_in_ui():
    for label in [
        "Who was there?",
        "What got done?",
        "What impacted today?",
        "What moved?",
        "Was the job safe?",
        "What happens next?",
    ]:
        assert label in _UI


# --- Progressive-disclosure architecture preserved (Track 19.06) ---

def test_progressive_disclosure_gates_still_present():
    assert "Did MASCI employees work on site today?" in _UI
    assert "Were subcontractors on site today?" in _UI
    assert "Were visitors or inspectors on site today?" in _UI
    assert "Was MASCI equipment on site or used today?" in _UI
    assert "Were materials delivered or imported today?" in _UI
    assert "Were materials exported or hauled off today?" in _UI
    assert "Did anything delay, change, or impact production today?" in _UI


def test_photo_min_still_six():
    schema = (FRONTEND / "src/lib/dailyReportSchema.js").read_text(encoding="utf-8")
    assert "photo_min: 6" in schema


def test_smart_prefill_offer_intact():
    for k in ["smartPrefillOffer",
              "daily-report-smart-prefill-apply",
              "daily-report-smart-prefill-dismiss"]:
        assert k in _UI


def test_autosave_hook_intact():
    assert "useFormDraft" in _UI


def test_hr_roster_binding_intact():
    src = (FRONTEND / "src/components/EmployeeCombo.jsx").read_text(encoding="utf-8")
    assert "fetchHrRoster" in src
    assert "subscribeHrRoster" in src


def test_actor_scoped_draft_still_stamps():
    src = (FRONTEND / "src/lib/resiliency/draftStore.js").read_text(encoding="utf-8")
    assert "savedByActor" in src


def test_attachment_upload_still_mounted():
    assert "<AttachmentUpload" in _UI


def test_photo_upload_still_mounted():
    assert "<PhotoUpload" in _UI


def test_tomorrow_plan_field_still_present():
    assert 'data-testid="input-tomorrow-plan"' in _UI


def test_submit_button_still_present():
    assert 'data-testid="submit-top-btn"' in _UI
    assert "Submit Daily Report" in _UI


def test_excavation_hard_gate_still_present():
    src = (BACKEND / "routes/daily_reports.py").read_text(encoding="utf-8")
    assert "excavation_record_required" in src or "linked_excavation_ids" in src


def test_final_go_verdict_present():
    p = (MEMORY / "TRACK_19_07_TEST_REPORT.md").read_text(encoding="utf-8")
    assert "GO" in p
