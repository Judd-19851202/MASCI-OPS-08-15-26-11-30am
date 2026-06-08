"""
Integration Center · cleanup.py — MCC-1 · Motive Mapping Cleanup Center.
========================================================================
Read-side aggregator + operator-action endpoints powering the
"Mapping Cleanup" tab inside the existing Integration Center.

MCC-1 doctrine
--------------
- No new collections. Cleanup state rides on existing
  asset_mappings / employee_mappings docs via two new fields:
    `cleanup_status` ∈ {"", "ignored", "former_employee",
                         "ignored_gateway", "retired", "resolved"}
    `cleanup_notes`   free-text audit string
- No automation. Operator must explicitly act per row.
- Reuses existing match logic (_propose_asset_links /
  _propose_driver_links) so MCC-1 lists the *same* candidates the
  Auto-Link tool sees — no parallel match engine.
- Mapping conflicts are derived at query time from
  asset_mappings / employee_mappings; no new collection introduced.

Exposed:
  GET  /api/admin/integrations/cleanup/trust-score
  GET  /api/admin/integrations/cleanup/drivers
  GET  /api/admin/integrations/cleanup/assets
  GET  /api/admin/integrations/cleanup/conflicts

  POST /api/admin/integrations/cleanup/drivers/{mapping_id}/link
       body: {employee_id: str, note?: str}
  POST /api/admin/integrations/cleanup/drivers/{mapping_id}/ignore
       body: {note?: str}
  POST /api/admin/integrations/cleanup/drivers/{mapping_id}/former-employee
       body: {note?: str}

  POST /api/admin/integrations/cleanup/assets/{mapping_id}/link
       body: {equipment_id: str, note?: str}
  POST /api/admin/integrations/cleanup/assets/{mapping_id}/ignore-gateway
       body: {note?: str}
  POST /api/admin/integrations/cleanup/assets/{mapping_id}/retire
       body: {note?: str}

  POST /api/admin/integrations/cleanup/conflicts/resolve
       body: {kind: "asset"|"driver", action: "keep_a"|"keep_b"|"manual_link"|"dismiss",
              mapping_a_id: str, mapping_b_id?: str, manual_target_id?: str, note?: str}
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException

from ._storage import now_iso, write_sync_log
from .autolink import _propose_asset_links, _propose_driver_links


def _is_resolved(cleanup_status: Optional[str]) -> bool:
    return (cleanup_status or "") in {
        "ignored", "former_employee", "ignored_gateway", "retired", "resolved",
    }


async def _build_driver_queue(db) -> Dict[str, Any]:
    """List every Motive driver row + its match candidate + status."""
    props = await _propose_driver_links(db)
    by_mapping = {p["mapping_id"]: p for p in props}

    rows: List[Dict[str, Any]] = []
    counts = {"active_unlinked": 0, "deactivated": 0, "resolved": 0, "linked": 0}

    async for m in db.employee_mappings.find(
        {"provider": "motive"}, {"_id": 0}
    ).sort("updated_at", -1):
        mv = m.get("motive") or {}
        status = (mv.get("status") or "").lower()  # "active" | "deactivated"
        existing_link = (m.get("masci_employee_id") or "").strip()
        cleanup_status = m.get("cleanup_status") or ""
        prop = by_mapping.get(m.get("id"), {})

        is_resolved = bool(existing_link) or _is_resolved(cleanup_status)
        if is_resolved:
            counts["resolved"] += 1
            if existing_link:
                counts["linked"] += 1
        else:
            if status == "deactivated":
                counts["deactivated"] += 1
            else:
                counts["active_unlinked"] += 1

        rows.append({
            "mapping_id": m.get("id"),
            "motive_driver_id": mv.get("driver_id") or mv.get("user_id") or "",
            "motive_user_id": mv.get("user_id") or "",
            "motive_name": (
                m.get("masci_employee_name")
                or mv.get("driver_name")
                or (mv.get("first_name", "") + " " + mv.get("last_name", "")).strip()
                or "—"
            ),
            "motive_email": mv.get("email") or "",
            "motive_phone": mv.get("phone") or "",
            "motive_status": status or "unknown",
            "existing_employee_id": existing_link,
            "existing_employee_name": m.get("masci_employee_name") or "",
            "candidate_employee_id": prop.get("candidate_employee_id") or "",
            "candidate_employee_name": prop.get("candidate_employee_name") or "",
            "match_method": prop.get("match_method") or "",
            "match_confidence": prop.get("match_confidence") or "",
            "cleanup_status": cleanup_status,
            "cleanup_notes": m.get("cleanup_notes") or "",
            "is_resolved": is_resolved,
        })

    return {"counts": counts, "rows": rows}


async def _build_asset_queue(db) -> Dict[str, Any]:
    props = await _propose_asset_links(db)
    by_mapping = {p["mapping_id"]: p for p in props}

    rows: List[Dict[str, Any]] = []
    counts = {
        "operational": 0, "retired": 0, "unlinked": 0, "resolved": 0, "linked": 0,
    }

    async for m in db.asset_mappings.find(
        {"provider": "motive"}, {"_id": 0}
    ).sort("updated_at", -1):
        mv = m.get("motive") or {}
        existing_link = (m.get("masci_equipment_id") or "").strip()
        cleanup_status = m.get("cleanup_status") or ""
        prop = by_mapping.get(m.get("id"), {})

        # Operational vs retired heuristic — `motive.status` if present,
        # else infer from `located_at` recency. Operator can override
        # via `mark retired`.
        gps_enabled = bool(mv.get("gps_enabled"))
        located_at = mv.get("located_at")
        explicit_retired = cleanup_status == "retired"
        is_operational = (
            not explicit_retired
            and (gps_enabled or located_at)
        )

        is_resolved = bool(existing_link) or _is_resolved(cleanup_status)
        if is_resolved:
            counts["resolved"] += 1
            if existing_link:
                counts["linked"] += 1
        else:
            counts["unlinked"] += 1
        if explicit_retired:
            counts["retired"] += 1
        elif is_operational:
            counts["operational"] += 1

        rows.append({
            "mapping_id": m.get("id"),
            "asset_kind": m.get("asset_kind") or (mv.get("kind") or ""),
            "unit_number": (
                m.get("masci_unit_number")
                or mv.get("number")
                or mv.get("name")
                or "—"
            ),
            "motive_name": mv.get("name") or "",
            "motive_vehicle_id": mv.get("vehicle_id") or "",
            "motive_asset_id": mv.get("asset_id") or "",
            "vin": mv.get("vin") or "",
            "equipment_type": (
                m.get("masci_equipment_type")
                or mv.get("make")
                or mv.get("model")
                or ""
            ),
            "gps_enabled": gps_enabled,
            "located_at": located_at,
            "existing_equipment_id": existing_link,
            "existing_equipment_name": m.get("masci_equipment_name") or "",
            "candidate_equipment_id": prop.get("candidate_equipment_id") or "",
            "candidate_unit_number": prop.get("candidate_unit_number") or "",
            "candidate_display": prop.get("candidate_display") or "",
            "match_method": prop.get("match_method") or "",
            "match_confidence": prop.get("match_confidence") or "",
            "cleanup_status": cleanup_status,
            "cleanup_notes": m.get("cleanup_notes") or "",
            "is_resolved": is_resolved,
            "is_operational": is_operational,
        })

    return {"counts": counts, "rows": rows}


async def _find_conflicts(db) -> Dict[str, Any]:
    """Detect 1:N conflicts in both collections.

    Asset conflict = 2+ asset_mappings rows with the same
    masci_equipment_id (or 2+ candidates targeting the same
    equipment_id from auto-link preview).
    Driver conflict = analogous on masci_employee_id."""

    # ── ASSETS ─────────────────────────────────────────────────────
    asset_conflicts: List[Dict[str, Any]] = []
    # 1. Existing duplicates in asset_mappings
    pipeline_asset = [
        {"$match": {"provider": "motive", "masci_equipment_id": {"$nin": ["", None]}}},
        {"$group": {"_id": "$masci_equipment_id", "count": {"$sum": 1},
                    "mappings": {"$push": {"id": "$id",
                                             "motive": "$motive",
                                             "masci_unit_number": "$masci_unit_number",
                                             "masci_equipment_name": "$masci_equipment_name",
                                             "cleanup_status": "$cleanup_status",
                                             "updated_at": "$updated_at"}}}},
        {"$match": {"count": {"$gt": 1}}},
    ]
    async for row in db.asset_mappings.aggregate(pipeline_asset):
        active = [mp for mp in (row.get("mappings") or [])
                  if (mp.get("cleanup_status") or "") not in {"dismissed"}]
        if len(active) < 2:
            continue
        a, b = active[0], active[1]
        asset_conflicts.append({
            "conflict_id": f"asset:{row['_id']}",
            "kind": "asset",
            "conflict_type": "duplicate_target",
            "reason": f"{len(active)} Motive mappings all pointing at MASCI equipment {row['_id']}",
            "target_equipment_id": row["_id"],
            "mapping_a": {
                "id": a.get("id"),
                "motive_vehicle_id": (a.get("motive") or {}).get("vehicle_id") or "",
                "motive_unit": (a.get("motive") or {}).get("number") or (a.get("motive") or {}).get("name") or "",
                "masci_unit_number": a.get("masci_unit_number") or "",
                "masci_equipment_name": a.get("masci_equipment_name") or "",
                "updated_at": a.get("updated_at"),
            },
            "mapping_b": {
                "id": b.get("id"),
                "motive_vehicle_id": (b.get("motive") or {}).get("vehicle_id") or "",
                "motive_unit": (b.get("motive") or {}).get("number") or (b.get("motive") or {}).get("name") or "",
                "masci_unit_number": b.get("masci_unit_number") or "",
                "masci_equipment_name": b.get("masci_equipment_name") or "",
                "updated_at": b.get("updated_at"),
            },
        })

    # 2. Auto-link proposal collisions — two unmapped Motive rows
    #    both proposing the same MASCI equipment_id.
    asset_props = await _propose_asset_links(db)
    by_candidate: Dict[str, List[Dict[str, Any]]] = {}
    for p in asset_props:
        cid = p.get("candidate_equipment_id") or ""
        if not cid or p.get("decision") != "link":
            continue
        by_candidate.setdefault(cid, []).append(p)
    for cid, lst in by_candidate.items():
        if len(lst) >= 2:
            a, b = lst[0], lst[1]
            asset_conflicts.append({
                "conflict_id": f"asset-proposal:{cid}",
                "kind": "asset",
                "conflict_type": "proposal_collision",
                "reason": f"{len(lst)} unlinked Motive rows propose the same MASCI equipment {cid}",
                "target_equipment_id": cid,
                "mapping_a": {
                    "id": a.get("mapping_id"),
                    "motive_vehicle_id": a.get("motive_vehicle_id") or "",
                    "motive_unit": a.get("motive_number") or "",
                    "masci_unit_number": a.get("candidate_unit_number") or "",
                    "masci_equipment_name": a.get("candidate_display") or "",
                    "match_method": a.get("match_method") or "",
                    "match_confidence": a.get("match_confidence") or "",
                },
                "mapping_b": {
                    "id": b.get("mapping_id"),
                    "motive_vehicle_id": b.get("motive_vehicle_id") or "",
                    "motive_unit": b.get("motive_number") or "",
                    "masci_unit_number": b.get("candidate_unit_number") or "",
                    "masci_equipment_name": b.get("candidate_display") or "",
                    "match_method": b.get("match_method") or "",
                    "match_confidence": b.get("match_confidence") or "",
                },
            })

    # ── DRIVERS ────────────────────────────────────────────────────
    driver_conflicts: List[Dict[str, Any]] = []
    pipeline_emp = [
        {"$match": {"provider": "motive", "masci_employee_id": {"$nin": ["", None]}}},
        {"$group": {"_id": "$masci_employee_id", "count": {"$sum": 1},
                    "mappings": {"$push": {"id": "$id",
                                             "motive": "$motive",
                                             "masci_employee_name": "$masci_employee_name",
                                             "cleanup_status": "$cleanup_status",
                                             "updated_at": "$updated_at"}}}},
        {"$match": {"count": {"$gt": 1}}},
    ]
    async for row in db.employee_mappings.aggregate(pipeline_emp):
        active = [mp for mp in (row.get("mappings") or [])
                  if (mp.get("cleanup_status") or "") not in {"dismissed"}]
        if len(active) < 2:
            continue
        a, b = active[0], active[1]
        driver_conflicts.append({
            "conflict_id": f"driver:{row['_id']}",
            "kind": "driver",
            "conflict_type": "duplicate_target",
            "reason": f"{len(active)} Motive drivers all linked to MASCI employee {row['_id']}",
            "target_employee_id": row["_id"],
            "mapping_a": {
                "id": a.get("id"),
                "motive_driver_id": (a.get("motive") or {}).get("driver_id") or "",
                "motive_name": (a.get("motive") or {}).get("driver_name") or "",
                "masci_employee_name": a.get("masci_employee_name") or "",
                "updated_at": a.get("updated_at"),
            },
            "mapping_b": {
                "id": b.get("id"),
                "motive_driver_id": (b.get("motive") or {}).get("driver_id") or "",
                "motive_name": (b.get("motive") or {}).get("driver_name") or "",
                "masci_employee_name": b.get("masci_employee_name") or "",
                "updated_at": b.get("updated_at"),
            },
        })

    return {
        "asset_conflicts": asset_conflicts,
        "driver_conflicts": driver_conflicts,
        "counts": {
            "asset": len(asset_conflicts),
            "driver": len(driver_conflicts),
            "total": len(asset_conflicts) + len(driver_conflicts),
        },
    }


def _band(pct: float) -> str:
    if pct >= 95:
        return "green"
    if pct >= 85:
        return "amber"
    return "red"


async def _trust_score(db) -> Dict[str, Any]:
    """MCC-1D · Motive Mapping Health.

    Uses the same OIS GPS-band language: green / amber / red.
    Aggregates total assets/drivers linked, conflicts open, derives a
    single trust % that operators try to drive toward 100%."""
    # Drivers
    drivers_total = await db.employee_mappings.count_documents({"provider": "motive"})
    drivers_linked = await db.employee_mappings.count_documents({
        "provider": "motive", "masci_employee_id": {"$nin": ["", None]},
    })
    drivers_resolved_no_link = await db.employee_mappings.count_documents({
        "provider": "motive",
        "masci_employee_id": {"$in": ["", None]},
        "cleanup_status": {"$in": ["ignored", "former_employee"]},
    })

    # Assets
    assets_total = await db.asset_mappings.count_documents({"provider": "motive"})
    assets_linked = await db.asset_mappings.count_documents({
        "provider": "motive", "masci_equipment_id": {"$nin": ["", None]},
    })
    assets_resolved_no_link = await db.asset_mappings.count_documents({
        "provider": "motive",
        "masci_equipment_id": {"$in": ["", None]},
        "cleanup_status": {"$in": ["ignored_gateway", "retired"]},
    })

    conflicts = await _find_conflicts(db)
    conflict_total = conflicts["counts"]["total"]

    # Resolved = linked + explicitly-ignored.
    drivers_resolved = drivers_linked + drivers_resolved_no_link
    assets_resolved = assets_linked + assets_resolved_no_link

    weight_total = drivers_total + assets_total + max(1, conflict_total)
    weight_resolved = drivers_resolved + assets_resolved + (
        # Conflicts subtract from trust — count each open conflict as
        # 1 unresolved unit. When count is zero, contribution is zero.
        max(0, max(1, conflict_total) - conflict_total)
    )
    trust_pct = round((weight_resolved / weight_total) * 100, 1) if weight_total else 100.0

    drivers_pct = round((drivers_resolved / drivers_total) * 100, 1) if drivers_total else 100.0
    assets_pct = round((assets_resolved / assets_total) * 100, 1) if assets_total else 100.0

    return {
        "as_of": datetime.now(timezone.utc).isoformat(),
        "drivers": {
            "total": drivers_total,
            "linked": drivers_linked,
            "ignored_or_former": drivers_resolved_no_link,
            "resolved": drivers_resolved,
            "pct": drivers_pct,
            "band": _band(drivers_pct),
        },
        "assets": {
            "total": assets_total,
            "linked": assets_linked,
            "ignored_or_retired": assets_resolved_no_link,
            "resolved": assets_resolved,
            "pct": assets_pct,
            "band": _band(assets_pct),
        },
        "conflicts": {
            "total": conflict_total,
            "asset": conflicts["counts"]["asset"],
            "driver": conflicts["counts"]["driver"],
        },
        "trust": {
            "pct": trust_pct,
            "band": _band(trust_pct),
            "label": "Healthy" if trust_pct >= 95 else "Needs Attention" if trust_pct >= 85 else "Critical",
        },
    }


# ── HTTP routes ─────────────────────────────────────────────────────
def register_cleanup_routes(api_router: APIRouter, db, require_admin) -> None:

    BASE = "/admin/integrations/cleanup"

    @api_router.get(f"{BASE}/trust-score", dependencies=[Depends(require_admin)])
    async def get_trust_score():
        return await _trust_score(db)

    @api_router.get(f"{BASE}/drivers", dependencies=[Depends(require_admin)])
    async def get_driver_queue():
        return await _build_driver_queue(db)

    @api_router.get(f"{BASE}/assets", dependencies=[Depends(require_admin)])
    async def get_asset_queue():
        return await _build_asset_queue(db)

    @api_router.get(f"{BASE}/conflicts", dependencies=[Depends(require_admin)])
    async def get_conflicts():
        return await _find_conflicts(db)

    # ── DRIVER ACTIONS ─────────────────────────────────────────────
    @api_router.post(
        f"{BASE}/drivers/{{mapping_id}}/link",
        dependencies=[Depends(require_admin)],
    )
    async def link_driver(mapping_id: str, body: Dict[str, Any] = Body(...)):
        emp_id = (body.get("employee_id") or "").strip()
        if not emp_id:
            raise HTTPException(400, "employee_id required")
        m = await db.employee_mappings.find_one({"id": mapping_id}, {"_id": 0})
        if not m:
            raise HTTPException(404, "mapping not found")
        emp = await db.employees.find_one(
            {"id": emp_id},
            {"_id": 0, "name": 1, "email": 1, "trade": 1, "role": 1},
        )
        if not emp:
            raise HTTPException(404, f"employee {emp_id} not found")
        # 1:1 guard — refuse if another mapping already owns this employee
        clash = await db.employee_mappings.find_one(
            {"masci_employee_id": emp_id, "id": {"$ne": mapping_id}},
            {"_id": 0, "id": 1},
        )
        if clash:
            raise HTTPException(409, f"employee already mapped by another row ({clash['id']})")

        await db.employee_mappings.update_one({"id": mapping_id}, {"$set": {
            "masci_employee_id": emp_id,
            "masci_employee_name": emp.get("name") or "",
            "masci_employee_email": emp.get("email") or "",
            "masci_employee_trade": emp.get("trade") or "",
            "masci_employee_role": emp.get("role") or "",
            "cleanup_status": "resolved",
            "cleanup_notes": (body.get("note") or "Manually linked via MCC-1 · " + now_iso())[:300],
            "mapping_notes": f"MCC-1 manual link · {now_iso()}",
            "motive.mapping_status": "Mapped",
            "updated_at": now_iso(),
        }})
        await write_sync_log(
            db, integration="motive", sync_type="mcc1_driver_link",
            status="Success", triggered_by="admin",
            records_created=0, records_updated=1, records_skipped=0, records_failed=0,
            notes=f"mapping_id={mapping_id} employee_id={emp_id}",
        )
        return await db.employee_mappings.find_one({"id": mapping_id}, {"_id": 0})

    @api_router.post(
        f"{BASE}/drivers/{{mapping_id}}/ignore",
        dependencies=[Depends(require_admin)],
    )
    async def ignore_driver(mapping_id: str, body: Dict[str, Any] = Body(default={})):
        m = await db.employee_mappings.find_one({"id": mapping_id}, {"_id": 0})
        if not m:
            raise HTTPException(404, "mapping not found")
        await db.employee_mappings.update_one({"id": mapping_id}, {"$set": {
            "cleanup_status": "ignored",
            "cleanup_notes": (body.get("note") or "Ignored via MCC-1 · " + now_iso())[:300],
            "updated_at": now_iso(),
        }})
        await write_sync_log(
            db, integration="motive", sync_type="mcc1_driver_ignore",
            status="Success", triggered_by="admin",
            records_created=0, records_updated=1, records_skipped=0, records_failed=0,
            notes=f"mapping_id={mapping_id}",
        )
        return {"ok": True}

    @api_router.post(
        f"{BASE}/drivers/{{mapping_id}}/former-employee",
        dependencies=[Depends(require_admin)],
    )
    async def mark_former_employee(mapping_id: str, body: Dict[str, Any] = Body(default={})):
        m = await db.employee_mappings.find_one({"id": mapping_id}, {"_id": 0})
        if not m:
            raise HTTPException(404, "mapping not found")
        await db.employee_mappings.update_one({"id": mapping_id}, {"$set": {
            "cleanup_status": "former_employee",
            "cleanup_notes": (body.get("note") or "Marked as former employee via MCC-1 · " + now_iso())[:300],
            "updated_at": now_iso(),
        }})
        await write_sync_log(
            db, integration="motive", sync_type="mcc1_driver_former",
            status="Success", triggered_by="admin",
            records_created=0, records_updated=1, records_skipped=0, records_failed=0,
            notes=f"mapping_id={mapping_id}",
        )
        return {"ok": True}

    # ── ASSET ACTIONS ──────────────────────────────────────────────
    @api_router.post(
        f"{BASE}/assets/{{mapping_id}}/link",
        dependencies=[Depends(require_admin)],
    )
    async def link_asset(mapping_id: str, body: Dict[str, Any] = Body(...)):
        eq_id = (body.get("equipment_id") or "").strip()
        if not eq_id:
            raise HTTPException(400, "equipment_id required")
        m = await db.asset_mappings.find_one({"id": mapping_id}, {"_id": 0})
        if not m:
            raise HTTPException(404, "mapping not found")
        eq = await db.equipment_master.find_one(
            {"id": eq_id},
            {"_id": 0, "unit_number": 1, "display_label": 1,
             "make_model": 1, "category": 1, "name": 1, "equipment_type": 1},
        )
        if not eq:
            raise HTTPException(404, f"equipment {eq_id} not found")
        clash = await db.asset_mappings.find_one(
            {"masci_equipment_id": eq_id, "id": {"$ne": mapping_id}},
            {"_id": 0, "id": 1},
        )
        if clash:
            raise HTTPException(409, f"equipment already mapped by another row ({clash['id']})")

        await db.asset_mappings.update_one({"id": mapping_id}, {"$set": {
            "masci_equipment_id": eq_id,
            "masci_unit_number": eq.get("unit_number") or "",
            "masci_equipment_name": eq.get("display_label") or eq.get("name") or eq.get("make_model") or "",
            "masci_equipment_type": eq.get("category") or eq.get("equipment_type") or "",
            "cleanup_status": "resolved",
            "cleanup_notes": (body.get("note") or "Manually linked via MCC-1 · " + now_iso())[:300],
            "mapping_notes": f"MCC-1 manual link · {now_iso()}",
            "motive.mapping_status": "Mapped",
            "updated_at": now_iso(),
        }})
        await write_sync_log(
            db, integration="motive", sync_type="mcc1_asset_link",
            status="Success", triggered_by="admin",
            records_created=0, records_updated=1, records_skipped=0, records_failed=0,
            notes=f"mapping_id={mapping_id} equipment_id={eq_id}",
        )
        return await db.asset_mappings.find_one({"id": mapping_id}, {"_id": 0})

    @api_router.post(
        f"{BASE}/assets/{{mapping_id}}/ignore-gateway",
        dependencies=[Depends(require_admin)],
    )
    async def ignore_gateway(mapping_id: str, body: Dict[str, Any] = Body(default={})):
        m = await db.asset_mappings.find_one({"id": mapping_id}, {"_id": 0})
        if not m:
            raise HTTPException(404, "mapping not found")
        await db.asset_mappings.update_one({"id": mapping_id}, {"$set": {
            "cleanup_status": "ignored_gateway",
            "cleanup_notes": (body.get("note") or "Asset Gateway ignored via MCC-1 · " + now_iso())[:300],
            "updated_at": now_iso(),
        }})
        await write_sync_log(
            db, integration="motive", sync_type="mcc1_asset_ignore_gateway",
            status="Success", triggered_by="admin",
            records_created=0, records_updated=1, records_skipped=0, records_failed=0,
            notes=f"mapping_id={mapping_id}",
        )
        return {"ok": True}

    @api_router.post(
        f"{BASE}/assets/{{mapping_id}}/retire",
        dependencies=[Depends(require_admin)],
    )
    async def retire_asset(mapping_id: str, body: Dict[str, Any] = Body(default={})):
        m = await db.asset_mappings.find_one({"id": mapping_id}, {"_id": 0})
        if not m:
            raise HTTPException(404, "mapping not found")
        await db.asset_mappings.update_one({"id": mapping_id}, {"$set": {
            "cleanup_status": "retired",
            "cleanup_notes": (body.get("note") or "Marked retired via MCC-1 · " + now_iso())[:300],
            "updated_at": now_iso(),
        }})
        await write_sync_log(
            db, integration="motive", sync_type="mcc1_asset_retire",
            status="Success", triggered_by="admin",
            records_created=0, records_updated=1, records_skipped=0, records_failed=0,
            notes=f"mapping_id={mapping_id}",
        )
        return {"ok": True}

    # ── CONFLICT RESOLUTION ────────────────────────────────────────
    @api_router.post(
        f"{BASE}/conflicts/resolve",
        dependencies=[Depends(require_admin)],
    )
    async def resolve_conflict(body: Dict[str, Any] = Body(...)):
        kind = (body.get("kind") or "").strip()
        action = (body.get("action") or "").strip()
        a_id = (body.get("mapping_a_id") or "").strip()
        b_id = (body.get("mapping_b_id") or "").strip()
        manual_target = (body.get("manual_target_id") or "").strip()
        note = (body.get("note") or "")[:300]
        if kind not in {"asset", "driver"}:
            raise HTTPException(400, "kind must be 'asset' or 'driver'")
        if action not in {"keep_a", "keep_b", "manual_link", "dismiss"}:
            raise HTTPException(400, "invalid action")
        if not a_id:
            raise HTTPException(400, "mapping_a_id required")

        coll = db.asset_mappings if kind == "asset" else db.employee_mappings
        target_field = "masci_equipment_id" if kind == "asset" else "masci_employee_id"

        if action == "keep_a":
            if not b_id:
                raise HTTPException(400, "mapping_b_id required for keep_a")
            # Strip MASCI link off the loser (b)
            await coll.update_one({"id": b_id}, {"$set": {
                target_field: "",
                "cleanup_status": "resolved",
                "cleanup_notes": f"Conflict resolved · kept {a_id} · {now_iso()} · {note}"[:300],
                "motive.mapping_status": "Unmapped",
                "updated_at": now_iso(),
            }})
            # Stamp the winner so it's audited
            await coll.update_one({"id": a_id}, {"$set": {
                "cleanup_status": "resolved",
                "cleanup_notes": f"Conflict winner over {b_id} · {now_iso()} · {note}"[:300],
                "updated_at": now_iso(),
            }})
        elif action == "keep_b":
            if not b_id:
                raise HTTPException(400, "mapping_b_id required for keep_b")
            await coll.update_one({"id": a_id}, {"$set": {
                target_field: "",
                "cleanup_status": "resolved",
                "cleanup_notes": f"Conflict resolved · kept {b_id} · {now_iso()} · {note}"[:300],
                "motive.mapping_status": "Unmapped",
                "updated_at": now_iso(),
            }})
            await coll.update_one({"id": b_id}, {"$set": {
                "cleanup_status": "resolved",
                "cleanup_notes": f"Conflict winner over {a_id} · {now_iso()} · {note}"[:300],
                "updated_at": now_iso(),
            }})
        elif action == "manual_link":
            if not manual_target:
                raise HTTPException(400, "manual_target_id required for manual_link")
            # Clear both rows' MASCI links, then link `a` to the manual target.
            for mid in [m for m in [a_id, b_id] if m]:
                await coll.update_one({"id": mid}, {"$set": {
                    target_field: "",
                    "motive.mapping_status": "Unmapped",
                    "updated_at": now_iso(),
                }})
            # Re-link via the existing link endpoints' logic
            if kind == "asset":
                eq = await db.equipment_master.find_one(
                    {"id": manual_target},
                    {"_id": 0, "unit_number": 1, "display_label": 1,
                     "make_model": 1, "category": 1, "name": 1, "equipment_type": 1},
                )
                if not eq:
                    raise HTTPException(404, f"equipment {manual_target} not found")
                await coll.update_one({"id": a_id}, {"$set": {
                    target_field: manual_target,
                    "masci_unit_number": eq.get("unit_number") or "",
                    "masci_equipment_name": eq.get("display_label") or eq.get("name") or eq.get("make_model") or "",
                    "masci_equipment_type": eq.get("category") or eq.get("equipment_type") or "",
                    "cleanup_status": "resolved",
                    "cleanup_notes": f"Conflict manual-linked · {now_iso()} · {note}"[:300],
                    "motive.mapping_status": "Mapped",
                    "updated_at": now_iso(),
                }})
            else:
                emp = await db.employees.find_one(
                    {"id": manual_target},
                    {"_id": 0, "name": 1, "email": 1, "trade": 1, "role": 1},
                )
                if not emp:
                    raise HTTPException(404, f"employee {manual_target} not found")
                await coll.update_one({"id": a_id}, {"$set": {
                    target_field: manual_target,
                    "masci_employee_name": emp.get("name") or "",
                    "masci_employee_email": emp.get("email") or "",
                    "masci_employee_trade": emp.get("trade") or "",
                    "masci_employee_role": emp.get("role") or "",
                    "cleanup_status": "resolved",
                    "cleanup_notes": f"Conflict manual-linked · {now_iso()} · {note}"[:300],
                    "motive.mapping_status": "Mapped",
                    "updated_at": now_iso(),
                }})
        else:  # dismiss
            for mid in [m for m in [a_id, b_id] if m]:
                await coll.update_one({"id": mid}, {"$set": {
                    "cleanup_status": "resolved",
                    "cleanup_notes": f"Conflict dismissed · {now_iso()} · {note}"[:300],
                    "updated_at": now_iso(),
                }})

        await write_sync_log(
            db, integration="motive", sync_type=f"mcc1_conflict_{action}",
            status="Success", triggered_by="admin",
            records_created=0, records_updated=2 if b_id else 1,
            records_skipped=0, records_failed=0,
            notes=f"kind={kind} a={a_id} b={b_id} target={manual_target}",
        )
        return {"ok": True}


__all__ = ["register_cleanup_routes"]
