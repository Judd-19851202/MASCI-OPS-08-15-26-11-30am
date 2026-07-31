from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, "/app/backend")

from lib.backup_coverage_policy import backup_policy_for_collection  # noqa: E402
from lib.cors_truth import summarize_cors_truth  # noqa: E402
from services.operations_control import backups as backups_mod  # noqa: E402
from services.operations_control import deploy as deploy_mod  # noqa: E402
from services.operations_control.security import _security_posture  # noqa: E402


def test_summarize_cors_truth_treats_blank_env_as_pinned_regex_policy():
    out = summarize_cors_truth({"CORS_ORIGINS": "", "CORS_ORIGIN_REGEX": ""})
    assert out["cors_pinned"] is True
    assert out["origin_regex_configured"] is True
    assert out["allows_wildcard_origin"] is False


def test_backup_policy_marks_motive_events_non_blocking_ttl():
    policy = backup_policy_for_collection("motive_events")
    assert policy.classification == "ttl_telemetry"
    assert policy.coverage_requirement == "do_not_require_for_complete_coverage"
    assert policy.blocking is False


def test_security_posture_uses_effective_cors_truth_not_blank_env_flag(monkeypatch):
    class _Identity:
        def to_safe_dict(self):
            return {"app_env": "production", "db_name": "masci_safety"}

    class _Validation:
        status = "VERIFIED"
        valid = True
        mismatch_category = None

        def to_safe_dict(self):
            return {"detail": "ok"}

    for key in ["APP_ENV", "DB_NAME", "MONGO_URL", "CORS_ORIGINS"]:
        monkeypatch.setenv(key, "present")
    monkeypatch.setenv("CORS_ORIGINS", "")
    out = asyncio.run(_security_posture({
        "_runtime_identity_bundle": {
            "identity": _Identity(),
            "validation": _Validation(),
        }
    }))
    assert out["cors_pinned"] is True
    assert out["status"] == "healthy"


def test_backup_health_prefers_canonical_truth_over_empty_local_cache(monkeypatch):
    async def fake_canonical(_payload):
        return {
            "available": True,
            "status": "healthy",
            "summary": "Canonical recovery posture GREEN · latest archive.zip · age 12.0m",
            "snapshot": {"pill": "GREEN"},
        }

    monkeypatch.setattr(backups_mod, "load_canonical_backup_truth", fake_canonical)
    monkeypatch.setattr(backups_mod, "local_backup_cache_snapshot", lambda: {
        "backup_dir": "/tmp/none",
        "exists": False,
        "file_count": 0,
        "total_bytes": 0,
        "latest": None,
    })
    out = asyncio.run(backups_mod._backup_health_dry_run({"_db": object()}))
    assert out["status"] == "healthy"
    assert out["canonical_source"] == "/api/admin/recovery/snapshot"
    assert "authoritative backup truth" in out["warnings"][0]


def test_deploy_recovery_playbook_uses_canonical_backup_timestamp(monkeypatch):
    async def fake_canonical(_payload):
        return {
            "available": True,
            "status": "warning",
            "summary": "Canonical recovery posture AMBER",
            "snapshot": {
                "pill": "AMBER",
                "last_backup": {"ts": "2026-07-31T13:17:00+00:00"},
                "archive_lineage": {},
            },
        }

    monkeypatch.setattr(deploy_mod, "load_canonical_backup_truth", fake_canonical)
    monkeypatch.setattr(deploy_mod, "local_backup_cache_snapshot", lambda: {
        "backup_dir": "/tmp/none",
        "exists": False,
        "file_count": 0,
        "total_bytes": 0,
        "latest": None,
    })
    out = asyncio.run(deploy_mod._deploy_recovery_status({"_db": object()}))
    assert out["status"] == "warning"
    assert out["latest_canonical_backup_at"] == "2026-07-31T13:17:00+00:00"
    assert out["canonical_source"] == "/api/admin/recovery/snapshot"