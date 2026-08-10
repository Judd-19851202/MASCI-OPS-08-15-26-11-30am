from __future__ import annotations

import os
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


def test_recent_context_requires_authenticated_pm_or_admin_access():
    signed_out = requests.get(f"{BASE_URL}/api/jobs/OD-100/recent-context", timeout=120)
    assert signed_out.status_code == 401

    login = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": "jaymn.judd@mascigc.com", "password": "Maddix123!", "rememberMe": True},
        headers={"Content-Type": "application/json"},
        timeout=120,
    )
    login.raise_for_status()
    body = login.json()
    authed = requests.get(
        f"{BASE_URL}/api/jobs/OD-100/recent-context",
        headers={
            "X-Admin-Token": body["portal_tokens"]["admin"],
            "X-Directory-Token": body["session_token"],
        },
        timeout=120,
    )
    authed.raise_for_status()
    payload = authed.json()
    assert str(payload["contract_version"]).startswith("19.")
    assert "masci_crews" in payload
