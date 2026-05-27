#!/usr/bin/env python3
"""verify_no_contamination.py — iter437 · 2026-02 · permanent deploy gate

After the 2026-02 production contamination cleanup, the operator
demanded that contamination NEVER re-accumulate in production silently.
This script is wired into the pre-deploy gate. It probes the
production database for the EXACT contamination patterns that were
cleaned up and aborts the deploy if any has re-appeared above a
small tolerance.

Doctrine:
  Zero tolerance for the equipment-prefix contamination
  (TST-/PE-) and zero tolerance for the operator-test names
  (Office Jane / Steve Office / Maria Mobile / Brand Check).

Patterns checked:
  - notifications.title  matching ^Failed pre-op — (TST-|PE-...)
  - tasks.title          matching ^Failed pre-op — (TST-|PE-...)
  - field_leadership_records WHERE employee_name IN (test-name-list)
  - time_off_public_links    WHERE employee_name IN (test-name-list)

Optional check (when --strict):
  - notifications created in the last 24h with the same pattern
    must be zero (prevents a SLOW re-leak that creeps back in)

Exit codes:
  0 — clean (deploy may proceed)
  1 — contamination detected (deploy MUST be blocked)
  2 — DB unreachable / config error
"""
from __future__ import annotations

import argparse
import asyncio
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from motor.motor_asyncio import AsyncIOMotorClient


def _load_env() -> None:
    for line in Path("/app/backend/.env").read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_env()

# Targets
TARGET_DB = "masci_safety"
TST_PE_RX = r"^(New task: )?Failed pre-op — (TST-[A-Z0-9]+|PE-[a-f0-9]{6,})"
TEST_NAMES = ["Office Jane", "Steve Office", "Maria Mobile", "Brand Check"]


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--target", default=TARGET_DB,
        help="DB to probe (defaults to production). Useful for testing in preview.",
    )
    parser.add_argument(
        "--strict", action="store_true",
        help="Also fail if ANY TST/PE notification was created in the last 24h",
    )
    parser.add_argument(
        "--tolerance", type=int, default=0,
        help="Max contamination rows allowed before failure (default 0)",
    )
    args = parser.parse_args()

    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[args.target]

    print(f"\n══════════════════════════════════════════════════════════════")
    print(f"  iter437 · post-deploy contamination probe")
    print(f"  target db    : {db.name}")
    print(f"  tolerance    : {args.tolerance} rows")
    print(f"  strict mode  : {args.strict}")
    print(f"══════════════════════════════════════════════════════════════\n")

    findings: list[tuple[str, int]] = []

    # 1. notifications with TST/PE pattern
    n_notif = await db.notifications.count_documents(
        {"title": {"$regex": TST_PE_RX, "$options": "i"}}
    )
    findings.append(("notifications · TST/PE pre-op", n_notif))

    # 2. tasks with TST/PE pattern
    n_tasks = await db.tasks.count_documents(
        {"title": {"$regex": TST_PE_RX, "$options": "i"}}
    )
    findings.append(("tasks · TST/PE pre-op", n_tasks))

    # 3. field-leadership-records w/ test employee names
    n_flr = await db.field_leadership_records.count_documents(
        {"employee_name": {"$in": TEST_NAMES}, "kind": "time_off_request"}
    )
    findings.append(("field_leadership_records · test-name TO requests", n_flr))

    # 4. time-off public links w/ test employee names
    n_links = await db.time_off_public_links.count_documents(
        {"employee_name": {"$in": TEST_NAMES}}
    )
    findings.append(("time_off_public_links · test names", n_links))

    # 5. (strict mode only) very-recent TST/PE notifications
    if args.strict:
        since = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
        n_recent = await db.notifications.count_documents({
            "title": {"$regex": TST_PE_RX, "$options": "i"},
            "$or": [
                {"created_at": {"$gte": since}},
                {"created_at": {"$gte": datetime.now(timezone.utc) - timedelta(hours=24)}},
            ],
        })
        findings.append(("notifications · TST/PE created last 24h (strict)", n_recent))

    # Render the report
    fail = False
    for label, count in findings:
        status = "✅" if count <= args.tolerance else "❌"
        print(f"  {status}  {label:55s}  count={count}")
        if count > args.tolerance:
            fail = True

    print()
    if fail:
        print("❌ POST-DEPLOY CONTAMINATION PROBE FAILED — DEPLOY BLOCKED")
        print("   Re-run /app/scripts/scan_production_contamination.py for a full report,")
        print("   then /app/scripts/cleanup_production_contamination.py to clean.")
        return 1

    print("🟢 contamination probe clean · deploy may proceed")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
