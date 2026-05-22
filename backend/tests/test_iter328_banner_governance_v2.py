"""iter328 · Banner Governance V2 — operational + cultural contract.

Locks down:
  • The new `cultural` severity tier is accepted by the API.
  • Cultural banners sort BELOW every operational severity (so a
    Memorial Day banner can never visually outrank a hurricane).
  • Operational severities still validate.
  • Bilingual broadcast — title_es / body_es are stored verbatim
    when the admin supplies them (no overwrite by auto-translate
    when copy is pre-curated).
  • Holiday templates ship with curated EN + ES copy at the source
    (no LLM dependency for cultural banners).
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import pytest
import requests


def _read_env_var(key, default=None):
    for path in ("/app/frontend/.env", "/app/backend/.env"):
        try:
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(f"{key}="):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
        except Exception:
            pass
    return os.environ.get(key, default)


def _env(key: str):
    path = "/app/backend/.env"
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    if k.strip() == key:
                        return v.strip().strip('"').strip("'")
    except Exception:
        return None
    return None


BASE_URL = _read_env_var("REACT_APP_BACKEND_URL").rstrip("/")
TIMEOUT = 60


@pytest.fixture(scope="module")
def admin_token():
    pw = _env("ADMIN_PASSWORD") or "MASCI1982!"
    r = requests.post(f"{BASE_URL}/api/admin/login", json={"password": pw}, timeout=TIMEOUT)
    if r.status_code != 200:
        pytest.skip(f"Admin login failed: {r.status_code}")
    return r.json()["token"]


# ─── Backend contract ────────────────────────────────────────────────


def test_iter328_cultural_severity_accepted(admin_token):
    """POST /api/admin/banners with severity='cultural' must succeed —
    Memorial Day / Independence Day / etc. ship at this tier."""
    r = requests.post(
        f"{BASE_URL}/api/admin/banners",
        headers={"X-Admin-Token": admin_token, "Content-Type": "application/json"},
        json={
            "title_en": "ITER328 TEST · Cultural Banner",
            "body_en": "Bounded smoke test for cultural severity.",
            "title_es": "ITER328 PRUEBA · Banner Cultural",
            "body_es": "Prueba de humo limitada para severidad cultural.",
            "severity": "cultural",
            "require_ack": False,
            "auto_translate": False,
            "template_id": "iter328_smoke",
            "expires_at": None,
        },
        timeout=TIMEOUT,
    )
    assert r.status_code == 200, f"Cultural severity rejected: {r.status_code} · {r.text[:200]}"
    body = r.json()
    banner_id = body.get("banner", {}).get("id")
    assert banner_id, f"Missing banner id in response: {body}"

    # Cleanup — DELETE so the smoke banner doesn't leak.
    requests.delete(
        f"{BASE_URL}/api/admin/banners/{banner_id}",
        headers={"X-Admin-Token": admin_token},
        timeout=TIMEOUT,
    )


def test_iter328_legacy_severities_still_validate(admin_token):
    """Operational severities (info / advisory / warning / critical)
    continue to validate after the cultural tier was added."""
    for sev in ("info", "advisory", "warning", "critical"):
        r = requests.post(
            f"{BASE_URL}/api/admin/banners",
            headers={"X-Admin-Token": admin_token, "Content-Type": "application/json"},
            json={
                "title_en": f"ITER328 TEST · {sev}",
                "body_en": "Smoke.",
                "title_es": f"ITER328 PRUEBA · {sev}",
                "body_es": "Humo.",
                "severity": sev,
                "require_ack": False,
                "auto_translate": False,
            },
            timeout=TIMEOUT,
        )
        assert r.status_code == 200, f"{sev} rejected: {r.status_code} · {r.text[:200]}"
        bid = r.json()["banner"]["id"]
        # Cleanup — DELETE (the only correct way to remove a banner;
        # PATCH does not accept a `disabled` field).
        requests.delete(
            f"{BASE_URL}/api/admin/banners/{bid}",
            headers={"X-Admin-Token": admin_token},
            timeout=TIMEOUT,
        )


def test_iter328_invalid_severity_still_rejected(admin_token):
    """Anything outside the 5-tier whitelist must still 400."""
    r = requests.post(
        f"{BASE_URL}/api/admin/banners",
        headers={"X-Admin-Token": admin_token, "Content-Type": "application/json"},
        json={
            "title_en": "should fail",
            "body_en": "",
            "severity": "purple-emergency",
            "auto_translate": False,
        },
        timeout=TIMEOUT,
    )
    assert r.status_code == 400, f"Invalid severity should 400, got {r.status_code}"


# ─── Frontend governance contract ────────────────────────────────────


FRONTEND = Path("/app/frontend/src")


def test_iter328_frontend_has_cultural_in_severity_meta():
    """SEVERITY_META in the shared templates file must include the new
    `cultural` tier with a priority field that sorts it BELOW every
    operational severity."""
    src = (FRONTEND / "lib/hubBannerTemplates.js").read_text()
    assert "cultural" in src, "cultural severity missing from SEVERITY_META"

    # Pull priority numbers via regex — keeps the test robust to
    # ordering or whitespace changes.
    priorities = dict(re.findall(r"^\s+(critical|warning|advisory|info|cultural):.*?priority:\s*(\d+)", src, re.M | re.S))
    assert all(k in priorities for k in ("critical", "warning", "advisory", "info", "cultural")), (
        f"Missing priorities: {priorities}"
    )
    nums = {k: int(v) for k, v in priorities.items()}
    # Cultural must yield to every operational tier.
    for op in ("critical", "warning", "advisory", "info"):
        assert nums["cultural"] > nums[op], (
            f"cultural priority ({nums['cultural']}) must be > {op} ({nums[op]}) — "
            "cultural banners must NEVER outrank operational alerts."
        )


def test_iter328_holiday_templates_ship_bilingual_at_source():
    """Each cultural template must ship with non-empty title_es +
    body_es — NO LLM dependency for holiday / remembrance copy."""
    src = (FRONTEND / "lib/hubBannerTemplates.js").read_text()
    # Templates that should be bilingual at source:
    REQUIRED = [
        "memorial_day", "independence_day", "labor_day", "veterans_day",
        "thanksgiving", "christmas", "new_year", "work_zone_awareness",
    ]
    for tid in REQUIRED:
        # Look for the block that contains id: "<tid>" — assert
        # title_es and body_es appear before the next closing brace.
        m = re.search(rf'id:\s*"{tid}".*?\n\s*\}},', src, re.S)
        assert m, f"Holiday template missing: {tid}"
        block = m.group(0)
        assert "title_es" in block, f"{tid} missing title_es"
        assert "body_es" in block, f"{tid} missing body_es"
        # Ensure the ES fields aren't empty strings.
        assert re.search(r'title_es:\s*"[^"]+', block), f"{tid} has empty title_es"
        assert re.search(r'body_es:\s*"[^"]+', block), f"{tid} has empty body_es"


def test_iter328_bannerstrip_renders_bilingual_broadcast():
    """BannerStrip.jsx must render both EN and ES content (not gated by
    the user's lang toggle) so morning-briefing messaging reaches the
    full workforce."""
    src = (FRONTEND / "components/BannerStrip.jsx").read_text()
    # The render path must reference both title_en + title_es AND
    # body_en + body_es (the bilingual broadcast contract).
    for token in ("titleEn", "titleEs", "bodyEn", "bodyEs"):
        assert token in src, f"BannerStrip.jsx must render {token} for bilingual broadcast"
    # Acknowledge button label must include both languages.
    assert "I Acknowledge" in src and "Reconozco" in src, (
        "BannerStrip.jsx ack button must show bilingual label "
        "(I Acknowledge · Reconozco) for ack-required banners."
    )


def test_iter328_calm_chrome_no_full_bleed_bright_bars():
    """V2 chrome rule: severity BARS use `bg-<color>-50 ... border-l-4`
    soft-fill pattern (no `bg-red-700 text-white` full-bleed slabs).
    Sentry against future regressions to the legacy heavy chrome.

    Buttons (`cls_btn`) are scoped separately — they legitimately use
    saturated colors for CTA contrast. We only audit the bar."""
    src = (FRONTEND / "lib/hubBannerTemplates.js").read_text()
    # Extract every cls_bar value via regex — these are the bar
    # classes that paint full-width across the page.
    bar_values = re.findall(r'cls_bar:\s*"([^"]+)"', src)
    assert len(bar_values) == 5, f"Expected 5 severity cls_bar entries, got {len(bar_values)}"
    forbidden_bar_substrings = (
        "bg-red-700",   # legacy warning slab
        "bg-red-950",   # legacy critical pulse slab
        "bg-amber-500", # legacy advisory full-fill
        "bg-blue-700",  # legacy info full-fill
    )
    for bv in bar_values:
        for pat in forbidden_bar_substrings:
            assert pat not in bv, (
                f"iter328 V2 chrome violation — legacy heavy bar pattern '{pat}' "
                f"found in SEVERITY_META cls_bar: {bv!r}. Use `bg-<color>-50 ... "
                "border-l-4` soft fill."
            )
        # Soft-fill check — every bar must be a -50 background with
        # a border-l-4 accent stripe (the platform family pattern).
        assert "border-l-4" in bv, (
            f"iter328 V2 chrome violation — bar value {bv!r} missing border-l-4."
        )
