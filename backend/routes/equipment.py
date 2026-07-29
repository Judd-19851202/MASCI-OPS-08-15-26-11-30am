"""Equipment Pre-Op inspections + shop sign-off + trends.

Extracted from server.py 2026-04-28 (P1 refactor batch 4).

Routes registered:
    POST    /equipment-inspections                                    public
    GET     /equipment-inspections                                    shop or admin
    GET     /equipment-inspections/{id}                               shop or admin
    DELETE  /equipment-inspections/{id}                               admin only
    GET     /admin/equipment-inspections/trends?days=                 admin only (iter180 P0: /api/admin/* is strict-admin)
    GET     /admin/equipment-inspections/open-items?severity=         admin only (iter180 P0: /api/admin/* is strict-admin)
    POST    /admin/equipment-inspections/{id}/signoff                 admin only (iter180 P0: /api/admin/* is strict-admin)
    DELETE  /admin/equipment-inspections/{id}/signoff?section=&item=  admin only (iter180 P0: /api/admin/* is strict-admin)
"""
from __future__ import annotations

import re as _re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from lib.enterprise_governance import governance_project_scope_allows, governance_project_scope_filter


# ============================================================
# Pydantic models
# ============================================================
class EquipmentInspectionCreate(BaseModel):
    """Daily pre-shift OSHA equipment inspection."""
    model_config = ConfigDict(extra="allow")

    project_name: str
    project_number: Optional[str] = ""
    location: str
    inspection_date: str  # YYYY-MM-DD
    inspection_time: str  # HH:MM

    operator_name: str
    equipment_type: str
    equipment_unit: str
    equipment_make: Optional[str] = ""
    equipment_model: Optional[str] = ""
    equipment_serial: Optional[str] = ""

    hour_meter: Optional[str] = ""
    odometer: Optional[str] = ""

    checklist: Dict[str, Any] = Field(default_factory=dict)
    fail_count: int = 0
    pass_count: int = 0
    na_count: int = 0

    deficiency_notes: Optional[str] = ""
    corrective_actions: Optional[str] = ""
    out_of_service: Optional[str] = "No"

    photos: List[str] = Field(default_factory=list)
    operator_signature: Optional[str] = ""

    # Track 13.31B-D5.4 · structured canonical section capture (additive).
    # Mirror of the canonical inspection sections rendered from the
    # /api/asset-spine/inspection-templates registry. Persisted alongside
    # the legacy `checklist` so existing defect routing keeps firing.
    inspection_sections: Optional[Dict[str, Any]] = None


class EquipmentInspection(EquipmentInspectionCreate):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    doc_id: Optional[str] = ""  # PRE-YYYY-NNNNN, stamped on insert
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class EquipmentInspectionSummary(BaseModel):
    id: str
    project_name: str
    project_number: str
    location: str
    inspection_date: str
    operator_name: str
    equipment_type: str
    equipment_unit: str
    fail_count: int
    out_of_service: str
    photo_count: int
    created_at: str
    signoff_count: int = 0
    cleared: bool = False


class ShopSignoffPayload(BaseModel):
    section: str
    item: str
    signed_by: str
    signed_by_employee_id: Optional[str] = ""  # iter364 · canonical roster employee_id on shop sign-off
    notes: Optional[str] = ""
    action_taken: Optional[str] = ""


# ============================================================
# Major OOS items list — anything in this set escalates a FAIL to
# "OUT OF SERVICE" instead of "Needs Attention". Keep in sync with
# /app/frontend/src/lib/equipmentSeverity.js.
# ============================================================
MAJOR_OOS_ITEMS_BACKEND = [
    "Steps, grab handles, ladders secure & clean",
    "Air filter / pre-cleaner condition",
    "ROPS / FOPS structure - no cracks or damage",
    "Seat & seat belt - functional, not torn",
    "Horn operational",
    "Backup alarm operational",
    "Service brakes - firm pedal, holds machine",
    "Parking brake - holds machine on grade",
    "Steering - responsive, no excessive play",
    "Emergency / kill switch operational",
    "Visible fluid leaks (engine, hydraulic, fuel, coolant)",
    "Belts and hoses - no cracks, fraying, or leaks",
    "Tires - inflation, cuts, sidewall damage, tread wear",
    "Tires - inflation, cuts, tread wear",
    "Tires - inflation, condition, no cuts (front & rear)",
    "Tires - inflation, cuts, tread",
    "Tires - inflation, cuts, tread depth (all positions)",
    "Tires - inflation, cuts, tread (front & rear)",
    "Tires (rear, if smooth-drum) - inflation, wear",
    "Tires / tracks - condition & wear",
    "Tracks or tires - condition & wear",
    "Tracks / undercarriage - tension, wear, no missing pads",
    "Tracks / undercarriage - tension, wear",
    "Tracks / undercarriage - tension & wear",
    "Tracks / undercarriage - condition & wear",
    "Tracks - tension, drive sprockets, idlers",
    "Strobe / beacon light (Required)",
    "Fire extinguisher present, charged & inspected",
    "Hydraulic hoses - no chafing or bulges",
    "Hydraulic cylinders - rod condition, no leaks",
    "Hydraulic cylinders & hoses",
    "Hydraulic couplers / auxiliary lines - no leaks",
    "Hydraulic hoses & cylinders",
    "Boom, stick, bucket - no cracks at pivot points",
    "Backhoe boom, dipper, bucket - no cracks at pivots",
    "Lift arms & linkage - no cracks",
    "Lift arms - no cracks, pivot pins secure",
    "Loader arms, pins, retainers secure",
    "Tow arms / tow points - no cracks",
    "Boom sections - no cracks, wear pads in place",
    "Stabilizer pads / outriggers - operate, no leaks",
    "Stabilizer / outrigger controls",
    "Stabilizer / outrigger pads (if equipped) operate freely",
    "Stabilizer / frame-level controls",
]
MAJOR_OOS_SET = set(MAJOR_OOS_ITEMS_BACKEND)


def _iter_failed_items(insp: Dict[str, Any]):
    """Yield (section_title, item_name, result_dict, severity) for every FAIL."""
    for sec_title, sec in (insp.get("checklist") or {}).items():
        if not isinstance(sec, dict):
            continue
        for item_name, res in sec.items():
            if not isinstance(res, dict):
                continue
            if res.get("status") == "fail":
                sev = "oos" if item_name in MAJOR_OOS_SET else "attn"
                yield sec_title, item_name, res, sev


# ============================================================
# Route registration
# ============================================================
def register_equipment_routes(
    api_router: APIRouter, db, require_admin, require_shop_or_admin,
    rate_limit_public_post, schedule_auto_email, remember_unit,
):
    """Attach Equipment Pre-Op + Shop Sign-Off endpoints to the shared router.

    `remember_unit` is a callable that takes (equipment_type, unit_label, make,
    model, serial) and stores the unit in the equipment-units dropdown
    catalog. Lives in server.py (legacy `create_equipment_unit` route),
    injected here so we don't pull that whole module along.
    """

    @api_router.post(
        "/equipment-inspections", response_model=EquipmentInspection,
        dependencies=[Depends(rate_limit_public_post)],
    )
    async def create_equipment_inspection(payload: EquipmentInspectionCreate, request: Request):
        # TRACK 22.4b-followup-Idempotency-Spine-Phase-2 · P1 protection.
        # Same-key retries → exactly one inspection + exactly one Shop
        # notification + exactly one Trust Spine event + exactly one
        # Maintenance Hold on failure.
        from lib.idempotency import with_idempotency, idem_key_from_request  # noqa: PLC0415
        key = idem_key_from_request(request)

        async def _do_create():
            insp = EquipmentInspection(**payload.model_dump())
            doc = insp.model_dump()
            from doc_ids import ensure_doc_id
            await ensure_doc_id(db, doc, "PRE", when=doc.get("inspection_date") or doc.get("created_at"))
            insp.doc_id = doc["doc_id"]
            # ── Phase 2B-2A · Job-ownership team_snapshot embed ──
            try:
                from lib.team_routing import snapshot_team  # noqa: PLC0415
                _snap = await snapshot_team(db, doc.get("project_number"))
                if _snap:
                    doc["team_snapshot"] = _snap
            except Exception:  # noqa: BLE001
                pass
            await db.equipment_inspections.insert_one(doc)
            doc.pop("_id", None)
            # ── Track 13.31B-D5.1 · Smart Pre-Op canonical write stamp ──
            # Resolve the canonical asset_class/type from equipment_master via
            # the asset spine resolver and patch the row in place. Additive
            # only — legacy `equipment_type` is preserved for backward compat.
            try:
                from services.inspection_classification import (
                    stamp_inspection_canonical, EXISTING_PREOP_TEMPLATES,
                )
                stamp = await stamp_inspection_canonical(
                    db, doc.get("id"), insp.equipment_unit,
                    legacy_equipment_type=insp.equipment_type or "",
                    template_set=EXISTING_PREOP_TEMPLATES,
                )
                if stamp:
                    doc.update(stamp)
            except Exception:
                pass
            # Also remember this unit so it shows up in the dropdown next time
            if insp.equipment_unit and insp.equipment_type:
                try:
                    await remember_unit(
                        insp.equipment_type, insp.equipment_unit,
                        insp.equipment_make or "", insp.equipment_model or "",
                        insp.equipment_serial or "",
                    )
                except Exception:
                    pass
            # TRACK 15.76 · Trust Spine — open record lifecycle. Workflow
            # is "equipment-inspection" for pre-op (default) and "dvir"
            # when ``insp.kind == "dvir"`` (iter251 split).
            try:
                from lib.trust_spine import emit_record_created  # noqa: PLC0415
                _wf = "dvir" if (doc.get("kind") or "").lower() == "dvir" else "equipment-inspection"
                await emit_record_created(
                    db, workflow=_wf, record=doc,
                    module="routes/equipment.py:create_inspection",
                )
            except Exception:  # noqa: BLE001
                pass
            schedule_auto_email("equipment-inspection", doc)

            # ── Failed Pre-Op → Pending Maintenance Hold (iter128) ──
            # Fire-and-forget. Failure here MUST NOT abort the pre-op save.
            if (insp.fail_count or 0) > 0 and insp.equipment_unit:
                try:
                    # Resolve unit_number → equipment_master.id (case-insensitive).
                    eq = await db.equipment_master.find_one(
                        {"unit_number": {"$regex": f"^{_re.escape(insp.equipment_unit)}$", "$options": "i"}},
                        {"_id": 0, "id": 1},
                    )
                    if eq:
                        from routes.operations import create_pending_maintenance_hold
                        fail_summary = (
                            f"{insp.fail_count} item(s) failed pre-op inspection · "
                            f"operator: {insp.operator_name or '—'} · doc: {insp.doc_id or insp.id}"
                        )
                        await create_pending_maintenance_hold(
                            db,
                            asset_id=eq["id"],
                            reason=f"Failed pre-op inspection ({insp.fail_count} item{'' if insp.fail_count == 1 else 's'})",
                            severity="high" if insp.fail_count >= 3 else "medium",
                            notes=fail_summary,
                            source_module="field",
                            source_record_id=insp.id,
                            created_by=insp.operator_name or "field-preop",
                        )
                except Exception:
                    # Never break the pre-op flow on hold creation issues
                    pass

                # Phase E · Cross-system fan-out — failed pre-ops must
                # spawn a shop equipment-issue task + notifications to
                # shop and dispatch. Fire-and-forget; never blocks save.
                try:
                    from lib.event_fanout import emit_task_and_notification, emit_notification  # noqa: PLC0415
                    from lib.team_routing import apply_routing  # noqa: PLC0415
                    fail_n = int(insp.fail_count or 0)
                    priority = "Critical" if fail_n >= 3 else "High"
                    eq_id_for_link = None
                    try:
                        eq2 = await db.equipment_master.find_one(
                            {"unit_number": {"$regex": f"^{_re.escape(insp.equipment_unit)}$", "$options": "i"}},
                            {"_id": 0, "id": 1},
                        )
                        eq_id_for_link = (eq2 or {}).get("id")
                    except Exception:
                        eq_id_for_link = None
                    title = f"Failed pre-op — {insp.equipment_unit or '—'} ({fail_n} item{'s' if fail_n != 1 else ''})"
                    _shop_notif = {
                        "type": "preop.failed",
                        "title": title[:200],
                        "message": (f"Operator: {insp.operator_name or '—'} · "
                                    f"{fail_n} failed item(s)")[:200],
                        "severity": "Critical" if priority == "Critical" else "Warning",
                        "recipient_role": "shop",
                        "linked_source_module": "equipment.preop",
                        "linked_source_record_id": insp.id,
                        "linked_equipment_id": eq_id_for_link,
                        "linked_project_number": insp.project_number or None,
                    }
                    await apply_routing(db, _shop_notif,
                                        project_number=insp.project_number,
                                        event_key="preop.failed")
                    await emit_task_and_notification(
                        db,
                        task={
                            "title": title[:200],
                            "description": (f"Operator: {insp.operator_name or '—'} · "
                                            f"Doc: {insp.doc_id or insp.id} · "
                                            f"Equipment: {insp.equipment_make or ''} {insp.equipment_model or ''}".strip())[:4000],
                            "source_module": "equipment.preop",
                            "source_record_id": insp.id,
                            "linked_equipment_id": eq_id_for_link,
                            "linked_project_number": insp.project_number or None,
                            "assignee_role": "shop",
                            "priority": priority,
                            "created_by": {"role": "system", "via": "preop-fanout"},
                        },
                        notification=_shop_notif,
                    )
                    # Dispatch visibility — same event, no task assignment
                    _dispatch_notif = {
                        "type": "preop.failed",
                        "title": title[:200],
                        "message": f"{insp.equipment_unit or '—'} flagged from pre-op",
                        "severity": "Warning",
                        "recipient_role": "dispatch",
                        "linked_source_module": "equipment.preop",
                        "linked_source_record_id": insp.id,
                        "linked_equipment_id": eq_id_for_link,
                        "linked_project_number": insp.project_number or None,
                    }
                    await apply_routing(db, _dispatch_notif,
                                        project_number=insp.project_number,
                                        event_key="preop.dispatch_visibility")
                    await emit_notification(db, _dispatch_notif)
                    # Iter160 · Operational signal — equipment fail throughput
                    try:
                        from lib.operational_signals import record_signal  # noqa: PLC0415
                        await record_signal(
                            db, signal="equipment.fail", module="equipment.preop",
                            dims={
                                "priority": priority,
                                "fail_count": int(fail_n),
                                "equipment_id": (eq_id_for_link or "")[:48],
                            },
                        )
                    except Exception:
                        pass
                except Exception as e:  # noqa: BLE001
                    import logging
                    logging.getLogger(__name__).warning("[preop-fanout] failed: %s", e)

            return insp

        return await with_idempotency(db, key, {"role": "public"}, _do_create, workflow="equipment_inspection")


    @api_router.get("/equipment-inspections", response_model=List[EquipmentInspectionSummary])
    async def list_equipment_inspections(actor=Depends(require_shop_or_admin)):
        # $size aggregation skips pulling the photos[] array — much faster.
        # Iter520 · Phase V.5 · P0-2A — apply PM scope filter so PM sees
        # only inspections for projects they manage (matches the detail
        # endpoint's behavior; prevents 404-bounce on row click).
        scope_query = await governance_project_scope_filter(db, actor)
        if scope_query is None:
            return []
        match_stage = dict(scope_query)
        pipeline = []
        if match_stage:
            pipeline.append({"$match": match_stage})
        pipeline.extend([
            {"$sort": {"created_at": -1}},
            {"$limit": 1000},
            {"$project": {
                "_id": 0, "id": 1, "project_name": 1, "project_number": 1,
                "location": 1, "inspection_date": 1, "operator_name": 1,
                "equipment_type": 1, "equipment_unit": 1, "fail_count": 1,
                "out_of_service": 1, "created_at": 1,
                "photo_count":   {"$size": {"$ifNull": ["$photos", []]}},
                "signoff_count": {"$size": {"$ifNull": ["$shop_signoffs", []]}},
            }},
        ])
        docs = await db.equipment_inspections.aggregate(pipeline).to_list(1000)
        return [
            EquipmentInspectionSummary(
                id=d.get("id", ""),
                project_name=d.get("project_name", ""),
                project_number=d.get("project_number", ""),
                location=d.get("location", ""),
                inspection_date=d.get("inspection_date", ""),
                operator_name=d.get("operator_name", ""),
                equipment_type=d.get("equipment_type", ""),
                equipment_unit=d.get("equipment_unit", ""),
                fail_count=d.get("fail_count", 0) or 0,
                out_of_service=d.get("out_of_service", "No"),
                photo_count=d.get("photo_count", 0) or 0,
                created_at=d.get("created_at", ""),
                signoff_count=d.get("signoff_count", 0) or 0,
                cleared=(d.get("fail_count", 0) or 0) > 0
                        and (d.get("signoff_count", 0) or 0) >= (d.get("fail_count", 0) or 0),
            )
            for d in docs
        ]

    @api_router.get("/equipment-inspections/{inspection_id}")
    async def get_equipment_inspection(inspection_id: str, actor=Depends(require_shop_or_admin)):
        doc = await db.equipment_inspections.find_one({"id": inspection_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="Equipment inspection not found")
        if not await governance_project_scope_allows(db, actor, doc.get("project_number")):
            raise HTTPException(status_code=404, detail="Equipment inspection not found")
        return doc

    @api_router.delete("/equipment-inspections/{inspection_id}")
    async def delete_equipment_inspection(inspection_id: str, _: bool = Depends(require_admin)):
        result = await db.equipment_inspections.delete_one({"id": inspection_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Equipment inspection not found")
        return {"deleted": True, "id": inspection_id}

    # ---------- Trends ----------
    @api_router.get("/admin/equipment-inspections/trends")
    async def equipment_inspection_trends(
        days: int = 90,
        actor=Depends(require_shop_or_admin),
    ):
        """Three leaderboards: most-problematic equipment units, operators with
        most failed inspections, and jobsites trending bad. Last `days` days.
        """
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        scope_query = await governance_project_scope_filter(db, actor, base_filter={"created_at": {"$gte": since}})
        if scope_query is None:
            return {
                "window_days": days,
                "totals": {
                    "inspections": 0,
                    "out_of_service_fails": 0,
                    "needs_attention_fails": 0,
                },
                "equipment": [],
                "operators": [],
                "jobsites": [],
            }
        cursor = db.equipment_inspections.find(
            scope_query,
            {"_id": 0},
        )
        eq: Dict[str, Dict[str, Any]] = {}
        op: Dict[str, Dict[str, Any]] = {}
        site: Dict[str, Dict[str, Any]] = {}
        total_inspections = 0
        total_oos = 0
        total_attn = 0

        async for d in cursor:
            total_inspections += 1
            oos_count = 0
            attn_count = 0
            for _sec, _it, _res, sev in _iter_failed_items(d):
                if sev == "oos":
                    oos_count += 1
                else:
                    attn_count += 1
            total_oos += oos_count
            total_attn += attn_count

            eq_key = f"{d.get('equipment_type','?')} · {d.get('equipment_unit','?')}".strip()
            e = eq.setdefault(eq_key, {
                "equipment_type": d.get("equipment_type", ""),
                "equipment_unit": d.get("equipment_unit", ""),
                "inspections": 0, "oos_fails": 0, "attn_fails": 0,
                "last_inspection_date": "",
            })
            e["inspections"] += 1
            e["oos_fails"] += oos_count
            e["attn_fails"] += attn_count
            if (d.get("inspection_date") or "") > e["last_inspection_date"]:
                e["last_inspection_date"] = d.get("inspection_date") or ""

            op_key = (d.get("operator_name") or "—").strip() or "—"
            o = op.setdefault(op_key, {
                "operator_name": op_key,
                "inspections": 0, "oos_fails": 0, "attn_fails": 0,
            })
            o["inspections"] += 1
            o["oos_fails"] += oos_count
            o["attn_fails"] += attn_count

            site_key = (d.get("project_number") or d.get("project_name") or "—").strip() or "—"
            s = site.setdefault(site_key, {
                "project_number": d.get("project_number", ""),
                "project_name": d.get("project_name", ""),
                "inspections": 0, "oos_fails": 0, "attn_fails": 0,
            })
            s["inspections"] += 1
            s["oos_fails"] += oos_count
            s["attn_fails"] += attn_count

        def by_severity(rec):
            return (-rec["oos_fails"], -rec["attn_fails"], -rec["inspections"])

        return {
            "window_days": days,
            "totals": {
                "inspections": total_inspections,
                "out_of_service_fails": total_oos,
                "needs_attention_fails": total_attn,
            },
            "equipment": sorted(eq.values(), key=by_severity)[:50],
            "operators": sorted(op.values(), key=by_severity)[:50],
            "jobsites": sorted(site.values(), key=by_severity)[:50],
        }

    # ---------- Open shop items ----------
    @api_router.get("/admin/equipment-inspections/open-items")
    async def open_signoff_items(
        severity: str = "all",  # oos | attn | all
        actor=Depends(require_shop_or_admin),
    ):
        """Every still-open FAIL item (no shop sign-off yet) across all
        equipment inspections, sorted by inspection date desc."""
        scope_query = await governance_project_scope_filter(db, actor, base_filter={"fail_count": {"$gt": 0}})
        if scope_query is None:
            return {"items": [], "count": 0}
        cursor = db.equipment_inspections.find(
            scope_query, {"_id": 0}
        ).sort("created_at", -1)
        out: List[Dict[str, Any]] = []
        async for d in cursor:
            signoffs = {s.get("key"): s for s in (d.get("shop_signoffs") or [])}
            for sec_title, item, res, sev in _iter_failed_items(d):
                if severity != "all" and severity != sev:
                    continue
                key = f"{sec_title}|{item}"
                if signoffs.get(key, {}).get("signed_off"):
                    continue
                out.append({
                    "inspection_id": d.get("id"),
                    "inspection_date": d.get("inspection_date") or "",
                    "equipment_type": d.get("equipment_type") or "",
                    "equipment_unit": d.get("equipment_unit") or "",
                    "operator_name": d.get("operator_name") or "",
                    "project_number": d.get("project_number") or "",
                    "project_name": d.get("project_name") or "",
                    "section": sec_title,
                    "item": item,
                    "severity": sev,
                    "operator_note": res.get("note") or "",
                    "operator_photo": res.get("photo") or "",
                    "key": key,
                })
        return {"items": out, "count": len(out)}

    # ---------- Signoff create / remove ----------
    @api_router.post("/admin/equipment-inspections/{inspection_id}/signoff")
    async def signoff_inspection_item(
        inspection_id: str,
        payload: ShopSignoffPayload,
        _: bool = Depends(require_shop_or_admin),
    ):
        """Record a shop sign-off on a single FAIL line of an equipment inspection."""
        insp = await db.equipment_inspections.find_one({"id": inspection_id}, {"_id": 0})
        if not insp:
            raise HTTPException(status_code=404, detail="Inspection not found")
        key = f"{payload.section}|{payload.item}"
        entry = {
            "key": key,
            "section": payload.section,
            "item": payload.item,
            "signed_by": payload.signed_by.strip(),
            "signed_by_employee_id": (payload.signed_by_employee_id or "").strip(),
            "signed_at": datetime.now(timezone.utc).isoformat(),
            "notes": (payload.notes or "").strip(),
            "action_taken": (payload.action_taken or "").strip(),
            "signed_off": True,
        }
        if not entry["signed_by"]:
            raise HTTPException(status_code=400, detail="signed_by is required")
        existing = list(insp.get("shop_signoffs") or [])
        existing = [s for s in existing if s.get("key") != key] + [entry]
        await db.equipment_inspections.update_one(
            {"id": inspection_id},
            {"$set": {"shop_signoffs": existing, "shop_last_signoff_at": entry["signed_at"]}},
        )
        return {"ok": True, "signoff": entry, "signoff_count": len(existing)}

    @api_router.delete("/admin/equipment-inspections/{inspection_id}/signoff")
    async def remove_signoff(
        inspection_id: str,
        section: str,
        item: str,
        _: bool = Depends(require_shop_or_admin),
    ):
        """Reopen a previously-signed-off item (e.g. shop made a mistake)."""
        key = f"{section}|{item}"
        res = await db.equipment_inspections.update_one(
            {"id": inspection_id},
            {"$pull": {"shop_signoffs": {"key": key}}},
        )
        if res.matched_count == 0:
            raise HTTPException(status_code=404, detail="Inspection not found")
        return {"ok": True}
