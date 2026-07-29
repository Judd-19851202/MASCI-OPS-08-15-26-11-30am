from __future__ import annotations

import json
from pathlib import Path


ROOT = Path("/app/backend")
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


def classify(path: Path, lines: list[str], line_no: int) -> tuple[str, str] | None:
    line = lines[line_no - 1]
    text = line.strip()
    rel = f"/{path.relative_to(ROOT.parent).as_posix()}"
    nearby = "\n".join(lines[max(0, line_no - 9):line_no])
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
    if ("build_notif_filter(" in text or "_scope_filter(" in text) and "def " not in text:
        return ("legacy_migratable", "Module-specific notification/task scope filter")
    if "if role == \"admin\"" in text or "if role == \"pm\"" in text:
        if _is_display_only(text, nearby):
            return None
        if _has_auth_context(text, nearby):
            return ("legacy_migratable", "Inline role branch")
        return ("governance_candidate", "Role branch needs manual governance review")
    if "role in {" in text or "role in (" in text:
        if _is_display_only(text, nearby):
            return None
        if _has_auth_context(text, nearby):
            return ("legacy_migratable", "Inline role set check")
        return ("governance_candidate", "Role set check needs manual governance review")
    if "is_super_admin" in text and "bool(" in text:
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

    summary = {
        "total_authorization_decision_points_discovered": len(findings),
        "canonical_governance_engine": sum(1 for row in findings if row["category"] == "canonical"),
        "legacy_but_migratable": sum(1 for row in findings if row["category"] == "legacy_migratable"),
        "special_case_infrastructure": sum(1 for row in findings if row["category"] == "special_case_infrastructure"),
        "governance_candidate_manual_review": sum(1 for row in findings if row["category"] == "governance_candidate"),
        "dead_or_unused_code": 0,
        "findings": findings,
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()