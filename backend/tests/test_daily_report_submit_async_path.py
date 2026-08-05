from pathlib import Path


def test_daily_report_submit_offloads_heavy_post_submit_pipeline():
    src = Path("/app/backend/routes/daily_reports.py").read_text()

    assert "async def _run_post_submit_pipeline" in src
    assert 'background_tasks.add_task(\n                _run_post_submit_pipeline,' in src or "background_tasks.add_task(_run_post_submit_pipeline" in src
    assert 'report_dict.setdefault("schedule_actual_candidates", [])' in src
    assert 'schedule_auto_email("daily-report", merged_doc)' in src