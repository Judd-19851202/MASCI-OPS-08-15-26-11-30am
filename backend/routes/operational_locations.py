"""
routes/operational_locations.py · M-3 · Geocode Foundation.

Canonical operational location registry that links MASCI jobs with Motive
geofences (and, in the future, plants, pits, yards, shops, disposal sites,
vendors). Read-only against Motive — never pushes back.

Doctrine: MOTIVE_001_CONSTITUTIONAL_AUDIT.md §D + MOTIVE_INTEGRATION_STRATEGY.md.
Boundaries:
  • No automatic project assignment — operator approves every match.
  • No writes to Motive.
  • No writes into daily_reports, material_movement, dispatch_*.
  • No notifications, no OA events.
  • Motive remains source of truth for *geofences*; MASCI remains source of
    truth for *operational location identity* (which job/plant/yard a
    geofence belongs to).

Collection: `operational_locations`

Mounted at /api/admin/locations/* — X-Admin-Token gated.
"""
from __future__ import annotations

import logging
import math
import re
import uuid
from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import Any, Callable, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

LOCATION_TYPES = {
    "JOB", "ASPHALT_PLANT", "CONCRETE_PLANT", "PIT",
    "YARD", "SHOP", "DISPOSAL_SITE", "VENDOR",
}

# Geocode lifecycle. `Verified` is the trusted state.
GEOCODE_STATUSES = {
    "Not Geocoded", "Imported", "Matched", "Verified", "Rejected",
}

# Confidence bands (per M-3 brief §M3-3).
HIGH_CONFIDENCE = 0.85
MEDIUM_CONFIDENCE = 0.55


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return str(uuid.uuid4())


# ──────────────────────────────────────────────────────────────────────
# Geometry helpers (polygon centroid + max-radius)
# ──────────────────────────────────────────────────────────────────────
def _polygon_centroid(points: List[Dict[str, float]]) -> Optional[Dict[str, float]]:
    """Average centroid of a polygon. Returns None if no usable points."""
    if not points:
        return None
    lats, lons = [], []
    for p in points:
        try:
            la = float(p.get("lat"))
            lo = float(p.get("lon"))
        except (TypeError, ValueError):
            continue
        lats.append(la)
        lons.append(lo)
    if not lats:
        return None
    return {"lat": sum(lats) / len(lats), "lon": sum(lons) / len(lons)}


def _haversine_ft(a: Dict[str, float], b: Dict[str, float]) -> float:
    """Distance between two lat/lon points in FEET."""
    r_earth_m = 6_371_000.0
    la1, lo1 = math.radians(a["lat"]), math.radians(a["lon"])
    la2, lo2 = math.radians(b["lat"]), math.radians(b["lon"])
    dl = lo2 - lo1
    dp = la2 - la1
    h = math.sin(dp / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin(dl / 2) ** 2
    meters = 2 * r_earth_m * math.asin(min(1.0, math.sqrt(h)))
    return meters * 3.28084


def _polygon_radius_ft(points: List[Dict[str, float]], centroid: Dict[str, float]) -> int:
    """Conservative geofence radius (ft) = max distance from centroid to
    any polygon vertex. Defaults to 250 ft per doctrine if undef."""
    if not centroid or not points:
        return 250
    m = 0.0
    for p in points:
        try:
            d = _haversine_ft(centroid, {"lat": float(p["lat"]), "lon": float(p["lon"])})
            if d > m:
                m = d
        except (TypeError, ValueError, KeyError):
            continue
    return int(round(m)) if m > 0 else 250


# ──────────────────────────────────────────────────────────────────────
# Reconciliation scoring
# ──────────────────────────────────────────────────────────────────────
_PROJECT_NUM_RE = re.compile(r"\b(\d{2}-\d{2}(?:\s*-\s*CP)?)\b", re.IGNORECASE)
_T_NUM_RE = re.compile(r"\b(T\d{4})\b", re.IGNORECASE)
_HWY_RE = re.compile(r"\b(SR\s?\d+|I-?\d+|US\s?\d+|CR\s?\d+)\b", re.IGNORECASE)


def _norm(s: Optional[str]) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def _extract_project_keys(text: str) -> Dict[str, List[str]]:
    """Pull out structural identifiers we can match on."""
    t = text or ""
    return {
        "project_numbers": [m.group(1).upper().replace(" ", "")
                            for m in _PROJECT_NUM_RE.finditer(t)],
        "t_numbers": [m.group(1).upper() for m in _T_NUM_RE.finditer(t)],
        "highways": [re.sub(r"\s+", "", m.group(1).upper())
                     for m in _HWY_RE.finditer(t)],
    }


def _score_match(job: Dict[str, Any], geofence: Dict[str, Any]) -> Dict[str, Any]:
    """Score how confident we are that ``geofence`` represents ``job``.

    Signals (highest of):
      1. Direct project_number in fence name           → 0.95
      2. T-number from project_name in fence name      → 0.92
      3. Highway + location substring match            → 0.85
      4. Token-set fuzzy of project_name vs fence name → SequenceMatcher
    """
    fence_name = (geofence.get("name") or "").strip()
    fence_addr = (geofence.get("address") or "").strip()
    fence_text = _norm(f"{fence_name} {fence_addr}")

    job_pn = (job.get("project_number") or "").strip().upper().replace(" ", "")
    job_pname = (job.get("project_name") or "").strip()
    job_loc = (job.get("location") or "").strip()
    job_text = _norm(f"{job_pn} {job_pname} {job_loc}")

    job_keys = _extract_project_keys(f"{job_pn} {job_pname} {job_loc}")
    fence_keys = _extract_project_keys(f"{fence_name} {fence_addr}")

    signals: List[Dict[str, Any]] = []

    # 1. Direct project_number match
    if job_pn and job_pn in [p.replace(" ", "") for p in fence_keys["project_numbers"]]:
        signals.append({"score": 0.95, "kind": "project_number",
                        "evidence": f"'{job_pn}' present in fence name"})

    # 2. T-number from project_name appears in fence name
    common_tnums = set(job_keys["t_numbers"]) & set(fence_keys["t_numbers"])
    if common_tnums:
        signals.append({"score": 0.92, "kind": "t_number",
                        "evidence": f"T-number {sorted(common_tnums)[0]} shared"})

    # 3. Highway + location token overlap (e.g., SR46 + Mellonville)
    common_hwy = set(job_keys["highways"]) & set(fence_keys["highways"])
    if common_hwy:
        # Bonus: does any non-highway location token also appear?
        loc_tokens = [w for w in _norm(job_loc).split()
                      if len(w) >= 4 and not _HWY_RE.match(w)]
        loc_in_fence = any(w in fence_text for w in loc_tokens)
        if loc_in_fence:
            signals.append({"score": 0.85, "kind": "highway+place",
                            "evidence": f"hwy={sorted(common_hwy)[0]} + place token match"})
        else:
            signals.append({"score": 0.70, "kind": "highway",
                            "evidence": f"hwy={sorted(common_hwy)[0]} only"})

    # 4. Fuzzy fallback on full text
    fuzzy = SequenceMatcher(None, job_text, fence_text).ratio()
    if fuzzy > 0:
        signals.append({"score": round(fuzzy, 3), "kind": "fuzzy",
                        "evidence": f"text similarity {round(fuzzy, 3)}"})

    if not signals:
        return {"score": 0.0, "band": "low", "signals": []}

    best = max(signals, key=lambda s: s["score"])
    score = float(best["score"])
    band = ("high" if score >= HIGH_CONFIDENCE
            else "medium" if score >= MEDIUM_CONFIDENCE
            else "low")
    return {"score": round(score, 3), "band": band,
            "best_signal": best, "all_signals": signals}


# ──────────────────────────────────────────────────────────────────────
# Pydantic models
# ──────────────────────────────────────────────────────────────────────
class ApproveBody(BaseModel):
    pass  # reserved


class ReassignBody(BaseModel):
    project_number: str = Field(..., min_length=1, max_length=64)


class BulkApproveBody(BaseModel):
    ids: List[str] = Field(default_factory=list)


# ──────────────────────────────────────────────────────────────────────
# Router builder
# ──────────────────────────────────────────────────────────────────────
def build_operational_locations_router(db, require_admin_dep: Callable) -> APIRouter:
    """Build the M-3 operational locations router.

    Mounted at /api/admin/locations/* — X-Admin-Token gated.
    """
    router = APIRouter(prefix="/api", tags=["operational-locations"])

    async def _ensure_indexes():
        try:
            await db.operational_locations.create_index("motive_geofence_id", unique=False, sparse=True)
            await db.operational_locations.create_index("project_number", sparse=True)
            await db.operational_locations.create_index("location_type")
            await db.operational_locations.create_index("geocode_status")
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[m3 indexes] {e}")

    # ── M3-2 · Import existing Motive geofences (read-only) ───────────
    @router.post("/admin/locations/import-geofences",
                 dependencies=[Depends(require_admin_dep)])
    async def import_geofences(
        location_type: str = Query(default="JOB",
                                   description="The location_type to assign on import "
                                               "(M-3 ships only with JOB seeding)."),
    ):
        """Pull existing rows out of `motive_geofences` (read-only) and seed
        `operational_locations`. Idempotent on motive_geofence_id. NEVER
        calls Motive's API directly — relies on the existing sync."""
        if location_type not in LOCATION_TYPES:
            raise HTTPException(400, f"Unknown location_type: {location_type}")
        await _ensure_indexes()

        imported, skipped, updated = 0, 0, 0
        async for g in db.motive_geofences.find({}):
            gid = (g.get("motive_geofence_id") or "").strip()
            if not gid:
                continue
            centroid = _polygon_centroid(g.get("location_points") or [])
            radius = _polygon_radius_ft(g.get("location_points") or [], centroid or {})

            existing = await db.operational_locations.find_one({"motive_geofence_id": gid})
            if existing:
                patch = {
                    "name": existing.get("name") or g.get("name"),
                    "address": existing.get("address") or g.get("address") or "",
                    "latitude": (centroid or {}).get("lat") or existing.get("latitude"),
                    "longitude": (centroid or {}).get("lon") or existing.get("longitude"),
                    "geofence_radius": radius if radius else existing.get("geofence_radius"),
                    "motive_category": g.get("category") or "",
                    "motive_status": g.get("status") or "",
                    "updated_at": _now(),
                }
                await db.operational_locations.update_one(
                    {"id": existing["id"]}, {"$set": patch}
                )
                updated += 1
                continue

            # Heuristic: respect Motive's category to choose the location_type.
            cat = (g.get("category") or "").lower()
            inferred_type = location_type
            if "yard" in cat or "terminal" in cat:
                inferred_type = "YARD"
            elif "maintenance" in cat or "shop" in cat:
                inferred_type = "SHOP"
            elif "plant" in cat and "asphalt" in cat:
                inferred_type = "ASPHALT_PLANT"
            elif "plant" in cat and "concrete" in cat:
                inferred_type = "CONCRETE_PLANT"
            elif "plant" in cat:
                inferred_type = "ASPHALT_PLANT"
            elif "pit" in cat:
                inferred_type = "PIT"
            elif "disposal" in cat or "dump" in cat:
                inferred_type = "DISPOSAL_SITE"

            doc = {
                "id": _new_id(),
                "location_type": inferred_type,
                "name": (g.get("name") or "").strip(),
                "address": (g.get("address") or "").strip(),
                "latitude": (centroid or {}).get("lat"),
                "longitude": (centroid or {}).get("lon"),
                "geofence_radius": radius,
                "geocode_status": "Imported",
                "motive_geofence_id": gid,
                "motive_category": g.get("category") or "",
                "motive_status": g.get("status") or "",
                "project_number": None,
                "proposed_project_number": None,
                "confidence_score": None,
                "confidence_band": None,
                "match_signal": None,
                "active": True,
                "created_at": _now(),
                "created_by": "import-geofences",
                "updated_at": _now(),
                "verified_at": None,
                "verified_by": None,
            }
            await db.operational_locations.insert_one(doc)
            imported += 1

        return {
            "ok": True,
            "imported": imported,
            "updated": updated,
            "skipped": skipped,
            "total_geofences_in_motive": await db.motive_geofences.count_documents({}),
        }

    # ── M3-3 · Reconciliation engine ──────────────────────────────────
    @router.post("/admin/locations/reconcile",
                 dependencies=[Depends(require_admin_dep)])
    async def reconcile():
        """For each `operational_locations` row of type JOB that is not yet
        Verified or Rejected, compute its best candidate against
        `jobs_master`. Persists `proposed_project_number`, `confidence_score`,
        `confidence_band`, `match_signal`. NEVER auto-sets `project_number`."""
        jobs = await db.jobs_master.find({"active": True}).to_list(2000)
        scored = 0
        bands = {"high": 0, "medium": 0, "low": 0}

        cursor = db.operational_locations.find({
            "location_type": "JOB",
            "geocode_status": {"$nin": ["Verified", "Rejected"]},
        })
        async for loc in cursor:
            if not jobs:
                continue
            results = []
            for j in jobs:
                results.append((j, _score_match(j, loc)))
            results.sort(key=lambda r: r[1]["score"], reverse=True)
            best_job, best = results[0]
            patch = {
                "proposed_project_number": best_job.get("project_number") if best["score"] > 0 else None,
                "proposed_project_name": best_job.get("project_name") if best["score"] > 0 else None,
                "confidence_score": best["score"],
                "confidence_band": best["band"],
                "match_signal": best.get("best_signal"),
                "updated_at": _now(),
            }
            # Promote status from "Imported" → "Matched" if any candidate found.
            if best["score"] > 0:
                patch["geocode_status"] = (
                    loc.get("geocode_status")
                    if loc.get("geocode_status") in ("Verified", "Rejected")
                    else "Matched"
                )
            await db.operational_locations.update_one({"id": loc["id"]}, {"$set": patch})
            scored += 1
            bands[best["band"]] = bands.get(best["band"], 0) + 1

        return {"ok": True, "scored": scored, "bands": bands,
                "jobs_considered": len(jobs)}

    # ── M3-4 · Reconciliation queue ───────────────────────────────────
    @router.get("/admin/locations/reconciliation-queue",
                dependencies=[Depends(require_admin_dep)])
    async def reconciliation_queue(
        band: Optional[str] = Query(default=None, regex="^(high|medium|low)$"),
        status: Optional[str] = Query(default=None),
    ):
        """List candidate matches for operator review.
        Default: all bands, all unverified statuses."""
        q: Dict[str, Any] = {"location_type": "JOB"}
        if band:
            q["confidence_band"] = band
        if status:
            if status not in GEOCODE_STATUSES:
                raise HTTPException(400, f"Unknown status: {status}")
            q["geocode_status"] = status
        rows: List[Dict[str, Any]] = []
        async for r in db.operational_locations.find(q).sort([("confidence_score", -1)]):
            r.pop("_id", None)
            rows.append(r)
        # Sidecar counts for tile chips.
        counts = {b: 0 for b in ["high", "medium", "low", "verified", "rejected", "total"]}
        async for r in db.operational_locations.find({"location_type": "JOB"}, {"confidence_band": 1, "geocode_status": 1}):
            counts["total"] += 1
            cb = r.get("confidence_band")
            gs = r.get("geocode_status")
            if gs == "Verified":
                counts["verified"] += 1
            elif gs == "Rejected":
                counts["rejected"] += 1
            elif cb in counts:
                counts[cb] += 1
        return {"ok": True, "rows": rows, "counts": counts}

    # ── M3-5 · Per-project linkage view ───────────────────────────────
    @router.get("/admin/locations/by-project",
                dependencies=[Depends(require_admin_dep)])
    async def by_project():
        """Return a map keyed by project_number for the AdminJobs panel.
        Only Verified linkages are surfaced as authoritative; proposals
        are returned separately so the panel can show 'pending review'."""
        verified: Dict[str, Any] = {}
        proposed: Dict[str, List[Any]] = {}
        async for r in db.operational_locations.find({"location_type": "JOB"}):
            r.pop("_id", None)
            if r.get("geocode_status") == "Verified" and r.get("project_number"):
                verified[r["project_number"]] = r
            elif r.get("proposed_project_number"):
                proposed.setdefault(r["proposed_project_number"], []).append(r)
        return {"ok": True, "verified": verified, "proposed": proposed}

    # ── Approve / Reject / Reassign / Bulk approve ────────────────────
    @router.post("/admin/locations/{loc_id}/approve",
                 dependencies=[Depends(require_admin_dep)])
    async def approve(loc_id: str):
        loc = await db.operational_locations.find_one({"id": loc_id})
        if not loc:
            raise HTTPException(404, "Location not found")
        pn = (loc.get("proposed_project_number") or "").strip()
        if not pn:
            raise HTTPException(400, "No proposal to approve. Use /reassign with an explicit project_number.")
        await db.operational_locations.update_one(
            {"id": loc_id},
            {"$set": {
                "project_number": pn,
                "geocode_status": "Verified",
                "verified_at": _now(),
                "verified_by": "admin",
                "updated_at": _now(),
            }},
        )
        return {"ok": True, "id": loc_id, "project_number": pn, "geocode_status": "Verified"}

    @router.post("/admin/locations/{loc_id}/reject",
                 dependencies=[Depends(require_admin_dep)])
    async def reject(loc_id: str):
        loc = await db.operational_locations.find_one({"id": loc_id})
        if not loc:
            raise HTTPException(404, "Location not found")
        await db.operational_locations.update_one(
            {"id": loc_id},
            {"$set": {
                "geocode_status": "Rejected",
                "verified_at": _now(),
                "verified_by": "admin",
                "updated_at": _now(),
                # clear the auto proposal but keep the geofence link for audit
                "proposed_project_number": None,
                "proposed_project_name": None,
            }},
        )
        return {"ok": True, "id": loc_id, "geocode_status": "Rejected"}

    @router.post("/admin/locations/{loc_id}/reassign",
                 dependencies=[Depends(require_admin_dep)])
    async def reassign(loc_id: str, body: ReassignBody):
        loc = await db.operational_locations.find_one({"id": loc_id})
        if not loc:
            raise HTTPException(404, "Location not found")
        # Sanity: ensure the project exists. Reject otherwise.
        job = await db.jobs_master.find_one({"project_number": body.project_number})
        if not job:
            raise HTTPException(400, f"Unknown project_number {body.project_number!r}")
        await db.operational_locations.update_one(
            {"id": loc_id},
            {"$set": {
                "project_number": body.project_number.strip(),
                "geocode_status": "Verified",
                "verified_at": _now(),
                "verified_by": "admin",
                "updated_at": _now(),
                # Record that this was a manual reassignment.
                "match_signal": {"score": 1.0, "kind": "manual",
                                 "evidence": f"manually reassigned to {body.project_number}"},
                "confidence_score": 1.0,
                "confidence_band": "high",
            }},
        )
        return {"ok": True, "id": loc_id, "project_number": body.project_number,
                "geocode_status": "Verified"}

    @router.post("/admin/locations/bulk-approve",
                 dependencies=[Depends(require_admin_dep)])
    async def bulk_approve(body: BulkApproveBody):
        """Bulk approve ONLY for ids with confidence ≥ 0.85 (HIGH band).
        Rows below the threshold are skipped and returned in `skipped`."""
        approved, skipped = [], []
        for lid in body.ids:
            loc = await db.operational_locations.find_one({"id": lid})
            if not loc:
                skipped.append({"id": lid, "reason": "not_found"})
                continue
            score = float(loc.get("confidence_score") or 0)
            pn = (loc.get("proposed_project_number") or "").strip()
            if score < HIGH_CONFIDENCE or not pn:
                skipped.append({"id": lid, "reason": "below_high_confidence",
                                "score": score})
                continue
            await db.operational_locations.update_one(
                {"id": lid},
                {"$set": {
                    "project_number": pn,
                    "geocode_status": "Verified",
                    "verified_at": _now(),
                    "verified_by": "admin-bulk",
                    "updated_at": _now(),
                }},
            )
            approved.append({"id": lid, "project_number": pn})
        return {"ok": True, "approved": approved, "skipped": skipped,
                "approved_count": len(approved), "skipped_count": len(skipped)}

    # ── Listing endpoint ──────────────────────────────────────────────
    @router.get("/admin/locations",
                dependencies=[Depends(require_admin_dep)])
    async def list_locations(
        location_type: Optional[str] = None,
        status: Optional[str] = None,
    ):
        q: Dict[str, Any] = {}
        if location_type:
            if location_type not in LOCATION_TYPES:
                raise HTTPException(400, f"Unknown location_type: {location_type}")
            q["location_type"] = location_type
        if status:
            if status not in GEOCODE_STATUSES:
                raise HTTPException(400, f"Unknown status: {status}")
            q["geocode_status"] = status
        out: List[Dict[str, Any]] = []
        async for r in db.operational_locations.find(q).sort([("name", 1)]):
            r.pop("_id", None)
            out.append(r)
        return {"ok": True, "rows": out, "count": len(out)}

    return router


__all__ = ["build_operational_locations_router", "LOCATION_TYPES", "GEOCODE_STATUSES"]
