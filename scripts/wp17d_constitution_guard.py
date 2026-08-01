#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path("/app")

CHECKS = [
    {
        "name": "home_banned_terminology",
        "file": ROOT / "frontend/src/pages/Hub.jsx",
        "patterns": [
            re.compile(r'\bMASCI Hub\b', re.IGNORECASE),
            re.compile(r'\bShared Operational Hub\b', re.IGNORECASE),
            re.compile(r'\bHome Hub\b', re.IGNORECASE),
            re.compile(r'\bOperations Hub\b', re.IGNORECASE),
        ],
    },
    {
        "name": "home_duplicate_sign_in",
        "file": ROOT / "frontend/src/pages/Hub.jsx",
        "patterns": [re.compile(r'>\s*Sign in\s*<', re.IGNORECASE)],
        "max_hits": 1,
    },
    {
        "name": "home_local_card_survivor",
        "file": ROOT / "frontend/src/pages/Hub.jsx",
        "patterns": [re.compile(r'wp17-public-card')],
        "max_hits": 0,
    },
    {
        "name": "home_explanatory_panel_survivor",
        "file": ROOT / "frontend/src/pages/Hub.jsx",
        "patterns": [
            re.compile(r'What needs attention now', re.IGNORECASE),
            re.compile(r'hub-attention-panel'),
        ],
        "max_hits": 0,
    },
    {
        "name": "home_duplicate_hero_identity",
        "file": ROOT / "frontend/src/pages/Hub.jsx",
        "patterns": [
            re.compile(r'wp17-kicker[^\n]*MASCI Operations Platform'),
            re.compile(r't\("MASCI Operations Platform"\)'),
        ],
        "max_hits": 0,
    },
    {
        "name": "header_whitewash_regression",
        "file": ROOT / "frontend/src/design-system/wp17.css",
        "patterns": [re.compile(r'\.masci-canonical-header\s*\{[^}]*rgba\(11, 18, 33, 0\.92\)', re.DOTALL)],
        "min_hits": 1,
    },
    {
        "name": "language_control_governance",
        "file": ROOT / "frontend/src/components/LangToggle.jsx",
        "patterns": [
            re.compile(r'SemanticIcon'),
            re.compile(r'border-red-500/38'),
            re.compile(r'aria-label="Select language"'),
        ],
        "min_hits": 3,
    },
    {
        "name": "home_brand_block_present",
        "file": ROOT / "frontend/src/components/CanonicalHeader.jsx",
        "patterns": [
            re.compile(r'masci-canonical-header__brand-company'),
            re.compile(r'masci-canonical-header__brand-product'),
            re.compile(r'brandCompany\s*=\s*"MASCI"'),
            re.compile(r'brandProduct\s*=\s*"Operations Platform"'),
        ],
        "min_hits": 4,
    },
    {
        "name": "home_brand_visual_hierarchy",
        "file": ROOT / "frontend/src/design-system/wp17.css",
        "patterns": [
            re.compile(r'masci-canonical-header__brand-company[^}]*color:\s*var\(--wp17-critical\)', re.DOTALL),
            re.compile(r'masci-canonical-header__brand-product[^}]*color:\s*rgba\(255, 255, 255, 0\.9\)', re.DOTALL),
            re.compile(r'masci-canonical-header__brand-company[^}]*font-weight:\s*900', re.DOTALL),
        ],
        "min_hits": 3,
    },
    {
        "name": "portal_shell_brand_propagation",
        "file": ROOT / "frontend/src/design-system/PortalShell.jsx",
        "patterns": [
            re.compile(r'contextLabel=\{resolvedContextLabel\}'),
            re.compile(r'variant="platform"'),
        ],
        "min_hits": 2,
    },
    {
        "name": "form_shell_brand_propagation",
        "file": ROOT / "frontend/src/components/FormShell.jsx",
        "patterns": [
            re.compile(r'contextLabel=\{title \|\| headerPortalLabel\}'),
            re.compile(r'variant="platform"'),
        ],
        "min_hits": 2,
    },
    {
        "name": "field_wave_no_hub_language",
        "file": ROOT / "frontend/src/components/BackLink.jsx",
        "patterns": [re.compile(r'label:\s*"Hub"')],
        "max_hits": 0,
    },
    {
        "name": "field_wave_no_ui_emoji_shortcuts",
        "file": ROOT / "frontend/src/pages/DailyReportsDashboard.jsx",
        "patterns": [re.compile(r'👷|🤝|🚶')],
        "max_hits": 0,
    },
    {
        "name": "field_wave_no_local_calculator_buttons",
        "file": ROOT / "frontend/src/pages/MaterialCalculators.jsx",
        "patterns": [
            re.compile(r'bg-amber-600'),
            re.compile(r'border-2 border-slate-300'),
        ],
        "max_hits": 0,
    },
    {
        "name": "field_wave_no_local_daily_report_cta_styles",
        "file": ROOT / "frontend/src/pages/ViewDailyReport.jsx",
        "patterns": [
            re.compile(r'bg-red-700'),
            re.compile(r'uppercase tracking-wide'),
        ],
        "max_hits": 0,
    },
    {
        "name": "field_wave_no_local_equipment_header",
        "file": ROOT / "frontend/src/pages/ViewEquipmentInspection.jsx",
        "patterns": [
            re.compile(r'<header className=`bg-slate-900'),
            re.compile(r'MasciLogo'),
        ],
        "max_hits": 0,
    },
    {
        "name": "logo_home_behavior",
        "file": ROOT / "frontend/src/components/MasciLogo.jsx",
        "patterns": [re.compile(r'aria-label="Go to MASCI Operations Platform Home"')],
        "min_hits": 1,
    },
]

EMOJI_RANGES = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002600-\U000027BF"
    "]",
    re.UNICODE,
)


def main() -> int:
    failures: list[str] = []

    for check in CHECKS:
        content = check["file"].read_text(encoding="utf-8")
        hits = sum(len(pattern.findall(content)) for pattern in check["patterns"])
        if "max_hits" in check and hits > check["max_hits"]:
            failures.append(f"{check['name']}: expected <= {check['max_hits']} hits, found {hits}")
        if "min_hits" in check and hits < check["min_hits"]:
            failures.append(f"{check['name']}: expected >= {check['min_hits']} hits, found {hits}")

    scoped_files = [
        ROOT / "frontend/src/pages/Hub.jsx",
        ROOT / "frontend/src/components/CanonicalHeader.jsx",
        ROOT / "frontend/src/components/LangToggle.jsx",
    ]
    emoji_hits = []
    for file_path in scoped_files:
        content = file_path.read_text(encoding="utf-8")
        if EMOJI_RANGES.search(content):
          emoji_hits.append(str(file_path))
    if emoji_hits:
        failures.append(f"ui_emoji_guard: emoji/unicode UI symbols detected in {', '.join(emoji_hits)}")

    if failures:
        print("WP-17D constitution guard failed:")
        for failure in failures:
            print(f" - {failure}")
        return 1

    print("WP-17D constitution guard passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())