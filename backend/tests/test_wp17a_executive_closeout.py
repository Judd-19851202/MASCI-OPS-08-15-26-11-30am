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
        json={"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD},
        headers={"Content-Type": "application/json"},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return {
        "X-Admin-Token": data["portal_tokens"]["admin"],
        "X-Directory-Token": data["session_token"],
    }


def test_wp17a_kpi_dictionary_contract():
    r = requests.get(f"{BASE_URL}/api/admin/wp17a/kpi-dictionary", headers=_admin_headers(), timeout=30)
    assert r.status_code == 200, r.text[:200]
    body = r.json()
    assert body["status"] == "EXECUTIVE_READY_FOR_APPROVAL"
    assert body["entry_count"] >= 25
    assert isinstance(body["entries"], list)
    first = body["entries"][0]
    for key in [
        "identifier",
        "display_name",
        "category",
        "description",
        "formula",
        "owner",
        "refresh_interval",
        "confidence",
        "validation_status",
        "consumer_portals",
    ]:
        assert key in first["kpi_metadata"], key


def test_wp17a_reconciliation_passes_without_blocking_findings():
    r = requests.get(f"{BASE_URL}/api/admin/wp17a/reconciliation", headers=_admin_headers(), timeout=60)
    assert r.status_code == 200, r.text[:200]
    body = r.json()
    assert body["status"] == "PASS", body
    assert body["blocking_finding_count"] == 0, body
    assert body["runtime_probe_count"] >= 18


def test_wp17a_certification_ready_for_approval():
    r = requests.get(f"{BASE_URL}/api/admin/wp17a/certification", headers=_admin_headers(), timeout=60)
    assert r.status_code == 200, r.text[:200]
    body = r.json()
    assert body["certification_status"] == "EXECUTIVE_READY_FOR_APPROVAL", body
    assert all(body["checks"].values()), body


def test_cluster_capacity_history_exposes_predictive_contract():
    r = requests.get(f"{BASE_URL}/api/cluster/capacity/history?days=30", timeout=30)
    assert r.status_code == 200, r.text[:200]
    body = r.json()
    assert body["ok"] is True
    assert "predictive" in body
    predictive = body["predictive"]
    for key in [
        "daily_growth_rate_mb",
        "weekly_growth_rate_mb",
        "monthly_growth_rate_mb",
        "storage_velocity_mb_per_day",
        "prediction_quality",
        "capacity_risk_level",
        "recommendations",
    ]:
        assert key in predictive, key
    assert body.get("kpi_metadata", {}).get("identifier") == "WP17A-KPI-021-history"


def test_cluster_capacity_current_snapshot_exposes_metadata():
    r = requests.get(f"{BASE_URL}/api/cluster/capacity", timeout=30)
    assert r.status_code == 200, r.text[:200]
    body = r.json()
    assert body["ok"] is True
    assert body.get("kpi_metadata", {}).get("identifier") == "WP17A-KPI-021-current"