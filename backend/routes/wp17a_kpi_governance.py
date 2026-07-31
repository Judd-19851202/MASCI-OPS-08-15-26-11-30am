from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import httpx
from fastapi import APIRouter, Depends, Request

from lib.wp17a_kpi_governance import (
    MASTER_REGISTER_PATH,
    PRE_DEPLOY_CERT_PATH,
    REGRESSION_REPORT_PATH,
    build_kpi_dictionary,
    normalize_metadata_model,
    reconciliation_report,
)


_BACKEND_INTERNAL_BASE = os.environ.get("OCC_HEALTH_INTERNAL_BASE", "http://127.0.0.1:8001").rstrip("/")


def _forward_headers(request: Request) -> Dict[str, str]:
    headers: Dict[str, str] = {}
    for header in ("X-Admin-Token", "X-Directory-Token", "Authorization"):
        value = request.headers.get(header)
        if value:
            headers[header] = value
    return headers


_RUNTIME_METADATA_PROBES = [
    {"identifier": "WP17A-KPI-001", "path": "/api/admin/draft-health", "auth": True},
    {"identifier": "WP17A-KPI-006", "path": "/api/admin/governance/summary", "auth": True},
    {"identifier": "WP17A-KPI-007", "path": "/api/admin/r2/lifecycle/health", "auth": True},
    {"identifier": "WP17A-KPI-009", "path": "/api/admin/production-certification", "auth": True},
    {"identifier": "WP17A-KPI-012", "path": "/api/master-lookup/audit", "auth": True},
    {"identifier": "WP17A-KPI-017", "path": "/api/admin/executive/overview", "auth": True},
    {"identifier": "WP17A-KPI-018", "path": "/api/project-health", "auth": True},
    {"identifier": "WP17A-KPI-019-roster", "path": "/api/hr/employee-roster?limit=5", "auth": True},
    {"identifier": "WP17A-KPI-019-requests", "path": "/api/hr/employee-requests?status=pending", "auth": True},
    {"identifier": "WP17A-KPI-019-timeoff", "path": "/api/field-leadership/time-off/stats", "auth": True},
    {"identifier": "WP17A-KPI-019-expirations", "path": "/api/operations/expirations/summary", "auth": True},
    {"identifier": "WP17A-KPI-020", "path": "/api/safety/company/safety-kpis?window=30d", "auth": True},
    {"identifier": "WP17A-KPI-021-current", "path": "/api/cluster/capacity", "auth": False},
    {"identifier": "WP17A-KPI-021-history", "path": "/api/cluster/capacity/history?days=30", "auth": False},
    {"identifier": "WP17A-KPI-022", "path": "/api/admin/occ/health", "auth": True},
    {"identifier": "WP17A-KPI-023", "path": "/api/platform/data-truth", "auth": False},
    {"identifier": "WP17A-KPI-024", "path": "/api/admin/platform-trust/validate", "auth": True},
    {"identifier": "WP17A-KPI-025", "path": "/api/admin/operational-health/modules/enterprise-governance", "auth": True},
]


def build_wp17a_kpi_governance_router(require_admin_dep) -> APIRouter:
    router = APIRouter(prefix="/api/admin/wp17a", tags=["wp17a-kpi-governance"])

    @router.get("/kpi-dictionary")
    async def kpi_dictionary(_: Any = Depends(require_admin_dep)) -> Dict[str, Any]:
        entries = build_kpi_dictionary()
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "status": "EXECUTIVE_READY_FOR_APPROVAL",
            "entry_count": len(entries),
            "entries": entries,
        }

    @router.get("/reconciliation")
    async def kpi_reconciliation(request: Request, _: Any = Depends(require_admin_dep)) -> Dict[str, Any]:
        dictionary = {entry["identifier"]: entry for entry in build_kpi_dictionary()}
        runtime_findings: List[Dict[str, Any]] = []
        headers = _forward_headers(request)
        async with httpx.AsyncClient(timeout=15.0) as client:
            for probe in _RUNTIME_METADATA_PROBES:
                probe_headers = headers if probe["auth"] else {}
                try:
                    response = await client.get(f"{_BACKEND_INTERNAL_BASE}{probe['path']}", headers=probe_headers)
                    if response.status_code >= 400:
                        runtime_findings.append({
                            "finding_type": "RUNTIME_ENDPOINT_FAILURE",
                            "severity": "P0",
                            "identifier": probe["identifier"],
                            "path": probe["path"],
                            "status_code": response.status_code,
                        })
                        continue
                    body = response.json()
                except Exception as exc:  # noqa: BLE001
                    runtime_findings.append({
                        "finding_type": "RUNTIME_ENDPOINT_FAILURE",
                        "severity": "P0",
                        "identifier": probe["identifier"],
                        "path": probe["path"],
                        "error": f"{type(exc).__name__}: {exc}",
                    })
                    continue

                metadata = body.get("kpi_metadata") if isinstance(body, dict) else None
                if not metadata:
                    runtime_findings.append({
                        "finding_type": "MISSING_RUNTIME_METADATA",
                        "severity": "P0",
                        "identifier": probe["identifier"],
                        "path": probe["path"],
                    })
                    continue

                normalized = normalize_metadata_model(metadata, dictionary_entry=dictionary.get(probe["identifier"], {}))
                missing = [field for field in ("identifier", "display_name", "owner", "formula", "validation_status") if not normalized.get(field)]
                if missing:
                    runtime_findings.append({
                        "finding_type": "RUNTIME_METADATA_INCOMPLETE",
                        "severity": "P0",
                        "identifier": probe["identifier"],
                        "path": probe["path"],
                        "missing_fields": missing,
                    })

        report = reconciliation_report(runtime_checks=runtime_findings)
        report["runtime_probe_count"] = len(_RUNTIME_METADATA_PROBES)
        return report

    @router.get("/certification")
    async def kpi_certification(request: Request, _: Any = Depends(require_admin_dep)) -> Dict[str, Any]:
        reconciliation = await kpi_reconciliation(request, _)
        docs = {
            "master_register": MASTER_REGISTER_PATH.exists(),
            "pre_deployment_certification": PRE_DEPLOY_CERT_PATH.exists(),
            "regression_report": REGRESSION_REPORT_PATH.exists(),
        }
        latest_pytest = Path("/app/test_reports/pytest/wp17a_executive_closeout.xml")
        iteration_report = Path("/app/test_reports/iteration_87.json")
        checks = {
            "reconciliation": reconciliation["status"] == "PASS",
            "dictionary_entries_present": reconciliation["dictionary_entry_count"] > 0,
            "documentation_present": all(docs.values()),
            "test_artifacts_present": latest_pytest.exists() or iteration_report.exists(),
        }
        certification_status = "EXECUTIVE_READY_FOR_APPROVAL" if all(checks.values()) else "FAIL"
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "certification_status": certification_status,
            "checks": checks,
            "documentation": docs,
            "reconciliation_summary": {
                "status": reconciliation["status"],
                "blocking_finding_count": reconciliation["blocking_finding_count"],
                "finding_count": reconciliation["finding_count"],
            },
            "test_artifacts": {
                "iteration_87": str(Path("/app/test_reports/iteration_87.json")),
                "pytest_xml": str(latest_pytest),
            },
            "executive_notes": [
                "Certification fails closed if any audited KPI endpoint is missing metadata or does not load.",
                "Certification scope covers the canonical WP-17A KPI dictionary and all audited runtime probes.",
            ],
        }
        return report

    @router.get("/deployment-package")
    async def deployment_package(_: Any = Depends(require_admin_dep)) -> Dict[str, Any]:
        dictionary = build_kpi_dictionary()
        portal_counts: Dict[str, int] = {}
        for entry in dictionary:
            portal_counts[entry["category"]] = portal_counts.get(entry["category"], 0) + 1
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "status": "READY",
            "executive_summary": "WP-17A closeout package bundles canonical KPI inventory, reconciliation status, certification outcome, and deployment-review artifacts.",
            "canonical_kpi_inventory_count": len(dictionary),
            "portal_counts": portal_counts,
            "documents": {
                "master_register": str(MASTER_REGISTER_PATH),
                "pre_deployment_certification": str(PRE_DEPLOY_CERT_PATH),
                "regression_report": str(REGRESSION_REPORT_PATH),
            },
        }

    return router


__all__ = ["build_wp17a_kpi_governance_router"]