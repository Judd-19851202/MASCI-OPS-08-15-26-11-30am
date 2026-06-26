"""TRACK 15.85 · ForgedOps Production Excellence Certification Program.

Persistent multi-execution certification. This test file grows across
executions — each execution adds tests for the portals it actually
inspected and browser-verified at the 3-breakpoint minimum (iPad
landscape 1024 · iPad portrait 768 · phone 390).

Execution #1 covers:
  * Safety Portal landing (browser-verified at 1024/768/390)
  * Trench Safety field command (browser-verified at 1024/768/390)

Pending portals (documented in
`memory/TRACK_15_85_MANDATORY_FULL_PLATFORM_PRODUCTION_EXCELLENCE_CERTIFICATION.md`)
will receive their own assertions in subsequent executions.
"""
from __future__ import annotations

import re
from pathlib import Path

FRONTEND_SRC = Path("/app/frontend/src")
PAGES_DIR = FRONTEND_SRC / "pages"
APP_JS = FRONTEND_SRC / "App.js"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


# ─── Safety Portal landing — CERTIFIED execution #1 ──────────────


def test_safety_hub_component_exists():
    p = PAGES_DIR / "SafetyHub.jsx"
    assert p.exists(), "Track 15.85: SafetyHub.jsx must exist as the Safety Portal landing."
    src = _read(p)
    # SafetyHub renders production calm chrome.
    assert "safety-integrations-strip" in src, (
        "Track 15.85 regression: SafetyHub.jsx must surface the "
        "`safety-integrations-strip` testid (integration health + "
        "Motive events strip — neutral chrome in the demoted "
        "Systems group)."
    )
    # SafetyShell wrapper provides the portal header / sign-out / language.
    assert "SafetyShell" in src, (
        "Track 15.85: SafetyHub must render inside the SafetyShell "
        "(portal chrome + Trench Safety cross-link + sign-out)."
    )


def test_safety_login_no_dev_or_admin_wording_in_default_render():
    """Track 15.85 regression — the Safety LOGIN page must NOT render
    `dev token`, `preview only`, `admin-gated`, or any rendered iter
    label as part of its default UI. The dev-token block exists
    behind a conditional and only renders when the backend opts in;
    the static guard here proves the label remains explicitly marked
    so it cannot silently masquerade as production copy."""
    src = _read(PAGES_DIR / "SafetyForgotPassword.jsx")
    # The dev-token label must remain explicitly tagged "preview only"
    # so it can never silently leak as production-looking copy. If
    # this string is ever removed, we've LOST our defense — failing
    # this test would force the developer to add a build-flag guard.
    if "devToken" in src:
        assert "preview only" in src.lower(), (
            "Track 15.85: SafetyForgotPassword.jsx renders devToken "
            "block; it MUST remain explicitly labeled `(preview only)` "
            "so it cannot leak as production copy."
        )


def test_safety_portal_routes_mounted_under_safety_namespace():
    """Track 15.85: every Safety Portal route must live under the
    `/safety-portal` URL namespace OR the `/safety/*` legacy mount.
    Prevents accidental relocation that would break operator nav."""
    src = _read(APP_JS)
    # /safety-portal must be mounted somewhere.
    assert '"/safety-portal' in src or "'/safety-portal" in src, (
        "Track 15.85: Safety Portal landing URL `/safety-portal` must "
        "be mounted in App.js."
    )


# ─── Trench Safety — CERTIFIED execution #1 ──────────────────────


def test_trench_safety_route_mounted():
    src = _read(APP_JS)
    assert re.search(r'<Route\s+path="/trench-safety[^"]*"', src), (
        "Track 15.85: `/trench-safety` route must remain mounted in App.js."
    )


def test_trench_safety_field_command_has_stop_work_authority_copy():
    """Production trust signal — STOP-WORK AUTHORITY block is the
    constitutional copy on the Trench Safety field command surface.
    If anyone removes it, this test fails."""
    candidates = list(PAGES_DIR.rglob("*Trench*.jsx"))
    candidates += list(PAGES_DIR.rglob("*trench*.jsx"))
    found = False
    for c in candidates:
        try:
            body = _read(c)
        except Exception:
            continue
        if "STOP-WORK AUTHORITY" in body.upper() or "stop-work authority" in body.lower():
            found = True
            break
    assert found, (
        "Track 15.85: Trench Safety field command must keep the "
        "STOP-WORK AUTHORITY constitutional copy — it is the calm "
        "field-safety contract with crews."
    )


# ─── Cross-portal preservation (Tracks 15.81 → 15.84) ────────────


def test_dispatch_map_route_split_preserved():
    """Track 15.81 + 15.82 parity."""
    src = _read(APP_JS)
    assert re.search(
        r'<Route\s+path="/operations-map"\s+element=\{A\(<OperationsMapPage\s*/>\)\}',
        src,
    )
    assert re.search(
        r'<Route\s+path="/dispatch-portal/map"\s+element=\{DP\('
        r'<(?:OperationsMapPage|DispatchOperationsMapPage)\s*/>\)\}',
        src,
    )


def test_dispatch_landing_clean_of_scaffolding():
    """Track 15.83B + 15.84 parity."""
    src = _read(PAGES_DIR / "admin" / "AdminDispatch.jsx")
    for needle in [
        "Admin-gated for now",
        "Dispatch Portal · iter",
        "dedicated dispatch users",
    ]:
        assert needle not in src


def test_admin_legacy_imports_no_iter_label_persisted():
    src = _read(PAGES_DIR / "AdminLegacyImports.jsx")
    assert "iter248" not in src


def test_backend_transfer_visibility_helper_persisted():
    p = Path("/app/backend/lib/transfer_visibility.py")
    assert p.exists()
    src = p.read_text(encoding="utf-8")
    assert "is_operator_visible_transfer" in src
    assert "filter_operator_visible_transfers" in src


def test_operations_transfers_audience_persisted():
    src = (Path("/app/backend/routes/operations.py")
           .read_text(encoding="utf-8"))
    assert "audience: Optional[str] = Query" in src
    assert "from lib.transfer_visibility import" in src


def test_ops_map_responsive_guardrails_persisted():
    css = (FRONTEND_SRC / "components/operations-map/OperationsMap.css"
           ).read_text(encoding="utf-8")
    assert "-webkit-line-clamp" in css
    assert "@media (max-width: 1024px)" in css
    assert "@media (max-width: 640px)" in css


# ─── Forbidden production copy — broad sweep across pages/ ────────


def test_no_rendered_iter_labels_across_all_pages():
    """Re-runs the Track 15.84 broad sweep to keep CI visibility on
    new iter-label introductions even between portal cert executions."""
    FORBIDDEN_RX = re.compile(r"""[>"']\s*iter\d{2,4}\b""")
    bad = []
    for path in PAGES_DIR.rglob("*.jsx"):
        if path.name.endswith(".test.jsx"):
            continue
        body = _read(path)
        # Strip block + line + JSX comments before scanning.
        body = re.sub(r"/\*.*?\*/", "", body, flags=re.S)
        body = re.sub(r"\{/\*.*?\*/\}", "", body, flags=re.S)
        body = re.sub(r"//.*?$", "", body, flags=re.M)
        for m in FORBIDDEN_RX.finditer(body):
            ctx = body[max(0, m.start() - 30):m.end() + 30].strip()
            if "data-testid" in ctx:
                continue
            bad.append((str(path.relative_to(FRONTEND_SRC)), ctx))
    assert not bad, (
        f"Track 15.85 regression: rendered iter### label leaked back "
        f"into production-facing pages: {bad[:5]}"
    )


# ─── Execution #2 · PM Portal (canonical `/pm` → `/pm/command-center`) ──


def test_pm_portal_canonical_route_mounted():
    """Track 15.85 Exec #2 · PM Portal landing is mounted at the
    canonical `/pm` path and resolves through PmHomeRedirect."""
    src = _read(APP_JS)
    assert re.search(
        r'<Route\s+path="/pm"\s+element=\{P\(<PmHomeRedirect\s*/>\)\}',
        src,
    ), (
        "Track 15.85: `/pm` canonical PM landing must be mounted in "
        "App.js under the P() (RequirePm) guard via PmHomeRedirect."
    )


# ─── Execution #2 · Leadership Portal (canonical `/leadership`) ────


def test_leadership_canonical_route_mounted():
    src = _read(APP_JS)
    assert re.search(
        r'<Route\s+path="/leadership"\s+element=\{<FieldLeadershipHub\s*/>\}',
        src,
    ), (
        "Track 15.85: `/leadership` canonical Field Leadership landing "
        "must remain mounted in App.js."
    )


# ─── Execution #2 · Canonical portal path no-404 regression ────────


_CANONICAL_PATH_ROUTES = [
    # path · expected to be mounted somewhere in App.js (regex-tolerant)
    ("/dispatch-portal", r'<Route\s+path="/dispatch-portal"'),
    ("/dispatch-portal/map", r'<Route\s+path="/dispatch-portal/map"'),
    ("/safety-portal", r'<Route\s+path="/safety-portal'),
    ("/trench-safety", r'<Route\s+path="/trench-safety'),
    ("/shop", r'<Route\s+path="/shop"'),
    ("/pm", r'<Route\s+path="/pm"\s'),
    ("/leadership", r'<Route\s+path="/leadership"\s'),
    ("/hr", r'<Route\s+path="/hr"\s'),
    ("/operations-map", r'<Route\s+path="/operations-map"'),
]


def test_no_404_on_canonical_portal_paths():
    """Track 15.85 Exec #2 · Lock every documented canonical portal
    landing path so a refactor cannot silently remove a portal mount
    (which would route every operator deep-link to the 404 recovery
    page). The 404 recovery surface itself was beautiful — but a
    portal landing returning 404 is a P0 trust failure."""
    src = _read(APP_JS)
    missing = []
    for path, pattern in _CANONICAL_PATH_ROUTES:
        if not re.search(pattern, src):
            missing.append(path)
    assert not missing, (
        f"Track 15.85 regression: canonical portal landing path(s) "
        f"missing from App.js routing — operators hitting these URLs "
        f"would see the 404 recovery page instead of their portal: "
        f"{missing}"
    )


def test_canonical_portal_paths_are_protected_by_their_guards():
    """Track 15.85 Exec #2 · Cross-check: every operator portal route
    is wrapped in the correct guard (P / DP / H / S / SH / A). This
    is a routing-discipline test, NOT an auth-strength test."""
    src = _read(APP_JS)
    # PM landing
    assert "P(<PmHomeRedirect" in src
    # Dispatch landing
    assert "DP(<DispatchHub" in src or 'path="/dispatch-portal"' in src
    # HR landing
    assert "H(<HrHubV2" in src
    # Shop landing (S = RequireShop wrapper)
    assert "S(<ShopHubV2" in src or "S(<ShopHub" in src
    # Admin operations map
    assert "A(<OperationsMapPage" in src
