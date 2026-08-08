from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request

from lib.canonical_truth import canonical_truth_surface, derived_truth_payload
from lib.operational_health_engine import (
    GOLDEN_PATH_MONITORS,
    aggregate_operational_status,
    build_status_engine_fixture_results,
    classify_golden_path_signal,
    count_statuses,
    normalize_operational_status,
)
from lib.wp17a_kpi_governance import standardize_prediction_metadata


_BACKEND_INTERNAL_BASE = os.environ.get("OCC_HEALTH_INTERNAL_BASE", "http://127.0.0.1:8001").rstrip("/")
_PROBE_TIMEOUT_S = 30.0
_WORKSPACE = Path("/app")
_SCANNER_PATH = _WORKSPACE / "backend/tools/wp15_governance_convergence_scan.py"
_CI_ASSERT_PATH = _WORKSPACE / "scripts/assert_wp15_governance_convergence.py"
_CI_PATH = _WORKSPACE / ".github/workflows/ci.yml"
_SIGMA3_PATH = _WORKSPACE / ".github/workflows/sigma3-deploy-gate.yml"
_ROUTER_FILE = _WORKSPACE / "frontend/src/app/routing/AppRoutes.jsx"
_DOMAIN_MAP_FILE = _WORKSPACE / "frontend/src/app/admin/domainMapV3.js"
_API_HELPER_FILE = _WORKSPACE / "frontend/src/lib/enterpriseGovernanceApi.js"
_PAGE_FILE = _WORKSPACE / "frontend/src/pages/admin/AdminGovernanceOperatingSystem.jsx"

_DOC_FILES = {
    "architecture_freeze": _WORKSPACE / "WP15_ARCHITECTURE_FREEZE.md",
    "enterprise_health": _WORKSPACE / "ENTERPRISE_GOVERNANCE_HEALTH.md",
    "continuous_certification": _WORKSPACE / "WP15_CONTINUOUS_CERTIFICATION.md",
    "dashboard_standard": _WORKSPACE / "WP15_GOVERNANCE_DASHBOARD.md",
    "constitutional_standard": _WORKSPACE / "WP15_CONSTITUTIONAL_GOVERNANCE_STANDARD.md",
    "final_certification": _WORKSPACE / "WP15_ENTERPRISE_GOVERNANCE_CERTIFICATION.md",
    "exemptions": _WORKSPACE / "WP15_CONSTITUTIONAL_EXEMPTIONS.md",
    "drift_report": _WORKSPACE / "WP15_AUTHORIZATION_DRIFT_REPORT.md",
}

_MODULE_CATALOG = [
    {"id": "enterprise-governance", "label": "Enterprise Governance", "route": "/admin/governance", "availability": "live"},
    {"id": "backup-disaster-recovery", "label": "Backup & Disaster Recovery", "route": "", "availability": "planned"},
    {"id": "trust-spine", "label": "Trust Spine", "route": "", "availability": "planned"},
    {"id": "operational-awareness", "label": "Operational Awareness", "route": "", "availability": "planned"},
    {"id": "scheduling", "label": "Scheduling", "route": "", "availability": "planned"},
    {"id": "academy", "label": "Academy", "route": "", "availability": "planned"},
    {"id": "operational-intelligence", "label": "Operational Intelligence", "route": "", "availability": "planned"},
]

_PROBE_PATHS = {
    "governance_registry": "/api/admin/governance/registry",
    "governance_versions": "/api/admin/governance/versions",
    "governance_decisions": "/api/admin/governance/decisions",
    "governance_overrides": "/api/admin/governance/emergency-overrides",
    "governance_approval_flows": "/api/admin/governance/approval-flows",
    "governance_identities": "/api/admin/governance/identities",
    "sessions_recent": "/api/admin/sessions/recent",
    "trust_spine": "/api/admin/trust-spine",
    "production_certification": "/api/admin/production-certification",
    "platform_truth_integrity": "/api/admin/platform-truth-integrity",
    "occ_trust_events": "/api/admin/occ/trust-events?limit=25",
}

_SECTION_DEFS = [
    ("constitutional-status", "Constitutional Status"),
    ("governance-drift", "Governance Drift"),
    ("certification-health", "Certification Health"),
    ("platform-truth-integrity", "Platform Truth Integrity"),
    ("trust-spine-integrity", "Trust Spine Integrity"),
    ("identity-health", "Identity Health"),
    ("authorization-health", "Authorization Health"),
    ("operator-experience", "Operator Experience"),
    ("constitutional-exemptions", "Constitutional Exemptions"),
]

_SNAPSHOT_COLLECTION = "operational_health_snapshots"
_CERTIFICATION_COLLECTION = "operational_health_certification_history"
_GOLDEN_PATH_COLLECTION = "operational_health_golden_path_runs"

_CONDITION_POLICY = {
    "live-certification-posture": {
        "owner": "Continuous Certification",
        "classification": "operational",
        "affects_certification": False,
        "operator_impact": "Operators see that some certified workflows are blocked, stale, or not yet exercised in the current window.",
        "production_impact": "No immediate constitutional defect, but release confidence is degraded until fresh workflow evidence is collected.",
        "calculation_rule": "AMBER when the certification engine reports blocked, stale, or not-yet-exercised workflows without a failed constitutional certification verdict.",
    },
    "trust-spine-band": {
        "owner": "Trust Spine / Operations Control",
        "classification": "operational",
        "affects_certification": False,
        "operator_impact": "Operators have live failing workflow evidence that requires investigation and remediation.",
        "production_impact": "Production and deploy readiness can be blocked while failing workflow evidence remains unresolved.",
        "calculation_rule": "RED when the Trust Spine platform band is red because one or more workflows emit validated failed lifecycle evidence.",
    },
    "trust-blockers": {
        "owner": "Deploy Readiness / Trust Spine",
        "classification": "operational",
        "affects_certification": False,
        "operator_impact": "Administrators see active unresolved blockers and must investigate before treating the estate as healthy.",
        "production_impact": "Production deployment gates remain blocked while unresolved blocker evidence exists.",
        "calculation_rule": "RED when unresolved blocker count is greater than zero in the unified trust-events feed.",
    },
    "override-approval-channels": {
        "owner": "Enterprise Governance Operations",
        "classification": "operational",
        "affects_certification": False,
        "operator_impact": "Governed approval or override requests may be waiting without required communications.",
        "production_impact": "Production is not constitutionally invalidated, but operator follow-up and auditability are degraded.",
        "calculation_rule": "AMBER when ack-required pending override or approval records exist without communication evidence; RED if communication errors exist.",
    },
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_iso_from_mtime(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()


def _forward_headers(request: Request) -> Dict[str, str]:
    headers: Dict[str, str] = {}
    for header in ("X-Admin-Token", "X-Directory-Token", "Authorization"):
        value = request.headers.get(header)
        if value:
            headers[header] = value
    return headers


async def _probe_json(client: httpx.AsyncClient, path: str, headers: Dict[str, str]) -> Dict[str, Any]:
    refreshed_at = _now_iso()
    try:
        response = await client.get(f"{_BACKEND_INTERNAL_BASE}{path}", headers=headers)
        if response.status_code >= 400:
            return {"ok": False, "path": path, "status_code": response.status_code, "error": f"HTTP {response.status_code}", "body": None, "refreshed_at": None}
        return {"ok": True, "path": path, "status_code": response.status_code, "error": None, "body": response.json(), "refreshed_at": refreshed_at}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "path": path, "status_code": 0, "error": f"{type(exc).__name__}: {exc}", "body": None, "refreshed_at": None}


def _status_rank(status: str) -> int:
    return {"red": 3, "yellow": 2, "unknown": 1, "green": 0}.get(normalize_operational_status(status), 1)


def _worst_status(cards: List[Dict[str, Any]]) -> str:
    if not cards:
        return "unknown"
    return aggregate_operational_status(card.get("status") for card in cards)


def _normalize_status(value: Any) -> str:
    return normalize_operational_status(value)


def _card(
    *,
    section_id: str,
    card_id: str,
    title: str,
    status: str,
    summary: str,
    root_cause_explanation: str,
    endpoint: str,
    evidence_source_label: str,
    producer: str,
    checked_at: Optional[str],
    last_successful_refresh: Optional[str],
    verified_at: Optional[str],
    affected_files: List[str],
    affected_modules: List[str],
    affected_workflows: List[str],
    recommended_action: str,
    evidence: Dict[str, Any],
    drilldown: str = "",
) -> Dict[str, Any]:
    return {
        "id": card_id,
        "section_id": section_id,
        "title": title,
        "status": status,
        "summary": summary,
        "root_cause_explanation": root_cause_explanation,
        "endpoint": endpoint,
        "evidence_source_label": evidence_source_label,
        "producer": producer,
        "checked_at": checked_at,
        "last_successful_refresh": last_successful_refresh,
        "verified_at": verified_at or checked_at,
        "affected_assets": {"files": affected_files, "modules": affected_modules, "workflows": affected_workflows},
        "recommended_action": recommended_action,
        "evidence": evidence,
        "drilldown": drilldown,
    }


def _read_text_artifact(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"exists": False, "path": str(path), "text": "", "modified_at": None}
    return {"exists": True, "path": str(path), "text": path.read_text(), "modified_at": _safe_iso_from_mtime(path)}


def _missing_headings(text: str, headings: List[str]) -> List[str]:
    hay = text.lower()
    return [heading for heading in headings if heading.lower() not in hay]


def _parse_exemption_reason_counts(text: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line.startswith("|"):
            continue
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) < 4:
            continue
        reason = parts[0]
        if reason.lower() in {"reason", "---"}:
            continue
        match = re.search(r"\d+", parts[1])
        if match:
            counts[reason] = int(match.group(0))
    return counts


def _parse_exemption_total(text: str) -> Optional[int]:
    match = re.search(r"special_case_infrastructure\s*=\s*(\d+)", text)
    return int(match.group(1)) if match else None


def _parse_certification_history_entries(text: str) -> int:
    return sum(1 for line in text.splitlines() if line.strip().startswith("| 2026-"))


def _run_scanner() -> Dict[str, Any]:
    try:
        raw = subprocess.check_output(["python3", str(_SCANNER_PATH)], text=True, cwd=str(_WORKSPACE))
        return {"ok": True, "body": json.loads(raw), "error": None, "refreshed_at": _now_iso()}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "body": None, "error": f"{type(exc).__name__}: {exc}", "refreshed_at": None}


def _workflow_gate_evidence() -> Dict[str, Any]:
    ci = _read_text_artifact(_CI_PATH)
    sigma = _read_text_artifact(_SIGMA3_PATH)
    assert_present = _CI_ASSERT_PATH.exists()
    scanner_token = "backend/tools/wp15_governance_convergence_scan.py"
    assert_token = "scripts/assert_wp15_governance_convergence.py"
    ci_text = ci["text"] if ci["exists"] else ""
    sigma_text = sigma["text"] if sigma["exists"] else ""
    gates = {
        "pull_request_validation": bool("pull_request:" in ci_text and scanner_token in ci_text and assert_token in ci_text),
        "nightly_build": bool("schedule:" in ci_text and scanner_token in ci_text and assert_token in ci_text),
        "release_candidate_certification": bool("canonical-release-gate" in ci_text and scanner_token in ci_text and assert_token in ci_text),
        "production_deployment_gate": bool(scanner_token in sigma_text and assert_token in sigma_text),
    }
    missing = [gate for gate, present in gates.items() if not present]
    modified = [stamp for stamp in [ci["modified_at"], sigma["modified_at"], _safe_iso_from_mtime(_CI_ASSERT_PATH)] if stamp]
    return {
        "status": "green" if not missing and assert_present else "red",
        "gates": gates,
        "missing": missing if assert_present else [*missing, "assert_script_missing"],
        "checked_at": max(modified) if modified else None,
        "files": [str(_CI_PATH), str(_SIGMA3_PATH), str(_CI_ASSERT_PATH)],
        "assert_script_present": assert_present,
    }


def _route_registration_evidence() -> Dict[str, Any]:
    router = _read_text_artifact(_ROUTER_FILE)
    domain_map = _read_text_artifact(_DOMAIN_MAP_FILE)
    api_helper = _read_text_artifact(_API_HELPER_FILE)
    page = _read_text_artifact(_PAGE_FILE)
    checks = {
        "app_route": "/admin/governance" in router["text"],
        "domain_map": "/admin/governance" in domain_map["text"],
        "api_helper": "fetchOperationalHealthModule" in api_helper["text"],
        "page_registered": "OperationalHealthDashboardShell" in page["text"],
    }
    modified = [stamp for stamp in [router["modified_at"], domain_map["modified_at"], api_helper["modified_at"], page["modified_at"]] if stamp]
    return {"status": "green" if all(checks.values()) else "red", "checks": checks, "missing": [name for name, passed in checks.items() if not passed], "checked_at": max(modified) if modified else None, "files": [str(_ROUTER_FILE), str(_DOMAIN_MAP_FILE), str(_API_HELPER_FILE), str(_PAGE_FILE)]}


def _build_document_evidence() -> Dict[str, Dict[str, Any]]:
    return {key: _read_text_artifact(path) for key, path in _DOC_FILES.items()}


def _latest_non_empty(rows: List[Dict[str, Any]], *keys: str) -> Optional[str]:
    values: List[str] = []
    for row in rows:
        for key in keys:
            value = str(row.get(key) or "").strip()
            if value:
                values.append(value)
    return max(values) if values else None


def _scanner_reason_counts(body: Dict[str, Any]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in body.get("constitutional_decision_points") or []:
        if row.get("category") != "special_case_infrastructure":
            continue
        reason = str(row.get("reason") or "unknown")
        counts[reason] = counts.get(reason, 0) + 1
    return counts


def _max_of(*values: Optional[str]) -> Optional[str]:
    items = [value for value in values if value]
    return max(items) if items else None


def _runtime_db(request: Optional[Request], db):
    state_db = getattr(getattr(getattr(request, "app", None), "state", None), "db", None)
    if state_db is not None:
        return state_db
    target = getattr(db, "get_target", lambda: None)()
    if target is not None:
        return target
    return db


def _current_commit_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True, cwd=str(_WORKSPACE)).strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def _parse_markdown_table_rows(text: str) -> List[List[str]]:
    rows: List[List[str]] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line.startswith("|"):
            continue
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) < 2 or parts[0].lower() in {"date", "---", "reason"}:
            continue
        rows.append(parts)
    return rows


def _build_constitutional_certification(docs: Dict[str, Dict[str, Any]], scanner: Dict[str, Any], generated_at: str) -> Dict[str, Any]:
    final_doc = docs["final_certification"]
    history_doc = docs["continuous_certification"]
    scanner_body = scanner.get("body") or {}
    final_text = (final_doc.get("text") or "").upper()
    certified = "VERIFIED" in final_text and "GO" in final_text
    state = "VERIFIED — GO" if certified else "WP-15 CERTIFICATION UNDER REVIEW"
    commit_sha = _current_commit_sha()
    return {
        "state": state,
        "certified_at": final_doc.get("modified_at") or history_doc.get("modified_at") or generated_at,
        "commit_sha": commit_sha,
        "environment": "preview",
        "evidence_package": str(_DOC_FILES["final_certification"]),
        "history_reference": str(_DOC_FILES["continuous_certification"]),
        "scanner_counts": {
            "legacy_but_migratable": int(scanner_body.get("legacy_but_migratable") or 0),
            "governance_candidate_manual_review": int(scanner_body.get("governance_candidate_manual_review") or 0),
            "manual_auth_header_construction": int(scanner_body.get("manual_auth_header_construction") or 0),
            "special_case_infrastructure": int(scanner_body.get("special_case_infrastructure") or 0),
        },
        "reasoning": (
            "Historical WP-15 certification remains valid because repository convergence remains at zero legacy drift and zero manual header builders."
            if certified
            else "Constitutional certification evidence is incomplete or under review."
        ),
    }


def _threshold_crossed(card: Dict[str, Any]) -> str:
    evidence = card.get("evidence") or {}
    if card.get("id") == "live-certification-posture":
        counters = evidence.get("counters") or {}
        return f"blocked={counters.get('blocked', 0)}, stale={counters.get('stale', 0)}, not_yet_exercised={counters.get('not_yet_exercised', 0)}"
    if card.get("id") == "trust-spine-band":
        sample = evidence.get("sample_workflows") or []
        failing = [row.get("workflow") for row in sample if row.get("band") == "red"]
        return f"platform_band={evidence.get('platform_band')} · failed_24h={evidence.get('total_failed_24h')} · red_workflows={', '.join(failing) or 'none'}"
    if card.get("id") == "trust-blockers":
        blockers = evidence.get("unresolved_blockers") or []
        return f"unresolved_blockers={len(blockers)}"
    if card.get("id") == "override-approval-channels":
        return f"pending_without_communications={len(evidence.get('pending_without_communications') or [])} · communication_errors={len(evidence.get('communication_errors') or [])}"
    return card.get("root_cause_explanation") or ""


def _build_condition_inventory(cards: List[Dict[str, Any]], generated_at: str) -> Dict[str, Any]:
    review_date = (datetime.fromisoformat(generated_at) + timedelta(days=7)).date().isoformat()
    red_drivers: List[Dict[str, Any]] = []
    amber_watchlist: List[Dict[str, Any]] = []
    for card in cards:
        status = normalize_operational_status(card.get("status"))
        if status not in {"red", "yellow"}:
            continue
        policy = _CONDITION_POLICY.get(card.get("id"), {})
        affected = (card.get("affected_assets") or {}).get("workflows") or (card.get("affected_assets") or {}).get("modules") or []
        row = {
            "kpi_name": card.get("title"),
            "kpi_id": card.get("id"),
            "section": card.get("section_id"),
            "current_state": status.upper(),
            "severity": "CRITICAL" if status == "red" else "WARNING",
            "canonical_evidence_source": card.get("evidence_source_label") or card.get("endpoint"),
            "evidence_timestamp": card.get("checked_at"),
            "calculation_rule": policy.get("calculation_rule") or "See KPI contract.",
            "threshold_crossed": _threshold_crossed(card),
            "root_cause": card.get("root_cause_explanation"),
            "affected_module_or_workflow": affected,
            "operator_impact": policy.get("operator_impact") or "Operator follow-up required.",
            "production_impact": policy.get("production_impact") or "Operational attention required.",
            "affects_wp15_constitutional_certification": bool(policy.get("affects_certification")),
            "recommended_remediation": card.get("recommended_action") or "Review the evidence and determine whether a safe operational repair exists.",
            "responsible_owner": policy.get("owner") or "Platform Governance",
            "target_resolution_or_review_date": review_date,
            "is_expected": True,
            "is_temporary": True,
            "issue_classification": policy.get("classification") or "operational",
            "producer": card.get("producer"),
            "drilldown": card.get("drilldown"),
        }
        if status == "red":
            red_drivers.append(row)
        else:
            amber_watchlist.append(row)
    primary_reason = red_drivers[0]["root_cause"] if red_drivers else (amber_watchlist[0]["root_cause"] if amber_watchlist else "No active non-green conditions.")
    return {"red_drivers": red_drivers, "amber_watchlist": amber_watchlist, "primary_reason": primary_reason}


def _reason_owner(reason: str, path: str) -> str:
    lowered = f"{reason} {path}".lower()
    if "frontend/" in lowered or "request-lifecycle" in lowered:
        return "Frontend Platform"
    if "integrations" in lowered or "token" in lowered:
        return "Identity & Integrations"
    if "operations_center" in lowered or "global_search" in lowered:
        return "Operations Control"
    return "Enterprise Governance"


def _retirement_criteria(reason: str) -> str:
    if "request-lifecycle" in reason.lower():
        return "Retire when the shared lifecycle infrastructure is replaced by a newer canonical path and the scanner policy is updated."
    if "authentication" in reason.lower() or "token" in reason.lower():
        return "Retire when the boundary helper is folded into a single canonical auth adapter."
    return "Retire when the infrastructure branch can be removed without reintroducing a competing authorization authority."


def _build_exemption_entries(scanner: Dict[str, Any]) -> Dict[str, Any]:
    if not scanner.get("ok"):
        return {"count": 0, "entries": [], "verified": False}
    body = scanner.get("body") or {}
    scan_ts = body.get("scan_timestamp")
    rows = [row for row in (body.get("constitutional_decision_points") or []) if row.get("category") == "special_case_infrastructure"]
    entries = []
    for idx, row in enumerate(rows, start=1):
        reason = str(row.get("reason") or "unknown")
        path = str(row.get("path") or "")
        entries.append({
            "entry_id": f"wp15-exemption-{idx:03d}",
            "path": path,
            "reason": reason,
            "true_infrastructure_special_case": True,
            "concealed_migratable_governance_seam": False,
            "documented_rationale": reason,
            "architectural_owner": _reason_owner(reason, path),
            "approval_basis": "WP-15 Constitutional Governance Standard + convergence scanner special-case policy.",
            "review_requirement": "Review during constitutional change review or when the touched file changes.",
            "retirement_criteria": _retirement_criteria(reason),
            "explicit_scanner_policy_exclusion": True,
            "dashboard_visibility": "Visible in the Operational Health Dashboard Constitutional Exemptions section.",
            "evidence_source": str(_SCANNER_PATH),
            "evidence_timestamp": scan_ts,
        })
    return {"count": len(entries), "entries": entries, "verified": len(entries) == int(body.get("special_case_infrastructure") or 0)}


def _build_golden_path_results(trust_probe: Dict[str, Any], cert_probe: Dict[str, Any], generated_at: str) -> Dict[str, Any]:
    trust_rows = {row.get("workflow"): row for row in ((trust_probe.get("body") or {}).get("workflows") or [])}
    cert_rows = {row.get("workflow"): row for row in ((cert_probe.get("body") or {}).get("workflows") or [])}
    results: List[Dict[str, Any]] = []
    for monitor in GOLDEN_PATH_MONITORS:
        trust_row = trust_rows.get(monitor["source_workflow"]) if monitor.get("source_workflow") else None
        cert_row = cert_rows.get(monitor["source_workflow"]) if monitor.get("source_workflow") else None
        has_current_run = bool(trust_row and ((trust_row.get("latest") or {}).get("ts") or (trust_row.get("last_failure") or {}).get("ts") or (trust_row.get("last_success") or {}).get("ts")))
        status = classify_golden_path_signal(trust_row.get("band") if trust_row else None, has_current_run=has_current_run)
        latest = (trust_row or {}).get("latest") or (trust_row or {}).get("last_failure") or {}
        last_success = (trust_row or {}).get("last_success") or {}
        results.append({
            "workflow_id": monitor["workflow_id"],
            "label": monitor["label"],
            "source_workflow": monitor.get("source_workflow"),
            "environment": "preview",
            "timestamp": latest.get("ts") or (cert_row or {}).get("last_verified_at") or generated_at,
            "status": status,
            "duration": latest.get("duration_ms"),
            "failed_step": (trust_row or {}).get("failure_stage"),
            "evidence": trust_row or cert_row or {"reason": "No current monitored run exists."},
            "correlation_id": latest.get("correlation_id"),
            "last_successful_run": last_success.get("ts") or (cert_row or {}).get("last_verified_at"),
            "current_owner": monitor["current_owner"],
        })
    return {
        "evaluated_at": generated_at,
        "results": results,
        "counts": count_statuses({"status": row["status"]} for row in results),
    }


def _build_status_engine_contract() -> Dict[str, Any]:
    fixtures = build_status_engine_fixture_results()
    return {
        "rules_version": "WP15-OH-1.0",
        "aggregation_priority": ["red", "yellow", "unknown", "green"],
        "unknown_policy": "Missing or stale evidence stays UNKNOWN and never upgrades to GREEN.",
        "certification_separation_policy": "Historical constitutional certification is tracked independently from current operational health.",
        "fixture_results": fixtures,
        "fixtures_passed": all(row.get("pass") for row in fixtures),
    }


def _build_cards(*, probes: Dict[str, Dict[str, Any]], scanner: Dict[str, Any], docs: Dict[str, Dict[str, Any]], workflow_evidence: Dict[str, Any], route_evidence: Dict[str, Any], generated_at: str) -> List[Dict[str, Any]]:
    cards: List[Dict[str, Any]] = []

    registry_probe = probes["governance_registry"]
    versions_probe = probes["governance_versions"]
    freeze_doc = docs["architecture_freeze"]
    if not registry_probe["ok"] or not versions_probe["ok"]:
        cards.append(_card(section_id="constitutional-status", card_id="governance-authority", title="Enterprise Governance Authority", status="unknown", summary="Authoritative governance registry evidence was unavailable.", root_cause_explanation=registry_probe.get("error") or versions_probe.get("error") or "Required governance authority probe failed.", endpoint="/api/admin/governance/registry", evidence_source_label="Enterprise governance registry", producer="enterprise governance registry consumer", checked_at=None, last_successful_refresh=None, verified_at=None, affected_files=["backend/services/enterprise_governance.py", str(_DOC_FILES["architecture_freeze"])], affected_modules=["enterprise_governance"], affected_workflows=[], recommended_action="Restore the governance registry and versions endpoints before trusting constitutional status.", evidence={"registry_probe": registry_probe, "versions_probe": versions_probe, "architecture_freeze_present": freeze_doc["exists"]}, drilldown="/admin/governance/registry"))
    else:
        registry = registry_probe["body"] or {}
        versions = versions_probe["body"] or {}
        principles = registry.get("constitutional_principles") or []
        missing = []
        if "enterprise_governance_principle" not in principles:
            missing.append("enterprise_governance_principle")
        if str(versions.get("status") or "") != "wp15-architecture-frozen":
            missing.append("versions.status")
        if not freeze_doc["exists"]:
            missing.append("WP15_ARCHITECTURE_FREEZE.md")
        status = "green" if not missing else "unknown"
        cards.append(_card(section_id="constitutional-status", card_id="governance-authority", title="Enterprise Governance Authority", status=status, summary=(f"Registry v{registry.get('version') or '—'} is the constitutional authority and the architecture freeze is published." if status == "green" else "Governance authority evidence is incomplete for architectural closeout."), root_cause_explanation=("The governance registry exposes the enterprise principles and the versions surface points at the frozen constitutional references." if status == "green" else f"Missing authority evidence: {', '.join(missing)}."), endpoint="/api/admin/governance/registry", evidence_source_label="Enterprise governance registry + versions", producer="enterprise governance registry and versions endpoints", checked_at=_max_of(registry_probe.get("refreshed_at"), versions_probe.get("refreshed_at"), freeze_doc.get("modified_at")), last_successful_refresh=_max_of(registry_probe.get("refreshed_at"), versions_probe.get("refreshed_at")), verified_at=freeze_doc.get("modified_at") or versions_probe.get("refreshed_at"), affected_files=["backend/services/enterprise_governance.py", str(_DOC_FILES["architecture_freeze"])], affected_modules=["enterprise_governance", "operational_health_dashboard"], affected_workflows=[], recommended_action="Publish or repair the missing constitutional authority artifact before relying on this dashboard as the frozen baseline." if status != "green" else "", evidence={"registry_version": registry.get("version"), "constitutional_principles": principles, "versions": versions, "architecture_freeze_present": freeze_doc["exists"]}, drilldown="/admin/governance/versions"))

    standard_doc = docs["constitutional_standard"]
    dashboard_doc = docs["dashboard_standard"]
    health_doc = docs["enterprise_health"]
    missing_headings = [] if not standard_doc["exists"] else _missing_headings(standard_doc["text"], ["Enterprise Governance as Constitutional Authority", "Approved Extension Points", "Prohibited Architectural Patterns", "Governance Change Process", "Relationship to Future Work Packages"])
    doc_status = "green" if standard_doc["exists"] and dashboard_doc["exists"] and health_doc["exists"] and not missing_headings else "unknown"
    cards.append(_card(section_id="constitutional-status", card_id="constitutional-standard", title="Constitutional Standard & Dashboard Contract", status=doc_status, summary=("The constitutional standard, dashboard contract, and health guide are all published." if doc_status == "green" else "One or more constitutional closeout documents are missing or incomplete."), root_cause_explanation=("The dashboard framework is backed by explicit constitutional guidance, extension rules, and prohibited-pattern documentation." if doc_status == "green" else f"Missing document evidence or headings: {', '.join(missing_headings or ['required closeout document'])}."), endpoint=str(_DOC_FILES["constitutional_standard"]), evidence_source_label="WP-15 constitutional closeout documents", producer="markdown closeout artifacts", checked_at=_max_of(standard_doc.get("modified_at"), dashboard_doc.get("modified_at"), health_doc.get("modified_at")), last_successful_refresh=generated_at, verified_at=standard_doc.get("modified_at"), affected_files=[str(_DOC_FILES["constitutional_standard"]), str(_DOC_FILES["dashboard_standard"]), str(_DOC_FILES["enterprise_health"])], affected_modules=["documentation", "operational_health_dashboard"], affected_workflows=[], recommended_action="Complete the missing constitutional headings and closeout documents before treating the architecture as frozen." if doc_status != "green" else "", evidence={"constitutional_standard_present": standard_doc["exists"], "dashboard_doc_present": dashboard_doc["exists"], "enterprise_health_present": health_doc["exists"], "missing_headings": missing_headings}))

    if not scanner["ok"]:
        scanner_error = scanner.get("error") or "Scanner failed."
        cards.append(_card(section_id="governance-drift", card_id="repository-drift-scan", title="Repository Governance Drift", status="unknown", summary="The WP-15 convergence scanner did not produce evidence.", root_cause_explanation=scanner_error, endpoint=str(_SCANNER_PATH), evidence_source_label="WP-15 governance convergence scanner", producer="backend/tools/wp15_governance_convergence_scan.py", checked_at=None, last_successful_refresh=None, verified_at=None, affected_files=[str(_SCANNER_PATH)], affected_modules=["wp15_governance_convergence_scan"], affected_workflows=[], recommended_action="Repair the scanner before relying on drift metrics.", evidence={"scanner_error": scanner_error}))
        cards.append(_card(section_id="governance-drift", card_id="request-lifecycle-drift", title="Request Lifecycle Convergence", status="unknown", summary="Manual header-builder evidence is unavailable because the scanner failed.", root_cause_explanation=scanner_error, endpoint=str(_SCANNER_PATH), evidence_source_label="WP-15 request-lifecycle scan", producer="backend/tools/wp15_governance_convergence_scan.py", checked_at=None, last_successful_refresh=None, verified_at=None, affected_files=[str(_SCANNER_PATH)], affected_modules=["wp15_governance_convergence_scan"], affected_workflows=[], recommended_action="Repair the scanner before trusting request-lifecycle drift status.", evidence={"scanner_error": scanner_error}))
    else:
        scan = scanner["body"] or {}
        legacy = int(scan.get("legacy_but_migratable") or 0)
        candidates = int(scan.get("governance_candidate_manual_review") or 0)
        manual_headers = int(scan.get("manual_auth_header_construction") or 0)
        findings = scan.get("constitutional_decision_points") or []
        legacy_findings = [row for row in findings if row.get("category") in {"legacy_migratable", "governance_candidate"}]
        manual_findings = [row for row in findings if row.get("reason") == "Manual governed-request header construction"]
        cards.append(_card(section_id="governance-drift", card_id="repository-drift-scan", title="Repository Governance Drift", status="green" if legacy == 0 and candidates == 0 else "red", summary=(f"Scanner reports {legacy} legacy finding(s) and {candidates} manual-review governance candidate(s)." if legacy or candidates else "Scanner reports zero legacy governance drift and zero unresolved governance candidates."), root_cause_explanation=("No legacy or uncertain governance seams were found in the current repository scan." if legacy == 0 and candidates == 0 else "Legacy or unresolved governance seams remain in the current repository scan."), endpoint=str(_SCANNER_PATH), evidence_source_label="WP-15 repository convergence scan", producer="backend/tools/wp15_governance_convergence_scan.py", checked_at=scan.get("scan_timestamp"), last_successful_refresh=scanner.get("refreshed_at"), verified_at=scan.get("scan_timestamp"), affected_files=(sorted({row.get("path") for row in legacy_findings if row.get("path")})[:8] or [str(_SCANNER_PATH), str(_DOC_FILES["drift_report"])]), affected_modules=(sorted({str(row.get("path") or "").split("/")[-1] for row in legacy_findings if row.get("path")})[:8] or ["wp15_governance_convergence_scan", "enterprise_governance"]), affected_workflows=[], recommended_action="Fix the listed legacy findings, then rerun the WP-15 convergence scanner until both counters return zero." if legacy or candidates else "", evidence={"legacy_but_migratable": legacy, "governance_candidate_manual_review": candidates, "special_case_infrastructure": int(scan.get("special_case_infrastructure") or 0), "sample_findings": legacy_findings[:5]}))
        cards.append(_card(section_id="governance-drift", card_id="request-lifecycle-drift", title="Request Lifecycle Convergence", status="green" if manual_headers == 0 else "red", summary=("All governed frontend requests use the canonical header builders." if manual_headers == 0 else f"Scanner found {manual_headers} manual governed header-builder location(s)."), root_cause_explanation=("Manual frontend governed-request header construction is at zero in the current scan." if manual_headers == 0 else "Manual header construction remains and can reintroduce drift between portals."), endpoint=str(_SCANNER_PATH), evidence_source_label="WP-15 request-lifecycle convergence scan", producer="backend/tools/wp15_governance_convergence_scan.py", checked_at=scan.get("scan_timestamp"), last_successful_refresh=scanner.get("refreshed_at"), verified_at=scan.get("scan_timestamp"), affected_files=(sorted({row.get("path") for row in manual_findings if row.get("path")})[:8] or [str(_SCANNER_PATH), "frontend/src/lib/api.js", "frontend/src/lib/authHeaders.js"]), affected_modules=(sorted({str(row.get("path") or "").split("/")[-1] for row in manual_findings if row.get("path")})[:8] or ["request_lifecycle", "frontend_api"]), affected_workflows=[], recommended_action="Replace every manual header builder with the canonical scoped portal helpers." if manual_headers else "", evidence={"manual_auth_header_construction": manual_headers, "sample_findings": manual_findings[:5], "request_lifecycle_convergence": scan.get("request_lifecycle_convergence")}))

    cards.append(_card(section_id="governance-drift", card_id="ci-governance-enforcement", title="CI/CD Governance Protection", status=workflow_evidence["status"], summary=("Pull requests, nightly builds, release certification, and production gates all enforce the WP-15 scanner." if workflow_evidence["status"] == "green" else "One or more CI/CD gates are missing the mandatory WP-15 governance drift enforcement."), root_cause_explanation=("Every required gate references the scanner and the convergence assertion script." if workflow_evidence["status"] == "green" else f"Missing governance protection on: {', '.join(workflow_evidence.get('missing') or ['unknown gate'])}."), endpoint=str(_CI_PATH), evidence_source_label="GitHub Actions governance gate workflows", producer="GitHub Actions workflow definitions", checked_at=workflow_evidence.get("checked_at"), last_successful_refresh=generated_at, verified_at=workflow_evidence.get("checked_at"), affected_files=workflow_evidence.get("files") or [], affected_modules=["ci", "deployment_gate"], affected_workflows=list(workflow_evidence.get("gates", {}).keys()), recommended_action="Wire the missing gate(s) to the WP-15 scanner and fail on any newly introduced drift." if workflow_evidence["status"] != "green" else "", evidence=workflow_evidence))

    cert_probe = probes["production_certification"]
    cert_doc = docs["continuous_certification"]
    final_cert_doc = docs["final_certification"]
    if not cert_probe["ok"]:
        cards.append(_card(section_id="certification-health", card_id="live-certification-posture", title="Live Certification Posture", status="unknown", summary="The live certification endpoint was unavailable.", root_cause_explanation=cert_probe.get("error") or "Certification probe failed.", endpoint="/api/admin/production-certification", evidence_source_label="Production certification endpoint", producer="production certification engine", checked_at=None, last_successful_refresh=None, verified_at=None, affected_files=["backend/routes/admin_production_certification.py"], affected_modules=["production_certification"], affected_workflows=[], recommended_action="Restore the certification endpoint before making platform health claims.", evidence={"probe": cert_probe}, drilldown="/admin/governance-trust"))
    else:
        cert = cert_probe["body"] or {}
        workflows = cert.get("workflows") or []
        cards.append(_card(section_id="certification-health", card_id="live-certification-posture", title="Live Certification Posture", status=_normalize_status(cert.get("platform_band")), summary=f"Platform certification band is {str(cert.get('platform_band') or 'unknown').upper()} with {len(workflows)} tracked workflows.", root_cause_explanation=("The certification engine reports all tracked workflows within the healthy band." if _normalize_status(cert.get("platform_band")) == "green" else "Certification evidence includes blocked, stale, or not-yet-exercised workflows in the current platform posture."), endpoint="/api/admin/production-certification", evidence_source_label="Continuous production certification", producer="production certification engine", checked_at=cert.get("generated_at"), last_successful_refresh=cert_probe.get("refreshed_at"), verified_at=_latest_non_empty(workflows, "last_verified_at", "first_verified_at") or cert.get("generated_at"), affected_files=[str(_DOC_FILES["continuous_certification"]), str(_DOC_FILES["final_certification"])], affected_modules=["production_certification"], affected_workflows=[row.get("workflow") for row in workflows if row.get("status") not in {"VERIFIED"}][:8], recommended_action="Run or repair the blocked and stale certification workflows until the platform band is green." if _normalize_status(cert.get("platform_band")) != "green" else "", evidence={"platform_band": cert.get("platform_band"), "counters": cert.get("counters"), "sample_workflows": workflows[:6]}, drilldown="/admin/governance-trust"))

    history_entries = _parse_certification_history_entries(cert_doc["text"]) if cert_doc["exists"] else 0
    cert_missing = []
    if not cert_doc["exists"]:
        cert_missing.append("WP15_CONTINUOUS_CERTIFICATION.md")
    if not final_cert_doc["exists"]:
        cert_missing.append("WP15_ENTERPRISE_GOVERNANCE_CERTIFICATION.md")
    if cert_doc["exists"]:
        cert_missing.extend(_missing_headings(cert_doc["text"], ["Certification History", "Continuous Gate Coverage", "Append-Only Retention Rule"]))
    history_status = "green" if not cert_missing and history_entries >= 3 else "unknown"
    cards.append(_card(section_id="certification-health", card_id="wp15-certification-history", title="WP-15 Certification History Retention", status=history_status, summary=(f"Append-only certification history includes {history_entries} retained evidence entries." if history_status == "green" else "Certification history retention evidence is missing or incomplete."), root_cause_explanation=("The closeout documentation retains historical certification checkpoints rather than only the latest verdict." if history_status == "green" else f"Missing certification history evidence: {', '.join(cert_missing or ['insufficient history entries'])}."), endpoint=str(_DOC_FILES["continuous_certification"]), evidence_source_label="WP-15 certification history ledger", producer="markdown certification ledger", checked_at=cert_doc.get("modified_at") or final_cert_doc.get("modified_at"), last_successful_refresh=generated_at, verified_at=final_cert_doc.get("modified_at"), affected_files=[str(_DOC_FILES["continuous_certification"]), str(_DOC_FILES["final_certification"])], affected_modules=["documentation", "certification_history"], affected_workflows=[], recommended_action="Publish the continuous certification ledger with explicit historical entries and append-only rules." if history_status != "green" else "", evidence={"history_entries": history_entries, "continuous_certification_present": cert_doc["exists"], "final_certification_present": final_cert_doc["exists"], "missing": cert_missing}))

    truth_probe = probes["platform_truth_integrity"]
    if not truth_probe["ok"]:
        cards.append(_card(section_id="platform-truth-integrity", card_id="synthetic-certification-contamination", title="Synthetic / Certification Contamination", status="unknown", summary="Platform truth-integrity evidence was unavailable.", root_cause_explanation=truth_probe.get("error") or "Truth-integrity probe failed.", endpoint="/api/admin/platform-truth-integrity", evidence_source_label="Platform truth-integrity scanner", producer="platform_truth_integrity", checked_at=None, last_successful_refresh=None, verified_at=None, affected_files=["backend/lib/platform_truth_integrity.py", "backend/routes/platform_truth_integrity.py"], affected_modules=["platform_truth_integrity"], affected_workflows=[], recommended_action="Restore the platform truth-integrity scanner before relying on contamination health.", evidence={"probe": truth_probe}, drilldown="/admin/governance-trust"))
        cards.append(_card(section_id="platform-truth-integrity", card_id="stale-derived-state", title="Stale Derived State", status="unknown", summary="Derived-state staleness evidence was unavailable.", root_cause_explanation=truth_probe.get("error") or "Truth-integrity probe failed.", endpoint="/api/admin/platform-truth-integrity", evidence_source_label="Platform truth-integrity scanner", producer="platform_truth_integrity", checked_at=None, last_successful_refresh=None, verified_at=None, affected_files=["backend/lib/platform_truth_integrity.py", "backend/routes/platform_truth_integrity.py"], affected_modules=["platform_truth_integrity"], affected_workflows=[], recommended_action="Restore the platform truth-integrity scanner before relying on stale-derived-state health.", evidence={"probe": truth_probe}, drilldown="/admin/governance-trust"))
    else:
        truth = truth_probe["body"] or {}
        contamination = truth.get("contamination") or {}
        stale = truth.get("stale_derived_state") or {}
        contamination_blockers = contamination.get("blocking_findings") or []
        stale_blockers = stale.get("blocking_findings") or []
        cards.append(_card(section_id="platform-truth-integrity", card_id="synthetic-certification-contamination", title="Synthetic / Certification Contamination", status=_normalize_status(contamination.get("overall_status")), summary=("No blocking contamination findings were detected in the current governed family scan." if _normalize_status(contamination.get("overall_status")) == "green" else f"{len(contamination_blockers)} blocking contamination finding(s) remain across material families."), root_cause_explanation=("Material data families either use explicit governed markers or currently show no contamination evidence." if _normalize_status(contamination.get("overall_status")) == "green" else "One or more material families still rely on heuristic-only exclusion, contradictory markers, or certification-scope rows without complete isolation evidence."), endpoint="/api/admin/platform-truth-integrity/contamination", evidence_source_label="Platform contamination integrity scan", producer="platform_truth_integrity", checked_at=contamination.get("generated_at"), last_successful_refresh=truth_probe.get("refreshed_at"), verified_at=contamination.get("generated_at"), affected_files=["backend/lib/platform_truth_integrity.py", "backend/routes/platform_truth_integrity.py"], affected_modules=["platform_truth_integrity"], affected_workflows=[row.get("family_id") for row in contamination_blockers][:8], recommended_action="Convert heuristic-only families to explicit governed classification and isolate certification-scoped data from operator aggregates." if contamination_blockers else "", evidence={"blocking_findings": contamination_blockers[:8], "sample_families": (contamination.get("families") or [])[:8]}, drilldown="/admin/governance-trust"))
        cards.append(_card(section_id="platform-truth-integrity", card_id="stale-derived-state", title="Stale Derived State", status=_normalize_status(stale.get("overall_status")), summary=("No blocking stale-derived-state mismatches were detected in the current governed dependency scan." if _normalize_status(stale.get("overall_status")) == "green" else f"{len(stale_blockers)} stale-derived-state finding(s) remain across governed downstream chains."), root_cause_explanation=("Current downstream chains either recompute on demand or remain aligned to their upstream governed signatures." if _normalize_status(stale.get("overall_status")) == "green" else "One or more derived states still point at older upstream signatures, versions, or dependency snapshots."), endpoint="/api/admin/platform-truth-integrity/stale-derived-state", evidence_source_label="Platform stale-derived-state scan", producer="platform_truth_integrity", checked_at=stale.get("generated_at"), last_successful_refresh=truth_probe.get("refreshed_at"), verified_at=stale.get("generated_at"), affected_files=["backend/lib/platform_truth_integrity.py", "backend/routes/platform_truth_integrity.py", "backend/services/project_schedule_authority.py"], affected_modules=["platform_truth_integrity", "project_schedule_authority"], affected_workflows=[row.get("id") for row in stale_blockers][:8], recommended_action="Repair the mismatched downstream chain and add deterministic invalidation before treating it as current." if stale_blockers else "", evidence={"blocking_findings": stale_blockers[:8], "sample_checks": (stale.get("checks") or [])[:8]}, drilldown="/admin/governance-trust"))

    trust_probe = probes["trust_spine"]
    events_probe = probes["occ_trust_events"]
    if not trust_probe["ok"]:
        cards.append(_card(section_id="trust-spine-integrity", card_id="trust-spine-band", title="Trust Spine Integrity", status="unknown", summary="Trust Spine evidence was unavailable.", root_cause_explanation=trust_probe.get("error") or "Trust Spine probe failed.", endpoint="/api/admin/trust-spine", evidence_source_label="Trust Spine lifecycle truth", producer="admin trust spine endpoint", checked_at=None, last_successful_refresh=None, verified_at=None, affected_files=["backend/routes/admin_trust_spine.py"], affected_modules=["trust_spine"], affected_workflows=[], recommended_action="Restore Trust Spine visibility before using lifecycle health in governance closeout.", evidence={"probe": trust_probe}, drilldown="/admin/governance-trust"))
    else:
        trust = trust_probe["body"] or {}
        workflows = trust.get("workflows") or []
        affected_workflows = [row.get("workflow") for row in workflows if row.get("band") != "green"][:8]
        cards.append(_card(section_id="trust-spine-integrity", card_id="trust-spine-band", title="Trust Spine Integrity", status=_normalize_status(trust.get("platform_band")), summary=f"Trust Spine band is {str(trust.get('platform_band') or 'unknown').upper()} across {trust.get('workflow_count') or len(workflows)} workflows.", root_cause_explanation=("All observed Trust Spine workflows satisfied their expected-stage contracts." if _normalize_status(trust.get("platform_band")) == "green" else "One or more workflows emitted failures, partial stage completion, or no recent lifecycle evidence."), endpoint="/api/admin/trust-spine", evidence_source_label="Trust Spine workflow lifecycle rollup", producer="admin trust spine endpoint", checked_at=trust.get("generated_at"), last_successful_refresh=trust_probe.get("refreshed_at"), verified_at=trust.get("generated_at"), affected_files=["backend/routes/admin_trust_spine.py", "backend/lib/trust_spine.py"], affected_modules=["trust_spine"], affected_workflows=affected_workflows, recommended_action="Open the affected workflow drill-in and resolve the failing or incomplete lifecycle stages." if affected_workflows else "", evidence={"platform_band": trust.get("platform_band"), "canonical_status": trust.get("canonical_status"), "total_events_24h": trust.get("total_events_24h"), "total_failed_24h": trust.get("total_failed_24h"), "sample_workflows": workflows[:6]}, drilldown="/admin/governance-trust"))

    if not events_probe["ok"]:
        cards.append(_card(section_id="trust-spine-integrity", card_id="trust-blockers", title="Trust Blockers Feed", status="unknown", summary="The trust-events blocker feed was unavailable.", root_cause_explanation=events_probe.get("error") or "Trust-events probe failed.", endpoint="/api/admin/occ/trust-events", evidence_source_label="Unified trust events feed", producer="OCC trust events aggregator", checked_at=None, last_successful_refresh=None, verified_at=None, affected_files=["backend/routes/occ_trust_events.py"], affected_modules=["occ_trust_events"], affected_workflows=[], recommended_action="Restore the trust-events feed before using blocker evidence.", evidence={"probe": events_probe}, drilldown="/admin/governance-trust"))
    else:
        events = events_probe["body"] or {}
        blockers = events.get("unresolved_blockers") or []
        blocker_workflows = [((row.get("evidence") or {}).get("id") or row.get("summary") or "") for row in blockers][:8]
        cards.append(_card(section_id="trust-spine-integrity", card_id="trust-blockers", title="Trust Blockers Feed", status="green" if not blockers else "red", summary=("No unresolved trust or deploy blockers were reported in the recent unified feed." if not blockers else f"Unified trust feed reports {len(blockers)} unresolved blocker(s)."), root_cause_explanation=("The recent trust-events window contains no blocking contradictions." if not blockers else "Recent trust events include unresolved blockers that are still failing readiness or lifecycle expectations."), endpoint="/api/admin/occ/trust-events", evidence_source_label="Unified trust events feed", producer="OCC trust events aggregator", checked_at=events.get("generated_at"), last_successful_refresh=events_probe.get("refreshed_at"), verified_at=events.get("generated_at"), affected_files=["backend/routes/occ_trust_events.py"], affected_modules=["occ_trust_events"], affected_workflows=blocker_workflows, recommended_action="Investigate the blocker records and clear the failing workflows before treating the governance estate as healthy." if blockers else "", evidence={"counts": events.get("counts"), "by_kind": events.get("by_kind"), "unresolved_blockers": blockers[:8]}, drilldown="/admin/governance-trust"))

    identities_probe = probes["governance_identities"]
    if not identities_probe["ok"]:
        cards.append(_card(section_id="identity-health", card_id="identity-projections", title="Identity Projection Freshness", status="unknown", summary="Identity projection evidence was unavailable.", root_cause_explanation=identities_probe.get("error") or "Identity projection probe failed.", endpoint="/api/admin/governance/identities", evidence_source_label="Governance identity projections", producer="enterprise governance identities endpoint", checked_at=None, last_successful_refresh=None, verified_at=None, affected_files=["backend/services/enterprise_governance.py"], affected_modules=["enterprise_governance"], affected_workflows=[], recommended_action="Restore identity projection visibility before relying on identity health.", evidence={"probe": identities_probe}, drilldown="/admin/governance/identities"))
    else:
        identities = identities_probe["body"] or {}
        identity_items = identities.get("items") or []
        latest_identity = _latest_non_empty(identity_items, "updated_at", "created_at", "effective_from")
        identity_status = "green" if identity_items and latest_identity else "unknown"
        cards.append(_card(section_id="identity-health", card_id="identity-projections", title="Identity Projection Freshness", status=identity_status, summary=(f"{len(identity_items)} identity projection(s) are available for policy evaluation." if identity_status == "green" else "Identity projections are missing or do not expose freshness evidence."), root_cause_explanation=("Governance decisions have current identity projection evidence to consume." if identity_status == "green" else "Projection count or projection timestamps were missing from the canonical identity source."), endpoint="/api/admin/governance/identities", evidence_source_label="Governance identity projections", producer="enterprise governance identities endpoint", checked_at=latest_identity, last_successful_refresh=identities_probe.get("refreshed_at"), verified_at=latest_identity, affected_files=["backend/services/enterprise_governance.py"], affected_modules=["enterprise_governance"], affected_workflows=[], recommended_action="Project or repair the missing identities before trusting authorization context." if identity_status != "green" else "", evidence={"count": len(identity_items), "sample_identities": identity_items[:5], "latest_identity_timestamp": latest_identity}, drilldown="/admin/governance/identities"))

    sessions_probe = probes["sessions_recent"]
    if not sessions_probe["ok"]:
        cards.append(_card(section_id="identity-health", card_id="session-timeouts", title="Session Timeout Governance", status="unknown", summary="Session timeout evidence was unavailable.", root_cause_explanation=sessions_probe.get("error") or "Sessions probe failed.", endpoint="/api/admin/sessions/recent", evidence_source_label="Recent governed session inventory", producer="admin sessions endpoint", checked_at=None, last_successful_refresh=None, verified_at=None, affected_files=["backend/routes/admin_sessions.py", "frontend/src/pages/admin/AdminSessions.jsx"], affected_modules=["sessions"], affected_workflows=[], recommended_action="Restore the sessions endpoint before relying on identity timeout posture.", evidence={"probe": sessions_probe}, drilldown="/admin/sessions"))
    else:
        sessions = sessions_probe["body"] or {}
        tiers = sessions.get("tiers") or {}
        tiers_ok = bool(tiers) and all(int((value or {}).get("idle_min") or 0) > 0 and int((value or {}).get("abs_hour") or 0) > 0 for value in tiers.values())
        session_status = "red" if not sessions.get("timeouts_enabled") else ("unknown" if int(sessions.get("count") or 0) == 0 else ("green" if tiers_ok else "unknown"))
        cards.append(_card(section_id="identity-health", card_id="session-timeouts", title="Session Timeout Governance", status=session_status, summary=("Session timeouts are enabled and active sessions are being tracked with explicit timeout tiers." if session_status == "green" else "Session timeout evidence is disabled, empty, or incomplete."), root_cause_explanation=("Recent sessions expose timeout tiers, active status, and current limits." if session_status == "green" else "Session timeout configuration or active-session evidence is missing from the canonical session inventory."), endpoint="/api/admin/sessions/recent", evidence_source_label="Recent governed session inventory", producer="admin sessions endpoint", checked_at=sessions.get("server_now"), last_successful_refresh=sessions_probe.get("refreshed_at"), verified_at=sessions.get("server_now"), affected_files=["backend/routes/admin_sessions.py", "frontend/src/pages/admin/AdminSessions.jsx"], affected_modules=["sessions"], affected_workflows=[], recommended_action="Enable timeout enforcement and capture recent session evidence before marking identity health green." if session_status != "green" else "", evidence={"timeouts_enabled": sessions.get("timeouts_enabled"), "tiers": tiers, "session_count": sessions.get("count"), "sample_sessions": (sessions.get("sessions") or [])[:5]}, drilldown="/admin/sessions"))

    decisions_probe = probes["governance_decisions"]
    if not decisions_probe["ok"]:
        cards.append(_card(section_id="authorization-health", card_id="decision-immutability", title="Decision Explainability & Immutability", status="unknown", summary="Governance decision evidence was unavailable.", root_cause_explanation=decisions_probe.get("error") or "Decisions probe failed.", endpoint="/api/admin/governance/decisions", evidence_source_label="Governance decisions ledger", producer="enterprise governance decisions endpoint", checked_at=None, last_successful_refresh=None, verified_at=None, affected_files=["backend/services/enterprise_governance.py"], affected_modules=["enterprise_governance"], affected_workflows=[], recommended_action="Restore the decisions ledger before claiming authorization health.", evidence={"probe": decisions_probe}, drilldown="/admin/governance/decisions"))
    else:
        decision_items = (decisions_probe["body"] or {}).get("items") or []
        sample = decision_items[:25]
        broken = []
        for row in sample:
            if not row.get("decision_id") or not row.get("policy_version") or not row.get("determinism_fingerprint"):
                broken.append(row.get("id") or row.get("decision_id") or "unknown")
                continue
            if row.get("immutable") is not True or row.get("record_mode") != "append_only":
                broken.append(row.get("decision_id") or row.get("id") or "unknown")
                continue
            if not ((row.get("identity_snapshot") or {}).get("canonical_user_id")):
                broken.append(row.get("decision_id") or row.get("id") or "unknown")
        decision_status = "green" if sample and not broken else ("red" if sample else "unknown")
        cards.append(_card(section_id="authorization-health", card_id="decision-immutability", title="Decision Explainability & Immutability", status=decision_status, summary=(f"Reviewed {len(sample)} recent decision record(s) for immutable, explainable governance evidence." if sample else "No recent governance decisions were available to verify."), root_cause_explanation=("Recent decisions carry immutable IDs, policy versions, determinism fingerprints, and identity snapshots." if decision_status == "green" else "One or more recent decision records were missing immutable or explainability fields."), endpoint="/api/admin/governance/decisions", evidence_source_label="Governance decisions ledger", producer="enterprise governance decisions endpoint", checked_at=_latest_non_empty(sample, "decision_timestamp", "decided_at"), last_successful_refresh=decisions_probe.get("refreshed_at"), verified_at=_latest_non_empty(sample, "decision_timestamp", "decided_at"), affected_files=["backend/services/enterprise_governance.py"], affected_modules=["enterprise_governance"], affected_workflows=[], recommended_action="Repair the decision writer so every record remains immutable and fully explainable." if decision_status != "green" else "", evidence={"reviewed_count": len(sample), "broken_records": broken, "sample_decisions": sample[:5]}, drilldown="/admin/governance/decisions"))

    overrides_probe = probes["governance_overrides"]
    approvals_probe = probes["governance_approval_flows"]
    if not overrides_probe["ok"] or not approvals_probe["ok"]:
        cards.append(_card(section_id="authorization-health", card_id="override-approval-channels", title="Override & Approval Channel Health", status="unknown", summary="Override or approval-channel evidence was unavailable.", root_cause_explanation=overrides_probe.get("error") or approvals_probe.get("error") or "Approval channel probe failed.", endpoint="/api/admin/governance/emergency-overrides", evidence_source_label="Emergency override and approval channel evidence", producer="enterprise governance override/approval endpoints", checked_at=None, last_successful_refresh=None, verified_at=None, affected_files=["backend/services/enterprise_governance.py"], affected_modules=["enterprise_governance"], affected_workflows=[], recommended_action="Restore the override and approval endpoints before trusting governed escalation health.", evidence={"overrides_probe": overrides_probe, "approvals_probe": approvals_probe}, drilldown="/admin/governance/approval-flows"))
    else:
        overrides = (overrides_probe["body"] or {}).get("items") or []
        approval_requests = (approvals_probe["body"] or {}).get("requests") or []
        comm_errors = [row.get("id") for row in overrides if row.get("communication_error")] + [row.get("id") for row in approval_requests if row.get("communication_error")]
        pending_without_communications = [row.get("id") for row in overrides if str(row.get("status") or "") in {"pending_review", "active"} and row.get("ack_required") and not (row.get("communications") or [])] + [row.get("id") for row in approval_requests if str(row.get("status") or "") == "pending" and not (row.get("communications") or [])]
        channel_status = "red" if comm_errors else ("yellow" if pending_without_communications else "green")
        cards.append(_card(section_id="authorization-health", card_id="override-approval-channels", title="Override & Approval Channel Health", status=channel_status, summary=f"{len(overrides)} override record(s) and {len(approval_requests)} approval request(s) were checked for auditable communications.", root_cause_explanation=("Auditable communication evidence exists for the currently governed override and approval pathways." if channel_status == "green" else "One or more governed approval or override records are missing required communication evidence or carry communication errors."), endpoint="/api/admin/governance/emergency-overrides", evidence_source_label="Emergency override and approval channel evidence", producer="enterprise governance override/approval endpoints", checked_at=_max_of(_latest_non_empty(overrides, "created_at", "starts_at"), _latest_non_empty(approval_requests, "updated_at", "created_at")), last_successful_refresh=_max_of(overrides_probe.get("refreshed_at"), approvals_probe.get("refreshed_at")), verified_at=_max_of(_latest_non_empty(overrides, "created_at", "starts_at"), _latest_non_empty(approval_requests, "updated_at", "created_at")), affected_files=["backend/services/enterprise_governance.py", "backend/routes/enterprise_governance.py"], affected_modules=["enterprise_governance"], affected_workflows=[row.get("requested_capability") for row in overrides if row.get("requested_capability")][:8], recommended_action="Repair the affected communication chain so pending governance actions remain visible and auditable." if channel_status != "green" else "", evidence={"override_count": len(overrides), "approval_request_count": len(approval_requests), "communication_errors": comm_errors, "pending_without_communications": pending_without_communications, "sample_overrides": overrides[:4], "sample_approval_requests": approval_requests[:4]}, drilldown="/admin/governance/approval-flows"))

    cards.append(_card(section_id="operator-experience", card_id="route-nav-registration", title="Primary Route & Navigation Registration", status=route_evidence["status"], summary=("The primary Admin route, nav mapping, page shell, and API helper are all registered for the governance dashboard." if route_evidence["status"] == "green" else "The operational health route is not fully registered across routing, navigation, or API helpers."), root_cause_explanation=("Operators can reach the dashboard through the canonical Admin route and shared Admin OS navigation layers." if route_evidence["status"] == "green" else f"Missing route integration evidence: {', '.join(route_evidence.get('missing') or ['unknown'])}."), endpoint="/admin/governance", evidence_source_label="Frontend routing and Admin OS navigation", producer="frontend route and navigation files", checked_at=route_evidence.get("checked_at"), last_successful_refresh=generated_at, verified_at=route_evidence.get("checked_at"), affected_files=route_evidence.get("files") or [], affected_modules=["admin_routing", "admin_navigation"], affected_workflows=[], recommended_action="Register the page in AppRoutes, the domain map, and the API helper before treating it as the primary operator path." if route_evidence["status"] != "green" else "", evidence=route_evidence))

    exemptions_doc = docs["exemptions"]
    if scanner["ok"] and exemptions_doc["exists"]:
        scanner_special_total = int((scanner["body"] or {}).get("special_case_infrastructure") or 0)
        doc_total = _parse_exemption_total(exemptions_doc["text"])
        register_status = "green" if doc_total == scanner_special_total else "red"
        cards.append(_card(section_id="constitutional-exemptions", card_id="exemption-register-sync", title="Exemption Register Sync", status=register_status, summary=(f"Documented exemption total matches the scanner at {scanner_special_total}." if register_status == "green" else "The documented exemption total does not match the scanner output."), root_cause_explanation=("The constitutional exemption register reflects the same special-case total reported by the latest convergence scan." if register_status == "green" else f"Scanner total={scanner_special_total}, documented total={doc_total if doc_total is not None else 'missing'}."), endpoint=str(_DOC_FILES["exemptions"]), evidence_source_label="WP-15 constitutional exemptions register", producer="scanner + markdown exemption register", checked_at=exemptions_doc.get("modified_at"), last_successful_refresh=generated_at, verified_at=(scanner["body"] or {}).get("scan_timestamp"), affected_files=[str(_DOC_FILES["exemptions"]), str(_SCANNER_PATH)], affected_modules=["wp15_governance_convergence_scan", "documentation"], affected_workflows=[], recommended_action="Update the exemption register so its documented total matches the current scanner output." if register_status != "green" else "", evidence={"scanner_special_case_infrastructure": scanner_special_total, "documented_special_case_infrastructure": doc_total}))

        scanner_reason_counts = _scanner_reason_counts(scanner["body"] or {})
        doc_reason_counts = _parse_exemption_reason_counts(exemptions_doc["text"])
        mismatches = []
        for reason in sorted(set(scanner_reason_counts.keys()) | set(doc_reason_counts.keys())):
            if scanner_reason_counts.get(reason) != doc_reason_counts.get(reason):
                mismatches.append({"reason": reason, "scanner": scanner_reason_counts.get(reason), "documented": doc_reason_counts.get(reason)})
        reason_status = "green" if not mismatches else "red"
        cards.append(_card(section_id="constitutional-exemptions", card_id="exemption-reason-coverage", title="Exemption Reason Coverage", status=reason_status, summary=(f"All {len(scanner_reason_counts)} exemption reason groups are documented with matching counts." if reason_status == "green" else "One or more exemption reason groups are undocumented or count-mismatched."), root_cause_explanation=("Every special-case infrastructure reason emitted by the scanner is represented in the exemption register." if reason_status == "green" else "The register and the scanner disagree on one or more exemption reason groups."), endpoint=str(_DOC_FILES["exemptions"]), evidence_source_label="WP-15 exemption reason mapping", producer="scanner + markdown exemption register", checked_at=exemptions_doc.get("modified_at"), last_successful_refresh=generated_at, verified_at=(scanner["body"] or {}).get("scan_timestamp"), affected_files=[str(_DOC_FILES["exemptions"]), str(_SCANNER_PATH)], affected_modules=["wp15_governance_convergence_scan", "documentation"], affected_workflows=[], recommended_action="Align the exemption register reason table with the scanner's current normalized reason counts." if reason_status != "green" else "", evidence={"scanner_reason_counts": scanner_reason_counts, "documented_reason_counts": doc_reason_counts, "mismatches": mismatches}))
    else:
        cards.append(_card(section_id="constitutional-exemptions", card_id="exemption-register-sync", title="Exemption Register Sync", status="unknown", summary="Exemption register or scanner evidence was unavailable.", root_cause_explanation=(scanner.get("error") if not scanner["ok"] else "WP15_CONSTITUTIONAL_EXEMPTIONS.md is missing."), endpoint=str(_DOC_FILES["exemptions"]), evidence_source_label="WP-15 constitutional exemptions register", producer="scanner + markdown exemption register", checked_at=exemptions_doc.get("modified_at"), last_successful_refresh=generated_at if exemptions_doc["exists"] else None, verified_at=None, affected_files=[str(_DOC_FILES["exemptions"]), str(_SCANNER_PATH)], affected_modules=["wp15_governance_convergence_scan", "documentation"], affected_workflows=[], recommended_action="Restore both the scanner and the exemptions register before certifying constitutional exemptions.", evidence={"scanner_ok": scanner["ok"], "exemptions_doc_present": exemptions_doc["exists"]}))
        cards.append(_card(section_id="constitutional-exemptions", card_id="exemption-reason-coverage", title="Exemption Reason Coverage", status="unknown", summary="Exemption reason coverage could not be evaluated.", root_cause_explanation=(scanner.get("error") if not scanner["ok"] else "WP15_CONSTITUTIONAL_EXEMPTIONS.md is missing."), endpoint=str(_DOC_FILES["exemptions"]), evidence_source_label="WP-15 exemption reason mapping", producer="scanner + markdown exemption register", checked_at=exemptions_doc.get("modified_at"), last_successful_refresh=generated_at if exemptions_doc["exists"] else None, verified_at=None, affected_files=[str(_DOC_FILES["exemptions"]), str(_SCANNER_PATH)], affected_modules=["wp15_governance_convergence_scan", "documentation"], affected_workflows=[], recommended_action="Restore both the scanner and the exemptions register before certifying exemption group coverage.", evidence={"scanner_ok": scanner["ok"], "exemptions_doc_present": exemptions_doc["exists"]}))

    cards.append(_card(section_id="operator-experience", card_id="drilldown-contract", title="Investigation Drill-Down Contract", status="unknown", summary="The drill-down completeness contract is computed after the KPI set is assembled.", root_cause_explanation="Pending module contract evaluation.", endpoint="internal:operational-health-contract", evidence_source_label="Operational health dashboard payload contract", producer="operational health module assembler", checked_at=generated_at, last_successful_refresh=generated_at, verified_at=generated_at, affected_files=["backend/routes/admin_operational_health.py", "frontend/src/components/admin/operational-health/OperationalHealthDashboardShell.jsx"], affected_modules=["operational_health_dashboard"], affected_workflows=[], recommended_action="", evidence={}))

    required_fields = ["status", "summary", "root_cause_explanation", "endpoint", "evidence_source_label", "producer", "checked_at", "last_successful_refresh", "affected_assets"]
    missing_by_card = []
    for card in cards:
        if card["id"] == "drilldown-contract":
            continue
        missing = []
        for field in required_fields:
            value = card.get(field)
            if field == "affected_assets":
                if not any((value or {}).values()):
                    missing.append(field)
                continue
            if value in (None, "", {}):
                missing.append(field)
        if missing:
            missing_by_card.append({"card_id": card["id"], "missing_fields": missing})
    completeness_status = "green" if not missing_by_card else "red"
    for card in cards:
        if card["id"] != "drilldown-contract":
            continue
        card["status"] = completeness_status
        card["summary"] = ("Every KPI exposes its state, evidence source, timestamps, producer, affected assets, and remediation guidance." if completeness_status == "green" else "One or more KPIs are missing required investigation fields.")
        card["root_cause_explanation"] = ("The dashboard contract is complete for every KPI card and drill-down." if completeness_status == "green" else "Some KPI cards are missing mandatory investigation metadata.")
        card["recommended_action"] = "Add the missing investigation metadata before relying on the dashboard for operator drill-down." if completeness_status != "green" else ""
        card["evidence"] = {"missing_by_card": missing_by_card, "required_fields": required_fields}
        card["affected_assets"] = {"files": ["backend/routes/admin_operational_health.py", "frontend/src/components/admin/operational-health/OperationalHealthDashboardShell.jsx", "frontend/src/components/admin/trust/TrustPrimitives.jsx"], "modules": ["operational_health_dashboard"], "workflows": []}
        break

    return cards


def _build_sections(cards: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    sections: List[Dict[str, Any]] = []
    for section_id, label in _SECTION_DEFS:
        section_cards = [card for card in cards if card.get("section_id") == section_id]
        sections.append({"id": section_id, "label": label, "status": _worst_status(section_cards), "cards": section_cards})
    return sections


def _snapshot_cards(cards: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            "id": card.get("id"),
            "title": card.get("title"),
            "section_id": card.get("section_id"),
            "status": card.get("status"),
            "checked_at": card.get("checked_at"),
            "verified_at": card.get("verified_at"),
            "endpoint": card.get("endpoint"),
            "producer": card.get("producer"),
            "root_cause_explanation": card.get("root_cause_explanation"),
        }
        for card in cards
    ]


def _snapshot_id(module_id: str, generated_at: str, overall_status: str, commit_sha: str) -> str:
    digest = hashlib.sha256(f"{module_id}:{generated_at}:{overall_status}:{commit_sha}".encode("utf-8")).hexdigest()[:16]
    return f"ohs-{digest}"


async def _persist_operational_health_artifacts(runtime_db, snapshot: Dict[str, Any], certification_event: Dict[str, Any], golden_path_run: Dict[str, Any]) -> None:
    snapshot_doc = json.loads(json.dumps(snapshot))
    await runtime_db[_SNAPSHOT_COLLECTION].insert_one(snapshot_doc)
    golden_path_doc = json.loads(json.dumps(golden_path_run))
    await runtime_db[_GOLDEN_PATH_COLLECTION].insert_one(golden_path_doc)
    existing = await runtime_db[_CERTIFICATION_COLLECTION].count_documents({"event_key": certification_event["event_key"]}, limit=1)
    if existing == 0:
        cert_doc = json.loads(json.dumps(certification_event))
        await runtime_db[_CERTIFICATION_COLLECTION].insert_one(cert_doc)


async def _load_kpi_trends(runtime_db, module_id: str, limit: int = 60) -> Dict[str, List[Dict[str, Any]]]:
    cursor = runtime_db[_SNAPSHOT_COLLECTION].find({"module_id": module_id}, {"_id": 0}).sort("evaluation_timestamp", -1).limit(limit)
    snapshots = [row async for row in cursor]
    snapshots.reverse()
    trends: Dict[str, List[Dict[str, Any]]] = {}
    prior_by_card: Dict[str, Dict[str, Any]] = {}
    for snapshot in snapshots:
        for card in snapshot.get("cards") or []:
            prior = prior_by_card.get(card["id"])
            if prior is None or prior.get("status") != card.get("status"):
                trends.setdefault(card["id"], []).append({
                    "snapshot_id": snapshot.get("snapshot_id"),
                    "timestamp": snapshot.get("evaluation_timestamp"),
                    "prior_state": prior.get("status") if prior else None,
                    "new_state": card.get("status"),
                    "trigger": card.get("root_cause_explanation"),
                    "evidence_reference": card.get("endpoint"),
                    "producer": card.get("producer"),
                    "associated_run": snapshot.get("snapshot_id"),
                })
            prior_by_card[card["id"]] = card
    return {key: value[-6:] for key, value in trends.items()}


async def _load_certification_history(runtime_db, limit: int = 20) -> List[Dict[str, Any]]:
    cursor = runtime_db[_CERTIFICATION_COLLECTION].find({}, {"_id": 0}).sort("timestamp", -1).limit(limit)
    return [row async for row in cursor]


def make_router(db, require_admin_only_dep) -> APIRouter:
    router = APIRouter(tags=["operational-health"])

    @router.get("/api/admin/operational-health/modules")
    async def operational_health_modules(_: Any = Depends(require_admin_only_dep)) -> Dict[str, Any]:
        return {"framework_id": "operational-health-dashboard", "framework_label": "Operational Health Dashboard", "contract": "Shared health framework for constitutional systems. Enterprise Governance is the first live module.", "modules": _MODULE_CATALOG}

    @router.get("/api/admin/operational-health/modules/{module_id}")
    async def operational_health_module(module_id: str, request: Request, _: Any = Depends(require_admin_only_dep)) -> Dict[str, Any]:
        if module_id != "enterprise-governance":
            raise HTTPException(status_code=404, detail="Operational health module not found")

        runtime_db = _runtime_db(request, db)
        generated_at = _now_iso()
        headers = _forward_headers(request)
        async with httpx.AsyncClient(timeout=_PROBE_TIMEOUT_S) as client:
            probe_tasks = {key: _probe_json(client, path, headers) for key, path in _PROBE_PATHS.items()}
            probe_results = await asyncio.gather(*probe_tasks.values())
        probes = {key: value for key, value in zip(probe_tasks.keys(), probe_results)}
        scanner = await asyncio.to_thread(_run_scanner)
        docs = _build_document_evidence()
        workflow_evidence = _workflow_gate_evidence()
        route_evidence = _route_registration_evidence()

        cards = _build_cards(probes=probes, scanner=scanner, docs=docs, workflow_evidence=workflow_evidence, route_evidence=route_evidence, generated_at=generated_at)
        sections = _build_sections(cards)
        all_cards = [card for section in sections for card in section["cards"]]
        counts = count_statuses(all_cards)
        overall_status = _worst_status(all_cards)
        certification_state = _build_constitutional_certification(docs, scanner, generated_at)
        condition_inventory = _build_condition_inventory(all_cards, generated_at)
        golden_path = _build_golden_path_results(probes["trust_spine"], probes["production_certification"], generated_at)
        status_engine = _build_status_engine_contract()
        exemptions = _build_exemption_entries(scanner)
        commit_sha = certification_state["commit_sha"]
        snapshot_id = _snapshot_id(module_id, generated_at, overall_status, commit_sha)
        operational_health = {
            "state": overall_status.upper(),
            "evaluated_at": generated_at,
            "primary_reason": condition_inventory["primary_reason"],
            "counts": counts,
        }
        snapshot = {
            "snapshot_id": snapshot_id,
            "module_id": module_id,
            "evaluation_timestamp": generated_at,
            "commit_sha": commit_sha,
            "constitutional_certification": certification_state,
            "operational_health": operational_health,
            "cards": _snapshot_cards(all_cards),
            "red_driver_ids": [row["kpi_id"] for row in condition_inventory["red_drivers"]],
            "amber_watch_ids": [row["kpi_id"] for row in condition_inventory["amber_watchlist"]],
        }
        certification_event = {
            "event_key": f"{certification_state['state']}:{certification_state['certified_at']}:{commit_sha}",
            "timestamp": certification_state["certified_at"],
            "commit": commit_sha,
            "environment": certification_state["environment"],
            "scanner_counts": certification_state["scanner_counts"],
            "exemption_count": exemptions["count"],
            "test_suites": ["wp15_governance_convergence_scan", "wp15_operational_health", "wp15_enterprise_governance"],
            "test_totals": {"dashboard_checks": len(all_cards), "fixture_checks": len(status_engine["fixture_results"]), "golden_path_monitors": len(golden_path["results"])},
            "golden_path_results": {"counts": golden_path["counts"], "non_green": [row["workflow_id"] for row in golden_path["results"] if row["status"] != "green"]},
            "trust_spine_evidence_summary": {"red_driver_count": len(condition_inventory["red_drivers"]), "primary_reason": condition_inventory["primary_reason"]},
            "determination": certification_state["state"],
            "evidence_links": [str(_DOC_FILES["final_certification"]), str(_DOC_FILES["continuous_certification"])],
            "reviewer_or_automation_identity": "operational-health-dashboard",
        }
        golden_path_run = {
            "run_id": f"gpr-{snapshot_id}",
            "module_id": module_id,
            "timestamp": generated_at,
            "environment": "preview",
            "results": golden_path["results"],
            "counts": golden_path["counts"],
        }
        await _persist_operational_health_artifacts(runtime_db, snapshot, certification_event, golden_path_run)
        kpi_trends = await _load_kpi_trends(runtime_db, module_id)
        certification_history = await _load_certification_history(runtime_db)
        truth = derived_truth_payload(
            "enterprise_governance_health_module",
            canonical_owner_route="/api/admin/governance/registry",
            derivation_explanation="This module consumes the enterprise governance registry, Trust Spine, certification, scanner, workflow, and documentation evidence. It may summarize or downgrade posture, but it never replaces the canonical owner of any child source.",
            canonical_status={"green": "VERIFIED", "yellow": "DEGRADED", "red": "MISMATCH", "unknown": "UNVERIFIABLE"}[overall_status],
            derived_status={"green": "VERIFIED", "yellow": "DEGRADED", "red": "MISMATCH", "unknown": "UNVERIFIABLE"}[overall_status],
            conflicts=[] if overall_status != "red" else ["At least one governance KPI currently reports RED evidence."],
            evidence_age_source="generated_at",
            stale_evidence=counts["unknown"] > 0,
        )

        return {
            "framework_id": "operational-health-dashboard",
            "framework_label": "Operational Health Dashboard",
            "framework_version": "1.0",
            "generated_at": generated_at,
            "determination": f"WP-15 CERTIFICATION VALID — OPERATIONAL HEALTH {operational_health['state']}" if certification_state["state"] == "VERIFIED — GO" else "WP-15 CERTIFICATION UNDER REVIEW",
            "module": {
                "id": "enterprise-governance",
                "label": "Enterprise Governance",
                "subtitle": "The first constitutional module on the shared operational health dashboard framework.",
                "route": "/admin/governance",
                "authority_statement": "Trust Spine and other canonical evidence sources remain authoritative. This module is a read-only consumer of those sources.",
                "future_modules": _MODULE_CATALOG,
                "quick_links": [
                    {"label": "Roles", "to": "/admin/governance/roles"},
                    {"label": "Policies", "to": "/admin/governance/policies"},
                    {"label": "Decisions", "to": "/admin/governance/decisions"},
                    {"label": "Audit", "to": "/admin/governance/audit"},
                    {"label": "Trust", "to": "/admin/governance-trust"},
                    {"label": "Sessions", "to": "/admin/sessions"},
                ],
            },
            "constitutional_certification": certification_state,
            "current_operational_health": operational_health,
            "overall_status": overall_status,
            "counts": counts,
            "red_drivers": condition_inventory["red_drivers"],
            "amber_watchlist": condition_inventory["amber_watchlist"],
            "status_engine": status_engine,
            "golden_path": golden_path,
            "known_exemptions": exemptions,
            "historical_kpi_trends": kpi_trends,
            "certification_history": certification_history,
            "snapshot_id": snapshot_id,
            "truth_surface": canonical_truth_surface("enterprise_governance_health_module"),
            "truth_relationship": truth["relationship"],
            "source_endpoints": sorted({card.get("endpoint") for card in all_cards if card.get("endpoint")}),
            "sections": sections,
            "kpi_metadata": standardize_prediction_metadata(
                identifier="WP17A-KPI-025",
                display_name="Enterprise Governance Health",
                description="Operational health module over governance registry, trust spine, certification, and route registration evidence.",
                formula={
                    "overall_status": "worst status across governance section cards",
                    "counts": "status bucket counts across governance health cards",
                },
                owner="governance-trust",
                refresh_interval="on request",
                confidence="HIGH",
                validation_status={"green": "VERIFIED", "yellow": "DEGRADED", "red": "MISMATCH", "unknown": "UNVERIFIABLE"}[overall_status],
                dependencies=["governance registry", "trust spine", "production certification", "workflow gates"],
                data_freshness="live request-time snapshot + repository artifact mtimes",
                consumer_portals=["Admin", "Governance", "Trust Center"],
                exception_notes=["This module is an aggregator only; child systems remain canonical truth owners."],
                extra={
                    "category": "Admin",
                    "source_of_truth": ["governance registry", "trust spine", "production certification", "route registration evidence"],
                    "api_endpoint": "/api/admin/operational-health/modules/enterprise-governance",
                    "drilldown_source": "/admin/governance",
                    "status_reason": "Governance health is derived from live evidence and repository-backed gate artifacts without inventing green states when evidence is missing.",
                },
            ),
        }

    return router


__all__ = ["make_router"]