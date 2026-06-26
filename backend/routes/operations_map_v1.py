"""
routes/operations_map_v1.py · FORGEDOPS Live Operations Map · Phase 5B V1

Five aggregator endpoints powering the operator-facing live map. All routes
read-only over EXISTING collections — no new data stores, no parallel
systems (per the approved PHASE_5B_LIVE_OPERATIONS_MAP_V1_PLAN doctrine).

  1. GET /api/operations-map/snapshot          — full map payload
  2. GET /api/operations-map/asset/{key}       — asset detail card
  3. GET /api/operations-map/timeline          — bottom timeline
  4. GET /api/operations-map/search            — instant search
  5. GET /api/operations-map/geofence/{gf_id}  — geofence detail

Trust contract: every payload carries `source`, `timestamp`, `age_seconds`,
`confidence`. No interpolation, no estimation, no fake locations.
"""
from __future__ import annotations
import logging
import re
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Path, Query

logger = logging.getLogger("operations_map_v1")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_iso(s: Any) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except Exception:
        return None


def _age_seconds(ts: Any) -> Optional[int]:
    dt = _parse_iso(ts)
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int((datetime.now(timezone.utc) - dt).total_seconds())


def _band_from_age(age_s: Optional[int]) -> str:
    """green = <5min · amber = <60min · red = <24h · gray = none/older.
    Mirrors the Fleet GPS Intelligence endpoint's thresholds."""
    if age_s is None:
        return "gray"
    if age_s <= 300:
        return "green"
    if age_s <= 3600:
        return "amber"
    if age_s <= 86400:
        return "red"
    return "gray"


def _confidence(band: str, has_link: bool) -> str:
    if not has_link:
        return "unmapped"
    if band == "green":
        return "high"
    if band == "amber":
        return "medium"
    if band == "red":
        return "low"
    return "stale"


def _asset_kind_for_marker(equipment_type: Optional[str], unit_number: Optional[str]) -> str:
    """Map MASCI equipment family to one of the 11 V1 sprite categories.

    Sprite categories (per spec):
      paver | mill | roller | excavator | dozer | motor_grader | loader |
      water_truck | dump_truck | service_truck | pickup
    """
    et = (equipment_type or "").upper()
    un = (unit_number or "").upper()

    # Mill / Paver / Roller / Grader by equipment family keywords
    if "PAVER" in et or un.startswith("PV"):
        return "paver"
    if "MILL" in et or un.startswith("MIL"):
        return "mill"
    if "ROLLER" in et or un.startswith("RL"):
        return "roller"
    if "EXCAVAT" in et or un.startswith("EXC"):
        return "excavator"
    if "DOZER" in et or "BULL" in et or un.startswith("DZ"):
        return "dozer"
    if "GRADER" in et or un.startswith("MG"):
        return "motor_grader"
    if "LOADER" in et or "BACKHOE" in et or un.startswith("BH"):
        return "loader"

    # Trucks by unit_number prefix (matches MASCI fleet convention)
    if un.startswith("WT"):
        return "water_truck"
    if un.startswith("DPT"):
        return "dump_truck"
    # Track 15.82 — Roll-Off Truck visibility on the map. Until a custom
    # sprite ships, render Roll-Offs with the dump_truck silhouette
    # (closest visual + already DOT-class hauler).
    if "ROLL" in et or "ROLLOFF" in et or "ROLL-OFF" in et or "ROLL OFF" in et \
            or "CONTAINER" in et or un.startswith("RO"):
        return "dump_truck"
    if un.startswith("ST") or "SERVICE" in et:
        return "service_truck"
    if un.startswith("PKU") or "PICKUP" in et:
        return "pickup"

    # Sensible fallback
    return "service_truck"


# ──────────────────────────────────────────────────────────────────────────
# Geofence membership · pure Python (no Shapely dep needed for V1's 67
# rectangular / polygon Motive geofences). Uses standard ray-casting.
# ──────────────────────────────────────────────────────────────────────────
def _polygon_from_motive(geofence_doc: Dict[str, Any]) -> List[Tuple[float, float]]:
    """Extract a polygon coord list from a Motive geofence row.

    Motive returns geofences in several shapes. We try, in order:
      1. doc['polygon'] / doc['raw']['polygon']  (list of {lat,lon})
      2. doc['boundary']['coordinates']          (GeoJSON [lon,lat])
      3. doc['center'] + doc['radius_m']         (synthesise an 8-pt circle)
    """
    raw = geofence_doc.get("raw") or {}
    poly = (geofence_doc.get("polygon")
            or raw.get("polygon")
            or raw.get("boundary"))
    pts: List[Tuple[float, float]] = []
    if isinstance(poly, list):
        for pt in poly:
            if isinstance(pt, dict) and "lat" in pt and ("lon" in pt or "lng" in pt):
                pts.append((float(pt["lat"]), float(pt.get("lon") or pt.get("lng"))))
            elif isinstance(pt, (list, tuple)) and len(pt) >= 2:
                # GeoJSON lon,lat
                pts.append((float(pt[1]), float(pt[0])))
    if pts:
        return pts
    # Synth circle from center + radius if available
    center = geofence_doc.get("center") or raw.get("center") or {}
    radius = (geofence_doc.get("radius_m")
              or raw.get("radius_m") or raw.get("radius") or 0)
    if (isinstance(center, dict) and center.get("lat") and center.get("lon")
            and radius):
        import math
        clat, clon = float(center["lat"]), float(center["lon"])
        r_deg = float(radius) / 111000.0
        for i in range(8):
            ang = (i / 8.0) * 2 * math.pi
            pts.append((clat + r_deg * math.cos(ang),
                        clon + r_deg * math.sin(ang)))
    return pts


def _point_in_polygon(lat: float, lon: float,
                      polygon: List[Tuple[float, float]]) -> bool:
    if len(polygon) < 3:
        return False
    inside = False
    j = len(polygon) - 1
    for i in range(len(polygon)):
        yi, xi = polygon[i]
        yj, xj = polygon[j]
        if ((yi > lat) != (yj > lat)) and (
                lon < (xj - xi) * (lat - yi) / (yj - yi + 1e-12) + xi):
            inside = not inside
        j = i
    return inside


# ──────────────────────────────────────────────────────────────────────────
# Router
# ──────────────────────────────────────────────────────────────────────────
def register_operations_map_v1_routes(
    router: APIRouter,
    db,
    require_any_portal_token_dep: Callable[..., Awaitable[Dict[str, Any]]],
) -> None:
    """Mount five new V1 endpoints onto the existing
    /api/operations-map router."""

    # ── helpers shared inside the closure ─────────────────────────────
    async def _load_assets_and_events() -> Tuple[
            List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
        """Pull every motive-linked asset + the freshest motive event
        per vehicle. Returns (assets_list, latest_event_by_vehicle_id).
        """
        assets: List[Dict[str, Any]] = []
        async for a in db.asset_mappings.find(
            {"provider": "motive"},
            {"_id": 0, "id": 1, "asset_kind": 1, "motive": 1,
             "masci_equipment_id": 1, "masci_unit_number": 1,
             "masci_equipment_name": 1, "mapping_confidence": 1,
             "mapping_notes": 1, "updated_at": 1},
        ):
            assets.append(a)

        latest: Dict[str, Dict[str, Any]] = {}
        try:
            async for e in db.motive_events.find(
                {"provider": "motive",
                 "event_kind": {"$in": [
                     "vehicle_gps", "vehicle_location_received", "location",
                     "vehicle.location", "vehicle_location", "telemetry"]}},
                {"_id": 0, "vehicle_id": 1, "event_at": 1, "received_at": 1,
                 "lat": 1, "lon": 1, "speed_kph": 1, "speed_mph": 1,
                 "bearing": 1, "city": 1, "state": 1, "source": 1,
                 "event_kind": 1, "event_signature": 1},
            ).sort([("event_at", -1)]).limit(8000):
                vid = str(e.get("vehicle_id") or "")
                if vid and vid not in latest:
                    latest[vid] = e
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[ops-map-v1 load events] {e}")
        return assets, latest

    def _build_marker(asset: Dict[str, Any],
                      latest_event: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        mv = asset.get("motive") or {}
        unit_number = (asset.get("masci_unit_number") or mv.get("number")
                       or mv.get("name") or "")
        equipment_name = asset.get("masci_equipment_name") or ""
        has_link = bool(asset.get("masci_equipment_id"))

        # Prefer most recent location from motive_events; fall back to
        # asset_mappings.motive coords (less fresh but real).
        if latest_event and latest_event.get("lat") is not None:
            lat = latest_event.get("lat")
            lon = latest_event.get("lon")
            ts = latest_event.get("event_at")
            speed_kph = latest_event.get("speed_kph")
            speed_mph = latest_event.get("speed_mph")
            bearing = latest_event.get("bearing")
            source = "motive:webhook" if latest_event.get("source") == "webhook" else "motive:poll"
        else:
            lat = mv.get("lat")
            lon = mv.get("lon")
            ts = mv.get("located_at")
            speed_kph = None
            speed_mph = None
            bearing = None
            source = "motive:mapping"

        age_s = _age_seconds(ts)
        band = _band_from_age(age_s)
        if lat is None or lon is None:
            band = "gray"  # no_gps
        confidence = _confidence(band, has_link)

        return {
            "asset_id":        asset.get("id"),
            "masci_equipment_id": asset.get("masci_equipment_id") or None,
            "unit_number":     unit_number,
            "equipment_name":  equipment_name,
            "asset_kind":      asset.get("asset_kind"),
            "marker_kind":     _asset_kind_for_marker(
                                  equipment_name or mv.get("type") or "",
                                  unit_number),
            "motive_vehicle_id": str(mv.get("vehicle_id") or "") or None,
            "motive_asset_id":   str(mv.get("asset_id") or "") or None,
            "vin":              mv.get("vin"),
            "lat":              lat,
            "lon":              lon,
            "speed_kph":        speed_kph,
            "speed_mph":        speed_mph,
            "bearing":          bearing,
            "last_seen_at":     ts,
            "age_seconds":      age_s,
            "band":             band,         # green | amber | red | gray
            "trust": {
                "source":      source,
                "timestamp":   ts,
                "age_seconds": age_s,
                "confidence":  confidence,    # high | medium | low | stale | unmapped
            },
        }

    # ── 1. /snapshot ──────────────────────────────────────────────────
    @router.get("/snapshot")
    async def snapshot(
        actor: Dict[str, Any] = Depends(require_any_portal_token_dep),
        limit: int = Query(default=2000, ge=1, le=5000),
    ) -> Dict[str, Any]:
        assets, latest = await _load_assets_and_events()
        markers = [_build_marker(a, latest.get(str((a.get("motive") or {}).get("vehicle_id") or "")))
                   for a in assets[:limit]]

        # Geofences (read-only from motive_geofences).
        geofences: List[Dict[str, Any]] = []
        async for g in db.motive_geofences.find(
            {}, {"_id": 0, "motive_geofence_id": 1, "name": 1, "category": 1,
                 "polygon": 1, "raw": 1, "center": 1, "radius_m": 1,
                 "updated_at": 1, "created_at": 1},
        ).limit(500):
            poly = _polygon_from_motive(g)
            if not poly:
                continue
            geofences.append({
                "id":         g.get("motive_geofence_id"),
                "name":       g.get("name"),
                "category":   g.get("category") or "Uncategorized",
                "polygon":    [[lat, lon] for lat, lon in poly],
                "updated_at": g.get("updated_at"),
            })

        # Aggregate counts.
        counts = {"total": len(markers), "green": 0, "amber": 0, "red": 0,
                  "gray": 0, "unmapped": 0, "with_gps": 0}
        for m in markers:
            counts[m["band"]] += 1
            if not m["masci_equipment_id"]:
                counts["unmapped"] += 1
            if m["lat"] is not None and m["lon"] is not None:
                counts["with_gps"] += 1

        # ── Real attention-reason data (defects + inspections) ──────
        # Single aggregation pass per collection — keeps snapshot fast.
        # These maps drive the "why is this asset red?" breakdown so
        # operators see WHY, not just THAT, an asset needs review.
        open_defects_by_unit: Dict[str, int] = {}
        try:
            pipe = [
                {"$match": {"status": {"$in": ["open", "acknowledged"]}}},
                {"$group": {"_id": "$truck_unit_number", "n": {"$sum": 1}}},
            ]
            async for row in db.fleet_defects.aggregate(pipe):
                if row.get("_id"):
                    open_defects_by_unit[str(row["_id"])] = int(row.get("n") or 0)
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[ops-map snapshot defects agg] {e}")

        open_inspections_by_em: Dict[str, int] = {}
        try:
            pipe = [
                {"$match": {"status": {"$nin": ["closed", "completed", "passed"]}}},
                {"$group": {"_id": "$equipment_id", "n": {"$sum": 1}}},
            ]
            async for row in db.equipment_inspections.aggregate(pipe):
                if row.get("_id"):
                    open_inspections_by_em[str(row["_id"])] = int(row.get("n") or 0)
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[ops-map snapshot inspections agg] {e}")

        # ── Project / Geofence assignment + rollups ──────────────
        # Assignment priority (per directive §10):
        #   1. explicit_project    (high)   — masci_equipment.project_number when present
        #   2. geofence_membership (high)   — point-in-polygon over real Motive shapes
        #   3. gps_location        (medium) — city/state text from latest telemetry
        #   4. missing_assignment  (low)    — final Unassigned / Unknown fallback
        gf_polys = []
        for g in geofences:
            if g.get("polygon"):
                gf_polys.append({
                    "id": g["id"], "name": g["name"],
                    "category": g["category"],
                    "poly": [(lat, lon) for lat, lon in g["polygon"]],
                })

        # Precompute explicit project_number lookup for assets carrying
        # a masci_equipment_id. One short equipment_master query — keeps
        # snapshot inside the SLA.
        em_ids = [m.get("masci_equipment_id") for m in markers if m.get("masci_equipment_id")]
        explicit_project_by_em: Dict[str, str] = {}
        if em_ids:
            try:
                async for em in db.equipment_master.find(
                    {"id": {"$in": em_ids}},
                    {"_id": 0, "id": 1, "project_number": 1, "current_project": 1, "assigned_project": 1},
                ):
                    pn = (em.get("project_number")
                          or em.get("current_project")
                          or em.get("assigned_project"))
                    if pn:
                        explicit_project_by_em[em.get("id")] = str(pn).strip()
            except Exception as e:  # noqa: BLE001
                logger.warning(f"[ops-map-v1 explicit-project lookup] {e}")

        # Resolve latest event city for each vehicle (cheap — already
        # loaded as `latest` map inside _load_assets_and_events).
        def _city_bucket(city: Optional[str], state: Optional[str]) -> Optional[str]:
            c = (city or "").strip()
            if not c:
                return None
            s = (state or "").strip()
            return f"{c}, {s} Area" if s else f"{c} Area"

        latest_by_vid = latest  # alias from outer scope

        rollups: Dict[str, Dict[str, Any]] = {}
        for m in markers:
            name = None
            source = None
            confidence = None
            bucket_type = None

            # 1. Explicit project
            em_id = m.get("masci_equipment_id")
            if em_id and explicit_project_by_em.get(em_id):
                name = explicit_project_by_em[em_id]
                source = "explicit_project"
                confidence = "high"
                bucket_type = "project"

            # 2. Geofence membership
            if not name and m.get("lat") is not None and m.get("lon") is not None and gf_polys:
                for g in gf_polys:
                    if _point_in_polygon(m["lat"], m["lon"], g["poly"]):
                        name = g["name"]
                        source = "geofence_membership"
                        confidence = "high"
                        bucket_type = "geofence"
                        break

            # 3. GPS location fallback (city from latest telemetry)
            if not name:
                vid = str((m.get("motive_vehicle_id") or ""))
                ev = latest_by_vid.get(vid) if vid else None
                if ev:
                    cb = _city_bucket(ev.get("city"), ev.get("state"))
                    if cb:
                        name = cb
                        source = "gps_location"
                        confidence = "medium"
                        bucket_type = "location"

            # 4. Final fallback
            if not name:
                name = "Unassigned / Unknown"
                source = "missing_assignment"
                confidence = "low"
                bucket_type = "unassigned"

            m["assignment"] = {
                "name": name, "source": source,
                "confidence": confidence, "bucket_type": bucket_type,
            }

            # ── Attention reason classification (red band only) ──────
            # Real categories from real data — no fabrication. Reason
            # priority: maintenance → inspection → assignment → stale.
            reason = None
            if m["band"] == "red":
                un = m.get("unit_number") or ""
                em_id = m.get("masci_equipment_id") or ""
                if open_defects_by_unit.get(un, 0) > 0:
                    reason = "maintenance"
                elif open_inspections_by_em.get(em_id, 0) > 0:
                    reason = "inspection"
                elif bucket_type == "unassigned" or confidence == "low":
                    reason = "assignment"
                else:
                    reason = "stale_position"
            m["attention_reason"] = reason

            r = rollups.setdefault(name, {
                "name": name,
                "display_name": name,
                "bucket_type": bucket_type,
                "total": 0,
                "connected_count": 0,
                "attention_required_count": 0,
                "offline_count": 0,
                "last_activity_at": None,
                "assignment_source": source,
                "assignment_confidence": confidence,
                "attention_breakdown": {
                    "maintenance": 0, "inspection": 0,
                    "assignment": 0, "stale_position": 0,
                },
            })
            r["total"] += 1
            if m["band"] in ("green", "amber"):
                r["connected_count"] += 1
            if m["band"] == "red":
                r["attention_required_count"] += 1
                if reason:
                    r["attention_breakdown"][reason] = r["attention_breakdown"].get(reason, 0) + 1
            if m["band"] == "gray":
                r["offline_count"] += 1
            if m.get("last_seen_at") and (
                not r["last_activity_at"]
                or m["last_seen_at"] > r["last_activity_at"]
            ):
                r["last_activity_at"] = m["last_seen_at"]

        # Rank: attention desc, offline desc, total desc, last_activity desc
        ranked = sorted(
            rollups.values(),
            key=lambda x: (
                -x["attention_required_count"],
                -x["offline_count"],
                -x["total"],
                -(int(_age_seconds(x["last_activity_at"]) or 10**12) * -1
                  if x["last_activity_at"] else 0),
            ),
        )
        # Reason → operator-readable label, owner, and next-action string.
        # Deterministic mapping — no AI, no guessing. Owners map to real
        # MASCI operational roles only.
        REASON_LABEL = {
            "maintenance":    "Maintenance Due",
            "inspection":     "Inspection Overdue",
            "assignment":     "Assignment Unknown",
            "stale_position": "Position Update Overdue",
        }
        OWNER_BY_REASON = {
            "maintenance":    "Shop",
            "inspection":     "Shop / Safety",
            "assignment":     "PM / Dispatch",
            "stale_position": "Truck Boss / Dispatch",
        }
        NEXT_BY_REASON = {
            "maintenance":    "Shop review open issue",
            "inspection":     "Shop review inspection",
            "assignment":     "Assign asset to project or yard",
            "stale_position": "Truck Boss verify asset location",
        }
        for r in ranked:
            bd = r.pop("attention_breakdown", {}) or {}
            ordered = sorted(bd.items(), key=lambda kv: -kv[1])
            r["attention_breakdown"] = [
                {"id": rid, "label": REASON_LABEL[rid],
                 "count": cnt, "owner": OWNER_BY_REASON[rid]}
                for rid, cnt in ordered if cnt > 0
            ]
            # Dominant cause + operational next-action for the area
            if r["attention_breakdown"]:
                top = r["attention_breakdown"][0]
                r["next_action"]     = NEXT_BY_REASON[top["id"]]
                r["dominant_owner"]  = top["owner"]
                r["dominant_reason"] = top["label"]
            elif r["offline_count"] > 0:
                r["next_action"]     = "Dispatch confirm last known location"
                r["dominant_owner"]  = "Truck Boss / Dispatch"
                r["dominant_reason"] = "No Recent Position"
            elif r.get("bucket_type") == "unassigned" and r["total"] > 0:
                r["next_action"]     = "Assign asset to project or yard"
                r["dominant_owner"]  = "PM / Dispatch"
                r["dominant_reason"] = "Assignment Unknown"
            else:
                r["next_action"]     = None
                r["dominant_owner"]  = None
                r["dominant_reason"] = None
        project_rollups_top = ranked[:5]
        project_rollups_overflow = max(0, len(ranked) - 5)

        # ── Snapshot-level attention_breakdown summary ──────────────
        snap_bd = {"maintenance": 0, "inspection": 0,
                   "assignment": 0, "stale_position": 0}
        for m in markers:
            if m["band"] == "red" and m.get("attention_reason"):
                snap_bd[m["attention_reason"]] = snap_bd.get(m["attention_reason"], 0) + 1
        attention_breakdown = [
            {"id": rid, "label": REASON_LABEL[rid],
             "count": cnt, "owner": OWNER_BY_REASON[rid]}
            for rid, cnt in sorted(snap_bd.items(), key=lambda kv: -kv[1])
            if cnt > 0
        ]

        # Assets Assigned — confidently placed (project / geofence / location).
        assets_assigned = sum(
            1 for m in markers
            if (m.get("assignment") or {}).get("bucket_type") in ("project", "geofence", "location")
        )

        # ── Operational Summary · MASCI-native vocabulary ────────────
        # Single source of truth that the UI consumes. Maps the
        # internal band buckets onto the operational language the
        # rest of the Operations Center already uses (Working / Idle /
        # Needs Attention / Offline). Raw `counts` are kept for
        # backward-compat and internal consumers, but the banner UI
        # binds to `operational_summary`.
        operational_summary = [
            {"id": "attention",
             "label": "Attention Required",
             "value": counts["red"],
             "tone": "rose",
             "band": "red",
             "breakdown": attention_breakdown},
            {"id": "offline",
             "label": "No Recent Position",
             "value": counts["gray"],
             "tone": "slate",
             "band": "gray"},
            {"id": "working",
             "label": "Working",
             "value": counts["green"],
             "tone": "emerald",
             "band": "green"},
            {"id": "idle",
             "label": "Idle",
             "value": counts["amber"],
             "tone": "amber",
             "band": "amber"},
            {"id": "assigned",
             "label": "Assets Assigned",
             "value": assets_assigned,
             "tone": "slate",
             "band": None},
            {"id": "total",
             "label": "Total Assets",
             "value": counts["total"],
             "tone": "slate",
             "band": None},
        ]

        # ── Data feed status · operator-language summary ────────────
        # green tier present → Live; amber present → Delayed;
        # otherwise → Offline. This bubbles up to the header chip.
        if counts["green"] > 0:
            feed_status = "live"
            feed_label  = "Live Data"
        elif counts["amber"] > 0:
            feed_status = "delayed"
            feed_label  = "Delayed Data"
        else:
            feed_status = "offline"
            feed_label  = "No Recent Updates"

        return {
            "ok": True,
            "as_of": _now_iso(),
            "operational_summary": operational_summary,
            "attention_breakdown": attention_breakdown,
            "feed_status": {
                "status": feed_status,
                "label":  feed_label,
            },
            "counts": counts,  # kept for internal consumers; UI binds to operational_summary
            "assets": markers,
            "geofences": geofences,
            "geofence_count": len(geofences),
            "project_rollups": project_rollups_top,
            "project_rollups_overflow": project_rollups_overflow,
            "project_rollups_total": len(rollups),
        }

    # ── 2. /asset/{key} ───────────────────────────────────────────────
    @router.get("/asset/{key}")
    async def asset_detail(
        key: str = Path(..., min_length=1, max_length=128),
        actor: Dict[str, Any] = Depends(require_any_portal_token_dep),
    ) -> Dict[str, Any]:
        """Lookup by unit_number, masci_equipment_id, or motive vehicle_id."""
        key_norm = key.strip()
        key_upper = key_norm.upper()

        # Find the asset_mapping by any of the candidate keys.
        mapping = await db.asset_mappings.find_one(
            {"provider": "motive",
             "$or": [
                 {"masci_equipment_id": key_norm},
                 {"masci_unit_number": key_upper},
                 {"motive.vehicle_id": key_norm},
                 {"motive.number": key_upper},
                 {"motive.name": key_upper},
             ]},
            {"_id": 0},
        )
        if not mapping:
            # Allow looking up an unmapped equipment_master by unit_number.
            em = await db.equipment_master.find_one(
                {"unit_number": key_upper},
                {"_id": 0, "id": 1, "unit_number": 1, "vin_serial_number": 1,
                 "display_label": 1, "make_model": 1, "type": 1},
            )
            if not em:
                raise HTTPException(404, f"asset not found for key={key}")
            return {
                "ok": True, "as_of": _now_iso(),
                "asset": {
                    "masci_equipment_id": em.get("id"),
                    "unit_number":        em.get("unit_number"),
                    "equipment_name":     em.get("display_label"),
                    "vin":                em.get("vin_serial_number"),
                    "asset_kind":         em.get("type"),
                    "marker_kind":        _asset_kind_for_marker(em.get("display_label"), em.get("unit_number")),
                    "lat": None, "lon": None,
                    "last_seen_at": None, "age_seconds": None,
                    "band": "gray",
                    "trust": {"source": "equipment_master", "timestamp": None,
                              "age_seconds": None, "confidence": "unmapped"},
                },
                "driver": None, "geofence_status": None,
                "open_inspections": [], "open_defects": [],
                "recent_events": [], "asset_health": {"status": "unknown"},
                "motive_status": {"status": "not_motive_mapped"},
            }

        mv = mapping.get("motive") or {}
        vid = str(mv.get("vehicle_id") or "")

        # Latest motive event for live coords.
        latest_event = None
        if vid:
            latest_event = await db.motive_events.find_one(
                {"provider": "motive", "vehicle_id": vid,
                 "event_kind": {"$in": ["vehicle_gps", "vehicle_location_received"]}},
                {"_id": 0}, sort=[("event_at", -1)],
            )

        marker = _build_marker(mapping, latest_event)

        # Assignment: same priority as snapshot (explicit project →
        # geofence membership → GPS location → unassigned).
        assignment_name = None
        assignment_source = None
        assignment_confidence = None
        em_id = mapping.get("masci_equipment_id")
        if em_id:
            em_doc = await db.equipment_master.find_one(
                {"id": em_id},
                {"_id": 0, "project_number": 1, "current_project": 1, "assigned_project": 1},
            ) or {}
            pn = (em_doc.get("project_number")
                  or em_doc.get("current_project")
                  or em_doc.get("assigned_project"))
            if pn:
                assignment_name = str(pn).strip()
                assignment_source = "explicit_project"
                assignment_confidence = "high"
        if not assignment_name and marker.get("lat") is not None and marker.get("lon") is not None:
            async for g in db.motive_geofences.find({}, {"_id": 0}):
                poly = _polygon_from_motive(g)
                if poly and _point_in_polygon(marker["lat"], marker["lon"], poly):
                    assignment_name = g.get("name")
                    assignment_source = "geofence_membership"
                    assignment_confidence = "high"
                    break
        if not assignment_name and latest_event:
            c = (latest_event.get("city") or "").strip()
            s = (latest_event.get("state") or "").strip()
            if c:
                assignment_name = f"{c}, {s} Area" if s else f"{c} Area"
                assignment_source = "gps_location"
                assignment_confidence = "medium"
        if not assignment_name:
            assignment_name = "Unassigned / Unknown"
            assignment_source = "missing_assignment"
            assignment_confidence = "low"
        marker["assignment"] = {
            "name": assignment_name,
            "source": assignment_source,
            "confidence": assignment_confidence,
        }

        # Driver: prefer current_vehicle_id match in employee_mappings.
        driver = None
        if vid:
            drv_doc = await db.employee_mappings.find_one(
                {"provider": "motive", "motive.current_vehicle_id": int(vid) if vid.isdigit() else vid},
                {"_id": 0, "motive": 1, "masci_employee_id": 1, "masci_employee_name": 1},
            )
            if drv_doc:
                dmv = drv_doc.get("motive") or {}
                driver = {
                    "name": (drv_doc.get("masci_employee_name")
                             or f"{dmv.get('first_name') or ''} {dmv.get('last_name') or ''}".strip()),
                    "motive_driver_id": str(dmv.get("driver_id") or "") or None,
                    "masci_employee_id": drv_doc.get("masci_employee_id"),
                    "username": dmv.get("username"),
                    "status":   dmv.get("status"),
                }

        # Geofence status (in / out and which one).
        geofence_status = None
        if marker.get("lat") is not None and marker.get("lon") is not None:
            lat, lon = marker["lat"], marker["lon"]
            async for g in db.motive_geofences.find({}, {"_id": 0}):
                poly = _polygon_from_motive(g)
                if poly and _point_in_polygon(lat, lon, poly):
                    geofence_status = {
                        "inside": True,
                        "id": g.get("motive_geofence_id"),
                        "name": g.get("name"),
                        "category": g.get("category") or "Uncategorized",
                    }
                    break
            if not geofence_status:
                geofence_status = {"inside": False}

        # Open inspections + defects.
        open_inspections: List[Dict[str, Any]] = []
        try:
            em_id = mapping.get("masci_equipment_id")
            if em_id:
                async for ins in db.equipment_inspections.find(
                    {"equipment_id": em_id,
                     "status": {"$nin": ["closed", "completed", "passed"]}},
                    {"_id": 0, "id": 1, "form_type": 1, "status": 1, "created_at": 1, "due_at": 1},
                ).limit(5):
                    open_inspections.append(ins)
        except Exception:
            pass

        open_defects: List[Dict[str, Any]] = []
        try:
            un = mapping.get("masci_unit_number")
            if un:
                async for d in db.fleet_defects.find(
                    {"truck_unit_number": un, "status": {"$in": ["open", "acknowledged"]}},
                    {"_id": 0, "id": 1, "severity": 1, "summary": 1, "created_at": 1},
                ).limit(5):
                    open_defects.append(d)
        except Exception:
            pass

        # Recent events (last 10).
        recent: List[Dict[str, Any]] = []
        if vid:
            async for e in db.motive_events.find(
                {"provider": "motive", "vehicle_id": vid},
                {"_id": 0, "event_kind": 1, "event_family": 1, "event_at": 1,
                 "severity": 1, "lat": 1, "lon": 1, "speed_mph": 1, "source": 1},
            ).sort([("event_at", -1)]).limit(10):
                recent.append(e)

        motive_settings = await db.integration_settings.find_one(
            {"provider": "motive"},
            {"_id": 0, "enabled": 1, "status": 1, "last_successful_sync_at": 1,
             "webhook_secret_value": 1},
        ) or {}
        motive_status = {
            "enabled": bool(motive_settings.get("enabled")),
            "status":  motive_settings.get("status") or "unknown",
            "last_successful_sync_at": motive_settings.get("last_successful_sync_at"),
            "webhook_armed": bool((motive_settings.get("webhook_secret_value") or "").strip()),
        }

        # ── Action Required · action-first verdict for the asset card ──
        # Real data only. Each verdict carries operational owner + next-step
        # so the asset card answers "who has to do something, and what?".
        action_label = "No Action Required"
        action_tone  = "emerald"
        action_id    = "ok"
        action_owner = "None"
        action_next  = "Current status acceptable"
        if open_defects:
            action_label = "Maintenance Due"
            action_tone  = "rose"
            action_id    = "maintenance"
            action_owner = "Shop"
            action_next  = "Shop review open issue"
        elif open_inspections:
            action_label = "Inspection Overdue"
            action_tone  = "rose"
            action_id    = "inspection"
            action_owner = "Shop / Safety"
            action_next  = "Shop review inspection"
        elif marker["band"] == "gray":
            action_label = "No Recent Position"
            action_tone  = "slate"
            action_id    = "no_recent_position"
            action_owner = "Truck Boss / Dispatch"
            action_next  = "Verify last known location"
        elif (assignment_source in ("missing_assignment",) or assignment_confidence == "low"):
            action_label = "Assignment Unknown"
            action_tone  = "amber"
            action_id    = "assignment"
            action_owner = "PM / Dispatch"
            action_next  = "Assign asset to project or yard"
        elif marker["band"] == "red":
            action_label = "Position Update Overdue"
            action_tone  = "rose"
            action_id    = "stale_position"
            action_owner = "Truck Boss / Dispatch"
            action_next  = "Verify asset location"
        elif marker["band"] == "amber":
            action_label = "Idle · Awaiting Assignment"
            action_tone  = "amber"
            action_id    = "idle"
            action_owner = "Dispatch"
            action_next  = "Confirm next move"

        return {
            "ok": True, "as_of": _now_iso(),
            "asset":           marker,
            "action_required": {
                "id":    action_id,
                "label": action_label,
                "tone":  action_tone,
                "owner": action_owner,
                "next_step": action_next,
                "open_defects_count":      len(open_defects),
                "open_inspections_count":  len(open_inspections),
            },
            "driver":          driver,
            "geofence_status": geofence_status,
            "open_inspections": open_inspections,
            "open_defects":    open_defects,
            "recent_events":   recent,
            "asset_health":    {"status": marker["band"], "confidence": marker["trust"]["confidence"]},
            "motive_status":   motive_status,
        }

    # ── 3. /timeline ──────────────────────────────────────────────────
    @router.get("/timeline")
    async def timeline(
        actor: Dict[str, Any] = Depends(require_any_portal_token_dep),
        limit: int = Query(default=50, ge=1, le=200),
        since: Optional[str] = Query(default=None),
        families: Optional[str] = Query(default=None,
            description="comma-separated families: vehicle_gps,geofence_enter,geofence_exit,harsh_event,fault_code,dvir"),
    ) -> Dict[str, Any]:
        q: Dict[str, Any] = {"provider": "motive"}
        if since:
            q["event_at"] = {"$gt": since}
        if families:
            fam_list = [f.strip() for f in families.split(",") if f.strip()]
            if fam_list:
                q["event_family"] = {"$in": fam_list}
        rows: List[Dict[str, Any]] = []
        async for e in db.motive_events.find(
            q,
            {"_id": 0, "id": 1, "event_kind": 1, "event_family": 1, "event_at": 1,
             "received_at": 1, "severity": 1, "vehicle_id": 1, "driver_id": 1,
             "lat": 1, "lon": 1, "speed_mph": 1, "speed_kph": 1, "city": 1,
             "state": 1, "source": 1, "summary": 1, "unit_number": 1,
             "driver_name": 1, "event_signature": 1},
        ).sort([("event_at", -1)]).limit(limit):
            e["age_seconds"] = _age_seconds(e.get("event_at"))
            rows.append(e)
        return {"ok": True, "as_of": _now_iso(), "count": len(rows), "rows": rows}

    # ── 4. /search ────────────────────────────────────────────────────
    @router.get("/search")
    async def search(
        q: str = Query(..., min_length=1, max_length=64),
        actor: Dict[str, Any] = Depends(require_any_portal_token_dep),
        limit: int = Query(default=20, ge=1, le=50),
    ) -> Dict[str, Any]:
        needle = q.strip()
        if not needle:
            return {"ok": True, "as_of": _now_iso(), "count": 0, "hits": []}
        # Escape regex specials so user input can't break the query.
        safe = re.escape(needle)
        rx = {"$regex": safe, "$options": "i"}

        hits: List[Dict[str, Any]] = []

        # 1) asset_mappings by unit / vin / name / motive.number
        async for a in db.asset_mappings.find(
            {"provider": "motive",
             "$or": [
                 {"masci_unit_number": rx},
                 {"masci_equipment_name": rx},
                 {"motive.number":  rx},
                 {"motive.name":    rx},
                 {"motive.vin":     rx},
             ]},
            {"_id": 0, "masci_equipment_id": 1, "masci_unit_number": 1,
             "masci_equipment_name": 1, "motive": 1},
        ).limit(limit):
            mv = a.get("motive") or {}
            hits.append({
                "kind": "asset",
                "key":  a.get("masci_unit_number") or mv.get("number") or mv.get("name"),
                "label": a.get("masci_equipment_name") or mv.get("name") or "",
                "unit_number": a.get("masci_unit_number") or mv.get("number"),
                "vin": mv.get("vin"),
                "masci_equipment_id": a.get("masci_equipment_id"),
            })

        # 2) employee_mappings by driver name / username
        remaining = max(0, limit - len(hits))
        if remaining:
            async for d in db.employee_mappings.find(
                {"provider": "motive",
                 "$or": [
                     {"motive.first_name": rx},
                     {"motive.last_name":  rx},
                     {"motive.username":   rx},
                     {"masci_employee_name": rx},
                 ]},
                {"_id": 0, "masci_employee_id": 1, "masci_employee_name": 1, "motive": 1},
            ).limit(remaining):
                mv = d.get("motive") or {}
                hits.append({
                    "kind": "driver",
                    "key": str(mv.get("driver_id") or ""),
                    "label": (d.get("masci_employee_name")
                              or f"{mv.get('first_name') or ''} {mv.get('last_name') or ''}".strip()),
                    "username": mv.get("username"),
                    "masci_employee_id": d.get("masci_employee_id"),
                })

        return {"ok": True, "as_of": _now_iso(), "count": len(hits), "hits": hits}

    # ── 5. /geofence/{id} ─────────────────────────────────────────────
    @router.get("/geofence/{geofence_id}")
    async def geofence_detail(
        geofence_id: str = Path(..., min_length=1, max_length=128),
        actor: Dict[str, Any] = Depends(require_any_portal_token_dep),
    ) -> Dict[str, Any]:
        gid = geofence_id.strip()
        gf = await db.motive_geofences.find_one(
            {"$or": [{"motive_geofence_id": gid},
                     {"id": gid}, {"motive_geofence_id": int(gid)} if gid.isdigit() else {}]},
            {"_id": 0},
        )
        if not gf:
            raise HTTPException(404, f"geofence not found: {gid}")

        poly = _polygon_from_motive(gf)
        # Membership: walk current asset positions and classify in / out.
        assets, latest = await _load_assets_and_events()
        inside, outside = [], []
        for a in assets:
            marker = _build_marker(a, latest.get(str((a.get("motive") or {}).get("vehicle_id") or "")))
            if marker["lat"] is None or marker["lon"] is None:
                continue
            if poly and _point_in_polygon(marker["lat"], marker["lon"], poly):
                inside.append(marker)
            else:
                outside.append(marker)

        # Recent enter / exit events.
        recent_events: List[Dict[str, Any]] = []
        try:
            async for e in db.motive_events.find(
                {"provider": "motive",
                 "event_family": {"$in": ["geofence_enter", "geofence_exit",
                                          "asset_geofence_enter", "asset_geofence_exit"]}},
                {"_id": 0, "event_kind": 1, "event_family": 1, "event_at": 1,
                 "vehicle_id": 1, "unit_number": 1},
            ).sort([("event_at", -1)]).limit(50):
                # Loose match: geofence id may appear in raw or notes.
                recent_events.append(e)
        except Exception:
            pass

        return {
            "ok": True, "as_of": _now_iso(),
            "geofence": {
                "id":         gf.get("motive_geofence_id") or gf.get("id"),
                "name":       gf.get("name"),
                "category":   gf.get("category") or "Uncategorized",
                "polygon":    [[lat, lon] for lat, lon in poly],
            },
            "assets_inside":  inside,
            "assets_outside": outside[:50],   # cap outside list to keep payload sane
            "inside_count":   len(inside),
            "outside_count":  len(outside),
            "recent_events":  recent_events,
        }


__all__ = ["register_operations_map_v1_routes"]
