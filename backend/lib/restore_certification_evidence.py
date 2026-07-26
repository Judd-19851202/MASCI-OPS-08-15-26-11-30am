from __future__ import annotations

import hashlib
import json
import os
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    import psutil  # type: ignore
except Exception:  # pragma: no cover
    psutil = None  # type: ignore

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # type: ignore

EVIDENCE_SCHEMA_VERSION = "ops8-restore-certification-evidence-v1"
FINGERPRINT_SCHEMA_VERSION = "ops8-canonical-preview-fingerprint-v1"
QA_REVIEW_SCHEMA_VERSION = "ops8-restore-certification-qa-v1"
REPRESENTATIVE_SAMPLE_SIZE = 5

PHASE_SEQUENCE = [
    "preflight",
    "lineage_validation",
    "archive_download",
    "manifest_loaded",
    "checksum_validation",
    "canonical_fingerprint_before",
    "namespace_restore",
    "verification",
    "canonical_fingerprint_after",
    "cleanup",
    "final_health",
    "guard_release",
    "final_report",
]

FINGERPRINT_EXCLUSION_RULES: Dict[str, Dict[str, str]] = {
    "system.*": {
        "reason": "MongoDB internal system collection",
        "owner": "mongodb",
    },
    "backup_jobs": {
        "reason": "restore-certification guard and backup job ledger mutated by drill execution",
        "owner": "bcss_backup_job_execution",
    },
    "drill_runs": {
        "reason": "restore drill evidence ledger mutated by drill execution",
        "owner": "bcss_restore_drill_evidence",
    },
    "health_monitor_runs": {
        "reason": "regenerable synthetic health probe history",
        "owner": "backup-platform",
    },
    "runtime_incident_forensics": {
        "reason": "runtime incident telemetry may change independently of restore content",
        "owner": "runtime-reliability",
    },
    "runtime_boot_markers": {
        "reason": "runtime boot markers change on process restart",
        "owner": "runtime-reliability",
    },
    "scheduler_locks": {
        "reason": "scheduler singleton locks are mutable runtime lease state",
        "owner": "bcss_backup_slot_execution",
    },
    "scheduler_runs": {
        "reason": "scheduler execution ledger is mutable runtime state",
        "owner": "bcss_backup_slot_execution",
    },
    "usage_events": {
        "reason": "regenerable API telemetry",
        "owner": "backup-platform",
    },
    "job_photo_thumb_cache": {
        "reason": "regenerable derivative photo cache",
        "owner": "backup-platform",
    },
    "backup_integrity_jobs": {
        "reason": "regenerable operator integrity job ledger",
        "owner": "backup-platform",
    },
}

RESTORE_NAMESPACE_PREFIXES = (
    "ops8_drill_",
    "restore_drill_",
    "preview_restore_",
    "ops8_restore_",
)

AUDIT_COLLECTIONS = (
    "audit_events",
    "admin_audit",
    "admin_audit_log",
    "mfa_audit_events",
)
IDENTITY_COLLECTIONS = (
    "user_directory",
    "users",
    "hr_users",
    "shop_users",
    "pm_users",
    "project_managers",
)
ROLE_COLLECTIONS = ("role_templates",)
ASSIGNMENT_COLLECTIONS = ("project_team_assignments",)
SCHEDULER_STATE_COLLECTIONS = (
    "scheduler_locks",
    "scheduler_runs",
    "backup_jobs",
)

OWNER_TRACE = {
    "deterministic_database_fingerprinting": {
        "owner": "backend/lib/restore_certification_evidence.py",
        "reuses": [
            "backend/lib/runtime_identity.py",
            "backend/server.py BACKUP_EXPLICIT_EXCLUSIONS semantics",
            "bcss_restore_drill_evidence",
        ],
    },
    "collection_inventory_and_counts": {
        "owner": "backend/lib/restore_certification_evidence.py",
        "reuses": ["backend/server.py complete-archive manifest inventory contract"],
    },
    "representative_record_sampling": {
        "owner": "backend/lib/restore_certification_evidence.py",
        "reuses": ["drill archive JSON payloads", "restored namespace collections"],
    },
    "audit_collection_identification": {
        "owner": "backend/lib/restore_certification_evidence.py",
        "reuses": ["backend/ops_manual.py", "backend/routes/* audit_events/admin_audit writers"],
    },
    "identity_role_collection_identification": {
        "owner": "backend/lib/restore_certification_evidence.py",
        "reuses": ["backend/ops_manual.py", "backend/routes/operations_actions/api.py"],
    },
    "scheduler_state_identification": {
        "owner": "backend/lib/restore_certification_evidence.py",
        "reuses": ["backend/lib/scheduler_runs.py", "backend/lib/backup_runtime.py", "backend/routes/recovery_dashboard.py"],
    },
    "health_and_runtime_telemetry": {
        "owner": "backend/lib/restore_certification_evidence.py",
        "reuses": ["backend/lib/runtime_reliability.py", "runtime_boot_markers", "local health endpoints"],
    },
    "drill_evidence_persistence": {
        "owner": "/app/scripts/ops8_namespace_restore_drill.py",
        "reuses": ["drill_runs", "backup_jobs"],
    },
    "independent_verification_review": {
        "owner": "/app/scripts/ops8_restore_drill_qa_review.py",
        "reuses": ["backend/lib/restore_certification_evidence.py review helpers"],
    },
}


def canonical_owner_trace() -> Dict[str, Any]:
    return dict(OWNER_TRACE)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_scalar(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat() if value.tzinfo else value.replace(tzinfo=timezone.utc).isoformat()
    if isinstance(value, bytes):
        return {"$bytes_hex": value.hex()}
    return value


def canonicalize_for_fingerprint(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): canonicalize_for_fingerprint(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, list):
        return [canonicalize_for_fingerprint(v) for v in value]
    if isinstance(value, tuple):
        return [canonicalize_for_fingerprint(v) for v in value]
    if isinstance(value, set):
        return sorted(canonicalize_for_fingerprint(v) for v in value)
    if hasattr(value, "binary") and hasattr(value, "generation_time"):
        return {"$oid": str(value)}
    return _normalize_scalar(value)


def stable_json_dumps(value: Any) -> str:
    return json.dumps(canonicalize_for_fingerprint(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def stable_document_hash(doc: Dict[str, Any]) -> str:
    return hashlib.sha256(stable_json_dumps(doc).encode("utf-8")).hexdigest()


def _collection_exclusion_rule(name: str, *, namespace_prefixes: Iterable[str] = RESTORE_NAMESPACE_PREFIXES) -> Optional[Dict[str, str]]:
    if name.startswith("system."):
        return dict(FINGERPRINT_EXCLUSION_RULES["system.*"])
    if any(name.startswith(prefix) for prefix in namespace_prefixes):
        return {
            "reason": "restore namespace collections must be excluded from canonical live fingerprint",
            "owner": "bcss_restore_drill_evidence",
        }
    if name in FINGERPRINT_EXCLUSION_RULES:
        return dict(FINGERPRINT_EXCLUSION_RULES[name])
    return None


def _iter_collection_documents(collection: Any) -> Iterable[Dict[str, Any]]:
    cursor = collection.find({}, None)
    for doc in cursor:
        if isinstance(doc, dict):
            yield dict(doc)


def build_canonical_preview_fingerprint(
    db: Any,
    *,
    runtime_identity: Dict[str, Any],
    namespace_prefixes: Iterable[str] = RESTORE_NAMESPACE_PREFIXES,
) -> Dict[str, Any]:
    included_collections: List[str] = []
    excluded_collections: List[str] = []
    exclusion_rules: Dict[str, Dict[str, str]] = {}
    per_collection_record_counts: Dict[str, int] = {}
    per_collection_fingerprints: Dict[str, Dict[str, Any]] = {}

    for name in sorted(db.list_collection_names()):
        rule = _collection_exclusion_rule(name, namespace_prefixes=namespace_prefixes)
        if rule is not None:
            excluded_collections.append(name)
            exclusion_rules[name] = rule
            continue
        included_collections.append(name)

    for name in included_collections:
        doc_hashes: List[str] = []
        count = 0
        for doc in _iter_collection_documents(db[name]):
            doc_hashes.append(stable_document_hash(doc))
            count += 1
        coll_fp = hashlib.sha256("\n".join(sorted(doc_hashes)).encode("utf-8")).hexdigest()
        per_collection_record_counts[name] = count
        per_collection_fingerprints[name] = {
            "record_count": count,
            "collection_fingerprint": coll_fp,
        }

    aggregate_source = [
        f"{name}|{per_collection_record_counts[name]}|{per_collection_fingerprints[name]['collection_fingerprint']}"
        for name in included_collections
    ]
    aggregate_fingerprint = hashlib.sha256("\n".join(aggregate_source).encode("utf-8")).hexdigest()

    return {
        "fingerprint_schema_version": FINGERPRINT_SCHEMA_VERSION,
        "captured_at": _now_iso(),
        "environment": runtime_identity.get("app_env"),
        "database": runtime_identity.get("db_name"),
        "environment_fingerprint": runtime_identity.get("environment_fingerprint"),
        "cluster_fingerprint": runtime_identity.get("cluster_fingerprint"),
        "collection_count": len(included_collections),
        "included_collections": included_collections,
        "excluded_collections": excluded_collections,
        "excluded_collection_rules": exclusion_rules,
        "per_collection_record_counts": per_collection_record_counts,
        "per_collection_fingerprints": per_collection_fingerprints,
        "aggregate_fingerprint": aggregate_fingerprint,
    }


def compare_fingerprints(before: Optional[Dict[str, Any]], after: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not isinstance(before, dict) or not isinstance(after, dict):
        return {
            "match": False,
            "difference": {
                "status": "fingerprint_missing",
                "before_present": isinstance(before, dict),
                "after_present": isinstance(after, dict),
            },
        }

    before_counts = before.get("per_collection_record_counts") or {}
    after_counts = after.get("per_collection_record_counts") or {}
    before_fps = before.get("per_collection_fingerprints") or {}
    after_fps = after.get("per_collection_fingerprints") or {}
    names = sorted(set(before_counts) | set(after_counts) | set(before_fps) | set(after_fps))
    diffs = []
    for name in names:
        b_count = before_counts.get(name)
        a_count = after_counts.get(name)
        b_fp = ((before_fps.get(name) or {}).get("collection_fingerprint"))
        a_fp = ((after_fps.get(name) or {}).get("collection_fingerprint"))
        if b_count != a_count or b_fp != a_fp:
            diffs.append({
                "collection": name,
                "before_count": b_count,
                "after_count": a_count,
                "before_fingerprint": b_fp,
                "after_fingerprint": a_fp,
            })
    match = not diffs and before.get("aggregate_fingerprint") == after.get("aggregate_fingerprint")
    return {
        "match": match,
        "difference": {
            "aggregate_before": before.get("aggregate_fingerprint"),
            "aggregate_after": after.get("aggregate_fingerprint"),
            "collection_differences": diffs,
        },
    }


def build_restore_evidence_skeleton(
    *,
    drill_id: str,
    namespace_prefix: str,
    authorized_archive_key: str,
    requested_env: str,
    target_db: str,
    guard: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    phases = {
        phase: {
            "phase": phase,
            "phase_status": "pending",
            "phase_started_at": None,
            "phase_completed_at": None,
            "heartbeat_at": None,
            "owner_pid": None,
            "owner_token": (guard or {}).get("owner_token"),
            "phase_evidence": {},
        }
        for phase in PHASE_SEQUENCE
    }
    return {
        "evidence_schema_version": EVIDENCE_SCHEMA_VERSION,
        "drill_id": drill_id,
        "requested_source_environment": requested_env,
        "target_namespace_prefix": namespace_prefix,
        "target_db": target_db,
        "authorized_archive_key": authorized_archive_key,
        "phase_history": phases,
        "current_phase": None,
        "last_started_phase": None,
        "last_completed_phase": None,
        "telemetry_timeline": [],
        "source_authority": {},
        "explicit_key_resolution": {},
        "canonical_before_fingerprint": None,
        "canonical_after_fingerprint": None,
        "canonical_fingerprint_match": None,
        "canonical_fingerprint_difference": None,
        "restore_results": {"collections": {}, "totals": {}},
        "representative_content_verification": {"state": "PENDING", "collections": {}},
        "audit_verification": {"state": "PENDING", "collections": {}},
        "identity_role_verification": {
            "identity_verification_state": "PENDING",
            "role_verification_state": "PENDING",
            "assignment_verification_state": "PENDING",
            "reference_integrity_state": "PENDING",
            "collections": {},
        },
        "scheduler_state_verification": {
            "state": "PENDING",
            "scheduler_data_restored": None,
            "scheduler_execution_triggered": False,
            "collections": {},
        },
        "photo_object_verification": {"state": "PENDING"},
        "cleanup": {"state": "PENDING"},
        "final_health": {"state": "PENDING"},
        "guard_release": {"state": "PENDING"},
        "qa_status": "PENDING_INDEPENDENT_REVIEW",
        "qa_reviews": [],
        "evidence_completeness_state": "INCOMPLETE",
        "missing_evidence_sections": [],
        "contradictory_evidence_sections": [],
        "certification_eligible": False,
    }


def _phase_slot(evidence: Dict[str, Any], phase: str) -> Dict[str, Any]:
    phases = evidence.setdefault("phase_history", {})
    if phase not in phases:
        phases[phase] = {
            "phase": phase,
            "phase_status": "pending",
            "phase_started_at": None,
            "phase_completed_at": None,
            "heartbeat_at": None,
            "owner_pid": None,
            "owner_token": None,
            "phase_evidence": {},
        }
    return phases[phase]


def mark_phase_status(
    evidence: Dict[str, Any],
    *,
    phase: str,
    status: str,
    owner_pid: Optional[int],
    owner_token: Optional[str],
    phase_evidence: Optional[Dict[str, Any]] = None,
    telemetry: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    now = _now_iso()
    slot = _phase_slot(evidence, phase)
    slot["phase_status"] = status
    slot["heartbeat_at"] = now
    slot["owner_pid"] = owner_pid
    slot["owner_token"] = owner_token
    if status == "started" and not slot.get("phase_started_at"):
        slot["phase_started_at"] = now
    if status in {"completed", "failed", "interrupted"}:
        slot["phase_completed_at"] = now
    if phase_evidence:
        slot.setdefault("phase_evidence", {}).update(phase_evidence)
    evidence["current_phase"] = phase
    evidence["last_started_phase"] = phase if status == "started" else evidence.get("last_started_phase") or phase
    if status == "completed":
        evidence["last_completed_phase"] = phase
    if telemetry:
        timeline = evidence.setdefault("telemetry_timeline", [])
        timeline.append(dict(telemetry))
    return evidence


def _primary_identifier(doc: Dict[str, Any]) -> str:
    for key in (
        "id",
        "backup_id",
        "job_id",
        "user_id",
        "employee_id",
        "project_id",
        "email",
        "asset_id",
        "archive_key",
        "name",
    ):
        value = doc.get(key)
        if value not in (None, ""):
            return str(value)
    return stable_document_hash(doc)[:16]


def deterministic_sample_identifiers(docs: List[Dict[str, Any]], *, sample_size: int = REPRESENTATIVE_SAMPLE_SIZE) -> Dict[str, Any]:
    keyed = sorted((_primary_identifier(doc), stable_document_hash(doc)) for doc in docs)
    ids = [item[0] for item in keyed]
    if len(ids) <= sample_size:
        selected = ids
    else:
        candidate_positions = [0, 1, len(ids) // 2, len(ids) - 2, len(ids) - 1]
        selected = []
        for idx in candidate_positions:
            value = ids[idx]
            if value not in selected:
                selected.append(value)
        selected = selected[:sample_size]
    return {
        "sampling_method": "deterministic-lowest-middle-highest-identifiers",
        "sample_size": len(selected),
        "sample_identifiers": selected,
    }


def _index_docs(docs: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {_primary_identifier(doc): doc for doc in docs}


def build_collection_sample_verification(
    *,
    collection: str,
    expected_docs: List[Dict[str, Any]],
    restored_docs: List[Dict[str, Any]],
) -> Dict[str, Any]:
    sample_meta = deterministic_sample_identifiers(expected_docs)
    expected_idx = _index_docs(expected_docs)
    restored_idx = _index_docs(restored_docs)
    expected_hashes: Dict[str, str] = {}
    restored_hashes: Dict[str, Optional[str]] = {}
    mismatches: List[Dict[str, Any]] = []
    for identifier in sample_meta["sample_identifiers"]:
        expected_doc = expected_idx.get(identifier)
        restored_doc = restored_idx.get(identifier)
        if expected_doc is None:
            continue
        expected_hash = stable_document_hash(expected_doc)
        expected_hashes[identifier] = expected_hash
        if restored_doc is None:
            restored_hashes[identifier] = None
            mismatches.append({"identifier": identifier, "code": "missing_sample_identifier"})
            continue
        restored_hash = stable_document_hash(restored_doc)
        restored_hashes[identifier] = restored_hash
        if restored_hash != expected_hash:
            mismatches.append({"identifier": identifier, "code": "sample_hash_mismatch"})
    return {
        "collection": collection,
        **sample_meta,
        "expected_hashes": expected_hashes,
        "restored_hashes": restored_hashes,
        "matched": len(mismatches) == 0,
        "mismatches": mismatches,
    }


def verify_representative_content(
    expected_by_collection: Dict[str, List[Dict[str, Any]]],
    restored_by_collection: Dict[str, List[Dict[str, Any]]],
) -> Dict[str, Any]:
    collections = {}
    overall = True
    for coll in sorted(expected_by_collection):
        evidence = build_collection_sample_verification(
            collection=coll,
            expected_docs=list(expected_by_collection.get(coll) or []),
            restored_docs=list(restored_by_collection.get(coll) or []),
        )
        collections[coll] = evidence
        overall = overall and evidence["matched"]
    return {
        "state": "PASS" if overall else "FAIL",
        "collections": collections,
    }


def _field_presence(doc: Dict[str, Any], keys: Iterable[str]) -> bool:
    return any(doc.get(key) not in (None, "") for key in keys)


def verify_audit_data(
    expected_by_collection: Dict[str, List[Dict[str, Any]]],
    restored_by_collection: Dict[str, List[Dict[str, Any]]],
) -> Dict[str, Any]:
    collections = {}
    overall = True
    for coll in AUDIT_COLLECTIONS:
        if coll not in expected_by_collection:
            continue
        evidence = build_collection_sample_verification(
            collection=coll,
            expected_docs=list(expected_by_collection.get(coll) or []),
            restored_docs=list(restored_by_collection.get(coll) or []),
        )
        expected_idx = _index_docs(list(expected_by_collection.get(coll) or []))
        sampled_docs = [expected_idx[sid] for sid in evidence["sample_identifiers"] if sid in expected_idx]
        evidence["actor_identity_survived"] = all(_field_presence(doc, ("actor", "actor_id", "actor_email", "user_id", "performed_by")) for doc in sampled_docs) if sampled_docs else True
        evidence["timestamps_survived"] = all(_field_presence(doc, ("at", "ts", "created_at", "reviewed_at", "timestamp")) for doc in sampled_docs) if sampled_docs else True
        evidence["event_types_survived"] = all(_field_presence(doc, ("kind", "action", "type", "event")) for doc in sampled_docs) if sampled_docs else True
        evidence["entity_references_survived"] = all(_field_presence(doc, ("entity_id", "record_id", "target_id", "project_id", "employee_id", "asset_id")) for doc in sampled_docs) if sampled_docs else True
        evidence["matched"] = bool(
            evidence["matched"]
            and evidence["actor_identity_survived"]
            and evidence["timestamps_survived"]
            and evidence["event_types_survived"]
            and evidence["entity_references_survived"]
        )
        collections[coll] = evidence
        overall = overall and evidence["matched"]
    return {
        "state": "PASS" if overall else "FAIL",
        "collections": collections,
    }


def verify_identity_role_data(
    expected_by_collection: Dict[str, List[Dict[str, Any]]],
    restored_by_collection: Dict[str, List[Dict[str, Any]]],
) -> Dict[str, Any]:
    collections = {}
    identity_ok = True
    role_ok = True
    assignment_ok = True
    reference_ok = True

    for coll in list(IDENTITY_COLLECTIONS) + list(ROLE_COLLECTIONS) + list(ASSIGNMENT_COLLECTIONS):
        if coll not in expected_by_collection:
            continue
        evidence = build_collection_sample_verification(
            collection=coll,
            expected_docs=list(expected_by_collection.get(coll) or []),
            restored_docs=list(restored_by_collection.get(coll) or []),
        )
        collections[coll] = evidence
        if coll in IDENTITY_COLLECTIONS:
            identity_ok = identity_ok and evidence["matched"]
        elif coll in ROLE_COLLECTIONS:
            role_ok = role_ok and evidence["matched"]
        else:
            assignment_ok = assignment_ok and evidence["matched"]

    identities = []
    for coll in IDENTITY_COLLECTIONS:
        identities.extend(restored_by_collection.get(coll) or [])
    known_refs = set()
    for row in identities:
        for key in ("id", "user_id", "employee_id", "email"):
            value = row.get(key)
            if value not in (None, ""):
                known_refs.add(str(value))

    for coll in ASSIGNMENT_COLLECTIONS:
        for row in restored_by_collection.get(coll) or []:
            refs = [str(row.get(key)) for key in ("user_id", "employee_id", "assignee_id", "email") if row.get(key) not in (None, "")]
            if refs and not any(ref in known_refs for ref in refs):
                reference_ok = False

    return {
        "identity_verification_state": "PASS" if identity_ok else "FAIL",
        "role_verification_state": "PASS" if role_ok else "FAIL",
        "assignment_verification_state": "PASS" if assignment_ok else "FAIL",
        "reference_integrity_state": "PASS" if reference_ok else "FAIL",
        "collections": collections,
    }


def verify_scheduler_state(
    expected_by_collection: Dict[str, List[Dict[str, Any]]],
    restored_by_collection: Dict[str, List[Dict[str, Any]]],
) -> Dict[str, Any]:
    collections = {}
    overall = True
    scheduler_data_restored = False
    for coll in SCHEDULER_STATE_COLLECTIONS:
        if coll not in expected_by_collection:
            continue
        scheduler_data_restored = True
        evidence = build_collection_sample_verification(
            collection=coll,
            expected_docs=list(expected_by_collection.get(coll) or []),
            restored_docs=list(restored_by_collection.get(coll) or []),
        )
        evidence["scheduler_execution_triggered"] = False
        collections[coll] = evidence
        overall = overall and evidence["matched"]
    return {
        "state": "PASS" if overall else "FAIL",
        "scheduler_data_restored": scheduler_data_restored,
        "scheduler_execution_triggered": False,
        "collections": collections,
    }


def verify_photo_object_evidence(
    *,
    expected_refs: Iterable[str],
    archive_object_keys: Iterable[str],
    rehydration_result: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    expected = sorted(set(str(ref) for ref in expected_refs if ref))
    objects = sorted(set(str(key) for key in archive_object_keys if key))
    missing = sorted(set(expected) - set(objects))
    return {
        "state": "PASS" if not missing and int((rehydration_result or {}).get("failed") or 0) == 0 else "FAIL",
        "expected_photo_object_references": expected,
        "restored_photo_object_references": objects,
        "missing_objects": missing,
        "orphan_references": [],
        "rehydration_result": dict(rehydration_result or {}),
    }


def build_restore_counts(
    manifest_per_kind: Dict[str, Any],
    per_kind_restore: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    collections = {}
    totals = {"expected": 0, "restored": 0, "inserted": 0, "updated": 0, "skipped": 0, "failed": 0}
    for coll in sorted(manifest_per_kind):
        normalized = coll.replace("-", "_")
        restore_row = dict(per_kind_restore.get(normalized) or {})
        expected = int(manifest_per_kind.get(coll) or 0)
        restored = int(restore_row.get("inserted") or 0)
        collections[coll] = {
            "expected_record_count": expected,
            "restored_record_count": restored,
            "inserted": int(restore_row.get("inserted") or 0),
            "updated": int(restore_row.get("updated") or 0),
            "skipped": int(restore_row.get("skipped_bad") or restore_row.get("skipped") or 0),
            "failed": int(restore_row.get("failed") or 0),
            "parity_result": expected == restored,
        }
        totals["expected"] += expected
        totals["restored"] += restored
        totals["inserted"] += collections[coll]["inserted"]
        totals["updated"] += collections[coll]["updated"]
        totals["skipped"] += collections[coll]["skipped"]
        totals["failed"] += collections[coll]["failed"]
    totals["parity_result"] = totals["expected"] == totals["restored"]
    return {"collections": collections, "totals": totals}


def validate_restore_certification_evidence(evidence: Dict[str, Any]) -> Dict[str, Any]:
    missing: List[str] = []
    contradictory: List[str] = []

    def _require(path: str, condition: bool) -> None:
        if not condition:
            missing.append(path)

    source_authority = evidence.get("source_authority") or {}
    explicit = evidence.get("explicit_key_resolution") or {}
    guard_release = evidence.get("guard_release") or {}
    cleanup = evidence.get("cleanup") or {}
    final_health = evidence.get("final_health") or {}
    photo = evidence.get("photo_object_verification") or {}
    qa_reviews = evidence.get("qa_reviews") or []

    _require("source_authority", bool(source_authority))
    _require("explicit_key_fanout_proof", explicit.get("remote_manifest_fanout_enabled") is False and int(explicit.get("remote_manifest_reads_attempted") or 0) == 0)
    _require("embedded_manifest", explicit.get("embedded_manifest_loaded") is True and explicit.get("embedded_manifest_reconciled") is True)
    _require("checksum", explicit.get("checksum_validated") is True)
    _require("canonical_before_fingerprint", isinstance(evidence.get("canonical_before_fingerprint"), dict))
    _require("restore_counts", bool((evidence.get("restore_results") or {}).get("collections")))
    _require("representative_content", (evidence.get("representative_content_verification") or {}).get("state") == "PASS")
    _require("audit_evidence", (evidence.get("audit_verification") or {}).get("state") == "PASS")
    identity = evidence.get("identity_role_verification") or {}
    _require("identity_role_evidence", all(identity.get(key) == "PASS" for key in ("identity_verification_state", "role_verification_state", "assignment_verification_state", "reference_integrity_state")))
    scheduler = evidence.get("scheduler_state_verification") or {}
    _require("scheduler_evidence", scheduler.get("state") == "PASS" and scheduler.get("scheduler_execution_triggered") is False)
    _require("photo_object_verification", photo.get("state") == "PASS")
    _require("canonical_after_fingerprint", isinstance(evidence.get("canonical_after_fingerprint"), dict))
    _require("canonical_equality", evidence.get("canonical_fingerprint_match") is True)
    _require("cleanup", cleanup.get("state") == "PASS")
    _require("final_health", final_health.get("state") == "PASS")
    _require("guard_release", guard_release.get("state") == "PASS")
    _require("independent_qa", bool(qa_reviews))

    before = evidence.get("canonical_before_fingerprint")
    after = evidence.get("canonical_after_fingerprint")
    if isinstance(before, dict) and isinstance(after, dict) and evidence.get("canonical_fingerprint_match") is True:
        cmp = compare_fingerprints(before, after)
        if not cmp["match"]:
            contradictory.append("canonical_fingerprint_match")

    if explicit.get("remote_manifest_fanout_enabled") is False and int(explicit.get("remote_manifest_reads_attempted") or 0) > 0:
        contradictory.append("explicit_key_fanout_proof")
    if explicit.get("checksum_validated") is True:
        persisted = str(explicit.get("persisted_checksum") or explicit.get("persisted_checksum_sha256") or "")
        computed = str(explicit.get("computed_checksum") or explicit.get("calculated_checksum_sha256") or "")
        if persisted and computed and persisted.lower() != computed.lower():
            contradictory.append("checksum")
    if cleanup.get("state") == "PASS" and cleanup.get("orphan_restore_collections") not in (0, None):
        contradictory.append("cleanup")
    if guard_release.get("state") == "PASS" and not guard_release.get("released_at"):
        contradictory.append("guard_release")

    qa_status = str(evidence.get("qa_status") or "")
    if qa_status == "PASS":
        contradictory.append("qa_status")

    evidence_complete = not missing and not contradictory
    certification_eligible = evidence_complete and any((review.get("qa_outcome") == "PASS") for review in qa_reviews)
    completeness_state = "PASS" if evidence_complete else ("CONTRADICTORY" if contradictory else "INCOMPLETE")
    return {
        "evidence_completeness_state": completeness_state,
        "missing_evidence_sections": sorted(set(missing)),
        "contradictory_evidence_sections": sorted(set(contradictory)),
        "certification_eligible": certification_eligible,
    }


def build_independent_qa_review(
    evidence: Dict[str, Any],
    *,
    reviewer_mode: str,
    qa_review_id: Optional[str] = None,
    exceptions: Optional[List[str]] = None,
) -> Dict[str, Any]:
    completeness = validate_restore_certification_evidence(evidence)
    exc = list(exceptions or [])
    qa_outcome = "PASS"
    if exc:
        qa_outcome = "BLOCKED"
    elif completeness["contradictory_evidence_sections"]:
        qa_outcome = "FAIL"
    elif completeness["missing_evidence_sections"]:
        qa_outcome = "INCOMPLETE"
    review = {
        "qa_review_id": qa_review_id or f"qa-{uuid.uuid4().hex[:12]}",
        "drill_id": evidence.get("drill_id"),
        "reviewed_at": _now_iso(),
        "reviewer_mode": reviewer_mode,
        "evidence_schema_version": QA_REVIEW_SCHEMA_VERSION,
        "evidence_complete": completeness["evidence_completeness_state"] == "PASS",
        "authority_checks_verified": bool(evidence.get("source_authority")) and bool(evidence.get("explicit_key_resolution")),
        "manifest_and_checksum_verified": bool((evidence.get("explicit_key_resolution") or {}).get("embedded_manifest_reconciled")) and bool((evidence.get("explicit_key_resolution") or {}).get("checksum_validated")),
        "restore_parity_verified": bool(((evidence.get("restore_results") or {}).get("totals") or {}).get("parity_result")),
        "representative_content_verified": (evidence.get("representative_content_verification") or {}).get("state") == "PASS",
        "canonical_immutability_verified": evidence.get("canonical_fingerprint_match") is True,
        "cleanup_verified": (evidence.get("cleanup") or {}).get("state") == "PASS",
        "runtime_stability_verified": (evidence.get("final_health") or {}).get("state") == "PASS",
        "exceptions": exc,
        "qa_outcome": qa_outcome,
    }
    return review


def local_health_snapshot(base_url: str = "http://127.0.0.1:8001") -> Dict[str, Any]:
    results: Dict[str, Any] = {}
    if requests is None:
        return {path: {"error": "requests_unavailable"} for path in ("health", "healthz", "ready", "health_full")}
    routes = {
        "health": f"{base_url}/api/health",
        "healthz": f"{base_url}/api/healthz",
        "ready": f"{base_url}/api/ready",
        "health_full": f"{base_url}/api/health/full",
    }
    for key, url in routes.items():
        try:
            resp = requests.get(url, timeout=5)
            payload = None
            try:
                payload = resp.json()
            except Exception:
                payload = {"raw": resp.text[:160]}
            results[key] = {"status": resp.status_code, "ok": resp.status_code == 200, "payload": payload}
        except Exception as exc:  # noqa: BLE001
            results[key] = {"status": None, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return results


def _discover_backend_process() -> Dict[str, Any]:
    if psutil is None:
        return {
            "backend_pid": None,
            "backend_process_exists": None,
            "backend_process_start_time": None,
            "memory_rss": None,
            "cpu_percent": None,
            "thread_count": None,
            "open_file_descriptors": None,
        }
    backend_proc = None
    supervisor_proc = None
    for proc in psutil.process_iter(["pid", "ppid", "cmdline", "create_time"]):
        cmdline = " ".join(proc.info.get("cmdline") or [])
        if "uvicorn" in cmdline and "server:app" in cmdline and backend_proc is None:
            backend_proc = proc
        if "supervisord" in cmdline and supervisor_proc is None:
            supervisor_proc = proc
    backend = {
        "backend_pid": backend_proc.pid if backend_proc else None,
        "backend_process_exists": bool(backend_proc and backend_proc.is_running()),
        "backend_process_start_time": datetime.fromtimestamp(backend_proc.create_time(), tz=timezone.utc).isoformat() if backend_proc else None,
        "memory_rss": backend_proc.memory_info().rss if backend_proc else None,
        "cpu_percent": backend_proc.cpu_percent(interval=None) if backend_proc else None,
        "thread_count": backend_proc.num_threads() if backend_proc else None,
        "open_file_descriptors": backend_proc.num_fds() if backend_proc and hasattr(backend_proc, "num_fds") else None,
        "supervisor_pid": supervisor_proc.pid if supervisor_proc else None,
        "supervisor_process_start_time": datetime.fromtimestamp(supervisor_proc.create_time(), tz=timezone.utc).isoformat() if supervisor_proc else None,
    }
    return backend


def capture_runtime_telemetry(
    *,
    db: Optional[Any],
    drill_phase: str,
    drill_pid: Optional[int] = None,
    base_url: str = "http://127.0.0.1:8001",
) -> Dict[str, Any]:
    proc = _discover_backend_process()
    restart_count = None
    if db is not None:
        try:
            boot = db.runtime_boot_markers.find_one({"_id": "latest"}, {"_id": 0, "restart_count": 1})
            restart_count = int((boot or {}).get("restart_count") or 0)
        except Exception:
            restart_count = None
    health = local_health_snapshot(base_url)
    return {
        "captured_at": _now_iso(),
        "drill_phase": drill_phase,
        "backend_pid": proc.get("backend_pid"),
        "backend_process_start_time": proc.get("backend_process_start_time"),
        "supervisor_pid": proc.get("supervisor_pid"),
        "drill_pid": drill_pid,
        "drill_process_exists": bool(drill_pid and Path(f"/proc/{drill_pid}").exists()),
        "backend_process_exists": proc.get("backend_process_exists"),
        "memory_rss": proc.get("memory_rss"),
        "cpu_percent": proc.get("cpu_percent"),
        "thread_count": proc.get("thread_count"),
        "open_file_descriptors": proc.get("open_file_descriptors"),
        "health": health.get("health"),
        "healthz": health.get("healthz"),
        "ready": health.get("ready"),
        "health_full": health.get("health_full"),
        "supervisor_restart_count": restart_count,
    }


def extract_archive_collection_documents(zip_file: Any) -> Dict[str, List[Dict[str, Any]]]:
    collections: Dict[str, List[Dict[str, Any]]] = {}
    aggregated = [name for name in zip_file.namelist() if name.startswith("collections/") and name.endswith(".json")]
    if aggregated:
        for name in aggregated:
            coll = Path(name).stem.replace("-", "_")
            payload = json.loads(zip_file.read(name).decode("utf-8"))
            docs = payload if isinstance(payload, list) else [payload]
            collections[coll] = [dict(doc) for doc in docs if isinstance(doc, dict)]
        return collections
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for name in zip_file.namelist():
        if name == "MANIFEST.json" or not name.endswith(".json") or "/json/" not in name:
            continue
        coll = name.split("/json/", 1)[0].replace("-", "_")
        try:
            payload = json.loads(zip_file.read(name).decode("utf-8"))
        except Exception:
            continue
        if isinstance(payload, dict):
            grouped.setdefault(coll, []).append(dict(payload))
    return grouped


def load_namespace_collection_documents(db: Any, namespace_prefix: str, collection_names: Iterable[str]) -> Dict[str, List[Dict[str, Any]]]:
    out: Dict[str, List[Dict[str, Any]]] = {}
    for coll in collection_names:
        physical = f"{namespace_prefix}__{coll}"
        docs = [dict(doc) for doc in _iter_collection_documents(db[physical])]
        out[coll] = docs
    return out


def count_supervisor_restarts_from_log(log_path: str = "/var/log/supervisor/supervisord.log") -> int:
    path = Path(log_path)
    if not path.exists():
        return 0
    try:
        return sum(1 for line in path.read_text(errors="replace").splitlines() if "supervisord started with pid" in line)
    except Exception:
        return 0
