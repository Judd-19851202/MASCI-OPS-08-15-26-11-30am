"""Track 19.38 · Cross-portal read fanout + Portfolio Attention Feed.

Read-only aggregator that surfaces incident intelligence to the right
portals in the right shape. Never mutates. Never invents. Reuses
Track 19.37 ``compute_presence_score`` — no duplicate scoring logic.

Endpoints registered here
-------------------------
- GET /api/incident-intelligence/portfolio-attention
    Safety + Admin. Full portfolio rollup sorted by attention score.
- GET /api/incident-intelligence/safety-priority
    Safety only. Adds Safety preview fields (root_cause presence,
    executive reviewer presence).
- GET /api/incident-intelligence/pm-project-cases?project_id=…
    Safety + Admin + PM. Strict allow-list projection — no safety_block,
    no regulatory_review, no signal rationales, no OSHA / liability /
    root-cause / discipline / insurance vocabulary.

Every response goes through ``_view_*`` projection helpers that produce
role-scoped dictionaries from a common ``_row_for_case`` builder. The
Safety view is the widest; the PM view is the strictest. A single
lock test greps the PM payload for forbidden keys.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from . import workspace as ws
from .evidence import list_evidence
from .corrective_actions import list_actions, summary_for_case
from .presence_score import compute_presence_score
from .constants import COLLECTION_CASES


PORTFOLIO_MODEL_VERSION = "1.0.0"

# PM projection allow-list. If a caller adds a new field to
# ``_row_for_case`` it MUST also be added here to be visible to PMs.
# Anything not on this list is stripped by ``_view_pm``.
_PM_ALLOWED_KEYS = {
    "case_id",
    "case_number",
    "state",
    "incident_type",
    "job_number",
    "location_label",
    "occurred_at",
    "submitted_at",
    "days_open",
    "capa_open",
    "capa_total",
    "tasks_open",
    "readiness_band",
    "attention_level",
}

# Vocabulary that must never appear in a PM-facing response (nested
# under any key). Enforced by lock test grep + assertion in the runtime
# projection helper.
_PM_FORBIDDEN_TOKENS = (
    "safety_block",
    "regulatory_review",
    "osha_recordable",
    "root_cause",
    "liability",
    "discipline",
    "preventability",
    "insurance",
    "signal_rationale",
    "rationale",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _days_between_iso(a_iso: str, b_iso: str) -> Optional[int]:
    try:
        a = datetime.fromisoformat(a_iso.replace("Z", "+00:00"))
        b = datetime.fromisoformat(b_iso.replace("Z", "+00:00"))
    except Exception:
        return None
    return max(0, int((b - a).total_seconds() // 86400))


async def _list_cases_readonly(
    db, *, limit: int, job_number: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Direct read-only Mongo query. Bypasses ``case_service.list_cases``
    (which requires a write-side actor permission) so the portfolio
    aggregator can serve read-only endpoints. Zero mutation."""
    q: Dict[str, Any] = {}
    if job_number:
        q["field_block.job_number"] = job_number
    cur = (
        db[COLLECTION_CASES]
        .find(q, {"_id": 0})
        .sort("created_at", -1)
        .limit(max(1, min(int(limit), 500)))
    )
    return [d async for d in cur]


async def _rows_for_cases(
    db, cases: List[Dict[str, Any]], *, want_attention: bool = True,
) -> List[Dict[str, Any]]:
    """Build one uniform row per case. Callers project via ``_view_*``."""
    now = _now_iso()

    async def _build_row(case: Dict[str, Any], sem: asyncio.Semaphore) -> Dict[str, Any]:
        cid = case.get("id") or ""
        fb = case.get("field_block") or {}
        sb = case.get("safety_block") or {}
        submitted = case.get("submitted_at") or case.get("created_at") or ""
        closed = case.get("closed_at") or ""
        days_open = _days_between_iso(submitted, closed or now) if submitted else None

        async with sem:
            if want_attention:
                capa_summary, tasks, capa_list, evidence, medical, agency = await asyncio.gather(
                    summary_for_case(db, case_id=cid),
                    ws.list_tasks(db, case_id=cid),
                    list_actions(db, consumer_kind="incident_case", consumer_id=cid),
                    list_evidence(db, case_id=cid, include_withdrawn=False),
                    ws.list_medical(db, case_id=cid),
                    ws.list_agency(db, case_id=cid),
                )
            else:
                capa_summary, tasks = await asyncio.gather(
                    summary_for_case(db, case_id=cid),
                    ws.list_tasks(db, case_id=cid),
                )
                capa_list, evidence, medical, agency = [], [], [], []

        capa_open = int((capa_summary or {}).get("open") or 0)
        capa_total = int((capa_summary or {}).get("total") or 0)
        tasks = tasks or []
        tasks_open = sum(1 for t in tasks
                         if (t.get("status") or "").lower()
                         in ("open", "in_progress", "blocked"))

        attention = None
        if want_attention:
            attention = compute_presence_score(
                case, evidence=evidence, capa=capa_list,
                medical=medical, agency=agency, tasks=tasks,
            )

        readiness_band = _readiness_band_from_case(case, capa_open,
                                                   len(tasks or []) > 0,
                                                   tasks_open)

        row = {
            "case_id":        cid,
            "case_number":    case.get("case_number") or "",
            "state":          case.get("state") or "",
            "incident_type":  fb.get("incident_type") or "",
            "job_number":     fb.get("job_number") or "",
            "location_label": fb.get("location_label") or "",
            "occurred_at":    fb.get("occurred_at") or "",
            "submitted_at":   submitted,
            "days_open":      days_open,
            "capa_open":      capa_open,
            "capa_total":     capa_total,
            "tasks_open":     tasks_open,
            "readiness_band": readiness_band,
            # Attention fields (safe-shape: level + overall only; the
            # full signal payload with rationales is added by
            # ``_view_portfolio``/``_view_safety`` explicitly).
            "attention_level": (attention or {}).get("attention_level", "low"),
            "attention_score": (attention or {}).get("overall_attention_score", 0),
            # Not projected by PM view — kept in the row for Safety+Admin only.
            "_attention_full":  attention,
            "_safety_block":    sb,
        }
        return row

    sem = asyncio.Semaphore(12)
    return await asyncio.gather(*[_build_row(case, sem) for case in cases])


def _readiness_band_from_case(case: Dict[str, Any], capa_open: int,
                              has_any_tasks: bool, tasks_open: int) -> str:
    """Coarse readiness band derived from public fields only. No writes."""
    state = (case.get("state") or "").upper()
    if state == "CLOSED":
        return "high"
    if capa_open == 0 and tasks_open == 0:
        return "medium"
    return "low"


# ---------------------------------------------------------------------------
# Role-scoped projections
# ---------------------------------------------------------------------------
def _view_portfolio(row: Dict[str, Any]) -> Dict[str, Any]:
    """Executive/Admin/Safety portfolio view — attention full."""
    attention = row.get("_attention_full") or {}
    signals = attention.get("signals") or []
    top = sorted(signals, key=lambda s: -(s.get("score") or 0.0))[:3]
    return {
        "case_id":         row["case_id"],
        "case_number":     row["case_number"],
        "state":           row["state"],
        "incident_type":   row["incident_type"],
        "job_number":      row["job_number"],
        "location_label":  row["location_label"],
        "occurred_at":     row["occurred_at"],
        "submitted_at":    row["submitted_at"],
        "days_open":       row["days_open"],
        "capa_open":       row["capa_open"],
        "capa_total":      row["capa_total"],
        "tasks_open":      row["tasks_open"],
        "readiness_band":  row["readiness_band"],
        "attention_level": row["attention_level"],
        "attention_score": row["attention_score"],
        "top_signals":     top,
    }


def _view_safety(row: Dict[str, Any]) -> Dict[str, Any]:
    """Safety-only view — adds Safety preview fields."""
    base = _view_portfolio(row)
    sb = row.get("_safety_block") or {}
    base["safety_preview"] = {
        "root_cause_documented": bool((sb.get("root_cause_summary") or "").strip()),
        "executive_reviewer_present": bool((sb.get("executive_reviewer") or "").strip()),
        "investigator_name": sb.get("investigator_name") or "",
    }
    return base


def _view_pm(row: Dict[str, Any]) -> Dict[str, Any]:
    """Strict allow-list projection. Discards every field not in
    ``_PM_ALLOWED_KEYS``. Additionally scans the resulting dict for
    forbidden vocabulary and raises if any leak is detected — this is
    a runtime safety net in addition to the compile-time allow-list."""
    projected = {k: row.get(k) for k in _PM_ALLOWED_KEYS if k in row}
    _assert_pm_safe(projected)
    return projected


def _assert_pm_safe(payload: Dict[str, Any]) -> None:
    dump = repr(payload).lower()
    for tok in _PM_FORBIDDEN_TOKENS:
        if tok in dump:
            raise HTTPException(
                status_code=500,
                detail={
                    "code": "pm_projection_leak",
                    "detail": (
                        f"PM projection would leak forbidden token {tok!r}; "
                        "aborting to preserve Track 19.34 doctrine."
                    ),
                },
            )


# ---------------------------------------------------------------------------
# Actor helper — the mixed require_safety_admin_or_pm dep returns:
#   True                                             (admin bypass)
#   {..., "_actor": "safety" | "pm", "_actor_kind": ...}
# ---------------------------------------------------------------------------
def _actor_kind(actor: Any) -> str:
    if actor is True:
        return "admin"
    if isinstance(actor, dict):
        return (actor.get("_actor") or "").lower() or "unknown"
    return "unknown"


# ---------------------------------------------------------------------------
# Route registration
# ---------------------------------------------------------------------------
def register_portfolio_intelligence_routes(
    api_router: APIRouter, db, *,
    require_safety_or_admin,
    require_safety_token,
    require_safety_admin_or_pm,
) -> None:
    """Register three additive read-only routes.

    Each route gets a different auth gate. Passed in as callables so
    ``server.py`` can wire the correct deps at boot without introducing
    circular imports.
    """

    @api_router.get("/incident-intelligence/portfolio-attention")
    async def portfolio_attention(
        limit: int = Query(50, ge=1, le=200),
        actor=Depends(require_safety_or_admin),
    ):
        cases = await _list_cases_readonly(db, limit=limit)
        rows = await _rows_for_cases(db, cases, want_attention=True)
        # Sort by attention_score DESC, then days_open DESC as tiebreak.
        rows.sort(key=lambda r: (
            -(r.get("attention_score") or 0),
            -(r.get("days_open") or 0),
        ))
        return {
            "model_version": PORTFOLIO_MODEL_VERSION,
            "generated_at": _now_iso(),
            "actor_role": _actor_kind(actor),
            "view": "portfolio",
            "cases": [_view_portfolio(r) for r in rows],
            "count": len(rows),
            "sorted_by": "attention_score_desc",
        }

    @api_router.get("/incident-intelligence/safety-priority")
    async def safety_priority(
        limit: int = Query(100, ge=1, le=500),
        actor=Depends(require_safety_token),
    ):
        cases = await _list_cases_readonly(db, limit=limit)
        rows = await _rows_for_cases(db, cases, want_attention=True)
        rows.sort(key=lambda r: (
            -(r.get("attention_score") or 0),
            -(r.get("days_open") or 0),
        ))
        return {
            "model_version": PORTFOLIO_MODEL_VERSION,
            "generated_at": _now_iso(),
            "actor_role": "safety",
            "view": "safety_priority",
            "cases": [_view_safety(r) for r in rows],
            "count": len(rows),
            "sorted_by": "attention_score_desc",
        }

    @api_router.get("/incident-intelligence/pm-project-cases")
    async def pm_project_cases(
        project_id: str = Query(..., min_length=1),
        limit: int = Query(100, ge=1, le=500),
        actor=Depends(require_safety_admin_or_pm),
    ):
        cases = await _list_cases_readonly(db, limit=limit,
                                            job_number=project_id)
        # PM view does not need attention SIGNALS — only the level.
        # We still call the scorer so the "level" is deterministic and
        # unified, but the full signal payload is stripped by _view_pm.
        rows = await _rows_for_cases(db, cases, want_attention=True)
        rows.sort(key=lambda r: (
            -(r.get("attention_score") or 0),
            -(r.get("days_open") or 0),
        ))
        role = _actor_kind(actor)
        projected = [_view_pm(r) for r in rows]
        return {
            "model_version": PORTFOLIO_MODEL_VERSION,
            "generated_at": _now_iso(),
            "actor_role": role,
            "view": "pm_project_cases",
            "project_id": project_id,
            "cases": projected,
            "count": len(projected),
            "sorted_by": "attention_score_desc",
        }


__all__ = [
    "PORTFOLIO_MODEL_VERSION",
    "register_portfolio_intelligence_routes",
    "_PM_ALLOWED_KEYS",
    "_PM_FORBIDDEN_TOKENS",
]
