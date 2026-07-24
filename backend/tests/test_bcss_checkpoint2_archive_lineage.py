from __future__ import annotations

from datetime import datetime, timedelta, timezone

from lib.archive_lineage import (
    backup_recent_truth,
    consumer_freshness_status,
    resolve_archive_lineage_from_inputs,
)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def _archive(filename: str, minutes_ago: int, *, size_bytes: int = 1000) -> dict:
    return {
        "filename": filename,
        "key": f"backups/auto-90d/{filename}",
        "last_modified_iso": _iso(datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)),
        "size_bytes": size_bytes,
        "etag": f"etag-{filename}",
    }


def _row(filename: str, minutes_ago: int, *, ok: bool = True, error: str | None = None) -> dict:
    lineage = {"checksum_sha256": f"sha-{filename}", "created_at": _iso(datetime.now(timezone.utc) - timedelta(minutes=minutes_ago + 2))}
    return {
        "filename": filename,
        "ts": _iso(datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)),
        "ok": ok,
        "mode": "complete-r2",
        "records": 123,
        "size_bytes": 1000,
        "error": error or {"lineage": lineage},
    }


def _manifest(minutes_ago: int, *, complete: bool = True, integrity: str = "PASS", logical: bool = True, env: str = "preview", db_name: str = "masci") -> dict:
    logical_time = _iso(datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)) if logical else None
    completed_time = _iso(datetime.now(timezone.utc) - timedelta(minutes=max(minutes_ago - 1, 0)))
    return {
        "manifest": {
            "manifest_version": "1",
            "app_env": env,
            "db_name": db_name,
            "coverage_complete": complete,
            "classification": "COMPLETE" if complete else "PARTIAL",
            "integrity_result": integrity,
            "logical_recovery_point_time": logical_time,
            "backup_completed_at": completed_time,
        },
        "manifest_name": "backup_manifest.json",
        "last_modified_iso": completed_time,
        "content_length": 1000,
        "checksum_sha256": "sha",
    }


def _resolve(archives, rows, manifests):
    return resolve_archive_lineage_from_inputs(
        runtime_identity={"app_env": "preview", "db_name": "masci"},
        archive_rows=archives,
        recent_rows=rows,
        manifest_bundles=manifests,
    )


def test_prefers_older_valid_artifact_over_newer_failed_artifact():
    good = _archive("good.zip", 120)
    bad = _archive("bad.zip", 10)
    payload = _resolve(
        [bad, good],
        [_row("bad.zip", 10, ok=False, error="failed"), _row("good.zip", 120)],
        {"bad.zip": _manifest(10, complete=False, integrity="FAIL"), "good.zip": _manifest(120)},
    )

    assert payload["authoritative_artifact"]["filename"] == "good.zip"
    assert payload["newest_observed_artifact"]["filename"] == "bad.zip"
    assert "newer_invalid_artifact_rejected" in payload["degradation_reasons"]


def test_prefers_complete_artifact_over_newer_partial_artifact():
    payload = _resolve(
        [_archive("partial.zip", 5), _archive("complete.zip", 100)],
        [_row("partial.zip", 5), _row("complete.zip", 100)],
        {"partial.zip": _manifest(5, complete=False), "complete.zip": _manifest(100)},
    )

    assert payload["authoritative_artifact"]["filename"] == "complete.zip"
    assert payload["newest_observed_artifact"]["filename"] == "partial.zip"


def test_unverified_artifact_does_not_override_verified_artifact():
    payload = _resolve(
        [_archive("new.zip", 15), _archive("old.zip", 90)],
        [_row("new.zip", 15), _row("old.zip", 90)],
        {"new.zip": _manifest(15, integrity="UNKNOWN"), "old.zip": _manifest(90, integrity="PASS")},
    )

    assert payload["authoritative_artifact"]["filename"] == "old.zip"
    assert payload["newest_observed_artifact"]["filename"] == "new.zip"


def test_multiple_valid_artifacts_selects_newest_logical_recovery_point():
    payload = _resolve(
        [_archive("new.zip", 30), _archive("old.zip", 90)],
        [_row("new.zip", 30), _row("old.zip", 90)],
        {"new.zip": _manifest(30), "old.zip": _manifest(90)},
    )

    assert payload["authoritative_artifact"]["filename"] == "new.zip"
    assert payload["freshness_age_minutes"] is not None


def test_no_artifacts_returns_unknown():
    payload = _resolve([], [], {})
    assert payload["authoritative_recovery_point_time"] is None
    assert payload["availability_status"] == "ABSENT"


def test_legacy_record_falls_back_to_provider_completion_degraded():
    payload = _resolve(
        [_archive("legacy.zip", 45)],
        [_row("legacy.zip", 45)],
        {},
    )

    assert payload["authoritative_artifact"]["authoritative_time_source"] == "PROVIDER_DURABLE_COMPLETION_TIME"
    assert payload["authoritative_artifact"]["completeness_status"] == "LEGACY — LINEAGE INCOMPLETE"


def test_threshold_boundaries_and_one_second_beyond():
    lineage = {
        "freshness_age_minutes": 60.0,
        "authoritative_recovery_point_time": _iso(datetime.now(timezone.utc) - timedelta(minutes=60)),
        "authoritative_artifact": {"filename": "a.zip"},
    }
    exact = consumer_freshness_status(lineage, threshold_minutes=60.0)
    assert exact["status"] == "CURRENT"

    lineage["freshness_age_minutes"] = 60.02
    over = consumer_freshness_status(lineage, threshold_minutes=60.0)
    assert over["status"] == "STALE"


def test_future_timestamp_is_not_stale_but_is_exposed():
    future = datetime.now(timezone.utc) + timedelta(minutes=5)
    payload = _resolve(
        [_archive("future.zip", -5)],
        [_row("future.zip", -5)],
        {"future.zip": _manifest(-5)},
    )
    assert payload["authoritative_artifact"]["freshness_age_minutes"] <= 0
    assert payload["authoritative_recovery_point_time"] is not None


def test_duplicate_archive_records_do_not_break_selection():
    archive = _archive("dup.zip", 30)
    row = _row("dup.zip", 30)
    payload = _resolve([archive, archive], [row, row], {"dup.zip": _manifest(30)})
    assert payload["authoritative_artifact"]["filename"] == "dup.zip"


def test_environment_mismatch_rejects_candidate():
    payload = _resolve(
        [_archive("wrong-env.zip", 30)],
        [_row("wrong-env.zip", 30)],
        {"wrong-env.zip": _manifest(30, env="production", db_name="other")},
    )
    assert payload["authoritative_artifact"] is None
    assert payload["newest_observed_artifact"]["environment_match"] is False


def test_backup_recent_truth_uses_canonical_authoritative_point():
    payload = _resolve(
        [_archive("fresh.zip", 20)],
        [_row("fresh.zip", 20)],
        {"fresh.zip": _manifest(20)},
    )
    truth = backup_recent_truth(payload, threshold_hours=1)
    assert truth["ok"] is True
    assert truth["signal_source"].startswith("canonical_archive_lineage")
