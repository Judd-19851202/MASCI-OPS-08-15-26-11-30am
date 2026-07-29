"""TRACK 15.13E · Production Auth Session Recovery — regression tests.

Each test maps to a specific failure / requirement of the 15.13E fix:

  1. Backend dep `require_admin_or_asset_admin` is wired to the 4
     Asset Care read endpoints under /api/asset-spine/dashboard/* and
     the /api/asset-care/* read surface, and to nothing else.
  2. The dep accepts:
       a) Admin token                                       → "admin_token"
       b) Per-shop-user token whose user_directory row has
          `is_asset_admin == True`                          → "directory_flag"
       c) Per-shop-user token whose shop_users.role label is
          one of the ASSET_ADMIN_ROLE_LABELS (legacy)        → "legacy_shop_role"
     A normal mechanic / parts coordinator / shop manager
     WITHOUT the role and WITHOUT the flag is REJECTED.
  3. Mutation routes on /api/daily-reports/* (POST/DELETE) and on
     /api/asset-spine/dashboard/required-documents-config/* (PUT/DELETE)
     remain admin-only — the new gate is read-only by intent.
  4. Frontend Axios interceptor in /app/frontend/src/lib/api.js
     scopes 401 cleanup to the *active* portal (inferred from
     window.location.pathname) so a non-namespaced 401 cannot wipe
     unrelated portal sessions.

Tests use static source-code inspection where the contract is at the
shape-of-the-code level (mounting, dep-routing) and live behavioral
checks against the in-process app where we need to prove auth chain
behavior. Live tests are skipped automatically if the backend can't
be imported (e.g. when running outside a real preview pod).
"""
from __future__ import annotations

import re
from pathlib import Path
import hashlib
from datetime import datetime, timezone

import pytest

BACKEND = Path(__file__).resolve().parents[1]
SERVER_PY = (BACKEND / "server.py").read_text()
DAILY_REPORTS_PY = (BACKEND / "routes" / "daily_reports.py").read_text()
ASSET_CARE_PY = (BACKEND / "routes" / "asset_care.py").read_text()
ASSET_DOCS_PY = (BACKEND / "routes" / "asset_documents.py").read_text()
ASSET_ADMIN_SETTINGS_PY = (BACKEND / "routes" / "asset_admin_settings.py").read_text()
PM_AUTH_PY = (BACKEND / "pm_auth.py").read_text()

FRONTEND = BACKEND.parent / "frontend" / "src"
API_JS = (FRONTEND / "lib" / "api.js").read_text()


# ---------------------------------------------------------------------
# 1) require_admin_or_asset_admin is defined and used on the 4 reads
# ---------------------------------------------------------------------
class TestAssetAdminDependencyDefinitionAndWiring:
    def test_dep_is_defined_in_server(self):
        assert "async def require_admin_or_asset_admin(" in SERVER_PY, (
            "require_admin_or_asset_admin must be defined in server.py"
        )

    def test_dep_returns_auth_path_tag(self):
        """Tests #2 in the spec — the dep must tag the actor with
        `_auth_path` so callers (and audit reports) can prove which
        path resolved: directory_flag vs legacy_shop_role vs admin_token.
        """
        # All three paths must be tagged.
        assert '"_auth_path": "admin_token"' in SERVER_PY
        assert '"_auth_path": "directory_flag"' in SERVER_PY
        assert '"_auth_path": "legacy_shop_role"' in SERVER_PY

    def test_dep_consults_user_directory_first(self):
        # The directory-flag path must occur BEFORE the legacy fallback.
        idx_dir = SERVER_PY.index('"_auth_path": "directory_flag"')
        idx_legacy = SERVER_PY.index('"_auth_path": "legacy_shop_role"')
        assert idx_dir < idx_legacy, (
            "directory_flag must be checked before legacy_shop_role"
        )

    def test_dep_rejects_shared_shop_token(self):
        # Shared shop token (no `.`) doesn't identify a user so it
        # cannot satisfy the gate; check the explicit reject.
        block = SERVER_PY[
            SERVER_PY.index("async def require_admin_or_asset_admin(") :
        ]
        block = block[: block.index("\n\n\n")]
        assert '"." not in x_shop_token' in block

    def test_dep_uses_403_for_authenticated_non_asset_user(self):
        """A valid Shop user who is NOT an Asset Admin must get 403,
        not 401. Otherwise the frontend interceptor will treat it as
        an expired session and bounce them out."""
        block = SERVER_PY[
            SERVER_PY.index("async def require_admin_or_asset_admin(") :
        ]
        block = block[: block.index("\n\n\n")]
        # Final reject after both paths failed must be 403.
        m = re.findall(r"status_code=(\d{3}).*?Asset Administrator", block, re.DOTALL)
        assert "403" in m, (
            "Final reject for authenticated non-asset shop user must be 403"
        )

    def test_dep_wired_to_4_asset_spine_dashboard_endpoints(self):
        # The asset_documents.py module routes the 4 dashboard reads
        # through `_dashboard_read_dep`, which is set to the new dep.
        assert "_dashboard_read_dep = require_admin_or_asset_admin_dep" in ASSET_DOCS_PY
        # Each endpoint must depend on `_dashboard_read_dep`, not the
        # old `_require_asset_admin` closure.
        for path in (
            "/dashboard/missing-documents",
            "/dashboard/renewals",
            "/dashboard/recent-uploads",
            "/dashboard/required-documents-config",
        ):
            # Find the route line and the next Depends() block.
            idx = ASSET_DOCS_PY.index(f'@router.get("{path}")')
            # The next Depends within ~600 chars must reference _dashboard_read_dep.
            window = ASSET_DOCS_PY[idx : idx + 600]
            assert "Depends(_dashboard_read_dep)" in window, (
                f"{path} must depend on _dashboard_read_dep, got window=\n{window[:300]}"
            )

    def test_dep_wired_to_asset_care_reads(self):
        # asset_care.py routes summary / readiness / alerts / work-queue
        # through `_read_dep`, set to the new dep at register time.
        assert (
            "_read_dep = require_admin_or_asset_admin_dep or require_admin_dep"
            in ASSET_CARE_PY
        )
        for fn in ("def summary(", "def readiness(", "def work_queue(", "def alerts(", "def notifications_matrix("):
            idx = ASSET_CARE_PY.index(fn)
            window = ASSET_CARE_PY[idx : idx + 500]
            assert "Depends(_read_dep)" in window, (
                f"{fn} must depend on _read_dep"
            )

    def test_dep_wired_to_required_docs_config_effective(self):
        # asset_admin_settings.py — the read endpoint that the
        # RequiredDocsEditor calls. Mutations (PUT/DELETE) stay
        # admin-only.
        assert (
            "_read_dep = require_admin_or_asset_admin_dep or require_admin_dep"
            in ASSET_ADMIN_SETTINGS_PY
        )
        # Find the @router.get(...required-documents-config-effective) block.
        m = re.search(
            r'@router\.get\(\s*\n?\s*"[^"]*required-documents-config-effective"[\s\S]{0,500}?actor=Depends\(([A-Za-z_]+)\)',
            ASSET_ADMIN_SETTINGS_PY,
        )
        assert m, "Could not find the effective-required-docs endpoint"
        assert m.group(1) == "_read_dep", (
            f"effective_required_documents must depend on _read_dep, got {m.group(1)}"
        )

    def test_required_docs_mutations_stay_admin_only(self):
        # PUT + DELETE on required-documents-config/* must keep
        # `require_admin_dep`. The new read dep MUST NOT touch them.
        for op in ("@router.put(", "@router.delete("):
            # Find every occurrence; for each PUT/DELETE under
            # required-documents-config, the dep must be admin.
            for m in re.finditer(re.escape(op) + r"[\s\S]*?required-documents-config", ASSET_ADMIN_SETTINGS_PY):
                tail = ASSET_ADMIN_SETTINGS_PY[m.start() : m.start() + 800]
                # tail must NOT route through the new read dep.
                if "required-documents-config-effective" in tail:
                    continue  # that's the GET, already checked.
                assert "Depends(require_admin_dep)" in tail, (
                    f"Mutation under {op} must keep require_admin_dep, got:\n{tail[:300]}"
                )


# ---------------------------------------------------------------------
# 2) require_admin_pm_or_hr_read — daily report HR read
# ---------------------------------------------------------------------
class TestHrDailyReportReadDependency:
    def test_dep_is_defined_in_server(self):
        assert "async def require_admin_pm_or_hr_read(" in SERVER_PY

    def test_dep_accepts_admin_pm_hr(self):
        block = SERVER_PY[
            SERVER_PY.index("async def require_admin_pm_or_hr_read(") :
        ]
        block = block[: block.index("\n\n\n")]
        # All three token branches must be present.
        assert "x_admin_token" in block
        assert "x_pm_token" in block
        assert "x_hr_token" in block
        # HR resolves through is_valid_hr_user_token_async.
        assert "is_valid_hr_user_token_async" in block
        # HR actor must be tagged `_actor_kind=hr_user` so
        # compute_pm_scope treats them as unrestricted readers.
        assert '"_actor_kind": "hr_user"' in block

    def test_dep_passed_to_daily_reports_registration(self):
        # Server passes the dep when registering daily reports.
        assert (
            "require_admin_pm_or_hr_read=require_admin_pm_or_hr_read"
            in SERVER_PY
        )

    def test_daily_reports_get_uses_new_dep(self):
        # Only the singular GET endpoint should use the new dep.
        # List / CSV / audit-footer / create / delete must still use require_admin.
        gets = re.findall(
            r'@api_router\.get\("(?P<path>/daily-reports[^"]*)"\)[\s\S]{0,400}?actor=Depends\((?P<dep>[A-Za-z_]+)\)',
            DAILY_REPORTS_PY,
        )
        # Map { path: dep } using the first match per path.
        first = {}
        for path, dep in gets:
            first.setdefault(path, dep)
        # Identifier wired into the register function is `_read_dep`.
        assert first.get("/daily-reports/{report_id}") == "_read_dep", (
            f"GET /daily-reports/{{report_id}} must use _read_dep, got {first}"
        )

    def test_daily_reports_delete_remains_admin_only(self):
        # DELETE is currently frozen but historically used require_admin;
        # ensure no HR read dep snuck onto a mutation.
        del_block = DAILY_REPORTS_PY[
            DAILY_REPORTS_PY.index('@api_router.delete("/daily-reports/{report_id}")') :
        ]
        # Must depend on require_admin, NOT _read_dep or the new dep.
        assert "Depends(require_admin)" in del_block[:600]
        assert "Depends(_read_dep)" not in del_block[:600]
        assert "Depends(require_admin_pm_or_hr_read" not in del_block[:600]

    def test_daily_reports_create_remains_admin_or_pm(self):
        # POST /daily-reports — the create endpoint. Must NOT accept HR.
        idx = DAILY_REPORTS_PY.index("async def create_daily_report(")
        block = DAILY_REPORTS_PY[idx : idx + 1500]
        # The body must NOT contain a reference to the new HR-read dep.
        assert "require_admin_pm_or_hr_read" not in block
        assert "_read_dep" not in block

    def test_compute_pm_scope_treats_hr_users_as_unrestricted(self):
        # HR readers must be granted cross-job read scope (same way
        # safety/shop are) so that GET /daily-reports/{id} doesn't
        # 404 every report just because the HR user isn't in
        # jobs_master.pm_email or co_pm_emails.
        assert '_actor_kind") == "hr_user"' in PM_AUTH_PY
        # Ensure the line that follows it returns is_admin=True.
        idx = PM_AUTH_PY.index('_actor_kind") == "hr_user"')
        window = PM_AUTH_PY[idx : idx + 200]
        assert "PmScope(is_admin=True)" in window


# ---------------------------------------------------------------------
# 3) Frontend interceptor portal-scoping
# ---------------------------------------------------------------------
class TestFrontendInterceptorScoping:
    def test_pathname_based_active_portal_inference(self):
        # The new non-namespaced 401 branch reads
        # window.location.pathname and maps it to one active portal.
        # Each portal must be enumerated and only the active one's
        # token cleared.
        assert "window.location.pathname" in API_JS
        for needle in (
            '"/admin/"',
            '"/hr/"',
            '"/shop/"',
            '"/pm/"',
            '"/safety/"',
            '"/dispatch/"',
        ):
            assert needle in API_JS, f"missing pathname check for {needle}"

    def test_portal_scoped_cleanup_doesnt_wipe_other_tokens(self):
        # TRACK 15.13H — Revised contract. The active-portal branch
        # must NOT clear any token (a single 401 on a feature
        # endpoint is overwhelmingly a "feature not authorized"
        # signal, not a session-expiry signal). Token-clearing is
        # now reserved exclusively for the no-portal-context
        # fallback below.
        idx_start = API_JS.index('if (activePortal) {')
        idx_end = API_JS.index('} else {', idx_start)
        active_branch = API_JS[idx_start:idx_end]
        # Active branch must NOT call any clearer (15.13H rule).
        clears = re.findall(r"clear[A-Z][A-Za-z]+Token\(\)", active_branch)
        assert clears == [], (
            f"active-portal branch must not clear any token, "
            f"got {sorted(set(clears))}"
        )
        # And it must NOT call clearJwt().
        assert "clearJwt()" not in active_branch

    def test_no_portal_inference_falls_back_to_legacy_wipe(self):
        # If pathname is something like / or /login, we have no
        # portal context — legacy behavior of wiping every token the
        # request carried is preserved as a safety net.
        idx_else = API_JS.index('} else {\n          // No portal context')
        legacy_tail = API_JS[idx_else : idx_else + 2000]
        # Legacy fallback must call every portal's clearer.
        for clr in (
            "clearAdminToken",
            "clearShopToken",
            "clearPmToken",
            "clearHrToken",
            "clearSafetyToken",
            "clearDispatchToken",
            "clearFlToken",
            "clearLeadershipToken",
            "clearJwt",
        ):
            assert f"{clr}()" in legacy_tail, f"legacy fallback missing {clr}"

    def test_namespaced_handled_suppresses_global_modal(self):
        # TRACK 15.13H — The active-portal branch must set
        # `_namespacedHandled = true` so the global "Session
        # Expired" modal does NOT fire. This applies regardless of
        # whether the failing request used the active portal's
        # token (lifecycle 401 case) or not (stale background
        # helper case). Both must absorb silently.
        idx_start = API_JS.index('if (activePortal) {')
        idx_end = API_JS.index('} else {', idx_start)
        active_branch = API_JS[idx_start:idx_end]
        assert "_namespacedHandled = true" in active_branch


# ---------------------------------------------------------------------
# 4) Live behavioral checks against the running backend
# ---------------------------------------------------------------------
# These tests hit the actual running backend via HTTP instead of an
# in-process TestClient, sidestepping the Motor / asyncio event-loop
# conflict that breaks TestClient on apps with module-scoped Motor
# connections. Skipped if the backend isn't reachable (e.g. CI box
# without a running supervisor pod).
import os as _os  # noqa: E402

import requests as _requests  # noqa: E402

try:
    from dotenv import dotenv_values as _dotenv_values  # noqa: E402
    _FE_ENV = _dotenv_values("/app/frontend/.env")
    _BACKEND_URL = (_FE_ENV.get("REACT_APP_BACKEND_URL") or "").strip().strip('"').rstrip("/")
    # Load /app/backend/.env so MONGO_URL/DB_NAME are available even
    # when tests run in isolation (without server.py importing first).
    _BE_ENV = _dotenv_values("/app/backend/.env")
    for _k, _v in _BE_ENV.items():
        if _k and _v is not None and _k not in _os.environ:
            _os.environ[_k] = str(_v).strip().strip('"')
except Exception:
    _BACKEND_URL = ""


def _live_backend_or_skip():
    """Returns the live backend base URL; skips the test if unreachable
    or if APP_ENV would point at the production DB (refuse to seed)."""
    if not _BACKEND_URL:
        pytest.skip("REACT_APP_BACKEND_URL not configured")
    try:
        r = _requests.get(f"{_BACKEND_URL}/api/health", timeout=5)
        if r.status_code != 200:
            pytest.skip(f"backend unhealthy: HTTP {r.status_code}")
    except Exception as exc:
        pytest.skip(f"backend not reachable: {exc!r}")
    # Refuse to run if not preview DB.
    app_env = (_os.environ.get("APP_ENV") or "").lower()
    db_name = (_os.environ.get("DB_NAME") or "")
    if app_env == "production" or db_name == "masci_safety":
        pytest.skip("refusing to seed against production DB")
    return _BACKEND_URL


class TestLiveBehavior:
    """Live integration checks against the running backend service.

    Each check exercises the actual auth dependency chain end-to-end
    via HTTP. Skipped if the backend isn't reachable.
    """

    def _seed_shop_user(self, role: str, is_asset_admin_dir: bool, email: str):
        """Seed a per-shop-user with an optional `is_asset_admin`
        directory flag. Returns the per-shop-user token."""
        from shop_users import make_shop_user_token  # type: ignore
        from pm_auth import hash_password  # type: ignore
        import uuid as _uuid
        from pymongo import MongoClient as _MongoClient

        pw_hash = hash_password("Test1234!@#$")
        uid = f"test-shop-{_uuid.uuid4().hex[:12]}"
        sync = _MongoClient(_os.environ["MONGO_URL"])
        sdb = sync[_os.environ["DB_NAME"]]
        sdb.shop_users.delete_many({"email": email})
        sdb.user_directory.delete_many({"email": email})
        sdb.shop_users.insert_one({
            "id": uid, "name": "Test Shop User", "email": email,
            "phone": "", "role": role, "is_active": True, "disabled": False,
            "password_hash": pw_hash, "must_change_password": False,
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
        })
        if is_asset_admin_dir:
            sdb.user_directory.insert_one({
                "id": f"dir-{uid}", "email": email, "name": "Test Shop User",
                "portals": [], "disabled": False, "must_change_password": False,
                "password_hash": None, "is_asset_admin": True,
                "created_at": "2026-01-01T00:00:00+00:00",
                "updated_at": "2026-01-01T00:00:00+00:00",
            })
        token = make_shop_user_token(uid, pw_hash)
        now = datetime.now(timezone.utc)
        sdb.session_activity.update_one(
            {"token_hash": hashlib.sha256(token.encode("utf-8")).hexdigest()},
            {
                "$set": {
                    "token_hash": hashlib.sha256(token.encode("utf-8")).hexdigest(),
                    "tier": "OPERATIONS",
                    "first_seen_at": now,
                    "last_seen_at": now,
                    "user_id": uid,
                    "email": email,
                    "actor_label": "shop",
                }
            },
            upsert=True,
        )
        sync.close()
        return uid, token

    @pytest.fixture
    def live_base_url(self):
        return _live_backend_or_skip()

    def test_directory_flag_path_unlocks(self, live_base_url):
        _, tok = self._seed_shop_user(
            role="Mechanic", is_asset_admin_dir=True,
            email="track1513e.dir@test.local",
        )
        r = _requests.get(
            f"{live_base_url}/api/asset-care/summary",
            headers={"X-Shop-Token": tok}, timeout=10,
        )
        assert r.status_code == 200, (
            f"directory_flag user must get 200, got {r.status_code} {r.text[:300]}"
        )

    def test_legacy_role_path_unlocks(self, live_base_url):
        _, tok = self._seed_shop_user(
            role="Asset Administrator", is_asset_admin_dir=False,
            email="track1513e.legacy@test.local",
        )
        r = _requests.get(
            f"{live_base_url}/api/asset-care/summary",
            headers={"X-Shop-Token": tok}, timeout=10,
        )
        assert r.status_code == 200, (
            f"legacy_shop_role user must get 200, got {r.status_code} {r.text[:300]}"
        )

    def test_normal_mechanic_is_rejected_with_403(self, live_base_url):
        _, tok = self._seed_shop_user(
            role="Mechanic", is_asset_admin_dir=False,
            email="track1513e.mechanic@test.local",
        )
        r = _requests.get(
            f"{live_base_url}/api/asset-care/summary",
            headers={"X-Shop-Token": tok}, timeout=10,
        )
        # Critical: 403 NOT 401 — otherwise the frontend interceptor
        # treats it as expired session and bounces the user out.
        assert r.status_code == 403, (
            f"normal mechanic must get 403, got {r.status_code} {r.text[:300]}"
        )

    def test_no_token_is_401(self, live_base_url):
        r = _requests.get(f"{live_base_url}/api/asset-care/summary", timeout=10)
        assert r.status_code == 401

    def test_asset_spine_dashboard_renewals_accepts_legacy_role(self, live_base_url):
        _, tok = self._seed_shop_user(
            role="Asset Manager", is_asset_admin_dir=False,
            email="track1513e.legacy2@test.local",
        )
        r = _requests.get(
            f"{live_base_url}/api/asset-spine/dashboard/renewals",
            headers={"X-Shop-Token": tok}, timeout=10,
        )
        assert r.status_code == 200, (
            f"asset-spine dashboard must accept legacy role, got {r.status_code} {r.text[:200]}"
        )

    def test_hr_can_read_daily_report_singular(self, live_base_url):
        """An HR token must be able to GET a single daily report,
        but must NOT be able to POST or DELETE one."""
        from hr_users import make_hr_user_token  # type: ignore
        from pm_auth import hash_password  # type: ignore
        import uuid as _uuid
        from pymongo import MongoClient as _MongoClient

        sync = _MongoClient(_os.environ["MONGO_URL"])
        sdb = sync[_os.environ["DB_NAME"]]
        try:
            email = "track1513e.hr@test.local"
            uid = f"test-hr-{_uuid.uuid4().hex[:12]}"
            pw_hash = hash_password("Test1234!@#$")
            sdb.hr_users.delete_many({"email": email})
            sdb.hr_users.insert_one({
                "id": uid, "name": "Test HR User", "email": email,
                "role": "HR Manager", "is_active": True, "disabled": False,
                "password_hash": pw_hash, "must_change_password": False,
                "created_at": "2026-01-01T00:00:00+00:00",
                "updated_at": "2026-01-01T00:00:00+00:00",
            })
            hr_tok = make_hr_user_token(uid, pw_hash)
            now = datetime.now(timezone.utc)
            sdb.session_activity.update_one(
                {"token_hash": hashlib.sha256(hr_tok.encode("utf-8")).hexdigest()},
                {
                    "$set": {
                        "token_hash": hashlib.sha256(hr_tok.encode("utf-8")).hexdigest(),
                        "tier": "ADMIN_HR",
                        "first_seen_at": now,
                        "last_seen_at": now,
                        "user_id": uid,
                        "email": email,
                        "actor_label": "hr",
                    }
                },
                upsert=True,
            )
            dr_id = f"dr-track1513e-{_uuid.uuid4().hex[:8]}"
            sdb.daily_reports.delete_many({"id": dr_id})
            sdb.daily_reports.insert_one({
                "id": dr_id, "project_number": "TRACK1513E-CERT",
                "date": "2026-06-17", "weather": "Clear",
                "crew_count": 0, "sub_count": 0, "visitor_count": 0,
                "created_at": "2026-06-17T00:00:00+00:00",
                "constraints": [], "photos": [],
                "subcontractor_log": [], "material_deliveries": [],
            })
            r_get = _requests.get(
                f"{live_base_url}/api/daily-reports/{dr_id}",
                headers={"X-HR-Token": hr_tok}, timeout=10,
            )
            assert r_get.status_code == 200, (
                f"HR must read singular DR, got {r_get.status_code} {r_get.text[:200]}"
            )
            r_del = _requests.delete(
                f"{live_base_url}/api/daily-reports/{dr_id}",
                headers={"X-HR-Token": hr_tok}, timeout=10,
            )
            assert r_del.status_code in (401, 403, 410), (
                f"HR must NOT delete DR, got {r_del.status_code}"
            )
            r_post = _requests.post(
                f"{live_base_url}/api/daily-reports",
                headers={"X-HR-Token": hr_tok}, timeout=10,
                json={
                    "project_number": "TRACK1513E-CERT", "date": "2026-06-18",
                    "weather": "Clear", "crew_count": 0, "sub_count": 0,
                    "visitor_count": 0, "constraints": [], "photos": [],
                    "subcontractor_log": [], "material_deliveries": [],
                },
            )
            assert r_post.status_code in (401, 403, 422), (
                f"HR must NOT create DR, got {r_post.status_code}"
            )
        finally:
            sync.close()
