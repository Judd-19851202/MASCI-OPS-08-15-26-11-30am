"""
test_iter350_hr_safety_cdl_visibility.py — iter350 regression

P0 LIVE DATA VISIBILITY DEFECT closure:
  1. Safety -> HR visibility for safety_training_records.
  2. Safety -> HR visibility for safety_documents.
  3. CDL / Approved Driver visibility via /api/hr/driver-qualification/dashboard.
  4. Employee Linkage Standard:
     - Primary: employee_id
     - Fallback: normalized name + email
     - Graceful None for unlinked records (no crash, no silent drop)
  5. HR READ-ONLY contract: HR cannot POST/PATCH/DELETE on safety
     training, safety documents, or driver-qualification surfaces.

Run from /app/backend:
    cd /app/backend && python -m pytest tests/test_iter350_hr_safety_cdl_visibility.py -v
"""
from __future__ import annotations

import os
import re
import asyncio
import uuid
from pathlib import Path

import pytest
import requests


API_BASE = os.environ.get("API_BASE_URL", "http://localhost:8001")
API = f"{API_BASE}/api"

ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PW = "Maddix123!"


# ─────────────────────────────────────────────────────────────────────
# 1 · Employee Linkage Standard (utility-level locks)
# ─────────────────────────────────────────────────────────────────────
def test_employee_linkage_utility_exists():
    """The shared linkage utility must live at lib/employee_linkage.py."""
    util = Path(__file__).parent.parent / "lib" / "employee_linkage.py"
    assert util.exists(), f"missing {util}"
    src = util.read_text()
    # Required exported names
    for sym in ("normalize_name", "normalize_email", "resolve_employee",
                "attach_employee_link", "attach_employee_links"):
        assert sym in src, f"linkage util missing symbol {sym!r}"
    # The four-tier ladder must all be present (primary + 3 fallbacks).
    for marker in ("employee_id", "employee_master_id", "name_email", "unlinked"):
        assert marker in src, f"linkage util missing tier marker {marker!r}"


def test_employee_linkage_normalize_functions():
    """normalize_name / normalize_email are pure functions — verify
    deterministic behavior without needing the DB."""
    import sys
    bdir = str(Path(__file__).parent.parent)
    if bdir not in sys.path:
        sys.path.insert(0, bdir)
    from lib.employee_linkage import normalize_name, normalize_email

    assert normalize_name("  Alec  Perkins ") == "alec perkins"
    assert normalize_name("ALEC\tPERKINS") == "alec perkins"
    assert normalize_name(None) == ""
    assert normalize_name("") == ""

    assert normalize_email("  Foo@Bar.COM ") == "foo@bar.com"
    assert normalize_email(None) == ""
    assert normalize_email("") == ""


def test_employee_linkage_resolves_by_primary_and_fallback():
    """Spin up an in-memory motor mock to verify the resolver picks
    each tier correctly without hitting the live DB."""
    import sys
    bdir = str(Path(__file__).parent.parent)
    if bdir not in sys.path:
        sys.path.insert(0, bdir)
    from lib.employee_linkage import resolve_employee

    class _Coll:
        def __init__(self, docs):
            self.docs = docs

        async def find_one(self, query, projection=None):
            for d in self.docs:
                ok = True
                for k, v in query.items():
                    if isinstance(v, dict) and "$regex" in v:
                        pat = v["$regex"]
                        flags = re.I if "i" in (v.get("$options") or "") else 0
                        if not re.search(pat, str(d.get(k) or ""), flags):
                            ok = False
                            break
                    else:
                        if d.get(k) != v:
                            ok = False
                            break
                if ok:
                    return {k: v for k, v in d.items() if k != "_id"}
            return None

    class _DB:
        def __init__(self, docs):
            self.employees = _Coll(docs)

    docs = [
        {"id": "EMP-A", "employee_id": "1001", "name": "Alec Perkins", "email": "alec@mascigc.com"},
        {"id": "EMP-B", "employee_id": "1002", "name": "Bob Jones",    "email": "bob@mascigc.com"},
    ]
    db = _DB(docs)

    # Primary: employee_id (canonical id) match
    r = asyncio.run(resolve_employee(db, employee_id="EMP-A"))
    assert r and r["id"] == "EMP-A", "primary employee_id match failed"

    # Primary: employee_id (code) match
    r = asyncio.run(resolve_employee(db, employee_id="1002"))
    assert r and r["id"] == "EMP-B", "primary employee code match failed"

    # Fallback name+email
    r = asyncio.run(resolve_employee(
        db, employee_id="UNKNOWN",
        employee_name="  ALEC   perkins  ", email="ALEC@MASCIGC.COM",
    ))
    assert r and r["id"] == "EMP-A", "name+email fallback failed"

    # Fallback name only
    r = asyncio.run(resolve_employee(db, employee_name="Bob Jones"))
    assert r and r["id"] == "EMP-B", "name-only fallback failed"

    # No match → graceful None
    r = asyncio.run(resolve_employee(db, employee_name="Ghost Person"))
    assert r is None, "no-match must return None, not raise"

    # All-empty → None
    r = asyncio.run(resolve_employee(db))
    assert r is None, "all-empty input must return None"


# ─────────────────────────────────────────────────────────────────────
# 2 · HR route source-level locks
# ─────────────────────────────────────────────────────────────────────
def test_hr_training_records_unions_both_collections():
    """The HR endpoint must read from BOTH safety_training_records and
    training_track_records — not just one. Source-level lock."""
    src = (Path(__file__).parent.parent / "routes" / "hr_portal.py").read_text()
    # Locate the training-records route block
    idx = src.find('@router.get("/hr/training-records")')
    assert idx >= 0, "/hr/training-records route missing"
    # Block runs until the next route decorator.
    end = src.find("@router.", idx + 1)
    block = src[idx:end if end > 0 else len(src)]
    assert "db.safety_training_records.find" in block, (
        "/hr/training-records must query safety_training_records "
        "(iter350 fix — was missing before)"
    )
    assert "db.training_track_records.find" in block, (
        "/hr/training-records must still UNION the legacy "
        "training_track_records collection"
    )
    assert "attach_employee_links" in block, (
        "/hr/training-records must enrich rows via the linkage utility"
    )


def test_hr_safety_documents_endpoint_registered():
    """iter350 — HR gets a dedicated /api/hr/safety-documents endpoint."""
    src = (Path(__file__).parent.parent / "routes" / "hr_portal.py").read_text()
    assert '@router.get("/hr/safety-documents")' in src, (
        "iter350 endpoint /api/hr/safety-documents missing"
    )
    assert '@router.get("/hr/safety-documents/{doc_id}/download")' in src, (
        "iter350 download endpoint missing"
    )


def test_hr_safety_documents_is_read_only():
    """No POST/PATCH/DELETE/PUT on /hr/safety-documents — read-only contract."""
    src = (Path(__file__).parent.parent / "routes" / "hr_portal.py").read_text()
    forbidden = [
        '@router.post("/hr/safety-documents',
        '@router.patch("/hr/safety-documents',
        '@router.delete("/hr/safety-documents',
        '@router.put("/hr/safety-documents',
    ]
    for sig in forbidden:
        assert sig not in src, (
            f"HR read-only contract violated: {sig} found in hr_portal.py"
        )


def test_hr_training_records_is_read_only():
    """No POST/PATCH/DELETE on /hr/training-records."""
    src = (Path(__file__).parent.parent / "routes" / "hr_portal.py").read_text()
    forbidden = [
        '@router.post("/hr/training-records',
        '@router.patch("/hr/training-records',
        '@router.delete("/hr/training-records',
        '@router.put("/hr/training-records',
    ]
    for sig in forbidden:
        assert sig not in src, (
            f"HR read-only contract violated: {sig} found in hr_portal.py"
        )


def test_hr_driver_qualification_is_read_only():
    """employee_lifecycle.py — /hr/driver-qualification/dashboard must
    have NO write peer endpoints under /hr/driver-qualification/*."""
    src = (Path(__file__).parent.parent / "routes" / "employee_lifecycle.py").read_text()
    forbidden = [
        '@router.post("/api/hr/driver-qualification',
        '@router.patch("/api/hr/driver-qualification',
        '@router.delete("/api/hr/driver-qualification',
        '@router.put("/api/hr/driver-qualification',
    ]
    for sig in forbidden:
        assert sig not in src, (
            f"HR read-only contract violated: {sig} found in employee_lifecycle.py"
        )


# ─────────────────────────────────────────────────────────────────────
# 3 · Live E2E (preview backend running on port 8001)
# ─────────────────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def admin_tokens():
    r = requests.post(
        f"{API}/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PW},
        timeout=10,
    )
    assert r.status_code == 200, f"super-admin login failed: {r.status_code} {r.text}"
    tokens = r.json().get("portal_tokens") or {}
    assert tokens.get("hr"), "super-admin must mint an HR token"
    assert tokens.get("safety"), "super-admin must mint a Safety token"
    return tokens


def test_live_hr_training_records_includes_safety_source(admin_tokens):
    """The fix: HR sees safety_training_records under /hr/training-records."""
    r = requests.get(
        f"{API}/hr/training-records?limit=500",
        headers={"X-HR-Token": admin_tokens["hr"]},
        timeout=15,
    )
    assert r.status_code == 200, f"HR training-records failed: {r.status_code} {r.text}"
    data = r.json()
    assert data.get("ok") is True
    items = data.get("items") or []
    counts = data.get("counts") or {}
    # The endpoint must always carry the new shape.
    assert "safety" in counts and "track" in counts and "total" in counts, (
        f"new union shape missing — got {counts}"
    )
    # Every row must carry its source + linkage_method.
    for row in items[:50]:
        assert row.get("source") in ("safety", "track"), (
            f"row missing source tag: {row.get('id')}"
        )
        assert "linkage_method" in row, f"row missing linkage_method: {row.get('id')}"


def test_live_hr_training_records_linkage_attaches_employee(admin_tokens):
    """Each row should either resolve to a roster employee or
    gracefully report 'unlinked' — never crash, never silently drop."""
    r = requests.get(
        f"{API}/hr/training-records?limit=200",
        headers={"X-HR-Token": admin_tokens["hr"]},
        timeout=15,
    )
    data = r.json()
    methods = {row.get("linkage_method") for row in (data.get("items") or [])}
    # methods can be empty (zero records); the shape contract is what matters
    valid = {"id", "master_id", "name_email", "name", "unlinked"}
    assert methods.issubset(valid), f"unexpected linkage methods: {methods}"


def test_live_hr_safety_documents_endpoint(admin_tokens):
    """HR can list safety_documents via the dedicated /hr/safety-documents."""
    r = requests.get(
        f"{API}/hr/safety-documents",
        headers={"X-HR-Token": admin_tokens["hr"]},
        timeout=15,
    )
    assert r.status_code == 200, f"safety-documents failed: {r.status_code} {r.text}"
    data = r.json()
    assert data.get("ok") is True
    assert isinstance(data.get("items"), list)
    assert "summary" in data
    # file_data must be projected OUT of listings (don't leak base64 blobs).
    for d in data["items"][:10]:
        assert "file_data" not in d, (
            f"safety_documents list must NOT include file_data — {d.get('id')}"
        )


def test_live_hr_driver_qualification_dashboard(admin_tokens):
    """HR token authorizes the driver-qualification dashboard. The
    base scope only surfaces employees who actually have a driver
    signal — never the full roster."""
    r = requests.get(
        f"{API}/hr/driver-qualification/dashboard?limit=10",
        headers={"X-HR-Token": admin_tokens["hr"]},
        timeout=15,
    )
    assert r.status_code == 200, f"driver-qualification failed: {r.status_code} {r.text}"
    data = r.json()
    assert "items" in data and "summary" in data
    # Every returned row must carry at least one driver-qualification
    # field — base scope discipline.
    for item in data["items"][:20]:
        has_signal = bool(
            item.get("cdl_holder")
            or item.get("approved_company_driver")
            or item.get("cdl_expiration_date")
            or item.get("medical_card_expiration_date")
        )
        assert has_signal, (
            f"driver-qualification returned employee without any driver "
            f"signal — base scope leak: {item.get('id')}"
        )


# ─────────────────────────────────────────────────────────────────────
# 4 · Read-only contract enforced at the wire
# ─────────────────────────────────────────────────────────────────────
def test_live_hr_cannot_post_training_record(admin_tokens):
    """POST /hr/training-records must NOT be a registered endpoint."""
    r = requests.post(
        f"{API}/hr/training-records",
        headers={"X-HR-Token": admin_tokens["hr"]},
        json={"employee_id": "x", "training_name": "x"},
        timeout=10,
    )
    # 405 Method Not Allowed = exactly what we want; 404 also acceptable.
    assert r.status_code in (404, 405), (
        f"HR POST /hr/training-records returned {r.status_code} — "
        "write surface must NOT exist (read-only contract)"
    )


def test_live_hr_cannot_delete_safety_document(admin_tokens):
    """HR token must not be able to mutate safety_documents via the
    Safety write routes (/safety/documents/{id} DELETE requires
    X-Safety-Token, not X-HR-Token)."""
    fake_id = str(uuid.uuid4())
    r = requests.delete(
        f"{API}/safety/documents/{fake_id}",
        headers={"X-HR-Token": admin_tokens["hr"]},
        timeout=10,
    )
    # Either 401 (gate refused HR token for a write) or 404 (route
    # doesn't accept HR token, gate runs first → 401 typical).
    assert r.status_code in (401, 403, 404), (
        f"HR token unexpectedly accepted by safety DELETE — got "
        f"{r.status_code} {r.text}"
    )


def test_live_hr_cannot_post_safety_training_record(admin_tokens):
    """HR token must not POST a safety_training_record via the Safety
    write surface."""
    r = requests.post(
        f"{API}/safety/training-records",
        headers={"X-HR-Token": admin_tokens["hr"]},
        json={"employee_id": "x", "training_name": "x"},
        timeout=10,
    )
    assert r.status_code in (401, 403, 405), (
        f"Safety POST accepted HR token — wrote a training record! got "
        f"{r.status_code} {r.text}"
    )


# ─────────────────────────────────────────────────────────────────────
# 5 · End-to-end Safety→HR visibility loop (seed + read-back)
# ─────────────────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def seed_safety_training(admin_tokens):
    """Seed a safety_training_record using the Safety token, then
    confirm HR can see it. The seed uses a unique training_name so we
    can isolate the row even when other tests also seed."""
    sentinel = f"iter350-sentinel-{uuid.uuid4().hex[:8]}"
    payload = {
        "employee_id": "iter350-emp-id-test",
        "employee_name": "Iter350 Sentinel Person",
        "training_name": sentinel,
        "certification_type": "iter350 test",
        "completed_date": "2026-01-01",
        "expiration_date": "2099-01-01",
        "issued_by": "iter350 regression",
    }
    r = requests.post(
        f"{API}/safety/training-records",
        headers={"X-Safety-Token": admin_tokens["safety"]},
        json=payload, timeout=15,
    )
    assert r.status_code == 200, f"safety training seed failed: {r.status_code} {r.text}"
    rec = r.json()
    yield {"sentinel": sentinel, "id": rec.get("id")}
    # Teardown — clean up the test record so we don't pollute preview.
    try:
        requests.delete(
            f"{API}/safety/training-records/{rec.get('id')}",
            headers={"X-Safety-Token": admin_tokens["safety"]},
            timeout=10,
        )
    except Exception:
        pass


def test_live_safety_to_hr_visibility_loop(admin_tokens, seed_safety_training):
    """After Safety inserts a training record, HR must see it via
    /hr/training-records — the headline P0 fix."""
    sentinel = seed_safety_training["sentinel"]
    r = requests.get(
        f"{API}/hr/training-records?employee=Sentinel&limit=500",
        headers={"X-HR-Token": admin_tokens["hr"]},
        timeout=15,
    )
    assert r.status_code == 200
    items = r.json().get("items") or []
    matched = [it for it in items if it.get("training_name") == sentinel]
    assert matched, (
        f"P0 DEFECT NOT FIXED — HR cannot see safety_training_records "
        f"row with training_name={sentinel!r}. Items: {[i.get('training_name') for i in items]}"
    )
    row = matched[0]
    assert row.get("source") == "safety"
    assert "linkage_method" in row
    # The seed used employee_id="iter350-emp-id-test" which doesn't
    # exist in the roster → row should be marked unlinked GRACEFULLY
    # (no crash, no missing record).
    assert row.get("linkage_method") in ("unlinked", "name", "name_email", "id", "master_id")


def test_live_safety_to_hr_employee_accountability_includes_safety_trainings(admin_tokens, seed_safety_training):
    """employee-accountability also surfaces safety_training_records."""
    r = requests.get(
        f"{API}/hr/employee-accountability?employee=Sentinel",
        headers={"X-HR-Token": admin_tokens["hr"]},
        timeout=15,
    )
    assert r.status_code == 200
    data = r.json()
    trainings = data.get("trainings") or []
    matched = [t for t in trainings if t.get("training_name") == seed_safety_training["sentinel"]]
    assert matched, (
        "employee-accountability missing the safety training record — "
        "iter350 employee-accountability fix did not land"
    )
    assert matched[0].get("source") == "safety"
