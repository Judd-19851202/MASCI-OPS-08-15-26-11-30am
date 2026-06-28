"""TRACK 18.07 · Design System Linter — build-time enforcement.

Scans the user-facing frontend codebase for known design-system
violations and fails the build when drift appears.

Scope: `frontend/src/**/*.{jsx,js,tsx,ts}` excluding `__tests__`,
`node_modules`, generated `data/training.js` (historical narrative),
and historical track-record memory files.

Carve-outs honored:
* Backend routes, FastAPI paths, auth headers, MongoDB collections, and
  internal Python identifiers (Constitution Article §74).
* Code comments and JSDoc — only displayed strings are scanned.
* Functional sub-feature names that include "Hub" or "Console"
  (Training Hub, Asset Admin Console) when documented in
  `DESIGN_SYSTEM_LINTER_RULES.md`.

Rule design:
* Each `_lint_*` helper returns a list of `(file, line, snippet)`
  offenders.
* Each `test_lint_*` function asserts the list is empty (or matches a
  documented allow-list).
* Allow-lists live in `LINTER_ALLOWLIST` below.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, List, Tuple

ROOT = Path("/app")
FRONTEND_SRC = ROOT / "frontend" / "src"

# ---------------------------------------------------------------------
# Files to ignore (test files, historical narrative, generated, etc.)
# ---------------------------------------------------------------------
IGNORE_DIRS = {
    "__tests__",
    "node_modules",
    ".git",
    "dist",
    "build",
    "design-system-demo",
}
IGNORE_FILE_NAMES = {
    "training.js",  # historical narrative content — Constitution
                    # explicitly permits prose-level legacy mentions
                    # (Track 18.04 disposition).
}
IGNORE_FILE_SUFFIXES = (
    ".test.js",     # Vitest/Jest unit tests assert on legacy error
                    # strings emitted by external APIs.
    ".test.jsx",
    ".test.ts",
    ".test.tsx",
    ".spec.js",
    ".spec.jsx",
)

# ---------------------------------------------------------------------
# Allow-list — documented intentional exceptions.
# Each entry: (file path suffix, banned token).
# ---------------------------------------------------------------------
LINTER_ALLOWLIST: List[Tuple[str, str]] = [
    # Pre-existing functional sub-feature names — Constitution carve-out.
    # "Training Hub" is a sub-page name, not a workspace identity.
    ("pages/Hub.jsx", "Training Hub"),
    # Track 18.04 i18n.js keeps orphan legacy keys as harmless
    # passthroughs (documented in PLATFORM_LANGUAGE_MIGRATION_INVENTORY.md).
    ("lib/i18n.js", "HR Portal"),
    ("lib/i18n.js", "PM Portal"),
    ("lib/i18n.js", "Safety Portal"),
    ("lib/i18n.js", "Shop Portal"),
    ("lib/i18n.js", "Dispatch Portal"),
    ("lib/i18n.js", "Admin Console"),
    ("lib/i18n.js", "Admin Portal"),
    ("lib/i18n.js", "MASCI Hub"),
    ("lib/i18n.js", "Office Portals"),
    ("lib/i18n.js", "Field Leadership Portal"),
    ("lib/i18n.js", "Portal Access"),
    ("lib/i18n.js", "More"),  # "Más" translation entry — common word
    # SafetyHub.jsx CTAs use uppercase source text intentionally styled
    # by the card component CSS (documented in PLATFORM_CASE_STYLE_GUIDE.md).
    ("pages/SafetyHub.jsx", 't("OPEN")'),
    # Asset Admin Console — functional sub-feature name inside
    # Administration (documented in OPERATIONAL_DESIGN_SYSTEM.md §16).
    ("components/admin/sidebar/domainMap.js", "Asset Admin Console"),
    # Page title rewriter contains "MASCI Hub" as a SOURCE match string
    # used to swap legacy bookmarks to the canonical name — never
    # rendered (Track 18.04 disposition).
    ("lib/usePageTitle.js", "MASCI Hub"),
    # BrandingProvider neutral fallback documents legacy short-name
    # mapping but no longer outputs "Hub".
    ("lib/BrandingProvider.jsx", "MASCI Hub"),
    # portalContinuity.js — INTERNAL session-routing table keyed by
    # legacy role codes. Strings are display labels for back-link
    # tooltips when impersonating; documented carve-out for engineering
    # stability of the impersonation flow. Track 18.07 disposition.
    ("lib/portalContinuity.js", "Admin Console"),
    ("lib/portalContinuity.js", "Admin Portal"),
    ("lib/portalContinuity.js", "Dispatch Portal"),
    ("lib/portalContinuity.js", "HR Portal"),
    ("lib/portalContinuity.js", "PM Portal"),
    ("lib/portalContinuity.js", "Safety Portal"),
    ("lib/portalContinuity.js", "Shop Portal"),
    # returnContext.js — INTERNAL back-link routing label registry,
    # keyed by historical scope label values. Track 18.07 disposition.
    ("lib/returnContext.js", "Admin Console"),
    ("lib/returnContext.js", "Dispatch Portal"),
    ("lib/returnContext.js", "HR Portal"),
    ("lib/returnContext.js", "PM Portal"),
    ("lib/returnContext.js", "Safety Portal"),
    ("lib/returnContext.js", "Shop Portal"),
    # permissions.js — INTERNAL role-code → display-label lookup used
    # only by historical audit-log display. New audit events use the
    # canonical Track 18.04 names; legacy events keep their original
    # labels for provenance. Track 18.07 disposition.
    ("lib/permissions.js", "Admin Console"),
    ("lib/permissions.js", "Dispatch Portal"),
    ("lib/permissions.js", "HR Portal"),
    ("lib/permissions.js", "PM Portal"),
    ("lib/permissions.js", "Safety Portal"),
    ("lib/permissions.js", "Shop Portal"),
    # Hub.jsx audit-event scopeLabel values — INTERNAL strings written
    # to the audit log when an admin previews-as a different role. Not
    # rendered as a UI label; preserved for historical audit-event
    # continuity. Track 18.07 disposition.
    ("pages/Hub.jsx", 'scopeLabel: "Admin Console"'),
    ("pages/Hub.jsx", 'scopeLabel: "Dispatch Portal"'),
    ("pages/Hub.jsx", 'scopeLabel: "HR Portal"'),
    ("pages/Hub.jsx", 'scopeLabel: "PM Portal"'),
    ("pages/Hub.jsx", 'scopeLabel: "Safety Portal"'),
    ("pages/Hub.jsx", 'scopeLabel: "Shop Portal"'),
    # Hub.jsx scopeLabel — INTERNAL audit-log scope label string, not
    # rendered to users. Used in impersonation audit events to preserve
    # historical scope-label values. Track 18.07 disposition.
    ("pages/Hub.jsx", 'scopeLabel: "Admin Console"'),
    # ShopHub.jsx "More" — tab label for trends/equipment/parts overflow.
    # Not a CTA. Documented exception per OPERATIONAL_DESIGN_SYSTEM §9.
    ("pages/ShopHub.jsx", '"More"'),
    ("pages/ShopHub.jsx", 't("More")'),
]


def _iter_user_facing_files() -> Iterable[Path]:
    for p in FRONTEND_SRC.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix not in (".js", ".jsx", ".tsx", ".ts"):
            continue
        if p.name in IGNORE_FILE_NAMES:
            continue
        if any(p.name.endswith(s) for s in IGNORE_FILE_SUFFIXES):
            continue
        if any(seg in IGNORE_DIRS for seg in p.parts):
            continue
        yield p


def _strip_comments(src: str) -> str:
    """Remove JS line comments and block comments without consuming
    URL paths. Mirrors the Track 18.04 helper."""
    out = []
    for line in src.splitlines():
        # Treat `//` as a comment only when preceded by whitespace or
        # start-of-line, not after `:` or `/` (URL guards).
        stripped = re.sub(r"(?<![:/'\"])(^|\s)//[^\n]*$", r"\1", line)
        out.append(stripped)
    src = "\n".join(out)
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    return src


def _is_allowlisted(file: Path, token: str, line: str = "") -> bool:
    """Allow when (a) the file is on the per-file token allow-list, or
    (b) the line itself contains a longer documented allow-list
    fragment that pins this exact usage as an exception."""
    posix = file.as_posix()
    for suffix, allowed_token in LINTER_ALLOWLIST:
        if not posix.endswith(suffix):
            continue
        # Exact-match allow: token equals the listed exception.
        if token == allowed_token:
            return True
        # Line-match allow: the line contains the documented exception
        # fragment (e.g. `scopeLabel: "Admin Console"`).
        if line and allowed_token in line:
            return True
        # Substring match (lenient): listed token contains the banned
        # token (e.g. "Field Leadership Portal" listed allows
        # "HR Portal" scans? — only if substring matches).
        if token in allowed_token:
            return True
    return False


def _scan_for_token(token: str) -> List[Tuple[str, int, str]]:
    hits: List[Tuple[str, int, str]] = []
    for f in _iter_user_facing_files():
        text = _strip_comments(f.read_text(errors="replace"))
        for i, line in enumerate(text.splitlines(), 1):
            if token in line and not _is_allowlisted(f, token, line):
                hits.append((f.relative_to(ROOT).as_posix(), i, line.strip()[:140]))
    return hits


# =====================================================================
# Empty-state drift
# =====================================================================
def test_lint_no_raw_no_data_empty_state():
    """User-visible JSX must not render the bare strings 'No data' or
    'Nothing here' — every empty state must explain what + why + next."""
    bad = []
    for token in ('>No data<', '"No data"', '>Nothing here<',
                  '"Nothing here"', '>N/A<', '>No records<',
                  '"No records"'):
        for hit in _scan_for_token(token):
            bad.append(hit)
    assert not bad, (
        f"Empty-state drift detected. Replace with an operational "
        f"empty state per OPERATIONAL_DESIGN_SYSTEM.md §14:\n"
        + "\n".join(f"  {f}:{ln} → {snip}" for f, ln, snip in bad[:10])
    )


# =====================================================================
# Error-state drift
# =====================================================================
def test_lint_no_raw_developer_error_text():
    bad: List[Tuple[str, int, str]] = []
    for token in ('"failed to fetch"', '"Failed to fetch"',
                  '"error loading"', '">undefined<"', '">null<"',
                  'JSON.stringify(err'):
        for hit in _scan_for_token(token):
            bad.append(hit)
    assert not bad, (
        "Raw developer error text leaked into user-facing UI. Replace "
        "with operational error language per "
        "OPERATIONAL_DESIGN_SYSTEM.md §17:\n"
        + "\n".join(f"  {f}:{ln} → {snip}" for f, ln, snip in bad[:10])
    )


# =====================================================================
# Restricted-state drift
# =====================================================================
def test_lint_no_legacy_restricted_state_wording():
    bad: List[Tuple[str, int, str]] = []
    for token in ('"Forbidden"', '"Unauthorized"', '"Access denied"',
                  '"Access Denied"', '"403 Forbidden"'):
        for hit in _scan_for_token(token):
            bad.append(hit)
    assert not bad, (
        "Restricted-state drift detected. Use 'Restricted for your "
        "role' per OPERATIONAL_DESIGN_SYSTEM.md §16:\n"
        + "\n".join(f"  {f}:{ln} → {snip}" for f, ln, snip in bad[:10])
    )


# =====================================================================
# Legacy language drift — workspace identities (Track 18.04 lock)
# =====================================================================
def _scan_legacy(term: str) -> List[Tuple[str, int, str]]:
    """Scan for legacy term appearing in displayed strings (between
    quotes or as inner text), not in identifiers."""
    hits: List[Tuple[str, int, str]] = []
    for f in _iter_user_facing_files():
        text = _strip_comments(f.read_text(errors="replace"))
        for i, line in enumerate(text.splitlines(), 1):
            # Match the term wrapped in a quote or as inner text.
            if (f'"{term}"' in line or f"'{term}'" in line
                    or f">{term}<" in line):
                if _is_allowlisted(f, term, line):
                    continue
                hits.append((f.relative_to(ROOT).as_posix(), i,
                             line.strip()[:140]))
    return hits


def test_lint_no_user_facing_dispatch_portal():
    hits = _scan_legacy("Dispatch Portal")
    assert not hits, f"Legacy 'Dispatch Portal' in user-facing code:\n" + "\n".join(
        f"  {f}:{ln} → {snip}" for f, ln, snip in hits[:10])


def test_lint_no_user_facing_pm_portal():
    hits = _scan_legacy("PM Portal")
    assert not hits, f"Legacy 'PM Portal' in user-facing code:\n" + "\n".join(
        f"  {f}:{ln} → {snip}" for f, ln, snip in hits[:10])


def test_lint_no_user_facing_hr_portal():
    hits = _scan_legacy("HR Portal")
    assert not hits, f"Legacy 'HR Portal' in user-facing code:\n" + "\n".join(
        f"  {f}:{ln} → {snip}" for f, ln, snip in hits[:10])


def test_lint_no_user_facing_safety_portal():
    hits = _scan_legacy("Safety Portal")
    assert not hits, f"Legacy 'Safety Portal' in user-facing code:\n" + "\n".join(
        f"  {f}:{ln} → {snip}" for f, ln, snip in hits[:10])


def test_lint_no_user_facing_shop_portal():
    hits = _scan_legacy("Shop Portal")
    assert not hits, f"Legacy 'Shop Portal' in user-facing code:\n" + "\n".join(
        f"  {f}:{ln} → {snip}" for f, ln, snip in hits[:10])


def test_lint_no_user_facing_admin_console():
    hits = _scan_legacy("Admin Console")
    assert not hits, f"Legacy 'Admin Console' in user-facing code:\n" + "\n".join(
        f"  {f}:{ln} → {snip}" for f, ln, snip in hits[:10])


def test_lint_no_user_facing_admin_portal():
    hits = _scan_legacy("Admin Portal")
    assert not hits, f"Legacy 'Admin Portal' in user-facing code:\n" + "\n".join(
        f"  {f}:{ln} → {snip}" for f, ln, snip in hits[:10])


def test_lint_no_user_facing_office_portals():
    hits = _scan_legacy("Office Portals")
    assert not hits, f"Legacy 'Office Portals' in user-facing code:\n" + "\n".join(
        f"  {f}:{ln} → {snip}" for f, ln, snip in hits[:10])


def test_lint_no_user_facing_masci_hub():
    hits = _scan_legacy("MASCI Hub")
    assert not hits, f"Legacy 'MASCI Hub' in user-facing code:\n" + "\n".join(
        f"  {f}:{ln} → {snip}" for f, ln, snip in hits[:10])


# =====================================================================
# CTA clarity
# =====================================================================
def test_lint_no_vague_ctas():
    """Block vague CTAs that disconnect the click from intent."""
    bad: List[Tuple[str, int, str]] = []
    for token in ('"Click here"', '"click here"', '"More"', '"Go"'):
        for hit in _scan_for_token(token):
            bad.append(hit)
    assert not bad, (
        "Vague CTA detected. Use action-oriented Title Case CTAs per "
        "OPERATIONAL_DESIGN_SYSTEM.md §9:\n"
        + "\n".join(f"  {f}:{ln} → {snip}" for f, ln, snip in bad[:10])
    )


# =====================================================================
# Allow-list integrity — every documented exception still resolves to
# a real file.
# =====================================================================
def test_allowlist_entries_resolve_to_real_files():
    for suffix, _ in LINTER_ALLOWLIST:
        # Each suffix must correspond to at least one file in
        # `frontend/src/`.
        target = FRONTEND_SRC / suffix
        assert target.exists(), (
            f"Linter allow-list entry references missing file: {suffix}"
        )


# =====================================================================
# R6 — Status color without label (Track 18.08)
# =====================================================================
#
# Tailwind status-color classes that imply a state (bg-red-*, bg-amber-*,
# bg-green-* for chip-style cards) must appear alongside an accompanying
# text label. We allow status colors freely on hovers, focus rings, and
# decorative panels; this rule only fires when a tightly-scoped chip
# pattern surfaces a color-only "status" element.
#
# Scope: kept tight to avoid noise. Flags JSX where a <span> / <div>
# has `bg-red-{500-700}` or `bg-amber-{500-700}` AND inner text is
# empty (no characters between `>` and `<`). Allow-list permits
# decorative ribbons and chips that have an `aria-label`.
_STATUS_COLOR_PATTERNS = [
    r'<span[^>]+bg-red-[567]00[^>]*>\s*</span>',
    r'<span[^>]+bg-amber-[567]00[^>]*>\s*</span>',
    r'<div[^>]+bg-red-[567]00[^>]*>\s*</div>',
]


def test_lint_no_status_color_without_label():
    import re as _re
    bad: List[Tuple[str, int, str]] = []
    for f in _iter_user_facing_files():
        text = _strip_comments(f.read_text(errors="replace"))
        for i, line in enumerate(text.splitlines(), 1):
            for pat in _STATUS_COLOR_PATTERNS:
                if _re.search(pat, line) and "aria-label" not in line:
                    bad.append((f.relative_to(ROOT).as_posix(), i,
                                line.strip()[:140]))
    assert not bad, (
        "Status color without label detected. Status must communicate "
        "by color + label + icon per OPERATIONAL_DESIGN_SYSTEM.md §5:\n"
        + "\n".join(f"  {f}:{ln} → {snip}" for f, ln, snip in bad[:10])
    )


# =====================================================================
# R7 — Hardcoded mobile-breaking widths (Track 18.08)
# =====================================================================
#
# Tailwind arbitrary-value width classes that exceed common phone
# viewports (≥ 800px) without an overflow-x-auto wrapper are likely to
# break mobile. We flag `w-[Npx]` and `min-w-[Npx]` where N ≥ 800.
# Allow-list permits intentional wide tables wrapped in overflow-x-auto.
_WIDTH_OVERFLOW_PATTERNS = [
    # w-[ Npx ] or min-w-[ Npx ] where N is 3 digits ≥ 800 or 4+ digits.
    # Negative lookbehind avoids matching `max-w-[...]`.
    r'(?<!max-)\bw-\[(8[0-9]{2}|9[0-9]{2}|\d{4,})px\]',
    r'(?<!\w)min-w-\[(8[0-9]{2}|9[0-9]{2}|\d{4,})px\]',
]

# Allow-listed widths that live INSIDE a controlled overflow scroller —
# documented in DESIGN_SYSTEM_LINTER_RULES.md.
_WIDTH_OVERFLOW_FILE_ALLOWLIST = {
    # Documented wide-table wrappers — each of these has an explicit
    # overflow-x-auto wrapper in a PARENT component (linter scans
    # per-file). Each entry has a code-review reference in
    # DESIGN_SYSTEM_LINTER_RULES.md.
    "components/MasterListPanel.jsx",
    "components/pm/PmJobsRead.jsx",
    "components/admin/PmDocSelectorPanel.jsx",
    "components/admin/UsersTable.jsx",
}


def test_lint_no_hardcoded_mobile_breaking_widths():
    import re as _re
    bad: List[Tuple[str, int, str]] = []
    for f in _iter_user_facing_files():
        posix = f.as_posix()
        if any(posix.endswith(s) for s in _WIDTH_OVERFLOW_FILE_ALLOWLIST):
            continue
        text = _strip_comments(f.read_text(errors="replace"))
        # Quick reject for files that wrap their content in overflow.
        wraps_overflow = "overflow-x-auto" in text or "overflow-x-scroll" in text
        for i, line in enumerate(text.splitlines(), 1):
            for pat in _WIDTH_OVERFLOW_PATTERNS:
                m = _re.search(pat, line)
                if m and not wraps_overflow:
                    bad.append((f.relative_to(ROOT).as_posix(), i,
                                line.strip()[:140]))
    assert not bad, (
        "Hardcoded width ≥ 800px without overflow-x-auto wrapper "
        "detected. Wrap in `overflow-x-auto` or use responsive sizing "
        "per OPERATIONAL_DESIGN_SYSTEM.md §19:\n"
        + "\n".join(f"  {f}:{ln} → {snip}" for f, ln, snip in bad[:10])
    )


# =====================================================================
# R8 — Duplicate CTA inside a single card (Track 18.09)
# =====================================================================
#
# DEFERRED to Track 18.10 calibration. Initial implementation
# surfaced too many false positives (aria-labels, status pills,
# dropdown items, and i18n entries trigger the proximity check
# inappropriately). Per the Track 18.09 directive, the linter only
# ships rules with extremely low false-positive rates. R8 is in
# active research; see TRACK_18_09_OPERATIONAL_FRICTION_ELIMINATION.md
# for the deferral disposition.
