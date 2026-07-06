"""Inspection submission + listing endpoints."""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from ._helpers import (
    apply_resolved_status,
    clear_hold,
    now_iso,
    open_hold,
    upsert_equipment_master_mirror,
    write_audit,
)
from ._models import (
    INSPECTION_RESULTS,
    INSPECTION_TYPES,
    SEVERITIES,
    InspectionSubmit,
)


def register_inspection_routes(
    api_router: APIRouter,
    db,
    *,
    require_safety_or_admin,
    require_any_portal,
) -> None:
    LIST_PATH = "/trench-safety/assets/{ident}/inspections"

    # ──────────────────────────────────────────────────────────────────
    # List inspections for an asset
    # ──────────────────────────────────────────────────────────────────
    @api_router.get(LIST_PATH)
    async def list_inspections(
        ident: str,
        limit: int = Query(default=100, ge=1, le=500),
        _actor: dict = Depends(require_any_portal),
    ):
        asset = await db.trench_safety_assets.find_one(
            {"$or": [{"asset_id": ident}, {"id": ident}]},
            {"_id": 0, "asset_id": 1},
        )
        if not asset:
            raise HTTPException(404, "Trench safety asset not found")

        cursor = (
            db.trench_safety_inspections.find(
                {"asset_id": asset["asset_id"]}, {"_id": 0}
            )
            .sort("submitted_at", -1)
            .limit(limit)
        )
        return {"items": await cursor.to_list(limit)}

    # ──────────────────────────────────────────────────────────────────
    # Submit inspection (Safety + Admin) — Phase 4B severity matrix
    # ──────────────────────────────────────────────────────────────────
    @api_router.post(LIST_PATH)
    async def submit_inspection(
        ident: str,
        payload: InspectionSubmit,
        request: Request,
        actor: dict = Depends(require_safety_or_admin),
    ):
        # TRACK 22.4b-followup-Trench-Writes-Idempotency · exactly-once.
        # All side effects (inspection insert, hold transitions, repair
        # stub, asset status recompute, audit, notification) live inside
        # `_do_create` so a replay returns the cached response without
        # re-emitting any downstream signals.
        from lib.idempotency import with_idempotency, idem_key_from_request  # noqa: PLC0415
        key = idem_key_from_request(request)

        async def _do_create():
            if payload.inspection_type not in INSPECTION_TYPES:
                raise HTTPException(
                    422, f"inspection_type must be one of {list(INSPECTION_TYPES)}"
                )
            if payload.result not in INSPECTION_RESULTS:
                raise HTTPException(
                    422, f"result must be one of {list(INSPECTION_RESULTS)}"
                )
            if payload.severity not in SEVERITIES:
                raise HTTPException(
                    422, f"severity must be one of {list(SEVERITIES)}"
                )

            asset = await db.trench_safety_assets.find_one(
                {"$or": [{"asset_id": ident}, {"id": ident}]},
                {"_id": 0},
            )
            if not asset:
                raise HTTPException(404, "Trench safety asset not found")

            # Monthly/Annual require competent person flag
            if (
                payload.inspection_type in {"Monthly Competent Person", "Annual Review"}
                and not payload.competent_person_confirmed
            ):
                raise HTTPException(
                    422,
                    "competent_person_confirmed must be true for "
                    "Monthly Competent Person or Annual Review inspections",
                )

            actor_email = (actor or {}).get("email") or (actor or {}).get("_actor") or "unknown"
            doc = {
                "id": str(uuid.uuid4()),
                "asset_id": asset["asset_id"],
                "asset_uuid": asset["id"],
                "inspection_type": payload.inspection_type,
                "inspector_name": payload.inspector_name,
                "inspector_role": payload.inspector_role,
                "competent_person_confirmed": bool(payload.competent_person_confirmed),
                "checklist": [item.model_dump() for item in payload.checklist],
                "findings": payload.findings,
                "corrective_actions": payload.corrective_actions,
                "result": payload.result,
                "severity": payload.severity,
                "signature": payload.signature,
                "project_id": payload.project_id or asset.get("current_project_id"),
                "project_name": payload.project_name or asset.get("current_project_name"),
                "location": payload.location or asset.get("current_location"),
                "follow_up_action": payload.follow_up_action,
                "photo_refs": list(payload.photo_refs),
                "submitted_at": now_iso(),
                "submitted_by": actor_email,
            }
            await db.trench_safety_inspections.insert_one(doc)
            doc.pop("_id", None)

            # Persist last_inspection_* on the asset; hold transitions go through
            # the hold engine (single source of truth).
            await db.trench_safety_assets.update_one(
                {"id": asset["id"]},
                {"$set": {
                    "last_inspection_at": doc["submitted_at"],
                    "last_inspection_result": payload.result,
                    "last_inspection_severity": payload.severity,
                    "updated_at": now_iso(),
                    "updated_by": actor_email,
                }},
            )

            audit_kind = "trench_asset_inspection_submitted"
            repair_stub_id: Optional[str] = None

            if payload.result == "Fail":
                audit_kind = "trench_asset_inspection_failed"
                # Always open Inspection Hold on Fail
                await open_hold(
                    db, asset_id=asset["asset_id"], kind="Inspection Hold",
                    reason=f"Failed {payload.inspection_type}: {payload.findings or 'no findings recorded'}",
                    source="inspection", source_ref=f"inspection:{doc['id']}",
                    opened_by=actor_email,
                )
                # Critical severity → also open Safety Hold
                if payload.severity == "Critical":
                    await open_hold(
                        db, asset_id=asset["asset_id"], kind="Safety Hold",
                        reason=f"Critical damage observed in {payload.inspection_type}: {payload.findings or 'no findings'}",
                        source="inspection", source_ref=f"inspection:{doc['id']}",
                        opened_by=actor_email,
                    )
                # Major or Critical severity → auto Repair stub (Shop visibility)
                if payload.severity in {"Major", "Critical"}:
                    stub = {
                        "id": str(uuid.uuid4()),
                        "asset_id": asset["asset_id"],
                        "asset_uuid": asset["id"],
                        "status": "Open",
                        "kind": "repair_recommendation",
                        "source": f"inspection:{doc['id']}",
                        "severity_at_creation": payload.severity,
                        "issue_description": payload.findings
                            or f"{payload.severity} severity finding in {payload.inspection_type}",
                        "reported_by": actor_email,
                        "photo_refs": list(payload.photo_refs),
                        "repair_vendor": None,
                        "repair_cost": None,
                        "completion_notes": "",
                        "requires_reinspection": True,
                        "opened_at": now_iso(),
                        "opened_by": actor_email,
                        "closed_at": None,
                        "closed_by": None,
                    }
                    await db.trench_safety_repairs.insert_one(stub)
                    stub.pop("_id", None)
                    repair_stub_id = stub["id"]
                    # Opening a repair stub also opens Maintenance Hold
                    await open_hold(
                        db, asset_id=asset["asset_id"], kind="Maintenance Hold",
                        reason=f"Auto repair stub from {payload.inspection_type} (severity {payload.severity})",
                        source="repair", source_ref=f"repair:{stub['id']}",
                        opened_by=actor_email,
                    )

            elif payload.result == "Pass":
                audit_kind = "trench_asset_inspection_passed"
                # Monthly/Annual Pass with competent person → clear Inspection Hold
                if (
                    payload.inspection_type in {"Monthly Competent Person", "Annual Review"}
                    and payload.competent_person_confirmed
                ):
                    await clear_hold(
                        db, asset_id=asset["asset_id"], kind="Inspection Hold",
                        clear_reason=f"Cleared by {payload.inspection_type} Pass (competent person confirmed)",
                        clear_source="monthly_pass", cleared_by=actor_email,
                    )

            # Recompute final operational_status from the hold engine and mirror.
            fresh = await apply_resolved_status(db, asset["asset_id"], actor_email)

            await write_audit(
                db, kind=audit_kind, asset_id=asset["asset_id"], actor=actor,
                detail={
                    "inspection_id": doc["id"],
                    "inspection_type": payload.inspection_type,
                    "result": payload.result,
                    "severity": payload.severity,
                    "status_after": fresh.get("operational_status"),
                    "repair_stub_id": repair_stub_id,
                },
            )
            # Phase 7.5C — bell + email fanout for Fail Major/Critical
            if payload.result == "Fail" and payload.severity in {"Major", "Critical"}:
                try:
                    from routes.trench_safety.notifications import notify_inspection_failed  # noqa: PLC0415
                    # Construct an inspector_name surrogate from actor for the email body
                    doc_for_notif = dict(doc)
                    doc_for_notif.setdefault("inspector_name", actor_email)
                    doc_for_notif.setdefault("notes", payload.findings or "")
                    await notify_inspection_failed(db, fresh or asset, doc_for_notif)
                except Exception:  # noqa: BLE001
                    pass
            return {"inspection": doc, "asset": fresh, "repair_stub_id": repair_stub_id}

        return await with_idempotency(
            db, key, actor or {"role": "public"}, _do_create,
            workflow="trench_inspection",
        )
