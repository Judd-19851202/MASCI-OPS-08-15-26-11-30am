from __future__ import annotations

import asyncio
import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


RESOLVER_VERSION = "bcss-r02-1"
TRUTH_SUBJECT = "bcss_backup_archive_lineage"
PUBLIC_HEALTH_THRESHOLD_HOURS = 26.0
DEFAULT_POSTURE_TARGET_HOURS = 24.0
DEFAULT_VERIFICATION_MAX_AGE_HOURS = 36.0
MAX_RECENT_CANDIDATES = 6
_CACHE: Dict[str, Any] = {"ts": 0.0, "payload": None}
_CACHE_TTL_SECONDS = 15.0


def parse_dt(raw: Any) -> Optional[datetime]:
    if isinstance(raw, datetime):
        return raw if raw.tzinfo else raw.replace(tzinfo=timezone.utc)
    if isinstance(raw, str) and raw:
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except Exception:
            return None
    return None


def iso_or_none(raw: Any) -> Optional[str]:
    dt = parse_dt(raw)
    return dt.isoformat() if dt else None


def minutes_since(raw: Any, *, now: Optional[datetime] = None) -> Optional[float]:
    dt = parse_dt(raw)
    if not dt:
        return None
    current = now or datetime.now(timezone.utc)
    return round((current - dt).total_seconds() / 60.0, 2)


def hours_since(raw: Any, *, now: Optional[datetime] = None) -> Optional[float]:
    mins = minutes_since(raw, now=now)
    return round(mins / 60.0, 2) if mins is not None else None


def _env_float(name: str, default: float) -> float:
    raw = (os.environ.get(name) or "").strip()
    try:
        return float(raw)
    except (TypeError, ValueError):
        return float(default)


def threshold_inventory() -> Dict[str, Any]:
    return {
        "public_health_recent_hours": {
            "value": PUBLIC_HEALTH_THRESHOLD_HOURS,
            "source": "legacy_public_health_contract",
            "authority": "GOVERNANCE APPROVAL PENDING",
        },
        "posture_target_hours": {
            "value": _env_float("BACKUP_AGE_TARGET_HOURS", DEFAULT_POSTURE_TARGET_HOURS),
            "source": "env:BACKUP_AGE_TARGET_HOURS",
            "authority": "existing_runtime_configuration",
        },
        "verification_max_age_hours": {
            "value": _env_float("BACKUP_VERIFICATION_MAX_AGE_HOURS", DEFAULT_VERIFICATION_MAX_AGE_HOURS),
            "source": "env:BACKUP_VERIFICATION_MAX_AGE_HOURS",
            "authority": "existing_runtime_configuration",
        },
    }


def _safe_json_dict(raw: Any) -> Dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str) or not raw:
        return {}
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def _row_lineage(row: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    payload = _safe_json_dict((row or {}).get("error"))
    lineage = payload.get("lineage") if isinstance(payload.get("lineage"), dict) else {}
    return lineage if isinstance(lineage, dict) else {}


def _runtime_identity(current_env: Optional[str], current_db: Optional[str]) -> Dict[str, str]:
    return {
        "app_env": str(current_env or os.environ.get("APP_ENV") or "").lower() or "unknown",
        "db_name": str(current_db or os.environ.get("DB_NAME") or "").strip() or "unknown",
    }


def _manifest_identity(manifest: Dict[str, Any]) -> Dict[str, str]:
    return {
        "app_env": str(manifest.get("app_env") or manifest.get("environment") or "").lower(),
        "db_name": str(manifest.get("db_name") or manifest.get("database_name") or "").strip(),
    }


def _candidate_key(archive: Optional[Dict[str, Any]], row: Optional[Dict[str, Any]]) -> str:
    archive_key = str((archive or {}).get("key") or "").strip()
    if archive_key:
        return archive_key
    filename = str((archive or {}).get("filename") or (row or {}).get("filename") or "").strip()
    return filename or f"candidate:{time.time()}"


def _derive_integrity(manifest: Dict[str, Any], archive: Optional[Dict[str, Any]], row_lineage: Dict[str, Any]) -> Tuple[str, List[str], bool]:
    reasons: List[str] = []
    integrity_result = str(manifest.get("integrity_result") or "").upper()
    if integrity_result == "PASS":
        return "PASS", reasons, True
    if integrity_result == "FAIL":
        reasons.append("manifest_integrity_failed")
        return "FAIL", reasons, False

    checksum = row_lineage.get("checksum_sha256") or (archive or {}).get("etag")
    if checksum:
        reasons.append("integrity_evidence_unverified")
        return "UNVERIFIED", reasons, False

    reasons.append("integrity_evidence_absent")
    return "UNKNOWN", reasons, False


def _derive_completeness(manifest: Dict[str, Any], row: Optional[Dict[str, Any]]) -> Tuple[str, List[str], bool]:
    reasons: List[str] = []
    if manifest:
        coverage_complete = manifest.get("coverage_complete")
        classification = str(manifest.get("classification") or "").upper()
        if coverage_complete is True and classification in {"", "COMPLETE"}:
            return "COMPLETE", reasons, True
        if coverage_complete is False or classification in {"BACKUP_INCOMPLETE", "FAIL", "PARTIAL"}:
            reasons.append("manifest_reports_incomplete_coverage")
            return "PARTIAL", reasons, False
        reasons.append("manifest_completeness_unknown")
        return "UNKNOWN", reasons, False

    if row and row.get("ok") is True and str(row.get("mode") or "").lower() == "complete-r2":
        reasons.append("legacy_lineage_without_manifest")
        return "LEGACY — LINEAGE INCOMPLETE", reasons, True

    reasons.append("completeness_unproven")
    return "UNKNOWN", reasons, False


def _derive_availability(archive: Optional[Dict[str, Any]], row: Optional[Dict[str, Any]]) -> Tuple[str, List[str], bool]:
    reasons: List[str] = []
    if archive and archive.get("key"):
        return "AVAILABLE", reasons, True
    if row and row.get("filename"):
        reasons.append("durable_artifact_not_observed")
        return "UNAVAILABLE", reasons, False
    reasons.append("artifact_absent")
    return "ABSENT", reasons, False


def _derive_failure_state(row: Optional[Dict[str, Any]], manifest: Dict[str, Any]) -> Tuple[str, Optional[str]]:
    if row and row.get("ok") is False:
        return "FAILED", str(row.get("error") or "backup_health_failure")[:240]
    if str(manifest.get("integrity_result") or "").upper() == "FAIL":
        return "CORRUPT", "manifest_integrity_failed"
    if manifest and manifest.get("classification") and str(manifest.get("classification")).upper() != "COMPLETE":
        return "PARTIAL", str(manifest.get("classification"))
    return "NONE", None


def _pick_authoritative_time(
    *,
    logical_recovery_point_time: Optional[str],
    completed_archive_time: Optional[str],
    durable_storage_completion_time: Optional[str],
    estimated_recovery_point_time: Optional[str],
    availability_ok: bool,
    integrity_ok: bool,
    integrity_evidence_present: bool,
    completeness_ok: bool,
    allow_estimation: bool,
) -> Tuple[Optional[str], str, List[str]]:
    reasons: List[str] = []
    if availability_ok and integrity_ok and completeness_ok and logical_recovery_point_time:
        return logical_recovery_point_time, "VERIFIED_LOGICAL_RECOVERY_POINT", reasons
    if availability_ok and integrity_ok and completeness_ok and completed_archive_time:
        return completed_archive_time, "COMPLETED_ARCHIVE_TIME", reasons
    if availability_ok and (integrity_ok or integrity_evidence_present) and durable_storage_completion_time:
        reasons.append("fallback_to_provider_completion_time")
        return durable_storage_completion_time, "PROVIDER_DURABLE_COMPLETION_TIME", reasons
    if allow_estimation and estimated_recovery_point_time:
        reasons.append("fallback_to_estimated_recovery_point")
        return estimated_recovery_point_time, "ESTIMATED_RECOVERY_POINT", reasons
    reasons.append("no_constitutionally_acceptable_timestamp")
    return None, "UNKNOWN", reasons


def _lineage_confidence(
    manifest: Dict[str, Any],
    row_lineage: Dict[str, Any],
    time_source: str,
    env_match: bool,
) -> str:
    if manifest and env_match and time_source in {"VERIFIED_LOGICAL_RECOVERY_POINT", "COMPLETED_ARCHIVE_TIME"}:
        return "HIGH"
    if manifest or row_lineage.get("checksum_sha256") or row_lineage.get("archive_key"):
        return "MEDIUM"
    return "LOW"


def _build_candidate(
    *,
    archive: Optional[Dict[str, Any]],
    row: Optional[Dict[str, Any]],
    manifest_bundle: Optional[Dict[str, Any]],
    runtime_identity: Dict[str, str],
    now: datetime,
) -> Dict[str, Any]:
    manifest = manifest_bundle.get("manifest") if isinstance(manifest_bundle, dict) else {}
    manifest = manifest if isinstance(manifest, dict) else {}
    row = row or {}
    row_lineage = _row_lineage(row)
    manifest_identity = _manifest_identity(manifest)
    env_match = not (manifest_identity["app_env"] or manifest_identity["db_name"]) or manifest_identity == runtime_identity
    reasons: List[str] = []

    availability_status, availability_reasons, availability_ok = _derive_availability(archive, row)
    completeness_status, completeness_reasons, completeness_ok = _derive_completeness(manifest, row)
    integrity_status, integrity_reasons, integrity_ok = _derive_integrity(manifest, archive, row_lineage)
    failure_state, failure_reason = _derive_failure_state(row, manifest)

    reasons.extend(availability_reasons)
    reasons.extend(completeness_reasons)
    reasons.extend(integrity_reasons)
    if not env_match:
        reasons.append("environment_identity_mismatch")
    if failure_reason:
        reasons.append(str(failure_reason))

    logical_recovery_point_time = iso_or_none(
        manifest.get("logical_recovery_point_time")
        or manifest.get("recovery_point_time")
        or row_lineage.get("logical_recovery_point_time")
    )
    completed_archive_time = iso_or_none(
        manifest.get("backup_completed_at")
        or manifest.get("completed_at")
    )
    durable_storage_completion_time = iso_or_none(
        (archive or {}).get("last_modified_iso")
        or row_lineage.get("uploaded_at")
    )
    estimated_recovery_point_time = iso_or_none(
        row.get("ts")
        or manifest.get("generated_at")
        or row_lineage.get("created_at")
    )

    authoritative_time, evidence_quality, precedence_reasons = _pick_authoritative_time(
        logical_recovery_point_time=logical_recovery_point_time,
        completed_archive_time=completed_archive_time,
        durable_storage_completion_time=durable_storage_completion_time,
        estimated_recovery_point_time=estimated_recovery_point_time,
        availability_ok=availability_ok,
        integrity_ok=integrity_ok,
        integrity_evidence_present=integrity_status in {"PASS", "UNVERIFIED"},
        completeness_ok=completeness_ok,
        allow_estimation=False,
    )
    reasons.extend(precedence_reasons)

    observed_time = iso_or_none(
        durable_storage_completion_time
        or completed_archive_time
        or logical_recovery_point_time
        or estimated_recovery_point_time
    )

    can_treat_legacy_complete = (
        completeness_status.startswith("LEGACY")
        and availability_ok
        and evidence_quality == "PROVIDER_DURABLE_COMPLETION_TIME"
    )
    valid_recoverable = bool(
        availability_ok
        and env_match
        and (integrity_ok or can_treat_legacy_complete)
        and evidence_quality != "UNKNOWN"
        and failure_state not in {"FAILED", "CORRUPT", "PARTIAL"}
        and (completeness_ok or can_treat_legacy_complete)
    )

    confidence = _lineage_confidence(manifest, row_lineage, evidence_quality, env_match)
    artifact_key = _candidate_key(archive, row)
    filename = (archive or {}).get("filename") or row.get("filename")
    archive_key = (archive or {}).get("key") or row_lineage.get("archive_key") or (f"backups/auto-90d/{filename}" if filename else None)
    created_by = row_lineage.get("job_id") or manifest.get("backup_id") or filename or artifact_key
    selected_dt = parse_dt(authoritative_time)
    observed_dt = parse_dt(observed_time)

    return {
        "artifact_key": artifact_key,
        "artifact_identity": {
            "artifact_id": manifest.get("backup_id") or row.get("archive_identifier") or filename or artifact_key,
            "truth_subject": TRUTH_SUBJECT,
            "source_subsystem": "complete-r2",
            "source_record_id": created_by,
            "archive_type": manifest.get("backup_type") or row.get("mode") or "complete-r2",
            "capture_method": row_lineage.get("trigger") or "scheduler_or_operator",
            "storage_destination": archive_key,
            "originating_environment": manifest_identity["app_env"] or runtime_identity["app_env"],
            "database_name": manifest_identity["db_name"] or runtime_identity["db_name"],
        },
        "filename": filename,
        "archive_size_bytes": (archive or {}).get("size_bytes") or row.get("size_bytes") or 0,
        "records": row.get("records") or 0,
        "object_key": archive_key,
        "source_truth": manifest.get("source") or row_lineage.get("release_sha") or "masci-ops",
        "source_system": "server._run_complete_archive_to_r2",
        "creation_initiated_at": iso_or_none(manifest.get("backup_started_at") or row_lineage.get("created_at")),
        "completed_at": completed_archive_time,
        "logical_recovery_point_time": logical_recovery_point_time,
        "provider_completed_at": durable_storage_completion_time,
        "estimated_recovery_point_time": estimated_recovery_point_time,
        "verification_time": iso_or_none(manifest.get("verification_timestamp")),
        "parent_lineage": None,
        "predecessor_lineage": None,
        "generation": None,
        "manifest_identity": {
            "manifest_name": (manifest_bundle or {}).get("manifest_name"),
            "manifest_version": manifest.get("manifest_version") or manifest.get("version"),
        },
        "integrity_status": integrity_status,
        "completeness_status": completeness_status,
        "retention_status": "UNKNOWN",
        "availability_status": availability_status,
        "supersession_status": "CURRENT_CANDIDATE",
        "failure_state": failure_state,
        "failure_reason": failure_reason,
        "evidence_references": {
            "backup_health_row_ts": row.get("ts"),
            "archive_last_modified": (archive or {}).get("last_modified_iso"),
            "checksum_sha256": row_lineage.get("checksum_sha256") or (manifest_bundle or {}).get("checksum_sha256"),
            "etag": (archive or {}).get("etag"),
            "audit_reference": row.get("audit_reference"),
        },
        "lineage_confidence": confidence,
        "environment_match": env_match,
        "authoritative_time": authoritative_time,
        "authoritative_time_source": evidence_quality,
        "observed_time": observed_time,
        "freshness_age_minutes": minutes_since(authoritative_time, now=now),
        "observed_age_minutes": minutes_since(observed_time, now=now),
        "valid_recoverable": valid_recoverable,
        "rejection_reasons": sorted(dict.fromkeys(reasons)),
        "sort_authoritative_epoch": selected_dt.timestamp() if selected_dt else float("-inf"),
        "sort_observed_epoch": observed_dt.timestamp() if observed_dt else float("-inf"),
    }


def resolve_archive_lineage_from_inputs(
    *,
    runtime_identity: Dict[str, str],
    archive_rows: List[Dict[str, Any]],
    recent_rows: List[Dict[str, Any]],
    manifest_bundles: Dict[str, Dict[str, Any]],
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    current = now or datetime.now(timezone.utc)
    recent_by_filename: Dict[str, Dict[str, Any]] = {}
    for row in recent_rows:
        filename = str(row.get("filename") or "").strip()
        if filename and filename not in recent_by_filename:
            recent_by_filename[filename] = row

    archive_by_filename: Dict[str, Dict[str, Any]] = {}
    for archive in archive_rows:
        filename = str(archive.get("filename") or "").strip()
        if filename and filename not in archive_by_filename:
            archive_by_filename[filename] = archive

    candidate_names = []
    seen = set()
    for name in list(archive_by_filename.keys()) + list(recent_by_filename.keys()):
        if name and name not in seen:
            candidate_names.append(name)
            seen.add(name)

    candidates: List[Dict[str, Any]] = []
    for name in candidate_names[:MAX_RECENT_CANDIDATES]:
        archive = archive_by_filename.get(name)
        row = recent_by_filename.get(name)
        manifest_bundle = manifest_bundles.get(name)
        candidates.append(
            _build_candidate(
                archive=archive,
                row=row,
                manifest_bundle=manifest_bundle,
                runtime_identity=runtime_identity,
                now=current,
            )
        )

    candidates.sort(key=lambda item: item.get("sort_observed_epoch") or float("-inf"), reverse=True)
    for index, candidate in enumerate(candidates, start=1):
        candidate["generation"] = index

    valid_candidates = [candidate for candidate in candidates if candidate.get("valid_recoverable") and candidate.get("authoritative_time")]
    valid_candidates.sort(key=lambda item: item.get("sort_authoritative_epoch") or float("-inf"), reverse=True)

    newest_observed = candidates[0] if candidates else None
    newest_valid = valid_candidates[0] if valid_candidates else None

    if newest_valid:
        valid_index = valid_candidates.index(newest_valid)
        predecessor = valid_candidates[valid_index + 1] if valid_index + 1 < len(valid_candidates) else None
        newest_valid["predecessor_lineage"] = (predecessor or {}).get("artifact_identity", {}).get("artifact_id") if predecessor else None
    if newest_observed and newest_valid and newest_observed.get("artifact_key") != newest_valid.get("artifact_key"):
        newest_observed["supersession_status"] = "REJECTED_NEWER_THAN_AUTHORITATIVE"
        newest_valid["supersession_status"] = "AUTHORITATIVE_VALID_RECOVERABLE"
    elif newest_valid:
        newest_valid["supersession_status"] = "AUTHORITATIVE_VALID_RECOVERABLE"

    freshness_minutes = newest_valid.get("freshness_age_minutes") if newest_valid else None
    freshness_hours = round(freshness_minutes / 60.0, 2) if freshness_minutes is not None else None
    degradation_reasons: List[str] = []
    if not newest_valid:
        degradation_reasons.append("authoritative_recoverable_artifact_absent")
    if newest_observed and newest_valid and newest_observed.get("artifact_key") != newest_valid.get("artifact_key"):
        degradation_reasons.append("newer_invalid_artifact_rejected")
    if newest_valid and newest_valid.get("authoritative_time_source") in {"PROVIDER_DURABLE_COMPLETION_TIME", "ESTIMATED_RECOVERY_POINT"}:
        degradation_reasons.append("fallback_timestamp_in_use")
    if newest_valid and newest_valid.get("lineage_confidence") != "HIGH":
        degradation_reasons.append("lineage_confidence_not_high")

    return {
        "truth_subject": TRUTH_SUBJECT,
        "resolver_version": RESOLVER_VERSION,
        "evaluated_at": current.isoformat(),
        "freshness_definition": (
            "Elapsed time between evaluation time and the logical recovery point of the newest "
            "constitutionally valid, complete, available, and integrity-acceptable archive artifact."
        ),
        "timestamp_precedence": [
            "VERIFIED_LOGICAL_RECOVERY_POINT",
            "COMPLETED_ARCHIVE_TIME",
            "PROVIDER_DURABLE_COMPLETION_TIME",
            "ESTIMATED_RECOVERY_POINT",
            "UNKNOWN",
        ],
        "runtime_identity": runtime_identity,
        "thresholds": threshold_inventory(),
        "newest_observed_artifact": newest_observed,
        "newest_valid_recoverable_artifact": newest_valid,
        "authoritative_artifact": newest_valid,
        "authoritative_recovery_point_time": (newest_valid or {}).get("authoritative_time"),
        "authoritative_time_source": (newest_valid or {}).get("authoritative_time_source") or "UNKNOWN",
        "freshness_age_minutes": freshness_minutes,
        "freshness_age_hours": freshness_hours,
        "evidence_quality": (newest_valid or {}).get("authoritative_time_source") or "UNKNOWN",
        "lineage_confidence": (newest_valid or {}).get("lineage_confidence") or "LOW",
        "integrity_status": (newest_valid or {}).get("integrity_status") or "UNKNOWN",
        "completeness_status": (newest_valid or {}).get("completeness_status") or "UNKNOWN",
        "availability_status": (newest_valid or {}).get("availability_status") or ((newest_observed or {}).get("availability_status") or "ABSENT"),
        "degradation_reasons": sorted(dict.fromkeys(degradation_reasons)),
        "rejected_candidates": [candidate for candidate in candidates if not candidate.get("valid_recoverable")][:5],
        "all_candidates": candidates[:MAX_RECENT_CANDIDATES],
    }


async def build_canonical_archive_lineage(
    db: Any,
    *,
    current_env: Optional[str] = None,
    current_db: Optional[str] = None,
    force_refresh: bool = False,
) -> Dict[str, Any]:
    now_mono = time.time()
    if not force_refresh and _CACHE.get("payload") is not None and (now_mono - float(_CACHE.get("ts") or 0.0)) < _CACHE_TTL_SECONDS:
        return dict(_CACHE["payload"])

    from backup_verification import list_r2_backup_archives, read_r2_backup_manifest  # noqa: PLC0415

    runtime = _runtime_identity(current_env=current_env, current_db=current_db)
    archives = await list_r2_backup_archives(prefix="backups/auto-90d/")
    archive_rows = archives[:MAX_RECENT_CANDIDATES]
    if hasattr(db.backup_health, "find"):
        recent_rows = await db.backup_health.find(
            {"mode": "complete-r2", "filename": {"$nin": [None, ""]}},
            {"_id": 0, "ts": 1, "ok": 1, "mode": 1, "filename": 1, "size_bytes": 1, "records": 1, "error": 1, "archive_identifier": 1, "audit_reference": 1},
            sort=[("ts", -1)],
        ).to_list(length=MAX_RECENT_CANDIDATES)
    else:
        single = await db.backup_health.find_one(
            {"mode": "complete-r2", "filename": {"$nin": [None, ""]}},
            {"_id": 0, "ts": 1, "ok": 1, "mode": 1, "filename": 1, "size_bytes": 1, "records": 1, "error": 1, "archive_identifier": 1, "audit_reference": 1},
            sort=[("ts", -1)],
        )
        recent_rows = [single] if single else []

    manifest_bundles: Dict[str, Dict[str, Any]] = {}
    manifest_tasks = []
    manifest_names = []
    for archive in archive_rows:
        key = archive.get("key")
        filename = archive.get("filename")
        if not key or not filename:
            continue
        manifest_tasks.append(read_r2_backup_manifest(key))
        manifest_names.append(filename)

    if manifest_tasks:
        for filename, bundle in zip(manifest_names, await asyncio.gather(*manifest_tasks, return_exceptions=True)):
            if isinstance(bundle, dict):
                manifest_bundles[filename] = bundle

    payload = resolve_archive_lineage_from_inputs(
        runtime_identity=runtime,
        archive_rows=archive_rows,
        recent_rows=recent_rows,
        manifest_bundles=manifest_bundles,
    )
    _CACHE.update({"ts": now_mono, "payload": payload})
    return dict(payload)


def consumer_freshness_status(
    lineage: Dict[str, Any],
    *,
    threshold_minutes: float,
    warning_minutes: Optional[float] = None,
) -> Dict[str, Any]:
    age = lineage.get("freshness_age_minutes")
    if age is None:
        return {
            "status": "UNKNOWN",
            "ok": False,
            "reason": "authoritative_recovery_point_unknown",
            "threshold_minutes": threshold_minutes,
        }

    warn_at = float(warning_minutes if warning_minutes is not None else threshold_minutes)
    stale_at = float(threshold_minutes)
    if age > stale_at:
        return {"status": "STALE", "ok": False, "reason": "freshness_threshold_exceeded", "threshold_minutes": stale_at}
    if age > warn_at:
        return {"status": "AGING", "ok": True, "reason": "freshness_warning_threshold_exceeded", "threshold_minutes": stale_at}
    return {"status": "CURRENT", "ok": True, "reason": "within_threshold", "threshold_minutes": stale_at}


def backup_recent_truth(lineage: Dict[str, Any], *, threshold_hours: float = PUBLIC_HEALTH_THRESHOLD_HOURS) -> Dict[str, Any]:
    freshness = consumer_freshness_status(lineage, threshold_minutes=threshold_hours * 60.0)
    selected = lineage.get("authoritative_artifact") or {}
    newest_observed = lineage.get("newest_observed_artifact") or {}
    return {
        "ok": bool(freshness.get("ok") and freshness.get("status") == "CURRENT"),
        "signal_source": f"canonical_archive_lineage:{lineage.get('authoritative_time_source') or 'UNKNOWN'}",
        "evidence_ts": lineage.get("authoritative_recovery_point_time") or newest_observed.get("observed_time"),
        "age_s": round(float(lineage.get("freshness_age_minutes") or 0.0) * 60.0, 2) if lineage.get("freshness_age_minutes") is not None else None,
        "filename": selected.get("filename") or newest_observed.get("filename"),
        "status": freshness.get("status"),
        "reason": freshness.get("reason"),
        "degradation_reasons": lineage.get("degradation_reasons") or [],
    }


def summarize_artifact(candidate: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not candidate:
        return None
    return {
        "artifact_id": (candidate.get("artifact_identity") or {}).get("artifact_id"),
        "filename": candidate.get("filename"),
        "object_key": candidate.get("object_key"),
        "authoritative_time": candidate.get("authoritative_time"),
        "observed_time": candidate.get("observed_time"),
        "authoritative_time_source": candidate.get("authoritative_time_source"),
        "freshness_age_minutes": candidate.get("freshness_age_minutes"),
        "integrity_status": candidate.get("integrity_status"),
        "completeness_status": candidate.get("completeness_status"),
        "availability_status": candidate.get("availability_status"),
        "lineage_confidence": candidate.get("lineage_confidence"),
        "valid_recoverable": candidate.get("valid_recoverable"),
        "supersession_status": candidate.get("supersession_status"),
        "failure_state": candidate.get("failure_state"),
        "rejection_reasons": candidate.get("rejection_reasons") or [],
    }


def public_archive_lineage_payload(lineage: Dict[str, Any]) -> Dict[str, Any]:
    thresholds = lineage.get("thresholds") or {}
    return {
        "truth_subject": lineage.get("truth_subject"),
        "resolver_version": lineage.get("resolver_version"),
        "evaluated_at": lineage.get("evaluated_at"),
        "timestamp_precedence": lineage.get("timestamp_precedence") or [],
        "freshness_definition": lineage.get("freshness_definition"),
        "authoritative_recovery_point_time": lineage.get("authoritative_recovery_point_time"),
        "authoritative_time_source": lineage.get("authoritative_time_source"),
        "freshness_age_minutes": lineage.get("freshness_age_minutes"),
        "freshness_age_hours": lineage.get("freshness_age_hours"),
        "evidence_quality": lineage.get("evidence_quality"),
        "lineage_confidence": lineage.get("lineage_confidence"),
        "integrity_status": lineage.get("integrity_status"),
        "completeness_status": lineage.get("completeness_status"),
        "availability_status": lineage.get("availability_status"),
        "degradation_reasons": lineage.get("degradation_reasons") or [],
        "thresholds": thresholds,
        "newest_observed_artifact": summarize_artifact(lineage.get("newest_observed_artifact")),
        "newest_valid_recoverable_artifact": summarize_artifact(lineage.get("newest_valid_recoverable_artifact")),
        "rejected_candidates": [summarize_artifact(candidate) for candidate in (lineage.get("rejected_candidates") or [])],
    }


__all__ = [
    "PUBLIC_HEALTH_THRESHOLD_HOURS",
    "RESOLVER_VERSION",
    "TRUTH_SUBJECT",
    "backup_recent_truth",
    "build_canonical_archive_lineage",
    "consumer_freshness_status",
    "hours_since",
    "iso_or_none",
    "minutes_since",
    "parse_dt",
    "public_archive_lineage_payload",
    "resolve_archive_lineage_from_inputs",
    "summarize_artifact",
    "threshold_inventory",
]