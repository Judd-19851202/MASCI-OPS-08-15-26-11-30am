"""Sprint A · DocExp-60/90 + Future-Day Dispatch — read-only endpoints.

Two endpoints. Zero new collections. Reuse existing
`document_expirations`, `safety_training_records`, and
`dispatch_assignments` only.

Endpoints (admin-strict; HR / Safety reuse the existing
multi-portal actor dep where wired by server.py):

  GET /api/operations/expirations/summary
      band counts + per-band sample list (≤ 25 per band)
      bands: expired | in_30 | in_60 | in_90 | healthy

  GET /api/operations/dispatch/by-day?bucket=today|tomorrow|upcoming|all
      buckets `assigned_at` into the requested day; existing
      `current_state` semantics preserved (read-only filter).
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Query


def _band(today: str, exp: str) -> str:
    """today, exp are ISO date strings (YYYY-MM-DD)."""
    if not exp:
        return "healthy"
    if exp < today:
        return "expired"
    # gap days
    try:
        d_today = datetime.fromisoformat(today)
        d_exp = datetime.fromisoformat(exp[:10])
        gap = (d_exp - d_today).days
    except Exception:
        return "healthy"
    if gap <= 30:
        return "in_30"
    if gap <= 60:
        return "in_60"
    if gap <= 90:
        return "in_90"
    return "healthy"


def register_sprint_a_routes(api_router: APIRouter, db, require_actor) -> None:

    @api_router.get("/operations/expirations/summary")
    async def expirations_summary(actor: Any = Depends(require_actor)):
        now = datetime.now(timezone.utc)
        today = now.date().isoformat()

        bands = {"expired": [], "in_30": [], "in_60": [], "in_90": [], "healthy": []}
        counts = {k: 0 for k in bands}

        async def _absorb(src_name, doc, title, exp_date, owner_name, owner_id, kind):
            band = _band(today, (exp_date or "")[:10])
            counts[band] += 1
            if len(bands[band]) < 25:
                bands[band].append({
                    "source": src_name,
                    "id": doc.get("id"),
                    "title": title or kind or "—",
                    "kind": kind,
                    "expiration_date": exp_date,
                    "owner_name": owner_name,
                    "owner_id": owner_id,
                })

        # document_expirations
        async for d in db.document_expirations.find(
            {"deleted_at": None,
             "expiration_date": {"$nin": [None, ""]}},
            {"_id": 0, "id": 1, "title": 1, "document_type": 1, "category": 1,
             "expiration_date": 1, "linked_employee_id": 1,
             "linked_employee_name": 1, "linked_equipment_id": 1},
        ):
            await _absorb(
                "document_expirations", d,
                d.get("title") or d.get("document_type") or d.get("category"),
                d.get("expiration_date"),
                d.get("linked_employee_name") or "",
                d.get("linked_employee_id") or d.get("linked_equipment_id") or "",
                d.get("category") or d.get("document_type") or "Document",
            )

        # safety_training_records
        async for t in db.safety_training_records.find(
            {"expiration_date": {"$nin": [None, ""]}},
            {"_id": 0, "id": 1, "training_name": 1, "certification_type": 1,
             "expiration_date": 1, "employee_id": 1, "employee_name": 1},
        ):
            await _absorb(
                "safety_training_records", t,
                t.get("training_name") or t.get("certification_type"),
                t.get("expiration_date"),
                t.get("employee_name") or "",
                t.get("employee_id") or "",
                t.get("certification_type") or "Training",
            )

        return {
            "as_of": now.isoformat(),
            "counts": counts,
            "bands": bands,
            "thresholds": {"expired_max": "today",
                            "in_30_max_days": 30,
                            "in_60_max_days": 60,
                            "in_90_max_days": 90},
        }

    @api_router.get("/operations/dispatch/by-day")
    async def dispatch_by_day(
        actor: Any = Depends(require_actor),
        bucket: str = Query("today", pattern="^(today|tomorrow|upcoming|all)$"),
        limit: int = Query(300, le=1000),
    ):
        now = datetime.now(timezone.utc)
        today_str = now.date().isoformat()
        tomorrow_str = (now + timedelta(days=1)).date().isoformat()

        # Filter strategy: prefer explicit scheduled_for if any future-dated
        # `assigned_at` is in the future; otherwise fall back to assigned_at
        # date.  Honesty caveat: existing dispatch_assignments do not carry
        # a separate scheduled-future-date column — this endpoint surfaces
        # what's already in `assigned_at`.

        match: Dict[str, Any] = {}
        if bucket == "today":
            match["assigned_at"] = {
                "$gte": today_str + "T00:00:00",
                "$lt":  tomorrow_str + "T00:00:00",
            }
        elif bucket == "tomorrow":
            day_after = (now + timedelta(days=2)).date().isoformat()
            match["assigned_at"] = {
                "$gte": tomorrow_str + "T00:00:00",
                "$lt":  day_after + "T00:00:00",
            }
        elif bucket == "upcoming":
            day_after = (now + timedelta(days=2)).date().isoformat()
            match["assigned_at"] = {"$gte": day_after + "T00:00:00"}
        # all → no filter

        rows: List[Dict[str, Any]] = []
        async for a in db.dispatch_assignments.find(
            match,
            {"_id": 0, "id": 1, "driver_id": 1, "driver_name": 1,
             "truck_id": 1, "equipment_id": 1, "equipment_label": 1,
             "project_number": 1, "project_name": 1, "material": 1,
             "pickup_location": 1, "dropoff_location": 1,
             "current_state": 1, "assigned_at": 1, "last_transition_at": 1},
        ).sort("assigned_at", -1).limit(limit):
            rows.append(a)

        # Coverage rollups (jobs without coverage + double-booked drivers
        # within the same bucket).
        jobs_covered = {(r.get("project_number") or "") for r in rows if r.get("project_number")}
        driver_counts: Dict[str, int] = {}
        truck_counts: Dict[str, int] = {}
        for r in rows:
            d = r.get("driver_id") or ""
            t = r.get("truck_id") or ""
            if d:
                driver_counts[d] = driver_counts.get(d, 0) + 1
            if t:
                truck_counts[t] = truck_counts.get(t, 0) + 1
        conflicts = {
            "drivers_double_booked": [d for d, c in driver_counts.items() if c > 1],
            "trucks_double_booked": [t for t, c in truck_counts.items() if c > 1],
        }

        return {
            "bucket": bucket,
            "as_of": now.isoformat(),
            "count": len(rows),
            "assignments": rows,
            "coverage": {
                "jobs_with_coverage": sorted(jobs_covered),
                "job_count": len(jobs_covered),
            },
            "conflicts": conflicts,
        }


__all__ = ["register_sprint_a_routes"]
