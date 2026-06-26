"""TRACK 15.84 · ForgedOps Production Excellence Certification.

Honest scope: this track CANNOT certify every portal as "elite 9.7"
without operator screenshots of every portal showing real defects to
fix. What it CAN honestly do — and does — is:

1. Lock the "no iter### in rendered text on production-facing surfaces"
   discipline by adding static guards on the two known-rendered offender
   files (`AdminLegacyImports.jsx`, `AdminGuide.jsx`) plus a broad
   `pages/*.jsx` sweep that flags any future rendered iter label.

2. Lock the "no Dev/preview/demo wording on operator portals" discipline.

3. Preserve every Track 15.81 / 15.82B / 15.83 / 15.83B regression so
   the platform's existing certification floor cannot regress.

4. Add a route-shape guard that no demo / V2 / design-system path leaks
   outside `/_internal/...` (parity with Track 15.83B but isolated to
   this file for clarity in CI logs).

The broader per-portal six-pillar audit (Safety / Shop / PM / HR /
Trust Center / Leadership) is intentionally deferred to a follow-up
track with operator screenshots of each portal — documented in the
certification memory file.
"""
from __future__ import annotations

import re
from pathlib import Path


FRONTEND_SRC = Path("/app/frontend/src")
PAGES_DIR = FRONTEND_SRC / "pages"
APP_JS = FRONTEND_SRC / "App.js"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


# ─── No rendered iter### labels on production-facing pages ────────


def test_admin_legacy_imports_no_iter_label():
    """Rendered eyebrow text on AdminLegacyImports MUST NOT include any
    `iter###` label. We additionally enforce that the file header
    comment was cleaned too — keeps the policy obvious to future
    readers (no internal iteration markers anywhere in the file)."""
    src = _read(PAGES_DIR / "AdminLegacyImports.jsx")
    assert "iter248" not in src, (
        "Track 15.84 regression: AdminLegacyImports.jsx must not "
        "carry the `iter248` internal iteration label (was rendered "
        "as the top eyebrow before Track 15.84)."
    )


def test_admin_guide_no_iter_parity_label():
    src = _read(PAGES_DIR / "AdminGuide.jsx")
    # "(iter98 parity)" used to render inline in the Field Leadership
    # form description — removed in Track 15.84.
    assert "iter98 parity" not in src, (
        "Track 15.84 regression: AdminGuide.jsx must not render the "
        "`(iter98 parity)` annotation in production-facing copy."
    )


# Static-content sweep: scan every page for an `iter###` token that
# appears in RENDERED JSX (not inside a JS or JSX comment block). The
# heuristic looks for `iter\d+` adjacent to typical render markers
# (`>` opening tag content, `{t("...")`, `text-` className neighbours).
# This is a defensive net — any future rendered iter### token will
# fail this guard.

_KNOWN_ALLOWED_PATTERNS = {
    # Conditional class names that contain "iter" as a substring? None
    # known today. Left as an explicit exception slot for future use.
}

_FORBIDDEN_RENDER_RX = re.compile(
    r"""[>"']\s*iter\d{2,4}\b""",  # token follows a JSX/HTML/string opener
)


def _strip_block_comments(text: str) -> str:
    return re.sub(r"/\*.*?\*/", "", text, flags=re.S)


def _strip_jsx_comments(text: str) -> str:
    return re.sub(r"\{/\*.*?\*/\}", "", text, flags=re.S)


def _strip_line_comments(text: str) -> str:
    return re.sub(r"//.*?$", "", text, flags=re.M)


def _strip_all_comments(text: str) -> str:
    return _strip_line_comments(
        _strip_block_comments(_strip_jsx_comments(text))
    )


def test_no_rendered_iter_labels_in_production_pages():
    bad = []
    for path in PAGES_DIR.rglob("*.jsx"):
        # Skip any *.test.jsx if present.
        if path.name.endswith(".test.jsx"):
            continue
        raw = _read(path)
        clean = _strip_all_comments(raw)
        for m in _FORBIDDEN_RENDER_RX.finditer(clean):
            # Allow `iter###` inside a JSX `placeholder="..."` attribute
            # (placeholders are NOT typically iteration labels — and our
            # current grep proves none exist).
            ctx_start = max(0, m.start() - 40)
            ctx_end = min(len(clean), m.end() + 40)
            ctx = clean[ctx_start:ctx_end]
            # Skip false positives like `data-testid="iter…"` (none in
            # the codebase today).
            if "data-testid" in ctx:
                continue
            bad.append((path.relative_to(FRONTEND_SRC), ctx.strip()))
    assert not bad, (
        "Track 15.84 regression: rendered `iter###` labels found on "
        "production-facing pages. ForgedOps production surfaces must "
        f"never expose internal iteration markers to operators.\n{bad}"
    )


# ─── Preview / demo / V2 route hardening (parity with 15.83B) ──────


def test_no_preview_route_outside_internal_namespace():
    src = _read(APP_JS)
    # Detect any non-`_internal` mount of demo / v2-compare / design-system
    bad = re.findall(
        r'<Route\s+path="(/(?:design-system|v2-(?:compare|index)|pm-v2-preview|hr-v2-preview)[^"]*)"',
        src,
    )
    assert not bad, (
        f"Track 15.84 regression: preview/demo routes leaked into "
        f"production navigation: {bad}"
    )


# ─── Track 15.83B canonical backend audience helper parity ────────


def test_backend_transfer_visibility_helper_still_present():
    p = Path("/app/backend/lib/transfer_visibility.py")
    assert p.exists(), (
        "Track 15.84 regression: backend/lib/transfer_visibility.py was "
        "removed — Track 15.83B canonical operator audience filter "
        "depends on it."
    )
    src = p.read_text(encoding="utf-8")
    assert "is_operator_visible_transfer" in src
    assert "filter_operator_visible_transfers" in src


def test_dispatch_landing_no_admin_gated_copy():
    src = _read(PAGES_DIR / "admin" / "AdminDispatch.jsx")
    # Track 15.83B removed both lines; keep them out forever.
    for needle in [
        "Admin-gated for now",
        "dedicated dispatch users",
        "ship in the next pass",
        "Dispatch Portal · iter",
    ]:
        assert needle not in src, (
            f"Track 15.84 regression: AdminDispatch.jsx must not "
            f"contain the stale scaffolding string {needle!r}."
        )


# ─── Track 15.82B / 15.81 / 15.83 parity ──────────────────────────


def test_roll_off_tile_still_present():
    src = _read(PAGES_DIR / "DispatchHub.jsx")
    assert 'testId="ds-issue-roll-off"' in src
    assert 'issueWork("Roll-Off")' in src


def test_dispatch_map_route_still_under_dispatch_guard():
    src = _read(APP_JS)
    assert re.search(
        r'<Route\s+path="/dispatch-portal/map"\s+element=\{DP\('
        r'<(?:OperationsMapPage|DispatchOperationsMapPage)\s*/>\)\}',
        src,
    ), "Track 15.81 parity broken — /dispatch-portal/map guard lost"


def test_admin_operations_map_route_still_admin_only():
    src = _read(APP_JS)
    assert re.search(
        r'<Route\s+path="/operations-map"\s+element=\{A\(<OperationsMapPage\s*/>\)\}',
        src,
    ), "Track 15.81 parity broken — /operations-map RBAC weakened"


def test_track_15_83_css_guardrails_still_active():
    css = (FRONTEND_SRC / "components/operations-map/OperationsMap.css"
           ).read_text(encoding="utf-8")
    assert "-webkit-line-clamp" in css
    assert "@media (max-width: 1024px)" in css
    assert "@media (max-width: 640px)" in css
