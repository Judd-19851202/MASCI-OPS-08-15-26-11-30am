"""scan_signatures.py — quick audit of base64 signature bytes in the DB.

One-shot script. Counts base64 vs cloud signatures per collection and
totals the DB-resident base64 bytes — used to size the migration.
"""
from __future__ import annotations

import asyncio
import os

from dotenv import load_dotenv

load_dotenv("/app/backend/.env")

from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402

COLLECTIONS = [
    "daily_reports", "inspections", "field_leadership",
    "equipment_inspections", "pre_op_inspections", "toolbox_talks",
    "concrete_inspections", "rebar_inspections", "subcontractor_inspections",
    "incidents", "job_hazard_plans",
]

SIG_FIELDS = [
    "prepared_by_signature", "superintendent_signature", "signature",
    "supervisor_signature", "employee_signature", "witness_signature",
    "inspector_signature", "foreman_signature", "operator_signature",
    "sub_rep_signature",
]


async def main() -> None:
    c = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = c[os.environ["DB_NAME"]]
    grand = {"docs": 0, "with": 0, "b64": 0, "cloud": 0, "bytes": 0}
    existing = await db.list_collection_names()
    for col in COLLECTIONS:
        if col not in existing:
            continue
        count = await db[col].estimated_document_count()
        if not count:
            continue
        n_with = n_b64 = n_cloud = 0
        bytes_total = 0
        projection = {f: 1 for f in SIG_FIELDS}
        projection.update({"signatures": 1, "attendees": 1, "witnesses": 1})
        async for d in db[col].find({}, projection):
            has = False
            for f in SIG_FIELDS:
                v = d.get(f)
                if isinstance(v, str) and v:
                    has = True
                    if v.startswith("data:"):
                        n_b64 += 1
                        bytes_total += len(v)
                    elif v.startswith("photo://"):
                        n_cloud += 1
            for nk in ("signatures", "attendees", "witnesses"):
                arr = d.get(nk)
                if isinstance(arr, list):
                    for e in arr:
                        if isinstance(e, dict):
                            for sk in ("signature", "sig"):
                                sv = e.get(sk)
                                if isinstance(sv, str) and sv:
                                    has = True
                                    if sv.startswith("data:"):
                                        n_b64 += 1
                                        bytes_total += len(sv)
                                    elif sv.startswith("photo://"):
                                        n_cloud += 1
            if has:
                n_with += 1
        grand["docs"] += count
        grand["with"] += n_with
        grand["b64"] += n_b64
        grand["cloud"] += n_cloud
        grand["bytes"] += bytes_total
        if n_with or n_b64:
            print(f"{col:30s} docs={count:5d} with_sig={n_with:5d} "
                  f"base64={n_b64:5d} cloud={n_cloud:5d} "
                  f"bytes={bytes_total / 1024 / 1024:.2f} MB")
    print()
    print(f"GRAND  docs={grand['docs']}  with_sig={grand['with']}  "
          f"base64={grand['b64']}  cloud={grand['cloud']}")
    print(f"DB signature base64 = {grand['bytes'] / 1024 / 1024:.2f} MB")


if __name__ == "__main__":
    asyncio.run(main())
