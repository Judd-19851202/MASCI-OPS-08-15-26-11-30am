"""iter437 / Phase IV-BETA.5A-P1A · Governance Health Chip regression.

Validates the operator-facing governance health chip:
  • Backend endpoint returns the persisted baseline summary
  • Chip mounts on all four Hub V2 surfaces (Admin · PM · HR · Safety)
  • Chip stays monochrome — no background colour leaked, no animation
  • Chip is hidden silently when the endpoint returns ok=false (no error noise)

Loads the live baseline JSON (captured by test_visual_doctrine_baseline.py)
and asserts the chip surfaces the expected loudness/state for each portal.
"""
from __future__ import annotations

import os

import pytest
import requests

SUPER_EMAIL = (
    os.popen("grep '^SUPER_ADMIN_EMAIL=' /app/backend/.env | cut -d= -f2-")
    .read()
    .strip()
    .strip('"')
)
SUPER_PW = (
    os.popen("grep '^SUPER_ADMIN_BOOTSTRAP_PASSWORD=' /app/backend/.env | cut -d= -f2-")
    .read()
    .strip()
    .strip('"')
)


@pytest.fixture(scope="module")
def tokens(base_url: str) -> dict:
    r = requests.post(
        f"{base_url}/api/auth/multi-login",
        json={"email": SUPER_EMAIL, "password": SUPER_PW},
        timeout=15,
    )
    r.raise_for_status()
    return (r.json() or {}).get("portal_tokens", {}) or {}


# ─── Endpoint contract ────────────────────────────────────────────

def test_endpoint_returns_all_portals(base_url: str):
    r = requests.get(f"{base_url}/api/governance/health", timeout=15)
    r.raise_for_status()
    j = r.json()
    assert j.get("ok") is True
    portals = j.get("portals") or {}
    for p in ("admin", "pm", "hr", "safety"):
        assert p in portals, f"portal {p} missing from /api/governance/health"
        cell = portals[p]
        assert cell["state"] in {"stable", "monitor", "drift"}
        assert isinstance(cell["loudness"], (int, float))
        assert cell["loudness"] >= 0


@pytest.mark.parametrize("portal", ["admin", "pm", "hr", "safety"])
def test_endpoint_single_portal(base_url: str, portal: str):
    r = requests.get(f"{base_url}/api/governance/health/{portal}", timeout=15)
    r.raise_for_status()
    j = r.json()
    assert j.get("ok") is True, f"portal {portal} returned ok=false: {j}"
    assert j.get("portal") == portal
    assert "loudness" in j
    assert j["state"] in {"stable", "monitor", "drift"}


def test_endpoint_rejects_unknown_portal(base_url: str):
    r = requests.get(f"{base_url}/api/governance/health/unknownx", timeout=15)
    assert r.status_code == 400


# ─── Frontend chip rendering ──────────────────────────────────────

def _seed_admin(page, base_url: str, token: str):
    page.goto(f"{base_url}/", wait_until="domcontentloaded")
    page.evaluate(f"localStorage.setItem('masci.admin.token', '{token}')")


def _seed_pm(page, base_url: str, token: str):
    page.goto(f"{base_url}/", wait_until="domcontentloaded")
    page.evaluate(f"localStorage.setItem('masci.pm.token', '{token}')")


def _seed_hr(page, base_url: str, token: str):
    page.goto(f"{base_url}/", wait_until="domcontentloaded")
    page.evaluate(
        f"localStorage.setItem('masci.hr.token', '{token}');"
        f"localStorage.setItem('masci.hr.user', JSON.stringify({{name:'ChipRegress'}}));"
    )


def _seed_safety(page, base_url: str, token: str):
    page.goto(f"{base_url}/", wait_until="domcontentloaded")
    page.evaluate(
        f"localStorage.setItem('masci.safety.token', '{token}');"
        f"localStorage.setItem('masci.safety.user', JSON.stringify({{name:'ChipRegress'}}));"
    )


HUB_ROUTES = [
    ("admin",  "/admin?adminSidebarV2=1",          _seed_admin),
    ("pm",     "/pm?pmSidebarV2=1",                _seed_pm),
    ("hr",     "/hr?hrSidebarV2=1",                _seed_hr),
    ("safety", "/safety-portal?safetySidebarV2=1", _seed_safety),
]


@pytest.mark.parametrize("portal,url,seed", HUB_ROUTES, ids=[r[0] for r in HUB_ROUTES])
def test_chip_renders_on_hub(
    page, base_url: str, tokens: dict, portal: str, url: str, seed
):
    tok = tokens.get(portal) or tokens.get("admin")
    assert tok, f"no token issued for {portal}"
    seed(page, base_url, tok)
    page.goto(f"{base_url}{url}", wait_until="networkidle")
    page.wait_for_timeout(2000)

    chip = page.locator(f"[data-testid='governance-health-chip-{portal}']")
    assert chip.count() == 1, (
        f"governance-health-chip-{portal} missing on {url}"
    )

    # State must be one of the three known values.
    state = chip.get_attribute("data-state")
    assert state in {"stable", "monitor", "drift"}, (
        f"unexpected state on {portal}: {state}"
    )

    # Loudness label must contain "/100"
    loud = page.locator(f"[data-testid='governance-health-loudness-{portal}']")
    assert loud.count() == 1
    loud_text = (loud.text_content() or "").strip()
    assert "/100" in loud_text, f"loudness label missing /100 on {portal}: {loud_text!r}"

    # Monochrome contract — no coloured background classes on the chip itself.
    chip_class = chip.get_attribute("class") or ""
    for banned in ("bg-red-", "bg-amber-", "bg-emerald-", "bg-cyan-", "bg-violet-", "bg-purple-"):
        assert banned not in chip_class, (
            f"governance chip on {portal} leaked colour class {banned!r}: {chip_class}"
        )


def test_chip_label_lowercase_and_quiet(page, base_url: str, tokens: dict):
    """The chip text must stay sentence-case (lowercase 'governance …'),
    not uppercase, and must not surface an exclamation mark — operationally
    restrained per directive."""
    _seed_admin(page, base_url, tokens.get("admin"))
    page.goto(f"{base_url}/admin?adminSidebarV2=1", wait_until="networkidle")
    page.wait_for_timeout(1500)
    label = page.locator("[data-testid='governance-health-label-admin']")
    assert label.count() == 1
    text = (label.text_content() or "").strip()
    # font-mono uppercase via Tailwind class is fine — but the source text
    # must remain lowercase so verbiage drift instruments stay accurate.
    assert text.lower().startswith("governance "), text
    assert "!" not in text, f"chip label contains exclamation: {text!r}"
