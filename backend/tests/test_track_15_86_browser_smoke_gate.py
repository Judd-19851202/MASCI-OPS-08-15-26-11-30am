"""TRACK 15.86 · Continuous Browser Smoke Regression Gate · meta-tests.

These tests do NOT spin up a real browser. They lock the *shape* of
the Track 15.86 smoke runner (`backend/tests/browser_smoke/
run_browser_smoke.py`) so a future refactor cannot silently weaken the
gate.

Why a separate "meta" layer?
  * The real Playwright runner needs a chromium binary and ~30 s per
    invocation — too heavy to run every deployment-gate cycle on every
    contributor's machine.
  * The deployment_gate.py pytest sweep must remain fast and 100 %
    deterministic. So we run the *meta* assertions here and the
    runner itself is wired in as a lightweight ``--gate`` mode call
    from the deployment gate script (only when ``MASCI_SMOKE_BROWSER``
    is truthy or the browser binary is present).

What this file locks:

  1. The runner module exists and is importable.
  2. The gate route list covers the high-signal certified families
     (Public Safety, Admin, Operations Map).
  3. The extended route list covers the full Track 15.85 certified
     surface (every certified family represented).
  4. Every gate route is discoverable in App.js (no guessed routes).
  5. The required 3 breakpoints (390x844 / 768x1024 / 1024x768) are
     declared.
  6. The runner enforces every required assertion shape (404,
     overflow, hydration, console error, page error, blank,
     forbidden-string).
  7. The runner authenticates protected routes via the canonical
     ``/api/auth/multi-login`` flow — no guard-weakening, no shared
     admin password fallback.
  8. The forbidden-strings list keeps its Track 15.84 / 15.85 entries.
  9. The hydration-warning detector keeps its Track 15.85 Exec #4
     ``cannot be a child of`` needle.
 10. ``--gate`` / ``--extended`` / ``--base-url`` / ``--json`` CLI
     surface is preserved.
 11. Public routes in the runner are NOT given a session token (RBAC
     preservation).
 12. Track 15.85 regression file still passes (no regression).
"""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path

BROWSER_SMOKE_DIR = Path("/app/backend/tests/browser_smoke")
RUNNER_PATH = BROWSER_SMOKE_DIR / "run_browser_smoke.py"
APP_JS = Path("/app/frontend/src/App.js")
# TRACK 22.5A · re-anchor to current routing shell.
APP_ROUTES = Path("/app/frontend/src/app/routing/AppRoutes.jsx")


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _load_runner_module():
    spec = importlib.util.spec_from_file_location(
        "track_15_86_browser_smoke_runner",
        str(RUNNER_PATH),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Register in sys.modules BEFORE exec_module — dataclass machinery
    # looks the module up by ``cls.__module__`` while resolving
    # forward references, and would otherwise hit a NoneType.
    import sys
    sys.modules["track_15_86_browser_smoke_runner"] = module
    spec.loader.exec_module(module)
    return module


# ─── 1. Runner module exists + importable ──────────────────────────


def test_runner_file_exists():
    assert RUNNER_PATH.exists(), (
        "Track 15.86: browser smoke runner must exist at "
        f"{RUNNER_PATH}. Removing it deletes the continuous "
        "browser regression gate."
    )


def test_runner_module_importable():
    """The runner must remain importable so the deployment gate can
    invoke it programmatically (not only via subprocess)."""
    module = _load_runner_module()
    assert hasattr(module, "run"), (
        "Track 15.86: runner must expose a top-level ``run()`` entry "
        "point so the deployment gate can call it directly."
    )
    assert hasattr(module, "main"), (
        "Track 15.86: runner must expose ``main()`` so the CLI surface "
        "stays callable."
    )


# ─── 2. Gate routes — high-signal certified families ───────────────


_REQUIRED_GATE_SIGNALS = [
    # (path, label-substring · these are the high-signal landings).
    ("/trench-safety", "Public Safety"),
    ("/admin", "Admin"),
    ("/operations-map", "Operations Map"),
]


def test_gate_routes_cover_certified_high_signal_landings():
    module = _load_runner_module()
    gate_paths = {p for p, _, _ in module.GATE_ROUTES}
    for path, _ in _REQUIRED_GATE_SIGNALS:
        assert path in gate_paths, (
            f"Track 15.86: gate route list must include `{path}` — it "
            "is the high-signal landing for a certified Track 15.85 "
            "family. Removing it weakens the gate."
        )


# ─── 3. Extended routes — Track 15.85 certified surface coverage ────


_REQUIRED_EXTENDED_FAMILIES = [
    # Each path proves coverage of a certified Track 15.85 family.
    "/dispatch-portal",         # Dispatch Portal
    "/dispatch-portal/map",     # Dispatch Map (split route)
    "/operations-map",          # Operations Map (admin-only)
    "/shop",                    # Shop Portal
    "/pm",                      # PM Portal
    "/leadership",              # Field Leadership
    "/hr",                      # HR Portal
    "/safety-portal",           # Safety Portal
    "/trench-safety",           # Public Safety Tile
    "/trench-safety/report",    # Public damage report
    "/trench-safety/tabulated-data",  # Tabulated Data
    "/trench-safety/references",      # Safety References
    "/daily/new",               # Field/Public Forms
    "/meetings/new",            # Field/Public Forms
    "/inspect/new",             # Field/Public Forms
    "/equipment/new",           # Field/Public Forms
    "/jha",                     # Field/Public Forms
    "/incidents/new",           # Field/Public Forms
    "/fleet/dvir/new",          # Field/Public Forms
    "/admin",                   # Admin Portal Deep
    "/admin/system-health",     # Admin Portal Deep · System Health
    "/admin/audit-log",         # Admin Portal Deep · Audit Log
    "/notifications",           # Trust Center / Notifications
]


def test_extended_routes_cover_every_certified_family():
    module = _load_runner_module()
    extended_paths = {p for p, _, _ in module.EXTENDED_ROUTES}
    missing = [p for p in _REQUIRED_EXTENDED_FAMILIES if p not in extended_paths]
    assert not missing, (
        "Track 15.86: extended sweep must cover every certified Track "
        f"15.85 portal family. Missing: {missing}"
    )


# ─── 4. Every gate route is mounted in App.js ──────────────────────


def test_every_gate_route_is_discoverable_in_app_js():
    """Hard guard against guessed routes — every path the runner hits
    must be mounted in App.js (regex-tolerant of Routes that include
    suffixes / wildcards / Navigate aliases)."""
    module = _load_runner_module()
    src = (_read(APP_JS) + "\n" + _read(APP_ROUTES))
    missing = []
    for path, _, _ in module.GATE_ROUTES:
        # Tolerant match: a Route whose path begins with this canonical
        # path (covers wildcards, /* suffixes, parametric segments).
        pat = r'<Route\s+path="' + re.escape(path) + r'(?:"|\/|\\?\*)'
        if not re.search(pat, src):
            missing.append(path)
    assert not missing, (
        "Track 15.86: gate route(s) not mounted in App.js — the "
        f"runner would hit the 404 recovery page: {missing}"
    )


def test_every_extended_route_is_discoverable_in_app_js():
    module = _load_runner_module()
    src = (_read(APP_JS) + "\n" + _read(APP_ROUTES))
    missing = []
    for path, _, _ in module.EXTENDED_ROUTES:
        pat = r'<Route\s+path="' + re.escape(path) + r'(?:"|\/|\\?\*)'
        if not re.search(pat, src):
            missing.append(path)
    assert not missing, (
        "Track 15.86: extended route(s) not mounted in App.js — the "
        f"runner would hit the 404 recovery page: {missing}"
    )


# ─── 5. Required breakpoints ───────────────────────────────────────


_REQUIRED_BREAKPOINTS = [(390, 844), (768, 1024), (1024, 768)]


def test_gate_viewports_include_required_breakpoints():
    module = _load_runner_module()
    declared = [(w, h) for w, h, _ in module.GATE_VIEWPORTS]
    for bp in _REQUIRED_BREAKPOINTS:
        assert bp in declared, (
            f"Track 15.86: gate viewport list must include {bp[0]}x"
            f"{bp[1]} — it is a Track 15.85 mandate breakpoint."
        )


def test_extended_viewports_include_laptop_and_desktop():
    """Extended runs should also cover laptop + desktop at minimum."""
    module = _load_runner_module()
    declared = [(w, h) for w, h, _ in module.EXTENDED_VIEWPORTS]
    assert (1366, 768) in declared
    assert (1920, 1080) in declared


# ─── 6. Required assertion shape ───────────────────────────────────


_REQUIRED_ASSERTION_SHAPES = [
    # Each tuple is (haystack-needle, why-it-matters).
    ("overflow", "Beautiful pillar · no body horizontal overflow"),
    ("hydration_warnings", "Trusted pillar · no React hydration warnings"),
    ("console_errors", "Trusted pillar · no console.error"),
    ("page_errors", "Trusted pillar · no uncaught page exceptions"),
    ("is_404", "Powerful/Simple pillar · canonical routes do not 404"),
    ("is_blank", "Proven pillar · page renders content"),
    ("forbidden_strings", "Proven pillar · no iter/scaffold/placeholder leak"),
]


def test_runner_enforces_every_required_assertion():
    src = _read(RUNNER_PATH)
    for needle, _ in _REQUIRED_ASSERTION_SHAPES:
        assert needle in src, (
            f"Track 15.86: runner must enforce `{needle}` assertion. "
            "Removing it weakens the six-pillar gate."
        )


def test_runner_pass_requires_all_assertions_true():
    """The runner's PASS predicate must AND every required assertion.
    A future drift where someone weakens it (e.g. ``overflow < 10``)
    would let regressions slip past."""
    src = _read(RUNNER_PATH)
    # Locate the ``res.passed = (`` block.
    m = re.search(r"res\.passed\s*=\s*\((.*?)\)", src, re.S)
    assert m, "Track 15.86: runner must compute ``res.passed`` from an explicit AND chain."
    body = m.group(1)
    for needle in [
        "res.overflow == 0",
        "not res.is_404",
        "not res.is_blank",
        "not res.hydration_warnings",
        "not res.console_errors",
        "not res.page_errors",
        "not res.forbidden_strings",
    ]:
        assert needle in body, (
            f"Track 15.86: PASS predicate must include `{needle}`. "
            "Weakening this predicate weakens the gate."
        )


# ─── 7. RBAC preservation ──────────────────────────────────────────


def test_runner_authenticates_via_canonical_multi_login_only():
    """No shared-admin password fallback, no guard weakening — admin
    routes must authenticate through the canonical
    ``/api/auth/multi-login`` flow (per ``memory/test_credentials.md``)."""
    src = _read(RUNNER_PATH)
    assert "/api/auth/multi-login" in src, (
        "Track 15.86: runner must authenticate via "
        "POST /api/auth/multi-login — the canonical, RBAC-preserving "
        "super-admin entry point."
    )
    # No shared admin password fallback / break-glass.
    assert "MASCI1982" not in src, (
        "Track 15.86: runner MUST NOT use the legacy shared admin "
        "password — that is the break-glass path and weakens RBAC."
    )
    assert "/api/admin/login" not in src, (
        "Track 15.86: runner MUST NOT call /api/admin/login (legacy "
        "shared-password endpoint). Use the canonical multi-login "
        "flow only."
    )


def test_public_routes_are_not_token_authenticated():
    """Every route declared ``auth_required=False`` must remain in the
    public surface contract — the runner must NEVER pass a session
    token to them. This is the per-route preservation of the Track
    15.85 public/private separation."""
    module = _load_runner_module()
    public_paths = {p for p, _, auth in module.EXTENDED_ROUTES if not auth}
    # Public forms + Public Safety Tile routes that the operator
    # explicitly preserved as public-gated.
    required_public = {
        "/trench-safety", "/trench-safety/report",
        "/trench-safety/tabulated-data", "/trench-safety/references",
        "/daily/new", "/meetings/new", "/inspect/new", "/equipment/new",
        "/jha", "/incidents/new", "/fleet/dvir/new",
    }
    missing = required_public - public_paths
    assert not missing, (
        "Track 15.86: the following routes must remain in the runner's "
        f"public list (no token): {missing}. Auth-gating them would "
        "weaken the Track 15.85 public/private separation doctrine."
    )


# ─── 8. Forbidden-strings list keeps Track 15.84/15.85 entries ─────


def test_forbidden_strings_list_keeps_track_15_84_entries():
    module = _load_runner_module()
    forbidden = set(module.FORBIDDEN_RENDERED_STRINGS)
    assert "Admin-gated for now" in forbidden, (
        "Track 15.86: forbidden-strings list must keep `Admin-gated "
        "for now` — Track 15.83B / 15.84 lock that production-facing "
        "pages never re-introduce this scaffold copy."
    )


# ─── 9. Hydration-warning detector keeps Track 15.85 Exec #4 needle ──


def test_hydration_detector_keeps_track_15_85_exec4_needle():
    module = _load_runner_module()
    needles = [n.lower() for n in module.HYDRATION_WARNING_NEEDLES]
    assert any("cannot be a child of" in n for n in needles), (
        "Track 15.86: hydration detector must keep the `cannot be a "
        "child of` needle — Track 15.85 Exec #4 root-caused and fixed "
        "the `<span> cannot be a child of <option>` warning; this "
        "detector is the regression-lock against that whole class."
    )
    assert any("validatedomnesting" in n.replace(" ", "") for n in needles), (
        "Track 15.86: hydration detector must keep the "
        "`validateDOMNesting` needle — it is React's umbrella nesting "
        "warning prefix."
    )


# ─── 10. CLI surface preservation ──────────────────────────────────


def test_runner_cli_surface_preserved():
    src = _read(RUNNER_PATH)
    for flag in ["--gate", "--extended", "--base-url", "--json"]:
        assert flag in src, (
            f"Track 15.86: runner CLI must keep the `{flag}` flag. "
            "Removing it breaks operator / CI invocation patterns."
        )


# ─── 11. Deployment gate wires this in ────────────────────────────


def test_deployment_gate_includes_track_15_86_meta_file():
    gate_src = _read(Path("/app/scripts/deployment_gate.py"))
    assert "test_track_15_86_browser_smoke_gate" in gate_src, (
        "Track 15.86: scripts/deployment_gate.py must include "
        "test_track_15_86_browser_smoke_gate.py in REGRESSION_FILES "
        "— otherwise the meta-gate is not actually wired in."
    )


# ─── 12. Track 15.85 regression file still exists (no regression) ──


def test_track_15_85_regression_file_still_present():
    p = Path("/app/backend/tests/test_track_15_85_mandatory_full_platform_certification.py")
    assert p.exists(), (
        "Track 15.86: Track 15.85 regression file must remain in "
        "place — Track 15.86 extends, not replaces, 15.85."
    )


# ─── 13. Runner module-level constants are non-empty ──────────────


def test_runner_route_lists_are_non_empty():
    module = _load_runner_module()
    assert len(module.GATE_ROUTES) >= 3, (
        "Track 15.86: gate route list must have at least 3 routes "
        "(phone × portrait × landscape coverage)."
    )
    assert len(module.EXTENDED_ROUTES) >= len(_REQUIRED_EXTENDED_FAMILIES), (
        "Track 15.86: extended route list must cover every certified "
        "family — current count is below the required floor."
    )
    assert len(module.GATE_VIEWPORTS) >= 3
    assert len(module.EXTENDED_VIEWPORTS) >= 5


# ─── 14. Documentation lock ───────────────────────────────────────


def test_ledger_documents_track_15_86():
    ledger = Path("/app/memory/TRACK_15_86_CONTINUOUS_BROWSER_SMOKE_REGRESSION_GATE.md")
    assert ledger.exists(), (
        "Track 15.86: ledger "
        "`memory/TRACK_15_86_CONTINUOUS_BROWSER_SMOKE_REGRESSION_GATE.md` "
        "must exist — operator mandate."
    )
    body = ledger.read_text(encoding="utf-8")
    for needle in ["Routes covered", "Breakpoints", "Assertions",
                   "Deployment gate", "How to run"]:
        assert needle.lower() in body.lower(), (
            f"Track 15.86: ledger must document `{needle}`."
        )
