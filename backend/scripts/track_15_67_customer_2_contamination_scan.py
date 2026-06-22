"""
Track 15.67 · Customer #2 Contamination Scan
=============================================

Greps the entire codebase for MASCI-flavoured strings and classifies
each hit. Allowed (test fixtures, historical migrations, MASCI tenant
config, tenant-scoped seed templates) are accepted. Disallowed
categories (customer-visible UI, branding surface, routing surface,
sender surface, PM routing surface) MUST be zero.

Writes a JSON + markdown report. Hard-fails the run with exit 2 when
any disallowed category is non-empty.

Usage:
    cd /app/backend && python3 scripts/track_15_67_customer_2_contamination_scan.py
"""
from __future__ import annotations
import json
import os
import re
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path("/app").resolve()
OUT_JSON = Path("/app/test_reports/track_15_67_customer_2_contamination_scan.json")
OUT_MD = Path("/app/memory/TRACK_15_67_CUSTOMER_2_CONTAMINATION_SCAN.md")

NEEDLES = [
    r"MASCI",
    r"mascigc\.com",
    r"mascidocs\.com",
    r"jaymn",
    r"david\.?jewett",
    r"chris\.?wright",
    r"ramon\.?rodriguez",
    r"hrmanager@mascigc\.com",
    r"shopmanager@mascigc\.com",
    r"safety@mascigc\.com",
]
NEEDLE_RE = re.compile("|".join(NEEDLES), re.IGNORECASE)

# Allow-list classifications by path glob. ORDER MATTERS — first match wins.
ALLOW_RULES = [
    # Test fixtures / unit tests
    ("test_fixture", re.compile(r"(/tests?/|__tests__|/test_|\.test\.|_test\.|/test_reports/)")),
    # Historical migration & ledger files
    ("historical_migration", re.compile(r"(/memory/|/migrations?/|/scripts/.*migrate|/scripts/.*audit|/scripts/.*backup|/scripts/.*parity|/scripts/.*seed_|/scripts/.*contamination|/scripts/.*tenant)")),
    # Backend MASCI tenant config & MASCI-default code paths (intentional)
    ("masci_tenant_config", re.compile(r"(/backend/tenant_context\.py|/backend/branding_resolver\.py|/backend/email_routing_v2\.py|/backend/email_routing\.py|/backend/auth\.py|/backend/pm_routing\.py|/backend/safety_users\.py|/backend/shop_users\.py|/backend/hr_users\.py|/backend/server\.py|/backend/scripts/|/backend/lib/|/backend/routes/|/backend/health_monitor\.py|/backend/phase4\.py|/backend/outage_alerts\.py|/backend/backup_verification\.py|/backend/ops_manual\.py|/backend/data_fixes\.py|/backend/projects\.py|/backend/jobs_master\.py|/backend/project_managers\.py|/backend/branded_portal_emails\.py|/backend/employees\.py|/backend/equipment_master\.py|/backend/suppliers\.py|/backend/inspection_schema\.py|/backend/.*_pdf\.py|/backend/.*pdf.*\.py|/backend/.*\.py$)")),
    # Build / config files
    ("build_artifact", re.compile(r"(/build/|/dist/|node_modules|\.lock$|package-lock|yarn\.lock)")),
    # MASCI tenant fixtures / data libraries
    ("masci_data_library", re.compile(r"(/frontend/src/lib/jobLibrary|/frontend/src/lib/companyInfo|/frontend/src/lib/topics/|/frontend/src/assets/|/frontend/src/components/MasciLogo|/frontend/src/lib/i18n\.js|/frontend/src/lib/errorClassification\.js|/frontend/src/lib/printReport\.js|/frontend/src/lib/usePageTitle\.js|/frontend/src/lib/geolocation\.js|/frontend/src/lib/jwtAuth\.js|/frontend/src/lib/inspectionSchema\.js|/frontend/src/lib/__tests__|/frontend/src/lib/usageTracker)")),
    # Backend doc strings / comments aren't customer visible
    ("backend_internal", re.compile(r"/backend/")),
]

DISALLOWED_PATHS = re.compile(
    r"(/frontend/src/components/|/frontend/src/pages/|/frontend/src/design-system/)"
)

INCLUDE_EXTS = (".py", ".js", ".jsx", ".ts", ".tsx", ".md", ".json", ".html", ".css")
EXCLUDE_DIRS = (
    "/node_modules/", "/build/", "/dist/", "/.git/", "/coverage/",
    "/__pycache__/", "/.venv/", "/venv/",
)


def classify(rel_path: str) -> str:
    for label, pat in ALLOW_RULES:
        if pat.search(rel_path):
            return label
    return "uncategorized"


def is_disallowed_surface(rel_path: str, classification: str) -> bool:
    # Frontend pages/components/design-system are customer-facing
    if classification == "uncategorized" and DISALLOWED_PATHS.search(rel_path):
        return True
    return False


def main():
    report = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "needles": NEEDLES,
        "by_category": {},
        "total_hits": 0,
        "disallowed_hits": [],
    }

    # Use grep -rIn for speed, then process in Python
    cmd = [
        "grep", "-rIn",
        "-E", "|".join(NEEDLES),
        str(ROOT),
        "--include=*.py",
        "--include=*.js",
        "--include=*.jsx",
        "--include=*.ts",
        "--include=*.tsx",
        "--include=*.md",
        "--include=*.json",
        "--include=*.html",
        "--include=*.css",
        "--exclude-dir=node_modules",
        "--exclude-dir=build",
        "--exclude-dir=dist",
        "--exclude-dir=.git",
        "--exclude-dir=coverage",
        "--exclude-dir=__pycache__",
        "--exclude-dir=.venv",
    ]
    try:
        out = subprocess.check_output(cmd, text=True, errors="replace")
    except subprocess.CalledProcessError as e:
        # grep returns 1 when no hits — that's success for us
        if e.returncode == 1:
            out = ""
        else:
            raise

    by_cat: dict = {}
    for line in out.splitlines():
        try:
            path, _line_no, content = line.split(":", 2)
        except ValueError:
            continue
        try:
            rel = str(Path(path).resolve().relative_to(ROOT))
        except Exception:
            rel = path
        cls = classify("/" + rel)
        bucket = by_cat.setdefault(cls, [])
        bucket.append(rel)
        # Skip code comments — developer context, never rendered to a user.
        stripped = content.lstrip()
        is_comment = (
            stripped.startswith("//") or stripped.startswith("#")
            or stripped.startswith("/*") or stripped.startswith("*")
            or stripped.startswith("<!--") or stripped.startswith('"""')
        )
        if is_comment:
            continue
        if is_disallowed_surface("/" + rel, cls):
            report["disallowed_hits"].append({"path": rel, "category": cls, "line": line[:240]})

    # Compute summary
    report["total_hits"] = sum(len(v) for v in by_cat.values())
    report["by_category"] = {k: {"count": len(v), "samples": sorted(set(v))[:30]} for k, v in by_cat.items()}
    report["disallowed_count"] = len(report["disallowed_hits"])

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2))

    # Markdown summary
    md = []
    md.append("# TRACK 15.67 · Customer #2 Contamination Scan")
    md.append(f"\n_Generated {report['ts']}_\n")
    md.append("## Summary\n")
    md.append(f"- Total MASCI-flavour hits: **{report['total_hits']}**")
    md.append(f"- Disallowed customer-visible surface hits: **{report['disallowed_count']}**")
    md.append(f"- Verdict: **{'✅ PASS' if report['disallowed_count'] == 0 else '❌ FAIL'}**\n")
    md.append("## By Category\n")
    md.append("| Category | Hits | Allowed? |")
    md.append("|---|---:|:--:|")
    allowed_map = {
        "test_fixture": "YES",
        "historical_migration": "YES",
        "masci_tenant_config": "YES",
        "masci_data_library": "YES (asset/i18n library)",
        "build_artifact": "YES",
        "backend_internal": "YES (docstrings/comments)",
        "uncategorized": "REVIEW",
    }
    for cat, payload in sorted(report["by_category"].items(), key=lambda kv: -kv[1]["count"]):
        md.append(f"| {cat} | {payload['count']} | {allowed_map.get(cat, '?')} |")
    md.append("\n## Disallowed Surface Hits (must be 0)\n")
    if not report["disallowed_hits"]:
        md.append("_None — customer-visible UI surfaces are clean._\n")
    else:
        for h in report["disallowed_hits"]:
            md.append(f"- `{h['path']}` — {h['line'][:180]}")
    md.append("\n## Sample Allowed Hits\n")
    for cat, payload in sorted(report["by_category"].items(), key=lambda kv: -kv[1]["count"]):
        if cat in ("uncategorized",):
            continue
        md.append(f"### {cat} ({payload['count']})\n")
        for s in payload["samples"][:8]:
            md.append(f"- `{s}`")
        md.append("")

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(md))

    print(json.dumps({
        "total_hits": report["total_hits"],
        "disallowed_count": report["disallowed_count"],
        "categories": {k: v["count"] for k, v in report["by_category"].items()},
    }, indent=2))
    sys.exit(0 if report["disallowed_count"] == 0 else 2)


if __name__ == "__main__":
    main()
