"""
test_iter395_governance.py · Phase 11.4 · DLS Governance + CSV.

Backend regression for iter395:
  • Four governance detectors (ASSIGNMENT_STUCK, WAIT_THRESHOLD_EXCEEDED,
    BREAKDOWN_ACTIVE, NON_STANDARD_TRANSITION_PATTERN) fire correctly
    against seeded iter392 data.
  • Findings endpoint is read-gated by any portal token (anon = 401).
  • Three CSV endpoints (assignments / state-events / haul-cycles)
    return well-formed CSV with the expected header and rows.
  • CSV endpoints are dispatch+admin only (anon = 401).
  • Tenant isolation is honored everywhere.
"""
from __future__ import annotations

import csv
import io
import json
import os
import time
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


def _anon_status(method: str, path: str) -> int:
    req = urllib.request.Request(
        f"{API}{path}", method=method,
        headers={"User-Agent": "Mozilla/5.0 (iter395 anon test)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


@pytest.fixture(scope="module")
def tenant_id() -> str:
    return f"iter395-{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="module")
def hdrs(tenant_id: str) -> dict:
    return {"X-Tenant-Id": tenant_id, "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def seeded_assignments(hdrs: dict) -> dict:
    """Create one assignment per detector path, ensure timestamps are
    far enough in the past that thresholds with `5 min` floor still
    fire by backdating via direct Mongo writes after creation."""
    out: dict = {}

    # A · "Stuck": ASSIGNED state, never transitioned past it.
    r = requests.post(f"{API}/dispatch/assignments", headers=hdrs, timeout=15,
                      json={"truck_id": "T-STUCK", "driver_id": "drv-stuck"})
    out["stuck"] = r.json()["assignment"]

    # B · "Waiting": ASSIGNED -> ENROUTE -> AT_LOAD_SITE -> WAITING.
    r = requests.post(f"{API}/dispatch/assignments", headers=hdrs, timeout=15,
                      json={"truck_id": "T-WAIT", "driver_id": "drv-wait"})
    wait_id = r.json()["assignment"]["id"]
    for step in ("ENROUTE_TO_LOAD", "AT_LOAD_SITE", "WAITING"):
        body = {"to_state": step}
        if step == "WAITING":
            body["wait_reason"] = "WAITING_ON_PLANT"
        requests.post(f"{API}/dispatch/assignments/{wait_id}/transition",
                      headers=hdrs, json=body, timeout=10)
    out["wait"] = wait_id

    # C · "Breakdown": ASSIGNED -> BREAKDOWN.
    r = requests.post(f"{API}/dispatch/assignments", headers=hdrs, timeout=15,
                      json={"truck_id": "T-BREAK", "driver_id": "drv-break"})
    brk_id = r.json()["assignment"]["id"]
    requests.post(f"{API}/dispatch/assignments/{brk_id}/transition",
                  headers=hdrs, json={"to_state": "BREAKDOWN"}, timeout=10)
    out["breakdown"] = brk_id

    # D · "Non-standard pattern": one truck, ≥3 non-standard transitions
    # (jumps that don't match the preferred graph).
    r = requests.post(f"{API}/dispatch/assignments", headers=hdrs, timeout=15,
                      json={"truck_id": "T-NONSTD", "driver_id": "drv-nonstd"})
    nstd_id = r.json()["assignment"]["id"]
    # Walk: ASSIGNED -> DUMPING -> LOADING -> ARRIVED_JOB
    # Each of those is non-standard from its predecessor.
    for step in ("DUMPING", "LOADING", "ARRIVED_JOB"):
        requests.post(f"{API}/dispatch/assignments/{nstd_id}/transition",
                      headers=hdrs, json={"to_state": step,
                                          "correction_reason": "test"}, timeout=10)
    out["non_standard"] = nstd_id

    # Give Mongo a beat (writes are async; thresholds compare ISO strings).
    time.sleep(0.5)
    return out


# ════════════════════════════════════════════════════════════════════
# 1. Findings endpoint — RBAC + four detectors
# ════════════════════════════════════════════════════════════════════
def test_findings_anon_rejected():
    code = _anon_status("GET", "/dispatch/governance/findings")
    assert code == 401


def test_findings_all_four_detectors_fire(hdrs, seeded_assignments):
    # Use very low thresholds so every seeded row trips its detector.
    r = requests.get(
        f"{API}/dispatch/governance/findings",
        headers=hdrs,
        params={
            "stuck_threshold": 0,
            "wait_threshold": 0,
            "non_standard_window": 60,
            "non_standard_min": 2,
        },
        timeout=15,
    )
    assert r.status_code == 200, r.text
    j = r.json()
    counts = j["counts"]
    # Sanity: every detector saw at least its seeded fixture.
    assert counts["ASSIGNMENT_STUCK"] >= 1
    assert counts["WAIT_THRESHOLD_EXCEEDED"] >= 1
    assert counts["BREAKDOWN_ACTIVE"] >= 1
    assert counts["NON_STANDARD_TRANSITION_PATTERN"] >= 1
    kinds = {f["kind"] for f in j["findings"]}
    assert kinds == {
        "ASSIGNMENT_STUCK", "WAIT_THRESHOLD_EXCEEDED",
        "BREAKDOWN_ACTIVE", "NON_STANDARD_TRANSITION_PATTERN",
    }


def test_findings_default_thresholds_are_quiet_for_fresh_seed(hdrs, seeded_assignments):
    """At default thresholds (30/20/120 min) freshly seeded data is too
    young to fire ASSIGNMENT_STUCK or WAIT_THRESHOLD. BREAKDOWN and the
    non-standard pattern are time-window aware but should still fire
    since the assignments live forever in BREAKDOWN."""
    r = requests.get(
        f"{API}/dispatch/governance/findings",
        headers=hdrs,
        timeout=15,
    )
    assert r.status_code == 200
    j = r.json()
    # Breakdown is always active until cleared, so it MUST fire.
    assert j["counts"]["BREAKDOWN_ACTIVE"] >= 1
    # Stuck + wait need time-in-state ≥ 30/20 min — too young here.
    assert j["counts"]["ASSIGNMENT_STUCK"] == 0
    assert j["counts"]["WAIT_THRESHOLD_EXCEEDED"] == 0


def test_findings_wait_carries_reason(hdrs, seeded_assignments):
    r = requests.get(
        f"{API}/dispatch/governance/findings",
        headers=hdrs,
        params={"wait_threshold": 0, "stuck_threshold": 0},
        timeout=15,
    )
    waits = [f for f in r.json()["findings"]
             if f["kind"] == "WAIT_THRESHOLD_EXCEEDED" and f["truck_id"] == "T-WAIT"]
    assert len(waits) == 1
    assert waits[0]["wait_reason"] == "WAITING_ON_PLANT"
    assert waits[0]["minutes_waiting"] >= 0


def test_findings_non_standard_pattern_samples(hdrs, seeded_assignments):
    r = requests.get(
        f"{API}/dispatch/governance/findings",
        headers=hdrs,
        params={"non_standard_min": 2, "non_standard_window": 60},
        timeout=15,
    )
    nstd = [f for f in r.json()["findings"]
            if f["kind"] == "NON_STANDARD_TRANSITION_PATTERN"
            and f["truck_id"] == "T-NONSTD"]
    assert len(nstd) == 1
    assert nstd[0]["count_in_window"] >= 2
    assert isinstance(nstd[0]["samples"], list)


def test_findings_tenant_isolated(hdrs, seeded_assignments):
    other = {"X-Tenant-Id": f"iter395-other-{uuid.uuid4().hex[:6]}"}
    r = requests.get(f"{API}/dispatch/governance/findings", headers=other, timeout=10)
    assert r.status_code == 200
    j = r.json()
    assert j["counts"]["total"] == 0


# ════════════════════════════════════════════════════════════════════
# 2. CSV endpoints
# ════════════════════════════════════════════════════════════════════
def test_csv_anon_rejected():
    assert _anon_status("GET", "/dispatch/exports/assignments.csv") == 401
    assert _anon_status("GET", "/dispatch/exports/state-events.csv") == 401
    assert _anon_status("GET", "/dispatch/exports/haul-cycles.csv") == 401


def _read_csv(text: str):
    reader = csv.reader(io.StringIO(text.lstrip("\ufeff")))
    rows = list(reader)
    return rows[0], rows[1:]


def test_csv_assignments_well_formed(hdrs, seeded_assignments):
    r = requests.get(
        f"{API}/dispatch/exports/assignments.csv",
        headers=hdrs, timeout=15,
    )
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    header, rows = _read_csv(r.text)
    # Must include canonical fields from iter392.
    for col in ("assignment_id", "tenant_id", "truck_id",
                "current_state", "transitions_count", "non_standard_count"):
        assert col in header
    # All 4 seeded assignments must appear.
    truck_ids = {r[header.index("truck_id")] for r in rows}
    assert {"T-STUCK", "T-WAIT", "T-BREAK", "T-NONSTD"}.issubset(truck_ids)


def test_csv_state_events_well_formed(hdrs, seeded_assignments):
    r = requests.get(
        f"{API}/dispatch/exports/state-events.csv?limit=200",
        headers=hdrs, timeout=15,
    )
    assert r.status_code == 200
    header, rows = _read_csv(r.text)
    assert "from_state" in header and "to_state" in header
    assert "standard" in header and "warning_tag" in header
    # At least one non-standard row from the T-NONSTD fixture.
    std_idx = header.index("standard")
    non_std = [row for row in rows if row[std_idx] == "false"]
    assert non_std, "expected at least one non-standard row in CSV"


def test_csv_state_events_non_standard_only_filter(hdrs, seeded_assignments):
    r = requests.get(
        f"{API}/dispatch/exports/state-events.csv?non_standard_only=true&limit=200",
        headers=hdrs, timeout=15,
    )
    assert r.status_code == 200
    header, rows = _read_csv(r.text)
    std_idx = header.index("standard")
    assert all(row[std_idx] == "false" for row in rows)


def test_csv_haul_cycles_well_formed(hdrs):
    """Cycles only materialize on COMPLETE — create a happy-path
    assignment that completes, then verify it shows up."""
    r0 = requests.post(
        f"{API}/dispatch/assignments", headers=hdrs, timeout=15,
        json={"truck_id": "T-CYC-395", "driver_id": "drv-cyc-395"},
    )
    aid = r0.json()["assignment"]["id"]
    for step in ("ENROUTE_TO_LOAD", "AT_LOAD_SITE", "LOADING", "LOADED",
                 "ENROUTE_TO_JOB", "ARRIVED_JOB", "DUMPING", "COMPLETE"):
        requests.post(
            f"{API}/dispatch/assignments/{aid}/transition",
            headers=hdrs, json={"to_state": step}, timeout=10,
        )
    rc = requests.get(
        f"{API}/dispatch/exports/haul-cycles.csv?truck_id=T-CYC-395",
        headers=hdrs, timeout=15,
    )
    assert rc.status_code == 200
    header, rows = _read_csv(rc.text)
    assert "total_seconds" in header and "transitions" in header
    truck_idx = header.index("truck_id")
    matched = [r for r in rows if r[truck_idx] == "T-CYC-395"]
    assert len(matched) == 1


def test_csv_tenant_isolated(seeded_assignments):
    other = {"X-Tenant-Id": f"iter395-empty-{uuid.uuid4().hex[:6]}"}
    r = requests.get(
        f"{API}/dispatch/exports/assignments.csv", headers=other, timeout=10,
    )
    assert r.status_code == 200
    header, rows = _read_csv(r.text)
    # Header still present, rows empty.
    assert "assignment_id" in header
    assert rows == []
