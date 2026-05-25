"""scripts/migrate_attachments_to_r2.py · iter429 · Phase 28 · Part 1.

Cold-storage migration for `operational_attachments` records.

Reads every legacy `storage_backend in (None, "inline_b64")` row that still
carries a `data_b64` payload, uploads the bytes to Cloudflare R2 via
`photo_storage.upload_photo_bytes`, and rewrites the row so it points at
the R2 object instead of the inline base64.

Doctrine
--------
- DRY RUN by default. Pass `--apply` to actually mutate Mongo and upload
  bytes to R2. The dry run is identical apart from the network calls
  being skipped — you'll see exactly which rows would change.
- Verifies a sha256 round-trip before deleting `data_b64` so we can
  never destroy operational truth if R2 silently corrupts a byte.
- Idempotent: rows already on `storage_backend == "r2"` are skipped.
- Batch-friendly: `--limit N` migrates the oldest N candidates.
- Append-only safety net: rows that fail verification are LEFT ALONE.
  The script logs the failure and moves on.

Usage
-----
    # 1. Inspect what would change (no writes, no R2 upload)
    cd /app/backend && python ../scripts/migrate_attachments_to_r2.py --limit 50

    # 2. Run the migration for real
    cd /app/backend && python ../scripts/migrate_attachments_to_r2.py --apply --limit 50

    # 3. Migrate everything
    cd /app/backend && python ../scripts/migrate_attachments_to_r2.py --apply

Environment
-----------
Requires all of:
    MONGO_URL · DB_NAME · S3_ENDPOINT_URL · S3_BUCKET · S3_ACCESS_KEY · S3_SECRET_KEY
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import hashlib
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict

# Make the backend package importable when run from /app/scripts.
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv  # noqa: E402
load_dotenv(BACKEND_DIR / ".env")

from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402
import photo_storage  # noqa: E402  (lives in /app/backend)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s · %(levelname)s · %(message)s",
)
log = logging.getLogger("migrate-attachments-to-r2")


async def _candidates(db, limit: int | None):
    """Yield legacy rows that still have inline base64 bytes."""
    q: Dict[str, Any] = {
        "$and": [
            {"data_b64": {"$exists": True, "$ne": ""}},
            {"$or": [
                {"storage_backend": {"$exists": False}},
                {"storage_backend": "inline_b64"},
            ]},
        ],
    }
    cur = db.operational_attachments.find(q, {"_id": 0}).sort("uploaded_at", 1)
    if limit:
        cur = cur.limit(limit)
    async for doc in cur:
        yield doc


def _ext_from_content_type(ct: str) -> str:
    ct = (ct or "").lower()
    table = {
        "image/jpeg": "jpg", "image/jpg": "jpg",
        "image/png": "png", "image/webp": "webp",
        "image/avif": "avif", "image/heic": "heic",
        "image/heif": "heif", "image/gif": "gif",
    }
    return table.get(ct, "jpg")


async def migrate_one(db, doc: Dict[str, Any], *, apply: bool) -> str:
    """Migrate a single attachment row. Returns a status string."""
    aid = doc.get("id") or "?"
    raw_b64 = doc.get("data_b64") or ""
    try:
        raw = base64.b64decode(raw_b64)
    except Exception as e:  # noqa: BLE001
        return f"SKIP {aid} · base64 decode failed: {e}"
    sha_expected = doc.get("sha256") or hashlib.sha256(raw).hexdigest()

    ext = _ext_from_content_type(doc.get("content_type") or "")
    source_id = (
        f"opattach/{doc.get('host_kind','unknown')}/"
        f"{doc.get('host_id','unknown')}/{aid}"
    )

    if not apply:
        return (
            f"DRY  {aid} · {len(raw)} bytes · sha256={sha_expected[:12]}…"
            f" · would upload to R2 ({ext})"
        )

    try:
        ref = await photo_storage.upload_photo_bytes(
            raw,
            ext=ext,
            source_id=source_id,
            content_type=doc.get("content_type") or "application/octet-stream",
        )
    except Exception as e:  # noqa: BLE001
        return f"FAIL {aid} · R2 upload error: {e}"

    if not ref.startswith("photo://"):
        return f"FAIL {aid} · unexpected ref: {ref[:80]}"
    _, _, rest = ref.partition("photo://")
    _, _, r2_key = rest.partition("/")
    if not r2_key:
        return f"FAIL {aid} · ref missing key: {ref[:80]}"

    # Verify round-trip before clearing data_b64 (operational truth guard).
    try:
        round_trip = await photo_storage.read_photo_bytes(ref)
        sha_actual = hashlib.sha256(round_trip).hexdigest()
    except Exception as e:  # noqa: BLE001
        return f"FAIL {aid} · verify read failed: {e}"
    if sha_actual != sha_expected or len(round_trip) != len(raw):
        return (
            f"FAIL {aid} · sha mismatch (expected={sha_expected[:12]}, "
            f"got={sha_actual[:12]}) · LEFT data_b64 IN PLACE"
        )

    await db.operational_attachments.update_one(
        {"id": aid, "tenant_id": doc.get("tenant_id")},
        {
            "$set": {
                "storage_backend": "r2",
                "r2_key": r2_key,
                "sha256": sha_expected,
            },
            "$unset": {"data_b64": ""},
        },
    )
    return f"OK   {aid} · {len(raw)} bytes · → {r2_key}"


async def main() -> int:
    ap = argparse.ArgumentParser(description="Migrate operational_attachments to R2 cold-storage")
    ap.add_argument("--apply", action="store_true",
                    help="Perform the migration (default: dry-run only)")
    ap.add_argument("--limit", type=int, default=None,
                    help="Cap the number of rows processed (default: all)")
    args = ap.parse_args()

    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    if not mongo_url or not db_name:
        log.error("MONGO_URL or DB_NAME missing from /app/backend/.env")
        return 2

    if args.apply and not photo_storage.is_configured():
        log.error(
            "photo_storage is not configured · refusing to --apply without R2 "
            "credentials (S3_ENDPOINT_URL / S3_BUCKET / S3_ACCESS_KEY / S3_SECRET_KEY)",
        )
        return 3

    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    total = await db.operational_attachments.count_documents({
        "$and": [
            {"data_b64": {"$exists": True, "$ne": ""}},
            {"$or": [
                {"storage_backend": {"$exists": False}},
                {"storage_backend": "inline_b64"},
            ]},
        ],
    })
    log.info(f"Found {total} candidate attachment(s) on inline_b64 storage")
    if args.limit:
        log.info(f"Limiting this run to {args.limit} oldest row(s)")
    if not args.apply:
        log.info("DRY-RUN · no writes will be performed · pass --apply to migrate")

    processed = ok = skipped = failed = 0
    async for doc in _candidates(db, args.limit):
        status = await migrate_one(db, doc, apply=args.apply)
        processed += 1
        if status.startswith("OK"):
            ok += 1
        elif status.startswith("SKIP") or status.startswith("DRY"):
            skipped += 1
        else:
            failed += 1
        log.info(status)

    log.info(
        f"Done · processed={processed} · ok={ok} · skipped={skipped} "
        f"· failed={failed} · apply={args.apply}",
    )
    client.close()
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
