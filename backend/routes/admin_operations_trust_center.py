"""TRACK 15.76B · Operations Trust Center · finalization.

Adds (without breaking the Track 15.76A contract):

  * categorized 7-axis Trust Score with per-category penalties
  * three-tier finding split — critical · warning · cleanup
  * operator action panel (sorted by impact, with remediation links)
  * subsystem health cards (one per operational subsystem)
  * trust-score trend (24h/7d/30d) backed by persisted snapshots
  * executive narrative (sentence-form platform status)
  * estimated remediation time (sum of seconds)

Endpoint contract:

  GET /api/admin/operations-trust-center?trend_hours=24
    →  Same envelope as 15.76A, plus:
       - categories[]           (7 named subsystems with score/band/inputs)
       - critical_problems[]    (production-blocking)
       - operational_warnings[] (attention needed, not blocking)
       - cleanup_opportunities[] (pure data hygiene)
       - operator_actions[]     (prioritized fix-it list)
       - subsystems[]           (compact health cards)
       - trend[]                ([{ts, score, band}, ...])
       - executive_narrative    (human sentence)
       - estimated_remediation_seconds (sum)

All previous keys (``trust_score``, ``score_band``, ``summary``,
``workflows``, ``master_data``, ``red_alert``) remain present, so
the existing 10 capstone tests continue to pass.
"""
from __future__ import annotations

import os
from inspect import isawaitable
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Depends

from lib.canonical_truth import canonical_truth_surface, derived_truth_payload
from lib.email_audit_status import (
    normalized_allowed_email_audit_statuses,
    normalized_failure_statuses,
    normalized_notification_attempt_statuses,
)
from lib.ots_truth import (
    CORRELATED,
    OBSERVED,
    UNKNOWN,
    canonical_truth_card,
    claim_rank,
    compatibility_projection,
    projected_truth_relationship,
    public_ots_projection,
)
from lib.trust_score import compute_score
from lib.trust_score_v2 import compute_categorized_score, CATEGORY_WEIGHTS
from lib.trust_score_history import (
    ensure_indexes as _hist_ensure,
    write_snapshot, read_trend,
)
from lib.master_data_trust import collect_findings, overall_band
from lib import red_alert


_WORKFLOW_LABELS: Dict[str, str] = {
    "daily-report": "Daily Report",
    "meeting": "Safety Meeting",
    "jha": "JHA / JHP",
    "incident": "Incident",
    "inspection": "Site Inspection",
    "qaqc": "QA/QC",
    "equipment-inspection": "Equipment Pre-Op",
    "dvir": "DVIR",
    "hr-request": "HR Request",
    "dispatch-assignment": "Dispatch Assignment",
    "shop-defect": "Shop Defect",
}

_STAGE_LABELS: Dict[str, str] = {
    "record_created": "the record was saved",
    "validation_complete": "the record passed validation",
    "routing_resolved": "the system resolved who should be notified",
    "recipients_built": "the recipient list was finalized",
    "notification_queued": "the email was queued for delivery",
    "provider_accepted": "the email provider accepted the message",
    "audit_written": "the audit trail row was written",
    "dashboard_updated": "the operator dashboard was updated",
    "completed": "the workflow finished cleanly",
}

_SUBSYSTEM_LABELS = {
    "workflow_health":       "Workflow Lifecycle",
    "routing_integrity":     "Routing",
    "notification_delivery": "Notifications",
    "master_data":           "Master Data",
    "audit_integrity":       "Audit Trail",
    "infrastructure":        "Infrastructure",
    "security":              "Authentication",
}

_OTC_AUDIT_REFERENCE = "C2-R1-OPERATIONS-TRUST-CENTER"


def _normalized_claim(claim: Any) -> str:
    value = str(claim or "").upper()
    return value if claim_rank(value) >= 0 else UNKNOWN


def _lowest_claim(*claims: Any) -> str:
    normalized = [_normalized_claim(claim) for claim in claims]
    return min(normalized, key=claim_rank) if normalized else UNKNOWN


def _bounded_score_band_label(band: str) -> str:
    return {
        "green": "Green score band",
        "amber": "Amber score band",
        "red": "Red score band",
    }.get(band, "Derived score band")


def _owner_claim_from_payload(spine_payload: Dict[str, Any] | None) -> str:
    owner_ots = (spine_payload or {}).get("ots_truth") or {}
    direct_claim = _normalized_claim(owner_ots.get("permitted_claim"))
    if direct_claim != UNKNOWN:
        return direct_claim

    status = str((spine_payload or {}).get("canonical_status") or "").upper()
    return {
        "VERIFIED": CORRELATED,
        "DEGRADED": OBSERVED,
        "MISMATCH": CORRELATED,
    }.get(status, UNKNOWN)


def _load_trust_spine_payload(db):
    from routes.admin_trust_spine import make_router as _spine_router  # noqa: PLC0415

    spine_router = _spine_router(db, lambda: None)
    return next(
        r.endpoint for r in spine_router.routes
        if getattr(r, "path", "") == "/api/admin/trust-spine"
    )


def _build_otc_ots_projection(
    *,
    now_iso: str,
    spine_payload: Dict[str, Any] | None,
    owner_load_error: str | None,
    cat: Dict[str, Any],
    summary: Dict[str, Any],
    critical_problems: List[Dict[str, Any]],
    actions: List[Dict[str, Any]],
    trend: List[Dict[str, Any]],
    data_flags: Dict[str, bool],
) -> Dict[str, Any]:
    owner_ots = (spine_payload or {}).get("ots_truth") or {}
    owner_claim = _owner_claim_from_payload(spine_payload)
    owner_truth_eval = str(owner_ots.get("truth_evaluation") or "UNVERIFIABLE").upper()
    owner_unknowns = list(owner_ots.get("unknowns") or [])
    owner_contradictions = list(owner_ots.get("contradictory_evidence") or [])
    owner_audit_reference = owner_ots.get("audit_reference") or None

    unknowns: List[str] = []
    contradictions: List[str] = []
    degradation_reasons: List[str] = []
    claim_basis: List[str] = [
        "trust_spine_owner_truth",
        "master_data_findings",
        "email_routing_audit_v2",
        "trust_spine_events",
        "trust_score_history",
        "red_alert_state",
        "derived_operational_score",
    ]

    if owner_load_error:
        unknowns.append("Trust Spine owner truth could not be loaded, so the derived claim cannot be advanced beyond UNKNOWN.")
        degradation_reasons.append("Canonical owner truth was unavailable during the current evaluation.")
    if owner_claim == UNKNOWN:
        unknowns.append("Canonical owner claim is unavailable or malformed in the current Trust Spine response.")
    if not owner_audit_reference:
        unknowns.append("Canonical owner audit reference was unavailable in the current Trust Spine response.")
    if owner_unknowns:
        unknowns.append("Trust Spine reported unresolved lifecycle evidence gaps that still bound this derived surface.")
    contradictions.extend(owner_contradictions)

    if not data_flags.get("master_data_available", True):
        unknowns.append("Master-data evaluation was unavailable, so the score cannot stand as complete evidence.")
        degradation_reasons.append("Master-data trust findings were unavailable during evaluation.")
    if not data_flags.get("audit_available", True):
        unknowns.append("Audit integrity counts were unavailable, so missing audit evidence cannot be ruled out.")
        degradation_reasons.append("Audit evidence availability was partial during evaluation.")
    if not data_flags.get("notification_available", True):
        unknowns.append("Notification delivery counts were unavailable, so delivery health remains incomplete.")
        degradation_reasons.append("Notification evidence availability was partial during evaluation.")
    if not trend:
        unknowns.append("Trend history has not accumulated enough stored snapshots yet.")
    if summary.get("workflows_idle", 0) > 0:
        unknowns.append("One or more workflows were idle in the current window; missing activity is not proof of health.")
    if summary.get("unknown_audit_count_24h", 0) > 0:
        contradictions.append(
            f"Audit integrity observed {summary.get('unknown_audit_count_24h', 0)} unsupported audit status event(s)."
        )
    if summary.get("silent_failure_count_24h", 0) > 0:
        contradictions.append(
            f"{summary.get('silent_failure_count_24h', 0)} failed Trust Spine event(s) lacked remediation detail in the current window."
        )
    if cat.get("score_band") == "green" and owner_claim in {UNKNOWN, OBSERVED}:
        contradictions.append(
            f"Derived operational score is green while Trust Spine supports only {owner_claim} owner truth."
        )
    if cat.get("score_band") == "green" and critical_problems:
        contradictions.append("Derived operational score is green while critical operational problems are still present.")
    if not actions and critical_problems:
        contradictions.append("No derived operator actions were produced even though critical operational problems are present.")
    if owner_truth_eval == "MISMATCH":
        contradictions.append("Trust Spine owner truth is already contradicted, so this derived surface cannot present a stronger trust claim.")

    if owner_load_error or owner_claim == UNKNOWN:
        evidence_state = "owner_unavailable"
        evidence_quality = "UNAVAILABLE"
        evidence_confidence = "UNKNOWN"
        truth_evaluation = "UNVERIFIABLE"
        local_claim = UNKNOWN
    elif contradictions:
        evidence_state = "contradicted"
        evidence_quality = "CORRELATED"
        evidence_confidence = "LOW"
        truth_evaluation = "MISMATCH"
        local_claim = OBSERVED
    elif any(not data_flags.get(flag, True) for flag in ("master_data_available", "audit_available", "notification_available")) or summary.get("workflows_idle", 0) > 0:
        evidence_state = "partial"
        evidence_quality = "DURABLE_OBSERVED"
        evidence_confidence = "LOW"
        truth_evaluation = "DEGRADED"
        local_claim = OBSERVED
    else:
        evidence_state = "correlated"
        evidence_quality = "CORRELATED"
        evidence_confidence = "MEDIUM"
        truth_evaluation = "VERIFIED"
        local_claim = CORRELATED

    permitted_claim = _lowest_claim(owner_claim, local_claim, CORRELATED)

    truth_card = canonical_truth_card(
        truth_subject="shared_operational_trust_score",
        canonical_owner="trust_spine",
        truth_surface_id="operations_trust_center",
        evidence_state=evidence_state,
        evidence_quality=evidence_quality,
        evidence_confidence=evidence_confidence,
        truth_evaluation=truth_evaluation,
        permitted_claim=permitted_claim,
        claim_ceiling=CORRELATED,
        claim_basis=claim_basis,
        prohibited_claims=[
            "CERTIFIED",
            "validated platform trust",
            "deployment readiness",
            "production readiness",
            "canonical owner truth",
            "platform certification",
        ],
        degradation_reasons=sorted(set(degradation_reasons)),
        unknowns=sorted(set(unknowns)),
        contradictory_evidence=sorted(set(contradictions)),
        evidence_timestamp=owner_ots.get("evidence_timestamp") or summary.get("last_success_at") or now_iso,
        evaluation_timestamp=now_iso,
        audit_reference=_OTC_AUDIT_REFERENCE,
        evidence_required_to_raise_claim=[
            "Trust Spine owner truth with a higher supported claim in the current window",
            "complete master-data, routing, audit, and notification evidence without contradictions",
            "separate certification or deploy-readiness evidence outside this derived consumer scope",
        ],
        notes=[
            "Operations Trust Center is a derived consumer only.",
            "Operational score, trend, and narrative remain operator summaries and may never replace Trust Spine owner truth.",
        ],
    )
    return {
        "ots_truth": public_ots_projection(truth_card),
        "truth_relationship": projected_truth_relationship(
            surface_id="operations_trust_center",
            card=truth_card,
            canonical_owner_route="/api/admin/trust-spine",
            derivation_explanation="Operations Trust Center is a derived operational summary over Trust Spine and supporting evidence. It may narrow claims when evidence is incomplete or contradictory, but it may never upgrade, certify, or replace canonical owner truth.",
            derived_status=truth_card["truth_evaluation"],
        ),
        "compatibility": compatibility_projection(
            preserved_fields=25,
            deprecated_fields=0,
            new_fields=2,
            alias_fields=[],
            breaking_changes=0,
        ),
    }


def _workflow_label(wf: str) -> str:
    return _WORKFLOW_LABELS.get(wf, wf.replace("-", " ").title())


def _humanize_workflow_row(row: Dict[str, Any]) -> Dict[str, Any]:
    label = _workflow_label(row.get("workflow") or "")
    band = row.get("band")
    out = dict(row)
    out["workflow_label"] = label
    out["band_label"] = {
        "green": "Current evidence complete",
        "amber": "Missing evidence",
        "amber-no-activity": "No activity 24h",
        "red": "Contradiction detected",
    }.get(band, band)
    if band == "red":
        lf = row.get("last_failure") or {}
        fr = lf.get("failure_reason") or ""
        stage = lf.get("stage") or row.get("failure_stage") or ""
        stage_human = _STAGE_LABELS.get(stage, stage)
        out["operator_summary"] = (
            f"{label} saved, but {stage_human} did not complete: {fr}"
            if stage_human else
            f"{label} failed: {fr or 'see drill-in for details'}"
        )
        out["operator_remediation"] = (
            lf.get("remediation")
            or row.get("remediation")
            or f"Open the {label} drill-in for the failing record_id and "
               "inspect backend logs for that correlation_id."
        )
    elif band == "amber":
        missing = row.get("missing_stages") or []
        miss_label = ", ".join(
            _STAGE_LABELS.get(s, s) for s in missing[:3]
        ) or "one or more lifecycle stages"
        out["operator_summary"] = (
            f"{label} has recent activity but {miss_label} did not "
            "complete on every record."
        )
        out["operator_remediation"] = (
            row.get("remediation")
            or "Submit a new record for this workflow and verify the "
               "drill-in shows every expected stage as ok."
        )
    elif band == "amber-no-activity":
        out["operator_summary"] = (
            f"{label} has not been submitted in the last 24 hours, so "
            "the platform cannot prove it is currently healthy."
        )
        out["operator_remediation"] = (
            "If this workflow is expected to be in daily use, ask the "
            f"field to submit a {label} so the platform can collect fresh "
            "evidence."
        )
    else:
        out["operator_summary"] = (
            f"{label} has complete recent lifecycle evidence for this workflow in the last 24h."
        )
        out["operator_remediation"] = None
    return out


def _build_operator_actions(
    workflows: List[Dict[str, Any]],
    findings: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Sorted prioritized fix-it list. Critical first, then warnings,
    then cleanup. Each item carries an estimated time + impact."""
    actions: List[Dict[str, Any]] = []
    # Critical findings first.
    for f in findings:
        if f.get("severity") == "critical":
            actions.append({
                "id": f["code"],
                "priority": "critical",
                "title": f["summary"],
                "remediation": f["remediation"],
                "remediation_link": f.get("remediation_link") or "/admin",
                "estimated_remediation_seconds": f.get(
                    "estimated_remediation_seconds", 60
                ),
                "impact": f.get("impact") or "Restores production routing.",
                "samples": f.get("samples", [])[:5],
            })
    # Failing workflows (each one)
    for w in workflows:
        if w.get("band") == "red":
            lf = w.get("last_failure") or {}
            actions.append({
                "id": f"workflow_red:{w.get('workflow')}",
                "priority": "critical",
                "title": (
                    f"{_workflow_label(w.get('workflow') or '')} "
                    "workflow is failing"
                ),
                "remediation": (
                    lf.get("remediation")
                    or "Open the workflow drill-in for the failing record."
                ),
                "remediation_link": "/admin/email",
                "estimated_remediation_seconds": 300,
                "impact": (
                    f"Restores {_workflow_label(w.get('workflow') or '')} "
                    "notifications and audit evidence."
                ),
                "samples": [lf.get("record_id")] if lf.get("record_id") else [],
            })
    # Warnings.
    for f in findings:
        if f.get("severity") == "warning":
            actions.append({
                "id": f["code"],
                "priority": "warning",
                "title": f["summary"],
                "remediation": f["remediation"],
                "remediation_link": f.get("remediation_link") or "/admin",
                "estimated_remediation_seconds": f.get(
                    "estimated_remediation_seconds", 120
                ),
                "impact": f.get("impact") or "Reduces drift risk.",
                "samples": f.get("samples", [])[:5],
            })
    # Cleanup (lowest priority).
    for f in findings:
        if f.get("severity") == "cleanup":
            actions.append({
                "id": f["code"],
                "priority": "cleanup",
                "title": f["summary"],
                "remediation": f["remediation"],
                "remediation_link": f.get("remediation_link") or "/admin",
                "estimated_remediation_seconds": f.get(
                    "estimated_remediation_seconds", 600
                ),
                "impact": f.get("impact") or "Data hygiene only.",
                "samples": f.get("samples", [])[:5],
            })
    return actions


def _build_subsystem_cards(
    categories: Dict[str, Any],
    workflows: List[Dict[str, Any]],
    findings: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """One compact health card per subsystem — used by the dashboard's
    summary row. Pulls last_success/last_failure from the workflows
    + findings already collected so we do not re-query the DB."""
    out: List[Dict[str, Any]] = []
    for key, label in _SUBSYSTEM_LABELS.items():
        cat = categories.get(key, {})
        out.append({
            "id": key,
            "label": label,
            "score": cat.get("score", 100),
            "band": cat.get("band", "green"),
            "headline": (
                cat.get("inputs", [{}])[0].get("label", "")
                if cat.get("inputs") else "No current penalty surfaced"
            ),
            "operator_action": (
                cat.get("inputs", [{}])[0].get("label", "")
                if cat.get("inputs") else None
            ),
        })
    return out


def _executive_narrative(
    *,
    score: int,
    band: str,
    categories: Dict[str, Any],
    workflows: List[Dict[str, Any]],
    findings: List[Dict[str, Any]],
    eta_seconds: int,
) -> str:
    """Two-sentence operator summary."""
    red_wf = [w for w in workflows if w.get("band") == "red"]
    critical_findings = [f for f in findings if f.get("severity") == "critical"]
    parts: List[str] = []
    if band == "green":
        parts.append("Derived operational score is in the green band.")
    elif band == "amber":
        parts.append("Derived operational score is in the amber band because evidence or conditions are degraded.")
    else:
        parts.append("Derived operational score is in the red band because critical operational problems or contradictions are present.")

    if red_wf:
        parts.append(
            f"{len(red_wf)} workflow(s) currently failing "
            f"({', '.join(_workflow_label(w.get('workflow') or '') for w in red_wf[:3])})."
        )
    if critical_findings:
        # Use the most-impactful single finding.
        f = critical_findings[0]
        parts.append(f["summary"])
    if eta_seconds:
        mins = max(1, round(eta_seconds / 60))
        parts.append(f"Estimated remediation time: ~{mins} minute(s).")
    if band == "green":
        parts.append("No immediate derived action is surfaced by the current scoring model.")
    return " ".join(parts)


def make_router(db, require_admin_only_dep) -> APIRouter:
    router = APIRouter()
    allowed_audit_statuses = sorted(normalized_allowed_email_audit_statuses())
    failure_statuses = sorted(normalized_failure_statuses())
    notification_attempt_statuses = sorted(normalized_notification_attempt_statuses())

    @router.get("/api/admin/operations-trust-center")
    async def operations_trust_center(
        trend_hours: int = 24,
        _: Any = Depends(require_admin_only_dep),
    ) -> Dict[str, Any]:
        await _hist_ensure(db)
        trend_hours = max(1, min(int(trend_hours or 24), 720))
        now_iso = datetime.now(timezone.utc).isoformat()

        # 1) Workflow rollup (reuse existing spine aggregator).
        owner_load_error = None
        spine_payload: Dict[str, Any] | None = None
        try:
            spine_handler = _load_trust_spine_payload(db)
            spine_result = spine_handler(_=None)
            spine_payload = await spine_result if isawaitable(spine_result) else spine_result
        except Exception as exc:  # noqa: BLE001
            owner_load_error = str(exc)[:180]
            spine_payload = {}
        workflows: List[Dict[str, Any]] = list((spine_payload or {}).get("workflows", []))
        humanized = [_humanize_workflow_row(w) for w in workflows]

        # 2) Master data.
        master_data_available = True
        try:
            findings = await collect_findings(db)
        except Exception:
            findings = []
            master_data_available = False
        md_band = overall_band(findings)

        # 3) Audit health.
        since_iso = _since_24h_iso()
        audit_available = True
        try:
            unknown_audit = await db.email_routing_audit_v2.count_documents({
                "ts": {"$gte": since_iso},
                "status": {"$nin": allowed_audit_statuses},
            })
        except Exception:
            unknown_audit = 0
            audit_available = False
        try:
            silent_failures = await db.trust_spine_events.count_documents({
                "ts": {"$gte": since_iso},
                "status": "failed",
                "$or": [
                    {"remediation": None}, {"remediation": ""},
                    {"remediation": {"$exists": False}},
                ],
            })
        except Exception:
            silent_failures = 0
            audit_available = False

        # 4) Notification delivery 24h.
        notification_available = True
        try:
            notif_total = await db.email_routing_audit_v2.count_documents({
                "ts": {"$gte": since_iso},
                "status": {"$in": notification_attempt_statuses},
            })
            notif_failed = await db.email_routing_audit_v2.count_documents({
                "ts": {"$gte": since_iso}, "status": {"$in": failure_statuses},
            })
        except Exception:
            notif_total = notif_failed = 0
            notification_available = False

        # 5) Categorized score.
        missing_route_count = sum(
            1 for f in findings if f.get("code") == "critical_route_missing"
        )
        cat = compute_categorized_score(
            workflows=workflows,
            master_data_findings=findings,
            unknown_audit_count_24h=unknown_audit,
            silent_failure_count_24h=silent_failures,
            missing_critical_routes=missing_route_count,
            notification_failed_24h=notif_failed,
            notification_total_24h=notif_total,
        )

        # 6) Legacy flat score (kept for 15.76A backward-compat tests).
        legacy = compute_score(
            workflows=workflows,
            master_data_findings=findings,
            unknown_audit_count_24h=unknown_audit,
            silent_failure_count_24h=silent_failures,
            missing_critical_routes=[
                f["summary"] for f in findings
                if f.get("code") == "critical_route_missing"
            ],
        )

        # 7) Build summary, action panel, narrative.
        last_success_at = None
        last_failure_at = None
        for w in workflows:
            ls = (w.get("last_success") or {}).get("ts")
            lf = (w.get("last_failure") or {}).get("ts")
            if ls and (not last_success_at or ls > last_success_at):
                last_success_at = ls
            if lf and (not last_failure_at or lf > last_failure_at):
                last_failure_at = lf

        summary = {
            "platform_band": spine_payload.get("platform_band"),
            "workflow_count": spine_payload.get("workflow_count"),
            "workflows_trusted": sum(1 for w in workflows if w["band"] == "green"),
            "workflows_amber": sum(1 for w in workflows if w["band"] == "amber"),
            "workflows_idle": sum(1 for w in workflows if w["band"] == "amber-no-activity"),
            "workflows_red": sum(1 for w in workflows if w["band"] == "red"),
            "events_24h": spine_payload.get("total_events_24h", 0),
            "failed_24h": spine_payload.get("total_failed_24h", 0),
            "last_success_at": last_success_at,
            "last_failure_at": last_failure_at,
            "master_data_band": md_band,
            "master_data_findings_count": len(findings),
            "unknown_audit_count_24h": unknown_audit,
            "silent_failure_count_24h": silent_failures,
            "notification_failed_24h": notif_failed,
            "notification_total_24h": notif_total,
        }

        critical_problems = [
            f for f in findings if f.get("severity") == "critical"
        ]
        cleanup_opportunities = [
            f for f in findings if f.get("severity") == "cleanup"
        ]
        operational_warnings = [
            f for f in findings
            if f.get("severity") not in ("critical", "cleanup")
        ]
        actions = _build_operator_actions(workflows, findings)
        eta_seconds = sum(
            a.get("estimated_remediation_seconds", 0)
            for a in actions if a.get("priority") == "critical"
        )
        subsystems = _build_subsystem_cards(
            cat["categories"], workflows, findings
        )
        narrative = _executive_narrative(
            score=cat["trust_score"],
            band=cat["score_band"],
            categories=cat["categories"],
            workflows=workflows,
            findings=findings,
            eta_seconds=eta_seconds,
        )

        # 8) Persist trend snapshot (de-duped by minute).
        await write_snapshot(
            db,
            score=cat["trust_score"],
            band=cat["score_band"],
            categories=cat["categories"],
            summary=summary,
        )
        trend_result = read_trend(db, window_hours=trend_hours)
        trend = await trend_result if isawaitable(trend_result) else trend_result

        # 9) Red alert hook — fire only on RED transitions.
        trust_center_url = (
            os.environ.get("PUBLIC_APP_URL", "") or "https://mascidocs.com"
        ) + "/admin/email"
        alert_result = await red_alert.maybe_send(
            db,
            current_band=cat["score_band"],
            score=cat["trust_score"],
            score_reason=cat["score_reason"],
            workflows=workflows,
            trust_center_url=trust_center_url,
        )

        ots_projection = _build_otc_ots_projection(
            now_iso=now_iso,
            spine_payload=spine_payload,
            owner_load_error=owner_load_error,
            cat=cat,
            summary=summary,
            critical_problems=critical_problems,
            actions=actions,
            trend=trend,
            data_flags={
                "master_data_available": master_data_available,
                "audit_available": audit_available,
                "notification_available": notification_available,
            },
        )

        return {
            "track": "15.76B",
            "generated_at": now_iso,
            "truth_surface": canonical_truth_surface("operations_trust_center"),
            "truth_relationship": ots_projection["truth_relationship"],
            "ots_truth": ots_projection["ots_truth"],
            "compatibility": ots_projection["compatibility"],
            # Flat fields (15.76A compatibility).
            "trust_score": cat["trust_score"],
            "score_band": cat["score_band"],
            "score_band_label": _bounded_score_band_label(cat["score_band"]),
            "score_reason": cat["score_reason"],
            "score_inputs": cat["score_inputs"],
            # New categorized + sections.
            "categories": cat["categories"],
            "category_weights": CATEGORY_WEIGHTS,
            "critical_problems": critical_problems,
            "operational_warnings": operational_warnings,
            "cleanup_opportunities": cleanup_opportunities,
            "operator_actions": actions,
            "subsystems": subsystems,
            "trend": trend,
            "trend_hours": trend_hours,
            "executive_narrative": narrative,
            "estimated_remediation_seconds": eta_seconds,
            # Existing keys preserved.
            "summary": summary,
            "workflows": humanized,
            "master_data": {"band": md_band, "findings": findings},
            "red_alert": alert_result,
            # Backward-compat: legacy flat score under a sub-key.
            "legacy_flat_score": legacy["trust_score"],
        }

    @router.post("/api/admin/operations-trust-center/test-alert")
    async def test_alert(
        _: Any = Depends(require_admin_only_dep),
    ) -> Dict[str, Any]:
        from routes.admin_trust_spine import make_router as _spine_router  # noqa: PLC0415
        spine = _spine_router(db, lambda: None)
        handler = next(
            r.endpoint for r in spine.routes
            if getattr(r, "path", "") == "/api/admin/trust-spine"
        )
        spine_payload = await handler(_=None)
        return await red_alert.maybe_send(
            db,
            current_band="red",
            score=0,
            score_reason="manual test alert",
            workflows=spine_payload.get("workflows", []),
            trust_center_url=(
                os.environ.get("PUBLIC_APP_URL", "")
                or "https://mascidocs.com"
            ) + "/admin/email",
            dry_run=True,
        )

    return router


def _since_24h_iso() -> str:
    from datetime import datetime as _dt, timedelta, timezone as _tz  # noqa: PLC0415
    return (_dt.now(_tz.utc) - timedelta(hours=24)).isoformat()


__all__ = [
    "make_router", "_humanize_workflow_row",
    "_build_operator_actions", "_executive_narrative",
]
