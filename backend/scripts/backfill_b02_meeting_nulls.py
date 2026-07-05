"""TRACK 22.4b-followup-Safety · B-02 backfill.

Repairs the legacy Safety Meeting attendee corpus in place.

Root cause (pre TRACK 15.73 slice 2)
------------------------------------
Meetings inserted before the Slice-2 attendee normalization guard did
not carry ``company``, ``attendee_type``, ``is_masci_employee``, or
``review_status``. This produced a 43-meeting / 160-attendee legacy
tail of records that show blank company columns in reports.

Repair rules
------------
For every meeting attendee where ``company`` is null or empty:

1. If the attendee's ``employee_id`` still resolves to a row in
   ``employees``: lock ``company="MASCI"``, set
   ``is_masci_employee=True``, ``attendee_type="employee"``,
   ``source="employee_master"``, ``review_status=""``.

2. Else if the attendee's ``name`` (case-insensitive trimmed) matches
   exactly one row in ``employees``: same promotion as (1), plus
   backfill the ``employee_id``.

3. Else if the attendee's ``non_masci`` flag is True: leave
   ``company`` untouched (it may still be blank for legacy
   subcontractor rows) but tag ``attendee_type="subcontractor"``,
   ``review_status="needs_review"`` — subcontractor rows without a
   company still require human attention.

4. Otherwise: mark ``attendee_type="manual"``,
   ``review_status="needs_review"``. Company stays blank; this signals
   the safety admin queue to resolve identity.

Doctrine
--------
- **Idempotent.** Re-running produces zero diffs after the first
  successful pass.
- **Dry-run capable.** Pass ``--dry-run`` to preview updates without
  writing.
- **Preview-safe.** Refuses to run when APP_ENV=production unless
  ``--allow-production`` is explicitly passed.
- **No fabrication.** Never invents a company for an attendee that
  cannot be tied to an employees row.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from typing import Any

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")

TENANT_COMPANY_NAME = "MASCI"


def _print_summary(counts: dict[str, int]) -> None:
    print("── TRACK 22.4b-followup-Safety B-02 backfill summary ──")
    for k, v in counts.items():
        print(f"  {k:32s} {v}")


async def run(dry_run: bool, allow_production: bool) -> int:
    app_env = (os.environ.get("APP_ENV") or "").strip().lower()
    if app_env == "production" and not allow_production:
        print(f"REFUSING to run: APP_ENV={app_env!r}. Use --allow-production to override.")
        return 2

    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    if not mongo_url or not db_name:
        print("MONGO_URL / DB_NAME are missing from the environment.")
        return 3

    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    # Preload a name→id lookup (case-insensitive) for name-based promotion.
    name_index: dict[str, list[dict]] = {}
    async for emp in db.employees.find(
        {"name": {"$exists": True}},
        {"_id": 0, "id": 1, "name": 1, "is_active": 1},
    ):
        key = (emp.get("name") or "").strip().lower()
        if key:
            name_index.setdefault(key, []).append(emp)

    id_index: dict[str, dict] = {}
    async for emp in db.employees.find(
        {},
        {"_id": 0, "id": 1, "name": 1, "is_active": 1},
    ):
        eid = emp.get("id")
        if eid:
            id_index[eid] = emp

    counts = {
        "meetings_scanned": 0,
        "meetings_touched": 0,
        "attendees_scanned": 0,
        "attendees_needing_repair": 0,
        "repaired_via_employee_id": 0,
        "repaired_via_name": 0,
        "tagged_subcontractor_needs_review": 0,
        "tagged_manual_needs_review": 0,
        "would_write_updates": 0,
    }

    async for meeting in db.meetings.find({}):
        counts["meetings_scanned"] += 1
        attendees = meeting.get("attendees") or []
        new_attendees: list[dict] = []
        touched = False

        for att in attendees:
            counts["attendees_scanned"] += 1
            if not isinstance(att, dict):
                new_attendees.append(att)
                continue
            row = dict(att)
            company = (row.get("company") or "").strip()
            attendee_type = (row.get("attendee_type") or "").strip()
            already_normalized = (
                attendee_type in {"employee", "subcontractor", "manual"}
                and "is_masci_employee" in row
                and "review_status" in row
            )
            needs_repair = (not company and not already_normalized) or (
                not attendee_type or "is_masci_employee" not in row
            )
            if not needs_repair:
                new_attendees.append(row)
                continue
            counts["attendees_needing_repair"] += 1
            eid = (row.get("employee_id") or "").strip()
            non_masci = bool(row.get("non_masci"))

            emp = id_index.get(eid) if eid else None
            if emp is None and not eid and not non_masci:
                key = (row.get("name") or "").strip().lower()
                matches = name_index.get(key) or []
                if len(matches) == 1:
                    emp = matches[0]
                    eid = emp.get("id") or ""
                    row["employee_id"] = eid

            if emp is not None and not non_masci:
                # Resolved MASCI employee.
                row["company"] = TENANT_COMPANY_NAME
                row["non_masci"] = False
                row["attendee_type"] = "employee"
                row["source"] = "employee_master"
                row["is_masci_employee"] = True
                row["is_subcontractor"] = False
                row["is_manual"] = False
                row["review_status"] = ""
                if row.get("employee_id") != (emp.get("id") or ""):
                    row["employee_id"] = emp.get("id") or ""
                counts["repaired_via_employee_id" if att.get("employee_id") else "repaired_via_name"] += 1
                touched = True
            elif non_masci:
                # Subcontractor with legacy blank company — flag but don't invent.
                row["attendee_type"] = "subcontractor"
                row["source"] = "subcontractor_directory"
                row["is_masci_employee"] = False
                row["is_subcontractor"] = True
                row["is_manual"] = False
                if not (row.get("company") or "").strip():
                    row["review_status"] = "needs_review"
                counts["tagged_subcontractor_needs_review"] += 1
                touched = True
            else:
                # Unresolvable manual entry — flag for admin review, no fabrication.
                row["employee_id"] = ""
                row["non_masci"] = False
                row["attendee_type"] = "manual"
                row["source"] = "manual"
                row["is_masci_employee"] = False
                row["is_subcontractor"] = False
                row["is_manual"] = True
                row["review_status"] = "needs_review"
                counts["tagged_manual_needs_review"] += 1
                touched = True
            new_attendees.append(row)

        if touched:
            counts["meetings_touched"] += 1
            counts["would_write_updates"] += 1
            if not dry_run:
                await db.meetings.update_one(
                    {"_id": meeting["_id"]},
                    {"$set": {"attendees": new_attendees}},
                )

    _print_summary(counts)
    if dry_run:
        print("\nDRY RUN — no writes performed. Re-run without --dry-run to apply.")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="scan only, do not write")
    ap.add_argument("--allow-production", action="store_true", help="explicit override")
    args = ap.parse_args()
    sys.exit(asyncio.run(run(dry_run=args.dry_run, allow_production=args.allow_production)))


if __name__ == "__main__":
    main()
