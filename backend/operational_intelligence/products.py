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
    d = await compose_digest(
        db,
        digest_window_days=kwargs.get("window", 7),
        top_n=kwargs.get("top_n", 5),
    )
    # Adapt into the canonical section-based shape the engine renderer
    # understands, while keeping every original field for consumers that
    # still read the 19.39 shape.
    es = d["executive_summary"]
    top = d["top_attention_cases"]
    needs = d["needs_attention_today"]
    trends = d["portfolio_trends"]
    sections = [
        {"title": "Executive Summary", "kind": "kv", "rows": {
            "Open cases":       es["total_open_cases"],
            "High attention":   es["high_attention_cases"],
            "Opened last 7d":   es["cases_opened_recent"],
            "Closed last 7d":   es["cases_closed_recent"],
            "Overdue CAPAs":    es["overdue_capas"],
            "Avg readiness %":  es["average_readiness_pct"],
        }},
        {"title": "Top Attention Cases", "kind": "table",
         "headers": ["Case", "Project", "Type", "Attention",
                     "Days open", "CAPA open", "Top signal"],
         "rows": [[
             {"href": _base_link(r["case_id"]), "text": f"#{r['case_number'] or r['case_id'][:8]}"},
             r.get("job_number") or "",
             r.get("incident_type") or "",
             f"{(r.get('attention_level') or 'low').upper()} · {r.get('attention_score')}",
             r.get("days_open") or "",
             r.get("capa_open") or 0,
             f"{r.get('top_signal_key','')} — {r.get('top_signal_rationale','')}",
         ] for r in top]},
        {"title": "Needs Attention Today", "kind": "list", "items": [
            f"Evidence gaps: {needs['evidence_gaps']}",
            f"Overdue CAPAs: {needs['overdue_capas']}",
            f"Delayed closeout: {needs['delayed_closeout']}",
            f"Executive review needed: {needs['executive_review_needed']}",
        ]},
        {"title": "Portfolio Trends", "kind": "list", "items": [
            f"{k.replace('_',' ')}: {v}" for k, v in trends.items() if v > 0
        ] or ["No open cases in tracked categories."]},
    ]
    return {
        "subject": SUBJECT_DEFAULT,
        "sections": sections,
        "no_auto_decision_notice": d["no_auto_decision_notice"],
        # Original 19.39 shape preserved for downstream consumers.
        "legacy_v1_shape": d,
    }


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
    cases = await _list_cases_readonly(db, limit=kwargs.get("limit", 200))
    rows = await _rows_for_cases(db, cases, want_attention=True)
    total = len(rows)
    open_states = {"CLOSED"}
    open_ = sum(1 for r in rows if (r.get("state") or "").upper() not in open_states)
    high = sum(1 for r in rows if r.get("attention_level") == "high")
    med = sum(1 for r in rows if r.get("attention_level") == "medium")
    low = sum(1 for r in rows if r.get("attention_level") == "low")
    capa_open = sum(r.get("capa_open") or 0 for r in rows)
    days_open_vals = [r.get("days_open") or 0 for r in rows]
    avg_days = round(sum(days_open_vals) / len(days_open_vals)) if days_open_vals else 0
    sections = [
        {"title": "Portfolio", "kind": "kv", "rows": {
            "Total cases":  total,
            "Open":         open_,
            "High attention": high,
            "Medium":       med,
            "Low":          low,
            "Total open CAPAs": capa_open,
            "Avg days open": avg_days,
        }},
        {"title": "Top 5 Priority Cases", "kind": "table",
         "headers": ["Case", "Type", "State", "Attention",
                     "Days open", "CAPA open"],
         "rows": [[
             {"href": _base_link(r["case_id"]), "text": f"#{r.get('case_number','')[:12] or r['case_id'][:8]}"},
             r.get("incident_type") or "",
             r.get("state") or "",
             f"{(r.get('attention_level') or 'low').upper()} · {r.get('attention_score')}",
             r.get("days_open") or 0,
             r.get("capa_open") or 0,
         ] for r in sorted(rows, key=lambda x: -(x.get("attention_score") or 0))[:5]]},
    ]
    return {
        "subject": "MASCI Executive Operations Brief",
        "sections": sections,
        "no_auto_decision_notice": (
            "This brief is an attention signal only. Domain owners "
            "(Safety · Operations · HR · Fleet · Transportation) own "
            "investigation and classification. The platform does not "
            "decide OSHA recordability, root cause, liability, fault, "
            "discipline, or insurance responsibility."
        ),
    }


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
        product_id="transportation_intelligence",
        display_name="Transportation Intelligence Digest",
        summary="Fleet · drivers · DVIR · utilization · assignments.",
        permission_role="safety_or_admin", template_key="executive_v1",
        schedule_freq="weekly", schedule_iso_day=1, schedule_hour_utc=13,
        tags=["transportation", "fleet"],
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
