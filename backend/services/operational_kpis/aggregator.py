"""services/operational_kpis/aggregator.py — TRACK 23.7.

Shared operational KPI aggregator for MASCI project workspaces.

**One aggregation, three consumers**:

    PM Project workspace  ─┐
    Safety Portal         ─┼─▶  aggregate_project_kpis()
    Future Scheduling     ─┘

All three consumers get the SAME numbers from the SAME source-of-truth
(ODS `operational_facts` + canonical safety/JHA/meeting/inspection
collections). Never re-derived per-surface. Never scraped from PDFs.

**ABSOLUTE RULE**: NO cost, NO dollars, NO rates, NO labor spend, NO
budget, NO finance assumptions. Operational production intelligence
only. This module MUST NOT compute or emit any monetary value.

Windows: `7d` (default), `30d`, `mtd`, `ptd`.

The aggregator reads:

    * `operational_facts` (ODS spine) filtered by `project_id` +
      `is_current=True` + date window.
    * `incidents` (canonical accident/injury/near-miss log)
    * `jhas` (canonical JHA records)
    * `meetings` (canonical safety toolbox talks)
    * `inspections` (canonical safety inspections)
    * `trench_excavations` (canonical trench inspections)
    * `trench_safety_holds` (asset-scoped — cannot filter by
      project_number, so surfaced as PARTIAL in source classification)

Response emits `scheduling_readiness` and `safety_sources` blocks so
downstream consumers can honestly present what is LIVE vs
PARTIAL vs MISSING · FUTURE.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta, date
from typing import Any, Dict, Iterable, List, Optional, Tuple

from lib.kpi_percent_complete import utilization_percent

# --------------------------------------------------------------------------
# Windows
# --------------------------------------------------------------------------
_ALLOWED_WINDOWS = {"7d", "30d", "mtd", "ptd"}


def _today_utc() -> date:
    return datetime.now(timezone.utc).date()


def _resolve_window(window: str) -> Tuple[Optional[str], Optional[str], str]:
    """Return (date_from_iso, date_to_iso, canonical_window)."""
    w = (window or "7d").lower()
    if w not in _ALLOWED_WINDOWS:
        w = "7d"
    today = _today_utc()
    if w == "7d":
        return (today - timedelta(days=6)).isoformat(), today.isoformat(), w
    if w == "30d":
        return (today - timedelta(days=29)).isoformat(), today.isoformat(), w
    if w == "mtd":
        return today.replace(day=1).isoformat(), today.isoformat(), w
    # ptd — no lower bound
    return None, today.isoformat(), w


# --------------------------------------------------------------------------
# Fact utilities
# --------------------------------------------------------------------------
def _num(v: Any) -> float:
    try:
        if v in (None, "", False):
            return 0.0
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _s(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip()


def _date_of(doc: Dict[str, Any]) -> Optional[str]:
    d = doc.get("date") or doc.get("record_date")
    if isinstance(d, str) and len(d) >= 10:
        return d[:10]
    return None


async def _fetch_facts(
    db, project_number: str, date_from: Optional[str], date_to: Optional[str],
) -> Dict[str, List[Dict[str, Any]]]:
    """Fetch operational_facts for a project + window, grouped by
    fact_type. Cheaper than a per-type query and lets the aggregator
    walk the whole set once."""
    q: Dict[str, Any] = {
        "tenant_id": "masci",
        "project_id": project_number,
        "is_current": True,
    }
    if date_from or date_to:
        d: Dict[str, Any] = {}
        if date_from:
            d["$gte"] = date_from
        if date_to:
            d["$lte"] = date_to
        q["date"] = d
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    async for f in db.operational_facts.find(q, {"_id": 0}):
        grouped[f.get("fact_type") or ""].append(f)
    return grouped


# --------------------------------------------------------------------------
# Labor KPIs (from labor_fact + Track 23.5 display keys)
# --------------------------------------------------------------------------
def _labor_kpis(facts: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_hours = 0.0
    employee_ids: set = set()
    person_names: set = set()
    by_trade: Counter = Counter()
    by_crew: Counter = Counter()
    by_supervisor: Counter = Counter()
    by_cost_code: Counter = Counter()
    by_day: Dict[str, float] = defaultdict(float)

    for f in facts:
        p = f.get("payload") or {}
        hours = _num(p.get("hours"))
        total_hours += hours
        eid = _s(p.get("employee_id"))
        if eid:
            employee_ids.add(eid)
        pname = _s(p.get("person_name"))
        if pname:
            person_names.add(pname.lower())
        # Alias-tolerant reads — pre-23.5 payloads only had `role`,
        # post-23.5 also carry *_display keys.
        trade = (
            _s(p.get("trade_role_display"))
            or _s(p.get("trade_snapshot"))
            or _s(p.get("role"))
        )
        crew = (
            _s(p.get("crew_display"))
            or _s(p.get("crew_snapshot"))
        )
        sup = (
            _s(p.get("supervisor_display"))
            or _s(p.get("supervisor_snapshot"))
        )
        cc = _s(p.get("cost_code"))
        if trade:
            by_trade[trade] += hours
        if crew:
            by_crew[crew] += hours
        if sup:
            by_supervisor[sup] += hours
        if cc:
            by_cost_code[cc] += hours
        d = _date_of(f)
        if d:
            by_day[d] += hours

    # Employee count = union of verified IDs + unique names (best-effort).
    unique_employee_count = len(employee_ids) + max(
        0, len(person_names) - len(employee_ids)
    )
    return {
        "total_man_hours": round(total_hours, 2),
        "labor_row_count": len(facts),
        "unique_employee_count": unique_employee_count,
        "verified_employee_count": len(employee_ids),
        "by_trade": [{"key": k, "hours": round(v, 2)} for k, v in by_trade.most_common(50)],
        "by_crew": [{"key": k, "hours": round(v, 2)} for k, v in by_crew.most_common(50)],
        "by_supervisor": [{"key": k, "hours": round(v, 2)} for k, v in by_supervisor.most_common(50)],
        "by_cost_code": [{"key": k, "hours": round(v, 2)} for k, v in by_cost_code.most_common(50)],
        "daily_trend": [
            {"date": d, "hours": round(by_day[d], 2)} for d in sorted(by_day.keys())
        ],
    }


# --------------------------------------------------------------------------
# Equipment KPIs (from equipment_fact)
# --------------------------------------------------------------------------
def _equipment_kpis(facts: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_run = 0.0
    total_idle = 0.0
    equipment_ids: set = set()
    issues = 0
    by_equipment: Dict[str, Dict[str, float]] = defaultdict(lambda: {"run": 0.0, "idle": 0.0})
    by_day_run: Dict[str, float] = defaultdict(float)
    by_day_idle: Dict[str, float] = defaultdict(float)
    by_cost_code_run: Counter = Counter()
    by_cost_code_idle: Counter = Counter()
    issues_by_label: Counter = Counter()

    for f in facts:
        p = f.get("payload") or {}
        run = _num(p.get("hours_used"))
        idle = _num(p.get("idle_hours"))
        label = _s(p.get("equipment_label")) or _s(p.get("equipment_id")) or "(unlabelled)"
        breakdown = bool(p.get("breakdown"))
        maintenance = bool(p.get("maintenance"))
        cc = _s(p.get("cost_code"))
        total_run += run
        total_idle += idle
        equipment_ids.add(label)
        if breakdown or maintenance:
            issues += 1
            issues_by_label[label] += 1
        by_equipment[label]["run"] += run
        by_equipment[label]["idle"] += idle
        if cc:
            by_cost_code_run[cc] += run
            by_cost_code_idle[cc] += idle
        d = _date_of(f)
        if d:
            by_day_run[d] += run
            by_day_idle[d] += idle

    denom = total_run + total_idle
    # KPI-UTILIZATION (equipment run): run / (run + idle). Governed zero-denom -> 0.
    utilization = utilization_percent(total_run, denom, ndigits=6)
    per_eq = sorted(
        (
            {
                "equipment": lbl,
                "run": round(v["run"], 2),
                "idle": round(v["idle"], 2),
                "utilization": utilization_percent(v["run"], v["run"] + v["idle"], ndigits=1),
            }
            for lbl, v in by_equipment.items()
        ),
        key=lambda r: -r["run"],
    )
    trend_days = sorted(set(list(by_day_run.keys()) + list(by_day_idle.keys())))
    return {
        "total_run_hours": round(total_run, 2),
        "total_idle_hours": round(total_idle, 2),
        "utilization_percent": round(utilization, 1),
        "equipment_count": len(equipment_ids),
        "issue_count": issues,
        "issues_by_equipment": [
            {"equipment": k, "count": v} for k, v in issues_by_label.most_common(20)
        ],
        "by_equipment": per_eq[:50],
        "by_cost_code": [
            {"key": k, "run": round(by_cost_code_run[k], 2),
             "idle": round(by_cost_code_idle[k], 2)}
            for k in sorted(set(list(by_cost_code_run.keys()) + list(by_cost_code_idle.keys())))
        ],
        "daily_trend": [
            {"date": d, "run": round(by_day_run.get(d, 0.0), 2),
             "idle": round(by_day_idle.get(d, 0.0), 2)}
            for d in trend_days
        ],
    }


# --------------------------------------------------------------------------
# Material KPIs (from material_fact)
# --------------------------------------------------------------------------
def _material_kpis(facts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Inbound vs outbound classification is a best-effort:
    signed quantity → negative == outbound (haul-out); positive ==
    inbound. If direction field present (`direction`, `movement`),
    use it. Never inflate numbers by double-counting."""
    inbound: Dict[Tuple[str, str], float] = defaultdict(float)   # (material, unit) → qty
    outbound: Dict[Tuple[str, str], float] = defaultdict(float)
    carrier_counts: Counter = Counter()
    ticket_count = 0
    load_count = 0
    by_day_in: Dict[str, float] = defaultdict(float)
    by_day_out: Dict[str, float] = defaultdict(float)

    for f in facts:
        p = f.get("payload") or {}
        material = _s(p.get("material")) or "(unlabelled)"
        unit = _s(p.get("unit")) or "EA"
        qty = _num(p.get("quantity"))
        supplier = _s(p.get("supplier")) or _s(p.get("carrier"))
        ticket = _s(p.get("ticket"))
        direction = _s(p.get("direction") or p.get("movement")).lower()
        d = _date_of(f)
        if ticket:
            ticket_count += 1
        load_count += 1

        is_outbound = (
            direction in ("outbound", "out", "haul_out", "haul-out")
            or qty < 0
        )
        abs_qty = abs(qty)
        if is_outbound:
            outbound[(material, unit)] += abs_qty
            if d:
                by_day_out[d] += abs_qty
        else:
            inbound[(material, unit)] += abs_qty
            if d:
                by_day_in[d] += abs_qty
        if supplier:
            carrier_counts[supplier] += 1

    def _emit(pairs) -> List[Dict[str, Any]]:
        return sorted(
            [{"material": m, "unit": u, "quantity": round(q, 2)}
             for (m, u), q in pairs.items()],
            key=lambda r: -r["quantity"],
        )

    trend_days = sorted(set(list(by_day_in.keys()) + list(by_day_out.keys())))
    return {
        "inbound_by_material_unit": _emit(inbound),
        "outbound_by_material_unit": _emit(outbound),
        "load_count": load_count,
        "ticket_count": ticket_count,
        "carriers": [
            {"carrier": k, "loads": v}
            for k, v in carrier_counts.most_common(30)
        ],
        "daily_trend": [
            {"date": d,
             "inbound": round(by_day_in.get(d, 0.0), 2),
             "outbound": round(by_day_out.get(d, 0.0), 2)}
            for d in trend_days
        ],
    }


# --------------------------------------------------------------------------
# Production KPIs (from production_fact)
# --------------------------------------------------------------------------
def _production_kpis(facts: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_activity_unit: Dict[Tuple[str, str], float] = defaultdict(float)
    by_cost_code_unit: Dict[Tuple[str, str], float] = defaultdict(float)
    by_day: Dict[str, int] = defaultdict(int)
    percent_complete_snapshots: List[Dict[str, Any]] = []
    stations: List[Dict[str, str]] = []

    for f in facts:
        p = f.get("payload") or {}
        activity = _s(p.get("activity")) or "(unlabelled)"
        unit = _s(p.get("unit")) or "EA"
        qty = _num(p.get("quantity"))
        cc = _s(p.get("cost_code"))
        by_activity_unit[(activity, unit)] += qty
        if cc:
            by_cost_code_unit[(cc, unit)] += qty
        pc = p.get("percent_complete")
        if isinstance(pc, (int, float)):
            percent_complete_snapshots.append({
                "activity": activity, "date": _date_of(f) or "",
                "percent_complete": float(pc),
            })
        sf = _s(p.get("station_from"))
        st = _s(p.get("station_to"))
        if sf or st:
            stations.append({"activity": activity, "from": sf, "to": st,
                             "date": _date_of(f) or ""})
        d = _date_of(f)
        if d:
            by_day[d] += 1

    return {
        "by_activity_unit": sorted(
            [{"activity": a, "unit": u, "quantity": round(q, 2)}
             for (a, u), q in by_activity_unit.items()],
            key=lambda r: -r["quantity"],
        ),
        "by_cost_code_unit": sorted(
            [{"cost_code": c, "unit": u, "quantity": round(q, 2)}
             for (c, u), q in by_cost_code_unit.items()],
            key=lambda r: -r["quantity"],
        ),
        "percent_complete_snapshots": percent_complete_snapshots[:25],
        "station_coverage": stations[:25],
        "row_count": len(facts),
        "daily_trend": [
            {"date": d, "entries": by_day[d]} for d in sorted(by_day.keys())
        ],
    }


# --------------------------------------------------------------------------
# Delay KPIs (from delay_fact)
# --------------------------------------------------------------------------
def _delay_kpis(facts: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_hours = 0.0
    by_category: Dict[str, Dict[str, float]] = defaultdict(lambda: {"count": 0, "hours": 0.0})
    highest_severity: List[Dict[str, Any]] = []
    unresolved = 0

    for f in facts:
        p = f.get("payload") or {}
        hrs = _num(p.get("duration_hours"))
        cat = _s(p.get("delay_category")) or "(uncategorized)"
        total_hours += hrs
        by_category[cat]["count"] += 1
        by_category[cat]["hours"] += hrs
        if _s(p.get("impact")).lower() in ("high", "severe", "critical"):
            highest_severity.append({
                "category": cat, "reason": _s(p.get("reason")),
                "hours": round(hrs, 2), "date": _date_of(f) or "",
                "responsible_party": _s(p.get("responsible_party")),
            })
        if _s(p.get("needed_action")):
            unresolved += 1

    return {
        "delay_count": len(facts),
        "total_hours_impact": round(total_hours, 2),
        "by_category": sorted(
            [{"category": k, "count": int(v["count"]),
              "hours": round(v["hours"], 2)}
             for k, v in by_category.items()],
            key=lambda r: -r["hours"],
        ),
        "highest_severity": highest_severity[:25],
        "unresolved_follow_ups": unresolved,
    }


# --------------------------------------------------------------------------
# Safety KPIs — multi-source, honest classification
# --------------------------------------------------------------------------
async def _safety_kpis(
    db, project_number: str,
    daily_safety_facts: List[Dict[str, Any]],
    photo_facts: List[Dict[str, Any]],
    date_from: Optional[str], date_to: Optional[str],
) -> Dict[str, Any]:
    # 1) Daily Report safety events (safety_fact from ODS)
    types: Counter = Counter()
    injuries = 0
    contacted_yes = 0
    contacted_no = 0
    utility_strikes = 0
    for f in daily_safety_facts:
        p = f.get("payload") or {}
        st = _s(p.get("safety_type")).lower()
        types[st or "unspecified"] += 1
        if p.get("injuries_reported"):
            injuries += 1
        contacted = p.get("safety_contacted")
        if contacted is True:
            contacted_yes += 1
        elif contacted is False:
            contacted_no += 1
        if "utility" in st or "utility_strike" in st:
            utility_strikes += 1

    # 2) Incidents (canonical) — filter by project_number + date
    incident_q: Dict[str, Any] = {"project_number": project_number}
    if date_from or date_to:
        d: Dict[str, Any] = {}
        if date_from:
            d["$gte"] = date_from
        if date_to:
            d["$lte"] = date_to
        incident_q["incident_date"] = d
    inc_count = 0
    accident_count = 0
    near_miss_count = 0
    inc_utility_strike = 0
    inc_open = 0
    async for inc in db.incidents.find(incident_q, {
        "_id": 0, "incident_type": 1, "incident_date": 1,
        "id": 1, "status": 1, "case_status": 1, "closed_at": 1,
    }):
        inc_count += 1
        t = _s(inc.get("incident_type")).lower()
        if "accident" in t or "injury" in t:
            accident_count += 1
        if "near" in t:
            near_miss_count += 1
        if "utility" in t or "strike" in t:
            inc_utility_strike += 1
        if not inc.get("closed_at"):
            inc_open += 1

    utility_strikes += inc_utility_strike

    # 3) Safety meetings (canonical) — filter by project_number + date
    meeting_q: Dict[str, Any] = {"project_number": project_number}
    if date_from or date_to:
        d = {}
        if date_from:
            d["$gte"] = date_from
        if date_to:
            d["$lte"] = date_to
        meeting_q["meeting_date"] = d
    meeting_count = await db.meetings.count_documents(meeting_q)

    # 4) JHAs
    jha_q: Dict[str, Any] = {"project_number": project_number}
    if date_from or date_to:
        d = {}
        if date_from:
            d["$gte"] = date_from
        if date_to:
            d["$lte"] = date_to
        jha_q["jha_date"] = d
    jha_count = await db.jhas.count_documents(jha_q)

    # 5) Safety inspections (canonical)
    insp_q: Dict[str, Any] = {"project_number": project_number}
    if date_from or date_to:
        d = {}
        if date_from:
            d["$gte"] = date_from
        if date_to:
            d["$lte"] = date_to
        insp_q["inspection_date"] = d
    inspection_count = await db.inspections.count_documents(insp_q)

    # 6) Trench excavations
    trench_q: Dict[str, Any] = {"project_number": project_number}
    if date_from or date_to:
        d = {}
        if date_from:
            d["$gte"] = date_from
        if date_to:
            d["$lte"] = date_to
        trench_q["date_of_work"] = d
    trench_count = await db.trench_excavations.count_documents(trench_q)

    # 7) Safety photo evidence
    safety_photo_count = 0
    for pf in photo_facts:
        p = pf.get("payload") or {}
        cap = _s(p.get("caption")).lower()
        act = _s(p.get("linked_activity")).lower()
        if any(t in cap or t in act for t in ("safety", "ppe", "hazard", "jha")):
            safety_photo_count += 1

    # 8) Missing escalation gap — safety events where contacted_no
    #    (fields required by policy Track 23.4A)
    escalation_gaps = contacted_no

    total_events = len(daily_safety_facts) + inc_count
    return {
        "safety_event_count": total_events,
        "daily_report_safety_events": len(daily_safety_facts),
        "incident_count": inc_count,
        "accident_count": accident_count,
        "near_miss_count": near_miss_count,
        "utility_strike_count": utility_strikes,
        "injuries_reported": injuries,
        "safety_contacted_yes": contacted_yes,
        "safety_contacted_no": contacted_no,
        "escalation_gap_count": escalation_gaps,
        "open_incidents": inc_open,
        "safety_meetings_count": meeting_count,
        "jha_count": jha_count,
        "safety_inspection_count": inspection_count,
        "trench_inspection_count": trench_count,
        "safety_photo_count": safety_photo_count,
        "by_daily_safety_type": [
            {"type": k, "count": v} for k, v in types.most_common(15)
        ],
    }


async def _safety_source_classification(
    db, project_number: str,
) -> Dict[str, Dict[str, Any]]:
    """Return per-source availability so Safety Portal can render
    honest LIVE / PARTIAL / MISSING · FUTURE badges."""
    def _cls(count: int) -> str:
        return "LIVE" if count > 0 else "PARTIAL"

    daily_safety = await db.operational_facts.count_documents({
        "tenant_id": "masci",
        "fact_type": "safety_fact", "project_id": project_number,
    })
    incident_count = await db.incidents.count_documents({
        "project_number": project_number,
    })
    meeting_count = await db.meetings.count_documents({
        "project_number": project_number,
    })
    jha_count = await db.jhas.count_documents({
        "project_number": project_number,
    })
    insp_count = await db.inspections.count_documents({
        "project_number": project_number,
    })
    trench_count = await db.trench_excavations.count_documents({
        "project_number": project_number,
    })
    dvir_count = await db.equipment_inspections.count_documents({})
    # trench_safety_holds is asset-scoped, cannot be project-filtered
    # without traversing deployments — surfaced as PARTIAL.
    return {
        "daily_report_safety_events": {
            "status": "LIVE" if daily_safety > 0 else "PARTIAL",
            "count": daily_safety,
            "source": "operational_facts.safety_fact",
        },
        "incidents": {
            "status": _cls(incident_count),
            "count": incident_count,
            "source": "db.incidents",
        },
        "safety_meetings": {
            "status": _cls(meeting_count),
            "count": meeting_count,
            "source": "db.meetings",
        },
        "jha_records": {
            "status": _cls(jha_count),
            "count": jha_count,
            "source": "db.jhas",
        },
        "safety_inspections": {
            "status": _cls(insp_count),
            "count": insp_count,
            "source": "db.inspections",
        },
        "trench_excavations": {
            "status": _cls(trench_count),
            "count": trench_count,
            "source": "db.trench_excavations",
        },
        "equipment_dvir": {
            "status": "PARTIAL" if dvir_count > 0 else "MISSING · FUTURE",
            "count": dvir_count,
            "source": "db.equipment_inspections",
            "note": "Not project-scoped in schema — surfaced as PARTIAL until project-linking lands.",
        },
        "trench_holds": {
            "status": "PARTIAL",
            "count": None,
            "source": "db.trench_safety_holds",
            "note": "Asset-scoped only. Project cross-walk requires deployment join — future track.",
        },
        "near_miss_reports": {
            "status": "PARTIAL",
            "count": None,
            "source": "db.incidents (filtered)",
            "note": "Currently derived from incident_type; dedicated near-miss form is future work.",
        },
    }


# --------------------------------------------------------------------------
# Intelligence KPIs (from intelligence_fact + photo_evidence_fact +
# day_summary_fact if present)
# --------------------------------------------------------------------------
def _intelligence_kpis(
    intelligence_facts: List[Dict[str, Any]],
    photo_facts: List[Dict[str, Any]],
) -> Dict[str, Any]:
    accepted = 0
    latest_summary: Optional[Dict[str, Any]] = None
    for f in sorted(intelligence_facts, key=lambda x: x.get("date", ""), reverse=True):
        p = f.get("payload") or {}
        if p.get("accepted") or p.get("status") in ("accepted", "approved"):
            accepted += 1
        if latest_summary is None:
            latest_summary = {
                "date": _date_of(f) or "",
                "audience": _s(p.get("audience")),
                "agent": _s(p.get("agent")),
                "chars": int(p.get("chars") or 0),
                "language": _s(p.get("language")),
            }
    photo_tags: Counter = Counter()
    photo_observations = 0
    for f in photo_facts:
        p = f.get("payload") or {}
        photo_observations += 1
        for tag in (p.get("tags") or []):
            t = _s(tag)
            if t:
                photo_tags[t] += 1
        # Fallback: use linked_activity as a coarse tag when no
        # explicit `tags` are present.
        la = _s(p.get("linked_activity"))
        if la and not p.get("tags"):
            photo_tags[la] += 1

    return {
        "accepted_summaries_count": accepted,
        "intelligence_row_count": len(intelligence_facts),
        "latest_summary": latest_summary,
        "photo_observation_count": photo_observations,
        "top_photo_tags": [
            {"tag": k, "count": v} for k, v in photo_tags.most_common(15)
        ],
    }


# --------------------------------------------------------------------------
# Scheduling readiness — what future scheduling can consume today
# --------------------------------------------------------------------------
def _scheduling_readiness(bundles: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    return {
        "labor_signal_available": bool(bundles.get("labor_fact")),
        "equipment_signal_available": bool(bundles.get("equipment_fact")),
        "material_signal_available": bool(bundles.get("material_fact")),
        "production_signal_available": bool(bundles.get("production_fact")),
        "delay_signal_available": bool(bundles.get("delay_fact")),
        "safety_signal_available": bool(bundles.get("safety_fact")),
        "weather_signal_available": bool(bundles.get("weather_fact")),
        "tomorrow_plan_available": False,  # tomorrow-plan facts not yet emitted
        "readiness_signal_available": bool(bundles.get("readiness_fact")),
        "notes": (
            "Scheduling can consume every LIVE signal above. "
            "Tomorrow-plan / crew-availability forecasting are FUTURE."
        ),
    }


# --------------------------------------------------------------------------
# Public entrypoint
# --------------------------------------------------------------------------
async def aggregate_project_kpis(
    db,
    project_number: str,
    window: str = "7d",
) -> Dict[str, Any]:
    """Read-only. No cost. No dollars. No rates. Shared spine for PM,
    Safety Portal, and future Scheduling."""
    date_from, date_to, canonical_window = _resolve_window(window)
    bundles = await _fetch_facts(db, project_number, date_from, date_to)

    labor = _labor_kpis(bundles.get("labor_fact", []))
    equipment = _equipment_kpis(bundles.get("equipment_fact", []))
    materials = _material_kpis(bundles.get("material_fact", []))
    production = _production_kpis(bundles.get("production_fact", []))
    delays = _delay_kpis(bundles.get("delay_fact", []))
    safety = await _safety_kpis(
        db, project_number,
        bundles.get("safety_fact", []),
        bundles.get("photo_evidence_fact", []),
        date_from, date_to,
    )
    intelligence = _intelligence_kpis(
        bundles.get("intelligence_fact", []),
        bundles.get("photo_evidence_fact", []),
    )
    safety_sources = await _safety_source_classification(db, project_number)
    scheduling_readiness = _scheduling_readiness(bundles)

    # Project name resolution — best-effort, non-fatal.
    project_name = ""
    try:
        j = await db.jobs_master.find_one(
            {"project_number": project_number},
            {"_id": 0, "project_name": 1, "name": 1},
        )
        if j:
            project_name = _s(j.get("project_name") or j.get("name"))
    except Exception:
        project_name = ""

    return {
        "project_number": project_number,
        "project_name": project_name,
        "window": canonical_window,
        "date_from": date_from,
        "date_to": date_to,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "contract_version": "23.7",
        "labor": labor,
        "equipment": equipment,
        "materials": materials,
        "production": production,
        "delays": delays,
        "safety": safety,
        "intelligence": intelligence,
        "safety_sources": safety_sources,
        "scheduling_readiness": scheduling_readiness,
    }


__all__ = [
    "aggregate_project_kpis",
    "_resolve_window",
]
