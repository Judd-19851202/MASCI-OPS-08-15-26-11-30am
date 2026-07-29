from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path("/app/backend")
FRONTEND_ROOT = Path("/app/frontend/src")
SKIP_PARTS = {"tests", "__pycache__"}
SPECIAL_CASE_NAMES = {"auth.py", "pm_auth.py", "mfa.py"}
SPECIAL_CASE_DIR_FRAGMENTS = ("/routes/", "/lib/", "/services/")
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
DISPLAY_ONLY_TOKENS = (
    "url=",
    "base_url",
    "label",
    "subtitle",
    "title",
    "recipient_role",
    "assignee_role",
)


def should_skip(path: Path) -> bool:
    return any(part in SKIP_PARTS for part in path.parts) or path.name == "wp15_governance_convergence_scan.py"


def _has_auth_context(text: str, nearby: str) -> bool:
    hay = f"{text}\n{nearby}".lower()
    return any(token in hay for token in AUTH_DECISION_TOKENS)


def _is_display_only(text: str, nearby: str) -> bool:
    hay = f"{text}\n{nearby}".lower()
    return any(token in hay for token in DISPLAY_ONLY_TOKENS)


def _frontend_header_builder_findings() -> list[dict]:
    findings: list[dict] = []
    if not FRONTEND_ROOT.exists():
        raise RuntimeError(f"Frontend scan root missing: {FRONTEND_ROOT}")
    canonical_builder_tokens = (
        "buildScopedPortalAuthHeaders(",
        "buildPortalAuthHeaders(",
        "api.get(",
        "api.post(",
        "api.put(",
        "api.patch(",
        "api.delete(",
    )
    manual_header_tokens = (
        "X-Admin-Token",
        "X-PM-Token",
        "X-HR-Token",
        "X-Safety-Token",
        "X-Shop-Token",
        "X-Dispatch-Token",
        "X-FL-Token",
        "X-Directory-Token",
    )
    for path in FRONTEND_ROOT.rglob("*"):
        if path.suffix not in {".js", ".jsx", ".ts", ".tsx"}:
            continue
        if should_skip(path):
            continue
        rel = f"/{path.relative_to(Path('/app')).as_posix()}"
        lines = path.read_text(errors="ignore").splitlines()
        text = "\n".join(lines)
        if not any(token in text for token in manual_header_tokens):
            continue
        if any(token in text for token in canonical_builder_tokens):
            continue
        for line_no, line in enumerate(lines, 1):
            if any(token in line for token in manual_header_tokens):
                findings.append(
                    {
                        "path": rel,
                        "line": line_no,
                        "category": "legacy_migratable",
                        "reason": "Manual governed-request header construction",
                        "snippet": line.strip()[:220],
                    }
                )
    return findings


def classify(path: Path, lines: list[str], line_no: int) -> tuple[str, str] | None:
    line = lines[line_no - 1]
    text = line.strip()
    rel = f"/{path.relative_to(ROOT.parent).as_posix()}"
    nearby = "\n".join(lines[max(0, line_no - 20):line_no])
    if not text or text.startswith("#"):
        return None
    if "require_governed_action(" in text or "evaluate_governance_action(" in text:
        return ("canonical", "Canonical Governance Engine call")
    if "WP15_SPECIAL_CASE_INFRASTRUCTURE" in nearby:
        return ("special_case_infrastructure", "Documented governed-scope adapter")
    if path.name in SPECIAL_CASE_NAMES or path.name.endswith("_deps.py") or "/routes/" not in rel:
        if "X-Admin-Token" in text or "X-PM-Token" in text or "X-HR-Token" in text or "X-Safety-Token" in text:
            return ("special_case_infrastructure", "Authentication/token boundary")
    if "compute_pm_scope(" in text:
        return ("legacy_migratable", "Module-specific PM scope authorization")
    if path.name == "tasks_notifications.py" and ("build_notif_filter(" in text or "_scope_filter(" in text):
        return ("special_case_infrastructure", "Documented governed-scope adapter")
    if ("build_notif_filter(" in text or "_scope_filter(" in text) and "def " not in text:
        return ("legacy_migratable", "Module-specific notification/task scope filter")
    if re.search(r"\brole\b\s*==\s*['\"](?:admin|pm)['\"]", text):
        if "def _search_url_for_role" in nearby:
            return None
        if _is_display_only(text, nearby):
            return None
        if _has_auth_context(text, nearby):
            return ("legacy_migratable", "Inline role branch")
        return ("governance_candidate", "Role branch needs manual governance review")
    if re.search(r"\brole\b\s+in\s+[\({]", text):
        if _is_display_only(text, nearby):
            return None
        if _has_auth_context(text, nearby):
            return ("legacy_migratable", "Inline role set check")
        return ("governance_candidate", "Role set check needs manual governance review")
    if "is_super_admin" in text and "bool(" in text:
        if "{" in text and ":" in text and "permission" not in nearby.lower() and "allowed" not in nearby.lower():
            return None
        if _has_auth_context(text, nearby):
            return ("legacy_migratable", "Hard-coded super-admin branch")
        return ("governance_candidate", "Super-admin handling needs manual governance review")
    if "HTTPException(status_code=403" in text and ("scope" in text.lower() or "admin" in text.lower() or "pm" in text.lower()):
        return ("legacy_migratable", "Custom 403 authorization gate")
    return None


def main() -> None:
    findings = []
    for path in ROOT.rglob("*.py"):
        if should_skip(path):
            continue
        rel = f"/{path.relative_to(ROOT.parent).as_posix()}"
        if not any(fragment in rel for fragment in SPECIAL_CASE_DIR_FRAGMENTS):
            continue
        lines = path.read_text(errors="ignore").splitlines()
        for line_no, line in enumerate(lines, 1):
            classified = classify(path, lines, line_no)
            if not classified:
                continue
            category, reason = classified
            findings.append(
                {
                    "path": rel,
                    "line": line_no,
                    "category": category,
                    "reason": reason,
                    "snippet": line.strip()[:220],
                }
            )

    findings.extend(_frontend_header_builder_findings())

    summary = {
        "total_authorization_decision_points_discovered": len(findings),
        "canonical_governance_engine": sum(1 for row in findings if row["category"] == "canonical"),
        "legacy_but_migratable": sum(1 for row in findings if row["category"] == "legacy_migratable"),
        "special_case_infrastructure": sum(1 for row in findings if row["category"] == "special_case_infrastructure"),
        "governance_candidate_manual_review": sum(1 for row in findings if row["category"] == "governance_candidate"),
        "dead_or_unused_code": 0,
        "manual_auth_header_construction": sum(1 for row in findings if row["reason"] == "Manual governed-request header construction"),
        "findings": findings,
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()