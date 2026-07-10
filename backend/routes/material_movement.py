"""MM-001B · E-5 · Material Movement Rollup (derived view).

Server-derived visibility layer combining:
  • dispatch_assignments        — Category A · MASCI-controlled hauling
  • daily_reports.materials[]   — Category B · foreman-authored external deliveries (INBOUND)
  • daily_reports.outbound_materials[]
                                — Category C · foreman-authored material LEAVING the project
                                  (MM-ENTRY-002 / K-MM-2)

MM-001B-F1 (2026-02-09) · False-Outgoing Defect Fix
  • `daily_reports.production[]` is EXPLICITLY EXCLUDED from this rollup.
    Production rows describe work performed (RCP installed, asphalt placed,
    grading, etc.) — they are NOT material movement. Production renders only
    in its own Production section on the read view and PDF.

MM-ENTRY-002 (2026-02-09) · Outbound capture sprint
  • `outgoing[]` is now populated from `daily_reports.outbound_materials[]`
    (the new foreman-authored outbound section). Dispatch outbound (when
    the haul is MASCI-dispatched) continues to surface inside the
    `dispatch` sub-object, unchanged.

Track 13.19 · Phase A · Material Movement Ledger Foundation (2026-06-12)
  • ADDITIVE only — every existing response key is preserved.
  • Joins `operational_attachments` (Track 13.14 scale-ticket family) on
    dispatch row ids for proof surfacing. host_kind="assignment" only —
    matching the walking-skeleton contract of operational_attachments.
  • Joins `haul_cycles` on (project_number, completed_at within day) for
    cycle-truth counters.
  • Adds: `scale_ticket_proofs[]`, `haul_cycles[]`, `proof_summary{}`,
    `rollups{}`, `verification_status` (virtual · no persistence),
    `source_breakdown{}`.
  • NO new collection. NO mutation. NO FleetWatcher (NOT_CONNECTED).
  • Doctrine: TRACK_13_18_MATERIAL_MOVEMENT_LEDGER_CERTIFICATION_AND_ARCHITECTURE.md

NO new collection. NO duplicate persistence. NO background jobs.
Pure read · derived only.
Doctrine: MM_001A_A_EXTERNAL_MATERIAL_MOVEMENT_GAP_AUDIT.md
         MM_ENTRY_001_DAILY_REPORT_MATERIAL_CAPTURE_AUDIT.md
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException

from lib.synthetic_dr_filter import apply_synthetic_dr_exclusion


# ── Track 13.19 · attachment kinds that count as material-movement proof.
# Mirrors operational_attachments.ATTACHMENT_TYPES — only the kinds that
# materially evidence a haul/delivery. Damage / breakdown / inspection /
# transfer photos are NOT proof of material movement.
_PROOF_ATTACHMENT_TYPES = {
    "scale_ticket",
    "asphalt_ticket",
    "delivery_receipt",
    "dump_receipt",
    "tanker_BOL",
}


def _net_lbs_to_tons(net_lbs: Optional[float]) -> Optional[float]:
    """Convert lbs → US short tons (2000 lbs). Returns None if input None."""
    if net_lbs is None:
        return None
    try:
        return round(float(net_lbs) / 2000.0, 3)
    except (TypeError, ValueError):
        return None


def register_material_movement_routes(router: APIRouter, db) -> None:

    @router.get("/material-movement/daily/{project_number}/{date}")
    async def daily_material_movement(project_number: str, date: str):
        """Returns a single-day rollup for a project. Public read — same
        access posture as /api/jobs. Pure derivation; no writes.

        Track 13.19 · Phase A enrichment additive fields:
          - scale_ticket_proofs[]
          - haul_cycles[]
          - proof_summary{}
          - rollups{}
          - verification_status
          - source_breakdown{}

        All existing keys (dispatch, incoming, outgoing) are preserved
        verbatim. Existing consumers (MaterialMovementTile.jsx and any
        future tiles) remain forward-compatible.
        """
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

        # ── Category B · Daily Report materials[] (inbound deliveries) ──
        # MM-001B-F1: production[] is intentionally NOT read here. Production
        # rows describe installed work, not material movement, and surfacing
        # them as "Outgoing" produced false hauling visibility in the field.
        # MM-ENTRY-002: outgoing[] is now populated from `outbound_materials[]`
        # below (K-MM-2). Production stays excluded.
        incoming: List[Dict[str, Any]] = []
        outgoing: List[Dict[str, Any]] = []
        async for d in db.daily_reports.find(
            apply_synthetic_dr_exclusion({
                "project_number": project_number, "report_date": date,
                "deleted_at": {"$in": [None, "", False]},
            }),
            {"_id": 0, "id": 1, "materials": 1, "outbound_materials": 1},
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
            # K-MM-2 · Foreman-authored outbound material rows.
            for o in d.get("outbound_materials") or []:
                outgoing.append({
                    "material": o.get("material") or o.get("description") or "",
                    "quantity": o.get("quantity"),
                    "unit": o.get("unit") or "",
                    "hauler": o.get("hauler") or "",
                    "destination": o.get("destination") or "",
                    "ticket_or_manifest": (
                        o.get("ticket_or_manifest")
                        or o.get("manifest_number")
                        or o.get("ticket_number")
                        or ""
                    ),
                    "notes": o.get("notes") or "",
                    "dr_id": d.get("id"),
                })

        # ─────────────────────────────────────────────────────────────
        # Track 13.19 · Phase A enrichment starts here. All additive.
        # ─────────────────────────────────────────────────────────────

        # ── Proof join · operational_attachments on dispatch row ids.
        # operational_attachments.host_kind="assignment" walking-skeleton
        # contract — host_id is the dispatch_assignment id. Filter to
        # proof-bearing types only.
        dispatch_ids = [r["id"] for r in dispatch_rows if r.get("id")]
        rows_with_proof_ids: set = set()
        scale_ticket_proofs: List[Dict[str, Any]] = []
        proof_net_lbs_total = 0.0
        proof_net_lbs_present = False

        if dispatch_ids:
            async for att in db.operational_attachments.find(
                {
                    "host_kind": "assignment",
                    "host_id": {"$in": dispatch_ids},
                    "type": {"$in": list(_PROOF_ATTACHMENT_TYPES)},
                },
                {
                    "_id": 0, "id": 1, "host_id": 1, "type": 1,
                    "uploaded_by": 1, "uploaded_role": 1, "uploaded_at": 1,
                    "operational_note": 1,
                    "weight_gross_lbs": 1, "weight_tare_lbs": 1,
                    "weight_net_lbs": 1, "material_code": 1,
                    "filename": 1, "content_type": 1,
                },
            ).limit(2000):
                host_id = att.get("host_id")
                if host_id:
                    rows_with_proof_ids.add(host_id)
                net_lbs = att.get("weight_net_lbs")
                if net_lbs is not None:
                    proof_net_lbs_present = True
                    try:
                        proof_net_lbs_total += float(net_lbs)
                    except (TypeError, ValueError):
                        pass

                # Find truck/driver from the joined dispatch row when
                # available (read-only enrichment for the proof row).
                _src_row = next(
                    (r for r in dispatch_rows if r.get("id") == host_id), None,
                )

                scale_ticket_proofs.append({
                    "id": att.get("id"),
                    "type": att.get("type"),
                    "host_kind": "assignment",
                    "host_id": host_id,
                    "dispatch_assignment_id": host_id,
                    "truck_id": (_src_row or {}).get("truck_id"),
                    "driver_name": (_src_row or {}).get("driver_name"),
                    "material_code": att.get("material_code"),
                    "weight_gross_lbs": att.get("weight_gross_lbs"),
                    "weight_tare_lbs": att.get("weight_tare_lbs"),
                    "weight_net_lbs": net_lbs,
                    "net_tons": _net_lbs_to_tons(net_lbs),
                    "uploaded_by": att.get("uploaded_by"),
                    "uploaded_role": att.get("uploaded_role"),
                    "uploaded_at": att.get("uploaded_at"),
                    "operational_note": att.get("operational_note") or "",
                    "filename": att.get("filename"),
                    "content_type": att.get("content_type"),
                    "source": "scale_ticket",
                })

        scale_ticket_count = len(scale_ticket_proofs)
        matched_proof_count = len(rows_with_proof_ids)
        missing_proof_count = max(0, len(dispatch_rows) - matched_proof_count)
        partial_proof_count = matched_proof_count if (
            matched_proof_count > 0 and missing_proof_count > 0
        ) else 0

        # ── Haul cycle join · haul_cycles is derived cycle truth (one
        # row per completed assignment). Match on project_number AND
        # completed_at falling on the target date (string-prefix join —
        # ISO-8601 timestamps sort lexically by day).
        haul_cycle_rows: List[Dict[str, Any]] = []
        async for hc in db.haul_cycles.find(
            {
                "project_number": project_number,
                "completed_at": {"$regex": f"^{date}"},
            },
            {
                "_id": 0, "id": 1, "assignment_id": 1, "truck_id": 1,
                "driver_name": 1, "material": 1, "haul_type": 1,
                "source_location": 1, "destination": 1,
                "started_at": 1, "completed_at": 1,
                "total_seconds": 1, "wait_seconds": 1, "operating_seconds": 1,
                "transitions": 1,
            },
        ).limit(500):
            haul_cycle_rows.append(hc)

        # ── Rollup counters · additive · only what source supports.
        unique_materials: set = set()
        for r in dispatch_rows:
            m = (r.get("material") or "").strip()
            if m:
                unique_materials.add(m.lower())
        for inc in incoming:
            m = (inc.get("material") or "").strip()
            if m:
                unique_materials.add(m.lower())
        for out in outgoing:
            m = (out.get("material") or "").strip()
            if m:
                unique_materials.add(m.lower())

        # Inbound / outbound quantity totals — only sum when every row's
        # quantity is a number. Mixed units would make this misleading, so
        # we only expose the count of rows here; full unit-aware totals
        # belong to Phase D.
        rollups = {
            "inbound_count": len(incoming),
            "outbound_count": len(outgoing),
            "haul_cycles_count": len(haul_cycle_rows),
            "scale_ticket_count": scale_ticket_count,
            "loads_count": int(total_loads),
            "trucks_count": len(truck_ids),
            "materials_count": len(unique_materials),
            "net_lbs_from_tickets": round(proof_net_lbs_total, 2) if proof_net_lbs_present else None,
            "net_tons_from_tickets": _net_lbs_to_tons(proof_net_lbs_total) if proof_net_lbs_present else None,
        }

        proof_summary = {
            "scale_ticket_count": scale_ticket_count,
            "scale_ticket_net_lbs": round(proof_net_lbs_total, 2) if proof_net_lbs_present else None,
            "scale_ticket_net_tons": _net_lbs_to_tons(proof_net_lbs_total) if proof_net_lbs_present else None,
            "missing_proof_count": missing_proof_count,
            "matched_proof_count": matched_proof_count,
            "partial_proof_count": partial_proof_count,
        }

        # ── Verification status · virtual · no persistence.
        # Conservative classifier — when uncertain we choose `needs_review`,
        # never `verified`. Rules per Track 13.19 §3.
        has_any_activity = bool(
            dispatch_rows or incoming or outgoing
            or haul_cycle_rows or scale_ticket_proofs
        )
        if not has_any_activity:
            verification_status = "no_activity"
        elif not dispatch_rows and not scale_ticket_proofs and (incoming or outgoing):
            # Daily-report-only day · no MASCI dispatch · no proof.
            # Could be a legitimate third-party haul — not a defect, but
            # also not verified.
            verification_status = "needs_review"
        elif dispatch_rows and missing_proof_count == 0 and matched_proof_count > 0:
            verification_status = "verified"
        elif dispatch_rows and matched_proof_count > 0 and missing_proof_count > 0:
            verification_status = "partial"
        elif dispatch_rows and matched_proof_count == 0:
            verification_status = "missing_proof"
        else:
            verification_status = "needs_review"

        source_breakdown = {
            "daily_reports": len(incoming) + len(outgoing),
            "dispatch_assignments": len(dispatch_rows),
            "haul_cycles": len(haul_cycle_rows),
            "scale_tickets": scale_ticket_count,
            # ODR MaterialEvent · per Track 13.18 architecture this stays
            # a Supporting View. Phase A does not join ODR; the field is
            # exposed as 0 so consumers can rely on the key shape.
            "odr_events": 0,
            # FleetWatcher remains NOT_CONNECTED. Hard rule: never emit
            # a fake non-zero here.
            "fleetwatcher": 0,
        }

        return {
            # ── Existing (preserved verbatim) ──────────────────────
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
            # ── Track 13.19 · Phase A additive ─────────────────────
            "scale_ticket_proofs": scale_ticket_proofs,
            "haul_cycles": haul_cycle_rows,
            "proof_summary": proof_summary,
            "rollups": rollups,
            "verification_status": verification_status,
            "source_breakdown": source_breakdown,
        }


__all__ = ["register_material_movement_routes"]
