"""Track 13.21 · Phase C · Dispatch Companion Haul Ledger (derived view).

Read-only company-wide haul ledger feed. Composes existing data from:
  • haul_cycles            — Dispatch completion truth (primary row source)
  • dispatch_assignments   — backfill for haul_type / source / destination when
                             haul_cycles row pre-dates the iter409 cycle fields
  • operational_attachments — scale-ticket family proof join (Track 13.14)
  • daily_reports          — foreman-authored material in/out totals

Doctrine:
  • TRACK_13_18_MATERIAL_MOVEMENT_LEDGER_CERTIFICATION_AND_ARCHITECTURE.md
  • TRACK_13_19_MATERIAL_MOVEMENT_LEDGER_PHASE_A_PROOF_JOIN.md
  • TRACK_13_20_MATERIAL_MOVEMENT_LEDGER_PHASE_B_PM_PANEL.md

Hard rules honored:
  • NO new collection · NO writes · NO persistence · NO background jobs.
  • Dispatch sees company-wide. PMs do NOT consume this endpoint.
  • FleetWatcher fields remain NOT_CONNECTED (never fabricated).
  • Date-range capped at 90 days to keep the read bounded.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query


# Reuse the same proof-bearing attachment types defined in Phase A.
_PROOF_ATTACHMENT_TYPES = (
    "scale_ticket",
    "asphalt_ticket",
    "delivery_receipt",
    "dump_receipt",
    "tanker_BOL",
)

# Bound the read so an open-ended range cannot DoS the backend.
_MAX_RANGE_DAYS = 90


def _today_yyyymmdd() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _parse_yyyymmdd(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def _net_lbs_to_tons(net_lbs: Optional[float]) -> Optional[float]:
    if net_lbs is None:
        return None
    try:
        return round(float(net_lbs) / 2000.0, 3)
    except (TypeError, ValueError):
        return None


def build_dispatch_haul_ledger_router(
    db,
    require_dispatch_or_admin_dep: Callable[..., Awaitable[Dict[str, Any]]],
) -> APIRouter:
    """Factory for the Dispatch Companion Haul Ledger router."""
    router = APIRouter(prefix="/api/dispatch", tags=["dispatch-haul-ledger"])

    @router.get("/haul-ledger")
    async def haul_ledger(
        _actor: Dict[str, Any] = Depends(require_dispatch_or_admin_dep),  # noqa: ARG001
        date_from: Optional[str] = Query(None, description="YYYY-MM-DD inclusive · defaults to today"),
        date_to:   Optional[str] = Query(None, description="YYYY-MM-DD inclusive · defaults to today"),
        project_number: Optional[str] = Query(None, max_length=64),
        material_code:  Optional[str] = Query(None, max_length=64),
        truck:          Optional[str] = Query(None, max_length=64),
        verification_status: Optional[str] = Query(
            None,
            description="Filter on derived per-row status. Closed set.",
        ),
    ) -> Dict[str, Any]:
        # ── Resolve + validate date range ────────────────────────────
        date_from_s = (date_from or _today_yyyymmdd()).strip()
        date_to_s   = (date_to   or date_from_s).strip()
        try:
            d_from = _parse_yyyymmdd(date_from_s)
            d_to   = _parse_yyyymmdd(date_to_s)
        except ValueError:
            raise HTTPException(422, "date_from / date_to must be YYYY-MM-DD")
        if d_to < d_from:
            raise HTTPException(422, "date_to must be ≥ date_from")
        if (d_to - d_from).days > _MAX_RANGE_DAYS:
            raise HTTPException(
                422,
                f"Date range exceeds {_MAX_RANGE_DAYS} days · narrow the window.",
            )

        valid_status = {"no_activity", "verified", "partial", "missing_proof", "needs_review"}
        if verification_status and verification_status not in valid_status:
            raise HTTPException(422, f"verification_status must be one of {sorted(valid_status)}")

        # ── Build the per-day prefix list for completed_at matching ──
        day_prefixes: List[str] = []
        cur = d_from
        while cur <= d_to:
            day_prefixes.append(cur.strftime("%Y-%m-%d"))
            cur += timedelta(days=1)

        # ── Pull haul_cycles in range (primary row source) ───────────
        hc_query: Dict[str, Any] = {
            "completed_at": {"$regex": f"^({'|'.join(day_prefixes)})"},
        }
        if project_number:
            hc_query["project_number"] = project_number.strip()
        if truck:
            hc_query["truck_id"] = truck.strip()

        haul_cycle_rows: List[Dict[str, Any]] = []
        async for hc in db.haul_cycles.find(
            hc_query,
            {
                "_id": 0, "id": 1, "assignment_id": 1,
                "project_number": 1, "project_name": 1,
                "truck_id": 1, "driver_name": 1,
                "material": 1, "haul_type": 1,
                "source_location": 1, "destination": 1,
                "started_at": 1, "completed_at": 1,
                "total_seconds": 1, "wait_seconds": 1,
            },
        ).limit(2000):
            haul_cycle_rows.append(hc)

        # ── Pull operational_attachments proof rows joined on assignment_id
        assignment_ids = [hc.get("assignment_id") for hc in haul_cycle_rows if hc.get("assignment_id")]
        att_query: Dict[str, Any] = {
            "host_kind": "assignment",
            "type": {"$in": list(_PROOF_ATTACHMENT_TYPES)},
        }
        if assignment_ids:
            att_query["host_id"] = {"$in": assignment_ids}
        if material_code:
            att_query["material_code"] = material_code.strip()

        att_by_assignment: Dict[str, List[Dict[str, Any]]] = {}
        if assignment_ids:
            async for att in db.operational_attachments.find(
                att_query,
                {
                    "_id": 0, "id": 1, "host_id": 1, "type": 1,
                    "material_code": 1,
                    "weight_gross_lbs": 1, "weight_tare_lbs": 1,
                    "weight_net_lbs": 1,
                    "uploaded_by": 1, "uploaded_at": 1,
                    "filename": 1,
                },
            ).limit(5000):
                hid = att.get("host_id")
                if not hid:
                    continue
                att_by_assignment.setdefault(hid, []).append(att)

        # ── Pull daily_reports in range for material in/out counts ───
        dr_query: Dict[str, Any] = {
            "report_date": {"$in": day_prefixes},
            "deleted_at": {"$in": [None, "", False]},
        }
        if project_number:
            dr_query["project_number"] = project_number.strip()
        dr_inbound_count = 0
        dr_outbound_count = 0
        dr_project_set: set = set()
        async for d in db.daily_reports.find(
            dr_query,
            {"_id": 0, "project_number": 1, "materials": 1, "outbound_materials": 1},
        ):
            mats = d.get("materials") or []
            outs = d.get("outbound_materials") or []
            dr_inbound_count  += len(mats)
            dr_outbound_count += len(outs)
            if (mats or outs) and d.get("project_number"):
                dr_project_set.add(d["project_number"])

        # ── Build the per-cycle ledger rows ──────────────────────────
        rows: List[Dict[str, Any]] = []
        total_loads = 0
        total_ticket_count = 0
        net_lbs_sum = 0.0
        net_lbs_has_value = False
        missing_proof = 0
        projects_set: set = set()
        trucks_set: set = set()
        materials_set: set = set()
        by_project_counts: Dict[str, Dict[str, int]] = {}
        by_material_counts: Dict[str, Dict[str, int]] = {}
        by_truck_counts: Dict[str, Dict[str, int]] = {}

        for hc in haul_cycle_rows:
            aid = hc.get("assignment_id") or ""
            proofs = att_by_assignment.get(aid, [])
            ticket_count = len(proofs)
            net_lbs_row: Optional[float] = None
            mat_code_row: Optional[str] = None
            for p in proofs:
                if p.get("weight_net_lbs") is not None:
                    try:
                        v = float(p["weight_net_lbs"])
                        net_lbs_sum += v
                        net_lbs_has_value = True
                        net_lbs_row = (net_lbs_row or 0) + v
                    except (TypeError, ValueError):
                        pass
                if mat_code_row is None and p.get("material_code"):
                    mat_code_row = p["material_code"]

            if ticket_count == 0:
                missing_proof += 1
                row_verification = "missing_proof"
            else:
                row_verification = "verified"

            row = {
                "haul_cycle_id": hc.get("id"),
                "assignment_id": aid,
                "date": (hc.get("completed_at") or "")[:10],
                "project_number": hc.get("project_number") or "",
                "project_name": hc.get("project_name") or "",
                "material_code": mat_code_row,
                "material_description": hc.get("material") or "",
                "haul_type": hc.get("haul_type") or "Material",
                "truck_id": hc.get("truck_id") or "",
                "driver_name": hc.get("driver_name") or "",
                "source_location": hc.get("source_location") or "",
                "destination_location": hc.get("destination") or "",
                "started_at": hc.get("started_at"),
                "completed_at": hc.get("completed_at"),
                "scale_ticket_count": ticket_count,
                "net_lbs": round(net_lbs_row, 2) if net_lbs_row is not None else None,
                "net_tons": _net_lbs_to_tons(net_lbs_row),
                "verification_status": row_verification,
                "source_system": "haul_cycle",
            }

            # Material-code filter: apply post-aggregation since attachment join
            # may be the source of the code. Row dropped if filter mismatch.
            if material_code and (mat_code_row or "").strip() != material_code.strip():
                continue
            if verification_status and row_verification != verification_status:
                continue

            rows.append(row)
            total_loads += 1
            total_ticket_count += ticket_count
            if row["project_number"]:
                projects_set.add(row["project_number"])
                pn_bucket = by_project_counts.setdefault(
                    row["project_number"],
                    {"loads": 0, "ticket_count": 0, "missing_proof": 0},
                )
                pn_bucket["loads"] += 1
                pn_bucket["ticket_count"] += ticket_count
                if ticket_count == 0:
                    pn_bucket["missing_proof"] += 1
            if row["truck_id"]:
                trucks_set.add(row["truck_id"])
                tk_bucket = by_truck_counts.setdefault(
                    row["truck_id"],
                    {"loads": 0, "ticket_count": 0},
                )
                tk_bucket["loads"] += 1
                tk_bucket["ticket_count"] += ticket_count
            mat_label = (mat_code_row or row["material_description"] or "").strip()
            if mat_label:
                materials_set.add(mat_label.lower())
                mt_bucket = by_material_counts.setdefault(
                    mat_label,
                    {"loads": 0, "ticket_count": 0},
                )
                mt_bucket["loads"] += 1
                mt_bucket["ticket_count"] += ticket_count

        # Sort rows newest-first by completed_at then by date desc.
        rows.sort(key=lambda r: (r.get("completed_at") or ""), reverse=True)

        by_project = [
            {"project_number": k, **v}
            for k, v in sorted(by_project_counts.items(), key=lambda kv: -kv[1]["loads"])
        ]
        by_material = [
            {"material": k, **v}
            for k, v in sorted(by_material_counts.items(), key=lambda kv: -kv[1]["loads"])
        ]
        by_truck = [
            {"truck_id": k, **v}
            for k, v in sorted(by_truck_counts.items(), key=lambda kv: -kv[1]["loads"])
        ]

        # Include DR-only projects in the projects_count rollup so Dispatch
        # sees days where foreman captured inbound/outbound but no MASCI
        # cycle ran.
        projects_set.update(dr_project_set)

        rollups = {
            "projects_count": len(projects_set),
            "loads_count": int(total_loads),
            "haul_cycles_count": len(haul_cycle_rows),
            "scale_ticket_count": int(total_ticket_count),
            "missing_proof_count": int(missing_proof),
            "net_lbs": round(net_lbs_sum, 2) if net_lbs_has_value else None,
            "net_tons": _net_lbs_to_tons(net_lbs_sum) if net_lbs_has_value else None,
            "trucks_count": len(trucks_set),
            "materials_count": len(materials_set),
            "dr_inbound_count": int(dr_inbound_count),
            "dr_outbound_count": int(dr_outbound_count),
        }

        source_breakdown = {
            "haul_cycles": len(haul_cycle_rows),
            "scale_tickets": int(total_ticket_count),
            "daily_reports_in":  int(dr_inbound_count),
            "daily_reports_out": int(dr_outbound_count),
            "odr_events": 0,
            "fleetwatcher": 0,
        }

        return {
            "ok": True,
            "date_from": date_from_s,
            "date_to": date_to_s,
            "filters": {
                "project_number": project_number,
                "material_code": material_code,
                "truck": truck,
                "verification_status": verification_status,
            },
            "rows": rows,
            "rollups": rollups,
            "by_project": by_project,
            "by_material": by_material,
            "by_truck": by_truck,
            "source_breakdown": source_breakdown,
            "fleetwatcher": {
                "connected": False,
                "reason": "not_connected",
            },
        }

    return router


__all__ = ["build_dispatch_haul_ledger_router"]
