#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = REPO_ROOT / "memory" / "WP18_OPERATOR_LANGUAGE_HARD_FAIL_REGISTER.csv"


@dataclass(frozen=True)
class BannedPattern:
    term: str
    pattern: re.Pattern[str]
    replacement: str


BANNED_PATTERNS = [
    BannedPattern("C1", re.compile(r"\bC1\b", re.IGNORECASE), "customer and project records"),
    BannedPattern("C2", re.compile(r"\bC2\b", re.IGNORECASE), "work planning records"),
    BannedPattern("C3", re.compile(r"\bC3\b", re.IGNORECASE), "budget records"),
    BannedPattern("C4", re.compile(r"\bC4\b", re.IGNORECASE), "schedule records"),
    BannedPattern("C5", re.compile(r"\bC5\b", re.IGNORECASE), "planned-vs-actual records"),
    BannedPattern("C6", re.compile(r"\bC6\b", re.IGNORECASE), "project performance records"),
    BannedPattern("C7", re.compile(r"\bC7\b", re.IGNORECASE), "forecast records"),
    BannedPattern("C8", re.compile(r"\bC8\b", re.IGNORECASE), "Earned Value records"),
    BannedPattern("C9", re.compile(r"\bC9\b", re.IGNORECASE), "portfolio view"),
    BannedPattern("C10", re.compile(r"\bC10\b", re.IGNORECASE), "next approved work package"),
    BannedPattern("WP-17", re.compile(r"\bWP-17\b", re.IGNORECASE), "approved workflow"),
    BannedPattern("WP-18", re.compile(r"\bWP-18\b", re.IGNORECASE), "approved workflow"),
    BannedPattern("ECAP", re.compile(r"\bECAP\b", re.IGNORECASE), "executive reporting"),
    BannedPattern("authority contract", re.compile(r"authority contract", re.IGNORECASE), "How this result is calculated"),
    BannedPattern("read model", re.compile(r"read model", re.IGNORECASE), "portfolio view"),
    BannedPattern("source lineage", re.compile(r"source lineage", re.IGNORECASE), "supporting records"),
    BannedPattern("source hash", re.compile(r"source_hash|source hash", re.IGNORECASE), "release fingerprint"),
    BannedPattern("runtime", re.compile(r"\bruntime\b", re.IGNORECASE), "current view"),
    BannedPattern("schema", re.compile(r"\bschema\b", re.IGNORECASE), "form layout"),
    BannedPattern("payload", re.compile(r"\bpayload\b", re.IGNORECASE), "submitted details"),
    BannedPattern("backend", re.compile(r"\bbackend\b", re.IGNORECASE), "system records"),
    BannedPattern("frontend", re.compile(r"\bfrontend\b", re.IGNORECASE), "page"),
    BannedPattern("API", re.compile(r"/api/|\bAPI\b", re.IGNORECASE), "admin settings"),
    BannedPattern("route", re.compile(r"\b(?:primary|public|top|legacy|auth-aware)\s+route\b|\broute catalog\b", re.IGNORECASE), "page"),
    BannedPattern("collection", re.compile(r"\bcollection\b", re.IGNORECASE), "record list"),
    BannedPattern("engine", re.compile(r"(?:earned value|decision|metric|forecast|forecasting|qualification|operational)\s+engine", re.IGNORECASE), "approved calculation"),
    BannedPattern("telemetry", re.compile(r"\btelemetry\b", re.IGNORECASE), "activity details"),
]

SCAN_ROOTS = [
    REPO_ROOT / "frontend" / "src" / "pages",
    REPO_ROOT / "frontend" / "src" / "components",
    REPO_ROOT / "frontend" / "src" / "data",
    REPO_ROOT / "frontend" / "src" / "lib",
    REPO_ROOT / "backend",
]
SCAN_SUFFIXES = {".js", ".jsx", ".ts", ".tsx", ".py", ".html", ".txt"}

EXEMPT_PATTERNS = [
    "frontend/src/data/training.js",
    "frontend/src/data/training_es.js",
    "frontend/src/pages/TrainingHub.jsx",
    "frontend/src/pages/DevHub.jsx",
    "frontend/src/pages/__tests__/**",
    "frontend/src/pages/AdminGuide.jsx",
    "frontend/src/pages/AdminDeployReadiness.jsx",
    "frontend/src/pages/AdminLegacyImports.jsx",
    "frontend/src/pages/AdminGeofenceReconciliation.jsx",
    "frontend/src/pages/AdminGovernanceListPage.jsx",
    "frontend/src/pages/AdminGuidanceCoverage.jsx",
    "frontend/src/pages/AdminMaterialLedgerQuality.jsx",
    "frontend/src/pages/legal/*",
    "frontend/src/pages/admin/**/*.jsx",
    "frontend/src/pages/admin/SelfProtection.jsx",
    "frontend/src/components/admin/**/*.jsx",
    "frontend/src/components/Admin*.jsx",
    "frontend/src/components/**/commandApi.js",
    "frontend/src/components/**/ocCommandApi.js",
    "frontend/src/components/RestoreBackupPanel.jsx",
    "frontend/src/components/BackendVersionBadge.jsx",
    "frontend/src/components/telemetry/*",
    "frontend/src/lib/*",
    "frontend/src/app/*",
    "backend/export_pdf_fallback.py",
    "backend/hub_banners_pdf.py",
    "backend/pdf_render.py",
    "backend/pm_welcome_pdf.py",
    "backend/training_pdf.py",
    "backend/routes/notifications.py",
    "backend/routes/notify_ownership_lock_seed.py",
    "backend/routes/odr/pdf.py",
    "backend/tests/**",
    "backend/scripts/*",
    "backend/lib/*",
    "memory/*",
    "docs/*",
]

OPERATOR_SURFACE_HINTS = {
    "frontend/src/components/project_controls/PortfolioIntelligenceWorkspace.jsx": ("Portfolio Intelligence shared workspace", "Executive / PM / Admin"),
    "frontend/src/pages/ExecutiveOverview.jsx": ("/admin/executive-overview", "Admin / Executive"),
    "frontend/src/pages/PmPortfolioIntelligence.jsx": ("/pm/portfolio-intelligence", "PM"),
    "frontend/src/pages/ExecutiveOperationalIntelligence.jsx": ("/admin/executive-operational-intelligence", "Admin / Executive"),
    "frontend/src/pages/admin/AdminCommandCenter.jsx": ("/admin/command-center", "Admin"),
}

JSX_TEXT_PATTERN = re.compile(r">\s*([^<>{][^<>]{1,260}?)\s*<")
TRANSLATION_TEXT_PATTERN = re.compile(r"t\(\s*([\"'`])((?:(?!\1).|\\.){1,260})\1\s*\)")
PROP_TEXT_PATTERN = re.compile(r"(?:title|label|subtitle|description|placeholder|emptyLabel|message|helperText|text|body|subject|why|headline)\s*[:=]\s*([\"'`])((?:(?!\1).|\\.){1,260})\1")
BACKEND_STRING_PATTERN = re.compile(r"([\"'])(?:(?=(\\?))\2.)*?\1")
CODE_MARKERS = ("${", "=>", "await ", "const ", "function ", "return ", "api.", "payload.", "props.", "onClick", "useState", ".map(", "<>")


def _matches_any(relative_path: str, patterns: Iterable[str]) -> bool:
    path = Path(relative_path)
    return any(path.match(pattern) for pattern in patterns)


def _classification(relative_path: str) -> str:
    if relative_path in OPERATOR_SURFACE_HINTS:
        return "OPERATOR_FACING"
    if relative_path.startswith("frontend/src/pages/admin/"):
        return "TECHNICAL_ADMIN_EXCEPTION"
    if relative_path.startswith("frontend/src/components/admin/"):
        return "TECHNICAL_ADMIN_EXCEPTION"
    if relative_path.startswith("frontend/src/pages/__tests__/"):
        return "TECHNICAL_ADMIN_EXCEPTION"
    if relative_path.startswith("backend/tests/"):
        return "TECHNICAL_ADMIN_EXCEPTION"
    if Path(relative_path).name.startswith("Admin") and relative_path.startswith("frontend/src/components/"):
        return "TECHNICAL_ADMIN_EXCEPTION"
    return "TECHNICAL_ADMIN_EXCEPTION" if _matches_any(relative_path, EXEMPT_PATTERNS) else "OPERATOR_FACING"


def _surface(relative_path: str) -> tuple[str, str]:
    if relative_path in OPERATOR_SURFACE_HINTS:
        return OPERATOR_SURFACE_HINTS[relative_path]
    name = Path(relative_path).stem
    if "/pages/" in relative_path:
        role = "Operator"
        if "Pm" in name:
            role = "PM"
        elif "Executive" in name:
            role = "Executive"
        elif "Safety" in name:
            role = "Safety"
        elif "Hr" in name or "HR" in name:
            role = "HR"
        elif "Dispatch" in name:
            role = "Dispatch"
        elif "FieldLeadership" in name:
            role = "Field Leadership"
        elif "Admin" in name:
            role = "Admin"
        return (f"/{name}", role)
    if "/components/" in relative_path:
        return (name, "Shared Operator Component")
    if "/data/" in relative_path:
        return (name, "Training / Localization")
    return (name, "Technical")


def _strip_comments(text: str, suffix: str) -> str:
    if suffix in {".js", ".jsx", ".ts", ".tsx"}:
        text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
        text = re.sub(r"//.*", "", text)
        return text
    if suffix == ".py":
        return re.sub(r"#.*", "", text)
    return text


def _line_number(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def _extract_snippets(path: Path, text: str) -> list[tuple[int, str]]:
    snippets: list[tuple[int, str]] = []
    suffix = path.suffix.lower()
    if suffix in {".js", ".jsx", ".ts", ".tsx"}:
        for pattern in (JSX_TEXT_PATTERN, TRANSLATION_TEXT_PATTERN, PROP_TEXT_PATTERN):
            for match in pattern.finditer(text):
                snippet = (match.group(2) if match.lastindex and match.lastindex >= 2 else match.group(1)).strip()
                if snippet:
                    snippets.append((_line_number(text, match.start()), snippet))
        return snippets
    if any(token in path.name.lower() for token in ("email", "pdf", "notify", "notification", "prompt", "briefing")):
        for match in BACKEND_STRING_PATTERN.finditer(text):
            raw = match.group(0)[1:-1].strip()
            if len(raw) >= 3:
                snippets.append((_line_number(text, match.start()), raw))
    return snippets


def _looks_like_code(snippet: str) -> bool:
    compact = snippet.strip()
    if not compact:
        return True
    if any(marker in compact for marker in CODE_MARKERS):
        return True
    if compact.startswith(("@/", "./", "../")):
        return True
    if compact.count("{") > 0 or compact.count("}") > 0:
        return True
    if compact.count(";") > 0:
        return True
    if compact.startswith("/api/") or compact.startswith("${API}") or compact.startswith("${api}"):
        return True
    if "/api/" in compact and " " not in compact:
        return True
    if "REACT_APP_BACKEND_URL" in compact or compact.startswith("@/"):
        return True
    return False


def _scan_file(path: Path) -> list[dict[str, str]]:
    relative_path = path.relative_to(REPO_ROOT).as_posix()
    classification = _classification(relative_path)
    surface, role = _surface(relative_path)
    text = path.read_text(encoding="utf-8", errors="ignore")
    stripped = _strip_comments(text, path.suffix.lower())
    rows: list[dict[str, str]] = []
    for line_number, snippet in _extract_snippets(path, stripped):
        compact = " ".join(snippet.split())
        if not compact or _looks_like_code(compact):
            continue
        for banned in BANNED_PATTERNS:
            if not banned.pattern.search(compact):
                continue
            status = "EXEMPT" if classification != "OPERATOR_FACING" else "FAIL"
            rows.append({
                "route/surface": surface,
                "role": role,
                "visible text": compact[:320],
                "banned term": banned.term,
                "classification": classification,
                "replacement": banned.replacement,
                "runtime proof": f"static_scan::{relative_path}:{line_number}",
                "status": status,
            })
    return rows


def run_scan() -> dict[str, object]:
    files: list[Path] = []
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        files.extend(path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in SCAN_SUFFIXES)
    unique_files = sorted({path.resolve() for path in files})
    findings: list[dict[str, str]] = []
    for path in unique_files:
        findings.extend(_scan_file(path))
    findings.sort(key=lambda row: (row["status"], row["route/surface"], row["runtime proof"], row["banned term"]))
    operator_failures = [row for row in findings if row["status"] == "FAIL"]
    technical_exemptions = [row for row in findings if row["status"] == "EXEMPT"]
    with CSV_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["route/surface", "role", "visible text", "banned term", "classification", "replacement", "runtime proof", "status"])
        writer.writeheader()
        writer.writerows(findings)
    return {
        "returncode": 0 if not operator_failures else 1,
        "scanned_files": len(unique_files),
        "operator_facing_banned_findings": len(operator_failures),
        "technical_admin_exceptions": len(technical_exemptions),
        "csv_path": str(CSV_PATH),
        "operator_failures": operator_failures[:50],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Operator-language hard fail scanner")
    parser.add_argument("--json", action="store_true", dest="emit_json")
    args = parser.parse_args()
    result = run_scan()
    if args.emit_json:
        print(json.dumps(result, indent=2))
    else:
        print(f"operator_facing_banned_findings={result['operator_facing_banned_findings']}")
        print(f"technical_admin_exceptions={result['technical_admin_exceptions']}")
        print(f"csv_path={result['csv_path']}")
    return int(result["returncode"])


if __name__ == "__main__":
    raise SystemExit(main())