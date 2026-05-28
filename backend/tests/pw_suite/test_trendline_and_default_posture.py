"""iter437 / Phase IV-BETA.5A-P2 · Doctrine Trendline + V2 Default Posture.

Locks the new P2A + P2B governance contracts:

  P2A — Doctrine Trendline System
    • `diff_doctrine_baseline.py --append` writes one record per portal
      per invocation to /app/memory/DOCTRINE_TRENDLINE.json
    • The trendline file remains valid JSON across appends
    • The `direction` field surfaces on the chip endpoint after enough
      records exist (recent vs older average comparison)

  P2B — V2 Default Posture
    • PM Sidebar V2 mounts by default on /pm (no flag needed)
    • HR Sidebar V2 mounts by default on /hr/* (no flag needed)
    • Safety Sidebar V2 mounts by default on /safety-portal/* (no flag
      needed) — flipped at IV-BETA.5A-P6 after a clean stabilization
      review (28 consecutive trendline records at calmness=72.41,
      direction=stable, delta=0.0).
    • `?pmSidebarV2=0`, `?hrSidebarV2=0`, and `?safetySidebarV2=0` are
      operator escape hatches
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest
import requests

SUPER_EMAIL = (
    os.popen("grep '^SUPER_ADMIN_EMAIL=' /app/backend/.env | cut -d= -f2-")
    .read().strip().strip('"')
)
SUPER_PW = (
    os.popen("grep '^SUPER_ADMIN_BOOTSTRAP_PASSWORD=' /app/backend/.env | cut -d= -f2-")
    .read().strip().strip('"')
)

TRENDLINE_PATH = Path("/app/memory/DOCTRINE_TRENDLINE.json")
TRENDLINE_MAX_RECORDS = 500  # mirrors scripts/diff_doctrine_baseline.py


@pytest.fixture(scope="module")
def tokens(base_url: str) -> dict:
    r = requests.post(
        f"{base_url}/api/auth/multi-login",
        json={"email": SUPER_EMAIL, "password": SUPER_PW},
        timeout=15,
    )
    r.raise_for_status()
    return (r.json() or {}).get("portal_tokens", {}) or {}


# ─── P2A · Doctrine Trendline append contract ─────────────────────

def test_trendline_append_writes_record(tmp_path):
    """`diff_doctrine_baseline.py --append` writes per-portal records
    and the file remains valid JSON."""
    before_count = 0
    if TRENDLINE_PATH.exists():
        before = json.loads(TRENDLINE_PATH.read_text())
        before_count = len(before.get("records") or [])

    result = subprocess.run(
        ["python3", "/app/scripts/diff_doctrine_baseline.py", "--append"],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr

    assert TRENDLINE_PATH.exists()
    after = json.loads(TRENDLINE_PATH.read_text())
    after_records = after.get("records") or []
    # The trendline file enforces a rolling cap (TRENDLINE_MAX_RECORDS).
    # Once at-cap, an --append cannot grow the file past the cap by
    # design — old records age out. The truthful invariant is:
    # either growth, OR steady-state at cap with the latest record
    # matching the current portal set.
    expected_min = min(TRENDLINE_MAX_RECORDS, before_count + 1)
    assert len(after_records) >= expected_min, (
        f"records did not grow as expected: "
        f"before={before_count}, after={len(after_records)}, "
        f"expected_min={expected_min}"
    )
    # Latest record must have the required fields.
    latest = after_records[-1]
    for key in (
        "portal", "timestamp", "calmness", "hierarchy_consistency",
        "escalation_noise", "hue_family_count", "badge_density", "status",
    ):
        assert key in latest, f"trendline record missing field {key}: {latest}"
    assert latest["portal"] in {"admin", "pm", "hr", "safety"}
    assert latest["status"] in {"stable", "monitor", "drift"}


def test_chip_endpoint_returns_direction_field(base_url: str):
    """After P2A, the chip endpoint surfaces a `direction` field per
    portal — `stable | improving | drifting | new`."""
    r = requests.get(f"{base_url}/api/governance/health/pm", timeout=15)
    r.raise_for_status()
    j = r.json()
    assert j.get("ok") is True
    assert "direction" in j, f"endpoint missing direction field: {j}"
    assert j["direction"] in {"stable", "improving", "drifting", "new"}


# ─── P2B · PM + HR Sidebar V2 default posture ─────────────────────

def _seed_pm(page, base_url: str, token: str):
    page.goto(f"{base_url}/", wait_until="domcontentloaded")
    page.evaluate(f"localStorage.setItem('masci.pm.token', '{token}')")
    # Clear any sticky V2 flag from prior runs so we test the true default.
    page.evaluate("localStorage.removeItem('masci.pm.sidebar.v2')")


def _seed_hr(page, base_url: str, token: str):
    page.goto(f"{base_url}/", wait_until="domcontentloaded")
    page.evaluate(
        f"localStorage.setItem('masci.hr.token', '{token}');"
        f"localStorage.setItem('masci.hr.user', JSON.stringify({{name:'DefaultPosture'}}));"
    )


def test_pm_sidebar_v2_is_default(page, base_url: str, tokens: dict):
    """No flag · V2 sidebar mounts by default on /pm. The V2 sidebar
    component carries its own `pm-side-nav-v2` testid in addition to
    the shared aside; we check the V2-specific one to distinguish from
    the legacy `<SideNav>` which renders in the same aside."""
    tok = tokens.get("pm") or tokens.get("admin")
    _seed_pm(page, base_url, tok)
    page.goto(f"{base_url}/pm", wait_until="networkidle")
    page.wait_for_timeout(2000)
    assert page.locator(
        "[data-testid~='pm-side-nav-v2']"
    ).count() >= 1, "PM Sidebar V2 must mount by default after P2B"


def test_pm_sidebar_v2_escape_hatch(page, base_url: str, tokens: dict):
    """`?pmSidebarV2=0` collapses PM back to the legacy <SideNav>."""
    tok = tokens.get("pm") or tokens.get("admin")
    _seed_pm(page, base_url, tok)
    page.goto(f"{base_url}/pm?pmSidebarV2=0", wait_until="networkidle")
    page.wait_for_timeout(2000)
    assert page.locator(
        "[data-testid~='pm-side-nav-v2']"
    ).count() == 0, "PM Sidebar V2 should collapse when ?pmSidebarV2=0"


def test_hr_sidebar_v2_is_default(page, base_url: str, tokens: dict):
    """No flag · V2 sidebar mounts by default on HR sub-pages that wrap
    in HrPageShell (the Hub itself does not use HrPageShell)."""
    tok = tokens.get("hr") or tokens.get("admin")
    _seed_hr(page, base_url, tok)
    page.goto(f"{base_url}/hr/time-verification", wait_until="networkidle")
    page.wait_for_timeout(2000)
    assert page.locator(
        "[data-testid='hr-side-nav-desktop']"
    ).count() == 1, "HR Sidebar V2 must mount by default after P2B"


def test_safety_sidebar_v2_is_default_posture(page, base_url: str, tokens: dict, viewport_name: str):
    """iter437 IV-BETA.5A-P6 · Safety Sidebar V2 is now the DEFAULT
    layout after a clean stabilization review. No flag · the V2 desktop
    nav must mount on Safety sub-pages that wrap in SafetyShell.

    Note: the Safety Hub root (`/safety-portal`) doesn't use SafetyShell
    so we hit a sub-page (`/safety-portal/incidents`) where the shell
    chrome is active.

    Mobile uses a separate mobile-nav surface, NOT `safety-side-nav-desktop`,
    so we skip the desktop selector check on the mobile viewport — its
    own scroll/leak regressions live in test_safety_sidebar_v2.py."""
    if viewport_name == "mobile":
        pytest.skip("desktop sidebar selector — mobile uses mobile-nav surface")
    tok = tokens.get("safety") or tokens.get("admin")
    page.goto(f"{base_url}/", wait_until="domcontentloaded")
    page.evaluate(
        f"localStorage.setItem('masci.safety.token', '{tok}');"
        f"localStorage.setItem('masci.safety.user', JSON.stringify({{name:'DefaultPosture'}}));"
        # Clear any sticky LS override so we test the true default.
        f"localStorage.removeItem('masci.safety.sidebar.v2');"
    )
    page.goto(f"{base_url}/safety-portal/incidents", wait_until="networkidle")
    page.wait_for_timeout(2000)
    assert page.locator(
        "[data-testid='safety-side-nav-desktop']"
    ).count() == 1, (
        "Safety Sidebar V2 must mount by default after IV-BETA.5A-P6"
    )


def test_safety_sidebar_v2_escape_hatch_query(page, base_url: str, tokens: dict):
    """`?safetySidebarV2=0` collapses Safety back to the legacy single-
    column chrome (operator escape hatch · mirrors PM/HR)."""
    tok = tokens.get("safety") or tokens.get("admin")
    page.goto(f"{base_url}/", wait_until="domcontentloaded")
    page.evaluate(
        f"localStorage.setItem('masci.safety.token', '{tok}');"
        f"localStorage.setItem('masci.safety.user', JSON.stringify({{name:'EscapeHatch'}}));"
        f"localStorage.removeItem('masci.safety.sidebar.v2');"
    )
    page.goto(
        f"{base_url}/safety-portal/incidents?safetySidebarV2=0",
        wait_until="networkidle",
    )
    page.wait_for_timeout(1500)
    assert page.locator(
        "[data-testid='safety-side-nav-desktop']"
    ).count() == 0, (
        "Safety Sidebar V2 should collapse when ?safetySidebarV2=0"
    )


# ─── Chip direction rendering (UI · uses live endpoint data) ──────

def test_chip_renders_direction_or_state(page, base_url: str, tokens: dict):
    """Chip label must read one of:
      • governance stable
      • governance monitor
      • governance drift
      • governance improving
      • governance drifting
    (lowercase source — Tailwind transforms presentation to uppercase)."""
    _seed_pm(page, base_url, tokens.get("pm") or tokens.get("admin"))
    page.goto(f"{base_url}/pm", wait_until="networkidle")
    page.wait_for_timeout(2000)
    label = page.locator("[data-testid='governance-health-label-pm']")
    assert label.count() == 1
    text = (label.text_content() or "").strip().lower()
    assert text in {
        "governance stable",
        "governance monitor",
        "governance drift",
        "governance improving",
        "governance drifting",
    }, f"unexpected chip label: {text!r}"
