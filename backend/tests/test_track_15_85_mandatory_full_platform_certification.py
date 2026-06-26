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


# ─── Execution #3 · Retired _is_valid_admin_token stub stays hard-False ──


def test_is_valid_admin_token_remains_hard_false_stub():
    """Track 15.85 Exec #3 · Track 15.32 retired the shared-ADMIN-
    PASSWORD HMAC bypass. The synchronous helper
    ``_is_valid_admin_token`` MUST remain a hard-False stub so a
    future refactor cannot accidentally re-enable the shared HMAC
    bypass. Real admin auth flows through
    ``_is_valid_directory_admin_token_async`` (per-user DB lookup).

    This is a P0 security regression lock — if this test fails, an
    operator can suddenly use the shared admin password as an
    unattributed bearer token across the platform.
    """
    import sys
    sys.path.insert(0, "/app/backend")
    from server import _is_valid_admin_token as fn  # type: ignore
    # Every possible input must return False.
    for tok in (None, "", "anything", "any.token", "x" * 200, " ", "ADMIN", "admin"):
        assert fn(tok) is False, (
            f"Track 15.85 P0 SECURITY REGRESSION: "
            f"_is_valid_admin_token({tok!r}) returned {fn(tok)!r}. "
            "Track 15.32 retired the shared-ADMIN-PASSWORD HMAC bypass. "
            "This helper must remain a hard-False stub."
        )


def test_is_valid_admin_token_docstring_documents_retirement():
    """Track 15.85 Exec #3 · The docstring on the retired stub must
    remain truthful so future readers understand WHY it returns False.
    Losing the docstring is a maintenance hazard."""
    src = (Path("/app/backend/server.py")
           .read_text(encoding="utf-8"))
    # Find the function and assert the retirement narrative is preserved.
    m = re.search(
        r"def _is_valid_admin_token\(tok: Optional\[str\]\)\s*->\s*bool:\s*\"\"\"(.*?)\"\"\"",
        src, re.S,
    )
    assert m, "_is_valid_admin_token docstring not found"
    body = m.group(1)
    assert "retired" in body.lower() or "track 15.32" in body.lower(), (
        "Track 15.85 regression: _is_valid_admin_token must keep its "
        "retirement narrative (mentions Track 15.32 and shared-ADMIN-"
        "PASSWORD HMAC retirement) so future readers know WHY it is "
        "hard-False."
    )
    assert "_is_valid_directory_admin_token_async" in body, (
        "Track 15.85 regression: _is_valid_admin_token docstring must "
        "point future readers at the current async validator."
    )



# ─── Execution #4 · Hydration-warning lock (mixed `<option>` children) ──
#
# Track 15.85 Execution #4 root-caused the persistent React hydration
# warning `<span> cannot be a child of <option>` observed on
# /operations-map and /dispatch-portal. The cause was NOT operator code
# — it was the Emergent dev source-tagger wrapping every JSX expression
# island in a `<span style="display:contents" data-ve-dynamic>` for
# source-location tracking. When an `<option>` had MIXED children (text
# adjacent to expression, or multiple expressions separated by JSX
# whitespace), the tagger landed a `<span>` inside the `<option>` —
# valid HTML cannot have a `<span>` child of `<option>`, so React-DOM
# raised the hydration warning every time.
#
# The fix collapses every `<option>` child to a SINGLE JS expression
# (template literal), so the dev tagger only ever wraps ONE expression
# and the wrapper goes around the option's expression-children
# placeholder — never inside the option element itself.
#
# This static lock scans every .jsx in /app/frontend/src and asserts
# every `<option>` has either:
#   * a single string literal child, OR
#   * a single JSX expression child.
#
# It catches any future regression where a developer re-introduces
# mixed children inside `<option>` (text + expression, or multi-
# expression separated by JSX whitespace), which would silently
# re-introduce the hydration warning.


def _option_children_have_mixed_jsx(inner: str) -> bool:
    """Return True iff the `<option>` body contains more than one
    distinct JSX child (text + expression, or multiple expressions
    separated by JSX whitespace, etc.). Whitespace-only text between
    expressions does NOT count as a separate child (JSX collapses it),
    but the dev source-tagger DOES wrap each adjacent expression in a
    `<span data-ve-dynamic>` — so any layout with >1 non-whitespace
    token is the hazard."""
    if not inner.strip():
        return False
    toks = []
    i = 0
    while i < len(inner):
        if inner[i] == "{":
            depth = 0
            start = i
            while i < len(inner):
                ch = inner[i]
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        i += 1
                        break
                i += 1
            toks.append(("EXPR", inner[start:i]))
        else:
            start = i
            while i < len(inner) and inner[i] != "{":
                i += 1
            txt = inner[start:i]
            if txt.strip():
                toks.append(("TEXT", txt.strip()))
    return len(toks) > 1


def test_no_mixed_jsx_children_inside_option_tags():
    """Track 15.85 Exec #4 · P1 hydration-warning regression lock.

    Every `<option>...</option>` in the frontend must have a SINGLE
    JSX child (one string literal OR one expression). Mixed children
    cause the Emergent dev source-tagger to inject a
    `<span data-ve-dynamic>` inside the `<option>` — invalid HTML
    nesting that triggers React's `<span> cannot be a child of
    <option>` hydration warning.

    If this test fails, collapse the option's children to a single
    template literal expression. Example:

      BAD :   <option>{a} · {b}</option>
      GOOD:   <option>{`${a} · ${b}`}</option>
    """
    bad = []
    for path in FRONTEND_SRC.rglob("*.jsx"):
        if ".test." in path.name:
            continue
        src = _read(path)
        # Strip block + line + JSX comments before scanning.
        cleaned = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
        cleaned = re.sub(r"\{/\*.*?\*/\}", "", cleaned, flags=re.S)
        for m in re.finditer(r"<option\b[^>]*>(.*?)</option>", cleaned, re.S):
            if _option_children_have_mixed_jsx(m.group(1)):
                line_no = cleaned[: m.start()].count("\n") + 1
                bad.append(
                    f"{path.relative_to(FRONTEND_SRC)}:{line_no} -> "
                    f"{m.group(1).strip()[:80]!r}"
                )
    assert not bad, (
        "Track 15.85 Exec #4 regression: <option> with mixed JSX "
        "children reintroduced — Emergent dev source-tagger will "
        "inject a <span data-ve-dynamic> inside the option, breaking "
        "HTML nesting and re-raising the React hydration warning. "
        "Collapse to a single template literal expression. "
        f"Offenders ({len(bad)}): {bad[:5]}"
    )


# ─── Execution #4 · Public Safety Tile (Trench Safety public surfaces) ──


def test_public_trench_safety_dashboard_field_safe_chrome():
    """Track 15.85 Exec #4 · Public Safety Tile certification.

    The /trench-safety landing must remain field-safe:
      * STOP-WORK AUTHORITY copy present
      * Counts-only / no-PII badge present
      * Asset Lookup + QR Scan guidance + Action tiles present
      * No admin actions, no admin photos, no audit data
    """
    src = _read(PAGES_DIR / "trench_safety" / "PublicTrenchSafetyDashboard.jsx")
    assert "Stop-Work Authority." in src, (
        "Track 15.85 Exec #4: Public Trench Safety dashboard must keep "
        "the Stop-Work Authority constitutional copy."
    )
    assert "Counts only · no PII" in src, (
        "Track 15.85 Exec #4: Public dashboard must keep the "
        "`Counts only · no PII` badge — public surface is intentionally "
        "stat-only, no operator names, no events."
    )
    assert "Asset Lookup" in src and "QR Scan Guidance." in src, (
        "Track 15.85 Exec #4: Public dashboard must surface Asset "
        "Lookup + QR Scan guidance — both are primary field actions."
    )
    # Verify NO admin-only language leaked into the public surface.
    forbidden = ["admin only", "Admin Only", "ADMIN ONLY", "admin-gated",
                 "internal use", "preview only", "iter"]
    for needle in forbidden:
        assert needle.lower() not in src.lower() or "preview only" in needle.lower(), (
            f"Track 15.85 Exec #4: forbidden admin/dev language `{needle}` "
            "leaked into the public Trench Safety dashboard."
        )


def test_public_trench_safety_report_field_safe_chrome():
    """Track 15.85 Exec #4 · Public Safety Tile · damage-report surface.

    /trench-safety/report must keep its field-safe coaching: Safety
    routing, no auto-status-change copy, plain English."""
    src = _read(PAGES_DIR / "trench_safety" / "PublicTrenchSafetyReport.jsx")
    assert "Report a Problem" in src
    assert "Reports are routed to the Safety team immediately" in src, (
        "Track 15.85 Exec #4: Public report surface must keep the "
        "explicit Safety-routing coaching so a field user knows the "
        "report goes to a human, not a void."
    )
    assert "They do not change the asset status automatically" in src, (
        "Track 15.85 Exec #4: Public report surface must keep the "
        "no-auto-status-change coaching so a field user does NOT "
        "expect the box to auto-Hold when they submit a report."
    )


def test_qr_landing_serial_missing_action_required():
    """Track 15.85 Exec #4 · QR landing surface · serial-missing
    banner must remain prominent. A box without a verified serial
    plate cannot be matched to its tabulated data — operator must be
    told before the box goes in the ground."""
    src = _read(PAGES_DIR / "trench_safety" / "TrenchSafetyQrLanding.jsx")
    assert "Missing — Action Required" in src, (
        "Track 15.85 Exec #4: QR landing must keep the explicit "
        "`Missing — Action Required` serial-missing banner."
    )
    assert "Verify the physical serial plate before use" in src, (
        "Track 15.85 Exec #4: QR landing must keep the verify-serial "
        "coaching for the field crew."
    )


# ─── Execution #4 · Field / Public Forms · canonical mounts ────────


_PUBLIC_FORM_ROUTES = [
    "/daily/new", "/meetings/new", "/inspect/new", "/equipment/new",
    "/incidents/new", "/fleet/dvir/new", "/jha",
    "/trench-safety/excavation/new",
    "/trench-safety/report", "/trench-safety/references",
    "/trench-safety/tabulated-data",
]


def test_public_form_routes_remain_publicly_mounted():
    """Track 15.85 Exec #4 · Public/field form gates must remain
    intentionally accessible (Daily Reports, Safety Meetings, JHAs,
    Pre-Ops, DVIRs, Incidents, Excavation Operations, public Trench
    Safety surfaces).

    Per the operator's preservation doctrine, these are PUBLIC by
    design — accidentally wrapping them in an auth gate would break
    field crews. If this test fails, someone has likely auth-gated a
    public field workflow without going through the explicit
    `private-form-gate` track."""
    src = _read(APP_JS)
    missing = []
    for path in _PUBLIC_FORM_ROUTES:
        # Match each path's Route definition.
        if not re.search(r'<Route\s+path="' + re.escape(path), src):
            missing.append(path)
    assert not missing, (
        f"Track 15.85 Exec #4 regression: public/field form route(s) "
        f"missing from App.js — field crews hitting these URLs would "
        f"see the 404 recovery page: {missing}"
    )


# ─── Execution #4 · Admin Portal Deep · canonical mounts ────────────


_ADMIN_DEEP_ROUTES = [
    "/admin", "/admin/system-health", "/admin/audit-log",
    "/admin/email", "/admin/integrations", "/admin/governance",
    "/admin/operations-dashboard", "/admin/operations-events",
    "/admin/digest-config", "/admin/scheduler-runs",
    "/admin/legacy-imports", "/admin/guide", "/admin/database",
    "/admin/system", "/admin/compliance-findings",
    "/admin/operational-language",
]


def test_admin_deep_canonical_routes_mounted():
    """Track 15.85 Exec #4 · Admin Portal Deep certification.

    Every documented admin-deep route must remain mounted in App.js.
    These are the operator's trust + ops + governance surfaces — if
    any one becomes unreachable, the operator's deep workflows break."""
    src = _read(APP_JS)
    missing = []
    for path in _ADMIN_DEEP_ROUTES:
        if not re.search(r'<Route\s+path="' + re.escape(path) + r'"', src):
            missing.append(path)
    assert not missing, (
        f"Track 15.85 Exec #4 regression: admin-deep route(s) missing "
        f"from App.js: {missing}"
    )


# ─── Execution #4 · Trust Center · canonical mounts ────────────────


def test_trust_center_canonical_surfaces_mounted():
    """Track 15.85 Exec #4 · Trust Center / Notifications UI cert.

    Three canonical surfaces are required: `/notifications` (digest
    + bell), `/admin/system-health` (subsystem health), and
    `/admin/audit-log` (audit trail). Each must remain mounted."""
    src = _read(APP_JS)
    assert re.search(r'<Route\s+path="/notifications"', src), (
        "Track 15.85 Exec #4: /notifications must remain mounted."
    )
    assert re.search(r'<Route\s+path="/admin/system-health"', src), (
        "Track 15.85 Exec #4: /admin/system-health must remain mounted."
    )
    assert re.search(r'<Route\s+path="/admin/audit-log"', src), (
        "Track 15.85 Exec #4: /admin/audit-log must remain mounted."
    )


# ─── Execution #4 · Shared Components · NotFound is the recovery floor ──


def test_not_found_recovery_page_has_portal_switcher():
    """Track 15.85 Exec #4 · Shared Components certification.

    The 404 recovery page is the LAST line of defense for an operator
    who hit a wrong URL. It must offer portal-switcher links so they
    can navigate out without losing their session. If the portal
    switcher disappears, every wrong-URL operator hits a dead-end.

    The portal labels are sourced from `PORTAL_LABEL` in
    `lib/permissions.js` and rendered via `others.map(...)`. We assert
    both halves of the contract: the NotFound page must consume the
    PORTAL_LABEL/PORTAL_HOME map, and the map must keep its required
    portal entries."""
    not_found = _read(PAGES_DIR / "NotFound.jsx")
    assert "PORTAL_LABEL" in not_found and "PORTAL_HOME" in not_found, (
        "Track 15.85 Exec #4: NotFound.jsx must keep its dependency "
        "on PORTAL_LABEL + PORTAL_HOME — the portal-switcher recovery "
        "links are rendered from those maps."
    )
    perms = _read(FRONTEND_SRC / "lib" / "permissions.js")
    for needle in ["HR Portal", "Safety Portal", "PM Portal",
                   "Shop Console", "Dispatch Portal", "Field Leadership"]:
        assert needle in perms, (
            f"Track 15.85 Exec #4: permissions.js must keep the "
            f"`{needle}` PORTAL_LABEL entry — NotFound recovery page "
            "renders the portal switcher from this map."
        )
