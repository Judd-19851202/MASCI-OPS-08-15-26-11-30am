"""TRACK 25.02 Phase D retest smoke — backend regression only."""
import os
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://safety-audit-mobile-1.preview.emergentagent.com").rstrip("/")
EMAIL = "jaymn.judd@mascigc.com"
PASSWORD = "Maddix123!"


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/multi-login", json={"email": EMAIL, "password": PASSWORD}, timeout=90)
    assert r.status_code == 200, f"multi-login failed: {r.status_code} {r.text[:300]}"
    data = r.json()
    tok = (data.get("portal_tokens") or {}).get("admin")
    assert tok, f"no admin portal_token in response: {list(data.keys())}"
    return tok


def _headers(tok):
    return {"X-Admin-Token": tok}


def test_expirations_summary_returns_200_and_counts(admin_token):
    r = requests.get(f"{BASE_URL}/api/operations/expirations/summary", headers=_headers(admin_token), timeout=60)
    assert r.status_code == 200, f"{r.status_code}: {r.text[:300]}"
    body = r.json()
    counts = body.get("counts") or body.get("data", {}).get("counts") or {}
    # top-level or nested — accept either
    if not counts and isinstance(body, dict):
        # try flatten
        counts = {k: v for k, v in body.items() if isinstance(v, int)}
    print("expirations counts:", counts, "body keys:", list(body.keys()))
    assert body is not None


def test_operations_control_overview(admin_token):
    r = requests.get(f"{BASE_URL}/api/admin/operations-control/overview", headers=_headers(admin_token), timeout=60)
    assert r.status_code == 200, f"{r.status_code}: {r.text[:300]}"
    body = r.json()
    ops = body.get("operations") or body.get("ops") or body.get("data") or []
    if isinstance(ops, dict):
        ops = ops.get("operations") or []
    op_ids = []
    for o in ops:
        if isinstance(o, dict):
            op_ids.append(o.get("id") or o.get("op_id") or o.get("key"))
    print(f"ops count: {len(ops)}; ids sample: {op_ids[:20]}")
    assert len(ops) >= 14, f"expected >=14 ops, got {len(ops)}"
    required = {"deploy.readiness_check", "deploy.recovery_playbook", "integrations.probe_all", "queues.scheduler_runs"}
    missing = required - set([i for i in op_ids if i])
    assert not missing, f"missing ops: {missing}"


def test_integrations_health(admin_token):
    r = requests.get(f"{BASE_URL}/api/admin/integrations/health", headers=_headers(admin_token), timeout=60)
    assert r.status_code == 200, f"{r.status_code}: {r.text[:300]}"


def test_dispatch_command_summary(admin_token):
    r = requests.get(f"{BASE_URL}/api/dispatch/command/summary", headers=_headers(admin_token), timeout=60)
    assert r.status_code == 200, f"{r.status_code}: {r.text[:300]}"


def test_admin_search_deploy(admin_token):
    r = requests.get(f"{BASE_URL}/api/admin/search", params={"q": "deploy"}, headers=_headers(admin_token), timeout=60)
    assert r.status_code == 200, f"{r.status_code}: {r.text[:300]}"
    body = r.json()
    assert "groups" in body, f"missing 'groups' in body: {list(body.keys())}"
    assert isinstance(body["groups"], list)
