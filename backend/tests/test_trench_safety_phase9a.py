"""Phase 9A — Reporting & Analytics Command Center tests.

Validates the 9 read-only reports and the CSV exporter. Reports are
computed against the live registry — these tests check structural
contracts (keys present, types correct, filters honoured).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
import requests

_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

API = os.environ.get("TS_API_BASE", "http://localhost:8001")


def _admin_token() -> str:
    pwd = os.environ.get("ADMIN_PASSWORD", "Maddix123!")
    r = requests.post(f"{API}/api/admin/login", json={"password": pwd}, timeout=15)
    r.raise_for_status()
    return r.json()["token"]


def _h(token: str) -> dict:
    return {"X-Admin-Token": token}


@pytest.fixture(scope="module")
def token():
    return _admin_token()


REPORT_IDS = [
    "executive", "road-plate", "inspection-compliance", "repair-backlog",
    "holds", "utilization", "missing-data", "project-assets", "activity",
]


def test_report_list(token):
    r = requests.get(f"{API}/api/trench-safety/reports/list", headers=_h(token), timeout=15)
    r.raise_for_status()
    items = r.json().get("reports", [])
    ids = {it["id"] for it in items}
    for rid in REPORT_IDS:
        assert rid in ids


@pytest.mark.parametrize("rid", REPORT_IDS)
def test_each_report_returns_shape(token, rid):
    r = requests.get(f"{API}/api/trench-safety/reports/{rid}", headers=_h(token), timeout=20)
    r.raise_for_status()
    data = r.json()
    # Every report includes filters + generated_at
    assert "filters" in data
    assert "generated_at" in data


def test_executive_includes_health_and_ratios(token):
    r = requests.get(f"{API}/api/trench-safety/reports/executive", headers=_h(token), timeout=15)
    r.raise_for_status()
    data = r.json()
    for k in ("totals", "ratios", "activity_trends"):
        assert k in data
    assert "total_assets" in data["totals"]
    assert "asset_availability_pct" in data["ratios"]
    # 7d / 30d / 90d trends
    for w in ("last_7d", "last_30d", "last_90d"):
        assert w in data["activity_trends"]


def test_road_plate_report_forces_type(token):
    # Even when caller filter mentions another type, road-plate report
    # forces asset_type=Road Plate.
    r = requests.get(
        f"{API}/api/trench-safety/reports/road-plate",
        headers=_h(token), params={"asset_type": "Trench Box"}, timeout=15,
    )
    r.raise_for_status()
    data = r.json()
    assert data["filters"]["asset_type"] == "Road Plate"
    assert "capacity_inventory" in data
    assert "trend_30d" in data


def test_filter_propagation(token):
    r = requests.get(
        f"{API}/api/trench-safety/reports/utilization",
        headers=_h(token), params={"asset_type": "Trench Box"}, timeout=15,
    )
    r.raise_for_status()
    data = r.json()
    assert data["filters"]["asset_type"] == "Trench Box"
    # Utilization breakdown shows the filtered type with > 0 entries
    by_type = data.get("by_asset_type", {})
    assert "Trench Box" in by_type


def test_missing_data_returns_counts_and_affected(token):
    r = requests.get(f"{API}/api/trench-safety/reports/missing-data", headers=_h(token), timeout=15)
    r.raise_for_status()
    data = r.json()
    assert "counts" in data
    assert "affected" in data
    # Counts are ints
    for v in data["counts"].values():
        assert isinstance(v, int)


def test_activity_report_has_three_windows(token):
    r = requests.get(f"{API}/api/trench-safety/reports/activity", headers=_h(token), timeout=15)
    r.raise_for_status()
    by = r.json().get("by_window", {})
    for w in ("last_7d", "last_30d", "last_90d"):
        assert w in by


def test_export_csv_streams(token):
    for rid in REPORT_IDS:
        r = requests.get(
            f"{API}/api/trench-safety/reports/{rid}/export.csv",
            headers=_h(token), timeout=20,
        )
        r.raise_for_status()
        assert r.headers["content-type"].startswith("text/csv")
        assert "filename=" in (r.headers.get("content-disposition") or "")
        body = r.text
        assert "MASCI Trench Safety Report" in body
        assert rid in body  # report id appears in the title row
        assert "Filters" in body  # filter section always appended


def test_export_unknown_report_404(token):
    r = requests.get(
        f"{API}/api/trench-safety/reports/does-not-exist/export.csv",
        headers=_h(token), timeout=10,
    )
    assert r.status_code == 404
