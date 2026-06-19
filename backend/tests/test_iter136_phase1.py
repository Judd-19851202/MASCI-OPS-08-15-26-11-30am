"""iter136 — Phase-1 Iter B/C/D backend validation.

Covers:
- Shared PDF chrome (training-center guide PDF + fire-ext history PDF).
- Training Center seed: count==18 with 2 new guides (safety-fire-ext-attachments + safety-corrective-actions-links).
- Deploy Readiness aggregator (auth, structure, 10 checks all pass).
- Index armament on hot collections & TTL on system_health_events / audit_events.
"""

import os
import pytest
import requests
from pathlib import Path
from pymongo import MongoClient


def _read_kv(path, key):
    try:
        with open(path) as f:
            for line in f:
                if line.startswith(f"{key}="):
                    return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:
        pass
    return ""


BASE_URL = (
    _read_kv(Path("/app/frontend/.env"), "REACT_APP_BACKEND_URL")
    or os.environ.get("REACT_APP_BACKEND_URL", "")
).rstrip("/")
ADMIN_PW = "Maddix123!"
SAFETY_EMAIL = "safety@mascigc.com"
SAFETY_PW = "Safety123!"

EXPECTED_CHECKS = {
    "mongo", "critical_collections", "critical_indexes", "ttl_indexes",
    "r2", "resend", "integration_errors_24h", "r2_degraded_24h",
    "training_seed", "default_admin",
}

HOT_ID_COLLECTIONS = [
    "fire_extinguishers", "corrective_actions", "incidents", "inspections",
    "safety_training_records", "equipment_master", "employees",
]


# --- Fixtures ----------------------------------------------------------------
@pytest.fixture(scope="session")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/admin/login", json={"password": ADMIN_PW}, timeout=20)
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture(scope="session")
def safety_token():
    r = requests.post(f"{BASE_URL}/api/safety/login",
                      json={"email": SAFETY_EMAIL, "password": SAFETY_PW}, timeout=20)
    if r.status_code != 200:
        pytest.skip(f"safety login unavailable: {r.status_code}")
    return r.json()["token"]


@pytest.fixture(scope="session")
def mongo_db():
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.environ.get("DB_NAME", "test_database")
    client = MongoClient(mongo_url)
    yield client[db_name]
    client.close()


# --- Iter C: Shared PDF chrome ----------------------------------------------
class TestSharedPdfChrome:
    def test_training_guide_pdf_bytes(self, admin_token):
        r = requests.get(
            f"{BASE_URL}/api/training-center/guide/safety-fire-ext-bulk-import/pdf",
            headers={"X-Admin-Token": admin_token}, timeout=30,
        )
        assert r.status_code == 200, r.text
        assert r.content[:5] == b"%PDF-", "Not a PDF magic header"
        assert len(r.content) > 16 * 1024, f"PDF too small ({len(r.content)} bytes)"

    def test_fire_ext_history_pdf(self, safety_token, mongo_db):
        # Pick any fire_extinguishers doc to test the history pdf endpoint.
        fe = mongo_db.fire_extinguishers.find_one({}, {"id": 1})
        if not fe:
            pytest.skip("No fire_extinguishers present to render history.pdf")
        fe_id = fe["id"]
        r = requests.get(
            f"{BASE_URL}/api/safety/fire-extinguishers/{fe_id}/history.pdf",
            headers={"X-Safety-Token": safety_token, "X-Admin-Token": ""},
            timeout=30,
        )
        assert r.status_code == 200, r.text
        assert r.content[:5] == b"%PDF-"
        assert len(r.content) > 4 * 1024


# --- Iter C: Training Center seed --------------------------------------------
class TestTrainingCenterSeed:
    def test_portals_total_guide_count(self, admin_token):
        r = requests.get(f"{BASE_URL}/api/training-center/portals",
                         headers={"X-Admin-Token": admin_token}, timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        portals = data.get("portals", [])
        total = sum(p.get("count", 0) for p in portals)
        assert total == 18, f"Expected 18 guides, got {total} across portals={[(p['key'], p['count']) for p in portals]}"

    def test_new_guide_fire_ext_attachments(self, admin_token):
        r = requests.get(
            f"{BASE_URL}/api/training-center/guide/safety-fire-ext-attachments",
            headers={"X-Admin-Token": admin_token}, timeout=20,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        sections = body.get("sections") or body.get("guide", {}).get("sections", [])
        assert len(sections) == 4, f"Expected 4 sections, got {len(sections)}"

    def test_new_guide_ca_links(self, admin_token):
        r = requests.get(
            f"{BASE_URL}/api/training-center/guide/safety-corrective-actions-links",
            headers={"X-Admin-Token": admin_token}, timeout=20,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        sections = body.get("sections") or body.get("guide", {}).get("sections", [])
        assert len(sections) == 5, f"Expected 5 sections, got {len(sections)}"


# --- Iter D: Deploy Readiness ------------------------------------------------
class TestDeployReadiness:
    def test_requires_admin_token(self):
        # conftest auto-attaches X-Admin-Token; we explicitly clobber to empty
        # to test the gate, while still satisfying the patcher's setdefault.
        r = requests.get(
            f"{BASE_URL}/api/admin/deploy-readiness",
            headers={"X-Admin-Token": ""},
            timeout=20,
        )
        assert r.status_code == 401, f"Expected 401 sans token, got {r.status_code}"

    def test_returns_ready_with_10_checks(self, admin_token):
        r = requests.get(f"{BASE_URL}/api/admin/deploy-readiness",
                         headers={"X-Admin-Token": admin_token}, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("overall_status") == "ready", f"overall={data.get('overall_status')}"
        checks = data.get("checks", [])
        assert len(checks) == 10, f"Expected 10 checks, got {len(checks)}"
        ids = {c.get("id") for c in checks}
        assert ids == EXPECTED_CHECKS, f"Unexpected check ids diff: {ids ^ EXPECTED_CHECKS}"
        # Every check must pass.
        failing = [c for c in checks if not c.get("passed")]
        assert not failing, f"Failing checks: {failing}"
        assert data.get("blocker_count", -1) == 0
        assert data.get("warn_count", -1) == 0


# --- Iter D: Index armament + TTL --------------------------------------------
class TestIndexArmament:
    @pytest.mark.parametrize("coll", HOT_ID_COLLECTIONS)
    def test_id_index_present(self, mongo_db, coll):
        info = mongo_db[coll].index_information()
        has_id = any(
            any(field == "id" for field, _ in spec.get("key", []))
            for spec in info.values()
        )
        assert has_id, f"{coll} missing id-field index. indexes={list(info.keys())}"

    @pytest.mark.parametrize("coll", ["system_health_events", "audit_events"])
    def test_ttl_index_30_days(self, mongo_db, coll):
        info = mongo_db[coll].index_information()
        ttl_specs = [s for s in info.values() if "expireAfterSeconds" in s]
        assert ttl_specs, f"{coll} has no TTL index. indexes={list(info.keys())}"
        # 30 days = 2592000 seconds
        seconds = {s["expireAfterSeconds"] for s in ttl_specs}
        assert 2592000 in seconds, f"{coll} TTL seconds={seconds}, expected 2592000"


# --- Regression: Safety flows from iter135 ----------------------------------
class TestSafetyRegression:
    def test_fire_extinguishers_list(self, safety_token):
        r = requests.get(f"{BASE_URL}/api/safety/fire-extinguishers",
                         headers={"X-Safety-Token": safety_token}, timeout=20)
        assert r.status_code == 200, r.text

    def test_corrective_actions_list(self, safety_token):
        r = requests.get(f"{BASE_URL}/api/safety/corrective-actions",
                         headers={"X-Safety-Token": safety_token}, timeout=20)
        assert r.status_code == 200, r.text
