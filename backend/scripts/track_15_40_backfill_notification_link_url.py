"""TRACK 15.40 · Notification link_url backfill (one-time idempotent).

Populates the `link_url` field on historical `project_team_assignment`
notifications that were written before the producer was fixed. Does NOT
modify recipients, content, timestamps, or read state. Only fills the
single missing field — and only when it is currently null/empty.

Usage:
    python3 scripts/track_15_40_backfill_notification_link_url.py [--dry-run]

Idempotency:
    Re-running is safe. Rows that already have a `link_url` are skipped.

Verification output:
    BEFORE_COUNT — total project_team_assignment notifications
    NULL_BEFORE  — rows missing link_url
    MODIFIED     — rows updated this run
    SKIPPED      — rows already had link_url (idempotency proof)
    NULL_AFTER   — should be 0 when complete
"""

import asyncio
import os
import sys
from pathlib import Path

# Pin sys.path so we can `import server` / `import lib` if needed.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from motor.motor_asyncio import AsyncIOMotorClient


def _resolve_link(notif: dict) -> str | None:
    """Mirror the producer logic in routes/project_team_assignments.py
    `_notify_assignment` so the backfilled link matches what new rows
    will use going forward.
    """
    pn = (notif.get("linked_project_number") or "").strip()
    if not pn:
        return None
    recipient_role = (notif.get("recipient_role") or "").lower()
    if recipient_role == "pm":
        return f"/pm/projects/{pn}"
    # admin · safety · hr · shop · dispatch · fl all share the admin
    # team page (which is the canonical view for this event type).
    return f"/admin/jobs/{pn}/team"


async def main(dry_run: bool = False):
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    if not mongo_url or not db_name:
        print("ERROR: MONGO_URL and DB_NAME must be set in env")
        sys.exit(1)
    print(f"DB: {db_name}  dry_run: {dry_run}")
    db = AsyncIOMotorClient(mongo_url)[db_name]

    base_query = {"type": "project_team_assignment"}
    before_total = await db.notifications.count_documents(base_query)
    null_before = await db.notifications.count_documents({
        **base_query,
        "$or": [
            {"link_url": None},
            {"link_url": ""},
            {"link_url": {"$exists": False}},
        ],
    })
    print(f"BEFORE_COUNT: {before_total}")
    print(f"NULL_BEFORE:  {null_before}")

    modified = 0
    skipped = 0
    no_link_possible = 0
    samples: list[str] = []

    async for notif in db.notifications.find(base_query, {
        "_id": 1, "id": 1, "link_url": 1, "linked_project_number": 1,
        "recipient_role": 1, "type": 1, "linked_source_module": 1,
    }):
        cur = notif.get("link_url")
        if cur:
            skipped += 1
            continue
        link = _resolve_link(notif)
        if not link:
            no_link_possible += 1
            continue
        # also stamp linked_source_module for traceability when missing
        update_fields = {"link_url": link}
        if not notif.get("linked_source_module"):
            update_fields["linked_source_module"] = "team_assignment"
        if dry_run:
            modified += 1
            if len(samples) < 5:
                samples.append(
                    f"  would update id={notif.get('id')} → {link}"
                )
            continue
        res = await db.notifications.update_one(
            {"_id": notif["_id"]},
            {"$set": update_fields},
        )
        if res.modified_count == 1:
            modified += 1
            if len(samples) < 5:
                samples.append(
                    f"  updated id={notif.get('id')} → {link}"
                )

    null_after = await db.notifications.count_documents({
        **base_query,
        "$or": [
            {"link_url": None},
            {"link_url": ""},
            {"link_url": {"$exists": False}},
        ],
    })
    print(f"MODIFIED:     {modified}")
    print(f"SKIPPED:      {skipped}")
    print(f"NO_LINK_POSS: {no_link_possible}")
    print(f"NULL_AFTER:   {null_after}")
    for s in samples:
        print(s)
    if dry_run:
        print("DRY RUN — no writes performed")


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    asyncio.run(main(dry_run=dry))
