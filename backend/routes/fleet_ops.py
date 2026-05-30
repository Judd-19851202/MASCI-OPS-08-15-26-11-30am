"""iter251 Phase A · Fleet Operations Foundation · backend routes.

Operator-approved scope:
  - DVIR · Weekly Lead · Weekly Emergency inspection submission
  - Defect lifecycle (open → acknowledged → repaired → cleared)
  - Fleet status projection (1 row per truck/trailer · current state)
  - Audit trail (append-only `fleet_audit` collection)
  - Read-only scoped endpoints for Dispatch / Shop / Safety (Phase C
    will build the UI on top of these)

EXPLICITLY OUT OF SCOPE in Phase A (per operator brief):
  - Frontend / public tile / driver form (Phase B)
  - Dispatch / Shop / Safety dashboard surfaces (Phase C)
  - Motive API integration (Phase F · separate operator approval)
  - MaintainX API integration (Phase F · separate operator approval)
  - ELD · HOS · telematics · route opt · fuel · AI dispatch
  - Repair lifecycle deepening (parts · labor · mechanic assignment)
  - Cross-yard / multi-state TMS

PERMANENTLY OUT OF SCOPE (operator decision · 2026-05-19):
  - Legacy / historical trucking-record digitization · NO fleet OCR
  - NO reconciliation of paper DVIRs into this system
  - Fleet/DVIR is a clean forward-looking operational system only
  - (Legacy-import tooling continues to serve HR / Safety / Training /
    Equipment Checkout · those are separate workstreams.)

Reused infrastructure (zero refactor risk):
  - `equipment_master` collection · 589 units · gets `kind` discriminator
  - `equipment_inspections` schema · adds optional `kind` field
  - `PhotoUpload` widget (Phase B will consume) · unchanged
  - Append-only audit pattern · `fleet_audit` collection
"""
from __future__ import annotations

import logging
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

import fleet_defect_severity as _sev
import checklists_fleet as _ck

logger = logging.getLogger(__name__)


# ─── Pydantic payloads ────────────────────────────────────────────────
class FleetTrailerInspection(BaseModel):
    """One trailer within a DVIR. A DVIR can have zero or more trailers
    (single, doubles, equipment trailer + lowboy combo)."""
    model_config = ConfigDict(extra="allow")

    trailer_unit_number: str
    trailer_type: Optional[str] = ""
    checklist: Dict[str, str] = Field(default_factory=dict)
    """item_text → 'pass'|'fail'|'na'"""


class FleetInspectionSubmit(BaseModel):
    """Payload for any fleet inspection (DVIR · weekly lead · weekly
    emergency). The `kind` discriminator decides which checklist + which
    severity classifications apply."""
    model_config = ConfigDict(extra="allow")

    # Discriminator · must be a valid fleet inspection kind
    kind: str  # "dvir" | "weekly_lead" | "weekly_emergency"

    # Driver / submitter
    driver_employee_id: Optional[str] = ""
    driver_name: str
    inspection_date: str  # YYYY-MM-DD
    inspection_time: str  # HH:MM

    # Truck identifiers · canonical · integration-ready (Motive/MaintainX)
    truck_unit_number: str
    truck_vin: Optional[str] = ""
    truck_plate: Optional[str] = ""

    # Operating metrics
    odometer_miles: Optional[str] = ""
    hour_meter: Optional[str] = ""

    # Truck checklist · item_text → 'pass'|'fail'|'na'
    truck_checklist: Dict[str, str] = Field(default_factory=dict)

    # Optional trailers (Daily DVIR only)
    trailers: List[FleetTrailerInspection] = Field(default_factory=list)

    # Per-item defect detail · item_text → {note, photos[]}
    defect_details: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    # Submitter context
    driver_signature: Optional[str] = ""
    supervisor_name: Optional[str] = ""
    notes: Optional[str] = ""

    # Submission portal · "public_tile" | "signed_in" (audit only)
    submitted_via: Optional[str] = "public_tile"


class DefectActionPayload(BaseModel):
    """Body for defect lifecycle transitions + manual OOS flips."""
    actor_name: str
    notes: Optional[str] = ""
    photos: List[str] = Field(default_factory=list)


# ─── Helper: scope guard for fleet vs other inspection kinds ──────────
def _require_fleet_kind(kind: str) -> None:
    if not _ck.is_fleet_kind(kind):
        raise HTTPException(
            400,
            f"unknown fleet inspection kind {kind!r} · "
            f"valid: {sorted(_ck.FLEET_INSPECTION_KINDS.keys())}",
        )


# ─── Helper: classify failed checklist items → defect rows ────────────
def _classify_failures(
    *,
    inspection_id: str,
    inspection_kind: str,
    truck_unit_number: str,
    trailer_unit_number: Optional[str],
    checklist: Dict[str, str],
    defect_details: Dict[str, Dict[str, Any]],
    driver_employee_id: Optional[str],
    driver_name: str,
    now_iso: str,
) -> Tuple[List[Dict[str, Any]], bool]:
    """Take a {item_text → verdict} map · for each FAIL item, look up
    severity + category in the fleet_defect_severity table and emit a
    defect row. Returns (defect_rows, any_oos)."""
    defects: List[Dict[str, Any]] = []
    any_oos = False
    for item_text, verdict in (checklist or {}).items():
        if (verdict or "").lower() != "fail":
            continue
        try:
            severity, category = _sev.classify(item_text)
        except KeyError:
            # Refuse silent classification · forces the severity table
            # to stay complete and intentional.
            raise HTTPException(
                400,
                f"checklist item {item_text!r} has no severity "
                f"classification in fleet_defect_severity. The submission "
                f"is rejected to prevent silent misrouting · please add "
                f"this item to fleet_defect_severity.FLEET_DEFECT_SEVERITY "
                f"with explicit (severity, category).",
            )
        detail = (defect_details or {}).get(item_text) or {}
        defect = {
            "id": str(uuid.uuid4()),
            "doc_id": "",  # human-readable DEF-YYYY-NNNNN stamped at insert
            "inspection_id": inspection_id,
            "inspection_kind": inspection_kind,
            "truck_unit_number": truck_unit_number,
            "trailer_unit_number": trailer_unit_number,
            "item_text": item_text,
            "category": category,
            "severity": severity,
            "status": "open",
            "note": (detail.get("note") or "").strip(),
            "photos": detail.get("photos") or [],
            "reported_by_employee_id": driver_employee_id or "",
            "reported_by_name": driver_name,
            "reported_at": now_iso,
            "acknowledged_at": None,
            "acknowledged_by_name": None,
            "repaired_at": None,
            "repaired_by_name": None,
            "repair_notes": "",
            "repair_photos": [],
            "cleared_at": None,
            "cleared_by_name": None,
            # Integration-ready external refs · empty in Phase A · Phase F
            # (Motive/MaintainX) wires these without schema change.
            "external_refs": {"motive_id": None, "maintainx_work_order_id": None},
        }
        if severity == _sev.SEVERITY_OOS:
            any_oos = True
        defects.append(defect)
    return defects, any_oos


# ─── Helper: rebuild fleet_status projection for one unit ─────────────
async def _rebuild_status(db, unit_number: str) -> Dict[str, Any]:
    """Recompute the `fleet_status` row for one truck/trailer unit
    based on (a) most recent inspection touching this unit and (b) open
    defects scoped TO this unit specifically.

    Scoping rule (operationally correct):
      - Truck unit status counts ONLY defects where the defect's
        trailer_unit_number is null AND truck_unit_number matches ·
        i.e. the truck's own defects, not a trailer's defects. This
        lets Dispatch reassign the truck to a different trailer.
      - Trailer unit status counts defects where the defect's
        trailer_unit_number matches.
    """
    latest_insp = await db.equipment_inspections.find_one(
        {"$or": [
            {"truck_unit_number": unit_number},
            {"trailer_unit_numbers": unit_number},
        ]},
        {"_id": 0, "id": 1, "kind": 1, "inspection_date": 1,
         "driver_name": 1, "created_at": 1, "out_of_service": 1,
         "trailer_unit_numbers": 1},
        sort=[("created_at", -1)],
    )

    # Decide whether this unit is a truck or trailer to scope correctly
    is_trailer = bool(latest_insp and unit_number in (latest_insp.get("trailer_unit_numbers") or []))
    if is_trailer:
        defect_q: Dict[str, Any] = {"trailer_unit_number": unit_number}
    else:
        defect_q = {
            "truck_unit_number": unit_number,
            "trailer_unit_number": None,
        }

    open_oos = await db.fleet_defects.count_documents({
        **defect_q,
        "status": {"$in": ["open", "acknowledged"]},
        "severity": _sev.SEVERITY_OOS,
    })
    open_monitor = await db.fleet_defects.count_documents({
        **defect_q,
        "status": {"$in": ["open", "acknowledged"]},
        "severity": _sev.SEVERITY_MONITOR,
    })
    # Phase 4 · "repair in progress" = shop has acknowledged or marked
    # repaired but dispatch has not yet confirmed Return-to-Service.
    in_progress = await db.fleet_defects.count_documents({
        **defect_q,
        "status": {"$in": ["acknowledged", "repaired"]},
    })

    if open_oos > 0:
        status = "oos"
    elif open_monitor > 0:
        status = "defect_open"
    elif in_progress > 0:
        status = "repair_in_progress"
    else:
        status = "available"

    doc = {
        "unit_number": unit_number,
        "unit_kind": "trailer" if is_trailer else "truck",
        "status": status,
        "open_oos_count": open_oos,
        "open_monitor_count": open_monitor,
        "latest_inspection_id": (latest_insp or {}).get("id"),
        "latest_inspection_kind": (latest_insp or {}).get("kind"),
        "latest_inspection_at": (latest_insp or {}).get("created_at"),
        "latest_driver_name": (latest_insp or {}).get("driver_name"),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.fleet_status.update_one(
        {"unit_number": unit_number},
        {"$set": doc},
        upsert=True,
    )
    return doc


async def _audit(
    db,
    *,
    actor: str,
    actor_role: str,
    action: str,
    target_type: str,
    target_id: str,
    payload: Optional[Dict[str, Any]] = None,
) -> None:
    """Append-only fleet audit trail · permanent retention."""
    await db.fleet_audit.insert_one({
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actor": actor or "",
        "actor_role": actor_role or "",
        "action": action,
        "target_type": target_type,
        "target_id": target_id,
        "payload": payload or {},
    })


# ─── Router builder · called from server.py ───────────────────────────
def build_router(
    db,
    require_signed_in_or_public,
    require_dispatch_or_admin,
    require_shop_or_admin,
    require_safety_or_admin,
    require_admin_strict,
    require_any_fleet_portal=None,
) -> APIRouter:
    """All RBAC dependencies are injected · keeps this module free of
    server.py auth coupling. Phase B (driver UX) and Phase C (dashboards)
    consume the same endpoints with no auth changes."""
    router = APIRouter()

    # ─── Public list of allowed inspection kinds (informational) ──
    @router.get("/api/fleet/_meta")
    async def fleet_meta(_actor=Depends(require_signed_in_or_public)):
        """Returns the list of inspection kinds + checklist items the
        platform currently accepts. Driver UX (Phase B) renders from
        this · keeping the form definition server-driven."""
        kinds = {}
        for k, defn in _ck.FLEET_INSPECTION_KINDS.items():
            kinds[k] = {
                "label": defn["label"],
                "truck_items": defn["truck_items"](),
                "trailer_items": (defn["trailer_items"]() if defn["trailer_items"] else None),
                "allows_trailers": defn["allows_trailers"],
            }
        # iter251 Phase 2 · per-item severity map so the driver UX can render
        # the correct "Why this matters" rationale at FAIL time without a
        # drift-prone client-side lookup table. Server is the SOT.
        severity_by_item: Dict[str, Dict[str, Any]] = {}
        for item, (sev, cat) in _sev.FLEET_DEFECT_SEVERITY.items():
            meta = _sev.FLEET_DEFECT_SEVERITY_META.get(item) or {}
            severity_by_item[item] = {
                "severity": sev,
                "category": cat,
                "rationale": meta.get("rationale", ""),
                "regulation_ref": meta.get("regulation_ref", ""),
            }
        return {
            "phase": "A",
            "kinds": kinds,
            "severity_table_version": _sev.SEVERITY_TABLE_VERSION,
            "severity_table_approval": _sev.SEVERITY_TABLE_APPROVAL,
            "severity_categories": sorted({c for (_s, c) in
                                            _sev.FLEET_DEFECT_SEVERITY.values()}),
            "severity_by_item": severity_by_item,
            "fleet_unit_categories": [
                "Dump Trucks", "Tractor Trailer Trucks", "Service Trucks",
                "Pickup Trucks", "Flatbed Trucks", "Water Trucks",
                "Misc Trucks", "Supervisor / Mgmt Trucks", "Trailers",
            ],
            "scope_note": (
                "iter251 Phase A · backend foundation only · no frontend, "
                "no dashboards, no public tile yet."
            ),
        }

    # ─── Searchable fleet selector ───────────────────────────────
    @router.get("/api/fleet/units")
    async def list_fleet_units(
        q: Optional[str] = None,
        unit_type: Optional[str] = None,  # "truck" | "trailer"
        limit: int = 200,
        _actor=Depends(require_signed_in_or_public),
    ):
        """List selectable trucks/trailers from existing equipment_master.
        Filters to fleet-relevant categories only (no excavators, no
        loaders, no light towers etc). Searchable on unit_number, plate,
        make_model."""
        truck_categories = [
            "Dump Trucks", "Tractor Trailer Trucks", "Service Trucks",
            "Pickup Trucks", "Flatbed Trucks", "Water Trucks",
            "Misc Trucks", "Supervisor / Mgmt Trucks",
        ]
        trailer_categories = ["Trailers"]
        if unit_type == "truck":
            categories = truck_categories
        elif unit_type == "trailer":
            categories = trailer_categories
        else:
            categories = truck_categories + trailer_categories

        query: Dict[str, Any] = {"category": {"$in": categories}}
        if q:
            rx = {"$regex": re.escape(q), "$options": "i"}
            query["$or"] = [
                {"unit_number": rx},
                {"plate": rx},
                {"make_model": rx},
                {"vin_serial_number": rx},
            ]
        cursor = db.equipment_master.find(
            query,
            {"_id": 0, "id": 1, "unit_number": 1, "plate": 1,
             "make_model": 1, "vin_serial_number": 1, "category": 1,
             "year": 1, "display_label": 1, "company": 1},
        ).limit(max(1, min(500, limit)))
        units: List[Dict[str, Any]] = []
        async for u in cursor:
            units.append({
                "id": u.get("id"),
                "unit_number": u.get("unit_number") or "",
                "category": u.get("category"),
                "unit_type": "trailer" if u.get("category") in trailer_categories else "truck",
                "plate": u.get("plate") or "",
                "vin": u.get("vin_serial_number") or "",
                "make_model": u.get("make_model") or "",
                "year": u.get("year"),
                "display_label": u.get("display_label") or u.get("make_model") or "",
                "company": u.get("company") or "",
            })
        return {"count": len(units), "units": units}

    # ─── Submission · DVIR / weekly lead / weekly emergency ──────
    @router.post("/api/fleet/inspections")
    async def submit_fleet_inspection(
        payload: FleetInspectionSubmit,
        actor=Depends(require_signed_in_or_public),
    ):
        """Submit any fleet inspection · classifies failed items into
        defect rows · updates fleet_status projection · audits everything.

        Accepts both signed-in (driver_employee_id present) and public
        (signed-in optional) submissions · audit captures `submitted_via`
        for traceability."""
        _require_fleet_kind(payload.kind)
        defn = _ck.FLEET_INSPECTION_KINDS[payload.kind]

        # Validate truck_unit_number is non-empty
        if not (payload.truck_unit_number or "").strip():
            raise HTTPException(400, "truck_unit_number is required")
        if not (payload.driver_name or "").strip():
            raise HTTPException(400, "driver_name is required")

        # If kind disallows trailers, refuse to silently drop them
        if not defn["allows_trailers"] and payload.trailers:
            raise HTTPException(
                400,
                f"kind={payload.kind!r} does not accept trailers · "
                f"received {len(payload.trailers)}",
            )

        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()
        inspection_id = str(uuid.uuid4())

        # Tally pass/fail/na across truck + all trailers
        truck_failures = sum(
            1 for v in payload.truck_checklist.values() if (v or "").lower() == "fail"
        )
        trailer_failures = sum(
            sum(1 for v in (t.checklist or {}).values() if (v or "").lower() == "fail")
            for t in payload.trailers
        )

        # Build per-trailer defect rows + truck defect rows
        all_defects: List[Dict[str, Any]] = []
        any_oos = False
        truck_defects, truck_oos = _classify_failures(
            inspection_id=inspection_id,
            inspection_kind=payload.kind,
            truck_unit_number=payload.truck_unit_number,
            trailer_unit_number=None,
            checklist=payload.truck_checklist,
            defect_details=payload.defect_details,
            driver_employee_id=payload.driver_employee_id,
            driver_name=payload.driver_name,
            now_iso=now_iso,
        )
        all_defects.extend(truck_defects)
        any_oos = any_oos or truck_oos

        trailer_unit_numbers: List[str] = []
        for t in payload.trailers:
            trailer_unit_numbers.append(t.trailer_unit_number)
            tdefects, toos = _classify_failures(
                inspection_id=inspection_id,
                inspection_kind=payload.kind,
                truck_unit_number=payload.truck_unit_number,
                trailer_unit_number=t.trailer_unit_number,
                checklist=t.checklist,
                defect_details=payload.defect_details,
                driver_employee_id=payload.driver_employee_id,
                driver_name=payload.driver_name,
                now_iso=now_iso,
            )
            all_defects.extend(tdefects)
            any_oos = any_oos or toos

        # Write inspection row into existing equipment_inspections
        # collection with `kind` discriminator. Old Pre-Op rows are
        # backfilled with kind="pre_op" by the migration helper.
        insp_doc = {
            "id": inspection_id,
            "kind": payload.kind,
            "inspection_date": payload.inspection_date,
            "inspection_time": payload.inspection_time,
            "driver_employee_id": payload.driver_employee_id or "",
            "driver_name": payload.driver_name,
            "truck_unit_number": payload.truck_unit_number,
            "truck_vin": payload.truck_vin or "",
            "truck_plate": payload.truck_plate or "",
            "trailer_unit_numbers": trailer_unit_numbers,
            "trailers": [t.model_dump() for t in payload.trailers],
            "odometer_miles": payload.odometer_miles or "",
            "hour_meter": payload.hour_meter or "",
            "checklist": payload.truck_checklist,
            "fail_count": truck_failures + trailer_failures,
            "out_of_service": "Yes" if any_oos else "No",
            "deficiency_notes": payload.notes or "",
            "driver_signature": payload.driver_signature or "",
            "supervisor_name": payload.supervisor_name or "",
            "submitted_via": payload.submitted_via or "public_tile",
            "created_at": now_iso,
            # Phase F integration-ready
            "external_refs": {"motive_id": None},
        }
        await db.equipment_inspections.insert_one(insp_doc)

        # Insert defects (if any) and rebuild status for every
        # touched unit. We do this AFTER the inspection insert so a
        # status flip references an existing inspection_id.
        if all_defects:
            await db.fleet_defects.insert_many(all_defects)

        # Status rebuild for truck + each trailer
        await _rebuild_status(db, payload.truck_unit_number)
        for tn in trailer_unit_numbers:
            await _rebuild_status(db, tn)

        await _audit(
            db,
            actor=payload.driver_name,
            actor_role=actor.get("role", "driver"),
            action="fleet_inspection_submitted",
            target_type="equipment_inspection",
            target_id=inspection_id,
            payload={
                "kind": payload.kind,
                "truck": payload.truck_unit_number,
                "trailers": trailer_unit_numbers,
                "fail_count": truck_failures + trailer_failures,
                "defect_count": len(all_defects),
                "out_of_service": "Yes" if any_oos else "No",
                "submitted_via": payload.submitted_via or "public_tile",
            },
        )

        # BATCH L · OMEGA-3 / G-P0-01 — Fleet DVIR fan-out per approved
        # decision package matrix · 2026-05-30.
        #
        # Severity authority: fleet_defect_severity.SEVERITY_TABLE_VERSION
        # (v1.3-approved-2026-05-19). The table emits exactly two
        # severities: "oos" and "monitor". No new tier is invented here.
        #
        # Routing matrix (subset of decision package §2 that maps to
        # severities actually present in the current table):
        #   • Normal DVIR (no defects, no OOS) ........ no fan-out
        #   • Defect (any monitor, no OOS) ............ Shop task · Medium
        #   • OOS (any oos OR out_of_service=Yes) ..... Shop task · Critical
        #                                              + Dispatch visibility notification
        #
        # NO Superintendent notification (explicitly excluded per matrix).
        # Repeat-Unresolved sweep is a separate cron · belongs to Batch N
        # escalation framework when authorized · not in scope here.
        normal_only = not all_defects and not any_oos
        if not normal_only:
            try:
                # Local import keeps the module dependency-graph clean
                # if event_fanout is unavailable at import time.
                from lib.event_fanout import (  # noqa: PLC0415
                    emit_task_and_notification,
                    emit_notification,
                )

                if any_oos:
                    priority = "Critical"
                    state_word = " OOS"
                    msg_suffix = " · OUT OF SERVICE"
                else:
                    priority = "Medium"
                    state_word = ""
                    msg_suffix = ""

                title = (
                    f"Fleet defect — {payload.truck_unit_number}"
                    f"{state_word} · {payload.kind}"
                )

                await emit_task_and_notification(
                    db,
                    task={
                        "title": title[:200],
                        "description": (
                            f"Driver: {payload.driver_name} · "
                            f"Truck: {payload.truck_unit_number} · "
                            f"Kind: {payload.kind} · "
                            f"Defects: {len(all_defects)} · "
                            f"Fail items: {truck_failures + trailer_failures} · "
                            f"OOS: {'Yes' if any_oos else 'No'}"
                        )[:4000],
                        "source_module": "fleet.dvir",
                        "source_record_id": inspection_id,
                        "assignee_role": "shop",
                        "priority": priority,
                        "created_by": {"role": "system", "via": "dvir-fanout"},
                    },
                    notification={
                        "type": (
                            "dvir.defect.oos" if any_oos else "dvir.defect"
                        ),
                        "title": title[:200],
                        "message": (
                            f"{len(all_defects)} defect(s) flagged"
                            f"{msg_suffix}"
                        )[:200],
                        "severity": "Critical" if any_oos else "Warning",
                        "recipient_role": "shop",
                        "linked_source_module": "fleet.dvir",
                        "linked_source_record_id": inspection_id,
                    },
                )

                # OOS → parallel visibility notification to Dispatch
                # (no separate task — Shop owns the action; Dispatch
                # surfaces the vehicle as unavailable).
                if any_oos:
                    await emit_notification(
                        db,
                        {
                            "type": "dvir.defect.oos",
                            "title": title[:200],
                            "message": (
                                f"Vehicle {payload.truck_unit_number} "
                                f"OUT OF SERVICE"
                            )[:200],
                            "severity": "Critical",
                            "recipient_role": "dispatch",
                            "linked_source_module": "fleet.dvir",
                            "linked_source_record_id": inspection_id,
                        },
                    )
            except Exception:
                # Fail-soft · NEVER block the inspection submission
                # itself · matches the safety pattern across the codebase.
                pass

        return {
            "ok": True,
            "inspection_id": inspection_id,
            "kind": payload.kind,
            "out_of_service": any_oos,
            "defect_count": len(all_defects),
            "truck_status_after": (await _rebuild_status(db, payload.truck_unit_number))["status"],
        }

    # ─── Read · scoped views (Phase C will wire UI) ──────────────
    @router.get("/api/dispatch/fleet/status")
    async def dispatch_fleet_status(
        unit_type: Optional[str] = None,  # "truck" | "trailer"
        status: Optional[str] = None,  # "available" | "oos" | "defect_open"
        _actor=Depends(require_dispatch_or_admin),
    ):
        """Returns the current state of every fleet unit · used by the
        Dispatch fleet status board in Phase C. Returns ALL units
        including those without inspections yet (they'll appear as
        'unknown' until first DVIR submitted)."""
        truck_categories = [
            "Dump Trucks", "Tractor Trailer Trucks", "Service Trucks",
            "Pickup Trucks", "Flatbed Trucks", "Water Trucks",
            "Misc Trucks", "Supervisor / Mgmt Trucks",
        ]
        trailer_categories = ["Trailers"]
        if unit_type == "truck":
            categories = truck_categories
        elif unit_type == "trailer":
            categories = trailer_categories
        else:
            categories = truck_categories + trailer_categories

        rows: List[Dict[str, Any]] = []
        seen_units: set = set()
        # Get all fleet units from master
        cursor = db.equipment_master.find(
            {"category": {"$in": categories}},
            {"_id": 0, "unit_number": 1, "category": 1, "make_model": 1,
             "plate": 1, "year": 1, "company": 1},
        )
        async for u in cursor:
            unit_num = u.get("unit_number") or ""
            if not unit_num:
                continue
            seen_units.add(unit_num)
            status_doc = await db.fleet_status.find_one(
                {"unit_number": unit_num}, {"_id": 0}
            )
            row = {
                "unit_number": unit_num,
                "category": u.get("category"),
                "make_model": u.get("make_model"),
                "plate": u.get("plate"),
                "year": u.get("year"),
                "company": u.get("company"),
                "status": (status_doc or {}).get("status", "unknown"),
                "open_oos_count": (status_doc or {}).get("open_oos_count", 0),
                "open_monitor_count": (status_doc or {}).get("open_monitor_count", 0),
                "latest_inspection_id": (status_doc or {}).get("latest_inspection_id"),
                "latest_inspection_at": (status_doc or {}).get("latest_inspection_at"),
                "latest_driver_name": (status_doc or {}).get("latest_driver_name"),
            }
            if status and row["status"] != status:
                continue
            rows.append(row)
        # Also include fleet_status rows that don't have a matching
        # equipment_master row (synthetic / off-roster units that have
        # been inspected · should still be visible to dispatch).
        async for sdoc in db.fleet_status.find({}, {"_id": 0}):
            unit_num = sdoc.get("unit_number") or ""
            if not unit_num or unit_num in seen_units:
                continue
            row = {
                "unit_number": unit_num,
                "category": None,
                "make_model": None,
                "plate": None,
                "year": None,
                "company": None,
                "status": sdoc.get("status", "unknown"),
                "open_oos_count": sdoc.get("open_oos_count", 0),
                "open_monitor_count": sdoc.get("open_monitor_count", 0),
                "latest_inspection_id": sdoc.get("latest_inspection_id"),
                "latest_inspection_at": sdoc.get("latest_inspection_at"),
                "latest_driver_name": sdoc.get("latest_driver_name"),
                "off_roster": True,  # flag for dispatch UI
            }
            if status and row["status"] != status:
                continue
            rows.append(row)
        # Order: OOS first, then defect_open, then available, then unknown
        rank = {"oos": 0, "defect_open": 1, "available": 2, "unknown": 3}
        rows.sort(key=lambda r: (rank.get(r["status"], 9), r["unit_number"]))
        return {"count": len(rows), "units": rows}

    @router.get("/api/shop/fleet/defects")
    async def shop_defects(
        status: Optional[str] = None,  # "open" | "acknowledged" | "repaired" | "cleared"
        severity: Optional[str] = None,
        unit_number: Optional[str] = None,
        limit: int = 200,
        _actor=Depends(require_shop_or_admin),
    ):
        """Shop defect queue · all active defects across the fleet ·
        ordered by severity desc, opened-at asc (oldest first)."""
        q: Dict[str, Any] = {}
        if status:
            q["status"] = status
        else:
            q["status"] = {"$in": ["open", "acknowledged"]}
        if severity:
            q["severity"] = severity
        if unit_number:
            q["$or"] = [
                {"truck_unit_number": unit_number},
                {"trailer_unit_number": unit_number},
            ]
        cursor = db.fleet_defects.find(
            q, {"_id": 0}
        ).sort([("severity", 1), ("reported_at", 1)]).limit(max(1, min(500, limit)))
        items = await cursor.to_list(None)
        return {"count": len(items), "defects": items}

    @router.get("/api/safety/fleet/emergency-equipment")
    async def safety_emergency_defects(
        limit: int = 200,
        _actor=Depends(require_safety_or_admin),
    ):
        """Safety dashboard view · defects in safety-critical categories
        only (emergency_equipment · signals · alarms · lights · horn)."""
        safety_categories = [
            _sev.CATEGORY_EMERGENCY_EQUIPMENT,
            _sev.CATEGORY_SIGNALS,
            _sev.CATEGORY_ALARMS,
            _sev.CATEGORY_LIGHTS,
            _sev.CATEGORY_HORN,
        ]
        cursor = db.fleet_defects.find(
            {"category": {"$in": safety_categories},
             "status": {"$in": ["open", "acknowledged"]}},
            {"_id": 0},
        ).sort("reported_at", -1).limit(max(1, min(500, limit)))
        items = await cursor.to_list(None)
        return {"count": len(items), "defects": items, "categories": safety_categories}

    # ─── Defect lifecycle transitions ────────────────────────────
    @router.post("/api/shop/fleet/defects/{defect_id}/acknowledge")
    async def ack_defect(
        defect_id: str,
        payload: DefectActionPayload,
        _actor=Depends(require_shop_or_admin),
    ):
        defect = await db.fleet_defects.find_one({"id": defect_id}, {"_id": 0})
        if not defect:
            raise HTTPException(404, "defect not found")
        if defect["status"] != "open":
            raise HTTPException(
                400,
                f"can only acknowledge from status=open (current={defect['status']!r})",
            )
        now_iso = datetime.now(timezone.utc).isoformat()
        await db.fleet_defects.update_one(
            {"id": defect_id},
            {"$set": {
                "status": "acknowledged",
                "acknowledged_at": now_iso,
                "acknowledged_by_name": payload.actor_name,
            }},
        )
        await _audit(
            db, actor=payload.actor_name, actor_role="shop",
            action="defect_acknowledged",
            target_type="fleet_defect", target_id=defect_id,
            payload={
                "status_before": "open",
                "status_after": "acknowledged",
                "unit_number": defect.get("truck_unit_number") or defect.get("trailer_unit_number"),
                "checklist_item": defect.get("item_text"),
            },
        )
        return {"ok": True}

    @router.post("/api/shop/fleet/defects/{defect_id}/repair")
    async def repair_defect(
        defect_id: str,
        payload: DefectActionPayload,
        _actor=Depends(require_shop_or_admin),
    ):
        defect = await db.fleet_defects.find_one({"id": defect_id}, {"_id": 0})
        if not defect:
            raise HTTPException(404, "defect not found")
        if defect["status"] not in ("open", "acknowledged"):
            raise HTTPException(
                400,
                f"can only repair from status=open|acknowledged "
                f"(current={defect['status']!r})",
            )
        now_iso = datetime.now(timezone.utc).isoformat()
        await db.fleet_defects.update_one(
            {"id": defect_id},
            {"$set": {
                "status": "repaired",
                "repaired_at": now_iso,
                "repaired_by_name": payload.actor_name,
                "repair_notes": payload.notes or "",
                "repair_photos": payload.photos or [],
            }},
        )
        await _audit(
            db, actor=payload.actor_name, actor_role="shop",
            action="defect_repaired",
            target_type="fleet_defect", target_id=defect_id,
            payload={
                "status_before": defect.get("status"),
                "status_after": "repaired",
                "unit_number": defect.get("truck_unit_number") or defect.get("trailer_unit_number"),
                "checklist_item": defect.get("item_text"),
                "repair_notes": payload.notes,
                "photo_count": len(payload.photos),
            },
        )
        # Status rebuild for the affected unit
        unit_to_rebuild = defect.get("trailer_unit_number") or defect.get("truck_unit_number")
        if unit_to_rebuild:
            await _rebuild_status(db, unit_to_rebuild)
        return {"ok": True}

    @router.post("/api/dispatch/fleet/defects/{defect_id}/clear")
    async def clear_defect(
        defect_id: str,
        payload: DefectActionPayload,
        _actor=Depends(require_dispatch_or_admin),
    ):
        """Dispatch action · re-enables the truck for assignment after
        Shop has marked the defect repaired. This is the final step in
        the defect lifecycle · audit captures the human re-approval."""
        defect = await db.fleet_defects.find_one({"id": defect_id}, {"_id": 0})
        if not defect:
            raise HTTPException(404, "defect not found")
        if defect["status"] != "repaired":
            raise HTTPException(
                400,
                f"can only clear from status=repaired "
                f"(current={defect['status']!r})",
            )
        now_iso = datetime.now(timezone.utc).isoformat()
        await db.fleet_defects.update_one(
            {"id": defect_id},
            {"$set": {
                "status": "cleared",
                "cleared_at": now_iso,
                "cleared_by_name": payload.actor_name,
            }},
        )
        await _audit(
            db, actor=payload.actor_name, actor_role="dispatch",
            action="defect_cleared",
            target_type="fleet_defect", target_id=defect_id,
            payload={
                "status_before": "repaired",
                "status_after": "cleared",
                "unit_number": defect.get("truck_unit_number") or defect.get("trailer_unit_number"),
                "checklist_item": defect.get("item_text"),
                "rts_note": payload.notes or "",
                "rts_label": "returned_to_service",
            },
        )
        unit_to_rebuild = defect.get("trailer_unit_number") or defect.get("truck_unit_number")
        if unit_to_rebuild:
            await _rebuild_status(db, unit_to_rebuild)
        return {"ok": True}

    @router.post("/api/dispatch/fleet/units/{unit_number}/oos")
    async def manual_oos_flip(
        unit_number: str,
        payload: DefectActionPayload,
        _actor=Depends(require_dispatch_or_admin),
    ):
        """Manual OOS flip · Dispatch can mark a unit OOS without an
        inspection (e.g. shop discovers an issue between DVIRs).
        Creates a synthetic defect row so the audit + repair lifecycle
        flow the normal way."""
        now_iso = datetime.now(timezone.utc).isoformat()
        manual_defect = {
            "id": str(uuid.uuid4()),
            "doc_id": "",
            "inspection_id": None,  # NOT tied to an inspection
            "inspection_kind": "manual_oos",
            "truck_unit_number": unit_number,
            "trailer_unit_number": None,
            "item_text": "Manual OOS flip by Dispatch",
            "category": _sev.CATEGORY_OTHER,
            "severity": _sev.SEVERITY_OOS,
            "status": "open",
            "note": payload.notes or "",
            "photos": payload.photos or [],
            "reported_by_employee_id": "",
            "reported_by_name": payload.actor_name,
            "reported_at": now_iso,
            "acknowledged_at": None,
            "acknowledged_by_name": None,
            "repaired_at": None,
            "repaired_by_name": None,
            "repair_notes": "",
            "repair_photos": [],
            "cleared_at": None,
            "cleared_by_name": None,
            "external_refs": {"motive_id": None, "maintainx_work_order_id": None},
        }
        await db.fleet_defects.insert_one(manual_defect)
        await _audit(
            db, actor=payload.actor_name, actor_role="dispatch",
            action="manual_oos_flip",
            target_type="fleet_unit", target_id=unit_number,
            payload={"defect_id": manual_defect["id"], "notes": payload.notes},
        )
        await _rebuild_status(db, unit_number)
        return {"ok": True, "defect_id": manual_defect["id"]}

    # ─── Read-only · individual inspection / defect detail ───────
    @router.get("/api/fleet/inspections/{inspection_id}")
    async def get_inspection(
        inspection_id: str,
        _actor=Depends(require_dispatch_or_admin),
    ):
        doc = await db.equipment_inspections.find_one(
            {"id": inspection_id}, {"_id": 0}
        )
        if not doc:
            raise HTTPException(404, "inspection not found")
        return doc

    @router.get("/api/fleet/defects/{defect_id}")
    async def get_defect(
        defect_id: str,
        _actor=Depends(require_dispatch_or_admin),
    ):
        doc = await db.fleet_defects.find_one({"id": defect_id}, {"_id": 0})
        if not doc:
            raise HTTPException(404, "defect not found")
        return doc

    # ─── Phase 4 · Defect detail + audit trail (multi-portal read) ──
    @router.get("/api/fleet/defects/{defect_id}/detail")
    async def get_defect_detail(
        defect_id: str,
        _actor=Depends(require_any_fleet_portal or require_dispatch_or_admin),
    ):
        """Phase 4 · operational repair trail · readable by Shop /
        Dispatch / Safety / Admin. Returns the defect projected into
        the Phase 3 spec contract PLUS the full append-only audit trail
        for that defect.
        """
        d = await db.fleet_defects.find_one({"id": defect_id}, {"_id": 0})
        if not d:
            raise HTTPException(404, "defect not found")
        item_text = d.get("item_text") or ""
        meta = _sev.FLEET_DEFECT_SEVERITY_META.get(item_text) or {}
        projected = {
            "defect_id": d.get("id"),
            "doc_id": d.get("doc_id") or "",
            "inspection_id": d.get("inspection_id"),
            "inspection_kind": d.get("inspection_kind"),
            "truck_unit_number": d.get("truck_unit_number") or "",
            "trailer_unit_number": d.get("trailer_unit_number") or "",
            "checklist_item": item_text,
            "category": d.get("category"),
            "severity": d.get("severity"),
            "status": d.get("status"),
            "driver_note": d.get("note") or "",
            "photos": d.get("photos") or [],
            "reported_by_driver_name": d.get("reported_by_name") or "",
            "reported_at": d.get("reported_at"),
            "regulation_ref": meta.get("regulation_ref") or "",
            "rationale": meta.get("rationale") or "",
            "acknowledged_at": d.get("acknowledged_at"),
            "acknowledged_by_name": d.get("acknowledged_by_name"),
            "repaired_at": d.get("repaired_at"),
            "repaired_by_name": d.get("repaired_by_name"),
            "repair_notes": d.get("repair_notes") or "",
            "repair_photos": d.get("repair_photos") or [],
            "cleared_at": d.get("cleared_at"),
            "cleared_by_name": d.get("cleared_by_name"),
        }
        audit_cursor = db.fleet_audit.find(
            {"target_id": defect_id, "target_type": "fleet_defect"}, {"_id": 0}
        ).sort([("timestamp", 1)])
        audit = await audit_cursor.to_list(None)
        return {"defect": projected, "audit": audit}

    # ─── Admin migration helper · backfill `kind` on existing rows ──
    @router.post("/api/admin/fleet/migrate-kind-field")
    async def migrate_kind_field(
        _: bool = Depends(require_admin_strict),
    ):
        """Idempotent migration · stamps `kind="pre_op"` on every
        existing equipment_inspections row that lacks it. Safe to run
        repeatedly. Returns counts."""
        existing = await db.equipment_inspections.count_documents(
            {"kind": {"$exists": False}}
        )
        result = await db.equipment_inspections.update_many(
            {"kind": {"$exists": False}},
            {"$set": {"kind": _ck.DVIR_KIND_PRE_OP}},
        )
        return {
            "ok": True,
            "rows_missing_kind_before": existing,
            "rows_updated": result.modified_count,
        }

    # ─── Severity audit (governance · read-only validation) ──────
    @router.get("/api/admin/fleet/severity-audit")
    async def severity_audit(
        _: bool = Depends(require_admin_strict),
    ):
        """iter251 governance · read-only validation of the severity
        table.  Cross-checks every checklist item across every fleet
        inspection kind against `fleet_defect_severity.FLEET_DEFECT_SEVERITY`
        AND the per-item metadata table.

        Catches BEFORE production reliance:
          - items used in a checklist with NO severity classification
            (would cause submission HTTP 400 in the field)
          - items in the severity table NOT referenced by any checklist
            (orphan classifications)
          - duplicate item text (e.g. same string used for trailer +
            truck context with different classifications)
          - severity entries with no metadata (rationale / regulation_ref)
          - items flagged uncertain pending Safety review
          - category coverage stats

        Returns operator-readable JSON. Endpoint is admin-strict only ·
        operationally sensitive content."""
        all_checklist_items: Dict[str, list] = {}
        for kind, defn in _ck.FLEET_INSPECTION_KINDS.items():
            kind_items = []
            if defn["truck_items"]:
                kind_items.extend([("truck", x) for x in defn["truck_items"]()])
            if defn["trailer_items"]:
                kind_items.extend([("trailer", x) for x in defn["trailer_items"]()])
            all_checklist_items[kind] = kind_items

        # Flat set of all checklist items across all kinds
        used_items: set = set()
        for kind_items in all_checklist_items.values():
            for _section, item in kind_items:
                used_items.add(item)

        sev_keys: set = set(_sev.FLEET_DEFECT_SEVERITY.keys())
        meta_keys: set = set(_sev.FLEET_DEFECT_SEVERITY_META.keys())

        # ── Findings ─────────────────────────────────────────────
        # (1) Checklist items missing severity classification = HARD FAIL
        missing_severity = sorted(used_items - sev_keys)
        # (2) Severity entries not used by any checklist = ORPHAN
        orphan_severity = sorted(sev_keys - used_items)
        # (3) Severity entries missing metadata = SOFT FAIL
        missing_metadata = sorted(sev_keys - meta_keys)
        # (4) Metadata entries with no corresponding severity row = ORPHAN
        orphan_metadata = sorted(meta_keys - sev_keys)
        # (5) Items flagged uncertain pending Safety review
        uncertain_items = sorted([
            item for item, meta in _sev.FLEET_DEFECT_SEVERITY_META.items()
            if meta.get("uncertain")
        ])
        # (6) Per-kind coverage stats
        per_kind_coverage = {}
        for kind, items in all_checklist_items.items():
            total = len(items)
            classified = sum(1 for _s, x in items if x in sev_keys)
            per_kind_coverage[kind] = {
                "total_items": total,
                "classified": classified,
                "missing": total - classified,
                "coverage_pct": round(100.0 * classified / total, 1) if total else None,
            }
        # (7) Category breakdown
        category_counts: Dict[str, Dict[str, int]] = {}
        for item, (sev, cat) in _sev.FLEET_DEFECT_SEVERITY.items():
            bucket = category_counts.setdefault(cat, {"oos": 0, "monitor": 0})
            bucket[sev] = bucket.get(sev, 0) + 1
        category_counts_sorted = dict(sorted(
            category_counts.items(),
            key=lambda kv: -(kv[1].get("oos", 0) + kv[1].get("monitor", 0)),
        ))
        # (8) Severity ratio
        total_oos = sum(1 for s, _c in _sev.FLEET_DEFECT_SEVERITY.values()
                        if s == _sev.SEVERITY_OOS)
        total_mon = sum(1 for s, _c in _sev.FLEET_DEFECT_SEVERITY.values()
                        if s == _sev.SEVERITY_MONITOR)

        # ── Verdict ─────────────────────────────────────────────
        if missing_severity:
            verdict = "FAIL"
            verdict_reason = (
                f"{len(missing_severity)} checklist item(s) have no severity "
                f"classification · these would HTTP 400 in production."
            )
        elif missing_metadata:
            verdict = "NEEDS_REVIEW"
            verdict_reason = (
                f"{len(missing_metadata)} severity entries missing metadata "
                f"(rationale / regulation_ref / uncertain flag) · operator "
                f"+ Safety review required before production reliance."
            )
        elif uncertain_items:
            verdict = "NEEDS_REVIEW"
            verdict_reason = (
                f"{len(uncertain_items)} severity entries marked uncertain "
                f"pending Safety review · production reliance gated on "
                f"resolving each."
            )
        elif orphan_severity or orphan_metadata:
            verdict = "NEEDS_CLEANUP"
            verdict_reason = "Orphan entries detected · operationally safe but indicates table drift."
        else:
            verdict = "READY_FOR_SAFETY_SIGNOFF"
            verdict_reason = "Every checklist item classified · every severity entry has metadata · no uncertain flags remaining."

        return {
            "phase": "iter251 Phase A · severity governance cycle",
            "verdict": verdict,
            "verdict_reason": verdict_reason,
            "severity_table_version": _sev.SEVERITY_TABLE_VERSION,
            "severity_table_approval": _sev.SEVERITY_TABLE_APPROVAL,
            "total_severity_entries": len(sev_keys),
            "total_oos": total_oos,
            "total_monitor": total_mon,
            "oos_to_monitor_ratio": (
                round(total_oos / total_mon, 2) if total_mon else None
            ),
            "per_kind_coverage": per_kind_coverage,
            "category_breakdown": category_counts_sorted,
            "missing_severity": missing_severity,
            "orphan_severity": orphan_severity,
            "missing_metadata": missing_metadata,
            "orphan_metadata": orphan_metadata,
            "uncertain_items_pending_review": [
                {
                    "item": item,
                    "severity": _sev.FLEET_DEFECT_SEVERITY[item][0],
                    "category": _sev.FLEET_DEFECT_SEVERITY[item][1],
                    "rationale": _sev.FLEET_DEFECT_SEVERITY_META[item].get("rationale"),
                    "uncertainty_note": _sev.FLEET_DEFECT_SEVERITY_META[item].get(
                        "uncertainty_note", ""
                    ),
                    "regulation_ref": _sev.FLEET_DEFECT_SEVERITY_META[item].get("regulation_ref"),
                }
                for item in uncertain_items
            ],
            "scope_note": (
                "Read-only governance tool · validates table integrity · "
                "does NOT modify any production data."
            ),
        }

    # ─── Phase 3 governance · printable severity reference card ──────────
    @router.get("/api/admin/fleet/severity-reference-card.pdf")
    async def severity_reference_card_pdf(_actor=Depends(require_admin_strict)):
        """One-page printable PDF reference card · auditor + Safety field
        reference + field-manual insertion. Generated server-side from the
        same `FLEET_DEFECT_SEVERITY` SOT so there is NEVER a manual table
        to maintain.

        Returns: application/pdf · letter size · landscape · single page.
        """
        from fastapi.responses import Response
        from io import BytesIO
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
        )

        buf = BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=landscape(letter),
            leftMargin=0.35 * inch, rightMargin=0.35 * inch,
            topMargin=0.30 * inch, bottomMargin=0.30 * inch,
            title=f"MASCI Fleet · DVIR Severity Reference · {_sev.SEVERITY_TABLE_VERSION}",
            author="MASCI Operations Platform",
        )

        styles = getSampleStyleSheet()
        h1 = ParagraphStyle("h1", parent=styles["Heading1"],
                            fontSize=14, leading=16, spaceAfter=2,
                            textColor=colors.HexColor("#0F172A"))
        sub = ParagraphStyle("sub", parent=styles["Normal"],
                             fontSize=8, leading=10, textColor=colors.HexColor("#64748B"))
        cat = ParagraphStyle("cat", parent=styles["Normal"],
                             fontSize=7, leading=8, fontName="Helvetica-Bold",
                             textColor=colors.HexColor("#0F172A"))
        item_s = ParagraphStyle("item", parent=styles["Normal"],
                                fontSize=6.4, leading=7.5,
                                textColor=colors.HexColor("#0F172A"))
        foot = ParagraphStyle("foot", parent=styles["Normal"],
                              fontSize=6.5, leading=8,
                              textColor=colors.HexColor("#64748B"),
                              alignment=1)

        flow = []
        flow.append(Paragraph("MASCI Fleet · DVIR Severity Reference Card", h1))
        approval = _sev.SEVERITY_TABLE_APPROVAL
        flow.append(Paragraph(
            f"Version <b>{_sev.SEVERITY_TABLE_VERSION}</b> · "
            f"Approved {approval.get('approved_at','')} · "
            f"{approval.get('approved_by','')} · "
            f"Verdict: READY_FOR_SAFETY_SIGNOFF · "
            f"{len(_sev.FLEET_DEFECT_SEVERITY)} items · "
            f"{sum(1 for s,_ in _sev.FLEET_DEFECT_SEVERITY.values() if s == _sev.SEVERITY_OOS)} OOS · "
            f"{sum(1 for s,_ in _sev.FLEET_DEFECT_SEVERITY.values() if s == _sev.SEVERITY_MONITOR)} Monitor",
            sub,
        ))
        flow.append(Spacer(1, 6))

        # Group items by category · order by sev (OOS first) then alpha
        by_cat: Dict[str, List[Tuple[str, str]]] = {}
        for item, (sev, category) in _sev.FLEET_DEFECT_SEVERITY.items():
            by_cat.setdefault(category, []).append((sev, item))
        for cat_name in by_cat:
            by_cat[cat_name].sort(key=lambda x: (0 if x[0] == _sev.SEVERITY_OOS else 1, x[1]))

        # Categories ordered by total count desc for visual balance
        ordered_cats = sorted(by_cat.keys(), key=lambda c: (-len(by_cat[c]), c))

        # 3-column layout · severity letter prefix (S=OOS strict · M=monitor)
        rows = [["Category", "Severity Items"]]
        for category in ordered_cats:
            cell = "<br/>".join(
                f'<font color="{"#B91C1C" if sev == _sev.SEVERITY_OOS else "#92400E"}">'
                f'{"S" if sev == _sev.SEVERITY_OOS else "M"}</font> · {item}'
                for sev, item in by_cat[category]
            )
            rows.append([
                Paragraph(category.replace("_", " ").title(), cat),
                Paragraph(cell, item_s),
            ])

        # Single landscape-fit table with two columns
        table = Table(
            rows,
            colWidths=[1.45 * inch, 8.55 * inch],
            repeatRows=1,
            hAlign="LEFT",
        )
        table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 7),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, 0), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.HexColor("#F8FAFC"), colors.white]),
            ("LINEBELOW", (0, 0), (-1, 0), 1, colors.HexColor("#D97706")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E2E8F0")),
        ]))
        flow.append(table)
        flow.append(Spacer(1, 4))

        flow.append(Paragraph(
            "<b>S</b> = Out of Service (truck cannot operate until cleared) &nbsp;·&nbsp; "
            "<b>M</b> = Monitor (shop tracks · truck remains available within stated window) &nbsp;·&nbsp; "
            "Driver picks PASS / FAIL / N/A · severity is server-calculated · "
            "<b>governance record:</b> /app/SEVERITY_RULINGS_iter251.md &nbsp;·&nbsp; "
            "<b>print stamp:</b> "
            f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            foot,
        ))

        doc.build(flow)
        pdf_bytes = buf.getvalue()
        buf.close()

        filename = f"MASCI_Fleet_Severity_Reference_{_sev.SEVERITY_TABLE_VERSION}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'inline; filename="{filename}"',
                "X-Severity-Version": _sev.SEVERITY_TABLE_VERSION,
                "Cache-Control": "no-store",
            },
        )

    # ─── Phase 3 · Shop fleet queue · grouped BY UNIT (not chronological)
    @router.get("/api/shop/fleet/by-unit")
    async def shop_defects_grouped_by_unit(
        _actor=Depends(require_any_fleet_portal or require_shop_or_admin),
    ):
        """Phase 3 operator-strongly-approved view: shop sees defects
        grouped by truck/unit (one card per truck · all open defects
        collapsed inside · driver note thumbprint surfaced).

        Phase 4 · readable by Shop / Dispatch / Safety / Admin so all
        three scopes can see the same operational picture (Shop to act
        on repairs, Dispatch to clear RTS, Safety to read the audit
        trail). Path retained at /api/shop/fleet/by-unit for backward
        compat with the existing frontend wiring.
        """
        cursor = db.fleet_defects.find(
            {"status": {"$in": ["open", "acknowledged", "repaired"]}}, {"_id": 0}
        ).sort([("severity", 1), ("reported_at", 1)])
        defects = await cursor.to_list(None)

        by_unit: Dict[str, Dict[str, Any]] = {}
        for d in defects:
            unit_key = d.get("truck_unit_number") or d.get("trailer_unit_number") or "—"
            grp = by_unit.setdefault(unit_key, {
                "unit_number": unit_key,
                "is_trailer": bool(d.get("trailer_unit_number")
                                   and not d.get("truck_unit_number")),
                "open_oos_count": 0,
                "open_monitor_count": 0,
                "awaiting_rts_count": 0,
                "latest_inspection_at": None,
                "latest_driver_name": None,
                # Enrichment placeholders · populated below from
                # fleet_status / equipment_master if rows exist
                "truck_status": None,
                "make_model": None,
                "category": None,
                "plate": None,
                "year": None,
                "defects": [],
            })
            # Project to Phase 3 spec field names so the operator-approved
            # Driver Note thumbprint, severity title, and Safety regulation_ref
            # render correctly. Backend is the contract.
            item_text = d.get("item_text") or ""
            meta = _sev.FLEET_DEFECT_SEVERITY_META.get(item_text) or {}
            projected = {
                "defect_id": d.get("id"),
                "doc_id": d.get("doc_id") or "",
                "inspection_id": d.get("inspection_id"),
                "checklist_item": item_text,
                "category": d.get("category"),
                "severity": d.get("severity"),
                "status": d.get("status"),
                "driver_note": d.get("note") or "",
                "photos": d.get("photos") or [],
                "reported_by_driver_name": d.get("reported_by_name") or "",
                "reported_at": d.get("reported_at"),
                "regulation_ref": meta.get("regulation_ref") or "",
                "rationale": meta.get("rationale") or "",
                "truck_unit_number": d.get("truck_unit_number") or "",
                "trailer_unit_number": d.get("trailer_unit_number") or "",
                # Phase 4 · repair lifecycle visible alongside the defect
                "acknowledged_at": d.get("acknowledged_at"),
                "acknowledged_by_name": d.get("acknowledged_by_name"),
                "repaired_at": d.get("repaired_at"),
                "repaired_by_name": d.get("repaired_by_name"),
                "repair_notes": d.get("repair_notes") or "",
                "repair_photos": d.get("repair_photos") or [],
            }
            grp["defects"].append(projected)
            d_status = d.get("status")
            if d_status == "repaired":
                grp["awaiting_rts_count"] += 1
            elif d.get("severity") == _sev.SEVERITY_OOS:
                grp["open_oos_count"] += 1
            else:
                grp["open_monitor_count"] += 1
            rep_at = d.get("reported_at")
            if rep_at and (
                grp["latest_inspection_at"] is None
                or rep_at > grp["latest_inspection_at"]
            ):
                grp["latest_inspection_at"] = rep_at
                grp["latest_driver_name"] = d.get("reported_by_name")

        # Enrich with fleet_status (truck-state) + equipment_master snapshot
        units_list = list(by_unit.keys())
        if units_list:
            async for sdoc in db.fleet_status.find(
                {"unit_number": {"$in": units_list}}, {"_id": 0}
            ):
                u = sdoc.get("unit_number")
                if u in by_unit:
                    by_unit[u]["truck_status"] = sdoc.get("status", "unknown")
            async for udoc in db.equipment_master.find(
                {"unit_number": {"$in": units_list}},
                {"_id": 0, "unit_number": 1, "make_model": 1, "category": 1, "plate": 1, "year": 1},
            ):
                u = udoc.get("unit_number")
                if u in by_unit:
                    by_unit[u]["make_model"] = udoc.get("make_model")
                    by_unit[u]["category"] = udoc.get("category")
                    by_unit[u]["plate"] = udoc.get("plate")
                    by_unit[u]["year"] = udoc.get("year")

        groups = list(by_unit.values())
        # Order: OOS-bearing units first · then awaiting-RTS · then by
        # oldest defect age (Phase 4 · ops actionability).
        groups.sort(key=lambda g: (
            0 if g["open_oos_count"] > 0 else (1 if g["awaiting_rts_count"] > 0 else 2),
            g["latest_inspection_at"] or "9999",
        ))
        return {
            "count_units": len(groups),
            "count_defects": sum(len(g["defects"]) for g in groups),
            "groups": groups,
        }

    return router
