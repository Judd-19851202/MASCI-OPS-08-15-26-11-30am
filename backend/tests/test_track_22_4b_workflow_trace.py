"""TRACK 22.4b · Workflow Deep Trace regression locks.

Non-mutating contract tests that lock down the routing/RBAC/email-safety
invariants surfaced during the workflow trace. These tests exercise
NOTHING that would send real email, mutate live records, or degrade
Motive behavior.
"""
from __future__ import annotations

import os

import httpx

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8001")
ADMIN_EMAIL = os.environ.get("TEST_SUPER_ADMIN_EMAIL", "jaymn.judd@mascigc.com")
ADMIN_PASS = os.environ.get("TEST_SUPER_ADMIN_PASSWORD", "Maddix123!")


def _admin_token() -> str:
    r = httpx.post(
        f"{BACKEND_URL}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASS},
        timeout=10.0,
    )
    r.raise_for_status()
    return (r.json().get("portal_tokens") or {}).get("admin") or ""


# ── RBAC locks ────────────────────────────────────────────────────

def test_workflow_read_endpoints_reject_anonymous():
    """Every record-fetch endpoint must reject anonymous callers.

    This is the F-01/F-02 invariant extended to the whole workflow
    surface: no operational data leaks to unauthenticated users.
    """
    protected = [
        "/api/daily-reports",
        "/api/incidents",
        "/api/meetings",
        "/api/dispatch/assignments",
        "/api/trench-safety/dashboard",
        "/api/admin/integrations/truth-status",
        "/api/dispatch/motive-posture",
    ]
    for path in protected:
        r = httpx.get(f"{BACKEND_URL}{path}", timeout=10.0)
        assert r.status_code in (401, 403), (
            f"{path} should require auth (got {r.status_code})"
        )


# ── Email safety lock ─────────────────────────────────────────────

def test_email_safety_mode_strict_in_preview():
    """Preview must NEVER send real email. The presence of
    EMAIL_SAFETY_MODE=strict is the guard, and Trust Spine
    'notification_queued/skipped/email_safety_mode:strict' rows are
    the evidence trail.
    """
    env = os.environ.get("EMAIL_SAFETY_MODE") or ""
    app_env = os.environ.get("APP_ENV") or ""
    if app_env in ("preview", "test", "staging"):
        assert env.lower() == "strict", (
            "preview/test/staging MUST have EMAIL_SAFETY_MODE=strict "
            f"(got {env!r} · app_env={app_env!r})"
        )


# ── Motive protection lock ────────────────────────────────────────

def test_motive_posture_shape_stable():
    """Motive protection: the truth surface response shape must remain
    stable so dispatch/frontend ribbons keep working across releases.
    """
    token = _admin_token()
    r = httpx.get(
        f"{BACKEND_URL}/api/dispatch/motive-posture",
        headers={"X-Admin-Token": token},
        timeout=15.0,
    )
    assert r.status_code == 200
    body = r.json()
    for key in ("id", "name", "config_status", "connectivity_status",
                "operational_status", "overall"):
        assert key in body, f"missing motive posture key: {key}"
    assert body["id"] == "motive"
    # F-02 invariant re-locked here at the workflow level.
    if body["overall"] == "LIVE_VERIFIED":
        assert body["operational_status"] == "LIVE_VERIFIED"


# ── Canonical Daily Report endpoint lock ──────────────────────────

def test_canonical_daily_reports_endpoint_is_alive():
    """Confirms the canonical /api/daily-reports endpoint continues to
    serve records (DR-UNIFY-003 invariant).
    """
    token = _admin_token()
    r = httpx.get(
        f"{BACKEND_URL}/api/daily-reports?limit=1",
        headers={"X-Admin-Token": token},
        timeout=15.0,
    )
    assert r.status_code == 200


# ── Trench Safety cross-portal source-of-truth lock ───────────────

def test_trench_safety_dashboard_returns_total_active_assets():
    """SafetyHub reads total_active_assets from this endpoint. If the
    field disappears, the Safety Trench tile silently regresses to
    'No Recent Data'.
    """
    token = _admin_token()
    r = httpx.get(
        f"{BACKEND_URL}/api/trench-safety/dashboard",
        headers={"X-Admin-Token": token},
        timeout=15.0,
    )
    assert r.status_code == 200
    body = r.json()
    assert "total_active_assets" in body, (
        "SafetyHubV2 cross-portal wiring requires total_active_assets"
    )
    assert isinstance(body["total_active_assets"], int)
