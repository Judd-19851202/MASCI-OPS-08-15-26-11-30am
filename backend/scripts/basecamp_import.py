#!/usr/bin/env python3
"""Guarded Basecamp import for project docs.

Dry-run is the default. Mutation requires:
- --execute
- --allow-production
- --confirm IMPORT_BASECAMP_DATA
- --backup-ack

This entry point is the canonical small-file importer. It never executes
in tests here; tests only assert guard semantics and discovery coverage.
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import hashlib
import json
import mimetypes
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

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


def _iter_files(root: Path):
    for f in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = f.relative_to(root)
        parts = rel.parts
        category = FOLDER_TO_CAT.get(parts[0]) if parts else None
        size = f.stat().st_size
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


async def _preflight(db, root: Path) -> Dict[str, Any]:
    files = list(_iter_files(root))
    project = await db.projects.find_one({"id": PROJECT_ID}, {"_id": 0, "id": 1, "name": 1})
    uploader = await db.users.find_one({"id": UPLOADER_ID}, {"_id": 0, "id": 1, "name": 1})
    valid = [f for f in files if f["category"] and 0 < f["size"] <= MAX_BYTES]
    oversized = [f for f in files if f["size"] > MAX_BYTES]
    invalid = [f for f in files if not f["category"] or f["size"] == 0]
    existing = await db.docs.count_documents({"project_id": PROJECT_ID, "notes": {"$regex": "^Basecamp import"}})
    return {
        "project_exists": bool(project),
        "uploader_exists": bool(uploader),
        "project": project,
        "uploader": uploader,
        "source_root": str(root),
        "source_snapshot": datetime.now(timezone.utc).isoformat(),
        "source_total": len(files),
        "valid": len(valid),
        "oversized": len(oversized),
        "invalid": len(invalid),
        "existing_import_docs": existing,
        "sample": valid[:5],
    }


async def _execute(db, root: Path) -> Dict[str, Any]:
    files = [f for f in _iter_files(root) if f["category"] and 0 < f["size"] <= MAX_BYTES]
    batch_id = str(uuid.uuid4())
    await db.project_memberships.update_one(
        {"project_id": PROJECT_ID, "user_id": UPLOADER_ID},
        {"$setOnInsert": {"id": str(uuid.uuid4()), "project_id": PROJECT_ID, "user_id": UPLOADER_ID, "added_at": now_iso()}},
        upsert=True,
    )
    cleared = await db.docs.delete_many({"project_id": PROJECT_ID, "notes": {"$regex": "^Basecamp import"}})
    inserted = 0
    conflicts = 0
    for item in files:
        raw = item["path"].read_bytes()
        mime = mimetypes.guess_type(item["path"].name)[0] or "application/octet-stream"
        data_url = f"data:{mime};base64,{base64.b64encode(raw).decode('ascii')}"
        doc = {
            "id": str(uuid.uuid4()),
            "project_id": PROJECT_ID,
            "category": item["category"],
            "filename": item["display_name"],
            "file_data": data_url,
            "mime": mime,
            "size_bytes": item["size"],
            "notes": f"Basecamp import · batch {batch_id} · {datetime.now(timezone.utc).date().isoformat()}",
            "uploaded_at": now_iso(),
            "uploaded_by": UPLOADER_ID,
            "import_batch_id": batch_id,
            "import_checksum": item["checksum"],
        }
        try:
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
        print("ERROR: MONGO_URL / DB_NAME missing", file=sys.stderr)
        return 2
    if not ROOT.exists():
        print(f"ERROR: source root missing: {ROOT}", file=sys.stderr)
        return 3
    target = redact_target_identity(mongo_url, db_name)
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    try:
        preflight = await _preflight(db, ROOT)
        print(json.dumps({"mode": "dry-run" if not args.execute else "execute", "target": target, "preflight": preflight}, indent=2, default=str))
        if not args.execute:
            return 0
        require_cli_execute(args.execute)
        require_cli_confirmation(args.confirm, expected="IMPORT_BASECAMP_DATA")
        require_cli_backup_ack(args.backup_ack)
        require_cli_runtime_guard(app_env=app_env, db_name=db_name, allow_production=args.allow_production, expected_db_name="masci_safety")
        if not preflight["project_exists"] or not preflight["uploader_exists"] or preflight["valid"] == 0:
            print("Refusing execute: preflight prerequisites failed or empty valid input.", file=sys.stderr)
            return 4
        result = await _execute(db, ROOT)
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
    return ap.parse_args()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main_async(parse_args())))
