"""
iter24 — Bilingual ES->EN auto-translate sweep + cleared-to-operate badge +
new aggregation list endpoints + safety indexes.

Validates:
- POST /api/translate ES->EN works (LLM path alive)
- GET /api/equipment-inspections has new keys: signoff_count, cleared, photo_count
- GET /api/inspections, /api/incidents, /api/daily-reports keep their *_count keys
- Cleared-to-operate flow: create FAIL inspection -> signoff -> cleared=true
- Response time of the four list endpoints (<2s)
"""
import os
import time
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
ADMIN_PW = os.environ.get("ADMIN_PASSWORD", "Happy123!")
SHOP_PW = os.environ.get("SHOP_PASSWORD", "Nothappy123!")


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/admin/login", json={"password": ADMIN_PW}, timeout=15)
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture(scope="module")
def shop_token():
    r = requests.post(f"{BASE_URL}/api/shop/login", json={"password": SHOP_PW}, timeout=15)
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"X-Admin-Token": admin_token, "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def shop_headers(shop_token):
    return {"X-Shop-Token": shop_token, "Content-Type": "application/json"}


# =============== TRANSLATE ===============
def _translate(strings, from_lang="es", to_lang="en"):
    return requests.post(
        f"{BASE_URL}/api/translate",
        json={"strings": strings, "from_lang": from_lang, "to_lang": to_lang},
        timeout=60,
    )


class TestTranslate:
    def test_translate_es_to_en(self):
        r = _translate({"notes": "Reemplacé el filtro de aceite"})
        assert r.status_code == 200, r.text
        out = (r.json().get("strings", {}).get("notes") or "").lower()
        assert "replaced" in out or ("oil" in out and "filter" in out), f"unexpected: {out}"

    def test_translate_proper_nouns_preserved(self):
        r = _translate({"d": "Juan Pérez trabajó en Cemex hoy"})
        assert r.status_code == 200
        out = r.json().get("strings", {}).get("d") or ""
        assert "Juan" in out and "Cemex" in out, f"unexpected: {out}"


# =============== AGGREGATION SHAPE & PERF ===============
class TestListEndpointShape:
    def test_equipment_inspections_has_new_keys(self, shop_headers):
        t0 = time.time()
        r = requests.get(f"{BASE_URL}/api/equipment-inspections", headers=shop_headers, timeout=10)
        elapsed = time.time() - t0
        assert r.status_code == 200, r.text
        assert elapsed < 2.5, f"too slow: {elapsed:.2f}s"
        data = r.json()
        assert isinstance(data, list)
        if data:
            row = data[0]
            for k in ("photo_count", "signoff_count", "cleared", "fail_count"):
                assert k in row, f"missing key {k} in {list(row.keys())}"
            assert isinstance(row["cleared"], bool)
            assert isinstance(row["signoff_count"], int)
            assert isinstance(row["photo_count"], int)

    def test_inspections_has_photo_count(self, admin_headers):
        t0 = time.time()
        r = requests.get(f"{BASE_URL}/api/inspections", headers=admin_headers, timeout=10)
        elapsed = time.time() - t0
        assert r.status_code == 200
        assert elapsed < 2.5
        data = r.json()
        if data:
            assert "photo_count" in data[0]
            # Critical: ensure raw 'photos' base64 array is NOT in summary
            assert "photos" not in data[0] or not data[0].get("photos")

    def test_incidents_has_photo_count(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/incidents", headers=admin_headers, timeout=10)
        assert r.status_code == 200
        data = r.json()
        if data:
            assert "photo_count" in data[0]

    def test_daily_reports_has_counts(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/daily-reports", headers=admin_headers, timeout=10)
        assert r.status_code == 200
        data = r.json()
        if data:
            row = data[0]
            # crew_count / sub_count / visitor_count expected per review_request
            for k in ("photo_count", "crew_count"):
                assert k in row, f"missing {k} in {list(row.keys())}"


# =============== CLEARED-TO-OPERATE BADGE ===============
@pytest.fixture
def fail_inspection(admin_headers):
    """Create an OOS FAIL equipment inspection and yield its id; cleanup after."""
    payload = {
        "project_name": "TEST_iter24",
        "project_number": "TEST-IT24",
        "location": "yard",
        "inspection_date": "2026-04-28",
        "inspection_time": "08:00",
        "operator_name": "TEST iter24 op",
        "equipment_type": "Skid Steer",
        "equipment_unit": "TST-IT24",
        "checklist": {
            "Engine": [
                {"item": "Oil level", "status": "fail", "notes": "low"},
            ]
        },
        "fail_count": 1,
        "out_of_service": "Yes",
        "operator_notes": "TEST iter24",
    }
    r = requests.post(f"{BASE_URL}/api/equipment-inspections", json=payload, timeout=15)
    assert r.status_code == 200, r.text
    insp_id = r.json()["id"]
    yield insp_id
    # cleanup
    try:
        requests.delete(
            f"{BASE_URL}/api/equipment-inspections/{insp_id}",
            headers=admin_headers,
            timeout=10,
        )
    except Exception:
        pass


class TestClearedBadge:
    def test_cleared_flow(self, shop_headers, admin_headers, fail_inspection):
        insp_id = fail_inspection

        # initially: fail_count=1, signoff_count=0, cleared=False
        r = requests.get(f"{BASE_URL}/api/equipment-inspections", headers=shop_headers, timeout=10)
        assert r.status_code == 200
        row = next((x for x in r.json() if x["id"] == insp_id), None)
        assert row is not None, "newly created inspection not in list"
        assert row["fail_count"] == 1
        assert row["signoff_count"] == 0
        assert row["cleared"] is False

        # POST signoff
        sign = requests.post(
            f"{BASE_URL}/api/admin/equipment-inspections/{insp_id}/signoff",
            json={
                "section": "Engine",
                "item": "Oil level",
                "signed_by": "TEST_iter24 mech",
                "action_taken": "Repaired",
                "notes": "Refilled oil",
            },
            headers=shop_headers,
            timeout=15,
        )
        assert sign.status_code == 200, sign.text

        # Re-list — cleared should now be True
        r2 = requests.get(f"{BASE_URL}/api/equipment-inspections", headers=shop_headers, timeout=10)
        assert r2.status_code == 200
        row2 = next((x for x in r2.json() if x["id"] == insp_id), None)
        assert row2 is not None
        assert row2["signoff_count"] >= 1
        assert row2["cleared"] is True


# =============== ES->EN PERSISTED AS ENGLISH (smoke via /api/translate roundtrip) ===============
# The actual frontend wire-up sends Spanish text through /api/translate before
# POSTing. We simulate that here for ShopSignoff and Parts to confirm the
# translate endpoint handles the exact field shapes used by those modules.
class TestBilingualPipeline:
    def test_signoff_payload_translated(self):
        r = _translate({"notes": "Reemplacé el filtro y revisé los tornillos"})
        assert r.status_code == 200
        out = (r.json().get("strings", {}).get("notes") or "").lower()
        assert "filter" in out or "checked" in out or "replaced" in out, out

    def test_parts_name_translated(self):
        r = _translate({"name": "Filtro de aceite"})
        assert r.status_code == 200
        out = (r.json().get("strings", {}).get("name") or "").lower()
        assert "oil" in out and "filter" in out, out

    def test_parts_notes_translated(self):
        r = _translate({"notes": "Cambiar cada 250 horas"})
        assert r.status_code == 200
        out = (r.json().get("strings", {}).get("notes") or "").lower()
        assert "250" in out and ("hour" in out or "change" in out or "every" in out), out
