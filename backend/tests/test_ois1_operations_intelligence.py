"""OIS-1 · Operations Intelligence backend contract tests.

Covers:
  · GET /api/operations/intelligence              (OIS-1E)
  · GET /api/operations/intelligence/shop         (OIS-1D)
  · GET /api/operations/intelligence/fleet-gps    (OIS-1A)
  · GET /api/operations/intelligence/driver/{key} (OIS-1C)

All four are admin-strict (X-Admin-Token required).
"""
import os
import requests
import pytest
from pathlib import Path


def _read_kv(path, key):
    try:
        with open(path) as f:
            for line in f:
                if line.startswith(f"{key}="):
                    return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:
        return ""
    return ""


BASE_URL = (
    _read_kv(Path("/app/frontend/.env"), "REACT_APP_BACKEND_URL")
    or os.environ.get("REACT_APP_BACKEND_URL", "")
).rstrip("/")
ADMIN_PASSWORD = _read_kv(Path("/app/backend/.env"), "ADMIN_PASSWORD")


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(
        f"{BASE_URL}/api/admin/login",
        json={"password": ADMIN_PASSWORD},
        timeout=15,
    )
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text[:200]}"
    tok = r.json().get("token")
    assert tok
    return tok


@pytest.fixture(scope="module")
def H(admin_token):
    return {"X-Admin-Token": admin_token}


# OIS-1E · single-pane payload
class TestOIS1E_OperationsIntelligence:
    def test_admin_strict_no_token_rejected(self):
        r = requests.get(
            f"{BASE_URL}/api/operations/intelligence",
            timeout=15,
            headers={"X-Admin-Token": "not-a-real-token"},
        )
        # backend's require_admin rejects with 401 (or 403)
        assert r.status_code in (401, 403), f"got {r.status_code}: {r.text[:200]}"

    def test_payload_shape(self, H):
        r = requests.get(
            f"{BASE_URL}/api/operations/intelligence", headers=H, timeout=20
        )
        assert r.status_code == 200, r.text[:300]
        data = r.json()
        for k in (
            "fleet",
            "drivers",
            "equipment",
            "safety",
            "geofences",
            "recent_high_priority",
            "gps_band_thresholds",
        ):
            assert k in data, f"missing key {k}"

        # fleet rollups
        fleet = data["fleet"]
        for k in ("gps_total", "moving", "idle", "not_reporting"):
            assert k in fleet and isinstance(fleet[k], int)

        # drivers / equipment / safety counts
        assert {"active", "deactivated_in_motive", "hos_violations_24h"} <= set(
            data["drivers"]
        )
        assert {
            "critical_faults_open_24h",
            "gateways_offline_24h",
            "dvir_critical_24h",
        } <= set(data["equipment"])
        assert "high_severity_events_24h" in data["safety"]

        # thresholds match backend constants
        thr = data["gps_band_thresholds"]
        assert thr["green_max_minutes"] == 30
        assert thr["amber_max_minutes"] == 24 * 60

        # recent feed is a list (may be empty)
        assert isinstance(data["recent_high_priority"], list)


# OIS-1D · shop slice
class TestOIS1D_ShopIntelligence:
    def test_admin_strict(self):
        r = requests.get(
            f"{BASE_URL}/api/operations/intelligence/shop", timeout=15, headers={"X-Admin-Token": "not-a-real-token"}
        )
        assert r.status_code in (401, 403)

    def test_payload_shape(self, H):
        r = requests.get(
            f"{BASE_URL}/api/operations/intelligence/shop", headers=H, timeout=20
        )
        assert r.status_code == 200, r.text[:300]
        data = r.json()
        for k in (
            "critical_faults_open",
            "gateway_offline",
            "dvir_defects",
            "recent_fault_closures",
            "equipment_not_reporting",
            "counts",
        ):
            assert k in data, f"missing key {k}"
            if k != "counts":
                assert isinstance(data[k], list)

        counts = data["counts"]
        for k in (
            "critical_faults_open",
            "gateway_offline",
            "dvir_defects",
            "recent_fault_closures",
            "equipment_not_reporting",
        ):
            assert k in counts and isinstance(counts[k], int)
            # counts must equal list length
            assert counts[k] == len(data[k])

        # not_reporting entries shape
        for row in data["equipment_not_reporting"][:5]:
            assert "unit_number" in row
            assert "band" in row
            assert row["band"] in ("red", "amber", "green")


# OIS-1A · per-asset fleet-gps
class TestOIS1A_FleetGPS:
    def test_admin_strict(self):
        r = requests.get(
            f"{BASE_URL}/api/operations/intelligence/fleet-gps", timeout=15, headers={"X-Admin-Token": "not-a-real-token"}
        )
        assert r.status_code in (401, 403)

    def test_payload_shape(self, H):
        r = requests.get(
            f"{BASE_URL}/api/operations/intelligence/fleet-gps", headers=H, timeout=20
        )
        assert r.status_code == 200, r.text[:300]
        data = r.json()
        assert "assets" in data and isinstance(data["assets"], list)
        assert "count" in data
        assert data["count"] == len(data["assets"])
        assert "gps_band_thresholds" in data

        # Sample first row shape
        if data["assets"]:
            row = data["assets"][0]
            for k in (
                "unit_number",
                "vehicle_id",
                "band",
                "label",
                "minutes",
                "located_at",
                "speed_kph",
                "moving",
                "gps_enabled",
            ):
                assert k in row, f"row missing key {k}"
            assert row["band"] in ("red", "amber", "green")

        # Spec note: smoke screenshots showed 18 mapped vehicles for DispatchBoard
        # but fleet-gps returns ALL Motive-mapped assets — must be non-empty
        assert data["count"] > 0


# OIS-1C · driver intel
class TestOIS1C_DriverIntel:
    def test_admin_strict(self):
        r = requests.get(
            f"{BASE_URL}/api/operations/intelligence/driver/foo",
            timeout=15,
            headers={"X-Admin-Token": "not-a-real-token"},
        )
        assert r.status_code in (401, 403)

    def test_unknown_driver_returns_zero_counts(self, H):
        r = requests.get(
            f"{BASE_URL}/api/operations/intelligence/driver/__nope__not_real__",
            headers=H,
            timeout=20,
        )
        assert r.status_code == 200, r.text[:300]
        data = r.json()
        assert data["mapping"] is None
        assert data["counts_30d"]["hos_violations"] == 0
        assert data["counts_30d"]["harsh_events"] == 0
        assert data["counts_30d"]["dvir_inspections"] == 0
        assert data["counts_24h"]["hos_violations"] == 0
        assert data["counts_24h"]["harsh_events_high"] == 0
        assert isinstance(data["recent_events"], list)

    def test_known_driver_via_motive_or_masci_key(self, H):
        # Find a real mapping to drive both lookup paths
        r = requests.get(
            f"{BASE_URL}/api/employees/mappings?provider=motive&limit=5",
            headers=H,
            timeout=20,
        )
        # mapping list endpoint may not match this exact path — try a few
        candidates = []
        if r.status_code == 200:
            try:
                payload = r.json()
                if isinstance(payload, list):
                    candidates = payload
                elif isinstance(payload, dict):
                    candidates = (
                        payload.get("items")
                        or payload.get("mappings")
                        or payload.get("data")
                        or []
                    )
            except Exception:
                candidates = []

        if not candidates:
            pytest.skip(
                "no employee mapping list endpoint to discover a real driver key"
            )

        motive_key = None
        masci_key = None
        for c in candidates:
            mv = (c or {}).get("motive") or {}
            uid = mv.get("user_id") or mv.get("id")
            mid = c.get("masci_employee_id")
            if uid:
                motive_key = str(uid)
            if mid:
                masci_key = str(mid)
            if motive_key or masci_key:
                break

        if not (motive_key or masci_key):
            pytest.skip("no usable driver key in mappings sample")

        for key in [k for k in (motive_key, masci_key) if k]:
            rr = requests.get(
                f"{BASE_URL}/api/operations/intelligence/driver/{key}",
                headers=H,
                timeout=20,
            )
            assert rr.status_code == 200, rr.text[:300]
            data = rr.json()
            assert data["driver_key"] == key
            # mapping must resolve for at least one of the two key forms
            assert data["mapping"] is not None or data["motive_user_id"] != ""
