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
SUPER_ADMIN_EMAIL = "jaymn.judd@mascigc.com"
SUPER_ADMIN_PASSWORD = "Maddix123!"


def _admin_headers() -> dict[str, str]:
    resp = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD, "rememberMe": True},
        headers={"Content-Type": "application/json"},
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    return {
        "X-Admin-Token": data["portal_tokens"]["admin"],
        "X-Directory-Token": data["session_token"],
    }


def test_pm_operational_kpis_expose_governed_metadata_and_shared_spine():
    headers = _admin_headers()
    pm = requests.get(
        f"{BASE_URL}/api/pm/projects/OD-100/operational-kpis?window=ptd",
        headers=headers,
        timeout=120,
    )
    safety = requests.get(
        f"{BASE_URL}/api/safety/projects/OD-100/safety-kpis?window=ptd",
        headers=headers,
        timeout=120,
    )
    pm.raise_for_status()
    safety.raise_for_status()
    pm_body = pm.json()
    safety_body = safety.json()

    metadata = pm_body.get("kpi_metadata") or {}
    assert metadata.get("page", {}).get("api_endpoint") == "/api/pm/projects/OD-100/operational-kpis"
    assert metadata.get("page", {}).get("formula", {}).get("shared_spine") == "aggregate_project_kpis()"
    assert metadata.get("page", {}).get("owner") == "operations-control"
    sections = metadata.get("sections") or {}
    for key in [
        "labor",
        "equipment",
        "materials",
        "production",
        "delays",
        "safety",
        "intelligence",
        "scheduling_readiness",
        "safety_sources",
    ]:
        assert key in sections

    assert pm_body["safety"] == safety_body["safety"]
    assert pm_body["safety_sources"] == safety_body["safety_sources"]