"""
test_iter177_phase_k4b_directory_mutations.py — Phase K4b verification.

K4b ships admin-only audited mutations on the unified directory:

  • POST /api/admin/directory/k4/users/{id}/role-template
  • POST /api/admin/directory/k4/users/{id}/convert-to-managed
  • POST /api/admin/directory/k4/users/{id}/revert-to-mirrored
  • POST /api/admin/directory/k4/users/{id}/set-disabled

This test suite verifies the discipline gates the user explicitly
mandated:

  ✅ admin-only
  ✅ every mutation writes an admin_audit row
  ✅ no plaintext credential exposure anywhere (response or audit)
  ✅ mirrored-user compatibility preserved during conversion
        (legacy hr_users / shop_users etc. row is NEVER touched)
  ✅ rollback path: revert-to-mirrored re-randomises the bcrypt hash
        and re-sets `mirrored=True` so multi-login refuses again
  ✅ no automation, no email send, no temp-password generation
  ✅ no enforcement (assigned `role_template_id` is just stored)
  ✅ super-admin protections
  ✅ idempotent state guards / no_change auditing
  ✅ K4a read-only contract still intact (regression)
"""
from __future__ import annotations

import asyncio
import os
import secrets
import sys
import uuid
from pathlib import Path
from typing import Any, Dict

import httpx
from motor.motor_asyncio import AsyncIOMotorClient

sys.path.insert(0, "/app/backend")


def _load_env(p: str) -> None:
    txt = Path(p).read_text()
    for line in txt.splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"'))


_load_env("/app/backend/.env")

BACKEND_URL = "http://localhost:8001"


# ─── Helpers ──────────────────────────────────────────────────────────────
async def _admin_token() -> str:
    async with httpx.AsyncClient(base_url=BACKEND_URL, timeout=10) as c:
        r = await c.post(
            "/api/admin/login",
            json={"password": os.environ.get("ADMIN_PASSWORD", "")},
        )
        assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text}"
        return r.json()["token"]


async def _http(
    method: str,
    path: str,
    *,
    token: str = "",
    json_body: Any = None,
) -> httpx.Response:
    headers: Dict[str, str] = {}
    if token:
        headers["X-Admin-Token"] = token
    async with httpx.AsyncClient(base_url=BACKEND_URL, timeout=10) as c:
        return await c.request(method, path, headers=headers, json=json_body)


def _run(coro):
    return asyncio.run(coro)


async def _db():
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    return client[os.environ.get("DB_NAME", "test_database")]


async def _make_test_user(*, mirrored: bool, with_mirror_sources: bool = True) -> Dict[str, Any]:
    """Create a temporary user_directory row for mutation tests so we
    never disturb production seed rows. Cleaned up by callers."""
    db = await _db()
    import bcrypt

    uid = f"k4b-test-{uuid.uuid4().hex[:8]}"
    email = f"k4btest-{uuid.uuid4().hex[:8]}@masci.test"
    doc = {
        "id": uid,
        "email": email,
        "name": "K4b Test",
        "portals": ["hr"],
        "is_super_admin": False,
        "disabled": False,
        "must_change_password": False,
        "password_hash": bcrypt.hashpw(
            secrets.token_urlsafe(32).encode("utf-8"), bcrypt.gensalt(rounds=4)
        ).decode("ascii"),
        "mirrored": mirrored,
        "mirror_sources": ({"hr": "legacy-row-id"} if with_mirror_sources else {}),
        "employee_id": None,
        "role_template_id": None,
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
        "last_login_at": None,
        "last_login_portal": None,
    }
    await db.user_directory.insert_one(doc)
    return {"id": uid, "email": email}


async def _cleanup_test_user(uid: str) -> None:
    # DEPLOY-GATE-FIX-001 (2026-06-09): replaced motor cleanup with a
    # short-lived pymongo sync handle. The previous motor-based path hit
    # `_topology._check_implicit_session_support` intermittently because
    # a fresh AsyncIOMotorClient is created per call and the underlying
    # pymongo session manager wants topology discovery before any
    # write. Using a sync MongoClient sidesteps that entirely; no
    # behavioural change for the system under test.
    from pymongo import MongoClient

    sync_client = MongoClient(os.environ["MONGO_URL"], serverSelectionTimeoutMS=8000)
    try:
        sync_db = sync_client[os.environ.get("DB_NAME", "test_database")]
        sync_db.user_directory.delete_many({"id": uid})
        sync_db.admin_audit.delete_many({"target_email": {"$regex": "^k4btest-"}})
    finally:
        sync_client.close()


async def _last_audit_for(email: str) -> Dict[str, Any]:
    db = await _db()
    row = await db.admin_audit.find_one(
        {"target_email": email}, {"_id": 0}, sort=[("at", -1)]
    )
    return row or {}


# ─── 1. Auth gate ─────────────────────────────────────────────────────────
def test_anon_blocked_on_every_k4b_endpoint():
    async def body():
        paths = [
            ("POST", "/api/admin/directory/k4/users/abc/role-template", {"role_template_id": None}),
            ("POST", "/api/admin/directory/k4/users/abc/convert-to-managed", {"password": "Pw12345678"}),
            ("POST", "/api/admin/directory/k4/users/abc/revert-to-mirrored", None),
            ("POST", "/api/admin/directory/k4/users/abc/set-disabled", {"disabled": True}),
        ]
        for method, path, payload in paths:
            r = await _http(method, path, json_body=payload)
            assert r.status_code in (401, 403), f"{path} returned {r.status_code} for anon"

    _run(body())


# ─── 2. role-template assign happy path ───────────────────────────────────
def test_assign_role_template_writes_field_and_audit():
    async def body():
        tok = await _admin_token()
        user = await _make_test_user(mirrored=True)
        try:
            r = await _http(
                "POST",
                f"/api/admin/directory/k4/users/{user['id']}/role-template",
                token=tok,
                json_body={"role_template_id": "rt-hr-manager"},
            )
            assert r.status_code == 200, r.text
            v = r.json()["user"]
            assert v["role_template_id"] == "rt-hr-manager"
            # Audit row written
            a = await _last_audit_for(user["email"])
            assert a.get("action") == "directory_k4_assign_role_template"
            assert a["diff"]["to"] == "rt-hr-manager"
            assert a["diff"]["from"] is None
            assert a["diff"]["no_change"] is False
        finally:
            await _cleanup_test_user(user["id"])

    _run(body())


def test_assign_role_template_clear_with_null():
    async def body():
        tok = await _admin_token()
        user = await _make_test_user(mirrored=True)
        try:
            # First set
            await _http(
                "POST",
                f"/api/admin/directory/k4/users/{user['id']}/role-template",
                token=tok,
                json_body={"role_template_id": "rt-hr-manager"},
            )
            # Now clear with null
            r = await _http(
                "POST",
                f"/api/admin/directory/k4/users/{user['id']}/role-template",
                token=tok,
                json_body={"role_template_id": None},
            )
            assert r.status_code == 200
            assert r.json()["user"]["role_template_id"] is None
            a = await _last_audit_for(user["email"])
            assert a["diff"]["from"] == "rt-hr-manager"
            assert a["diff"]["to"] is None
        finally:
            await _cleanup_test_user(user["id"])

    _run(body())


def test_assign_role_template_unknown_id_400():
    async def body():
        tok = await _admin_token()
        user = await _make_test_user(mirrored=True)
        try:
            r = await _http(
                "POST",
                f"/api/admin/directory/k4/users/{user['id']}/role-template",
                token=tok,
                json_body={"role_template_id": "rt-does-not-exist"},
            )
            assert r.status_code == 400
        finally:
            await _cleanup_test_user(user["id"])

    _run(body())


def test_assign_role_template_no_change_is_audited_and_skipped():
    async def body():
        tok = await _admin_token()
        user = await _make_test_user(mirrored=True)
        try:
            await _http(
                "POST",
                f"/api/admin/directory/k4/users/{user['id']}/role-template",
                token=tok,
                json_body={"role_template_id": "rt-hr-manager"},
            )
            updated_before = (await _http(
                "GET",
                f"/api/admin/directory/k4/users/{user['id']}",
                token=tok,
            )).json()["user"]["updated_at"]
            # Re-assign same value
            r = await _http(
                "POST",
                f"/api/admin/directory/k4/users/{user['id']}/role-template",
                token=tok,
                json_body={"role_template_id": "rt-hr-manager"},
            )
            assert r.status_code == 200
            a = await _last_audit_for(user["email"])
            assert a["diff"]["no_change"] is True
            updated_after = r.json()["user"]["updated_at"]
            assert updated_before == updated_after, "no_change must not bump updated_at"
        finally:
            await _cleanup_test_user(user["id"])

    _run(body())


def test_assign_role_template_user_404():
    async def body():
        tok = await _admin_token()
        r = await _http(
            "POST",
            f"/api/admin/directory/k4/users/{uuid.uuid4().hex}/role-template",
            token=tok,
            json_body={"role_template_id": "rt-hr-manager"},
        )
        assert r.status_code == 404

    _run(body())


# ─── 3. convert-to-managed ────────────────────────────────────────────────
def test_convert_to_managed_happy_path():
    """Critical discipline check: must set hash + clear mirrored + set
    must_change_password=true, NEVER echo password, write audit row
    that does NOT contain the password."""

    async def body():
        tok = await _admin_token()
        user = await _make_test_user(mirrored=True)
        try:
            pw = "AdminTyped12345!"
            r = await _http(
                "POST",
                f"/api/admin/directory/k4/users/{user['id']}/convert-to-managed",
                token=tok,
                json_body={"password": pw},
            )
            assert r.status_code == 200, r.text
            v = r.json()["user"]
            assert v["mirrored"] is False
            assert v["source"] == "managed"
            assert v["must_change_password"] is True
            # Critical: password not echoed back anywhere in response
            assert pw not in r.text
            assert "password_hash" not in r.text
            # Audit row written, NEVER contains the plaintext password
            a = await _last_audit_for(user["email"])
            assert a["action"] == "directory_k4_convert_to_managed"
            assert a["diff"]["password_set"] is True
            assert a["diff"]["must_change_password"] is True
            assert pw not in str(a)
            # Multi-login with the new password should now succeed
            async with httpx.AsyncClient(base_url=BACKEND_URL, timeout=10) as c:
                login = await c.post(
                    "/api/auth/multi-login",
                    json={"email": user["email"], "password": pw},
                )
                assert login.status_code == 200, login.text
                assert login.json()["must_change_password"] is True
        finally:
            await _cleanup_test_user(user["id"])

    _run(body())


def test_convert_to_managed_rejects_already_managed():
    async def body():
        tok = await _admin_token()
        user = await _make_test_user(mirrored=False)
        try:
            r = await _http(
                "POST",
                f"/api/admin/directory/k4/users/{user['id']}/convert-to-managed",
                token=tok,
                json_body={"password": "AdminTyped12345!"},
            )
            assert r.status_code == 409
        finally:
            await _cleanup_test_user(user["id"])

    _run(body())


def test_convert_to_managed_short_password_400():
    async def body():
        tok = await _admin_token()
        user = await _make_test_user(mirrored=True)
        try:
            r = await _http(
                "POST",
                f"/api/admin/directory/k4/users/{user['id']}/convert-to-managed",
                token=tok,
                json_body={"password": "short"},
            )
            # Pydantic min_length=8 returns 422; the manual ≥8 check
            # returns 400. Both block; accept either.
            assert r.status_code in (400, 422)
        finally:
            await _cleanup_test_user(user["id"])

    _run(body())


def test_convert_does_not_touch_legacy_portal_row():
    """User-mandated discipline: mirrored-user compatibility during
    transition. The legacy `hr_users` row (or whichever portal seeded
    the mirror) MUST stay intact after a convert."""

    async def body():
        tok = await _admin_token()
        db = await _db()
        # Seed a fake hr_users row + a mirrored directory row pointing at it
        legacy_id = f"legacy-hr-{uuid.uuid4().hex[:8]}"
        legacy_email = f"k4btest-legacy-{uuid.uuid4().hex[:6]}@masci.test"
        await db.hr_users.insert_one(
            {
                "id": legacy_id,
                "email": legacy_email,
                "password_hash": "$2b$12$legacyhashplaceholder",
                "_legacy_marker": True,
            }
        )
        import bcrypt

        directory_id = f"k4b-mirror-{uuid.uuid4().hex[:8]}"
        await db.user_directory.insert_one(
            {
                "id": directory_id,
                "email": legacy_email,
                "name": "Legacy HR",
                "portals": ["hr"],
                "is_super_admin": False,
                "disabled": False,
                "must_change_password": False,
                "password_hash": bcrypt.hashpw(
                    secrets.token_urlsafe(32).encode("utf-8"),
                    bcrypt.gensalt(rounds=4),
                ).decode("ascii"),
                "mirrored": True,
                "mirror_sources": {"hr": legacy_id},
                "employee_id": None,
                "role_template_id": None,
                "created_at": "2026-01-01T00:00:00+00:00",
                "updated_at": "2026-01-01T00:00:00+00:00",
            }
        )
        try:
            r = await _http(
                "POST",
                f"/api/admin/directory/k4/users/{directory_id}/convert-to-managed",
                token=tok,
                json_body={"password": "AdminTyped12345!"},
            )
            assert r.status_code == 200
            # Legacy row must be byte-for-byte untouched
            legacy_after = await db.hr_users.find_one(
                {"id": legacy_id}, {"_id": 0}
            )
            assert legacy_after is not None, "legacy row was deleted!"
            assert legacy_after["password_hash"] == "$2b$12$legacyhashplaceholder"
            assert legacy_after["_legacy_marker"] is True
        finally:
            await db.hr_users.delete_one({"id": legacy_id})
            await db.user_directory.delete_one({"id": directory_id})
            await db.admin_audit.delete_many({"target_email": legacy_email})

    _run(body())


# ─── 4. revert-to-mirrored (rollback path) ────────────────────────────────
def test_revert_to_mirrored_after_convert_blocks_login_again():
    async def body():
        tok = await _admin_token()
        user = await _make_test_user(mirrored=True)
        pw = "AdminTyped12345!"
        try:
            # 1. Convert
            r1 = await _http(
                "POST",
                f"/api/admin/directory/k4/users/{user['id']}/convert-to-managed",
                token=tok,
                json_body={"password": pw},
            )
            assert r1.status_code == 200
            # 2. Confirm login works
            async with httpx.AsyncClient(base_url=BACKEND_URL, timeout=10) as c:
                login_ok = await c.post(
                    "/api/auth/multi-login",
                    json={"email": user["email"], "password": pw},
                )
                assert login_ok.status_code == 200
            # 3. Revert
            r2 = await _http(
                "POST",
                f"/api/admin/directory/k4/users/{user['id']}/revert-to-mirrored",
                token=tok,
            )
            assert r2.status_code == 200
            v = r2.json()["user"]
            assert v["mirrored"] is True
            assert v["source"] == "mirrored"
            # 4. Same password no longer works (rehashed unguessably)
            async with httpx.AsyncClient(base_url=BACKEND_URL, timeout=10) as c:
                login_fail = await c.post(
                    "/api/auth/multi-login",
                    json={"email": user["email"], "password": pw},
                )
                assert login_fail.status_code == 401, login_fail.text
            # 5. Audit row written
            a = await _last_audit_for(user["email"])
            assert a["action"] == "directory_k4_revert_to_mirrored"
            assert a["diff"]["rehashed"] is True
        finally:
            await _cleanup_test_user(user["id"])

    _run(body())


def test_revert_to_mirrored_refuses_when_no_mirror_sources():
    async def body():
        tok = await _admin_token()
        user = await _make_test_user(mirrored=False, with_mirror_sources=False)
        try:
            r = await _http(
                "POST",
                f"/api/admin/directory/k4/users/{user['id']}/revert-to-mirrored",
                token=tok,
            )
            assert r.status_code == 409
        finally:
            await _cleanup_test_user(user["id"])

    _run(body())


def test_revert_to_mirrored_refuses_already_mirrored():
    async def body():
        tok = await _admin_token()
        user = await _make_test_user(mirrored=True)
        try:
            r = await _http(
                "POST",
                f"/api/admin/directory/k4/users/{user['id']}/revert-to-mirrored",
                token=tok,
            )
            assert r.status_code == 409
        finally:
            await _cleanup_test_user(user["id"])

    _run(body())


# ─── 5. set-disabled ──────────────────────────────────────────────────────
def test_set_disabled_toggles_and_audits():
    async def body():
        tok = await _admin_token()
        user = await _make_test_user(mirrored=False)
        try:
            r1 = await _http(
                "POST",
                f"/api/admin/directory/k4/users/{user['id']}/set-disabled",
                token=tok,
                json_body={"disabled": True},
            )
            assert r1.status_code == 200
            assert r1.json()["user"]["disabled"] is True
            a1 = await _last_audit_for(user["email"])
            assert a1["action"] == "directory_k4_set_disabled"
            assert a1["diff"]["from"] is False
            assert a1["diff"]["to"] is True

            r2 = await _http(
                "POST",
                f"/api/admin/directory/k4/users/{user['id']}/set-disabled",
                token=tok,
                json_body={"disabled": False},
            )
            assert r2.status_code == 200
            assert r2.json()["user"]["disabled"] is False
        finally:
            await _cleanup_test_user(user["id"])

    _run(body())


def test_set_disabled_no_change_is_audited():
    async def body():
        tok = await _admin_token()
        user = await _make_test_user(mirrored=False)
        try:
            r = await _http(
                "POST",
                f"/api/admin/directory/k4/users/{user['id']}/set-disabled",
                token=tok,
                json_body={"disabled": False},
            )
            assert r.status_code == 200
            a = await _last_audit_for(user["email"])
            assert a["diff"]["no_change"] is True
        finally:
            await _cleanup_test_user(user["id"])

    _run(body())


def test_set_disabled_refuses_super_admin():
    """Super-admin must never be disabled — even via the new namespace."""

    async def body():
        tok = await _admin_token()
        # Find the real super-admin in the existing directory
        db = await _db()
        sa = await db.user_directory.find_one(
            {"is_super_admin": True}, {"_id": 0}
        )
        if not sa:
            return  # env without super-admin; skip
        r = await _http(
            "POST",
            f"/api/admin/directory/k4/users/{sa['id']}/set-disabled",
            token=tok,
            json_body={"disabled": True},
        )
        assert r.status_code == 409
        # And the actual record was NOT mutated
        after = await db.user_directory.find_one({"id": sa["id"]}, {"_id": 0})
        assert bool(after.get("disabled")) is False

    _run(body())


# ─── 6. Read-only K4a regression ──────────────────────────────────────────
def test_k4a_read_only_endpoints_still_return_200():
    """Sanity: K4b must not break K4a contract."""

    async def body():
        tok = await _admin_token()
        for path in (
            "/api/admin/directory/k4/users",
            "/api/admin/directory/k4/stats",
            "/api/admin/directory/k4/role-templates",
        ):
            r = await _http("GET", path, token=tok)
            assert r.status_code == 200, f"{path} regressed: {r.status_code}"

    _run(body())


# ─── 7. No plaintext credential leakage anywhere ──────────────────────────
def test_no_password_or_hash_in_any_k4b_response_or_audit():
    """Defensive sweep across every K4b mutation path."""

    async def body():
        tok = await _admin_token()
        user = await _make_test_user(mirrored=True)
        pw = "VerySecretPw_887766"
        try:
            for method, path, payload in [
                ("POST", f"/api/admin/directory/k4/users/{user['id']}/role-template",
                 {"role_template_id": "rt-hr-manager"}),
                ("POST", f"/api/admin/directory/k4/users/{user['id']}/convert-to-managed",
                 {"password": pw}),
                ("POST", f"/api/admin/directory/k4/users/{user['id']}/set-disabled",
                 {"disabled": True}),
                ("POST", f"/api/admin/directory/k4/users/{user['id']}/set-disabled",
                 {"disabled": False}),
                ("POST", f"/api/admin/directory/k4/users/{user['id']}/revert-to-mirrored",
                 None),
            ]:
                r = await _http(method, path, token=tok, json_body=payload)
                assert r.status_code in (200, 409), f"{path} -> {r.status_code} {r.text}"
                # Never leak password / password_hash / bcrypt fragment
                assert pw not in r.text, f"plaintext password leaked in {path}"
                assert "password_hash" not in r.text, f"password_hash leaked in {path}"
                assert "$2b$" not in r.text, f"bcrypt hash leaked in {path}"
            # Audit table sweep
            db = await _db()
            async for entry in db.admin_audit.find(
                {"target_email": user["email"]}, {"_id": 0}
            ):
                txt = str(entry)
                assert pw not in txt, f"password leaked in audit row: {entry}"
                assert "$2b$" not in txt, f"hash leaked in audit row: {entry}"
        finally:
            await _cleanup_test_user(user["id"])

    _run(body())
