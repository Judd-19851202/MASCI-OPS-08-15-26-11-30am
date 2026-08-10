from __future__ import annotations

from pathlib import Path

import pytest
import requests


def _backend_url() -> str:
    env = Path("/app/frontend/.env")
    for line in env.read_text().splitlines():
        if line.startswith("REACT_APP_BACKEND_URL="):
            return line.split("=", 1)[1].strip().rstrip("/")
    raise RuntimeError("REACT_APP_BACKEND_URL missing")


BASE_URL = _backend_url()
API = f"{BASE_URL}/api"
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"
HR_EMAIL = "cert.hr@example.com"
HR_PASSWORD = "CertProof2026!"


@pytest.fixture(scope="session")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="session")
def admin_token(session):
    response = session.post(
        f"{API}/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "rememberMe": True},
        timeout=120,
    )
    assert response.status_code == 200, response.text[:400]
    token = (response.json().get("portal_tokens") or {}).get("admin")
    assert token, "admin portal token missing from multi-login response"
    return token


@pytest.fixture(scope="session")
def hr_token(session):
    response = session.post(
        f"{API}/hr/login",
        json={"email": HR_EMAIL, "password": HR_PASSWORD},
        timeout=120,
    )
    assert response.status_code == 200, response.text[:400]
    token = response.json().get("token")
    assert token, "hr token missing"
    return token


def test_field_packet_stays_public(session):
    response = session.get(
        f"{API}/training/packet.pdf",
        params={"track": "field", "lang": "en"},
        timeout=120,
    )
    assert response.status_code == 200, response.text[:300]
    assert response.content[:4] == b"%PDF"


def test_hr_packet_requires_auth(session):
    response = session.get(
        f"{API}/training/packet.pdf",
        params={"track": "hr", "lang": "en"},
        timeout=120,
    )
    assert response.status_code == 401
    assert "HR or Admin login required" in response.text


def test_hr_packet_accepts_hr_token(session, hr_token):
    response = session.get(
        f"{API}/training/packet.pdf",
        params={"track": "hr", "lang": "en"},
        headers={"X-HR-Token": hr_token},
        timeout=120,
    )
    assert response.status_code == 200, response.text[:300]
    assert response.content[:4] == b"%PDF"


def test_hr_packet_accepts_admin_token(session, admin_token):
    response = session.get(
        f"{API}/training/packet.pdf",
        params={"track": "hr", "lang": "en"},
        headers={"X-Admin-Token": admin_token},
        timeout=120,
    )
    assert response.status_code == 200, response.text[:300]
    assert response.content[:4] == b"%PDF"


def test_leadership_packet_is_not_exposed(session):
    response = session.get(
        f"{API}/training/packet.pdf",
        params={"track": "leadership", "lang": "en"},
        timeout=120,
    )
    assert response.status_code == 404
