"""TRACK 16.06 · Transportation Experience Layer · aggregation endpoints.

Backend endpoints needed by the new Transportation Compliance Center UI.
Everything here is read-only and reuses the Phase 1 + Phase 2 collections
already in place. No new identity, no new storage, no new audit system.

Routes:
* GET /api/admin/transportation/dashboard
* GET /api/admin/transportation/documents/queue
* GET /api/admin/transportation/inspections/queue
* GET /api/admin/transportation/audit-timeline
* GET /api/admin/transportation/carriers/{id}/workspace
* GET /api/admin/transportation/persons/{id}/workspace
* GET /api/admin/transportation/trucks/{id}/workspace
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from lib.transport_phase2 import TENANT, INSPECTION_DISCLAIMER

logger = logging.getLogger(__name__)


def _project(d: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not d:
        return None
    return {k: v for k, v in d.items() if k != "_id"}


async def _count_states(db, target_type: str) -> Dict[str, int]:
    cur = db.transport_eligibility_state.find(
        {"tenant": TENANT, "target_type": target_type})
    out: Dict[str, int] = {}
    for r in await cur.to_list(10000):
        s = r.get("state") or "unknown"
        out[s] = out.get(s, 0) + 1
    return out


async def _compute_compliance_score(buckets_per_target: Dict[str, Dict[str, int]]
                                    ) -> int:
    """Operator-friendly score · 0-100. Counts eligible vs total across
    drivers + trucks + carriers. Returns 0 when no entities exist —
    operators read an empty fleet as "nothing yet" rather than "100% OK"."""
    total = eligible = 0
    for buckets in buckets_per_target.values():
        for state, n in buckets.items():
            total += n
            if state == "eligible":
                eligible += n
    if total == 0:
        return 0
    return int(round((eligible / total) * 100))


def register_transportation_experience_routes(
    app, db, require_admin_dep: Callable
) -> APIRouter:
    router = APIRouter(prefix="/api", tags=["transportation-experience"])

    # ─────────────────────── Dashboard ───────────────────────
    @router.get("/admin/transportation/dashboard")
    async def dashboard(_: Any = Depends(require_admin_dep)):
        carrier_buckets = await _count_states(db, "carrier")
        person_buckets = await _count_states(db, "person")
        truck_buckets = await _count_states(db, "truck")
        score = await _compute_compliance_score({
            "carrier": carrier_buckets, "person": person_buckets,
            "truck": truck_buckets,
        })

        # Active rate.
        active_rate = await db.transport_rate_schedules.find_one(
            {"tenant": TENANT, "status": "active"})

        # Pending review counts (status field on the source rows, not eligibility).
        pending_drivers = await db.transport_persons.count_documents(
            {"tenant": TENANT, "status": "pending_review"})
        pending_carriers = await db.carriers.count_documents(
            {"tenant": TENANT, "status": "pending_review"})

        # Trucks pending inspection = leased trucks with NO inspection or
        # inspection.result != "ready".
        trucks = await db.transport_trucks.find(
            {"tenant": TENANT, "ownership": {"$ne": "masci_owned"}}
        ).to_list(2000)
        truck_ids = [t["id"] for t in trucks]
        insp_rows = await db.transport_truck_inspections.find(
            {"tenant": TENANT, "transport_truck_id": {"$in": truck_ids}}
        ).to_list(10000)
        latest: Dict[str, Dict[str, Any]] = {}
        for r in insp_rows:
            tid = r.get("transport_truck_id")
            cur_ts = latest.get(tid, {}).get("inspected_at", "")
            if (r.get("inspected_at") or "") > cur_ts:
                latest[tid] = r
        pending_inspection = 0
        for t in trucks:
            r = latest.get(t["id"])
            if not r or r.get("result") != "ready":
                pending_inspection += 1

        # Document queue counts.
        carrier_docs_pending = await db.carrier_documents.count_documents(
            {"tenant": TENANT, "status": "pending_review"})
        driver_docs_pending = await db.driver_documents.count_documents(
            {"tenant": TENANT, "status": "pending_review"})
        needs_corr = (
            await db.carrier_documents.count_documents(
                {"tenant": TENANT, "status": "needs_correction"})
            + await db.driver_documents.count_documents(
                {"tenant": TENANT, "status": "needs_correction"})
        )

        # Expiring docs (next 30 days) + overdue.
        now_iso = datetime.now(timezone.utc).isoformat()
        soon_iso = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        expiring = (
            await db.carrier_documents.count_documents({
                "tenant": TENANT, "expires_at": {"$gte": now_iso, "$lt": soon_iso},
                "status": {"$in": ["accepted", "pending_review"]},
            })
            + await db.driver_documents.count_documents({
                "tenant": TENANT, "expires_at": {"$gte": now_iso, "$lt": soon_iso},
                "status": {"$in": ["accepted", "pending_review"]},
            })
        )

        # Inspections due in 30 days.
        insp_due_30 = 0
        for r in latest.values():
            exp = r.get("expires_at")
            if exp and exp >= now_iso and exp < soon_iso:
                insp_due_30 += 1

        return {
            "compliance_score": score,
            "tiles": {
                "eligible_drivers": person_buckets.get("eligible", 0),
                "eligible_trucks": truck_buckets.get("eligible", 0),
                "eligible_carriers": carrier_buckets.get("eligible", 0),
                "drivers_pending_review": pending_drivers,
                "carriers_pending_review": pending_carriers,
                "trucks_pending_inspection": pending_inspection,
                "documents_awaiting_review": carrier_docs_pending + driver_docs_pending,
                "expiring_documents_30d": expiring,
                "annual_inspections_due_30d": insp_due_30,
                "pending_corrections": needs_corr,
            },
            "active_rate": _project(active_rate),
            "buckets": {
                "carrier": carrier_buckets,
                "person": person_buckets,
                "truck": truck_buckets,
            },
            "disclaimer": INSPECTION_DISCLAIMER,
        }

    # ─────────────────────── Document Queue ───────────────────────
    @router.get("/admin/transportation/documents/queue")
    async def documents_queue(
        status: Optional[str] = Query(None),
        scope: Optional[str] = Query("all"),  # all|carrier|driver
        carrier_id: Optional[str] = Query(None),
        person_id: Optional[str] = Query(None),
        expiring_within_days: Optional[int] = Query(None, ge=0, le=365),
        limit: int = Query(300, ge=1, le=1000),
        _: Any = Depends(require_admin_dep),
    ):
        out: List[Dict[str, Any]] = []
        q: Dict[str, Any] = {"tenant": TENANT}
        if status:
            q["status"] = status
        if expiring_within_days is not None:
            now_iso = datetime.now(timezone.utc).isoformat()
            soon_iso = (datetime.now(timezone.utc)
                        + timedelta(days=expiring_within_days)).isoformat()
            q["expires_at"] = {"$gte": now_iso, "$lt": soon_iso}

        if scope in ("all", "carrier"):
            q_c = {**q}
            if carrier_id:
                q_c["carrier_id"] = carrier_id
            cur = db.carrier_documents.find(q_c).sort("uploaded_at", -1).limit(limit)
            for d in await cur.to_list(limit):
                p = _project(d)
                if p:
                    p["scope"] = "carrier"
                    out.append(p)
        if scope in ("all", "driver"):
            q_d = {**q}
            if person_id:
                q_d["transport_person_id"] = person_id
            cur = db.driver_documents.find(q_d).sort("uploaded_at", -1).limit(limit)
            for d in await cur.to_list(limit):
                p = _project(d)
                if p:
                    p["scope"] = "driver"
                    out.append(p)
        # Sort combined by uploaded_at desc.
        out.sort(key=lambda r: r.get("uploaded_at") or "", reverse=True)
        return {"count": len(out), "items": out[:limit]}

    # ─────────────────────── Inspection Queue ───────────────────────
    @router.get("/admin/transportation/inspections/queue")
    async def inspections_queue(
        trigger: Optional[str] = Query(None),
        result: Optional[str] = Query(None),
        due_within_days: Optional[int] = Query(None, ge=0, le=365),
        overdue: Optional[bool] = Query(None),
        limit: int = Query(300, ge=1, le=1000),
        _: Any = Depends(require_admin_dep),
    ):
        q: Dict[str, Any] = {"tenant": TENANT}
        if trigger:
            q["trigger"] = trigger
        if result:
            q["result"] = result
        now_iso = datetime.now(timezone.utc).isoformat()
        if due_within_days is not None:
            soon_iso = (datetime.now(timezone.utc)
                        + timedelta(days=due_within_days)).isoformat()
            q["expires_at"] = {"$gte": now_iso, "$lt": soon_iso}
        if overdue is True:
            q.setdefault("expires_at", {})
            q["expires_at"] = {"$lt": now_iso}
        cur = db.transport_truck_inspections.find(q).sort("inspected_at", -1).limit(limit)
        rows = [_project(d) for d in await cur.to_list(limit)]
        return {"count": len(rows), "items": rows,
                "disclaimer": INSPECTION_DISCLAIMER}

    # ─────────────────────── Audit Timeline ───────────────────────
    @router.get("/admin/transportation/audit-timeline")
    async def audit_timeline(
        entity_type: Optional[str] = Query(None),
        entity_id: Optional[str] = Query(None),
        kind_prefix: Optional[str] = Query("transport_"),
        limit: int = Query(200, ge=1, le=1000),
        _: Any = Depends(require_admin_dep),
    ):
        q: Dict[str, Any] = {"tenant": TENANT}
        if kind_prefix:
            q["kind"] = {"$regex": f"^{kind_prefix}", "$options": "i"}
        if entity_type:
            q["entity_type"] = entity_type
        if entity_id:
            q["entity_id"] = entity_id
        cur = db.audit_events.find(q).sort("ts", -1).limit(limit)
        rows = [_project(d) for d in await cur.to_list(limit)]
        return {"count": len(rows), "items": rows}

    # ─────────────────────── Per-entity Compliance Timeline ───────────────────────
    @router.get("/admin/transportation/timeline/{entity_type}/{entity_id}")
    async def entity_timeline(
        entity_type: str, entity_id: str,
        limit: int = Query(200, ge=1, le=1000),
        _: Any = Depends(require_admin_dep),
    ):
        """TRACK 16.07 · Per-entity Compliance Timeline.

        Returns the full audit lineage for one carrier, driver, or truck
        — ordered ASC so the operator reads creation → current state."""
        if entity_type not in ("carrier", "person", "truck"):
            raise HTTPException(422, "entity_type must be carrier|person|truck")
        # Existence check — match the 404 contract enforced by the
        # carrier/driver/truck workspace endpoints in this same file.
        collection_for_type = {
            "carrier": db.carriers,
            "person": db.transport_persons,
            "truck": db.transport_trucks,
        }[entity_type]
        entity = await collection_for_type.find_one(
            {"id": entity_id, "tenant": TENANT})
        if not entity:
            raise HTTPException(404, f"{entity_type} not found")
        # Collect direct audit rows for this entity.
        cur = db.audit_events.find({
            "tenant": TENANT, "entity_id": entity_id,
        }).sort("ts", 1).limit(limit)
        direct = [_project(d) for d in await cur.to_list(limit)]

        # Plus indirect rows (e.g., documents/inspections/packet referencing
        # this entity — we widen the timeline so the operator sees the
        # whole onboarding story without context-switching).
        related: List[Dict[str, Any]] = []
        if entity_type == "carrier":
            # Documents + packet + inspections-on-trucks-of-this-carrier.
            doc_ids = [d["id"] async for d in db.carrier_documents.find(
                {"tenant": TENANT, "carrier_id": entity_id}, {"id": 1})]
            pkt_ids = [d["id"] async for d in db.transport_packet_submissions.find(
                {"tenant": TENANT, "carrier_id": entity_id}, {"id": 1})]
            truck_ids = [d["id"] async for d in db.transport_trucks.find(
                {"tenant": TENANT, "carrier_id": entity_id}, {"id": 1})]
            insp_ids = []
            if truck_ids:
                insp_ids = [d["id"] async for d in db.transport_truck_inspections.find(
                    {"tenant": TENANT, "transport_truck_id": {"$in": truck_ids}}, {"id": 1})]
            all_ids = list(set(doc_ids + pkt_ids + insp_ids))
            if all_ids:
                cur2 = db.audit_events.find({
                    "tenant": TENANT, "entity_id": {"$in": all_ids}
                }).sort("ts", 1).limit(limit)
                related = [_project(d) for d in await cur2.to_list(limit)]
        elif entity_type == "person":
            doc_ids = [d["id"] async for d in db.driver_documents.find(
                {"tenant": TENANT, "transport_person_id": entity_id}, {"id": 1})]
            if doc_ids:
                cur2 = db.audit_events.find({
                    "tenant": TENANT, "entity_id": {"$in": doc_ids}
                }).sort("ts", 1).limit(limit)
                related = [_project(d) for d in await cur2.to_list(limit)]
        elif entity_type == "truck":
            insp_ids = [d["id"] async for d in db.transport_truck_inspections.find(
                {"tenant": TENANT, "transport_truck_id": entity_id}, {"id": 1})]
            if insp_ids:
                cur2 = db.audit_events.find({
                    "tenant": TENANT, "entity_id": {"$in": insp_ids}
                }).sort("ts", 1).limit(limit)
                related = [_project(d) for d in await cur2.to_list(limit)]
        combined = direct + related
        combined.sort(key=lambda r: r.get("ts") or "")
        return {"count": len(combined), "items": combined}

    # ─────────────────────── Workspace aggregators ───────────────────────
    @router.get("/admin/transportation/carriers/{cid}/workspace")
    async def carrier_workspace(cid: str, _: Any = Depends(require_admin_dep)):
        carrier = await db.carriers.find_one({"id": cid, "tenant": TENANT})
        if not carrier:
            raise HTTPException(404, "Carrier not found")
        persons = await db.transport_persons.find(
            {"tenant": TENANT, "carrier_id": cid}).to_list(500)
        trucks = await db.transport_trucks.find(
            {"tenant": TENANT, "carrier_id": cid}).to_list(500)
        docs = await db.carrier_documents.find(
            {"tenant": TENANT, "carrier_id": cid}).sort("uploaded_at", -1).to_list(500)
        packet = await db.transport_packet_submissions.find_one(
            {"tenant": TENANT, "carrier_id": cid}, sort=[("created_at", -1)])
        rate = await db.transport_rate_schedules.find_one(
            {"tenant": TENANT, "status": "active"})
        elig = await db.transport_eligibility_state.find_one(
            {"tenant": TENANT, "target_type": "carrier", "target_id": cid})
        return {
            "carrier": _project(carrier),
            "drivers": [_project(p) for p in persons],
            "trucks": [_project(t) for t in trucks],
            "documents": [_project(d) for d in docs],
            "packet": _project(packet),
            "active_rate": _project(rate),
            "eligibility": _project(elig),
            "disclaimer": INSPECTION_DISCLAIMER,
        }

    @router.get("/admin/transportation/persons/{pid}/workspace")
    async def driver_workspace(pid: str, _: Any = Depends(require_admin_dep)):
        person = await db.transport_persons.find_one({"id": pid, "tenant": TENANT})
        if not person:
            raise HTTPException(404, "Driver not found")
        carrier = None
        if person.get("carrier_id"):
            carrier = await db.carriers.find_one(
                {"id": person["carrier_id"], "tenant": TENANT})
        docs = await db.driver_documents.find(
            {"tenant": TENANT, "transport_person_id": pid}
        ).sort("uploaded_at", -1).to_list(500)
        elig = await db.transport_eligibility_state.find_one(
            {"tenant": TENANT, "target_type": "person", "target_id": pid})
        # HR linkage hint (read-only).
        hr_link = None
        hr_projection = None
        if person.get("kind") == "masci_employee" and person.get("employee_id"):
            try:
                hr = await db.employees.find_one(
                    {"$or": [{"employee_id": person["employee_id"]},
                             {"id": person["employee_id"]}],
                     "deleted_at": None},
                    {"_id": 0},
                )
                if hr:
                    # Minimal identity surface for the panel.
                    hr_link = {
                        "id": hr.get("id"),
                        "employee_id": hr.get("employee_id"),
                        "name": hr.get("name"),
                        "first_name": hr.get("first_name") or hr.get("legal_first_name"),
                        "last_name": hr.get("last_name") or hr.get("legal_last_name"),
                        "status": hr.get("status"),
                        "lifecycle_status": hr.get("lifecycle_status"),
                        "role": hr.get("role"),
                        "trade": hr.get("trade"),
                        "department": hr.get("department"),
                        "driver_status": hr.get("driver_status"),
                        "updated_at": hr.get("updated_at"),
                    }
                # TRACK 16.11 · projection (read-only). Prefer the
                # snapshot stored on the transport_person itself; if
                # absent (e.g. legacy person row), recompute on the fly.
                hr_projection = person.get("hr_projection")
                if not hr_projection and hr:
                    from lib.transport_hr_lifecycle import (
                        map_hr_lifecycle_to_transport,
                    )
                    hr_projection = map_hr_lifecycle_to_transport(hr)
            except Exception:  # noqa: BLE001
                pass
        return {
            "driver": _project(person),
            "carrier": _project(carrier),
            "documents": [_project(d) for d in docs],
            "eligibility": _project(elig),
            "hr_linkage": hr_link,
            "hr_projection": hr_projection,
            "disclaimer": INSPECTION_DISCLAIMER,
        }

    @router.get("/admin/transportation/trucks/{tid}/workspace")
    async def truck_workspace(tid: str, _: Any = Depends(require_admin_dep)):
        truck = await db.transport_trucks.find_one({"id": tid, "tenant": TENANT})
        if not truck:
            raise HTTPException(404, "Truck not found")
        carrier = None
        if truck.get("carrier_id"):
            carrier = await db.carriers.find_one(
                {"id": truck["carrier_id"], "tenant": TENANT})
        inspections = await db.transport_truck_inspections.find(
            {"tenant": TENANT, "transport_truck_id": tid}
        ).sort("inspected_at", -1).to_list(50)
        elig = await db.transport_eligibility_state.find_one(
            {"tenant": TENANT, "target_type": "truck", "target_id": tid})
        return {
            "truck": _project(truck),
            "carrier": _project(carrier),
            "inspections": [_project(i) for i in inspections],
            "eligibility": _project(elig),
            "disclaimer": INSPECTION_DISCLAIMER,
        }

    app.include_router(router)
    return router
