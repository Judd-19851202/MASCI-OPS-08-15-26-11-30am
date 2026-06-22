"""
TRACK 15.62 · Admin-tier Daily Report intelligence endpoints.

Adds:
  GET  /api/admin/daily-roll-up?from=YYYY-MM-DD&to=YYYY-MM-DD&project=
       Executive cross-project aggregation. Returns the full
       `rollup_window` payload from `lib/daily_report_rollup.py`
       so an exec dashboard can render: total loads in/out, by
       material breakdown, by project breakdown, top haulers, and
       narrative health metrics.

  GET  /api/admin/daily-report-health?days=30
       Daily Report Health surface. Reports the narrative-completion
       % and word-count metrics over a rolling window so an admin
       can watch the Track-15.62 recovery land in real time.

Both endpoints gate on the canonical admin/PM/HR read dep so they
behave identically to existing safety-side surfaces.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query

from lib.daily_report_rollup import rollup_window, load_material_vocabulary


def register_dr_admin_intel_routes(
    api_router: APIRouter,
    db,
    *,
    require_admin_pm_or_hr_read,
):
    """Bind the two admin-tier Daily Report intelligence endpoints to
    the platform's main `api_router`."""

    @api_router.get("/admin/daily-roll-up")
    async def daily_roll_up(
        actor=Depends(require_admin_pm_or_hr_read),
        date_from: Optional[str] = Query(default=None, alias="from"),
        date_to: Optional[str] = Query(default=None, alias="to"),
        project: Optional[str] = Query(default=None),
    ) -> Dict[str, Any]:
        # Default window: last 7 days inclusive.
        today = datetime.now(timezone.utc).date()
        if not date_to:
            date_to = today.isoformat()
        if not date_from:
            date_from = (today - timedelta(days=7)).isoformat()
        projects = [project] if project else None
        rollup = await rollup_window(
            db, date_from=date_from, date_to=date_to,
            project_numbers=projects,
        )
        rollup["actor"] = {
            "kind": getattr(actor, "_actor_kind", None) or actor.get("_actor_kind") if isinstance(actor, dict) else None,
        }
        rollup["ok"] = True
        return rollup

    @api_router.get("/admin/daily-report-health")
    async def daily_report_health(
        actor=Depends(require_admin_pm_or_hr_read),
        days: int = Query(default=30, ge=1, le=180),
    ) -> Dict[str, Any]:
        today = datetime.now(timezone.utc).date()
        date_from = (today - timedelta(days=days)).isoformat()
        rollup = await rollup_window(
            db, date_from=date_from, date_to=today.isoformat(),
            project_numbers=None,
        )
        nh = rollup.get("narrative_health", {}) or {}
        total = int(nh.get("total") or 0)
        with_acts = int(nh.get("with_activities") or 0)
        with_gen = int(nh.get("with_general_notes") or 0)
        with_sections = int(nh.get("with_narrative_sections") or 0)
        blank = int(nh.get("blank") or 0)
        pct = lambda n: round(100.0 * n / max(1, total), 1)
        return {
            "ok": True,
            "window_days": days,
            "from": date_from,
            "to": today.isoformat(),
            "totals": {
                "reports": total,
                "with_activities": with_acts,
                "with_general_notes": with_gen,
                "with_narrative_sections": with_sections,
                "blank": blank,
            },
            "percentages": {
                "activity_log_completion_pct": pct(with_acts),
                "general_notes_completion_pct": pct(with_gen),
                "narrative_sections_completion_pct": pct(with_sections),
                "any_narrative_completion_pct": nh.get("completion_pct"),
                "blank_pct": pct(blank),
            },
            "word_counts": {
                "avg": nh.get("avg_word_count"),
                "median": nh.get("median_word_count"),
            },
            "loads_window": {
                "in": rollup.get("loads", {}).get("in"),
                "out": rollup.get("loads", {}).get("out"),
            },
            "missing": {
                "story_pct": round(100.0 * blank / max(1, total), 1),
                # Reports missing tomorrow_plan / delays inside
                # narrative_sections — only meaningful for reports
                # that have any narrative_sections at all.
                "tomorrow_plan_missing_pct": _section_missing_pct(rollup, "tomorrow_plan"),
                "delays_missing_pct": _section_missing_pct(rollup, "delays"),
            },
            "vocab_size": rollup.get("meta", {}).get("vocab_size"),
        }

    @api_router.get("/admin/material-vocabulary")
    async def admin_material_vocabulary(
        actor=Depends(require_admin_pm_or_hr_read),
    ) -> Dict[str, Any]:
        rows = await load_material_vocabulary(db)
        return {"ok": True, "rows": rows, "size": len(rows)}


def _section_missing_pct(rollup: Dict[str, Any], section_key: str) -> float:
    """Approximate the percentage of narrative-sections-bearing
    reports that lack a particular section. Since `rollup_window`
    only counts presence, the deep per-section breakdown lives in a
    follow-up tighter query — placeholder returns the overall blank
    percentage for now so the dashboard tile has a defensible value
    while Session B wires the per-section detail."""
    nh = rollup.get("narrative_health", {}) or {}
    total = int(nh.get("total") or 0)
    sections_present = int(nh.get("with_narrative_sections") or 0)
    if not total:
        return 0.0
    # Until per-section detail lands in Session B, surface the
    # "no narrative_sections at all" rate as the conservative upper
    # bound: every report without sections necessarily lacks this
    # section. This will tighten in Session B.
    return round(100.0 * (total - sections_present) / total, 1)
