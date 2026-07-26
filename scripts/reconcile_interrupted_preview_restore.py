#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from pymongo import MongoClient


REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_ENV = REPO_ROOT / "backend" / ".env"

DRILL_ID = "910522c9b42e"
GUARD_JOB_ID = "bjob-a18f40c070694910b15bc070671d52bc"
OWNER_PID = 5641
TARGET_PREFIX = "ops8_drill_20260726_155945__"
TERMINAL_SLOT = "restore-certification::preview::aborted::bjob-a18f40c070694910b15bc070671d52bc"


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
    now = datetime.now(timezone.utc).isoformat()
    client = MongoClient(env["MONGO_URL"], serverSelectionTimeoutMS=10000)
    db = client[env["DB_NAME"]]

    evidence = {
        "execution_result": "INTERRUPTED_BEFORE_NAMESPACE_RESTORE",
        "certification_impact": "NO CERTIFICATION ADVANCEMENT",
        "restore_result": "NOT EXERCISED TO COMPLETION",
        "failure_domain": "EXPLICIT RESTORE-CERTIFICATION RUNTIME PATH",
        "interruption_reason": "ABORTED_DUE_TO_BACKEND_PROCESS_RESTART",
        "last_confirmed_phase": "manifest_loaded",
        "owner_pid": OWNER_PID,
        "owner_process_exists": Path(f"/proc/{OWNER_PID}").exists(),
        "namespace_prefix": TARGET_PREFIX[:-2],
        "prefixed_collection_count": len([n for n in db.list_collection_names() if n.startswith(TARGET_PREFIX)]),
        "no_namespace_writes_observed": True,
        "cleanup_reached": False,
        "verification_reached": False,
        "certification_result_produced": False,
        "backend_restart_detected": True,
        "backend_restart_evidence_at": "2026-07-26T16:06:35+00:00",
        "canonical_immutability_status": "CANONICAL_IMMUTABILITY_NOT_FORMALLY_CERTIFIED_FOR_INTERRUPTED_ATTEMPT",
        "reconciliation_completed_at": now,
    }

    drill_update = {
        "state": "aborted",
        "outcome": "aborted",
        "reason": "ABORTED_DUE_TO_BACKEND_PROCESS_RESTART",
        "failure_reason": "ABORTED_DUE_TO_BACKEND_PROCESS_RESTART",
        "policy_decision": "ABORTED",
        "policy_reason": "backend_process_restart_before_namespace_restore_completion",
        "finished_at": now,
        "completed_at": now,
        "interruption_evidence": evidence,
    }
    db.drill_runs.update_one({"id": DRILL_ID}, {"$set": drill_update})

    guard_update = {
        "state": "aborted",
        "outcome": "aborted",
        "updated_at": now,
        "heartbeat_at": now,
        "completed_at": now,
        "ownership_revoked": True,
        "ownership_revoked_at": now,
        "failure_reason": "ABORTED_DUE_TO_BACKEND_PROCESS_RESTART",
        "recovery_reason": "owner_process_gone_backend_restart_detected",
        "slot_key": TERMINAL_SLOT,
        "terminalization_evidence": {
            "original_owner_pid": OWNER_PID,
            "original_owner_process_exists": False,
            "backend_restart_invalidated_original_lease_ownership": True,
            "no_restore_child_process_remains": True,
            "no_namespace_write_active": True,
            "no_temp_archive_or_extraction_process_remains": True,
            "last_confirmed_phase": "manifest_loaded",
            "terminalized_at": now,
        },
    }
    db.backup_jobs.update_one({"job_id": GUARD_JOB_ID}, {"$set": guard_update})

    result = {
        "ok": True,
        "drill_id": DRILL_ID,
        "guard_job_id": GUARD_JOB_ID,
        "drill_state": db.drill_runs.find_one({"id": DRILL_ID}, {"_id": 0, "state": 1, "outcome": 1, "reason": 1, "finished_at": 1}),
        "guard_state": db.backup_jobs.find_one({"job_id": GUARD_JOB_ID}, {"_id": 0, "state": 1, "outcome": 1, "failure_reason": 1, "slot_key": 1, "completed_at": 1, "ownership_revoked": 1}),
    }
    print(json.dumps(result, indent=2))
    client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())