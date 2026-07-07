"""TRACK 23.10-C · Trench Safety Project Linker.

The single, authoritative resolver that maps any trench-safety record
(hold · inspection · repair · deployment · excavation · photo) to a
project. Implements the 6-rung ladder locked in
`/app/memory/TRACK_23_10_TRENCH_PROJECT_JOIN_AUDIT.md` §5.

Rules
-----
* Never fabricates a project.
* Never promotes medium/low confidence to LIVE at the source-classification
  layer (that is the aggregator's job downstream).
* Never writes the resolved project back into the source document —
  linkage is derived at read time (or emitted into ODS facts).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, Optional


LINK_STATUSES = (
    "explicit",                        # rung 1
    "inherited_from_daily_report",     # rung 2
    "inherited_from_parent_record",    # rung 3
    "inferred_from_assignment",        # rung 4
    "inferred_from_current_asset",     # rung 5
    "ambiguous",                       # rung 6 (multiple candidates)
    "missing",                         # rung 7 (no deployment ever)
)

LINK_CONFIDENCE = ("high", "medium", "low", "none")


@dataclass(frozen=True)
class ProjectLinkage:
    project_number: Optional[str]
    project_name_snapshot: Optional[str]
    project_id_snapshot: Optional[str]
    project_link_status: str
    confidence: str
    linker_notes: str
    matched_deployment_id: Optional[str] = None
    matched_source: Optional[str] = None            # daily-report id, parent id, ...

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ─── Helpers ──────────────────────────────────────────────────────────
def _iso(v: Any) -> str:
    if not v:
        return ""
    return str(v)


def _coerce_dt(v: Any) -> Optional[datetime]:
    if not v:
        return None
    s = str(v)
    try:
        # `fromisoformat` handles YYYY-MM-DD and full ISO with timezone.
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        # Some legacy rows carry YYYY-MM-DD only.
        try:
            return datetime.fromisoformat(s[:10]).replace(tzinfo=timezone.utc)
        except Exception:
            return None


def _record_datetime(record: Mapping[str, Any]) -> Optional[datetime]:
    """The moment against which we test the deployment window."""
    for k in ("opened_at", "created_at", "inspection_datetime", "assigned_at",
              "returned_at", "date_of_work", "date"):
        v = record.get(k)
        dt = _coerce_dt(v)
        if dt is not None:
            return dt
    return None


def _norm_project_number(v: Any) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip()
    return s or None


# ─── Individual rungs ─────────────────────────────────────────────────
def _rung_explicit(record: Mapping[str, Any]) -> Optional[ProjectLinkage]:
    pn = _norm_project_number(
        record.get("project_number") or record.get("project_id"),
    )
    if not pn:
        return None
    return ProjectLinkage(
        project_number=pn,
        project_name_snapshot=_iso(record.get("project_name")) or None,
        project_id_snapshot=_iso(record.get("project_id")) or None,
        project_link_status="explicit",
        confidence="high",
        linker_notes="explicit project field on record",
    )


async def _rung_daily_report(db, record: Mapping[str, Any]) -> Optional[ProjectLinkage]:
    dr_ref = record.get("daily_report_doc_id") or record.get("report_id") \
        or record.get("daily_report_id")
    if not dr_ref:
        return None
    dr = await db.daily_reports.find_one(
        {"$or": [{"id": dr_ref}, {"doc_id": dr_ref}]},
        {"_id": 0, "id": 1, "doc_id": 1, "project_number": 1,
         "project_name": 1, "day_setup": 1},
    )
    if not dr:
        return None
    setup = dr.get("day_setup") or {}
    pn = _norm_project_number(
        dr.get("project_number") or setup.get("project_number"),
    )
    if not pn:
        return None
    return ProjectLinkage(
        project_number=pn,
        project_name_snapshot=(dr.get("project_name")
                               or setup.get("project_name") or None),
        project_id_snapshot=None,
        project_link_status="inherited_from_daily_report",
        confidence="high",
        linker_notes=f"inherited from daily_report {dr.get('id') or dr_ref}",
        matched_source=str(dr.get("id") or dr_ref),
    )


async def _rung_parent_record(
    db, record: Mapping[str, Any], _seen: Optional[set] = None,
) -> Optional[ProjectLinkage]:
    """Recurse ONCE — hold.source_ref → inspection; repair.parent_hold_id
    → hold; photo.hold_id → hold; etc."""
    _seen = _seen or set()
    parent_ref = None
    parent_coll = None
    if record.get("source_ref"):
        parent_ref = record["source_ref"]
        parent_coll = record.get("source_ref_kind") or "trench_safety_inspections"
    elif record.get("parent_hold_id"):
        parent_ref = record["parent_hold_id"]
        parent_coll = "trench_safety_holds"
    elif record.get("hold_id"):
        parent_ref = record["hold_id"]
        parent_coll = "trench_safety_holds"
    elif record.get("inspection_id"):
        parent_ref = record["inspection_id"]
        parent_coll = "trench_safety_inspections"
    if not parent_ref or (parent_coll, parent_ref) in _seen:
        return None
    _seen.add((parent_coll, parent_ref))
    parent = await db[parent_coll].find_one({"id": parent_ref}, {"_id": 0})
    if not parent:
        return None
    linkage = await resolve_project(db, parent, _seen=_seen, _depth=1)
    if linkage.project_number and linkage.project_link_status not in {"missing", "ambiguous"}:
        return ProjectLinkage(
            project_number=linkage.project_number,
            project_name_snapshot=linkage.project_name_snapshot,
            project_id_snapshot=linkage.project_id_snapshot,
            project_link_status="inherited_from_parent_record",
            confidence="high",
            linker_notes=f"parent {parent_coll}:{parent_ref} → {linkage.project_link_status}",
            matched_source=str(parent_ref),
        )
    return None


async def _rung_deployment_assignment(
    db, record: Mapping[str, Any],
) -> Optional[ProjectLinkage]:
    """Rung 4 — asset active deployment at record's date. If exactly ONE
    match → medium confidence. If multiple → ambiguous."""
    asset_id = record.get("asset_id") or record.get("asset_uuid")
    if not asset_id:
        return None
    rec_dt = _record_datetime(record)
    if rec_dt is None:
        return None
    rec_iso = rec_dt.isoformat()

    # Find deployments whose window contains rec_dt.
    q = {
        "$and": [
            {"$or": [{"asset_id": asset_id}, {"asset_uuid": asset_id}]},
            {"assigned_at": {"$lte": rec_iso}},
            {"$or": [
                {"returned_at": None},
                {"returned_at": {"$exists": False}},
                {"returned_at": {"$gte": rec_iso}},
            ]},
        ],
    }
    depls = await db.trench_safety_deployments.find(q, {"_id": 0}).to_list(20)
    depls = [d for d in depls if _norm_project_number(
        d.get("project_number") or d.get("project_id")
    )]
    if not depls:
        return None
    if len(depls) > 1:
        return ProjectLinkage(
            project_number=None, project_name_snapshot=None,
            project_id_snapshot=None,
            project_link_status="ambiguous",
            confidence="low",
            linker_notes=f"{len(depls)} overlapping deployments for asset {asset_id}",
        )
    d = depls[0]
    pn = _norm_project_number(d.get("project_number") or d.get("project_id"))
    return ProjectLinkage(
        project_number=pn,
        project_name_snapshot=d.get("project_name") or None,
        project_id_snapshot=d.get("project_id") or None,
        project_link_status="inferred_from_assignment",
        confidence="medium",
        linker_notes=f"deployment {d.get('id')} · assigned {d.get('assigned_at')} · returned {d.get('returned_at') or 'NULL'}",
        matched_deployment_id=d.get("id"),
    )


async def _rung_current_asset(
    db, record: Mapping[str, Any],
) -> Optional[ProjectLinkage]:
    """Rung 5 — fallback to asset.current_project when the record has no
    reliable date. Only used when record.opened_at (if any) is within
    24h of asset.updated_at — else skipped."""
    asset_id = record.get("asset_id") or record.get("asset_uuid")
    if not asset_id:
        return None
    asset = await db.trench_safety_assets.find_one(
        {"$or": [{"asset_id": asset_id}, {"id": asset_id}]}, {"_id": 0},
    )
    if not asset:
        return None
    pn = _norm_project_number(
        asset.get("current_project_number") or asset.get("current_project_id"),
    )
    if not pn:
        return None
    rec_dt = _record_datetime(record)
    asset_upd = _coerce_dt(asset.get("updated_at"))
    if rec_dt and asset_upd:
        delta = abs((rec_dt - asset_upd).total_seconds())
        if delta > 86400:
            return None                      # too stale — skip
    return ProjectLinkage(
        project_number=pn,
        project_name_snapshot=asset.get("current_project_name"),
        project_id_snapshot=asset.get("current_project_id"),
        project_link_status="inferred_from_current_asset",
        confidence="low",
        linker_notes=f"asset current_project (asset {asset.get('id')})",
    )


# ─── Public API ───────────────────────────────────────────────────────
async def resolve_project(
    db, record: Mapping[str, Any],
    *, _seen: Optional[set] = None, _depth: int = 0,
) -> ProjectLinkage:
    """Run the 6-rung ladder against a single trench record.

    Stops at the first successful rung; records which one matched via
    `project_link_status`. Never fabricates. Never mutates the record.
    """
    if record is None:
        return ProjectLinkage(
            project_number=None, project_name_snapshot=None,
            project_id_snapshot=None,
            project_link_status="missing",
            confidence="none",
            linker_notes="empty record",
        )

    # Rung 1 · explicit
    hit = _rung_explicit(record)
    if hit:
        return hit

    # Rung 2 · daily report
    hit = await _rung_daily_report(db, record)
    if hit:
        return hit

    # Rung 3 · parent record (recurse ONCE)
    if _depth < 1:
        hit = await _rung_parent_record(db, record, _seen=_seen)
        if hit:
            return hit

    # Rung 4 · deployment assignment window
    hit = await _rung_deployment_assignment(db, record)
    if hit:
        return hit

    # Rung 5 · asset current project (24h window)
    hit = await _rung_current_asset(db, record)
    if hit:
        return hit

    # Rung 6/7 — missing
    return ProjectLinkage(
        project_number=None, project_name_snapshot=None,
        project_id_snapshot=None,
        project_link_status="missing",
        confidence="none",
        linker_notes="no deployment / no explicit link / no parent",
    )


async def resolve_project_batch(
    db, records: Iterable[Mapping[str, Any]],
) -> List[ProjectLinkage]:
    """Convenience — resolve N records serially. Callers can parallelise
    across worker pools if throughput matters (backfill script does)."""
    out: List[ProjectLinkage] = []
    for r in records:
        out.append(await resolve_project(db, r))
    return out
