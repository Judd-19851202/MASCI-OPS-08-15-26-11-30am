#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from pymongo import MongoClient

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_ENV = REPO_ROOT / "backend" / ".env"
sys.path.insert(0, str(REPO_ROOT / "backend"))

from lib.restore_certification_evidence import (  # noqa: E402
    build_canonical_preview_fingerprint,
    build_independent_qa_review,
    build_restore_evidence_skeleton,
    canonical_owner_trace,
    validate_restore_certification_evidence,
)


def _load_env() -> dict[str, str]:
    env = dict(os.environ)
    if BACKEND_ENV.exists():
        for line in BACKEND_ENV.read_text().splitlines():
            s = line.strip()
            if not s or s.startswith("#") or "=" not in s:
                continue
            k, v = s.split("=", 1)
            env.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    return env


def main() -> int:
    env = _load_env()
    mongo = MongoClient(env["MONGO_URL"], serverSelectionTimeoutMS=10000)
    db = mongo[env["DB_NAME"]]
    runtime_identity = {
        "app_env": env.get("APP_ENV", "preview"),
        "db_name": env["DB_NAME"],
        "environment_fingerprint": "dry-validation-preview",
        "cluster_fingerprint": "dry-validation-cluster",
    }
    fp = build_canonical_preview_fingerprint(db, runtime_identity=runtime_identity)
    evidence = build_restore_evidence_skeleton(
        drill_id="dry-validation",
        namespace_prefix="ops8_dry_validation",
        authorized_archive_key="backups/auto-90d/MASCI_complete_backup_2026-07-25_230328Z.zip",
        requested_env="preview",
        target_db=env["DB_NAME"],
        guard={"owner_token": "dry-owner-token"},
    )
    evidence["canonical_before_fingerprint"] = fp
    evidence["canonical_after_fingerprint"] = fp
    evidence["canonical_fingerprint_match"] = True
    evidence["canonical_fingerprint_difference"] = {"aggregate_before": fp["aggregate_fingerprint"], "aggregate_after": fp["aggregate_fingerprint"], "collection_differences": []}
    evidence["source_authority"] = {"environment": "preview", "database": env["DB_NAME"]}
    evidence["explicit_key_resolution"] = {
        "lineage_resolution_mode": "EXPLICIT_KEY_PERSISTED_AUTHORITY",
        "remote_manifest_fanout_enabled": False,
        "remote_manifest_reads_attempted": 0,
        "embedded_manifest_loaded": True,
        "embedded_manifest_reconciled": True,
        "checksum_validated": True,
    }
    evidence["restore_results"] = {"collections": {"daily_reports": {"expected_record_count": 1, "restored_record_count": 1, "inserted": 1, "updated": 0, "skipped": 0, "failed": 0, "parity_result": True}}, "totals": {"expected": 1, "restored": 1, "inserted": 1, "updated": 0, "skipped": 0, "failed": 0, "parity_result": True}}
    evidence["representative_content_verification"] = {"state": "PASS", "collections": {}}
    evidence["audit_verification"] = {"state": "PASS", "collections": {}}
    evidence["identity_role_verification"] = {"identity_verification_state": "PASS", "role_verification_state": "PASS", "assignment_verification_state": "PASS", "reference_integrity_state": "PASS", "collections": {}}
    evidence["scheduler_state_verification"] = {"state": "PASS", "scheduler_data_restored": True, "scheduler_execution_triggered": False, "collections": {}}
    evidence["photo_object_verification"] = {"state": "PASS"}
    evidence["cleanup"] = {"state": "PASS"}
    evidence["final_health"] = {"state": "PASS"}
    evidence["guard_release"] = {"state": "PASS", "released_at": "dry"}
    completeness = validate_restore_certification_evidence(evidence)
    evidence.update(completeness)
    review = build_independent_qa_review(evidence, reviewer_mode="dry-validation")
    evidence.setdefault("qa_reviews", []).append(review)
    evidence["qa_status"] = review["qa_outcome"]
    print(json.dumps({
        "real_restore_executed": False,
        "real_guard_acquired": False,
        "real_archive_downloaded": False,
        "namespace_created": False,
        "Production_accessed": False,
        "nonterminal_preview_drills": db.drill_runs.count_documents({"$and": [{"state": {"$nin": ["ok", "failed", "aborted", "cancelled", "completed", "done"]}}, {"outcome": {"$nin": ["ok", "failed", "aborted", "cancelled", "completed"]}}]}),
        "active_preview_guards": db.backup_jobs.count_documents({"state": {"$nin": ["completed", "failed", "aborted", "cancelled", "released"]}, "kind": "restore_drill"}),
        "orphan_restore_namespaces": len([n for n in db.list_collection_names() if n.startswith("ops8_dry_validation__")]),
        "owner_trace": canonical_owner_trace(),
        "fingerprint_aggregate": fp["aggregate_fingerprint"],
        "completeness": completeness,
        "qa_review": review,
    }, indent=2))
    mongo.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())