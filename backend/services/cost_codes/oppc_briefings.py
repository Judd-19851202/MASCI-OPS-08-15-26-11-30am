from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from io import BytesIO
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from services.cost_codes.foundation import load_project_confidence_history, load_project_forecast_history, now_iso
from services.cost_codes.oppc_confidence import summarize_confidence_portfolio
from services.cost_codes.oppc_confidence_data import build_project_confidence_payload
from services.cost_codes.oppc_execution import build_project_execution_workspace
from services.cost_codes.oppc_intelligence import build_executive_operations_center


BRIEFINGS_COLL = "oppc_monday_briefings"


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _hash(payload: Dict[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


async def ensure_monday_briefing_indexes(db) -> None:
    try:
        await db[BRIEFINGS_COLL].create_index(
            [("scope_type", 1), ("scope_key", 1), ("week_ending", 1)],
            unique=True,
            name="oppc_monday_briefing_scope_week_idx",
        )
    except Exception:
        return


async def load_monday_briefing_doc(db, *, scope_type: str, scope_key: str, week_ending: str) -> Dict[str, Any]:
    doc = await db[BRIEFINGS_COLL].find_one(
        {"scope_type": scope_type, "scope_key": scope_key, "week_ending": week_ending},
        {"_id": 0},
    )
    return dict(doc or {})


async def persist_monday_briefing_doc(db, doc: Dict[str, Any]) -> Dict[str, Any]:
    payload = dict(doc or {})
    payload["updated_at"] = now_iso()
    await db[BRIEFINGS_COLL].update_one(
        {
            "scope_type": payload.get("scope_type"),
            "scope_key": payload.get("scope_key"),
            "week_ending": payload.get("week_ending"),
        },
        {"$set": payload},
        upsert=True,
    )
    return payload


def _status_payload(existing: Dict[str, Any], *, actor_label: str, status: str, note: str = "") -> Dict[str, Any]:
    history = list(existing.get("approval_history") or [])
    history.append({
        "status": status,
        "at": now_iso(),
        "by": actor_label,
        "note": _clean(note),
    })
    return {
        "status": status,
        "approval_history": history,
    }


def _project_freshness(workspace: Dict[str, Any], confidence: Dict[str, Any]) -> Dict[str, Any]:
    latest_report_date = _clean((workspace.get("production_summary") or {}).get("latest_report_date"))
    payroll_complete = bool((workspace.get("payroll_summary") or {}).get("complete"))
    return {
        "latest_report_date": latest_report_date,
        "payroll_complete": payroll_complete,
        "report_freshness": _clean((confidence.get("freshness") or {}).get("report_freshness")) or "missing",
        "warnings": sorted(set((workspace.get("monday_review") or {}).get("warnings") or []) | set(confidence.get("warnings") or [])),
    }


async def build_project_monday_briefing(db, *, project_number: str, week_ending: str, actor_label: str) -> Dict[str, Any]:
    workspace = await build_project_execution_workspace(db, project_number, week_ending)
    job = await db.jobs_master.find_one({"project_number": project_number}, {"_id": 0}) or {}
    confidence = await build_project_confidence_payload(db, job)
    forecast_history = await load_project_forecast_history(db, project_number)
    confidence_history = await load_project_confidence_history(db, project_number)
    freshness = _project_freshness(workspace, confidence)
    schedule = workspace.get("schedule") or {}
    monday = workspace.get("monday_review") or {}
    summary_lines = [
        f"Health status: {(workspace.get('project_health') or {}).get('status') or 'UNKNOWN'}.",
        f"Confidence score: {confidence.get('score')} ({str(confidence.get('band') or '').replace('_', ' ')}).",
        f"Projected finish: {schedule.get('projected_finish_date') or '—'} · committed finish: {schedule.get('committed_finish_date') or '—'}.",
        f"Open variances: {monday.get('open_variances') or 0} · outstanding recovery: {monday.get('outstanding_recovery') or 0}.",
    ]
    actions = list((workspace.get("monday_review") or {}).get("workspace", {}).get("executive_actions") or [])
    doc = {
        "doc_type": "oppc_monday_morning_briefing",
        "version": 1,
        "scope_type": "project",
        "scope_key": project_number,
        "project_number": project_number,
        "project_name": job.get("project_name") or job.get("name") or project_number,
        "week_ending": week_ending,
        "status": "draft",
        "generated_at": now_iso(),
        "generated_by": actor_label,
        "frozen": False,
        "freshness": freshness,
        "summary_lines": summary_lines,
        "warnings": freshness.get("warnings") or [],
        "sections": {
            "forecast": {
                "projected_finish_date": schedule.get("projected_finish_date") or "",
                "committed_finish_date": schedule.get("committed_finish_date") or "",
                "critical_path": list(schedule.get("critical_path") or []),
                "hardening_summary": dict(schedule.get("hardening_summary") or {}),
                "forecast_snapshot_count": len(forecast_history.get("snapshots") or []),
            },
            "confidence": {
                "score": confidence.get("score"),
                "band": confidence.get("band"),
                "components": list(confidence.get("components") or []),
                "confidence_snapshot_count": len(confidence_history.get("snapshots") or []),
                "explainability": list(confidence.get("explainability") or []),
            },
            "production": dict(workspace.get("production_summary") or {}),
            "payroll": dict(workspace.get("payroll_summary") or {}),
            "variances": dict((workspace.get("variance_intelligence") or {}).get("summary") or {}),
            "monday_review": {
                "completion_percent": monday.get("completion_percent"),
                "blocking_items": list(monday.get("blocking_items") or []),
                "critical_path_changes": list(monday.get("critical_path_changes") or []),
                "executive_actions": actions,
            },
        },
        "explainability": {
            "truth_basis": "canonical_operational_data",
            "sources": [
                "jobs_master.assigned_cost_codes",
                "daily_reports.cost_code_quantities",
                "payroll_variance_batches",
                "operational_variance_reviews",
                "trust_spine_events",
            ],
            "logic": [
                "Schedule forecast uses the existing deterministic schedule engine.",
                "Confidence score uses the shared oppc_confidence engine.",
                "Briefing warnings surface stale or missing source data without replacing the calculated result.",
            ],
        },
        "approval_history": [],
    }
    doc["content_hash"] = _hash({"scope_type": doc["scope_type"], "scope_key": doc["scope_key"], "week_ending": doc["week_ending"], "sections": doc["sections"], "warnings": doc["warnings"]})
    return doc


async def build_enterprise_monday_briefing(db, *, week_ending: str, actor_label: str) -> Dict[str, Any]:
    operations = await build_executive_operations_center(db, week_ending)
    jobs = [row async for row in db.jobs_master.find({"project_number": {"$ne": ""}}, {"_id": 0})]
    confidence_rows = []
    for job in jobs:
        confidence_rows.append({
            "project_number": job.get("project_number"),
            "project_name": job.get("project_name") or job.get("name") or job.get("project_number"),
            "production_confidence": await build_project_confidence_payload(db, job),
        })
    confidence_rows.sort(key=lambda row: float((row.get("production_confidence") or {}).get("score") or 0.0))
    confidence_summary = summarize_confidence_portfolio(confidence_rows)
    at_risk = confidence_rows[:5]
    warnings: List[str] = []
    for row in at_risk:
        warnings.extend((row.get("production_confidence") or {}).get("warnings") or [])
    doc = {
        "doc_type": "oppc_monday_morning_briefing",
        "version": 1,
        "scope_type": "enterprise",
        "scope_key": "enterprise",
        "week_ending": week_ending,
        "status": "draft",
        "generated_at": now_iso(),
        "generated_by": actor_label,
        "frozen": False,
        "summary_lines": [
            f"Leadership projects: {(operations.get('summary') or {}).get('leadership_projects') or 0}.",
            f"Open variances: {(operations.get('summary') or {}).get('open_variances') or 0}.",
            f"Resource conflicts: {(operations.get('summary') or {}).get('resource_conflicts') or 0}.",
            f"Average production confidence: {confidence_summary.get('average_score') or 0}.",
        ],
        "warnings": sorted(set(warnings)),
        "freshness": {
            "generated_at": now_iso(),
            "warning_count": len(set(warnings)),
        },
        "sections": {
            "portfolio_summary": dict(operations.get("summary") or {}),
            "portfolio_projects": list(operations.get("projects") or []),
            "confidence_summary": confidence_summary,
            "at_risk_projects": at_risk,
        },
        "explainability": {
            "truth_basis": "canonical_operational_data",
            "sources": [
                "oppc executive operations center",
                "shared oppc_confidence engine",
            ],
            "logic": [
                "Enterprise briefing is an executive rollup of shared project workspaces and confidence calculations.",
                "No manual briefing-only data replaces the approved schedule or health record.",
            ],
        },
        "approval_history": [],
    }
    doc["content_hash"] = _hash({"scope_type": doc["scope_type"], "week_ending": doc["week_ending"], "sections": doc["sections"], "warnings": doc["warnings"]})
    return doc


def freeze_briefing(doc: Dict[str, Any], *, actor_label: str, note: str = "") -> Dict[str, Any]:
    payload = dict(doc or {})
    payload.update(_status_payload(payload, actor_label=actor_label, status="frozen", note=note))
    payload["frozen"] = True
    payload["frozen_at"] = now_iso()
    payload["frozen_by"] = actor_label
    payload["content_hash"] = _hash({"sections": payload.get("sections") or {}, "warnings": payload.get("warnings") or []})
    return payload


def approve_briefing(doc: Dict[str, Any], *, actor_label: str, note: str = "") -> Dict[str, Any]:
    payload = dict(doc or {})
    payload.update(_status_payload(payload, actor_label=actor_label, status="approved", note=note))
    payload["approved_at"] = now_iso()
    payload["approved_by"] = actor_label
    return payload


def render_monday_briefing_pdf(doc: Dict[str, Any]) -> bytes:
    buf = BytesIO()
    pdf = SimpleDocTemplate(buf, pagesize=letter, leftMargin=32, rightMargin=32, topMargin=36, bottomMargin=32)
    styles = getSampleStyleSheet()
    flow = [
        Paragraph(f"<b>Monday Morning Briefing — {(_clean(doc.get('scope_key')) or _clean(doc.get('project_number')) or 'Enterprise').upper()}</b>", styles["Title"]),
        Paragraph(f"Week ending: {_clean(doc.get('week_ending')) or '—'}", styles["Normal"]),
        Paragraph(f"Status: {_clean(doc.get('status')) or 'draft'}", styles["Normal"]),
        Spacer(1, 8),
    ]
    for line in (doc.get("summary_lines") or []):
        flow.append(Paragraph(line, styles["BodyText"]))
        flow.append(Spacer(1, 4))
    flow.append(Spacer(1, 8))
    table_rows = [["Section", "Key facts"]]
    for key, value in (doc.get("sections") or {}).items():
        if isinstance(value, dict):
            text = "; ".join(f"{k}: {v}" for k, v in list(value.items())[:5])
        elif isinstance(value, list):
            text = f"{len(value)} items"
        else:
            text = _clean(value)
        table_rows.append([key.replace("_", " ").title(), text[:250]])
    table = Table(table_rows, colWidths=[150, 360])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
    ]))
    flow.append(table)
    if doc.get("warnings"):
        flow.append(Spacer(1, 10))
        flow.append(Paragraph("<b>Warnings</b>", styles["Heading3"]))
        for warning in doc.get("warnings")[:12]:
            flow.append(Paragraph(f"• {_clean(warning)}", styles["BodyText"]))
    pdf.build(flow)
    return buf.getvalue()


__all__ = [
    "BRIEFINGS_COLL",
    "approve_briefing",
    "build_enterprise_monday_briefing",
    "build_project_monday_briefing",
    "ensure_monday_briefing_indexes",
    "freeze_briefing",
    "load_monday_briefing_doc",
    "persist_monday_briefing_doc",
    "render_monday_briefing_pdf",
]