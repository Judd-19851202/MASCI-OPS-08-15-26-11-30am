"""
routes/odr/continuity.py — Phase V.1 · M0.2 · Public Link Continuity Engine.

Doctrine:
  /app/memory/ODR_PUBLIC_LINK_DEVICE_CONTINUITY_ADDENDUM.md (O11–O20)
  /app/memory/ODR_DATA_MODEL.md  (P1–P9 addendum)

Mission · "An ODR generated today must remain accessible tomorrow,
next month, next year, and during future audits."

Contract surfaces:
  * continuity-safe identifiers — every ODR carries an immutable
    `id` (uuid4) and a year-scoped `doc_id` (ODR-YYYY-NNNNN). Public
    URLs reference `doc_id` — never the Mongo _id, never the
    sequence-only number, never the report_date.
  * no broken historical links — `superseded` / `archived` ODRs are
    still reachable; they redirect to the newest non-amended version
    metadata but expose their own full record at the original URL.
  * no silent URL mutation — every `public_access.link_id` is server-
    issued + immutable + recorded in `odr_public_links` registry.
  * version continuity — a chain of amendments preserves
    `head_id` → list of `prior_ids[]`. Every prior version is
    fetchable.
  * public-view traceability — every public GET via the continuity
    engine emits a row to `odr_preload_attempts` (audit-only · admin
    + PM read · NEVER public).
  * audit continuity — `odr_section_events` and `odr_amendments`
    are append-only, integrity-anchored by trendline probe.

This module is the SERVER-SIDE bias of the continuity contract; the
public-link surface itself ships in M0.3 (frontend).

API surface (M0.2):
  POST   /api/odr/{id}/link              admin/PM · mint a public link
  GET    /api/odr/public/{doc_id}        public · resolve doc_id → ODR (with continuity gate)
  GET    /api/odr/{id}/version-chain     any portal · prior versions / amendments
  GET    /api/odr/public-links           admin · registry index
  PATCH  /api/odr/public-links/{link_id} admin · revoke / re-scope

Append-only collections:
  odr_public_links            — registry of issued public link_ids
  odr_preload_attempts        — every public preload attempt (continuity audit)
  odr_amendments              — Super+ amendments post-window (already shipped in M0.1 indexes)
"""
from __future__ import annotations

import hashlib
import logging
import secrets
import uuid
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


# ── Helpers ──────────────────────────────────────────────────────────


def _utc_iso(dt: Optional[datetime] = None) -> str:
    d = dt or datetime.now(timezone.utc)
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.") + \
        f"{d.microsecond // 1000:03d}Z"


def _actor_uid(actor: Dict[str, Any]) -> str:
    if not isinstance(actor, dict):
        return "system"
    return (
        actor.get("id")
        or actor.get("user_id")
        or actor.get("uid")
        or actor.get("email")
        or actor.get("name")
        or "unknown"
    )


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _mint_opaque_token() -> str:
    """Server-issued opaque token; never echoed back after issue."""
    return secrets.token_urlsafe(32)


# ── DTOs ─────────────────────────────────────────────────────────────


class LinkMintBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    link_scope: str = Field(default="project_crew", pattern="^(project|project_crew)$")
    note: Optional[str] = Field(default=None, max_length=280)


class LinkPatchBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    revoke: bool = False
    note: Optional[str] = Field(default=None, max_length=280)


class PublicLinkRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    link_id: str
    odr_id: str
    doc_id: str
    project_id: str
    crew_id: str
    link_scope: str
    created_at_utc: str
    created_by_uid: str
    revoked_at_utc: Optional[str] = None
    revoked_by_uid: Optional[str] = None
    note: Optional[str] = None


# ── Indexes ──────────────────────────────────────────────────────────


async def ensure_continuity_indexes(db) -> None:
    await db.odr_public_links.create_index("link_id", unique=True)
    await db.odr_public_links.create_index("doc_id")
    await db.odr_public_links.create_index([("odr_id", 1), ("created_at_utc", -1)])
    await db.odr_public_links.create_index([("project_id", 1), ("created_at_utc", -1)])
    # M0.35 · Audience Projection Doctrine — audit every PDF render.
    await db.odr_pdf_renders.create_index("render_id", unique=True)
    await db.odr_pdf_renders.create_index([("odr_id", 1), ("at_utc", -1)])
    await db.odr_pdf_renders.create_index([("audience", 1), ("at_utc", -1)])
    logger.info("ODR continuity indexes ensured.")


# ── Router factory ───────────────────────────────────────────────────


def build_odr_continuity_router(
    db,
    require_actor: Callable[..., Awaitable[Dict[str, Any]]],
    require_admin: Callable[..., Awaitable[Any]],
) -> APIRouter:

    router = APIRouter(prefix="/api/odr", tags=["odr-continuity"])

    # ── POST /api/odr/{id}/link — mint a public link ─────────────────

    @router.post("/{odr_id}/link")
    async def mint_link(
        odr_id: str,
        body: LinkMintBody,
        actor: Dict[str, Any] = Depends(require_actor),
    ) -> Dict[str, Any]:
        # Admin or PM only — never FL/safety/dispatch/shop/hr mint public links.
        portal = (actor.get("_actor") or "").lower()
        if portal not in ("admin", "pm"):
            raise HTTPException(403, "Only Admin or PM may mint public links.")

        odr = await db.odr.find_one({"id": odr_id}, {"_id": 0})
        if not odr:
            raise HTTPException(404, "ODR not found")

        link_id = str(uuid.uuid4())
        now = _utc_iso()
        # M0.35 · Audience Projection Doctrine — public links ALWAYS use External projection.
        row = {
            "link_id": link_id,
            "odr_id": odr_id,
            "doc_id": odr["doc_id"],
            "project_id": (odr.get("project") or {}).get("project_id", ""),
            "crew_id": (odr.get("crew_profile") or {}).get("crew_id", ""),
            "link_scope": body.link_scope,
            "audience_profile_locked": "external",      # never user-selectable on public links
            "projection_audience": "external",
            "created_at_utc": now,
            "created_by_uid": _actor_uid(actor),
            "created_by_portal": portal,
            "revoked_at_utc": None,
            "revoked_by_uid": None,
            "note": (body.note or "")[:280] or None,
        }
        await db.odr_public_links.insert_one(row)

        # Mirror onto the ODR for fast lookup.
        await db.odr.update_one(
            {"id": odr_id},
            {"$set": {
                "public_access.link_id": link_id,
                "public_access.link_scope": body.link_scope,
                "public_access.link_created_at_utc": now,
                "public_access.link_created_by_uid": _actor_uid(actor),
                "public_access.link_revoked_at_utc": None,
            }},
        )
        row.pop("_id", None)
        return row

    # ── GET /api/odr/public-links — registry index (admin) ───────────

    @router.get("/public-links")
    async def list_public_links(
        project_id: Optional[str] = Query(default=None),
        revoked: Optional[bool] = Query(default=None),
        limit: int = Query(default=100, ge=1, le=500),
        _admin: Any = Depends(require_admin),
    ) -> Dict[str, Any]:
        q: Dict[str, Any] = {}
        if project_id:
            q["project_id"] = project_id
        if revoked is True:
            q["revoked_at_utc"] = {"$ne": None}
        elif revoked is False:
            q["revoked_at_utc"] = None
        cur = db.odr_public_links.find(q, {"_id": 0}).sort(
            "created_at_utc", -1,
        ).limit(limit)
        rows = await cur.to_list(length=limit)
        return {"items": rows, "count": len(rows)}

    # ── PATCH /api/odr/public-links/{link_id} — revoke ───────────────

    @router.patch("/public-links/{link_id}")
    async def patch_public_link(
        link_id: str,
        body: LinkPatchBody,
        actor: Dict[str, Any] = Depends(require_actor),
    ) -> Dict[str, Any]:
        portal = (actor.get("_actor") or "").lower()
        if portal not in ("admin", "pm"):
            raise HTTPException(403, "Only Admin or PM may modify public links.")
        existing = await db.odr_public_links.find_one(
            {"link_id": link_id}, {"_id": 0}
        )
        if not existing:
            raise HTTPException(404, "Public link not found")
        now = _utc_iso()
        update: Dict[str, Any] = {}
        if body.revoke and not existing.get("revoked_at_utc"):
            update["revoked_at_utc"] = now
            update["revoked_by_uid"] = _actor_uid(actor)
        if body.note is not None:
            update["note"] = body.note[:280] or None
        if update:
            await db.odr_public_links.update_one({"link_id": link_id}, {"$set": update})
            if "revoked_at_utc" in update:
                await db.odr.update_one(
                    {"public_access.link_id": link_id},
                    {"$set": {"public_access.link_revoked_at_utc": now}},
                )
        new = await db.odr_public_links.find_one({"link_id": link_id}, {"_id": 0})
        return new or {}

    # ── GET /api/odr/public/{doc_id} — continuity-gated resolver ─────

    @router.get("/public/{doc_id}")
    async def public_resolve(
        doc_id: str,
        request: Request,
        link_id: Optional[str] = Query(default=None),
        device_token: Optional[str] = Query(default=None),
    ) -> Dict[str, Any]:
        """Public (no-auth) resolver.

        Doctrine: never silently leak prior data. The continuity gate
        returns ONLY the public-safe envelope of the requested ODR.
        Prior-day preload (Flow A) is NOT served by this route — it
        requires the device token continuity check shipped with the
        UI in M0.3. This route is the **read-now** layer.
        """
        odr = await db.odr.find_one(
            {"doc_id": doc_id},
            {
                "_id": 0,
                # Public-safe field set (no telemetry · no audit · no
                # consumer_dispatch · no device fingerprints).
                "id": 1, "doc_id": 1, "schema_version": 1, "status": 1,
                "submitted_at": 1, "amend_allowed_until_utc": 1,
                "amendment_count": 1, "last_amended_at_utc": 1,
                "project": 1, "crew_profile": 1,
                "work_areas": 1, "production_segments": 1,
                "delays": 1, "extra_work": 1, "constraints": 1,
                "safety.any_event": 1,
                "weather_impact": 1,
                "tomorrow": 1, "plan_vs_actual": 1,
                "signature.foreman_acknowledgement.acknowledged": 1,
                "signature.foreman_acknowledgement.acknowledged_at_utc": 1,
                "public_access.link_id": 1,
                "public_access.link_revoked_at_utc": 1,
                "public_access.link_scope": 1,
            },
        )

        # Build a preload-attempt audit row regardless of outcome.
        attempt = {
            "attempt_id": str(uuid.uuid4()),
            "requested_at_utc": _utc_iso(),
            "public_link_id": link_id or "",
            "doc_id": doc_id,
            "project_id": ((odr or {}).get("project") or {}).get("project_id", ""),
            "target_report_date": ((odr or {}).get("project") or {}).get("report_date", ""),
            "prior_odr_id": None,
            "outcome": "denied_no_prior",
            "signals_matched": [],
            "signals_failed": [],
            "override_actor_uid": None,
            "override_portal": None,
            "notes": None,
            "device_token_hash": _hash_token(device_token) if device_token else None,
            "client_ip": (request.client.host if request.client else None),
        }

        if not odr:
            attempt["outcome"] = "denied_no_prior"
            attempt["signals_failed"] = ["doc_id_not_found"]
            await db.odr_preload_attempts.insert_one(dict(attempt))
            raise HTTPException(404, "ODR not found")

        link_state = odr.get("public_access") or {}
        if not link_state.get("link_id"):
            attempt["outcome"] = "denied_missing_token"
            attempt["signals_failed"] = ["no_public_link_issued"]
            await db.odr_preload_attempts.insert_one(dict(attempt))
            raise HTTPException(403, "Public access not configured for this ODR")

        if link_state.get("link_revoked_at_utc"):
            attempt["outcome"] = "denied_expired_context"
            attempt["signals_failed"] = ["link_revoked"]
            await db.odr_preload_attempts.insert_one(dict(attempt))
            raise HTTPException(410, "Public link has been revoked")

        if link_id and link_id != link_state.get("link_id"):
            attempt["outcome"] = "denied_wrong_link"
            attempt["signals_failed"] = ["link_id_mismatch"]
            await db.odr_preload_attempts.insert_one(dict(attempt))
            raise HTTPException(403, "Public link mismatch")

        # Allowed.
        attempt["outcome"] = "allowed"
        attempt["signals_matched"] = ["doc_id_found", "link_present", "link_active"]
        if link_id == link_state.get("link_id"):
            attempt["signals_matched"].append("link_match")
        attempt["prior_odr_id"] = odr["id"]
        await db.odr_preload_attempts.insert_one(dict(attempt))

        odr.pop("_id", None)
        # Public-safe — strip continuity envelope before return.
        if "public_access" in odr:
            pa = odr["public_access"]
            odr["public_access"] = {
                "link_scope": pa.get("link_scope"),
                "link_revoked_at_utc": pa.get("link_revoked_at_utc"),
            }
        return odr

    # ── GET /api/odr/{id}/version-chain ──────────────────────────────

    @router.get("/{odr_id}/version-chain")
    async def version_chain(
        odr_id: str,
        actor: Dict[str, Any] = Depends(require_actor),
    ) -> Dict[str, Any]:
        """Returns the amendment chain for an ODR.

        Each ODR is its own canonical row; amendments are stored in
        `odr_amendments` (append-only). The chain returned here is
        the ordered list of (when, who, action, field_path, reason).
        """
        odr = await db.odr.find_one(
            {"id": odr_id},
            {"_id": 0, "id": 1, "doc_id": 1, "status": 1,
             "amendment_count": 1, "submitted_at": 1,
             "amend_allowed_until_utc": 1},
        )
        if not odr:
            raise HTTPException(404, "ODR not found")

        cur = db.odr_amendments.find(
            {"odr_id": odr_id}, {"_id": 0}
        ).sort("at_utc", -1).limit(500)
        amendments = await cur.to_list(length=500)
        return {
            "odr_id": odr_id,
            "doc_id": odr.get("doc_id"),
            "status": odr.get("status"),
            "submitted_at": odr.get("submitted_at"),
            "amend_allowed_until_utc": odr.get("amend_allowed_until_utc"),
            "amendment_count": odr.get("amendment_count", 0),
            "amendments": amendments,
            "amendment_chain_length": len(amendments),
        }

    return router


__all__ = ["build_odr_continuity_router", "ensure_continuity_indexes"]
