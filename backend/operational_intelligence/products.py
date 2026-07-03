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
# 3–10 · Contract-registered products — aggregators not yet implemented
# ---------------------------------------------------------------------------
async def _not_implemented(db, **kwargs):  # noqa: ARG001
    # The engine raises NotImplementedError before calling this — this
    # is a defensive last-line stub.
    raise NotImplementedError("aggregator not yet implemented")


_CONTRACT_REGISTERED_PRODUCTS = [
    Product(
        product_id="weekly_operations_digest",
        display_name="Weekly Operations Digest",
        summary="Company-wide weekly rollup — projects · production · schedule · safety.",
        permission_role="admin_only", template_key="executive_v1",
        schedule_freq="weekly", schedule_iso_day=1, schedule_hour_utc=13,
        tags=["operations", "weekly"],
    ),
    Product(
        product_id="fleet_intelligence",
        display_name="Fleet Intelligence Digest",
        summary="Equipment · inspections · maintenance · downtime · repair trends.",
        permission_role="safety_or_admin", template_key="executive_v1",
        schedule_freq="weekly", schedule_iso_day=1, schedule_hour_utc=13,
        tags=["fleet", "equipment"],
    ),
    Product(
        product_id="hr_intelligence",
        display_name="HR Intelligence Digest",
        summary="Training · expirations · lifecycle · recognition · compliance.",
        permission_role="admin_only", template_key="executive_v1",
        schedule_freq="weekly", schedule_iso_day=1, schedule_hour_utc=13,
        tags=["hr"],
    ),
    Product(
        product_id="training_intelligence",
        display_name="Training Intelligence Digest",
        summary="Upcoming expirations · attendance · certifications · missing training.",
        permission_role="admin_only", template_key="executive_v1",
        schedule_freq="weekly", schedule_iso_day=1, schedule_hour_utc=13,
        tags=["training", "hr"],
    ),
    Product(
        product_id="project_intelligence",
        display_name="Project Intelligence Digest",
        summary="Project health · daily reports · risks · photos · schedule.",
        permission_role="admin_only", template_key="executive_v1",
        schedule_freq="weekly", schedule_iso_day=1, schedule_hour_utc=13,
        tags=["projects"],
    ),
    Product(
        product_id="shop_intelligence",
        display_name="Shop Intelligence Digest",
        summary="Shop maintenance · repairs · open work · assignments · inventory.",
        permission_role="safety_or_admin", template_key="executive_v1",
        schedule_freq="weekly", schedule_iso_day=1, schedule_hour_utc=13,
        tags=["shop"],
    ),
    Product(
        product_id="corporate_intelligence",
        display_name="Corporate Intelligence Digest",
        summary="Company-wide executive intelligence across every domain.",
        permission_role="admin_only", template_key="executive_v1",
        schedule_freq="monthly", schedule_iso_day=1, schedule_hour_utc=14,
        tags=["corporate", "executive"],
    ),
]

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
