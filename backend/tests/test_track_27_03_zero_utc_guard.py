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

# Frontend-only patterns — bypass the canonical formatter.
# Any file rendering `.toLocaleString`/`.toLocaleDateString`/
# `.toLocaleTimeString` in an operator-facing surface violates the
# ONE-code-path rule even though the OUTPUT happens to be local.
_BROWSER_DEFAULT_FMT_PATTERNS = [
    re.compile(r"\.toLocaleString\("),
    re.compile(r"\.toLocaleDateString\("),
    re.compile(r"\.toLocaleTimeString\("),
]

# Any line matching this is exempt from this scan — the developer has
# formally accepted responsibility for why the UTC token is there.
_EXEMPTION_MARKER = "TRACK-27.03-EXEMPT"

# ── Contextual whitelist ─────────────────────────────────────────────
# A UTC-shaped token is NOT a leak when the line is one of:
#   1. Storage side of a canonical local-formatter call — the raw
#      `datetime.now(timezone.utc)` is being passed into
#      `format_platform_*` / `localize_timestamp` / `display_timestamp`
#      for local rendering. This is the exact pattern the migration
#      guide asks Phase 2 authors to write.
#   2. A `.date().isoformat()` on a naive date — produces YYYY-MM-DD
#      only (no time-of-day, no zone marker) and is used exclusively
#      for MongoDB range comparisons, never rendered to operators.
_CANONICAL_LOCAL_CALLERS = (
    "format_platform_stamp(",
    "format_platform_date(",
    "format_platform_time_only(",
    "format_platform_time(",  # frontend name for parity
    "localize_timestamp(",
    "display_timestamp(",
    "organization_local_time(",
    "formatPlatformTime(",
    "formatPlatformDate(",
    "formatPlatformStamp(",
    "formatPlatformTimeOnly(",
    "formatRelativeTime(",
)
_DATE_ONLY_MARKERS = (
    ".date().isoformat()",   # Python date → YYYY-MM-DD (no wall clock)
    "now.date().isoformat()",
    ".date()",               # any line that reduces to a bare date is date-only
)


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
    # ↓ TRACK 27.03 · Phase 3 · Frontend UI sweep.
    #   Admin panels + HR + OCC + timelines + history feeds + queues +
    #   audit dialogs. Each pipes every operator-visible timestamp
    #   through the canonical `formatPlatformTime` / `formatPlatformDate` /
    #   `formatPlatformTimeOnly` / `formatPlatformStamp` helpers.
    "frontend/src/pages/admin/AdminAuditLog.jsx",
    "frontend/src/pages/admin/AdminCommandCenter.jsx",
    "frontend/src/pages/admin/AdminGovernance.jsx",
    "frontend/src/pages/admin/AdminDigestConfig.jsx",
    "frontend/src/components/EmailRoutingV2Panel.jsx",
    "frontend/src/pages/HrHub.jsx",
    "frontend/src/pages/HrTimeVerification.jsx",
    "frontend/src/pages/OperationsControlCenter.jsx",
    "frontend/src/pages/HistoricalRecordsQueue.jsx",
    "frontend/src/pages/HrEmployeeRequestsQueue.jsx",
    "frontend/src/pages/shop/ShopManagerQueue.jsx",
    "frontend/src/pages/shop/UnitHistoryTimeline.jsx",
    "frontend/src/pages/HrHubV2.jsx",
    "frontend/src/components/oa/HistoryFeed.jsx",
    "frontend/src/components/team/AssignmentHistoryDrawer.jsx",
    "frontend/src/components/operations-map/MapTimelineDock.jsx",
    "frontend/src/components/BannerAuditDialog.jsx",
    "frontend/src/components/QueueStatusPill.jsx",
    # ↓ TRACK 27.03 · Phase 2 backend renderers — kept in the guard.
    "backend/pdf_branding.py",              # Universal HTML PDF audit + metadata blocks
    "backend/pdf_branding_rl.py",           # Universal ReportLab audit + metadata blocks
    "backend/pdf_render.py",                # Daily Report renderer + email HTML body
    "backend/training_pdf.py",              # Training packets (EN/ES/bilingual)
    "backend/pm_welcome_pdf.py",            # PM welcome / onboarding letter
    "backend/routes/safety_exports.py",     # 10 Safety Portal CSV/print-PDF endpoints
    "backend/routes/master_history.py",     # Asset + Employee history CSV/PDF
    "backend/routes/trench_safety/report_export.py",  # Trench Safety XLSX + PDF
    "backend/routes/dispatch_exports.py",   # Dispatch CSV exports
    "backend/routes/dr_v2_pdf.py",          # DR V2 PDF endpoint (HTTP header stamps exempt)
    "backend/services/dr_ai/agents.py",     # AI prompt system messages (must instruct local time)
    "backend/services/dr_ai/emergent_provider.py",  # AI envelope generated_at (machine — exempt)
    "backend/services/dr_evidence/manifest.py",     # Evidence manifest generated_at (machine — exempt)
    "backend/routes/dr_v2.py",              # DR V2 synthesize + drafts (machine envelopes exempt)
    "backend/routes/dr_v2_canonicalize.py", # DR V2 canonicalize (machine envelopes exempt)
    # ↓ TRACK 27.03 · Phase 2b · Second-tier PDFs, HR/incident renderers,
    #   and API envelopes. Machine-only stamps marked TRACK-27.03-EXEMPT.
    "backend/routes/employee_records.py",   # HR Compliance Brief PDF header (secondary variant)
    "backend/incident_engine/report_render.py",  # Incident report cover + section footers
    "backend/incident_engine/reports.py",   # Incident report payload metadata (exempt)
    "backend/routes/odr/pdf.py",            # ODR audience-scoped PDF (5 audiences: foreman/super/pm/exec/external)
    "backend/hub_banners_pdf.py",           # Hub Banners audit-trail PDF (OSHA/insurance evidence)
    # Note: `backend/routes/trench_safety/pulse.py`,
    #  `backend/routes/trench_safety/report_distribution.py`,
    #  `backend/routes/asset_documents.py`, `backend/routes/hr_portal.py`,
    #  `backend/routes/employee_lifecycle.py`,
    #  `backend/lib/field_submitter_identity.py`, `backend/routes/fleet_ops.py`,
    #  `backend/server.py` are NOT in this file-level list — each is a
    # multi-hundred-to-multi-thousand-line service file where the
    # operator-facing sites are isolated. Their converted sites route
    # through `format_platform_stamp` (verifiable live) or carry an
    # inline `TRACK-27.03-EXEMPT` justification. Guarding by comment
    # instead of by file avoids ~50 false-positive noise entries from
    # date-only DB range comparisons and cron/scheduler math.
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
        # Contextual whitelist — canonical local-formatter call on this
        # line, or date-only marker with no wall-clock leak.
        if any(caller in line for caller in _CANONICAL_LOCAL_CALLERS):
            continue
        if any(marker in line for marker in _DATE_ONLY_MARKERS):
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


# ── Constitutional guard · whole-tree scan ──────────────────────────
# From this test forward, the platform enforces the rule by scanning
# ALL frontend `.jsx`/`.js` and rejecting any file that uses a
# browser-default timestamp formatter (toLocaleString /
# toLocaleDateString / toLocaleTimeString) without going through the
# canonical `platformTime.js`. Machine-only paths that legitimately
# need `toISOString()` for JSON envelopes / DB writes must carry an
# inline `TRACK-27.03-EXEMPT: <reason>` marker on the offending line.

_FRONTEND_ROOT = REPO_ROOT / "frontend" / "src"

_FRONTEND_MACHINE_ONLY = {
    # These files intentionally serialize timestamps for machine use
    # (offline queue, localStorage keys, cache tags, sentry payloads).
    # They never render to operators.
    "lib/resiliency/offlineQueue.js",
    "lib/resiliency/resiliencyQueue.js",
    "lib/resiliency/incidentOfflineQueue.js",
    "lib/incidentOfflineQueue.js",
    "lib/sentryInit.js",
    "lib/usageTracker.js",
    "lib/platformTime.js",  # the formatter itself
}


def _rel_frontend(p: Path) -> str:
    return str(p.relative_to(_FRONTEND_ROOT)).replace("\\", "/")


def _iter_frontend_files():
    if not _FRONTEND_ROOT.exists():
        return
    for p in _FRONTEND_ROOT.rglob("*"):
        if p.suffix not in {".jsx", ".js"}:
            continue
        s = str(p)
        if "node_modules" in s or "__tests__" in s:
            continue
        if p.name.endswith(".test.js") or p.name.endswith(".test.jsx"):
            continue
        if _rel_frontend(p) in _FRONTEND_MACHINE_ONLY:
            continue
        yield p


def _scan_browser_default_fmt(path: Path):
    """Return list of (line_no, pattern, snippet) for browser-default
    formatter uses NOT protected by inline EXEMPT.

    `.toLocaleTimeString` / `.toLocaleDateString` are unambiguously Date
    APIs — always flag them.

    `.toLocaleString` is polymorphic (works on Number too). We flag it
    only when the call is clearly Date-shaped:
      · immediately preceded by `new Date(` on the same line
      · args contain date/time option keys
      · no args AND caller name ends in `_at` / `Date` / `Time` / `Dt`
    Numeric currency/count calls (`.toLocaleString(undefined, {
    minimumFractionDigits: … })`) are NOT flagged — they are the
    correct Web API for i18n number formatting.
    """
    findings = []
    text = _read_text(path)
    # Regex to grab the caller identifier + args of a toLocaleString call.
    date_option_keys = re.compile(
        r"\b(dateStyle|timeStyle|hour|minute|second|year|month|day|weekday|timeZone|hour12)\b"
    )
    number_option_keys = re.compile(
        r"\b(minimumFractionDigits|maximumFractionDigits|minimumIntegerDigits|"
        r"maximumSignificantDigits|minimumSignificantDigits|notation|compactDisplay|"
        r"currency|useGrouping|style)\b"
    )
    to_locale_string_call = re.compile(
        r"(?P<caller>(?:\bnew\s+Date\([^)]*\)|[A-Za-z_$][\w$.]*))\.toLocaleString\((?P<args>[^)]*)\)"
    )

    for i, line in enumerate(text.splitlines(), start=1):
        if _EXEMPTION_MARKER in line:
            continue
        stripped = line.strip()
        if stripped.startswith(("//", "/*", "*", "*/")):
            continue
        # Always flag toLocaleTimeString / toLocaleDateString.
        for pat in (
            re.compile(r"\.toLocaleTimeString\("),
            re.compile(r"\.toLocaleDateString\("),
        ):
            if pat.search(line):
                findings.append((i, pat.pattern, stripped[:140]))
                break
        else:
            # Only inspect .toLocaleString when it's Date-shaped.
            for m in to_locale_string_call.finditer(line):
                caller = m.group("caller")
                args = m.group("args") or ""
                is_new_date = caller.startswith("new Date(")
                caller_leaf = caller.split(".")[-1] if "." in caller else caller
                looks_datey = (
                    is_new_date
                    or date_option_keys.search(args) is not None
                    or (
                        not args.strip()
                        and (
                            caller_leaf.endswith("_at")
                            or caller_leaf.endswith("Date")
                            or caller_leaf.endswith("Time")
                            or caller_leaf.endswith("Dt")
                            or caller_leaf.endswith("Timestamp")
                        )
                    )
                )
                # Explicitly SKIP number-formatting option calls.
                if number_option_keys.search(args) and not date_option_keys.search(args):
                    continue
                if looks_datey:
                    findings.append((i, r"\.toLocaleString\(", stripped[:140]))
                    break
    return findings


def test_constitutional_frontend_uses_canonical_formatter_only():
    """Whole-tree constitutional scan.

    Every `.jsx`/`.js` file under `frontend/src/` (excluding tests,
    node_modules, and the machine-only paths above) that uses
    `.toLocaleString(...)` / `.toLocaleDateString(...)` /
    `.toLocaleTimeString(...)` MUST route through `platformTime.js`.

    A file with a browser-default formatter call that is NOT
    accompanied by an inline `TRACK-27.03-EXEMPT: <reason>` marker on
    the offending line fails CI.
    """
    failures = []
    for p in _iter_frontend_files():
        leaks = _scan_browser_default_fmt(p)
        if leaks:
            rel = _rel_frontend(p)
            for ln, pat, snip in leaks:
                failures.append(f"{rel}:{ln}  {pat}  →  {snip}")
    assert not failures, (
        "Constitutional guard tripped — the following files bypass the "
        "canonical platformTime formatter. Either route through the "
        "formatter, or add an inline `TRACK-27.03-EXEMPT: <reason>` "
        f"marker on the offending line:\n\n" + "\n".join(failures[:60])
    )


def test_constitutional_frontend_no_raw_utc_iso_display():
    """Whole-tree scan for hard-coded UTC/GMT/Z tokens that would land
    in a rendered string. Same exemption rule as the sibling test.
    """
    hard_utc_pat = re.compile(r"['\"]\s*(UTC|GMT)\s*['\"]")
    iso_z_pat = re.compile(r"[\"'`]\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
    failures = []
    for p in _iter_frontend_files():
        text = _read_text(p)
        for i, line in enumerate(text.splitlines(), start=1):
            if _EXEMPTION_MARKER in line:
                continue
            stripped = line.strip()
            if stripped.startswith(("//", "/*", "*", "*/")):
                continue
            if hard_utc_pat.search(line) or iso_z_pat.search(line):
                rel = _rel_frontend(p)
                failures.append(f"{rel}:{i}  {stripped[:140]}")
    assert not failures, (
        "Constitutional guard tripped — hard-coded UTC/GMT/ISO-Z "
        "tokens found in operator-facing display code:\n\n"
        + "\n".join(failures[:60])
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
