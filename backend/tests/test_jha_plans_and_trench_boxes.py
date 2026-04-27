"""Backend tests for the new Job Hazard Plans hub + Trench Box tabulated data
endpoints added in iteration 13."""
import base64
import os
from pathlib import Path

import pytest
import requests


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
ADMIN_PASSWORD = _read_kv(Path("/app/backend/.env"), "ADMIN_PASSWORD") or os.environ.get(
    "ADMIN_PASSWORD", ""
)

# Get a fresh token for tests that need to strip it
_r = requests.post(f"{BASE_URL}/api/admin/login", json={"password": ADMIN_PASSWORD}, timeout=10)
ADMIN_TOKEN = _r.json().get("token", "") if _r.status_code == 200 else ""

# Minimal real PDF header so content_type detection works
_PDF_BYTES = (
    b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n"
    b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj\n"
    b"xref\n0 4\n0000000000 65535 f\ntrailer<</Size 4/Root 1 0 R>>\n%%EOF\n"
)
PDF_DATA_URL = "data:application/pdf;base64," + base64.b64encode(_PDF_BYTES).decode()


# ============================================================
# Job Hazard Plans
# ============================================================
class TestJobHazardPlans:
    TEST_PN = "TEST-24-99"

    @classmethod
    def teardown_class(cls):
        # Clean up any test plan we created
        try:
            requests.delete(f"{BASE_URL}/api/job-hazard-plans/{cls.TEST_PN}", timeout=10)
        except Exception:
            pass

    def test_list_returns_200_array_without_file_blob(self):
        r = requests.get(f"{BASE_URL}/api/job-hazard-plans", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        for item in data:
            assert "_id" not in item
            assert "file_data" not in item
            assert "id" in item
            assert "project_number" in item

    def test_post_requires_admin_token(self):
        # Explicitly pass an empty-ish header to bypass the conftest patch
        r = requests.post(
            f"{BASE_URL}/api/job-hazard-plans",
            json={
                "project_number": self.TEST_PN,
                "project_name": "X",
                "filename": "x.pdf",
                "file_data": PDF_DATA_URL,
            },
            headers={"X-Admin-Token": "not-a-real-token"},
            timeout=15,
        )
        assert r.status_code == 401, r.text

    def test_post_creates_plan_then_upsert_replaces(self):
        payload = {
            "project_number": self.TEST_PN,
            "project_name": "Test Job",
            "location": "Nowhere",
            "filename": "first.pdf",
            "file_data": PDF_DATA_URL,
            "uploaded_by": "pytest",
            "notes": "first upload",
        }
        r1 = requests.post(f"{BASE_URL}/api/job-hazard-plans", json=payload, timeout=15)
        assert r1.status_code == 200, r1.text
        d1 = r1.json()
        assert d1["project_number"] == self.TEST_PN
        assert d1["filename"] == "first.pdf"
        assert d1["file_size"] > 0
        assert "file_data" not in d1  # blob shouldn't echo back
        first_id = d1["id"]

        # Second POST with same project_number REPLACES, not duplicates
        payload2 = {**payload, "filename": "second.pdf", "notes": "replaced"}
        r2 = requests.post(f"{BASE_URL}/api/job-hazard-plans", json=payload2, timeout=15)
        assert r2.status_code == 200
        d2 = r2.json()
        assert d2["project_number"] == self.TEST_PN
        assert d2["filename"] == "second.pdf"
        assert d2["notes"] == "replaced"

        # List shouldn't have two rows for the same project_number
        lst = requests.get(f"{BASE_URL}/api/job-hazard-plans", timeout=10).json()
        matches = [p for p in lst if p["project_number"] == self.TEST_PN]
        assert len(matches) == 1, f"Expected upsert but found {len(matches)} rows"

    def test_file_download_streams_pdf(self):
        r = requests.get(
            f"{BASE_URL}/api/job-hazard-plans/{self.TEST_PN}/file", timeout=10
        )
        assert r.status_code == 200
        assert r.headers.get("content-type", "").startswith("application/pdf")
        assert r.content.startswith(b"%PDF-")

    def test_file_download_404_when_no_plan(self):
        r = requests.get(
            f"{BASE_URL}/api/job-hazard-plans/DOES-NOT-EXIST-999/file", timeout=10
        )
        assert r.status_code == 404

    def test_delete_requires_admin(self):
        r = requests.delete(
            f"{BASE_URL}/api/job-hazard-plans/{self.TEST_PN}",
            headers={"X-Admin-Token": "bogus"},
            timeout=10,
        )
        assert r.status_code == 401

    def test_delete_returns_deleted_true(self):
        r = requests.delete(
            f"{BASE_URL}/api/job-hazard-plans/{self.TEST_PN}", timeout=10
        )
        assert r.status_code == 200
        assert r.json().get("deleted") is True
        # Now 404 on file download
        r2 = requests.get(
            f"{BASE_URL}/api/job-hazard-plans/{self.TEST_PN}/file", timeout=10
        )
        assert r2.status_code == 404


# ============================================================
# Trench Boxes
# ============================================================
class TestTrenchBoxes:
    created_ids = []

    @classmethod
    def teardown_class(cls):
        for bid in cls.created_ids:
            try:
                requests.delete(f"{BASE_URL}/api/trench-boxes/{bid}", timeout=10)
            except Exception:
                pass

    def test_list_returns_200_array(self):
        r = requests.get(f"{BASE_URL}/api/trench-boxes", timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        for b in r.json():
            assert "_id" not in b

    def test_post_requires_admin(self):
        r = requests.post(
            f"{BASE_URL}/api/trench-boxes",
            json={"manufacturer": "TEST_Mfg", "model": "TEST_M1"},
            headers={"X-Admin-Token": "bogus"},
            timeout=10,
        )
        assert r.status_code == 401

    def test_post_requires_manufacturer_and_model(self):
        r = requests.post(
            f"{BASE_URL}/api/trench-boxes",
            json={"manufacturer": "  ", "model": "   "},
            timeout=10,
        )
        assert r.status_code == 400

    def test_full_crud_flow(self):
        # CREATE
        payload = {
            "manufacturer": "TEST_Efficiency",
            "model": "TEST_SBS8x20",
            "box_type": "Steel",
            "length_ft": "20",
            "max_depth_type_a_ft": "18",
            "max_depth_type_c_60_ft": "12",
            "tabulated_data_file": PDF_DATA_URL,
            "tabulated_data_filename": "spec.pdf",
        }
        r = requests.post(f"{BASE_URL}/api/trench-boxes", json=payload, timeout=15)
        assert r.status_code == 200, r.text
        box = r.json()
        assert box["manufacturer"] == "TEST_Efficiency"
        assert box["model"] == "TEST_SBS8x20"
        assert "id" in box
        box_id = box["id"]
        self.__class__.created_ids.append(box_id)

        # GET one
        r2 = requests.get(f"{BASE_URL}/api/trench-boxes/{box_id}", timeout=10)
        assert r2.status_code == 200
        assert r2.json()["id"] == box_id
        assert r2.json()["max_depth_type_a_ft"] == "18"

        # File download
        r3 = requests.get(f"{BASE_URL}/api/trench-boxes/{box_id}/file", timeout=10)
        assert r3.status_code == 200
        assert r3.content.startswith(b"%PDF-")

        # PUT update
        upd = {**payload, "length_ft": "24", "max_depth_type_a_ft": "20"}
        # tabulated_data_file left out to test "don't require re-upload"
        upd.pop("tabulated_data_file")
        r4 = requests.put(
            f"{BASE_URL}/api/trench-boxes/{box_id}", json=upd, timeout=15
        )
        assert r4.status_code == 200
        assert r4.json()["length_ft"] == "24"
        assert r4.json()["max_depth_type_a_ft"] == "20"

        # Confirm persisted
        r5 = requests.get(f"{BASE_URL}/api/trench-boxes/{box_id}", timeout=10)
        assert r5.json()["length_ft"] == "24"

        # DELETE requires admin
        rd = requests.delete(
            f"{BASE_URL}/api/trench-boxes/{box_id}",
            headers={"X-Admin-Token": "bogus"},
            timeout=10,
        )
        assert rd.status_code == 401

        # Real delete
        rd2 = requests.delete(f"{BASE_URL}/api/trench-boxes/{box_id}", timeout=10)
        assert rd2.status_code == 200
        assert rd2.json().get("deleted") is True

        # GET returns 404
        r6 = requests.get(f"{BASE_URL}/api/trench-boxes/{box_id}", timeout=10)
        assert r6.status_code == 404
        self.__class__.created_ids.remove(box_id)

    def test_file_download_404_when_no_file(self):
        # Create box without file
        r = requests.post(
            f"{BASE_URL}/api/trench-boxes",
            json={"manufacturer": "TEST_NoFile", "model": "TEST_NF1"},
            timeout=10,
        )
        assert r.status_code == 200
        bid = r.json()["id"]
        self.__class__.created_ids.append(bid)
        rf = requests.get(f"{BASE_URL}/api/trench-boxes/{bid}/file", timeout=10)
        assert rf.status_code == 404


# ============================================================
# Smoke — make sure other modules still load after the refactor
# ============================================================
class TestRegressionSmoke:
    def test_root_api(self):
        r = requests.get(f"{BASE_URL}/api/", timeout=10)
        assert r.status_code == 200

    @pytest.mark.parametrize(
        "endpoint",
        [
            "/api/inspections",
            "/api/meetings",
            "/api/jhas",
            "/api/incidents",
            "/api/daily-reports",
            "/api/equipment-inspections",
        ],
    )
    def test_legacy_list_endpoints(self, endpoint):
        r = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
        # These are admin-gated GETs; conftest attaches the token
        assert r.status_code == 200, f"{endpoint} → {r.status_code}"
        assert isinstance(r.json(), list)
