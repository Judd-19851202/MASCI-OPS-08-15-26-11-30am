from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace

from lib.archive_lineage import public_archive_lineage_payload
from backup_verification import render_verification_email_html
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


def _email_report(*, authoritative=True, observed=True, partial=False, corrupt=False, unknown=False):
    lineage = _lineage_payload()
    if unknown:
        lineage.update({
            "authoritative_recovery_point_time": None,
            "authoritative_time_source": "UNKNOWN",
            "freshness_age_hours": None,
            "lineage_confidence": "LOW",
            "integrity_status": "UNKNOWN",
            "completeness_status": "UNKNOWN",
            "availability_status": "AVAILABLE" if observed else "ABSENT",
            "degradation_reasons": ["authoritative_recoverable_artifact_absent"],
            "newest_valid_recoverable_artifact": None,
        })
    if partial:
        lineage.update({
            "authoritative_recovery_point_time": None,
            "authoritative_time_source": "UNKNOWN",
            "integrity_status": "UNKNOWN",
            "completeness_status": "PARTIAL",
            "degradation_reasons": ["authoritative_recoverable_artifact_absent"],
            "newest_valid_recoverable_artifact": None,
        })
    if corrupt:
        lineage.update({
            "authoritative_recovery_point_time": None,
            "authoritative_time_source": "UNKNOWN",
            "integrity_status": "FAIL",
            "completeness_status": "PARTIAL",
            "degradation_reasons": ["newer_invalid_artifact_rejected"],
            "newest_valid_recoverable_artifact": None,
        })
    if not observed:
        lineage["newest_observed_artifact"] = None
        lineage["availability_status"] = "ABSENT"
    if not authoritative:
        lineage["newest_valid_recoverable_artifact"] = None

    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "verdict": "warn",
        "r2": {
            "archive_count": 2 if observed else 0,
            "total_size_human": "2 GB",
            "all_archives": [
                {"key": "backups/auto-90d/obs.zip", "size_bytes": 1000, "last_modified_iso": datetime.now(timezone.utc).isoformat()}
            ] if observed else [],
            "all_archives_truncated": False,
            "newest": {"key": "backups/auto-90d/obs.zip", "filename": "obs.zip", "last_modified_iso": datetime.now(timezone.utc).isoformat()} if observed else None,
            "newest_age_hrs": 0.1 if observed else None,
            "authoritative_artifact": lineage.get("newest_valid_recoverable_artifact"),
            "archive_lineage": lineage,
            "issues": [],
        },
        "ledger": {"last_full": {}, "last_r2": {}, "last_failure": {}, "issues": []},
        "data": {"per_collection_counts": {}, "total_records": 0},
        "archive_lineage": lineage,
    }


def test_email_uses_authoritative_recoverable_point_not_newest_object_age():
    html = render_verification_email_html(_email_report())
    assert "Authoritative Recoverable Point" in html
    assert "Newest Observed Archive Object (Secondary Diagnostic Evidence Only)" in html
    assert "authoritative recoverable point" in html.lower()


def test_email_does_not_label_newest_age_as_authoritative():
    html = render_verification_email_html(_email_report())
    assert "· newest:" not in html


def test_email_reports_no_authoritative_recoverable_point_when_only_observed_exists():
    html = render_verification_email_html(_email_report(authoritative=False, observed=True, unknown=True))
    assert "No authoritative recoverable point is currently proven" in html


def test_email_reports_no_archive_evidence_when_none_exists():
    html = render_verification_email_html(_email_report(authoritative=False, observed=False, unknown=True))
    assert "No archive evidence is currently available" in html


def test_email_renders_partial_lineage_truthfully():
    html = render_verification_email_html(_email_report(authoritative=False, observed=True, partial=True))
    assert "completeness=PARTIAL" in html


def test_email_renders_corrupt_or_failed_truthfully():
    html = render_verification_email_html(_email_report(authoritative=False, observed=True, corrupt=True))
    assert "integrity=FAIL" in html


def test_email_does_not_imply_restore_certification_or_deployment_readiness():
    html = render_verification_email_html(_email_report())
    assert "does not prove restore certification" in html
    assert "deployment readiness" in html
