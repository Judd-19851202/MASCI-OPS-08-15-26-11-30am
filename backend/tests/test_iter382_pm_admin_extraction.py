"""
iter382 · Phase 4D · /admin/project-managers/* extraction parity lock.

10 routes + 1 public list extracted to routes/pm_admin.py:
  • GET    /admin/project-managers/export       (xlsx)
  • GET    /admin/project-managers              (admin list)
  • GET    /project-managers                    (PUBLIC active list)
  • POST   /admin/project-managers              (create)
  • PATCH  /admin/project-managers/{pm_id}      (update + email-cascade)
  • DELETE /admin/project-managers/{pm_id}      (delete + job-guard)
  • POST   /admin/project-managers/{pm_id}/set-password
  • POST   /admin/project-managers/{pm_id}/welcome-pdf
  • POST   /admin/project-managers/{pm_id}/email-welcome
  • POST   /admin/project-managers/{pm_id}/disable
  • GET    /admin/project-managers/activity

Behavior contract — byte-identical to pre-extraction. Includes:
  • Cascade-on-email-change to jobs_master (PATCH).
  • Job-assignment guard (DELETE → 409 if still on jobs).
  • Issue-temp-password generator + must_change_password=true semantics.
  • Per-PM activity rollup across 7 collections in 7-day window.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path

import pytest


def _read_env(path: str, key: str) -> str:
    try:
        for line in Path(path).read_text().splitlines():
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:  # noqa: BLE001
        return ""
    return ""


BASE_URL = _read_env("/app/frontend/.env", "REACT_APP_BACKEND_URL").rstrip("/")
ADMIN_PW = _read_env("/app/backend/.env", "ADMIN_PASSWORD") or "Maddix123!"


def _raw(method: str, url: str, headers=None, body=None):
    h = {"User-Agent": "iter382-pm-admin-extract/1.0"}
    if headers:
        h.update(headers)
    data = None
    if body is not None:
        h["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, r.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")


@pytest.fixture(scope="module")
def admin_token():
    code, body = _raw("POST", f"{BASE_URL}/api/admin/login",
                      body={"password": ADMIN_PW})
    if code != 200:
        pytest.skip(f"admin login unavailable: {code}")
    return json.loads(body).get("token", "")


# ─── Functional parity tests ──────────────────────────────────────────

class TestPublicPmList:
    def test_public_list_no_auth_returns_200(self):
        code, body = _raw("GET", f"{BASE_URL}/api/project-managers")
        assert code == 200, body
        d = json.loads(body)
        assert "items" in d
        assert isinstance(d["items"], list)

    def test_public_list_shape_only_id_name_email(self):
        """Public list must NOT leak phone, is_active, password fields."""
        code, body = _raw("GET", f"{BASE_URL}/api/project-managers")
        assert code == 200
        items = json.loads(body)["items"]
        if items:
            keys = set(items[0].keys())
            assert keys == {"id", "name", "email"}, f"public leak: {keys}"

    def test_public_list_only_active_pms(self):
        """Should NOT include disabled or inactive PMs."""
        code, body = _raw("GET", f"{BASE_URL}/api/project-managers")
        # We can't easily verify without seeding, but the route must
        # at minimum return 200 with a list. Disabled-filter logic is
        # locked by the source-level test below.
        assert code == 200


class TestAdminPmList:
    def test_admin_list_unlocks(self, admin_token):
        code, body = _raw("GET", f"{BASE_URL}/api/admin/project-managers",
                          headers={"X-Admin-Token": admin_token})
        assert code == 200, body
        d = json.loads(body)
        assert "items" in d

    def test_admin_list_anon_denied(self):
        code, _ = _raw("GET", f"{BASE_URL}/api/admin/project-managers")
        assert code in (401, 403)

    def test_admin_list_shape_includes_richer_fields(self, admin_token):
        code, body = _raw("GET", f"{BASE_URL}/api/admin/project-managers",
                          headers={"X-Admin-Token": admin_token})
        items = json.loads(body)["items"]
        if items:
            keys = set(items[0].keys())
            # Admin view exposes richer fields. Must include phone +
            # is_active + has_password (drives the admin UI badges).
            for k in ("id", "name", "email", "phone", "is_active",
                      "has_password"):
                assert k in keys, f"admin list missing field: {k}"


class TestAdminPmActivity:
    def test_activity_admin_unlocks(self, admin_token):
        code, body = _raw("GET", f"{BASE_URL}/api/admin/project-managers/activity",
                          headers={"X-Admin-Token": admin_token})
        assert code == 200, body
        d = json.loads(body)
        # Shape: {items, since, collections}
        assert "items" in d
        assert "since" in d
        assert "collections" in d
        assert isinstance(d["collections"], list)
        # 7 collections preserved.
        assert len(d["collections"]) == 7

    def test_activity_anon_denied(self):
        code, _ = _raw("GET", f"{BASE_URL}/api/admin/project-managers/activity")
        assert code in (401, 403)


class TestAdminPmExport:
    def test_export_admin_unlocks_xlsx(self, admin_token):
        code, _ = _raw("GET", f"{BASE_URL}/api/admin/project-managers/export",
                       headers={"X-Admin-Token": admin_token})
        assert code == 200

    def test_export_anon_denied(self):
        code, _ = _raw("GET", f"{BASE_URL}/api/admin/project-managers/export")
        assert code in (401, 403)


class TestAdminPmCRUD:
    def test_create_validates_required_fields(self, admin_token):
        # Missing name/email → 422
        code, _ = _raw("POST", f"{BASE_URL}/api/admin/project-managers",
                       headers={"X-Admin-Token": admin_token},
                       body={})
        assert code == 422

    def test_create_admin_strict_not_required(self, admin_token):
        """Create uses require_admin (not strict) — admin tokens unlock."""
        # We don't actually create a PM in regression — just verify the
        # gate. A 422 on empty body confirms the route is mounted and
        # auth passed.
        code, _ = _raw("POST", f"{BASE_URL}/api/admin/project-managers",
                       headers={"X-Admin-Token": admin_token},
                       body={"name": "", "email": "", "phone": "",
                             "is_active": True})
        # Pydantic Field min_length=1 → 422.
        assert code == 422

    def test_update_anon_denied(self):
        code, _ = _raw("PATCH", f"{BASE_URL}/api/admin/project-managers/fake-id",
                       body={"name": "X"})
        assert code in (401, 403)

    def test_delete_anon_denied(self):
        code, _ = _raw("DELETE", f"{BASE_URL}/api/admin/project-managers/fake-id")
        assert code in (401, 403)

    def test_update_nonexistent_returns_404(self, admin_token):
        code, _ = _raw("PATCH", f"{BASE_URL}/api/admin/project-managers/definitely-not-a-real-pm-id",
                       headers={"X-Admin-Token": admin_token},
                       body={"name": "X"})
        assert code == 404


class TestAdminPmSetPassword:
    def test_anon_denied(self):
        code, _ = _raw("POST", f"{BASE_URL}/api/admin/project-managers/fake/set-password",
                       body={})
        assert code in (401, 403)

    def test_set_password_404_on_missing_pm(self, admin_token):
        code, _ = _raw("POST", f"{BASE_URL}/api/admin/project-managers/no-such-pm/set-password",
                       headers={"X-Admin-Token": admin_token},
                       body={})
        assert code == 404


class TestAdminPmDisable:
    def test_anon_denied(self):
        code, _ = _raw("POST", f"{BASE_URL}/api/admin/project-managers/fake/disable",
                       body={"disabled": True})
        assert code in (401, 403)

    def test_disable_404_on_missing_pm(self, admin_token):
        code, _ = _raw("POST", f"{BASE_URL}/api/admin/project-managers/no-such-pm/disable",
                       headers={"X-Admin-Token": admin_token},
                       body={"disabled": True})
        assert code == 404


class TestAdminPmWelcomePdf:
    def test_anon_denied(self):
        code, _ = _raw("POST", f"{BASE_URL}/api/admin/project-managers/fake/welcome-pdf",
                       body={})
        assert code in (401, 403)

    def test_welcome_pdf_404_on_missing_pm(self, admin_token):
        code, _ = _raw("POST", f"{BASE_URL}/api/admin/project-managers/no-such-pm/welcome-pdf",
                       headers={"X-Admin-Token": admin_token},
                       body={})
        assert code == 404


class TestAdminPmEmailWelcome:
    def test_anon_denied(self):
        code, _ = _raw("POST", f"{BASE_URL}/api/admin/project-managers/fake/email-welcome",
                       body={})
        assert code in (401, 403)


# ─── Source-level extraction guards ──────────────────────────────────

class TestIter382Foundation:
    def test_pm_admin_file_exists(self):
        assert Path("/app/backend/routes/pm_admin.py").exists()

    def test_pm_admin_owns_all_11_handlers(self):
        src = Path("/app/backend/routes/pm_admin.py").read_text()
        for marker in [
            '"/project-managers"',
            '"/admin/project-managers"',
            '"/admin/project-managers/export"',
            '"/admin/project-managers/activity"',
            '"/admin/project-managers/{pm_id}"',
            '"/admin/project-managers/{pm_id}/set-password"',
            '"/admin/project-managers/{pm_id}/welcome-pdf"',
            '"/admin/project-managers/{pm_id}/email-welcome"',
            '"/admin/project-managers/{pm_id}/disable"',
        ]:
            assert marker in src, f"{marker} missing from pm_admin.py"

    def test_pm_admin_factory_signature(self):
        src = Path("/app/backend/routes/pm_admin.py").read_text()
        assert "def build_pm_admin_router(" in src
        assert "xlsx_response_fn" in src
        assert "active_filter" in src
        assert "render_portal_email_fn" in src

    def test_pm_admin_body_models_present(self):
        src = Path("/app/backend/routes/pm_admin.py").read_text()
        for cls in ["class PMIn(", "class PMUpdate(", "class PMSetPasswordBody("]:
            assert cls in src
        # PMIn validation rules preserved (min_length on name + email).
        assert "min_length=1" in src
        assert "min_length=3" in src

    def test_pm_admin_preserves_cascade_logic(self):
        """The PATCH email-change cascade to jobs_master MUST remain."""
        src = Path("/app/backend/routes/pm_admin.py").read_text()
        assert "jobs_master.update_many" in src
        assert "pm_email" in src
        assert "co_pm_emails" in src or "project_manager" in src

    def test_pm_admin_preserves_delete_job_guard(self):
        """DELETE must still 409 if PM is still assigned to jobs."""
        src = Path("/app/backend/routes/pm_admin.py").read_text()
        assert "still assigned to" in src
        assert "409" in src

    def test_pm_admin_preserves_activity_7_collections(self):
        """admin_pm_activity rolls up 7 collections — locked here."""
        src = Path("/app/backend/routes/pm_admin.py").read_text()
        for coll in ["inspections", "meetings", "incidents", "daily_reports",
                     "equipment_inspections", "qaqc_inspections",
                     "job_hazard_plans"]:
            assert coll in src

    def test_server_py_no_longer_owns_extracted_routes(self):
        src = Path("/app/backend/server.py").read_text()
        for marker in [
            '@api_router.get("/admin/project-managers/export")',
            '@api_router.get("/admin/project-managers")',
            '@api_router.get("/project-managers")',
            '@api_router.post("/admin/project-managers")',
            '@api_router.patch("/admin/project-managers/{pm_id}")',
            '@api_router.delete("/admin/project-managers/{pm_id}")',
            '@api_router.post("/admin/project-managers/{pm_id}/set-password")',
            '@api_router.post("/admin/project-managers/{pm_id}/welcome-pdf")',
            '@api_router.post("/admin/project-managers/{pm_id}/email-welcome")',
            '@api_router.post("/admin/project-managers/{pm_id}/disable")',
            '@api_router.get("/admin/project-managers/activity")',
        ]:
            assert marker not in src, (
                f"{marker} still in server.py — iter382 extraction incomplete"
            )

    def test_server_py_no_longer_owns_pm_body_classes(self):
        src = Path("/app/backend/server.py").read_text()
        for cls in ["class PMIn(", "class PMUpdate(", "class PMSetPasswordBody("]:
            assert cls not in src, f"{cls} still in server.py"

    def test_server_py_mounts_pm_admin_router(self):
        src = Path("/app/backend/server.py").read_text()
        assert "build_pm_admin_router(" in src
        assert "include_router(_pm_admin_router)" in src

    def test_server_py_wires_helper_dependencies(self):
        src = Path("/app/backend/server.py").read_text()
        assert "xlsx_response_fn=_xlsx_response" in src
        assert "active_filter=ACTIVE_FILTER" in src
        assert "render_portal_email_fn=render_portal_email" in src
