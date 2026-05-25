"""routes/last_activity.py — iter440 · last_activity probe.

Returns the timestamp of the most recent operational WRITE for a
given portal kind. Powers the calm one-line "Last submission · N
minutes ago" indicator on each role hub.

Doctrine
--------
- Read-only · NEVER counts or aggregates beyond a single timestamp
- Per-portal scoping · operationally-meaningful collections only
- NEVER touches `field_memory_notes` (those are wisdom, not activity)
- NEVER mixes portals (Dispatch sees Dispatch, Shop sees Shop, etc.)
- 7-day lookback cap · returns null if nothing recent
- Available to ANY portal token (read-only)
- Calm output · single optional timestamp + a human-readable kind label
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException


# Portal → collections that count as "operational activity" for that
# portal. The order matters: first match wins (we surface whichever
# write happened most recently). All listed collections use
# `created_at` as an ISO-string field.
_PORTAL_MAP: Dict[str, list[Dict[str, str]]] = {
    "field_leadership": [
        {"collection": "daily_reports", "field": "created_at", "label": "Daily report filed"},
        {"collection": "inspections", "field": "created_at", "label": "Inspection filed"},
        {"collection": "incidents", "field": "created_at", "label": "Incident filed"},
    ],
    "dispatch": [
        {"collection": "dispatch_continuity_events", "field": "captured_at", "label": "Operational moment logged"},
        {"collection": "dispatch_assignments", "field": "created_at", "label": "Assignment created"},
    ],
    "pm": [
        {"collection": "daily_reports", "field": "created_at", "label": "Daily report filed"},
        {"collection": "inspections", "field": "created_at", "label": "Inspection filed"},
    ],
    "shop": [
        {"collection": "equipment_inspections", "field": "created_at", "label": "Equipment inspection filed"},
        {"collection": "dispatch_continuity_events", "field": "captured_at", "label": "Recovery moment logged"},
    ],
    "safety": [
        {"collection": "inspections", "field": "created_at", "label": "Inspection filed"},
        {"collection": "incidents", "field": "created_at", "label": "Incident filed"},
        {"collection": "qaqc_inspections", "field": "created_at", "label": "QA/QC inspection filed"},
    ],
    "admin": [
        {"collection": "daily_reports", "field": "created_at", "label": "Daily report filed"},
        {"collection": "inspections", "field": "created_at", "label": "Inspection filed"},
        {"collection": "dispatch_continuity_events", "field": "captured_at", "label": "Operational moment logged"},
        {"collection": "incidents", "field": "created_at", "label": "Incident filed"},
    ],
}

_LOOKBACK_DAYS = 7
_VALID_PORTALS = set(_PORTAL_MAP.keys())


def _parse_iso(s: Any) -> Optional[datetime]:
    if not s:
        return None
    if isinstance(s, datetime):
        return s if s.tzinfo else s.replace(tzinfo=timezone.utc)
    try:
        # ISO 8601 · possibly with Z
        v = s.rstrip("Z") + ("+00:00" if str(s).endswith("Z") else "")
        d = datetime.fromisoformat(v)
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def build_last_activity_router(*, db, require_any_portal_token_dep) -> APIRouter:
    router = APIRouter(prefix="/api/diag", tags=["diag"])

    @router.get("/last-activity")
    async def last_activity(
        portal: str = "admin",
        _actor: Any = Depends(require_any_portal_token_dep),  # noqa: ARG001
    ) -> Dict[str, Any]:
        portal = (portal or "").strip().lower()
        if portal not in _VALID_PORTALS:
            raise HTTPException(400, f"portal must be one of {sorted(_VALID_PORTALS)}")
        cutoff = datetime.now(timezone.utc) - timedelta(days=_LOOKBACK_DAYS)
        candidates: list[Dict[str, Any]] = []
        for spec in _PORTAL_MAP[portal]:
            try:
                coll = db[spec["collection"]]
                # We use {field: {$gte: cutoff_iso}} so the query is an
                # index hit if the field is indexed. created_at is
                # stored as ISO string in this codebase so we compare
                # lexicographically (ISO 8601 is sort-stable).
                doc = await coll.find_one(
                    {spec["field"]: {"$gte": cutoff.isoformat()}},
                    sort=[(spec["field"], -1)],
                    projection={"_id": 0, spec["field"]: 1},
                )
                if doc and doc.get(spec["field"]):
                    candidates.append({
                        "at_iso": doc[spec["field"]],
                        "label": spec["label"],
                        "kind": spec["collection"],
                    })
            except Exception:
                # Silent · operational continuity · one bad collection
                # MUST NOT take down the indicator.
                continue
        if not candidates:
            return {"portal": portal, "last_activity_at": None, "label": None, "kind": None}
        # Pick the lexicographically-latest ISO timestamp (works because
        # all candidates are timezone-aware ISO 8601).
        best = max(candidates, key=lambda c: c["at_iso"])
        return {
            "portal": portal,
            "last_activity_at": best["at_iso"],
            "label": best["label"],
            "kind": best["kind"],
        }

    return router
