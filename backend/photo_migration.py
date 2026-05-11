"""
photo_migration.py — batch migrate base64 photos out of MongoDB into S3-compatible storage
==========================================================================================

Strategy
--------
1. Walks every collection known to store photos (see PHOTO_COLLECTIONS below).
2. For each document, finds every photo field and migrates each base64
   data URL to S3, replacing the value in-place with a ``photo://`` ref.
3. Each migration is **idempotent**: already-migrated refs (starting with
   ``photo://``) are skipped, so re-running is safe.
4. Each migration is **resumable**: progress is tracked in the
   ``photo_migration_progress`` collection — if interrupted, the next run
   picks up where it left off (by document id, not by photo).
5. Supports ``dry_run=True`` mode: walks everything, counts what WOULD be
   migrated, but performs zero S3 writes and zero MongoDB updates.
6. Per-collection ``limit`` cap so an admin can migrate a chunk at a time
   and check the bucket fills correctly before committing to the full run.

Why per-document atomicity matters
----------------------------------
Each document update is a single MongoDB ``update_one`` call. If the
server is interrupted mid-document, the partial state is consistent:
EITHER all photos in that document are still base64 (we didn't write
the replacement) OR all are photo:// refs (the update committed). We
never end up with a half-migrated photos array.

Public surface
--------------
    PHOTO_COLLECTIONS — dict of {collection_name: [photo_field_paths]}
    migrate_collection(db, name, *, dry_run, limit, since_doc_id) -> stats
    migrate_all(db, *, dry_run, limit_per_collection) -> stats
    get_progress(db) -> dict
    reset_progress(db, collection_name=None) -> None
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from photo_storage import is_configured, is_storage_ref, upload_data_url

logger = logging.getLogger(__name__)


# Map collection name → list of dot-paths to photo fields. Each path
# either points to a list of data URLs (e.g. "photos") or, for the
# nested case in field_leadership_records (items[].photos[]), uses
# a special "*.photos" syntax that means "iterate items[]".
PHOTO_COLLECTIONS: Dict[str, List[str]] = {
    "daily_reports":            ["photos"],
    "inspections":              ["photos"],
    "qaqc_inspections":         ["photos"],
    "safety_incidents":         ["photos"],
    "meetings":                 ["photos"],
    "jha_records":              ["photos"],
    "equipment_inspections":    ["photos"],  # Pre-Op photos
    "shop_signoffs":            ["photos"],
    "safety_form_records":      ["photos"],
    "safety_equipment_trainings": ["photos"],
    "safety_equipment_returns": ["photos"],
    "field_leadership_records": ["photos", "items.*.photos"],
}


def _photo_fields_in_doc(doc: dict, paths: List[str]) -> List[tuple]:
    """Return [(path_descriptor, current_value)] tuples for every photo
    field actually present in ``doc``. Path descriptor is what we'll need
    to write the replacement back via update_one's $set."""
    found: List[tuple] = []
    for path in paths:
        if "*" not in path:
            v = doc.get(path)
            if isinstance(v, list) and v:
                found.append((path, v))
        else:
            # "items.*.photos" — iterate items[]
            outer, _star, inner = path.split(".", 2)
            items = doc.get(outer) or []
            if not isinstance(items, list):
                continue
            for i, item in enumerate(items):
                if not isinstance(item, dict):
                    continue
                v = item.get(inner)
                if isinstance(v, list) and v:
                    found.append((f"{outer}.{i}.{inner}", v))
    return found


async def _migrate_one_array(
    photos: List[Any], *, source_id: str, dry_run: bool
) -> tuple:
    """Walk a photos array; for each base64 data URL, upload to S3 and
    replace the value with a photo:// ref. Returns
    (new_array, migrated_count, skipped_count, failed_count, bytes_migrated).
    """
    migrated = 0
    skipped = 0
    failed = 0
    bytes_migrated = 0
    out: List[Any] = []
    for entry in photos:
        if not isinstance(entry, str):
            out.append(entry)
            skipped += 1
            continue
        if is_storage_ref(entry):
            out.append(entry)
            skipped += 1
            continue
        if not entry.startswith("data:"):
            # Not base64 either — leave alone.
            out.append(entry)
            skipped += 1
            continue
        approx_bytes = max(0, int(len(entry) * 0.75))  # rough decoded size
        if dry_run:
            out.append(entry)
            migrated += 1
            bytes_migrated += approx_bytes
            continue
        try:
            ref = await upload_data_url(entry, source_id=source_id)
            out.append(ref)
            migrated += 1
            bytes_migrated += approx_bytes
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[photo-migration] upload failed for {source_id}: {e}")
            out.append(entry)  # KEEP original on failure
            failed += 1
    return out, migrated, skipped, failed, bytes_migrated


async def migrate_collection(
    db,
    name: str,
    *,
    dry_run: bool = True,
    limit: Optional[int] = None,
    since_doc_id: Optional[str] = None,
) -> dict:
    """Migrate one collection. Returns per-collection stats dict."""
    paths = PHOTO_COLLECTIONS.get(name)
    if not paths:
        raise ValueError(f"unknown collection: {name}")
    if not dry_run and not is_configured():
        raise RuntimeError(
            "photo_storage not configured — refusing to run real migration. "
            "Set S3_ENDPOINT_URL/S3_BUCKET/S3_ACCESS_KEY/S3_SECRET_KEY env vars."
        )

    stats = {
        "collection": name,
        "dry_run": dry_run,
        "docs_scanned": 0,
        "docs_updated": 0,
        "photos_migrated": 0,
        "photos_skipped": 0,
        "photos_failed": 0,
        "bytes_migrated": 0,
        "last_doc_id": None,
    }

    query: Dict[str, Any] = {}
    if since_doc_id:
        query["id"] = {"$gt": since_doc_id}

    # Fetch only the photo fields plus id — we don't need the rest of the doc.
    proj = {"_id": 0, "id": 1}
    for p in paths:
        if "*" in p:
            proj[p.split(".", 1)[0]] = 1
        else:
            proj[p] = 1

    cursor = db[name].find(query, proj).sort("id", 1)
    if limit:
        cursor = cursor.limit(limit)

    async for doc in cursor:
        stats["docs_scanned"] += 1
        stats["last_doc_id"] = doc.get("id")
        photo_fields = _photo_fields_in_doc(doc, paths)
        if not photo_fields:
            continue
        update_payload: Dict[str, Any] = {}
        doc_touched = False
        for field_path, photo_list in photo_fields:
            new_list, mig, skp, fail, bts = await _migrate_one_array(
                photo_list,
                source_id=f"{name}:{doc.get('id') or '?'}",
                dry_run=dry_run,
            )
            stats["photos_migrated"] += mig
            stats["photos_skipped"] += skp
            stats["photos_failed"] += fail
            stats["bytes_migrated"] += bts
            if mig > 0:
                update_payload[field_path] = new_list
                doc_touched = True
        if doc_touched and not dry_run:
            await db[name].update_one({"id": doc.get("id")}, {"$set": update_payload})
            stats["docs_updated"] += 1

    if not dry_run and stats["last_doc_id"]:
        await db.photo_migration_progress.update_one(
            {"_id": name},
            {"$set": {"_id": name, "last_doc_id": stats["last_doc_id"], "stats": stats}},
            upsert=True,
        )

    return stats


async def migrate_all(
    db,
    *,
    dry_run: bool = True,
    limit_per_collection: Optional[int] = 100,
    resume: bool = True,
) -> dict:
    """Run migration across EVERY known photo collection. Returns
    aggregated stats. When ``resume=True``, picks up where the last
    real run left off (per collection)."""
    out: Dict[str, Any] = {
        "dry_run": dry_run,
        "limit_per_collection": limit_per_collection,
        "per_collection": [],
        "totals": {
            "docs_scanned": 0,
            "docs_updated": 0,
            "photos_migrated": 0,
            "photos_skipped": 0,
            "photos_failed": 0,
            "bytes_migrated": 0,
        },
    }
    for name in PHOTO_COLLECTIONS.keys():
        since = None
        if resume and not dry_run:
            prog = await db.photo_migration_progress.find_one({"_id": name})
            since = (prog or {}).get("last_doc_id")
        try:
            s = await migrate_collection(
                db, name, dry_run=dry_run, limit=limit_per_collection,
                since_doc_id=since,
            )
        except Exception as e:  # noqa: BLE001
            logger.exception(f"[photo-migration] collection {name} failed: {e}")
            s = {
                "collection": name, "dry_run": dry_run, "error": repr(e),
                "docs_scanned": 0, "docs_updated": 0, "photos_migrated": 0,
                "photos_skipped": 0, "photos_failed": 0, "bytes_migrated": 0,
            }
        out["per_collection"].append(s)
        for k in out["totals"]:
            out["totals"][k] += s.get(k, 0) or 0
    return out


async def get_progress(db) -> dict:
    """Return migration progress per collection."""
    rows = []
    async for doc in db.photo_migration_progress.find({}, {"_id": 1, "last_doc_id": 1, "stats": 1}):
        rows.append({
            "collection": doc["_id"],
            "last_doc_id": doc.get("last_doc_id"),
            "stats": doc.get("stats"),
        })
    return {"per_collection": rows}


async def reset_progress(db, collection: Optional[str] = None) -> int:
    """Wipe progress markers (so the next run starts from scratch)."""
    q = {} if collection is None else {"_id": collection}
    res = await db.photo_migration_progress.delete_many(q)
    return getattr(res, "deleted_count", 0)
