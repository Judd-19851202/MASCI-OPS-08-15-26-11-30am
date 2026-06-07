"""Public (unauthenticated) endpoints for QR landings + damage intake.

These are the ONLY trench-safety endpoints that don't require a portal
token. They live behind the existing platform's public-POST rate-limit
(per-IP) and never expose admin data.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException, Request

from ._helpers import now_iso, public_view, write_audit
from ._models import DAMAGE_REPORT_KINDS, DamageReportPublic


def register_public_routes(api_router: APIRouter, db) -> None:

    # ──────────────────────────────────────────────────────────────────
    # PUBLIC OVERVIEW — counts only · no PII · no names · no IDs
    # Used by the public Trench Safety Dashboard (Phase 3.5 GAP-1).
    # ──────────────────────────────────────────────────────────────────
    @api_router.get("/trench-safety/public/overview")
    async def public_overview():
        """Anonymous fleet shape. Counts only — no asset identities."""
        # Single in-memory rollup (fleet ≤ 250 indefinitely; see audit §5).
        docs = await db.trench_safety_assets.find(
            {"is_active": True},
            {"_id": 0, "operational_status": 1, "asset_type": 1},
        ).to_list(5000)

        counts_by_status = {
            "Available": 0,
            "Assigned": 0,
            "In Transport": 0,
            "Inspection Hold": 0,
            "Repair": 0,
        }
        counts_by_type = {
            "Trench Box": 0,
            "End Panel": 0,
            "Spreader Bar": 0,
            "Hydraulic Shore": 0,
            "Slide Rail System": 0,
            "Trench Jack": 0,
            "Ladder": 0,
            "Accessory": 0,
        }
        for d in docs:
            s = d.get("operational_status") or "Available"
            if s in counts_by_status:
                counts_by_status[s] += 1
            t = d.get("asset_type") or "Trench Box"
            if t in counts_by_type:
                counts_by_type[t] += 1

        return {
            "total_active_assets": len(docs),
            "counts_by_status": counts_by_status,
            "counts_by_type": counts_by_type,
        }

    # ──────────────────────────────────────────────────────────────────
    # QR landing — field-safe projection by asset_id
    # ──────────────────────────────────────────────────────────────────
    @api_router.get("/trench-safety/public/assets/{asset_id}")
    async def public_qr_landing(
        asset_id: str,
        request: Request,
        x_forwarded_for: Optional[str] = Header(default=None),
    ):
        doc = await db.trench_safety_assets.find_one(
            {"asset_id": asset_id}, {"_id": 0}
        )
        if not doc:
            raise HTTPException(404, "Asset not found")

        # Record the scan (best-effort, never fail the landing)
        try:
            ip = (x_forwarded_for or "").split(",")[0].strip() or (
                request.client.host if request.client else None
            )
            await db.trench_safety_qr_scans.insert_one({
                "id": str(uuid.uuid4()),
                "asset_id": asset_id,
                "scanned_at": now_iso(),
                "scanned_by": None,
                "user_agent": request.headers.get("user-agent", ""),
                "ip": ip,
            })
        except Exception:  # noqa: BLE001
            pass

        return public_view(doc)

    # ──────────────────────────────────────────────────────────────────
    # Damage report intake (PUBLIC POST — mirrors existing public-POST
    # pattern; relies on the platform-level per-IP rate-limit applied
    # in CORS/limiter middleware)
    # ──────────────────────────────────────────────────────────────────
    @api_router.post("/trench-safety/public/damage-report")
    async def public_damage_report(
        payload: DamageReportPublic,
        request: Request,
        x_forwarded_for: Optional[str] = Header(default=None),
    ):
        if payload.kind not in DAMAGE_REPORT_KINDS:
            raise HTTPException(
                422, f"kind must be one of {list(DAMAGE_REPORT_KINDS)}"
            )
        asset = await db.trench_safety_assets.find_one(
            {"asset_id": payload.asset_id},
            {"_id": 0, "id": 1, "asset_id": 1, "operational_status": 1},
        )
        if not asset:
            raise HTTPException(404, "Asset not found")

        ip = (x_forwarded_for or "").split(",")[0].strip() or (
            request.client.host if request.client else None
        )

        doc = {
            "id": str(uuid.uuid4()),
            "asset_id": payload.asset_id,
            "asset_uuid": asset["id"],
            "kind": payload.kind,
            "description": payload.description,
            "reported_by_name": payload.reported_by_name,
            "contact": payload.contact,
            "received_at": now_iso(),
            "source": "Public QR Damage Report",
            "status": "Open",
            "ip": ip,
            "user_agent": request.headers.get("user-agent", ""),
        }
        # Persist as an Open repair so Shop sees it in their queue.
        # Status Open (not 'In Progress') because Shop hasn't reviewed yet.
        # Asset is NOT auto-moved to Repair — that would let an
        # anonymous caller take a box out of service. Shop reviews and
        # promotes via the authenticated repairs endpoint.
        repair_doc = {
            "id": str(uuid.uuid4()),
            "asset_id": payload.asset_id,
            "asset_uuid": asset["id"],
            "status": "Open",
            "issue_description": f"[{payload.kind}] {payload.description}",
            "report_kind": payload.kind,
            "reported_by": payload.reported_by_name or "anonymous",
            "photo_refs": [],
            "repair_vendor": None,
            "repair_cost": None,
            "completion_notes": "",
            "requires_reinspection": True,
            "opened_at": now_iso(),
            "opened_by": f"public:{ip or 'unknown'}",
            "closed_at": None,
            "closed_by": None,
            "pending_shop_review": True,
            "public_intake_id": doc["id"],
        }
        await db.trench_safety_repairs.insert_one(repair_doc)
        await write_audit(
            db, kind="trench_asset_damage_reported_public",
            asset_id=payload.asset_id,
            actor={"_actor": "public", "name": payload.reported_by_name or "anonymous"},
            detail={"repair_id": repair_doc["id"], "report_kind": payload.kind, "ip": ip},
        )
        # Phase 7.5C — bell fanout (no email per routing matrix)
        try:
            from routes.trench_safety.notifications import notify_damage_report  # noqa: PLC0415
            report_for_notif = {
                "id": doc["id"],
                "kind": payload.kind,
                "description": payload.description,
            }
            await notify_damage_report(db, asset, report_for_notif)
        except Exception:  # noqa: BLE001
            pass
        return {"ok": True, "received_at": doc["received_at"], "kind": payload.kind}
