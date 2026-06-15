"""TRACK 14.0-RC1 · Priority-One Defect Closure regression suite.

Pins the four defect fixes shipped in this track:

  D3 — Offline / Throttled / Aborted Request Trust Surface
       /app/frontend/src/components/OfflineBanner.jsx mounted globally
       in App.js, listens to navigator online/offline events, renders
       a calm sky-blue ribbon while offline. Pairs with QueueStatusPill.

  D1 — Hub / Public Route Background Poller 401 Noise
       Globally-mounted pollers (NotificationBell, GlobalKeepalive)
       already gate on `isSignedInAnywhere()` / public endpoints. This
       suite pins those guards so a future refactor doesn't accidentally
       remove them.

  D2 — PM Command Center First-Load 401 Race
       /app/frontend/src/components/pm/command/pmCommandApi.js now
       bails early (returns null) when no admin AND no PM token exist
       in localStorage. Prevents the 5×401 console storm reported by
       iteration_515.

  D4 — /safety/forms/login Confusion
       Title is now explicit: "Safety Forms · Password-Gated". Glance-
       anchor adopted. Submit aria-busy adopted for consistency.

These are fast static-source assertions. Runtime evidence is captured
by the testing-agent iteration following this track.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest


FRONTEND = Path("/app/frontend/src")
APP_JS = FRONTEND / "App.js"


# ── D3 · Offline trust-surface contract ─────────────────────────


def test_d3_offline_banner_component_exists():
    """The global OfflineBanner component must exist."""
    p = FRONTEND / "components" / "OfflineBanner.jsx"
    assert p.exists(), "components/OfflineBanner.jsx missing"


def test_d3_offline_banner_listens_to_online_offline_events():
    src = (FRONTEND / "components" / "OfflineBanner.jsx").read_text(encoding="utf-8")
    assert 'addEventListener("online"' in src, "missing online listener"
    assert 'addEventListener("offline"' in src, "missing offline listener"
    assert 'removeEventListener("online"' in src, "missing online cleanup"
    assert 'removeEventListener("offline"' in src, "missing offline cleanup"


def test_d3_offline_banner_uses_navigator_online():
    src = (FRONTEND / "components" / "OfflineBanner.jsx").read_text(encoding="utf-8")
    assert "navigator.onLine" in src, "must read navigator.onLine"


def test_d3_offline_banner_renders_null_when_online():
    """The banner must short-circuit to null when online so it doesn't
    take up viewport space."""
    src = (FRONTEND / "components" / "OfflineBanner.jsx").read_text(encoding="utf-8")
    # `if (online) return null;` (or with semicolon-on-next-line).
    assert re.search(r"if\s*\(\s*online\s*\)\s*return\s+null", src), (
        "OfflineBanner must short-circuit to null when navigator is online"
    )


def test_d3_offline_banner_mounted_in_app_js():
    """The banner is useless if it isn't actually mounted globally."""
    src = APP_JS.read_text(encoding="utf-8")
    assert "import OfflineBanner" in src, "OfflineBanner not imported in App.js"
    assert "<OfflineBanner" in src, "OfflineBanner not mounted in App.js JSX tree"


def test_d3_offline_banner_has_data_testid():
    """Tests + automation need a stable testid."""
    src = (FRONTEND / "components" / "OfflineBanner.jsx").read_text(encoding="utf-8")
    assert 'data-testid="offline-banner"' in src


def test_d3_classifier_treats_cancellation_as_non_event():
    """Defense-in-depth: errorClassification must treat axios
    CanceledError / AbortError as `kind: null` so a route change
    mid-fetch does NOT pop the disconnect modal."""
    src = (FRONTEND / "lib" / "errorClassification.js").read_text(encoding="utf-8")
    assert "CanceledError" in src
    assert "AbortError" in src
    assert "isCanceled" in src


# ── D2 · PM Command Center 401-race fix ─────────────────────────


def test_d2_pm_command_api_guards_on_missing_token():
    """pmCommandApi._get MUST return null instead of firing when no
    admin AND no PM token exist in localStorage. This is the fix for
    the iteration_515 5×401 race."""
    src = (FRONTEND / "components" / "pm" / "command" / "pmCommandApi.js").read_text(
        encoding="utf-8"
    )
    assert "getAdminToken" in src, "pmCommandApi must read admin token"
    assert "getPmToken" in src, "pmCommandApi must read PM token"
    # The guard must combine both: no admin AND no PM → bail.
    assert re.search(
        r"if\s*\(\s*!\s*getAdminToken\(\)\s*&&\s*!\s*getPmToken\(\)\s*\)",
        src,
    ), (
        "pmCommandApi missing the `if (!getAdminToken() && !getPmToken()) return null` "
        "guard — the D2 fix is regressed."
    )


def test_d2_pm_command_api_uses_skip_session_status():
    """skipSessionStatus: true is also required so the global modal
    is never raised by a benign background widget 401."""
    src = (FRONTEND / "components" / "pm" / "command" / "pmCommandApi.js").read_text(
        encoding="utf-8"
    )
    assert "skipSessionStatus: true" in src


# ── D1 · Hub / public-route poller hygiene ──────────────────────


def test_d1_notification_bell_gates_on_signed_in():
    """NotificationBell must early-return when no portal session
    exists — otherwise it fires a 401 on every public-route mount."""
    src = (FRONTEND / "components" / "NotificationBell.jsx").read_text(encoding="utf-8")
    assert "isSignedInAnywhere" in src, "NotificationBell missing signed-in guard"
    # The guard runs INSIDE refreshCount (the polling function).
    assert re.search(
        r"if\s*\(\s*!\s*isSignedInAnywhere\(\)\s*\)\s*return",
        src,
    ), "NotificationBell refreshCount must early-return when not signed in"


def test_d1_keepalive_pings_only_public_health_endpoint():
    """GlobalKeepalive must only hit /api/health — never a protected
    endpoint. /api/health never 401s."""
    src = (FRONTEND / "components" / "GlobalKeepalive.jsx").read_text(encoding="utf-8")
    assert "/api/health" in src
    # No protected endpoints accidentally added.
    forbidden = ["/api/admin", "/api/pm/", "/api/hr/", "/api/safety/", "/api/dispatch/"]
    for f in forbidden:
        assert f not in src, f"GlobalKeepalive must not hit protected endpoint {f}"


# ── D4 · Safety Forms login copy clarification ──────────────────


def test_d4_safety_forms_login_title_explicit():
    """The Safety Forms entry point must explicitly mention it is
    password-gated so users don't expect an email/password form like
    the other portal logins."""
    src = (FRONTEND / "pages" / "SafetyFormsLogin.jsx").read_text(encoding="utf-8")
    assert "Safety Forms · Password-Gated" in src, (
        "Safety Forms login title must mention password-gating "
        "(D4 copy clarification)."
    )


def test_d4_safety_forms_login_has_glance_anchor_and_aria_busy():
    src = (FRONTEND / "pages" / "SafetyFormsLogin.jsx").read_text(encoding="utf-8")
    assert "field-glance-anchor" in src
    assert "aria-busy=" in src


# ── Session-status overlay sanity (still global) ─────────────────


def test_session_status_overlay_still_mounted():
    """SessionStatusOverlay remains the single global modal so a
    storm of failing widgets collapses into one message."""
    src = APP_JS.read_text(encoding="utf-8")
    assert "SessionStatusOverlay" in src
