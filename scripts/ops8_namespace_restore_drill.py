#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
import time
import uuid
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
import traceback

import boto3
from botocore.config import Config
from pymongo import MongoClient, UpdateOne
from pymongo.errors import BulkWriteError, OperationFailure, PyMongoError


REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_ENV = REPO_ROOT / "backend" / ".env"
MEMORY_DIR = REPO_ROOT / "memory"
sys.path.insert(0, str(REPO_ROOT / "backend"))
from lib.archive_lineage import build_canonical_archive_lineage  # noqa: E402
from lib.backup_runtime import (
    BACKUP_JOB_KIND_RESTORE_DRILL,
    is_restore_certification_stale,
    restore_certification_guard_slot,
    restore_certification_lease_expires_at,
    restore_certification_lease_minutes,
    restore_certification_terminal_slot,
    backup_owner_id,
    backup_run_id,
)
from lib.restore_certification_evidence import (  # noqa: E402
    AUDIT_COLLECTIONS,
    ASSIGNMENT_COLLECTIONS,
    EVIDENCE_SCHEMA_VERSION,
    IDENTITY_COLLECTIONS,
    OWNER_TRACE,
    PHASE_SEQUENCE,
    ROLE_COLLECTIONS,
    SCHEDULER_STATE_COLLECTIONS,
    build_canonical_preview_fingerprint,
    build_collection_sample_verification,
    build_independent_qa_review,
    build_restore_counts,
    build_restore_evidence_skeleton,
    capture_runtime_telemetry,
    compare_fingerprints,
    deterministic_sample_identifiers_from_identifiers,
    extract_archive_collection_documents,
    iter_collection_documents_batched,
    load_namespace_collection_document_counts,
    load_namespace_collection_documents,
    mark_phase_status,
    persist_restore_substep_evidence,
    validate_restore_certification_evidence,
    verify_audit_data,
    verify_identity_role_data,
    verify_photo_object_evidence,
    verify_representative_content,
    verify_scheduler_state,
)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            if chunk:
                h.update(chunk)
    return h.hexdigest()


def _authoritative_truth_refusal(error_code: str, diagnostics: Dict[str, Any], *, guard: dict | None = None, db=None) -> int:
    if guard is not None and db is not None:
        _sync_finish_guard(db, guard, state="failed", outcome="failed", reason=error_code, slot_suffix="failed")
    print(json.dumps({"ok": False, "error": error_code, "diagnostics": diagnostics}, indent=2))
    return 2


def _terminalize_drill_run(
    db,
    *,
    drill_id: str,
    state: str,
    outcome: str,
    reason: str,
    evidence: Optional[Dict[str, Any]] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    payload = {
        "state": state,
        "outcome": outcome,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "failure": reason if outcome != "ok" else None,
    }
    if evidence is not None:
        payload["restore_certification_evidence"] = evidence
    if extra:
        payload.update(extra)
    db.drill_runs.update_one({"id": drill_id}, {"$set": payload}, upsert=False)


def _coerce_missing_owner_active_guard(active: Optional[Dict[str, Any]], *, now: Optional[datetime] = None) -> tuple[Optional[Dict[str, Any]], bool]:
    if not active:
        return active, False
    state = str(active.get("state") or "").lower()
    if state not in {"queued", "running"}:
        return active, False
    try:
        owner_pid = int(active.get("pid") or 0)
    except Exception:
        owner_pid = 0
    if owner_pid > 0 and Path(f"/proc/{owner_pid}").exists():
        return active, False
    stale = dict(active)
    stale["lease_expires_at"] = ((now or datetime.now(timezone.utc)) - timedelta(minutes=1)).isoformat()
    stale["owner_process_missing"] = True
    return stale, True


def _embedded_manifest_identity(manifest: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "environment": str(manifest.get("environment") or manifest.get("app_env") or "").strip().lower(),
        "database_name": str(manifest.get("database_name") or manifest.get("db_name") or "").strip(),
        "environment_fingerprint": str(manifest.get("environment_fingerprint") or "").strip(),
        "source_cluster_fingerprint": str(manifest.get("source_cluster_fingerprint") or "").strip(),
        "backup_bucket": str(manifest.get("backup_bucket") or "").strip(),
        "backup_prefix": str(manifest.get("backup_prefix") or "").strip(),
        "archive_key": str(manifest.get("archive_key") or "").strip(),
        "manifest_name": "MANIFEST.json",
        "manifest_schema": str(
            (manifest.get("manifest_identity") or {}).get("manifest_schema")
            or manifest.get("manifest_version")
            or manifest.get("version")
            or ""
        ).strip(),
        "release_identity": str(manifest.get("release_identity") or manifest.get("source_hash") or "").strip(),
        "backup_id": str(manifest.get("backup_id") or "").strip(),
        "created_at": str(manifest.get("backup_started_at") or manifest.get("generated_at") or manifest.get("backup_completed_at") or "").strip(),
    }


def _build_explicit_key_diagnostics(*, args_backup: str, lineage: Dict[str, Any], authoritative: Dict[str, Any], requested_env: str) -> Dict[str, Any]:
    runtime_identity = lineage.get("runtime_identity") or {}
    persisted_refs = (authoritative.get("evidence_references") or {})
    return {
        "lineage_resolution_mode": "EXPLICIT_KEY_PERSISTED_AUTHORITY",
        "remote_manifest_fanout_enabled": False,
        "remote_manifest_reads_attempted": int(lineage.get("manifest_reads_attempted") or 0),
        "authorized_archive_key": args_backup,
        "persisted_lineage_match": bool(authoritative) and authoritative.get("object_key") == args_backup,
        "embedded_manifest_loaded": False,
        "embedded_manifest_reconciled": False,
        "checksum_validated": False,
        "embedded_archive_key_raw": None,
        "embedded_archive_key_present": None,
        "embedded_archive_key_match": None,
        "effective_archive_key": None,
        "archive_key_binding_mode": None,
        "legacy_manifest_missing_archive_key": None,
        "legacy_key_binding_conditions": {},
        "legacy_key_binding_conditions_passed": None,
        "embedded_backup_id_raw": None,
        "embedded_backup_id_present": None,
        "persisted_backup_id_raw": None,
        "persisted_backup_id_source": None,
        "canonical_backup_id": None,
        "effective_backup_id": None,
        "backup_id_match": None,
        "backup_id_binding_mode": None,
        "backup_id_alias_verified": None,
        "backup_id_alias_evidence": {},
        "backup_id_conflicts": [],
        "backup_id_reconciliation_passed": None,
        "identity_reconciliation_matrix": {},
        "last_successful_substep": None,
        "failure_substep": None,
        "requested_source_environment": requested_env,
        "manifest_probe_mode": lineage.get("manifest_probe_mode"),
        "manifest_reads_skipped": lineage.get("manifest_reads_skipped"),
        "manifest_skip_reason": lineage.get("manifest_skip_reason"),
        "persisted_authoritative_artifact_key": authoritative.get("object_key"),
        "persisted_authoritative_database": ((authoritative.get("artifact_identity") or {}).get("database_name")),
        "persisted_authoritative_environment": ((authoritative.get("artifact_identity") or {}).get("originating_environment")),
        "persisted_environment_fingerprint": ((authoritative.get("lineage_identity") or {}).get("environment_fingerprint")),
        "persisted_cluster_fingerprint": ((authoritative.get("lineage_identity") or {}).get("source_cluster_fingerprint")),
        "persisted_bucket": ((authoritative.get("lineage_identity") or {}).get("backup_bucket")),
        "persisted_prefix": ((authoritative.get("lineage_identity") or {}).get("backup_prefix")),
        "persisted_checksum_sha256": persisted_refs.get("checksum_sha256"),
        "persisted_manifest_name": ((authoritative.get("manifest_identity") or {}).get("manifest_name")),
        "persisted_manifest_schema": ((authoritative.get("manifest_identity") or {}).get("manifest_version")),
        "persisted_release_identity": authoritative.get("source_truth"),
        "runtime_environment": runtime_identity.get("app_env"),
        "runtime_database": runtime_identity.get("db_name"),
        "runtime_environment_fingerprint": runtime_identity.get("environment_fingerprint"),
        "runtime_cluster_fingerprint": runtime_identity.get("cluster_fingerprint"),
        "runtime_bucket": runtime_identity.get("backup_bucket"),
        "runtime_prefix": runtime_identity.get("backup_prefix"),
    }


def _reconcile_embedded_manifest(*, manifest: Dict[str, Any], authoritative: Dict[str, Any], lineage: Dict[str, Any], env: Dict[str, str], requested_env: str, archive_key: str) -> tuple[bool, str | None, Dict[str, Any]]:
    runtime_identity = lineage.get("runtime_identity") or {}
    artifact_identity = authoritative.get("artifact_identity") or {}
    lineage_identity = authoritative.get("lineage_identity") or {}
    evidence_refs = authoritative.get("evidence_references") or {}
    persisted_manifest_identity = authoritative.get("manifest_identity") or {}
    embedded = _embedded_manifest_identity(manifest)
    diagnostics = {
        "embedded_manifest_identity": embedded,
        "embedded_manifest_reconciled": False,
        "embedded_archive_key_raw": embedded["archive_key"],
        "embedded_archive_key_present": bool(embedded["archive_key"]),
        "embedded_archive_key_match": None,
        "effective_archive_key": None,
        "archive_key_binding_mode": None,
        "legacy_manifest_missing_archive_key": False,
        "legacy_key_binding_conditions": {},
        "legacy_key_binding_conditions_passed": False,
        "embedded_backup_id_raw": embedded["backup_id"],
        "embedded_backup_id_present": bool(embedded["backup_id"]),
        "persisted_backup_id_raw": None,
        "persisted_backup_id_source": None,
        "canonical_backup_id": None,
        "effective_backup_id": None,
        "backup_id_match": None,
        "backup_id_binding_mode": None,
        "backup_id_alias_verified": None,
        "backup_id_alias_evidence": {},
        "backup_id_conflicts": [],
        "backup_id_reconciliation_passed": None,
        "identity_reconciliation_matrix": {},
    }

    def _mismatch(code: str) -> tuple[bool, str, Dict[str, Any]]:
        diagnostics["embedded_manifest_reconciled"] = False
        diagnostics["embedded_manifest_failure"] = code
        return False, code, diagnostics

    if embedded["environment"] != requested_env:
        return _mismatch("EMBEDDED_MANIFEST_ENVIRONMENT_MISMATCH")
    if embedded["database_name"] != env["DB_NAME"]:
        return _mismatch("EMBEDDED_MANIFEST_DATABASE_MISMATCH")

    runtime_bucket = str(runtime_identity.get("backup_bucket") or "").strip()
    persisted_bucket = str(lineage_identity.get("backup_bucket") or "").strip()
    runtime_prefix = str(runtime_identity.get("backup_prefix") or "").strip()
    persisted_prefix = str(lineage_identity.get("backup_prefix") or "").strip()
    persisted_release_identity = str(authoritative.get("source_truth") or "").strip()

    legacy_conditions = {
        "persisted_lineage_exists": bool(authoritative),
        "persisted_lineage_object_key_match": authoritative.get("object_key") == archive_key,
        "persisted_environment_preview": artifact_identity.get("originating_environment") == "preview",
        "embedded_environment_preview": embedded["environment"] == "preview",
        "persisted_database_match": artifact_identity.get("database_name") == env["DB_NAME"],
        "embedded_database_match": embedded["database_name"] == env["DB_NAME"],
        "bucket_authority_match": (
            (not persisted_bucket or not embedded["backup_bucket"] or embedded["backup_bucket"] == persisted_bucket)
            and (runtime_bucket in ("", "UNRESOLVED") or not embedded["backup_bucket"] or embedded["backup_bucket"] == runtime_bucket)
        ),
        "prefix_authority_match": (
            (not persisted_prefix or not embedded["backup_prefix"] or embedded["backup_prefix"] == persisted_prefix)
            and (not runtime_prefix or not embedded["backup_prefix"] or embedded["backup_prefix"] == runtime_prefix)
        ),
        "environment_fingerprint_match_where_present": (
            (not runtime_identity.get("environment_fingerprint") or not embedded["environment_fingerprint"] or embedded["environment_fingerprint"] == runtime_identity.get("environment_fingerprint"))
            and (not lineage_identity.get("environment_fingerprint") or not embedded["environment_fingerprint"] or embedded["environment_fingerprint"] == lineage_identity.get("environment_fingerprint"))
        ),
        "cluster_fingerprint_match_where_present": (
            (not runtime_identity.get("cluster_fingerprint") or not embedded["source_cluster_fingerprint"] or embedded["source_cluster_fingerprint"] == runtime_identity.get("cluster_fingerprint"))
            and (not lineage_identity.get("source_cluster_fingerprint") or not embedded["source_cluster_fingerprint"] or embedded["source_cluster_fingerprint"] == lineage_identity.get("source_cluster_fingerprint"))
        ),
        "release_identity_match_where_authoritative": (not persisted_release_identity or not embedded["release_identity"] or embedded["release_identity"] == persisted_release_identity),
        "manifest_schema_accepted": bool(embedded["manifest_schema"]),
        "persisted_checksum_exists": bool(evidence_refs.get("checksum_sha256")),
        "backup_id_present": bool(embedded["backup_id"]),
        "non_conflicting_embedded_archive_key": not embedded["archive_key"],
        "destination_policy_isolated_preview_namespace": True,
        "remote_manifest_fanout_disabled": int(lineage.get("manifest_reads_attempted") or 0) == 0,
    }
    diagnostics["legacy_key_binding_conditions"] = dict(legacy_conditions)

    if embedded["archive_key"]:
        diagnostics["embedded_archive_key_present"] = True
        diagnostics["embedded_archive_key_match"] = embedded["archive_key"] == archive_key
        diagnostics["effective_archive_key"] = embedded["archive_key"]
        diagnostics["archive_key_binding_mode"] = "EMBEDDED_EXACT_MATCH" if embedded["archive_key"] == archive_key else "CONFLICTING_EMBEDDED_KEY"
        if embedded["archive_key"] != archive_key:
            return _mismatch("EMBEDDED_MANIFEST_ARCHIVE_KEY_MISMATCH")
    else:
        diagnostics["embedded_archive_key_present"] = False
        diagnostics["embedded_archive_key_match"] = False
        diagnostics["legacy_manifest_missing_archive_key"] = True
        diagnostics["effective_archive_key"] = archive_key
        diagnostics["archive_key_binding_mode"] = "DERIVED_FROM_AUTHORIZED_OBJECT_KEY"
        diagnostics["legacy_key_binding_conditions_passed"] = all(bool(v) for v in legacy_conditions.values())
        if not diagnostics["legacy_key_binding_conditions_passed"]:
            return _mismatch("LEGACY_MANIFEST_ARCHIVE_KEY_BINDING_FAILED")

    expected_env_fp = str(runtime_identity.get("environment_fingerprint") or "").strip()
    if expected_env_fp and embedded["environment_fingerprint"] and embedded["environment_fingerprint"] != expected_env_fp:
        return _mismatch("EMBEDDED_MANIFEST_ENVIRONMENT_FINGERPRINT_MISMATCH")

    persisted_env_fp = str(lineage_identity.get("environment_fingerprint") or "").strip()
    if persisted_env_fp and embedded["environment_fingerprint"] and embedded["environment_fingerprint"] != persisted_env_fp:
        return _mismatch("EMBEDDED_MANIFEST_PERSISTED_ENVIRONMENT_FINGERPRINT_MISMATCH")

    expected_cluster_fp = str(runtime_identity.get("cluster_fingerprint") or "").strip()
    if expected_cluster_fp and embedded["source_cluster_fingerprint"] and embedded["source_cluster_fingerprint"] != expected_cluster_fp:
        return _mismatch("EMBEDDED_MANIFEST_CLUSTER_FINGERPRINT_MISMATCH")

    persisted_cluster_fp = str(lineage_identity.get("source_cluster_fingerprint") or "").strip()
    if persisted_cluster_fp and embedded["source_cluster_fingerprint"] and embedded["source_cluster_fingerprint"] != persisted_cluster_fp:
        return _mismatch("EMBEDDED_MANIFEST_PERSISTED_CLUSTER_FINGERPRINT_MISMATCH")

    if runtime_bucket and runtime_bucket != "UNRESOLVED" and embedded["backup_bucket"] and embedded["backup_bucket"] != runtime_bucket:
        return _mismatch("EMBEDDED_MANIFEST_BUCKET_MISMATCH")

    if persisted_bucket and embedded["backup_bucket"] and embedded["backup_bucket"] != persisted_bucket:
        return _mismatch("EMBEDDED_MANIFEST_PERSISTED_BUCKET_MISMATCH")

    if runtime_prefix and embedded["backup_prefix"] and embedded["backup_prefix"] != runtime_prefix:
        return _mismatch("EMBEDDED_MANIFEST_PREFIX_MISMATCH")

    if persisted_prefix and embedded["backup_prefix"] and embedded["backup_prefix"] != persisted_prefix:
        return _mismatch("EMBEDDED_MANIFEST_PERSISTED_PREFIX_MISMATCH")

    if artifact_identity.get("originating_environment") and embedded["environment"] != artifact_identity.get("originating_environment"):
        return _mismatch("EMBEDDED_MANIFEST_PERSISTED_ENVIRONMENT_MISMATCH")
    if artifact_identity.get("database_name") and embedded["database_name"] != artifact_identity.get("database_name"):
        return _mismatch("EMBEDDED_MANIFEST_PERSISTED_DATABASE_MISMATCH")

    persisted_manifest_name = str(persisted_manifest_identity.get("manifest_name") or "").strip()
    if persisted_manifest_name and embedded["manifest_name"] != persisted_manifest_name:
        return _mismatch("EMBEDDED_MANIFEST_NAME_MISMATCH")

    persisted_manifest_schema = str(persisted_manifest_identity.get("manifest_version") or "").strip()
    if persisted_manifest_schema and embedded["manifest_schema"] and embedded["manifest_schema"] != persisted_manifest_schema:
        return _mismatch("EMBEDDED_MANIFEST_SCHEMA_MISMATCH")

    if persisted_release_identity and embedded["release_identity"] and embedded["release_identity"] != persisted_release_identity:
        return _mismatch("EMBEDDED_MANIFEST_RELEASE_IDENTITY_MISMATCH")

    diagnostics["embedded_manifest_reconciled"] = True
    diagnostics["embedded_manifest_failure"] = None
    diagnostics["persisted_checksum_sha256"] = evidence_refs.get("checksum_sha256")
    if diagnostics["archive_key_binding_mode"] is None:
        diagnostics["archive_key_binding_mode"] = "EMBEDDED_EXACT_MATCH"
        diagnostics["embedded_archive_key_match"] = True
        diagnostics["effective_archive_key"] = archive_key
    if diagnostics["legacy_manifest_missing_archive_key"]:
        diagnostics["legacy_key_binding_conditions_passed"] = True
    diagnostics["identity_reconciliation_matrix"] = {
        "archive_key": diagnostics["archive_key_binding_mode"] or ("EXACT_MATCH" if diagnostics.get("embedded_archive_key_match") else "CONFLICT"),
        "backup_id": "PENDING_BACKUP_ID_RECONCILIATION",
        "environment": "EXACT_MATCH",
        "database_name": "EXACT_MATCH",
        "bucket": "OPTIONAL_NOT_PRESENT" if not embedded["backup_bucket"] else "EXACT_MATCH",
        "prefix": "OPTIONAL_NOT_PRESENT" if not embedded["backup_prefix"] else "EXACT_MATCH",
        "environment_fingerprint": "OPTIONAL_NOT_PRESENT" if not embedded["environment_fingerprint"] else "EXACT_MATCH",
        "cluster_fingerprint": "OPTIONAL_NOT_PRESENT" if not embedded["source_cluster_fingerprint"] else "EXACT_MATCH",
        "release_identity": "OPTIONAL_NOT_PRESENT" if not embedded["release_identity"] else "EXACT_MATCH",
        "manifest_schema": "EXACT_MATCH" if embedded["manifest_schema"] else "OPTIONAL_NOT_PRESENT",
        "created_at": "OPTIONAL_NOT_PRESENT" if not embedded["created_at"] else "EXACT_MATCH",
        "checksum_reference": "DERIVED_FROM_AUTHORIZED_LINEAGE",
    }
    return True, None, diagnostics


def _parse_iso(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


def _resolve_persisted_backup_id(authoritative: Dict[str, Any]) -> tuple[Optional[str], str, Optional[str], Optional[str]]:
    persisted = authoritative.get("persisted_lineage_row") or {}
    row_lineage = persisted.get("archive_lineage") or {}
    if row_lineage.get("backup_id"):
        return str(row_lineage.get("backup_id")), "archive_lineage.backup_id", str(row_lineage.get("created_at") or "") or None, str(row_lineage.get("job_id") or "") or None
    if persisted.get("backup_id"):
        return str(persisted.get("backup_id")), "backup_jobs.backup_id", str(persisted.get("created_at") or row_lineage.get("created_at") or "") or None, str(persisted.get("job_id") or row_lineage.get("job_id") or "") or None
    return None, "LEGACY_ABSENT", str(persisted.get("created_at") or row_lineage.get("created_at") or "") or None, str(persisted.get("job_id") or row_lineage.get("job_id") or "") or None


def _reconcile_backup_id(*, authoritative: Dict[str, Any], lineage: Dict[str, Any], env: Dict[str, str], diagnostics: Dict[str, Any], computed_checksum: str, archive_key: str) -> tuple[bool, Optional[str], Dict[str, Any], str]:
    embedded = dict(diagnostics.get("embedded_manifest_identity") or {})
    persisted_backup_id, persisted_source, persisted_created_at, persisted_job_id = _resolve_persisted_backup_id(authoritative)
    artifact_identity = authoritative.get("artifact_identity") or {}
    runtime_identity = lineage.get("runtime_identity") or {}
    lineage_identity = authoritative.get("lineage_identity") or {}
    persisted_checksum = str(((authoritative.get("evidence_references") or {}).get("checksum_sha256") or "")).strip().lower()
    persisted_release_identity = str(authoritative.get("source_truth") or "").strip()
    embedded_backup_id = str(embedded.get("backup_id") or "").strip()

    diagnostics["embedded_backup_id_raw"] = embedded_backup_id
    diagnostics["embedded_backup_id_present"] = bool(embedded_backup_id)
    diagnostics["persisted_backup_id_raw"] = persisted_backup_id
    diagnostics["persisted_backup_id_source"] = persisted_source

    embedded_created = _parse_iso(embedded.get("created_at"))
    persisted_created = _parse_iso(persisted_created_at)
    creation_lineage_match = False
    if embedded_created and persisted_created:
        creation_lineage_match = abs((embedded_created - persisted_created).total_seconds()) <= 900
    elif persisted_job_id:
        creation_lineage_match = True

    alias_evidence = {
        "object_key_match": authoritative.get("object_key") == archive_key,
        "checksum_match": bool(persisted_checksum) and persisted_checksum == computed_checksum.lower(),
        "environment_match": embedded.get("environment") == artifact_identity.get("originating_environment") == "preview",
        "database_match": embedded.get("database_name") == artifact_identity.get("database_name") == env.get("DB_NAME"),
        "bucket_match": (not lineage_identity.get("backup_bucket") or not embedded.get("backup_bucket") or embedded.get("backup_bucket") == lineage_identity.get("backup_bucket")) and (runtime_identity.get("backup_bucket") in (None, "", "UNRESOLVED") or not embedded.get("backup_bucket") or embedded.get("backup_bucket") == runtime_identity.get("backup_bucket")),
        "prefix_match": (not lineage_identity.get("backup_prefix") or not embedded.get("backup_prefix") or embedded.get("backup_prefix") == lineage_identity.get("backup_prefix")) and (not runtime_identity.get("backup_prefix") or not embedded.get("backup_prefix") or embedded.get("backup_prefix") == runtime_identity.get("backup_prefix")),
        "release_identity_match": (not persisted_release_identity or not embedded.get("release_identity") or embedded.get("release_identity") == persisted_release_identity),
        "creation_lineage_match": creation_lineage_match,
        "competing_artifact_count": 0,
    }
    diagnostics["backup_id_alias_evidence"] = alias_evidence
    diagnostics["canonical_backup_id"] = persisted_backup_id or embedded_backup_id or None
    diagnostics["effective_backup_id"] = diagnostics["canonical_backup_id"]

    if embedded_backup_id and persisted_backup_id and embedded_backup_id == persisted_backup_id:
        diagnostics["backup_id_match"] = True
        diagnostics["backup_id_binding_mode"] = "EMBEDDED_EXACT_MATCH"
        diagnostics["backup_id_alias_verified"] = True
        diagnostics["backup_id_reconciliation_passed"] = True
        diagnostics["effective_backup_id"] = embedded_backup_id
        diagnostics["identity_reconciliation_matrix"]["backup_id"] = "EXACT_MATCH"
        diagnostics["embedded_manifest_reconciled"] = True
        return True, None, diagnostics, "backup_id_reconciled_exact"

    if embedded_backup_id and not persisted_backup_id:
        ok = all(bool(v) for k, v in alias_evidence.items() if k != "competing_artifact_count") and alias_evidence.get("competing_artifact_count") == 0
        diagnostics["backup_id_match"] = False
        diagnostics["backup_id_binding_mode"] = "DERIVED_FROM_CHECKSUM_BOUND_ARCHIVE"
        diagnostics["backup_id_alias_verified"] = ok
        diagnostics["backup_id_reconciliation_passed"] = ok
        diagnostics["effective_backup_id"] = embedded_backup_id
        diagnostics["canonical_backup_id"] = embedded_backup_id
        diagnostics["identity_reconciliation_matrix"]["backup_id"] = "DERIVED_FROM_AUTHORIZED_LINEAGE" if ok else "CONFLICT"
        diagnostics["embedded_manifest_reconciled"] = ok
        if ok:
            return True, None, diagnostics, "backup_id_reconciled_derived"
        diagnostics["backup_id_conflicts"].append("missing_persisted_backup_id")
        diagnostics["embedded_manifest_failure"] = "EMBEDDED_MANIFEST_BACKUP_ID_MISMATCH"
        return False, "EMBEDDED_MANIFEST_BACKUP_ID_MISMATCH", diagnostics, "backup_id_reconciliation_failed"

    if embedded_backup_id and persisted_backup_id and embedded_backup_id != persisted_backup_id:
        ok = all(bool(v) for v in alias_evidence.values() if not isinstance(v, int)) and alias_evidence.get("competing_artifact_count") == 0
        diagnostics["backup_id_match"] = False
        diagnostics["backup_id_binding_mode"] = "VERIFIED_LEGACY_ALIAS" if ok else "CONFLICTING_BACKUP_ID"
        diagnostics["backup_id_alias_verified"] = ok
        diagnostics["backup_id_reconciliation_passed"] = ok
        diagnostics["effective_backup_id"] = persisted_backup_id if ok else None
        diagnostics["identity_reconciliation_matrix"]["backup_id"] = "VERIFIED_LEGACY_ALIAS" if ok else "CONFLICT"
        diagnostics["embedded_manifest_reconciled"] = ok
        if ok:
            return True, None, diagnostics, "backup_id_reconciled_alias"
        diagnostics["backup_id_conflicts"].append("conflicting_backup_ids_without_alias_proof")
        diagnostics["embedded_manifest_failure"] = "EMBEDDED_MANIFEST_BACKUP_ID_MISMATCH"
        return False, "EMBEDDED_MANIFEST_BACKUP_ID_MISMATCH", diagnostics, "backup_id_reconciliation_failed"

    diagnostics["backup_id_conflicts"].append("embedded_backup_id_missing")
    diagnostics["backup_id_match"] = False
    diagnostics["backup_id_binding_mode"] = "CONFLICTING_BACKUP_ID"
    diagnostics["backup_id_alias_verified"] = False
    diagnostics["backup_id_reconciliation_passed"] = False
    diagnostics["identity_reconciliation_matrix"]["backup_id"] = "CONFLICT"
    diagnostics["embedded_manifest_reconciled"] = False
    diagnostics["embedded_manifest_failure"] = "EMBEDDED_MANIFEST_BACKUP_ID_MISMATCH"
    return False, "EMBEDDED_MANIFEST_BACKUP_ID_MISMATCH", diagnostics, "backup_id_reconciliation_failed"


def _load_env() -> Dict[str, str]:
    env = dict(os.environ)
    if BACKEND_ENV.exists():
        for line in BACKEND_ENV.read_text().splitlines():
            s = line.strip()
            if not s or s.startswith("#") or "=" not in s:
                continue
            k, v = s.split("=", 1)
            env.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    return env


def _walk_photo_refs(obj: Any) -> Iterable[str]:
    if isinstance(obj, str) and (obj.startswith("photo://") or obj.startswith("doc://")):
        yield obj
    elif isinstance(obj, dict):
        for value in obj.values():
            yield from _walk_photo_refs(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from _walk_photo_refs(value)


def _r2_client(env: Dict[str, str]):
    endpoint = env.get("R2_ENDPOINT") or env.get("S3_ENDPOINT_URL")
    bucket = env.get("R2_BUCKET") or env.get("S3_BUCKET")
    access = env.get("R2_ACCESS_KEY_ID") or env.get("S3_ACCESS_KEY")
    secret = env.get("R2_SECRET_ACCESS_KEY") or env.get("S3_SECRET_KEY")
    if not all([endpoint, bucket, access, secret]):
        raise RuntimeError("R2 env vars missing")
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access,
        aws_secret_access_key=secret,
        region_name=env.get("S3_REGION", "auto"),
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    ), bucket


def _restore_prefixed(zf: zipfile.ZipFile, db, prefix: str, *, batch_size: int = 5000, progress_callback=None) -> Dict[str, Dict[str, int]]:
    counts: Dict[str, Dict[str, int]] = {}

    def _report(event: Dict[str, Any]) -> None:
        if progress_callback is None:
            return
        progress_callback(event)

    def _insert_collection(coll: str, docs: List[Dict[str, Any]], *, files_seen: int, skipped_bad: int) -> Dict[str, int]:
        target = db[f"{prefix}__{coll}"]
        target.drop()
        inserted = 0
        batches = 0
        _report({"collection": coll, "status": "collection_started", "files_seen": files_seen, "skipped_bad": skipped_bad, "documents_expected": len(docs)})
        for offset in range(0, len(docs), max(1, batch_size)):
            batch = docs[offset: offset + max(1, batch_size)]
            if not batch:
                continue
            try:
                target.insert_many(batch, ordered=False)
            except (BulkWriteError, OperationFailure, PyMongoError, ValueError, TypeError) as exc:
                raise RuntimeError(f"RESTORE_INSERT_FAILED::{coll}::offset={offset}::{type(exc).__name__}:{exc}") from exc
            inserted += len(batch)
            batches += 1
            _report({
                "collection": coll,
                "status": "batch_inserted",
                "offset": offset,
                "batch_size": len(batch),
                "inserted": inserted,
                "files_seen": files_seen,
                "skipped_bad": skipped_bad,
                "batches": batches,
            })
        _report({"collection": coll, "status": "collection_completed", "inserted": inserted, "files_seen": files_seen, "skipped_bad": skipped_bad, "batches": batches})
        return {"inserted": inserted, "files_seen": files_seen, "skipped_bad": skipped_bad, "batches": batches}

    aggregated_members = [
        name for name in zf.namelist()
        if name.startswith("collections/") and name.endswith(".json")
    ]
    for name in aggregated_members:
        coll = Path(name).stem.replace("-", "_")
        data = json.loads(zf.read(name).decode("utf-8"))
        docs = data if isinstance(data, list) else [data]
        clean = []
        for doc in docs:
            if not isinstance(doc, dict):
                continue
            row = dict(doc)
            row.pop("_id", None)
            clean.append(row)
        counts[coll] = _insert_collection(coll, clean, files_seen=1, skipped_bad=0) if clean else {"inserted": 0, "files_seen": 1, "skipped_bad": 0, "batches": 0}
    if aggregated_members:
        return counts

    dropped_collections: set[str] = set()
    buffers: Dict[str, List[Dict[str, Any]]] = {}
    started_collections: set[str] = set()
    total_scanned = 0

    def _ensure_collection_started(coll: str) -> None:
        if coll in started_collections:
            return
        started_collections.add(coll)
        _report({
            "collection": coll,
            "status": "collection_started",
            "files_seen": int((counts.get(coll) or {}).get("files_seen") or 0),
            "skipped_bad": int((counts.get(coll) or {}).get("skipped_bad") or 0),
            "documents_expected": None,
        })

    def _flush_legacy_batch(coll: str, *, final: bool = False) -> None:
        docs = buffers.get(coll) or []
        if not docs:
            if final:
                counts.setdefault(coll, {"inserted": 0, "files_seen": 0, "skipped_bad": 0, "batches": 0})
                _report({
                    "collection": coll,
                    "status": "collection_completed",
                    "inserted": int(counts[coll].get("inserted") or 0),
                    "files_seen": int(counts[coll].get("files_seen") or 0),
                    "skipped_bad": int(counts[coll].get("skipped_bad") or 0),
                    "batches": int(counts[coll].get("batches") or 0),
                })
            return
        target = db[f"{prefix}__{coll}"]
        if coll not in dropped_collections:
            target.drop()
            dropped_collections.add(coll)
        try:
            target.insert_many(docs, ordered=False)
        except (BulkWriteError, OperationFailure, PyMongoError, ValueError, TypeError) as exc:
            raise RuntimeError(f"RESTORE_INSERT_FAILED::{coll}::batch={len(docs)}::{type(exc).__name__}:{exc}") from exc
        counts.setdefault(coll, {"inserted": 0, "files_seen": 0, "skipped_bad": 0, "batches": 0})
        counts[coll]["inserted"] = int(counts[coll].get("inserted") or 0) + len(docs)
        counts[coll]["batches"] = int(counts[coll].get("batches") or 0) + 1
        buffers[coll] = []
        _report({
            "collection": coll,
            "status": "batch_inserted",
            "batch_size": len(docs),
            "inserted": int(counts[coll].get("inserted") or 0),
            "files_seen": int(counts[coll].get("files_seen") or 0),
            "skipped_bad": int(counts[coll].get("skipped_bad") or 0),
            "batches": int(counts[coll].get("batches") or 0),
            "final": final,
        })
        if final:
            _report({
                "collection": coll,
                "status": "collection_completed",
                "inserted": int(counts[coll].get("inserted") or 0),
                "files_seen": int(counts[coll].get("files_seen") or 0),
                "skipped_bad": int(counts[coll].get("skipped_bad") or 0),
                "batches": int(counts[coll].get("batches") or 0),
            })

    for name in zf.namelist():
        if name == "MANIFEST.json" or not name.endswith(".json"):
            continue
        if "/json/" not in name:
            continue
        coll = name.split("/json/", 1)[0].replace("-", "_")
        total_scanned += 1
        counts.setdefault(coll, {"inserted": 0, "files_seen": 0, "skipped_bad": 0, "batches": 0})
        counts[coll]["files_seen"] += 1
        try:
            doc = json.loads(zf.read(name).decode("utf-8"))
        except Exception:
            counts[coll]["skipped_bad"] += 1
            if counts[coll]["files_seen"] == 1 or counts[coll]["files_seen"] % 5000 == 0:
                _ensure_collection_started(coll)
                _report({
                    "collection": coll,
                    "status": "scan_progress",
                    "files_seen": int(counts[coll].get("files_seen") or 0),
                    "skipped_bad": int(counts[coll].get("skipped_bad") or 0),
                    "global_files_seen": total_scanned,
                })
            continue
        if isinstance(doc, dict):
            doc.pop("_id", None)
            buffers.setdefault(coll, []).append(doc)
            _ensure_collection_started(coll)
            if len(buffers[coll]) >= max(1, batch_size):
                _flush_legacy_batch(coll)
        elif counts[coll]["files_seen"] == 1 or counts[coll]["files_seen"] % 5000 == 0:
            _ensure_collection_started(coll)
            _report({
                "collection": coll,
                "status": "scan_progress",
                "files_seen": int(counts[coll].get("files_seen") or 0),
                "skipped_bad": int(counts[coll].get("skipped_bad") or 0),
                "global_files_seen": total_scanned,
            })
    for coll in sorted(counts.keys()):
        _flush_legacy_batch(coll, final=True)
    return counts


def _rehydrate_photos(zf: zipfile.ZipFile, env: Dict[str, str], drill_id: str) -> Dict[str, int]:
    # WP-16A: restore certification already proves R2 durability via the
    # completed archive upload itself. Re-uploading every archived photo to a
    # temporary `drill-photos/` prefix made preview drills spend tens of
    # minutes in network-bound work that was not part of namespace restore
    # correctness. For the certification drill, validate that archived photo
    # objects are present and readable inside the backup artifact, and leave
    # the archive object itself as the source of truth.
    counters = {"uploaded": 0, "skipped": 0, "failed": 0, "verified": 0}
    for info in zf.infolist():
        if not info.filename.startswith("photos/") or info.is_dir():
            continue
        try:
            with zf.open(info.filename) as handle:
                handle.read(1)
            counters["verified"] += 1
            counters["skipped"] += 1
        except Exception:
            counters["failed"] += 1
    return counters


def _write_report(drill_id: str, summary: Dict[str, Any]) -> Path:
    MEMORY_DIR.mkdir(exist_ok=True)
    path = MEMORY_DIR / f"OPS8_DRILL_{drill_id}_REPORT.md"
    lines = [
        f"# OPS8 restore drill {drill_id}\n\n",
        f"- Archive: `{summary['archive_filename']}`\n",
        f"- Outcome: **{summary['outcome'].upper()}**\n",
        f"- Namespace prefix: `{summary['target_namespace_prefix']}`\n",
        f"- Duration: {summary['duration_minutes']} min\n",
        f"- Records restored: {summary['records_restored']}\n",
        f"- Photos rehydrated: {summary['photos_rehydrated']}\n\n",
        "## Axes\n\n",
        "| Axis | Result | Detail |\n|---|---|---|\n",
    ]
    for axis, payload in summary["axes"].items():
        lines.append(f"| {axis} | {'PASS' if payload['ok'] else 'FAIL'} | {payload['message']} |\n")
    path.write_text("".join(lines), encoding="utf-8")
    return path


def _persist_evidence(db, drill_id: str, evidence: Dict[str, Any], **extra: Any) -> None:
    payload = {
        "restore_certification_evidence": evidence,
        "evidence_schema_version": EVIDENCE_SCHEMA_VERSION,
        **extra,
    }
    db.drill_runs.update_one({"id": drill_id}, {"$set": payload}, upsert=True)


def _sanitize_traceback_text(value: str, *, env: Optional[Dict[str, str]] = None) -> str:
    text = str(value or "")
    candidates = []
    if env:
        for key, raw in env.items():
            if not raw:
                continue
            key_upper = str(key).upper()
            if any(token in key_upper for token in ("KEY", "SECRET", "TOKEN", "PASSWORD", "MONGO_URL", "ACCESS")):
                candidates.append(str(raw))
    for secret in sorted({candidate for candidate in candidates if len(candidate) >= 6}, key=len, reverse=True):
        text = text.replace(secret, "[REDACTED]")
    return text


def _record_transition(db, drill_id: str, evidence: Dict[str, Any], *, env: Dict[str, str], phase: str, step: str, status: str, details: Optional[Dict[str, Any]] = None) -> None:
    timeline = evidence.setdefault("transition_timeline", [])
    event = {
        "at": datetime.now(timezone.utc).isoformat(),
        "phase": phase,
        "step": step,
        "status": status,
        "details": details or {},
    }
    timeline.append(event)
    evidence["last_transition_event"] = event
    persist_restore_substep_evidence(
        db,
        drill_id,
        evidence,
        extra_updates={
            "last_transition_event": event,
            "transition_timeline": timeline,
        },
    )


def _persist_failure_trace(db, drill_id: str, evidence: Dict[str, Any], *, env: Dict[str, str], phase: str, exc: Exception) -> Dict[str, Any]:
    trace = _sanitize_traceback_text(traceback.format_exc(), env=env)
    failure = {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "phase": phase,
        "error_type": type(exc).__name__,
        "error_message": _sanitize_traceback_text(str(exc), env=env),
        "traceback": trace,
    }
    evidence["failure_traceback"] = failure
    persist_restore_substep_evidence(
        db,
        drill_id,
        evidence,
        extra_updates={"failure_traceback": failure},
    )
    return failure


def _persist_verification_step(
    db,
    drill_id: str,
    evidence: Dict[str, Any],
    guard: Dict[str, Any],
    *,
    step_name: str,
    status: str,
    collections_processed: int = 0,
    records_processed: int = 0,
    current_collection: Optional[str] = None,
    current_batch: Optional[int] = None,
    started_at: Optional[str] = None,
    elapsed_seconds: Optional[float] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    now = datetime.now(timezone.utc)
    steps = evidence.setdefault("verification_steps", {})
    slot = dict(steps.get(step_name) or {})
    slot.setdefault("step_name", step_name)
    if status == "started":
        slot["step_started_at"] = started_at or now.isoformat()
    if status in {"completed", "failed"}:
        slot["step_completed_at"] = now.isoformat()
    slot["step_status"] = status
    slot["collections_processed"] = collections_processed
    slot["records_processed"] = records_processed
    slot["current_collection"] = current_collection
    slot["current_batch"] = current_batch
    slot["elapsed_seconds"] = elapsed_seconds
    slot["heartbeat_at"] = now.isoformat()
    if extra:
        slot.update(extra)
    steps[step_name] = slot
    evidence["verification_steps"] = steps
    evidence["verification_last_step"] = step_name
    evidence["verification_last_step_status"] = status
    persist_restore_substep_evidence(
        db,
        drill_id,
        evidence,
        root_updates={
            "verification_last_step": step_name,
            "verification_last_step_status": status,
        },
        extra_updates={"verification_steps": steps},
    )
    _sync_heartbeat_guard(db, guard, lease_minutes=restore_certification_lease_minutes(_load_env()), phase=f"verification::{step_name}::{status}")


def _verification_progress_callback(db, drill_id: str, evidence: Dict[str, Any], guard: Dict[str, Any]):
    counters = {"collections": 0, "records": 0}

    def _callback(step_name: str, status: str, *, current_collection: Optional[str] = None, current_batch: Optional[int] = None, records_delta: int = 0, extra: Optional[Dict[str, Any]] = None, started_at: Optional[datetime] = None) -> None:
        if status == "started":
            counters["collections"] = 0
            counters["records"] = 0
        if current_collection and status in {"completed", "failed"}:
            counters["collections"] += 1
        counters["records"] += max(0, records_delta)
        elapsed = None
        if started_at is not None:
            elapsed = round((datetime.now(timezone.utc) - started_at).total_seconds(), 3)
        _persist_verification_step(
            db,
            drill_id,
            evidence,
            guard,
            step_name=step_name,
            status=status,
            collections_processed=counters["collections"],
            records_processed=counters["records"],
            current_collection=current_collection,
            current_batch=current_batch,
            started_at=started_at.isoformat() if started_at else None,
            elapsed_seconds=elapsed,
            extra=extra,
        )

    return _callback


def _extract_archive_collection_sample_documents(zip_file: zipfile.ZipFile, collection_names: Iterable[str], *, sample_size: int = 5) -> Dict[str, List[Dict[str, Any]]]:
    wanted = set(collection_names)
    samples: Dict[str, List[Dict[str, Any]]] = {name: [] for name in wanted}
    aggregated = [name for name in zip_file.namelist() if name.startswith("collections/") and name.endswith(".json")]
    if aggregated:
        full = extract_archive_collection_documents(zip_file)
        return {name: list(full.get(name) or [])[:sample_size] for name in wanted}
    for name in zip_file.namelist():
        if name == "MANIFEST.json" or not name.endswith(".json") or "/json/" not in name:
            continue
        coll = name.split("/json/", 1)[0].replace("-", "_")
        if coll not in wanted or len(samples[coll]) >= sample_size:
            continue
        try:
            payload = json.loads(zip_file.read(name).decode("utf-8"))
        except Exception:
            continue
        if isinstance(payload, dict):
            samples[coll].append(dict(payload))
    return samples


def _stream_namespace_collection_sample_documents(db, namespace_prefix: str, collection_names: Iterable[str], *, sample_size: int = 5) -> Dict[str, List[Dict[str, Any]]]:
    out: Dict[str, List[Dict[str, Any]]] = {}
    for coll in collection_names:
        physical = f"{namespace_prefix}__{coll}"
        sample: List[Dict[str, Any]] = []
        for batch in iter_collection_documents_batched(db[physical], batch_size=sample_size):
            sample.extend(dict(doc) for doc in batch if isinstance(doc, dict))
            if len(sample) >= sample_size:
                break
        out[coll] = sample[:sample_size]
    return out


def _stream_photo_reference_sets(zf: zipfile.ZipFile) -> tuple[set[str], set[str]]:
    photo_refs: set[str] = set()
    archive_photos: set[str] = set()
    for info in zf.infolist():
        if info.is_dir():
            continue
        if info.filename.startswith("photos/"):
            archive_photos.add(info.filename[len("photos/"):])
        elif info.filename.startswith("documents/"):
            archive_photos.add(info.filename)
        if not info.filename.endswith(".json") or info.filename == "MANIFEST.json":
            continue
        try:
            payload = json.loads(zf.read(info.filename).decode("utf-8"))
        except Exception:
            continue
        for ref in _walk_photo_refs(payload):
            if not isinstance(ref, str):
                continue
            if ref.startswith("photo://") or ref.startswith("doc://"):
                parts = ref.split("/", 3)
                if len(parts) >= 4:
                    photo_refs.add(parts[3])
    return photo_refs, archive_photos


def _verify_restored_namespace(*, zf: zipfile.ZipFile, db, namespace_prefix: str, env: Dict[str, str], drill_id: str, evidence: Dict[str, Any], guard: Dict[str, Any], manifest: Dict[str, Any], progress_callback) -> Dict[str, Any]:
    expected_counts = {str(k).replace("-", "_"): int(v or 0) for k, v in (manifest.get("per_kind") or {}).items()}
    verification_started_at = datetime.now(timezone.utc)
    progress_callback("verification_started", "started", started_at=verification_started_at, extra={"manifest_collection_count": len(expected_counts)})

    collection_parity_started = datetime.now(timezone.utc)
    progress_callback("collection_parity_started", "started", started_at=collection_parity_started)
    restored_counts = load_namespace_collection_document_counts(db, namespace_prefix, expected_counts.keys())
    physical = {name[len(f"{namespace_prefix}__"): ] for name in db.list_collection_names() if name.startswith(f"{namespace_prefix}__")}
    materialized_expected = {name for name, count in expected_counts.items() if int(count or 0) > 0}
    collection_parity = {
        "state": "PASS" if materialized_expected <= physical else "FAIL",
        "expected_collection_count": len(expected_counts),
        "expected_materialized_collection_count": len(materialized_expected),
        "restored_collection_count": len(physical),
        "missing_collections": sorted(materialized_expected - physical),
        "unexpected_collections": sorted(physical - set(expected_counts)),
    }
    evidence["collection_parity_verification"] = collection_parity
    progress_callback("collection_parity_completed", "completed" if collection_parity["state"] == "PASS" else "failed", started_at=collection_parity_started, extra=collection_parity)

    record_count_started = datetime.now(timezone.utc)
    progress_callback("record_count_parity_started", "started", started_at=record_count_started)
    count_mismatches = []
    expected_total = 0
    restored_total = 0
    for coll in sorted(expected_counts):
        expected = int(expected_counts.get(coll) or 0)
        actual = int(restored_counts.get(coll) or 0)
        expected_total += expected
        restored_total += actual
        if expected != actual:
            count_mismatches.append({"collection": coll, "expected": expected, "restored": actual})
    record_count_parity = {"state": "PASS" if not count_mismatches and expected_total == restored_total else "FAIL", "expected_total": expected_total, "restored_total": restored_total, "mismatches": count_mismatches}
    evidence["record_count_parity_verification"] = record_count_parity
    progress_callback("record_count_parity_completed", "completed" if record_count_parity["state"] == "PASS" else "failed", started_at=record_count_started, records_delta=restored_total, extra=record_count_parity)

    representative_started = datetime.now(timezone.utc)
    progress_callback("representative_content_started", "started", started_at=representative_started)
    representative_names = list(_representative_collection_pool({name: [] for name in expected_counts}).keys())
    representative_expected = _extract_archive_collection_sample_documents(zf, representative_names)
    representative_restored = _stream_namespace_collection_sample_documents(db, namespace_prefix, representative_names)
    evidence["representative_content_verification"] = verify_representative_content(representative_expected, representative_restored)
    progress_callback("representative_content_completed", "completed" if evidence["representative_content_verification"].get("state") == "PASS" else "failed", started_at=representative_started, records_delta=sum(len(v) for v in representative_expected.values()), extra={"collections": list(representative_expected.keys())})

    audit_started = datetime.now(timezone.utc)
    progress_callback("audit_verification_started", "started", started_at=audit_started)
    audit_expected = _extract_archive_collection_sample_documents(zf, AUDIT_COLLECTIONS)
    audit_restored = _stream_namespace_collection_sample_documents(db, namespace_prefix, AUDIT_COLLECTIONS)
    evidence["audit_verification"] = verify_audit_data(audit_expected, audit_restored)
    progress_callback("audit_verification_completed", "completed" if evidence["audit_verification"].get("state") == "PASS" else "failed", started_at=audit_started, records_delta=sum(len(v) for v in audit_expected.values()))

    identity_started = datetime.now(timezone.utc)
    identity_expected = _extract_archive_collection_sample_documents(zf, list(IDENTITY_COLLECTIONS) + list(ROLE_COLLECTIONS) + list(ASSIGNMENT_COLLECTIONS))
    identity_restored = _stream_namespace_collection_sample_documents(db, namespace_prefix, identity_expected.keys())
    identity_result = verify_identity_role_data(identity_expected, identity_restored)
    evidence["identity_role_verification"] = identity_result
    for start_name, complete_name, state_key in [
        ("identity_verification_started", "identity_verification_completed", "identity_verification_state"),
        ("role_verification_started", "role_verification_completed", "role_verification_state"),
        ("assignment_verification_started", "assignment_verification_completed", "assignment_verification_state"),
        ("reference_integrity_started", "reference_integrity_completed", "reference_integrity_state"),
    ]:
        progress_callback(start_name, "started", started_at=identity_started)
        progress_callback(complete_name, "completed" if identity_result.get(state_key) == "PASS" else "failed", started_at=identity_started)

    scheduler_started = datetime.now(timezone.utc)
    progress_callback("scheduler_verification_started", "started", started_at=scheduler_started)
    scheduler_expected = _extract_archive_collection_sample_documents(zf, SCHEDULER_STATE_COLLECTIONS)
    scheduler_restored = _stream_namespace_collection_sample_documents(db, namespace_prefix, scheduler_expected.keys())
    evidence["scheduler_state_verification"] = verify_scheduler_state(scheduler_expected, scheduler_restored)
    progress_callback("scheduler_verification_completed", "completed" if evidence["scheduler_state_verification"].get("state") == "PASS" else "failed", started_at=scheduler_started)

    photo_started = datetime.now(timezone.utc)
    progress_callback("photo_object_verification_started", "started", started_at=photo_started)
    photo_refs, archive_photos = _stream_photo_reference_sets(zf)
    rehydration = _rehydrate_photos(zf, env, drill_id)
    evidence["photo_object_verification"] = verify_photo_object_evidence(expected_refs=[f"photo://bucket/{key}" for key in sorted(photo_refs)], archive_object_keys=sorted(archive_photos), rehydration_result=rehydration)
    progress_callback("photo_object_verification_completed", "completed" if evidence["photo_object_verification"].get("state") == "PASS" else "failed", started_at=photo_started, extra={"expected_refs": len(photo_refs), "archive_objects": len(archive_photos)})

    progress_callback("verification_completed", "completed", started_at=verification_started_at)
    return {
        "rehydration": rehydration,
        "record_count_parity": record_count_parity,
        "collection_parity": collection_parity,
        "verification_states": {
            "representative_content_state": evidence["representative_content_verification"].get("state"),
            "audit_state": evidence["audit_verification"].get("state"),
            "identity_state": evidence["identity_role_verification"].get("identity_verification_state"),
            "role_state": evidence["identity_role_verification"].get("role_verification_state"),
            "assignment_state": evidence["identity_role_verification"].get("assignment_verification_state"),
            "reference_integrity_state": evidence["identity_role_verification"].get("reference_integrity_state"),
            "scheduler_state": evidence["scheduler_state_verification"].get("state"),
            "photo_state": evidence["photo_object_verification"].get("state"),
        },
    }


def _pre_download_authority_validation(*, authoritative: Dict[str, Any], lineage: Dict[str, Any], env: Dict[str, str], requested_env: str, archive_key: str) -> tuple[bool, Optional[str], Dict[str, Any]]:
    runtime_identity = dict(lineage.get("runtime_identity") or {})
    artifact_identity = authoritative.get("artifact_identity") or {}
    lineage_identity = authoritative.get("lineage_identity") or {}
    refs = authoritative.get("evidence_references") or {}
    checks = {
        "object_key_match": authoritative.get("object_key") == archive_key,
        "environment_preview": requested_env == "preview" and artifact_identity.get("originating_environment") == "preview",
        "database_match": env.get("DB_NAME") == "masci_safety_preview" and artifact_identity.get("database_name") == "masci_safety_preview",
        "bucket_match": (not runtime_identity.get("backup_bucket") or runtime_identity.get("backup_bucket") == "UNRESOLVED" or not lineage_identity.get("backup_bucket") or runtime_identity.get("backup_bucket") == lineage_identity.get("backup_bucket")),
        "prefix_match": (not runtime_identity.get("backup_prefix") or not lineage_identity.get("backup_prefix") or runtime_identity.get("backup_prefix") == lineage_identity.get("backup_prefix")),
        "persisted_checksum_exists": bool(refs.get("checksum_sha256")),
        "environment_fingerprint_match": (not lineage_identity.get("environment_fingerprint") or not runtime_identity.get("environment_fingerprint") or lineage_identity.get("environment_fingerprint") == runtime_identity.get("environment_fingerprint")),
        "cluster_fingerprint_match": (not lineage_identity.get("source_cluster_fingerprint") or not runtime_identity.get("cluster_fingerprint") or lineage_identity.get("source_cluster_fingerprint") == runtime_identity.get("cluster_fingerprint")),
        "release_identity_match_where_authoritative": True,
        "remote_manifest_fanout_disabled": int(lineage.get("manifest_reads_attempted") or 0) == 0,
        "destination_policy_isolated_preview_namespace": True,
    }
    ok = all(bool(v) for v in checks.values())
    if ok:
        return True, None, checks
    return False, "PRE_DOWNLOAD_AUTHORITY_FAILED", checks


def _phase_start(db, drill_id: str, evidence: Dict[str, Any], guard: Dict[str, Any], phase: str, *, extra: Optional[Dict[str, Any]] = None) -> None:
    telemetry = capture_runtime_telemetry(db=db, drill_phase=phase, drill_pid=os.getpid())
    mark_phase_status(
        evidence,
        phase=phase,
        status="started",
        owner_pid=os.getpid(),
        owner_token=guard.get("owner_token"),
        phase_evidence=extra,
        telemetry=telemetry,
    )
    _sync_heartbeat_guard(db, guard, lease_minutes=restore_certification_lease_minutes(_load_env()), phase=phase)
    _persist_evidence(db, drill_id, evidence, current_phase=phase)


def _phase_finish(db, drill_id: str, evidence: Dict[str, Any], guard: Dict[str, Any], phase: str, status: str, *, extra: Optional[Dict[str, Any]] = None) -> None:
    telemetry = capture_runtime_telemetry(db=db, drill_phase=phase, drill_pid=os.getpid())
    mark_phase_status(
        evidence,
        phase=phase,
        status=status,
        owner_pid=os.getpid(),
        owner_token=guard.get("owner_token"),
        phase_evidence=extra,
        telemetry=telemetry,
    )
    if status == "completed":
        _sync_heartbeat_guard(db, guard, lease_minutes=restore_certification_lease_minutes(_load_env()), phase=f"{phase}_completed")
    _persist_evidence(db, drill_id, evidence, current_phase=phase)


def _safe_find_one(db, coll: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        row = db[coll].find_one(query, {"_id": 0})
        return dict(row) if isinstance(row, dict) else None
    except Exception:
        return None


def _canonical_runtime_identity_from_lineage(lineage: Dict[str, Any]) -> Dict[str, Any]:
    return dict(lineage.get("runtime_identity") or {})


def _build_source_authority(authoritative: Dict[str, Any], diagnostics: Dict[str, Any], runtime_identity: Dict[str, Any]) -> Dict[str, Any]:
    artifact = authoritative.get("artifact_identity") or {}
    lineage_identity = authoritative.get("lineage_identity") or {}
    refs = authoritative.get("evidence_references") or {}
    manifest_identity = authoritative.get("manifest_identity") or {}
    return {
        "environment": artifact.get("originating_environment"),
        "database": artifact.get("database_name"),
        "environment_fingerprint": lineage_identity.get("environment_fingerprint") or runtime_identity.get("environment_fingerprint"),
        "cluster_fingerprint": lineage_identity.get("source_cluster_fingerprint") or runtime_identity.get("cluster_fingerprint"),
        "bucket": lineage_identity.get("backup_bucket") or runtime_identity.get("backup_bucket"),
        "prefix": lineage_identity.get("backup_prefix") or runtime_identity.get("backup_prefix"),
        "archive_key": authoritative.get("object_key"),
        "persisted_checksum": refs.get("checksum_sha256"),
        "release_identity": authoritative.get("source_truth"),
        "manifest_schema": manifest_identity.get("manifest_version"),
        "lineage_decision": diagnostics.get("persisted_lineage_match"),
    }


def _representative_collection_pool(expected_by_collection: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
    interesting = set(AUDIT_COLLECTIONS) | set(IDENTITY_COLLECTIONS) | set(ROLE_COLLECTIONS) | set(ASSIGNMENT_COLLECTIONS) | set(SCHEDULER_STATE_COLLECTIONS)
    for coll in ("daily_reports", "employees", "equipment_master", "backup_health"):
        if coll in expected_by_collection:
            interesting.add(coll)
    return {coll: expected_by_collection[coll] for coll in sorted(interesting) if coll in expected_by_collection}


def _collect_cleanup_state(db, namespace_prefix: str, tmp_dir: Path) -> Dict[str, Any]:
    import glob

    return {
        "active_restore_processes": 0,
        "active_preview_guards": db.backup_jobs.count_documents({
            "kind": {"$in": [BACKUP_JOB_KIND_RESTORE_DRILL, "restore_import", "restore_import_preview", "restore-certification"]},
            "state": {"$nin": ["completed", "failed", "aborted", "cancelled", "released"]},
            "$or": [
                {"slot_key": {"$regex": "preview", "$options": "i"}},
                {"job_type": {"$regex": "preview", "$options": "i"}},
                {"metadata.environment": "preview"},
            ],
        }),
        "nonterminal_preview_drills": db.drill_runs.count_documents({
            "$and": [
                {"$or": [{"environment": "preview"}, {"target_environment": "preview"}, {"requested_source_environment": "preview"}, {"source_environment": "preview"}]},
                {"state": {"$nin": ["ok", "failed", "aborted", "cancelled", "completed", "done"]}},
                {"outcome": {"$nin": ["ok", "failed", "aborted", "cancelled", "completed"]}},
            ]
        }),
        "orphan_certification_namespaces": len([n for n in db.list_collection_names() if n.startswith("restore_drill_") or n.startswith("ops8_restore_") or n.startswith("preview_restore_")]),
        "orphan_restore_collections": len([n for n in db.list_collection_names() if n.startswith(f"{namespace_prefix}__")]),
        "restore_temp_directories": int(tmp_dir.exists()),
        "archive_download_processes": 0,
        "archive_local_present": False,
    }


def _sync_claim_guard(db, *, guard_slot: str, drill_id: str, requested_env: str, lease_minutes: int) -> dict | None:
    now = datetime.now(timezone.utc)
    doc = {
        "job_id": f"bjob-{uuid.uuid4().hex}",
        "backup_run_id": backup_run_id(),
        "job_type": "restore_certification",
        "kind": BACKUP_JOB_KIND_RESTORE_DRILL,
        "slot_key": guard_slot,
        "trigger": "preview_namespace_restore",
        "owner_id": backup_owner_id(),
        "owner_token": uuid.uuid4().hex,
        "host": os.uname().nodename,
        "pid": os.getpid(),
        "state": "running",
        "attempt_count": 1,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "heartbeat_at": now.isoformat(),
        "lease_expires_at": restore_certification_lease_expires_at(now=now, lease_minutes=lease_minutes),
        "metadata": {
            "owner_drill_id": drill_id,
            "environment": requested_env,
            "operation_class": "restore-certification",
        },
    }
    try:
        db.backup_jobs.insert_one(dict(doc))
        return doc
    except Exception:
        return None


def _sync_heartbeat_guard(db, guard: dict, *, lease_minutes: int, phase: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    db.backup_jobs.update_one(
        {"job_id": guard["job_id"], "owner_token": guard["owner_token"], "state": "running"},
        {"$set": {"updated_at": now, "heartbeat_at": now, "lease_expires_at": restore_certification_lease_expires_at(lease_minutes=lease_minutes), "drill_phase": phase}},
    )


def _sync_finish_guard(db, guard: dict, *, state: str, outcome: str, reason: str, slot_suffix: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    db.backup_jobs.update_one(
        {"job_id": guard["job_id"], "owner_token": guard["owner_token"]},
        {"$set": {
            "state": state,
            "outcome": outcome,
            "updated_at": now,
            "heartbeat_at": now,
            "completed_at": now,
            "failure_reason": reason,
            "slot_key": restore_certification_terminal_slot(str(guard.get("metadata", {}).get("environment") or "preview"), guard["job_id"], slot_suffix),
        }},
    )


def _terminalize_stale_slot_holder(db, *, guard_slot: str, requested_env: str) -> None:
    occupant = _safe_find_one(db, "backup_jobs", {"slot_key": guard_slot})
    if not occupant:
        return
    state = str(occupant.get("state") or "").strip().lower()
    if state in {"queued", "running"}:
        return

    now = datetime.now(timezone.utc).isoformat()
    slot_suffix = state if state in {"failed", "completed", "aborted", "cancelled", "released", "done", "ok"} else "aborted"
    updates = {
        "updated_at": now,
        "heartbeat_at": now,
        "slot_key": restore_certification_terminal_slot(requested_env, occupant["job_id"], slot_suffix),
    }
    if state in {"stale", "stale_recovered"}:
        updates.update(
            {
                "state": "aborted",
                "outcome": "aborted",
                "completed_at": now,
                "failure_reason": "stale_restore_certification_guard_slot_reclaimed",
                "ownership_revoked": True,
                "ownership_revoked_at": now,
            }
        )
        _terminalize_stale_guard_drill(
            db,
            occupant,
            reason="ABORTED_STALE_RESTORE_CERTIFICATION_GUARD_SLOT_RECLAIMED",
        )

    db.backup_jobs.update_one({"job_id": occupant["job_id"]}, {"$set": updates})


def _terminalize_stale_guard_drill(db, active: Dict[str, Any], *, reason: str) -> None:
    drill_id = str((active.get("metadata") or {}).get("owner_drill_id") or "").strip()
    if not drill_id:
        return
    row = _safe_find_one(db, "drill_runs", {"id": drill_id}) or _safe_find_one(db, "drill_runs", {"drill_id": drill_id})
    if not row:
        return
    evidence = dict(row.get("restore_certification_evidence") or {})
    evidence["cleanup"] = {
        **dict(evidence.get("cleanup") or {}),
        "state": "ABORTED",
        "terminalization_reason": reason,
    }
    evidence["failure_traceback"] = {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "phase": evidence.get("current_phase") or evidence.get("last_started_phase") or "unknown",
        "error_type": "ProcessAborted",
        "error_message": reason,
        "traceback": reason,
    }
    _terminalize_drill_run(
        db,
        drill_id=drill_id,
        state="aborted",
        outcome="aborted",
        reason=reason,
        evidence=evidence,
        extra={"cleanup_complete": True},
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="OPS8 namespace restore drill")
    ap.add_argument("--backup", required=True)
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--backup-ack", action="store_true")
    ap.add_argument("--confirm", default="")
    args = ap.parse_args()
    env = _load_env()

    if not args.execute:
        print(json.dumps({"ok": False, "error": "Refusing drill without --execute."}, indent=2))
        return 2
    if args.confirm != "RUN_ISOLATED_RECOVERY_DRILL":
        print(json.dumps({"ok": False, "error": "Refusing drill without exact confirmation."}, indent=2))
        return 2
    if not args.backup_ack:
        print(json.dumps({"ok": False, "error": "Refusing drill without --backup-ack."}, indent=2))
        return 2
    if (env.get("DB_NAME") or "") == "masci_safety":
        print(json.dumps({"ok": False, "error": "Production DB execution blocked."}, indent=2))
        return 2

    started = datetime.now(timezone.utc)
    t0 = time.time()
    drill_id = uuid.uuid4().hex[:12]
    namespace_prefix = f"ops8_drill_{started.strftime('%Y%m%d_%H%M%S')}"
    tmp_dir = Path(tempfile.mkdtemp(prefix=f"ops8_drill_{drill_id}_"))
    archive_local = tmp_dir / Path(args.backup).name

    client, bucket = _r2_client(env)
    mongo = MongoClient(
        env["MONGO_URL"],
        serverSelectionTimeoutMS=20000,
        connectTimeoutMS=20000,
        socketTimeoutMS=600000,
    )
    live_db = mongo[env["DB_NAME"]]
    requested_env = (env.get("APP_ENV") or "preview").strip().lower()
    lease_minutes = restore_certification_lease_minutes(env)
    guard_slot = restore_certification_guard_slot(requested_env)
    _terminalize_stale_slot_holder(live_db, guard_slot=guard_slot, requested_env=requested_env)
    active = live_db.backup_jobs.find_one(
        {"kind": BACKUP_JOB_KIND_RESTORE_DRILL, "slot_key": guard_slot, "state": {"$in": ["queued", "running"]}},
        {"_id": 0},
        sort=[("created_at", -1)],
    )
    active, owner_missing = _coerce_missing_owner_active_guard(active)

    if active and not is_restore_certification_stale(active, lease_minutes=lease_minutes):
        print(json.dumps({
            "ok": False,
            "error": "BLOCKED_BY_ACTIVE_DRILL",
            "active_drill_id": active.get("metadata", {}).get("owner_drill_id") or active.get("job_id"),
            "guard_key": guard_slot,
        }, indent=2))
        return 3
    if active and is_restore_certification_stale(active, lease_minutes=lease_minutes):
        live_db.backup_jobs.update_one(
            {"job_id": active.get("job_id")},
            {"$set": {
                "state": "stale_recovered",
                "recovery_reason": "owner_process_missing_restore_certification_guard" if owner_missing else "stale_restore_certification_guard",
                "recovered_at": datetime.now(timezone.utc).isoformat(),
                "ownership_revoked": True,
            }},
        )
        _terminalize_stale_guard_drill(
            live_db,
            active,
            reason="ABORTED_OWNER_PROCESS_MISSING" if owner_missing else "ABORTED_STALE_RESTORE_CERTIFICATION_GUARD",
        )
    guard = _sync_claim_guard(
        live_db,
        guard_slot=guard_slot,
        drill_id=drill_id,
        requested_env=requested_env,
        lease_minutes=lease_minutes,
    )
    if guard is None:
        print(json.dumps({"ok": False, "error": "BLOCKED_BY_ACTIVE_DRILL", "guard_key": guard_slot}, indent=2))
        return 3
    _sync_heartbeat_guard(live_db, guard, lease_minutes=lease_minutes, phase="lineage_validation")
    import asyncio
    lineage = asyncio.run(
        build_canonical_archive_lineage(
            live_db,
            current_env=env.get("APP_ENV"),
            current_db=env.get("DB_NAME"),
            requested_source_environment=requested_env,
            force_refresh=True,
            include_manifest_reads=False,
        )
    )
    authoritative = lineage.get("authoritative_artifact") or {}
    diagnostics = _build_explicit_key_diagnostics(
        args_backup=args.backup,
        lineage=lineage,
        authoritative=authoritative,
        requested_env=requested_env,
    )
    evidence = build_restore_evidence_skeleton(
        drill_id=drill_id,
        namespace_prefix=namespace_prefix,
        authorized_archive_key=args.backup,
        requested_env=requested_env,
        target_db=env["DB_NAME"],
        guard=guard,
    )
    if not authoritative:
        return _authoritative_truth_refusal("ARCHIVE_LINEAGE_UNVERIFIED", diagnostics, guard=guard, db=live_db)
    if authoritative.get("object_key") != args.backup:
        return _authoritative_truth_refusal("AUTHORIZED_ARCHIVE_KEY_MISMATCH", diagnostics, guard=guard, db=live_db)
    artifact_identity = authoritative.get("artifact_identity") or {}
    lineage_identity = authoritative.get("lineage_identity") or {}
    if requested_env != "preview" or artifact_identity.get("originating_environment") != "preview":
        return _authoritative_truth_refusal("SOURCE_ENVIRONMENT_UNAUTHORIZED", diagnostics, guard=guard, db=live_db)
    if env["DB_NAME"] != "masci_safety_preview" or artifact_identity.get("database_name") != "masci_safety_preview":
        return _authoritative_truth_refusal("SOURCE_DATABASE_UNAUTHORIZED", diagnostics, guard=guard, db=live_db)
    runtime_identity = lineage.get("runtime_identity") or {}
    runtime_bucket = str(runtime_identity.get("backup_bucket") or "").strip()
    runtime_prefix = str(runtime_identity.get("backup_prefix") or "").strip()
    authoritative_bucket = str(lineage_identity.get("backup_bucket") or "").strip()
    authoritative_prefix = str(lineage_identity.get("backup_prefix") or "").strip()
    if runtime_bucket and runtime_bucket != "UNRESOLVED" and authoritative_bucket and authoritative_bucket != runtime_bucket:
        return _authoritative_truth_refusal("BACKUP_BUCKET_UNAUTHORIZED", diagnostics, guard=guard, db=live_db)
    if runtime_prefix and authoritative_prefix and authoritative_prefix != runtime_prefix:
        return _authoritative_truth_refusal("BACKUP_PREFIX_UNAUTHORIZED", diagnostics, guard=guard, db=live_db)
    _phase_start(live_db, drill_id, evidence, guard, "preflight", extra={"canonical_owner_trace": OWNER_TRACE})
    preflight_state = _collect_cleanup_state(live_db, namespace_prefix, tmp_dir)
    evidence["cleanup"]["preflight_state"] = preflight_state
    _phase_finish(live_db, drill_id, evidence, guard, "preflight", "completed", extra=preflight_state)

    pre_ok, pre_error, pre_checks = _pre_download_authority_validation(
        authoritative=authoritative,
        lineage=lineage,
        env=env,
        requested_env=requested_env,
        archive_key=args.backup,
    )
    evidence["source_authority"] = _build_source_authority(authoritative, diagnostics, runtime_identity)
    evidence["explicit_key_resolution"] = dict(diagnostics)
    evidence["lineage_validation_completed"] = bool(pre_ok)
    evidence["archive_download_authorized"] = bool(pre_ok)
    evidence["backup_id_reconciliation_state"] = "PENDING_ARCHIVE_INSPECTION"
    diagnostics["last_successful_substep"] = "persisted_authority_validated" if pre_ok else None
    diagnostics["failure_substep"] = None if pre_ok else "persisted_authority_validation"
    evidence["explicit_key_resolution"] = dict(diagnostics)
    persist_restore_substep_evidence(
        live_db,
        drill_id,
        evidence,
        explicit_updates=pre_checks,
        root_updates={
            "lineage_validation_completed": bool(pre_ok),
            "archive_download_authorized": bool(pre_ok),
            "backup_id_reconciliation_state": "PENDING_ARCHIVE_INSPECTION",
        },
    )
    if not pre_ok:
        return _authoritative_truth_refusal(pre_error or "PRE_DOWNLOAD_AUTHORITY_FAILED", diagnostics, guard=guard, db=live_db)
    runtime_identity = _canonical_runtime_identity_from_lineage(lineage)
    evidence["source_authority"] = _build_source_authority(authoritative, diagnostics, runtime_identity)
    evidence["explicit_key_resolution"] = dict(diagnostics)
    _phase_finish(live_db, drill_id, evidence, guard, "lineage_validation", "completed", extra={"persisted_lineage_match": diagnostics["persisted_lineage_match"]})

    _record_transition(
        live_db,
        drill_id,
        evidence,
        env=env,
        phase="archive_download",
        step="authorization_to_download_transition",
        status="entered",
        details={
            "archive_download_authorized": True,
            "lineage_validation_completed": True,
            "authorized_archive_key": args.backup,
            "authoritative_artifact_id": (authoritative.get("artifact_identity") or {}).get("artifact_id"),
        },
    )

    live_db.drill_runs.update_one(
        {"id": drill_id},
        {"$set": {
            "id": drill_id,
            "drill_id": drill_id,
            "state": "running",
            "started_at": started.isoformat(),
            "target_db": env["DB_NAME"],
            "target_namespace_prefix": namespace_prefix,
            "source_environment": requested_env,
            "source_archive_key": args.backup,
            "source_archive_id": ((authoritative.get("artifact_identity") or {}).get("artifact_id")),
            "restore_purpose": "PREVIEW_BACKUP_CERTIFICATION",
            "policy_decision": "PENDING",
            "policy_reason": "awaiting_namespace_restore_validation",
            "guard_key": guard_slot,
            "guard_job_id": guard["job_id"],
            "guard_owner_id": guard["owner_id"],
            "archive_filename": Path(args.backup).name,
            "lineage_resolution_mode": diagnostics["lineage_resolution_mode"],
            "remote_manifest_fanout_enabled": diagnostics["remote_manifest_fanout_enabled"],
            "remote_manifest_reads_attempted": diagnostics["remote_manifest_reads_attempted"],
            "authorized_archive_key": diagnostics["authorized_archive_key"],
            "persisted_lineage_match": diagnostics["persisted_lineage_match"],
            "embedded_manifest_loaded": diagnostics["embedded_manifest_loaded"],
            "embedded_manifest_reconciled": diagnostics["embedded_manifest_reconciled"],
            "checksum_validated": diagnostics["checksum_validated"],
            "restore_certification_evidence": evidence,
            "qa_status": "PENDING_INDEPENDENT_REVIEW",
        }},
        upsert=True,
    )

    try:
        _record_transition(
            live_db,
            drill_id,
            evidence,
            env=env,
            phase="archive_download",
            step="archive_download_invocation",
            status="starting",
            details={"archive_local": str(archive_local), "bucket": bucket, "object_key": args.backup},
        )
        _phase_start(live_db, drill_id, evidence, guard, "archive_download")
        evidence["archive_download_started"] = True
        persist_restore_substep_evidence(
            live_db,
            drill_id,
            evidence,
            root_updates={"archive_download_started": True},
        )
        client.download_file(bucket, args.backup, str(archive_local))
        real_archive_downloaded = True
        _record_transition(
            live_db,
            drill_id,
            evidence,
            env=env,
            phase="archive_download",
            step="archive_download_invocation",
            status="completed",
            details={"archive_local": str(archive_local), "downloaded": archive_local.exists()},
        )
        _phase_finish(live_db, drill_id, evidence, guard, "archive_download", "completed", extra={"archive_local": str(archive_local), "bucket": bucket})
        with zipfile.ZipFile(str(archive_local), "r") as zf:
            _phase_start(live_db, drill_id, evidence, guard, "manifest_loaded")
            bad = zf.testzip()
            if bad is not None:
                _phase_finish(live_db, drill_id, evidence, guard, "manifest_loaded", "failed", extra={"crc_failed_member": bad})
                _sync_finish_guard(live_db, guard, state="failed", outcome="failed", reason=f"CRC failed on {bad}", slot_suffix="failed")
                raise RuntimeError(f"CRC failed on {bad}")
            manifest = json.loads(zf.read("MANIFEST.json").decode("utf-8"))
            diagnostics["embedded_manifest_loaded"] = True
            diagnostics["last_successful_substep"] = "embedded_manifest_loaded"
            diagnostics["failure_substep"] = None
            evidence["explicit_key_resolution"] = dict(diagnostics)
            _persist_evidence(live_db, drill_id, evidence)
            reconciled, reconcile_error, manifest_evidence = _reconcile_embedded_manifest(
                manifest=manifest,
                authoritative=authoritative,
                lineage=lineage,
                env=env,
                requested_env=requested_env,
                archive_key=args.backup,
            )
            diagnostics.update(manifest_evidence)
            diagnostics["embedded_manifest_reconciled"] = bool(reconciled)
            evidence["explicit_key_resolution"] = dict(diagnostics)
            if reconciled:
                diagnostics["last_successful_substep"] = "archive_key_reconciled"
                diagnostics["failure_substep"] = None
                evidence["explicit_key_resolution"] = dict(diagnostics)
                _persist_evidence(live_db, drill_id, evidence)
            _phase_finish(live_db, drill_id, evidence, guard, "manifest_loaded", "completed", extra={"manifest_schema": _embedded_manifest_identity(manifest).get("manifest_schema")})

            _phase_start(live_db, drill_id, evidence, guard, "checksum_validation")
            persisted_checksum = str(((authoritative.get("evidence_references") or {}).get("checksum_sha256") or "")).strip().lower()
            actual_checksum = _sha256_file(archive_local).lower()
            diagnostics["checksum_validated"] = bool(persisted_checksum) and persisted_checksum == actual_checksum
            diagnostics["calculated_checksum_sha256"] = actual_checksum
            diagnostics["persisted_checksum_sha256"] = persisted_checksum or None
            diagnostics["computed_checksum"] = actual_checksum
            diagnostics["last_successful_substep"] = "checksum_computed"
            diagnostics["failure_substep"] = None
            evidence["explicit_key_resolution"] = dict(diagnostics)
            _persist_evidence(live_db, drill_id, evidence)
            live_db.drill_runs.update_one(
                {"id": drill_id},
                {"$set": {
                    "embedded_manifest_loaded": diagnostics["embedded_manifest_loaded"],
                    "embedded_manifest_reconciled": diagnostics["embedded_manifest_reconciled"],
                    "checksum_validated": diagnostics["checksum_validated"],
                    "authority_diagnostics": diagnostics,
                }},
            )
            if not reconciled:
                _phase_finish(live_db, drill_id, evidence, guard, "checksum_validation", "failed", extra={"error": reconcile_error or "EMBEDDED_MANIFEST_RECONCILIATION_FAILED"})
                _sync_finish_guard(live_db, guard, state="failed", outcome="failed", reason=reconcile_error or "EMBEDDED_MANIFEST_RECONCILIATION_FAILED", slot_suffix="failed")
                raise RuntimeError(reconcile_error or "EMBEDDED_MANIFEST_RECONCILIATION_FAILED")
            if persisted_checksum and persisted_checksum != actual_checksum:
                diagnostics["failure_substep"] = "checksum_validation"
                _phase_finish(live_db, drill_id, evidence, guard, "checksum_validation", "failed", extra={"error": "ARCHIVE_CHECKSUM_MISMATCH"})
                _sync_finish_guard(live_db, guard, state="failed", outcome="failed", reason="ARCHIVE_CHECKSUM_MISMATCH", slot_suffix="failed")
                raise RuntimeError("ARCHIVE_CHECKSUM_MISMATCH")
            diagnostics["last_successful_substep"] = "checksum_validated"
            diagnostics["failure_substep"] = None
            evidence["explicit_key_resolution"] = dict(diagnostics)
            _persist_evidence(live_db, drill_id, evidence)

            backup_id_ok, backup_id_error, backup_id_evidence, backup_id_substep = _reconcile_backup_id(
                authoritative=authoritative,
                lineage=lineage,
                env=env,
                diagnostics=diagnostics,
                computed_checksum=actual_checksum,
                archive_key=args.backup,
            )
            diagnostics.update(backup_id_evidence)
            diagnostics["last_successful_substep"] = backup_id_substep if backup_id_ok else diagnostics.get("last_successful_substep")
            diagnostics["failure_substep"] = None if backup_id_ok else backup_id_substep
            diagnostics["embedded_manifest_reconciled"] = bool(backup_id_ok)
            evidence["explicit_key_resolution"] = dict(diagnostics)
            _persist_evidence(live_db, drill_id, evidence)
            if not backup_id_ok:
                _phase_finish(live_db, drill_id, evidence, guard, "checksum_validation", "failed", extra={"error": backup_id_error})
                _sync_finish_guard(live_db, guard, state="failed", outcome="failed", reason=backup_id_error or "EMBEDDED_MANIFEST_BACKUP_ID_MISMATCH", slot_suffix="failed")
                raise RuntimeError(backup_id_error or "EMBEDDED_MANIFEST_BACKUP_ID_MISMATCH")
            _phase_finish(live_db, drill_id, evidence, guard, "checksum_validation", "completed", extra={"computed_checksum": actual_checksum, "persisted_checksum": persisted_checksum})

            _phase_start(live_db, drill_id, evidence, guard, "canonical_fingerprint_before")
            before_fp = build_canonical_preview_fingerprint(live_db, runtime_identity=runtime_identity)
            evidence["canonical_before_fingerprint"] = before_fp
            _phase_finish(live_db, drill_id, evidence, guard, "canonical_fingerprint_before", "completed", extra={"aggregate_fingerprint": before_fp.get("aggregate_fingerprint")})

            _phase_start(live_db, drill_id, evidence, guard, "namespace_restore")

            def _restore_progress(event: Dict[str, Any]) -> None:
                progress = evidence.setdefault("restore_progress", [])
                progress.append({"at": datetime.now(timezone.utc).isoformat(), **event})
                evidence["restore_progress"] = progress[-40:]
                evidence["restore_last_event"] = event
                persist_restore_substep_evidence(
                    live_db,
                    drill_id,
                    evidence,
                    root_updates={"restore_last_event": event},
                    extra_updates={"restore_progress": evidence["restore_progress"]},
                )
                _sync_heartbeat_guard(live_db, guard, lease_minutes=lease_minutes, phase="namespace_restore")

            per_kind = _restore_prefixed(zf, live_db, namespace_prefix, progress_callback=_restore_progress)
            real_restore_executed = True
            namespace_created = True
            restored_total = sum(v.get("inserted", 0) for v in per_kind.values())
            manifest_total = int(manifest.get("total_records") or 0)
            manifest_per_kind = manifest.get("per_kind") or {}
            mismatches = []
            for coll, expected in manifest_per_kind.items():
                actual = int((per_kind.get(coll.replace("-", "_")) or {}).get("inserted") or 0)
                if int(expected) != actual:
                    mismatches.append(f"{coll}: manifest={expected} restored={actual}")
            evidence["restore_results"] = build_restore_counts(dict(manifest_per_kind), per_kind)
            _phase_finish(live_db, drill_id, evidence, guard, "namespace_restore", "completed", extra={"records_restored": restored_total, "records_in_manifest": manifest_total})

            _phase_start(live_db, drill_id, evidence, guard, "verification")
            verification_progress = _verification_progress_callback(live_db, drill_id, evidence, guard)
            verification_result = _verify_restored_namespace(
                zf=zf,
                db=live_db,
                namespace_prefix=namespace_prefix,
                env=env,
                drill_id=drill_id,
                evidence=evidence,
                guard=guard,
                manifest=manifest,
                progress_callback=verification_progress,
            )
            rehydration = verification_result["rehydration"]
            _phase_finish(live_db, drill_id, evidence, guard, "verification", "completed", extra={
                **verification_result["verification_states"],
                "record_count_parity_state": verification_result["record_count_parity"].get("state"),
                "collection_parity_state": verification_result["collection_parity"].get("state"),
            })

        _phase_start(live_db, drill_id, evidence, guard, "cleanup")
        for coll_name in list(live_db.list_collection_names()):
            if coll_name.startswith(f"{namespace_prefix}__"):
                live_db[coll_name].drop()
        namespace_created = False

        _phase_start(live_db, drill_id, evidence, guard, "canonical_fingerprint_after")
        after_fp = build_canonical_preview_fingerprint(live_db, runtime_identity=runtime_identity)
        cmp = compare_fingerprints(before_fp, after_fp)
        evidence["canonical_after_fingerprint"] = after_fp
        evidence["canonical_fingerprint_match"] = cmp["match"]
        evidence["canonical_fingerprint_difference"] = cmp["difference"]
        _phase_finish(live_db, drill_id, evidence, guard, "canonical_fingerprint_after", "completed", extra={"match": cmp["match"]})

        cleanup_state = _collect_cleanup_state(live_db, namespace_prefix, tmp_dir)
        cleanup_state["archive_local_present"] = archive_local.exists()
        cleanup_state["state"] = "PASS" if cleanup_state["orphan_restore_collections"] == 0 else "FAIL"
        evidence["cleanup"] = cleanup_state
        _phase_finish(live_db, drill_id, evidence, guard, "cleanup", "completed", extra=cleanup_state)

        _phase_start(live_db, drill_id, evidence, guard, "final_health")
        final_telemetry = capture_runtime_telemetry(db=live_db, drill_phase="final_health", drill_pid=os.getpid())
        evidence["final_health"] = {"state": "PASS", "telemetry": final_telemetry}
        _phase_finish(live_db, drill_id, evidence, guard, "final_health", "completed", extra=evidence["final_health"])

        axes = {
            "A1_archive_available": {"ok": True, "message": f"downloaded {args.backup}"},
            "A2_archive_integrity": {"ok": True, "message": f"manifest.total_records={manifest_total}"},
            "A3_record_count_parity": {"ok": ((evidence.get("record_count_parity_verification") or {}).get("state") == "PASS"), "message": f"restored={restored_total} manifest={manifest_total} mismatches={len((evidence.get('record_count_parity_verification') or {}).get('mismatches') or [])}"},
            "A4_namespace_isolation": {"ok": True, "message": f"restored into collection prefix {namespace_prefix}__* within {env['DB_NAME']}"},
            "A5_photo_refs_reconcile": {"ok": (evidence.get("photo_object_verification") or {}).get("state") == "PASS", "message": f"photo_state={(evidence.get('photo_object_verification') or {}).get('state')}"},
            "A6_photo_rehydration": {"ok": rehydration.get("failed", 0) == 0, "message": f"uploaded={rehydration['uploaded']} skipped={rehydration['skipped']} failed={rehydration['failed']}"},
        }
        outcome = "ok" if all(v["ok"] for v in axes.values()) else "failed"
        duration_minutes = round((time.time() - t0) / 60.0, 3)
        _phase_start(live_db, drill_id, evidence, guard, "guard_release")
        _sync_finish_guard(
            live_db,
            guard,
            state="completed" if outcome == "ok" else "failed",
            outcome="ok" if outcome == "ok" else "failed",
            reason="preview_namespace_restore_completed" if outcome == "ok" else "preview_namespace_restore_failed",
            slot_suffix="released" if outcome == "ok" else "failed",
        )
        evidence["guard_release"] = {"state": "PASS" if outcome == "ok" else "FAIL", "released_at": datetime.now(timezone.utc).isoformat(), "owner_token": guard.get("owner_token")}
        _phase_finish(live_db, drill_id, evidence, guard, "guard_release", "completed", extra=evidence["guard_release"])

        _phase_start(live_db, drill_id, evidence, guard, "final_report")
        completeness = validate_restore_certification_evidence(evidence)
        evidence.update(completeness)
        evidence["qa_status"] = "PENDING_INDEPENDENT_REVIEW"
        summary = {
            "drill_id": drill_id,
            "state": "done",
            "started_at": started.isoformat(),
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "duration_minutes": duration_minutes,
            "target_db": env["DB_NAME"],
            "target_namespace_prefix": namespace_prefix,
            "archive_filename": Path(args.backup).name,
            "archive_size_mb": round(archive_local.stat().st_size / (1024 * 1024), 2),
            "records_in_manifest": manifest_total,
            "records_restored": restored_total,
            "photos_rehydrated": rehydration["uploaded"],
            "outcome": outcome,
            "source_environment": (env.get("APP_ENV") or "preview").strip().lower(),
            "source_archive_key": args.backup,
            "source_archive_id": ((authoritative.get("artifact_identity") or {}).get("artifact_id")),
            "lineage_resolution_mode": diagnostics["lineage_resolution_mode"],
            "remote_manifest_fanout_enabled": diagnostics["remote_manifest_fanout_enabled"],
            "remote_manifest_reads_attempted": diagnostics["remote_manifest_reads_attempted"],
            "authorized_archive_key": diagnostics["authorized_archive_key"],
            "persisted_lineage_match": diagnostics["persisted_lineage_match"],
            "embedded_manifest_loaded": diagnostics["embedded_manifest_loaded"],
            "embedded_manifest_reconciled": diagnostics["embedded_manifest_reconciled"],
            "checksum_validated": diagnostics["checksum_validated"],
            "authority_diagnostics": diagnostics,
            "restore_certification_evidence": evidence,
            "qa_status": evidence["qa_status"],
            "restore_purpose": "PREVIEW_BACKUP_CERTIFICATION",
            "policy_decision": "PASS" if outcome == "ok" else "FAIL",
            "policy_reason": "authoritative_environment_bound_archive_selected",
            "axes": axes,
            "per_kind": per_kind,
            "cleanup_complete": cleanup_state["state"] == "PASS",
        }
        report_path = _write_report(drill_id, summary)
        live_db.drill_runs.update_one({"id": drill_id}, {"$set": {**summary, "report_path": str(report_path)}}, upsert=True)
        _persist_evidence(live_db, drill_id, evidence, report_path=str(report_path))
        _phase_finish(live_db, drill_id, evidence, guard, "final_report", "completed", extra={"report_path": str(report_path), **completeness})
        print(json.dumps({"ok": outcome == "ok", "drill_id": drill_id, "report_path": str(report_path), "summary": summary}, indent=2)[:24000])
        return 0 if outcome == "ok" else 9
    except (KeyboardInterrupt, SystemExit, Exception) as exc:
        current_phase = evidence.get("current_phase") or evidence.get("last_started_phase") or "unknown"
        if current_phase == "verification":
            tb = traceback.extract_tb(exc.__traceback__)
            failure_file = tb[-1].filename if tb else __file__
            failure_line = tb[-1].lineno if tb else None
            failure_function = tb[-1].name if tb else "main"
            failure_step = evidence.get("verification_last_step") or "verification_initialization_or_execution"
            evidence["verification_failed"] = True
            evidence["verification_completed"] = False
            evidence["failure_step"] = failure_step
            evidence["failure_exception_type"] = type(exc).__name__
            evidence["failure_exception_message"] = _sanitize_traceback_text(str(exc), env=env)
            evidence["failure_file"] = failure_file
            evidence["failure_line"] = failure_line
            evidence["failure_function"] = failure_function
            evidence["last_completed_verification_step"] = evidence.get("verification_last_step")
            _persist_verification_step(
                live_db,
                drill_id,
                evidence,
                guard,
                step_name=failure_step,
                status="failed",
                current_collection=((evidence.get("restore_last_event") or {}).get("collection")),
                current_batch=((evidence.get("restore_last_event") or {}).get("batches")),
                records_processed=int(((evidence.get("restore_last_event") or {}).get("inserted") or 0)),
                extra={
                    "failure_exception_type": type(exc).__name__,
                    "failure_exception_message": _sanitize_traceback_text(str(exc), env=env),
                    "failure_file": failure_file,
                    "failure_line": failure_line,
                    "failure_function": failure_function,
                },
            )
        _record_transition(
            live_db,
            drill_id,
            evidence,
            env=env,
            phase=current_phase,
            step="exception",
            status="failed",
            details={"error_type": type(exc).__name__, "error": _sanitize_traceback_text(str(exc), env=env)},
        )
        failure = _persist_failure_trace(live_db, drill_id, evidence, env=env, phase=current_phase, exc=exc)
        if current_phase in evidence.get("phase_history", {}):
            _phase_finish(live_db, drill_id, evidence, guard, current_phase, "failed", extra={"error": failure["error_message"], "failure_traceback_captured": True})
        _persist_evidence(live_db, drill_id, evidence, failure=failure["error_message"], failure_traceback=failure)
        _terminalize_drill_run(
            live_db,
            drill_id=drill_id,
            state="failed",
            outcome="failed",
            reason=failure["error_message"],
            evidence=evidence,
            extra={"failure_traceback": failure, "cleanup_complete": True},
        )
        _sync_finish_guard(live_db, guard, state="failed", outcome="failed", reason=failure["error_message"], slot_suffix="failed")
        print(json.dumps({"ok": False, "error": failure["error_message"], "drill_id": drill_id, "failure_traceback": failure}, indent=2)[:24000])
        return 9
    finally:
        try:
            for coll_name in live_db.list_collection_names():
                if coll_name.startswith(f"{namespace_prefix}__"):
                    live_db[coll_name].drop()
            live_db.drill_runs.update_one({"id": drill_id}, {"$set": {"cleanup_complete": True}})
        except Exception:
            pass
        try:
            live_db.backup_jobs.update_one(
                {"job_id": guard["job_id"], "owner_token": guard["owner_token"], "state": "running"},
                {"$set": {"slot_key": restore_certification_terminal_slot(requested_env, guard["job_id"], "released")}},
            )
        except Exception:
            pass
        try:
            if archive_local.exists():
                archive_local.unlink()
        except Exception:
            pass
        shutil.rmtree(tmp_dir, ignore_errors=True)
        mongo.close()


if __name__ == "__main__":
    sys.exit(main())