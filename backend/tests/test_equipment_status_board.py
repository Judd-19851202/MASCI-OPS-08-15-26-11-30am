"""Equipment Status Board — verifies aggregation logic per unit."""
import os
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pytest as _pytest  # noqa: E402
try:
    from tests.conftest import URL  # noqa: E402
except ImportError:
    URL = ''
if not URL:
    _pytest.skip(
        'tests.conftest.URL unavailable · live-HTTP test skipped (parity-lock safe).',
        allow_module_level=True,
    )


def _admin_token():
    r = requests.post(
        f"{URL}/api/admin/login",
        json={"password": os.environ.get("ADMIN_PASSWORD", "MASCI1982!")},
        timeout=10,
    )
    assert r.status_code == 200, r.text
    return r.json()["token"]


def _hdr():
    return {"X-Admin-Token": _admin_token()}


def test_status_board_returns_summary_shape():
    r = requests.get(f"{URL}/api/equipment-status-board", headers=_hdr(), timeout=10)
    assert r.status_code == 200
    body = r.json()
    assert "summary" in body
    assert "units" in body
    assert "generated_at" in body
    s = body["summary"]
    for k in ("total_units", "out_of_service", "never_inspected", "stale_7d"):
        assert k in s


def test_status_board_aggregates_inspection():
    """Submit a real Equipment Pre-Op with a FAIL → confirm the unit shows up
    on the board with last_status=fail and the failing item in top_failures."""
    suffix = str(int(time.time()))
    unit_label = f"PYTEST-Unit-{suffix}"
    payload = {
        "project_name": "T5824 - SR 46 (W 1ST ST.)",
        "project_number": "24-06",
        "location": "Status Board Test",
        "inspection_date": "2026-02-26",
        "inspection_time": "08:00",
        "operator_name": "Status Board Pytest",
        "equipment_type": "Excavator",
        "equipment_unit": unit_label,
        "checklist": {
            "Fluids & Leaks": {
                "Engine oil level": {"status": "fail", "note": "Sight glass empty for 2 days"},
                "Hydraulic fluid level": {"status": "pass", "note": ""},
            }
        },
        "fail_count": 1,
        "pass_count": 1,
        "na_count": 0,
        "out_of_service": "Yes",
    }
    r = requests.post(f"{URL}/api/equipment-inspections", json=payload, timeout=15)
    assert r.status_code == 200, r.text
    rid = r.json()["id"]

    try:
        b = requests.get(
            f"{URL}/api/equipment-status-board", headers=_hdr(), timeout=10
        ).json()
        match = next(
            (u for u in b["units"] if u["equipment_unit"] == unit_label), None
        )
        assert match is not None, f"Unit {unit_label} missing from status board"
        assert match["last_status"] == "fail"
        assert match["fail_count_14d"] >= 1
        assert match["inspection_count"] == 1
        assert match["last_inspected_days_ago"] in (0, 1)
        items = [t["item"] for t in match["top_failures"]]
        assert "Engine oil level" in items
    finally:
        requests.delete(
            f"{URL}/api/equipment-inspections/{rid}", headers=_hdr(), timeout=10
        )
        # Also remove the auto-saved unit so we don't pollute future runs
        units = requests.get(
            f"{URL}/api/equipment-units?equipment_type=Excavator",
            headers=_hdr(),
            timeout=10,
        ).json()
        # No DELETE endpoint for units yet — just leave the empty unit; it'll
        # show as never_inspected after the inspection is gone, which is fine.
        # (When the user wants, we can add a /api/equipment-units/{id} DELETE.)
        _ = units
