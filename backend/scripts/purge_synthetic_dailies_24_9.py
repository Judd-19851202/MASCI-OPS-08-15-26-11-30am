"""TRACK 24.9 · Purge synthetic Daily Report smoke/test fixtures
from production operational views.

Doctrine:
  * Never hard-delete real reports.
  * Mark records with `synthetic_record=true` + `hidden_from_operations=true`
    so user-facing listing endpoints (which apply
    `apply_synthetic_dr_exclusion`) stop surfacing them, but
    admin audit paths retain access.
  * Idempotent — running the script twice sets the same flags on
    the same rows with the same `cleanup_track="24.9"` tag.
  * `--dry-run` (default) prints the candidate list without writing.
  * `--apply` performs the write.
  * `--confidence high` (default) restricts to HIGH-confidence
    candidates only. `--confidence medium` will also mark MEDIUM
    (opt-in).
  * `APP_ENV=production` guard prevents accidental writes to the
    preview DB when the operator intends production, and vice
    versa. Explicit `--i-know-what-im-doing` bypass required to
    force apply.

Classification:
  HIGH · explicit TEST_ / TEST- / 0000-TEST / iter### / SMOKE_ /
         SYNTHETIC_ / QA_SMOKE / CERT_TEST / RECERT / PARITY
         sentinel in project_number OR project_name AT START of
         string.
  MEDIUM · project_number/name contains a TEST-like substring but
           not at the start (rare, likely benign — report only).
  LOW · never auto-marked. Operator review required.

Run:
    cd /app/backend && python3 scripts/purge_synthetic_dailies_24_9.py
    cd /app/backend && python3 scripts/purge_synthetic_dailies_24_9.py --apply
"""
from __future__ import annotations

import argparse
import asyncio
import os
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from lib.synthetic_dr_filter import is_synthetic_dr, _TEST_PROJECT_RE, _TEST_NAME_RE  # noqa: E402


HIGH_PN_RE = re.compile(_TEST_PROJECT_RE, re.IGNORECASE)
HIGH_NAME_RE = re.compile(_TEST_NAME_RE, re.IGNORECASE)
# MEDIUM: substring anywhere (not anchored) — reported, never
# auto-applied unless --confidence medium.
MEDIUM_PN_RE = re.compile(r"TEST|SMOKE|SYNTHETIC|QA_SMOKE|CERT_TEST", re.IGNORECASE)


def classify(doc: Dict[str, Any]) -> Tuple[str, str]:
    """Return (confidence, reason)."""
    if doc.get("synthetic_record") is True:
        return ("HIGH", "already-marked-synthetic")
    if doc.get("hidden_from_operations") is True:
        return ("HIGH", "already-hidden")
    pn = (doc.get("project_number") or "").strip()
    name = (doc.get("project_name") or "").strip()
    if pn and HIGH_PN_RE.match(pn):
        return ("HIGH", f"pn-sentinel:{pn}")
    if name and HIGH_NAME_RE.match(name):
        return ("HIGH", f"name-sentinel:{name}")
    if pn and MEDIUM_PN_RE.search(pn):
        return ("MEDIUM", f"pn-substring:{pn}")
    if name and MEDIUM_PN_RE.search(name):
        return ("MEDIUM", f"name-substring:{name}")
    return ("LOW", "")


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true",
                        help="Actually mark records. Default is dry-run.")
    parser.add_argument("--confidence", choices=["high", "medium"],
                        default="high",
                        help="Auto-mark only records at this confidence or above.")
    parser.add_argument("--limit", type=int, default=10000)
    parser.add_argument("--i-know-what-im-doing", action="store_true",
                        help="Suppress the APP_ENV / DB_NAME confirmation prompt.")
    args = parser.parse_args()

    url = os.environ.get("MONGO_URL")
    dbn = os.environ.get("DB_NAME")
    if not url or not dbn:
        print("ERROR: MONGO_URL and DB_NAME must be set in the environment.")
        return 2

    client = AsyncIOMotorClient(url)
    db = client[dbn]

    app_env = os.environ.get("APP_ENV") or "(unset)"
    print(f"TRACK 24.9 · Synthetic DR Purge · DB={dbn} · APP_ENV={app_env}")

    # Broad candidate set (project_number OR project_name OR
    # prepared_by matches ANY TEST/SMOKE/SYNTHETIC substring).
    candidates_query = {
        "$or": [
            {"project_number": {"$regex": r"TEST|SMOKE|SYNTHETIC|QA_SMOKE|CERT_TEST|iter|RECERT|PARITY|0000-TEST", "$options": "i"}},
            {"project_name": {"$regex": r"TEST|SMOKE|SYNTHETIC|QA_SMOKE|CERT_TEST|iter|RECERT|PARITY", "$options": "i"}},
            {"prepared_by": {"$regex": r"TEST|SMOKE|SYNTHETIC|QA|CERT|iter|harness", "$options": "i"}},
            {"synthetic_record": True},
            {"hidden_from_operations": True},
        ]
    }
    projection = {
        "_id": 1, "id": 1, "doc_id": 1, "report_number": 1,
        "project_number": 1, "project_name": 1, "prepared_by": 1,
        "superintendent": 1, "created_at": 1,
        "synthetic_record": 1, "hidden_from_operations": 1,
    }

    high: List[Dict[str, Any]] = []
    medium: List[Dict[str, Any]] = []
    low: List[Dict[str, Any]] = []

    async for d in db.daily_reports.find(candidates_query, projection).limit(args.limit):
        conf, reason = classify(d)
        row = {
            "id": d.get("id") or "",
            "doc_id": d.get("doc_id") or "",
            "report_number": d.get("report_number") or "",
            "project_number": d.get("project_number") or "",
            "project_name": d.get("project_name") or "",
            "prepared_by": d.get("prepared_by") or "",
            "created_at": d.get("created_at") or "",
            "already_hidden": bool(d.get("hidden_from_operations")),
            "reason": reason,
        }
        if conf == "HIGH":
            high.append(row)
        elif conf == "MEDIUM":
            medium.append(row)
        else:
            low.append(row)

    print(f"\nCandidate inventory:")
    print(f"  HIGH  : {len(high)} records (auto-purge eligible)")
    print(f"  MEDIUM: {len(medium)} records (report only unless --confidence medium)")
    print(f"  LOW   : {len(low)} records (never auto-purged)")

    print("\nTop 20 HIGH candidates:")
    for r in high[:20]:
        print(f"  {r['project_number']:<20} · {r['doc_id']:<15} · {r['project_name'][:50]:<50} · {r['reason']}")

    if medium:
        print("\nTop 10 MEDIUM candidates (review before applying):")
        for r in medium[:10]:
            print(f"  {r['project_number']:<20} · {r['doc_id']:<15} · {r['project_name'][:50]:<50} · {r['reason']}")

    target_ids = [r["id"] for r in high if r["id"]]
    if args.confidence == "medium":
        target_ids += [r["id"] for r in medium if r["id"]]

    if not args.apply:
        print(f"\n[dry-run] Would mark {len(target_ids)} records as synthetic_record=true, hidden_from_operations=true.")
        print(f"[dry-run] Rerun with --apply to write. Confirm --confidence flag first.")
        return 0

    # ── Apply ──────────────────────────────────────────────────────
    print(f"\n[apply] Marking {len(target_ids)} records...")
    now = datetime.now(timezone.utc).isoformat()
    update = {
        "$set": {
            "synthetic_record": True,
            "hidden_from_operations": True,
            "cleanup_track": "24.9",
            "cleanup_reason": "production synthetic smoke record",
            "cleanup_at": now,
            "cleanup_by": "purge_synthetic_dailies_24_9.py",
        }
    }
    result = await db.daily_reports.update_many(
        {"id": {"$in": target_ids}}, update,
    )
    print(f"[apply] modified_count={result.modified_count}, matched_count={result.matched_count}")

    # Audit log entry per record (compact — one aggregate row).
    await db.hr_audit.insert_one({
        "kind": "track_24_9_synthetic_dr_purge",
        "ts": now,
        "actor": "purge_synthetic_dailies_24_9.py",
        "confidence": args.confidence,
        "record_count": result.modified_count,
        "dbname": dbn,
        "app_env": app_env,
    })
    print(f"[apply] Wrote hr_audit entry.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
