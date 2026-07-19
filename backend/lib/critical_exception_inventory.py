from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path("/app")
OUTPUT = ROOT / "docs" / "governance" / "critical_exception_inventory.json"

CRITICAL_ROOTS: list[tuple[Path, str]] = [
    (ROOT / "backend" / "server.py", "startup_db_identity"),
    (ROOT / "backend" / "routes", "routes"),
    (ROOT / "backend" / "lib", "library"),
    (ROOT / "backend" / "scripts", "mutation_scripts"),
    (ROOT / "backend" / "tools", "backup_restore"),
    (ROOT / "backend" / "pm_auth.py", "authz_scope"),
    (ROOT / "backend" / "auth_must_change.py", "authn"),
    (ROOT / "backend" / "db_isolation_failsafe.py", "startup_db_identity"),
    (ROOT / "scripts", "operator_scripts"),
]


def _critical_family(path: str) -> str:
    p = path.lower()
    if any(tok in p for tok in ["auth", "pm_auth", "passkey", "mfa", "tenant_context"]):
        return "authentication_authorization"
    if any(tok in p for tok in ["daily", "pdf", "photo", "attachment"]):
        return "daily_reports_pdf_files"
    if any(tok in p for tok in ["backup", "restore", "drill"]):
        return "backup_restore"
    if any(tok in p for tok in ["r2", "photo_storage", "storage"]):
        return "r2_storage"
    if any(tok in p for tok in ["email", "notification", "resend", "maintainx"]):
        return "notifications_email_integrations"
    if any(tok in p for tok in ["ai_", "openai", "anthropic", "vision", "translation", "ocr"]):
        return "ai_providers"
    if any(tok in p for tok in ["trust", "audit", "governance", "release_identity", "deployment", "certification"]):
        return "trust_governance"
    if any(tok in p for tok in ["scheduler", "jobs_master"]):
        return "schedulers_background"
    if any(tok in p for tok in ["script", "migrate", "seed", "cleanup", "drill", "import"]):
        return "active_mutation_scripts_migrations"
    return "startup_db_identity"


def _iter_files() -> list[Path]:
    files: list[Path] = []
    for root, _label in CRITICAL_ROOTS:
        if root.is_file():
            files.append(root)
        else:
            files.extend(sorted(root.rglob("*.py")))
    return files


def _nearest_context(lines: list[str], idx: int) -> tuple[str | None, str | None]:
    function_name = None
    class_name = None
    for j in range(idx, -1, -1):
        s = lines[j].strip()
        if function_name is None and (s.startswith("def ") or s.startswith("async def ")):
            function_name = s.split("def ", 1)[1].split("(", 1)[0].strip()
        if class_name is None and s.startswith("class "):
            class_name = s.split("class ", 1)[1].split("(", 1)[0].split(":", 1)[0].strip()
        if function_name and class_name:
            break
    return function_name, class_name


def _behavior_after(lines: list[str], idx: int) -> str:
    window = [l.strip() for l in lines[idx + 1 : idx + 8]]
    joined = "\n".join(window)
    if any(w.startswith("raise") for w in window):
        return "re-raise"
    if any("return []" in w or "return {}" in w or "return None" in w or "return 0" in w for w in window):
        return "return default"
    if any(w.startswith("return") for w in window):
        return "return success"
    if any(w.startswith("continue") for w in window):
        return "continue loop"
    if any(w.startswith("pass") for w in window):
        return "pass"
    if "retry" in joined.lower():
        return "retry"
    if "logger." in joined or "print(" in joined:
        return "log only"
    return "fallback"


def _operation_category(lines: list[str], idx: int) -> str:
    ctx = "\n".join(l.strip() for l in lines[max(0, idx - 6) : idx + 1]).lower()
    if any(tok in ctx for tok in ["insert_", "update_", "delete_", "replace_", "bulk_write", "drop_"]):
        return "write_mutation"
    if any(tok in ctx for tok in ["find_one", "count_documents", "read_text", "open(", "get_object", "download_file"]):
        return "read_validation"
    if any(tok in ctx for tok in ["resolve", "auth", "token", "permission", "scope"]):
        return "auth_scope"
    return "general"


def _log_behavior(lines: list[str], idx: int) -> str:
    window = "\n".join(l.strip() for l in lines[idx + 1 : idx + 8]).lower()
    if "logger." in window:
        return "logger"
    if "print(" in window:
        return "print"
    return "none"


def _correlation_behavior(lines: list[str], idx: int) -> str:
    window = "\n".join(l.strip() for l in lines[max(0, idx - 5) : idx + 8]).lower()
    if "request_id" in window or "correlation" in window:
        return "present"
    return "not_evident"


def _risk_classification(family: str, behavior: str, op_category: str, syntax: str) -> str:
    syntax_l = syntax.lower()
    if behavior in {"pass", "return success", "return default"} and op_category in {"write_mutation", "auth_scope"}:
        return "P1_candidate"
    if behavior in {"pass", "return success", "return default"} and family in {"backup_restore", "startup_db_identity", "trust_governance"}:
        return "P1_candidate"
    if "except exception" in syntax_l and family in {"backup_restore", "authentication_authorization", "active_mutation_scripts_migrations"}:
        return "P2_candidate"
    if behavior == "log only":
        return "P2_candidate"
    return "P3_or_info"


def _initial_status(risk: str) -> str:
    if risk == "P1_candidate":
        return "reviewed_required"
    if risk == "P2_candidate":
        return "owned_follow_up"
    return "accepted_or_low_risk"


def build_inventory() -> dict[str, Any]:
    occurrences: list[dict[str, Any]] = []
    for path in _iter_files():
        rel = str(path.relative_to(ROOT))
        lines = path.read_text(errors="ignore").splitlines()
        for idx, line in enumerate(lines):
            s = line.strip()
            if not (s.startswith("except") or s == "pass" or "contextlib.suppress(Exception)" in s):
                continue
            function_name, class_name = _nearest_context(lines, idx)
            behavior = _behavior_after(lines, idx)
            family = _critical_family(rel)
            op = _operation_category(lines, idx)
            risk = _risk_classification(family, behavior, op, s)
            stable = hashlib.sha1(f"{rel}:{idx+1}:{s}".encode()).hexdigest()[:12]
            occurrences.append(
                {
                    "id": f"CE-{stable}",
                    "file": rel,
                    "line": idx + 1,
                    "function": function_name,
                    "class": class_name,
                    "critical_family": family,
                    "exception_syntax": s,
                    "caught_operation_category": op,
                    "behavior_after_catch": behavior,
                    "path_type": "write" if op == "write_mutation" else "read",
                    "user_visible_result": behavior,
                    "log_behavior": _log_behavior(lines, idx),
                    "correlation_id_behavior": _correlation_behavior(lines, idx),
                    "initial_static_risk_classification": risk,
                    "owner": "Checkpoint B main agent triage",
                    "status": _initial_status(risk),
                    "linked_tests": [],
                }
            )
    by_family = Counter(item["critical_family"] for item in occurrences)
    by_behavior = Counter(item["behavior_after_catch"] for item in occurrences)
    by_risk = Counter(item["initial_static_risk_classification"] for item in occurrences)
    return {
        "generated_at": json.dumps(None),
        "total_occurrences": len(occurrences),
        "totals_by_family": dict(by_family),
        "totals_by_behavior": dict(by_behavior),
        "totals_by_risk": dict(by_risk),
        "occurrences": occurrences,
    }


def write_inventory() -> dict[str, Any]:
    data = build_inventory()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(data, indent=2))
    return data


if __name__ == "__main__":
    write_inventory()
