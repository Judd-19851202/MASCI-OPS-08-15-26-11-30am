#!/usr/bin/env python3
"""
TRACK 19.00 · HR CDL → Transportation backfill (dry-run by default).

Iterates HR `employees` with `cdl_holder=True` and links any that are
not already represented in `transport_persons` (kind=masci_employee).
HR remains the source of truth for identity; this script only creates
the operational shell record.

USAGE (preview, dry-run — safe default):
    cd /app/backend && python3 scripts/track_19_00_link_hr_cdl_to_transport.py

USAGE (commit mode):
    cd /app/backend && python3 scripts/track_19_00_link_hr_cdl_to_transport.py --commit

USAGE (filter to one employee):
    cd /app/backend && python3 scripts/track_19_00_link_hr_cdl_to_transport.py \
        --employee-id c9d7ebc3-a292-4d7a-8765-0ce2739c6029 [--commit]

USAGE (limit batch):
    cd /app/backend && python3 scripts/track_19_00_link_hr_cdl_to_transport.py --limit 25 --commit

Operational guarantees:
    · idempotent — re-running cannot duplicate transport_persons rows
    · respects soft-deleted HR employees (deleted_at != null is skipped)
    · refuses to link non-CDL approved-only employees
    · never overwrites an existing transport_persons document
    · prints a one-line summary plus a per-record audit trail
    · default mode is DRY-RUN — commit must be requested explicitly
    · NOT wired to any boot path / scheduler; operator-run only
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Make `from server import ...` style work when this file is run from
# /app/backend or /app/backend/scripts.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402

TENANT = "masci"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_shell(emp: Dict[str, Any], actor: str) -> Dict[str, Any]:
    full_name = (emp.get("name") or "").strip()
    first, last = "", ""
    if full_name:
        parts = full_name.split(None, 1)
        first = parts[0]
        last = parts[1] if len(parts) > 1 else ""
    first = first or emp.get("first_name") or "Employee"
    canonical_emp_id = str(emp.get("employee_id") or emp.get("id") or "")
    last = last or emp.get("last_name") or canonical_emp_id
    now = _now_iso()
    return {
        "id": uuid.uuid4().hex,
        "tenant": TENANT,
        "kind": "masci_employee",
        "employee_id": canonical_emp_id,
        "carrier_id": None,
        "first_name": first[:120],
        "last_name": last[:120],
        "phone": emp.get("phone"),
        "email": emp.get("email"),
        "license_number": emp.get("cdl_license_number"),
        "cdl_class": emp.get("cdl_class"),
        "status": "pending_review",
        "safety_hold": False,
        "notes": None,
        "linked_from_hr_at": now,
        "linked_from_hr_by": actor,
        "created_at": now,
        "updated_at": now,
        "created_by": actor,
        "updated_by": actor,
    }


async def _resolve_db():
    # Load /app/backend/.env so the script works the same way the
    # FastAPI app does (server.py uses python-dotenv too).
    try:
        from dotenv import load_dotenv  # type: ignore
        load_dotenv(os.path.join(ROOT, ".env"))
    except Exception:
        pass
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    if not mongo_url or not db_name:
        raise SystemExit("MONGO_URL and DB_NAME must be set.")
    client = AsyncIOMotorClient(mongo_url)
    return client, client[db_name]


async def _run(args: argparse.Namespace) -> int:
    client, db = await _resolve_db()
    try:
        query: Dict[str, Any] = {"deleted_at": None, "cdl_holder": True}
        if args.employee_id:
            query["$or"] = [
                {"employee_id": args.employee_id},
                {"id": args.employee_id},
            ]
        candidates: List[Dict[str, Any]] = []
        async for emp in db.employees.find(query):
            candidates.append(emp)
            if args.limit and len(candidates) >= args.limit * 4:
                break

        existing_emp_ids = set()
        async for tp in db.transport_persons.find(
            {"tenant": TENANT, "kind": "masci_employee"},
            {"_id": 0, "employee_id": 1},
        ):
            if tp.get("employee_id"):
                existing_emp_ids.add(str(tp["employee_id"]))

        report = {
            "cdl_found": len(candidates),
            "already_linked": 0,
            "would_create": 0,
            "created": 0,
            "skipped_no_cdl_field": 0,
            "skipped_missing_id": 0,
            "errors": [],
        }
        actions: List[Dict[str, Any]] = []
        actor = "track_19_00_backfill_script"
        for emp in candidates:
            canonical_emp_id = str(emp.get("employee_id") or emp.get("id") or "")
            if not canonical_emp_id:
                report["skipped_missing_id"] += 1
                continue
            if not bool(emp.get("cdl_holder")):
                report["skipped_no_cdl_field"] += 1
                continue
            if canonical_emp_id in existing_emp_ids:
                report["already_linked"] += 1
                actions.append({"employee_id": canonical_emp_id, "name": emp.get("name"), "action": "skip_already_linked"})
                continue
            report["would_create"] += 1
            actions.append({"employee_id": canonical_emp_id, "name": emp.get("name"), "action": "create"})
            if args.commit:
                try:
                    doc = _build_shell(emp, actor)
                    await db.transport_persons.insert_one(doc.copy())
                    existing_emp_ids.add(canonical_emp_id)
                    report["created"] += 1
                except Exception as e:  # noqa: BLE001
                    report["errors"].append({
                        "employee_id": canonical_emp_id,
                        "error": str(e),
                    })
            if args.limit and report["would_create"] >= args.limit:
                break

        mode = "COMMIT" if args.commit else "DRY-RUN"
        print(f"\nTRACK 19.00 backfill · mode={mode}")
        print(f"  HR CDL employees scanned     : {report['cdl_found']}")
        print(f"  already linked (no-op)       : {report['already_linked']}")
        print(f"  would create / created       : {report['would_create']} / {report['created']}")
        print(f"  skipped (missing emp_id)     : {report['skipped_missing_id']}")
        print(f"  skipped (cdl_holder false)   : {report['skipped_no_cdl_field']}")
        if report["errors"]:
            print(f"  errors                       : {len(report['errors'])}")
            for err in report["errors"][:10]:
                print(f"     - {err['employee_id']}: {err['error']}")

        if args.show_actions:
            print("\n  actions:")
            for a in actions[:200]:
                print(f"     {a['action']:<22}  {a['employee_id']}  ({a.get('name')})")

        if not args.commit:
            print("\n  (no writes performed — pass --commit to apply)")
        return 0 if not report["errors"] else 1
    finally:
        client.close()


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Track 19.00 HR CDL → Transportation backfill")
    ap.add_argument("--commit", action="store_true",
                    help="Actually write transport_persons rows (default: dry-run).")
    ap.add_argument("--limit", type=int, default=0,
                    help="Cap the number of would-create rows.")
    ap.add_argument("--employee-id", default=None,
                    help="Run for one HR employee_id only (by employee_id OR id).")
    ap.add_argument("--show-actions", action="store_true",
                    help="Print the per-employee action plan (truncated to 200).")
    return ap.parse_args()


if __name__ == "__main__":
    sys.exit(asyncio.run(_run(_parse_args())))
