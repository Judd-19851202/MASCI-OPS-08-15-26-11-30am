#!/usr/bin/env python3
"""
odr_inheritance_drift_probe.py — Phase V.1 · M0.4 · ADVISORY · M1-prep.

Doctrine source: `/app/memory/ODR_PLATFORM_INHERITANCE_DOCTRINE.md`

Scans the ODR frontend surfaces for divergence from platform-inherited
components. Heuristic only. ADVISORY ONLY · exit code always 0.

Checks:
  * Off-palette hex colors in ODR JSX (color tokens MUST be platform tokens)
  * Custom font-family declarations
  * Imports from non-shared component paths
  * Hard-coded #fff / #000 alternatives outside theme tokens

Usage:
  python3 scripts/odr_inheritance_drift_probe.py
"""
from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REPORT_PATH = REPO_ROOT / "memory" / "ODR_INHERITANCE_DRIFT_REPORT.md"
TARGETS_DIR = REPO_ROOT / "frontend" / "src" / "pages" / "odr"

HEX_RX = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})\b")
FONT_FAMILY_RX = re.compile(r"font-family\s*:", re.IGNORECASE)
NON_SHARED_IMPORT_RX = re.compile(
    r"from\s+['\"](?!\.\./components/ui/|@/components/ui/|"
    r"\.\./../components/ui/|lucide-react|sonner|"
    r"\.\./../lib/|\.\./lib/|react|react-router|"
    r"\.\./components/odr/|\.\./../components/odr/)"
    r"[^'\"]+['\"]"
)

# Permit the platform color tokens (hsl(var(...)) or tailwind tokens via class).
ALLOWED_HEX_INSIDE_COMMENTS = True


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def scan(path: Path) -> dict:
    src = path.read_text(errors="ignore")
    advisories = []

    # Hex color tokens
    hexes = []
    for m in HEX_RX.finditer(src):
        line_start = src.rfind("\n", 0, m.start()) + 1
        line_end = src.find("\n", m.end())
        line = src[line_start:line_end if line_end != -1 else len(src)]
        if ALLOWED_HEX_INSIDE_COMMENTS and ("//" in line.split(m.group(0))[0]
                                            or line.strip().startswith("*")):
            continue
        hexes.append(m.group(0))
    if hexes:
        advisories.append({
            "kind": "off_palette_hex_color",
            "matches": list(set(hexes))[:10],
        })

    # font-family declarations
    if FONT_FAMILY_RX.search(src):
        advisories.append({"kind": "custom_font_family"})

    # Non-shared imports (heuristic)
    foreign_imports = []
    for m in NON_SHARED_IMPORT_RX.finditer(src):
        foreign_imports.append(m.group(0))
    # We don't flag every import; only those that look component-y
    flagged = [imp for imp in foreign_imports
               if any(tok in imp for tok in ("Card", "Dialog", "Filter",
                                             "Sidebar", "Modal", "Drawer"))
               and "/components/ui/" not in imp]
    if flagged:
        advisories.append({
            "kind": "non_inherited_component_import",
            "matches": flagged[:5],
        })

    return {"path": str(path.relative_to(REPO_ROOT)),
            "advisories": advisories}


def run() -> int:
    if not TARGETS_DIR.exists():
        msg = "ODR frontend dir not present — probe is a no-op."
        REPORT_PATH.write_text(
            "# ODR Inheritance Drift Report\n\n"
            f"_Generated: {_utc_now_iso()}_\n\n{msg}\n"
        )
        print(f"odr_inheritance_drift_probe · {msg}")
        return 0

    results = []
    for jsx in sorted(TARGETS_DIR.rglob("*.jsx")):
        results.append(scan(jsx))

    total_adv = sum(len(r["advisories"]) for r in results)
    state = "GREEN" if total_adv == 0 else "AMBER"

    lines = [
        "# ODR Inheritance Drift Report",
        "",
        f"_Generated: {_utc_now_iso()} · advisory probe._",
        "",
        "**Doctrine source:** `ODR_PLATFORM_INHERITANCE_DOCTRINE.md`",
        "",
        f"## Summary · {state} · {total_adv} advisory item(s)",
        "",
    ]
    for r in results:
        lines.append(f"### `{r['path']}`")
        if not r["advisories"]:
            lines.append("- No inheritance advisories.")
        else:
            for adv in r["advisories"]:
                lines.append(f"- **{adv['kind']}** · "
                             f"{ {k: v for k, v in adv.items() if k != 'kind'} }")
        lines.append("")

    lines += [
        "## ADVISORY",
        "",
        "This probe **never fails the build**. It surfaces likely",
        "inheritance drift that should pass through the documented",
        "divergence flow before merge.",
        "",
        "_Probe exit code: 0 (advisory)._",
    ]
    REPORT_PATH.write_text("\n".join(lines) + "\n")
    print(f"odr_inheritance_drift_probe · advisories={total_adv} · state={state}")
    print(f"  report -> {REPORT_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(run())
