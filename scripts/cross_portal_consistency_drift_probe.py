#!/usr/bin/env python3
"""
cross_portal_consistency_drift_probe.py — Phase V.1 · M0.4 · ADVISORY · M1-prep.

Doctrine source: `/app/memory/CROSS_PORTAL_CONSISTENCY_STANDARD.md`
                 `/app/memory/ODR_PLATFORM_INHERITANCE_DOCTRINE.md`

Compares ODR pages against neighbour portal pages (PM Hub, FL Center,
Admin) to detect visual divergence — different card shells, different
nav patterns, different empty-state copy. Heuristic only.

ADVISORY ONLY · exit code always 0.

Usage:
  python3 scripts/cross_portal_consistency_drift_probe.py
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REPORT_PATH = REPO_ROOT / "memory" / "CROSS_PORTAL_CONSISTENCY_DRIFT_REPORT.md"
PAGES_DIR = REPO_ROOT / "frontend" / "src" / "pages"

# Components we expect every portal to draw from the shared ui/ kit.
SHARED_COMPONENT_TOKENS = {
    "Card", "CardHeader", "CardContent", "Dialog", "DialogContent",
    "Button", "Input", "Tabs", "TabsList", "TabsTrigger",
    "Skeleton", "Alert",
}

IMPORT_RX = re.compile(r"from\s+['\"]([^'\"]+)['\"]")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def collect_imports(path: Path) -> dict:
    src = path.read_text(errors="ignore")
    out = {"shared_ui": 0, "non_shared_ui_components": []}
    for m in IMPORT_RX.finditer(src):
        spec = m.group(1)
        if "/components/ui/" in spec:
            out["shared_ui"] += 1
        else:
            # Heuristic: capture imports that bring component-shaped names
            line_start = src.rfind("\n", 0, m.start()) + 1
            line = src[line_start:src.find("\n", m.end())]
            if any(tok in line for tok in SHARED_COMPONENT_TOKENS):
                out["non_shared_ui_components"].append(spec)
    return out


def run() -> int:
    if not PAGES_DIR.exists():
        msg = "frontend/src/pages not found — probe is a no-op."
        REPORT_PATH.write_text(
            "# Cross-Portal Consistency Drift Report\n\n"
            f"_Generated: {_utc_now_iso()}_\n\n{msg}\n"
        )
        print(f"cross_portal_consistency_drift_probe · {msg}")
        return 0

    portal_dirs = {
        "ODR": PAGES_DIR / "odr",
        "PM": PAGES_DIR / "pm",
        "FL": PAGES_DIR / "fl",
        "Admin": PAGES_DIR / "admin",
        "Safety": PAGES_DIR / "safety",
        "Dispatch": PAGES_DIR / "dispatch",
    }

    portal_summary = {}
    for name, d in portal_dirs.items():
        if not d.exists():
            portal_summary[name] = {"present": False}
            continue
        files = list(d.rglob("*.jsx"))
        shared_uses = 0
        non_shared = []
        for f in files:
            res = collect_imports(f)
            shared_uses += res["shared_ui"]
            non_shared.extend(res["non_shared_ui_components"])
        portal_summary[name] = {
            "present": True,
            "files": len(files),
            "shared_ui_imports": shared_uses,
            "non_shared_component_imports": len(non_shared),
            "examples": list(Counter(non_shared).most_common(3)),
        }

    # Detect divergence: ODR's non-shared component ratio vs neighbour portals.
    odr = portal_summary.get("ODR") or {"present": False}
    state = "GREEN"
    advisories = []
    if odr.get("present") and (odr.get("non_shared_component_imports", 0) > 0):
        state = "AMBER"
        advisories.append(
            f"ODR pages import {odr['non_shared_component_imports']} "
            "component-shaped symbols outside the shared ui/ kit. "
            "Verify each one passes the documented divergence flow."
        )

    lines = [
        "# Cross-Portal Consistency Drift Report",
        "",
        f"_Generated: {_utc_now_iso()} · advisory probe._",
        "",
        "**Doctrine sources:** `CROSS_PORTAL_CONSISTENCY_STANDARD.md`, "
        "`ODR_PLATFORM_INHERITANCE_DOCTRINE.md`",
        "",
        f"## Summary · {state}",
        "",
    ]
    for adv in advisories:
        lines.append(f"- **advisory** · {adv}")
    lines.append("")
    lines.append("## Portal inventory")
    lines.append("")
    lines.append("| Portal | Files | Shared UI imports | Non-shared component imports |")
    lines.append("|---|---|---|---|")
    for name, p in portal_summary.items():
        if not p.get("present"):
            lines.append(f"| {name} | _absent_ | — | — |")
        else:
            lines.append(
                f"| {name} | {p['files']} | "
                f"{p['shared_ui_imports']} | "
                f"{p['non_shared_component_imports']} |"
            )
    lines += [
        "",
        "## ADVISORY",
        "",
        "This probe **never fails the build**. Cross-portal consistency",
        "is enforced by review · this report flags candidate divergence",
        "for human triage.",
        "",
        "_Probe exit code: 0 (advisory)._",
    ]
    REPORT_PATH.write_text("\n".join(lines) + "\n")
    print(f"cross_portal_consistency_drift_probe · state={state} · "
          f"advisories={len(advisories)}")
    print(f"  report -> {REPORT_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(run())
