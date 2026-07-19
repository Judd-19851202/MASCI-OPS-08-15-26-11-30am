#!/usr/bin/env python3
"""Guarded Basecamp oversized-file importer.

Dry-run is default. Mutation requires:
- --execute
- --allow-production
- --confirm IMPORT_BASECAMP_DATA
- --backup-ack

This is the oversized-file companion to basecamp_import.py.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import mimetypes
import os
import shutil
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from motor.motor_asyncio import AsyncIOMotorClient

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from lib.operator_safety import (  # noqa: E402
    redact_target_identity,
    require_cli_backup_ack,
    require_cli_confirmation,
    require_cli_execute,
    require_cli_runtime_guard,
)

ROOT = Path(os.environ.get("BASECAMP_EXTRACT_ROOT") or "/tmp/basecamp/extracted")
PROJECT_ID = os.environ.get("BASECAMP_PROJECT_ID") or "24-12"
UPLOADER_ID = os.environ.get("BASECAMP_UPLOADER_ID") or "4eca0a13-0ba1-4b8f-a1dd-23e7515ac836"
MAX_BYTES = int(11.5 * 1024 * 1024)
FOLDER_TO_CAT = {
    "Submittals": "Submittals",
    "Safety": "Safety",
    "Plans & Specs": "Plans & Specs",
    "Attachments": "Plans & Specs",
    "Daily Logs": "Daily Logs",
    "Locate Tickets": "Locate Tickets",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _checksum(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _iter_big_files(root: Path):
    for f in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = f.relative_to(root)
        parts = rel.parts
        category = FOLDER_TO_CAT.get(parts[0]) if parts else None
        size = f.stat().st_size
        if not category or size <= MAX_BYTES:
            continue
        sub = "/".join(parts[1:-1]) if len(parts) > 1 else ""
        display_name = f"{sub}/{f.name}" if sub else f.name
        yield {
            "path": f,
            "relative": str(rel),
            "category": category,
            "size": size,
            "display_name": display_name,
            "checksum": _checksum(f),
        }


def _r2_key_for(project_id: str, doc_id: str, ext: str) -> str:
    proj = "".join(c if c.isalnum() or c in "-_." else "_" for c in project_id)
    return f"project_docs/{proj}/{doc_id}{ext}"


async def _preflight(db) -> dict:
    files = list(_iter_big_files(ROOT))
    existing = await db.docs.count_documents({"project_id": PROJECT_ID, "notes": {"$regex": "^Basecamp big-file import"}})
    return {
        "source_root": str(ROOT),
        "source_snapshot": datetime.now(timezone.utc).isoformat(),
        "oversized_files": len(files),
        "existing_import_docs": existing,
        "sample": files[:5],
    }


async def _execute(db, files, fallback_to_disk: bool) -> dict:
    batch_id = str(uuid.uuid4())
    cleared = await db.docs.delete_many({"project_id": PROJECT_ID, "notes": {"$regex": "^Basecamp big-file import"}})
    inserted = 0
    conflicts = 0
    if fallback_to_disk:
        storage_dir = Path("/app/backend/storage/project_docs") / PROJECT_ID
        storage_dir.mkdir(parents=True, exist_ok=True)
    else:
        import photo_storage  # noqa: PLC0415
        if not photo_storage.is_configured():
            raise RuntimeError("R2 not configured; refusing execute without explicit fallback path.")
    for item in files:
        doc_id = str(uuid.uuid4())
        mime = mimetypes.guess_type(item["path"].name)[0] or "application/octet-stream"
        try:
            if fallback_to_disk:
                target = storage_dir / f"{doc_id}{item['path'].suffix}"
                shutil.copy2(item["path"], target)
                doc = {
                    "id": doc_id,
                    "project_id": PROJECT_ID,
                    "category": item["category"],
                    "filename": item["display_name"],
                    "file_path": str(target),
                    "mime": mime,
                    "size_bytes": item["size"],
                    "notes": f"Basecamp big-file import (disk fallback) · batch {batch_id}",
                    "uploaded_at": now_iso(),
                    "uploaded_by": UPLOADER_ID,
                    "import_batch_id": batch_id,
                }
            else:
                import photo_storage  # noqa: PLC0415
                key = _r2_key_for(PROJECT_ID, doc_id, item['path'].suffix)
                ref = await photo_storage.upload_local_file(str(item["path"]), key=key, content_type=mime)
                doc = {
                    "id": doc_id,
                    "project_id": PROJECT_ID,
                    "category": item["category"],
                    "filename": item["display_name"],
                    "attachment_ref": ref,
                    "storage_kind": "r2",
                    "mime": mime,
                    "size_bytes": item["size"],
                    "notes": f"Basecamp big-file import (R2-direct) · batch {batch_id}",
                    "uploaded_at": now_iso(),
                    "uploaded_by": UPLOADER_ID,
                    "import_batch_id": batch_id,
                }
            await db.docs.insert_one(doc)
            inserted += 1
        except Exception:
            conflicts += 1
    return {"batch_id": batch_id, "cleared": cleared.deleted_count, "inserted": inserted, "conflicts": conflicts}


async def main_async(args) -> int:
    mongo_url = os.environ.get("MONGO_URL") or ""
    db_name = os.environ.get("DB_NAME") or ""
    app_env = os.environ.get("APP_ENV") or ""
    if not mongo_url or not db_name:
        print("ERROR: missing MONGO_URL / DB_NAME", file=sys.stderr)
        return 2
    if not ROOT.exists():
        print(f"ERROR: source root missing: {ROOT}", file=sys.stderr)
        return 3
    target = redact_target_identity(mongo_url, db_name)
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    try:
        preflight = await _preflight(db)
        print(json.dumps({"mode": "dry-run" if not args.execute else "execute", "target": target, "fallback_to_disk": args.fallback_to_disk, "preflight": preflight}, indent=2, default=str))
        if not args.execute:
            return 0
        require_cli_execute(args.execute)
        require_cli_confirmation(args.confirm, expected="IMPORT_BASECAMP_DATA")
        require_cli_backup_ack(args.backup_ack)
        require_cli_runtime_guard(app_env=app_env, db_name=db_name, allow_production=args.allow_production, expected_db_name="masci_safety")
        files = list(_iter_big_files(ROOT))
        if not files:
            print("Refusing execute: no oversized files found.", file=sys.stderr)
            return 4
        result = await _execute(db, files, args.fallback_to_disk)
        print(json.dumps({"ok": result["conflicts"] == 0, "target": target, "result": result}, indent=2))
        return 0 if result["conflicts"] == 0 else 5
    finally:
        client.close()


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--allow-production", action="store_true")
    ap.add_argument("--confirm", default="")
    ap.add_argument("--backup-ack", action="store_true")
    ap.add_argument("--fallback-to-disk", action="store_true")
    return ap.parse_args()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main_async(parse_args())))
