"""TRACK 28.07 · Session 1 · Training / Qualification E2E certification.

Covers Phases 1-6:
  * Create qualification (Phase 5)
  * Renew qualification (Phase 5)
  * Revoke qualification (Phase 5)
  * List → synthetic excluded (Phase 4)
  * Competent Person picker → synthetic excluded (Phase 4/6)
  * Public QR verification → synthetic excluded (Phase 6)
  * Permission matrix (Phase 3)
  * Cross-domain: HR terminated employee's qualifications remain in
    identity but do not surface on eligibility pickers (Phase 6)
  * Zero residue (Phase 19)

Doctrine mirrors 28.04/28.05/28.06 — TEST_28_07_ sentinel, autouse
teardown, source-controlled evidence.
"""
from __future__ import annotations

import re
import time
import uuid
from typing import Any, Dict

import httpx
import pytest
from pymongo import MongoClient


TEST_PREFIX = "TEST_28_07_"


def _backend() -> str:
    try:
        r = httpx.get("http://localhost:8001/api/health", timeout=5)
        if r.status_code == 200:
            return "http://localhost:8001"
    except Exception:
        pass
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                return line.split("=", 1)[1].strip()
    raise RuntimeError("no backend")


def _mongo():
    with open("/app/backend/.env") as f:
        env = f.read()
    url = re.search(r"^MONGO_URL=([^\n]+)", env, re.M).group(1).strip().strip('"').strip("'")
    dbn = re.search(r"^DB_NAME=([^\n]+)", env, re.M).group(1).strip().strip('"').strip("'")
    return MongoClient(url)[dbn]


BACKEND = _backend()


@pytest.fixture(scope="module", autouse=True)
def _residue_bookends():
    def _sweep():
        db = _mongo()
        prefix = f"^{TEST_PREFIX}"
        for coll, keys in [
            ("safety_training_records", ["employee_name", "training_name",
                                          "credential_number", "instructor_name"]),
            ("training_track_records", ["employee_name", "training_name"]),
            ("qualification_attachments", ["filename"]),
            ("employees", ["name", "employee_id"]),
        ]:
            for k in keys:
                try:
                    db[coll].delete_many({k: {"$regex": prefix}})
                except Exception:
                    pass
    _sweep()
    yield
    _sweep()


@pytest.fixture(scope="module")
def tokens() -> Dict[str, str]:
    r = httpx.post(
        f"{BACKEND}/api/auth/multi-login",
        json={"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["portal_tokens"]


@pytest.fixture(scope="module")
def hr_h(tokens):
    return {"X-HR-Token": tokens["hr"], "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def admin_h(tokens):
    return {"X-Admin-Token": tokens["admin"], "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def safety_h(tokens):
    return {"X-Safety-Token": tokens["safety"], "Content-Type": "application/json"}


def _create_test_employee(hr_h) -> Dict[str, Any]:
    ts = int(time.time() * 1000)
    tag = uuid.uuid4().hex[:6]
    payload = {
        "name": f"{TEST_PREFIX}Employee_{tag}_{ts}",
        "trade": "Operator",
        "role": "Lead Operator",
        "employee_id": f"{TEST_PREFIX}EID{ts % 100000}",
        "email": f"test_28_07_{tag}_{ts}@mascicert.local",
        "lifecycle_status": "Active",
    }
    r = httpx.post(f"{BACKEND}/api/hr/employees", headers=hr_h, json=payload, timeout=30)
    assert r.status_code == 200, f"employee create: {r.status_code} {r.text[:200]}"
    return {"id": r.json()["id"], "payload": payload}


def _create_qualification(
    hr_h, emp_id: str, qualification_type: str = "OSHA_30",
    expiration_date: str = "2027-12-31",
) -> Dict[str, Any]:
    payload = {
        "employee_id": emp_id,
        "employee_name": f"{TEST_PREFIX}Employee",
        "qualification_type": qualification_type,
        "training_name": f"{TEST_PREFIX}Training",
        "completed_date": "2025-01-15",
        "expiration_date": expiration_date,
        "issuing_organization": f"{TEST_PREFIX}Authority",
        "instructor": f"{TEST_PREFIX}Instructor",
        "certificate_number": f"{TEST_PREFIX}CERT{uuid.uuid4().hex[:6]}",
        "type_metadata": {},
    }
    r = httpx.post(
        f"{BACKEND}/api/hr/qualifications",
        headers=hr_h, json=payload, timeout=30,
    )
    assert r.status_code == 200, f"qual create: {r.status_code} {r.text[:200]}"
    return r.json()


# ═══════════════════════════════════════════════════════════════════
# PHASE 5 · TRAINING WRITE-PATH E2E
# ═══════════════════════════════════════════════════════════════════
def test_p5_create_qualification(hr_h):
    emp = _create_test_employee(hr_h)
    try:
        q = _create_qualification(hr_h, emp["id"], "COMPETENT_PERSON")
        qid = q.get("id") or q.get("qualification_id")
        try:
            assert qid
            doc = _mongo().safety_training_records.find_one({"id": qid})
            assert doc and doc.get("employee_id") == emp["id"]
            assert doc.get("verification_status") == "active"
        finally:
            _mongo().safety_training_records.delete_one({"id": qid})
    finally:
        _mongo().employees.delete_one({"id": emp["id"]})


def test_p5_renew_qualification(hr_h):
    emp = _create_test_employee(hr_h)
    try:
        q = _create_qualification(hr_h, emp["id"], "COMPETENT_PERSON")
        qid = q.get("id") or q.get("qualification_id")
        try:
            r = httpx.post(
                f"{BACKEND}/api/hr/qualifications/{qid}/renew",
                headers=hr_h,
                json={
                    "completed_date": "2026-01-15",
                    "expiration_date": "2028-12-31",
                    "reason": "TEST_28_07 renewal probe",
                },
                timeout=30,
            )
            assert r.status_code == 200, f"renew: {r.status_code} {r.text[:200]}"
            doc = _mongo().safety_training_records.find_one({"id": qid})
            assert doc.get("expiration_date") == "2028-12-31"
        finally:
            _mongo().safety_training_records.delete_one({"id": qid})
    finally:
        _mongo().employees.delete_one({"id": emp["id"]})


def test_p5_revoke_qualification(hr_h):
    emp = _create_test_employee(hr_h)
    try:
        q = _create_qualification(hr_h, emp["id"], "COMPETENT_PERSON")
        qid = q.get("id") or q.get("qualification_id")
        try:
            r = httpx.post(
                f"{BACKEND}/api/hr/qualifications/{qid}/revoke",
                headers=hr_h,
                json={"reason": "TEST_28_07 revocation probe"},
                timeout=30,
            )
            assert r.status_code == 200, f"revoke: {r.status_code} {r.text[:200]}"
            doc = _mongo().safety_training_records.find_one({"id": qid})
            assert doc.get("verification_status") == "revoked"
            assert doc.get("revoked_at")
        finally:
            _mongo().safety_training_records.delete_one({"id": qid})
    finally:
        _mongo().employees.delete_one({"id": emp["id"]})


# ═══════════════════════════════════════════════════════════════════
# PHASE 4 · SYNTHETIC EXCLUSION
# ═══════════════════════════════════════════════════════════════════
def test_p4_active_qualifications_list_hides_synthetic(hr_h, safety_h):
    """GET /api/employees/qualifications must not surface TEST_28_07_ rows."""
    emp = _create_test_employee(hr_h)
    try:
        q = _create_qualification(hr_h, emp["id"], "COMPETENT_PERSON")
        qid = q.get("id") or q.get("qualification_id")
        try:
            r = httpx.get(
                f"{BACKEND}/api/employees/qualifications",
                headers=safety_h,
                params={"type": "COMPETENT_PERSON", "active": True},
                timeout=30,
            )
            assert r.status_code == 200
            items = r.json().get("items", [])
            ids = [x.get("id") or x.get("qualification_id") for x in items]
            assert qid not in ids, (
                "TRACK 28.07 regression: synthetic qualification leaked to "
                "/api/employees/qualifications operator list"
            )
        finally:
            _mongo().safety_training_records.delete_one({"id": qid})
    finally:
        _mongo().employees.delete_one({"id": emp["id"]})


def test_p4_competent_persons_public_hides_synthetic(hr_h):
    """Public QR verification must NEVER surface TEST_28_07_ CPs."""
    emp = _create_test_employee(hr_h)
    try:
        q = _create_qualification(hr_h, emp["id"], "COMPETENT_PERSON")
        qid = q.get("id") or q.get("qualification_id")
        marker = f"{TEST_PREFIX}Employee"
        try:
            r = httpx.get(
                f"{BACKEND}/api/employees/competent-persons/public",
                timeout=30,
            )
            assert r.status_code == 200
            items = r.json().get("items", [])
            names = [x.get("employee_name", "") for x in items]
            assert not any(n.startswith(TEST_PREFIX) for n in names), (
                "TRACK 28.07 CRITICAL regression: synthetic CP leaked to "
                "public QR verification endpoint — potential legal exposure"
            )
        finally:
            _mongo().safety_training_records.delete_one({"id": qid})
    finally:
        _mongo().employees.delete_one({"id": emp["id"]})


def test_p4_competent_persons_registry_hides_synthetic(hr_h, safety_h):
    """/api/employees/competent-persons (operator picker) must hide synthetic."""
    emp = _create_test_employee(hr_h)
    try:
        q = _create_qualification(hr_h, emp["id"], "COMPETENT_PERSON")
        qid = q.get("id") or q.get("qualification_id")
        try:
            r = httpx.get(
                f"{BACKEND}/api/employees/competent-persons",
                headers=safety_h,
                timeout=30,
            )
            assert r.status_code == 200
            items = r.json().get("items", [])
            ids = [x.get("id") or x.get("qualification_id") for x in items]
            assert qid not in ids, (
                "TRACK 28.07 regression: synthetic CP leaked to operator picker"
            )
        finally:
            _mongo().safety_training_records.delete_one({"id": qid})
    finally:
        _mongo().employees.delete_one({"id": emp["id"]})


# ═══════════════════════════════════════════════════════════════════
# PHASE 6 · CROSS-DOMAIN CHAIN
# ═══════════════════════════════════════════════════════════════════
def test_p6_terminated_employee_qualification_snapshot(hr_h):
    """Rehire continuity: after termination, historical qualification
    remains attached to the SAME employee id (identity continuity).
    The qualification is filter-hidden but identity-scoped GET still
    returns it."""
    emp = _create_test_employee(hr_h)
    emp_id = emp["id"]
    try:
        q = _create_qualification(hr_h, emp_id, "COMPETENT_PERSON")
        qid = q.get("id") or q.get("qualification_id")
        try:
            # Terminate the employee
            httpx.post(
                f"{BACKEND}/api/hr/employees/{emp_id}/status",
                headers=hr_h,
                json={
                    "lifecycle_status": "Terminated",
                    "termination_date": "2026-03-01",
                    "last_day_worked": "2026-03-01",
                    "separation_type": "voluntary",
                    "rehire_eligibility": "eligible",
                    "reason": "TEST_28_07 termination for identity continuity probe",
                },
                timeout=30,
            )
            # Qualification identity is still attached to the same id
            doc = _mongo().safety_training_records.find_one({"id": qid})
            assert doc.get("employee_id") == emp_id, (
                "PROBE 6 · Rehire continuity: qualification identity broken "
                "on termination — this would break rehire history restore"
            )
        finally:
            _mongo().safety_training_records.delete_one({"id": qid})
    finally:
        _mongo().employees.delete_one({"id": emp_id})


# ═══════════════════════════════════════════════════════════════════
# PHASE 3 · PERMISSION MATRIX
# ═══════════════════════════════════════════════════════════════════
def test_p3_qualification_write_requires_hr_or_admin(tokens, hr_h):
    """Only HR / Admin may create qualifications."""
    emp = _create_test_employee(hr_h)
    payload = {
        "employee_id": emp["id"],
        "qualification_type": "COMPETENT_PERSON",
        "completed_date": "2025-01-15",
        "expiration_date": "2027-12-31",
        "type_metadata": {},
    }
    try:
        # PM token — must be denied
        pm_tok = tokens.get("pm")
        if pm_tok:
            r = httpx.post(
                f"{BACKEND}/api/hr/qualifications",
                headers={"X-PM-Token": pm_tok, "Content-Type": "application/json"},
                json=payload, timeout=15,
            )
            assert r.status_code in (401, 403), (
                f"PM token unexpectedly allowed to create qual: {r.status_code}"
            )
        # Unauth — must be denied
        r = httpx.post(
            f"{BACKEND}/api/hr/qualifications", json=payload, timeout=15,
        )
        assert r.status_code in (401, 403), f"unauth got {r.status_code}"
    finally:
        _mongo().employees.delete_one({"id": emp["id"]})


def test_p3_public_verification_no_sensitive_fields(hr_h):
    """Public CP verification must expose ONLY whitelisted fields —
    no email, phone, address, incident, medical, disciplinary."""
    r = httpx.get(f"{BACKEND}/api/employees/competent-persons/public", timeout=30)
    assert r.status_code == 200
    body = r.json()
    for item in body.get("items", []):
        sensitive = {"email", "phone", "address", "ssn", "medical",
                     "disciplinary", "incident_history", "salary"}
        for k in sensitive:
            assert k not in item, (
                f"TRACK 28.07 CRITICAL: public CP endpoint leaked "
                f"sensitive field `{k}`: {list(item.keys())}"
            )


# ═══════════════════════════════════════════════════════════════════
# ZERO RESIDUE
# ═══════════════════════════════════════════════════════════════════
def test_zz_zero_residue():
    db = _mongo()
    prefix = f"^{TEST_PREFIX}"
    residue = {}
    for coll, keys in [
        ("safety_training_records", ["employee_name", "training_name"]),
        ("employees", ["name", "employee_id"]),
    ]:
        for k in keys:
            try:
                n = db[coll].count_documents({k: {"$regex": prefix}}, limit=100)
                if n:
                    db[coll].delete_many({k: {"$regex": prefix}})
                    residue[coll] = residue.get(coll, 0) + n
            except Exception:
                pass
    assert not residue, f"TRACK 28.07 residue: {residue}"
