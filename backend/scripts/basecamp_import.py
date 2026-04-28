#!/usr/bin/env python3
"""One-off Basecamp import for project 24-12 (Oxford Rd).

Walks /tmp/basecamp/extracted/, classifies each file by top-level folder,
and inserts into db.docs as a data URL — same shape /api/projects/{id}/docs
produces. Files larger than the BSON-safe limit are skipped and listed at
the end so the user can decide (move to disk, upload manually, etc.).
"""

import asyncio, base64, mimetypes, os, sys, uuid
from datetime import datetime, timezone
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient

ROOT = Path("/tmp/basecamp/extracted")
PROJECT_ID = "24-12"
UPLOADER_ID = "4eca0a13-0ba1-4b8f-a1dd-23e7515ac836"  # Jaymn Judd
# 11.5 MB raw → ~15.3 MB base64 → safely under MongoDB's 16 MB BSON limit.
MAX_BYTES = int(11.5 * 1024 * 1024)

# Map top-level folder name → DOC_CATEGORIES
FOLDER_TO_CAT = {
    "Submittals":      "Submittals",
    "Safety":          "Safety",
    "Plans & Specs":   "Plans & Specs",
    "Attachments":     "Plans & Specs",   # tp3 trimble export goes with plans
    "Daily Logs":      "Daily Logs",
    "Locate Tickets":  "Locate Tickets",
}

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

async def main():
    client = AsyncIOMotorClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))
    db = client[os.environ.get("DB_NAME", "test_database")]

    # Sanity: project exists?
    proj = await db.projects.find_one({"id": PROJECT_ID})
    if not proj:
        print(f"ERROR: project {PROJECT_ID} not found")
        sys.exit(1)
    print(f"✓ Project: {proj.get('name')} (id={PROJECT_ID})")

    # Sanity: uploader exists?
    user = await db.users.find_one({"id": UPLOADER_ID}, {"_id": 0, "name": 1})
    if not user:
        print(f"ERROR: uploader {UPLOADER_ID} not found")
        sys.exit(1)
    print(f"✓ Uploader: {user.get('name')}")

    # Make sure user is a project member (otherwise checks would fail in API,
    # but we're inserting directly so we just want activity log to work.)
    await db.project_memberships.update_one(
        {"project_id": PROJECT_ID, "user_id": UPLOADER_ID},
        {"$setOnInsert": {
            "id": str(uuid.uuid4()),
            "project_id": PROJECT_ID,
            "user_id": UPLOADER_ID,
            "added_at": now_iso(),
        }},
        upsert=True,
    )

    # Optional: clear any prior basecamp imports for this project so this is
    # idempotent on re-run.
    cleared = await db.docs.delete_many({
        "project_id": PROJECT_ID,
        "notes": {"$regex": "^Basecamp import"},
    })
    if cleared.deleted_count:
        print(f"  (cleared {cleared.deleted_count} prior basecamp-imported docs)")

    files = sorted(p for p in ROOT.rglob("*") if p.is_file())
    print(f"  scanning {len(files)} files…")

    inserted = 0
    skipped_big: list[tuple[Path, int]] = []
    skipped_other: list[tuple[Path, str]] = []

    for f in files:
        rel = f.relative_to(ROOT)
        parts = rel.parts
        top = parts[0]
        category = FOLDER_TO_CAT.get(top)
        if not category:
            skipped_other.append((rel, "unknown folder"))
            continue
        size = f.stat().st_size
        if size == 0:
            skipped_other.append((rel, "empty"))
            continue
        if size > MAX_BYTES:
            skipped_big.append((rel, size))
            continue

        # If the file lives in a subfolder (e.g. Safety/Meetings/foo.pdf),
        # prepend the folder path to the filename so it stays organised.
        sub = "/".join(parts[1:-1])
        display_name = f"{sub}/{f.name}" if sub else f.name

        try:
            raw = f.read_bytes()
        except Exception as e:
            skipped_other.append((rel, f"read error: {e}"))
            continue

        mime = mimetypes.guess_type(f.name)[0] or "application/octet-stream"
        data_url = f"data:{mime};base64,{base64.b64encode(raw).decode('ascii')}"

        doc = {
            "id": str(uuid.uuid4()),
            "project_id": PROJECT_ID,
            "category": category,
            "filename": display_name,
            "file_data": data_url,
            "mime": mime,
            "size_bytes": size,
            "notes": f"Basecamp import · {datetime.now().date().isoformat()}",
            "uploaded_at": now_iso(),
            "uploaded_by": UPLOADER_ID,
        }
        try:
            await db.docs.insert_one(doc)
            inserted += 1
            if inserted % 25 == 0:
                print(f"    inserted {inserted}…")
        except Exception as e:
            skipped_other.append((rel, f"insert error: {e}"))

    print()
    print(f"✓ Inserted {inserted} files into project {PROJECT_ID}")
    print()
    print(f"⚠ Skipped {len(skipped_big)} oversized files (>11.5 MB — Mongo BSON limit):")
    for p, s in skipped_big:
        print(f"    {s/1024/1024:6.1f} MB · {p}")
    if skipped_other:
        print()
        print(f"⚠ Skipped {len(skipped_other)} other:")
        for p, why in skipped_other:
            print(f"    {why}: {p}")

    # Show what's now in this project's library, by category
    print()
    print("Library by category:")
    for cat in ["Submittals", "Plans & Specs", "Safety", "Daily Logs", "Pictures & Drone", "Locate Tickets", "General"]:
        n = await db.docs.count_documents({"project_id": PROJECT_ID, "category": cat})
        if n:
            print(f"    {cat:20s} {n}")

if __name__ == "__main__":
    asyncio.run(main())
