"""routes/operational_attachments.py · iter417 · Phase 20.0 · iter429 · Phase 28.

Operational Attachments Foundation — walking-skeleton primitive.

Doctrine
--------
Attachments are NOT files. Attachments ARE operational proof continuity.

This module ships the smallest viable primitive:
  - ONE collection: `operational_attachments`
  - ONE host kind (iter417): `assignment` (dispatch_assignments.id)
  - 12 canonical operational attachment types
  - 5 MB per file · image MIME types only (jpg/png/heic/webp/gif)
  - 25 attachments cap per host (anti-abuse)
  - RBAC: dispatch+admin write · any-portal-token + driver-session read

iter429 · Phase 28 · R2 Cold-Storage Refactor
---------------------------------------------
Full-resolution image bytes now live in Cloudflare R2 (S3-compatible) when
photo_storage is configured. Only metadata + an `r2_key` pointer remain in
MongoDB. Legacy `data_b64` rows continue to read transparently so no
historical operational truth is lost.

Storage strategy (per upload):
  - If photo_storage.is_configured() → upload bytes to R2 ·
    persist  storage_backend="r2", r2_key=<bucket-key>, sha256=<hex>
  - Else (preview/dev fallback)      → persist storage_backend="inline_b64",
    data_b64=<base64> (legacy walking-skeleton behaviour)

Reads (`GET /{id}/file`):
  - storage_backend == "r2"          → stream bytes from R2
  - else if data_b64 present         → return inline bytes (legacy)

What is OUT of scope (deferred to later iter)
  - Folders / buckets / albums / "attachments management" page
  - Multi-host expansion (incidents · inspections · daily reports · etc.)
  - Bulk operations · download-all · rename · move
  - Versioning · history · audit trail beyond uploaded_at
  - Thumbnail generation (browser handles display from full image)
  - Public unauth uploads (driver magic-link path comes in 20.1)

Doctrine guards
  - Operational truth · NOT document management
  - Append-only attach (deletion only by uploader within 5 min · mistake recovery)
  - No `is_archived` / `is_deleted` lifecycle · keep operational truth
  - No "default" attachment type · forces type declaration on upload
"""
from __future__ import annotations

import base64
import hashlib
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Awaitable, Callable, Dict, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File, Form
from pydantic import BaseModel

import photo_storage

logger = logging.getLogger("operational_attachments")

DEFAULT_TENANT_ID = "masci"

# ── Canonical 12 attachment types (doctrine-locked) ────────────────
ATTACHMENT_TYPES = {
    "asphalt_ticket",
    "scale_ticket",
    "tanker_BOL",
    "fuel_receipt",
    "delivery_receipt",
    "load_photo",
    "damage_photo",
    "breakdown_photo",
    "inspection_photo",
    "transfer_document",
    "dump_receipt",
    "operational_note_photo",
}

# ── Caps ──────────────────────────────────────────────────────────
MAX_BYTES = 5 * 1024 * 1024          # 5 MB per file
MAX_PER_HOST = 25                    # 25 attachments cap per host
MAX_NOTE_LEN = 500                   # 500 char operational note cap
ALLOWED_MIME_PREFIXES = ("image/",)  # walking skeleton = images only
ALLOWED_MIME_TYPES = {
    "image/jpeg", "image/jpg", "image/png", "image/heic",
    "image/heif", "image/webp", "image/gif",
}
DELETE_GRACE_MINUTES = 5             # mistake-recovery window

# ── Supported host kinds (iter417 walking skeleton = assignment only)
SUPPORTED_HOST_KINDS = {"assignment"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _resolve_tenant(x_tenant_id: Optional[str]) -> str:
    return (x_tenant_id or DEFAULT_TENANT_ID).strip() or DEFAULT_TENANT_ID


def _actor_label(actor: Dict[str, Any]) -> str:
    if isinstance(actor, dict):
        return (actor.get("name") or actor.get("email") or actor.get("username") or "admin")
    return "admin"


def _actor_role(actor: Dict[str, Any]) -> str:
    if isinstance(actor, dict):
        return (actor.get("portal") or actor.get("role") or "admin")
    return "admin"


def _public_attachment(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Return the attachment WITHOUT the raw bytes / R2 key (small list).

    `storage_backend` is exposed so the FE can opt into a future presigned-URL
    fetch path without changing the response shape. The R2 key itself is
    intentionally NOT exposed — the FE fetches binaries through
    `/api/operational-attachments/{id}/file` only.
    """
    out: Dict[str, Any] = {
        "id": doc.get("id"),
        "type": doc.get("type"),
        "host_kind": doc.get("host_kind"),
        "host_id": doc.get("host_id"),
        "uploaded_by": doc.get("uploaded_by"),
        "uploaded_role": doc.get("uploaded_role"),
        "uploaded_at": doc.get("uploaded_at"),
        "operational_note": doc.get("operational_note") or "",
        "filename": doc.get("filename"),
        "content_type": doc.get("content_type"),
        "size_bytes": doc.get("size_bytes"),
        "storage_backend": doc.get("storage_backend") or ("inline_b64" if doc.get("data_b64") else None),
    }
    # Track 13.14 · Scale Ticket 4-field extension. Pass through only when
    # any structured value is present; never fabricate zeros, never invent
    # categories. Older attachments without these keys remain backwards-
    # compatible (consumer sees `undefined` and renders nothing).
    for k in ("weight_gross_lbs", "weight_tare_lbs", "weight_net_lbs", "material_code"):
        if k in doc and doc[k] is not None:
            out[k] = doc[k]
    return out


# Track 13.14 · safe numeric parser. Returns float on success, None on
# empty/invalid. Never raises. Never returns 0 for empty input.
def _parse_optional_lbs(raw: Any) -> Optional[float]:
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    # accept comma decimals, strip commas + "lbs" suffix
    s = s.replace(",", "").replace(" ", "").lower()
    if s.endswith("lbs"):
        s = s[:-3]
    if s.endswith("lb"):
        s = s[:-2]
    try:
        val = float(s)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail=f"Invalid numeric weight: {raw!r}")
    if val < 0:
        raise HTTPException(status_code=400, detail=f"Weight must be non-negative: {raw!r}")
    return val


class AttachmentDeleteResponse(BaseModel):
    ok: bool
    id: str


def build_operational_attachments_router(
    db,
    require_dispatch_or_admin_dep: Callable[..., Awaitable[Dict[str, Any]]],
    require_any_portal_token_dep: Callable[..., Awaitable[Dict[str, Any]]],
    require_admin_dep: Optional[Callable[..., Awaitable[Dict[str, Any]]]] = None,
) -> Tuple[APIRouter, APIRouter]:
    """Build the operational-attachments routers.

    Returns a 2-tuple:
      - main router  · `/api/operational-attachments/*`        (portal-facing)
      - admin router · `/api/admin/operational-attachments/*`  (admin-only)

    Two routers are returned (rather than one merged router) because
    FastAPI concatenates child-router prefixes onto the parent prefix
    when you `include_router(child)` — which would corrupt the admin
    URL. Returning both lets `server.py` mount each at the top level.
    """
    router = APIRouter(prefix="/api/operational-attachments", tags=["operational-attachments"])

    # iter429.1 · Phase 28.1 · admin-only storage summary lives under
    # `/api/admin/operational-attachments/*` so it joins the rest of the
    # platform's admin-only surface naturally. We merge this sub-router
    # into `router` at the end so callers still get a single APIRouter.
    admin_router = APIRouter(
        prefix="/api/admin/operational-attachments",
        tags=["operational-attachments-admin"],
    )

    @router.get("/types")
    async def list_types(
        actor: Dict[str, Any] = Depends(require_any_portal_token_dep),  # noqa: ARG001
    ):
        """Canonical 12 attachment types · single source of truth for the FE."""
        return {"types": sorted(ATTACHMENT_TYPES)}

    # ─── UPLOAD ───────────────────────────────────────────────────
    @router.post("/upload")
    async def upload_attachment(
        host_kind: str = Form(...),
        host_id: str = Form(...),
        attachment_type: str = Form(...),
        operational_note: str = Form(""),
        # Track 13.14 · Scale-ticket structured fields. All optional;
        # consumers without these keys remain backwards-compatible.
        # Backend never fabricates a zero; empty input → None.
        weight_gross_lbs: Optional[str] = Form(default=None),
        weight_tare_lbs:  Optional[str] = Form(default=None),
        weight_net_lbs:   Optional[str] = Form(default=None),
        material_code:    Optional[str] = Form(default=None),
        file: UploadFile = File(...),
        actor: Dict[str, Any] = Depends(require_dispatch_or_admin_dep),
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    ):
        tenant_id = _resolve_tenant(x_tenant_id)

        # ── Validate inputs
        if host_kind not in SUPPORTED_HOST_KINDS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported host_kind in iter417 walking skeleton: {host_kind}",
            )
        if attachment_type not in ATTACHMENT_TYPES:
            raise HTTPException(status_code=400, detail=f"Unknown attachment_type: {attachment_type}")
        host_id = (host_id or "").strip()
        if not host_id:
            raise HTTPException(status_code=400, detail="host_id is required")

        # ── Validate host exists (assignment kind for walking skeleton)
        if host_kind == "assignment":
            existing = await db.dispatch_assignments.find_one(
                {"id": host_id, "tenant_id": tenant_id}, {"_id": 0, "id": 1}
            )
            if not existing:
                raise HTTPException(status_code=404, detail="Host assignment not found")

        # ── Cap attachment count per host
        count = await db.operational_attachments.count_documents(
            {"tenant_id": tenant_id, "host_kind": host_kind, "host_id": host_id}
        )
        if count >= MAX_PER_HOST:
            raise HTTPException(
                status_code=400,
                detail=f"Maximum {MAX_PER_HOST} attachments per host reached",
            )

        # ── Validate MIME + read bytes
        content_type = (file.content_type or "").lower()
        if not any(content_type.startswith(p) for p in ALLOWED_MIME_PREFIXES) or content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported content_type: {content_type} (images only in iter417)",
            )
        raw = await file.read()
        size_bytes = len(raw)
        if size_bytes == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        if size_bytes > MAX_BYTES:
            raise HTTPException(
                status_code=400,
                detail=f"File too large ({size_bytes} bytes; max {MAX_BYTES})",
            )

        # ── Sanitize note
        operational_note = (operational_note or "").strip()
        if len(operational_note) > MAX_NOTE_LEN:
            operational_note = operational_note[:MAX_NOTE_LEN]

        attachment_id = str(uuid.uuid4())
        sha256_hex = hashlib.sha256(raw).hexdigest()

        # ── iter429 · R2 cold-storage path · falls back to inline base64
        #    in unconfigured (preview-only) environments so the walking-
        #    skeleton contract is preserved even without R2 credentials.
        ext = (content_type.split("/", 1)[-1] or "jpg").replace("jpeg", "jpg")
        r2_key: Optional[str] = None
        storage_backend = "inline_b64"
        if photo_storage.is_configured():
            try:
                # photo_storage returns a `photo://<bucket>/<key>` URL ·
                # we keep only the key portion in Mongo so the bucket can
                # rotate without a data migration.
                ref = await photo_storage.upload_photo_bytes(
                    raw,
                    ext=ext,
                    source_id=f"opattach/{host_kind}/{host_id}/{attachment_id}",
                    content_type=content_type,
                )
                # parse `photo://<bucket>/<key>` → keep <key>
                if ref.startswith("photo://"):
                    _, _, rest = ref.partition("photo://")
                    _, _, key_part = rest.partition("/")
                    r2_key = key_part or None
                if r2_key:
                    storage_backend = "r2"
            except Exception as exc:  # noqa: BLE001
                # R2 upload failed · keep operational continuity by writing
                # the inline-base64 path so the driver/dispatch user is
                # never blocked by a transient storage outage.
                logger.warning(
                    f"[op-attachments] R2 upload failed · falling back to inline_b64: {exc}",
                )

        doc: Dict[str, Any] = {
            "id": attachment_id,
            "tenant_id": tenant_id,
            "host_kind": host_kind,
            "host_id": host_id,
            "type": attachment_type,
            "uploaded_by": _actor_label(actor),
            "uploaded_role": _actor_role(actor),
            "uploaded_at": _now_iso(),
            "operational_note": operational_note,
            "filename": (file.filename or "attachment").strip()[:255],
            "content_type": content_type,
            "size_bytes": size_bytes,
            "sha256": sha256_hex,
            "storage_backend": storage_backend,
        }
        if storage_backend == "r2":
            doc["r2_key"] = r2_key
        else:
            doc["data_b64"] = base64.b64encode(raw).decode("ascii")

        # Track 13.14 · Scale-ticket structured fields. Persist ONLY for
        # scale_ticket attachments. Other attachment kinds are unaffected.
        # Net is auto-computed only when gross + tare are both valid AND
        # net is empty; an explicitly entered net is never overridden.
        if attachment_type == "scale_ticket":
            g = _parse_optional_lbs(weight_gross_lbs)
            t = _parse_optional_lbs(weight_tare_lbs)
            n = _parse_optional_lbs(weight_net_lbs)
            if g is None and t is not None and n is None:
                # tare alone is meaningful but yields no derived net
                pass
            if n is None and g is not None and t is not None:
                computed = g - t
                if computed < 0:
                    raise HTTPException(
                        status_code=400,
                        detail="Tare weight cannot exceed gross weight.",
                    )
                n = round(computed, 2)
            if g is not None:
                doc["weight_gross_lbs"] = g
            if t is not None:
                doc["weight_tare_lbs"] = t
            if n is not None:
                doc["weight_net_lbs"] = n
            mc = (material_code or "").strip()
            if mc:
                doc["material_code"] = mc[:64]

        await db.operational_attachments.insert_one(doc)

        return _public_attachment(doc)

    # ─── LIST (by host) ───────────────────────────────────────────
    @router.get("/list")
    async def list_attachments(
        host_kind: str,
        host_id: str,
        actor: Dict[str, Any] = Depends(require_any_portal_token_dep),  # noqa: ARG001
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    ):
        tenant_id = _resolve_tenant(x_tenant_id)
        if host_kind not in SUPPORTED_HOST_KINDS:
            raise HTTPException(status_code=400, detail=f"Unsupported host_kind: {host_kind}")
        if not (host_id or "").strip():
            raise HTTPException(status_code=400, detail="host_id is required")
        cur = db.operational_attachments.find(
            {"tenant_id": tenant_id, "host_kind": host_kind, "host_id": host_id.strip()},
            {"_id": 0, "data_b64": 0, "r2_key": 0},
        ).sort("uploaded_at", 1)
        items = [_public_attachment(d) async for d in cur]
        return {"attachments": items, "count": len(items)}

    # ─── FETCH BINARY ─────────────────────────────────────────────
    @router.get("/{attachment_id}/file")
    async def get_attachment_file(
        attachment_id: str,
        actor: Dict[str, Any] = Depends(require_any_portal_token_dep),  # noqa: ARG001
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    ):
        tenant_id = _resolve_tenant(x_tenant_id)
        doc = await db.operational_attachments.find_one(
            {"id": attachment_id, "tenant_id": tenant_id},
            {"_id": 0},
        )
        if not doc:
            raise HTTPException(status_code=404, detail="Attachment not found")
        from fastapi.responses import Response

        backend = doc.get("storage_backend") or ("r2" if doc.get("r2_key") else "inline_b64")
        if backend == "r2" and doc.get("r2_key"):
            try:
                # photo_storage reads any `photo://<bucket>/<key>` ref ·
                # we rebuild the canonical ref from the stored key + the
                # configured bucket so a bucket rotation is transparent.
                ref = photo_storage.build_ref_for_key(doc["r2_key"])
                raw = await photo_storage.read_photo_bytes(ref)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    f"[op-attachments] R2 fetch failed for {attachment_id}: {exc}",
                )
                # Last-chance legacy fallback (rare · only for docs that
                # have BOTH r2_key and an old data_b64 still attached).
                if doc.get("data_b64"):
                    raw = base64.b64decode(doc["data_b64"])
                else:
                    raise HTTPException(status_code=502, detail="Attachment storage unavailable")
        else:
            raw = base64.b64decode(doc.get("data_b64") or "")
        return Response(
            content=raw,
            media_type=doc.get("content_type") or "application/octet-stream",
            headers={
                "Content-Disposition": f'inline; filename="{doc.get("filename","attachment")}"',
                "Cache-Control": "private, max-age=300",
            },
        )

    # ─── DELETE (5-min mistake-recovery window only) ──────────────
    @router.delete("/{attachment_id}", response_model=AttachmentDeleteResponse)
    async def delete_attachment(
        attachment_id: str,
        actor: Dict[str, Any] = Depends(require_dispatch_or_admin_dep),
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    ):
        """Operational mistake recovery only. Deletion allowed:
          - by the original uploader OR an admin
          - within 5 minutes of upload (operational truth doctrine)
        After that, the attachment is permanent operational proof.
        """
        tenant_id = _resolve_tenant(x_tenant_id)
        # iter429 · Phase 28 · need r2_key for cold-storage cleanup
        doc = await db.operational_attachments.find_one(
            {"id": attachment_id, "tenant_id": tenant_id},
            {"_id": 0, "uploaded_at": 1, "uploaded_by": 1, "uploaded_role": 1,
             "storage_backend": 1, "r2_key": 1},
        )
        if not doc:
            raise HTTPException(status_code=404, detail="Attachment not found")

        # Admin or original uploader
        actor_label = _actor_label(actor)
        actor_role = _actor_role(actor)
        is_admin = actor_role == "admin" or (isinstance(actor, dict) and actor.get("admin"))
        is_uploader = doc.get("uploaded_by") == actor_label
        if not (is_admin or is_uploader):
            raise HTTPException(status_code=403, detail="Not allowed to delete this attachment")

        # 5-minute grace window
        try:
            upl_dt = datetime.fromisoformat(doc["uploaded_at"].replace("Z", "+00:00"))
            age = datetime.now(timezone.utc) - upl_dt
        except Exception:
            age = timedelta(days=999)
        if age > timedelta(minutes=DELETE_GRACE_MINUTES) and not is_admin:
            raise HTTPException(
                status_code=403,
                detail=f"Attachments become permanent operational proof after {DELETE_GRACE_MINUTES} minutes",
            )

        await db.operational_attachments.delete_one(
            {"id": attachment_id, "tenant_id": tenant_id}
        )
        # Best-effort R2 cleanup · orphaned R2 objects are cheap, but the
        # mistake-recovery doctrine says "make it as if it never happened".
        if doc.get("storage_backend") == "r2" and doc.get("r2_key"):
            try:
                ref = photo_storage.build_ref_for_key(doc["r2_key"])
                await photo_storage.delete_photo(ref)
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"[op-attachments] R2 delete best-effort failed: {exc}")
        return AttachmentDeleteResponse(ok=True, id=attachment_id)

    # ─── iter429.1 · Phase 28.1 · ADMIN STORAGE SUMMARY (JSON only) ───
    # Tiny doctrine-safe visibility: how many rows are inline_b64 vs R2.
    # NO frontend page · NO chart · NO dashboard. Admins curl it before
    # / after migration to verify cold-storage convergence.
    @admin_router.get("/storage-summary")
    async def storage_summary(
        actor: Dict[str, Any] = Depends(require_admin_dep or require_dispatch_or_admin_dep),
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    ):
        tenant_id = _resolve_tenant(x_tenant_id)
        # Only count rows that still carry usable bytes (legacy inline OR
        # r2-backed). Rows missing both fields are anomalies and are
        # surfaced separately so they can be investigated.
        coll = db.operational_attachments
        # Aggregate-once with a $facet so we make ONE round-trip to Atlas.
        pipeline = [
            {"$match": {"tenant_id": tenant_id}},
            {"$facet": {
                "by_backend": [
                    {"$group": {
                        "_id": {
                            "$cond": [
                                {"$eq": ["$storage_backend", "r2"]},
                                "r2",
                                {"$cond": [
                                    {"$or": [
                                        {"$eq": ["$storage_backend", "inline_b64"]},
                                        {"$and": [
                                            {"$ne": ["$data_b64", None]},
                                            {"$ne": ["$data_b64", ""]},
                                        ]},
                                    ]},
                                    "inline_b64",
                                    "unknown",
                                ]},
                            ],
                        },
                        "count": {"$sum": 1},
                        "total_size_bytes": {"$sum": {"$ifNull": ["$size_bytes", 0]}},
                    }},
                ],
                "totals": [{"$count": "total"}],
            }},
        ]
        rows = []
        async for r in coll.aggregate(pipeline):
            rows.append(r)
        result = rows[0] if rows else {"by_backend": [], "totals": []}
        by_backend = {b["_id"]: {"count": b["count"], "total_size_bytes": b["total_size_bytes"]}
                      for b in result.get("by_backend", [])}
        total = (result.get("totals") or [{"total": 0}])[0].get("total", 0) if result.get("totals") else 0
        r2_count = by_backend.get("r2", {}).get("count", 0)
        migration_pct = round(100 * r2_count / total, 2) if total else 100.0

        # iter430 · Phase 28.2 · Part 7 expansion
        # avg_attachment_size           — sum / count across BOTH backends
        # projected_90_day_growth_bytes — extrapolate from the rolling
        #                                 30-day window of uploaded rows.
        total_size = (
            by_backend.get("r2", {}).get("total_size_bytes", 0)
            + by_backend.get("inline_b64", {}).get("total_size_bytes", 0)
            + by_backend.get("unknown", {}).get("total_size_bytes", 0)
        )
        avg_size = round(total_size / total) if total else 0

        # Look back 30 days at uploaded_at to extrapolate a 90-day
        # projection. Calm prediction · NOT analytics · just a growth
        # number the operator can sanity-check against R2 billing.
        thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        recent_pipeline = [
            {"$match": {"tenant_id": tenant_id,
                        "uploaded_at": {"$gte": thirty_days_ago}}},
            {"$group": {
                "_id": None,
                "bytes": {"$sum": {"$ifNull": ["$size_bytes", 0]}},
                "count": {"$sum": 1},
            }},
        ]
        recent_bytes = 0
        recent_count = 0
        try:
            async for row in coll.aggregate(recent_pipeline):
                recent_bytes = row.get("bytes", 0) or 0
                recent_count = row.get("count", 0) or 0
        except Exception:
            pass
        # 90-day projection = (last 30d throughput) × 3 — no smoothing,
        # no decay; the operator owns the interpretation.
        projected_90_day_growth_bytes = recent_bytes * 3
        projected_90_day_growth_count = recent_count * 3
        return {
            "tenant_id": tenant_id,
            "total": total,
            "r2_backed": by_backend.get("r2", {"count": 0, "total_size_bytes": 0}),
            "inline_b64": by_backend.get("inline_b64", {"count": 0, "total_size_bytes": 0}),
            "unknown": by_backend.get("unknown", {"count": 0, "total_size_bytes": 0}),
            "migrated_pct": migration_pct,
            "avg_attachment_size_bytes": avg_size,
            "projected_90_day_growth": {
                "based_on_window_days": 30,
                "recent_window_count": recent_count,
                "recent_window_bytes": recent_bytes,
                "projected_count": projected_90_day_growth_count,
                "projected_bytes": projected_90_day_growth_bytes,
            },
            "captured_at": _now_iso(),
        }

    return router, admin_router


async def ensure_operational_attachments_indexes(db) -> None:
    """Index by host for list queries; index by id for fetches."""
    coll = db.operational_attachments
    await coll.create_index(
        [("tenant_id", 1), ("host_kind", 1), ("host_id", 1), ("uploaded_at", 1)],
        name="ix_op_attachments_host",
    )
    await coll.create_index(
        [("id", 1), ("tenant_id", 1)],
        name="ix_op_attachments_id",
        unique=True,
    )
