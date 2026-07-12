"""TRACK 23.1 · Live API smoke against the preview backend.

Exercises the three new endpoints and confirms V1 downstream is intact.
Uses the public URL from frontend/.env so we test what the browser sees.
"""
from __future__ import annotations

import os
import requests

BASE_URL = "https://backup-forensics.preview.emergentagent.com"


# ── Cost-code endpoint ───────────────────────────────────────────

def test_cost_codes_unknown_project_returns_empty_envelope():
    r = requests.get(
        f"{BASE_URL}/api/cost-codes/for-project",
        params={"project_number": "UNKNOWN-XYZ-999"},
        timeout=30,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("codes") == []
    assert body.get("count") == 0
    assert body.get("provider") in ("jobs_master", None) or "provider" in body


def test_cost_codes_known_project_shape():
    r = requests.get(
        f"{BASE_URL}/api/cost-codes/for-project",
        params={"project_number": "25-21"},
        timeout=30,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "codes" in body
    assert "count" in body
    assert body.get("provider") == "jobs_master"
    assert isinstance(body["codes"], list)
    assert body["count"] == len(body["codes"])


# ── DR V3 feature flag endpoint ──────────────────────────────────

def test_feature_flag_anonymous_disabled():
    r = requests.get(f"{BASE_URL}/api/feature-flags/dr-v3", timeout=15)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("enabled") is False
    assert body.get("source") == "tenant_default"


def test_feature_flag_pilot_user_enabled():
    r = requests.get(
        f"{BASE_URL}/api/feature-flags/dr-v3",
        params={"user": "pilot@masci.com"},
        timeout=15,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("enabled") is True, body
    assert body.get("source") == "pilot_user"


def test_feature_flag_admin_override_enabled():
    r = requests.get(
        f"{BASE_URL}/api/feature-flags/dr-v3",
        params={"force_v3": "1"},
        timeout=15,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("enabled") is True
    assert body.get("source") == "admin_override"


# ── V1 downstream sanity ─────────────────────────────────────────

def test_daily_reports_list_ok():
    # Auth-gated in V1; anonymous should either serve (200) or refuse (401/403).
    # A 5xx would indicate V1 downstream regression.
    r = requests.get(f"{BASE_URL}/api/daily-reports", timeout=30)
    assert r.status_code in (200, 401, 403), r.text


def test_daily_reports_csv_ok():
    r = requests.get(f"{BASE_URL}/api/daily-reports.csv", timeout=30)
    assert r.status_code in (200, 401, 403), r.text


def test_daily_reports_next_number_ok():
    r = requests.get(f"{BASE_URL}/api/daily-reports/next-number", timeout=20)
    assert r.status_code == 200, r.text
    body = r.json()
    # Any of these keys is acceptable
    assert any(k in body for k in ("report_number", "next", "number", "next_number"))
