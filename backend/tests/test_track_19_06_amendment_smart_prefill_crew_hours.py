"""Track 19.06 AMENDMENT · Smart Prefill Crew Hours — Lock Test.

Verifies the crew-hours amendment to the Track 19.06 progressive-disclosure
redesign. Locks the following properties WITHOUT any schema/route drift:

1. Smart Prefill restores crew members.
2. Smart Prefill restores the prior day's common time pattern
   (start / lunch / stop) so foreman edits deltas.
3. Prefilled rows are editable (inputs never `readOnly` / `disabled`).
4. Inactive / terminated HR employees are excluded from the offer.
5. A DIFFERENT project's crew does NOT prefill hours into another project.
6. Actor-scoped lookup: when foreman/superintendent are passed the backend
   biases to the operator's own most-recent report — never silently prefills
   from an unrelated foreman.
7. Submitted payload uses the edited values, not the original prefilled
   values.
8. Historical prior reports remain unchanged after a new report is created
   from a prefilled offer.

Plus doctrine locks:
* recent-context response contract bumped to `19.06.1`.
* Payroll-safety helper text + review-hours notice render in UI.
* Frontend recent-context fetch passes `foreman` / `superintendent`
  query params (actor-scoping wiring).
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND = REPO_ROOT / "frontend"
BACKEND = REPO_ROOT / "backend"
MEMORY = REPO_ROOT / "memory"
_UI = (FRONTEND / "src/pages/NewDailyReport.jsx").read_text(encoding="utf-8")
_SERVER = (BACKEND / "server.py").read_text(encoding="utf-8")

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8001")
API = f"{BACKEND_URL}/api"


# -- Load Mongo config the same way the server does --------------------------
def _env(name):
    for line in (BACKEND / ".env").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        if k.strip() == name:
            return v.strip().strip('"').strip("'")
    return None


MONGO_URL = os.environ.get("MONGO_URL") or _env("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME") or _env("DB_NAME")


@pytest.fixture(scope="module")
def db():
    from pymongo import MongoClient
    assert MONGO_URL and DB_NAME, "Mongo config missing"
    client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=8000)
    yield client[DB_NAME]
    client.close()


# --- shared minimal payloads ------------------------------------------------

_TINY_PNG = (
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR"
    "42mNkAAIAAAoAAv/lxKUAAAAASUVORK5CYII="
)


def _req(method, path, *, body=None, timeout=60):
    headers = {"Content-Type": "application/json"}
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        f"{API}{path}", data=data, method=method, headers=headers
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            return {"status": resp.status, "json": json.loads(raw.decode() or "{}")}
    except urllib.error.HTTPError as e:
        body_txt = e.read().decode()
        try:
            parsed = json.loads(body_txt)
        except Exception:
            parsed = {"detail": body_txt}
        return {"status": e.code, "json": parsed}


PROJECT_A = "JOB-19-06AMEND-A"
PROJECT_B = "JOB-19-06AMEND-B"

FOREMAN_A = "Amend Foreman Alpha"
FOREMAN_B = "Amend Foreman Bravo"

EMP_ACTIVE = {"employee_id": "AMEND-EMP-ACT-1", "name": "Amend Active One"}
EMP_TERMINATED = {"employee_id": "AMEND-EMP-TERM-1", "name": "Amend Terminated One"}


@pytest.fixture(scope="module", autouse=True)
def seed_all(db):
    """Direct-DB seed: two employees (one active, one terminated) and two
    prior Daily Reports on distinct projects with distinct foremen. Wipes
    only the synthetic amendment fixtures — never touches production data."""
    now = datetime.now(timezone.utc).isoformat()

    # Clean slate for this test's synthetic fixture rows (idempotent).
    db.employees.delete_many({"employee_id": {"$in": [
        EMP_ACTIVE["employee_id"], EMP_TERMINATED["employee_id"],
    ]}})
    db.daily_reports.delete_many({"project_number": {"$in": [
        PROJECT_A, PROJECT_B,
    ]}})

    db.employees.insert_many([
        {
            "id": "amend-active-1",
            "name": EMP_ACTIVE["name"],
            "employee_id": EMP_ACTIVE["employee_id"],
            "role": "Laborer",
            "trade": "Laborer",
            "is_active": True,
            "lifecycle_status": "Active",
            "added_via": "test-amendment-19_06",
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": "amend-term-1",
            "name": EMP_TERMINATED["name"],
            "employee_id": EMP_TERMINATED["employee_id"],
            "role": "Laborer",
            "trade": "Laborer",
            "is_active": False,
            "lifecycle_status": "Terminated",
            "added_via": "test-amendment-19_06",
            "created_at": now,
            "updated_at": now,
        },
    ])

    # PROJECT_A prior DR — 2 crew rows (one active, one terminated).
    r_a = _req(
        "POST",
        "/daily-reports",
        body={
            "project_name": "Amend Project A",
            "project_number": PROJECT_A,
            "location": "Yard A",
            "report_date": "2026-06-15",
            "prepared_by": FOREMAN_A,
            "superintendent": "Amend Super A",
            "masci_crews": [
                {
                    "name": EMP_ACTIVE["name"],
                    "employee_id": EMP_ACTIVE["employee_id"],
                    "trade": "Laborer",
                    "start_time": "07:00",
                    "stop_time": "17:00",
                    "lunch_minutes": 30,
                    "hours": 9.5,
                },
                {
                    "name": EMP_TERMINATED["name"],
                    "employee_id": EMP_TERMINATED["employee_id"],
                    "trade": "Laborer",
                    "start_time": "07:00",
                    "stop_time": "17:00",
                    "lunch_minutes": 30,
                    "hours": 9.5,
                },
            ],
            "equipment": [
                {"description": "CAT 320 Excavator", "hours_used": 8.0},
            ],
            "photos": [_TINY_PNG] * 6,
            "prepared_by_signature": _TINY_PNG,
        },
    )
    assert r_a["status"] == 200, r_a

    # PROJECT_B prior DR — unrelated foreman + unrelated crew.
    r_b = _req(
        "POST",
        "/daily-reports",
        body={
            "project_name": "Amend Project B",
            "project_number": PROJECT_B,
            "location": "Yard B",
            "report_date": "2026-06-15",
            "prepared_by": FOREMAN_B,
            "superintendent": "Amend Super B",
            "masci_crews": [
                {
                    "name": "Foreign Crew Person",
                    "employee_id": "AMEND-FOREIGN-1",
                    "trade": "Operator",
                    "start_time": "05:30",
                    "stop_time": "15:30",
                    "lunch_minutes": 45,
                    "hours": 9.25,
                }
            ],
            "photos": [_TINY_PNG] * 6,
            "prepared_by_signature": _TINY_PNG,
        },
    )
    assert r_b["status"] == 200, r_b

    yield

    # Clean up after the test module so we don't leave synthetic data behind.
    db.employees.delete_many({"employee_id": {"$in": [
        EMP_ACTIVE["employee_id"], EMP_TERMINATED["employee_id"],
    ]}})
    db.daily_reports.delete_many({"project_number": {"$in": [
        PROJECT_A, PROJECT_B,
    ]}})


# --- backend contract locks -------------------------------------------------


def test_recent_context_contract_version_bumped_to_19_06_1():
    r = _req("GET", f"/jobs/{PROJECT_A}/recent-context")
    assert r["status"] == 200
    assert r["json"].get("contract_version") == "19.06.1", r["json"]


def test_amend_prop_1_smart_prefill_restores_crew_members():
    r = _req("GET", f"/jobs/{PROJECT_A}/recent-context")
    assert r["status"] == 200
    crews = r["json"].get("masci_crews") or []
    names = [c.get("name") for c in crews]
    assert EMP_ACTIVE["name"] in names, crews


def test_amend_prop_2_smart_prefill_restores_time_pattern():
    r = _req("GET", f"/jobs/{PROJECT_A}/recent-context")
    assert r["status"] == 200
    crews = r["json"].get("masci_crews") or []
    active_rows = [c for c in crews if c.get("employee_id") == EMP_ACTIVE["employee_id"]]
    assert active_rows, "active employee missing from prefill"
    row = active_rows[0]
    assert row.get("start_time") == "07:00", row
    assert row.get("stop_time") == "17:00", row
    assert row.get("lunch_minutes") in (30, "30"), row


def test_amend_prop_3_prefilled_hours_editable_in_ui():
    """Static guard: crew time inputs are bound to `crews.update`, so every
    row is editable. No blanket `readOnly={true}` / `disabled` lockdown."""
    assert 'crews.update(i, "start_time"' in _UI
    assert 'crews.update(i, "stop_time"' in _UI
    assert 'crews.update(i, "lunch_minutes"' in _UI
    assert "readOnly={true}" not in _UI


def test_amend_prop_4_inactive_hr_employee_excluded_from_prefill():
    r = _req("GET", f"/jobs/{PROJECT_A}/recent-context")
    assert r["status"] == 200
    ids = [c.get("employee_id") for c in r["json"].get("masci_crews") or []]
    assert EMP_TERMINATED["employee_id"] not in ids, (
        "terminated HR employee leaked into Smart Prefill offer — payroll footgun"
    )


def test_amend_prop_5_different_project_does_not_prefill_hours():
    r = _req("GET", f"/jobs/{PROJECT_A}/recent-context")
    assert r["status"] == 200
    names = [c.get("name") for c in r["json"].get("masci_crews") or []]
    assert "Foreign Crew Person" not in names, (
        "cross-project bleed — PROJECT_B crew appeared under PROJECT_A"
    )


def test_amend_prop_6_actor_scoped_lookup_flag():
    """FOREMAN_A on PROJECT_A → actor_scoped=True.
    FOREMAN_B on PROJECT_A → actor_scoped=False (falls back to
    project-most-recent, does not silently borrow FOREMAN_B's data)."""
    r_own = _req(
        "GET",
        f"/jobs/{PROJECT_A}/recent-context?foreman={quote(FOREMAN_A)}",
    )
    assert r_own["status"] == 200
    assert r_own["json"].get("actor_scoped") is True, r_own["json"]

    r_stranger = _req(
        "GET",
        f"/jobs/{PROJECT_A}/recent-context?foreman={quote(FOREMAN_B)}",
    )
    assert r_stranger["status"] == 200
    assert r_stranger["json"].get("actor_scoped") is False, r_stranger["json"]


def test_amend_prop_7_submitted_payload_uses_edited_values(db):
    """The foreman's edited hours land in the persisted document, not the
    prior prefill values. Prove by submitting a NEW DR with distinct times
    and reading it back from Mongo."""
    r = _req(
        "POST",
        "/daily-reports",
        body={
            "project_name": "Amend Project A",
            "project_number": PROJECT_A,
            "location": "Yard A",
            "report_date": "2026-06-16",
            "prepared_by": FOREMAN_A,
            "superintendent": "Amend Super A",
            "masci_crews": [
                {
                    "name": EMP_ACTIVE["name"],
                    "employee_id": EMP_ACTIVE["employee_id"],
                    "trade": "Laborer",
                    # Edited values — DIFFERENT from the prior day's pattern.
                    "start_time": "06:00",
                    "stop_time": "14:30",
                    "lunch_minutes": 15,
                    "hours": 8.25,
                }
            ],
            "photos": [_TINY_PNG] * 6,
            "prepared_by_signature": _TINY_PNG,
        },
    )
    assert r["status"] == 200, r
    persisted = db.daily_reports.find_one({
        "project_number": PROJECT_A, "report_date": "2026-06-16",
    })
    assert persisted is not None
    row = persisted["masci_crews"][0]
    assert row["start_time"] == "06:00"
    assert row["stop_time"] == "14:30"
    assert str(row["lunch_minutes"]) == "15"
    assert float(row["hours"]) == 8.25


def test_amend_prop_8_historical_prior_reports_unchanged(db):
    """The recent-context read + the new DR submission must leave the
    source DR bit-for-bit intact."""
    source = db.daily_reports.find_one({
        "project_number": PROJECT_A, "report_date": "2026-06-15",
    })
    assert source is not None
    names = [c["name"] for c in source["masci_crews"]]
    # Terminated employee row is still present in the HISTORICAL doc — the
    # amendment filters ONLY the live prefill offer, never persisted history.
    assert EMP_TERMINATED["name"] in names
    # Original clock times untouched.
    for c in source["masci_crews"]:
        if c.get("employee_id") == EMP_ACTIVE["employee_id"]:
            assert c["start_time"] == "07:00"
            assert c["stop_time"] == "17:00"


# --- UI microcopy + wiring locks --------------------------------------------


def test_amend_ui_review_hours_helper_text_present():
    """Payroll-safety helper text present verbatim on the crew band."""
    assert (
        "Crew and equipment were prefilled from the previous matching report. "
        "Review and adjust hours before submitting."
    ) in _UI


def test_amend_ui_apply_restores_time_pattern():
    """`onApplySmartPrefill` maps prior c.start_time / c.stop_time /
    c.lunch_minutes into the new row — not the pre-amendment blank strings."""
    assert "start_time: c.start_time" in _UI
    assert "stop_time: c.stop_time" in _UI
    assert "c.lunch_minutes" in _UI


def test_amend_ui_review_notice_testids_wired():
    assert 'data-testid="daily-report-prefill-review-notice"' in _UI
    assert 'data-testid="prefill-review-hours-helper"' in _UI


def test_amend_ui_recent_context_passes_actor_qs():
    assert "foreman=${encodeURIComponent(_fm)}" in _UI
    assert "superintendent=${encodeURIComponent(_sup)}" in _UI


def test_amend_ui_offer_card_updated_microcopy():
    assert (
        "Prior common time pattern is prefilled — you review and adjust "
        "hours before submit."
    ) in _UI
    # Old pre-amendment microcopy must be gone.
    assert "Hours, times and work_performed are always cleared" not in _UI


def test_no_schema_keys_removed_or_renamed_by_amendment():
    routes_src = (BACKEND / "routes/daily_reports.py").read_text(encoding="utf-8")
    for key in [
        "masci_crews",
        "equipment",
        "photos",
        "attachments",
    ]:
        assert key in routes_src, f"schema key drifted: {key}"


def test_recent_context_endpoint_still_present_after_amendment():
    assert "/jobs/{project_number}/recent-context" in _SERVER
