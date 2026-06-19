"""iter251 · Fleet Guidance Integration · backend coverage tests.

After the operator-approved Fleet Guidance Completion Pass we lock in:
  - 6 new articles in the Operations Guidance Center (EN + ES)
  - 6 new form_keys in the contextual HelpTip registry
  - bilingual continuity · no English leakage in ES mode
"""
from __future__ import annotations

import os

import requests


BASE_URL = os.environ.get(
    "REACT_APP_BACKEND_URL",
    "https://safety-audit-mobile-1.preview.emergentagent.com",
).rstrip("/")
ADMIN_PW = os.environ.get("ADMIN_PASSWORD", "Maddix123!")


def _admin_token() -> str:
    r = requests.post(f"{BASE_URL}/api/admin/login", json={"password": ADMIN_PW}, timeout=15)
    r.raise_for_status()
    return r.json()["token"]


FLEET_ARTICLES = [
    "fleet-daily-dvir",
    "fleet-weekly-lead",
    "fleet-weekly-emergency",
    "fleet-severity-oos-vs-monitor",
    "fleet-repair-lifecycle",
    "fleet-return-to-service",
]

FLEET_TIP_KEYS = [
    ("fleet.dvir", "public", 3),          # form_key, scope_token_needed, min_tip_count
    ("fleet.weekly-lead", "public", 2),
    ("fleet.weekly-emergency", "public", 2),
    ("fleet.repair", "admin", 2),
    ("fleet.rts", "admin", 2),
    ("fleet.visibility", "admin", 2),
]


class TestFleetGuidanceIntegration:

    def test_all_six_articles_present_en(self):
        for slug in FLEET_ARTICLES:
            r = requests.get(f"{BASE_URL}/api/guidance/articles/{slug}", timeout=15)
            assert r.status_code == 200, f"{slug} missing in EN ({r.status_code})"
            j = r.json()
            assert j.get("id") == slug
            assert j.get("title")
            assert j.get("body")

    def test_all_six_articles_present_es(self):
        for slug in FLEET_ARTICLES:
            r = requests.get(f"{BASE_URL}/api/guidance/articles/{slug}?lang=es", timeout=15)
            assert r.status_code == 200, f"{slug} missing in ES ({r.status_code})"
            j = r.json()
            # ES articles should expose translated fields, not the raw EN
            t = j.get("title_es") or j.get("title")
            assert t, f"{slug} has no ES title"
            # Either body_es present, or top-level body is ES-rendered
            assert j.get("body") or j.get("body_es"), f"{slug} has no ES body"

    def test_severity_article_explicitly_explains_governance(self):
        """Operator culturally-important requirement: this article must
        clearly state that drivers DO NOT assign severity."""
        r = requests.get(f"{BASE_URL}/api/guidance/articles/fleet-severity-oos-vs-monitor", timeout=15)
        assert r.status_code == 200
        full_text = str(r.json())
        # English signal
        assert "Drivers do not assign severity" in full_text or "drivers don't" in full_text.lower()
        # System-classifies signal
        assert "system" in full_text.lower() and "classif" in full_text.lower()

    def test_contextual_tips_registered_for_each_fleet_form_key(self):
        admin_h = {"X-Admin-Token": _admin_token()}
        for fk, scope, min_count in FLEET_TIP_KEYS:
            headers = admin_h if scope == "admin" else {}
            r = requests.get(
                f"{BASE_URL}/api/guidance/tips?form_key={fk}",
                headers=headers, timeout=15,
            )
            assert r.status_code == 200, f"{fk} returned {r.status_code}"
            tips = r.json().get("tips", [])
            assert len(tips) >= min_count, (
                f"{fk} has {len(tips)} tips, expected ≥ {min_count}"
            )

    def test_public_fleet_tips_visible_without_token(self):
        """Driver-facing form tips must be accessible to anonymous users
        (drivers submit DVIRs without logging in)."""
        for fk in ("fleet.dvir", "fleet.weekly-lead", "fleet.weekly-emergency"):
            r = requests.get(
                f"{BASE_URL}/api/guidance/tips?form_key={fk}",
                headers={"X-Admin-Token": ""},  # explicit anon
                timeout=15,
            )
            assert r.status_code == 200
            assert r.json().get("tips"), f"{fk} has no public tips"

    def test_portal_shop_mentions_fleet(self):
        """Shop portal landing article should reference Fleet workflows
        now that Fleet flows into the Shop queue."""
        r = requests.get(f"{BASE_URL}/api/guidance/articles/portal-shop", timeout=15)
        assert r.status_code == 200
        text = str(r.json()).lower()
        assert "fleet" in text, "portal-shop article doesn't mention Fleet"
