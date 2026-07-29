from __future__ import annotations

import json
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple


BACKEND_ROOT = Path("/app/backend")
FRONTEND_ROOT = Path("/app/frontend/src")
APP_ROOT = Path("/app")
SCANNER_SCHEMA_VERSION = "2.0.0"
DETECTION_RULES_VERSION = "2.0.0"
METRIC_MODEL_VERSION = "2.0.0"
BASELINE_EXPANSION_REASON = "WP-15C Baseline Expansion — Frontend Request-Lifecycle Surface Added"
SKIP_PARTS = {"__pycache__", "node_modules", "dist", "build"}
SKIP_FILE_NAMES = {"wp15_governance_convergence_scan.py"}
SPECIAL_CASE_NAMES = {"auth.py", "pm_auth.py", "mfa.py"}
BACKEND_SCAN_FRAGMENTS = ("/routes/", "/lib/", "/services/")
DISPLAY_ONLY_TOKENS = (
    "url=",
    "base_url",
    "label",
    "subtitle",
    "title",
    "recipient_role",
    "assignee_role",
)
AUTH_DECISION_TOKENS = (
    "authorize",
    "authorization",
    "permission",
    "scope",
    "allowed",
    "approval",
    "governance",
    "access",
)
PORTAL_HEADER_TOKENS = (
    "X-Admin-Token",
    "X-PM-Token",
    "X-HR-Token",
    "X-Safety-Token",
    "X-Shop-Token",
    "X-Dispatch-Token",
    "X-FL-Token",
    "X-Directory-Token",
)
CANONICAL_FRONTEND_FILES = {
    "/frontend/src/lib/authHeaders.js",
    "/frontend/src/lib/api.js",
    "/frontend/src/lib/fetchPortalAuth.js",
    "/frontend/src/lib/axiosPortalAuth.js",
    "/frontend/src/lib/xhrPortalAuth.js",
    "/frontend/src/lib/sessionReset.js",
    "/frontend/src/lib/tokenValidation.js",
}


def should_skip(path: Path) -> bool:
    return any(part in SKIP_PARTS for part in path.parts) or path.name in SKIP_FILE_NAMES


def relpath(path: Path) -> str:
    return f"/{path.relative_to(APP_ROOT).as_posix()}"


def safe_git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(APP_ROOT), "rev-parse", "HEAD"],
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def enclosing_symbol(lines: List[str], line_no: int, *, frontend: bool = False) -> str:
    py_patterns = [
        re.compile(r"^\s*async\s+def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\("),
        re.compile(r"^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\("),
        re.compile(r"^\s*class\s+([A-Za-z_][A-Za-z0-9_]*)\b"),
    ]
    js_patterns = [
        re.compile(r"^\s*function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\("),
        re.compile(r"^\s*async\s+function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\("),
        re.compile(r"^\s*const\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?:async\s*)?\([^=]*=>"),
        re.compile(r"^\s*export\s+function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\("),
        re.compile(r"^\s*export\s+const\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?:async\s*)?\([^=]*=>"),
    ]
    patterns = js_patterns if frontend else py_patterns
    for idx in range(line_no - 1, -1, -1):
        text = lines[idx]
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                return match.group(1)
    return "<module>"


def backend_has_auth_context(text: str, nearby: str) -> bool:
    hay = f"{text}\n{nearby}".lower()
    return any(token in hay for token in AUTH_DECISION_TOKENS)


def backend_is_display_only(text: str, nearby: str) -> bool:
    hay = f"{text}\n{nearby}".lower()
    return any(token in hay for token in DISPLAY_ONLY_TOKENS)


def append_raw(
    findings: List[Dict[str, object]],
    *,
    path: str,
    line: int,
    category: str,
    reason: str,
    snippet: str,
    symbol: str,
    domain: str,
    layer: str,
) -> None:
    findings.append(
        {
            "path": path,
            "line": line,
            "symbol": symbol,
            "category": category,
            "reason": reason,
            "snippet": snippet[:220],
            "domain": domain,
            "layer": layer,
        }
    )


def scan_backend() -> List[Dict[str, object]]:
    findings: List[Dict[str, object]] = []
    for path in BACKEND_ROOT.rglob("*.py"):
        if should_skip(path):
            continue
        rel = relpath(path)
        if not any(fragment in rel for fragment in BACKEND_SCAN_FRAGMENTS):
            continue
        lines = path.read_text(errors="ignore").splitlines()
        for line_no, line in enumerate(lines, 1):
            text = line.strip()
            nearby = "\n".join(lines[max(0, line_no - 20):line_no])
            symbol = enclosing_symbol(lines, line_no)
            if not text or text.startswith("#"):
                continue
            if "require_governed_action(" in text or "evaluate_governance_action(" in text:
                append_raw(
                    findings,
                    path=rel,
                    line=line_no,
                    category="canonical",
                    reason="Canonical Governance Engine call",
                    snippet=text,
                    symbol=symbol,
                    domain="business_authorization",
                    layer="backend",
                )
                continue
            if any(
                token in text
                for token in (
                    "governance_project_scope_filter(",
                    "governance_project_scope_allows(",
                    "governance_project_scope(",
                )
            ):
                append_raw(
                    findings,
                    path=rel,
                    line=line_no,
                    category="canonical",
                    reason="Canonical governance scope adapter",
                    snippet=text,
                    symbol=symbol,
                    domain="business_authorization",
                    layer="backend",
                )
                continue
            if "WP15_SPECIAL_CASE_INFRASTRUCTURE" in nearby:
                append_raw(
                    findings,
                    path=rel,
                    line=line_no,
                    category="special_case_infrastructure",
                    reason="Documented governed-scope adapter",
                    snippet=text,
                    symbol=symbol,
                    domain="request_lifecycle",
                    layer="backend",
                )
                continue
            if path.name == "legacy_imports.py" and "_li_scope_filter(" in text:
                append_raw(
                    findings,
                    path=rel,
                    line=line_no,
                    category="special_case_infrastructure",
                    reason="Upload-portal partition after canonical actor gate",
                    snippet=text,
                    symbol=symbol,
                    domain="manual_review",
                    layer="backend",
                )
                continue
            if rel.endswith("/odr/routes.py") and "build_odr_scope_filter(" in text:
                append_raw(
                    findings,
                    path=rel,
                    line=line_no,
                    category="special_case_infrastructure",
                    reason="Read-visibility projector after auth gate",
                    snippet=text,
                    symbol=symbol,
                    domain="manual_review",
                    layer="backend",
                )
                continue
            if path.name == "integration_truth.py" and symbol == "_retirement_recommendation":
                append_raw(
                    findings,
                    path=rel,
                    line=line_no,
                    category="special_case_infrastructure",
                    reason="Environment heuristic, not business authorization",
                    snippet=text,
                    symbol=symbol,
                    domain="manual_review",
                    layer="backend",
                )
                continue
            if path.name == "enterprise_governance.py" and symbol == "_projection_defaults" and "is_super_admin" in text:
                append_raw(
                    findings,
                    path=rel,
                    line=line_no,
                    category="special_case_infrastructure",
                    reason="Identity projection snapshot field",
                    snippet=text,
                    symbol=symbol,
                    domain="manual_review",
                    layer="backend",
                )
                continue
            if path.name == "admin_directory_k4.py" and symbol == "_directory_full_view" and "is_super_admin" in text:
                append_raw(
                    findings,
                    path=rel,
                    line=line_no,
                    category="special_case_infrastructure",
                    reason="Directory view projection field",
                    snippet=text,
                    symbol=symbol,
                    domain="manual_review",
                    layer="backend",
                )
                continue
            if path.name in SPECIAL_CASE_NAMES or path.name.endswith("_deps.py") or "/routes/" not in rel:
                if any(tok in text for tok in ("X-Admin-Token", "X-PM-Token", "X-HR-Token", "X-Safety-Token")):
                    append_raw(
                        findings,
                        path=rel,
                        line=line_no,
                        category="special_case_infrastructure",
                        reason="Authentication/token boundary",
                        snippet=text,
                        symbol=symbol,
                        domain="request_lifecycle",
                        layer="backend",
                    )
                    continue
                if path.name.endswith("_deps.py") and "for tok, role in (" in text:
                    append_raw(
                        findings,
                        path=rel,
                        line=line_no,
                        category="special_case_infrastructure",
                        reason="Infrastructure portal-token probe",
                        snippet=text,
                        symbol=symbol,
                        domain="request_lifecycle",
                        layer="backend",
                    )
                    continue
            if "compute_pm_scope(" in text:
                append_raw(
                    findings,
                    path=rel,
                    line=line_no,
                    category="legacy_migratable",
                    reason="Module-specific PM scope authorization",
                    snippet=text,
                    symbol=symbol,
                    domain="business_authorization",
                    layer="backend",
                )
                continue
            if path.name == "tasks_notifications.py" and ("build_notif_filter(" in text or "_scope_filter(" in text):
                append_raw(
                    findings,
                    path=rel,
                    line=line_no,
                    category="special_case_infrastructure",
                    reason="Documented governed-scope adapter",
                    snippet=text,
                    symbol=symbol,
                    domain="request_lifecycle",
                    layer="backend",
                )
                continue
            if ("build_notif_filter(" in text or "_scope_filter(" in text) and "def " not in text:
                append_raw(
                    findings,
                    path=rel,
                    line=line_no,
                    category="legacy_migratable",
                    reason="Module-specific notification/task scope filter",
                    snippet=text,
                    symbol=symbol,
                    domain="business_authorization",
                    layer="backend",
                )
                continue
            if re.search(r"\brole\b\s*==\s*['\"](?:admin|pm)['\"]", text):
                if "def _search_url_for_role" in nearby or backend_is_display_only(text, nearby):
                    continue
                if path.name == "project_team_assignments.py" and symbol == "_is_pm_on_project":
                    append_raw(
                        findings,
                        path=rel,
                        line=line_no,
                        category="special_case_infrastructure",
                        reason="Domain classification branch",
                        snippet=text,
                        symbol=symbol,
                        domain="manual_review",
                        layer="backend",
                    )
                    continue
                if "pm_proj is not None" in text:
                    append_raw(
                        findings,
                        path=rel,
                        line=line_no,
                        category="special_case_infrastructure",
                        reason="Governed scope application branch",
                        snippet=text,
                        symbol=symbol,
                        domain="request_lifecycle",
                        layer="backend",
                    )
                    continue
                if backend_has_auth_context(text, nearby):
                    category = "legacy_migratable"
                    reason = "Inline role branch"
                    domain = "business_authorization"
                else:
                    category = "governance_candidate"
                    reason = "Role branch needs manual governance review"
                    domain = "manual_review"
                append_raw(
                    findings,
                    path=rel,
                    line=line_no,
                    category=category,
                    reason=reason,
                    snippet=text,
                    symbol=symbol,
                    domain=domain,
                    layer="backend",
                )
                continue
            if re.search(r"\brole\b\s+in\s+[\({]", text):
                if backend_is_display_only(text, nearby):
                    continue
                if path.name in {"canonical_truth.py", "oppc_intelligence.py", "project_team_assignments.py", "daily_reports.py"}:
                    append_raw(
                        findings,
                        path=rel,
                        line=line_no,
                        category="special_case_infrastructure",
                        reason="Domain classification branch",
                        snippet=text,
                        symbol=symbol,
                        domain="manual_review",
                        layer="backend",
                    )
                    continue
                if path.name in {"operational_constraints.py", "photo_governance.py", "employee_records.py", "employee_lifecycle.py"}:
                    append_raw(
                        findings,
                        path=rel,
                        line=line_no,
                        category="legacy_migratable",
                        reason="Route-local authorization helper",
                        snippet=text,
                        symbol=symbol,
                        domain="business_authorization",
                        layer="backend",
                    )
                    continue
                if backend_has_auth_context(text, nearby):
                    category = "legacy_migratable"
                    reason = "Inline role set check"
                    domain = "business_authorization"
                else:
                    category = "governance_candidate"
                    reason = "Role set check needs manual governance review"
                    domain = "manual_review"
                append_raw(
                    findings,
                    path=rel,
                    line=line_no,
                    category=category,
                    reason=reason,
                    snippet=text,
                    symbol=symbol,
                    domain=domain,
                    layer="backend",
                )
                continue
            if "is_super_admin" in text and "bool(" in text:
                if "{" in text and ":" in text and "permission" not in nearby.lower() and "allowed" not in nearby.lower():
                    continue
                if backend_has_auth_context(text, nearby):
                    category = "legacy_migratable"
                    reason = "Hard-coded super-admin branch"
                    domain = "business_authorization"
                else:
                    category = "governance_candidate"
                    reason = "Super-admin handling needs manual governance review"
                    domain = "manual_review"
                append_raw(
                    findings,
                    path=rel,
                    line=line_no,
                    category=category,
                    reason=reason,
                    snippet=text,
                    symbol=symbol,
                    domain=domain,
                    layer="backend",
                )
                continue
            if "HTTPException(status_code=403" in text and any(tok in text.lower() for tok in ("scope", "admin", "pm")):
                append_raw(
                    findings,
                    path=rel,
                    line=line_no,
                    category="legacy_migratable",
                    reason="Custom 403 authorization gate",
                    snippet=text,
                    symbol=symbol,
                    domain="business_authorization",
                    layer="backend",
                )
    return findings


def is_test_file(path: Path) -> bool:
    return any(part.startswith("__tests__") or part == "tests" for part in path.parts)


def looks_like_manual_header_builder(text: str) -> bool:
    return any(tok in text for tok in PORTAL_HEADER_TOKENS) and (
        "headers:" in text or "setRequestHeader" in text or "headers[" in text or "return {" in text
    )


def scan_frontend() -> List[Dict[str, object]]:
    findings: List[Dict[str, object]] = []
    if not FRONTEND_ROOT.exists():
        raise RuntimeError(f"Frontend scan root missing: {FRONTEND_ROOT}")
    for path in FRONTEND_ROOT.rglob("*"):
        if path.suffix not in {".js", ".jsx", ".ts", ".tsx"}:
            continue
        if should_skip(path) or is_test_file(path):
            continue
        rel = relpath(path)
        text = path.read_text(errors="ignore")
        lines = text.splitlines()
        if rel in CANONICAL_FRONTEND_FILES:
            symbol = enclosing_symbol(lines, 1, frontend=True)
            append_raw(
                findings,
                path=rel,
                line=1,
                category="special_case_infrastructure",
                reason="Canonical request-lifecycle infrastructure",
                snippet=(lines[0] if lines else rel),
                symbol=symbol,
                domain="request_lifecycle",
                layer="frontend",
            )
            continue
        if not any(tok in text for tok in PORTAL_HEADER_TOKENS):
            continue
        if "buildScopedPortalAuthHeaders(" in text or "buildPortalAuthHeaders(" in text:
            symbol = enclosing_symbol(lines, 1, frontend=True)
            append_raw(
                findings,
                path=rel,
                line=1,
                category="canonical",
                reason="Canonical scoped auth-header builder adoption",
                snippet=(lines[0] if lines else rel),
                symbol=symbol,
                domain="request_lifecycle",
                layer="frontend",
            )
            continue
        first_manual_line: Optional[int] = None
        first_manual_text: Optional[str] = None
        for idx, line in enumerate(lines, 1):
            if any(tok in line for tok in PORTAL_HEADER_TOKENS) and looks_like_manual_header_builder(line):
                first_manual_line = idx
                first_manual_text = line.strip()
                break
        if first_manual_line is None:
            continue
        symbol = enclosing_symbol(lines, first_manual_line, frontend=True)
        append_raw(
            findings,
            path=rel,
            line=first_manual_line,
            category="legacy_migratable",
            reason="Manual governed-request header construction",
            snippet=first_manual_text or "",
            symbol=symbol,
            domain="request_lifecycle",
            layer="frontend",
        )
    return findings


def normalize_findings(raw_findings: List[Dict[str, object]]) -> Dict[str, object]:
    implementation_sites: Dict[Tuple[str, str, str, str, str], Dict[str, object]] = {}
    constitutional_points: Dict[Tuple[str, str, str, str], Dict[str, object]] = {}
    module_breakdown: Dict[str, Counter] = defaultdict(Counter)
    portal_breakdown: Dict[str, Counter] = defaultdict(Counter)

    for row in raw_findings:
        path = str(row["path"])
        symbol = str(row["symbol"])
        category = str(row["category"])
        reason = str(row["reason"])
        domain = str(row["domain"])
        layer = str(row["layer"])
        line = int(row["line"])
        implementation_key = (path, symbol, category, reason, domain)
        point_key = (path, symbol, category, reason)

        if implementation_key not in implementation_sites:
            implementation_sites[implementation_key] = {
                "path": path,
                "symbol": symbol,
                "category": category,
                "reason": reason,
                "domain": domain,
                "layer": layer,
                "first_line": line,
                "occurrence_count": 0,
                "snippet": row["snippet"],
            }
        implementation_sites[implementation_key]["occurrence_count"] += 1

        if point_key not in constitutional_points:
            constitutional_points[point_key] = {
                "path": path,
                "symbol": symbol,
                "category": category,
                "reason": reason,
                "domain": domain,
                "layer": layer,
                "first_line": line,
                "raw_occurrence_count": 0,
                "snippet": row["snippet"],
            }
        constitutional_points[point_key]["raw_occurrence_count"] += 1

        module = "/".join(path.strip("/").split("/")[:4])
        module_breakdown[module][category] += 1
        if "pm" in path:
            portal_breakdown["pm"][category] += 1
        if "safety" in path:
            portal_breakdown["safety"][category] += 1
        if "shop" in path:
            portal_breakdown["shop"][category] += 1
        if "dispatch" in path:
            portal_breakdown["dispatch"][category] += 1
        if "hr" in path:
            portal_breakdown["hr"][category] += 1
        if "field_leadership" in path or "fl_" in path:
            portal_breakdown["field_leadership"][category] += 1
        if "admin" in path or "directory" in path:
            portal_breakdown["admin"][category] += 1

    normalized_points = list(constitutional_points.values())
    implementation_list = list(implementation_sites.values())
    normalized_counts = Counter(point["category"] for point in normalized_points)
    raw_counts = Counter(row["category"] for row in raw_findings)

    lifecycle_points = [p for p in normalized_points if p["domain"] == "request_lifecycle"]
    manual_header_points = [p for p in lifecycle_points if p["reason"] == "Manual governed-request header construction"]
    canonical_builder_points = [
        p for p in lifecycle_points if p["reason"] in (
            "Canonical scoped auth-header builder adoption",
            "Canonical request-lifecycle infrastructure",
        )
    ]
    lifecycle_total = len(lifecycle_points)
    lifecycle_compliance = 0.0
    if lifecycle_total:
        lifecycle_compliance = round((len(canonical_builder_points) / lifecycle_total) * 100, 2)

    by_reason = Counter((point["category"], point["reason"]) for point in normalized_points)
    shared_pattern_groups = [
        {
            "category": category,
            "reason": reason,
            "count": count,
        }
        for (category, reason), count in sorted(by_reason.items(), key=lambda item: (item[0][0], -item[1], item[0][1]))
    ]

    return {
        "raw_occurrence_counts": {
            "total": len(raw_findings),
            "canonical": raw_counts.get("canonical", 0),
            "legacy_migratable": raw_counts.get("legacy_migratable", 0),
            "special_case_infrastructure": raw_counts.get("special_case_infrastructure", 0),
            "governance_candidate": raw_counts.get("governance_candidate", 0),
            "dead_code": raw_counts.get("dead_code", 0),
        },
        "normalized_constitutional_counts": {
            "total": len(normalized_points),
            "canonical": normalized_counts.get("canonical", 0),
            "legacy_migratable": normalized_counts.get("legacy_migratable", 0),
            "special_case_infrastructure": normalized_counts.get("special_case_infrastructure", 0),
            "governance_candidate": normalized_counts.get("governance_candidate", 0),
            "dead_code": normalized_counts.get("dead_code", 0),
        },
        "business_authorization_convergence": {
            "legacy_scope_helpers": sum(1 for p in normalized_points if p["reason"] == "Module-specific PM scope authorization"),
            "inline_role_checks": sum(1 for p in normalized_points if p["reason"] in {"Inline role branch", "Inline role set check"}),
            "hard_coded_admin_checks": sum(1 for p in normalized_points if p["reason"] == "Hard-coded super-admin branch"),
            "duplicate_authorization": sum(1 for p in normalized_points if p["reason"] in {"Module-specific notification/task scope filter", "Custom 403 authorization gate"}),
            "category_f": normalized_counts.get("governance_candidate", 0),
        },
        "request_lifecycle_convergence": {
            "manual_auth_header_construction": len(manual_header_points),
            "canonical_request_builder_sites": len(canonical_builder_points),
            "total_request_lifecycle_sites": lifecycle_total,
            "canonical_request_builder_adoption_percentage": lifecycle_compliance,
        },
        "implementation_sites": implementation_list,
        "shared_pattern_groups": shared_pattern_groups,
        "constitutional_decision_points": normalized_points,
        "coverage_by_module": {
            module: dict(counter)
            for module, counter in sorted(module_breakdown.items())
        },
        "coverage_by_portal": {
            portal: dict(counter)
            for portal, counter in sorted(portal_breakdown.items())
        },
    }


def main() -> None:
    backend_findings = scan_backend()
    frontend_findings = scan_frontend()
    raw_findings = backend_findings + frontend_findings
    normalized = normalize_findings(raw_findings)

    summary = {
        "scanner_schema_version": SCANNER_SCHEMA_VERSION,
        "detection_rules_version": DETECTION_RULES_VERSION,
        "metric_model_version": METRIC_MODEL_VERSION,
        "repository_commit": safe_git_commit(),
        "scan_timestamp": datetime.now(timezone.utc).isoformat(),
        "comparable_to_previous_scan": False,
        "non_comparability_reason": BASELINE_EXPANSION_REASON,
        "newly_included_directories": ["/app/frontend/src"],
        "newly_included_languages": ["javascript", "jsx", "typescript", "tsx"],
        "newly_included_frontend_patterns": [
            "manual governed-request header construction",
            "canonical scoped auth-header builder adoption",
        ],
        "baseline_model_change": BASELINE_EXPANSION_REASON,
        "total_authorization_decision_points_discovered": normalized["normalized_constitutional_counts"]["total"],
        "canonical_governance_engine": normalized["normalized_constitutional_counts"]["canonical"],
        "legacy_but_migratable": normalized["normalized_constitutional_counts"]["legacy_migratable"],
        "special_case_infrastructure": normalized["normalized_constitutional_counts"]["special_case_infrastructure"],
        "governance_candidate_manual_review": normalized["normalized_constitutional_counts"]["governance_candidate"],
        "dead_or_unused_code": normalized["normalized_constitutional_counts"]["dead_code"],
        "manual_auth_header_construction": normalized["request_lifecycle_convergence"]["manual_auth_header_construction"],
        "raw_findings": raw_findings,
        **normalized,
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()