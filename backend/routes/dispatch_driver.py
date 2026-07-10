"""
routes/dispatch_driver.py · iter393 · DLS Driver Mobile Surface.

The minimal API surface the driver mobile experience consumes. Every
endpoint is intentionally narrow — the driver token is scope-limited to
the driver's own currently-assigned haul cycle.

Endpoints (prefix /api/dispatch/driver):
  • POST /magic-link                       dispatch + admin only · issue link
  • POST /session/exchange                 public · exchange magic token
  • GET  /me                               driver · session info
  • GET  /my-assignment                    driver · current assignment + allowed next states
  • POST /assignments/{id}/transition      driver · one-tap state change (forgiving)
  • POST /sessions/{id}/revoke             dispatch + admin only · revoke a session
  • GET  /sessions                         dispatch + admin only · list active sessions

The driver-side handlers DELEGATE every state mutation to the existing
iter392 ``_record_transition`` writer so the lifecycle engine remains
the single source of truth (no parallel pipelines).
"""
from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from pydantic import BaseModel, Field

import dispatch_lifecycle as DLS
import driver_sessions as DS
from dispatch_assignment_seeds import (
    HAUL_TYPES,
    SEEDED_SOURCES,
    SEEDED_DESTINATIONS,
    SEEDED_PICKUP_LOCATIONS,
    SEEDED_DROPOFF_LOCATIONS,
    EQUIPMENT_MOVE_CATEGORIES,
    EQUIPMENT_MOVE_EXAMPLE_LABELS,
    flat_material_options,
    # iter410 · Phase 15.1 · Tanker continuity
    SEEDED_TANKER_SOURCES,
    SEEDED_TANKER_DESTINATIONS,
    flat_liquid_product_options,
)
from routes.dispatch_lifecycle import (
    DEFAULT_TENANT_ID,
    _record_transition,                                            # reuse
    _record_acknowledgement,                                       # D-1.1
)

logger = logging.getLogger("dispatch_driver_routes")


# ════════════════════════════════════════════════════════════════════
# Pydantic models
# ════════════════════════════════════════════════════════════════════
class MagicLinkRequest(BaseModel):
    driver_id: str = Field(..., min_length=1, max_length=120)
    driver_name: Optional[str] = ""
    truck_id: Optional[str] = ""
    assignment_id: Optional[str] = ""


class SessionExchangeRequest(BaseModel):
    magic_token: str = Field(..., min_length=8, max_length=240)


class StartShiftRequest(BaseModel):
    """iter401 · Phase 12.8 · driver self-start (no dispatcher needed).

    iter402 · Phase 12.9 · optional reference IDs link the shift to the
    canonical employee + equipment records so operational identity stays
    consistent across the platform. Free-text fallbacks preserved for
    subs / temp drivers / rentals that aren't in the system yet."""
    driver_name: str = Field(..., min_length=1, max_length=120)
    truck_id: str = Field(..., min_length=1, max_length=64)
    company: Optional[str] = Field(default="", max_length=120)
    trailer_id: Optional[str] = Field(default="", max_length=64)
    material: Optional[str] = Field(default="", max_length=120)
    # iter402 · platform-linked identity (all optional; "Add temporary"
    # entries simply omit these and remain free-text-only).
    employee_id: Optional[str] = Field(default="", max_length=64)
    truck_unit_pk: Optional[str] = Field(default="", max_length=64)
    trailer_unit_pk: Optional[str] = Field(default="", max_length=64)


class DriverTransitionRequest(BaseModel):
    to_state: str = Field(..., min_length=1, max_length=64)
    note: Optional[str] = ""
    wait_reason: Optional[str] = ""
    correction_reason: Optional[str] = ""
    geo: Optional[Dict[str, Any]] = None


# ─── Phase D-1.1 / D-1.5 · Driver acknowledgement request ──────────
class DriverAckRequest(BaseModel):
    """Driver taps ACK from `DriverShift.jsx`. Both fields optional —
    server records sensible defaults if omitted.

    target_revision_seq: if present, the driver is acknowledging
    revision_seq=N (D-1.5 re-ack path). Omit for initial ack.
    """
    method: Optional[str] = "tap"
    device: Optional[str] = ""
    note: Optional[str] = ""
    target_revision_seq: Optional[int] = None


# ════════════════════════════════════════════════════════════════════
# Helpers
# ════════════════════════════════════════════════════════════════════
def _resolve_tenant(x_tenant_id: Optional[str]) -> str:
    if x_tenant_id and isinstance(x_tenant_id, str) and x_tenant_id.strip():
        return x_tenant_id.strip()
    return DEFAULT_TENANT_ID


def _public_link_for(request: Request, raw_token: str) -> str:
    """Build the magic-link URL the dispatcher reads/QR-shares. Uses
    the request's own scheme+host so preview / prod produce correct
    links without env coupling."""
    base = str(request.base_url).rstrip("/")
    # Strip /api if base_url ever inherits it (FastAPI returns the
    # mount root; in our setup it's the bare host).
    if base.endswith("/api"):
        base = base[:-4]
    return f"{base}/d/{raw_token}"


async def _current_assignment_for_session(
    db, *, session: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Resolve the haul assignment a driver should currently see.

    Priority:
      1. If the session was issued with a pinned ``assignment_id`` use that.
      2. Otherwise, latest non-terminal, non-cancelled assignment for
         the driver in their tenant (``driver_id`` match — magic-link path).
      3. iter401 fallback (self-start path): if no driver_id match AND
         the session carries a ``truck_id``, find the latest active
         assignment for that truck regardless of who originally owned it.
         Trucks rotate drivers; operational continuity follows the truck.
    """
    tenant_id = session["tenant_id"]
    pinned = session.get("assignment_id")
    if pinned:
        doc = await db.dispatch_assignments.find_one(
            {"id": pinned, "tenant_id": tenant_id},
            {"_id": 0},
        )
        if doc:
            return doc
    # 2 · driver_id match (magic-link path)
    cursor = (
        db.dispatch_assignments
        .find(
            {
                "tenant_id": tenant_id,
                "driver_id": session["driver_id"],
                "current_state": {"$nin": [DLS.COMPLETE, DLS.OFF_SHIFT]},
                "cancelled_at": None,
            },
            {"_id": 0},
        )
        .sort("assigned_at", -1)
        .limit(1)
    )
    rows = await cursor.to_list(length=1)
    if rows:
        return rows[0]
    # 3 · iter401 truck_id fallback (self-start path)
    truck_id = (session.get("truck_id") or "").strip()
    if truck_id:
        cursor = (
            db.dispatch_assignments
            .find(
                {
                    "tenant_id": tenant_id,
                    "truck_id": truck_id,
                    "current_state": {"$nin": [DLS.COMPLETE, DLS.OFF_SHIFT]},
                    "cancelled_at": None,
                },
                {"_id": 0},
            )
            .sort("assigned_at", -1)
            .limit(1)
        )
        rows = await cursor.to_list(length=1)
        if rows:
            return rows[0]
    return None


# ════════════════════════════════════════════════════════════════════
# Router factory
# ════════════════════════════════════════════════════════════════════
def build_driver_router(
    db,
    require_dispatch_or_admin_dep: Callable[..., Awaitable[Dict[str, Any]]],
) -> APIRouter:
    router = APIRouter(prefix="/api/dispatch/driver", tags=["dispatch-driver"])
    require_driver = DS.make_require_driver_session(db)

    # ────────────────────────────────────────────────────────────────
    # iter401 · Phase 12.8 · Driver self-start operational entry
    # ────────────────────────────────────────────────────────────────
    @router.post("/start-shift")
    async def start_shift_route(
        body: StartShiftRequest,
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    ):
        """Public · driver self-starts a shift.

        No dispatcher action required. No password. The driver lands on
        ``/shift``, fills four short fields, taps Start Shift, and gets a
        shift-scoped session immediately.

        Identity model: the synthetic ``driver_id`` is ``shift-<12hex>``.
        Trucks rotate drivers; the truck_id is the operational continuity
        key — assignments owned by this truck become visible to whichever
        driver is currently shifted onto it.

        Idempotence-ish: if an active session already exists for the same
        (tenant, truck), the previous session is revoked (last driver
        wins) so an old phone left logged in doesn't keep a stale claim.
        """
        import uuid as _uuid
        tenant_id = _resolve_tenant(x_tenant_id)
        driver_name = body.driver_name.strip()
        truck_id = body.truck_id.strip()
        if not driver_name or not truck_id:
            raise HTTPException(400, "Driver name and truck number are required")

        # Last-driver-wins: revoke any active session on this truck.
        try:
            stale = db.dispatch_driver_sessions.find(
                {
                    "tenant_id": tenant_id,
                    "truck_id": truck_id,
                    "revoked_at": None,
                },
                {"_id": 0, "id": 1},
            )
            async for s in stale:
                await DS.revoke_driver_session(
                    db,
                    session_id=s["id"],
                    revoked_by_name=f"Truck claimed by {driver_name}",
                )
        except Exception:
            # Non-fatal — fresh session still issues; stale will TTL.
            pass

        synthetic_driver_id = f"shift-{_uuid.uuid4().hex[:12]}"
        session = await DS.create_driver_session(
            db,
            tenant_id=tenant_id,
            driver_id=synthetic_driver_id,
            driver_name=driver_name,
            truck_id=truck_id,
            assignment_id=None,
            issued_by_name=driver_name,
            origin="self_start",
            company=body.company or None,
            trailer_id=body.trailer_id or None,
            material=body.material or None,
            employee_id=body.employee_id or None,
            truck_unit_pk=body.truck_unit_pk or None,
            trailer_unit_pk=body.trailer_unit_pk or None,
        )

        # Land the driver directly on their assignment if one exists.
        assignment = None
        try:
            session_row = await db.dispatch_driver_sessions.find_one(
                {"id": session["session_id"]}, {"_id": 0},
            )
            if session_row:
                assignment = await _current_assignment_for_session(
                    db, session=session_row,
                )
        except Exception:
            assignment = None

        return {
            "ok": True,
            "driver_token": session["token"],
            "session_id": session["session_id"],
            "expires_at": session["expires_at"],
            "tenant_id": tenant_id,
            "driver": {
                "driver_id": synthetic_driver_id,
                "driver_name": driver_name,
            },
            "shift": {
                "truck_id": truck_id,
                "company": (body.company or "").strip() or None,
                "trailer_id": (body.trailer_id or "").strip() or None,
                "material": (body.material or "").strip() or None,
            },
            "assignment": assignment,
        }

    # ────────────────────────────────────────────────────────────────
    # iter402 · Phase 12.9 · Shift-start lookups (public · narrow scope)
    # ────────────────────────────────────────────────────────────────
    @router.get("/shift-lookups")
    async def shift_lookups_route(
        q: Optional[str] = None,
        limit: int = 25,
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    ):
        """Public · powers the iter402 Shift Start dropdowns.

        Returned shape:
          { drivers:  [{employee_id, name}]      // q required (≥ 2 chars)
            trucks:   [{unit_pk, unit_number, label, company}]
            trailers: [{unit_pk, unit_number, label, company}]
            haulers:  [{name}]                   // MASCI + distinct companies
          }

        Privacy contract:
          • Driver list NEVER returns the full employee roster.
            ``q`` < 2 chars → empty list. Limited to ``limit`` rows.
            Projection includes ONLY name + employee_id — no PII.
          • Truck / trailer lists are operational assets — fine to show.
          • Hauler list is composed at request time (no new collection).
        """
        import re as _re
        from lib.synthetic_hr_filter import apply_synthetic_hr_exclusion  # noqa: PLC0415
        tenant_id = _resolve_tenant(x_tenant_id)  # noqa: F841 · reserved for tenant-aware filtering when employees collect tenant_id
        cap = max(1, min(int(limit or 25), 50))
        q_clean = (q or "").strip()

        # ── drivers (privacy-restrained search) ─────────────────────
        drivers: List[Dict[str, Any]] = []
        if len(q_clean) >= 2:
            rx = {"$regex": _re.escape(q_clean), "$options": "i"}
            emp_query: Dict[str, Any] = apply_synthetic_hr_exclusion({
                "deleted_at": None,
                "$or": [
                    {"name": rx},
                    {"employee_id": rx},
                ],
            })
            # Best-effort: filter to active statuses if the field exists.
            # The DB still returns rows that pre-date lifecycle_status
                # (legacy) — those are operationally fine.
            try:
                cur = (
                    db.employees
                    .find(emp_query, {"_id": 0, "id": 1, "employee_id": 1, "name": 1, "lifecycle_status": 1, "is_active": 1})
                    .sort("name", 1)
                    .limit(cap)
                )
                async for emp in cur:
                    if emp.get("lifecycle_status") in (
                        "OFFBOARDED", "TERMINATED", "DECEASED",
                    ):
                        continue
                    if emp.get("is_active") is False:
                        continue
                    name = (emp.get("name") or "").strip()
                    if not name:
                        continue
                    drivers.append({
                        "employee_id": emp.get("employee_id") or emp.get("id") or "",
                        "name": name,
                    })
            except Exception:
                drivers = []

        # ── trucks + trailers (operational assets, full list) ───────
        truck_categories = [
            "Dump Trucks", "Tractor Trailer Trucks", "Service Trucks",
            "Pickup Trucks", "Flatbed Trucks", "Water Trucks",
            "Misc Trucks", "Supervisor / Mgmt Trucks",
        ]
        trailer_categories = ["Trailers"]
        unit_query: Dict[str, Any] = {
            "category": {"$in": truck_categories + trailer_categories},
        }
        if q_clean:
            rx = {"$regex": _re.escape(q_clean), "$options": "i"}
            unit_query["$or"] = [
                {"unit_number": rx},
                {"display_label": rx},
                {"make_model": rx},
            ]
        trucks: List[Dict[str, Any]] = []
        trailers: List[Dict[str, Any]] = []
        company_set: set[str] = {"MASCI"}
        try:
            cur = (
                db.equipment_master
                .find(unit_query, {"_id": 0, "id": 1, "unit_number": 1,
                                   "category": 1, "make_model": 1,
                                   "display_label": 1, "company": 1})
                .sort("unit_number", 1)
                .limit(max(cap * 4, 50))
            )
            async for u in cur:
                unit_pk = u.get("id") or ""
                num = (u.get("unit_number") or "").strip()
                if not num:
                    continue
                label = (u.get("display_label") or u.get("make_model") or "").strip()
                co = (u.get("company") or "").strip()
                if co:
                    company_set.add(co)
                entry = {
                    "unit_pk": unit_pk,
                    "unit_number": num,
                    "label": label,
                    "company": co or "",
                }
                if u.get("category") in trailer_categories:
                    if len(trailers) < cap:
                        trailers.append(entry)
                else:
                    if len(trucks) < cap:
                        trucks.append(entry)
        except Exception:
            pass

        haulers = [{"name": n} for n in sorted(company_set, key=lambda s: (s != "MASCI", s.lower()))]

        return {
            "ok": True,
            "drivers": drivers,
            "trucks": trucks,
            "trailers": trailers,
            "haulers": haulers,
        }

    # ────────────────────────────────────────────────────────────────
    # iter407 + iter408 · Phase 14.1 + 14.2 · Dispatcher assignment lookups
    # ────────────────────────────────────────────────────────────────
    @router.get("/assignment-lookups")
    async def assignment_lookups_route(
        actor: Dict[str, Any] = Depends(require_dispatch_or_admin_dep),  # noqa: ARG001
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    ):
        """Dispatcher-gated · powers the iter407 Create Assignment drawer.

        Phase 14.1 contract: every dropdown gets a useful starting list
        even on a brand-new tenant (seeded defaults + historical recents
        + platform master records). No empty boxes.

        Phase 14.2 contract: returns haul_types and equipment options
        so the drawer can pivot between Material and Equipment Move
        without a second round-trip.

        Returned shape (sketched):
          {
            haul_types: ["Material", "Equipment Move", ...],
            drivers:  [{employee_id, name, cdl, status}],
            trucks:   [{unit_pk, unit_number, label, company}],
            trailers: [...],
            equipment:[{unit_pk, unit_number, label, category, company}],
            carriers: [{name}],   // MASCI first
            projects: [{project_number, project_name}],
            sources:       [{label, source}],   // source ∈ {seed, history}
            destinations:  [{label, source}],
            pickup_locations:  [{label, source}],
            dropoff_locations: [{label, source}],
            materials: [{label, category, source}],
          }
        """
        import re as _re
        tenant_id = _resolve_tenant(x_tenant_id)

        # ── DRIVERS · CDL-qualified employees ───────────────────────
        # Dispatch is authenticated — no q≥2 privacy gate. Filter to
        # active drivers with any qualification signal so the list is
        # operationally relevant (CDL, approved company driver, or
        # active driver_status).
        drivers: List[Dict[str, Any]] = []
        try:
            cur = (
                db.employees
                .find(
                    {
                        "deleted_at": None,
                        "$or": [
                            {"cdl_holder": True},
                            {"approved_company_driver": True},
                            {"driver_status": "active"},
                        ],
                    },
                    {
                        "_id": 0, "id": 1, "employee_id": 1, "name": 1,
                        "lifecycle_status": 1, "is_active": 1,
                        "cdl_holder": 1, "approved_company_driver": 1,
                        "driver_status": 1,
                    },
                )
                .sort("name", 1)
                .limit(500)
            )
            async for emp in cur:
                if emp.get("lifecycle_status") in (
                    "OFFBOARDED", "TERMINATED", "DECEASED",
                ):
                    continue
                if emp.get("is_active") is False:
                    continue
                name = (emp.get("name") or "").strip()
                if not name:
                    continue
                drivers.append({
                    "employee_id": emp.get("employee_id") or emp.get("id") or "",
                    "name": name,
                    "cdl": bool(emp.get("cdl_holder")),
                    "approved": bool(emp.get("approved_company_driver")),
                    "driver_status": emp.get("driver_status") or "",
                })
        except Exception:
            drivers = []

        # ── TRUCKS / TRAILERS (operational assets) ──────────────────
        truck_categories = [
            "Dump Trucks", "Tractor Trailer Trucks", "Service Trucks",
            "Pickup Trucks", "Flatbed Trucks", "Water Trucks",
            "Misc Trucks", "Supervisor / Mgmt Trucks",
        ]
        trailer_categories = ["Trailers"]
        trucks: List[Dict[str, Any]] = []
        trailers: List[Dict[str, Any]] = []
        equipment: List[Dict[str, Any]] = []
        company_set: set[str] = {"MASCI"}
        try:
            cur = (
                db.equipment_master
                .find(
                    {"category": {"$nin": [None, ""]}},
                    {"_id": 0, "id": 1, "unit_number": 1, "category": 1,
                     "make_model": 1, "display_label": 1, "company": 1},
                )
                .sort("unit_number", 1)
                .limit(2000)
            )
            async for u in cur:
                unit_pk = u.get("id") or ""
                num = (u.get("unit_number") or "").strip()
                if not num:
                    continue
                label = (u.get("display_label") or u.get("make_model") or "").strip()
                co = (u.get("company") or "").strip()
                if co:
                    company_set.add(co)
                entry = {
                    "unit_pk": unit_pk,
                    "unit_number": num,
                    "label": label,
                    "company": co or "",
                    "category": u.get("category") or "",
                }
                cat = u.get("category") or ""
                if cat in truck_categories:
                    if len(trucks) < 200:
                        trucks.append(entry)
                elif cat in trailer_categories:
                    if len(trailers) < 200:
                        trailers.append(entry)
                else:
                    # iter408 · everything that isn't a truck/trailer
                    # is candidate equipment-move cargo (lowboy haul).
                    if len(equipment) < 400:
                        equipment.append(entry)
        except Exception:
            pass

        # ── PROJECTS · daily_reports distinct values + dispatch history
        project_pairs: Dict[str, str] = {}
        try:
            pipeline = [
                {"$match": {"project_number": {"$nin": [None, ""]}}},
                {"$group": {
                    "_id": "$project_number",
                    "project_name": {"$last": "$project_name"},
                    "last_at": {"$max": "$report_date"},
                }},
                {"$sort": {"last_at": -1}},
                {"$limit": 200},
            ]
            async for row in db.daily_reports.aggregate(pipeline):
                pn = (row.get("_id") or "").strip()
                if pn and pn not in project_pairs:
                    project_pairs[pn] = (row.get("project_name") or "").strip()
        except Exception:
            pass
        # Merge any project_numbers seen ONLY on dispatch_assignments
        try:
            pipeline = [
                {"$match": {"tenant_id": tenant_id, "project_number": {"$nin": [None, ""]}}},
                {"$group": {
                    "_id": "$project_number",
                    "project_name": {"$last": "$project_name"},
                    "last_at": {"$max": "$assigned_at"},
                }},
                {"$sort": {"last_at": -1}},
                {"$limit": 100},
            ]
            async for row in db.dispatch_assignments.aggregate(pipeline):
                pn = (row.get("_id") or "").strip()
                if pn and pn not in project_pairs:
                    project_pairs[pn] = (row.get("project_name") or "").strip()
        except Exception:
            pass
        projects = [
            {"project_number": k, "project_name": v}
            for k, v in project_pairs.items()
        ]

        # ── Helper · merge seeded + historical into {label, source} ─
        async def _merge_seed_and_history(
            seed: List[str], field: str, *, cap_history: int = 25,
        ) -> List[Dict[str, Any]]:
            history: List[str] = []
            try:
                pipeline = [
                    {"$match": {
                        "tenant_id": tenant_id,
                        field: {"$nin": [None, ""]},
                    }},
                    {"$sort": {"assigned_at": -1}},
                    {"$group": {
                        "_id": f"${field}",
                        "last_at": {"$max": "$assigned_at"},
                    }},
                    {"$sort": {"last_at": -1}},
                    {"$limit": cap_history},
                ]
                async for row in db.dispatch_assignments.aggregate(pipeline):
                    v = (row.get("_id") or "").strip()
                    if v:
                        history.append(v)
            except Exception:
                history = []
            seen: set[str] = set()
            merged: List[Dict[str, Any]] = []
            for label in seed:
                key = label.lower()
                if key in seen:
                    continue
                seen.add(key)
                merged.append({"label": label, "source": "seed"})
            for label in history:
                key = label.lower()
                if key in seen:
                    continue
                seen.add(key)
                merged.append({"label": label, "source": "history"})
            return merged

        sources = await _merge_seed_and_history(SEEDED_SOURCES, "source_location")
        destinations = await _merge_seed_and_history(SEEDED_DESTINATIONS, "destination")
        pickup_locations = await _merge_seed_and_history(
            SEEDED_PICKUP_LOCATIONS, "pickup_location",
        )
        dropoff_locations = await _merge_seed_and_history(
            SEEDED_DROPOFF_LOCATIONS, "dropoff_location",
        )
        # iter410 · Phase 15.1 · Tanker terminal / destination continuity.
        # Tanker source values reuse the canonical `source_location` field
        # on the assignment doc; seeded terminal list is the operational
        # floor and historical tanker hauls layer in via the same field.
        tanker_sources = await _merge_seed_and_history(
            SEEDED_TANKER_SOURCES, "source_location",
        )
        tanker_destinations = await _merge_seed_and_history(
            SEEDED_TANKER_DESTINATIONS, "destination",
        )

        # ── Materials · catalog + historical ────────────────────────
        material_options: List[Dict[str, Any]] = []
        seen_mat: set[str] = set()
        for opt in flat_material_options():
            key = opt["label"].lower()
            if key in seen_mat:
                continue
            seen_mat.add(key)
            material_options.append({
                "label": opt["label"],
                "category": opt["category"],
                "source": "seed",
            })
        try:
            pipeline = [
                {"$match": {
                    "tenant_id": tenant_id,
                    "material": {"$nin": [None, ""]},
                }},
                {"$sort": {"assigned_at": -1}},
                {"$group": {
                    "_id": "$material",
                    "last_at": {"$max": "$assigned_at"},
                }},
                {"$sort": {"last_at": -1}},
                {"$limit": 50},
            ]
            async for row in db.dispatch_assignments.aggregate(pipeline):
                v = (row.get("_id") or "").strip()
                if not v:
                    continue
                key = v.lower()
                if key in seen_mat:
                    continue
                seen_mat.add(key)
                material_options.append({
                    "label": v,
                    "category": "Historical",
                    "source": "history",
                })
        except Exception:
            pass

        carriers = [
            {"name": n}
            for n in sorted(company_set, key=lambda s: (s != "MASCI", s.lower()))
        ]

        # iter410 · Phase 15.1 · Liquid product catalog + history merge
        liquid_products: List[Dict[str, Any]] = []
        seen_liquid: set[str] = set()
        for opt in flat_liquid_product_options():
            key = opt["label"].lower()
            if key in seen_liquid:
                continue
            seen_liquid.add(key)
            liquid_products.append({
                "label": opt["label"],
                "category": opt["category"],
                "source": "seed",
            })
        try:
            pipeline = [
                {"$match": {
                    "tenant_id": tenant_id,
                    "liquid_product": {"$nin": [None, ""]},
                }},
                {"$sort": {"assigned_at": -1}},
                {"$group": {
                    "_id": "$liquid_product",
                    "last_at": {"$max": "$assigned_at"},
                }},
                {"$sort": {"last_at": -1}},
                {"$limit": 25},
            ]
            async for row in db.dispatch_assignments.aggregate(pipeline):
                v = (row.get("_id") or "").strip()
                if not v:
                    continue
                key = v.lower()
                if key in seen_liquid:
                    continue
                seen_liquid.add(key)
                liquid_products.append({
                    "label": v,
                    "category": "Historical",
                    "source": "history",
                })
        except Exception:
            pass

        return {
            "ok": True,
            "tenant_id": tenant_id,
            "haul_types": HAUL_TYPES,
            "drivers": drivers,
            "trucks": trucks,
            "trailers": trailers,
            "equipment": equipment,
            "equipment_examples": EQUIPMENT_MOVE_EXAMPLE_LABELS,
            "equipment_categories": EQUIPMENT_MOVE_CATEGORIES,
            "carriers": carriers,
            "projects": projects,
            "sources": sources,
            "destinations": destinations,
            "pickup_locations": pickup_locations,
            "dropoff_locations": dropoff_locations,
            "materials": material_options,
            # iter410 · Phase 15.1 · Tanker / Liquid Asphalt continuity
            "tanker_sources": tanker_sources,
            "tanker_destinations": tanker_destinations,
            "liquid_products": liquid_products,
            # iter407 backward-compat aliases — DispatchBoard's old
            # consumer still expects these names.
            "recent_projects": projects,
            "recent_materials": [
                {"label": m["label"]} for m in material_options if m["source"] == "history"
            ],
            "recent_sources": [
                {"label": s["label"]} for s in sources if s["source"] == "history"
            ],
            "recent_destinations": [
                {"label": d["label"]} for d in destinations if d["source"] == "history"
            ],
        }

    # ────────────────────────────────────────────────────────────────
    # Magic link issuance (dispatch/admin) and exchange (public)
    # ────────────────────────────────────────────────────────────────
    @router.post("/magic-link")
    async def issue_magic_link_route(
        body: MagicLinkRequest,
        request: Request,
        actor: Dict[str, Any] = Depends(require_dispatch_or_admin_dep),
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    ):
        tenant_id = _resolve_tenant(x_tenant_id)
        try:
            result = await DS.issue_magic_link(
                db,
                tenant_id=tenant_id,
                driver_id=body.driver_id.strip(),
                driver_name=(body.driver_name or "").strip(),
                truck_id=(body.truck_id or "").strip() or None,
                assignment_id=(body.assignment_id or "").strip() or None,
                issued_by_name=(actor.get("name") or actor.get("email") or "Dispatch"),
                issued_by_role=actor.get("_actor") or "dispatch",
            )
        except DS.DriverIneligibleError as e:
            # iter437 Phase Sigma-III · structured rejection codes for the
            # dispatch UI so it can surface "driver disabled" vs "not found"
            # vs "id missing" distinctly.
            raise HTTPException(
                status_code=404 if e.code == "driver_not_found" else 400,
                detail={"code": e.code, "message": e.message},
            )
        return {
            "ok": True,
            "link_id": result["link_id"],
            "magic_token": result["token"],
            "expires_at": result["expires_at"],
            "url": _public_link_for(request, result["token"]),
            "ttl_seconds": DS.MAGIC_TOKEN_TTL_SECONDS,
        }

    @router.post("/session/exchange")
    async def exchange_magic_link_route(
        body: SessionExchangeRequest,
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    ):
        # Magic links are tenant-aware but the URL itself doesn't
        # encode tenant — header (default masci) decides scope.
        tenant_id = _resolve_tenant(x_tenant_id)
        link = await DS.consume_magic_link(
            db, raw_token=body.magic_token, tenant_id=tenant_id,
        )
        if not link:
            raise HTTPException(401, "Magic link invalid, used, or expired")

        session = await DS.create_driver_session(
            db,
            tenant_id=link["tenant_id"],
            driver_id=link["driver_id"],
            driver_name=link.get("driver_name") or "",
            truck_id=link.get("truck_id"),
            assignment_id=link.get("assignment_id"),
            issued_by_name=link.get("issued_by_name") or "",
        )
        await DS.mark_magic_link_used(
            db, link_id=link["id"], session_id=session["session_id"],
        )

        # Best-effort: also return the current assignment so the
        # driver UI lands directly on the shift screen.
        assignment = None
        try:
            session_row = await db.dispatch_driver_sessions.find_one(
                {"id": session["session_id"]}, {"_id": 0},
            )
            if session_row:
                assignment = await _current_assignment_for_session(
                    db, session=session_row,
                )
        except Exception:
            assignment = None

        return {
            "ok": True,
            "driver_token": session["token"],
            "session_id": session["session_id"],
            "expires_at": session["expires_at"],
            "tenant_id": link["tenant_id"],
            "driver": {
                "driver_id": link["driver_id"],
                "driver_name": link.get("driver_name") or "",
            },
            "assignment": assignment,
        }

    # ────────────────────────────────────────────────────────────────
    # Driver self-service reads
    # ────────────────────────────────────────────────────────────────
    @router.get("/me")
    async def driver_me(
        session: Dict[str, Any] = Depends(require_driver),
    ):
        return {
            "ok": True,
            "session": {
                "id": session["id"],
                "tenant_id": session["tenant_id"],
                "driver_id": session["driver_id"],
                "driver_name": session.get("driver_name") or "",
                "truck_id": session.get("truck_id"),
                "issued_at": session.get("issued_at"),
                "expires_at": session.get("expires_at"),
                "last_seen_at": session.get("last_seen_at"),
            },
        }

    @router.get("/my-assignment")
    async def driver_my_assignment(
        session: Dict[str, Any] = Depends(require_driver),
    ):
        assignment = await _current_assignment_for_session(db, session=session)
        if not assignment:
            return {
                "ok": True,
                "assignment": None,
                "allowed_next_states": [],
                "lifecycle_states": DLS.CANONICAL_STATES,
            }
        return {
            "ok": True,
            "assignment": assignment,
            "allowed_next_states": DLS.allowed_next_states(
                assignment.get("current_state") or "",
            ),
            "lifecycle_states": DLS.CANONICAL_STATES,
        }

    @router.post("/assignments/{assignment_id}/transition")
    async def driver_transition(
        assignment_id: str,
        body: DriverTransitionRequest,
        session: Dict[str, Any] = Depends(require_driver),
    ):
        tenant_id = session["tenant_id"]
        assignment = await db.dispatch_assignments.find_one(
            {"id": assignment_id, "tenant_id": tenant_id}, {"_id": 0},
        )
        if not assignment:
            raise HTTPException(404, "Assignment not found")
        # Scope: drivers can only transition assignments tied to them
        # OR — iter401 self-start path — assignments owned by the same
        # truck this driver is currently shifted onto. Trucks rotate
        # drivers; operational continuity follows the truck.
        if assignment.get("driver_id") and assignment["driver_id"] != session["driver_id"]:
            truck_id = (session.get("truck_id") or "").strip()
            if not truck_id or assignment.get("truck_id") != truck_id:
                raise HTTPException(
                    403,
                    "Driver session is not authorized for this assignment",
                )
        if assignment.get("cancelled_at"):
            raise HTTPException(409, "Assignment is cancelled")

        actor = {
            "_actor": "driver",
            "name": session.get("driver_name") or "Driver",
        }
        updated = await _record_transition(
            db,
            assignment=assignment,
            to_state=body.to_state.strip(),
            actor=actor,
            note=body.note or "",
            correction_reason=body.correction_reason or "",
            wait_reason=body.wait_reason or "",
            geo=body.geo,
        )
        latest = (updated.get("state_history") or [])[-1] if updated else None
        return {
            "ok": True,
            "assignment": updated,
            "transition": latest,
            "allowed_next_states": DLS.allowed_next_states(
                (updated or {}).get("current_state") or "",
            ),
        }

    # ────────────────────────────────────────────────────────────────
    # D-1.1 / D-1.5 · DRIVER ACKNOWLEDGEMENT
    # ────────────────────────────────────────────────────────────────
    @router.post("/assignments/{assignment_id}/acknowledge")
    async def driver_acknowledge(
        assignment_id: str,
        body: DriverAckRequest,
        request: Request,
        session: Dict[str, Any] = Depends(require_driver),
    ):
        """Driver taps the ACK card. Reuses ``_record_acknowledgement``
        from the lifecycle router so the audit pipeline stays
        single-sourced.

        Re-ack flow (D-1.5): when ``target_revision_seq`` is provided,
        the driver is confirming they read revision N. Server only
        clears revision_pending when the target matches the current
        revision_seq on the assignment.
        """
        tenant_id = session["tenant_id"]
        assignment = await db.dispatch_assignments.find_one(
            {"id": assignment_id, "tenant_id": tenant_id}, {"_id": 0},
        )
        if not assignment:
            raise HTTPException(404, "Assignment not found")
        # Same scope check as transition: driver tied to assignment OR
        # owning the truck this driver is shifted onto.
        if assignment.get("driver_id") and assignment["driver_id"] != session["driver_id"]:
            truck_id = (session.get("truck_id") or "").strip()
            if not truck_id or assignment.get("truck_id") != truck_id:
                raise HTTPException(
                    403,
                    "Driver session is not authorized for this assignment",
                )
        if assignment.get("cancelled_at"):
            raise HTTPException(409, "Assignment is cancelled")

        # Device default = User-Agent (truncated).
        device = (body.device or request.headers.get("User-Agent") or "")[:240]
        method = (body.method or "tap").strip() or "tap"
        actor = {
            "_actor": "driver",
            "name": session.get("driver_name") or "Driver",
        }
        updated = await _record_acknowledgement(
            db,
            assignment=assignment,
            actor=actor,
            method=method,
            device=device,
            note=body.note or "",
            target_revision=body.target_revision_seq,
        )
        return {
            "ok": True,
            "assignment": updated,
            "allowed_next_states": DLS.allowed_next_states(
                (updated or {}).get("current_state") or "",
            ),
        }

    # ────────────────────────────────────────────────────────────────
    # Dispatcher management of driver sessions
    # ────────────────────────────────────────────────────────────────
    @router.get("/sessions")
    async def list_sessions(
        actor: Dict[str, Any] = Depends(require_dispatch_or_admin_dep),  # noqa: ARG001
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
        active_only: bool = True,
        limit: int = 100,
    ):
        tenant_id = _resolve_tenant(x_tenant_id)
        query: Dict[str, Any] = {"tenant_id": tenant_id}
        if active_only:
            query["revoked_at"] = None
        limit = max(1, min(int(limit or 100), 500))
        cursor = (
            db.dispatch_driver_sessions
            .find(query, {"_id": 0})
            .sort("issued_at", -1)
            .limit(limit)
        )
        rows: List[Dict[str, Any]] = await cursor.to_list(length=limit)
        # Drop the native datetime field — not JSON serializable.
        for r in rows:
            r.pop("expires_at_ts", None)
        return {
            "ok": True,
            "tenant_id": tenant_id,
            "count": len(rows),
            "sessions": rows,
        }

    @router.post("/sessions/{session_id}/revoke")
    async def revoke_session(
        session_id: str,
        actor: Dict[str, Any] = Depends(require_dispatch_or_admin_dep),
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    ):
        tenant_id = _resolve_tenant(x_tenant_id)
        # Optional tenant guard — ensure the session belongs to the
        # caller's tenant. Cheap one-document lookup.
        row = await db.dispatch_driver_sessions.find_one(
            {"id": session_id, "tenant_id": tenant_id}, {"_id": 0},
        )
        if not row:
            raise HTTPException(404, "Session not found")
        revoked = await DS.revoke_driver_session(
            db,
            session_id=session_id,
            revoked_by_name=actor.get("name") or actor.get("email") or "Dispatch",
        )
        return {"ok": True, "revoked": revoked, "session_id": session_id}

    return router


__all__ = ["build_driver_router"]
