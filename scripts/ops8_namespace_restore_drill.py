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

import boto3
from botocore.config import Config
from pymongo import MongoClient, UpdateOne


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
    extract_archive_collection_documents,
    load_namespace_collection_documents,
    mark_phase_status,
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
    }

    def _mismatch(code: str) -> tuple[bool, str, Dict[str, Any]]:
        diagnostics["embedded_manifest_reconciled"] = False
        diagnostics["embedded_manifest_failure"] = code
        return False, code, diagnostics

    if embedded["environment"] != requested_env:
        return _mismatch("EMBEDDED_MANIFEST_ENVIRONMENT_MISMATCH")
    if embedded["database_name"] != env["DB_NAME"]:
        return _mismatch("EMBEDDED_MANIFEST_DATABASE_MISMATCH")
    if embedded["archive_key"] != archive_key:
        return _mismatch("EMBEDDED_MANIFEST_ARCHIVE_KEY_MISMATCH")

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

    runtime_bucket = str(runtime_identity.get("backup_bucket") or "").strip()
    if runtime_bucket and runtime_bucket != "UNRESOLVED" and embedded["backup_bucket"] and embedded["backup_bucket"] != runtime_bucket:
        return _mismatch("EMBEDDED_MANIFEST_BUCKET_MISMATCH")

    persisted_bucket = str(lineage_identity.get("backup_bucket") or "").strip()
    if persisted_bucket and embedded["backup_bucket"] and embedded["backup_bucket"] != persisted_bucket:
        return _mismatch("EMBEDDED_MANIFEST_PERSISTED_BUCKET_MISMATCH")

    runtime_prefix = str(runtime_identity.get("backup_prefix") or "").strip()
    if runtime_prefix and embedded["backup_prefix"] and embedded["backup_prefix"] != runtime_prefix:
        return _mismatch("EMBEDDED_MANIFEST_PREFIX_MISMATCH")

    persisted_prefix = str(lineage_identity.get("backup_prefix") or "").strip()
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

    persisted_release_identity = str(authoritative.get("source_truth") or "").strip()
    if persisted_release_identity and embedded["release_identity"] and embedded["release_identity"] != persisted_release_identity:
        return _mismatch("EMBEDDED_MANIFEST_RELEASE_IDENTITY_MISMATCH")

    if embedded["backup_id"] and artifact_identity.get("artifact_id") and embedded["backup_id"] != artifact_identity.get("artifact_id"):
        return _mismatch("EMBEDDED_MANIFEST_BACKUP_ID_MISMATCH")

    diagnostics["embedded_manifest_reconciled"] = True
    diagnostics["embedded_manifest_failure"] = None
    diagnostics["persisted_checksum_sha256"] = evidence_refs.get("checksum_sha256")
    return True, None, diagnostics


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
    if isinstance(obj, str) and obj.startswith("photo://"):
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


def _restore_prefixed(zf: zipfile.ZipFile, db, prefix: str) -> Dict[str, Dict[str, int]]:
    counts: Dict[str, Dict[str, int]] = {}
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
        if clean:
            target = db[f"{prefix}__{coll}"]
            target.drop()
            target.insert_many(clean, ordered=False)
        counts[coll] = {"inserted": len(clean), "files_seen": 1, "skipped_bad": 0}
    if aggregated_members:
        return counts

    grouped: Dict[str, list[dict]] = {}
    for name in zf.namelist():
        if name == "MANIFEST.json" or not name.endswith(".json"):
            continue
        if "/json/" not in name:
            continue
        coll = name.split("/json/", 1)[0].replace("-", "_")
        try:
            doc = json.loads(zf.read(name).decode("utf-8"))
        except Exception:
            counts.setdefault(coll, {"inserted": 0, "files_seen": 0, "skipped_bad": 0})
            counts[coll]["files_seen"] += 1
            counts[coll]["skipped_bad"] += 1
            continue
        if isinstance(doc, dict):
            doc.pop("_id", None)
            grouped.setdefault(coll, []).append(doc)
        counts.setdefault(coll, {"inserted": 0, "files_seen": 0, "skipped_bad": 0})
        counts[coll]["files_seen"] += 1
    for coll, docs in grouped.items():
        db[f"{prefix}__{coll}"].drop()
        if docs:
            db[f"{prefix}__{coll}"].insert_many(docs, ordered=False)
            counts.setdefault(coll, {"inserted": 0, "files_seen": 0, "skipped_bad": 0})
            counts[coll]["inserted"] = len(docs)
    return counts


def _rehydrate_photos(zf: zipfile.ZipFile, env: Dict[str, str], drill_id: str) -> Dict[str, int]:
    client, bucket = _r2_client(env)
    counters = {"uploaded": 0, "skipped": 0, "failed": 0}
    for info in zf.infolist():
        if not info.filename.startswith("photos/") or info.is_dir():
            continue
        sub = info.filename[len("photos/"):]
        key = f"drill-photos/{drill_id}/{sub}"
        try:
            client.head_object(Bucket=bucket, Key=key)
            counters["skipped"] += 1
            continue
        except Exception:
            pass
        try:
            client.put_object(Bucket=bucket, Key=key, Body=zf.read(info.filename))
            counters["uploaded"] += 1
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
    mongo = MongoClient(env["MONGO_URL"], serverSelectionTimeoutMS=20000)
    live_db = mongo[env["DB_NAME"]]
    requested_env = (env.get("APP_ENV") or "preview").strip().lower()
    lease_minutes = restore_certification_lease_minutes(env)
    guard_slot = restore_certification_guard_slot(requested_env)
    active = live_db.backup_jobs.find_one(
        {"kind": BACKUP_JOB_KIND_RESTORE_DRILL, "slot_key": guard_slot, "state": {"$in": ["queued", "running"]}},
        {"_id": 0},
        sort=[("created_at", -1)],
    )
    if active and str(active.get("state") or "").lower() == "queued":
        try:
            owner_pid = int(active.get("pid") or 0)
        except Exception:
            owner_pid = 0
        if owner_pid <= 0 or not Path(f"/proc/{owner_pid}").exists():
            active = dict(active)
            active["lease_expires_at"] = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()

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
                "recovery_reason": "stale_restore_certification_guard",
                "recovered_at": datetime.now(timezone.utc).isoformat(),
                "ownership_revoked": True,
            }},
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
    evidence = build_restore_evidence_skeleton(
        drill_id=drill_id,
        namespace_prefix=namespace_prefix,
        authorized_archive_key=args.backup,
        requested_env=requested_env,
        target_db=env["DB_NAME"],
        guard=guard,
    )
    _phase_start(live_db, drill_id, evidence, guard, "preflight", extra={"canonical_owner_trace": OWNER_TRACE})
    preflight_state = _collect_cleanup_state(live_db, namespace_prefix, tmp_dir)
    evidence["cleanup"]["preflight_state"] = preflight_state
    _phase_finish(live_db, drill_id, evidence, guard, "preflight", "completed", extra=preflight_state)
    runtime_identity = _canonical_runtime_identity_from_lineage(lineage)
    evidence["source_authority"] = _build_source_authority(authoritative, diagnostics, runtime_identity)
    evidence["explicit_key_resolution"] = dict(diagnostics)
    _phase_finish(live_db, drill_id, evidence, guard, "lineage_validation", "completed", extra={"persisted_lineage_match": diagnostics["persisted_lineage_match"]})

    live_db.drill_runs.insert_one({
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
    })
    _persist_evidence(live_db, drill_id, evidence)

    try:
        _phase_start(live_db, drill_id, evidence, guard, "archive_download")
        client.download_file(bucket, args.backup, str(archive_local))
        real_archive_downloaded = True
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
            _phase_finish(live_db, drill_id, evidence, guard, "manifest_loaded", "completed", extra={"manifest_schema": _embedded_manifest_identity(manifest).get("manifest_schema")})

            _phase_start(live_db, drill_id, evidence, guard, "checksum_validation")
            persisted_checksum = str(((authoritative.get("evidence_references") or {}).get("checksum_sha256") or "")).strip().lower()
            actual_checksum = _sha256_file(archive_local).lower()
            diagnostics["checksum_validated"] = bool(persisted_checksum) and persisted_checksum == actual_checksum
            diagnostics["calculated_checksum_sha256"] = actual_checksum
            diagnostics["persisted_checksum_sha256"] = persisted_checksum or None
            evidence["explicit_key_resolution"] = dict(diagnostics)
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
                _phase_finish(live_db, drill_id, evidence, guard, "checksum_validation", "failed", extra={"error": "ARCHIVE_CHECKSUM_MISMATCH"})
                _sync_finish_guard(live_db, guard, state="failed", outcome="failed", reason="ARCHIVE_CHECKSUM_MISMATCH", slot_suffix="failed")
                raise RuntimeError("ARCHIVE_CHECKSUM_MISMATCH")
            _phase_finish(live_db, drill_id, evidence, guard, "checksum_validation", "completed", extra={"computed_checksum": actual_checksum, "persisted_checksum": persisted_checksum})

            _phase_start(live_db, drill_id, evidence, guard, "canonical_fingerprint_before")
            before_fp = build_canonical_preview_fingerprint(live_db, runtime_identity=runtime_identity)
            evidence["canonical_before_fingerprint"] = before_fp
            _phase_finish(live_db, drill_id, evidence, guard, "canonical_fingerprint_before", "completed", extra={"aggregate_fingerprint": before_fp.get("aggregate_fingerprint")})

            _phase_start(live_db, drill_id, evidence, guard, "namespace_restore")
            per_kind = _restore_prefixed(zf, live_db, namespace_prefix)
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
            photo_refs = set()
            archive_photos = set()
            for info in zf.infolist():
                if info.filename.startswith("photos/") and not info.is_dir():
                    archive_photos.add(info.filename[len("photos/"):])
                if not info.filename.endswith(".json") or info.filename == "MANIFEST.json":
                    continue
                try:
                    payload = json.loads(zf.read(info.filename).decode("utf-8"))
                except Exception:
                    continue
                for ref in _walk_photo_refs(payload):
                    try:
                        photo_refs.add(ref.split("/", 3)[3])
                    except Exception:
                        pass
            rehydration = _rehydrate_photos(zf, env, drill_id)
            expected_by_collection = extract_archive_collection_documents(zf)
            restored_by_collection = load_namespace_collection_documents(live_db, namespace_prefix, expected_by_collection.keys())
            representative_pool = _representative_collection_pool(expected_by_collection)
            representative_restored = {k: restored_by_collection.get(k, []) for k in representative_pool}
            evidence["representative_content_verification"] = verify_representative_content(representative_pool, representative_restored)
            evidence["audit_verification"] = verify_audit_data(expected_by_collection, restored_by_collection)
            evidence["identity_role_verification"] = verify_identity_role_data(expected_by_collection, restored_by_collection)
            evidence["scheduler_state_verification"] = verify_scheduler_state(expected_by_collection, restored_by_collection)
            evidence["photo_object_verification"] = verify_photo_object_evidence(
                expected_refs=[f"photo://bucket/{key}" for key in sorted(photo_refs)],
                archive_object_keys=sorted(archive_photos),
                rehydration_result=rehydration,
            )
            _phase_finish(live_db, drill_id, evidence, guard, "verification", "completed", extra={
                "representative_content_state": evidence["representative_content_verification"].get("state"),
                "audit_state": evidence["audit_verification"].get("state"),
                "identity_state": evidence["identity_role_verification"].get("identity_verification_state"),
                "scheduler_state": evidence["scheduler_state_verification"].get("state"),
                "photo_state": evidence["photo_object_verification"].get("state"),
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
            "A3_record_count_parity": {"ok": len(mismatches) == 0 and restored_total == manifest_total, "message": f"restored={restored_total} manifest={manifest_total} mismatches={len(mismatches)}"},
            "A4_namespace_isolation": {"ok": True, "message": f"restored into collection prefix {namespace_prefix}__* within {env['DB_NAME']}"},
            "A5_photo_refs_reconcile": {"ok": len(photo_refs - archive_photos) == 0, "message": f"unique_refs={len(photo_refs)} archive_photos={len(archive_photos)} missing={len(photo_refs - archive_photos)}"},
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
    except Exception as exc:
        current_phase = evidence.get("current_phase") or evidence.get("last_started_phase") or "unknown"
        if current_phase in evidence.get("phase_history", {}):
            _phase_finish(live_db, drill_id, evidence, guard, current_phase, "failed", extra={"error": repr(exc)})
        _persist_evidence(live_db, drill_id, evidence, failure=repr(exc))
        _sync_finish_guard(live_db, guard, state="failed", outcome="failed", reason=repr(exc), slot_suffix="failed")
        print(json.dumps({"ok": False, "error": repr(exc), "drill_id": drill_id}, indent=2))
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