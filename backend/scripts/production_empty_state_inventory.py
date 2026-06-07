#!/usr/bin/env python3
"""Production Empty-State Inventory · READ-ONLY.

Run by operator against production DB after cutover. Outputs PASS/FAIL
plus exact contamination record IDs. Never writes.

Usage:
    PROD_MONGO_URL="mongodb+srv://..." \\
    PROD_DB_NAME="masci_safety" \\
    python /app/backend/scripts/production_empty_state_inventory.py

Exit codes:
    0   PASS   · zero contamination
    1   FAIL   · contamination found · do NOT declare production clean
    2   ERROR  · could not connect / could not query
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List

from motor.motor_asyncio import AsyncIOMotorClient


CONTAMINATION_MARKERS = [
    "test", "demo", "smoke", "preview", "fixture", "sample", "fake",
    "dummy", "safe-to-delete", "ITER", "QA", "sandbox", "FV-7", "FT-",
    "FV7", "field trial", "deploy-smoke",
]
TEST_EMAIL_DOMAINS = ["@test.", "@example.", "@demo.", "@fake.", "@qa.", "@sample."]
TB_PLACEHOLDER_PREFIXES = ["TB-NTF", "TB-TEST", "TB-DEMO", "TB-FAKE"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def inventory(db, regex: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {"collections": {}, "contamination": {}, "sample_contamination_ids": {}}

    # Per-collection totals
    for coll in [
        "users", "employees", "projects", "jobs_master",
        "trench_safety_assets", "trench_excavations", "daily_reports",
        "audit_events", "notifications",
    ]:
        try:
            out["collections"][coll] = await db[coll].count_documents({})
        except Exception as e:  # noqa: BLE001
            out["collections"][coll] = f"ERROR: {e}"

    # users with test domains
    test_user_ids: List[str] = []
    async for u in db.users.find(
        {"email": {"$regex": "|".join([d.replace(".", "\\.") for d in TEST_EMAIL_DOMAINS]), "$options": "i"}},
        {"_id": 0, "id": 1, "email": 1},
    ):
        test_user_ids.append(f"{u.get('id')} · {u.get('email')}")
    out["contamination"]["users_test_domains"] = len(test_user_ids)
    out["sample_contamination_ids"]["users"] = test_user_ids[:10]

    # excavations with contamination markers
    exc_ids: List[str] = []
    async for d in db.trench_excavations.find(
        {"project_name": {"$regex": regex, "$options": "i"}},
        {"_id": 0, "id": 1, "project_name": 1},
    ).limit(50):
        exc_ids.append(f"{d.get('id')} · {d.get('project_name')}")
    out["contamination"]["trench_excavations_contaminated"] = await db.trench_excavations.count_documents(
        {"project_name": {"$regex": regex, "$options": "i"}}
    )
    out["sample_contamination_ids"]["trench_excavations"] = exc_ids[:10]

    # daily reports with contamination markers
    dr_ids: List[str] = []
    async for d in db.daily_reports.find(
        {"project_name": {"$regex": regex, "$options": "i"}},
        {"_id": 0, "id": 1, "report_number": 1, "project_name": 1},
    ).limit(50):
        dr_ids.append(f"{d.get('report_number') or d.get('id')} · {d.get('project_name')}")
    out["contamination"]["daily_reports_contaminated"] = await db.daily_reports.count_documents(
        {"project_name": {"$regex": regex, "$options": "i"}}
    )
    out["sample_contamination_ids"]["daily_reports"] = dr_ids[:10]

    # trench safety assets with placeholder prefixes
    ts_ids: List[str] = []
    placeholder_q = {"asset_id": {"$regex": "|".join(TB_PLACEHOLDER_PREFIXES), "$options": "i"}}
    async for d in db.trench_safety_assets.find(placeholder_q, {"_id": 0, "asset_id": 1, "asset_type": 1}).limit(50):
        ts_ids.append(f"{d.get('asset_id')} · {d.get('asset_type')}")
    out["contamination"]["trench_safety_assets_placeholder"] = await db.trench_safety_assets.count_documents(placeholder_q)
    out["sample_contamination_ids"]["trench_safety_assets"] = ts_ids

    # FV-7.1A backfill stamp — must be zero on production unless operator authorized
    out["contamination"]["trench_safety_assets_fv7_1a_backfilled"] = await db.trench_safety_assets.count_documents(
        {"metadata_backfilled_from": "FV-7.1A"}
    )

    # jobs_master with contamination
    out["contamination"]["jobs_master_contaminated"] = await db.jobs_master.count_documents(
        {"$or": [
            {"job_number": {"$regex": regex, "$options": "i"}},
            {"name": {"$regex": regex, "$options": "i"}},
        ]}
    )

    # employees with test markers
    out["contamination"]["employees_contaminated"] = await db.employees.count_documents(
        {"$or": [
            {"name": {"$regex": regex, "$options": "i"}},
            {"email": {"$regex": "|".join([d.replace(".", "\\.") for d in TEST_EMAIL_DOMAINS]), "$options": "i"}},
        ]}
    )

    return out


async def main():
    mongo_url = os.environ.get("PROD_MONGO_URL") or os.environ.get("MONGO_URL")
    db_name = os.environ.get("PROD_DB_NAME") or os.environ.get("DB_NAME")
    if not mongo_url or not db_name:
        print("ERROR: PROD_MONGO_URL and PROD_DB_NAME env vars are required.", file=sys.stderr)
        sys.exit(2)

    print(f"[{_now()}] Production Empty-State Inventory · DB={db_name}")
    print("  READ-ONLY · no writes will occur · safe to run on production")
    print()

    try:
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        # quick ping
        await db.command("ping")
    except Exception as e:  # noqa: BLE001
        print(f"ERROR connecting to MongoDB: {e}", file=sys.stderr)
        sys.exit(2)

    regex = "|".join(CONTAMINATION_MARKERS)
    report = await inventory(db, regex)

    # PASS/FAIL determination
    contamination_total = sum(
        v for v in report["contamination"].values() if isinstance(v, int)
    )
    report["overall_verdict"] = "PASS" if contamination_total == 0 else "FAIL"
    report["contamination_total"] = contamination_total
    report["ran_at"] = _now()
    report["env"] = {"DB_NAME": db_name}

    # human summary
    print(json.dumps(report, indent=2))
    print()
    print(f"VERDICT: {report['overall_verdict']}  ·  contamination_total={contamination_total}")
    if report["overall_verdict"] == "FAIL":
        print("Production is NOT CLEAN. Do not declare empty-state certification.")
        sys.exit(1)
    print("Production empty-state certification: PASS.")
    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
