#!/usr/bin/env python3
"""Second-pass Basecamp big-file ingestion — TRACK 24.12 hardening.
====================================================================

Ingest the oversized Basecamp files (>= 11.5 MB) for a project into
Cloudflare R2 and create ``db.docs`` records that reference the R2
key (via ``attachment_ref``). Small-file imports continue to use the
main :mod:`scripts.basecamp_import` module.

TRACK 24.12 · Workstream B · Why this changed
---------------------------------------------
Prior implementation copied every big file into
``/app/backend/storage/project_docs/<project>/`` on the pod's local
disk. In production this filled the disk to 100% during the initial
24-12 backfill and again on every subsequent re-import.

The rewrite streams the bytes directly to R2 via
:func:`photo_storage.upload_local_file` (multipart, 8 MB parts) and
persists ``attachment_ref`` on the doc so the existing download
route in ``routes/tools.py`` serves it via a presigned R2 URL.

Fail-closed behavior
--------------------
If R2 is not configured (missing S3_ENDPOINT_URL / S3_BUCKET /
S3_ACCESS_KEY / S3_SECRET_KEY) the script REFUSES to run rather
than silently falling back to disk. Operators must configure R2 or
explicitly opt into the legacy disk path via
``--fallback-to-disk`` (kept only for one-off recovery scenarios;
NOT recommended for routine imports).

Usage
-----
::

    # Standard R2-direct import (production default)
    cd /app/backend && python3 scripts/basecamp_import_big.py

    # Recovery fallback — writes to disk instead of R2 (LEGACY)
    cd /app/backend && python3 scripts/basecamp_import_big.py --fallback-to-disk
"""
from __future__ import annotations

import argparse
import asyncio
import mimetypes
import os
import shutil
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from motor.motor_asyncio import AsyncIOMotorClient

# Ensure the backend package is importable when the script is run
# from an arbitrary CWD.
_HERE = Path(__file__).resolve()
_BACKEND = _HERE.parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))


ROOT = Path(os.environ.get("BASECAMP_EXTRACT_ROOT") or "/tmp/basecamp/extracted")
PROJECT_ID = os.environ.get("BASECAMP_PROJECT_ID") or "24-12"
UPLOADER_ID = (
    os.environ.get("BASECAMP_UPLOADER_ID")
    or "4eca0a13-0ba1-4b8f-a1dd-23e7515ac836"
)
# Files <= this went via the data-url path (small-file import).
MAX_BYTES = int(11.5 * 1024 * 1024)

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


def _r2_key_for(project_id: str, doc_id: str, ext: str) -> str:
    proj = "".join(c if c.isalnum() or c in "-_." else "_" for c in project_id)
    return f"project_docs/{proj}/{doc_id}{ext}"


async def _import_r2(db, files) -> int:
    """R2-direct path — streams each file to R2 and persists an
    ``attachment_ref`` on the doc. NEVER writes to local disk."""
    import photo_storage  # noqa: PLC0415

    if not photo_storage.is_configured():
        raise RuntimeError(
            "photo_storage / R2 is not configured. Refusing to import: the "
            "prior disk-backed path is what filled the pod disk. Set "
            "S3_ENDPOINT_URL / S3_BUCKET / S3_ACCESS_KEY / S3_SECRET_KEY or "
            "re-run with --fallback-to-disk (legacy, not recommended)."
        )

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
        ext = f.suffix
        key = _r2_key_for(PROJECT_ID, doc_id, ext)
        mime = mimetypes.guess_type(f.name)[0] or "application/octet-stream"

        # Stream to R2 (multipart under the hood). Bytes never touch
        # the pod's local disk beyond the source file itself, which
        # already existed (this script does not create it).
        ref = await photo_storage.upload_local_file(
            str(f), key=key, content_type=mime,
        )

        doc: Dict[str, Any] = {
            "id": doc_id,
            "project_id": PROJECT_ID,
            "category": category,
            "filename": display_name,
            # TRACK 24.12 · file_path intentionally OMITTED. The
            # download route reads attachment_ref first and mints a
            # presigned R2 URL — no disk hop, no disk growth.
            "attachment_ref": ref,
            "storage_kind": "r2",
            "mime": mime,
            "size_bytes": size,
            "notes": (
                f"Basecamp big-file import (R2-direct) · "
                f"{datetime.now().date().isoformat()}"
            ),
            "uploaded_at": now_iso(),
            "uploaded_by": UPLOADER_ID,
        }
        await db.docs.insert_one(doc)
        inserted += 1
        print(
            f"  + {size / 1024 / 1024:6.1f} MB · [{category}] "
            f"{display_name}  →  {ref}"
        )
    return inserted


async def _import_disk(db, files) -> int:
    """Legacy disk-backed path — kept only behind --fallback-to-disk.
    Emits a big fat warning so operators never forget this is the
    behavior that filled the disk to 100% in production."""
    print(
        "  ⚠ LEGACY DISK PATH — files will land on the pod filesystem. "
        "This is what caused the 24.12 disk-full incident.",
        file=sys.stderr,
    )
    storage_dir = Path("/app/backend/storage/project_docs") / PROJECT_ID
    storage_dir.mkdir(parents=True, exist_ok=True)
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
        ext = f.suffix
        target = storage_dir / f"{doc_id}{ext}"
        shutil.copy2(f, target)
        mime = mimetypes.guess_type(f.name)[0] or "application/octet-stream"
        await db.docs.insert_one({
            "id": doc_id, "project_id": PROJECT_ID, "category": category,
            "filename": display_name, "file_path": str(target),
            "mime": mime, "size_bytes": size,
            "notes": f"Basecamp big-file import (disk fallback) · "
                     f"{datetime.now().date().isoformat()}",
            "uploaded_at": now_iso(), "uploaded_by": UPLOADER_ID,
        })
        inserted += 1
        print(f"  + {size / 1024 / 1024:6.1f} MB · [{category}] {display_name}")
    return inserted


async def main(args) -> int:
    client = AsyncIOMotorClient(
        os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    )
    db = client[os.environ.get("DB_NAME", "test_database")]

    # Idempotency: clear any prior big-file imports first.
    cleared = await db.docs.delete_many({
        "project_id": PROJECT_ID,
        "notes": {"$regex": "^Basecamp big-file import"},
    })
    if cleared.deleted_count:
        print(f"  (cleared {cleared.deleted_count} prior big-file docs)")

    files = sorted(p for p in ROOT.rglob("*") if p.is_file())
    if args.fallback_to_disk:
        inserted = await _import_disk(db, files)
    else:
        inserted = await _import_r2(db, files)

    print()
    print(f"✓ Inserted {inserted} oversized files "
          f"({'DISK' if args.fallback_to_disk else 'R2'} backed)")

    print()
    print("Final library by category:")
    for cat in ["Submittals", "Plans & Specs", "Safety", "Daily Logs",
                "Pictures & Drone", "Locate Tickets", "General"]:
        n = await db.docs.count_documents(
            {"project_id": PROJECT_ID, "category": cat}
        )
        if n:
            print(f"    {cat:20s} {n}")
    return 0


def _parse_args():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--fallback-to-disk", action="store_true",
        help=(
            "Legacy path — write to /app/backend/storage/project_docs "
            "instead of R2. NOT RECOMMENDED. Kept only for recovery."
        ),
    )
    return ap.parse_args()


if __name__ == "__main__":
    _args = _parse_args()
    raise SystemExit(asyncio.run(main(_args)))
