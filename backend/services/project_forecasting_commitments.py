from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from services.cost_codes.foundation import (
    build_forecast_governance_summary,
    build_progress_snapshot,
    load_project_assignments,
    load_project_cost_code_actuals,
    load_project_forecast_history,
)
from services.cost_codes.schedule_engine import (
    SCENARIO_PROFILES,
    build_schedule_scenario_comparison,
    build_schedule_snapshot,
)
from services.project_budget_authority import (
    get_project_budget_overview,
    ensure_project_budget_foundation,
)
from services.project_controls_authority import ensure_project_controls_foundation
from services.project_operational_intelligence import get_project_operational_intelligence_snapshot
from services.project_schedule_actuals_spine import (
    ensure_schedule_actuals_foundation,
    get_schedule_actuals_overview,
)
from services.project_schedule_authority import ensure_project_schedule_foundation


COLL_FORECAST_COMMITMENTS = "project_forecast_commitments"
COLL_FORECAST_SNAPSHOTS = "project_forecasting_snapshots"
ALLOWED_COMMITMENT_STATUSES = {
    "proposed",
    "committed",
    "at_risk",
    "missed",
    "met",
    "revised",
    "cancelled",
}
ALLOWED_COMMITMENT_FAMILIES = {
    "labor_crew",
    "equipment",
    "materials",
    "vendor_subcontractor",
    "milestone_quantity",
}
DEFAULT_FORECAST_WINDOW_DAYS = 7


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().isoformat()


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except Exception:
        return default


def _date_text(value: Any) -> str:
    text = _clean(value)
    if not text:
        return ""
    return text[:10]


def _dt(value: Any) -> Optional[datetime]:
    text = _clean(value)
    if not text:
        return None
    try:
        if len(text) == 10:
            return datetime.fromisoformat(text).replace(tzinfo=timezone.utc)
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except Exception:
        return None


def _sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _sanitize(v) for k, v in value.items() if k != "_id"}
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat()
    return value


def _slug(value: str) -> str:
    text = _clean(value).lower()
    out = []
    for ch in text:
        out.append(ch if ch.isalnum() else "-")
    slug = "".join(out)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-") or "item"


def _confidence_band(confidence: str, likely: Optional[float]) -> Dict[str, Optional[float]]:
    if likely is None:
        return {"low": None, "likely": None, "high": None}
    span = 0.1 if confidence == "high" else 0.25 if confidence == "medium" else 0.4
    return {
        "low": round(max(likely * (1 - span), 0.0), 4),
        "likely": round(max(likely, 0.0), 4),
        "high": round(max(likely * (1 + span), 0.0), 4),
    }


def _window_days(finish_date: str) -> int:
    finish_dt = _dt(finish_date)
    if not finish_dt:
        return DEFAULT_FORECAST_WINDOW_DAYS
    return max((finish_dt.date() - _now().date()).days + 1, 1)


def _actor_label(actor: Optional[Dict[str, Any]]) -> str:
    actor = actor or {}
    return _clean(actor.get("name") or actor.get("email") or actor.get("id") or actor.get("user_id") or "system")


def _actor_identity(actor: Optional[Dict[str, Any]]) -> Dict[str, str]:
    actor = actor or {}
    return {
        "id": _clean(actor.get("id") or actor.get("user_id")),
        "email": _clean(actor.get("email")).lower(),
        "name": _clean(actor.get("name") or actor.get("display_name") or actor.get("email") or "System"),
        "role": _clean(actor.get("role") or actor.get("_actor") or actor.get("_actor_kind") or "system"),
    }


def _hash_payload(payload: Dict[str, Any]) -> str:
    encoded = json.dumps(_sanitize(payload), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


async def _write_audit(
    db,
    *,
    action: str,
    actor: Optional[Dict[str, Any]],
    project_number: str,
    resource_type: str,
    resource_id: str,
    after: Dict[str, Any],
    before: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    event = {
        "event_id": f"forecast-audit:{uuid4().hex[:16]}",
        "created_at": _now_iso(),
        "action": action,
        "project_number": project_number,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "actor": _actor_identity(actor),
        "before": _sanitize(before or {}),
        "after": _sanitize(after or {}),
        "metadata": _sanitize(metadata or {}),
    }
    await db.audit_events.insert_one(event)


async def _ensure_indexes(db) -> None:
    await db[COLL_FORECAST_COMMITMENTS].create_index([("project_number", 1), ("commitment_id", 1)], unique=True)
    await db[COLL_FORECAST_COMMITMENTS].create_index([("project_number", 1), ("status", 1), ("due_date", 1)])
    await db[COLL_FORECAST_COMMITMENTS].create_index([("project_number", 1), ("family", 1), ("updated_at", -1)])
    await db[COLL_FORECAST_SNAPSHOTS].create_index([("project_number", 1), ("version_number", -1)], unique=True)
    await db[COLL_FORECAST_SNAPSHOTS].create_index([("project_number", 1), ("fingerprint", 1)])
    await db[COLL_FORECAST_SNAPSHOTS].create_index([("project_number", 1), ("generated_at", -1)])


async def ensure_project_forecasting_commitments_foundation(db) -> Dict[str, Any]:
    await ensure_project_controls_foundation(db)
    await ensure_project_budget_foundation(db)
    await ensure_project_schedule_foundation(db)
    await ensure_schedule_actuals_foundation(db)
    await _ensure_indexes(db)
    return {
        "ok": True,
        "commitment_collection": COLL_FORECAST_COMMITMENTS,
        "snapshot_collection": COLL_FORECAST_SNAPSHOTS,
        "mode": "additive_only",
    }


def _latest_value(values: List[str]) -> str:
    valid = [value for value in values if _dt(value)]
    if not valid:
        return ""
    return max(valid, key=lambda value: _dt(value) or datetime.min.replace(tzinfo=timezone.utc))


async def _resolve_schedule_forecast(db, project_number: str) -> Dict[str, Any]:
    assignments = await load_project_assignments(db, project_number)
    daily_rows = await load_project_cost_code_actuals(db, project_number)
    progress = build_progress_snapshot(assignments, daily_rows) if assignments else None
    forecast_history = await load_project_forecast_history(db, project_number)
    overrides = forecast_history.get("overrides") or []
    schedule = build_schedule_snapshot(assignments, progress, daily_rows=daily_rows, overrides=overrides)
    scenario_comparison = build_schedule_scenario_comparison(
        assignments,
        progress,
        daily_rows=daily_rows,
        anchor_date=(schedule.get("window") or {}).get("anchor_date"),
        scenario_keys=["additional_crew", "weekend_work", "additional_shift"],
        overrides=overrides,
    )
    governance = build_forecast_governance_summary(forecast_history)
    tasks = schedule.get("tasks") or []
    slipped = sorted([row for row in tasks if int(row.get("slip_days") or 0) > 0], key=lambda row: int(row.get("slip_days") or 0), reverse=True)
    finish_dates = [
        _date_text(schedule.get("projected_finish_date")),
        *[_date_text(row.get("forecast_finish_date")) for row in tasks],
    ]
    likely_finish = _latest_value(finish_dates)
    committed_finish = _date_text(schedule.get("committed_finish_date"))
    current_finish = _latest_value([_date_text(row.get("forecast_finish_date")) for row in tasks if _clean(row.get("forecast_status")) == "completed"])
    confidence = "high" if tasks and len(slipped) <= max(len(tasks) // 3, 1) else "medium" if tasks else "review_required"
    schedule_days = _window_days(likely_finish or committed_finish)
    confidence_window = {
        "earliest": (_dt(likely_finish) - timedelta(days=2)).date().isoformat() if likely_finish and confidence == "high" else (_dt(likely_finish) - timedelta(days=5)).date().isoformat() if likely_finish and confidence == "medium" else likely_finish,
        "likely": likely_finish,
        "latest": (_dt(likely_finish) + timedelta(days=3)).date().isoformat() if likely_finish and confidence == "high" else (_dt(likely_finish) + timedelta(days=8)).date().isoformat() if likely_finish and confidence == "medium" else (_dt(likely_finish) + timedelta(days=12)).date().isoformat() if likely_finish else "",
    }
    drivers = []
    if slipped:
        first = slipped[0]
        drivers.append({
            "driver_id": f"schedule-slip:{first.get('code') or first.get('task_id') or 'top'}",
            "family": "schedule",
            "label": _clean(first.get("name") or first.get("activity_name") or first.get("code") or "Schedule slip"),
            "reason": f"Top slipped activity is carrying {int(first.get('slip_days') or 0)} day(s) of forecast variance.",
            "evidence": {
                "slip_days": int(first.get("slip_days") or 0),
                "forecast_finish_date": _date_text(first.get("forecast_finish_date")),
                "committed_finish_date": _date_text(first.get("committed_finish_date") or first.get("current_finish_date")),
            },
        })
    if not assignments:
        drivers.append({
            "driver_id": "schedule-insufficient-inputs",
            "family": "governance",
            "label": "Insufficient scheduling inputs",
            "reason": "No governed assignment rows were available for the legacy schedule engine.",
            "evidence": {"assignment_count": 0},
        })
    return {
        "status": "ready" if assignments else "insufficient_evidence",
        "truth_basis": "cost_codes.schedule_engine",
        "constitutional_rule": "Forecasts derive only from canonical operational data and audited overrides.",
        "scenario_library": [
            {
                "key": row.get("key"),
                "label": row.get("label"),
                "notes": row.get("notes"),
                "rate_multiplier": row.get("rate_multiplier"),
            }
            for row in SCENARIO_PROFILES.values()
        ],
        "governance": governance,
        "scenario_comparison": scenario_comparison,
        "schedule": schedule,
        "summary": {
            "activity_count": len(tasks),
            "slipped_activity_count": len(slipped),
            "likely_finish_date": likely_finish,
            "committed_finish_date": committed_finish,
            "days_to_likely_finish": schedule_days,
        },
        "confidence": confidence,
        "confidence_window": confidence_window,
        "drivers": drivers,
        "top_slipped_tasks": slipped[:8],
    }


def _build_unit_forecasts(quantity_rows: List[Dict[str, Any]], timeline_rows: List[Dict[str, Any]], schedule_finish_date: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    total_remaining = 0.0
    total_next_week = 0.0
    total_required_weekly = 0.0
    for quantity_row in quantity_rows:
        unit = _clean(quantity_row.get("unit") or "UNSPECIFIED") or "UNSPECIFIED"
        timeline = next((item for item in timeline_rows if _clean(item.get("unit")) == unit), {})
        remaining = round(_to_float(quantity_row.get("remaining_quantity"), 0.0), 4)
        total_remaining += remaining
        velocity = _to_float(timeline.get("production_velocity"), 0.0)
        average_daily = _to_float(timeline.get("average_daily_production"), 0.0)
        next_day = round(velocity or average_daily, 4) if (velocity or average_daily) > 0 else None
        next_week = round((velocity or average_daily) * 7.0, 4) if (velocity or average_daily) > 0 else None
        if next_week:
            total_next_week += next_week
        finish_window_days = _window_days(schedule_finish_date)
        required_daily = round(remaining / finish_window_days, 4) if remaining > 0 else 0.0
        required_weekly = round(required_daily * 7.0, 4)
        total_required_weekly += required_weekly
        confidence = _clean(timeline.get("confidence") or quantity_row.get("confidence") or "review_required") or "review_required"
        status = "ready" if next_day is not None and remaining > 0 else "insufficient_evidence" if remaining > 0 else "complete"
        drivers = []
        if status == "insufficient_evidence":
            drivers.append("No recent accepted production velocity is available for this unit.")
        if required_weekly and next_week is not None and next_week < required_weekly:
            drivers.append("Current weekly pace is below the required pace to hit the likely finish window.")
        if _to_float(quantity_row.get("rejected_quantity"), 0.0) > 0:
            drivers.append("Rejected quantity is preserved and limits decision confidence.")
        rows.append(
            {
                "unit": unit,
                "status": status,
                "remaining_quantity": remaining,
                "accepted_quantity": round(_to_float(quantity_row.get("accepted_quantity"), 0.0), 4),
                "next_day_quantity": next_day,
                "next_week_quantity": next_week,
                "confidence": confidence,
                "confidence_band": _confidence_band(confidence, next_week),
                "required_pace_per_day": required_daily,
                "required_pace_per_week": required_weekly,
                "recovery_pace_per_week": max(required_weekly, round((next_week or 0.0), 4)),
                "evidence": {
                    "daily_production": _to_float(timeline.get("daily_production"), 0.0),
                    "weekly_production": _to_float(timeline.get("weekly_production"), 0.0),
                    "rolling_14_day_production": _to_float(timeline.get("rolling_14_day_production"), 0.0),
                    "reporting_days": int(timeline.get("reporting_days") or 0),
                },
                "drivers": drivers,
                "formula": "next_week_quantity = production_velocity * 7; required pace = remaining_quantity / days_to_likely_finish",
            }
        )
    summary = {
        "remaining_quantity_total": round(total_remaining, 4),
        "forecast_next_week_total": round(total_next_week, 4),
        "required_weekly_total": round(total_required_weekly, 4),
        "unit_count": len(rows),
    }
    return rows, summary


def _build_resource_forecasts(snapshot: Dict[str, Any], production_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    required_weekly_total = sum(_to_float(row.get("required_pace_per_week"), 0.0) for row in production_rows)
    resources = snapshot.get("resource_productivity") or {}
    payload: Dict[str, Any] = {}
    for family_key in ["crews", "equipment", "materials", "vendors", "subcontractors"]:
        rows = resources.get(family_key) or []
        family_rows = []
        for row in rows[:12]:
            productivity = _to_float(row.get("productivity"), 0.0)
            likely_capacity = round(productivity * max(_to_float(row.get("hours"), 0.0), 1.0), 4) if productivity > 0 else None
            required_share = round(required_weekly_total * _to_float(row.get("utilization"), 0.0), 4) if required_weekly_total > 0 else 0.0
            confidence = _clean(row.get("confidence") or "review_required") or "review_required"
            family_rows.append(
                {
                    "id": row.get("id"),
                    "label": row.get("label"),
                    "unit": row.get("unit") or row.get("material_unit") or "",
                    "status": "ready" if productivity > 0 else "insufficient_evidence",
                    "productivity": productivity or None,
                    "hours_observed": round(_to_float(row.get("hours"), 0.0), 4),
                    "likely_next_week_capacity": likely_capacity,
                    "required_weekly_support": required_share,
                    "confidence": confidence,
                    "confidence_band": _confidence_band(confidence, likely_capacity),
                    "drivers": [
                        "Resource outlook reuses preserved work-block productivity; no duplicate staffing engine was introduced."
                    ],
                    "evidence": {
                        "accepted_quantity": round(_to_float(row.get("accepted_quantity"), 0.0), 4),
                        "source_report_ids": list(row.get("source_report_ids") or [])[:10],
                        "work_block_ids": list(row.get("work_block_ids") or [])[:10],
                    },
                }
            )
        payload[family_key] = family_rows
    return payload


def _build_cost_forecast(cost_rows: List[Dict[str, Any]], commitment_candidates: List[Dict[str, Any]], production_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    projected_remaining_cost = 0.0
    for cost_row in cost_rows:
        unit = _clean(cost_row.get("unit") or "UNSPECIFIED") or "UNSPECIFIED"
        production = next((row for row in production_rows if row.get("unit") == unit), {})
        remaining = _to_float(production.get("remaining_quantity"), 0.0)
        budget_cpu = _to_float(cost_row.get("budget_cost_per_unit"), 0.0)
        remaining_cost = round(remaining * budget_cpu, 2) if budget_cpu > 0 and remaining > 0 else None
        projected_remaining_cost += remaining_cost or 0.0
        rows.append(
            {
                "unit": unit,
                "status": "ready" if remaining_cost is not None else "insufficient_evidence",
                "remaining_quantity": remaining,
                "budget_cost_per_unit": budget_cpu or None,
                "projected_remaining_cost": remaining_cost,
                "labor_cost_per_unit": _to_float(cost_row.get("labor_cost_per_unit"), 0.0) or None,
                "equipment_cost_per_unit": _to_float(cost_row.get("equipment_cost_per_unit"), 0.0) or None,
                "material_cost_per_unit": _to_float(cost_row.get("material_cost_per_unit"), 0.0) or None,
                "vendor_cost_per_unit": _to_float(cost_row.get("vendor_cost_per_unit"), 0.0) or None,
                "subcontract_cost_per_unit": _to_float(cost_row.get("subcontract_cost_per_unit"), 0.0) or None,
                "actual_cost_confidence": cost_row.get("actual_cost_confidence") or "review_required",
                "limitations": [item for item in cost_row.get("limitations") or [] if item],
            }
        )
    commitment_exposure = round(sum(_to_float(row.get("commitment_amount"), 0.0) for row in commitment_candidates), 2)
    return {
        "status": "ready" if rows else "insufficient_evidence",
        "summary": {
            "projected_remaining_cost": round(projected_remaining_cost, 2),
            "commitment_exposure": commitment_exposure,
            "projected_final_cost_floor": round(projected_remaining_cost + commitment_exposure, 2),
        },
        "unit_rows": rows,
        "formula": "projected_remaining_cost = remaining_quantity * budget_cost_per_unit; commitment exposure is preserved from approved/closed PO requests.",
    }


def _classify_constraint_status(row: Dict[str, Any]) -> str:
    status = _clean(row.get("status") or row.get("state") or row.get("constraint_status") or "open").lower()
    if status in {"closed", "resolved", "complete", "completed", "cancelled", "canceled"}:
        return "closed"
    return "open"


async def _load_constraints(db, project_number: str) -> Dict[str, Any]:
    rows = [_sanitize(row) async for row in db.operational_constraints.find({"project_number": project_number}, {"_id": 0}).sort([("updated_at", -1), ("created_at", -1)]).limit(100)]
    open_rows = [row for row in rows if _classify_constraint_status(row) == "open"]
    if not open_rows:
        return {
            "status": "ready",
            "open_count": 0,
            "forecast_effects": [],
            "drivers": [],
            "weather_factor": {
                "status": "insufficient_evidence",
                "message": "No governed weather source is linked into the current constraint family.",
            },
        }
    effects = []
    for row in open_rows[:8]:
        effects.append(
            {
                "constraint_id": _clean(row.get("id") or row.get("constraint_id") or row.get("doc_id") or uuid4().hex[:8]),
                "title": _clean(row.get("title") or row.get("summary") or row.get("constraint_type") or "Open constraint"),
                "status": _clean(row.get("status") or row.get("state") or "open"),
                "impact": _clean(row.get("impact") or row.get("severity") or "needs review"),
                "reason": _clean(row.get("reason") or row.get("notes") or row.get("description") or "Constraint evidence preserved from operational constraints."),
            }
        )
    return {
        "status": "ready",
        "open_count": len(open_rows),
        "forecast_effects": effects,
        "drivers": [
            "Open constraints are preserved as forecast drivers and do not silently mutate the forecast result."
        ],
        "weather_factor": {
            "status": "insufficient_evidence",
            "message": "Weather is not being used as a forecast driver because no governed weather source is linked here yet.",
        },
    }


def _build_po_commitments(commitment_candidates: List[Dict[str, Any]], actual_cost_candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    actual_by_source = {str(row.get("source_record_id") or ""): row for row in actual_cost_candidates if _clean(row.get("source_record_id"))}
    items: List[Dict[str, Any]] = []
    for row in commitment_candidates:
        source_id = _clean(row.get("source_po_id"))
        actual = actual_by_source.get(source_id) or {}
        committed = _to_float(row.get("commitment_amount"), 0.0)
        actual_amount = _to_float(actual.get("candidate_amount"), 0.0)
        lifecycle = "met" if actual_amount and actual_amount >= committed else "committed" if committed > 0 else "proposed"
        if _clean(row.get("review_status")) == "review_required":
            lifecycle = "at_risk"
        items.append(
            {
                "commitment_id": f"po:{source_id}",
                "source": "po_candidate",
                "editable": False,
                "family": "vendor_subcontractor",
                "status": lifecycle,
                "title": _clean(row.get("po_number") or row.get("vendor") or source_id or "Vendor commitment"),
                "description": _clean(row.get("description")),
                "vendor": _clean(row.get("vendor")),
                "project_number": _clean(row.get("project_number")),
                "due_date": "",
                "target_amount": round(committed, 2),
                "actual_amount": round(actual_amount, 2),
                "confidence": "medium" if lifecycle == "at_risk" else "high",
                "drivers": [
                    "Commitment exposure is preserved from approved or closed PO requests.",
                    "Actual amount is read from reviewed vendor receipt candidates when available.",
                ],
                "evidence": {
                    "source_po_id": source_id,
                    "review_status": row.get("review_status"),
                    "trust_line": row.get("trust_line"),
                },
            }
        )
    return items


async def list_project_forecast_commitments(db, project_number: str) -> List[Dict[str, Any]]:
    rows = [
        _sanitize(row)
        async for row in db[COLL_FORECAST_COMMITMENTS].find({"project_number": project_number}, {"_id": 0}).sort([("updated_at", -1), ("created_at", -1)]).limit(200)
    ]
    return rows


def _normalize_status(status: str) -> str:
    value = _slug(status).replace("-", "_")
    return value if value in ALLOWED_COMMITMENT_STATUSES else "proposed"


def _normalize_family(family: str) -> str:
    value = _slug(family).replace("-", "_")
    return value if value in ALLOWED_COMMITMENT_FAMILIES else "milestone_quantity"


def _commitment_doc(project_number: str, payload: Dict[str, Any], *, actor: Dict[str, Any], existing: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    now = _now_iso()
    actor_row = _actor_identity(actor)
    current = deepcopy(existing or {})
    commitment_id = _clean(current.get("commitment_id")) or f"forecast-commitment:{project_number}:{uuid4().hex[:10]}"
    history = list(current.get("history") or [])
    status = _normalize_status(_clean(payload.get("status") or current.get("status") or "proposed"))
    note = _clean(payload.get("note") or "")
    if not existing or status != _clean(current.get("status")) or note:
        history.append(
            {
                "status": status,
                "note": note,
                "changed_at": now,
                "changed_by": actor_row,
            }
        )
    return {
        "commitment_id": commitment_id,
        "project_number": project_number,
        "family": _normalize_family(_clean(payload.get("family") or current.get("family") or "milestone_quantity")),
        "status": status,
        "title": _clean(payload.get("title") or current.get("title") or "Forecast commitment"),
        "description": _clean(payload.get("description") or current.get("description")),
        "due_date": _date_text(payload.get("due_date") or current.get("due_date")),
        "linked_unit": _clean(payload.get("linked_unit") or current.get("linked_unit")),
        "linked_activity_id": _clean(payload.get("linked_activity_id") or current.get("linked_activity_id")),
        "linked_work_package_id": _clean(payload.get("linked_work_package_id") or current.get("linked_work_package_id")),
        "target_quantity": round(_to_float(payload.get("target_quantity"), _to_float(current.get("target_quantity"), 0.0)), 4),
        "target_hours": round(_to_float(payload.get("target_hours"), _to_float(current.get("target_hours"), 0.0)), 4),
        "target_amount": round(_to_float(payload.get("target_amount"), _to_float(current.get("target_amount"), 0.0)), 2),
        "target_count": round(_to_float(payload.get("target_count"), _to_float(current.get("target_count"), 0.0)), 4),
        "confidence": _clean(payload.get("confidence") or current.get("confidence") or "medium"),
        "evidence_note": _clean(payload.get("evidence_note") or current.get("evidence_note")),
        "created_at": current.get("created_at") or now,
        "created_by": current.get("created_by") or actor_row,
        "updated_at": now,
        "updated_by": actor_row,
        "history": history[-25:],
        "source": "manual_commitment",
        "editable": True,
    }


def _actual_for_commitment(commitment: Dict[str, Any], production_rows: List[Dict[str, Any]], resource_forecasts: Dict[str, Any], po_commitments: List[Dict[str, Any]]) -> Dict[str, Any]:
    if commitment.get("source") == "po_candidate":
        return {
            "actual_amount": round(_to_float(commitment.get("actual_amount"), 0.0), 2),
            "evidence_label": "Vendor receipt candidate",
        }
    linked_unit = _clean(commitment.get("linked_unit"))
    production = next((row for row in production_rows if _clean(row.get("unit")) == linked_unit), {}) if linked_unit else {}
    actual_quantity = _to_float(production.get("accepted_quantity"), 0.0)
    actual_hours = None
    if commitment.get("family") in {"labor_crew", "equipment", "materials", "vendor_subcontractor"}:
        family_map = {
            "labor_crew": "crews",
            "equipment": "equipment",
            "materials": "materials",
            "vendor_subcontractor": "vendors",
        }
        family_rows = resource_forecasts.get(family_map.get(commitment.get("family"), "")) or []
        linked = next((row for row in family_rows if _clean(row.get("unit")) == linked_unit), {}) if linked_unit else {}
        actual_hours = _to_float(linked.get("hours_observed"), 0.0) or None
    return {
        "actual_quantity": round(actual_quantity, 4) if actual_quantity else 0.0,
        "actual_hours": round(actual_hours, 4) if actual_hours else None,
        "actual_amount": round(_to_float(commitment.get("actual_amount"), 0.0), 2) if commitment.get("actual_amount") is not None else None,
        "evidence_label": "Governed production / resource evidence",
    }


def _derive_commitment_status(commitment: Dict[str, Any], actual: Dict[str, Any]) -> Tuple[str, List[str]]:
    status = _normalize_status(_clean(commitment.get("status") or "proposed"))
    reasons: List[str] = []
    due_dt = _dt(commitment.get("due_date"))
    target_quantity = _to_float(commitment.get("target_quantity"), 0.0)
    target_hours = _to_float(commitment.get("target_hours"), 0.0)
    target_amount = _to_float(commitment.get("target_amount"), 0.0)
    actual_quantity = _to_float(actual.get("actual_quantity"), 0.0)
    actual_hours = _to_float(actual.get("actual_hours"), 0.0)
    actual_amount = _to_float(actual.get("actual_amount"), 0.0)
    if target_quantity > 0 and actual_quantity >= target_quantity:
        return "met", ["Accepted production met or exceeded the committed quantity."]
    if target_hours > 0 and actual_hours >= target_hours:
        return "met", ["Observed hours met or exceeded the committed support level."]
    if target_amount > 0 and actual_amount >= target_amount:
        return "met", ["Recorded amount met or exceeded the committed exposure."]
    if status == "cancelled":
        return status, ["Commitment was cancelled by an operator."]
    if due_dt and due_dt.date() < _now().date():
        return "missed", ["Commitment due date has passed without enough actual evidence."]
    if due_dt and due_dt.date() <= (_now().date() + timedelta(days=2)):
        reasons.append("Commitment due date is inside the next 48 hours.")
        if status in {"committed", "proposed", "revised"}:
            status = "at_risk"
    if status == "proposed" and (target_quantity or target_hours or target_amount):
        reasons.append("Commitment exists but has not yet been confirmed into the committed state.")
    return status, reasons


def _build_commitment_lane(
    manual_commitments: List[Dict[str, Any]],
    po_commitments: List[Dict[str, Any]],
    production_rows: List[Dict[str, Any]],
    resource_forecasts: Dict[str, Any],
) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for commitment in [*manual_commitments, *po_commitments]:
        actual = _actual_for_commitment(commitment, production_rows, resource_forecasts, po_commitments)
        derived_status, reasons = _derive_commitment_status(commitment, actual)
        row = {
            **commitment,
            **actual,
            "derived_status": derived_status,
            "drivers": [*list(commitment.get("drivers") or []), *reasons],
        }
        rows.append(row)
    rows.sort(key=lambda item: (_date_text(item.get("due_date")) or "9999-12-31", item.get("title") or ""))
    lifecycle_counts = {status: 0 for status in sorted(ALLOWED_COMMITMENT_STATUSES)}
    for row in rows:
        lifecycle_counts[row.get("derived_status") or "proposed"] = lifecycle_counts.get(row.get("derived_status") or "proposed", 0) + 1
    return {
        "status": "ready",
        "lifecycle_counts": lifecycle_counts,
        "items": rows,
        "at_risk_items": [row for row in rows if row.get("derived_status") in {"at_risk", "missed"}][:12],
    }


def _build_forecast_vs_actual(snapshot: Dict[str, Any], schedule_payload: Dict[str, Any], production_summary: Dict[str, Any]) -> Dict[str, Any]:
    quantity_rows = snapshot.get("quantity_by_unit") or []
    committed_finish = _date_text((schedule_payload.get("schedule") or {}).get("committed_finish_date"))
    likely_finish = _date_text((schedule_payload.get("summary") or {}).get("likely_finish_date"))
    return {
        "status": "ready",
        "summary": {
            "committed_finish_date": committed_finish,
            "likely_finish_date": likely_finish,
            "remaining_quantity_total": production_summary.get("remaining_quantity_total"),
            "forecast_next_week_total": production_summary.get("forecast_next_week_total"),
        },
        "unit_rows": [
            {
                "unit": row.get("unit"),
                "accepted_quantity": row.get("accepted_quantity"),
                "remaining_quantity": row.get("remaining_quantity"),
                "variance_reason": "Accepted quantity is behind the governed remaining scope." if _to_float(row.get("remaining_quantity"), 0.0) > 0 else "Scope appears complete for this unit.",
            }
            for row in quantity_rows[:20]
        ],
    }


def _build_confidence_report(schedule_payload: Dict[str, Any], production_rows: List[Dict[str, Any]], constraints_payload: Dict[str, Any], lineage: Dict[str, Any]) -> Dict[str, Any]:
    bands = {
        "high": sum(1 for row in production_rows if row.get("confidence") == "high"),
        "medium": sum(1 for row in production_rows if row.get("confidence") == "medium"),
        "review_required": sum(1 for row in production_rows if row.get("confidence") == "review_required"),
    }
    overall = "high" if schedule_payload.get("confidence") == "high" and not constraints_payload.get("open_count") and lineage.get("orphan_events", 0) == 0 else "medium" if bands["review_required"] < max(len(production_rows), 1) else "review_required"
    return {
        "overall": overall,
        "production_band_counts": bands,
        "lineage_confidence": lineage.get("traceability_confidence") or "review_required",
        "drivers": [
            "Confidence is reduced when lineage orphan events remain open.",
            "Confidence is reduced when open constraints are present or when production velocity is sparse.",
        ],
    }


def _diff_snapshots(previous: Optional[Dict[str, Any]], current: Dict[str, Any]) -> Dict[str, Any]:
    if not previous:
        return {
            "changed": True,
            "change_count": 1,
            "summary": ["Initial C7 workspace version captured."],
        }
    changes = []
    prev_schedule = ((previous.get("workspace") or {}).get("schedule") or {}).get("summary") or {}
    curr_schedule = (current.get("schedule") or {}).get("summary") or {}
    if _date_text(prev_schedule.get("likely_finish_date")) != _date_text(curr_schedule.get("likely_finish_date")):
        changes.append(f"Likely finish moved from {prev_schedule.get('likely_finish_date') or '—'} to {curr_schedule.get('likely_finish_date') or '—' }.")
    prev_remaining = (((previous.get("workspace") or {}).get("production") or {}).get("summary") or {}).get("remaining_quantity_total")
    curr_remaining = ((current.get("production") or {}).get("summary") or {}).get("remaining_quantity_total")
    if round(_to_float(prev_remaining, -1), 4) != round(_to_float(curr_remaining, -1), 4):
        changes.append(f"Remaining quantity changed from {_to_float(prev_remaining, 0.0):.4f} to {_to_float(curr_remaining, 0.0):.4f}.")
    prev_risk = (((previous.get("workspace") or {}).get("commitments") or {}).get("lifecycle_counts") or {}).get("at_risk", 0)
    curr_risk = ((current.get("commitments") or {}).get("lifecycle_counts") or {}).get("at_risk", 0)
    if int(prev_risk or 0) != int(curr_risk or 0):
        changes.append(f"At-risk commitments changed from {int(prev_risk or 0)} to {int(curr_risk or 0)}.")
    return {
        "changed": bool(changes),
        "change_count": len(changes),
        "summary": changes[:8] or ["No governed forecast change detected."],
    }


async def _persist_snapshot_version(db, project_number: str, workspace: Dict[str, Any], *, actor: Optional[Dict[str, Any]], note: str = "") -> Dict[str, Any]:
    base_payload = {
        "schedule": workspace.get("schedule"),
        "production": workspace.get("production"),
        "resources": workspace.get("resources"),
        "cost": workspace.get("cost"),
        "commitments": workspace.get("commitments"),
        "constraints": workspace.get("constraints"),
        "confidence": workspace.get("confidence"),
    }
    fingerprint = _hash_payload(base_payload)
    latest = await db[COLL_FORECAST_SNAPSHOTS].find_one({"project_number": project_number}, {"_id": 0}, sort=[("version_number", -1)])
    if latest and latest.get("fingerprint") == fingerprint and not note:
        return {
            "current_version_id": latest.get("version_id"),
            "version_number": latest.get("version_number"),
            "change_detection": _sanitize(latest.get("change_detection") or {"changed": False, "change_count": 0, "summary": ["No governed forecast change detected."]}),
            "recent_versions": [latest],
            "version_count": await db[COLL_FORECAST_SNAPSHOTS].count_documents({"project_number": project_number}),
            "persisted": False,
        }
    version_number = int((latest or {}).get("version_number") or 0) + 1
    change_detection = _diff_snapshots(latest, workspace)
    row = {
        "version_id": f"forecast-version:{project_number}:{version_number:04d}",
        "project_number": project_number,
        "version_number": version_number,
        "fingerprint": fingerprint,
        "generated_at": _now_iso(),
        "generated_by": _actor_identity(actor),
        "note": _clean(note),
        "change_detection": change_detection,
        "workspace": _sanitize(base_payload),
    }
    await db[COLL_FORECAST_SNAPSHOTS].insert_one(row)
    await _write_audit(
        db,
        action="forecast_workspace_versioned",
        actor=actor,
        project_number=project_number,
        resource_type="project_forecasting_workspace",
        resource_id=row["version_id"],
        after=row,
        before=latest,
        metadata={"note": _clean(note)},
    )
    await db["portfolio_intelligence_snapshots"].delete_many({"projects.project_number": project_number})
    await db["project_earned_value_snapshots"].delete_many({"project_number": project_number})
    recent_versions = [_sanitize(item) async for item in db[COLL_FORECAST_SNAPSHOTS].find({"project_number": project_number}, {"_id": 0, "version_id": 1, "version_number": 1, "generated_at": 1, "change_detection": 1, "note": 1}).sort([("version_number", -1)]).limit(8)]
    return {
        "current_version_id": row["version_id"],
        "version_number": row["version_number"],
        "change_detection": change_detection,
        "recent_versions": recent_versions,
        "version_count": await db[COLL_FORECAST_SNAPSHOTS].count_documents({"project_number": project_number}),
        "persisted": True,
    }


async def get_project_forecasting_workspace(
    db,
    project_number: str,
    *,
    actor: Optional[Dict[str, Any]] = None,
    audience: str = "pm",
    note: str = "",
) -> Dict[str, Any]:
    await ensure_project_forecasting_commitments_foundation(db)
    schedule_payload, budget_payload, actuals_payload, op_intel_payload, constraint_payload = await __import__("asyncio").gather(
        _resolve_schedule_forecast(db, project_number),
        get_project_budget_overview(db, project_number),
        get_schedule_actuals_overview(db, project_number),
        get_project_operational_intelligence_snapshot(db, project_number, actor=actor, force_refresh=False),
        _load_constraints(db, project_number),
    )
    quantity_rows = _sanitize(op_intel_payload.get("quantity_by_unit") or [])
    timeline_rows = _sanitize(op_intel_payload.get("timeline_metrics") or [])
    cost_rows = _sanitize(op_intel_payload.get("cost_metrics") or [])
    lineage = _sanitize(op_intel_payload.get("lineage_coverage") or {})
    schedule_finish = _date_text((schedule_payload.get("summary") or {}).get("likely_finish_date") or ((schedule_payload.get("schedule") or {}).get("projected_finish_date")))
    production_rows, production_summary = _build_unit_forecasts(quantity_rows, timeline_rows, schedule_finish)
    resource_payload = _build_resource_forecasts(op_intel_payload, production_rows)
    po_commitments = _build_po_commitments(
        _sanitize(budget_payload.get("commitment_candidates") or []),
        _sanitize(budget_payload.get("actual_cost_candidates") or []),
    )
    manual_commitments = await list_project_forecast_commitments(db, project_number)
    commitment_lane = _build_commitment_lane(manual_commitments, po_commitments, production_rows, resource_payload)
    cost_payload = _build_cost_forecast(cost_rows, budget_payload.get("commitment_candidates") or [], production_rows)
    confidence_payload = _build_confidence_report(schedule_payload, production_rows, constraint_payload, lineage)
    workspace = {
        "project": _sanitize(schedule_payload.get("schedule", {}).get("project") or budget_payload.get("project") or op_intel_payload.get("project") or {"project_number": project_number}),
        "audience": audience,
        "authority_boundaries": {
            "schedule_forecast_authority": "cost_codes.schedule_engine",
            "production_authority": "project_operational_intelligence",
            "budget_commitment_authority": "project_budget_authority",
            "manual_commitment_authority": COLL_FORECAST_COMMITMENTS,
            "actuals_authority": "project_schedule_actuals_spine",
            "constraint_authority": "operational_constraints",
            "ai_role": "advisory_only",
        },
        "generated_at": _now_iso(),
        "generated_by": _actor_label(actor),
        "schedule": schedule_payload,
        "production": {
            "status": "ready" if production_rows else "insufficient_evidence",
            "summary": production_summary,
            "unit_rows": production_rows,
        },
        "resources": {
            "status": "ready",
            **resource_payload,
        },
        "cost": cost_payload,
        "constraints": constraint_payload,
        "commitments": commitment_lane,
        "forecast_vs_actual": _build_forecast_vs_actual(op_intel_payload, schedule_payload, production_summary),
        "commitment_vs_actual": {
            "status": "ready",
            "summary": {
                "at_risk": commitment_lane.get("lifecycle_counts", {}).get("at_risk", 0),
                "missed": commitment_lane.get("lifecycle_counts", {}).get("missed", 0),
                "met": commitment_lane.get("lifecycle_counts", {}).get("met", 0),
            },
            "items": commitment_lane.get("items")[:20],
        },
        "work_block_lineage": {
            "status": "ready",
            "summary": lineage,
            "actual_chain": _sanitize(actuals_payload.get("forecast") or {}),
            "source_review_queue": _sanitize(op_intel_payload.get("review_queue") or [])[:12],
        },
        "confidence": confidence_payload,
        "drivers": [
            *list(schedule_payload.get("drivers") or []),
            *[
                {
                    "driver_id": f"constraint:{row.get('constraint_id')}",
                    "family": "constraint",
                    "label": row.get("title"),
                    "reason": row.get("reason"),
                    "evidence": {"impact": row.get("impact")},
                }
                for row in (constraint_payload.get("forecast_effects") or [])[:4]
            ],
        ],
    }
    versioning = await _persist_snapshot_version(db, project_number, workspace, actor=actor, note=note)
    workspace["versioning"] = versioning
    if audience == "field":
        workspace["field_summary"] = {
            "status": "ready",
            "next_week_quantity_total": production_summary.get("forecast_next_week_total"),
            "required_weekly_total": production_summary.get("required_weekly_total"),
            "at_risk_commitments": len(commitment_lane.get("at_risk_items") or []),
            "crew_rows": (resource_payload.get("crews") or [])[:6],
            "material_rows": (resource_payload.get("materials") or [])[:6],
            "top_drivers": (workspace.get("drivers") or [])[:6],
        }
    return _sanitize(workspace)


async def create_project_forecast_commitment(db, project_number: str, payload: Dict[str, Any], *, actor: Dict[str, Any]) -> Dict[str, Any]:
    await ensure_project_forecasting_commitments_foundation(db)
    row = _commitment_doc(project_number, payload, actor=actor)
    await db[COLL_FORECAST_COMMITMENTS].replace_one({"project_number": project_number, "commitment_id": row["commitment_id"]}, row, upsert=True)
    await _write_audit(
        db,
        action="forecast_commitment_created",
        actor=actor,
        project_number=project_number,
        resource_type="forecast_commitment",
        resource_id=row["commitment_id"],
        after=row,
        metadata={"status": row.get("status"), "family": row.get("family")},
    )
    return _sanitize(row)


async def update_project_forecast_commitment(db, project_number: str, commitment_id: str, payload: Dict[str, Any], *, actor: Dict[str, Any]) -> Dict[str, Any]:
    await ensure_project_forecasting_commitments_foundation(db)
    existing = await db[COLL_FORECAST_COMMITMENTS].find_one({"project_number": project_number, "commitment_id": commitment_id}, {"_id": 0})
    if not existing:
        raise LookupError("forecast commitment not found")
    before = _sanitize(existing)
    row = _commitment_doc(project_number, payload, actor=actor, existing=existing)
    row["commitment_id"] = commitment_id
    await db[COLL_FORECAST_COMMITMENTS].replace_one({"project_number": project_number, "commitment_id": commitment_id}, row, upsert=True)
    await _write_audit(
        db,
        action="forecast_commitment_updated",
        actor=actor,
        project_number=project_number,
        resource_type="forecast_commitment",
        resource_id=commitment_id,
        before=before,
        after=row,
        metadata={"status": row.get("status"), "family": row.get("family")},
    )
    return _sanitize(row)
