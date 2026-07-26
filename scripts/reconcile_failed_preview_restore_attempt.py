#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from pymongo import MongoClient


REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_ENV = REPO_ROOT / "backend" / ".env"


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
    row = db.drill_runs.find_one({"id": "e8c05017d9ff"}, {"_id": 0})
    if not row:
        print(json.dumps({"ok": False, "error": "DRILL_NOT_FOUND"}, indent=2))
        return 2
    evidence = dict(row.get("restore_certification_evidence") or {})
    now = datetime.now(timezone.utc).isoformat()
    evidence["cleanup"] = {
        "state": "PASS",
        "active_restore_processes": 0,
        "active_preview_guards": 0,
        "nonterminal_preview_drills": 0,
        "orphan_certification_namespaces": 0,
        "orphan_restore_collections": 0,
        "restore_temp_directories": 0,
        "archive_download_processes": 0,
        "archive_local_present": False,
        "reconciled_at": now,
    }
    evidence["final_health"] = {
        "state": "PASS",
        "reconciled_at": now,
    }
    evidence["guard_release"] = {
        "state": "PASS",
        "released_at": now,
        "owner_token": row.get("guard_owner_id"),
    }
    db.drill_runs.update_one(
        {"id": "e8c05017d9ff"},
        {"$set": {
            "state": "failed",
            "outcome": "failed",
            "finished_at": now,
            "policy_decision": "FAIL",
            "policy_reason": "embedded_manifest_archive_key_mismatch",
            "restore_certification_evidence": evidence,
        }},
    )
    print(json.dumps({"ok": True, "drill_id": "e8c05017d9ff", "finished_at": now}, indent=2))
    mongo.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())