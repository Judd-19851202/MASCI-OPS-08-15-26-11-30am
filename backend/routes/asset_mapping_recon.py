"""
routes/asset_mapping_recon.py · MOTIVE-DATA-001 · Asset mapping
reconciliation foundation.

Closes the join gap between:
    dispatch_assignments.truck_id  ←→  asset_mappings.masci_equipment_id
                                   ←→  motive vehicle/asset id

Compute-on-read + queue-driven. Idempotent. Operator approves every link.
Never auto-links, never auto-dispatches, never writes to Motive, never
mutates daily_reports / dispatch_assignments / motive_events.

Storage: a new collection `asset_mapping_proposals` holds OPERATOR-FACING
proposal rows (status: Imported / Matched / Verified / Rejected). The
existing `asset_mappings.masci_equipment_id` is updated ONLY when the
operator approves a proposal.
"""
from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import Any, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

HIGH_CONF = 0.85
MED_CONF = 0.55


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _nid() -> str:
    return str(uuid.uuid4())


def _norm(s: Optional[str]) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


# ── Pure scorer (testable in isolation) ──────────────────────────────
def score_match(dispatch_asset: Dict[str, Any],
                motive_mapping: Dict[str, Any],
                equipment_master_row: Optional[Dict[str, Any]] = None
                ) -> Dict[str, Any]:
    """Score the likelihood that `motive_mapping` (asset_mappings row)
    is the Motive twin of `dispatch_asset` (containing truck_id, etc.).

    Priority signals (highest wins):
      1. Exact MASCI Equipment ID                 → 1.00
      2. Unit Number match                         → 0.93
      3. Truck Number match                        → 0.90
      4. Equipment Number match                    → 0.88
      5. VIN match                                 → 0.95
      6. Serial match                              → 0.85
      7. Fuzzy display-name                        → 0..1
    """
    truck_id = (dispatch_asset.get("truck_id") or "").strip()
    eq_id = (dispatch_asset.get("equipment_id") or "").strip()
    eq_label = (dispatch_asset.get("equipment_label") or "").strip()
    masci_eq = (motive_mapping.get("masci_equipment_id") or "").strip()
    m = motive_mapping.get("motive") or {}
    mot_vin = (m.get("vin") or "").strip()
    mot_name = (m.get("name") or "").strip()
    mot_year = str(m.get("year") or "").strip()
    mot_make = str(m.get("make") or "").strip()
    mot_model = str(m.get("model") or "").strip()
    em = equipment_master_row or {}
    em_label = (em.get("display_label") or "").strip()
    em_vin = (em.get("vin") or "").strip()
    em_serial = (em.get("serial") or em.get("serial_number") or "").strip()
    em_unit = (em.get("unit_number") or em.get("unit_label") or "").strip()
    em_truck = (em.get("truck_number") or "").strip()

    signals: List[Dict[str, Any]] = []

    # 1. Exact MASCI equipment id
    if masci_eq and (masci_eq == truck_id or masci_eq == eq_id):
        signals.append({"score": 1.0, "kind": "masci_id_exact",
                        "evidence": f"masci_equipment_id={masci_eq}"})

    # 5. VIN
    if mot_vin and (mot_vin == em_vin or mot_vin == truck_id):
        signals.append({"score": 0.95, "kind": "vin",
                        "evidence": f"VIN {mot_vin}"})

    # 2. Unit number
    if em_unit and em_unit.upper() in (truck_id.upper(), eq_id.upper(), eq_label.upper()):
        signals.append({"score": 0.93, "kind": "unit_number",
                        "evidence": f"unit {em_unit}"})

    # 3. Truck number
    if em_truck and em_truck.upper() in (truck_id.upper(), eq_id.upper()):
        signals.append({"score": 0.90, "kind": "truck_number",
                        "evidence": f"truck {em_truck}"})

    # 4. Equipment number (em.asset_id often equals truck_id)
    em_aid = (em.get("asset_id") or "").strip()
    if em_aid and em_aid in (truck_id, eq_id):
        signals.append({"score": 0.88, "kind": "equipment_number",
                        "evidence": f"asset_id {em_aid}"})

    # 6. Serial
    if em_serial and em_serial.upper() in (truck_id.upper(), eq_id.upper(), eq_label.upper()):
        signals.append({"score": 0.85, "kind": "serial",
                        "evidence": f"serial {em_serial}"})

    # 7. Fuzzy
    label_target = _norm(em_label or eq_label)
    label_motive = _norm(mot_name or " ".join([mot_year, mot_make, mot_model]).strip())
    if label_target and label_motive:
        ratio = SequenceMatcher(None, label_target, label_motive).ratio()
        if ratio > 0:
            signals.append({"score": round(ratio, 3), "kind": "fuzzy_name",
                            "evidence": f"sim {ratio:.2f}"})

    if not signals:
        return {"score": 0.0, "band": "UNKNOWN", "best_signal": None,
                "all_signals": []}

    best = max(signals, key=lambda s: s["score"])
    score = float(best["score"])
    band = ("HIGH" if score >= HIGH_CONF
            else "MEDIUM" if score >= MED_CONF
            else "LOW")
    return {"score": round(score, 3), "band": band,
            "best_signal": best, "all_signals": signals}


# ── Pydantic ─────────────────────────────────────────────────────────
class ReassignBody(BaseModel):
    motive_mapping_id: str = Field(..., min_length=1)


class BulkApproveBody(BaseModel):
    ids: List[str] = Field(default_factory=list)


# ── Router builder ───────────────────────────────────────────────────
def build_asset_mapping_router(db, require_admin_dep: Callable) -> APIRouter:
    router = APIRouter(prefix="/api", tags=["asset-mapping"])

    async def _ensure_indexes():
        try:
            await db.asset_mapping_proposals.create_index("truck_id", sparse=True)
            await db.asset_mapping_proposals.create_index("motive_mapping_id", sparse=True)
            await db.asset_mapping_proposals.create_index("status")
            await db.asset_mapping_proposals.create_index("confidence_band")
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[motive-data-001] index err: {e}")

    # ── Scan: build proposals for every distinct unmapped truck_id ───
    @router.post("/admin/asset-mapping/scan",
                 dependencies=[Depends(require_admin_dep)])
    async def scan():
        """For every distinct dispatch truck_id WITHOUT a current
        motive mapping link, compute the best motive-mapping proposal.
        Idempotent: re-running the same scan produces the same set of
        proposal docs (keyed by truck_id)."""
        await _ensure_indexes()
        # 1. Distinct dispatch trucks
        trucks = [t for t in (await db.dispatch_assignments.distinct("truck_id")) if t]
        # 2. Load all asset_mappings + a sample of equipment_master
        mappings: List[Dict[str, Any]] = []
        async for m in db.asset_mappings.find({"provider": "motive"}):
            m.pop("_id", None)
            mappings.append(m)
        em_by_label: Dict[str, Dict[str, Any]] = {}
        em_by_aid: Dict[str, Dict[str, Any]] = {}
        async for em in db.equipment_master.find({}):
            em.pop("_id", None)
            lbl = (em.get("display_label") or "").strip().upper()
            if lbl:
                em_by_label.setdefault(lbl, em)
            aid = (em.get("asset_id") or "").strip()
            if aid:
                em_by_aid.setdefault(aid, em)

        scanned, upserted = 0, 0
        bands = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNKNOWN": 0}
        for truck in trucks:
            scanned += 1
            em_row = em_by_aid.get(truck) or em_by_label.get(truck.upper())
            # Find the best motive_mapping
            best_score, best = 0.0, None
            for m in mappings:
                out = score_match({"truck_id": truck}, m, em_row)
                if out["score"] > best_score:
                    best_score, best = out["score"], (m, out)
            if best:
                m, out = best
                bands[out["band"]] += 1
                proposal = {
                    "id": _nid(),
                    "truck_id": truck,
                    "motive_mapping_id": m.get("id"),
                    "motive_vehicle_id": (m.get("motive") or {}).get("vehicle_id"),
                    "motive_asset_id":   (m.get("motive") or {}).get("asset_id"),
                    "motive_label": " ".join(
                        [str(x).strip() for x in [
                            (m.get("motive") or {}).get("year"),
                            (m.get("motive") or {}).get("make"),
                            (m.get("motive") or {}).get("model"),
                            (m.get("motive") or {}).get("name"),
                        ] if x]
                    ).strip() or "(motive asset)",
                    "equipment_master_label": (em_row or {}).get("display_label"),
                    "confidence_score": out["score"],
                    "confidence_band": out["band"],
                    "match_signal": out["best_signal"],
                    "status": "Matched" if out["score"] > 0 else "Imported",
                    "active": True,
                    "created_at": _now(), "updated_at": _now(),
                }
                # Idempotency: upsert on (truck_id) — keep status if Verified/Rejected.
                existing = await db.asset_mapping_proposals.find_one(
                    {"truck_id": truck}
                )
                if existing and existing.get("status") in ("Verified", "Rejected"):
                    continue
                if existing:
                    await db.asset_mapping_proposals.update_one(
                        {"id": existing["id"]},
                        {"$set": {**proposal, "id": existing["id"],
                                  "created_at": existing.get("created_at")}},
                    )
                else:
                    await db.asset_mapping_proposals.insert_one(proposal)
                upserted += 1
            else:
                bands["UNKNOWN"] += 1

        return {"ok": True, "trucks_scanned": scanned, "upserted": upserted,
                "bands": bands, "motive_mappings_considered": len(mappings)}

    # ── Queue ─────────────────────────────────────────────────────────
    @router.get("/admin/asset-mapping/queue",
                dependencies=[Depends(require_admin_dep)])
    async def queue(band: Optional[str] = Query(default=None,
                                                  regex="^(HIGH|MEDIUM|LOW|UNKNOWN)$"),
                    status: Optional[str] = None):
        q: Dict[str, Any] = {}
        if band:
            q["confidence_band"] = band
        if status:
            q["status"] = status
        rows: List[Dict[str, Any]] = []
        async for r in db.asset_mapping_proposals.find(q).sort(
            [("confidence_score", -1)]
        ):
            r.pop("_id", None)
            rows.append(r)
        # Sidecar counts
        counts = {b: 0 for b in ("HIGH", "MEDIUM", "LOW", "UNKNOWN",
                                  "VERIFIED", "REJECTED", "TOTAL")}
        async for r in db.asset_mapping_proposals.find({}):
            counts["TOTAL"] += 1
            if r.get("status") == "Verified":
                counts["VERIFIED"] += 1
            elif r.get("status") == "Rejected":
                counts["REJECTED"] += 1
            elif r.get("confidence_band") in counts:
                counts[r["confidence_band"]] += 1
        return {"ok": True, "rows": rows, "counts": counts}

    # ── Approve / Reject / Reassign / Bulk-Approve ───────────────────
    async def _commit_approval(proposal: Dict[str, Any]) -> None:
        """Move the link into asset_mappings.masci_equipment_id."""
        mm_id = proposal.get("motive_mapping_id")
        truck = proposal.get("truck_id") or ""
        if not mm_id or not truck:
            return
        await db.asset_mappings.update_one(
            {"id": mm_id},
            {"$set": {"masci_equipment_id": truck, "updated_at": _now()}},
        )

    @router.post("/admin/asset-mapping/{prop_id}/approve",
                 dependencies=[Depends(require_admin_dep)])
    async def approve(prop_id: str):
        p = await db.asset_mapping_proposals.find_one({"id": prop_id})
        if not p:
            raise HTTPException(404, "Proposal not found")
        await _commit_approval(p)
        await db.asset_mapping_proposals.update_one(
            {"id": prop_id},
            {"$set": {"status": "Verified", "verified_at": _now(),
                      "verified_by": "admin", "updated_at": _now()}},
        )
        return {"ok": True, "id": prop_id, "status": "Verified"}

    @router.post("/admin/asset-mapping/{prop_id}/reject",
                 dependencies=[Depends(require_admin_dep)])
    async def reject(prop_id: str):
        p = await db.asset_mapping_proposals.find_one({"id": prop_id})
        if not p:
            raise HTTPException(404, "Proposal not found")
        await db.asset_mapping_proposals.update_one(
            {"id": prop_id},
            {"$set": {"status": "Rejected", "verified_at": _now(),
                      "verified_by": "admin", "updated_at": _now()}},
        )
        return {"ok": True, "id": prop_id, "status": "Rejected"}

    @router.post("/admin/asset-mapping/{prop_id}/reassign",
                 dependencies=[Depends(require_admin_dep)])
    async def reassign(prop_id: str, body: ReassignBody):
        p = await db.asset_mapping_proposals.find_one({"id": prop_id})
        if not p:
            raise HTTPException(404, "Proposal not found")
        m = await db.asset_mappings.find_one({"id": body.motive_mapping_id})
        if not m:
            raise HTTPException(400, f"Unknown motive_mapping_id {body.motive_mapping_id!r}")
        # Apply: link this dispatch.truck_id onto the chosen motive mapping
        await db.asset_mappings.update_one(
            {"id": body.motive_mapping_id},
            {"$set": {"masci_equipment_id": p["truck_id"], "updated_at": _now()}},
        )
        await db.asset_mapping_proposals.update_one(
            {"id": prop_id},
            {"$set": {"motive_mapping_id": body.motive_mapping_id,
                      "status": "Verified", "verified_at": _now(),
                      "verified_by": "admin",
                      "match_signal": {"score": 1.0, "kind": "manual",
                                       "evidence": "manually reassigned"},
                      "confidence_score": 1.0, "confidence_band": "HIGH",
                      "updated_at": _now()}},
        )
        return {"ok": True, "id": prop_id, "status": "Verified"}

    @router.post("/admin/asset-mapping/bulk-approve",
                 dependencies=[Depends(require_admin_dep)])
    async def bulk_approve(body: BulkApproveBody):
        approved, skipped = [], []
        for pid in body.ids:
            p = await db.asset_mapping_proposals.find_one({"id": pid})
            if not p:
                skipped.append({"id": pid, "reason": "not_found"})
                continue
            if float(p.get("confidence_score") or 0) < HIGH_CONF:
                skipped.append({"id": pid, "reason": "below_high_confidence",
                                "score": p.get("confidence_score")})
                continue
            await _commit_approval(p)
            await db.asset_mapping_proposals.update_one(
                {"id": pid},
                {"$set": {"status": "Verified", "verified_at": _now(),
                          "verified_by": "admin-bulk", "updated_at": _now()}},
            )
            approved.append({"id": pid, "truck_id": p.get("truck_id")})
        return {"ok": True, "approved_count": len(approved),
                "skipped_count": len(skipped),
                "approved": approved, "skipped": skipped}

    # ── Coverage tile (MOTIVE-DATA-001E) ──────────────────────────────
    @router.get("/admin/asset-mapping/coverage",
                dependencies=[Depends(require_admin_dep)])
    async def coverage():
        # Total distinct dispatch trucks
        trucks = [t for t in (await db.dispatch_assignments.distinct("truck_id")) if t]
        total = len(trucks)
        # Mapped = trucks where any asset_mappings row has masci_equipment_id == truck
        mapped_set = set()
        async for m in db.asset_mappings.find(
            {"masci_equipment_id": {"$nin": [None, ""]}},
            {"masci_equipment_id": 1}
        ):
            mapped_set.add(m["masci_equipment_id"])
        mapped = sum(1 for t in trucks if t in mapped_set)
        unmapped = total - mapped
        pct = round(100.0 * mapped / max(1, total), 1)
        return {"ok": True,
                "total_dispatch_trucks": total,
                "mapped_assets": mapped,
                "unmapped_assets": unmapped,
                "coverage_pct": pct}

    # ── Audit (MOTIVE-DATA-001G) ──────────────────────────────────────
    @router.get("/admin/asset-mapping/audit",
                dependencies=[Depends(require_admin_dep)])
    async def audit():
        trucks = [t for t in (await db.dispatch_assignments.distinct("truck_id")) if t]
        total_dispatch = len(trucks)
        total_motive = await db.asset_mappings.count_documents({"provider": "motive"})
        mapped_set = set()
        async for m in db.asset_mappings.find(
            {"masci_equipment_id": {"$nin": [None, ""]}},
            {"masci_equipment_id": 1}
        ):
            mapped_set.add(m["masci_equipment_id"])
        mapped = sum(1 for t in trucks if t in mapped_set)
        unmapped = total_dispatch - mapped
        # Duplicates: motive mappings that share the same masci_equipment_id
        dup_pipe = [{"$match": {"masci_equipment_id": {"$nin": [None, ""]}}},
                    {"$group": {"_id": "$masci_equipment_id", "n": {"$sum": 1}}},
                    {"$match": {"n": {"$gt": 1}}}]
        dups = await db.asset_mappings.aggregate(dup_pipe).to_list(100)
        # Conflicts: a truck that has > 1 proposal in queue Verified
        conf_pipe = [{"$match": {"status": "Verified"}},
                     {"$group": {"_id": "$truck_id", "n": {"$sum": 1}}},
                     {"$match": {"n": {"$gt": 1}}}]
        conflicts = await db.asset_mapping_proposals.aggregate(conf_pipe).to_list(100)
        # Top 5 risk gaps: unmapped trucks with most active dispatches
        risk_pipe = [
            {"$match": {"current_state": {"$nin": ["COMPLETE", "CANCELLED", "CANCELED"]},
                        "truck_id": {"$nin": [None, ""]}}},
            {"$group": {"_id": "$truck_id", "n": {"$sum": 1}}},
            {"$sort": {"n": -1}},
            {"$limit": 5},
        ]
        risks = await db.dispatch_assignments.aggregate(risk_pipe).to_list(5)
        risks = [{"truck_id": r["_id"], "active_dispatches": r["n"]}
                 for r in risks if r["_id"] not in mapped_set]
        # Estimated trust improvement: if all currently-Matched HIGH proposals
        # got approved → projected coverage
        high_pending = await db.asset_mapping_proposals.count_documents(
            {"confidence_band": "HIGH", "status": "Matched"}
        )
        projected_mapped = mapped + high_pending
        projected_pct = round(100.0 * projected_mapped / max(1, total_dispatch), 1)
        return {"ok": True, "answers": {
            "q1_total_dispatch_assets":  total_dispatch,
            "q2_total_motive_assets":    total_motive,
            "q3_total_mapped":           mapped,
            "q4_total_unmapped":         unmapped,
            "q5_total_duplicates":       len(dups),
            "q6_total_conflicts":        len(conflicts),
            "q7_coverage_pct":           round(100.0 * mapped / max(1, total_dispatch), 1),
            "q8_verification_unlock_pct": projected_pct,
            "q9_highest_risk_gaps":      risks,
            "q10_estimated_trust_improvement_pct": projected_pct - round(100.0 * mapped / max(1, total_dispatch), 1),
            "duplicates_sample": [{"masci_equipment_id": d["_id"], "n": d["n"]} for d in dups[:5]],
            "high_pending_proposals":    high_pending,
        }}

    # ── Top-N unmapped (002C) ─────────────────────────────────────────
    @router.get("/admin/asset-mapping/top-unmapped",
                dependencies=[Depends(require_admin_dep)])
    async def top_unmapped(limit: int = Query(default=10, ge=1, le=50)):
        # Active dispatch volume per truck, only those without masci link
        mapped_set = set()
        async for m in db.asset_mappings.find(
            {"masci_equipment_id": {"$nin": [None, ""]}},
            {"masci_equipment_id": 1}
        ):
            mapped_set.add(m["masci_equipment_id"])
        pipe = [
            {"$match": {"current_state": {"$nin": ["COMPLETE", "CANCELLED", "CANCELED"]},
                        "truck_id": {"$nin": [None, ""]}}},
            {"$group": {"_id": "$truck_id", "n": {"$sum": 1}}},
            {"$sort": {"n": -1}},
            {"$limit": 200},
        ]
        rows: List[Dict[str, Any]] = []
        async for r in db.dispatch_assignments.aggregate(pipe):
            tid = r["_id"]
            if tid in mapped_set:
                continue
            prop = await db.asset_mapping_proposals.find_one(
                {"truck_id": tid, "status": {"$ne": "Rejected"}}
            )
            rows.append({
                "truck_id": tid,
                "active_dispatch_count": r["n"],
                "suggested_match": (prop or {}).get("motive_label"),
                "confidence_band":  (prop or {}).get("confidence_band") or "UNKNOWN",
                "confidence_score": (prop or {}).get("confidence_score") or 0,
                "proposal_id":      (prop or {}).get("id"),
                "estimated_verification_gain_dispatches": r["n"],
            })
            if len(rows) >= limit:
                break
        return {"ok": True, "rows": rows, "limit": limit}

    # ── Impact preview (002E) ─────────────────────────────────────────
    @router.get("/admin/asset-mapping/impact-preview/{prop_id}",
                dependencies=[Depends(require_admin_dep)])
    async def impact_preview(prop_id: str):
        p = await db.asset_mapping_proposals.find_one({"id": prop_id}, {"_id": 0})
        if not p:
            raise HTTPException(404, "Proposal not found")
        # Currently — count of active dispatches affected by approving this
        affected = await db.dispatch_assignments.count_documents({
            "truck_id": p.get("truck_id"),
            "current_state": {"$nin": ["COMPLETE", "CANCELLED", "CANCELED"]},
        })
        return {"ok": True, "proposal_id": prop_id,
                "truck_id": p.get("truck_id"),
                "affected_active_dispatches": affected,
                "current_state": "pending_to_confirm",
                "after_approval_state":
                    f"+{affected} dispatches now eligible for CONFIRMED on next M-2 materialize"}

    # ── Operational Impact (MOTIVE-DATA-003) ──────────────────────────
    @router.get("/admin/asset-mapping/operational-impact",
                dependencies=[Depends(require_admin_dep)])
    async def operational_impact():
        """Aggregate read-only rollup for the Operational Impact Command
        Card. Pure derivation across coverage, queue, and verification
        signals — zero writes, zero new collections, zero workflow changes.
        """
        # Distinct dispatch trucks + currently-mapped set
        trucks = [t for t in (await db.dispatch_assignments.distinct("truck_id")) if t]
        total = len(trucks)
        mapped_set: set = set()
        async for m in db.asset_mappings.find(
            {"masci_equipment_id": {"$nin": [None, ""]}},
            {"masci_equipment_id": 1}
        ):
            mapped_set.add(m["masci_equipment_id"])
        mapped = sum(1 for t in trucks if t in mapped_set)
        unmapped = total - mapped
        cur_cov_pct = round(100.0 * mapped / max(1, total), 1)

        # HIGH-confidence proposals waiting (the operator action queue)
        high_props: List[Dict[str, Any]] = []
        async for p in db.asset_mapping_proposals.find(
            {"confidence_band": "HIGH", "status": "Matched"}
        ):
            p.pop("_id", None)
            high_props.append(p)
        high_waiting = len(high_props)

        # Sum of active dispatches impacted by approving those HIGH proposals
        high_truck_ids = [p.get("truck_id") for p in high_props if p.get("truck_id")]
        impacted = 0
        if high_truck_ids:
            impacted = await db.dispatch_assignments.count_documents({
                "truck_id": {"$in": high_truck_ids},
                "current_state": {"$nin": ["COMPLETE", "CANCELLED", "CANCELED"]},
            })

        # Projected state if every HIGH proposal were approved
        projected_mapped = mapped + high_waiting
        projected_unmapped = max(0, total - projected_mapped)
        projected_cov_pct = round(100.0 * projected_mapped / max(1, total), 1)

        # Trust score (current + potential) — same derivation VER-1 / 002G use
        verified_disp = 0
        considered = 0
        async for d in db.dispatch_assignments.find({
            "current_state": {"$nin": ["COMPLETE", "CANCELLED", "CANCELED"]}
        }).limit(500):
            considered += 1
            mm = await db.asset_mappings.find_one(
                {"masci_equipment_id": d.get("truck_id"), "provider": "motive"}
            )
            if not mm:
                continue
            mot = mm.get("motive") or {}
            actor_key = (f"vehicle:{mot.get('vehicle_id')}"
                         if mm.get("asset_kind") == "vehicle" and mot.get("vehicle_id")
                         else f"equipment:{mot.get('asset_id')}"
                         if mot.get("asset_id") else None)
            if not actor_key:
                continue
            if await db.operational_events.find_one({
                "asset_key": actor_key,
                "project_number": d.get("project_number") or "",
                "location_type": "JOB",
            }):
                verified_disp += 1
        cur_trust_pct = round(100.0 * verified_disp / max(1, considered), 1)
        # Potential = projected verifiable assignments / considered
        potential_trust_pct = round(
            100.0 * (verified_disp + projected_unmapped) / max(1, considered), 1
        )

        # Readiness banner (strict rules per directive)
        if cur_cov_pct >= 75.0 and high_waiting == 0:
            readiness = "READY_FOR_ACTIVATION"
            readiness_reason = f"Coverage {cur_cov_pct}% ≥ 75% · HIGH queue empty"
        elif cur_cov_pct > 25.0:
            readiness = "PARTIALLY_READY"
            readiness_reason = (f"Coverage {cur_cov_pct}% · "
                                f"{high_waiting} HIGH match(es) waiting")
        else:
            readiness = "NOT_READY"
            readiness_reason = (f"Coverage {cur_cov_pct}% < 25% · "
                                f"{high_waiting} HIGH match(es) waiting · "
                                f"{unmapped} unmapped truck(s)")

        return {
            "ok": True,
            "current": {
                "trust_score_pct":      cur_trust_pct,
                "coverage_pct":         cur_cov_pct,
                "mapped_assets":        mapped,
                "unmapped_assets":      unmapped,
                "total_dispatch_trucks": total,
            },
            "potential": {
                "trust_score_pct":      potential_trust_pct,
                "coverage_pct":         projected_cov_pct,
                "mapped_assets":        projected_mapped,
                "unmapped_assets":      projected_unmapped,
            },
            "actions": {
                "high_confidence_waiting":         high_waiting,
                "estimated_dispatches_impacted":   impacted,
                "estimated_assets_confirmed":      high_waiting,
            },
            "readiness":        readiness,
            "readiness_reason": readiness_reason,
            "runbook_path":     "/app/memory/MOTIVE_DAY1_ACTIVATION_RUNBOOK.md",
        }

    # ── Executive summary (002G) ──────────────────────────────────────
    @router.get("/admin/executive-summary",
                dependencies=[Depends(require_admin_dep)])
    async def executive_summary():
        # Projects verified / pending
        proj_verified = await db.operational_locations.count_documents(
            {"location_type": "JOB", "geocode_status": "Verified"}
        )
        proj_pending = await db.operational_locations.count_documents(
            {"location_type": "JOB", "geocode_status": "Matched"}
        )
        # Mapping coverage
        trucks = [t for t in (await db.dispatch_assignments.distinct("truck_id")) if t]
        total = len(trucks)
        mapped_set = set()
        async for m in db.asset_mappings.find(
            {"masci_equipment_id": {"$nin": [None, ""]}},
            {"masci_equipment_id": 1}
        ):
            mapped_set.add(m["masci_equipment_id"])
        mapped = sum(1 for t in trucks if t in mapped_set)
        unmapped = total - mapped
        coverage_pct = round(100.0 * mapped / max(1, total), 1)

        # Trust score from VER-1 (re-derive a quick scan)
        verified_disp = 0
        considered = 0
        async for d in db.dispatch_assignments.find({
            "current_state": {"$nin": ["COMPLETE", "CANCELLED", "CANCELED"]}
        }).limit(500):
            considered += 1
            mm = await db.asset_mappings.find_one(
                {"masci_equipment_id": d.get("truck_id"), "provider": "motive"}
            )
            if not mm:
                continue
            mot = mm.get("motive") or {}
            actor_key = (f"vehicle:{mot.get('vehicle_id')}"
                         if mm.get("asset_kind") == "vehicle" and mot.get("vehicle_id")
                         else f"equipment:{mot.get('asset_id')}"
                         if mot.get("asset_id") else None)
            if not actor_key:
                continue
            if await db.operational_events.find_one({
                "asset_key": actor_key,
                "project_number": d.get("project_number") or "",
                "location_type": "JOB",
            }):
                verified_disp += 1
        trust_pct = round(100.0 * verified_disp / max(1, considered), 1)
        # Potential trust if all top unmapped were approved AND telemetry caught up
        potential_pct = round(100.0 * (verified_disp + unmapped) / max(1, considered), 1)
        # Top 3 risk gaps via the existing pipe
        pipe = [
            {"$match": {"current_state": {"$nin": ["COMPLETE", "CANCELLED", "CANCELED"]},
                        "truck_id": {"$nin": [None, ""]}}},
            {"$group": {"_id": "$truck_id", "n": {"$sum": 1}}},
            {"$sort": {"n": -1}},
            {"$limit": 10},
        ]
        risks = []
        async for r in db.dispatch_assignments.aggregate(pipe):
            if r["_id"] not in mapped_set:
                risks.append({"truck_id": r["_id"], "active_dispatches": r["n"]})
        return {"ok": True,
                "projects_verified":  proj_verified,
                "projects_pending":   proj_pending,
                "mapped_assets":      mapped,
                "unmapped_assets":    unmapped,
                "coverage_pct":       coverage_pct,
                "trust_score_pct":    trust_pct,
                "potential_trust_score_pct": potential_pct,
                "highest_risk_gaps":  risks[:5],
                "top_opportunities":  risks[:3]}

    return router


__all__ = ["build_asset_mapping_router", "score_match", "HIGH_CONF", "MED_CONF"]
