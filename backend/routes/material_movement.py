"""MM-001B · E-5 · Material Movement Rollup (derived view).

Server-derived visibility layer combining:
  • dispatch_assignments        — Category A · MASCI-controlled hauling
  • daily_reports.materials[]   — Category B · foreman-authored external deliveries

MM-001B-F1 (2026-02-09) · False-Outgoing Defect Fix
  • `daily_reports.production[]` is EXPLICITLY EXCLUDED from this rollup.
    Production rows describe work performed (RCP installed, asphalt placed,
    grading, etc.) — they are NOT material movement. Production renders only
    in its own Production section on the read view and PDF.

NO new collection. NO duplicate persistence. NO background jobs.
Pure read · derived only.
Doctrine: MM_001A_A_EXTERNAL_MATERIAL_MOVEMENT_GAP_AUDIT.md
"""
from __future__ import annotations
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException


def register_material_movement_routes(router: APIRouter, db) -> None:

    @router.get("/material-movement/daily/{project_number}/{date}")
    async def daily_material_movement(project_number: str, date: str):
        """Returns a single-day rollup for a project. Public read — same
        access posture as /api/jobs. Pure derivation; no writes."""
        project_number = (project_number or "").strip()
        date = (date or "").strip()
        if not project_number or not date:
            raise HTTPException(422, "project_number and date are required")

        # ── Category A · MASCI dispatch_assignments ────────────────
        dispatch_rows: List[Dict[str, Any]] = []
        async for a in db.dispatch_assignments.find(
            {"project_number": project_number, "scheduled_date": date},
            {
                "_id": 0, "id": 1, "haul_type": 1, "material": 1,
                "source_location": 1, "destination": 1, "load_count": 1,
                "carrier": 1, "truck_id": 1, "driver_name": 1, "lifecycle_state": 1,
            },
        ).limit(500):
            dispatch_rows.append(a)

        haul_type_counts: Dict[str, int] = {}
        truck_ids: set = set()
        total_loads = 0
        for r in dispatch_rows:
            ht = (r.get("haul_type") or "Material").strip() or "Material"
            haul_type_counts[ht] = haul_type_counts.get(ht, 0) + 1
            if r.get("truck_id"):
                truck_ids.add(r["truck_id"])
            try:
                total_loads += int(r.get("load_count") or 0)
            except (TypeError, ValueError):
                pass

        # ── Category B · Daily Report materials[] (deliveries / removals) ──
        # MM-001B-F1: production[] is intentionally NOT read here. Production
        # rows describe installed work, not material movement, and surfacing
        # them as "Outgoing" produced false hauling visibility in the field.
        incoming: List[Dict[str, Any]] = []
        outgoing: List[Dict[str, Any]] = []
        async for d in db.daily_reports.find(
            {"project_number": project_number, "report_date": date,
             "deleted_at": {"$in": [None, "", False]}},
            {"_id": 0, "id": 1, "materials": 1},
        ):
            for m in d.get("materials") or []:
                incoming.append({
                    "material": m.get("description") or "",
                    "quantity": m.get("quantity"),
                    "unit": m.get("unit") or "",
                    "source": m.get("supplier") or "",
                    "ticket_number": m.get("ticket_number") or "",
                    "dr_id": d.get("id"),
                })

        return {
            "project_number": project_number,
            "date": date,
            "dispatch": {
                "assignments": len(dispatch_rows),
                "loads": total_loads,
                "trucks": len(truck_ids),
                "by_haul_type": haul_type_counts,
                "rows": dispatch_rows,
            },
            "incoming": incoming,
            "outgoing": outgoing,
        }


__all__ = ["register_material_movement_routes"]
