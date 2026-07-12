"""Sprint A · DocExp-60/90 + Future-Day Dispatch regression (2026-06-08)."""
from __future__ import annotations
import os
import pytest
import requests

BASE = os.environ.get("REACT_APP_BACKEND_URL", "https://backup-forensics.preview.emergentagent.com").rstrip("/")


@pytest.fixture(scope="module")
def admin_token() -> str:
    r = requests.post(f"{BASE}/api/auth/multi-login",
        json={"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"}, timeout=30)
    return r.json()["portal_tokens"]["admin"]


def test_expirations_summary_5_bands(admin_token):
    r = requests.get(f"{BASE}/api/operations/expirations/summary",
        headers={"X-Admin-Token": admin_token}, timeout=30)
    assert r.status_code == 200
    body = r.json()
    for k in ("expired", "in_30", "in_60", "in_90", "healthy"):
        assert k in body["counts"]
        assert k in body["bands"]


def test_expirations_summary_band_sample_limit(admin_token):
    r = requests.get(f"{BASE}/api/operations/expirations/summary",
        headers={"X-Admin-Token": admin_token}, timeout=30).json()
    for k, lst in r["bands"].items():
        assert len(lst) <= 25, f"band {k} sample exceeded 25"


@pytest.mark.parametrize("bucket", ["today", "tomorrow", "upcoming", "all"])
def test_dispatch_by_day_buckets(admin_token, bucket):
    r = requests.get(f"{BASE}/api/operations/dispatch/by-day?bucket={bucket}",
        headers={"X-Admin-Token": admin_token}, timeout=30)
    assert r.status_code == 200
    body = r.json()
    assert body["bucket"] == bucket
    assert "assignments" in body and "coverage" in body and "conflicts" in body


def test_dispatch_by_day_invalid_bucket(admin_token):
    r = requests.get(f"{BASE}/api/operations/dispatch/by-day?bucket=yesterday",
        headers={"X-Admin-Token": admin_token}, timeout=30)
    assert r.status_code in (400, 422)


def test_admin_strict_negative():
    r = requests.get(f"{BASE}/api/operations/expirations/summary",
        headers={"X-Admin-Token": "not-real"}, timeout=30)
    assert r.status_code in (401, 403)
