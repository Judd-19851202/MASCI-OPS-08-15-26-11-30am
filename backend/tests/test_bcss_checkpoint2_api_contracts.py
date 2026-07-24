from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace

from lib.archive_lineage import public_archive_lineage_payload
from routes.recovery_dashboard import build_recovery_dashboard_router


def _lineage_payload() -> dict:
    return {
        "truth_subject": "bcss_backup_archive_lineage",
        "resolver_version": "bcss-r02-1",
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "authoritative_recovery_point_time": datetime.now(timezone.utc).isoformat(),
        "authoritative_time_source": "VERIFIED_LOGICAL_RECOVERY_POINT",
        "freshness_age_minutes": 12.0,
        "freshness_age_hours": 0.2,
        "evidence_quality": "VERIFIED_LOGICAL_RECOVERY_POINT",
        "lineage_confidence": "HIGH",
        "integrity_status": "PASS",
        "completeness_status": "COMPLETE",
        "availability_status": "AVAILABLE",
        "degradation_reasons": [],
        "thresholds": {},
        "newest_observed_artifact": {
            "artifact_identity": {"artifact_id": "obs"},
            "filename": "obs.zip",
            "object_key": "backups/auto-90d/obs.zip",
            "authoritative_time": None,
            "observed_time": datetime.now(timezone.utc).isoformat(),
            "authoritative_time_source": "UNKNOWN",
            "freshness_age_minutes": 10.0,
            "integrity_status": "UNKNOWN",
            "completeness_status": "UNKNOWN",
            "availability_status": "AVAILABLE",
            "lineage_confidence": "MEDIUM",
            "valid_recoverable": False,
            "supersession_status": "CURRENT_CANDIDATE",
            "failure_state": "NONE",
            "rejection_reasons": [],
        },
        "newest_valid_recoverable_artifact": {
            "artifact_identity": {"artifact_id": "auth"},
            "filename": "auth.zip",
            "object_key": "backups/auto-90d/auth.zip",
            "authoritative_time": datetime.now(timezone.utc).isoformat(),
            "observed_time": datetime.now(timezone.utc).isoformat(),
            "authoritative_time_source": "VERIFIED_LOGICAL_RECOVERY_POINT",
            "freshness_age_minutes": 12.0,
            "integrity_status": "PASS",
            "completeness_status": "COMPLETE",
            "availability_status": "AVAILABLE",
            "lineage_confidence": "HIGH",
            "valid_recoverable": True,
            "supersession_status": "AUTHORITATIVE_VALID_RECOVERABLE",
            "failure_state": "NONE",
            "rejection_reasons": [],
        },
        "rejected_candidates": [],
    }


def test_public_archive_lineage_payload_exposes_required_fields():
    payload = public_archive_lineage_payload(_lineage_payload())
    required = {
        "truth_subject",
        "resolver_version",
        "authoritative_recovery_point_time",
        "authoritative_time_source",
        "freshness_age_minutes",
        "lineage_confidence",
        "integrity_status",
        "completeness_status",
        "newest_observed_artifact",
        "newest_valid_recoverable_artifact",
    }
    assert required.issubset(payload.keys())


class _FakeCursor:
    def __init__(self, docs):
        self.docs = docs

    async def to_list(self, length=None):
        return self.docs[:length] if length else self.docs


class _FakeCollection:
    def __init__(self, one=None, many=None):
        self.one = one
        self.many = many or []

    async def find_one(self, *args, **kwargs):
        return self.one

    def find(self, *args, **kwargs):
        return _FakeCursor(self.many)


class _FakeDB:
    def __init__(self):
        self.backup_health = _FakeCollection(one={"mode": "complete-r2", "ok": True, "ts": datetime.now(timezone.utc).isoformat()})
        self.drill_runs = _FakeCollection(one=None)
        self.scheduler_locks = _FakeCollection(one=None)


def test_recovery_snapshot_includes_archive_lineage(monkeypatch):
    fake_db = _FakeDB()
    router = build_recovery_dashboard_router(fake_db, lambda: True)
    endpoint = next(route.endpoint for route in router.routes if getattr(route, "path", "") == "/admin/recovery/snapshot")

    async def _fake_build_lineage(*args, **kwargs):
        payload = _lineage_payload()
        payload["authoritative_artifact"] = payload["newest_valid_recoverable_artifact"]
        payload["newest_observed_artifact"]["filename"] = "obs.zip"
        return payload

    monkeypatch.setattr("routes.recovery_dashboard.build_canonical_archive_lineage", _fake_build_lineage)

    import routes.recovery_dashboard as rd

    async def _fake_collect_backup_runtime_state(db):
        return {"overlap": {"overlap_blocked": False}}

    monkeypatch.setattr(rd, "_disk_preflight_summary", lambda: {"ok": True})
    monkeypatch.setitem(__import__("os").environ, "BACKUP_AGE_TARGET_HOURS", "24")

    async def _fake_hourly_activation(*args, **kwargs):
        return {"hourly_cadence_enabled": False, "activation_status": "DISABLED BY CONFIGURATION", "environment": "preview"}

    monkeypatch.setattr("server._build_hourly_activation_state", _fake_hourly_activation)
    monkeypatch.setattr("server._collect_backup_runtime_state", _fake_collect_backup_runtime_state)
    monkeypatch.setattr("server._BACKUP_SCHEDULER_STATE", {})

    snapshot = asyncio.run(endpoint(True))
    assert "archive_lineage" in snapshot
    assert snapshot["archive_lineage"]["authoritative_time_source"] == "VERIFIED_LOGICAL_RECOVERY_POINT"
    assert snapshot["last_backup"]["source"] == "canonical_archive_lineage"
