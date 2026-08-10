from __future__ import annotations

import os
import time
from pathlib import Path

import requests


def _kv(path: str, key: str) -> str:
    try:
        for line in Path(path).read_text().splitlines():
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"')
    except Exception:
        return ""
    return ""


BASE_URL = (_kv("/app/frontend/.env", "REACT_APP_BACKEND_URL") or os.environ.get("REACT_APP_BACKEND_URL", "")).rstrip("/")


def _admin_headers() -> dict[str, str]:
    login = None
    for _ in range(3):
        login = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": "jaymn.judd@mascigc.com", "password": "Maddix123!", "rememberMe": True},
            headers={"Content-Type": "application/json"},
            timeout=120,
        )
        if login.ok:
            break
        time.sleep(1)
    assert login is not None
    login.raise_for_status()
    body = login.json()
    return {
        "X-Admin-Token": body["portal_tokens"]["admin"],
        "X-Directory-Token": body["session_token"],
    }


def test_occ_health_uses_real_production_certification_signal():
    resp = requests.get(
        f"{BASE_URL}/api/admin/occ/health",
        headers=_admin_headers(),
        timeout=120,
    )
    resp.raise_for_status()
    sections = resp.json().get("sections") or []
    identity = next(section for section in sections if section.get("id") == "identity_security")
    production = next(card for card in identity.get("cards") or [] if card.get("id") == "production_certification")

    assert production["status"] != "UNVERIFIABLE"
    assert "Platform band:" in production["summary"]
    assert (production.get("evidence") or {}).get("platform_band") in {"amber", "yellow", "green", "red", "critical", "warning"}