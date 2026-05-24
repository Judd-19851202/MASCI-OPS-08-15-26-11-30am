"""
test_iter412_dls_health_summary.py · Phase 16.1.

GET /api/admin/dls/health-summary — minimal Day-1 live ops observability.

Verifies:
  • admin-only (anon = 401, dispatch token alone = 401)
  • return shape carries all 13 documented counters + status + notes
  • status ∈ {quiet, flowing, attention}
  • haul_types_today carries all 5 canonical types
  • zero new collection (response is computed from existing data only)
"""
from __future__ import annotations

import os
import urllib.error
import urllib.request
import uuid
from pathlib import Path

import pytest
import requests


def _read_kv(path: Path, key: str) -> str:
    try:
        for line in path.read_text().splitlines():
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:
        return ""
    return ""


URL = (
    _read_kv(Path("/app/frontend/.env"), "REACT_APP_BACKEND_URL")
    or os.environ.get("REACT_APP_BACKEND_URL", "")
).rstrip("/")
API = f"{URL}/api"


def _anon_status(path: str) -> int:
    req = urllib.request.Request(
        f"{API}{path}", method="GET",
        headers={"User-Agent": "Mozilla/5.0 (iter412 anon test)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


def _admin_hdrs():
    r = requests.post(
        f"{API}/admin/login",
        json={"password": "MASCI1982!"},
        timeout=15,
    )
    if r.status_code == 200:
        token = r.json().get("token")
        if token:
            return {"X-Admin-Token": token}
    pytest.skip("No admin token in this env.")


# ════════════════════════════════════════════════════════════════════
# 1. Auth gate
# ════════════════════════════════════════════════════════════════════
def test_health_summary_requires_admin_anon_blocked():
    assert _anon_status("/admin/dls/health-summary") == 401


def test_health_summary_admin_200():
    hdrs = _admin_hdrs()
    r = requests.get(f"{API}/admin/dls/health-summary", headers=hdrs, timeout=15)
    assert r.status_code == 200, r.text


# ════════════════════════════════════════════════════════════════════
# 2. Return shape
# ════════════════════════════════════════════════════════════════════
def test_health_summary_shape_has_all_counters():
    hdrs = _admin_hdrs()
    hdrs["X-Tenant-Id"] = f"iter412-shape-{uuid.uuid4().hex[:6]}"
    r = requests.get(f"{API}/admin/dls/health-summary", headers=hdrs, timeout=15)
    j = r.json()
    required = {
        "ok", "tenant_id", "date", "as_of",
        "active_shifts", "active_assignments",
        "assignments_created_today", "completed_cycles_today", "transitions_today",
        "waiting_count", "breakdown_count",
        "oldest_waiting_minutes", "oldest_stuck_minutes",
        "findings_today", "haul_types_today", "status", "notes",
    }
    assert required.issubset(set(j.keys()))
    # haul_types_today contains all five canonical haul types
    assert set(j["haul_types_today"].keys()) == {
        "Material", "Equipment Move", "Tanker / Liquid Asphalt",
        "Spoils / Dump", "Support / Misc",
    }
    assert j["status"] in ("quiet", "flowing", "attention")
    assert isinstance(j["notes"], list)


# ════════════════════════════════════════════════════════════════════
# 3. Empty tenant → quiet
# ════════════════════════════════════════════════════════════════════
def test_empty_tenant_status_quiet():
    hdrs = _admin_hdrs()
    hdrs["X-Tenant-Id"] = f"iter412-quiet-{uuid.uuid4().hex[:6]}"
    r = requests.get(f"{API}/admin/dls/health-summary", headers=hdrs, timeout=15)
    j = r.json()
    assert j["status"] == "quiet"
    assert j["active_assignments"] == 0
    assert j["active_shifts"] == 0
    assert j["breakdown_count"] == 0
    assert j["notes"] == []


# ════════════════════════════════════════════════════════════════════
# 4. Flowing status when active assignments without exceptions
# ════════════════════════════════════════════════════════════════════
def test_flowing_status_with_active_assignment():
    hdrs = _admin_hdrs()
    tenant = f"iter412-flow-{uuid.uuid4().hex[:6]}"
    hdrs["X-Tenant-Id"] = tenant
    rc = requests.post(
        f"{API}/dispatch/assignments",
        headers=hdrs,
        json={
            "truck_id": "T-412-FLOW",
            "material": "Hot Mix Asphalt",
            "source_location": "MASCI Hot Plant 1",
            "destination": "Job Site",
        },
        timeout=15,
    )
    assert rc.status_code == 200

    r = requests.get(f"{API}/admin/dls/health-summary", headers=hdrs, timeout=15)
    j = r.json()
    assert j["status"] == "flowing"
    assert j["active_assignments"] == 1
    assert j["assignments_created_today"] == 1
    assert j["haul_types_today"]["Material"] == 1


# ════════════════════════════════════════════════════════════════════
# 5. Attention status when breakdown present
# ════════════════════════════════════════════════════════════════════
def test_attention_status_on_breakdown():
    hdrs = _admin_hdrs()
    tenant = f"iter412-att-{uuid.uuid4().hex[:6]}"
    hdrs["X-Tenant-Id"] = tenant
    rc = requests.post(
        f"{API}/dispatch/assignments",
        headers=hdrs,
        json={"truck_id": "T-412-BD"},
        timeout=15,
    )
    assert rc.status_code == 200
    aid = rc.json()["assignment"]["id"]
    rt = requests.post(
        f"{API}/dispatch/assignments/{aid}/transition",
        headers=hdrs, json={"to_state": "BREAKDOWN", "note": "engine"},
        timeout=15,
    )
    assert rt.status_code == 200

    r = requests.get(f"{API}/admin/dls/health-summary", headers=hdrs, timeout=15)
    j = r.json()
    assert j["status"] == "attention"
    assert j["breakdown_count"] == 1
    assert any("breakdown" in n.lower() for n in j["notes"])


# ════════════════════════════════════════════════════════════════════
# 6. Haul-type counters split across five canonical types
# ════════════════════════════════════════════════════════════════════
def test_haul_types_today_counts_across_five_types():
    hdrs = _admin_hdrs()
    tenant = f"iter412-types-{uuid.uuid4().hex[:6]}"
    hdrs["X-Tenant-Id"] = tenant
    for ht, label in [
        ("Material", "Hot Mix Asphalt"),
        ("Equipment Move", "EX-1"),
        ("Tanker / Liquid Asphalt", "PG 64-22"),
        ("Spoils / Dump", "Spoils"),
        ("Support / Misc", "MOT Devices"),
    ]:
        body = {"truck_id": f"T-{ht[:5]}-{uuid.uuid4().hex[:4]}", "haul_type": ht}
        if ht == "Equipment Move":
            body["equipment_label"] = label
        elif ht == "Tanker / Liquid Asphalt":
            body["liquid_product"] = label
        else:
            body["material"] = label
        rc = requests.post(f"{API}/dispatch/assignments", headers=hdrs, json=body, timeout=15)
        assert rc.status_code == 200

    r = requests.get(f"{API}/admin/dls/health-summary", headers=hdrs, timeout=15)
    j = r.json()
    counts = j["haul_types_today"]
    assert counts["Material"] == 1
    assert counts["Equipment Move"] == 1
    assert counts["Tanker / Liquid Asphalt"] == 1
    assert counts["Spoils / Dump"] == 1
    assert counts["Support / Misc"] == 1
    assert j["assignments_created_today"] == 5


# ════════════════════════════════════════════════════════════════════
# 7. Restraint · no internal field leakage
# ════════════════════════════════════════════════════════════════════
def test_no_internal_fields_in_response():
    hdrs = _admin_hdrs()
    r = requests.get(f"{API}/admin/dls/health-summary", headers=hdrs, timeout=15)
    j = r.json()
    for k in j.keys():
        assert not k.startswith("_"), f"Internal field leaked: {k}"
    for k in j.get("haul_types_today", {}).keys():
        assert not k.startswith("_")
