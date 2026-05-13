"""
signature_migration.py — One-shot migration: base64 signatures → R2.
====================================================================

Walks the collections listed below, finds string fields that look like
a base64 `data:image/...` signature, uploads each blob to Cloudflare R2
via `photo_storage.upload_data_url()`, and replaces the field with the
returned `photo://` reference.

Verified by the read-side compatibility shim:
  - `pdf_render._signature()` and `field_leadership_pdf._signatures_block()`
    resolve `photo://` refs back to inline data URLs at print time
    (PDFs look identical).
  - Frontend `resolvePhotoSrc()` already rewrites `photo://` refs to
    `/api/photo-bytes?ref=…` for `<img>` rendering.

Endpoints (admin-only):
  POST /api/admin/signatures/migrate?dry_run=true&limit=200
      Returns a per-collection breakdown of how many records WOULD be
      migrated, total bytes recovered, and a 10-record sample.

  POST /api/admin/signatures/migrate?dry_run=false&limit=200
      Performs the migration. Each record is updated atomically — the
      original base64 is replaced with the photo:// ref ONLY after a
      successful R2 upload.

  GET  /api/admin/signatures/status
      Returns current state: total signatures, base64 still in DB, cloud,
      estimated bytes savings.

Schema fields scanned per collection (top-level + nested):
  Top-level string fields:
    prepared_by_signature, superintendent_signature, signature,
    supervisor_signature, employee_signature, witness_signature,
    inspector_signature, foreman_signature, operator_signature,
    sub_rep_signature, conductor_signature
  Nested-list signature fields:
    attendees[*].signature, attendees[*].sig
    witnesses[*].signature, witnesses[*].sig
    signatures[*].signature, signatures[*].sig
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query

import photo_storage

logger = logging.getLogger(__name__)

SCAN_COLLECTIONS = [
    "daily_reports",
    "inspections",
    "field_leadership",
    "equipment_inspections",
    "pre_op_inspections",
    "toolbox_talks",
    "concrete_inspections",
    "rebar_inspections",
    "subcontractor_inspections",
    "incidents",
    "job_hazard_plans",
]

TOP_LEVEL_FIELDS = [
    "prepared_by_signature",
    "superintendent_signature",
    "signature",
    "supervisor_signature",
    "employee_signature",
    "witness_signature",
    "inspector_signature",
    "foreman_signature",
    "operator_signature",
    "sub_rep_signature",
    "conductor_signature",
]

NESTED_LIST_FIELDS = ["attendees", "witnesses", "signatures"]
NESTED_SIG_KEYS = ["signature", "sig"]


def _is_base64(v: Any) -> bool:
    return isinstance(v, str) and v.startswith("data:image/")


def _is_cloud_ref(v: Any) -> bool:
    return isinstance(v, str) and v.startswith("photo://")


def _scan_record(rec: Dict[str, Any]) -> Tuple[int, int, int]:
    """Returns (n_base64, n_cloud, total_b64_bytes) for one record."""
    n_b64 = n_cloud = bytes_total = 0
    for f in TOP_LEVEL_FIELDS:
        v = rec.get(f)
        if _is_base64(v):
            n_b64 += 1
            bytes_total += len(v)
        elif _is_cloud_ref(v):
            n_cloud += 1
    for nk in NESTED_LIST_FIELDS:
        arr = rec.get(nk)
        if isinstance(arr, list):
            for entry in arr:
                if not isinstance(entry, dict):
                    continue
                for sk in NESTED_SIG_KEYS:
                    v = entry.get(sk)
                    if _is_base64(v):
                        n_b64 += 1
                        bytes_total += len(v)
                    elif _is_cloud_ref(v):
                        n_cloud += 1
    return n_b64, n_cloud, bytes_total


async def _migrate_record(
    db, collection: str, rec: Dict[str, Any], source_id: str
) -> Tuple[int, int]:
    """Replace every base64 signature on this record with a photo:// ref.

    Returns (count_migrated, count_failed). Atomic: collects all
    successful uploads first, then issues a single $set update.
    """
    updates: Dict[str, Any] = {}
    nested_updates: Dict[str, List[Dict[str, Any]]] = {}
    migrated = failed = 0

    # Top-level fields
    for f in TOP_LEVEL_FIELDS:
        v = rec.get(f)
        if not _is_base64(v):
            continue
        try:
            ref = await photo_storage.upload_data_url(v, source_id=f"{collection}-{source_id}-{f}")
            updates[f] = ref
            migrated += 1
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[sig-migrate] upload failed {collection}/{rec.get('id')}/{f}: {e}")
            failed += 1

    # Nested list fields — must update the WHOLE list, not in-place
    for nk in NESTED_LIST_FIELDS:
        arr = rec.get(nk)
        if not isinstance(arr, list):
            continue
        new_arr: List[Dict[str, Any]] = []
        changed = False
        for i, entry in enumerate(arr):
            if not isinstance(entry, dict):
                new_arr.append(entry)
                continue
            new_entry = dict(entry)
            for sk in NESTED_SIG_KEYS:
                v = new_entry.get(sk)
                if not _is_base64(v):
                    continue
                try:
                    ref = await photo_storage.upload_data_url(
                        v, source_id=f"{collection}-{source_id}-{nk}-{i}-{sk}"
                    )
                    new_entry[sk] = ref
                    changed = True
                    migrated += 1
                except Exception as e:  # noqa: BLE001
                    logger.warning(f"[sig-migrate] nested upload failed {collection}/{rec.get('id')}/{nk}[{i}].{sk}: {e}")
                    failed += 1
            new_arr.append(new_entry)
        if changed:
            nested_updates[nk] = new_arr

    if updates or nested_updates:
        set_doc = {**updates, **nested_updates}
        # Find by id if present, otherwise _id
        flt = {"id": rec.get("id")} if rec.get("id") else {"_id": rec.get("_id")}
        await db[collection].update_one(flt, {"$set": set_doc})

    return migrated, failed


def build_signature_migration_router(db, require_admin_dep: Callable) -> APIRouter:
    router = APIRouter(
        prefix="/api/admin/signatures",
        tags=["admin-signatures"],
    )

    @router.get("/status")
    async def status(_=Depends(require_admin_dep)):
        existing = await db.list_collection_names()
        rows: List[Dict[str, Any]] = []
        grand = {"docs_with_sig": 0, "base64": 0, "cloud": 0, "bytes": 0}
        for col in SCAN_COLLECTIONS:
            if col not in existing:
                continue
            try:
                count = await db[col].estimated_document_count()
            except Exception:  # noqa: BLE001
                count = 0
            if not count:
                continue
            n_with = n_b64 = n_cloud = 0
            bytes_total = 0
            projection = {f: 1 for f in TOP_LEVEL_FIELDS}
            projection.update({nk: 1 for nk in NESTED_LIST_FIELDS})
            projection["id"] = 1
            async for d in db[col].find({}, projection):
                a, b, c = _scan_record(d)
                if a or b:
                    n_with += 1
                n_b64 += a
                n_cloud += b
                bytes_total += c
            if n_with:
                rows.append({
                    "collection": col,
                    "total_records": count,
                    "records_with_signature": n_with,
                    "base64": n_b64,
                    "cloud": n_cloud,
                    "bytes_in_db": bytes_total,
                })
                grand["docs_with_sig"] += n_with
                grand["base64"] += n_b64
                grand["cloud"] += n_cloud
                grand["bytes"] += bytes_total
        return {
            "ok": True,
            "r2_configured": photo_storage.is_configured(),
            "rows": rows,
            "grand_total": grand,
        }

    @router.post("/migrate")
    async def migrate(
        _=Depends(require_admin_dep),
        dry_run: bool = Query(True, description="If true, count only — no R2 uploads"),
        limit: int = Query(200, ge=1, le=2000, description="Max records to process this run"),
        collection: Optional[str] = Query(None, description="Optional single collection"),
    ):
        if not photo_storage.is_configured():
            raise HTTPException(503, "Cloudflare R2 (photo_storage) not configured")

        existing = await db.list_collection_names()
        targets = [collection] if collection else SCAN_COLLECTIONS
        targets = [t for t in targets if t in existing]

        result: Dict[str, Any] = {
            "ok": True,
            "dry_run": dry_run,
            "limit": limit,
            "collections": [],
            "migrated": 0,
            "failed": 0,
            "bytes_recovered": 0,
            "sample": [],
        }
        remaining = limit
        for col in targets:
            if remaining <= 0:
                break
            projection = {f: 1 for f in TOP_LEVEL_FIELDS}
            projection.update({nk: 1 for nk in NESTED_LIST_FIELDS})
            projection["id"] = 1

            n_records_in_col = 0
            n_migrated = n_failed = 0
            bytes_recovered = 0
            cursor = db[col].find({}, projection).limit(remaining * 2)
            async for d in cursor:
                a, _b, byt = _scan_record(d)
                if not a:
                    continue
                if dry_run:
                    n_migrated += a
                    n_records_in_col += 1
                    bytes_recovered += byt
                    if len(result["sample"]) < 10:
                        result["sample"].append({
                            "collection": col,
                            "id": d.get("id"),
                            "signatures_in_record": a,
                            "bytes": byt,
                        })
                else:
                    m, f = await _migrate_record(db, col, d, source_id=str(d.get("id") or ""))
                    n_migrated += m
                    n_failed += f
                    n_records_in_col += 1
                    bytes_recovered += byt
                    if len(result["sample"]) < 10:
                        result["sample"].append({
                            "collection": col,
                            "id": d.get("id"),
                            "migrated": m,
                            "failed": f,
                            "bytes": byt,
                        })
                remaining -= 1
                if remaining <= 0:
                    break
            if n_records_in_col:
                result["collections"].append({
                    "collection": col,
                    "records": n_records_in_col,
                    "signatures_migrated": n_migrated,
                    "failed": n_failed,
                    "bytes_recovered": bytes_recovered,
                })
                result["migrated"] += n_migrated
                result["failed"] += n_failed
                result["bytes_recovered"] += bytes_recovered

        return result

    return router
