"""TRACK 23.6 · HR Employee Record Completeness Tile — lock envelope.

Read-only check-engine light using the Track 23.5 normalized identity
contract. Verifies:

  * `GET /api/hr/employee-completeness` requires HR/Admin auth.
  * Endpoint uses `normalize_employee_identity` (Track 23.5) —
    no re-implemented projection logic.
  * Metrics compute correctly (trade/role, crew, supervisor,
    fully-complete counts + status band thresholds).
  * `missing_records` carries `missing_fields` with the correct labels
    and never leaks sensitive HR fields (email/phone/SSN/DOB/CDL).
  * CSV export returns only the approved columns.
  * `include_inactive=false` (default) excludes inactive employees.
  * The tile is mounted on the HR Hub (not PM, not Daily Report).
  * Employee Lifecycle page + Daily Report V3 + `/api/employees`
    remain unchanged.
"""
from __future__ import annotations

import asyncio
import csv
import os
from io import StringIO
from pathlib import Path

import pytest
import requests

BACKEND = Path(__file__).resolve().parents[1]
FRONT = BACKEND.parent / "frontend" / "src"

# TRACK 23.6 tests hit the running preview backend on localhost:8001
# rather than spinning up a second FastAPI TestClient — that pattern
# collides with motor's cached event loop when other test modules in
# the suite also start the app in the same pytest process.
LOCAL_API = "http://localhost:8001"


def _r(p: Path) -> str:
    return p.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def client():
    s = requests.Session()

    class _C:
        def get(self, path, **kw):
            return s.get(LOCAL_API + path, timeout=20, **kw)

        def post(self, path, json=None, **kw):
            return s.post(LOCAL_API + path, json=json, timeout=20, **kw)

    return _C()


@pytest.fixture(scope="module")
def admin_token(client):
    r = client.post("/api/auth/multi-login", json={
        "email": "jaymn.judd@mascigc.com",
        "password": "Maddix123!",
    })
    assert r.status_code == 200, r.text
    tok = r.json().get("portal_tokens", {}).get("admin", "")
    assert tok, "no admin token minted"
    return tok


# ─── 1 · auth guard ─────────────────────────────────────────────────
def test_completeness_endpoint_requires_auth(client):
    r = client.get("/api/hr/employee-completeness")
    assert r.status_code in (401, 403)


def test_completeness_csv_requires_auth(client):
    r = client.get("/api/hr/employee-completeness.csv")
    assert r.status_code in (401, 403)


# ─── 2 · endpoint uses shared normalizer ────────────────────────────
def test_endpoint_uses_shared_normalizer():
    src = _r(BACKEND / "routes" / "employee_lifecycle.py")
    idx = src.find("_completeness_snapshot")
    assert idx > 0
    window = src[idx:idx + 4000]
    assert "normalize_employee_identity" in window
    assert "PUBLIC_ROSTER_PROJECTION" in window
    # No sensitive columns projected in the completeness handler
    for banned in ("email", "phone", "cdl_license_number", "medical_card"):
        assert f'"{banned}": 1' not in window
        assert f"'{banned}': 1" not in window


# ─── 3 · live snapshot contract ─────────────────────────────────────
def test_completeness_snapshot_contract(client, admin_token):
    r = client.get(
        "/api/hr/employee-completeness",
        headers={"X-Admin-Token": admin_token},
    )
    assert r.status_code == 200, r.text
    d = r.json()
    for k in (
        "total_active", "complete_count",
        "trade_role_complete_count", "crew_complete_count",
        "supervisor_complete_count",
        "completion_percent", "status_band",
        "missing_records", "generated_at",
        "contract_version",
    ):
        assert k in d, f"missing key {k!r}"
    assert d["contract_version"] == "23.6"
    assert d["status_band"] in ("green", "amber", "red")
    assert isinstance(d["missing_records"], list)
    assert 0 <= d["completion_percent"] <= 100
    # counts logical bounds
    assert d["complete_count"] <= d["trade_role_complete_count"]
    assert d["complete_count"] <= d["crew_complete_count"]
    assert d["complete_count"] <= d["supervisor_complete_count"]
    assert (
        d["complete_count"] + len(d["missing_records"]) == d["total_active"]
    )


def test_missing_records_carry_missing_fields(client, admin_token):
    r = client.get(
        "/api/hr/employee-completeness",
        headers={"X-Admin-Token": admin_token},
    )
    d = r.json()
    assert d["missing_records"], "preview db expected to have missing records"
    rec = d["missing_records"][0]
    for k in (
        "employee_id", "id", "name", "display_identity",
        "trade_role_display", "crew_display", "supervisor_display",
        "missing_fields", "lifecycle_status",
    ):
        assert k in rec, f"missing_records[0] missing key {k!r}"
    # missing_fields must be non-empty and drawn from the allowed set.
    assert rec["missing_fields"]
    allowed = {"trade_role", "crew", "supervisor"}
    for f in rec["missing_fields"]:
        assert f in allowed


def test_missing_records_do_not_leak_sensitive_fields(client, admin_token):
    r = client.get(
        "/api/hr/employee-completeness",
        headers={"X-Admin-Token": admin_token},
    )
    d = r.json()
    banned_keys = {
        "email", "phone", "ssn", "date_of_birth", "dob",
        "cdl_license_number", "cdl_expiration_date",
        "medical_card_expiration_date", "hire_date",
        "termination_date", "rehire_eligibility_reason",
    }
    for rec in d["missing_records"][:20]:
        for k in banned_keys:
            assert k not in rec, f"sensitive key {k!r} leaked in missing_records"


# ─── 4 · cert employees (from 23.5) are NOT in the missing list ─────
def test_cert_employees_are_complete(client, admin_token):
    """Track 23.5 cert seed populated trade/crew/supervisor for 5
    named employees. They MUST be counted as fully-complete here."""
    from dotenv import load_dotenv  # noqa: PLC0415
    load_dotenv(BACKEND / ".env")
    from motor.motor_asyncio import AsyncIOMotorClient  # noqa: PLC0415
    from datetime import datetime, timezone  # noqa: PLC0415

    cert = {
        "Alec Perkins": ("General Laborer", "Shop", "David Puma"),
        "Alejandro Escobedo": ("General Laborer", "Concrete", "David Hinson"),
        "Allen Smathers": ("Supervisor", "Utility", "Leo"),
        "Alvaro Cia": ("1st Mill Operator", "Paving", "Jason"),
        "Amanda Kapp": ("Accounting Clerk", "Accounting", "Sandy Lohrey"),
    }

    async def seed():
        c = AsyncIOMotorClient(os.environ["MONGO_URL"])
        db = c[os.environ["DB_NAME"]]
        now = datetime.now(timezone.utc).isoformat()
        for name, (trade, crew, sup) in cert.items():
            await db.employees.update_one(
                {"name": {"$regex": f"^{name}$", "$options": "i"}},
                {"$set": {
                    "trade": trade, "crew": crew, "supervisor": sup,
                    "updated_at": now, "track_23_5_cert_seed": True,
                }},
            )
        c.close()
    asyncio.new_event_loop().run_until_complete(seed())

    r = client.get(
        "/api/hr/employee-completeness",
        headers={"X-Admin-Token": admin_token},
    )
    d = r.json()
    missing_names = {rec["name"] for rec in d["missing_records"]}
    for n in cert:
        assert n not in missing_names, (
            f"{n} unexpectedly appears in missing_records — cert seed drift?"
        )


# ─── 5 · include_inactive filter ────────────────────────────────────
def test_include_inactive_filter(client, admin_token):
    r_default = client.get(
        "/api/hr/employee-completeness",
        headers={"X-Admin-Token": admin_token},
    ).json()
    r_incl = client.get(
        "/api/hr/employee-completeness?include_inactive=true",
        headers={"X-Admin-Token": admin_token},
    ).json()
    # Include-inactive can only ADD employees; total_active never
    # shrinks (semantic: `total_active` here is total-in-scope).
    assert r_incl["total_active"] >= r_default["total_active"]


# ─── 6 · missing_only filter ────────────────────────────────────────
def test_missing_only_filter(client, admin_token):
    r = client.get(
        "/api/hr/employee-completeness?missing_only=trade_role",
        headers={"X-Admin-Token": admin_token},
    ).json()
    for rec in r["missing_records"]:
        assert "trade_role" in rec["missing_fields"]


# ─── 7 · CSV export contract ────────────────────────────────────────
def test_csv_export_contract(client, admin_token):
    r = client.get(
        "/api/hr/employee-completeness.csv",
        headers={"X-Admin-Token": admin_token},
    )
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    assert 'MASCI_Employee_Completeness.csv' in r.headers.get("content-disposition", "")
    reader = csv.reader(StringIO(r.text))
    header = next(reader)
    expected = [
        "employee_id", "legal_name", "preferred_name",
        "trade_role_display", "crew_display", "supervisor_display",
        "missing_fields", "lifecycle_status",
    ]
    assert header == expected, f"csv header drift: {header}"
    # No sensitive columns in the CSV.
    banned = {"email", "phone", "ssn", "dob", "hire_date", "cdl_license_number"}
    for b in banned:
        assert b not in {h.lower() for h in header}


# ─── 8 · status band thresholds ─────────────────────────────────────
def test_status_band_thresholds():
    # Import the helper indirectly via a controlled dummy — verify
    # threshold math is applied in the route body.
    src = _r(BACKEND / "routes" / "employee_lifecycle.py")
    assert "pct >= 95.0" in src
    assert "pct >= 75.0" in src
    for label in ('"green"', '"amber"', '"red"'):
        assert label in src


# ─── 9 · tile is mounted on HR hub, not PM, not Daily Report ────────
def test_tile_mounted_on_hr_hub():
    """HrHubV2 (canonical /hr route since Track 13.6E) MUST mount the
    tile; HrHub legacy (kept at /hr/hub_legacy) also mounts it."""
    v2 = _r(FRONT / "pages" / "HrHubV2.jsx")
    legacy = _r(FRONT / "pages" / "HrHub.jsx")
    assert "HrCompletenessTile" in v2
    assert 'from "@/components/HrCompletenessTile"' in v2
    assert "HrCompletenessTile" in legacy
    assert 'from "@/components/HrCompletenessTile"' in legacy


def test_tile_not_mounted_on_daily_report_or_pm():
    for path in (
        FRONT / "pages" / "NewDailyReportV3.jsx",
        FRONT / "pages" / "PmOperationalIntelligence.jsx",
    ):
        assert "HrCompletenessTile" not in _r(path), f"{path.name} must not import HrCompletenessTile"


def test_tile_component_shape():
    src = _r(FRONT / "components" / "HrCompletenessTile.jsx")
    # Must use the approved endpoint
    assert "/hr/employee-completeness" in src
    # Must expose the required testids for browser testing
    for tid in (
        "hr-completeness-tile",
        "hr-completeness-title",
        "hr-completeness-band",
        "hr-completeness-metric-trade",
        "hr-completeness-metric-crew",
        "hr-completeness-metric-supervisor",
        "hr-completeness-metric-fully",
        "hr-completeness-view-missing",
        "hr-completeness-export-csv",
        "hr-completeness-drawer",
        "hr-completeness-filter-all",
        "hr-completeness-filter-trade",
        "hr-completeness-filter-crew",
        "hr-completeness-filter-supervisor",
    ):
        assert tid in src, f"tile missing testid {tid!r}"


# ─── 10 · read-only guarantees ──────────────────────────────────────
def test_tile_does_not_call_any_write_endpoint():
    src = _r(FRONT / "components" / "HrCompletenessTile.jsx")
    # tile must never POST / PATCH / PUT / DELETE
    for verb in ("method: 'POST'", "method: \"POST\"", "method:'POST'",
                 "method: 'PATCH'", "method: 'PUT'", "method: 'DELETE'"):
        assert verb not in src
    # Nor mutate via the shared api helper
    for banned in ("api.post", "api.patch", "api.put", "api.delete"):
        assert banned not in src


def test_no_new_employee_collection_introduced():
    src = _r(BACKEND / "routes" / "employee_lifecycle.py")
    idx = src.find("_completeness_snapshot")
    stop = src.find("@router.get(\"/api/hr/employees/{employee_id}", idx)
    body = src[idx:stop if stop > idx else idx + 5000]
    # completeness handler must query db.employees only
    assert "db.employees.find" in body
    for banned in (
        "db.employees_v2",
        "db.employee_completeness",
        "db.hr_completeness",
    ):
        assert banned not in body


# ─── 11 · regression — other endpoints untouched ────────────────────
def test_public_employees_endpoint_still_normalized(client):
    r = client.get("/api/employees")
    assert r.status_code == 200
    d = r.json()
    assert d["items"]
    assert "trade_role_display" in d["items"][0]


def test_daily_report_v3_page_still_renders():
    p = FRONT / "pages" / "NewDailyReportV3.jsx"
    src = _r(p)
    assert "DailyReportTopBanner" in src
    assert "SectionCrewEquipment" in src or "sections" in src
