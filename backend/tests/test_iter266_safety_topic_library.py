"""
test_iter266_safety_topic_library.py — F2-A · Safety Topic Library MVP

Tests POST /api/safety/library/pack:
  - RBAC: 401 no token, 401 bad safety token, 200 with valid safety, 200 with admin
  - Validation: 400 on empty topics, 400 on bad language, 400 on missing ES content
  - PDF: starts with %PDF-1.4, application/pdf content-type, expected text present
"""
from __future__ import annotations

import os
import re

import pytest
import requests
import urllib.request
import urllib.error
import json as _json


def _raw_post(url, body, headers=None):
    """Bypass conftest's auto-admin-token monkeypatch by using urllib."""
    data = _json.dumps(body).encode("utf-8")
    h = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 pytest-iter266"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=data, headers=h, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, resp.read(), dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read(), dict(e.headers)

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


BASE_URL = _read_env_var("REACT_APP_BACKEND_URL").rstrip("/")
TIMEOUT = 60


def _env(key: str):
    """Read backend/.env for ADMIN_PASSWORD and similar."""
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


# ───────── Fixtures ─────────

@pytest.fixture(scope="session")
def admin_token():
    """Master directory admin via multi-login → portal_tokens.admin"""
    r = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"},
        timeout=TIMEOUT,
    )
    if r.status_code != 200:
        pytest.skip(f"Master admin login failed: {r.status_code} {r.text[:200]}")
    return r.json()["portal_tokens"]["admin"]


@pytest.fixture(scope="session")
def safety_token():
    """Safety user — try seed pw, else self-bootstrap via admin reset."""
    r = requests.post(
        f"{BASE_URL}/api/safety/login",
        json={"email": "safety@mascigc.com", "password": "SafetyTest2026!"},
        timeout=TIMEOUT,
    )
    if r.status_code == 200:
        return r.json()["token"]

    # Self-bootstrap
    pw = _env("ADMIN_PASSWORD") or "MASCI1982!"
    a = requests.post(f"{BASE_URL}/api/admin/login", json={"password": pw}, timeout=TIMEOUT)
    if a.status_code != 200:
        pytest.skip(f"Admin bootstrap login failed: {a.status_code}")
    admin_tok = a.json()["token"]
    users_resp = requests.get(
        f"{BASE_URL}/api/admin/safety-users",
        headers={"X-Admin-Token": admin_tok},
        timeout=TIMEOUT,
    )
    if users_resp.status_code != 200:
        pytest.skip(f"Could not list safety users: {users_resp.status_code}")
    users = users_resp.json()
    users = users if isinstance(users, list) else users.get("items", [])
    target = next((u for u in users if u.get("email") == "safety@mascigc.com"), None)
    if not target:
        pytest.skip("safety@mascigc.com not in directory")
    rp = requests.post(
        f"{BASE_URL}/api/admin/safety-users/{target['id']}/reset-password",
        json={},
        headers={"X-Admin-Token": admin_tok},
        timeout=TIMEOUT,
    )
    if rp.status_code != 200:
        pytest.skip(f"Safety reset failed: {rp.status_code}")
    temp_pw = rp.json().get("temp_password")
    r2 = requests.post(
        f"{BASE_URL}/api/safety/login",
        json={"email": "safety@mascigc.com", "password": temp_pw},
        timeout=TIMEOUT,
    )
    if r2.status_code != 200:
        pytest.skip(f"Safety login after reset failed: {r2.status_code}")
    return r2.json()["token"]


# ───────── Sample payloads ─────────

def _topic_en():
    return {
        "key": "trucking_dump_truck",
        "domain": "trucking",
        "title": "Dump Truck Roll-Over Awareness",
        "severity": "fatal_risk",
        "incident_pattern": "Driver dumps on uneven ground; bed rises, COG shifts, truck rolls.",
        "hazards_reviewed": "Soft ground · Wind load · Incline",
        "discussion_notes": "Always level the truck before raising the bed.\nLook up for power lines.",
        "references_cited": "OSHA 1926.601",
        "action_items": "Check ground · Verify clearance",
    }


def _topic_es():
    return {
        "key": "trucking_dump_truck",
        "domain": "trucking",
        "title": "Conciencia de Vuelco de Camión Volquete",
        "severity": "fatal_risk",
        "incident_pattern": "El conductor descarga en terreno desigual; la caja sube y el camión vuelca.",
        "hazards_reviewed": "Terreno blando · Viento · Inclinación",
        "discussion_notes": "Siempre nivele el camión antes de subir la caja.",
        "references_cited": "OSHA 1926.601",
        "action_items": "Revisar terreno · Verificar líneas eléctricas",
    }


def _valid_body(languages="en", with_es=True):
    body = {"languages": languages, "topics": [{"en": _topic_en(), "es": _topic_es() if with_es else None}]}
    return body


# ───────── RBAC tests ─────────

class TestRBAC:
    def test_no_token_returns_401(self):
        status, body, _h = _raw_post(
            f"{BASE_URL}/api/safety/library/pack", _valid_body()
        )
        assert status == 401, f"Expected 401, got {status}: {body[:200]!r}"

    def test_bad_safety_token_returns_401(self):
        status, body, _h = _raw_post(
            f"{BASE_URL}/api/safety/library/pack",
            _valid_body(),
            headers={"X-Safety-Token": "garbage-token-xyz"},
        )
        assert status == 401, f"Expected 401, got {status}: {body[:200]!r}"

    def test_valid_safety_token_returns_200(self, safety_token):
        r = requests.post(
            f"{BASE_URL}/api/safety/library/pack",
            headers={"X-Safety-Token": safety_token},
            json=_valid_body(),
            timeout=TIMEOUT,
        )
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:300]}"
        assert "application/pdf" in r.headers.get("content-type", "")

    def test_valid_admin_token_returns_200(self, admin_token):
        r = requests.post(
            f"{BASE_URL}/api/safety/library/pack",
            headers={"X-Admin-Token": admin_token},
            json=_valid_body(),
            timeout=TIMEOUT,
        )
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:300]}"
        assert "application/pdf" in r.headers.get("content-type", "")


# ───────── Validation tests ─────────

class TestValidation:
    def test_empty_topics_returns_400(self, safety_token):
        body = {"languages": "en", "topics": []}
        r = requests.post(
            f"{BASE_URL}/api/safety/library/pack",
            headers={"X-Safety-Token": safety_token},
            json=body,
            timeout=TIMEOUT,
        )
        assert r.status_code == 400, f"Expected 400, got {r.status_code}: {r.text[:300]}"

    def test_invalid_language_returns_400(self, safety_token):
        body = _valid_body()
        body["languages"] = "de"
        r = requests.post(
            f"{BASE_URL}/api/safety/library/pack",
            headers={"X-Safety-Token": safety_token},
            json=body,
            timeout=TIMEOUT,
        )
        assert r.status_code == 400, f"Expected 400, got {r.status_code}: {r.text[:300]}"

    def test_both_with_missing_es_returns_400(self, safety_token):
        body = _valid_body(languages="both", with_es=False)
        r = requests.post(
            f"{BASE_URL}/api/safety/library/pack",
            headers={"X-Safety-Token": safety_token},
            json=body,
            timeout=TIMEOUT,
        )
        assert r.status_code == 400, f"Expected 400, got {r.status_code}: {r.text[:300]}"
        # error msg should reference the missing key
        assert "trucking_dump_truck" in r.text or "ES" in r.text.upper() or "missing" in r.text.lower()


# ───────── PDF content tests ─────────

class TestPDFContent:
    def test_pdf_starts_with_magic_bytes_en(self, safety_token):
        r = requests.post(
            f"{BASE_URL}/api/safety/library/pack",
            headers={"X-Safety-Token": safety_token},
            json=_valid_body(languages="en"),
            timeout=TIMEOUT,
        )
        assert r.status_code == 200
        # %PDF-1.x magic bytes
        assert r.content[:5] == b"%PDF-", f"Bad magic: {r.content[:16]!r}"
        assert b"%PDF-1." in r.content[:8]
        # Title metadata is rendered un-compressed in /Title field
        text = r.content.decode("latin-1", errors="ignore")
        assert "MASCI Safety" in text, "MASCI Safety title metadata missing"
        # ReportLab embeds /Producer + /Title — verify pack title metadata
        assert "Topic Pack" in text
        # Single topic, EN → should be 1 page
        pages = len(re.findall(rb"/Type\s*/Page[^s]", r.content))
        assert pages == 1, f"Expected 1 page for EN single-topic, got {pages}"

    def test_pdf_es_only(self, safety_token):
        r = requests.post(
            f"{BASE_URL}/api/safety/library/pack",
            headers={"X-Safety-Token": safety_token},
            json=_valid_body(languages="es"),
            timeout=TIMEOUT,
        )
        assert r.status_code == 200
        assert r.content[:5] == b"%PDF-"
        pages = len(re.findall(rb"/Type\s*/Page[^s]", r.content))
        assert pages == 1, f"Expected 1 page for ES single-topic, got {pages}"

    def test_pdf_both_languages(self, safety_token):
        r = requests.post(
            f"{BASE_URL}/api/safety/library/pack",
            headers={"X-Safety-Token": safety_token},
            json=_valid_body(languages="both"),
            timeout=TIMEOUT,
        )
        assert r.status_code == 200
        assert r.content[:8].startswith(b"%PDF-1.")
        # Both languages → should be ≥ 2 pages
        pages = len(re.findall(rb"/Type\s*/Page[^s]", r.content))
        assert pages >= 2, f"Expected ≥2 pages for 'both', counted {pages}"
