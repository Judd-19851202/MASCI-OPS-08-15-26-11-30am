"""
test_iter396_convergence.py · Phase 11.5 · DLS Convergence.

Backend regression for iter396:
  • The new `project_numbers` filter on `/governance/findings` is honored.
  • Cross-tenant + filter combinations remain isolated.
  • Truck-level NON_STANDARD_TRANSITION_PATTERN findings are dropped
    from project-filtered responses (PM scope is project-scoped, not
    truck-scoped).
"""
from __future__ import annotations

import os
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


@pytest.fixture(scope="module")
def tenant_id() -> str:
    return f"iter396-{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="module")
def hdrs(tenant_id: str) -> dict:
    return {"X-Tenant-Id": tenant_id, "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def seeded(hdrs: dict) -> dict:
    """Seed three projects: A, B, and an unrelated C. Mix of BREAKDOWN
    + WAITING so multiple finding kinds fire."""
    pa = f"PROJ-A-{uuid.uuid4().hex[:6]}"
    pb = f"PROJ-B-{uuid.uuid4().hex[:6]}"
    pc = f"PROJ-C-{uuid.uuid4().hex[:6]}"

    def _create(truck, project):
        r = requests.post(
            f"{API}/dispatch/assignments", headers=hdrs, timeout=10,
            json={
                "truck_id": truck, "driver_id": f"drv-{truck}",
                "project_number": project,
            },
        )
        return r.json()["assignment"]["id"]

    # A: project A, BREAKDOWN
    a_id = _create("T-A1", pa)
    requests.post(f"{API}/dispatch/assignments/{a_id}/transition",
                  headers=hdrs, json={"to_state": "BREAKDOWN"}, timeout=10)

    # B: project B, WAITING with reason
    b_id = _create("T-B1", pb)
    for st in ("ENROUTE_TO_LOAD", "AT_LOAD_SITE"):
        requests.post(f"{API}/dispatch/assignments/{b_id}/transition",
                      headers=hdrs, json={"to_state": st}, timeout=10)
    requests.post(f"{API}/dispatch/assignments/{b_id}/transition",
                  headers=hdrs,
                  json={"to_state": "WAITING", "wait_reason": "WAITING_ON_DUMP"},
                  timeout=10)

    # C: unrelated project, BREAKDOWN — should NOT appear when filter=A,B
    c_id = _create("T-C1", pc)
    requests.post(f"{API}/dispatch/assignments/{c_id}/transition",
                  headers=hdrs, json={"to_state": "BREAKDOWN"}, timeout=10)

    return {"pa": pa, "pb": pb, "pc": pc}


def test_project_filter_includes_only_listed_projects(hdrs, seeded):
    r = requests.get(
        f"{API}/dispatch/governance/findings",
        headers=hdrs,
        params={
            "project_numbers": f"{seeded['pa']},{seeded['pb']}",
            "stuck_threshold": 0, "wait_threshold": 0,
        },
        timeout=15,
    )
    assert r.status_code == 200, r.text
    j = r.json()
    projects = {f.get("project_number") for f in j["findings"]}
    # Only A + B may appear; unrelated C must NOT.
    assert seeded["pc"] not in projects
    assert seeded["pa"] in projects
    assert seeded["pb"] in projects


def test_project_filter_drops_truck_level_pattern(hdrs):
    """NON_STANDARD_TRANSITION_PATTERN has no project_number — when
    a project filter is applied, those findings must be dropped."""
    # Create a truck on no specific project that generates non-std hits
    other_tenant = {"X-Tenant-Id": f"iter396-pat-{uuid.uuid4().hex[:6]}",
                    "Content-Type": "application/json"}
    r0 = requests.post(
        f"{API}/dispatch/assignments", headers=other_tenant, timeout=10,
        json={"truck_id": "T-PAT", "driver_id": "drv-pat", "project_number": ""},
    )
    aid = r0.json()["assignment"]["id"]
    for step in ("DUMPING", "LOADING", "ARRIVED_JOB"):
        requests.post(f"{API}/dispatch/assignments/{aid}/transition",
                      headers=other_tenant,
                      json={"to_state": step, "correction_reason": "x"},
                      timeout=10)
    # Without filter: pattern fires
    r1 = requests.get(
        f"{API}/dispatch/governance/findings", headers=other_tenant,
        params={"non_standard_min": 2, "non_standard_window": 60},
        timeout=10,
    )
    assert any(f["kind"] == "NON_STANDARD_TRANSITION_PATTERN"
               for f in r1.json()["findings"])
    # With project filter pointing to a project that has no rows: pattern dropped
    r2 = requests.get(
        f"{API}/dispatch/governance/findings", headers=other_tenant,
        params={
            "non_standard_min": 2, "non_standard_window": 60,
            "project_numbers": "DOES-NOT-EXIST",
        },
        timeout=10,
    )
    kinds = {f["kind"] for f in r2.json()["findings"]}
    assert "NON_STANDARD_TRANSITION_PATTERN" not in kinds
    assert r2.json()["counts"]["total"] == 0


def test_empty_project_filter_returns_full(hdrs, seeded):
    """An empty / whitespace-only project_numbers parameter must be a
    no-op (not a 'filter to zero projects')."""
    r = requests.get(
        f"{API}/dispatch/governance/findings",
        headers=hdrs,
        params={"project_numbers": "  ", "stuck_threshold": 0, "wait_threshold": 0},
        timeout=10,
    )
    assert r.status_code == 200
    j = r.json()
    projects = {f.get("project_number") for f in j["findings"]}
    assert seeded["pa"] in projects
    assert seeded["pb"] in projects
    assert seeded["pc"] in projects
