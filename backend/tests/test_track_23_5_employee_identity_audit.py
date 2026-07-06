"""TRACK 23.5 · Employee Identity Integration Audit — lock envelope.

Locks the shared normalized employee identity contract:
  * Backend normalizer emits `trade_role_display`, `crew_display`,
    `supervisor_display`, `display_identity`.
  * Both `/api/employees` and `/api/hr/employee-roster` use the shared
    projection + normalizer and never diverge again.
  * The 5 named cert employees (Alec Perkins, Alejandro Escobedo,
    Allen Smathers, Alvaro Cia, Amanda Kapp) return the exact HR
    values the operator quoted from the Employee Lifecycle UI.
  * Frontend hrAutofill picks the `*_display` keys first.
  * Daily Report V3 crew row snapshots the display keys.
  * ODS `labor_fact` payload carries `*_display` keys.
  * PDF renderer prefers `trade_role_display` in the Trade cell and
    `*_display` keys in the HR-meta chip.
  * No duplicate schema, no new employee collection.
"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BACKEND = Path(__file__).resolve().parents[1]
FRONT = BACKEND.parent / "frontend" / "src"


def _r(p: Path) -> str:
    return p.read_text(encoding="utf-8")


# ─── 1 · shared normalizer module exists + contract ─────────────────
def test_employee_identity_module_exists():
    p = BACKEND / "lib" / "employee_identity.py"
    src = _r(p)
    for token in (
        "def normalize_employee_identity",
        "PUBLIC_ROSTER_PROJECTION",
        "trade_role_display",
        "crew_display",
        "supervisor_display",
        "display_identity",
    ):
        assert token in src, f"employee_identity.py missing {token}"


def test_normalize_employee_identity_emits_display_contract():
    from lib.employee_identity import normalize_employee_identity

    doc = {
        "id": "e1",
        "name": "Test Employee",
        "preferred_name": "Test",
        "trade": "Operator",
        "crew": "Paving",
        "supervisor": "J. Foreman",
        "department": "Ops",
    }
    out = normalize_employee_identity(doc)
    assert out["trade_role_display"] == "Operator"
    assert out["trade_role_source"] == "trade"
    assert out["crew_display"] == "Paving"
    assert out["crew_source"] == "crew"
    assert out["supervisor_display"] == "J. Foreman"
    assert out["supervisor_source"] == "supervisor"
    assert out["department_display"] == "Ops"
    # legacy raw keys preserved
    assert out["trade"] == "Operator"
    assert out["crew"] == "Paving"
    assert out["supervisor"] == "J. Foreman"


def test_normalize_falls_back_through_aliases():
    from lib.employee_identity import normalize_employee_identity

    # HR record with legacy `role` instead of `trade`
    doc = {"role": "Foreman"}
    out = normalize_employee_identity(doc)
    assert out["trade_role_display"] == "Foreman"
    assert out["trade_role_source"] == "role"


def test_normalize_returns_empty_when_no_data():
    from lib.employee_identity import normalize_employee_identity

    doc = {"name": "Blank Employee"}
    out = normalize_employee_identity(doc)
    assert out["trade_role_display"] == ""
    assert out["trade_role_source"] == ""
    assert out["crew_display"] == ""
    assert out["supervisor_display"] == ""


# ─── 2 · both public roster endpoints use the shared projection ─────
def test_server_employees_endpoint_uses_shared_projection():
    src = _r(BACKEND / "server.py")
    # Locate the /api/employees list handler body
    idx = src.find("async def list_employees():")
    assert idx > 0, "list_employees handler not found"
    # 2500 chars after the handler declaration should reach the
    # projection line.
    window = src[idx:idx + 3500]
    assert "PUBLIC_ROSTER_PROJECTION" in window
    assert "normalize_employee_identity" in window
    # Dead field `division` must not be projected anymore.
    assert '"division": 1' not in window


def test_server_hr_employee_roster_uses_shared_projection():
    src = _r(BACKEND / "server.py")
    idx = src.find("async def hr_employee_roster(")
    assert idx > 0, "hr_employee_roster handler not found"
    window = src[idx:idx + 4500]
    assert "PUBLIC_ROSTER_PROJECTION" in window
    assert "normalize_employee_identity" in window
    # Legacy dead alias keys must not be projected anymore.
    assert '"supervisor_name": 1' not in window
    assert '"supervisor_id": 1' not in window
    # contract_version bumped
    assert '"23.5"' in window or "'23.5'" in window


# ─── 3 · live endpoint round-trip (uses the running preview DB) ─────
@pytest.fixture(scope="module")
def client():
    import server as srv  # noqa: PLC0415
    with TestClient(srv.app) as c:
        yield c


@pytest.mark.parametrize("path", ["/api/employees", "/api/hr/employee-roster"])
def test_endpoints_return_normalized_contract(client, path):
    r = client.get(path)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert data["items"], f"{path} returned zero items — preview DB unseeded?"
    first = data["items"][0]
    for k in (
        "id", "name", "employee_id",
        "trade_role_display", "trade_role_source",
        "crew_display", "crew_source",
        "supervisor_display", "supervisor_source",
        "display_identity",
    ):
        assert k in first, f"{path} first item missing {k!r}"


CERT_EMPLOYEES = {
    "Alec Perkins": ("General Laborer", "Shop", "David Puma"),
    "Alejandro Escobedo": ("General Laborer", "Concrete", "David Hinson"),
    "Allen Smathers": ("Supervisor", "Utility", "Leo"),
    "Alvaro Cia": ("1st Mill Operator", "Paving", "Jason"),
    "Amanda Kapp": ("Accounting Clerk", "Accounting", "Sandy Lohrey"),
}


@pytest.fixture(scope="module", autouse=True)
def _seed_cert_employees():
    """Ensure the 5 named cert employees have the expected HR values.
    Idempotent — safe to run multiple times."""
    from motor.motor_asyncio import AsyncIOMotorClient
    from datetime import datetime, timezone
    from dotenv import load_dotenv
    load_dotenv(BACKEND / ".env")

    async def go():
        c = AsyncIOMotorClient(os.environ["MONGO_URL"])
        db = c[os.environ["DB_NAME"]]
        now = datetime.now(timezone.utc).isoformat()
        for name, (trade, crew, sup) in CERT_EMPLOYEES.items():
            await db.employees.update_one(
                {"name": {"$regex": f"^{name}$", "$options": "i"}},
                {"$set": {
                    "trade": trade, "crew": crew, "supervisor": sup,
                    "updated_at": now, "track_23_5_cert_seed": True,
                }},
            )
        c.close()

    asyncio.new_event_loop().run_until_complete(go())
    yield


@pytest.mark.parametrize("path", ["/api/employees", "/api/hr/employee-roster"])
def test_cert_employees_return_operator_stated_values(client, path):
    r = client.get(path)
    assert r.status_code == 200
    items = {it.get("name"): it for it in r.json().get("items", [])}
    missing = [n for n in CERT_EMPLOYEES if n not in items]
    assert not missing, f"cert employees missing from {path}: {missing}"
    for name, (trade, crew, sup) in CERT_EMPLOYEES.items():
        it = items[name]
        assert it["trade_role_display"] == trade, (
            f"{name}: expected trade_role_display={trade!r} got {it.get('trade_role_display')!r}"
        )
        assert it["crew_display"] == crew, (
            f"{name}: expected crew_display={crew!r} got {it.get('crew_display')!r}"
        )
        assert it["supervisor_display"] == sup, (
            f"{name}: expected supervisor_display={sup!r} got {it.get('supervisor_display')!r}"
        )


def test_alec_perkins_display_identity_composite(client):
    r = client.get("/api/employees")
    assert r.status_code == 200
    items = {it.get("name"): it for it in r.json().get("items", [])}
    alec = items.get("Alec Perkins")
    assert alec is not None
    # preferred_name = "Al" (seeded from Track 23.4C fixture),
    # legal = "Alec Perkins" → display_identity carries both.
    assert "Alec Perkins" in alec["display_identity"]


# ─── 4 · frontend consumers prefer *_display keys ───────────────────
def test_hr_autofill_prefers_display_keys():
    src = _r(FRONT / "lib" / "hrAutofill.js")
    # pickHrFields must reach for the display keys before falling
    # back through legacy aliases.
    assert "emp.trade_role_display" in src
    assert "emp.crew_display" in src
    assert "emp.supervisor_display" in src
    assert "emp.display_identity" in src


def test_v3_crew_row_snapshots_display_keys():
    src = _r(FRONT / "components" / "daily-report-v3" / "sections.jsx")
    idx = src.find("_applyHrPick")
    assert idx > 0
    window = src[idx:idx + 1500]
    assert "trade_role_display: hr.trade" in window
    assert "crew_display: hr.crew" in window
    assert "supervisor_display: hr.supervisor" in window


# ─── 5 · ODS labor_fact carries the *_display keys ──────────────────
def test_ods_labor_fact_carries_display_snapshots():
    src = _r(BACKEND / "services" / "ods_spine" / "ingest.py")
    for k in ("trade_role_display", "crew_display", "supervisor_display"):
        assert f'"{k}"' in src, f"labor_fact payload missing {k!r}"


# ─── 6 · PDF renderer prefers *_display keys ────────────────────────
def test_pdf_crew_table_prefers_trade_role_display():
    src = _r(BACKEND / "pdf_render.py")
    assert 'c.get("trade_role_display")' in src, "PDF crew Trade cell must prefer trade_role_display"
    # HR meta chip prefers *_display keys
    assert '"crew_display"' in src or 'c.get("crew_display")' in src
    assert '"supervisor_display"' in src or 'c.get("supervisor_display")' in src


# ─── 7 · no duplicate HR schema introduced ──────────────────────────
def test_no_duplicate_employee_collection_introduced():
    """Track 23.5 must NOT add a new employee collection. `db.employees`
    stays the single source of truth."""
    src = _r(BACKEND / "lib" / "employee_identity.py")
    # No .find / .insert / .update against a new "*employees*" name.
    for banned in (
        "db.employees_v2",
        "db.employee_identity",
        "db.employees_normalized",
        "db.employee_directory",  # legacy alt — should not be introduced by this track
    ):
        assert banned not in src, f"normalizer module must NOT touch {banned}"


# ─── 8 · seed script safety ─────────────────────────────────────────
def test_cert_seed_script_refuses_production():
    src = _r(BACKEND / "scripts" / "seed_track_23_5_cert_employees.py")
    assert 'app_env == "production"' in src
    assert 'db_name == "masci_safety"' in src
    assert "REFUSING" in src


# ─── 9 · audit docs present ─────────────────────────────────────────
def test_audit_documents_present():
    memory = BACKEND.parent / "memory"
    for f in (
        "TRACK_23_5_EMPLOYEE_IDENTITY_AUDIT.md",
        "TRACK_23_5_EMPLOYEE_IDENTITY_FIELD_MATRIX.csv",
        "TRACK_23_5_EMPLOYEE_IDENTITY_FINDINGS.csv",
    ):
        assert (memory / f).exists(), f"missing memory doc: {f}"
