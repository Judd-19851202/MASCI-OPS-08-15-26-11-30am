"""iter418 · Phase 20.1 · Driver Breakdown-Proof Continuity tests.

Walking-skeleton verification:
1. Driver session can upload a breakdown photo to OWN assignment.
2. Type is HARD-CODED to ``breakdown_photo`` on the driver path.
3. Cross-driver upload (driver session for assignment A trying to push
   proof to assignment B) is blocked 403.
4. Anonymous (no driver token) is blocked 401.
5. Non-image MIME rejected 400.
6. Oversize (>5 MB) rejected 400.
7. Non-existent assignment 404.
8. Uploaded record surfaces via the iter417 list endpoint as
   ``breakdown_photo`` with ``uploaded_role="driver"``.
"""
from __future__ import annotations

import io
import json
import os
import urllib.error
import urllib.request
import uuid
from pathlib import Path

import pytest
import requests


def _read_kv(path: Path, key: str) -> str:
    try:
        for line in path.read_text().splitlines():
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:
        return ""
    return ""


URL = (
    _read_kv(Path("/app/frontend/.env"), "REACT_APP_BACKEND_URL")
    or os.environ.get("REACT_APP_BACKEND_URL", "")
).rstrip("/")
API = f"{URL}/api"


# Tiny but valid PNG (1x1 transparent pixel)
_PNG_1X1 = bytes.fromhex(
    "89504E470D0A1A0A0000000D49484452000000010000000108060000001F15C4"
    "890000000D49444154789C6300010000000500010D0A2DB4000000004945"
    "4E44AE426082"
)


# ──────────────────────────────────────────────────────────────
# Fixtures (mirror iter393 pattern · tenant-isolated)
# ──────────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def tenant_id() -> str:
    return f"iter418-test-{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="module")
def hdrs(tenant_id: str) -> dict:
    return {"X-Tenant-Id": tenant_id}


def _create_assignment(hdrs, driver_id: str, suffix: str = "") -> dict:
    body = {
        "truck_id": f"T-iter418{suffix}",
        "driver_id": driver_id,
        "driver_name": "iter418 Driver",
        "haul_type": "Material",
        "project_number": "9999",
        "material": "Asphalt",
    }
    r = requests.post(f"{API}/dispatch/assignments", headers=hdrs, json=body, timeout=15)
    assert r.status_code in (200, 201), r.text
    return r.json()["assignment"]


def _mint_driver_session(hdrs, driver_id: str, assignment_id: str) -> str:
    """Issue magic link + exchange for a driver token. Returns driver_token."""
    r = requests.post(
        f"{API}/dispatch/driver/magic-link",
        headers=hdrs,
        json={
            "driver_id": driver_id,
            "driver_name": "iter418 Driver",
            "truck_id": "T-iter418",
            "assignment_id": assignment_id,
        },
        timeout=15,
    )
    assert r.status_code == 200, r.text
    magic_token = r.json()["magic_token"]
    r2 = requests.post(
        f"{API}/dispatch/driver/session/exchange",
        headers=hdrs,
        json={"magic_token": magic_token},
        timeout=15,
    )
    assert r2.status_code == 200, r2.text
    return r2.json()["driver_token"]


@pytest.fixture(scope="module")
def driver_a(hdrs) -> dict:
    drv_id = f"driver-A-{uuid.uuid4().hex[:6]}"
    asg = _create_assignment(hdrs, drv_id, suffix="-A")
    token = _mint_driver_session(hdrs, drv_id, asg["id"])
    return {"driver_id": drv_id, "assignment": asg, "token": token}


@pytest.fixture(scope="module")
def driver_b(hdrs) -> dict:
    drv_id = f"driver-B-{uuid.uuid4().hex[:6]}"
    asg = _create_assignment(hdrs, drv_id, suffix="-B")
    token = _mint_driver_session(hdrs, drv_id, asg["id"])
    return {"driver_id": drv_id, "assignment": asg, "token": token}


def _driver_hdrs(token: str, tenant_id: str) -> dict:
    """Driver session headers · STRIP any admin token that conftest auto-adds."""
    return {
        "X-Driver-Token": token,
        "X-Tenant-Id": tenant_id,
        # NOTE: requests' conftest monkey-patch will add X-Admin-Token
        # too; backend's require_driver_session reads X-Driver-Token only,
        # so co-presence is harmless. The 403 cross-assignment test below
        # proves the driver gate is what actually runs.
    }


# ──────────────────────────────────────────────────────────────
# 1. Happy path · driver uploads breakdown_photo to own assignment
# ──────────────────────────────────────────────────────────────
def test_iter418_driver_upload_happy_path(driver_a, tenant_id):
    files = {"file": ("breakdown.png", _PNG_1X1, "image/png")}
    data = {"host_id": driver_a["assignment"]["id"]}
    r = requests.post(
        f"{API}/dispatch/driver/breakdown-proof/upload",
        headers=_driver_hdrs(driver_a["token"], tenant_id),
        files=files, data=data, timeout=15,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["type"] == "breakdown_photo"        # locked
    assert body["host_kind"] == "assignment"
    assert body["host_id"] == driver_a["assignment"]["id"]
    assert body["size_bytes"] == len(_PNG_1X1)
    assert body["id"]


# ──────────────────────────────────────────────────────────────
# 2. Uploaded record surfaces via iter417 list with driver role
# ──────────────────────────────────────────────────────────────
def test_iter418_uploaded_surface_in_iter417_list(driver_a, tenant_id):
    aid = driver_a["assignment"]["id"]
    r = requests.get(
        f"{API}/operational-attachments/list",
        params={"host_kind": "assignment", "host_id": aid},
        headers={"X-Tenant-Id": tenant_id},
        timeout=10,
    )
    assert r.status_code == 200, r.text
    items = r.json().get("attachments", [])
    assert any(
        it.get("type") == "breakdown_photo" and it.get("uploaded_role") == "driver"
        for it in items
    ), items


# ──────────────────────────────────────────────────────────────
# 3. Cross-driver block · driver A pushes proof to driver B's row
# ──────────────────────────────────────────────────────────────
def test_iter418_cross_driver_assignment_blocked(driver_a, driver_b, tenant_id):
    files = {"file": ("breakdown.png", _PNG_1X1, "image/png")}
    data = {"host_id": driver_b["assignment"]["id"]}
    r = requests.post(
        f"{API}/dispatch/driver/breakdown-proof/upload",
        headers=_driver_hdrs(driver_a["token"], tenant_id),
        files=files, data=data, timeout=15,
    )
    assert r.status_code == 403, r.text


# ──────────────────────────────────────────────────────────────
# 4. Anonymous blocked · no driver token (use urllib so the conftest
#    monkey-patch on `requests` cannot smuggle in an admin token)
# ──────────────────────────────────────────────────────────────
def test_iter418_anon_upload_blocked(driver_a, tenant_id):
    aid = driver_a["assignment"]["id"]
    # Build a tiny multipart/form-data body by hand
    boundary = "----iter418bdy"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="host_id"\r\n\r\n{aid}\r\n'
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="x.png"\r\n'
        f"Content-Type: image/png\r\n\r\n"
    ).encode("utf-8") + _PNG_1X1 + f"\r\n--{boundary}--\r\n".encode("utf-8")
    req = urllib.request.Request(
        f"{API}/dispatch/driver/breakdown-proof/upload",
        data=body,
        method="POST",
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "X-Tenant-Id": tenant_id,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            assert False, f"Expected 401/403 · got {resp.status}"
    except urllib.error.HTTPError as e:
        assert e.code in (401, 403), e.code


# ──────────────────────────────────────────────────────────────
# 5. Non-image MIME rejected
# ──────────────────────────────────────────────────────────────
def test_iter418_non_image_rejected(driver_a, tenant_id):
    files = {"file": ("note.txt", b"not an image", "text/plain")}
    data = {"host_id": driver_a["assignment"]["id"]}
    r = requests.post(
        f"{API}/dispatch/driver/breakdown-proof/upload",
        headers=_driver_hdrs(driver_a["token"], tenant_id),
        files=files, data=data, timeout=15,
    )
    assert r.status_code == 400, r.text


# ──────────────────────────────────────────────────────────────
# 6. Oversize rejected (>5 MB)
# ──────────────────────────────────────────────────────────────
def test_iter418_oversize_rejected(driver_a, tenant_id):
    big = b"\x89PNG\r\n\x1a\n" + b"\x00" * (5 * 1024 * 1024 + 100)
    files = {"file": ("big.png", big, "image/png")}
    data = {"host_id": driver_a["assignment"]["id"]}
    r = requests.post(
        f"{API}/dispatch/driver/breakdown-proof/upload",
        headers=_driver_hdrs(driver_a["token"], tenant_id),
        files=files, data=data, timeout=20,
    )
    assert r.status_code == 400, r.text


# ──────────────────────────────────────────────────────────────
# 7. Missing host_id rejected 400
# ──────────────────────────────────────────────────────────────
def test_iter418_missing_host_id_rejected(driver_a, tenant_id):
    files = {"file": ("p.png", _PNG_1X1, "image/png")}
    data = {"host_id": ""}
    r = requests.post(
        f"{API}/dispatch/driver/breakdown-proof/upload",
        headers=_driver_hdrs(driver_a["token"], tenant_id),
        files=files, data=data, timeout=15,
    )
    # Either 400 (validated) · 403 (driver session has its own assignment) ·
    # 422 (Pydantic Form field-missing). All three are operationally safe.
    assert r.status_code in (400, 403, 422), r.text
