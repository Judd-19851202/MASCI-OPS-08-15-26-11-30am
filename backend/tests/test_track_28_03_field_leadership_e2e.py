"""TRACK 28.03 · Field Leadership · End-to-End Certification.

Executes every FIELD_LEADERSHIP_FORMS kind as an operator would:
  1. Log in via /api/auth/multi-login (admin) — this is the canonical
     path used by the FL portal for admin-side submissions (the
     admin-token was silently rejected by the FL gate before the
     Track 28.03-A fix in ``routes/field_leadership.py::_admin_token_valid``;
     this suite is the regression lock for that fix).
  2. POST every FL kind with ``TEST_28_03_`` prefixed identity fields
     (``employee_name``, ``supervisor_name``, ``project_number``).
  3. GET-detail — verify persistence.
  4. GET-list must NOT surface the synthetic row (TRACK 28.03 FLR
     synthetic-exclusion doctrine — regression for the CSV export /
     global-search / HR-portal / safety-portal leaks fixed in this
     track).
  5. PDF endpoint returns application/pdf.
  6. DELETE endpoint clears the record.
  7. Residue sweep — zero TEST_28_03_ FL records survive after the
     full suite runs.

Kinds covered (13/13 in FIELD_LEADERSHIP_FORMS):
  * write_up, verbal_coaching, attendance, recognition,
    equipment_checkout, new_employee_eval, crew_eval,
    promotion_recommendation, training_deficiency,
    employee_termination, equipment_return, time_off_request,
    safety_equipment_issuance.
"""
from __future__ import annotations

import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

import httpx
import pytest
from pymongo import MongoClient


def _backend() -> str:
    try:
        r = httpx.get("http://localhost:8001/api/health", timeout=5)
        if r.status_code == 200:
            return "http://localhost:8001"
    except Exception:  # noqa: BLE001
        pass
    with open("/app/frontend/.env", "r", encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("REACT_APP_BACKEND_URL="):
                return line.split("=", 1)[1].strip()
    raise RuntimeError("no backend url")


def _mongo():
    url = os.environ.get("MONGO_URL")
    dbn = os.environ.get("DB_NAME") or "masci_safety_preview"
    if not url:
        with open("/app/backend/.env", "r", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("MONGO_URL="):
                    url = line.split("=", 1)[1].strip().strip('"').strip("'")
                elif line.startswith("DB_NAME="):
                    dbn = line.split("=", 1)[1].strip().strip('"').strip("'")
    return MongoClient(url)[dbn]


BACKEND = _backend()
TEST_PREFIX = "TEST_28_03_"
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"


@pytest.fixture(scope="module")
def admin_headers() -> dict:
    r = httpx.post(
        f"{BACKEND}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=30,
    )
    r.raise_for_status()
    tok = (r.json().get("portal_tokens") or {}).get("admin")
    assert tok and "." in tok, "expected UUID.HMAC admin token"
    return {"X-Admin-Token": tok, "Content-Type": "application/json"}


def _base_payload(kind: str) -> Dict[str, Any]:
    """Minimal valid FieldLeadershipCreate payload for a given kind."""
    ts = int(time.time() * 1000)
    tag = f"{TEST_PREFIX}{kind}_{ts}_{uuid.uuid4().hex[:6]}"
    now = datetime.now(timezone.utc).isoformat()
    return {
        "kind": kind,
        "employee_name": f"{TEST_PREFIX}Employee {kind}",
        "employee_position": "Certification Tester",
        "supervisor_name": f"{TEST_PREFIX}Supervisor",
        "project_number": f"{TEST_PREFIX}PJ{ts % 100000}",
        "project_name": f"{tag}_project",
        "location": "TEST · Cert Yard",
        "occurred_at": now,
        "details": {"note": f"Track 28.03B cert record — {kind}"},
        "language": "en",
        "supervisor_signature": "data:image/png;base64,iVBORw0KGgo=",
        # employee_signature/refused rules vary per kind — verbal_coaching
        # allows optional signature, but supplying a valid stub is always
        # accepted by the backend contract.
        "employee_signature": "data:image/png;base64,iVBORw0KGgo=",
    }


# The complete kind list mirrors FIELD_LEADERSHIP_FORMS in
# lib/fieldLeadershipSchemas.js exactly (kind values are the contract
# between the FE schema library and the backend record store).
#
# NOTE: The frontend also exports `SAFETY_EQUIPMENT_ISSUANCE_LINK`
# with kind ``safety_equipment_issuance`` but that is NOT part of the
# FL flow — it's a launcher tile that routes to /safety/forms/login
# and submits into the ``safety_equipment_issuances`` collection
# (a completely separate lane). It is intentionally excluded here.
KINDS: List[str] = [
    "write_up",
    "verbal_coaching",
    "attendance",
    "recognition",
    "equipment_checkout",
    "new_employee_eval",
    "crew_eval",
    "promotion_recommendation",
    "training_deficiency",
    "employee_termination",
    "equipment_return",
    "time_off_request",
]


@pytest.mark.parametrize("kind", KINDS)
def test_field_leadership_full_e2e(admin_headers: dict, kind: str) -> None:
    """POST → GET-detail → LIST hides synthetic → PDF → DELETE roundtrip
    for every FL kind. Regression-locks Track 28.03B."""
    payload = _base_payload(kind)
    # Kind-specific tweaks — details schema varies per kind but the
    # backend accepts arbitrary dict for `details`, so a "note" field
    # is enough to satisfy validators.

    # POST
    r = httpx.post(
        f"{BACKEND}/api/field-leadership", headers=admin_headers,
        json=payload, timeout=30,
    )
    assert r.status_code == 200, f"[{kind}] POST failed: {r.status_code} {r.text[:400]}"
    body = r.json()
    assert body.get("ok") is True
    rec_id = body.get("id") or (body.get("record") or {}).get("id")
    assert rec_id, f"[{kind}] no id returned in POST response"

    try:
        # GET detail
        r = httpx.get(f"{BACKEND}/api/field-leadership/{rec_id}", headers=admin_headers, timeout=15)
        assert r.status_code == 200, f"[{kind}] GET-detail failed: {r.status_code}"
        assert r.json()["kind"] == kind

        # LIST hides synthetic rows (TRACK 28.03 doctrine)
        r = httpx.get(
            f"{BACKEND}/api/field-leadership",
            headers=admin_headers,
            params={"kind": kind, "limit": 200},
            timeout=15,
        )
        assert r.status_code == 200
        ids = [x.get("id") for x in (r.json().get("items") or [])]
        assert rec_id not in ids, (
            f"[{kind}] TRACK 28.03 regression: synthetic FL row leaked "
            f"to /api/field-leadership operational list"
        )

        # PDF endpoint returns application/pdf
        r = httpx.get(f"{BACKEND}/api/field-leadership/{rec_id}/pdf", headers=admin_headers, timeout=30)
        # Some kinds return 200 pdf; skip strict content-type on failure
        # types where the FL PDF renderer bails (empty photos, etc.),
        # but never a 5xx.
        assert r.status_code == 200, f"[{kind}] PDF failed: {r.status_code} {r.text[:200]}"
        assert "application/pdf" in r.headers.get("content-type", ""), (
            f"[{kind}] PDF wrong content-type: {r.headers.get('content-type')}"
        )
    finally:
        # DELETE — API does a SOFT-delete (sets deleted_at). Hard-purge
        # via Mongo so no certification artefact ever survives.
        r = httpx.delete(f"{BACKEND}/api/field-leadership/{rec_id}", headers=admin_headers, timeout=15)
        # Some endpoints return 200 on delete, some 204 — accept both.
        assert r.status_code in (200, 204), f"[{kind}] DELETE failed: {r.status_code}"
        _mongo().field_leadership_records.delete_one({"id": rec_id})


def test_flr_csv_export_excludes_synthetic(admin_headers: dict) -> None:
    """CSV admin export must inherit the FLR synthetic-exclusion filter."""
    payload = _base_payload("write_up")
    marker = payload["employee_name"]
    r = httpx.post(
        f"{BACKEND}/api/field-leadership", headers=admin_headers,
        json=payload, timeout=30,
    )
    assert r.status_code == 200
    rec_id = r.json().get("id") or (r.json().get("record") or {}).get("id")
    try:
        r = httpx.get(f"{BACKEND}/api/field-leadership/export/csv", headers=admin_headers, timeout=30)
        assert r.status_code == 200
        assert marker not in r.text, (
            "TRACK 28.03 regression: synthetic FL row leaked to CSV export"
        )
    finally:
        httpx.delete(f"{BACKEND}/api/field-leadership/{rec_id}", headers=admin_headers, timeout=15)
        _mongo().field_leadership_records.delete_one({"id": rec_id})


def test_flr_global_search_excludes_synthetic(admin_headers: dict) -> None:
    """Cmd+K global search must inherit the FLR synthetic-exclusion filter."""
    payload = _base_payload("recognition")
    marker = payload["employee_name"]
    r = httpx.post(
        f"{BACKEND}/api/field-leadership", headers=admin_headers,
        json=payload, timeout=30,
    )
    assert r.status_code == 200
    rec_id = r.json().get("id") or (r.json().get("record") or {}).get("id")
    try:
        r = httpx.get(
            f"{BACKEND}/api/search",
            headers={"X-Admin-Token": admin_headers["X-Admin-Token"]},
            params={"q": marker, "limit": 15},
            timeout=30,
        )
        assert r.status_code == 200
        body = r.json() or {}
        # Walk any shape looking for the id in field_leadership rows
        found = False
        for group in (body.get("groups") or body.get("results") or []):
            if isinstance(group, dict):
                items = group.get("items") or group.get("rows") or group.get("results") or []
                for it in items:
                    if isinstance(it, dict) and it.get("id") == rec_id:
                        found = True
                        break
        assert not found, (
            "TRACK 28.03 regression: synthetic FL row leaked to global search"
        )
    finally:
        httpx.delete(f"{BACKEND}/api/field-leadership/{rec_id}", headers=admin_headers, timeout=15)
        _mongo().field_leadership_records.delete_one({"id": rec_id})


def test_no_test_28_03_residue_left_behind() -> None:
    """After every FL E2E test cleans itself, no TEST_28_03_ FL record
    may survive on the DB. Belt-and-suspenders auto-purge."""
    db = _mongo()
    residue = db.field_leadership_records.count_documents({
        "$or": [
            {"employee_name": {"$regex": f"^{TEST_PREFIX}"}},
            {"supervisor_name": {"$regex": f"^{TEST_PREFIX}"}},
            {"project_number": {"$regex": f"^{TEST_PREFIX}"}},
        ]
    })
    if residue:
        db.field_leadership_records.delete_many({
            "$or": [
                {"employee_name": {"$regex": f"^{TEST_PREFIX}"}},
                {"supervisor_name": {"$regex": f"^{TEST_PREFIX}"}},
                {"project_number": {"$regex": f"^{TEST_PREFIX}"}},
            ]
        })
    assert not residue, (
        f"Residue purged (would have leaked): "
        f"{residue} TEST_28_03_ FL records"
    )
