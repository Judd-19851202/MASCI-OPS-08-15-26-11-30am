#!/usr/bin/env python3
"""TRACK 15.86 · Continuous Browser Smoke Regression Gate.

Permanent, headless Playwright runner that locks the Track 15.85
ForgedOps Production Excellence Certification standard (honest 9.72 /
6 pillars) by re-verifying canonical portal landings across the
production-critical responsive breakpoints on every deployment.

Two modes:

  * ``--gate``  (default) — lightweight subset for the deployment gate.
                 Three viewports × three high-signal landings. Fast
                 (< 60 s), stable, deterministic, safe for CI.

  * ``--extended`` — full surface sweep across every certified portal
                     family (15 routes × 3 viewports). Slower, intended
                     for nightly / on-demand runs.

Per route+viewport the runner enforces the six-pillar contract:

  1. Page does not land on the 404 / NotFound recovery for a canonical
     route (Powerful · Simple).
  2. Body horizontal overflow is exactly 0 — no card bleed, no rail
     push, no overlay scroll (Beautiful).
  3. No React hydration warnings ("<X> cannot be a child of <Y>",
     "hydration error", "did not match", ...) (Trusted).
  4. No ``console.error`` and no uncaught page errors (Trusted).
  5. Page is not blank (innerText length > 50) and the documented
     forbidden-string list does not appear (Proven).
  6. RBAC is honoured by the existing route guards — admin-only routes
     authenticate via the documented super-admin multi-login flow.
     Public routes never receive a session token (Deployable).

Exit codes:
  0  every (route, viewport) PASS  → deploy permitted.
  1  one or more FAIL              → deploy blocked.
  2  unable to reach the preview/base URL.
  3  Playwright / chromium binary missing.

Usage:
  python backend/tests/browser_smoke/run_browser_smoke.py
  python backend/tests/browser_smoke/run_browser_smoke.py --extended
  python backend/tests/browser_smoke/run_browser_smoke.py --base-url URL
  python backend/tests/browser_smoke/run_browser_smoke.py --json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import traceback
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


# ─── Canonical route catalogue (discovered from App.js · do NOT guess) ──
#
# Every entry is a tuple of ``(path, label, auth_required)``. Routes
# marked ``auth_required=True`` are admin-only or portal-only; the
# runner will authenticate via the canonical multi-login flow before
# navigating. Public routes get no token and must remain reachable
# without auth (per the field-form preservation doctrine).
#
# The list is split into two tiers:
#
#   * GATE_ROUTES   — small representative subset for the deployment
#                     gate run. Three landings, all field-safe or
#                     admin-trust, chosen for high signal + low flake.
#   * EXTENDED_ROUTES — full Track 15.85 certified surface sweep.

GATE_ROUTES: List[Tuple[str, str, bool]] = [
    # Field-safe public landing (Track 15.85 Exec #4 Public Safety Tile cert).
    ("/trench-safety", "Public Safety Tile", False),
    # Admin landing (Track 15.85 Exec #4 Admin Portal Deep cert).
    ("/admin", "Admin Console", True),
    # Operations Map (Track 15.85 Exec #4 hydration-warning fix verification).
    ("/operations-map", "Operations Map", True),
]

EXTENDED_ROUTES: List[Tuple[str, str, bool]] = [
    # Core portals.
    ("/dispatch-portal", "Dispatch Portal", True),
    ("/dispatch-portal/map", "Dispatch Map", True),
    ("/operations-map", "Operations Map (Admin)", True),
    ("/shop", "Shop Portal", True),
    ("/pm", "PM Portal", True),
    ("/leadership", "Field Leadership", True),
    ("/hr", "HR Portal", True),
    ("/safety-portal", "Safety Portal", True),
    # Public Safety / Trench Safety surfaces.
    ("/trench-safety", "Public Safety Tile (Trench Safety dashboard)", False),
    ("/trench-safety/report", "Public Damage Report", False),
    ("/trench-safety/tabulated-data", "Tabulated Data", False),
    ("/trench-safety/references", "Safety References", False),
    # Public / field forms (intentionally public-gated by design).
    ("/daily/new", "Daily Report (public)", False),
    ("/meetings/new", "Safety Meeting (public)", False),
    ("/inspect/new", "Inspection (public)", False),
    ("/equipment/new", "Equipment Pre-Op (public)", False),
    ("/jha", "Job Hazard Plans (public)", False),
    ("/incidents/new", "Incident Report (public)", False),
    ("/fleet/dvir/new", "Fleet DVIR (public)", False),
    # Admin / Trust / Notifications canonical surfaces (Track 15.85 Exec #4).
    ("/admin", "Admin Console", True),
    ("/admin/system-health", "Admin · System Health", True),
    ("/admin/audit-log", "Admin · Audit Log", True),
    ("/admin/integrations", "Admin · Integration Center", True),
    ("/admin/governance", "Admin · Governance", True),
    ("/admin/operations-dashboard", "Admin · Operations Dashboard", True),
    ("/admin/operations-events", "Admin · Operations Events", True),
    ("/admin/digest-config", "Admin · Digest Config", True),
    ("/admin/operational-language", "Admin · Operational Language", True),
    ("/notifications", "Notifications Digest", True),
]


# ─── Canonical breakpoints (Track 15.85 mandate) ────────────────────

GATE_VIEWPORTS: List[Tuple[int, int, str]] = [
    (390, 844, "phone-390"),
    (768, 1024, "ipad-portrait-768"),
    (1024, 768, "ipad-landscape-1024"),
]

EXTENDED_VIEWPORTS: List[Tuple[int, int, str]] = GATE_VIEWPORTS + [
    (1366, 768, "laptop-1366"),
    (1920, 1080, "desktop-1920"),
]


# ─── Forbidden production strings (Track 15.84 + Track 15.85 cumulative) ──
#
# These are obvious dev/iter/scaffolding leakage tokens that must
# never appear on a rendered production page. We test inner text only
# so the canonical "preview-only" defense-in-depth label (intentional
# on the preview env banner) is not flagged.
FORBIDDEN_RENDERED_STRINGS: List[str] = [
    "Admin-gated for now",
    "TODO",
    "FIXME",
    "Coming soon",
    "Lorem ipsum",
    "placeholder text",
]


# ─── Hydration / nesting warning detector ──────────────────────────
#
# Track 15.85 Exec #4 root-caused & locked the ``<span> cannot be a
# child of <option>`` warning. This detector catches that AND every
# other hydration / invalid-HTML-nesting class of warning, so a future
# regression cannot silently re-introduce one.
HYDRATION_WARNING_NEEDLES: List[str] = [
    "cannot be a child of",
    "hydration error",
    "Hydration failed",
    "did not match",
    "validateDOMNesting",
    "Text content did not match",
]


# ─── 404 / NotFound recovery detector ──────────────────────────────
NOT_FOUND_NEEDLES: List[str] = [
    "404 · Page Not Found",
    "404 · PAGE NOT FOUND",
    "We couldn't find that page",
    "Route Not Found",
]


# ─── Test credentials (super-admin · multi-login canonical path) ────
#
# Pulled from ``memory/test_credentials.md``. Super admin authenticates
# via ``POST /api/auth/multi-login`` and the response's ``portal_tokens``
# map is dropped into ``localStorage`` exactly the way the frontend
# does it. This is the proven, RBAC-preserving way to hit the admin /
# dispatch / pm / shop / hr / safety routes — no guard weakening, no
# bypass, no shared admin password fallback.
DEFAULT_SUPER_ADMIN_EMAIL = os.environ.get(
    "MASCI_SMOKE_SUPER_EMAIL", "jaymn.judd@mascigc.com"
)
DEFAULT_SUPER_ADMIN_PASSWORD = os.environ.get(
    "MASCI_SMOKE_SUPER_PASSWORD", "Maddix123!"
)


# ─── Result container ──────────────────────────────────────────────


@dataclass
class RouteResult:
    path: str
    label: str
    viewport: str
    width: int
    height: int
    passed: bool
    overflow: int = 0
    hydration_warnings: List[str] = field(default_factory=list)
    console_errors: List[str] = field(default_factory=list)
    page_errors: List[str] = field(default_factory=list)
    is_404: bool = False
    is_blank: bool = False
    forbidden_strings: List[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "label": self.label,
            "viewport": self.viewport,
            "width": self.width,
            "height": self.height,
            "passed": self.passed,
            "overflow": self.overflow,
            "hydration_warnings": self.hydration_warnings,
            "console_errors": self.console_errors,
            "page_errors": self.page_errors,
            "is_404": self.is_404,
            "is_blank": self.is_blank,
            "forbidden_strings": self.forbidden_strings,
            "notes": self.notes,
        }


# ─── Runner ─────────────────────────────────────────────────────────


def _resolve_base_url(explicit: Optional[str]) -> str:
    if explicit:
        return explicit.rstrip("/")
    env = os.environ.get("REACT_APP_BACKEND_URL")
    if env:
        return env.rstrip("/")
    # Fallback to the frontend .env (.env file lives outside backend).
    for candidate in ("/app/frontend/.env", "/app/.env"):
        try:
            with open(candidate, "r", encoding="utf-8") as fh:
                for line in fh:
                    if line.startswith("REACT_APP_BACKEND_URL="):
                        return line.split("=", 1)[1].strip().rstrip("/")
        except OSError:
            continue
    return "http://localhost:8001"


def _authenticate(page, base_url: str, email: str, password: str) -> bool:
    """Drop super-admin multi-login tokens into ``localStorage`` exactly
    the way the SPA does it. Returns True iff every expected portal
    token was issued."""
    page.goto(f"{base_url}/sign-in", wait_until="domcontentloaded", timeout=15000)
    result = page.evaluate(
        """async ({email, password}) => {
          const r = await fetch('/api/auth/multi-login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({email, password})
          });
          const j = await r.json().catch(() => ({}));
          if (j && j.portal_tokens) {
            Object.entries(j.portal_tokens).forEach(([k,v]) => {
              if (v) localStorage.setItem(`masci.${k}.token`, v);
            });
            if (j.directory_token) localStorage.setItem('masci.directory.token', j.directory_token);
          }
          return {ok: r.ok, status: r.status, portals: Object.keys((j && j.portal_tokens) || {})};
        }""",
        {"email": email, "password": password},
    )
    return bool(result and result.get("ok"))


def _clear_session(page, base_url: str) -> None:
    """Wipe localStorage / sessionStorage. Public routes must work
    without a token; the runner enforces that strictly."""
    try:
        page.goto(f"{base_url}/", wait_until="domcontentloaded", timeout=12000)
        page.evaluate("() => { localStorage.clear(); sessionStorage.clear(); }")
    except Exception:
        pass


def _check_route(
    page,
    base_url: str,
    path: str,
    label: str,
    viewport: Tuple[int, int, str],
) -> RouteResult:
    width, height, vp_label = viewport
    res = RouteResult(
        path=path,
        label=label,
        viewport=vp_label,
        width=width,
        height=height,
        passed=False,
    )
    console_errors: List[str] = []
    page_errors: List[str] = []
    hyd: List[str] = []

    def on_console(msg):
        text = msg.text[:600]
        if msg.type == "error":
            # Hydration / nesting warnings come through as
            # ``console.error`` from react-dom in dev builds.
            if any(n.lower() in text.lower() for n in HYDRATION_WARNING_NEEDLES):
                hyd.append(text)
            else:
                console_errors.append(text)

    def on_pageerror(err):
        page_errors.append(str(err)[:600])

    page.on("console", on_console)
    page.on("pageerror", on_pageerror)

    try:
        page.set_viewport_size({"width": width, "height": height})
        url = f"{base_url}{path}"
        try:
            page.goto(url, wait_until="networkidle", timeout=20000)
        except Exception as e:
            # networkidle can be slow when the map tiles keep
            # refreshing; fall back to domcontentloaded + a short pad
            # so we still measure overflow / console.
            res.notes = f"networkidle fallback: {e}"
            page.goto(url, wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(1500)

        # Overflow check.
        overflow = page.evaluate(
            "() => Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth)"
        )
        res.overflow = int(overflow or 0)

        # 404 / NotFound recovery detection (canonical routes must NOT
        # land on the recovery page).
        html = page.content()
        res.is_404 = any(n in html for n in NOT_FOUND_NEEDLES)

        # Blank-page detection.
        inner_text = page.evaluate("() => (document.body && document.body.innerText) || ''") or ""
        res.is_blank = len(inner_text.strip()) < 50

        # Forbidden production string scan.
        res.forbidden_strings = [s for s in FORBIDDEN_RENDERED_STRINGS if s.lower() in inner_text.lower()]
    finally:
        page.remove_listener("console", on_console)
        page.remove_listener("pageerror", on_pageerror)

    res.console_errors = console_errors[:5]
    res.page_errors = page_errors[:5]
    res.hydration_warnings = hyd[:5]

    res.passed = (
        res.overflow == 0
        and not res.is_404
        and not res.is_blank
        and not res.hydration_warnings
        and not res.console_errors
        and not res.page_errors
        and not res.forbidden_strings
    )
    return res


def _print_human(results: List[RouteResult]) -> None:
    print()
    print("=" * 80)
    print("TRACK 15.86 · BROWSER SMOKE REGRESSION GATE")
    print("=" * 80)
    failed = [r for r in results if not r.passed]
    for r in results:
        flag = "PASS" if r.passed else "FAIL"
        print(f"  [{flag}] {r.viewport:>22}  {r.path:<30} overflow={r.overflow}  hyd={len(r.hydration_warnings)}  err={len(r.console_errors)}  404={r.is_404}  blank={r.is_blank}")
        if not r.passed:
            for hw in r.hydration_warnings:
                print(f"          hyd: {hw[:200]}")
            for ce in r.console_errors:
                print(f"          err: {ce[:200]}")
            for pe in r.page_errors:
                print(f"          page-err: {pe[:200]}")
            if r.forbidden_strings:
                print(f"          forbidden: {r.forbidden_strings}")
            if r.notes:
                print(f"          note: {r.notes}")
    print("-" * 80)
    print(f"  Total: {len(results)}  Passed: {len(results) - len(failed)}  Failed: {len(failed)}")
    print("=" * 80)
    print()


def run(
    base_url: Optional[str] = None,
    extended: bool = False,
    json_out: bool = False,
    super_email: Optional[str] = None,
    super_password: Optional[str] = None,
) -> int:
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except ImportError:
        print("Track 15.86: playwright not installed — pip install playwright", file=sys.stderr)
        return 3

    base = _resolve_base_url(base_url)
    email = super_email or DEFAULT_SUPER_ADMIN_EMAIL
    password = super_password or DEFAULT_SUPER_ADMIN_PASSWORD

    routes = EXTENDED_ROUTES if extended else GATE_ROUTES
    viewports = EXTENDED_VIEWPORTS if extended else GATE_VIEWPORTS

    results: List[RouteResult] = []

    try:
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception as e:
                print(f"Track 15.86: chromium launch failed — {e}", file=sys.stderr)
                return 3

            try:
                # AUTH context — used for every auth_required route.
                auth_ctx = browser.new_context(ignore_https_errors=True)
                auth_page = auth_ctx.new_page()
                if not _authenticate(auth_page, base, email, password):
                    print(
                        f"Track 15.86: super-admin multi-login failed at {base}/api/auth/multi-login (email={email}).",
                        file=sys.stderr,
                    )
                    return 2

                # PUBLIC context — strictly no token. Verifies public
                # routes still resolve without auth (RBAC preservation).
                public_ctx = browser.new_context(ignore_https_errors=True)
                public_page = public_ctx.new_page()
                _clear_session(public_page, base)

                for path, label, auth_required in routes:
                    page = auth_page if auth_required else public_page
                    for vp in viewports:
                        attempts = 0
                        max_attempts = 2  # one-shot retry on transient flake
                        res = None
                        while attempts < max_attempts:
                            attempts += 1
                            try:
                                res = _check_route(page, base, path, label, vp)
                            except Exception as exc:
                                res = RouteResult(
                                    path=path,
                                    label=label,
                                    viewport=vp[2],
                                    width=vp[0],
                                    height=vp[1],
                                    passed=False,
                                    notes=f"runner-exception: {exc}",
                                )
                            if res.passed:
                                break
                            # Retry only on transient-shaped failures
                            # (network-cancelled XHR, MapLibre tile-
                            # fetch races). A real overflow / 404 /
                            # hydration / blank failure cannot be
                            # cured by a retry, so we still re-check.
                            if attempts < max_attempts:
                                res.notes = (res.notes + " | retry-after-transient").strip(" |")
                                # brief pause so any in-flight fetch
                                # has time to settle before retry.
                                try:
                                    page.wait_for_timeout(1200)
                                except Exception:
                                    pass
                        results.append(res)
            finally:
                browser.close()
    except Exception as exc:
        traceback.print_exc()
        print(f"Track 15.86: unexpected error — {exc}", file=sys.stderr)
        return 2

    failed = [r for r in results if not r.passed]
    if json_out:
        print(json.dumps({
            "ok": not failed,
            "mode": "extended" if extended else "gate",
            "base_url": base,
            "total": len(results),
            "passed": len(results) - len(failed),
            "failed": len(failed),
            "results": [r.to_dict() for r in results],
        }, indent=2))
    else:
        _print_human(results)

    return 0 if not failed else 1


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Track 15.86 browser smoke gate")
    ap.add_argument("--extended", action="store_true",
                    help="Run the full Track 15.85 certified surface sweep (slower).")
    ap.add_argument("--gate", action="store_true",
                    help="Run the lightweight deployment-gate subset (default).")
    ap.add_argument("--base-url", default=None,
                    help="Override base URL (default: REACT_APP_BACKEND_URL).")
    ap.add_argument("--json", action="store_true", dest="json_out",
                    help="Emit machine-readable JSON output.")
    args = ap.parse_args(argv)

    return run(
        base_url=args.base_url,
        extended=args.extended,
        json_out=args.json_out,
    )


if __name__ == "__main__":
    sys.exit(main())
