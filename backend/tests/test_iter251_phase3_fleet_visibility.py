"""iter251 Phase 3 — Fleet visibility surfaces backend tests."""
import os
import hmac
import hashlib
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://safety-audit-mobile-1.preview.emergentagent.com").rstrip("/")


def _admin_token():
    # Derive via the documented login endpoint to avoid epoch/secret drift.
    r = requests.post(f"{BASE_URL}/api/admin/login", json={"password": "MASCI1982!"}, timeout=15)
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text[:200]}"
    return r.json()["token"]


@pytest.fixture(scope="module")
def admin_token():
    return _admin_token()


class TestSeverityReferencePDF:
    """GET /api/admin/fleet/severity-reference-card.pdf"""

    def test_pdf_returns_200_and_pdf_bytes(self, admin_token):
        r = requests.get(
            f"{BASE_URL}/api/admin/fleet/severity-reference-card.pdf",
            headers={"X-Admin-Token": admin_token},
            timeout=30,
        )
        assert r.status_code == 200, f"PDF endpoint not 200: {r.status_code} body={r.text[:300]}"
        ct = r.headers.get("content-type", "")
        assert "application/pdf" in ct, f"Wrong content-type: {ct}"
        assert r.content[:5] == b"%PDF-", "Not a valid PDF (no %PDF- magic)"
        assert len(r.content) >= 5 * 1024, f"PDF too small: {len(r.content)} bytes"

    def test_severity_version_header(self, admin_token):
        r = requests.get(
            f"{BASE_URL}/api/admin/fleet/severity-reference-card.pdf",
            headers={"X-Admin-Token": admin_token},
            timeout=30,
        )
        assert r.status_code == 200
        sv = r.headers.get("x-severity-version") or r.headers.get("X-Severity-Version")
        assert sv == "v1.3-approved-2026-05-19", f"Bad X-Severity-Version: {sv}"

    def test_filename_includes_version(self, admin_token):
        r = requests.get(
            f"{BASE_URL}/api/admin/fleet/severity-reference-card.pdf",
            headers={"X-Admin-Token": admin_token},
            timeout=30,
        )
        cd = r.headers.get("content-disposition", "")
        assert "v1.3-approved-2026-05-19" in cd, f"Version not in filename header: {cd}"

    def test_pdf_requires_admin(self):
        r = requests.get(f"{BASE_URL}/api/admin/fleet/severity-reference-card.pdf", timeout=15)
        assert r.status_code in (401, 403), f"Unprotected PDF endpoint: {r.status_code}"


class TestFleetByUnit:
    """GET /api/shop/fleet/by-unit"""

    def test_by_unit_returns_200_with_shape(self, admin_token):
        r = requests.get(
            f"{BASE_URL}/api/shop/fleet/by-unit",
            headers={"X-Admin-Token": admin_token},
            timeout=20,
        )
        assert r.status_code == 200, f"by-unit not 200: {r.status_code} body={r.text[:300]}"
        j = r.json()
        for key in ("count_units", "count_defects", "groups"):
            assert key in j, f"Missing key {key} in response: {list(j.keys())}"
        assert isinstance(j["groups"], list)
        assert isinstance(j["count_units"], int)
        assert isinstance(j["count_defects"], int)

    def test_groups_ordered_oos_first(self, admin_token):
        r = requests.get(
            f"{BASE_URL}/api/shop/fleet/by-unit",
            headers={"X-Admin-Token": admin_token},
            timeout=20,
        )
        groups = r.json().get("groups", [])
        if len(groups) < 2:
            pytest.skip(f"Need >=2 groups to verify ordering; got {len(groups)}")
        # OOS-bearing units must come before non-OOS units in the list
        seen_non_oos = False
        for g in groups:
            if g.get("open_oos_count", 0) > 0:
                assert not seen_non_oos, f"OOS unit {g.get('unit_number')} appeared after a non-OOS unit"
            else:
                seen_non_oos = True

    def test_group_has_required_unit_fields(self, admin_token):
        r = requests.get(
            f"{BASE_URL}/api/shop/fleet/by-unit",
            headers={"X-Admin-Token": admin_token},
            timeout=20,
        )
        groups = r.json().get("groups", [])
        if not groups:
            pytest.skip("No defects in fleet yet — cannot verify group fields")
        g = groups[0]
        for f in ("unit_number", "open_oos_count", "open_monitor_count", "defects"):
            assert f in g, f"group missing field {f}: keys={list(g.keys())}"
        # Optional enrichment fields — at least should be present (even if null)
        for f in ("truck_status", "make_model", "plate"):
            assert f in g, f"group missing enrichment field {f}: keys={list(g.keys())}"

    def test_defect_has_driver_note_and_required_fields(self, admin_token):
        r = requests.get(
            f"{BASE_URL}/api/shop/fleet/by-unit",
            headers={"X-Admin-Token": admin_token},
            timeout=20,
        )
        groups = r.json().get("groups", [])
        all_defects = [d for g in groups for d in g.get("defects", [])]
        if not all_defects:
            pytest.skip("No defects to verify field schema")
        d = all_defects[0]
        required = ["severity", "checklist_item", "driver_note", "photos",
                    "reported_at", "status", "reported_by_driver_name"]
        missing = [k for k in required if k not in d]
        assert not missing, f"defect missing fields: {missing}; available={list(d.keys())}"
        # severity must be one of expected values
        assert d["severity"] in ("oos", "monitor"), f"unexpected severity {d['severity']}"

    def test_by_unit_requires_token(self):
        r = requests.get(f"{BASE_URL}/api/shop/fleet/by-unit", timeout=15)
        assert r.status_code in (401, 403), f"Unprotected by-unit endpoint: {r.status_code}"


class TestPortalRoutesRender:
    """Frontend routes return HTML 200 for the 3 fleet visibility scopes."""

    @pytest.mark.parametrize("path", ["/shop/fleet", "/dispatch-portal/fleet", "/safety-portal/fleet"])
    def test_route_html_loads(self, path):
        r = requests.get(f"{BASE_URL}{path}", timeout=15)
        assert r.status_code == 200, f"{path} did not load: {r.status_code}"
        assert "<div id=\"root\"" in r.text or "react" in r.text.lower(), "Not a React SPA shell"
