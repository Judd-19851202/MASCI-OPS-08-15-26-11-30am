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
        "name": "field_forms_no_legacy_input_override",
        "file": ROOT / "frontend/src/pages/NewEquipmentInspection.jsx",
        "patterns": [
            re.compile(r'border-2 border-slate-300'),
            re.compile(r'bg-red-700 hover:bg-red-800'),
        ],
        "max_hits": 0,
    },
    {
        "name": "field_forms_no_local_dvir_toggle_styles",
        "file": ROOT / "frontend/src/pages/NewFleetDVIR.jsx",
        "patterns": [
            re.compile(r'bg-amber-600 hover:bg-amber-700'),
            re.compile(r'border-2 border-amber-300'),
            re.compile(r'<textarea'),
        ],
        "max_hits": 0,
    },
    {
        "name": "daily_report_prefill_buttons_governed",
        "file": ROOT / "frontend/src/pages/NewDailyReportV3.jsx",
        "patterns": [
            re.compile(r'rounded-lg bg-amber-600'),
            re.compile(r'rounded-md bg-emerald-600'),
        ],
        "max_hits": 0,
    },
    {
        "name": "shared_input_primitive_governed",
        "file": ROOT / "frontend/src/components/ui/input.jsx",
        "patterns": [re.compile(r'wp17-control'), re.compile(r'wp17-focus-ring')],
        "min_hits": 2,
    },
    {
        "name": "shared_select_primitive_governed",
        "file": ROOT / "frontend/src/components/ui/select.jsx",
        "patterns": [re.compile(r'wp17-control'), re.compile(r'wp17-focus-ring')],
        "min_hits": 2,
    },
    {
        "name": "shared_textarea_primitive_governed",
        "file": ROOT / "frontend/src/components/ui/textarea.jsx",
        "patterns": [re.compile(r'wp17-control'), re.compile(r'wp17-focus-ring')],
        "min_hits": 2,
    },
    {
        "name": "button_primitive_governed",
        "file": ROOT / "frontend/src/components/ui/button.jsx",
        "patterns": [re.compile(r'wp17-cta')],
        "min_hits": 1,
    },
    {
        "name": "page_header_primitive_governed",
        "file": ROOT / "frontend/src/design-system/PageHeader.jsx",
        "patterns": [re.compile(r'wp17-page-header'), re.compile(r'font-display text-4xl')],
        "min_hits": 2,
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

OPERATOR_BANNED_TERMS = [
    "WP-14F",
    "WP-17",
    "Certification",
    "Canonical",
    "Backend",
    "Frontend",
    "Mutation",
    "Governed",
    "Runtime",
    "Preview",
    "Fixture",
    "Audit",
    "Developer",
    "Engineering",
]

OPERATOR_LANGUAGE_SCAN_FILES = [
    ROOT / "frontend/src/pages/OperationsControlCases.jsx",
    ROOT / "frontend/src/pages/OperationsControlCaseDetail.jsx",
    ROOT / "frontend/src/pages/OperationsControlCasesRoute.jsx",
    ROOT / "frontend/src/pages/OperationsControlCenter.jsx",
    ROOT / "frontend/src/pages/admin/Wp17dCertificationDashboard.jsx",
    ROOT / "frontend/src/components/admin/sidebar/domainMap.js",
    ROOT / "frontend/src/app/admin/domainMapV3.js",
    ROOT / "frontend/src/lib/portalContinuity.js",
]

STRING_LITERAL_PATTERN = re.compile(r'"([^"\\]*(?:\\.[^"\\]*)*)"|\'([^\'\\]*(?:\\.[^\'\\]*)*)\'')
JSX_TEXT_PATTERN = re.compile(r">\s*([^<>{\n][^<>{}]*)\s*<")


def strip_js_comments(content: str) -> str:
    content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
    content = re.sub(r"(^|\s)//.*$", "", content, flags=re.MULTILINE)
    return content


def iter_operator_ui_strings(content: str):
    for match in STRING_LITERAL_PATTERN.finditer(content):
        value = match.group(1) or match.group(2) or ""
        yield value.strip()
    for match in JSX_TEXT_PATTERN.finditer(content):
        value = match.group(1).strip()
        yield value


def looks_user_facing(value: str) -> bool:
    if not value or len(value) < 4:
        return False
    if value.startswith(("/", ".", "#", "http", "bg-", "text-", "px-", "py-", "sm:", "md:", "lg:")):
        return False
    if any(token in value for token in ["data-testid", "className", "REACT_APP_", "X-Admin-Token", "X-Directory-Token"]):
        return False
    if re.fullmatch(r"[a-z0-9_.:/-]+", value):
        return False
    return bool(re.search(r"[A-Za-z]", value))


def operator_language_failures() -> list[str]:
    failures: list[str] = []
    patterns = [re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE) for term in OPERATOR_BANNED_TERMS]
    for file_path in OPERATOR_LANGUAGE_SCAN_FILES:
        content = strip_js_comments(file_path.read_text(encoding="utf-8"))
        for snippet in iter_operator_ui_strings(content):
            if not looks_user_facing(snippet):
                continue
            for pattern in patterns:
                if pattern.search(snippet):
                    failures.append(f"operator_language_guard: {file_path.relative_to(ROOT)} contains banned visible copy → {snippet[:120]}")
                    break
            if failures and failures[-1].startswith(f"operator_language_guard: {file_path.relative_to(ROOT)}"):
                break
    return failures


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

    failures.extend(operator_language_failures())

    if failures:
        print("WP-17D constitution guard failed:")
        for failure in failures:
            print(f" - {failure}")
        return 1

    print("WP-17D constitution guard passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())