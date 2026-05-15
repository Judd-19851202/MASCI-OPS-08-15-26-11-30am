"""Iter154 · Phase F · UNIFIED SIGNATURE ENGINE — backend tests.

Tests:
  * POST /api/signatures — successful capture (with image)
  * POST /api/signatures — refusal flow (valid + invalid)
  * Pydantic validation (source_module, signature_type)
  * Image size guard (>1.8MB)
  * supersedes chain (append-only)
  * GET /api/signatures — filters + include_superseded
  * Auth gate — no portal token => 401
"""
import base64
import os
import uuid
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

SAFETY_EMAIL = "safety@mascigc.com"
SAFETY_PW = "SafetyTest2026!"
TAG = f"TEST_iter154_{uuid.uuid4().hex[:6]}"

# 1x1 transparent PNG base64
TINY_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7w"
    "AAAABJRU5ErkJggg=="
)
TINY_PNG_DATA_URL = f"data:image/png;base64,{TINY_PNG_B64}"


# ── fixtures ────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def safety_token():
    r = requests.post(
        f"{BASE_URL}/api/safety/login",
        json={"email": SAFETY_EMAIL, "password": SAFETY_PW},
        timeout=20,
    )
    if r.status_code != 200:
        pytest.skip(f"Safety login failed: {r.status_code} {r.text}")
    return r.json()["token"]


def _sh(tok):
    # X-Admin-Token is also auto-attached by conftest — that's fine, both are accepted.
    return {"X-Safety-Token": tok}


@pytest.fixture(scope="module")
def ca_id(safety_token):
    """Create a Safety CA we can attach signatures to."""
    body = {
        "title": f"{TAG} CA",
        "description": "iter154 signature engine fixture",
        "source_kind": "manual",
        "source_id": "n/a",
        "priority": "Low",
    }
    r = requests.post(
        f"{BASE_URL}/api/safety/corrective-actions",
        json=body, headers=_sh(safety_token), timeout=15,
    )
    assert r.status_code in (200, 201), r.text
    cid = r.json()["id"]
    yield cid
    try:
        requests.delete(
            f"{BASE_URL}/api/safety/corrective-actions/{cid}",
            headers=_sh(safety_token), timeout=15,
        )
    except Exception:
        pass


# ── core POST happy path ────────────────────────────────────────────
class TestSignatureCapture:
    def test_capture_employee_signature(self, safety_token, ca_id):
        body = {
            "source_module": "safety.corrective_actions",
            "source_record_id": ca_id,
            "signer_name": f"{TAG} John Worker",
            "signature_type": "employee",
            "signature_image": TINY_PNG_DATA_URL,
        }
        r = requests.post(
            f"{BASE_URL}/api/signatures", json=body,
            headers=_sh(safety_token), timeout=15,
        )
        assert r.status_code == 200, r.text
        sig = r.json()
        assert "id" in sig and isinstance(sig["id"], str)
        assert "created_at" in sig
        assert sig["signer_name"] == body["signer_name"]
        assert sig["signature_type"] == "employee"
        assert sig["source_module"] == "safety.corrective_actions"
        assert sig["source_record_id"] == ca_id
        assert sig["refusal"] is False
        # audit metadata
        assert sig.get("user_agent") is not None
        # ip may be None inside cluster but key must exist
        assert "ip" in sig
        cb = sig.get("created_by") or {}
        assert "role" in cb
        # save for chain test
        pytest.iter154_first_sig_id = sig["id"]

    def test_capture_refusal_valid(self, safety_token, ca_id):
        body = {
            "source_module": "safety.corrective_actions",
            "source_record_id": ca_id,
            "signer_name": f"{TAG} Refuser",
            "signature_type": "employee",
            "refusal": True,
            "refusal_reason": "Disagrees with classification",
        }
        r = requests.post(
            f"{BASE_URL}/api/signatures", json=body,
            headers=_sh(safety_token), timeout=15,
        )
        assert r.status_code == 200, r.text
        sig = r.json()
        assert sig["refusal"] is True
        assert sig["refusal_reason"] == "Disagrees with classification"
        assert sig["signature_image"] is None

    def test_refusal_without_reason_400(self, safety_token, ca_id):
        body = {
            "source_module": "safety.corrective_actions",
            "source_record_id": ca_id,
            "signer_name": f"{TAG} R2",
            "refusal": True,
        }
        r = requests.post(
            f"{BASE_URL}/api/signatures", json=body,
            headers=_sh(safety_token), timeout=15,
        )
        assert r.status_code == 400, r.text
        assert "refusal_reason" in r.text.lower()

    def test_no_image_no_refusal_400(self, safety_token, ca_id):
        body = {
            "source_module": "safety.corrective_actions",
            "source_record_id": ca_id,
            "signer_name": f"{TAG} Empty",
            "refusal": False,
        }
        r = requests.post(
            f"{BASE_URL}/api/signatures", json=body,
            headers=_sh(safety_token), timeout=15,
        )
        assert r.status_code == 400, r.text
        assert "signature_image" in r.text.lower()


# ── pydantic validation ─────────────────────────────────────────────
class TestSignatureValidation:
    def test_bad_source_module_422(self, safety_token, ca_id):
        body = {
            "source_module": "not.a.module",
            "source_record_id": ca_id,
            "signer_name": f"{TAG} X",
            "signature_image": TINY_PNG_DATA_URL,
        }
        r = requests.post(
            f"{BASE_URL}/api/signatures", json=body,
            headers=_sh(safety_token), timeout=15,
        )
        assert r.status_code == 422, r.text

    def test_bad_signature_type_422(self, safety_token, ca_id):
        body = {
            "source_module": "safety.corrective_actions",
            "source_record_id": ca_id,
            "signer_name": f"{TAG} X",
            "signature_type": "bogus",
            "signature_image": TINY_PNG_DATA_URL,
        }
        r = requests.post(
            f"{BASE_URL}/api/signatures", json=body,
            headers=_sh(safety_token), timeout=15,
        )
        assert r.status_code == 422, r.text

    def test_oversize_image_rejected(self, safety_token, ca_id):
        # Build a data URL that exceeds the 1.8MB string guard.
        # 2,100,000 raw chars > 2_000_000 max_length → Pydantic 422 (max_length)
        # OR if max_length is bypassed, runtime check 400.
        huge = "A" * 2_100_000
        body = {
            "source_module": "safety.corrective_actions",
            "source_record_id": ca_id,
            "signer_name": f"{TAG} Huge",
            "signature_image": f"data:image/png;base64,{huge}",
        }
        r = requests.post(
            f"{BASE_URL}/api/signatures", json=body,
            headers=_sh(safety_token), timeout=30,
        )
        # acceptable: 400 or 422 depending on which guard hits first
        assert r.status_code in (400, 422), f"got {r.status_code}: {r.text[:200]}"


# ── supersedes chain ────────────────────────────────────────────────
class TestSupersedesChain:
    def test_supersedes_creates_chain(self, safety_token, ca_id):
        # Capture v1
        b1 = {
            "source_module": "safety.corrective_actions",
            "source_record_id": ca_id,
            "signer_name": f"{TAG} Chain v1",
            "signature_image": TINY_PNG_DATA_URL,
        }
        r1 = requests.post(
            f"{BASE_URL}/api/signatures", json=b1,
            headers=_sh(safety_token), timeout=15,
        )
        assert r1.status_code == 200, r1.text
        v1_id = r1.json()["id"]

        # Capture v2 with supersedes=v1
        b2 = dict(b1, signer_name=f"{TAG} Chain v2", supersedes=v1_id)
        r2 = requests.post(
            f"{BASE_URL}/api/signatures", json=b2,
            headers=_sh(safety_token), timeout=15,
        )
        assert r2.status_code == 200, r2.text
        v2 = r2.json()
        assert v2["supersedes"] == v1_id

        # Default GET should exclude v1 (superseded)
        r_default = requests.get(
            f"{BASE_URL}/api/signatures",
            params={
                "source_module": "safety.corrective_actions",
                "source_record_id": ca_id,
            },
            headers=_sh(safety_token), timeout=15,
        )
        assert r_default.status_code == 200, r_default.text
        ids_default = [d["id"] for d in r_default.json()["items"]]
        assert v2["id"] in ids_default
        assert v1_id not in ids_default, "superseded row leaked into default GET"

        # include_superseded=true should include both, and v1 must be marked
        r_all = requests.get(
            f"{BASE_URL}/api/signatures",
            params={
                "source_module": "safety.corrective_actions",
                "source_record_id": ca_id,
                "include_superseded": "true",
            },
            headers=_sh(safety_token), timeout=15,
        )
        assert r_all.status_code == 200, r_all.text
        items = r_all.json()["items"]
        v1_row = next((d for d in items if d["id"] == v1_id), None)
        assert v1_row is not None
        assert v1_row["superseded_by"] == v2["id"]
        assert v1_row["superseded_at"] is not None


# ── GET list filters + ordering ─────────────────────────────────────
class TestSignatureList:
    def test_list_filtered_and_recent_first(self, safety_token, ca_id):
        r = requests.get(
            f"{BASE_URL}/api/signatures",
            params={
                "source_module": "safety.corrective_actions",
                "source_record_id": ca_id,
            },
            headers=_sh(safety_token), timeout=15,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert "items" in body and "count" in body
        items = body["items"]
        assert body["count"] == len(items)
        assert len(items) >= 1
        # ordering: most-recent first
        ts = [d["created_at"] for d in items]
        assert ts == sorted(ts, reverse=True), "items not sorted desc"
        # all match filter
        for d in items:
            assert d["source_module"] == "safety.corrective_actions"
            assert d["source_record_id"] == ca_id

    def test_list_filter_by_signer_employee_id(self, safety_token, ca_id):
        emp_id = f"{TAG}-emp1"
        # capture one tagged with employee id
        r = requests.post(
            f"{BASE_URL}/api/signatures",
            json={
                "source_module": "safety.corrective_actions",
                "source_record_id": ca_id,
                "signer_name": f"{TAG} EmpFiltered",
                "signer_employee_id": emp_id,
                "signature_image": TINY_PNG_DATA_URL,
            },
            headers=_sh(safety_token), timeout=15,
        )
        assert r.status_code == 200, r.text
        # filter
        r2 = requests.get(
            f"{BASE_URL}/api/signatures",
            params={"signer_employee_id": emp_id},
            headers=_sh(safety_token), timeout=15,
        )
        assert r2.status_code == 200, r2.text
        items = r2.json()["items"]
        assert len(items) >= 1
        for d in items:
            assert d["signer_employee_id"] == emp_id


# ── auth gate ───────────────────────────────────────────────────────
class TestAuthGate:
    def test_no_portal_token_401(self):
        # Bypass conftest's auto-attached X-Admin-Token by explicitly blanking it.
        r = requests.post(
            f"{BASE_URL}/api/signatures",
            json={
                "source_module": "safety.corrective_actions",
                "source_record_id": "anything",
                "signer_name": "x",
                "signature_image": TINY_PNG_DATA_URL,
            },
            headers={"X-Admin-Token": ""},
            timeout=15,
        )
        assert r.status_code == 401, f"expected 401, got {r.status_code}: {r.text[:200]}"

    def test_get_no_portal_token_401(self):
        r = requests.get(
            f"{BASE_URL}/api/signatures",
            headers={"X-Admin-Token": ""},
            timeout=15,
        )
        assert r.status_code == 401, f"expected 401, got {r.status_code}: {r.text[:200]}"
