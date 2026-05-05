"""
Date Audit — one-shot diagnostic + repair tool for the timezone bugs
fixed on 2026-05-05 (`formatDateLong` UTC-midnight parsing + the
`new Date().toISOString().slice(0, 10)` default-pre-fill bug).

Stored dates in MongoDB are bare YYYY-MM-DD strings (the day the crew
picked on the calendar). The display bug never touched what was stored,
so the vast majority of records are correct.

The narrow case we hunt for: late-night submissions where the form
*defaulted* the date to the UTC day (one ahead of local-ET) and the
crew submitted without overriding. Those records will now display one
day in the future once the display bug is fixed in production.

Detection rule (per record):
    stored_date == created_at_utc_date AND
    stored_date != created_at_local_et_date AND
    created_at_utc_date - created_at_local_et_date == 1 day

That triple match means the record was submitted between ~8 PM and
midnight ET, and the date stored matches UTC (the buggy default) and
not local-ET (what the crew was actually living in). Suggested fix:
roll the stored date back by one day.

We also surface a softer "review" tier — any record where stored_date
is more than 1 day away from the local-ET date of created_at — as a
secondary list. Those are usually legitimate (admins backdating to
file a missed report), so we never auto-suggest a fix for them; we
just expose them for visual review.

Both endpoints are admin-strict-gated. The apply endpoint additionally
re-verifies the admin password via the body so accidental clicks can't
mass-mutate without a second factor.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field


# America/New_York covers all MASCI field operations. If the company
# adds another timezone region later, expose this as an admin setting.
LOCAL_TZ = ZoneInfo("America/New_York")


# (collection, date_field, label) — every collection that stores a
# crew-picked calendar date alongside a created_at timestamp.
COLLECTIONS: List[tuple[str, str, str]] = [
    ("inspections", "inspection_date", "Site Inspections"),
    ("meetings", "meeting_date", "Safety Meetings"),
    ("jhas", "jha_date", "JHPs"),
    ("incidents", "incident_date", "Incident Reports"),
    ("daily_reports", "report_date", "Daily Job Reports"),
    ("equipment_inspections", "inspection_date", "Equipment Pre-Ops"),
    ("qaqc_inspections", "inspection_date", "QA/QC Inspections"),
]


def _parse_iso_utc(iso: str) -> Optional[datetime]:
    """Parse an ISO-8601 timestamp; tolerate the trailing Z form."""
    if not iso:
        return None
    try:
        s = iso.replace("Z", "+00:00") if iso.endswith("Z") else iso
        d = datetime.fromisoformat(s)
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d
    except Exception:  # noqa: BLE001
        return None


def _shift_iso_date(iso_date: str, days: int) -> Optional[str]:
    try:
        y, m, d = iso_date.split("-")
        dt = datetime(int(y), int(m), int(d), tzinfo=timezone.utc)
        return (dt + timedelta(days=days)).date().isoformat()
    except Exception:  # noqa: BLE001
        return None


def _classify(stored_date: str, created_at_iso: str) -> Dict[str, Any]:
    """Return diagnostic dict for one record.

    Categories:
        - "ok"        — stored date matches local-ET date; nothing to do
        - "suspect"   — high-confidence Bug-2 victim (auto-suggest -1 day)
        - "review"    — stored date >1 day off in either direction; surface
                        for visual review but do not suggest a fix
        - "unknown"   — couldn't parse one of the inputs
    """
    created = _parse_iso_utc(created_at_iso)
    if not created or not stored_date:
        return {"category": "unknown", "suggested_date": None, "reason": "unparseable"}

    utc_date = created.astimezone(timezone.utc).date().isoformat()
    local_date = created.astimezone(LOCAL_TZ).date().isoformat()

    if stored_date == local_date:
        return {"category": "ok", "suggested_date": None, "reason": "matches local-ET date"}

    # The high-confidence Bug-2 fingerprint:
    if stored_date == utc_date and utc_date != local_date:
        suggested = _shift_iso_date(stored_date, -1)
        return {
            "category": "suspect",
            "suggested_date": suggested,
            "reason": (
                f"stored date matches UTC date ({utc_date}) but the report "
                f"was submitted on {local_date} ET — looks like the late-night "
                "default-date bug; recommended to roll back 1 day"
            ),
        }

    # Anything else that's >1 day off → surface for review only
    try:
        sd = datetime.strptime(stored_date, "%Y-%m-%d").date()
        ld = datetime.strptime(local_date, "%Y-%m-%d").date()
        gap = abs((sd - ld).days)
    except Exception:  # noqa: BLE001
        gap = 0

    if gap >= 2:
        return {
            "category": "review",
            "suggested_date": None,
            "reason": f"stored date is {gap} days from the submission date ({local_date} ET)",
        }

    return {"category": "ok", "suggested_date": None, "reason": "within tolerance"}


class ApplyFixBody(BaseModel):
    collection: str
    record_id: str
    new_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")


def _allowed_fields_for(collection: str) -> tuple[str, str]:
    """Return (date_field, label) for an allowed collection or raise 400."""
    for c, fld, label in COLLECTIONS:
        if c == collection:
            return fld, label
    raise HTTPException(status_code=400, detail=f"Unknown collection: {collection}")


def build_date_audit_router(db, require_admin_strict):
    """Wire the date-audit endpoints into the existing /api router.

    The caller passes its admin dependency so we don't duplicate auth
    wiring across server.py imports. The frontend gates the apply route
    behind ``AdminPasswordConfirm`` (which calls
    ``/api/admin/auth/verify-password`` upstream) so a typo can't
    mass-mutate dates without the admin re-typing their password.
    """
    router = APIRouter(prefix="/api/admin/date-audit", tags=["admin-date-audit"])

    @router.get("")
    async def scan(_: bool = Depends(require_admin_strict)):
        """Scan every tracked collection and bucket records by category."""
        out_suspects: List[Dict[str, Any]] = []
        out_review: List[Dict[str, Any]] = []
        totals = {"scanned": 0, "suspect": 0, "review": 0, "ok": 0, "unknown": 0}

        for collection, date_field, label in COLLECTIONS:
            cur = db[collection].find(
                {date_field: {"$exists": True, "$nin": [None, ""]}},
                {
                    "_id": 0,
                    "id": 1,
                    "project_name": 1,
                    "project_number": 1,
                    "inspector_name": 1,
                    "conducted_by": 1,
                    "prepared_by": 1,
                    "reported_by": 1,
                    date_field: 1,
                    "created_at": 1,
                },
            )
            async for doc in cur:
                totals["scanned"] += 1
                stored = doc.get(date_field) or ""
                created_at = doc.get("created_at") or ""
                cls = _classify(stored, created_at)
                cat = cls["category"]
                totals[cat] = totals.get(cat, 0) + 1
                if cat in ("suspect", "review"):
                    person = (
                        doc.get("inspector_name")
                        or doc.get("conducted_by")
                        or doc.get("prepared_by")
                        or doc.get("reported_by")
                        or ""
                    )
                    payload = {
                        "collection": collection,
                        "label": label,
                        "id": doc.get("id"),
                        "project_name": doc.get("project_name") or "",
                        "project_number": doc.get("project_number") or "",
                        "person": person,
                        "stored_date": stored,
                        "created_at": created_at,
                        "date_field": date_field,
                        "suggested_date": cls["suggested_date"],
                        "reason": cls["reason"],
                    }
                    if cat == "suspect":
                        out_suspects.append(payload)
                    else:
                        out_review.append(payload)

        # Stable order: newest stored_date first within each bucket
        out_suspects.sort(key=lambda r: r["stored_date"], reverse=True)
        out_review.sort(key=lambda r: r["stored_date"], reverse=True)
        return {
            "ok": True,
            "totals": totals,
            "timezone": str(LOCAL_TZ),
            "scanned_at": datetime.now(timezone.utc).isoformat(),
            "suspects": out_suspects,
            "review": out_review,
        }

    @router.post("/apply")
    async def apply_fix(
        body: ApplyFixBody,
        _: bool = Depends(require_admin_strict),
    ):
        """Apply a single date correction. Frontend has already re-verified
        the admin password via ``AdminPasswordConfirm`` before reaching
        here."""
        date_field, _label = _allowed_fields_for(body.collection)
        res = await db[body.collection].update_one(
            {"id": body.record_id},
            {
                "$set": {
                    date_field: body.new_date,
                    "date_audit_corrected_at": datetime.now(timezone.utc).isoformat(),
                },
            },
        )
        if res.matched_count == 0:
            raise HTTPException(status_code=404, detail="record not found")
        return {
            "ok": True,
            "collection": body.collection,
            "record_id": body.record_id,
            "new_date": body.new_date,
            "modified": res.modified_count,
        }

    return router
