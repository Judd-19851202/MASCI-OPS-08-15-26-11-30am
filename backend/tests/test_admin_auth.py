"""Admin auth gate tests.

Field crews submit forms publicly, but reads / deletes (the office surface)
are protected by a shared admin password. These tests verify both halves of
that contract — POST stays open, GET/DELETE require the X-Admin-Token
header (or 401), and /api/admin/login mints a token for a correct password.

NOTE: this module deliberately does NOT use the conftest auto-patch when
testing the deny path. We bypass it by passing an explicit headers dict
that overrides the default header.
"""
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


URL = (
    _read_kv(Path("/app/frontend/.env"), "REACT_APP_BACKEND_URL")
    or os.environ.get("REACT_APP_BACKEND_URL", "")
).rstrip("/")
PASSWORD = _read_kv(Path("/app/backend/.env"), "ADMIN_PASSWORD")
API = f"{URL}/api"


# Sentinel that overrides the conftest auto-attached header.
_NO_AUTH = {"X-Admin-Token": ""}


class TestAdminLogin:
    def test_login_correct_password_returns_token(self):
        r = requests.post(
            f"{API}/admin/login",
            json={"password": PASSWORD},
            timeout=10,
        )
        assert r.status_code == 200
        body = r.json()
        assert body["ok"] is True
        assert isinstance(body["token"], str) and len(body["token"]) >= 20

    def test_login_wrong_password_returns_401(self):
        r = requests.post(
            f"{API}/admin/login",
            json={"password": "definitely-not-the-password"},
            timeout=10,
            headers=_NO_AUTH,
        )
        assert r.status_code == 401

    def test_login_missing_password_returns_422(self):
        r = requests.post(
            f"{API}/admin/login",
            json={},
            timeout=10,
            headers=_NO_AUTH,
        )
        assert r.status_code in (400, 422)


class TestAdminGate:
    @pytest.mark.parametrize(
        "path",
        [
            "/inspections",
            "/meetings",
            "/jhas",
            "/incidents",
            "/daily-reports",
        ],
    )
    def test_list_without_token_returns_401(self, path):
        r = requests.get(f"{API}{path}", headers=_NO_AUTH, timeout=10)
        assert r.status_code == 401

    @pytest.mark.parametrize(
        "path",
        [
            "/inspections/00000000-0000-0000-0000-000000000000",
            "/meetings/00000000-0000-0000-0000-000000000000",
            "/jhas/00000000-0000-0000-0000-000000000000",
            "/incidents/00000000-0000-0000-0000-000000000000",
            "/daily-reports/00000000-0000-0000-0000-000000000000",
        ],
    )
    def test_get_single_without_token_returns_401(self, path):
        r = requests.get(f"{API}{path}", headers=_NO_AUTH, timeout=10)
        assert r.status_code == 401

    @pytest.mark.parametrize(
        "path",
        [
            "/inspections/some-id",
            "/meetings/some-id",
            "/jhas/some-id",
            "/incidents/some-id",
            "/daily-reports/some-id",
        ],
    )
    def test_delete_without_token_returns_401(self, path):
        r = requests.delete(f"{API}{path}", headers=_NO_AUTH, timeout=10)
        assert r.status_code == 401

    def test_admin_check_endpoint_requires_token(self):
        r = requests.get(f"{API}/admin/check", headers=_NO_AUTH, timeout=10)
        assert r.status_code == 401

    def test_admin_check_with_token_returns_200(self):
        # Token is auto-attached by conftest
        r = requests.get(f"{API}/admin/check", timeout=10)
        assert r.status_code == 200
        assert r.json()["ok"] is True


class TestPublicPostStaysOpen:
    """POST endpoints must remain public — field crews don't log in.

    iter236 exception: `/api/inspections` POST moved fully under Safety
    portal ownership and now requires Safety or Admin auth. The remaining
    POST endpoints (translate, meetings, daily-reports, etc.) stay public.
    """

    def test_post_inspection_without_token_now_requires_safety_or_admin(self):
        """iter236 — Site Inspection submission is no longer public; it
        requires Safety or Admin auth. Without a token, the endpoint must
        return 401 (not 200, not 500)."""
        payload = {
            "project_name": "TEST_AUTH_OPEN_INSP",
            "location": "Test",
            "inspection_date": "2026-04-26",
            "inspection_time": "09:00",
            "inspector_name": "Test",
            "foreman_name": "Test",
            "work_activity": "Test",
        }
        r = requests.post(
            f"{API}/inspections", json=payload, headers=_NO_AUTH, timeout=10
        )
        assert r.status_code == 401, r.text

    def test_post_inspection_with_admin_token_succeeds(self):
        """Admin token (auto-attached by conftest) satisfies the iter236
        Safety-or-Admin gate on Site Inspection submission."""
        payload = {
            "project_name": "TEST_AUTH_OPEN_INSP",
            "location": "Test",
            "inspection_date": "2026-04-26",
            "inspection_time": "09:00",
            "inspector_name": "Test",
            "foreman_name": "Test",
            "work_activity": "Test",
        }
        r = requests.post(f"{API}/inspections", json=payload, timeout=10)
        assert r.status_code == 200, r.text
        rid = r.json()["id"]
        # Cleanup with admin token (auto-attached)
        requests.delete(f"{API}/inspections/{rid}", timeout=10)

    def test_post_translate_without_token_succeeds(self):
        r = requests.post(
            f"{API}/translate",
            json={"from_lang": "en", "to_lang": "en", "strings": {"a": "test"}},
            headers=_NO_AUTH,
            timeout=10,
        )
        assert r.status_code == 200
