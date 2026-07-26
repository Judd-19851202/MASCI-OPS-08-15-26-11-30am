#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from pymongo import MongoClient

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_ENV = REPO_ROOT / "backend" / ".env"
sys.path.insert(0, str(REPO_ROOT / "backend"))

from lib.restore_certification_evidence import build_independent_qa_review, validate_restore_certification_evidence  # noqa: E402


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
    ap = argparse.ArgumentParser(description="Persist independent QA review for an OPS8 restore drill")
    ap.add_argument("--drill-id", required=True)
    ap.add_argument("--reviewer-mode", required=True)
    ap.add_argument("--exception", action="append", default=[])
    args = ap.parse_args()

    env = _load_env()
    mongo = MongoClient(env["MONGO_URL"], serverSelectionTimeoutMS=10000)
    db = mongo[env["DB_NAME"]]
    row = db.drill_runs.find_one({"id": args.drill_id}, {"_id": 0})
    if not row:
        print(json.dumps({"ok": False, "error": "DRILL_NOT_FOUND", "drill_id": args.drill_id}, indent=2))
        return 2
    evidence = dict(row.get("restore_certification_evidence") or {})
    completeness = validate_restore_certification_evidence(evidence)
    evidence.update(completeness)
    review = build_independent_qa_review(evidence, reviewer_mode=args.reviewer_mode, exceptions=args.exception)
    evidence.setdefault("qa_reviews", []).append(review)
    evidence["qa_status"] = review["qa_outcome"]
    db.drill_runs.update_one(
        {"id": args.drill_id},
        {"$set": {
            "restore_certification_evidence": evidence,
            "qa_status": review["qa_outcome"],
            "qa_latest_review": review,
        }},
    )
    print(json.dumps({"ok": True, "review": review, "completeness": completeness}, indent=2))
    mongo.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())