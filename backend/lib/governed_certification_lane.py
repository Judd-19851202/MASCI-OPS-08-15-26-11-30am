from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional


GOVERNED_CERTIFICATION_PROJECT_NUMBER = "ZZ-RUNTIME-CERT-2026"
GOVERNED_CERTIFICATION_PROJECT_NAME = "Runtime Certification — Internal Test Project"
GOVERNED_CERTIFICATION_PM_EMAIL = "cert.pm@example.com"
GOVERNED_CERTIFICATION_CO_PM_EMAILS = ["cert.copm@example.com"]
GOVERNED_CERTIFICATION_EMAILS = {
    GOVERNED_CERTIFICATION_PM_EMAIL,
    *GOVERNED_CERTIFICATION_CO_PM_EMAILS,
    "cert.foreman@example.com",
    "cert.dispatch@example.com",
    "cert.hr@example.com",
    "cert.safety@example.com",
    "cert.shop@example.com",
}
GOVERNED_CERTIFICATION_WORKFLOWS = [
    "daily-report",
    "trust-spine",
    "audit",
    "ods",
    "search",
    "pdf",
]


def _clean_email(value: Any) -> str:
    return str(value or "").strip().lower()


def _clean_emails(values: Optional[Iterable[Any]]) -> List[str]:
    out: List[str] = []
    seen = set()
    for raw in values or []:
        email = _clean_email(raw)
        if not email or "@" not in email or email in seen:
            continue
        seen.add(email)
        out.append(email)
    return out


def is_governed_certification_identity(identity: Optional[Dict[str, Any]]) -> bool:
    if not isinstance(identity, dict):
        return False
    email = _clean_email(identity.get("email"))
    if email in GOVERNED_CERTIFICATION_EMAILS:
        return True
    return email.startswith("cert.") and "@" in email


def is_governed_certification_project(doc_or_project_number: Any, project_name: Optional[str] = None) -> bool:
    if isinstance(doc_or_project_number, dict):
        project_number = str(doc_or_project_number.get("project_number") or "").strip()
        project_name = str(doc_or_project_number.get("project_name") or project_name or "").strip()
        if bool(doc_or_project_number.get("certification_project")):
            return True
    else:
        project_number = str(doc_or_project_number or "").strip()
        project_name = str(project_name or "").strip()

    project_number_lower = project_number.lower()
    project_name_lower = project_name.lower()
    return (
        project_number_lower == GOVERNED_CERTIFICATION_PROJECT_NUMBER.lower()
        or project_number_lower.startswith("zz-runtime-cert-")
        or project_name_lower == GOVERNED_CERTIFICATION_PROJECT_NAME.lower()
    )


def build_governed_routing_override() -> Dict[str, Any]:
    to = [GOVERNED_CERTIFICATION_PM_EMAIL]
    cc = list(GOVERNED_CERTIFICATION_CO_PM_EMAILS)
    return {
        "enabled": True,
        "reason": "governed_production_certification_lane",
        "pm_email": GOVERNED_CERTIFICATION_PM_EMAIL,
        "pm_name": "Certification PM",
        "to": to,
        "cc": cc,
        "all": to + cc,
    }


def should_apply_governed_daily_report_lane(doc: Dict[str, Any]) -> bool:
    if bool(doc.get("certification_record")):
        return True
    if not is_governed_certification_project(doc):
        return False
    return is_governed_certification_identity(doc.get("prepared_by_identity"))


def apply_governed_daily_report_lane(
    doc: Dict[str, Any],
    *,
    project_doc: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if not should_apply_governed_daily_report_lane(doc):
        return doc

    out = dict(doc)
    out["certification_record"] = True
    out["synthetic_record"] = True
    out["hidden_from_operations"] = True
    out["certification_track_id"] = str(out.get("certification_track_id") or "27.11B")
    out["certification_release_reason"] = str(
        out.get("certification_release_reason") or "governed_production_certification_lane"
    )

    required = out.get("certification_required_workflows")
    existing_required: List[str]
    if required is None:
        existing_required = []
    elif isinstance(required, list):
        existing_required = [str(x).strip() for x in required if str(x).strip()]
    else:
        existing_required = [str(required).strip()] if str(required).strip() else []

    merged_required: List[str] = []
    seen_required = set()
    for value in existing_required + GOVERNED_CERTIFICATION_WORKFLOWS:
        if not value or value in seen_required:
            continue
        seen_required.add(value)
        merged_required.append(value)
    out["certification_required_workflows"] = merged_required

    routing_override = build_governed_routing_override()
    out["routing_override"] = routing_override
    out["certification_lane_allows_email"] = True
    out["email_dispatch_suppressed"] = False

    identity = out.get("prepared_by_identity") if isinstance(out.get("prepared_by_identity"), dict) else {}
    snapshot = {
        "project_number": (project_doc or {}).get("project_number") or out.get("project_number"),
        "project_name": (project_doc or {}).get("project_name") or out.get("project_name"),
        "pm_email": _clean_email((project_doc or {}).get("pm_email")),
        "co_pm_emails": _clean_emails((project_doc or {}).get("co_pm_emails")),
        "active": bool((project_doc or {}).get("active", True)),
    }
    out["certification_lane"] = {
        "mode": "governed_production",
        "project_verified": is_governed_certification_project(out),
        "identity_verified": is_governed_certification_identity(identity),
        "identity": {
            "directory": str(identity.get("directory") or ""),
            "user_id": str(identity.get("user_id") or ""),
            "name": str(identity.get("name") or ""),
            "email": _clean_email(identity.get("email")),
            "role": str(identity.get("role") or ""),
        },
        "routing": routing_override,
        "project_snapshot": snapshot,
        "preserves": {
            "trust_spine": True,
            "audit": True,
            "ods": True,
            "search_hidden": True,
            "pdf": True,
            "evidence": True,
        },
    }
    return out


__all__ = [
    "GOVERNED_CERTIFICATION_PROJECT_NUMBER",
    "GOVERNED_CERTIFICATION_PROJECT_NAME",
    "GOVERNED_CERTIFICATION_PM_EMAIL",
    "GOVERNED_CERTIFICATION_CO_PM_EMAILS",
    "GOVERNED_CERTIFICATION_WORKFLOWS",
    "apply_governed_daily_report_lane",
    "build_governed_routing_override",
    "is_governed_certification_identity",
    "is_governed_certification_project",
    "should_apply_governed_daily_report_lane",
]