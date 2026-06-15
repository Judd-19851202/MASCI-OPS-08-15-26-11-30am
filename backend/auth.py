"""
MASCI Safety Hub — Phase 1 user auth (JWT + bcrypt).

Coexists with the legacy shared-password admin gate in `server.py`. During
the 30-day migration window, admin-protected endpoints can accept EITHER:
  - X-Admin-Token header (legacy HMAC of ADMIN_PASSWORD), OR
  - Authorization: Bearer <jwt> / httpOnly access_token cookie, where the
    JWT belongs to a user with role `owner` or `admin`.

After migration the legacy path gets removed and only JWT-based auth remains.
"""
from __future__ import annotations

import os
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Header
from pydantic import BaseModel, EmailStr, Field

logger = logging.getLogger(__name__)

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = int(os.environ.get("ACCESS_TOKEN_MINUTES", "10080"))  # 7 days
REFRESH_TOKEN_DAYS = int(os.environ.get("REFRESH_TOKEN_DAYS", "30"))

VALID_ROLES = {"owner", "admin", "member"}

# Seed users — created on first backend boot if not present.
SEED_USERS = [
    ("david.jewett@mascigc.com", "David Jewett", "owner"),
    ("chris.wright@mascigc.com", "Chris Wright", "owner"),
    ("ramon.rodriguez@mascigc.com", "Ramon Rodriguez", "owner"),
    ("jaymn.judd@mascigc.com", "Jaymn Judd", "owner"),
    ("safety@mascigc.com", "MASCI Safety", "admin"),
]
# iter232 · Pulled from env (operator-stated stabilization-phase posture
# preserves auth-sensitive defaults as explicit operator decisions, not
# hardcoded constants). Fallback is the historical value to preserve
# current behavior on environments that haven't set the key yet — this
# is the documented safe fallback per the code-review triage.
SEED_DEFAULT_PASSWORD = os.environ.get("SEED_DEFAULT_PASSWORD", "Welcome2MASCI!")


# ------------------------- crypto helpers -------------------------
def _jwt_secret() -> str:
    v = os.environ.get("JWT_SECRET", "").strip()
    if not v:
        # Dev-only fallback. Production must set JWT_SECRET.
        logger.warning("JWT_SECRET not set — using an unstable dev fallback.")
        return "masci-dev-only-do-not-use-in-production"
    return v


def hash_password(password: str) -> str:
    # Track 14.0-AUTH-PASSWORD-PARITY-CERTIFICATION:
    # Pin to rounds=12 explicitly. Matches pm_auth.hash_password and
    # user_directory.hash_password. bcrypt's default IS currently 12,
    # so this change does NOT invalidate any existing hashes — it just
    # locks the contract so future bcrypt upgrades cannot silently
    # change the work factor.
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def create_access_token(user_id: str, email: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_MINUTES),
    }
    return jwt.encode(payload, _jwt_secret(), algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "type": "refresh",
        "exp": datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_DAYS),
    }
    return jwt.encode(payload, _jwt_secret(), algorithm=JWT_ALGORITHM)


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    # secure=False so dev (http preview) works; production is always behind HTTPS
    # ingress so browsers still respect the cookies.
    response.set_cookie(
        "access_token", access_token, httponly=True, secure=False,
        samesite="lax", max_age=ACCESS_TOKEN_MINUTES * 60, path="/",
    )
    response.set_cookie(
        "refresh_token", refresh_token, httponly=True, secure=False,
        samesite="lax", max_age=REFRESH_TOKEN_DAYS * 86400, path="/",
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")


# ------------------------- Pydantic models -------------------------
class User(BaseModel):
    id: str
    email: str
    name: str
    role: str
    is_active: bool = True
    must_change_password: bool = True
    created_at: str
    last_login_at: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=10, max_length=200)


class CreateUserRequest(BaseModel):
    email: str
    name: str
    role: str
    password: str = Field(..., min_length=10, max_length=200)


class UpdateUserRequest(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class ResetPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=10, max_length=200)


def _doc_to_user(doc: dict) -> User:
    return User(
        id=doc["id"],
        email=doc["email"],
        name=doc.get("name", ""),
        role=doc.get("role", "member"),
        is_active=doc.get("is_active", True),
        must_change_password=doc.get("must_change_password", False),
        created_at=doc.get("created_at", ""),
        last_login_at=doc.get("last_login_at"),
    )


# ------------------------- dependencies (DB-aware) -------------------------
def build_auth_router(db):
    """Build all auth routes + dependencies bound to the given Motor db."""
    router = APIRouter(prefix="/api")

    async def _extract_user_from_token(request: Request) -> Optional[dict]:
        # Cookie first (preferred — httpOnly)
        token = request.cookies.get("access_token")
        if not token:
            auth = request.headers.get("Authorization", "")
            if auth.startswith("Bearer "):
                token = auth[7:]
        if not token:
            return None
        try:
            payload = jwt.decode(token, _jwt_secret(), algorithms=[JWT_ALGORITHM])
            if payload.get("type") != "access":
                return None
            user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0})
            if not user or not user.get("is_active", True):
                return None
            user.pop("password_hash", None)
            return user
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    async def get_current_user(request: Request) -> dict:
        user = await _extract_user_from_token(request)
        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        return user

    def require_role(*roles: str):
        async def _inner(user: dict = Depends(get_current_user)) -> dict:
            if user.get("role") not in roles:
                raise HTTPException(status_code=403, detail="Insufficient role")
            return user
        return _inner

    async def require_admin_or_owner(user: dict = Depends(get_current_user)) -> dict:
        if user.get("role") not in {"owner", "admin"}:
            raise HTTPException(status_code=403, detail="Admin role required")
        return user

    async def optional_user(request: Request) -> Optional[dict]:
        return await _extract_user_from_token(request)

    # ------------------------- auth endpoints -------------------------
    @router.post("/auth/login")
    async def login(body: LoginRequest, response: Response, request: Request):
        email = body.email.strip().lower()
        user = await db.users.find_one({"email": email}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        if not user.get("is_active", True):
            raise HTTPException(status_code=403, detail="Account is disabled")
        if not verify_password(body.password, user.get("password_hash", "")):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        access = create_access_token(user["id"], user["email"], user["role"])
        refresh = create_refresh_token(user["id"])
        _set_auth_cookies(response, access, refresh)

        await db.users.update_one(
            {"id": user["id"]},
            {"$set": {"last_login_at": datetime.now(timezone.utc).isoformat()}},
        )
        user.pop("password_hash", None)
        return {"user": _doc_to_user(user), "access_token": access}

    @router.post("/auth/logout")
    async def logout(response: Response):
        _clear_auth_cookies(response)
        return {"ok": True}

    @router.get("/auth/me")
    async def me(user: dict = Depends(get_current_user)):
        return _doc_to_user(user)

    @router.post("/auth/change-password")
    async def change_password(
        body: ChangePasswordRequest,
        user: dict = Depends(get_current_user),
    ):
        fresh = await db.users.find_one({"id": user["id"]}, {"_id": 0})
        if not fresh or not verify_password(body.current_password, fresh.get("password_hash", "")):
            raise HTTPException(status_code=401, detail="Current password is incorrect")
        if body.new_password == body.current_password:
            raise HTTPException(status_code=400, detail="New password must be different")
        await db.users.update_one(
            {"id": user["id"]},
            {"$set": {
                "password_hash": hash_password(body.new_password),
                "must_change_password": False,
                "password_changed_at": datetime.now(timezone.utc).isoformat(),
            }},
        )
        return {"ok": True}

    @router.post("/auth/refresh")
    async def refresh_access_token(request: Request, response: Response):
        refresh = request.cookies.get("refresh_token")
        if not refresh:
            raise HTTPException(status_code=401, detail="No refresh token")
        try:
            payload = jwt.decode(refresh, _jwt_secret(), algorithms=[JWT_ALGORITHM])
            if payload.get("type") != "refresh":
                raise HTTPException(status_code=401, detail="Invalid refresh token")
            user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0})
            if not user or not user.get("is_active", True):
                raise HTTPException(status_code=401, detail="User not found or disabled")
            access = create_access_token(user["id"], user["email"], user["role"])
            response.set_cookie(
                "access_token", access, httponly=True, secure=False,
                samesite="lax", max_age=ACCESS_TOKEN_MINUTES * 60, path="/",
            )
            return {"ok": True}
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Refresh token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

    # ------------------------- user management -------------------------
    @router.get("/users", response_model=List[User])
    async def list_users(_: dict = Depends(require_admin_or_owner)):
        docs = await db.users.find(
            {}, {"_id": 0, "password_hash": 0}
        ).sort("email", 1).to_list(500)
        return [_doc_to_user(d) for d in docs]

    @router.post("/users", response_model=User)
    async def create_user(
        body: CreateUserRequest,
        _: dict = Depends(require_admin_or_owner),
    ):
        email = body.email.strip().lower()
        if body.role not in VALID_ROLES:
            raise HTTPException(status_code=400, detail=f"Role must be one of {sorted(VALID_ROLES)}")
        if await db.users.find_one({"email": email}):
            raise HTTPException(status_code=409, detail="A user with that email already exists")
        doc = {
            "id": str(uuid.uuid4()),
            "email": email,
            "name": body.name.strip(),
            "role": body.role,
            "password_hash": hash_password(body.password),
            "is_active": True,
            "must_change_password": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.users.insert_one(doc)
        doc.pop("_id", None)
        doc.pop("password_hash", None)
        return _doc_to_user(doc)

    @router.put("/users/{user_id}", response_model=User)
    async def update_user(
        user_id: str,
        body: UpdateUserRequest,
        actor: dict = Depends(require_admin_or_owner),
    ):
        patch: dict = {}
        if body.name is not None:
            patch["name"] = body.name.strip()
        if body.role is not None:
            if body.role not in VALID_ROLES:
                raise HTTPException(status_code=400, detail=f"Role must be one of {sorted(VALID_ROLES)}")
            patch["role"] = body.role
        if body.is_active is not None:
            if not body.is_active and user_id == actor["id"]:
                raise HTTPException(status_code=400, detail="You cannot disable your own account")
            patch["is_active"] = body.is_active
        if not patch:
            raise HTTPException(status_code=400, detail="No fields to update")
        res = await db.users.update_one({"id": user_id}, {"$set": patch})
        if res.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        doc = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
        return _doc_to_user(doc)

    @router.post("/users/{user_id}/reset-password")
    async def admin_reset_password(
        user_id: str,
        body: ResetPasswordRequest,
        _: dict = Depends(require_admin_or_owner),
    ):
        res = await db.users.update_one(
            {"id": user_id},
            {"$set": {
                "password_hash": hash_password(body.new_password),
                "must_change_password": True,
            }},
        )
        if res.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        return {"ok": True}

    @router.delete("/users/{user_id}")
    async def deactivate_user(
        user_id: str,
        actor: dict = Depends(require_admin_or_owner),
    ):
        if user_id == actor["id"]:
            raise HTTPException(status_code=400, detail="You cannot deactivate your own account")
        res = await db.users.update_one({"id": user_id}, {"$set": {"is_active": False}})
        if res.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        return {"ok": True}

    return router, get_current_user, require_admin_or_owner, optional_user


async def seed_initial_users(db) -> None:
    """Idempotent seed. Creates missing SEED_USERS with SEED_DEFAULT_PASSWORD,
    must_change_password=true. Existing users are left untouched so admins
    can reset passwords without this function undoing their changes."""
    try:
        await db.users.create_index("email", unique=True)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"users.email index: {e}")
    for email, name, role in SEED_USERS:
        if await db.users.find_one({"email": email}):
            continue
        await db.users.insert_one({
            "id": str(uuid.uuid4()),
            "email": email,
            "name": name,
            "role": role,
            "password_hash": hash_password(SEED_DEFAULT_PASSWORD),
            "is_active": True,
            "must_change_password": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        logger.info(f"Seeded user {email} ({role})")
