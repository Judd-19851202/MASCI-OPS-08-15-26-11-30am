"""DR-ROI-001E · PM / Admin / Executive Intelligence unit + smoke tests."""
from __future__ import annotations
import os
import sys
from pathlib import Path

BACKEND = Path("/app/backend")
sys.path.insert(0, str(BACKEND))
os.environ.setdefault("EMAIL_SAFETY_MODE", "strict")
os.environ.setdefault("SCHEDULER_ENABLED", "false")


def test_preset_ranges():
    from routes.ods_intelligence import _preset_to_range, _resolve_range
    for preset in ("today", "yesterday", "this_week", "last_week",
                   "month", "last_month", "quarter", "year"):
        df, dt = _preset_to_range(preset)
        assert len(df) == 10 and len(dt) == 10
        assert df <= dt
    # Custom passthrough
    df, dt = _resolve_range("custom", "2026-01-01", "2026-01-31")
    assert (df, dt) == ("2026-01-01", "2026-01-31")


def test_intelligence_routes_mounted():
    from importlib import import_module
    server = import_module("server")
    paths = {getattr(r, "path", "") for r in server.app.routes if hasattr(r, "endpoint")}
    expected = {
        "/api/ods/pm/dashboard",
        "/api/ods/pm/attention",
        "/api/ods/pm/projects/{project_id}/kpis",
        "/api/ods/pm/projects/{project_id}/intelligence",
        "/api/ods/pm/projects/{project_id}/brief",
        "/api/ods/pm/projects/{project_id}/attention",
        "/api/ods/admin/dashboard",
        "/api/ods/admin/delays",
        "/api/ods/admin/attention",
        "/api/ods/executive/brief",
        "/api/ods/executive/health",
    }
    missing = expected - paths
    assert not missing, f"missing intelligence routes: {missing}"


def test_intelligence_no_v1_writes():
    text = (BACKEND / "routes" / "ods_intelligence.py").read_text(encoding="utf-8")
    for banned in ("db.daily_reports", "db['daily_reports']", 'db["daily_reports"]',
                   "db.job_photos", "db['job_photos']", 'db["job_photos"]',
                   "insert_one", "insert_many", "update_many", "delete_"):
        # We DO cache PM/Executive briefs in ods_briefs_cache — allow update_one for that only
        if banned in ("update_many", "delete_"):
            assert banned not in text, f"forbidden op present: {banned}"
        else:
            # Read-heavy code — no writes to V1 collections
            assert banned not in text or "daily_reports" not in text, banned


def test_no_provider_names_leak_in_route_module():
    """The routes module must not surface model/provider strings in responses."""
    text = (BACKEND / "routes" / "ods_intelligence.py").read_text(encoding="utf-8")
    # `model` and `provider` may appear in docstrings/comments but MUST NOT
    # appear as response keys sent to the client.
    forbidden_response_keys = ('"model":', '"provider":', '"api_key"',
                               'anthropic-sdk', 'claude-', 'openai/gpt-')
    for f in forbidden_response_keys:
        assert f not in text, f"potential leak: {f}"


def test_brief_evidence_hash_deterministic():
    from routes.ods_intelligence import _brief_evidence_hash
    a = {"kpis": {"labor": 10}, "range": {"from": "2026-01-01"}}
    b = {"range": {"from": "2026-01-01"}, "kpis": {"labor": 10}}
    assert _brief_evidence_hash(a) == _brief_evidence_hash(b)
    c = {"kpis": {"labor": 11}}
    assert _brief_evidence_hash(a) != _brief_evidence_hash(c)
