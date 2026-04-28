#!/usr/bin/env python3
"""Second-pass: ingest the 13 oversized Basecamp files for project 24-12
into disk storage at /app/backend/storage/project_docs/24-12/, and create
db.docs records that reference file_path instead of file_data.

The download endpoint in tools.py now streams from disk when file_path
is set, so these big plan sets show up alongside the rest of the library.
"""

import asyncio, mimetypes, os, sys, uuid, shutil
from datetime import datetime, timezone
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient

ROOT = Path("/tmp/basecamp/extracted")
PROJECT_ID = "24-12"
UPLOADER_ID = "4eca0a13-0ba1-4b8f-a1dd-23e7515ac836"  # Jaymn Judd
STORAGE_DIR = Path("/app/backend/storage/project_docs") / PROJECT_ID
MAX_BYTES = int(11.5 * 1024 * 1024)  # files <= this went via the data-url path

FOLDER_TO_CAT = {
    "Submittals":      "Submittals",
    "Safety":          "Safety",
    "Plans & Specs":   "Plans & Specs",
    "Attachments":     "Plans & Specs",
    "Daily Logs":      "Daily Logs",
    "Locate Tickets":  "Locate Tickets",
}

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

async def main():
    client = AsyncIOMotorClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))
    db = client[os.environ.get("DB_NAME", "test_database")]
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)

    # Idempotency: clear any prior big-file imports first.
    cleared = await db.docs.delete_many({
        "project_id": PROJECT_ID,
        "notes": {"$regex": "^Basecamp big-file import"},
    })
    if cleared.deleted_count:
        print(f"  (cleared {cleared.deleted_count} prior big-file docs)")

    files = sorted(p for p in ROOT.rglob("*") if p.is_file())
    inserted = 0
    for f in files:
        size = f.stat().st_size
        if size <= MAX_BYTES:
            continue
        rel = f.relative_to(ROOT)
        parts = rel.parts
        category = FOLDER_TO_CAT.get(parts[0])
        if not category:
            continue
        sub = "/".join(parts[1:-1])
        display_name = f"{sub}/{f.name}" if sub else f.name

        doc_id = str(uuid.uuid4())
        # Disk-safe filename to avoid encoding issues in path
        ext = f.suffix
        target = STORAGE_DIR / f"{doc_id}{ext}"
        shutil.copy2(f, target)

        mime = mimetypes.guess_type(f.name)[0] or "application/octet-stream"
        doc = {
            "id": doc_id,
            "project_id": PROJECT_ID,
            "category": category,
            "filename": display_name,
            "file_path": str(target),  # disk-backed (NEW field)
            "mime": mime,
            "size_bytes": size,
            "notes": f"Basecamp big-file import · {datetime.now().date().isoformat()}",
            "uploaded_at": now_iso(),
            "uploaded_by": UPLOADER_ID,
        }
        await db.docs.insert_one(doc)
        inserted += 1
        print(f"  + {size/1024/1024:6.1f} MB · [{category}] {display_name}")

    print()
    print(f"✓ Inserted {inserted} oversized files (disk-backed)")
    print(f"  Storage dir: {STORAGE_DIR}  ({sum(f.stat().st_size for f in STORAGE_DIR.iterdir())/1024/1024:.0f} MB on disk)")

    print()
    print("Final library by category:")
    for cat in ["Submittals", "Plans & Specs", "Safety", "Daily Logs", "Pictures & Drone", "Locate Tickets", "General"]:
        n = await db.docs.count_documents({"project_id": PROJECT_ID, "category": cat})
        if n:
            print(f"    {cat:20s} {n}")

if __name__ == "__main__":
    asyncio.run(main())
