"""Every Operational Intelligence product registers itself here.

Two products ship IMPLEMENTED:
- ``safety_morning_digest`` — reuses Track 19.39 composition
- ``executive_operations_brief`` — real aggregator over portfolio data

Eight products ship CONTRACT_REGISTERED:
- weekly_operations_digest · transportation_intelligence · fleet_intelligence
- hr_intelligence · training_intelligence · project_intelligence
- shop_intelligence · corporate_intelligence

Contract-registered products expose full metadata (permission · schedule ·
template · deep-link builder) but their aggregator raises
``NotImplementedError`` so a caller cannot receive fabricated data.
"""
from __future__ import annotations

from typing import Any, Dict

from .registry import (
    OperationalIntelligenceProduct as Product,
    ProductStatus, register_product,
)


def _base_link(cid: str) -> str:
    return f"/safety/cases/{cid}/executive-report"


# ---------------------------------------------------------------------------
# 1 · Morning Safety Intelligence (IMPLEMENTED — Track 19.39 migrated)
# ---------------------------------------------------------------------------
async def _agg_safety_morning(db, **kwargs) -> Dict[str, Any]:
    # Reuse the Track 19.39 composer verbatim — no duplication.
    from incident_engine.morning_digest import compose_digest, SUBJECT_DEFAULT
    from .product_layout import build_standard_layout
    from .score_model import (
        score_from_contributors, Contributor, insufficient_data_score,
    )
    from .engine import compute_trend

    d = await compose_digest(
        db,
        digest_window_days=kwargs.get("window", 7),
        top_n=kwargs.get("top_n", 5),
    )
    es = d["executive_summary"]
    top = d["top_attention_cases"]
    needs = d["needs_attention_today"]
    trends = d["portfolio_trends"]

    total_open = int(es.get("total_open_cases") or 0)
    high = int(es.get("high_attention_cases") or 0)
    overdue_capas = int(es.get("overdue_capas") or 0)
    avg_readiness = int(es.get("average_readiness_pct") or 0)
    opened = int(es.get("cases_opened_recent") or 0)
    closed = int(es.get("cases_closed_recent") or 0)

    # Score contributors (real data, honest signals)
    positives, negatives = [], []
    if closed >= opened and opened > 0:
        positives.append(Contributor(
            key="closure_pace", label=f"Closed {closed} vs opened {opened} (last 7d)",
            impact=8, detail="Closure pace ≥ open pace."))
    if avg_readiness >= 80:
        positives.append(Contributor(
            key="high_readiness", label=f"Avg readiness {avg_readiness}%",
            impact=6, detail="Portfolio-wide readiness ≥ 80%."))
    if high > 0:
        negatives.append(Contributor(
            key="high_attention_cases",
            label=f"{high} high-attention case(s)",
            impact=-min(30, high * 8),
            detail="Cases scored HIGH by the passive scorer this period."))
    if overdue_capas > 0:
        negatives.append(Contributor(
            key="overdue_capas", label=f"{overdue_capas} overdue CAPA(s)",
            impact=-min(25, overdue_capas * 4),
            detail="CAPAs past due date."))
    if needs.get("evidence_gaps"):
        negatives.append(Contributor(
            key="evidence_gaps",
            label=f"{needs['evidence_gaps']} case(s) with evidence gaps",
            impact=-8, detail="Cases missing required evidence."))

    if total_open == 0 and opened == 0 and closed == 0:
        score = insufficient_data_score(
            "No open cases and no cases opened/closed in the last 7 days.")
    else:
        # Trend on open-case count: current week's opened vs closed.
        tr = compute_trend(opened, closed)
        score = score_from_contributors(
            baseline=100,
            positives=positives, negatives=negatives,
            trend_percent=tr["pct_change"],
            confidence="high" if total_open >= 3 else "medium",
            data_freshness="live",
            calculation_notes=(
                "Composite of high-attention volume, overdue CAPAs, "
                "evidence gaps, closure pace, and average readiness."
            ),
        )

    # Trend direction (open cases as headline metric)
    trend_dir = compute_trend(total_open, total_open - opened + closed)

    top_5_rows = [[
        {"href": _base_link(r["case_id"]),
         "text": f"#{r.get('case_number') or r['case_id'][:8]}"},
        r.get("job_number") or "",
        r.get("incident_type") or "",
        f"{(r.get('attention_level') or 'low').upper()} · {r.get('attention_score')}",
        r.get("days_open") or "",
        r.get("capa_open") or 0,
    ] for r in top]

    win_items = []
    if closed > 0:
        win_items.append(f"Closed {closed} case(s) this period.")
    if avg_readiness >= 80:
        win_items.append(f"Portfolio readiness holding at {avg_readiness}%.")
    if high == 0 and total_open > 0:
        win_items.append("Zero high-attention cases this period.")

    attention_items = []
    if needs.get("evidence_gaps"):
        attention_items.append(f"{needs['evidence_gaps']} case(s) with evidence gaps.")
    if needs.get("overdue_capas"):
        attention_items.append(f"{needs['overdue_capas']} case(s) with overdue CAPAs.")
    if needs.get("delayed_closeout"):
        attention_items.append(f"{needs['delayed_closeout']} case(s) with delayed closeout.")
    if needs.get("executive_review_needed"):
        attention_items.append(f"{needs['executive_review_needed']} case(s) need executive review.")

    recent_changes = [
        f"Opened last 7d: {opened}",
        f"Closed last 7d: {closed}",
    ]

    layout = build_standard_layout(
        product_id="safety_morning_digest",
        subject=SUBJECT_DEFAULT,
        period_label="Weekly · Monday 13:00 UTC",
        executive_summary={
            "Open cases":       total_open,
            "High attention":   high,
            "Opened last 7d":   opened,
            "Closed last 7d":   closed,
            "Overdue CAPAs":    overdue_capas,
            "Avg readiness %":  avg_readiness,
        },
        score=score.to_dict(),
        trend_direction={"arrow": trend_dir["arrow"], "tone": trend_dir["tone"],
                         "pct_change": trend_dir["pct_change"],
                         "current": total_open,
                         "previous": total_open - opened + closed},
        top_wins=win_items,
        needs_immediate_attention=attention_items,
        top_5_items={
            "title": "Top Attention Cases",
            "headers": ["Case", "Project", "Type", "Attention", "Days open", "CAPA open"],
            "rows": top_5_rows,
        } if top_5_rows else None,
        core_metrics={
            "Portfolio trends":
                ", ".join(f"{k.replace('_',' ')}={v}"
                          for k, v in trends.items() if v > 0) or "no signals",
        },
        recommendations=(
            [f"Prioritise {high} high-attention case(s) this week."] if high > 0 else []
        ) + (
            [f"Close overdue CAPAs ({overdue_capas})."] if overdue_capas > 0 else []
        ) + (
            ["Portfolio calm — maintain rhythm."] if not high and not overdue_capas else []
        ),
        upcoming_risks=[],
        recent_changes=recent_changes,
        deep_links=[
            {"href": "/safety/cases", "text": "Safety Case Center"},
            {"href": "/safety/case-workspace", "text": "Case Workspace"},
        ],
        no_auto_decision_notice=d["no_auto_decision_notice"],
        audit_footer=(
            "Reuses Track 19.39 aggregator (`compose_digest`) verbatim. "
            "Track 19.42 wraps its output in the standard 14-section layout."
        ),
    )
    # Preserve legacy 19.39 shape for downstream consumers.
    layout["legacy_v1_shape"] = d
    return layout


register_product(Product(
    product_id="safety_morning_digest",
    display_name="Morning Safety Intelligence",
    summary="Weekly Safety attention brief.",
    permission_role="safety_or_admin",
    template_key="executive_v1",
    schedule_freq="weekly",
    schedule_iso_day=1,   # Monday
    schedule_hour_utc=13, # 13:00 UTC ≈ 07:00 CT
    status=ProductStatus.IMPLEMENTED,
    aggregator=_agg_safety_morning,
    deep_link_builder=lambda ctx: _base_link(ctx.get("case_id", "")),
    tags=["safety", "weekly", "attention"],
))


# ---------------------------------------------------------------------------
# 2 · Executive Operations Brief (IMPLEMENTED — real aggregator)
# ---------------------------------------------------------------------------
async def _agg_executive_ops(db, **kwargs) -> Dict[str, Any]:
    from incident_engine.portfolio_intelligence import (
        _list_cases_readonly, _rows_for_cases,
    )
    from .product_layout import build_standard_layout
    from .score_model import (
        score_from_contributors, Contributor, insufficient_data_score,
    )

    cases = await _list_cases_readonly(db, limit=kwargs.get("limit", 200))
    rows = await _rows_for_cases(db, cases, want_attention=True)
    total = len(rows)
    open_ = sum(1 for r in rows if (r.get("state") or "").upper() != "CLOSED")
    high = sum(1 for r in rows if r.get("attention_level") == "high")
    med = sum(1 for r in rows if r.get("attention_level") == "medium")
    low = sum(1 for r in rows if r.get("attention_level") == "low")
    capa_open = sum(r.get("capa_open") or 0 for r in rows)
    days_open_vals = [r.get("days_open") or 0 for r in rows]
    avg_days = round(sum(days_open_vals) / len(days_open_vals)) if days_open_vals else 0

    positives, negatives = [], []
    if total > 0 and high == 0:
        positives.append(Contributor(
            key="no_high_attention", label="No HIGH-attention cases", impact=15,
            detail="Portfolio free of HIGH-scored cases."))
    if 0 < avg_days < 30:
        positives.append(Contributor(
            key="fast_closeout", label=f"Avg days-open {avg_days}", impact=6,
            detail="Cases closing under 30 days on average."))
    if high > 0:
        negatives.append(Contributor(
            key="high_attention", label=f"{high} HIGH-attention case(s)",
            impact=-min(35, high * 10),
            detail="HIGH-scored cases in portfolio."))
    if capa_open > 10:
        negatives.append(Contributor(
            key="capa_backlog", label=f"{capa_open} open CAPA(s)",
            impact=-min(20, capa_open // 2),
            detail="Aggregate open CAPA backlog."))
    if avg_days > 60:
        negatives.append(Contributor(
            key="long_avg_open", label=f"Avg days-open {avg_days}",
            impact=-10, detail="Cases running > 60 days on average."))

    if total == 0:
        score = insufficient_data_score(
            "No cases in the portfolio window — insufficient data to score.")
    else:
        score = score_from_contributors(
            baseline=100, positives=positives, negatives=negatives,
            trend_percent=None,
            confidence="high" if total >= 5 else "medium",
            data_freshness="live",
            calculation_notes=(
                "Composite of HIGH-attention count, open CAPA backlog, "
                "and average days-open across the portfolio window."),
        )

    top_5 = sorted(rows, key=lambda x: -(x.get("attention_score") or 0))[:5]
    top_5_rows = [[
        {"href": _base_link(r["case_id"]),
         "text": f"#{(r.get('case_number','') or '')[:12] or r['case_id'][:8]}"},
        r.get("incident_type") or "",
        r.get("state") or "",
        f"{(r.get('attention_level') or 'low').upper()} · {r.get('attention_score')}",
        r.get("days_open") or 0,
        r.get("capa_open") or 0,
    ] for r in top_5]

    win_items = []
    if total > 0 and high == 0:
        win_items.append(f"Zero HIGH-attention cases across {total} portfolio case(s).")
    if 0 < avg_days < 30:
        win_items.append(f"Portfolio avg days-open {avg_days} (under 30 days).")

    attention_items = []
    if high > 0:
        attention_items.append(f"{high} HIGH-attention case(s) require this week's focus.")
    if capa_open > 10:
        attention_items.append(f"{capa_open} open CAPA(s) — approaching backlog threshold.")
    if avg_days > 60:
        attention_items.append(f"Portfolio avg days-open at {avg_days} — closeout velocity slipping.")

    return build_standard_layout(
        product_id="executive_operations_brief",
        subject="MASCI Executive Operations Brief",
        period_label="Weekly · Monday 14:00 UTC",
        executive_summary={
            "Total cases":         total,
            "Open":                open_,
            "HIGH attention":      high,
            "MEDIUM attention":    med,
            "LOW attention":       low,
            "Total open CAPAs":    capa_open,
            "Avg days open":       avg_days,
        },
        score=score.to_dict(),
        trend_direction={"arrow": "→", "tone": "flat", "current": open_,
                         "previous": None, "pct_change": None},
        top_wins=win_items,
        needs_immediate_attention=attention_items,
        top_5_items={
            "title": "Top 5 Priority Cases",
            "headers": ["Case", "Type", "State", "Attention", "Days open", "CAPA open"],
            "rows": top_5_rows,
        } if top_5_rows else None,
        core_metrics={
            "HIGH / MEDIUM / LOW":  f"{high} / {med} / {low}",
            "Open CAPAs":           capa_open,
            "Avg days open":        avg_days,
        },
        recommendations=(
            ([f"Executive review of {high} HIGH case(s)."] if high > 0 else []) +
            (["Clear CAPA backlog — assign owners this week."] if capa_open > 10 else [])
            or ["Portfolio steady — maintain cadence."]
        ),
        upcoming_risks=[],
        recent_changes=[],
        deep_links=[
            {"href": "/safety/cases", "text": "Safety Case Center"},
            {"href": "/admin/executive-dashboard", "text": "Executive Dashboard"},
        ],
        no_auto_decision_notice=(
            "This brief is an attention signal only. Domain owners "
            "(Safety · Operations · HR · Fleet · Transportation) own "
            "investigation and classification. The platform does not "
            "decide OSHA recordability, root cause, liability, fault, "
            "discipline, or insurance responsibility."
        ),
        audit_footer=(
            "Real portfolio aggregator over Track 19.38 data. "
            "Track 19.42 retrofit into standard 14-section layout + Score."
        ),
    )


register_product(Product(
    product_id="executive_operations_brief",
    display_name="Executive Operations Brief",
    summary="Company-wide operational rollup for the executive team.",
    permission_role="admin_only",
    template_key="executive_v1",
    schedule_freq="weekly",
    schedule_iso_day=1,
    schedule_hour_utc=14,
    status=ProductStatus.IMPLEMENTED,
    aggregator=_agg_executive_ops,
    tags=["executive", "weekly", "portfolio"],
))


# ---------------------------------------------------------------------------
# 3 · Purchase Order Weekly Digest (IMPLEMENTED — Track 19.41 consolidation)
# ---------------------------------------------------------------------------
# Wraps the existing standalone `po_digest.send_po_digest_once(...)` in
# dry-run mode to produce section data. The legacy Monday-morning cron
# in server.py continues to fire unchanged (zero drift). This aggregator
# only exposes the same data through the Unified Operational Intelligence
# engine's preview + dispatch endpoints so admins can view/dry-run the
# same content under the standard product layout + Score + trend.
async def _agg_po_digest(db, **kwargs) -> Dict[str, Any]:
    from po_digest import send_po_digest_once, build_digest_subject
    from .product_layout import build_standard_layout
    from .score_model import score_from_contributors, Contributor

    results = await send_po_digest_once(
        db, send_email_fn=None, portal_url="", dry_run=True,
    )
    pms = results.get("pm") or []
    hrs = results.get("hr") or []
    skipped = results.get("skipped") or []

    total_open = sum((r.get("total_open") or 0) for r in pms + hrs)
    total_pms = len(pms)
    total_hrs = len(hrs)
    pms_with_openpos = sum(1 for r in pms if (r.get("total_open") or 0) > 0)

    # Top-attention PMs — most open POs.
    top_rows = sorted(
        [r for r in pms if (r.get("total_open") or 0) > 0],
        key=lambda r: -(r.get("total_open") or 0),
    )[:5]

    negatives = []
    if total_open > 50:
        negatives.append(Contributor(
            key="high_open_po_volume",
            label=f"{total_open} open POs across portfolio",
            impact=-max(0, min(40, total_open // 5)),
            detail="Aggregate open PO count exceeds 50.",
        ))
    if pms_with_openpos > (total_pms // 2 or 1):
        negatives.append(Contributor(
            key="wide_pm_impact",
            label=f"{pms_with_openpos}/{total_pms} PMs have open POs",
            impact=-8,
            detail="More than half of PMs carry open PO load.",
        ))

    positives = []
    if total_open == 0 and (total_pms + total_hrs) > 0:
        positives.append(Contributor(
            key="clean_slate", label="No open POs across scope",
            impact=15, detail="Clean-slate week."))

    score = score_from_contributors(
        baseline=100,
        positives=positives,
        negatives=negatives,
        trend_percent=None,   # first-run rollout — history required for trend
        confidence="medium" if (total_pms + total_hrs) > 0 else "insufficient_data",
        data_freshness="live" if (total_pms + total_hrs) > 0 else "insufficient_data",
        calculation_notes=(
            "PO Digest score derived from open PO volume across PM + HR "
            "recipient scopes. Trend engaged from Track 19.42 onward once "
            "history rows accumulate."
        ),
    )

    return build_standard_layout(
        product_id="po_weekly_digest",
        subject=build_digest_subject(),
        period_label="Weekly · Monday 14:00 UTC",
        executive_summary={
            "Total open POs (portfolio)": total_open,
            "PMs with open POs":          f"{pms_with_openpos}/{total_pms}",
            "HR recipients":              total_hrs,
            "PMs skipped (empty scope)":  len(skipped),
        },
        score=score.to_dict(),
        trend_direction={"arrow": score.trend_direction,
                         "tone": {"▲": "up", "▼": "down", "→": "flat"}.get(score.trend_direction, "flat"),
                         "current": total_open, "previous": None, "pct_change": None},
        top_wins=(["Clean slate — no open POs this week."]
                  if total_open == 0 else []),
        needs_immediate_attention=[
            f"{r.get('name') or r.get('email')} — {r.get('total_open')} open POs"
            for r in top_rows if (r.get("total_open") or 0) >= 5
        ],
        top_5_items={
            "title": "Top 5 PMs · Open PO Count",
            "headers": ["PM", "Email", "Scoped Jobs", "Open POs"],
            "rows": [[
                r.get("name") or "",
                r.get("email") or "",
                r.get("scoped_jobs") or 0,
                r.get("total_open") or 0,
            ] for r in top_rows],
        } if top_rows else None,
        core_metrics={
            "Active PM recipients":  total_pms,
            "Active HR recipients":  total_hrs,
            "Total open POs":        total_open,
            "Skipped (empty scope)": len(skipped),
        },
        recommendations=[
            "Review PMs with >5 open POs first · unblock approvals.",
            "Confirm PO recipient list matches current PM roster before Monday.",
        ] if total_open > 0 else ["No action required."],
        upcoming_risks=[],
        recent_changes=[],
        deep_links=[
            {"href": "/po-requests", "text": "Open PO Requests Center"},
            {"href": "/admin/po-digest/preview", "text": "Legacy PO Digest Preview"},
        ],
        no_auto_decision_notice=(
            "Attention signal only. PMs and HR own approval, receipt, and "
            "clarification decisions. The platform does not decide vendor "
            "selection, approval, or overdue liability."
        ),
        audit_footer=(
            "Consolidated under Unified Operational Intelligence Engine · Track 19.41. "
            "Legacy Monday cron continues unchanged for live send."
        ),
    )


register_product(Product(
    product_id="po_weekly_digest",
    display_name="Weekly Purchase Order Digest",
    summary="PMs + HR weekly rollup of open, pending, and overdue POs.",
    permission_role="admin_only",
    template_key="executive_v1",
    schedule_freq="weekly",
    schedule_iso_day=1,
    schedule_hour_utc=14,
    status=ProductStatus.IMPLEMENTED,
    aggregator=_agg_po_digest,
    tags=["procurement", "weekly", "po", "pm"],
))


# ---------------------------------------------------------------------------
# 4 · Transportation Intelligence Digest (IMPLEMENTED — Track 19.42)
# ---------------------------------------------------------------------------
# Real aggregator honouring the Track 19.41 readiness spec. Queries the
# transportation/fleet collections that actually exist today; anything
# missing surfaces as insufficient-data (never fabricated).
async def _agg_transportation_intelligence(db, **kwargs) -> Dict[str, Any]:
    from datetime import datetime, timedelta, timezone
    from .product_layout import build_standard_layout
    from .score_model import (
        score_from_contributors, Contributor, insufficient_data_score,
    )
    from .engine import compute_trend

    now = datetime.now(timezone.utc)
    week_ago = (now - timedelta(days=7)).isoformat()

    # Defensive counters — every source is treated as optional; empty
    # collections are handled honestly, not falsified.
    async def _count(name, q=None):
        try:
            return int(await db[name].count_documents(q or {}))
        except Exception:  # noqa: BLE001
            return 0

    # DVIR (per Track 19.12)
    dvirs_7d       = await _count("dvir", {"submitted_at": {"$gte": week_ago}})
    dvirs_open_def = await _count("dvir", {"has_open_defects": True})
    dvirs_total    = await _count("dvir", {})

    # Driver qualifications (per Track 19.00 audit)
    drivers_active = await _count("driver_qualifications",
                                  {"status": {"$in": ["active", "current"]}})
    drivers_expiring = await _count("driver_qualifications",
                                    {"expires_at": {"$lte": (now + timedelta(days=30)).isoformat(),
                                                    "$gte": now.isoformat()}})
    drivers_expired = await _count("driver_qualifications",
                                   {"expires_at": {"$lt": now.isoformat()}})

    # Fleet / equipment OOS
    equipment_oos  = await _count("equipment_units",
                                  {"status": {"$in": ["OOS", "Down", "Out of Service"]}})
    equipment_total = await _count("equipment_units", {})

    # Vehicle assignments
    vehicles_assigned   = await _count("vehicle_assignments",
                                       {"active": True})
    vehicles_unassigned = max(0, equipment_total - vehicles_assigned)

    # Vehicle incidents this week
    vehicle_accidents = await _count(
        "incident_cases",
        {"incident_type": "vehicle_accident",
         "submitted_at": {"$gte": week_ago}})

    # Transportation-adjacent transaction volume signals
    transport_action_items_open = await _count(
        "transport_action_items", {"status": {"$in": ["open", "in_progress"]}})

    # Determine confidence and freshness honestly
    has_any_transport_data = any([
        dvirs_total, drivers_active, equipment_total,
        vehicles_assigned, transport_action_items_open,
    ])
    if not has_any_transport_data:
        score = insufficient_data_score(
            "No transportation collections populated in this environment — "
            "Score cannot be computed."
        )
        confidence = "insufficient_data"
        data_freshness = "insufficient_data"
    else:
        positives, negatives = [], []
        # POSITIVE contributors
        if dvirs_7d > 0 and dvirs_open_def == 0:
            positives.append(Contributor(
                key="dvir_no_defects",
                label=f"{dvirs_7d} DVIR(s) submitted · 0 open defects",
                impact=10, detail="Clean DVIR pass in the last 7 days."))
        if drivers_active > 0 and drivers_expired == 0:
            positives.append(Contributor(
                key="qualifications_current",
                label=f"All {drivers_active} active driver qualification(s) current",
                impact=12, detail="No expired driver qualifications on record."))
        if equipment_total > 0 and equipment_oos == 0:
            positives.append(Contributor(
                key="full_availability",
                label=f"Full fleet availability · {equipment_total} unit(s)",
                impact=10, detail="No units out-of-service."))
        if vehicle_accidents == 0:
            positives.append(Contributor(
                key="no_accidents", label="Zero vehicle incidents (last 7d)",
                impact=8, detail="No vehicle accidents in the period."))
        # NEGATIVE contributors
        if drivers_expired > 0:
            negatives.append(Contributor(
                key="expired_qualifications",
                label=f"{drivers_expired} expired driver qualification(s)",
                impact=-min(30, drivers_expired * 8),
                detail="Driver qualifications past expiry."))
        if drivers_expiring > 0:
            negatives.append(Contributor(
                key="expiring_soon",
                label=f"{drivers_expiring} qualification(s) expiring in 30 days",
                impact=-min(15, drivers_expiring * 3),
                detail="Renewal window approaching."))
        if dvirs_open_def > 0:
            negatives.append(Contributor(
                key="open_dvir_defects",
                label=f"{dvirs_open_def} DVIR(s) with open defect(s)",
                impact=-min(20, dvirs_open_def * 4),
                detail="Open defects raised via DVIR."))
        if equipment_oos > 0:
            negatives.append(Contributor(
                key="oos_units", label=f"{equipment_oos} unit(s) out-of-service",
                impact=-min(25, equipment_oos * 3),
                detail="OOS aging weight applied."))
        if vehicle_accidents > 0:
            negatives.append(Contributor(
                key="vehicle_incidents",
                label=f"{vehicle_accidents} vehicle incident(s) this period",
                impact=-min(35, vehicle_accidents * 12),
                detail="Vehicle incidents raised via incident intake."))
        if transport_action_items_open > 5:
            negatives.append(Contributor(
                key="transport_backlog",
                label=f"{transport_action_items_open} open transportation action item(s)",
                impact=-min(15, transport_action_items_open // 2),
                detail="Aggregate transportation action backlog."))

        confidence = "high" if (dvirs_total > 10 and drivers_active > 5) else "medium"
        data_freshness = "live"
        score = score_from_contributors(
            baseline=100,
            positives=positives, negatives=negatives,
            trend_percent=None,  # history rows accumulate from Track 19.42 onward
            confidence=confidence,
            data_freshness=data_freshness,
            calculation_notes=(
                "Composite of DVIR completion + open-defect count · driver "
                "qualification currency · fleet OOS state · vehicle-incident "
                "volume · transportation action backlog. Trend engages once "
                "engine history rows accumulate."
            ),
        )

    # Trend direction — use expired-qualifications count as the safety-critical headline metric
    trend_dir_raw = compute_trend(drivers_expired, 0)  # no previous history yet
    trend_dir = {"arrow": "→", "tone": "flat",
                 "current": drivers_expired, "previous": None, "pct_change": None}

    # Win + attention items — derived from real signals only
    wins = []
    if equipment_total > 0 and equipment_oos == 0:
        wins.append(f"Zero OOS · fleet availability full ({equipment_total} unit(s)).")
    if vehicle_accidents == 0 and (drivers_active > 0 or equipment_total > 0):
        wins.append("No vehicle incidents recorded this week.")
    if drivers_active > 0 and drivers_expired == 0:
        wins.append(f"All {drivers_active} active driver qualification(s) current.")

    attention = []
    if drivers_expired > 0:
        attention.append(f"{drivers_expired} driver qualification(s) EXPIRED — remove from active roster.")
    if drivers_expiring > 0:
        attention.append(f"{drivers_expiring} qualification(s) expiring in the next 30 days.")
    if dvirs_open_def > 0:
        attention.append(f"{dvirs_open_def} DVIR(s) carrying open defects.")
    if equipment_oos > 0:
        attention.append(f"{equipment_oos} unit(s) currently out-of-service.")
    if vehicle_accidents > 0:
        attention.append(f"{vehicle_accidents} vehicle incident(s) this period — review each case.")

    # Top-5 fleet OOS units (if collection populated)
    top_5_rows = []
    if equipment_oos > 0:
        try:
            cursor = db["equipment_units"].find(
                {"status": {"$in": ["OOS", "Down", "Out of Service"]}},
                {"_id": 0, "unit_number": 1, "make": 1, "model": 1,
                 "status": 1, "oos_since": 1},
            ).limit(5)
            async for u in cursor:
                top_5_rows.append([
                    {"href": f"/fleet/units/{u.get('unit_number','')}",
                     "text": u.get("unit_number") or "—"},
                    u.get("make") or "",
                    u.get("model") or "",
                    u.get("status") or "OOS",
                    u.get("oos_since") or "—",
                ])
        except Exception:  # noqa: BLE001
            pass

    return build_standard_layout(
        product_id="transportation_intelligence",
        subject="MASCI Transportation Intelligence Digest",
        period_label="Weekly · Monday 13:00 UTC",
        executive_summary={
            "Active drivers":              drivers_active,
            "Drivers expired":             drivers_expired,
            "Drivers expiring (30d)":      drivers_expiring,
            "DVIRs submitted (7d)":        dvirs_7d,
            "DVIRs w/ open defects":       dvirs_open_def,
            "Units out-of-service":        equipment_oos,
            "Vehicle incidents (7d)":      vehicle_accidents,
        },
        score=score.to_dict(),
        trend_direction=trend_dir,
        top_wins=wins,
        needs_immediate_attention=attention,
        top_5_items={
            "title": "Top 5 · Units Out of Service",
            "headers": ["Unit", "Make", "Model", "Status", "OOS since"],
            "rows": top_5_rows,
        } if top_5_rows else None,
        core_metrics={
            "Fleet size":                     equipment_total,
            "Vehicles assigned":              vehicles_assigned,
            "Vehicles unassigned":            vehicles_unassigned,
            "DVIR total":                     dvirs_total,
            "Transportation action backlog":  transport_action_items_open,
        },
        recommendations=(
            ([f"Renew {drivers_expired} EXPIRED driver qualification(s) immediately."] if drivers_expired else []) +
            ([f"Address {dvirs_open_def} DVIR open defect(s) this week."] if dvirs_open_def else []) +
            ([f"Return {equipment_oos} OOS unit(s) to service."] if equipment_oos else []) +
            ([f"Review {vehicle_accidents} vehicle incident case(s)."] if vehicle_accidents else [])
            or ["Transportation operations steady — maintain cadence."]
        ),
        upcoming_risks=(
            [f"{drivers_expiring} driver qualification(s) expire in the next 30 days."]
            if drivers_expiring else []
        ),
        recent_changes=[
            f"DVIRs submitted last 7d: {dvirs_7d}",
        ],
        deep_links=[
            {"href": "/admin/transportation/command-queue", "text": "Transportation Command Queue"},
            {"href": "/fleet", "text": "Fleet Center"},
            {"href": "/admin/transportation/inspections", "text": "Inspection Center"},
            {"href": "/hr/training-records", "text": "Driver Qualification Records"},
            {"href": "/safety/cases?type=vehicle_accident", "text": "Vehicle Incidents"},
        ],
        no_auto_decision_notice=(
            "Attention signal only. Transportation · Fleet · Safety · HR own "
            "the investigation, classification, and disposition of every "
            "signal below. The platform does NOT decide DOT recordability, "
            "fault, preventability, driver discipline, or insurance liability."
        ),
        audit_footer=(
            "Track 19.42 · Transportation Intelligence Digest · real "
            "aggregator over DVIR + driver qualifications + fleet + incidents. "
            "Insufficient-data path preserved when collections are empty."
        ),
    )


register_product(Product(
    product_id="transportation_intelligence",
    display_name="Transportation Intelligence Digest",
    summary="Fleet · drivers · DVIR · vehicle incidents · assignments · backlog.",
    permission_role="safety_or_admin",
    template_key="executive_v1",
    schedule_freq="weekly", schedule_iso_day=1, schedule_hour_utc=13,
    status=ProductStatus.IMPLEMENTED,
    aggregator=_agg_transportation_intelligence,
    tags=["transportation", "fleet", "safety", "weekly"],
))


# ---------------------------------------------------------------------------
# 5 · Fleet Intelligence Digest (IMPLEMENTED — Track 19.43)
# ---------------------------------------------------------------------------
async def _agg_fleet_intelligence(db, **kwargs) -> Dict[str, Any]:
    from datetime import datetime, timedelta, timezone
    from .product_layout import build_standard_layout
    from .score_model import (
        score_from_contributors, Contributor, insufficient_data_score,
    )

    now = datetime.now(timezone.utc)
    week_ago = (now - timedelta(days=7)).isoformat()

    async def _c(name, q=None):
        try:
            return int(await db[name].count_documents(q or {}))
        except Exception:  # noqa: BLE001
            return 0

    total       = await _c("equipment_master", {})
    if total == 0:
        # fall back to equipment_units when master isn't populated
        total = await _c("equipment_units", {})
    oos         = await _c("equipment_units", {"status": {"$in": ["OOS", "Down", "Out of Service"]}})
    safety_hold = await _c("asset_holds", {"hold_type": "safety", "status": "active"})
    maint_hold  = await _c("asset_holds", {"hold_type": {"$in": ["maintenance", "repair"]}, "status": "active"})
    open_defects = await _c("fleet_defects", {"status": {"$in": ["open", "in_progress"]}})
    critical_defects = await _c("fleet_defects",
                                 {"severity": "critical",
                                  "status": {"$in": ["open", "in_progress"]}})
    inspections_7d = await _c("equipment_inspections",
                              {"submitted_at": {"$gte": week_ago}})
    overdue_insp   = await _c("equipment_inspections",
                              {"next_due_at": {"$lt": now.isoformat()},
                               "status": {"$in": ["due", "scheduled"]}})
    transfers_7d   = await _c("equipment_transfers",
                              {"created_at": {"$gte": week_ago}})
    equip_incidents = await _c("incident_cases",
                               {"incident_type": "equipment_damage",
                                "submitted_at": {"$gte": week_ago}})

    has_any = any([total, oos, safety_hold, maint_hold, open_defects,
                   inspections_7d, transfers_7d])
    if not has_any:
        score = insufficient_data_score(
            "No fleet/equipment collections populated in this environment."
        )
    else:
        positives, negatives = [], []
        if total > 0 and oos == 0:
            positives.append(Contributor(
                key="full_availability",
                label=f"All {total} unit(s) available",
                impact=12, detail="No OOS units."))
        if inspections_7d > 0 and open_defects == 0:
            positives.append(Contributor(
                key="clean_inspections",
                label=f"{inspections_7d} inspection(s) · 0 open defects",
                impact=8, detail="Clean inspection sweep."))
        if safety_hold == 0 and maint_hold == 0 and total > 0:
            positives.append(Contributor(
                key="no_holds", label="No active holds on any unit",
                impact=6, detail="No maintenance / safety holds."))
        if equip_incidents == 0:
            positives.append(Contributor(
                key="no_equip_incidents",
                label="Zero equipment-damage incidents this week",
                impact=8, detail="Clean equipment-safety period."))

        if critical_defects > 0:
            negatives.append(Contributor(
                key="critical_defects",
                label=f"{critical_defects} CRITICAL defect(s) open",
                impact=-min(35, critical_defects * 12),
                detail="Highest-severity defects blocking utilisation."))
        elif open_defects > 5:
            negatives.append(Contributor(
                key="defect_backlog",
                label=f"{open_defects} open defect(s)",
                impact=-min(20, open_defects // 2),
                detail="Open defect backlog above threshold."))
        if oos > 0:
            negatives.append(Contributor(
                key="oos_units", label=f"{oos} unit(s) out-of-service",
                impact=-min(25, oos * 3),
                detail="Availability drag."))
        if safety_hold > 0:
            negatives.append(Contributor(
                key="safety_holds",
                label=f"{safety_hold} unit(s) on safety hold",
                impact=-min(25, safety_hold * 6),
                detail="Safety hold — investigate immediately."))
        if maint_hold > 0:
            negatives.append(Contributor(
                key="maint_holds",
                label=f"{maint_hold} unit(s) on maintenance/repair hold",
                impact=-min(15, maint_hold * 2),
                detail="Availability drag."))
        if overdue_insp > 0:
            negatives.append(Contributor(
                key="overdue_inspections",
                label=f"{overdue_insp} overdue inspection(s)",
                impact=-min(15, overdue_insp * 3),
                detail="Compliance and utilisation exposure."))
        if equip_incidents > 0:
            negatives.append(Contributor(
                key="equipment_incidents",
                label=f"{equip_incidents} equipment incident(s) this period",
                impact=-min(25, equip_incidents * 10),
                detail="Equipment-damage incidents raised via intake."))

        score = score_from_contributors(
            baseline=100, positives=positives, negatives=negatives,
            trend_percent=None,
            confidence="high" if total >= 10 else "medium",
            data_freshness="live",
            calculation_notes=(
                "Fleet score composed from OOS count · defect severity · "
                "active holds · overdue inspections · equipment incidents. "
                "Trend engages once history rows accumulate."
            ),
        )

    # Top-5 units with active safety holds (or OOS if no holds populated)
    top_5_rows = []
    try:
        cursor = db["asset_holds"].find(
            {"hold_type": "safety", "status": "active"},
            {"_id": 0, "unit_number": 1, "reason": 1, "opened_at": 1,
             "opened_by": 1, "asset_id": 1},
        ).limit(5)
        async for h in cursor:
            unit = h.get("unit_number") or (h.get("asset_id") or "")[:10]
            top_5_rows.append([
                {"href": f"/fleet/units/{unit}", "text": unit or "—"},
                h.get("reason") or "",
                h.get("opened_at") or "",
                h.get("opened_by") or "",
            ])
    except Exception:  # noqa: BLE001
        pass
    if not top_5_rows and oos > 0:
        # fallback: top 5 OOS units
        try:
            cursor = db["equipment_units"].find(
                {"status": {"$in": ["OOS", "Down", "Out of Service"]}},
                {"_id": 0, "unit_number": 1, "status": 1, "oos_since": 1,
                 "make": 1, "model": 1},
            ).limit(5)
            async for u in cursor:
                top_5_rows.append([
                    {"href": f"/fleet/units/{u.get('unit_number','')}",
                     "text": u.get("unit_number") or "—"},
                    u.get("status") or "OOS",
                    u.get("oos_since") or "",
                    f"{u.get('make','')} {u.get('model','')}".strip(),
                ])
        except Exception:  # noqa: BLE001
            pass

    wins = []
    if total > 0 and oos == 0:
        wins.append(f"Full fleet availability · {total} unit(s).")
    if inspections_7d > 0 and open_defects == 0:
        wins.append(f"{inspections_7d} inspection(s) completed clean this week.")
    if equip_incidents == 0 and total > 0:
        wins.append("No equipment-damage incidents this period.")

    attention = []
    if critical_defects > 0:
        attention.append(f"{critical_defects} CRITICAL defect(s) — address immediately.")
    if safety_hold > 0:
        attention.append(f"{safety_hold} unit(s) on safety hold.")
    if oos > 0:
        attention.append(f"{oos} unit(s) OOS — return to service.")
    if overdue_insp > 0:
        attention.append(f"{overdue_insp} inspection(s) overdue.")
    if equip_incidents > 0:
        attention.append(f"{equip_incidents} equipment incident(s) this period.")

    return build_standard_layout(
        product_id="fleet_intelligence",
        subject="MASCI Fleet Intelligence Digest",
        period_label="Weekly · Monday 13:00 UTC",
        executive_summary={
            "Total units":              total,
            "OOS":                      oos,
            "On safety hold":           safety_hold,
            "On maint/repair hold":     maint_hold,
            "Open defects":             open_defects,
            "Critical defects":         critical_defects,
            "Overdue inspections":      overdue_insp,
        },
        score=score.to_dict(),
        trend_direction={"arrow": "→", "tone": "flat",
                         "current": oos, "previous": None, "pct_change": None},
        top_wins=wins,
        needs_immediate_attention=attention,
        top_5_items=({
            "title": "Top 5 · Fleet Attention",
            "headers": ["Unit", "Reason / Status", "Since", "Owner / Details"],
            "rows": top_5_rows,
        } if top_5_rows else None),
        core_metrics={
            "Inspections last 7d":  inspections_7d,
            "Transfers last 7d":    transfers_7d,
            "Equipment incidents":  equip_incidents,
        },
        recommendations=(
            ([f"Resolve {critical_defects} CRITICAL defect(s) this week."] if critical_defects else []) +
            ([f"Return {oos} OOS unit(s) to service."] if oos else []) +
            ([f"Close {overdue_insp} overdue inspection(s)."] if overdue_insp else []) +
            ([f"Investigate {safety_hold} safety hold(s)."] if safety_hold else [])
            or ["Fleet operations steady — maintain cadence."]
        ),
        upcoming_risks=[],
        recent_changes=[
            f"Inspections submitted last 7d: {inspections_7d}",
            f"Asset transfers last 7d: {transfers_7d}",
        ],
        deep_links=[
            {"href": "/fleet", "text": "Fleet Center"},
            {"href": "/fleet/holds", "text": "Active Holds"},
            {"href": "/fleet/defects", "text": "Defect Board"},
            {"href": "/fleet/inspections", "text": "Inspection Center"},
            {"href": "/safety/cases?type=equipment_damage", "text": "Equipment Incidents"},
        ],
        no_auto_decision_notice=(
            "Attention signal only. Fleet · Shop · Safety own investigation "
            "and classification. The platform does NOT determine fault, "
            "root cause, mechanic responsibility, insurance liability, or "
            "return-to-service authorisation."
        ),
        audit_footer=(
            "Track 19.43 · Fleet Intelligence Digest · aggregator over "
            "equipment_master / equipment_units / asset_holds / fleet_defects / "
            "equipment_inspections / incident_cases."
        ),
    )


register_product(Product(
    product_id="fleet_intelligence",
    display_name="Fleet Intelligence Digest",
    summary="Equipment · inspections · holds · defects · downtime signals.",
    permission_role="safety_or_admin",
    template_key="executive_v1",
    schedule_freq="weekly", schedule_iso_day=1, schedule_hour_utc=13,
    status=ProductStatus.IMPLEMENTED,
    aggregator=_agg_fleet_intelligence,
    tags=["fleet", "equipment", "weekly"],
))


# ---------------------------------------------------------------------------
# 6 · HR Intelligence Digest (IMPLEMENTED — Track 19.43)
# ---------------------------------------------------------------------------
async def _agg_hr_intelligence(db, **kwargs) -> Dict[str, Any]:
    from datetime import datetime, timedelta, timezone
    from .product_layout import build_standard_layout
    from .score_model import (
        score_from_contributors, Contributor, insufficient_data_score,
    )

    now = datetime.now(timezone.utc)
    week_ago = (now - timedelta(days=7)).isoformat()
    plus_30d = (now + timedelta(days=30)).isoformat()

    async def _c(name, q=None):
        try:
            return int(await db[name].count_documents(q or {}))
        except Exception:  # noqa: BLE001
            return 0

    total_emp = await _c("employees", {"active": True})
    if total_emp == 0:
        total_emp = await _c("employee_records", {"active": True})
    new_hires_7d = await _c("employee_lifecycle_events",
                             {"event_type": "hired",
                              "occurred_at": {"$gte": week_ago}})
    terminations_7d = await _c("employee_lifecycle_events",
                                {"event_type": {"$in": ["terminated", "resigned"]},
                                 "occurred_at": {"$gte": week_ago}})

    # Training / qualification expiries — reuse driver_qualifications
    # collection because training records live there for driver + safety
    # certs today (per Track 19.00 audit).
    quals_expired = await _c("driver_qualifications",
                             {"expires_at": {"$lt": now.isoformat()}})
    quals_expiring_30d = await _c("driver_qualifications",
                                  {"expires_at": {"$lte": plus_30d,
                                                  "$gte": now.isoformat()}})

    trainings_recent = await _c("training_hits",
                                {"created_at": {"$gte": week_ago}})

    # Orientation / onboarding hits
    orientation_active = await _c("employee_lifecycle_events",
                                  {"event_type": "orientation_started",
                                   "status": "in_progress"})

    has_any = any([total_emp, new_hires_7d, terminations_7d, quals_expired,
                   quals_expiring_30d, trainings_recent, orientation_active])
    if not has_any:
        score = insufficient_data_score(
            "No HR collections populated in this environment."
        )
    else:
        positives, negatives = [], []
        if total_emp > 0 and quals_expired == 0:
            positives.append(Contributor(
                key="all_current",
                label=f"All {total_emp} active employee(s) currently qualified",
                impact=15, detail="No expired qualifications on record."))
        if trainings_recent > 0:
            positives.append(Contributor(
                key="training_activity",
                label=f"{trainings_recent} training activit(y|ies) this week",
                impact=6, detail="Active training engagement."))
        if new_hires_7d > 0 and terminations_7d == 0:
            positives.append(Contributor(
                key="net_growth",
                label=f"+{new_hires_7d} new hire(s) · 0 exits this week",
                impact=5, detail="Net workforce growth."))
        if quals_expired > 0:
            negatives.append(Contributor(
                key="expired_quals",
                label=f"{quals_expired} employee qualification(s) EXPIRED",
                impact=-min(35, quals_expired * 8),
                detail="Safety-critical — remove from covered work assignments."))
        if quals_expiring_30d > 0:
            negatives.append(Contributor(
                key="expiring_30d",
                label=f"{quals_expiring_30d} qualification(s) expiring in 30d",
                impact=-min(15, quals_expiring_30d * 2),
                detail="Renewal window approaching."))
        if terminations_7d > (new_hires_7d + 1):
            negatives.append(Contributor(
                key="net_churn",
                label=f"{terminations_7d} exit(s) vs {new_hires_7d} new hire(s)",
                impact=-8, detail="Net workforce contraction."))

        score = score_from_contributors(
            baseline=100, positives=positives, negatives=negatives,
            trend_percent=None,
            confidence="high" if total_emp >= 20 else "medium",
            data_freshness="live",
            calculation_notes=(
                "HR score composed from qualification currency · renewal "
                "backlog · net workforce movement · training engagement. "
                "Trend engages once history rows accumulate."
            ),
        )

    # Top-5 employees with expired qualifications
    top_5_rows = []
    if quals_expired > 0:
        try:
            cursor = db["driver_qualifications"].find(
                {"expires_at": {"$lt": now.isoformat()}},
                {"_id": 0, "employee_name": 1, "employee_id": 1,
                 "cert_type": 1, "expires_at": 1},
            ).limit(5)
            async for r in cursor:
                emp = r.get("employee_name") or r.get("employee_id") or "—"
                top_5_rows.append([
                    {"href": f"/hr/employees/{r.get('employee_id','')}",
                     "text": emp},
                    r.get("cert_type") or "—",
                    r.get("expires_at") or "—",
                ])
        except Exception:  # noqa: BLE001
            pass

    wins = []
    if total_emp > 0 and quals_expired == 0:
        wins.append(f"All {total_emp} active employee qualification(s) current.")
    if trainings_recent > 0:
        wins.append(f"{trainings_recent} training activit(y|ies) logged this week.")
    if new_hires_7d > 0 and terminations_7d == 0:
        wins.append(f"+{new_hires_7d} new hire(s) · zero exits this week.")

    attention = []
    if quals_expired > 0:
        attention.append(f"{quals_expired} employee qualification(s) EXPIRED.")
    if quals_expiring_30d > 0:
        attention.append(f"{quals_expiring_30d} qualification(s) expiring in the next 30 days.")
    if orientation_active > 0:
        attention.append(f"{orientation_active} orientation(s) in progress.")

    return build_standard_layout(
        product_id="hr_intelligence",
        subject="MASCI HR Intelligence Digest",
        period_label="Weekly · Monday 13:00 UTC",
        executive_summary={
            "Active employees":      total_emp,
            "New hires (7d)":        new_hires_7d,
            "Exits (7d)":            terminations_7d,
            "Expired quals":         quals_expired,
            "Expiring (30d)":        quals_expiring_30d,
            "Orientations active":   orientation_active,
        },
        score=score.to_dict(),
        trend_direction={"arrow": "→", "tone": "flat",
                         "current": quals_expired, "previous": None,
                         "pct_change": None},
        top_wins=wins,
        needs_immediate_attention=attention,
        top_5_items=({
            "title": "Top 5 · Expired Qualifications",
            "headers": ["Employee", "Cert Type", "Expired on"],
            "rows": top_5_rows,
        } if top_5_rows else None),
        core_metrics={
            "Total active employees":     total_emp,
            "Training activities (7d)":   trainings_recent,
            "Orientations in progress":   orientation_active,
        },
        recommendations=(
            ([f"Renew {quals_expired} expired qualification(s) immediately."] if quals_expired else []) +
            ([f"Schedule renewal for {quals_expiring_30d} qualification(s) expiring in 30d."] if quals_expiring_30d else []) +
            ([f"Follow up on {orientation_active} in-progress orientation(s)."] if orientation_active else [])
            or ["HR operations steady — maintain cadence."]
        ),
        upcoming_risks=(
            [f"{quals_expiring_30d} qualification(s) expire in the next 30 days."]
            if quals_expiring_30d else []
        ),
        recent_changes=[
            f"New hires last 7d: {new_hires_7d}",
            f"Exits last 7d: {terminations_7d}",
            f"Training activities last 7d: {trainings_recent}",
        ],
        deep_links=[
            {"href": "/hr/employees", "text": "Employee Directory"},
            {"href": "/hr/training-records", "text": "Training Records"},
            {"href": "/hr/lifecycle", "text": "Lifecycle Events"},
            {"href": "/hr/orientation", "text": "Orientation Center"},
        ],
        no_auto_decision_notice=(
            "Attention signal only. HR · Safety own investigation, "
            "classification, and disposition. The platform does NOT "
            "determine termination cause, discipline, performance rating, "
            "eligibility for rehire, or legal liability."
        ),
        audit_footer=(
            "Track 19.43 · HR Intelligence Digest · aggregator over "
            "employees / employee_lifecycle_events / driver_qualifications / "
            "training_hits."
        ),
    )


register_product(Product(
    product_id="hr_intelligence",
    display_name="HR Intelligence Digest",
    summary="Employees · lifecycle · qualification currency · training · orientation.",
    permission_role="admin_only",
    template_key="executive_v1",
    schedule_freq="weekly", schedule_iso_day=1, schedule_hour_utc=13,
    status=ProductStatus.IMPLEMENTED,
    aggregator=_agg_hr_intelligence,
    tags=["hr", "training", "weekly"],
))


# ---------------------------------------------------------------------------
# 7 · Training Intelligence Digest (IMPLEMENTED — Track 19.44)
# ---------------------------------------------------------------------------
async def _agg_training_intelligence(db, **kwargs) -> Dict[str, Any]:
    from datetime import datetime, timedelta, timezone
    from .product_layout import build_standard_layout
    from .score_model import (
        score_from_contributors, Contributor, insufficient_data_score,
    )

    now = datetime.now(timezone.utc)
    week_ago = (now - timedelta(days=7)).isoformat()
    plus_30d = (now + timedelta(days=30)).isoformat()
    plus_60d = (now + timedelta(days=60)).isoformat()

    async def _c(name, q=None):
        try:
            return int(await db[name].count_documents(q or {}))
        except Exception:  # noqa: BLE001
            return 0

    # Employee scope
    active_emp = await _c("employees", {"active": True})
    if active_emp == 0:
        active_emp = await _c("employee_records", {"active": True})

    # Training completion signals — use safety_training_records + training_track_records
    completed_7d = await _c("safety_training_records", {"completed_at": {"$gte": week_ago}})
    if completed_7d == 0:
        completed_7d = await _c("training_track_records", {"created_at": {"$gte": week_ago}})
    completed_total = await _c("safety_training_records", {})

    # Expiring / expired across driver_qualifications (canonical cert store)
    expired = await _c("driver_qualifications", {"expires_at": {"$lt": now.isoformat()}})
    expiring_30d = await _c("driver_qualifications",
                            {"expires_at": {"$lte": plus_30d, "$gte": now.isoformat()}})
    expiring_60d = await _c("driver_qualifications",
                            {"expires_at": {"$lte": plus_60d, "$gte": now.isoformat()}})

    # Meeting attendance
    meetings_7d = await _c("safety_meetings", {"held_at": {"$gte": week_ago}})
    if meetings_7d == 0:
        meetings_7d = await _c("meetings", {"held_at": {"$gte": week_ago}})

    # Missing / pending signals
    missing_records = await _c("training_track_records",
                               {"status": {"$in": ["missing", "pending"]}})
    pending_approval = await _c("training_track_records",
                                {"status": "pending_approval"})

    has_any = any([active_emp, completed_total, expired, expiring_30d,
                    meetings_7d, missing_records])
    if not has_any:
        score = insufficient_data_score(
            "No training collections populated in this environment.")
    else:
        positives, negatives = [], []
        if completed_7d > 0:
            positives.append(Contributor(
                key="completion_activity",
                label=f"{completed_7d} training completion(s) this week",
                impact=8, detail="Active training engagement."))
        if active_emp > 0 and expired == 0:
            positives.append(Contributor(
                key="no_expired",
                label=f"All {active_emp} active employee(s) currently qualified",
                impact=15, detail="No expired training/certifications."))
        if meetings_7d > 0:
            positives.append(Contributor(
                key="meeting_attendance",
                label=f"{meetings_7d} safety meeting(s) held this week",
                impact=6, detail="Ongoing safety touchpoints."))
        if expired > 0:
            negatives.append(Contributor(
                key="expired_certs",
                label=f"{expired} expired certification(s)",
                impact=-min(35, expired * 8),
                detail="Safety-critical — remove employees from covered work."))
        if expiring_30d > 0:
            negatives.append(Contributor(
                key="expiring_30d",
                label=f"{expiring_30d} certification(s) expiring in 30 days",
                impact=-min(20, expiring_30d * 3),
                detail="Immediate renewal window."))
        elif expiring_60d > 0:
            negatives.append(Contributor(
                key="expiring_60d",
                label=f"{expiring_60d} certification(s) expiring in 60 days",
                impact=-min(10, expiring_60d * 2),
                detail="Renewal window approaching."))
        if missing_records > 0:
            negatives.append(Contributor(
                key="missing_records",
                label=f"{missing_records} missing/pending training record(s)",
                impact=-min(15, missing_records * 3),
                detail="Records not attached · attention required."))
        if pending_approval > 5:
            negatives.append(Contributor(
                key="approval_backlog",
                label=f"{pending_approval} record(s) pending approval",
                impact=-min(12, pending_approval // 2),
                detail="Approval backlog exceeds threshold."))

        score = score_from_contributors(
            baseline=100, positives=positives, negatives=negatives,
            trend_percent=None,
            confidence="high" if (active_emp >= 20 and completed_total >= 10) else "medium",
            data_freshness="live",
            calculation_notes=(
                "Training score composed from completion activity · "
                "certification currency · meeting attendance · record "
                "completeness · approval backlog. Trend engages once "
                "history rows accumulate."
            ),
        )

    # Top-5 expired certifications
    top_5_rows = []
    if expired > 0:
        try:
            cursor = db["driver_qualifications"].find(
                {"expires_at": {"$lt": now.isoformat()}},
                {"_id": 0, "employee_name": 1, "employee_id": 1,
                 "cert_type": 1, "expires_at": 1},
            ).limit(5)
            async for r in cursor:
                emp = r.get("employee_name") or r.get("employee_id") or "—"
                top_5_rows.append([
                    {"href": f"/hr/employees/{r.get('employee_id','')}",
                     "text": emp},
                    r.get("cert_type") or "—",
                    r.get("expires_at") or "—",
                ])
        except Exception:  # noqa: BLE001
            pass

    wins = []
    if completed_7d > 0:
        wins.append(f"{completed_7d} training completion(s) this week.")
    if active_emp > 0 and expired == 0:
        wins.append(f"All {active_emp} active employees currently qualified.")
    if meetings_7d > 0:
        wins.append(f"{meetings_7d} safety meeting(s) held this week.")

    attention = []
    if expired > 0:
        attention.append(f"{expired} EXPIRED certification(s) — remove employees from covered work.")
    if expiring_30d > 0:
        attention.append(f"{expiring_30d} certification(s) expiring in the next 30 days.")
    if missing_records > 0:
        attention.append(f"{missing_records} missing / pending training record(s).")
    if pending_approval > 0:
        attention.append(f"{pending_approval} record(s) awaiting approval.")

    return build_standard_layout(
        product_id="training_intelligence",
        subject="MASCI Training Intelligence Digest",
        period_label="Weekly · Monday 13:00 UTC",
        executive_summary={
            "Active employees":       active_emp,
            "Completions (7d)":       completed_7d,
            "Total training records": completed_total,
            "Expired certs":          expired,
            "Expiring (30d)":         expiring_30d,
            "Missing records":        missing_records,
        },
        score=score.to_dict(),
        trend_direction={"arrow": "→", "tone": "flat",
                         "current": expired, "previous": None, "pct_change": None},
        top_wins=wins,
        needs_immediate_attention=attention,
        top_5_items=({
            "title": "Top 5 · Expired Certifications",
            "headers": ["Employee", "Cert Type", "Expired on"],
            "rows": top_5_rows,
        } if top_5_rows else None),
        core_metrics={
            "Meetings held (7d)":       meetings_7d,
            "Records pending approval": pending_approval,
            "Expiring (60d)":           expiring_60d,
        },
        recommendations=(
            ([f"Renew {expired} EXPIRED certification(s) immediately."] if expired else []) +
            ([f"Schedule renewal for {expiring_30d} cert(s) expiring in 30d."] if expiring_30d else []) +
            ([f"Chase {missing_records} missing training record(s)."] if missing_records else []) +
            ([f"Clear {pending_approval} record(s) pending approval."] if pending_approval else [])
            or ["Training operations steady — maintain cadence."]
        ),
        upcoming_risks=(
            [f"{expiring_30d} certification(s) expire in the next 30 days."] if expiring_30d else []
        ) + (
            [f"{expiring_60d} certification(s) expire in the next 60 days."]
            if expiring_60d and not expiring_30d else []
        ),
        recent_changes=[
            f"Completions last 7d: {completed_7d}",
            f"Meetings last 7d: {meetings_7d}",
        ],
        deep_links=[
            {"href": "/hr/training-records", "text": "Training Records"},
            {"href": "/hr/employees", "text": "Employee Directory"},
            {"href": "/meetings", "text": "Safety Meetings"},
            {"href": "/hr/historical-records/queue", "text": "Historical Import Queue"},
        ],
        no_auto_decision_notice=(
            "Attention signal only. HR · Safety own investigation and "
            "classification. The platform does NOT determine discipline, "
            "employment eligibility, OSHA recordability, or legal compliance "
            "beyond surfacing missing/expired records."
        ),
        audit_footer=(
            "Track 19.44 · Training Intelligence Digest · aggregator over "
            "employees / safety_training_records / training_track_records / "
            "driver_qualifications / safety_meetings."
        ),
    )


register_product(Product(
    product_id="training_intelligence",
    display_name="Training Intelligence Digest",
    summary="Training completion · expirations · meeting attendance · record gaps.",
    permission_role="admin_only",
    template_key="executive_v1",
    schedule_freq="weekly", schedule_iso_day=1, schedule_hour_utc=13,
    status=ProductStatus.IMPLEMENTED,
    aggregator=_agg_training_intelligence,
    tags=["training", "hr", "weekly"],
))


# ---------------------------------------------------------------------------
# 8 · Project Intelligence Digest (IMPLEMENTED — Track 19.44)
# ---------------------------------------------------------------------------
async def _agg_project_intelligence(db, **kwargs) -> Dict[str, Any]:
    from datetime import datetime, timedelta, timezone
    from .product_layout import build_standard_layout
    from .score_model import (
        score_from_contributors, Contributor, insufficient_data_score,
    )

    now = datetime.now(timezone.utc)
    week_ago = (now - timedelta(days=7)).isoformat()

    async def _c(name, q=None):
        try:
            return int(await db[name].count_documents(q or {}))
        except Exception:  # noqa: BLE001
            return 0

    # Project scope
    active_projects = await _c("jobs_master", {"status": {"$in": ["active", "in_progress"]}})
    if active_projects == 0:
        active_projects = await _c("jobs", {"status": {"$in": ["active", "in_progress"]}})
    if active_projects == 0:
        active_projects = await _c("projects", {"status": {"$in": ["active", "in_progress"]}})

    # Daily reports
    reports_7d = await _c("daily_reports", {"submitted_at": {"$gte": week_ago}})
    missing_reports = await _c("daily_reports",
                               {"status": {"$in": ["missing", "overdue"]}})
    photos_7d = await _c("job_photos", {"uploaded_at": {"$gte": week_ago}})

    # Constraints / attention
    open_constraints = await _c("operational_constraints",
                                {"status": {"$in": ["open", "in_progress"]}})
    aging_constraints = await _c("operational_constraints",
                                 {"status": {"$in": ["open", "in_progress"]},
                                  "opened_at": {"$lt": (now - timedelta(days=30)).isoformat()}})

    # Project-linked incidents (last 7d)
    project_incidents_7d = await _c("incident_cases",
                                    {"submitted_at": {"$gte": week_ago},
                                     "job_number": {"$exists": True, "$ne": None}})
    high_attention_cases = await _c("incident_cases",
                                    {"attention_level": "high",
                                     "state": {"$ne": "CLOSED"}})

    # PO backlog by project (already scoped in po_digest via project_managers)
    open_pos = await _c("po_requests",
                        {"status": {"$in": ["Submitted", "Pending Approval",
                                             "Clarification Needed",
                                             "Approved", "Pending Receipt",
                                             "Overdue Receipt"]}})

    has_any = any([active_projects, reports_7d, photos_7d, open_constraints,
                    project_incidents_7d, high_attention_cases, open_pos])
    if not has_any:
        score = insufficient_data_score(
            "No project collections populated in this environment.")
    else:
        positives, negatives = [], []
        if reports_7d > 0 and active_projects > 0 and reports_7d >= active_projects * 3:
            positives.append(Contributor(
                key="strong_daily_report_coverage",
                label=f"{reports_7d} daily report(s) across {active_projects} project(s)",
                impact=10, detail="Robust field documentation cadence."))
        if photos_7d > 0:
            positives.append(Contributor(
                key="photo_activity",
                label=f"{photos_7d} job photo(s) uploaded this week",
                impact=5, detail="Site documentation staying current."))
        if project_incidents_7d == 0 and active_projects > 0:
            positives.append(Contributor(
                key="no_incidents",
                label="Zero project incidents this week",
                impact=10, detail="Clean safety period across active projects."))
        if high_attention_cases == 0:
            positives.append(Contributor(
                key="no_high_attention",
                label="No HIGH-attention project cases",
                impact=8, detail="Project portfolio free of HIGH-scored cases."))
        if high_attention_cases > 0:
            negatives.append(Contributor(
                key="high_attention_project_cases",
                label=f"{high_attention_cases} HIGH-attention case(s)",
                impact=-min(30, high_attention_cases * 10),
                detail="High-attention cases still open."))
        if missing_reports > 0:
            negatives.append(Contributor(
                key="missing_reports",
                label=f"{missing_reports} missing / overdue daily report(s)",
                impact=-min(20, missing_reports * 3),
                detail="Daily documentation gap."))
        if aging_constraints > 0:
            negatives.append(Contributor(
                key="aging_constraints",
                label=f"{aging_constraints} constraint(s) open > 30 days",
                impact=-min(15, aging_constraints * 3),
                detail="Chronic unresolved constraints."))
        elif open_constraints > 5:
            negatives.append(Contributor(
                key="constraint_load",
                label=f"{open_constraints} open constraint(s)",
                impact=-min(10, open_constraints // 2),
                detail="High constraint load."))
        if open_pos > 30 and active_projects > 0:
            negatives.append(Contributor(
                key="po_bottleneck",
                label=f"{open_pos} open PO(s) across portfolio",
                impact=-min(15, open_pos // 10),
                detail="PO backlog impacting project throughput."))
        if project_incidents_7d > 0:
            negatives.append(Contributor(
                key="project_incidents",
                label=f"{project_incidents_7d} project incident(s) this week",
                impact=-min(20, project_incidents_7d * 6),
                detail="Project-linked safety incidents raised via intake."))

        score = score_from_contributors(
            baseline=100, positives=positives, negatives=negatives,
            trend_percent=None,
            confidence="high" if (active_projects >= 5 and reports_7d >= 5) else "medium",
            data_freshness="live",
            calculation_notes=(
                "Project score composed from daily-report coverage · "
                "photo activity · incident volume · attention-level distribution · "
                "constraint age · PO backlog. Trend engages once history "
                "rows accumulate."
            ),
        )

    # Top-5 projects with the most incidents in the last 7d
    top_5_rows = []
    try:
        # Aggregate incidents by job_number
        cursor = db["incident_cases"].aggregate([
            {"$match": {"submitted_at": {"$gte": week_ago},
                        "job_number": {"$exists": True, "$ne": None}}},
            {"$group": {"_id": "$job_number", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5},
        ])
        async for r in cursor:
            job = r.get("_id") or "—"
            top_5_rows.append([
                {"href": f"/pm/projects/{job}", "text": str(job)},
                r.get("count") or 0,
            ])
    except Exception:  # noqa: BLE001
        pass

    wins = []
    if reports_7d > 0 and active_projects > 0:
        wins.append(f"{reports_7d} daily report(s) across {active_projects} active project(s).")
    if project_incidents_7d == 0 and active_projects > 0:
        wins.append("Zero project incidents this week.")
    if photos_7d > 0:
        wins.append(f"{photos_7d} job photo(s) uploaded this week.")

    attention = []
    if high_attention_cases > 0:
        attention.append(f"{high_attention_cases} HIGH-attention case(s) still open.")
    if missing_reports > 0:
        attention.append(f"{missing_reports} missing / overdue daily report(s).")
    if aging_constraints > 0:
        attention.append(f"{aging_constraints} constraint(s) open > 30 days.")
    if project_incidents_7d > 0:
        attention.append(f"{project_incidents_7d} project incident(s) this period.")

    return build_standard_layout(
        product_id="project_intelligence",
        subject="MASCI Project Intelligence Digest",
        period_label="Weekly · Monday 13:00 UTC",
        executive_summary={
            "Active projects":         active_projects,
            "Daily reports (7d)":      reports_7d,
            "Missing / overdue DRs":   missing_reports,
            "Project incidents (7d)":  project_incidents_7d,
            "HIGH-attention cases":    high_attention_cases,
            "Open constraints":        open_constraints,
        },
        score=score.to_dict(),
        trend_direction={"arrow": "→", "tone": "flat",
                         "current": high_attention_cases,
                         "previous": None, "pct_change": None},
        top_wins=wins,
        needs_immediate_attention=attention,
        top_5_items=({
            "title": "Top 5 · Projects by Incident Volume (7d)",
            "headers": ["Project", "Incident count (7d)"],
            "rows": top_5_rows,
        } if top_5_rows else None),
        core_metrics={
            "Job photos (7d)":         photos_7d,
            "Constraints > 30d":       aging_constraints,
            "Portfolio open POs":      open_pos,
        },
        recommendations=(
            ([f"Executive review of {high_attention_cases} HIGH case(s)."] if high_attention_cases else []) +
            ([f"Chase {missing_reports} missing daily report(s)."] if missing_reports else []) +
            ([f"Resolve {aging_constraints} aging constraint(s)."] if aging_constraints else []) +
            ([f"Address {project_incidents_7d} project incident(s)."] if project_incidents_7d else [])
            or ["Portfolio steady — maintain cadence."]
        ),
        upcoming_risks=[],
        recent_changes=[
            f"Daily reports last 7d: {reports_7d}",
            f"Photos last 7d: {photos_7d}",
            f"Project incidents last 7d: {project_incidents_7d}",
        ],
        deep_links=[
            {"href": "/pm/projects", "text": "PM Project Center"},
            {"href": "/pm/daily", "text": "Daily Reports"},
            {"href": "/pm/photos", "text": "Job Photos"},
            {"href": "/safety/cases", "text": "Safety Cases"},
            {"href": "/pm/constraints", "text": "Constraints Board"},
        ],
        no_auto_decision_notice=(
            "Attention signal only. Project Managers · Operations · Safety "
            "own investigation, classification, and disposition. The platform "
            "does NOT declare projects on-time or off-track, does NOT assign "
            "blame, does NOT determine fault, and does NOT infer financial "
            "overrun beyond surfacing what the underlying systems record."
        ),
        audit_footer=(
            "Track 19.44 · Project Intelligence Digest · aggregator over "
            "jobs_master / daily_reports / job_photos / operational_constraints / "
            "incident_cases / po_requests."
        ),
    )


register_product(Product(
    product_id="project_intelligence",
    display_name="Project Intelligence Digest",
    summary="Daily reports · project incidents · constraints · photos · PO backlog.",
    permission_role="admin_only",
    template_key="executive_v1",
    schedule_freq="weekly", schedule_iso_day=1, schedule_hour_utc=13,
    status=ProductStatus.IMPLEMENTED,
    aggregator=_agg_project_intelligence,
    tags=["projects", "pm", "weekly"],
))


# ---------------------------------------------------------------------------
# 9 · Shop Intelligence Digest (IMPLEMENTED — Track 19.45B)
# ---------------------------------------------------------------------------
# Real aggregator over the confirmed shop/maintenance/fleet-defect data
# sources present in the codebase today. Zero drift — reuses existing
# collections (asset_holds · fleet_defects · equipment_units /
# equipment_master · equipment_inspections · maintainx_work_orders ·
# pm_work_orders · dvir · incident_cases · equipment_transfers). If a
# collection is empty the metric is 0 (honest) — never fabricated.
async def _agg_shop_intelligence(db, **kwargs) -> Dict[str, Any]:
    from datetime import datetime, timedelta, timezone
    from .product_layout import build_standard_layout
    from .score_model import (
        score_from_contributors, Contributor, insufficient_data_score,
    )

    now = datetime.now(timezone.utc)
    week_ago = (now - timedelta(days=7)).isoformat()
    fourteen_days_ago = (now - timedelta(days=14)).isoformat()

    async def _c(name, q=None):
        try:
            return int(await db[name].count_documents(q or {}))
        except Exception:  # noqa: BLE001
            return 0

    # Fleet / asset scope
    fleet_total = await _c("equipment_master", {})
    if fleet_total == 0:
        fleet_total = await _c("equipment_units", {})
    oos_units = await _c("equipment_units",
                         {"status": {"$in": ["OOS", "Down", "Out of Service"]}})

    # Holds
    safety_holds = await _c("asset_holds",
                            {"hold_type": "safety", "status": "active"})
    maint_holds = await _c("asset_holds",
                           {"hold_type": {"$in": ["maintenance", "repair"]},
                            "status": "active"})

    # Defects
    open_defects = await _c("fleet_defects",
                            {"status": {"$in": ["open", "in_progress"]}})
    critical_defects = await _c(
        "fleet_defects",
        {"severity": "critical",
         "status": {"$in": ["open", "in_progress"]}})
    aging_critical_defects = await _c(
        "fleet_defects",
        {"severity": "critical",
         "status": {"$in": ["open", "in_progress"]},
         "created_at": {"$lt": fourteen_days_ago}})
    defects_opened_7d = await _c("fleet_defects",
                                 {"created_at": {"$gte": week_ago}})
    defects_closed_7d = await _c("fleet_defects",
                                 {"status": {"$in": ["closed", "resolved"]},
                                  "closed_at": {"$gte": week_ago}})

    # Work orders (MaintainX + PM-scoped)
    mx_wo_open = await _c(
        "maintainx_work_orders",
        {"status": {"$in": ["open", "in_progress", "OPEN", "IN_PROGRESS"]}})
    pm_wo_open = await _c(
        "pm_work_orders",
        {"status": {"$in": ["open", "in_progress"]}})
    work_orders_open = mx_wo_open + pm_wo_open

    # Inspections + DVIR
    insp_7d = await _c("equipment_inspections",
                       {"submitted_at": {"$gte": week_ago}})
    overdue_insp = await _c("equipment_inspections",
                            {"next_due_at": {"$lt": now.isoformat()},
                             "status": {"$in": ["due", "scheduled"]}})
    dvir_open_defects = await _c("dvir", {"has_open_defects": True})

    # Equipment-linked incidents
    equip_incidents_7d = await _c(
        "incident_cases",
        {"incident_type": "equipment_damage",
         "submitted_at": {"$gte": week_ago}})

    # Recent transfers (informational — shop workload signal)
    transfers_7d = await _c("equipment_transfers",
                            {"created_at": {"$gte": week_ago}})

    # Insufficient-data guard — every collection empty means we cannot score.
    has_any = any([fleet_total, oos_units, safety_holds, maint_holds,
                   open_defects, work_orders_open, insp_7d,
                   dvir_open_defects, equip_incidents_7d, transfers_7d])
    if not has_any:
        score = insufficient_data_score(
            "No shop / fleet / defect / work-order / inspection "
            "collections populated in this environment.")
    else:
        positives, negatives = [], []
        if fleet_total > 0 and oos_units == 0:
            positives.append(Contributor(
                key="full_availability",
                label=f"Full availability · {fleet_total} unit(s)",
                impact=10, detail="No OOS units."))
        if safety_holds == 0 and fleet_total > 0:
            positives.append(Contributor(
                key="no_safety_holds",
                label="Zero active safety holds",
                impact=10, detail="No units flagged unsafe by field."))
        if critical_defects == 0 and (open_defects > 0 or defects_closed_7d > 0):
            positives.append(Contributor(
                key="no_critical_defects",
                label="No CRITICAL open defects",
                impact=8, detail="No highest-severity blockers."))
        if defects_closed_7d > 0 and defects_closed_7d >= defects_opened_7d:
            positives.append(Contributor(
                key="closing_pace",
                label=f"Closed {defects_closed_7d} vs opened "
                      f"{defects_opened_7d} defect(s) (7d)",
                impact=8, detail="Closure pace ≥ open pace."))
        if equip_incidents_7d == 0 and (fleet_total > 0 or work_orders_open > 0):
            positives.append(Contributor(
                key="no_equipment_incidents",
                label="Zero equipment-damage incidents this week",
                impact=8, detail="Clean equipment-safety period."))

        if safety_holds > 0:
            negatives.append(Contributor(
                key="safety_holds",
                label=f"{safety_holds} active safety hold(s)",
                impact=-min(30, safety_holds * 8),
                detail="Investigate immediately — units flagged unsafe."))
        if aging_critical_defects > 0:
            negatives.append(Contributor(
                key="aging_critical_defects",
                label=f"{aging_critical_defects} CRITICAL defect(s) open > 14 days",
                impact=-min(35, aging_critical_defects * 10),
                detail="Chronic critical defects · assign owner today."))
        elif critical_defects > 0:
            negatives.append(Contributor(
                key="critical_defects",
                label=f"{critical_defects} CRITICAL defect(s) open",
                impact=-min(28, critical_defects * 8),
                detail="Highest-severity defects blocking utilisation."))
        if oos_units > 0:
            negatives.append(Contributor(
                key="oos_units",
                label=f"{oos_units} unit(s) out-of-service",
                impact=-min(20, oos_units * 3),
                detail="Availability drag."))
        if maint_holds > 0:
            negatives.append(Contributor(
                key="maint_holds",
                label=f"{maint_holds} unit(s) on maintenance/repair hold",
                impact=-min(12, maint_holds * 2),
                detail="Availability drag."))
        if open_defects > 10 and not aging_critical_defects and not critical_defects:
            negatives.append(Contributor(
                key="defect_backlog",
                label=f"{open_defects} open defect(s) · backlog above threshold",
                impact=-min(15, open_defects // 3),
                detail="Aggregate defect backlog."))
        if work_orders_open > 15:
            negatives.append(Contributor(
                key="work_order_backlog",
                label=f"{work_orders_open} open work order(s)",
                impact=-min(15, work_orders_open // 5),
                detail="Repair backlog above threshold."))
        if overdue_insp > 0:
            negatives.append(Contributor(
                key="overdue_inspections",
                label=f"{overdue_insp} overdue inspection(s)",
                impact=-min(12, overdue_insp * 3),
                detail="Compliance & utilisation exposure."))
        if dvir_open_defects > 0:
            negatives.append(Contributor(
                key="dvir_open_defects",
                label=f"{dvir_open_defects} DVIR(s) with open defect(s)",
                impact=-min(15, dvir_open_defects * 3),
                detail="Field defects awaiting shop action."))
        if equip_incidents_7d > 0:
            negatives.append(Contributor(
                key="equipment_incidents",
                label=f"{equip_incidents_7d} equipment incident(s) this week",
                impact=-min(25, equip_incidents_7d * 10),
                detail="Equipment-damage incidents raised via intake."))

        score = score_from_contributors(
            baseline=100, positives=positives, negatives=negatives,
            trend_percent=None,
            confidence=("high" if (fleet_total >= 10 and
                                    (open_defects + work_orders_open) >= 5)
                        else "medium"),
            data_freshness="live",
            calculation_notes=(
                "Shop score composed from safety-hold count · critical + "
                "aging-critical defect count · OOS units · maintenance/"
                "repair holds · defect backlog · work-order backlog · "
                "overdue inspections · DVIR field defects · equipment "
                "incidents · defect closure pace. Trend engages once "
                "engine history rows accumulate."
            ),
        )

    # Top 5 — preferred order: safety holds → aging critical defects → OOS units.
    top_5_rows: list = []
    top_5_title = "Top 5 · Shop Attention"
    top_5_headers = ["Unit / Item", "Reason / Status", "Since / Age", "Detail"]
    if safety_holds > 0:
        try:
            cursor = db["asset_holds"].find(
                {"hold_type": "safety", "status": "active"},
                {"_id": 0, "unit_number": 1, "asset_id": 1, "reason": 1,
                 "opened_at": 1, "opened_by": 1},
            ).limit(5)
            async for h in cursor:
                unit = h.get("unit_number") or (h.get("asset_id") or "")[:10] or "—"
                top_5_rows.append([
                    {"href": f"/fleet/units/{unit}", "text": unit},
                    f"Safety hold — {h.get('reason') or 'no reason'}",
                    h.get("opened_at") or "—",
                    h.get("opened_by") or "—",
                ])
        except Exception:  # noqa: BLE001
            pass
    if not top_5_rows and aging_critical_defects > 0:
        try:
            cursor = db["fleet_defects"].find(
                {"severity": "critical",
                 "status": {"$in": ["open", "in_progress"]},
                 "created_at": {"$lt": fourteen_days_ago}},
                {"_id": 0, "unit_number": 1, "defect_title": 1,
                 "created_at": 1, "assigned_to": 1},
            ).limit(5)
            async for d in cursor:
                unit = d.get("unit_number") or "—"
                top_5_rows.append([
                    {"href": f"/fleet/units/{unit}", "text": unit},
                    f"CRITICAL · {d.get('defect_title') or ''}",
                    d.get("created_at") or "—",
                    d.get("assigned_to") or "unassigned",
                ])
        except Exception:  # noqa: BLE001
            pass
    if not top_5_rows and oos_units > 0:
        try:
            cursor = db["equipment_units"].find(
                {"status": {"$in": ["OOS", "Down", "Out of Service"]}},
                {"_id": 0, "unit_number": 1, "status": 1, "oos_since": 1,
                 "make": 1, "model": 1},
            ).limit(5)
            async for u in cursor:
                top_5_rows.append([
                    {"href": f"/fleet/units/{u.get('unit_number','')}",
                     "text": u.get("unit_number") or "—"},
                    u.get("status") or "OOS",
                    u.get("oos_since") or "—",
                    f"{u.get('make','')} {u.get('model','')}".strip() or "—",
                ])
        except Exception:  # noqa: BLE001
            pass

    wins = []
    if fleet_total > 0 and oos_units == 0:
        wins.append(f"Full fleet availability · {fleet_total} unit(s).")
    if safety_holds == 0 and fleet_total > 0:
        wins.append("Zero active safety holds this period.")
    if defects_closed_7d > 0 and defects_closed_7d >= defects_opened_7d:
        wins.append(f"Closed {defects_closed_7d} defect(s) — pace ≥ open pace.")
    if equip_incidents_7d == 0 and (fleet_total > 0 or work_orders_open > 0):
        wins.append("No equipment-damage incidents this week.")

    attention = []
    if safety_holds > 0:
        attention.append(f"{safety_holds} active safety hold(s) — investigate immediately.")
    if aging_critical_defects > 0:
        attention.append(
            f"{aging_critical_defects} CRITICAL defect(s) open > 14 days.")
    elif critical_defects > 0:
        attention.append(f"{critical_defects} CRITICAL defect(s) open.")
    if oos_units > 0:
        attention.append(f"{oos_units} unit(s) OOS — return to service.")
    if dvir_open_defects > 0:
        attention.append(f"{dvir_open_defects} DVIR(s) with open defect(s).")
    if work_orders_open > 15:
        attention.append(f"{work_orders_open} open work order(s) — backlog above threshold.")
    if equip_incidents_7d > 0:
        attention.append(f"{equip_incidents_7d} equipment incident(s) this week.")

    return build_standard_layout(
        product_id="shop_intelligence",
        subject="MASCI Shop Intelligence Digest",
        period_label="Weekly · Monday 13:00 UTC",
        executive_summary={
            "Fleet size":                fleet_total,
            "OOS units":                 oos_units,
            "Safety holds (active)":     safety_holds,
            "Maint/repair holds":        maint_holds,
            "Open defects":              open_defects,
            "CRITICAL defects":          critical_defects,
            "Open work orders":          work_orders_open,
        },
        score=score.to_dict(),
        trend_direction={"arrow": "→", "tone": "flat",
                         "current": safety_holds + critical_defects,
                         "previous": None, "pct_change": None},
        top_wins=wins,
        needs_immediate_attention=attention,
        top_5_items=({
            "title": top_5_title,
            "headers": top_5_headers,
            "rows": top_5_rows,
        } if top_5_rows else None),
        core_metrics={
            "Aging CRITICAL defects (>14d)": aging_critical_defects,
            "Defects opened (7d)":           defects_opened_7d,
            "Defects closed (7d)":           defects_closed_7d,
            "Inspections (7d)":              insp_7d,
            "Overdue inspections":           overdue_insp,
            "DVIR w/ open defects":          dvir_open_defects,
            "Equipment incidents (7d)":      equip_incidents_7d,
            "Asset transfers (7d)":          transfers_7d,
        },
        recommendations=(
            ([f"Investigate {safety_holds} safety hold(s) today."] if safety_holds else []) +
            ([f"Resolve {aging_critical_defects} aging CRITICAL defect(s) — assign owners."]
             if aging_critical_defects else []) +
            ([f"Return {oos_units} OOS unit(s) to service."] if oos_units else []) +
            ([f"Address {dvir_open_defects} DVIR field defect(s)."] if dvir_open_defects else []) +
            ([f"Burn down {work_orders_open} open work order(s)."]
             if work_orders_open > 15 else []) +
            ([f"Review {equip_incidents_7d} equipment incident(s)."]
             if equip_incidents_7d else [])
            or ["Shop operations steady — maintain cadence."]
        ),
        upcoming_risks=(
            ([f"{overdue_insp} inspection(s) overdue."] if overdue_insp else []) +
            ([f"{maint_holds} unit(s) on maintenance/repair hold — plan return-to-service."]
             if maint_holds else [])
        ),
        recent_changes=[
            f"Defects opened last 7d: {defects_opened_7d}",
            f"Defects closed last 7d: {defects_closed_7d}",
            f"Inspections completed last 7d: {insp_7d}",
            f"Asset transfers last 7d: {transfers_7d}",
        ],
        deep_links=[
            {"href": "/shop", "text": "Shop Console"},
            {"href": "/fleet", "text": "Fleet Center"},
            {"href": "/fleet/holds", "text": "Active Holds"},
            {"href": "/fleet/defects", "text": "Defect Board"},
            {"href": "/fleet/inspections", "text": "Inspection Center"},
            {"href": "/equipment-status-board", "text": "Equipment Status Board"},
            {"href": "/safety/cases?type=equipment_damage",
             "text": "Equipment-Damage Incidents"},
        ],
        no_auto_decision_notice=(
            "Attention signal only. Shop · Fleet · Safety own investigation, "
            "classification, and disposition. The platform does NOT determine "
            "mechanic fault, operator fault, preventability, discipline, "
            "return-to-service authorisation, or insurance liability."
        ),
        audit_footer=(
            "Track 19.45B · Shop Intelligence Digest · aggregator over "
            "equipment_master / equipment_units / asset_holds / fleet_defects / "
            "maintainx_work_orders / pm_work_orders / equipment_inspections / "
            "dvir / equipment_transfers / incident_cases. "
            "Zero-drift — no new collections."
        ),
    )


register_product(Product(
    product_id="shop_intelligence",
    display_name="Shop Intelligence Digest",
    summary="Shop maintenance · repairs · open work · defects · holds · incidents.",
    permission_role="safety_or_admin",
    template_key="executive_v1",
    schedule_freq="weekly", schedule_iso_day=1, schedule_hour_utc=13,
    status=ProductStatus.IMPLEMENTED,
    aggregator=_agg_shop_intelligence,
    tags=["shop", "fleet", "maintenance", "weekly"],
))


# ---------------------------------------------------------------------------
# 10 · Corporate Intelligence Digest (IMPLEMENTED — Track 19.45B)
# ---------------------------------------------------------------------------
# Cross-domain weighted rollup of every implemented OI product. Composes
# each domain aggregator via `compose(db, product_id=X)` and folds
# scores into a weighted corporate score. Insufficient-data domains are
# skipped (weight redistributed) — never faked as healthy.
CORPORATE_WEIGHTS = {
    "safety_morning_digest":     20,
    "project_intelligence":      20,
    "fleet_intelligence":        12,
    "shop_intelligence":         10,
    "transportation_intelligence": 10,
    "hr_intelligence":           8,
    "training_intelligence":     8,
    "po_weekly_digest":          7,
    "executive_operations_brief": 5,
}


async def _agg_corporate_intelligence(db, **kwargs) -> Dict[str, Any]:
    from .product_layout import build_standard_layout
    from .score_model import (
        score_from_contributors, Contributor, insufficient_data_score,
        attention_from_score,
    )
    from .engine import compose as _oi_compose

    # Compose every implemented domain digest. If one raises (should not
    # after 19.45B, but defensive), we treat it as insufficient-data.
    domain_scores: Dict[str, Dict[str, Any]] = {}
    domain_attention_items: Dict[str, list] = {}
    for pid in CORPORATE_WEIGHTS.keys():
        try:
            d = await _oi_compose(db, product_id=pid)
        except Exception:  # noqa: BLE001
            continue
        sc = d.get("operational_intelligence_score") or {}
        domain_scores[pid] = sc
        # Grab that domain's attention items (5 max) for later top-5.
        try:
            att_sec = next(s for s in d["sections"]
                           if s["section_key"] == "needs_immediate_attention")
            items = [i for i in (att_sec.get("items") or [])
                     if isinstance(i, str)
                     and not i.startswith("— Not applicable")]
            domain_attention_items[pid] = items[:5]
        except Exception:  # noqa: BLE001
            domain_attention_items[pid] = []

    # Filter to domains with real (non-insufficient) confidence.
    scored: Dict[str, int] = {}
    weighted_total = 0.0
    weighted_denom = 0.0
    for pid, sc in domain_scores.items():
        conf = (sc or {}).get("confidence") or "insufficient_data"
        if conf == "insufficient_data":
            continue
        s = int(sc.get("overall_score") or 0)
        w = int(CORPORATE_WEIGHTS.get(pid) or 0)
        scored[pid] = s
        weighted_total += s * w
        weighted_denom += w

    if weighted_denom == 0:
        score = insufficient_data_score(
            "No domain product has sufficient data — corporate score "
            "cannot be computed this period."
        )
        corp_score = 0
        attention_level = "CRITICAL"
    else:
        corp_score = int(round(weighted_total / weighted_denom))
        attention_level = attention_from_score(corp_score)
        positives, negatives = [], []
        # Highest-scoring domain becomes a positive contributor.
        top_domain = max(scored.items(), key=lambda kv: kv[1])
        low_domain = min(scored.items(), key=lambda kv: kv[1])
        if top_domain[1] >= 85:
            positives.append(Contributor(
                key="strong_domain",
                label=f"{top_domain[0]} at score {top_domain[1]}",
                impact=6,
                detail=f"Strongest domain — {top_domain[0]}."))
        high_crit_domains = [pid for pid, s in scored.items() if s < 65]
        if not high_crit_domains:
            positives.append(Contributor(
                key="all_domains_healthy",
                label=f"All {len(scored)} scored domain(s) at LOW/MEDIUM attention",
                impact=10,
                detail="No domain in HIGH/CRITICAL."))
        else:
            negatives.append(Contributor(
                key="high_crit_domains",
                label=f"{len(high_crit_domains)} domain(s) in HIGH/CRITICAL",
                impact=-min(30, len(high_crit_domains) * 8),
                detail=f"Domains: {', '.join(high_crit_domains)}"))
        if low_domain[1] < 40:
            negatives.append(Contributor(
                key="lowest_domain_critical",
                label=f"{low_domain[0]} at score {low_domain[1]} (CRITICAL)",
                impact=-15,
                detail=f"Lowest domain — {low_domain[0]} needs executive attention."))

        score = score_from_contributors(
            baseline=corp_score, positives=positives, negatives=negatives,
            trend_percent=None,
            confidence=("high" if len(scored) >= 6 else "medium"),
            data_freshness="live",
            calculation_notes=(
                "Corporate score = weighted rollup of every domain "
                "Operational Intelligence Score. Weights: "
                + ", ".join(f"{k}={v}%"
                            for k, v in CORPORATE_WEIGHTS.items())
                + ". Domains with insufficient data are excluded from "
                "the rollup (never scored as healthy)."
            ),
        )
        # Preserve the underlying weighted rollup score explicitly (the
        # contributor pass may have pushed it up/down slightly).
        score.overall_score = corp_score
        score.attention_level = attention_level

    # Domain summary table (Top-5 semantic — sorted by lowest score first)
    top_5_rows: list = []
    for pid, s in sorted(scored.items(), key=lambda kv: kv[1]):
        p = next((x for x in [_get(pid)] if x), None)
        display = p.display_name if p else pid
        top_5_rows.append([
            display,
            s,
            attention_from_score(s),
            {"href": f"/api/operational-intelligence/{pid}/preview",
             "text": "Preview"},
        ])
    # Note: insufficient-data domains appear below the scored ones so the
    # executive can see gaps at a glance (honest, not hidden).
    for pid in CORPORATE_WEIGHTS.keys():
        if pid in scored or pid not in domain_scores:
            continue
        p = next((x for x in [_get(pid)] if x), None)
        display = p.display_name if p else pid
        top_5_rows.append([
            display,
            "—",
            "insufficient_data",
            {"href": f"/api/operational-intelligence/{pid}/preview",
             "text": "Preview"},
        ])
    top_5_rows = top_5_rows[:9]  # cap for boardroom cleanliness

    # Highest-attention concrete signals — union of attention items from
    # the lowest-scoring 3 domains.
    attention_signals: list = []
    for pid, _ in sorted(scored.items(), key=lambda kv: kv[1])[:3]:
        for it in (domain_attention_items.get(pid) or []):
            attention_signals.append(f"[{pid}] {it}")
        if len(attention_signals) >= 8:
            break
    attention_signals = attention_signals[:8]

    wins = []
    if scored:
        n_low_attention = sum(1 for s in scored.values() if s >= 85)
        if n_low_attention:
            wins.append(f"{n_low_attention} domain(s) at LOW attention "
                        f"(score ≥ 85).")
        if not any(s < 40 for s in scored.values()):
            wins.append("No domain scored CRITICAL this period.")
        n_scored = len(scored)
        if n_scored >= 6:
            wins.append(f"Cross-domain visibility across {n_scored} scored domains.")

    executive_summary = {
        "Corporate Score":              corp_score if weighted_denom else "insufficient_data",
        "Attention Level":              attention_level,
        "Domains scored":               len(scored),
        "Domains w/ insufficient data": len(domain_scores) - len(scored),
        "HIGH / CRITICAL domains":      sum(1 for s in scored.values() if s < 65),
        "LOW attention domains":        sum(1 for s in scored.values() if s >= 85),
    }

    recommendations = []
    if scored:
        worst = sorted(scored.items(), key=lambda kv: kv[1])[:3]
        for pid, s in worst:
            if s < 65:
                recommendations.append(
                    f"Executive review of {pid} (score {s} · "
                    f"{attention_from_score(s)}).")
        if not recommendations:
            recommendations.append(
                "Portfolio steady across every scored domain — maintain cadence."
            )
    else:
        recommendations.append(
            "Populate domain data sources — corporate score cannot be "
            "computed from insufficient-data domains alone."
        )

    return build_standard_layout(
        product_id="corporate_intelligence",
        subject="MASCI Corporate Intelligence Digest",
        period_label="Monthly · First Monday 14:00 UTC",
        executive_summary=executive_summary,
        score=score.to_dict(),
        trend_direction={"arrow": "→", "tone": "flat",
                         "current": corp_score if weighted_denom else None,
                         "previous": None, "pct_change": None},
        top_wins=wins,
        needs_immediate_attention=attention_signals,
        top_5_items=({
            "title": "Domain Scores (Lowest First)",
            "headers": ["Domain", "Score", "Attention", "Preview"],
            "rows": top_5_rows,
        } if top_5_rows else None),
        core_metrics={
            "Weight model":
                ", ".join(f"{k}={v}%" for k, v in CORPORATE_WEIGHTS.items()),
        },
        recommendations=recommendations,
        upcoming_risks=[],
        recent_changes=[
            f"Domains composed: {len(domain_scores)}",
            f"Domains scored: {len(scored)}",
        ],
        deep_links=[
            {"href": "/safety/cases", "text": "Safety Case Center"},
            {"href": "/pm/projects", "text": "PM Project Center"},
            {"href": "/fleet", "text": "Fleet Center"},
            {"href": "/shop", "text": "Shop Console"},
            {"href": "/hr/employees", "text": "HR Directory"},
            {"href": "/hr/training-records", "text": "Training Records"},
            {"href": "/po-requests", "text": "Purchase Orders"},
            {"href": "/admin/executive-dashboard", "text": "Executive Dashboard"},
            {"href": "/api/operational-intelligence/products",
             "text": "OI Product Registry"},
        ],
        no_auto_decision_notice=(
            "Cross-domain attention signal only. Domain owners "
            "(Safety · PM · Fleet · Shop · HR · Training · Transportation · "
            "Procurement · Executive) own investigation, classification, "
            "and disposition. The platform does NOT declare the company "
            "compliant, does NOT declare legal risk conclusions, does NOT "
            "determine liability, discipline, or issue automatic executive "
            "decisions."
        ),
        audit_footer=(
            "Track 19.45B · Corporate Intelligence Digest · weighted "
            "rollup of every implemented OI product. Composes via "
            "engine.compose() — zero new data sources · zero drift."
        ),
    )


def _get(pid: str):
    """Local shim — avoids re-importing get_product inside the aggregator."""
    from .registry import get_product
    return get_product(pid)


register_product(Product(
    product_id="corporate_intelligence",
    display_name="Corporate Intelligence Digest",
    summary="Cross-domain executive rollup — weighted score across every domain.",
    permission_role="admin_only",
    template_key="executive_v1",
    schedule_freq="monthly",
    schedule_iso_day=1, schedule_hour_utc=14,
    status=ProductStatus.IMPLEMENTED,
    aggregator=_agg_corporate_intelligence,
    tags=["corporate", "executive", "monthly", "rollup"],
))


# ---------------------------------------------------------------------------
# 11 · Weekly Operations Digest (IMPLEMENTED — Track 19.46)
# ---------------------------------------------------------------------------
# Distinct from Corporate Intelligence:
#   • Corporate  — "How is the company?" (weighted snapshot)
#   • Weekly Ops — "What changed operationally this week?" (WoW deltas)
#
# Method: compose each implemented domain, then diff each domain's
# overall_score against the most-recent prior history row for that
# product (`operational_intelligence_history` collection). No new data
# sources. No new email provider. No new scheduler. No new history
# collection. Every signal earns its place by answering:
#   "Would leadership make a worse Monday decision if this disappeared?"
async def _agg_weekly_operations(db, **kwargs) -> Dict[str, Any]:
    from .product_layout import build_standard_layout
    from .score_model import (
        score_from_contributors, Contributor, insufficient_data_score,
        attention_from_score,
    )
    from .engine import compose as _oi_compose, COLLECTION_HISTORY

    # Domains to fold into the weekly view. We exclude the Weekly digest
    # itself (obviously) and Corporate (which itself already composes
    # everything — including its own signal would double-count and
    # create noise, violating the "every section must earn its place"
    # rule).
    DOMAINS = [
        "safety_morning_digest",
        "project_intelligence",
        "fleet_intelligence",
        "shop_intelligence",
        "transportation_intelligence",
        "hr_intelligence",
        "training_intelligence",
        "po_weekly_digest",
        "executive_operations_brief",
    ]

    current: Dict[str, Dict[str, Any]] = {}
    attention_by_domain: Dict[str, list] = {}
    for pid in DOMAINS:
        try:
            d = await _oi_compose(db, product_id=pid)
        except Exception:  # noqa: BLE001
            continue
        current[pid] = d.get("operational_intelligence_score") or {}
        # Pull that domain's own attention items so we can bubble
        # them up when the domain is declining or in HIGH/CRITICAL.
        try:
            att_sec = next(s for s in d["sections"]
                           if s["section_key"] == "needs_immediate_attention")
            items = [i for i in (att_sec.get("items") or [])
                     if isinstance(i, str)
                     and not i.startswith("— Not applicable")]
            attention_by_domain[pid] = items
        except Exception:  # noqa: BLE001
            attention_by_domain[pid] = []

    # Look up the most-recent prior history row per domain to compute
    # WoW deltas. This is the ONE reason Weekly Ops exists.
    prior: Dict[str, Dict[str, Any]] = {}
    for pid in DOMAINS:
        try:
            row = await db[COLLECTION_HISTORY].find_one(
                {"product_id": pid},
                {"_id": 0, "digest_object.operational_intelligence_score": 1,
                 "generated_at": 1, "period": 1},
                sort=[("generated_at", -1)],
            )
            if row:
                prior[pid] = ((row.get("digest_object") or {})
                              .get("operational_intelligence_score") or {})
        except Exception:  # noqa: BLE001
            pass

    # Filter to domains with a current real score (skip insufficient_data).
    scored: Dict[str, int] = {}
    for pid, sc in current.items():
        conf = (sc or {}).get("confidence") or "insufficient_data"
        if conf == "insufficient_data":
            continue
        scored[pid] = int(sc.get("overall_score") or 0)

    # Compute deltas. Positive delta = improvement.
    deltas: Dict[str, int] = {}
    for pid, s in scored.items():
        p = prior.get(pid) or {}
        prev = p.get("overall_score")
        if prev is None:
            continue
        try:
            deltas[pid] = int(s) - int(prev)
        except (TypeError, ValueError):
            continue

    improvers = [(pid, deltas[pid]) for pid in deltas if deltas[pid] > 0]
    decliners = [(pid, deltas[pid]) for pid in deltas if deltas[pid] < 0]
    high_crit_now = [pid for pid, s in scored.items() if s < 65]

    # Insufficient-data guard — must have at least one scored domain
    # to say anything meaningful about the week.
    if not scored:
        score = insufficient_data_score(
            "No domain has sufficient data — Weekly Operations "
            "cannot compute this week's change signals.")
    else:
        positives, negatives = [], []
        if improvers:
            positives.append(Contributor(
                key="domains_improving",
                label=f"{len(improvers)} domain(s) improved WoW",
                impact=min(12, len(improvers) * 3),
                detail="Score increase vs. last recorded period."))
        if decliners:
            negatives.append(Contributor(
                key="domains_declining",
                label=f"{len(decliners)} domain(s) declined WoW",
                impact=-min(20, len(decliners) * 5),
                detail="Score decrease vs. last recorded period."))
        if high_crit_now:
            negatives.append(Contributor(
                key="domains_in_high_or_critical",
                label=f"{len(high_crit_now)} domain(s) in HIGH/CRITICAL now",
                impact=-min(25, len(high_crit_now) * 8),
                detail=f"Domains: {', '.join(high_crit_now)}"))
        elif scored:
            positives.append(Contributor(
                key="no_domains_in_high_or_critical",
                label=f"No domain in HIGH/CRITICAL ({len(scored)} scored)",
                impact=10,
                detail="Every scored domain sits at LOW or MEDIUM attention."))

        # Baseline = mean of current domain scores — Weekly Ops is a
        # cross-domain view, not a weighted rollup (that's Corporate).
        baseline = int(round(sum(scored.values()) / max(1, len(scored))))
        # Trend percent = mean of per-domain deltas normalised to prior.
        trend_percent = None
        if deltas:
            prior_scores = [((prior.get(pid) or {}).get("overall_score") or 0)
                            for pid in deltas]
            prior_mean = sum(prior_scores) / max(1, len(prior_scores))
            curr_mean = sum(scored[pid] for pid in deltas) / max(1, len(deltas))
            if prior_mean > 0:
                trend_percent = round(
                    ((curr_mean - prior_mean) / prior_mean) * 100.0, 1)

        score = score_from_contributors(
            baseline=baseline, positives=positives, negatives=negatives,
            trend_percent=trend_percent,
            confidence=("high" if (len(scored) >= 6 and deltas) else
                        "medium" if len(scored) >= 3 else "low"),
            data_freshness="live",
            calculation_notes=(
                "Weekly Operations score is a cross-domain execution "
                "score for the reporting week. Baseline is the mean of "
                "current domain scores. Positive contributor = number "
                "of domains improving WoW. Negative contributors = "
                "domains declining WoW + domains currently HIGH/CRITICAL. "
                "Trend percent = WoW mean-score change. If no prior "
                "history rows exist, trend renders honestly as →."
            ),
        )

    # Top Wins — meaningful improvements (real deltas · not noise).
    wins = []
    for pid, d in sorted(improvers, key=lambda kv: -kv[1])[:4]:
        p = _get(pid)
        name = p.display_name if p else pid
        wins.append(f"{name} ▲ {d} points WoW (score {scored[pid]}).")
    if scored and not high_crit_now:
        wins.append(f"No domain in HIGH/CRITICAL across "
                    f"{len(scored)} scored domain(s).")
    if not deltas and scored:
        wins.append(
            "First-run bootstrap — WoW deltas engage next period "
            "once history rows accumulate."
        )

    # Needs Immediate Attention — real operational concerns only.
    # Priority: current HIGH/CRITICAL domains first, then declining
    # domains, then the actual attention items each declining domain
    # already surfaces.
    attention: list = []
    for pid, s in sorted(
            ((pid, scored[pid]) for pid in high_crit_now),
            key=lambda kv: kv[1]):
        p = _get(pid)
        name = p.display_name if p else pid
        d = deltas.get(pid)
        d_str = f" · WoW ▼ {abs(d)}" if d and d < 0 else ""
        attention.append(f"{name} — {attention_from_score(s)} (score {s}){d_str}.")
    for pid, d in sorted(decliners, key=lambda kv: kv[1])[:4]:
        if pid in high_crit_now:
            continue
        p = _get(pid)
        name = p.display_name if p else pid
        attention.append(f"{name} declined {abs(d)} points WoW (score now {scored[pid]}).")
    # Bubble one concrete signal from the worst two declining domains.
    for pid, _ in sorted(decliners, key=lambda kv: kv[1])[:2]:
        for it in (attention_by_domain.get(pid) or [])[:1]:
            attention.append(f"[{pid}] {it}")

    # Top 5 — cross-domain operational priorities. Rows are ranked by
    # attention severity first, then WoW delta magnitude. Not five rows
    # from Mongo — five rows leadership should look at first.
    ranked: list = []
    for pid, s in scored.items():
        p = _get(pid)
        name = p.display_name if p else pid
        d = deltas.get(pid)
        # Priority score: lower = more urgent. HIGH/CRITICAL rank first,
        # then within a bucket the biggest decliners.
        att = attention_from_score(s)
        att_rank = {"CRITICAL": 0, "HIGH": 1,
                    "MEDIUM": 2, "LOW": 3}.get(att, 4)
        delta_rank = (d or 0)   # negative deltas first
        ranked.append((att_rank, delta_rank, name, s, att, d, pid))
    ranked.sort()
    top_5_rows = []
    for att_rank, delta_rank, name, s, att, d, pid in ranked[:5]:
        d_str = ("▲ " + str(d)) if d and d > 0 else \
                ("▼ " + str(abs(d))) if d and d < 0 else "—"
        top_5_rows.append([
            name,
            s,
            att,
            d_str,
            {"href": f"/api/operational-intelligence/{pid}/preview",
             "text": "Preview"},
        ])

    # Recommendations — every recommendation must be specific.
    recommendations = []
    for pid, s in sorted(
            ((pid, scored[pid]) for pid in high_crit_now),
            key=lambda kv: kv[1])[:3]:
        p = _get(pid)
        name = p.display_name if p else pid
        recommendations.append(
            f"Executive review of {name} (score {s} · "
            f"{attention_from_score(s)}) at the Monday operations meeting.")
    for pid, d in sorted(decliners, key=lambda kv: kv[1])[:2]:
        if pid in high_crit_now:
            continue
        p = _get(pid)
        name = p.display_name if p else pid
        recommendations.append(
            f"Investigate {name} — declined {abs(d)} points WoW; "
            f"identify the root-cause signal before it becomes HIGH.")
    if not recommendations:
        recommendations.append(
            "Operations steady across every scored domain — maintain "
            "cadence and confirm next week's Monday agenda.")

    # Upcoming Risks — emerging (not existing) issues. A "MEDIUM" domain
    # that is declining is an emerging risk. A "LOW" domain that is
    # improving is not a risk. This is the only place we surface
    # "things about to become problems", not current problems.
    upcoming_risks: list = []
    for pid, d in decliners:
        s = scored[pid]
        att = attention_from_score(s)
        if att == "MEDIUM" and d <= -3:
            p = _get(pid)
            name = p.display_name if p else pid
            upcoming_risks.append(
                f"{name} sliding toward HIGH (score {s}, ▼ {abs(d)} WoW).")

    # Recent Changes — meaningful deltas.
    recent_changes: list = []
    if improvers:
        recent_changes.append(
            f"↑ {len(improvers)} domain(s) improved WoW (best: "
            f"{improvers[0][0]} +{improvers[0][1]}).")
    if decliners:
        worst = min(decliners, key=lambda kv: kv[1])
        recent_changes.append(
            f"↓ {len(decliners)} domain(s) declined WoW (worst: "
            f"{worst[0]} {worst[1]}).")
    if not deltas and scored:
        recent_changes.append(
            "No prior history rows yet — WoW deltas engage next period.")

    # Trend table — the last 4 recorded score rows per scored domain
    # from the history collection. If a domain has < 2 rows the trend
    # column honestly reads "insufficient".
    trend_headers = ["Domain", "Score now", "Attention", "WoW Δ",
                     "History (up to 4 latest)"]
    trend_rows = []
    for pid, s in sorted(scored.items(), key=lambda kv: kv[1]):
        p = _get(pid)
        name = p.display_name if p else pid
        d = deltas.get(pid)
        d_str = ("▲ " + str(d)) if d and d > 0 else \
                ("▼ " + str(abs(d))) if d and d < 0 else "—"
        history_cell = "insufficient"
        try:
            cursor = db[COLLECTION_HISTORY].find(
                {"product_id": pid},
                {"_id": 0,
                 "digest_object.operational_intelligence_score.overall_score": 1,
                 "period": 1},
            ).sort([("generated_at", -1)]).limit(4)
            hist_scores = []
            async for row in cursor:
                v = (((row.get("digest_object") or {})
                      .get("operational_intelligence_score") or {})
                     .get("overall_score"))
                if v is not None:
                    hist_scores.append(int(v))
            if hist_scores:
                history_cell = " → ".join(str(x) for x in reversed(hist_scores))
        except Exception:  # noqa: BLE001
            pass
        trend_rows.append([name, s, attention_from_score(s), d_str, history_cell])

    executive_summary = {
        "Domains scored":         len(scored),
        "Domains insufficient":   len(current) - len(scored),
        "Improved WoW":           len(improvers),
        "Declined WoW":           len(decliners),
        "HIGH / CRITICAL now":    len(high_crit_now),
        "Mean domain score":      (int(round(sum(scored.values()) /
                                              max(1, len(scored))))
                                    if scored else "insufficient_data"),
    }

    return build_standard_layout(
        product_id="weekly_operations_digest",
        subject="MASCI Weekly Operations Digest",
        period_label="Weekly · Monday 13:30 UTC",
        executive_summary=executive_summary,
        score=score.to_dict(),
        trend_direction={
            "arrow": score.trend_direction,
            "tone": {"▲": "up", "▼": "down", "→": "flat"}
                    .get(score.trend_direction, "flat"),
            "current": (int(round(sum(scored.values()) / max(1, len(scored))))
                        if scored else None),
            "previous": None,
            "pct_change": score.trend_percent,
        },
        top_wins=wins,
        needs_immediate_attention=attention,
        top_5_items=({
            "title": "Top 5 · Cross-Domain Priorities This Week",
            "headers": ["Domain", "Score", "Attention", "WoW Δ", "Preview"],
            "rows": top_5_rows,
        } if top_5_rows else None),
        core_metrics={
            "Scored domains":         ", ".join(sorted(scored.keys())) or "—",
            "Improvers":              ", ".join(pid for pid, _ in improvers) or "—",
            "Decliners":              ", ".join(pid for pid, _ in decliners) or "—",
        },
        trend_table=({"headers": trend_headers, "rows": trend_rows}
                     if trend_rows else None),
        recommendations=recommendations,
        upcoming_risks=upcoming_risks,
        recent_changes=recent_changes,
        deep_links=[
            {"href": "/safety/cases", "text": "Safety Case Center"},
            {"href": "/pm/projects", "text": "PM Project Center"},
            {"href": "/fleet", "text": "Fleet Center"},
            {"href": "/shop", "text": "Shop Console"},
            {"href": "/admin/transportation/command-queue",
             "text": "Transportation Command Queue"},
            {"href": "/hr/employees", "text": "HR Directory"},
            {"href": "/hr/training-records", "text": "Training Records"},
            {"href": "/po-requests", "text": "Purchase Orders"},
            {"href": "/admin/executive-dashboard", "text": "Executive Dashboard"},
        ],
        no_auto_decision_notice=(
            "Weekly Operations is an attention signal only. Domain "
            "owners (Safety · PM · Fleet · Shop · HR · Training · "
            "Transportation · Procurement · Executive) own "
            "investigation, classification, and disposition. The "
            "platform does NOT determine fault, discipline, "
            "preventability, OSHA recordability, liability, or "
            "compliance status. Every recommendation is a discussion "
            "prompt for the Monday operations meeting — never an "
            "automatic executive decision."
        ),
        audit_footer=(
            "Track 19.46 · Weekly Operations Digest · cross-domain WoW "
            "delta report. Composes 9 domain products via "
            "engine.compose() · diffs against prior history rows in "
            "operational_intelligence_history. Zero new data sources · "
            "zero drift."
        ),
    )


register_product(Product(
    product_id="weekly_operations_digest",
    display_name="Weekly Operations Digest",
    summary="What changed operationally this week · WoW deltas across every domain.",
    permission_role="admin_only",
    template_key="executive_v1",
    schedule_freq="weekly",
    schedule_iso_day=1, schedule_hour_utc=13,  # Monday 13:00 UTC
    status=ProductStatus.IMPLEMENTED,
    aggregator=_agg_weekly_operations,
    tags=["operations", "weekly", "leadership", "delta"],
))


# ---------------------------------------------------------------------------
# 12 · Contract-registered products — aggregators not yet implemented
# ---------------------------------------------------------------------------
async def _not_implemented(db, **kwargs):  # noqa: ARG001
    # The engine raises NotImplementedError before calling this — this
    # is a defensive last-line stub.
    raise NotImplementedError("aggregator not yet implemented")


_CONTRACT_REGISTERED_PRODUCTS: list = []

for _p in _CONTRACT_REGISTERED_PRODUCTS:
    register_product(Product(
        product_id=_p.product_id, display_name=_p.display_name,
        summary=_p.summary, permission_role=_p.permission_role,
        template_key=_p.template_key, schedule_freq=_p.schedule_freq,
        schedule_iso_day=_p.schedule_iso_day,
        schedule_hour_utc=_p.schedule_hour_utc,
        status=ProductStatus.CONTRACT_REGISTERED,
        aggregator=_not_implemented,
        tags=list(_p.tags),
    ))


__all__ = []
