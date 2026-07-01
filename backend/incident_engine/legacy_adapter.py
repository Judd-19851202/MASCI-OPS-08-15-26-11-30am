"""Track 19.16 · Phase A · LEGACY INCIDENT ADAPTER.

Historical fidelity is mandatory (Zero-Drift Doctrine).

Legacy ``db.incidents`` documents surface as READ-ONLY
``LegacyIncidentCase`` view models. No writes ever touch the legacy
collection through this adapter.

The adapter maps legacy fields onto the new IncidentCase shape best-
effort. Missing fields simply return as empty strings — the adapter
never invents data. Every returned document carries the flag
``__legacy__ = True`` and the raw legacy doc under ``__raw_legacy__``
so downstream consumers can inspect the original without a second
round trip.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .constants import COLLECTION_LEGACY_INCIDENTS


def _guess_incident_type(legacy: Dict[str, Any]) -> str:
    """Best-effort mapping from legacy text fields onto the 9 new codes."""
    blob = " ".join(str(legacy.get(k, "")) for k in (
        "incident_type", "type", "category", "kind", "description", "summary"
    )).lower()

    checks = (
        ("utility_strike",     ("utility", "strike", "locate", "damage to line")),
        ("vehicle_accident",   ("vehicle", "auto", "collision", "mvr", "truck accident")),
        ("equipment_accident", ("equipment", "excavator", "loader", "backhoe", "grader")),
        ("employee_injury",    ("injury", "injured", "medical", "hurt")),
        ("near_miss",          ("near miss", "close call", "near-miss")),
        ("property_damage",    ("property", "damage",)),
        ("environmental",      ("spill", "environmental", "fuel", "hazmat", "leak")),
        ("workplace_violence", ("violence", "threat", "assault", "harassment")),
        ("public_complaint",   ("complaint", "public",)),
    )
    for code, needles in checks:
        for needle in needles:
            if needle in blob:
                return code
    # Fallback — Public Complaint is the safest neutral bucket for
    # unknown legacy content.
    return "public_complaint"


def project_legacy(legacy: Dict[str, Any]) -> Dict[str, Any]:
    """Map a raw legacy incident doc → LegacyIncidentCase view model."""
    if not legacy:
        return {}

    inc_type = _guess_incident_type(legacy)
    state = str(legacy.get("lifecycle_state") or "").strip().upper() or "CLOSED"

    return {
        "id":            legacy.get("id") or legacy.get("doc_id") or "",
        "case_number":   str(legacy.get("doc_id") or legacy.get("case_number") or ""),
        "tenant_id":     str(legacy.get("tenant_id") or ""),
        "state":         state,
        "created_at":    str(legacy.get("created_at") or ""),
        "created_by":    str(legacy.get("reporter_name") or ""),
        "updated_at":    str(legacy.get("lifecycle_updated_at") or legacy.get("updated_at") or ""),
        "submitted_at":  str(legacy.get("created_at") or ""),
        "closed_at":     str(legacy.get("lifecycle_closed_at") or ""),
        "reopened_at":   "",
        "field_block_locked": True,   # legacy is always locked
        "field_block": {
            "incident_type":   inc_type,
            "occurred_at":     str(legacy.get("incident_date") or legacy.get("occurred_at") or ""),
            "reported_at":     str(legacy.get("created_at") or ""),
            "location_label":  str(legacy.get("location") or legacy.get("project_name") or ""),
            "job_number":      str(legacy.get("project_number") or legacy.get("job_number") or ""),
            "reporter_name":   str(legacy.get("reporter_name") or ""),
            "reporter_role":   str(legacy.get("reporter_role") or ""),
            "observed_conditions": str(legacy.get("description") or legacy.get("summary") or ""),
            "immediate_actions":   str(legacy.get("immediate_actions") or ""),
            "personnel_present":   [],
            "immediate_notifications": [],
            "weather": str(legacy.get("weather") or ""),
        },
        "safety_block": {
            "osha_recordable": (
                True if str(legacy.get("osha_recordable") or "").strip().lower() == "yes"
                else False if str(legacy.get("osha_recordable") or "").strip().lower() == "no"
                else None
            ),
            "root_cause_summary":     str(legacy.get("root_cause") or ""),
            "root_cause_categories":  list(legacy.get("root_cause_categories") or []),
        },
        "cross_links": [],
        "evidence_count": 0,
        "corrective_action_count": 0,
        "corrective_action_open": 0,
        "__legacy__": True,
        "__raw_legacy__": legacy,
    }


async def find_legacy(db, incident_id: str) -> Optional[Dict[str, Any]]:
    """Locate a single legacy incident by UUID or doc_id."""
    doc = await db[COLLECTION_LEGACY_INCIDENTS].find_one(
        {"id": incident_id}, {"_id": 0}
    )
    if not doc:
        doc = await db[COLLECTION_LEGACY_INCIDENTS].find_one(
            {"doc_id": incident_id}, {"_id": 0}
        )
    return doc


async def list_legacy(db, *, limit: int = 100) -> List[Dict[str, Any]]:
    """List legacy incidents projected onto the new shape."""
    cur = (
        db[COLLECTION_LEGACY_INCIDENTS]
        .find({}, {"_id": 0})
        .sort("created_at", -1)
        .limit(max(1, min(int(limit), 500)))
    )
    return [project_legacy(d) async for d in cur]


__all__ = ["project_legacy", "find_legacy", "list_legacy"]
