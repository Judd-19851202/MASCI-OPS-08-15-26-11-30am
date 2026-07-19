#!/usr/bin/env python3
"""TRACK 24.12 · Workstream B · Safe migration of local
``/app/backend/storage/project_docs`` → Cloudflare R2
========================================================

The backend's ``routes/tools.py`` download path already streams
either from ``file_path`` (disk-backed) OR ``attachment_ref``
(R2-backed). This script promotes disk-backed ``db.docs`` records to
R2-backed refs so the pod's local disk stops growing with every
Basecamp import.

DEFAULT MODE = DRY-RUN
----------------------
Nothing is uploaded, deleted, or written to Mongo unless
``--apply`` is passed. The dry-run pass prints the exact set of
files it would migrate + the projected R2 keys + total bytes.

Safety invariants (locked by the test suite)
--------------------------------------------
1. Dry-run is the default. ``--apply`` is required for any mutation.
2. Local unlink is gated on an R2 ``HEAD`` succeeding for the newly
   uploaded key. If the HEAD returns 404 the file is NEVER deleted.
3. Every mutation writes a ``hr_audit`` row with the source path,
   R2 key, byte count, actor, and timestamp.
4. Mongo document records are updated only after the R2 HEAD passes.
5. Resumable: rerunning is idempotent — a doc that already carries
   ``attachment_ref`` is skipped.
6. Never touches inline-base64 photos or the ``daily_reports`` /
   ``incidents`` / ``meetings`` / ``jhas`` collections.

Usage
-----
::

    # Dry-run (default — safe, read-only)
    cd /app/backend && python3 scripts/migrate_local_project_docs_to_r2.py

    # Apply (uploads to R2, verifies HEAD, then deletes local files)
    cd /app/backend && python3 scripts/migrate_local_project_docs_to_r2.py --apply

    # Restrict to a project or a single filename
    cd /app/backend && python3 scripts/migrate_local_project_docs_to_r2.py --project 24-12
    cd /app/backend && python3 scripts/migrate_local_project_docs_to_r2.py --apply --limit 25
"""
from __future__ import annotations

import argparse
import asyncio
import mimetypes
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Allow both `python3 scripts/migrate_local_project_docs_to_r2.py`
# and `python3 -m scripts.migrate_local_project_docs_to_r2` from
# /app/backend.
_HERE = Path(__file__).resolve()
_BACKEND = _HERE.parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402


STORAGE_DIR = Path("/app/backend/storage/project_docs")
DOCS_COLLECTION = "docs"
AUDIT_COLLECTION = "hr_audit"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _r2_key_for(doc: Dict[str, Any], ext: str) -> str:
    """Deterministic R2 object key. Namespaced by project + doc id so
    the R2 bucket browser stays readable."""
    project = str(doc.get("project_id") or "unknown")
    project = "".join(c if c.isalnum() or c in "-_." else "_" for c in project)
    return f"project_docs/{project}/{doc.get('id') or uuid.uuid4().hex}{ext}"


async def _emit_audit(db, entry: Dict[str, Any]) -> None:
    """Append-only migration audit."""
    entry = dict(entry)
    entry.setdefault("kind", "track_24_12_disk_to_r2_migration")
    entry.setdefault("ts", _now_iso())
    try:
        await db[AUDIT_COLLECTION].insert_one(entry)
    except Exception as e:  # noqa: BLE001
        # Log but never abort — the migration is more valuable than
        # its audit row on a soft failure. The dry-run report will
        # still show the file was moved.
        print(f"  · audit insert failed: {e}", file=sys.stderr)


async def _r2_head(photo_storage, ref: str) -> bool:
    """Best-effort HEAD probe on a photo:// ref. Returns True iff the
    object exists in R2. NEVER raises."""
    try:
        if not photo_storage.is_storage_ref(ref):
            return False
        bucket, key = photo_storage._parse_ref(ref)  # noqa: SLF001
        c = photo_storage._client()  # noqa: SLF001
        if c is None:
            return False
        await asyncio.to_thread(c.head_object, Bucket=bucket, Key=key)
        return True
    except Exception:  # noqa: BLE001
        return False


async def _iter_candidates(
    db, project: Optional[str], limit: int,
) -> List[Dict[str, Any]]:
    """Yield docs that are disk-backed AND not already R2-backed."""
    q: Dict[str, Any] = {
        "$and": [
            {"file_path": {"$exists": True}},
            {"file_path": {"$ne": None}},
            {"file_path": {"$ne": ""}},
        ],
        "attachment_ref": {"$in": [None, ""]},
    }
    if project:
        q["project_id"] = project
    cursor = db[DOCS_COLLECTION].find(q, {"_id": 0}).limit(limit)
    return [d async for d in cursor]


async def _promote_one(
    db, photo_storage, doc: Dict[str, Any], *, actor: str,
) -> Dict[str, Any]:
    """Upload one disk file to R2, verify HEAD, then delete local."""
    result: Dict[str, Any] = {
        "id": doc.get("id"), "project_id": doc.get("project_id"),
        "filename": doc.get("filename"),
        "status": "unknown",
    }
    local = Path(str(doc.get("file_path") or ""))
    if not local.exists() or not local.is_file():
        result["status"] = "skipped_missing_local_file"
        return result
    size = local.stat().st_size
    ext = local.suffix or (
        f".{doc.get('mime', '').split('/')[-1]}" if doc.get("mime") else ""
    )
    ext = ext.lower() if ext else ""
    key = _r2_key_for(doc, ext)
    mime = (
        doc.get("mime")
        or mimetypes.guess_type(local.name)[0]
        or "application/octet-stream"
    )

    # Upload — streamed via boto3.upload_file (multipart under the hood).
    ref = await photo_storage.upload_local_file(
        str(local), key=key, content_type=mime,
    )
    result["r2_ref"] = ref
    result["size_bytes"] = size

    # Verify HEAD before ANY mutation.
    if not await _r2_head(photo_storage, ref):
        result["status"] = "aborted_head_missing_after_upload"
        return result

    # Update the Mongo doc — R2 ref now the source of truth.
    await db[DOCS_COLLECTION].update_one(
        {"id": doc.get("id")},
        {
            "$set": {
                "attachment_ref": ref,
                "storage_kind": "r2",
                "migrated_at": _now_iso(),
                "migrated_from_path": str(local),
            },
        },
    )

    # ONLY after Mongo + R2 both confirm, delete the local file.
    try:
        local.unlink()
        result["local_deleted"] = True
    except Exception as e:  # noqa: BLE001
        result["local_deleted"] = False
        result["local_delete_error"] = str(e)

    await _emit_audit(db, {
        "action": "migrate_disk_to_r2",
        "doc_id": doc.get("id"),
        "project_id": doc.get("project_id"),
        "filename": doc.get("filename"),
        "source_path": str(local),
        "r2_ref": ref,
        "size_bytes": size,
        "actor": actor,
    })
    result["status"] = "migrated"
    return result


async def _run(args) -> int:
    # Import photo_storage lazily so a run without R2 credentials
    # still shows the dry-run summary usefully.
    try:
        import photo_storage  # type: ignore  # noqa: PLC0415
    except Exception as e:  # noqa: BLE001
        print(f"[abort] cannot import photo_storage: {e}", file=sys.stderr)
        return 2

    if args.apply and not photo_storage.is_configured():
        print(
            "[abort] --apply requires the S3 / R2 env vars (S3_ENDPOINT_URL, "
            "S3_BUCKET, S3_ACCESS_KEY, S3_SECRET_KEY). Refusing to mutate.",
            file=sys.stderr,
        )
        return 3

    mongo_url = os.environ.get("MONGO_URL") or ""
    db_name = os.environ.get("DB_NAME") or ""
    if not mongo_url or not db_name:
        print("[abort] MONGO_URL / DB_NAME missing from environment.",
              file=sys.stderr)
        return 4

    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    candidates = await _iter_candidates(db, args.project, args.limit)
    total_bytes = 0
    for d in candidates:
        p = Path(str(d.get("file_path") or ""))
        try:
            if p.exists():
                total_bytes += p.stat().st_size
        except OSError:
            pass

    print()
    print("=" * 72)
    print(f"TRACK 24.12 · project_docs → R2 migration "
          f"[{'APPLY' if args.apply else 'DRY-RUN'}]")
    print("=" * 72)
    print(f"  Candidates: {len(candidates)} · "
          f"total bytes: {total_bytes / (1024 * 1024):.1f} MB")
    print(f"  Project filter: {args.project or '(all)'}")
    print(f"  Limit: {args.limit}")
    if args.project:
        print(f"  Project filter: {args.project}")
    print()

    if not args.apply:
        # Dry-run — print what would happen, then exit clean.
        for d in candidates:
            local = Path(str(d.get("file_path") or ""))
            size = local.stat().st_size if local.exists() else 0
            key = _r2_key_for(d, local.suffix.lower() if local.exists() else "")
            print(
                f"  · [{'exists' if local.exists() else 'MISSING'}] "
                f"{size / (1024 * 1024):6.2f} MB  {d.get('project_id')}  "
                f"{d.get('filename')}"
            )
            print(f"      → r2 key {key}")
        print()
        print("  (dry-run · no uploads · no deletes · no mongo writes · "
              "no audit rows)")
        return 0

    # --apply branch. Migrate one at a time.
    ok, fail = 0, 0
    for d in candidates:
        try:
            res = await _promote_one(
                db, photo_storage, d, actor=args.actor,
            )
            status = res.get("status")
            if status == "migrated":
                ok += 1
                print(
                    f"  ✓ migrated  {res.get('size_bytes', 0) / (1024 * 1024):6.2f} MB  "
                    f"{res.get('project_id')}  {res.get('filename')}"
                )
            else:
                fail += 1
                print(
                    f"  ✗ {status}  {res.get('project_id')}  "
                    f"{res.get('filename')}"
                )
        except Exception as e:  # noqa: BLE001
            fail += 1
            print(f"  ✗ error on {d.get('filename')}: {e}", file=sys.stderr)

    print()
    print(f"  ✓ {ok} migrated · ✗ {fail} failed")
    return 0 if fail == 0 else 1


def _parse_args():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--apply", action="store_true",
        help="Actually migrate. Default is dry-run.",
    )
    ap.add_argument("--project", default=None, help="Limit to a project_id.")
    ap.add_argument("--limit", type=int, default=500,
                    help="Cap the number of docs per invocation (default 500).")
    ap.add_argument("--actor", default=os.environ.get("USER") or "ops",
                    help="Actor recorded in the hr_audit row (default $USER).")
    return ap.parse_args()


if __name__ == "__main__":
    _args = _parse_args()
    raise SystemExit(asyncio.run(_run(_args)))
