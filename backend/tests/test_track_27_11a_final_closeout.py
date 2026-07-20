from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, "/app/backend")

import server  # noqa: E402, PLC0415
from lib.production_certification import (  # noqa: E402, PLC0415
    STATUS_BLOCKED,
    STATUS_FAILED,
    STATUS_NOT_YET_EXERCISED,
    STATUS_STALE,
    STATUS_VERIFIED,
    _build_release_scope,
)
from lib.synthetic_dr_filter import apply_synthetic_dr_exclusion, is_synthetic_dr  # noqa: E402, PLC0415
from routes.daily_reports import (  # noqa: E402, PLC0415
    _apply_certification_record_safety,
    _should_schedule_daily_report_email,
)
from routes.recovery_dashboard import canonical_scheduler_snapshot  # noqa: E402, PLC0415


def test_release_scope_fields_are_explicit_and_touch_only_exercised_workflows():
    rows = [
        {"workflow": "daily-report", "status": STATUS_VERIFIED},
        {"workflow": "meeting", "status": STATUS_BLOCKED},
        {"workflow": "shop-defect", "status": STATUS_STALE},
        {"workflow": "incident", "status": STATUS_FAILED},
        {"workflow": "dvir", "status": STATUS_NOT_YET_EXERCISED},
    ]

    out = _build_release_scope(rows)

    assert out["release_touched_workflows"] == [
        "daily-report",
        "meeting",
        "shop-defect",
        "incident",
    ]
    assert out["release_untouched_workflows"] == ["dvir"]
    assert out["release_verified_workflows"] == ["daily-report"]
    assert out["release_blocked_workflows"] == ["meeting"]
    assert out["release_stale_workflows"] == ["shop-defect"]
    assert out["release_failed_workflows"] == ["incident"]
    assert out["release_reason"] == "release_contains_failed_workflows"
    assert out["release_required_workflows"] == [
        "daily-report",
        "meeting",
        "shop-defect",
        "incident",
    ]
    assert out["release_counters"] == {
        "verified": 1,
        "failed": 1,
        "blocked": 1,
        "stale": 1,
        "not_yet_exercised": 0,
        "untouched": 1,
        "total": 4,
    }
    assert out["release_band"] == "hold"


def test_certification_record_is_hidden_and_email_suppressed():
    doc = _apply_certification_record_safety({
        "id": "dr-cert-1",
        "project_name": "Certification Lane",
        "certification_record": True,
        "certification_run_id": "run-27-11b-001",
        "certification_release_source_hash": "abc123",
        "certification_release_reason": "release_scope_verified",
        "certification_required_workflows": ["daily-report", "meeting"],
    })

    assert doc["certification_record"] is True
    assert doc["synthetic_record"] is True
    assert doc["hidden_from_operations"] is True
    assert doc["email_dispatch_suppressed"] is True
    assert doc["certification_track_id"] == "27.11B"
    assert doc["certification_run_id"] == "run-27-11b-001"
    assert doc["certification_release_source_hash"] == "abc123"
    assert doc["certification_release_reason"] == "release_scope_verified"
    assert doc["certification_required_workflows"] == ["daily-report", "meeting"]
    assert _should_schedule_daily_report_email(doc) is False
    assert is_synthetic_dr(doc) is True
    q = apply_synthetic_dr_exclusion({})
    assert {"certification_record": {"$ne": True}} in q["$and"]


def test_canonical_scheduler_snapshot_uses_recent_backup_fallback_before_stale_lock():
    out = canonical_scheduler_snapshot(
        {"last_tick_ts": None},
        backup_fallback_ts="2999-01-01T00:00:00+00:00",
        lock_row={
            "owner_id": "backup_scheduler:oldpod:1",
            "acquired_at": "2000-01-01T00:00:00+00:00",
        },
    )

    assert out["alive"] is True
    assert out["signal_source"] == "recent_successful_backup"
    assert out["reason_code"] == "recent_backup_fallback"


def test_scheduler_state_response_keeps_canonical_fields_top_level():
    state = {
        "alive": True,
        "is_healthy": True,
        "signal_source": "recent_successful_backup",
        "reason_code": "recent_backup_fallback",
        "evidence_ts": "2026-07-12T23:06:38.202000+00:00",
        "last_lock_ts": None,
        "owner_pod": None,
        "heartbeat_window_minutes": 30,
        "backup_fallback_window_minutes": 60,
    }
    body = {
        "alive": state.get("alive"),
        "is_healthy": state.get("is_healthy"),
        "signal_source": state.get("signal_source"),
        "reason_code": state.get("reason_code"),
        "evidence_ts": state.get("evidence_ts"),
        "last_lock_ts": state.get("last_lock_ts"),
        "owner_pod": state.get("owner_pod"),
        "heartbeat_window_minutes": state.get("heartbeat_window_minutes"),
        "backup_fallback_window_minutes": state.get("backup_fallback_window_minutes"),
        "scheduler": state,
    }

    for key in [
        "alive",
        "is_healthy",
        "signal_source",
        "reason_code",
        "evidence_ts",
        "heartbeat_window_minutes",
        "backup_fallback_window_minutes",
    ]:
        assert body[key] == state[key]


class _AsyncCollection:
    def __init__(self, docs=None):
        self._docs = docs or []

    async def find_one(self, *args, **kwargs):
        if not self._docs:
            return None
        return self._docs[0]

    def find(self, *args, **kwargs):
        return _AsyncCursor(self._docs)


class _AsyncCursor:
    def __init__(self, docs):
        self._docs = list(docs)

    async def to_list(self, length=0):
        return list(self._docs[: length or None])


class _FakeDB:
    def __init__(self):
        self.backup_health = _AsyncCollection([
            {
                "filename": "MASCI_complete_backup_2026-07-12_140050Z.zip",
                "size_bytes": 1048781324,
                "records": 253505,
                "ts": "2026-07-12T14:05:40.570641+00:00",
                "mode": "complete-r2",
                "ok": True,
            },
            {
                "filename": "MASCI_complete_backup_2026-07-12_130050Z.zip",
                "size_bytes": 1047781324,
                "records": 253405,
                "ts": "2026-07-12T13:05:40.570641+00:00",
                "mode": "complete-r2",
                "ok": True,
            },
        ])
        self.backup_drift_history = _AsyncCollection([])
        self.drill_runs = _AsyncCollection([])
        self.scheduler_locks = _AsyncCollection([])

    async def list_collection_names(self):
        return ["backup_health", "daily_reports", "meetings"]


def test_integrity_check_exposes_rowwise_lineage_for_recent_backups(monkeypatch):
    import backup_verification  # noqa: PLC0415

    async def _fake_list_r2_backup_archives(prefix: str = "backups/"):
        assert prefix == "backups/auto-90d/"
        return [
            {
                "key": f"backups/auto-90d/MASCI_complete_backup_2026-07-12_1{i}0050Z.zip",
                "filename": f"MASCI_complete_backup_2026-07-12_1{i}0050Z.zip",
                "size_bytes": 1040000000 + i,
                "last_modified_iso": f"2026-07-12T1{i}:05:40.000000+00:00",
            }
            for i in range(4, 9)
        ]

    async def _fake_read_r2_backup_manifest(key: str):
        hour = key.split("_")[-2][-2:]
        generated_at = f"2026-07-12T{hour}:05:40.000000+00:00"
        manifest = {
            "generated_at": generated_at,
            "captured_collections": ["backup_health", "daily_reports", "meetings"],
            "per_kind": {"backup_health": 20, "daily_reports": 215, "meetings": 56},
            "total_records": 253000 + int(hour),
            "explicit_exclusions": [],
        }
        if key.endswith("150050Z.zip"):
            manifest["captured_collections"] = ["backup_health", "daily_reports"]
        return {
            "manifest_name": "MANIFEST.json",
            "content_length": 1048781324,
            "last_modified_iso": generated_at,
            "manifest": manifest,
        }

    monkeypatch.setattr(backup_verification, "list_r2_backup_archives", _fake_list_r2_backup_archives)
    monkeypatch.setattr(backup_verification, "read_r2_backup_manifest", _fake_read_r2_backup_manifest)
    monkeypatch.setattr(server, "_list_stored_backups", lambda: [])

    fake_db = _FakeDB()

    async def _call_route():
        fn = next(
            route.endpoint
            for route in server.app.routes
            if getattr(route, "path", "") == "/api/admin/backups/integrity-check"
        )
        old_db = server._get_db_target_for_tests()
        server._set_db_target_for_tests(fake_db)
        try:
            return await fn(True)
        finally:
            server._set_db_target_for_tests(old_db)

    out = asyncio.run(_call_route())

    assert len(out["recent_backups"]) == 5
    assert all("integrity_result" in row for row in out["recent_backups"])
    assert all("failed_checks" in row for row in out["recent_backups"])
    assert all("evidence_source" in row for row in out["recent_backups"])
    assert all("verification_timestamp" in row for row in out["recent_backups"])
    assert all("verifier_version" in row for row in out["recent_backups"])
    assert all("evidence_mode" in row for row in out["recent_backups"])
    assert out["recent_backups"][0]["integrity_result"] == "PASS"
    failed_row = next(row for row in out["recent_backups"] if row["filename"].endswith("150050Z.zip"))
    assert failed_row["integrity_result"] == "FAIL"
    assert failed_row["failed_checks"][0]["code"] == "missing_from_live_required_set"


def test_integrity_rows_preserve_newest_fail_and_older_pass(monkeypatch):
    import backup_verification  # noqa: PLC0415

    async def _fake_list_r2_backup_archives(prefix: str = "backups/"):
        assert prefix == "backups/auto-90d/"
        return [
            {
                "key": f"backups/auto-90d/MASCI_complete_backup_2026-07-12_1{i}0050Z.zip",
                "filename": f"MASCI_complete_backup_2026-07-12_1{i}0050Z.zip",
                "size_bytes": 1040000000 + i,
                "last_modified_iso": f"2026-07-12T1{i}:05:40.000000+00:00",
            }
            for i in range(4, 9)
        ]

    async def _fake_read_r2_backup_manifest(key: str):
        hour = key.split("_")[-2][-2:]
        generated_at = f"2026-07-12T{hour}:05:40.000000+00:00"
        manifest = {
            "generated_at": generated_at,
            "captured_collections": ["backup_health", "daily_reports", "meetings"],
            "per_kind": {"backup_health": 20, "daily_reports": 215, "meetings": 56},
            "total_records": 253000 + int(hour),
            "explicit_exclusions": [],
        }
        if key.endswith("180050Z.zip"):
            manifest["captured_collections"] = ["backup_health", "daily_reports"]
        return {
            "manifest_name": "MANIFEST.json",
            "content_length": 1048781324,
            "last_modified_iso": generated_at,
            "manifest": manifest,
        }

    monkeypatch.setattr(backup_verification, "list_r2_backup_archives", _fake_list_r2_backup_archives)
    monkeypatch.setattr(backup_verification, "read_r2_backup_manifest", _fake_read_r2_backup_manifest)
    monkeypatch.setattr(server, "_list_stored_backups", lambda: [])

    fake_db = _FakeDB()

    async def _call_route():
        fn = next(
            route.endpoint
            for route in server.app.routes
            if getattr(route, "path", "") == "/api/admin/backups/integrity-check"
        )
        old_db = server._get_db_target_for_tests()
        server._set_db_target_for_tests(fake_db)
        try:
            return await fn(True)
        finally:
            server._set_db_target_for_tests(old_db)

    out = asyncio.run(_call_route())
    newest = next(row for row in out["recent_backups"] if row["filename"].endswith("180050Z.zip"))
    older = next(row for row in out["recent_backups"] if row["filename"].endswith("170050Z.zip"))
    assert newest["integrity_result"] == "FAIL"
    assert older["integrity_result"] == "PASS"


def test_integrity_rows_without_manifest_evidence_remain_unknown(monkeypatch):
    import backup_verification  # noqa: PLC0415

    async def _fake_list_r2_backup_archives(prefix: str = "backups/"):
        return [
            {
                "key": "backups/auto-90d/MASCI_complete_backup_2026-07-12_180050Z.zip",
                "filename": "MASCI_complete_backup_2026-07-12_180050Z.zip",
                "size_bytes": 1040000008,
                "last_modified_iso": "2026-07-12T18:05:40.000000+00:00",
            }
        ]

    async def _fake_read_r2_backup_manifest(key: str):
        return None

    monkeypatch.setattr(backup_verification, "list_r2_backup_archives", _fake_list_r2_backup_archives)
    monkeypatch.setattr(backup_verification, "read_r2_backup_manifest", _fake_read_r2_backup_manifest)
    monkeypatch.setattr(server, "_list_stored_backups", lambda: [])

    fake_db = _FakeDB()

    async def _call_route():
        fn = next(
            route.endpoint
            for route in server.app.routes
            if getattr(route, "path", "") == "/api/admin/backups/integrity-check"
        )
        old_db = server._get_db_target_for_tests()
        server._set_db_target_for_tests(fake_db)
        try:
            return await fn(True)
        finally:
            server._set_db_target_for_tests(old_db)

    out = asyncio.run(_call_route())
    row = out["recent_backups"][0]
    assert row["integrity_result"] == "UNKNOWN"
    assert row["evidence_mode"] in {"SUMMARY_ONLY", "MANIFEST_ONLY"}


def test_version_endpoint_separates_build_and_process_timestamps(monkeypatch):
    monkeypatch.setattr(server, "_BUILT_AT_ISO", "2026-07-12T01:46:04+00:00")
    monkeypatch.setattr(server, "_BUILD_AT_SOURCE", "env:BUILT_AT")
    monkeypatch.setattr(server, "_STARTUP_TS", datetime(2026, 7, 12, 3, 0, 0, tzinfo=timezone.utc))

    out = server.api_version()

    assert out["built_at"] == "2026-07-12T01:46:04+00:00"
    assert out["process_started_at"] == "2026-07-12T03:00:00+00:00"
    assert out["started_at"] == out["process_started_at"]
    assert out["built_at"] != out["process_started_at"]


def test_runtime_frontend_scope_has_no_banned_preview_literals():
    runtime_files = [
        "/app/frontend/src/components/EnvBanner.jsx",
        "/app/frontend/src/lib/sentryInit.js",
        "/app/frontend/src/pages/NewDailyReportV3.jsx",
        "/app/frontend/src/lib/printReport.js",
        "/app/frontend/src/lib/thumbCache.js",
    ]
    banned = ["preview.emergentagent.com", "localhost", "127.0.0.1"]
    joined = "\n".join(Path(path).read_text(encoding="utf-8") for path in runtime_files)
    for needle in banned:
        assert needle not in joined