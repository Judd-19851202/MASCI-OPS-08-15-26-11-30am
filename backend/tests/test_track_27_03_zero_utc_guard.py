"""TRACK 27.03 · Zero-UTC regression guard.

Runs as part of the standard pytest suite. Fails if any file listed in
`_OPERATOR_FACING_MODULES` displays a UTC token an operator would see.

The scanner is intentionally narrow: it inspects only *user-facing*
files (PDF renderers, email templates, dashboard components,
AI-prompt assemblers, export writers). Backend internal code paths
(scheduler, background workers, DB writes, log statements) continue
to use UTC and are excluded by design.

Adding a file to the exclusion list requires a code comment
`# TRACK-27.03-EXEMPT: <reason>` on the offending line, or a
one-line justification in this file.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


# ── Regex bank: patterns that leak UTC to operators ─────────────────
_UTC_TOKEN_PATTERNS = [
    re.compile(r"\butcnow\("),
    re.compile(r"datetime\.now\(\s*timezone\.utc\s*\)"),
    re.compile(r"\btoISOString\("),
    re.compile(r"\btoUTCString\("),
    re.compile(r"\.isoformat\(\)"),
    # A hard-coded literal " UTC" or " GMT" in strings printed to users.
    re.compile(r"['\"]\s*(UTC|GMT)\s*['\"]"),
    # ISO stamps in template strings (crude heuristic).
    re.compile(r"[\"'`]\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z"),
]

# Any line matching this is exempt from this scan — the developer has
# formally accepted responsibility for why the UTC token is there.
_EXEMPTION_MARKER = "TRACK-27.03-EXEMPT"


# ── Operator-facing surfaces that MUST NOT leak UTC ─────────────────
# The list starts intentionally narrow — 5 highest-visibility surfaces
# we converted in Phase 1. As Phase 2 lands each additional module,
# add its file(s) here and this test will catch regressions.
_OPERATOR_FACING_MODULES = [
    "frontend/src/lib/platformTime.js",     # canonical formatter itself
    "backend/lib/platform_time.py",         # canonical backend formatter
    # ↓ Converted in Phase 1 — proof-of-pattern surfaces.
    "frontend/src/components/HrCompletenessTile.jsx",
    "frontend/src/pages/AdminDeployReadiness.jsx",
    "frontend/src/pages/admin/AdminAIConfiguration.jsx",
    "frontend/src/components/OperationsCenter.jsx",
    "frontend/src/components/dispatch/DispatchDecisionChip.jsx",
    # Additional modules added as Phase 2 lands them — see
    # /app/memory/TRACK_27_03_PLATFORM_TIME_MIGRATION.md.
]


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _scan_for_utc_leaks(path: Path) -> list[tuple[int, str, str]]:
    """Return a list of (line_no, pattern_repr, line_text) for every
    line in `path` that violates the zero-UTC rule and is not
    explicitly exempted."""
    findings: list[tuple[int, str, str]] = []
    text = _read_text(path)
    if not text:
        return findings

    lines = text.splitlines()
    # Track whether we're inside a Python triple-quoted docstring so
    # we can skip the doc-lines that mention UTC as documentation.
    in_py_docstring = False
    py_open = ('"""', "'''")

    for i, line in enumerate(lines, start=1):
        if _EXEMPTION_MARKER in line:
            continue
        stripped = line.strip()
        # Toggle Python docstring state.
        if path.suffix == ".py":
            for token in py_open:
                if token in stripped:
                    # Even number of occurrences on the line = neutral;
                    # odd = toggle.
                    if stripped.count(token) % 2 == 1:
                        in_py_docstring = not in_py_docstring
                        break
            if in_py_docstring:
                continue
        # Skip C/JS comment lines (including JSDoc `*` continuations).
        if stripped.startswith(("#", "//", "/*", "*", "*/")):
            continue
        for pat in _UTC_TOKEN_PATTERNS:
            if pat.search(line):
                findings.append((i, pat.pattern, stripped[:140]))
                break
    return findings


# ── Canonical formatter contract tests ──────────────────────────────
def test_backend_platform_time_contract():
    """The canonical backend formatter must:
    · never return a raw ISO-Z string
    · never render the literal 'UTC' or 'GMT'
    · render local zone name (EDT/EST/PDT/etc.)"""
    from lib.platform_time import (  # noqa: PLC0415
        localize_timestamp, format_platform_stamp, format_platform_date,
        format_platform_time_only,
    )
    ts = "2026-07-09T18:53:24Z"  # 2:53 PM EDT
    rendered = localize_timestamp(ts, tz="America/New_York")
    assert "UTC" not in rendered
    assert "GMT" not in rendered
    assert "Z" not in rendered.split()  # accept 'Zone' etc. but not standalone Z
    assert "T18:53:24" not in rendered

    stamp = format_platform_stamp(ts, tz="America/New_York")
    assert "UTC" not in stamp and "GMT" not in stamp
    # Zone name must be present (e.g. EDT / EST)
    assert any(z in stamp for z in ("EDT", "EST", "AST", "PDT", "PST"))

    assert format_platform_date(ts, tz="America/New_York") == "Jul 9, 2026"
    assert "PM" in format_platform_time_only(ts, tz="America/New_York")


def test_backend_platform_time_honours_tz_argument():
    from lib.platform_time import localize_timestamp
    ts = "2026-07-09T18:53:24Z"
    ny = localize_timestamp(ts, tz="America/New_York")
    la = localize_timestamp(ts, tz="America/Los_Angeles")
    # Different zones must render different local times.
    assert ny != la


def test_backend_platform_time_gracefully_handles_bad_input():
    from lib.platform_time import localize_timestamp
    assert localize_timestamp(None) == "—"
    assert localize_timestamp("") == "—"
    assert localize_timestamp("garbage") == "—"
    assert localize_timestamp("2026-07-09T18:53:24Z", fallback="n/a")


def test_no_operator_facing_file_leaks_utc():
    """Any file registered in `_OPERATOR_FACING_MODULES` MUST NOT leak
    UTC tokens. Adding a module to the list without cleaning it first
    will fail this test — which is the whole point."""
    failures: list[str] = []
    for rel in _OPERATOR_FACING_MODULES:
        path = REPO_ROOT / rel
        if not path.exists():
            failures.append(f"missing: {rel}")
            continue
        leaks = _scan_for_utc_leaks(path)
        # For the canonical formatter itself, docstrings mention UTC —
        # only fail if the token appears OUTSIDE a comment (already
        # skipped above) or without an EXEMPT marker.
        real_leaks = [
            f"  line {ln}: /{pat}/  →  {snip}"
            for ln, pat, snip in leaks
        ]
        if real_leaks:
            failures.append(f"{rel}\n" + "\n".join(real_leaks))
    assert not failures, (
        "Zero-UTC guard tripped in operator-facing modules:\n\n"
        + "\n\n".join(failures)
    )


@pytest.mark.parametrize("rel_path", [
    "frontend/src/lib/platformTime.js",
    "backend/lib/platform_time.py",
])
def test_canonical_formatter_exports_expected_symbols(rel_path):
    """The canonical formatters must continue to export the documented
    symbol names — Phase 2 files import them by name."""
    text = _read_text(REPO_ROOT / rel_path)
    if rel_path.endswith(".js"):
        for symbol in ("formatPlatformTime", "formatPlatformDate",
                       "formatPlatformTimeOnly", "formatRelativeTime",
                       "formatPlatformStamp", "getPlatformTimezone"):
            assert f"export function {symbol}" in text or f"export {{" in text, symbol
    else:
        for symbol in ("localize_timestamp", "display_timestamp",
                       "format_platform_date", "format_platform_time_only",
                       "format_platform_stamp", "organization_local_time",
                       "resolve_tz"):
            assert f"def {symbol}" in text, symbol
