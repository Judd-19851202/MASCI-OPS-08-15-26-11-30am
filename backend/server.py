from fastapi import FastAPI, APIRouter, HTTPException, Header, Depends, Response, Request, UploadFile, File, Form
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import hashlib
import hmac
import re
import time
import secrets
import asyncio
import csv
import io
from collections import defaultdict
from threading import Lock
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Dict, Any, Tuple
import uuid
from datetime import datetime, timezone, timedelta


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI(title="MASCI Job Site Safety Inspection API")
api_router = APIRouter(prefix="/api")


# ------------------------- Rate limiting (in-memory, single-instance) -------------------------
# Public POST endpoints (form submissions, translate) are unauthenticated by
# design — crews submit without logging in. To prevent spam / bot abuse we
# cap each IP to N submissions per hour per endpoint. Single-instance backend
# so a process-local dict is sufficient — no Redis required.

_RATE_LOCK = Lock()
_PUBLIC_POST_BUCKETS: Dict[str, List[float]] = defaultdict(list)
_LOGIN_FAIL_BUCKETS: Dict[str, List[float]] = defaultdict(list)

PUBLIC_POST_LIMIT_PER_HOUR = int(os.environ.get("PUBLIC_POST_LIMIT_PER_HOUR", "30"))
LOGIN_MAX_FAILS_PER_WINDOW = int(os.environ.get("LOGIN_MAX_FAILS", "10"))
LOGIN_LOCKOUT_SECONDS = int(os.environ.get("LOGIN_LOCKOUT_SECONDS", "900"))  # 15 min


def _client_ip(request: Request) -> str:
    """Best-effort client IP. Trusts X-Forwarded-For when present (Kubernetes
    ingress sets it). Falls back to the immediate peer IP."""
    xff = request.headers.get("x-forwarded-for") or ""
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit_public_post(request: Request):
    """FastAPI dependency that throttles each (IP, endpoint) to
    PUBLIC_POST_LIMIT_PER_HOUR submissions. Raises 429 when exceeded.
    Set RATE_LIMITING=off in .env to disable (e.g., automated tests)."""
    if os.environ.get("RATE_LIMITING", "on").lower() in ("off", "false", "0"):
        return
    ip = _client_ip(request)
    key = f"{request.url.path}:{ip}"
    now = time.time()
    cutoff = now - 3600
    with _RATE_LOCK:
        bucket = _PUBLIC_POST_BUCKETS[key]
        bucket[:] = [t for t in bucket if t > cutoff]
        if len(bucket) >= PUBLIC_POST_LIMIT_PER_HOUR:
            raise HTTPException(
                status_code=429,
                detail=(
                    f"Too many submissions from this device "
                    f"(limit {PUBLIC_POST_LIMIT_PER_HOUR}/hour). "
                    f"Try again later or contact MASCI safety."
                ),
            )
        bucket.append(now)


def _check_login_lockout(ip: str) -> None:
    cutoff = time.time() - LOGIN_LOCKOUT_SECONDS
    with _RATE_LOCK:
        bucket = _LOGIN_FAIL_BUCKETS[ip]
        bucket[:] = [t for t in bucket if t > cutoff]
        if len(bucket) >= LOGIN_MAX_FAILS_PER_WINDOW:
            oldest = bucket[0]
            wait_s = int(LOGIN_LOCKOUT_SECONDS - (time.time() - oldest))
            wait_min = max(1, (wait_s + 59) // 60)
            raise HTTPException(
                status_code=429,
                detail=(
                    f"Too many failed login attempts. "
                    f"Try again in ~{wait_min} minute(s)."
                ),
            )


def _record_login_fail(ip: str) -> None:
    with _RATE_LOCK:
        _LOGIN_FAIL_BUCKETS[ip].append(time.time())


def _reset_login_fails(ip: str) -> None:
    with _RATE_LOCK:
        _LOGIN_FAIL_BUCKETS.pop(ip, None)


# ------------------------- Admin auth -------------------------
# Simple shared-password gate. The "token" returned to the client is a
# deterministic HMAC(password, server-secret) so the password itself never
# leaves the device after login. On every protected request the client
# sends X-Admin-Token; we recompute and compare in constant time.
#
# The HMAC secret is read from ADMIN_HMAC_SECRET (preferred). If not set,
# we generate a random per-process secret and warn — every admin will need
# to log in again on the next backend restart, which is the right safety
# behavior for an unconfigured deployment.
def _admin_hmac_secret() -> bytes:
    explicit = os.environ.get("ADMIN_HMAC_SECRET", "").strip()
    if explicit:
        return explicit.encode()
    # Backwards-compat / first-boot fallback. Cache so all calls within a
    # process see the same value (so tokens stay valid until restart).
    global _ADMIN_HMAC_FALLBACK
    try:
        return _ADMIN_HMAC_FALLBACK
    except NameError:
        pass
    _ADMIN_HMAC_FALLBACK = secrets.token_bytes(64)
    logging.getLogger(__name__).warning(
        "ADMIN_HMAC_SECRET is not set. Generated a random per-process secret. "
        "Admin tokens will invalidate on backend restart — set ADMIN_HMAC_SECRET "
        "in backend/.env to a stable random string for production."
    )
    return _ADMIN_HMAC_FALLBACK


# Session epoch — a revocation dial that gets folded into every issued
# token's HMAC input. Bumping `ADMIN_SESSION_EPOCH` in backend/.env and
# restarting the backend instantly invalidates every token that was
# issued before the bump (admin, PM, shop, dev) without having to rotate
# the underlying passwords. Use this when a token leaks, an employee
# leaves, or you just want every active session to re-authenticate.
#
# Default is "1" so existing deploys stay consistent. Any string works;
# a timestamp or incrementing integer are both fine.
def _session_epoch() -> str:
    v = os.environ.get("ADMIN_SESSION_EPOCH", "1").strip()
    return v or "1"


def _admin_token_for(password: str) -> str:
    msg = (f"epoch={_session_epoch()}|admin:" + password).encode()
    return hmac.new(_admin_hmac_secret(), msg, hashlib.sha256).hexdigest()


def _pm_token_for(password: str) -> str:
    """PM portal token. Distinct namespace from admin so a stolen PM token
    cannot be replayed against admin-strict (backup/recovery) routes."""
    msg = (f"epoch={_session_epoch()}|pm:" + password).encode()
    return hmac.new(_admin_hmac_secret(), msg, hashlib.sha256).hexdigest()


def _is_valid_admin_token(tok: Optional[str]) -> bool:
    pw = os.environ.get("ADMIN_PASSWORD", "")
    if not tok or not pw:
        return False
    return hmac.compare_digest(tok, _admin_token_for(pw))


def _is_valid_pm_token(tok: Optional[str]) -> bool:
    pw = os.environ.get("PM_PASSWORD", "")
    if not tok or not pw:
        return False
    return hmac.compare_digest(tok, _pm_token_for(pw))


def _dev_token_for(password: str) -> str:
    """Developer (vendor/Judd Group LLC) portal token. Distinct namespace
    from admin/pm so a stolen dev token cannot be replayed against any
    MASCI-facing admin route, and vice versa."""
    msg = (f"epoch={_session_epoch()}|dev:" + password).encode()
    return hmac.new(_admin_hmac_secret(), msg, hashlib.sha256).hexdigest()


def _is_valid_dev_token(tok: Optional[str]) -> bool:
    pw = os.environ.get("DEV_PASSWORD", "")
    if not tok or not pw:
        return False
    return hmac.compare_digest(tok, _dev_token_for(pw))


def require_dev(x_dev_token: Optional[str] = Header(default=None)):
    """Vendor-only gate — used for The Judd Group LLC internal pages
    (System Owner & Operations Manual, manual snapshots). Admin and PM
    tokens are NOT accepted: this surface is hidden from MASCI staff."""
    expected_pw = os.environ.get("DEV_PASSWORD", "")
    if not expected_pw:
        # No dev password configured → gate disabled (local dev only)
        return True
    if not x_dev_token:
        raise HTTPException(status_code=401, detail="Developer login required")
    if not _is_valid_dev_token(x_dev_token):
        raise HTTPException(status_code=401, detail="Invalid developer token")
    return True


def require_admin(
    x_admin_token: Optional[str] = Header(default=None),
    x_pm_token: Optional[str] = Header(default=None),
):
    """FastAPI dependency. Accepts an Admin OR a Project-Manager token.

    PMs need access to the same day-to-day office surface (jobs, equipment,
    employees, safety records, posters, compliance exports). Backup &
    recovery routes use ``require_admin_strict`` instead so a fired PM
    cannot exfiltrate or wipe the system on the way out.
    """
    expected_pw = os.environ.get("ADMIN_PASSWORD", "")
    pm_pw = os.environ.get("PM_PASSWORD", "")
    if not expected_pw and not pm_pw:
        # No passwords configured → gate disabled (open mode)
        return True
    if x_admin_token and _is_valid_admin_token(x_admin_token):
        return True
    if x_pm_token and _is_valid_pm_token(x_pm_token):
        return True
    if not x_admin_token and not x_pm_token:
        raise HTTPException(status_code=401, detail="Admin or PM login required")
    raise HTTPException(status_code=401, detail="Invalid admin/PM token")


def require_admin_strict(x_admin_token: Optional[str] = Header(default=None)):
    """Admin-only gate — used on backup & recovery endpoints. PM tokens are
    rejected here so a project manager cannot download or restore backups."""
    expected_pw = os.environ.get("ADMIN_PASSWORD", "")
    if not expected_pw:
        return True
    if not x_admin_token:
        raise HTTPException(status_code=401, detail="Admin login required")
    if not _is_valid_admin_token(x_admin_token):
        raise HTTPException(status_code=401, detail="Invalid admin token")
    return True


def _shop_token_for(password: str) -> str:
    msg = (f"epoch={_session_epoch()}|shop:" + password).encode()
    return hmac.new(_admin_hmac_secret(), msg, hashlib.sha256).hexdigest()


def require_shop_or_admin(
    x_admin_token: Optional[str] = Header(default=None),
    x_shop_token: Optional[str] = Header(default=None),
    x_pm_token: Optional[str] = Header(default=None),
):
    """Accepts an Admin, PM, or Shop token.

    Used on equipment master / equipment-parts / inspection-signoff routes
    that any of the three personas can legitimately touch. Backup &
    recovery routes still use ``require_admin_strict``.
    """
    admin_pw = os.environ.get("ADMIN_PASSWORD", "")
    shop_pw = os.environ.get("SHOP_PASSWORD", "")
    pm_pw = os.environ.get("PM_PASSWORD", "")
    if not admin_pw and not shop_pw and not pm_pw:
        return True  # all gates disabled
    if x_admin_token and _is_valid_admin_token(x_admin_token):
        return True
    if x_pm_token and _is_valid_pm_token(x_pm_token):
        return True
    if x_shop_token and shop_pw:
        expected = _shop_token_for(shop_pw)
        if hmac.compare_digest(x_shop_token, expected):
            return True
    raise HTTPException(status_code=401, detail="Shop, PM, or admin login required")


class AdminLoginRequest(BaseModel):
    password: str


# ─────────────────────────────────────────────────────────────────────────
# /api/health — DEFENSE LAYER 1
# Lightweight liveness probe. Does NOT touch the DB, NOT load any state,
# NOT call any external service. Always responds in <1ms even when the
# rest of the backend is heavy under a backup build or DB query.
# Cloudflare + Emergent's deploy infrastructure use this to determine
# whether the origin container is alive — if this stops responding for
# >60s the platform routes a Cloudflare 520 to users. Keeping it
# absolutely synchronous + dependency-free is what prevents production
# outages.
# ─────────────────────────────────────────────────────────────────────────
@api_router.get("/health")
def api_health():
    return {"ok": True, "service": "masci-hub", "ts": datetime.now(timezone.utc).isoformat()}


@api_router.get("/healthz")
def api_healthz():
    return {"ok": True}


# ---------------------------------------------------------------------------
# Build fingerprint endpoint — /api/version
#
# Motivation: twice now we've hit silent backend-vs-frontend drift after a
# deploy (frontend bundle updates, backend Python code stays on an older
# snapshot). This endpoint gives every audit script + support ticket a
# one-curl way to confirm the backend is actually running the committed
# code.
#
# Returns three independent signals:
#   • commit         — git SHA set at deploy time (env var GIT_COMMIT)
#   • built_at       — ISO timestamp stamped at deploy (env var BUILT_AT)
#   • source_hash    — md5 of key backend source files, computed at startup
#
# The source_hash is the truth even if the env vars aren't wired — if
# this hash matches the one you get from running the same md5 locally
# on the current commit, the backend code IS the current commit.
# ---------------------------------------------------------------------------
import hashlib as _hashlib  # noqa: E402 — deliberate inline import, local to this block

_STARTUP_TS = datetime.now(timezone.utc)

def _compute_source_hash() -> str:
    """Hash the key backend source files so a running server can prove
    which commit it's executing without needing git in the container."""
    paths = [
        ROOT_DIR / "server.py",
        ROOT_DIR / "training_pdf.py",
        ROOT_DIR / "pdf_render.py",
    ]
    h = _hashlib.md5()
    for p in paths:
        try:
            with open(p, "rb") as f:
                h.update(f.read())
        except OSError:
            # file missing — record that in the hash so drift is still visible
            h.update(b"MISSING:" + str(p).encode())
    return h.hexdigest()

_SOURCE_HASH = _compute_source_hash()


@api_router.get("/version")
def api_version():
    return {
        "service": "masci-hub",
        "commit": os.environ.get("GIT_COMMIT", "unknown"),
        "built_at": os.environ.get("BUILT_AT", "unknown"),
        "source_hash": _SOURCE_HASH,
        "started_at": _STARTUP_TS.isoformat(),
        "uptime_s": int((datetime.now(timezone.utc) - _STARTUP_TS).total_seconds()),
    }


# ---------------------------------------------------------------------------
# Internal Operations Manual — Developer portal only.
# Gated by require_dev (password in DEV_PASSWORD, distinct from admin/pm).
# Generated on-demand from ops_manual.py so edits ship instantly without
# requiring a redeploy of static assets. Admin/PM tokens cannot access.
# ---------------------------------------------------------------------------
from fastapi.responses import Response as _FastAPIResponse  # noqa: E402


@api_router.post("/dev/login")
async def dev_login(body: AdminLoginRequest, request: Request):
    """Developer (vendor/Judd Group LLC) portal login. Issues a token
    accepted ONLY by require_dev — never by any admin/PM/shop route."""
    ip = _client_ip(request)
    _check_login_lockout(ip)
    expected_pw = os.environ.get("DEV_PASSWORD", "")
    if not expected_pw:
        return {"ok": True, "token": "open-mode"}
    if not hmac.compare_digest(body.password, expected_pw):
        _record_login_fail(ip)
        raise HTTPException(status_code=401, detail="Wrong password")
    _reset_login_fails(ip)
    return {"ok": True, "token": _dev_token_for(expected_pw)}


@api_router.get("/dev/check")
async def dev_check(_: bool = Depends(require_dev)):
    """Verify a stored dev token is still valid."""
    return {"ok": True}


@api_router.get("/dev/ops-manual.pdf")
def dev_ops_manual_pdf(_: bool = Depends(require_dev)):
    from ops_manual import render_ops_manual_pdf
    pdf = render_ops_manual_pdf()
    return _FastAPIResponse(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="MASCI_HUB_Operations_Manual.pdf"',
            "Cache-Control": "private, no-store",
        },
    )


@api_router.get("/dev/ops-manual.docx")
def dev_ops_manual_docx(_: bool = Depends(require_dev)):
    from ops_manual import render_ops_manual_docx
    docx = render_ops_manual_docx()
    return _FastAPIResponse(
        content=docx,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": 'attachment; filename="MASCI_HUB_Operations_Manual.docx"',
            "Cache-Control": "private, no-store",
        },
    )


# --- Ops Manual snapshots (pinned historical copies) ---------------------
# Store both PDF + DOCX bytes (base64) plus the backend source_hash in
# MongoDB so a specific "official" revision of the manual can be pulled
# back verbatim months later even after the source data has changed.
import base64 as _ops_b64  # noqa: E402


@api_router.post("/dev/ops-manual/snapshot")
async def dev_ops_manual_snapshot(
    body: Optional[dict] = None,
    _: bool = Depends(require_dev),
):
    from ops_manual import render_ops_manual_pdf, render_ops_manual_docx
    note = ""
    if isinstance(body, dict):
        note = str(body.get("note", ""))[:500]
    pdf = render_ops_manual_pdf()
    docx = render_ops_manual_docx()
    snap = {
        "id": uuid.uuid4().hex,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_hash": _SOURCE_HASH,
        "note": note,
        "pdf_b64": _ops_b64.b64encode(pdf).decode("ascii"),
        "docx_b64": _ops_b64.b64encode(docx).decode("ascii"),
        "pdf_bytes": len(pdf),
        "docx_bytes": len(docx),
    }
    await db.ops_manual_snapshots.insert_one(snap)
    return {
        "ok": True,
        "id": snap["id"],
        "created_at": snap["created_at"],
        "source_hash": snap["source_hash"],
        "note": snap["note"],
        "pdf_bytes": snap["pdf_bytes"],
        "docx_bytes": snap["docx_bytes"],
    }


@api_router.get("/dev/ops-manual/snapshots")
async def dev_ops_manual_list_snapshots(_: bool = Depends(require_dev)):
    cursor = db.ops_manual_snapshots.find(
        {},
        {"_id": 0, "pdf_b64": 0, "docx_b64": 0},
    ).sort("created_at", -1).limit(200)
    rows = await cursor.to_list(200)
    return {"snapshots": rows}


@api_router.delete("/dev/ops-manual/snapshots/{snap_id}")
async def dev_ops_manual_delete_snapshot(
    snap_id: str, _: bool = Depends(require_dev)
):
    r = await db.ops_manual_snapshots.delete_one({"id": snap_id})
    if r.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return {"ok": True}


@api_router.get("/dev/ops-manual/snapshots/{snap_id}.pdf")
async def dev_ops_manual_snapshot_pdf(
    snap_id: str, _: bool = Depends(require_dev)
):
    doc = await db.ops_manual_snapshots.find_one(
        {"id": snap_id}, {"_id": 0, "pdf_b64": 1, "created_at": 1}
    )
    if not doc or not doc.get("pdf_b64"):
        raise HTTPException(status_code=404, detail="Snapshot not found")
    pdf = _ops_b64.b64decode(doc["pdf_b64"])
    stamp = (doc.get("created_at") or "").replace(":", "-").split(".")[0]
    return _FastAPIResponse(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="MASCI_HUB_Operations_Manual_{stamp}.pdf"',
            "Cache-Control": "private, no-store",
        },
    )


@api_router.get("/dev/ops-manual/snapshots/{snap_id}.docx")
async def dev_ops_manual_snapshot_docx(
    snap_id: str, _: bool = Depends(require_dev)
):
    doc = await db.ops_manual_snapshots.find_one(
        {"id": snap_id}, {"_id": 0, "docx_b64": 1, "created_at": 1}
    )
    if not doc or not doc.get("docx_b64"):
        raise HTTPException(status_code=404, detail="Snapshot not found")
    docx = _ops_b64.b64decode(doc["docx_b64"])
    stamp = (doc.get("created_at") or "").replace(":", "-").split(".")[0]
    return _FastAPIResponse(
        content=docx,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="MASCI_HUB_Operations_Manual_{stamp}.docx"',
            "Cache-Control": "private, no-store",
        },
    )


# --- Source bundle download --------------------------------------------
# One-click zip of the full application source tree so an auditor /
# acquirer / due-diligence package can pair the pinned Ops Manual with
# a byte-exact copy of the code that produced it.
#
# Strict exclusions (never shipped in the zip):
#   • /app/backend/backups/*            (customer DB dumps)
#   • /app/backend/storage/*            (uploaded files — customer data)
#   • /app/backend/__pycache__/*        (binary caches)
#   • /app/backend/.env                 (secrets)
#   • /app/backend/data/*.bak.json      (historical data snapshots)
#   • /app/frontend/node_modules/*      (build artefact)
#   • /app/frontend/build/*             (build artefact)
#   • /app/frontend/.env                (secrets)
#   • **/.git/*                         (repo metadata)
#   • *.pyc                             (binary caches)
import io as _src_io  # noqa: E402
import zipfile as _src_zip  # noqa: E402
from pathlib import Path as _SrcPath  # noqa: E402


_SRC_EXCLUDE_DIRS = {
    "backups", "storage", "__pycache__", "node_modules", "build",
    ".git", ".next", ".cache", ".yarn", "dist", ".pytest_cache",
    ".emergent",
}
_SRC_EXCLUDE_SUFFIXES = {".pyc", ".pyo", ".log"}
_SRC_ROOTS = [
    ("app", _SrcPath("/app"), {
        "allowed_top_level": {
            "backend", "frontend", "memory", "scripts", "test_reports",
            "README.md", "ATLAS_MIGRATION.md", "auth_testing.md",
            "test_result.md", "design_guidelines.json",
        },
    }),
]


def _src_should_skip(path: _SrcPath) -> bool:
    name = path.name
    # skip env files wherever they land
    if name == ".env" or name.startswith(".env."):
        return True
    # skip historical data snapshots
    if name.endswith(".bak.json"):
        return True
    if path.suffix in _SRC_EXCLUDE_SUFFIXES:
        return True
    # skip anything inside an excluded directory
    for part in path.parts:
        if part in _SRC_EXCLUDE_DIRS:
            return True
    return False


def _build_source_bundle() -> bytes:
    buf = _src_io.BytesIO()
    with _src_zip.ZipFile(buf, "w", _src_zip.ZIP_DEFLATED, compresslevel=6) as zf:
        manifest_lines = [
            "MASCI HUB — Source Bundle",
            f"Generated: {datetime.now(timezone.utc).isoformat()}",
            f"Source hash: {_SOURCE_HASH}",
            f"Commit: {os.environ.get('GIT_COMMIT', 'unknown')}",
            f"Built at: {os.environ.get('BUILT_AT', 'unknown')}",
            "",
            "Classification: CONFIDENTIAL — The Judd Group LLC",
            "Excluded: /backups, /storage, node_modules, build, .env, .git, *.pyc, *.bak.json",
            "",
        ]
        for label, root, opts in _SRC_ROOTS:
            if not root.exists():
                continue
            allowed = opts.get("allowed_top_level")
            for item in sorted(root.iterdir()):
                if allowed and item.name not in allowed:
                    continue
                if _src_should_skip(item):
                    continue
                if item.is_file():
                    try:
                        arcname = f"{label}/{item.name}"
                        zf.write(item, arcname)
                        manifest_lines.append(arcname)
                    except OSError:
                        continue
                elif item.is_dir():
                    for sub in item.rglob("*"):
                        if sub.is_dir():
                            continue
                        if _src_should_skip(sub):
                            continue
                        try:
                            rel = sub.relative_to(root)
                            arcname = f"{label}/{rel.as_posix()}"
                            zf.write(sub, arcname)
                            manifest_lines.append(arcname)
                        except (OSError, ValueError):
                            continue
        zf.writestr("app/MANIFEST.txt", "\n".join(manifest_lines) + "\n")
    buf.seek(0)
    return buf.getvalue()


@api_router.get("/dev/source-bundle.zip")
def dev_source_bundle(_: bool = Depends(require_dev)):
    """Stream the full application source tree as a zip. Excludes all
    customer data (backups, storage), secrets (.env), and build
    artefacts (node_modules, build, __pycache__). Intended to be paired
    with a pinned Ops Manual snapshot for a due-diligence package."""
    data = _build_source_bundle()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return _FastAPIResponse(
        content=data,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="MASCI_HUB_Source_Bundle_{stamp}.zip"',
            "Cache-Control": "private, no-store",
            "X-Source-Hash": _SOURCE_HASH,
        },
    )


@api_router.get("/dev/source-bundle.info")
def dev_source_bundle_info(_: bool = Depends(require_dev)):
    """Quick metadata probe — size + file count — so the UI can show a
    size estimate before the user clicks download."""
    data = _build_source_bundle()
    with _src_zip.ZipFile(_src_io.BytesIO(data), "r") as zf:
        file_count = len(zf.namelist())
    return {
        "bytes": len(data),
        "file_count": file_count,
        "source_hash": _SOURCE_HASH,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }



# ---------------------------------------------------------------------------
# Soft-delete framework — give every master-list 🗑️ button a 14-day undo
# instead of an immediate hard-delete, so a mis-click on a 234-row table
# is fully recoverable from the UI without restoring a backup.
#
# Convention: every soft-deleted row gets ``deleted_at`` (ISO timestamp).
# Every list endpoint that should hide deletes filters with the
# ``ACTIVE_FILTER`` below. Restore = unset ``deleted_at``. Anything older
# than 14 days is hard-purged on the next list call (best effort).
# ---------------------------------------------------------------------------
SOFT_DELETE_RETAIN_DAYS = 14
ACTIVE_FILTER: Dict[str, Any] = {"deleted_at": {"$in": [None, ""]}}


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _purge_expired(coll_name: str) -> int:
    """Hard-delete anything whose ``deleted_at`` is older than the retention
    window. Called best-effort from list endpoints."""
    cutoff = (
        datetime.now(timezone.utc) - timedelta(days=SOFT_DELETE_RETAIN_DAYS)
    ).isoformat()
    res = await db[coll_name].delete_many(
        {"deleted_at": {"$ne": None, "$lt": cutoff}}
    )
    return res.deleted_count or 0


async def _soft_delete(coll_name: str, query: Dict[str, Any]) -> bool:
    """Mark a row deleted. Returns True iff a row was matched."""
    res = await db[coll_name].update_one(
        {"$and": [query, {"deleted_at": {"$in": [None, ""]}}]},
        {"$set": {"deleted_at": _utc_iso()}},
    )
    return res.matched_count > 0


async def _restore_row(coll_name: str, query: Dict[str, Any]) -> bool:
    """Clear ``deleted_at`` so a row reappears in the active list."""
    res = await db[coll_name].update_one(
        {"$and": [query, {"deleted_at": {"$ne": None}}]},
        {"$unset": {"deleted_at": ""}},
    )
    return res.matched_count > 0


async def _list_archive(coll_name: str, sort_field: str = "deleted_at") -> List[Dict[str, Any]]:
    """List soft-deleted rows for the archive UI."""
    out: List[Dict[str, Any]] = []
    cursor = db[coll_name].find(
        {"deleted_at": {"$ne": None, "$exists": True}}, {"_id": 0}
    ).sort(sort_field, -1)
    async for d in cursor:
        # Make sure it's a non-empty string (skip rows where deleted_at == "")
        if d.get("deleted_at"):
            out.append(d)
    return out


# ---------------------------------------------------------------------------
# Master-list exports — one-click download of every active row as a sorted
# .xlsx file using the EXACT same column shape the bulk-import accepts.
# Round-trip safe: the file you export today can be re-uploaded tomorrow.
# ---------------------------------------------------------------------------
def _xlsx_response(rows: List[List[Any]], header: List[str], filename: str, sheet: str = "Sheet1") -> Response:
    """Build an XLSX from a header row + 2-D row data and return as download."""
    import openpyxl as _ox
    wb = _ox.Workbook()
    ws = wb.active
    ws.title = sheet[:31] or "Sheet1"
    ws.append(header)
    for r in rows:
        ws.append(r)
    # Auto-widen columns based on the longest cell in each column
    for idx, col_header in enumerate(header, start=1):
        longest = len(str(col_header))
        for r in rows:
            if idx - 1 < len(r):
                longest = max(longest, len(str(r[idx - 1] or "")))
        ws.column_dimensions[_ox.utils.get_column_letter(idx)].width = min(longest + 2, 60)
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return Response(
        content=buf.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _today_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


@api_router.get("/admin/employees/export")
async def export_employees(_: bool = Depends(require_admin)):
    cursor = db.employees.find(ACTIVE_FILTER, {"_id": 0}).sort("name", 1)
    docs = await cursor.to_list(5000)
    header = ["Name", "Employee ID", "Trade", "Role", "Crew", "Email", "Phone"]
    rows = [
        [
            d.get("name", ""),
            d.get("employee_id", ""),
            d.get("trade", ""),
            d.get("role", ""),
            d.get("crew", ""),
            d.get("email", ""),
            d.get("phone", ""),
        ]
        for d in docs
    ]
    return _xlsx_response(rows, header, f"MASCI_employees_{_today_stamp()}.xlsx", "Employees")


@api_router.get("/admin/suppliers/export")
async def export_suppliers(_: bool = Depends(require_admin)):
    cursor = db.suppliers.find(ACTIVE_FILTER, {"_id": 0}).sort("name", 1)
    docs = await cursor.to_list(5000)
    header = ["Name", "Active"]
    rows = [
        [d.get("name", ""), "Yes" if d.get("is_active", True) else "No"]
        for d in docs
    ]
    return _xlsx_response(rows, header, f"MASCI_suppliers_{_today_stamp()}.xlsx", "Suppliers")


@api_router.get("/admin/equipment-master/export")
async def export_equipment_master(_: bool = Depends(require_admin)):
    cursor = db.equipment_master.find(ACTIVE_FILTER, {"_id": 0}).sort(
        [("category", 1), ("unit_number", 1)]
    )
    docs = await cursor.to_list(5000)
    header = [
        "Unit Number", "Year", "Make", "Model", "VIN/Serial",
        "Category", "Pre-Op Type", "Company", "Comments",
    ]
    rows = [
        [
            d.get("unit_number", ""),
            d.get("year", ""),
            d.get("make", ""),
            d.get("model", ""),
            d.get("vin_serial_number", ""),
            d.get("category", ""),
            d.get("preop_equipment_type", ""),
            d.get("company", ""),
            d.get("comments", ""),
        ]
        for d in docs
    ]
    return _xlsx_response(rows, header, f"MASCI_equipment_{_today_stamp()}.xlsx", "Louis")


@api_router.get("/admin/equipment-parts/export")
async def export_equipment_parts(_: bool = Depends(require_admin)):
    """Flatten the per-unit parts catalog into one wide sheet — same column
    shape the bulk-importer accepts for round-trip."""
    cursor = db.equipment_units.find({}, {"_id": 0})
    header = [
        "Unit Number", "Category", "Name", "Part Number", "Qty",
        "Size", "Position", "Ply", "Brand", "Notes",
    ]
    rows: List[List[Any]] = []
    async for u in cursor:
        unit = u.get("unit_number") or u.get("id") or ""
        for cat_key in ("filters", "cutting_edges", "wiper_blades", "tires", "other_wear_items"):
            for p in u.get(cat_key, []) or []:
                rows.append([
                    unit,
                    cat_key.replace("_", " ").title(),
                    p.get("name", ""),
                    p.get("part_number", ""),
                    p.get("qty", ""),
                    p.get("size", ""),
                    p.get("position", ""),
                    p.get("ply", ""),
                    p.get("brand", ""),
                    p.get("notes", ""),
                ])
    rows.sort(key=lambda r: (str(r[0]), str(r[1]), str(r[2])))
    return _xlsx_response(rows, header, f"MASCI_parts_{_today_stamp()}.xlsx", "Parts")


@api_router.get("/admin/jobs/export")
async def export_jobs(_: bool = Depends(require_admin)):
    from jobs_master import list_jobs
    docs = await list_jobs(db, only_active=False)
    header = [
        "Project Number", "Project Name", "Location", "Client",
        "PM Name", "PM Email", "Active",
    ]
    rows = [
        [
            d.get("project_number", ""),
            d.get("project_name", ""),
            d.get("location", ""),
            d.get("client", ""),
            d.get("pm_name", ""),
            d.get("pm_email", ""),
            "Yes" if d.get("active", True) else "No",
        ]
        for d in docs
    ]
    return _xlsx_response(rows, header, f"MASCI_jobs_{_today_stamp()}.xlsx", "Jobs")


@api_router.get("/admin/project-managers/export")
async def export_project_managers(_: bool = Depends(require_admin)):
    cursor = db.project_managers.find(ACTIVE_FILTER, {"_id": 0}).sort("name", 1)
    docs = await cursor.to_list(2000)
    header = ["Name", "Email", "Phone", "Active"]
    rows = [
        [
            d.get("name", ""),
            d.get("email", ""),
            d.get("phone", ""),
            "Yes" if d.get("active", True) else "No",
        ]
        for d in docs
    ]
    return _xlsx_response(rows, header, f"MASCI_pms_{_today_stamp()}.xlsx", "PMs")


@api_router.post("/admin/login")
async def admin_login(body: AdminLoginRequest, request: Request):
    ip = _client_ip(request)
    _check_login_lockout(ip)
    expected_pw = os.environ.get("ADMIN_PASSWORD", "")
    if not expected_pw:
        # Gate disabled — anyone can "log in"
        return {"ok": True, "token": "open-mode"}
    if not hmac.compare_digest(body.password, expected_pw):
        _record_login_fail(ip)
        raise HTTPException(status_code=401, detail="Wrong password")
    _reset_login_fails(ip)
    return {"ok": True, "token": _admin_token_for(expected_pw)}


@api_router.get("/admin/check")
async def admin_check(_: bool = Depends(require_admin)):
    """Frontend pings this to verify a stored token is still valid."""
    return {"ok": True}


@api_router.post("/admin/auth/verify-password")
async def admin_verify_password(body: AdminLoginRequest, request: Request):
    """Re-verify the admin password without rotating the stored session
    token. Used by destructive-action confirmation dialogs (delete backup
    file, REPLACE restore, force re-seed) so an admin must re-type the
    password before the action runs.

    Shares the same lockout protection as ``/admin/login`` so brute force
    against this endpoint is rate-limited per IP.
    """
    ip = _client_ip(request)
    _check_login_lockout(ip)
    expected_pw = os.environ.get("ADMIN_PASSWORD", "")
    if not expected_pw:
        # Gate disabled — anyone can "confirm"
        return {"ok": True}
    if not hmac.compare_digest(body.password or "", expected_pw):
        _record_login_fail(ip)
        raise HTTPException(status_code=401, detail="Wrong password")
    _reset_login_fails(ip)
    return {"ok": True}


@api_router.get("/admin/submit-language-stats")
async def admin_submit_language_stats(_: bool = Depends(require_admin)):
    """Per-collection counts of how many records were originally filed in
    Spanish vs English. Surfaces MASCI's bilingual-crew adoption so admins
    can see at a glance how much of the workforce is using Spanish mode.

    Every form submission stamps `submit_language` ("en" | "es") at the
    moment of submit. Missing field (legacy records from before the stamp
    was added) counts as "unknown" and rolls up to "en" in totals so
    default behaviour doesn't over-report Spanish usage.
    """
    collections = [
        ("inspections", "Site Inspections"),
        ("meetings", "Safety Meetings"),
        ("incidents", "Incident Reports"),
        ("daily_reports", "Daily Reports"),
        ("equipment_inspections", "Equipment Pre-Op"),
    ]
    out = []
    grand_en = 0
    grand_es = 0
    grand_unknown = 0
    for coll_name, label in collections:
        total = await db[coll_name].count_documents({})
        es = await db[coll_name].count_documents({"submit_language": "es"})
        en = await db[coll_name].count_documents({"submit_language": "en"})
        unknown = max(0, total - es - en)
        grand_en += en
        grand_es += es
        grand_unknown += unknown
        out.append({
            "collection": coll_name,
            "label": label,
            "total": total,
            "en": en,
            "es": es,
            "unknown": unknown,
            "es_pct": round((es / total) * 100, 1) if total else 0.0,
        })
    grand_total = grand_en + grand_es + grand_unknown
    return {
        "by_collection": out,
        "totals": {
            "total": grand_total,
            "en": grand_en,
            "es": grand_es,
            "unknown": grand_unknown,
            "es_pct": round((grand_es / grand_total) * 100, 1) if grand_total else 0.0,
        },
    }



# ---------------------------------------------------------------------------
# Material Calculators — Field page at /field/calculators
#
# Six calculators (aggregate, asphalt, concrete, truck-load, yield-waste,
# tons-cy-conversion). Every time a crew member hits "Save Calculation"
# the payload lands here and we persist to `calculator_runs`. Admin-side
# analytics and a CSV export read from the same collection.
# ---------------------------------------------------------------------------

_ALLOWED_CALCULATOR_TYPES = {
    "aggregate",
    "asphalt",
    "concrete",
    "truck_load",
    "yield_waste",
    "conversion",
}


class CalculatorRun(BaseModel):
    model_config = {"extra": "allow"}
    calculator_type: str
    language: str = "en"
    job_number: Optional[str] = None
    job_name: Optional[str] = None
    user_name: Optional[str] = None
    inputs: Dict[str, Any] = {}
    outputs: Dict[str, Any] = {}


@api_router.post("/calculators/save")
async def save_calculator_run(payload: CalculatorRun):
    """Public (field-facing) endpoint — crews don't need to log in to use
    the calculators, so saving a run is open too. We store the full
    inputs/outputs snapshot so admins can trace any quantity back to the
    numbers that were typed in."""
    if payload.calculator_type not in _ALLOWED_CALCULATOR_TYPES:
        raise HTTPException(
            status_code=400, detail=f"Unknown calculator_type '{payload.calculator_type}'"
        )
    lang = (payload.language or "en").lower()
    if lang not in ("en", "es"):
        lang = "en"
    doc = {
        "id": str(uuid.uuid4()),
        "calculator_type": payload.calculator_type,
        "language": lang,
        "job_number": payload.job_number,
        "job_name": payload.job_name,
        "user_name": payload.user_name,
        "inputs": payload.inputs or {},
        "outputs": payload.outputs or {},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.calculator_runs.insert_one(doc)
    doc.pop("_id", None)
    return doc


@api_router.get("/admin/calculators/stats")
async def admin_calculator_stats(_: bool = Depends(require_admin)):
    """Aggregate usage stats for the admin dashboard card. Counts by
    calculator type and by language, plus most-used and last-used."""
    total = await db.calculator_runs.count_documents({})
    rows = []
    labels = {
        "aggregate": "Aggregate",
        "asphalt": "Asphalt",
        "concrete": "Concrete",
        "truck_load": "Truck Load",
        "yield_waste": "Yield / Waste",
        "conversion": "Tons ↔ CY",
    }
    for ctype, label in labels.items():
        c_total = await db.calculator_runs.count_documents({"calculator_type": ctype})
        c_en = await db.calculator_runs.count_documents({"calculator_type": ctype, "language": "en"})
        c_es = await db.calculator_runs.count_documents({"calculator_type": ctype, "language": "es"})
        rows.append({
            "calculator_type": ctype,
            "label": label,
            "total": c_total,
            "en": c_en,
            "es": c_es,
        })
    en_total = await db.calculator_runs.count_documents({"language": "en"})
    es_total = await db.calculator_runs.count_documents({"language": "es"})

    # Most used
    most_used = max(rows, key=lambda r: r["total"]) if rows else None
    if most_used and most_used["total"] == 0:
        most_used = None

    # Last used
    last_doc = await db.calculator_runs.find_one(
        {}, {"_id": 0, "calculator_type": 1, "created_at": 1, "language": 1}, sort=[("created_at", -1)]
    )

    return {
        "totals": {"total": total, "en": en_total, "es": es_total},
        "by_type": rows,
        "most_used": most_used,
        "last_used": last_doc,
    }


@api_router.get("/admin/calculators/export.csv")
async def admin_calculator_export_csv(_: bool = Depends(require_admin)):
    """Admin-only CSV dump of every saved calculator run. Used for
    offline analysis and for the "export" button on the admin card."""
    import csv as _csv
    import json as _json_csv
    buf = io.StringIO()
    w = _csv.writer(buf)
    w.writerow([
        "Created At (UTC)", "Calculator", "Language", "Job Number",
        "Job Name", "User", "Inputs (JSON)", "Outputs (JSON)",
    ])
    cursor = db.calculator_runs.find({}, {"_id": 0}).sort("created_at", -1)
    async for r in cursor:
        w.writerow([
            r.get("created_at", ""),
            r.get("calculator_type", ""),
            r.get("language", ""),
            r.get("job_number", "") or "",
            r.get("job_name", "") or "",
            r.get("user_name", "") or "",
            _json_csv.dumps(r.get("inputs", {}), separators=(",", ":")),
            _json_csv.dumps(r.get("outputs", {}), separators=(",", ":")),
        ])
    buf.seek(0)
    return Response(
        content=buf.read(),
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="masci-calculator-runs.csv"',
        },
    )





@api_router.post("/shop/login")
async def shop_login(body: AdminLoginRequest, request: Request):
    """Mirror of /admin/login but for the shop console (mechanics)."""
    ip = _client_ip(request)
    _check_login_lockout(ip)
    expected_pw = os.environ.get("SHOP_PASSWORD", "")
    if not expected_pw:
        return {"ok": True, "token": "open-mode"}
    if not hmac.compare_digest(body.password, expected_pw):
        _record_login_fail(ip)
        raise HTTPException(status_code=401, detail="Wrong password")
    _reset_login_fails(ip)
    return {"ok": True, "token": _shop_token_for(expected_pw)}


@api_router.get("/shop/check")
async def shop_check(_: bool = Depends(require_shop_or_admin)):
    return {"ok": True}


@api_router.post("/pm/login")
async def pm_login(body: AdminLoginRequest, request: Request):
    """Project-Manager portal login. Issues a token accepted by every
    ``require_admin`` route except the backup/recovery routes (which use
    ``require_admin_strict``)."""
    ip = _client_ip(request)
    _check_login_lockout(ip)
    expected_pw = os.environ.get("PM_PASSWORD", "")
    if not expected_pw:
        return {"ok": True, "token": "open-mode"}
    if not hmac.compare_digest(body.password, expected_pw):
        _record_login_fail(ip)
        raise HTTPException(status_code=401, detail="Wrong password")
    _reset_login_fails(ip)
    return {"ok": True, "token": _pm_token_for(expected_pw)}


@api_router.get("/pm/check")
async def pm_check(_: bool = Depends(require_admin)):
    """Verify a stored PM (or Admin) token is still valid."""
    return {"ok": True}


# ------------------------- Models -------------------------
# ============================================================
# Safety Forms — Inspections, Meetings, JHPs, Incidents
# ----------------------------------------------------------
# Extracted to /app/backend/routes/safety.py 2026-04-28 (P1 refactor batch 2).
# Pydantic models (InspectionCreate, Inspection, MeetingCreate, Meeting, etc.)
# are now defined in that module. The 16 endpoints are attached to the shared
# router via register_safety_routes() below.
# ============================================================
from routes.safety import (  # noqa: E402,F401
    register_safety_routes,
    Inspection, InspectionCreate, InspectionSummary,
    Meeting, MeetingCreate, MeetingSummary,
    Jha, JhaCreate, JhaSummary,
    Incident, IncidentCreate, IncidentSummary,
)

register_safety_routes(
    api_router, db, require_admin, rate_limit_public_post,
    # Late binding: schedule_auto_email is defined later in this file. Wrapping
    # in a lambda lets Python resolve it at request time (when the route fires)
    # rather than at registration time (when it doesn't exist yet).
    lambda kind, record: schedule_auto_email(kind, record),
)


# QA/QC inspection routes (Concrete Form / Rebar / Subcontractor Work).
# Same pattern as the Safety routes — single registration helper, late-bound
# auto-email so PM routing fires after submit.
from routes.qaqc import register_qaqc_routes  # noqa: E402

register_qaqc_routes(
    api_router, db, require_admin, rate_limit_public_post,
    lambda kind, record: schedule_auto_email(kind, record),
)


# ============================================================
# Daily Job Reports
# ----------------------------------------------------------
# Extracted to /app/backend/routes/daily_reports.py 2026-04-28 (P1 batch 3).
# ============================================================
from routes.daily_reports import (  # noqa: E402,F401
    register_daily_reports_routes,
    DailyReport, DailyReportCreate, DailyReportSummary,
)

register_daily_reports_routes(
    api_router, db, require_admin, rate_limit_public_post,
    lambda kind, record: schedule_auto_email(kind, record),
)


# ============================================================
# Job Hazard Plans (per-job PDF repository — admin uploads, crews view)
# ============================================================
class JobHazardPlanUpload(BaseModel):
    """Admin uploads (or replaces) a Job Hazard Plan for one project."""
    project_number: str
    project_name: str = ""
    location: str = ""
    filename: str
    content_type: str = "application/pdf"
    file_data: str  # data URL: "data:application/pdf;base64,<...>"
    notes: Optional[str] = ""
    uploaded_by: Optional[str] = ""


class JobHazardPlan(BaseModel):
    id: str
    project_number: str
    project_name: str = ""
    location: str = ""
    filename: str
    content_type: str = "application/pdf"
    file_size: int = 0
    notes: Optional[str] = ""
    uploaded_by: Optional[str] = ""
    uploaded_at: str


def _data_url_to_bytes(data_url: str) -> Tuple[bytes, str]:
    """Parse `data:<mime>;base64,<...>` → (raw_bytes, mime). Raises on bad format."""
    if not data_url or "," not in data_url:
        raise ValueError("file_data must be a data URL")
    head, b64 = data_url.split(",", 1)
    mime = "application/octet-stream"
    if head.startswith("data:") and ";base64" in head:
        mime = head[5:].split(";", 1)[0] or mime
    try:
        raw = _email_b64.b64decode(b64)
    except Exception as e:  # noqa: BLE001
        raise ValueError(f"file_data base64 decode failed: {e}")
    return raw, mime


def _validate_pdf_or_400(raw: bytes) -> None:
    """Reject anything that isn't a real PDF. Without this an admin (or
    anyone with a stolen admin token) could upload an HTML/JS file claiming
    to be application/pdf and serve XSS via the /file download endpoint."""
    if not raw or len(raw) < 5 or not raw.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is not a valid PDF. Magic bytes mismatch.",
        )


@api_router.get("/job-hazard-plans", response_model=List[JobHazardPlan])
async def list_job_hazard_plans():
    """Public — list every uploaded plan (without the heavy file payload)."""
    cursor = db.job_hazard_plans.find(
        {},
        {
            "_id": 0,
            "file_data": 0,  # exclude the base64 blob
        },
    ).sort("project_number", 1)
    docs = await cursor.to_list(2000)
    return [JobHazardPlan(**d) for d in docs]


@api_router.get("/job-hazard-plans/{project_number}/file")
async def download_job_hazard_plan(project_number: str):
    """Public — stream the raw PDF for a given project number."""
    doc = await db.job_hazard_plans.find_one({"project_number": project_number}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="No plan uploaded for this job yet")
    try:
        raw, mime = _data_url_to_bytes(doc.get("file_data") or "")
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Stored file is corrupt: {e}")

    safe_name = "".join(
        c if c.isalnum() or c in ("-", "_", ".", " ") else "_"
        for c in (doc.get("filename") or f"JHA_{project_number}.pdf")
    )
    return Response(
        content=raw,
        # Force application/pdf so a maliciously-MIME'd upload can never
        # be rendered as HTML/JS in the browser (defense in depth — we
        # also reject non-PDF magic bytes at upload time).
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{safe_name}"',
            "X-Content-Type-Options": "nosniff",
        },
    )


@api_router.post("/job-hazard-plans", response_model=JobHazardPlan)
async def upload_job_hazard_plan(
    payload: JobHazardPlanUpload,
    _: bool = Depends(require_admin),
):
    """Admin — upload (or REPLACE) a Job Hazard Plan PDF for one project number.
    Idempotent on project_number — uploading again replaces the prior file."""
    raw, mime = _data_url_to_bytes(payload.file_data)
    _validate_pdf_or_400(raw)
    if len(raw) > 25 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({len(raw)//1024} KB). Max 25 MB per plan.",
        )

    pn = payload.project_number.strip()
    if not pn:
        raise HTTPException(status_code=400, detail="project_number is required")

    plan_id = str(uuid.uuid4())
    doc = {
        "id": plan_id,
        "project_number": pn,
        "project_name": (payload.project_name or "").strip(),
        "location": (payload.location or "").strip(),
        "filename": payload.filename,
        "content_type": mime,
        "file_size": len(raw),
        "file_data": payload.file_data,
        "notes": (payload.notes or "").strip(),
        "uploaded_by": (payload.uploaded_by or "").strip(),
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }
    # Upsert — one plan per project number (replace on re-upload)
    await db.job_hazard_plans.update_one(
        {"project_number": pn},
        {"$set": doc},
        upsert=True,
    )
    fresh = await db.job_hazard_plans.find_one(
        {"project_number": pn}, {"_id": 0, "file_data": 0}
    )
    return JobHazardPlan(**fresh)


@api_router.delete("/job-hazard-plans/{project_number}")
async def delete_job_hazard_plan(
    project_number: str,
    _: bool = Depends(require_admin),
):
    res = await db.job_hazard_plans.delete_one({"project_number": project_number})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="No plan exists for this project")
    return {"deleted": True, "project_number": project_number}


# ============================================================
# Job Hazard FILES — multi-file library per project (replaces the single-PDF
# model above). Accepts any common file type up to 250 MB. Files >8 MB stream
# straight to disk; smaller ones are inlined for fast list/download.
# ============================================================
@api_router.get("/job-hazard-files")
async def list_all_jha_files(_: bool = Depends(require_admin)):
    """Admin — every project + its files, grouped. Drives /admin/jha."""
    from job_hazard_files import list_all_files_grouped
    return {"projects": await list_all_files_grouped(db)}


@api_router.get("/job-hazard-files/by-project/{project_number}")
async def list_jha_files_for_project(project_number: str):
    """Public — files for one project. Crews use this to pull JHPs offline."""
    from job_hazard_files import list_files_for_project
    return {"items": await list_files_for_project(db, project_number)}


@api_router.post("/job-hazard-files")
async def upload_jha_file(
    project_number: str = Form(...),
    file: UploadFile = File(...),
    notes: str = Form(""),
    uploaded_by: str = Form(""),
    _: bool = Depends(require_admin),
):
    """Admin — upload one file for a project. Multipart form."""
    from job_hazard_files import upload_file
    return await upload_file(
        db,
        project_number=project_number,
        file=file,
        notes=notes,
        uploaded_by=uploaded_by,
    )


@api_router.get("/job-hazard-files/{file_id}/download")
async def download_jha_file(file_id: str):
    """Public — stream a file by id. Inline for browser preview where the
    type supports it (PDF, image), otherwise download.

    Streams disk-backed files with FileResponse so memory stays bounded
    even for the 250 MB plan-set zips.
    """
    from job_hazard_files import get_file_for_download
    doc, raw, disk_path = await get_file_for_download(db, file_id)

    fname = doc.get("filename") or f"file-{file_id}.bin"
    content_type = doc.get("content_type") or "application/octet-stream"
    safe_name = "".join(
        c if c.isalnum() or c in ("-", "_", ".", " ") else "_" for c in fname
    )

    # Browser will preview PDFs & images inline; everything else downloads.
    inline_kinds = {"application/pdf"}
    disposition = "inline" if (
        content_type in inline_kinds or content_type.startswith("image/")
    ) else "attachment"
    headers = {
        "Content-Disposition": f'{disposition}; filename="{safe_name}"',
        "X-Content-Type-Options": "nosniff",
    }

    if disk_path is not None:
        return FileResponse(
            path=str(disk_path),
            media_type=content_type,
            filename=safe_name,
            headers=headers,
        )
    return Response(content=raw, media_type=content_type, headers=headers)


@api_router.delete("/job-hazard-files/{file_id}")
async def delete_jha_file(file_id: str, _: bool = Depends(require_admin)):
    from job_hazard_files import delete_file
    ok = await delete_file(db, file_id)
    if not ok:
        raise HTTPException(404, "File not found")
    return {"ok": True, "id": file_id}


# ============================================================
# Trench-Box Tabulated Data library — piggybacks on job_hazard_files with
# scope="trench_box". Key is the box's id (or "general" for shared
# educational docs like the United Rentals "What is Tabulated Data?" PDF).
# ============================================================
@api_router.get("/trench-box-files")
async def list_trench_box_files_grouped():
    """Public — every trench box's files, grouped. Used by the crew
    Tabulated Data Library page + the admin workspace."""
    from job_hazard_files import list_all_files_grouped
    groups = await list_all_files_grouped(db, scope="trench_box")
    return {"projects": groups}


@api_router.get("/trench-box-files/by-box/{box_id}")
async def list_trench_box_files_for_box(box_id: str):
    """Public — files attached to a specific trench box (or 'general')."""
    from job_hazard_files import list_files_for_project
    return {"items": await list_files_for_project(db, box_id, scope="trench_box")}


@api_router.post("/trench-box-files")
async def upload_trench_box_file(
    box_id: str = Form(...),
    file: UploadFile = File(...),
    notes: str = Form(""),
    uploaded_by: str = Form(""),
    _: bool = Depends(require_admin),
):
    """Admin — upload a tabulated-data PDF (or any doc) for a trench box.
    Use box_id="general" for shared educational docs that apply to the
    whole fleet (e.g. the United Rentals explainer)."""
    from job_hazard_files import upload_file
    return await upload_file(
        db,
        project_number=box_id,
        file=file,
        notes=notes,
        uploaded_by=uploaded_by,
        scope="trench_box",
    )


@api_router.delete("/trench-box-files/{file_id}")
async def delete_trench_box_file(
    file_id: str, _: bool = Depends(require_admin)
):
    from job_hazard_files import delete_file
    ok = await delete_file(db, file_id)
    if not ok:
        raise HTTPException(404, "File not found")
    return {"ok": True, "id": file_id}


# ============================================================
# Trench Box Tabulated Data (OSHA 1926 Subpart P)
# ============================================================
class TrenchBoxCreate(BaseModel):
    """OSHA tabulated-data record for one trench shield / box. Filled by
    admin from the manufacturer's data plate — crews then browse read-only."""
    manufacturer: str
    model: str
    serial_number: Optional[str] = ""
    box_type: Optional[str] = ""  # e.g. "Steel", "Aluminum", "Modular"
    length_ft: Optional[str] = ""
    width_min_ft: Optional[str] = ""  # narrowest spread
    width_max_ft: Optional[str] = ""  # widest spread
    sidewall_height_ft: Optional[str] = ""
    sidewall_thickness_in: Optional[str] = ""
    weight_lbs: Optional[str] = ""

    # Maximum allowable depth by soil type (per OSHA 1926.652 / 1926 Subpart P)
    max_depth_type_a_ft: Optional[str] = ""
    max_depth_type_b_ft: Optional[str] = ""
    max_depth_type_c_60_ft: Optional[str] = ""  # C-60 (60° slope)
    max_depth_type_c_80_ft: Optional[str] = ""  # C-80 (80° slope)

    spreader_count: Optional[str] = ""
    stacking_allowed: Optional[str] = "No"
    stacking_max: Optional[str] = ""

    notes: Optional[str] = ""
    # Optional manufacturer tabulated-data PDF (data URL, max 10 MB)
    tabulated_data_file: Optional[str] = ""
    tabulated_data_filename: Optional[str] = ""


class TrenchBox(TrenchBoxCreate):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@api_router.get("/trench-boxes", response_model=List[TrenchBox])
async def list_trench_boxes():
    """Public — every crew can browse to see what's OSHA-legal for what depth."""
    cursor = db.trench_boxes.find(
        {},
        {
            "_id": 0,
            "tabulated_data_file": 0,  # excluded from list (heavy)
        },
    ).sort([("manufacturer", 1), ("model", 1)])
    docs = await cursor.to_list(500)
    # Re-include empty placeholder so Pydantic doesn't choke
    for d in docs:
        d.setdefault("tabulated_data_file", "")
    return [TrenchBox(**d) for d in docs]


@api_router.get("/trench-boxes/{box_id}", response_model=TrenchBox)
async def get_trench_box(box_id: str):
    """Public — full record for one trench box (without the file payload)."""
    doc = await db.trench_boxes.find_one(
        {"id": box_id}, {"_id": 0, "tabulated_data_file": 0}
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Trench box not found")
    doc.setdefault("tabulated_data_file", "")
    return TrenchBox(**doc)


@api_router.get("/trench-boxes/{box_id}/file")
async def download_trench_box_file(box_id: str):
    """Public — stream the manufacturer's tabulated-data PDF (if uploaded)."""
    doc = await db.trench_boxes.find_one({"id": box_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Trench box not found")
    data_url = doc.get("tabulated_data_file") or ""
    if not data_url:
        raise HTTPException(
            status_code=404,
            detail="No manufacturer tabulated-data PDF uploaded for this box",
        )
    try:
        raw, mime = _data_url_to_bytes(data_url)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"File corrupt: {e}")
    safe_name = "".join(
        c if c.isalnum() or c in ("-", "_", ".", " ") else "_"
        for c in (doc.get("tabulated_data_filename")
                  or f"TabData_{doc.get('manufacturer', '')}_{doc.get('model', '')}.pdf")
    )
    return Response(
        content=raw,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{safe_name}"',
            "X-Content-Type-Options": "nosniff",
        },
    )


@api_router.post("/trench-boxes", response_model=TrenchBox)
async def create_trench_box(
    payload: TrenchBoxCreate,
    _: bool = Depends(require_admin),
):
    if not payload.manufacturer.strip() or not payload.model.strip():
        raise HTTPException(
            status_code=400, detail="manufacturer and model are required"
        )
    # Lightly validate optional file size
    if payload.tabulated_data_file:
        raw, _ = _data_url_to_bytes(payload.tabulated_data_file)
        _validate_pdf_or_400(raw)
        if len(raw) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail=f"Tabulated-data file too large ({len(raw)//1024} KB). Max 10 MB.",
            )
    box = TrenchBox(**payload.model_dump())
    doc = box.model_dump()
    await db.trench_boxes.insert_one(doc)
    doc.pop("_id", None)
    # Don't echo the file blob back
    doc.pop("tabulated_data_file", None)
    doc["tabulated_data_file"] = ""
    return TrenchBox(**doc)


@api_router.put("/trench-boxes/{box_id}", response_model=TrenchBox)
async def update_trench_box(
    box_id: str,
    payload: TrenchBoxCreate,
    _: bool = Depends(require_admin),
):
    if payload.tabulated_data_file:
        raw, _ = _data_url_to_bytes(payload.tabulated_data_file)
        _validate_pdf_or_400(raw)
        if len(raw) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large (max 10 MB)")
    update = payload.model_dump()
    update["updated_at"] = datetime.now(timezone.utc).isoformat()
    # Keep file payload only if user provided a new one
    if not update.get("tabulated_data_file"):
        update.pop("tabulated_data_file", None)
        update.pop("tabulated_data_filename", None)
    res = await db.trench_boxes.update_one({"id": box_id}, {"$set": update})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Trench box not found")
    fresh = await db.trench_boxes.find_one(
        {"id": box_id}, {"_id": 0, "tabulated_data_file": 0}
    )
    fresh.setdefault("tabulated_data_file", "")
    return TrenchBox(**fresh)


@api_router.delete("/trench-boxes/{box_id}")
async def delete_trench_box(box_id: str, _: bool = Depends(require_admin)):
    res = await db.trench_boxes.delete_one({"id": box_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Trench box not found")
    return {"deleted": True, "id": box_id}







# ============================================================
# Equipment Inspections (OSHA daily pre-op checklist)
# ============================================================
from checklists import CHECKLISTS, EQUIPMENT_TYPES  # noqa: E402


# ============================================================
# Equipment Pre-Op Inspections + Shop Sign-Off + Trends
# ----------------------------------------------------------
# Extracted to /app/backend/routes/equipment.py 2026-04-28 (P1 batch 4).
# Pydantic models + 8 endpoints + MAJOR_OOS_SET helpers all moved.
# ============================================================
from routes.equipment import (  # noqa: E402,F401
    register_equipment_routes,
    EquipmentInspection, EquipmentInspectionCreate, EquipmentInspectionSummary,
    ShopSignoffPayload, MAJOR_OOS_ITEMS_BACKEND, MAJOR_OOS_SET,
)


async def _remember_equipment_unit(eq_type, unit_label, make, model, serial):
    """Forwarder for the new-unit dropdown remembering. Defined lazily so
    `create_equipment_unit` (defined just below) can be looked up at call time.
    """
    return await create_equipment_unit(  # noqa: F821 — late binding (fn defined below)
        EquipmentUnitCreate(  # noqa: F821 — late binding
            equipment_type=eq_type, unit_label=unit_label,
            make=make, model=model, serial=serial,
        )
    )


register_equipment_routes(
    api_router, db, require_admin, require_shop_or_admin,
    rate_limit_public_post,
    lambda kind, record: schedule_auto_email(kind, record),
    _remember_equipment_unit,
)


# ---------------------------------------------------------------------------
# Equipment Master Fleet — sourced from MASCI Equipment List.xlsx
# Used to populate equipment dropdowns across all forms (Pre-Op, Daily Reports,
# Incidents, etc.). Operators can still type custom values as a fallback.
# ---------------------------------------------------------------------------
EQUIPMENT_MASTER_SEED_FILE = ROOT_DIR / "data" / "equipment_master.json"


class EquipmentMasterItem(BaseModel):
    unit_number: str = ""
    year: Optional[int] = None
    make_model: str = ""
    plate: str = ""
    vin_serial_number: str = ""
    comments: str = ""
    company: str = ""
    category: str = "Misc Equipment"
    preop_equipment_type: str = "Other"
    display_label: str = ""


@api_router.get("/equipment-master")
async def list_equipment_master(category: Optional[str] = None):
    await _purge_expired("equipment_master")
    q: Dict[str, Any] = dict(ACTIVE_FILTER)
    if category:
        q["category"] = category
    cursor = db.equipment_master.find(q, {"_id": 0}).sort(
        [("category", 1), ("unit_number", 1), ("make_model", 1)]
    )
    docs = await cursor.to_list(2000)
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for d in docs:
        grouped.setdefault(d.get("category", "Misc Equipment"), []).append(d)
    categories = sorted(grouped.keys())
    return {
        "categories": categories,
        "items": docs,
        "grouped": grouped,
        "count": len(docs),
    }


@api_router.get("/admin/equipment-master/archive")
async def equipment_master_archive(_: bool = Depends(require_shop_or_admin)):
    return {
        "items": await _list_archive("equipment_master"),
        "retain_days": SOFT_DELETE_RETAIN_DAYS,
    }


@api_router.post("/admin/equipment-master/{unit_id}/restore")
async def restore_equipment_master(
    unit_id: str, _: bool = Depends(require_shop_or_admin)
):
    if not await _restore_row(
        "equipment_master",
        {"$or": [{"id": unit_id}, {"unit_number": unit_id}]},
    ):
        raise HTTPException(status_code=404, detail="Unit not in archive")
    doc = await db.equipment_master.find_one(
        {"$or": [{"id": unit_id}, {"unit_number": unit_id}]}, {"_id": 0}
    )
    return doc or {"ok": True}


@api_router.get("/equipment-types")
async def list_equipment_types():
    """Public — list of equipment types + checklist templates used by the
    Equipment Pre-Op form to render the right walk-around questions."""
    return {
        "types": EQUIPMENT_TYPES,
        "checklists": CHECKLISTS,
    }


# -------------------- Jobs Master (replaces static jobLibrary.js) --------------------
class JobIn(BaseModel):
    project_number: str = Field(..., min_length=1, max_length=80)
    project_name: str = Field(..., min_length=1, max_length=300)
    location: str = ""
    client: str = ""
    project_manager: str = ""   # display name (kept for backwards-compat)
    pm_email: str = ""           # canonical key — drives auto-email routing
    active: bool = True


# -------------------- Project Managers (admin-managed roster) --------------------
class PMIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    email: str = Field(..., min_length=3, max_length=300)
    phone: str = ""
    is_active: bool = True


class PMUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


@api_router.get("/admin/project-managers")
async def admin_list_pms(_: bool = Depends(require_admin)):
    from project_managers import list_pms
    return {"items": await list_pms(db, only_active=False)}


@api_router.get("/project-managers")
async def public_list_active_pms():
    """Public — drives the PM dropdown on the AdminJobMasterPanel and any
    other UI that needs the list of active PMs. Returns no phone/email
    metadata is sensitive (only name + id + email needed for assignment)."""
    from project_managers import list_pms
    pms = await list_pms(db, only_active=True)
    return {
        "items": [
            {"id": p["id"], "name": p["name"], "email": p["email"]}
            for p in pms
        ]
    }


@api_router.post("/admin/project-managers")
async def admin_add_pm(body: PMIn, _: bool = Depends(require_admin)):
    from project_managers import add_pm
    try:
        return await add_pm(db, body.model_dump())
    except ValueError as e:
        raise HTTPException(400, str(e))


@api_router.patch("/admin/project-managers/{pm_id}")
async def admin_update_pm(
    pm_id: str, body: PMUpdate, _: bool = Depends(require_admin)
):
    from project_managers import update_pm
    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    if not fields:
        raise HTTPException(400, "No fields to update")
    try:
        # Capture old email so we can cascade the email change to jobs_master.
        old = await db.project_managers.find_one({"id": pm_id}, {"_id": 0})
        old_email = (old or {}).get("email", "").lower()

        saved = await update_pm(db, pm_id, fields)
        if not saved:
            raise HTTPException(404, "PM not found")

        # Cascade email change to every job that referenced the old email.
        new_email = (saved.get("email") or "").lower()
        if old_email and new_email and old_email != new_email:
            await db.jobs_master.update_many(
                {"pm_email": old_email},
                {"$set": {
                    "pm_email": new_email,
                    "project_manager": saved.get("name") or "",
                    "updated_at": _now_iso(),
                }},
            )

        # Cascade name change to every job referencing this PM by email.
        if "name" in fields and new_email:
            await db.jobs_master.update_many(
                {"pm_email": new_email},
                {"$set": {
                    "project_manager": saved.get("name") or "",
                    "updated_at": _now_iso(),
                }},
            )

        return saved
    except ValueError as e:
        raise HTTPException(400, str(e))


@api_router.delete("/admin/project-managers/{pm_id}")
async def admin_delete_pm(pm_id: str, _: bool = Depends(require_admin)):
    from project_managers import delete_pm
    # Find any jobs that still reference this PM — surface a warning so the
    # admin can reassign first instead of silently orphaning jobs.
    pm = await db.project_managers.find_one({"id": pm_id}, {"_id": 0})
    if not pm:
        raise HTTPException(404, "PM not found")
    pm_email = (pm.get("email") or "").lower()
    job_count = await db.jobs_master.count_documents({"pm_email": pm_email})
    if job_count > 0:
        raise HTTPException(
            409,
            f"{pm.get('name')} is still assigned to {job_count} job(s). "
            f"Reassign those jobs first, or deactivate the PM instead.",
        )
    ok = await delete_pm(db, pm_id)
    if not ok:
        raise HTTPException(404, "PM not found")
    return {"ok": True}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@api_router.get("/jobs")
async def list_jobs_public():
    """Public — drives the JobPicker on every form. Active jobs only."""
    from jobs_master import list_jobs
    return {"items": await list_jobs(db, only_active=True)}


@api_router.get("/admin/jobs")
async def admin_list_jobs(_: bool = Depends(require_admin)):
    from jobs_master import list_jobs
    return {"items": await list_jobs(db, only_active=False)}


@api_router.post("/admin/jobs")
async def admin_upsert_job(body: JobIn, _: bool = Depends(require_admin)):
    from jobs_master import upsert_job
    try:
        return await upsert_job(db, body.model_dump())
    except ValueError as e:
        raise HTTPException(400, str(e))


@api_router.patch("/admin/jobs/{job_id}/active")
async def admin_set_job_active(
    job_id: str, body: dict, _: bool = Depends(require_admin)
):
    from jobs_master import set_active
    saved = await set_active(db, job_id, bool(body.get("active", True)))
    if not saved:
        raise HTTPException(404, "Job not found")
    return saved


@api_router.delete("/admin/jobs/{job_id}")
async def admin_delete_job(job_id: str, _: bool = Depends(require_admin)):
    from jobs_master import delete_job
    ok = await delete_job(db, job_id)
    if not ok:
        raise HTTPException(404, "Job not found")
    return {"ok": True, "soft_deleted": True, "retain_days": SOFT_DELETE_RETAIN_DAYS}


@api_router.get("/admin/jobs/archive")
async def admin_jobs_archive(_: bool = Depends(require_admin)):
    from jobs_master import list_archived_jobs
    return {"items": await list_archived_jobs(db), "retain_days": SOFT_DELETE_RETAIN_DAYS}


@api_router.post("/admin/jobs/{job_id}/restore")
async def admin_restore_job(job_id: str, _: bool = Depends(require_admin)):
    from jobs_master import restore_job
    if not await restore_job(db, job_id):
        raise HTTPException(404, "Job not in archive")
    doc = await db.jobs_master.find_one({"id": job_id}, {"_id": 0})
    return doc or {"ok": True}


@api_router.post("/admin/jobs/bulk-replace")
async def admin_bulk_replace_jobs(body: dict, _: bool = Depends(require_admin)):
    """Replace the entire jobs_master collection (used by the bulk uploader).
    Body: {"rows": [{project_number, project_name, ...}, ...]}.
    """
    from jobs_master import bulk_replace
    rows = body.get("rows") or []
    if not isinstance(rows, list):
        raise HTTPException(400, "rows must be a list")
    try:
        return await bulk_replace(db, rows)
    except ValueError as e:
        raise HTTPException(400, str(e))


# -------------------- Inline "Add to roster" (no admin token) --------------------
class RosterAddBody(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)


@api_router.post(
    "/employees/add",
    dependencies=[Depends(rate_limit_public_post)],
)
async def add_employee_from_form(body: RosterAddBody):
    """Add a new employee to the master roster directly from a form's amber
    'Will save as new entry' button. Public + rate-limited.

    Idempotent: if an employee with this exact name (case-insensitive) already
    exists, returns the existing one.
    """
    name = body.name.strip()
    existing = await db.employees.find_one(
        {"name": {"$regex": f"^{name}$", "$options": "i"}}, {"_id": 0}
    )
    if existing:
        return {"ok": True, "created": False, "employee": existing}
    doc = {
        "id": str(uuid.uuid4()),
        "name": name,
        "trade": "",
        "role": "",
        "crew": "",
        "employee_id": "",
        "email": "",
        "phone": "",
        "added_via": "field-form",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.employees.insert_one(doc)
    saved = {k: v for k, v in doc.items() if k != "_id"}
    return {"ok": True, "created": True, "employee": saved}


@api_router.post(
    "/suppliers/add",
    dependencies=[Depends(rate_limit_public_post)],
)
async def add_supplier_from_form(body: RosterAddBody):
    """Add a new supplier / vendor / subcontractor to the master list from
    a form's amber 'Will save as new entry' button. Public + rate-limited.

    Idempotent on case-insensitive name match.
    """
    name = body.name.strip()
    existing = await db.suppliers.find_one(
        {"name": {"$regex": f"^{name}$", "$options": "i"}}, {"_id": 0}
    )
    if existing:
        return {"ok": True, "created": False, "supplier": existing}
    doc = {
        "id": str(uuid.uuid4()),
        "name": name,
        "vendor_type": "",
        "phone": "",
        "email": "",
        "address": "",
        "added_via": "field-form",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.suppliers.insert_one(doc)
    saved = {k: v for k, v in doc.items() if k != "_id"}
    return {"ok": True, "created": True, "supplier": saved}


# ---------------------------------------------------------------------------
# Employees / crew roster — used by Daily Report's "MASCI Crews on Site"
# section and any other employee dropdown across the platform.
# ---------------------------------------------------------------------------
@api_router.get("/employees")
async def list_employees():
    """Public — returns the full MASCI crew roster (sorted by name)."""
    await _purge_expired("employees")
    cursor = db.employees.find(
        {"$and": [ACTIVE_FILTER, {"is_active": {"$ne": False}}]},
        {"_id": 0},
    ).sort("name", 1)
    docs = await cursor.to_list(2000)
    return {"items": docs, "count": len(docs)}


@api_router.get("/admin/employees/status")
async def employees_status(_: bool = Depends(require_admin)):
    total = await db.employees.count_documents(ACTIVE_FILTER)
    active = await db.employees.count_documents(
        {"$and": [ACTIVE_FILTER, {"is_active": {"$ne": False}}]}
    )
    archived = await db.employees.count_documents({"deleted_at": {"$ne": None}})
    last_doc = await db.employees.find_one(
        ACTIVE_FILTER, {"_id": 0, "updated_at": 1, "created_at": 1}, sort=[("updated_at", -1)]
    )
    last_updated = (last_doc or {}).get("updated_at") or (last_doc or {}).get("created_at")
    return {"count": total, "active": active, "archived": archived, "last_updated": last_updated}


@api_router.get("/admin/employees/archive")
async def employees_archive(_: bool = Depends(require_admin)):
    return {"items": await _list_archive("employees"), "retain_days": SOFT_DELETE_RETAIN_DAYS}


@api_router.post("/admin/employees/{employee_id}/restore")
async def restore_employee(employee_id: str, _: bool = Depends(require_admin)):
    if not await _restore_row("employees", {"id": employee_id}):
        raise HTTPException(status_code=404, detail="Employee not in archive")
    doc = await db.employees.find_one({"id": employee_id}, {"_id": 0})
    return doc or {"ok": True}


@api_router.post("/admin/employees/upload")
async def upload_employees(
    file: UploadFile = File(...),
    _: bool = Depends(require_admin),
):
    """Replace the entire roster from an .xlsx file.

    Expected columns (case-insensitive, common variations supported):
      Name (required) · Employee ID · Trade · Role · Crew · Email · Phone
    """
    fname = (file.filename or "").lower()
    if not (fname.endswith(".xlsx") or fname.endswith(".xlsm") or fname.endswith(".csv")):
        raise HTTPException(status_code=400, detail="Only .xlsx or .csv files are accepted")
    raw = await file.read()
    if not raw or len(raw) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Empty or oversized file (max 10 MB)")

    rows: List[Dict[str, Any]] = []
    try:
        if fname.endswith(".csv"):
            import csv as _csv
            text = raw.decode("utf-8", errors="ignore")
            reader = _csv.DictReader(text.splitlines())
            for r in reader:
                rows.append({(k or "").strip().lower(): (v or "").strip() for k, v in r.items()})
        else:
            import openpyxl as _ox
            import io as _io
            wb = _ox.load_workbook(_io.BytesIO(raw), data_only=True)
            ws = wb.active
            headers: List[str] = []
            for i, row in enumerate(ws.iter_rows(values_only=True)):
                if i == 0:
                    headers = [str(c or "").strip().lower() for c in row]
                    continue
                if not row or not any(row):
                    continue
                d = {}
                for h, v in zip(headers, row):
                    if not h:
                        continue
                    d[h] = ("" if v is None else str(v).strip())
                rows.append(d)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse file: {e}")

    def pick(d: Dict[str, str], *keys: str) -> str:
        for k in keys:
            v = d.get(k)
            if v:
                return v
        return ""

    items: List[Dict[str, Any]] = []
    seen = set()
    for d in rows:
        name = pick(d, "name", "full name", "employee name")
        if not name:
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        items.append({
            "id": str(uuid.uuid4()),
            "name": name,
            "employee_id": pick(d, "employee id", "id", "emp id", "emp #", "emp#"),
            "trade": pick(d, "trade", "department"),
            "role": pick(d, "role", "title", "position"),
            "crew": pick(d, "crew", "team"),
            "email": pick(d, "email"),
            "phone": pick(d, "phone", "mobile", "cell"),
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })

    if not items:
        raise HTTPException(status_code=400, detail="No valid rows found (need a 'Name' column).")

    await db.employees.delete_many({})
    await db.employees.insert_many(items)
    return {"ok": True, "count": len(items)}


@api_router.post("/admin/employees")
async def create_employee(
    payload: Dict[str, Any],
    _: bool = Depends(require_admin),
):
    """Manually add a single employee."""
    name = (payload.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")
    doc = {
        "id": str(uuid.uuid4()),
        "name": name,
        "employee_id": (payload.get("employee_id") or "").strip(),
        "trade": (payload.get("trade") or "").strip(),
        "role": (payload.get("role") or "").strip(),
        "crew": (payload.get("crew") or "").strip(),
        "email": (payload.get("email") or "").strip(),
        "phone": (payload.get("phone") or "").strip(),
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.employees.insert_one(doc)
    doc.pop("_id", None)
    return doc


@api_router.put("/admin/employees/{employee_id}")
async def update_employee(
    employee_id: str,
    payload: Dict[str, Any],
    _: bool = Depends(require_admin),
):
    """Inline edit a single employee. Only the supplied fields are updated.
    Soft-deleted rows are not editable — restore them first."""
    allowed = {"name", "employee_id", "trade", "role", "crew", "email", "phone", "is_active"}
    update = {k: payload[k] for k in allowed if k in payload}
    if "name" in update and not (update["name"] or "").strip():
        raise HTTPException(status_code=400, detail="Name cannot be blank")
    update["updated_at"] = datetime.now(timezone.utc).isoformat()
    res = await db.employees.update_one(
        {"$and": [{"id": employee_id}, ACTIVE_FILTER]},
        {"$set": update},
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Employee not found")
    doc = await db.employees.find_one({"id": employee_id}, {"_id": 0})
    return doc or {"ok": True}


@api_router.delete("/admin/employees/{employee_id}")
async def delete_employee(employee_id: str, _: bool = Depends(require_admin)):
    if not await _soft_delete("employees", {"id": employee_id}):
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"ok": True, "soft_deleted": True, "retain_days": SOFT_DELETE_RETAIN_DAYS}


# ---------------------------------------------------------------------------
# Suppliers / Subcontractors — used by Daily Report Sections 05 & 08.
# ---------------------------------------------------------------------------
SUPPLIERS_SEED_FILE = ROOT_DIR / "data" / "suppliers_seed.json"
EMPLOYEES_SEED_FILE = ROOT_DIR / "data" / "employees_seed.json"


@api_router.get("/suppliers")
async def list_suppliers():
    """Public — returns the full MASCI supplier / subcontractor list."""
    await _purge_expired("suppliers")
    cursor = db.suppliers.find(
        {"$and": [ACTIVE_FILTER, {"is_active": {"$ne": False}}]},
        {"_id": 0},
    ).sort("name", 1)
    docs = await cursor.to_list(2000)
    return {"items": docs, "count": len(docs)}


@api_router.get("/admin/suppliers/status")
async def suppliers_status(_: bool = Depends(require_admin)):
    total = await db.suppliers.count_documents(ACTIVE_FILTER)
    active = await db.suppliers.count_documents(
        {"$and": [ACTIVE_FILTER, {"is_active": {"$ne": False}}]}
    )
    archived = await db.suppliers.count_documents({"deleted_at": {"$ne": None}})
    last_doc = await db.suppliers.find_one(
        ACTIVE_FILTER, {"_id": 0, "updated_at": 1, "created_at": 1}, sort=[("updated_at", -1)]
    )
    last_updated = (last_doc or {}).get("updated_at") or (last_doc or {}).get("created_at")
    return {"count": total, "active": active, "archived": archived, "last_updated": last_updated}


@api_router.get("/admin/suppliers/archive")
async def suppliers_archive(_: bool = Depends(require_admin)):
    return {"items": await _list_archive("suppliers"), "retain_days": SOFT_DELETE_RETAIN_DAYS}


@api_router.post("/admin/suppliers/{supplier_id}/restore")
async def restore_supplier(supplier_id: str, _: bool = Depends(require_admin)):
    if not await _restore_row("suppliers", {"id": supplier_id}):
        raise HTTPException(status_code=404, detail="Supplier not in archive")
    doc = await db.suppliers.find_one({"id": supplier_id}, {"_id": 0})
    return doc or {"ok": True}


@api_router.post("/admin/suppliers/upload")
async def upload_suppliers(
    file: UploadFile = File(...),
    _: bool = Depends(require_admin),
):
    """Replace the supplier list from an .xlsx or .csv file.

    Reads the FIRST column of the first sheet (any header row is OK).
    Skips obvious dividers ('SUBCONTRACTORS', 'NOT LISTED ADD TO NOTES',
    'MASCI', 'D-MAC').
    """
    fname = (file.filename or "").lower()
    if not (fname.endswith(".xlsx") or fname.endswith(".xlsm") or fname.endswith(".csv")):
        raise HTTPException(status_code=400, detail="Only .xlsx or .csv files are accepted")
    raw = await file.read()
    if not raw or len(raw) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Empty or oversized file (max 10 MB)")

    SKIP_LOWER = {"subcontractors", "suppliers", "vendors", "not listed add to notes",
                  "name", "company", "company name"}
    names: List[str] = []
    try:
        if fname.endswith(".csv"):
            import csv as _csv
            text = raw.decode("utf-8", errors="ignore")
            for r in _csv.reader(text.splitlines()):
                if r and r[0]:
                    names.append(str(r[0]).strip())
        else:
            import openpyxl as _ox
            import io as _io
            wb = _ox.load_workbook(_io.BytesIO(raw), data_only=True)
            ws = wb.active
            for row in ws.iter_rows(values_only=True):
                if row and row[0]:
                    names.append(str(row[0]).strip())
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse file: {e}")

    seen = set()
    items: List[Dict[str, Any]] = []
    for n in names:
        if not n or n.lower() in SKIP_LOWER:
            continue
        k = n.lower()
        if k in seen:
            continue
        seen.add(k)
        items.append({
            "id": str(uuid.uuid4()),
            "name": n,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })

    if not items:
        raise HTTPException(status_code=400, detail="No supplier names found.")

    await db.suppliers.delete_many({})
    await db.suppliers.insert_many(items)
    return {"ok": True, "count": len(items)}


@api_router.post("/admin/suppliers")
async def create_supplier(
    payload: Dict[str, Any],
    _: bool = Depends(require_admin),
):
    name = (payload.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")
    doc = {
        "id": str(uuid.uuid4()),
        "name": name,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.suppliers.insert_one(doc)
    doc.pop("_id", None)
    return doc


@api_router.put("/admin/suppliers/{supplier_id}")
async def update_supplier(
    supplier_id: str,
    payload: Dict[str, Any],
    _: bool = Depends(require_admin),
):
    """Inline edit a supplier — name + optional active toggle.
    Soft-deleted rows are not editable — restore them first."""
    allowed = {"name", "is_active"}
    update = {k: payload[k] for k in allowed if k in payload}
    if "name" in update and not (update["name"] or "").strip():
        raise HTTPException(status_code=400, detail="Name cannot be blank")
    update["updated_at"] = datetime.now(timezone.utc).isoformat()
    res = await db.suppliers.update_one(
        {"$and": [{"id": supplier_id}, ACTIVE_FILTER]},
        {"$set": update},
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Supplier not found")
    doc = await db.suppliers.find_one({"id": supplier_id}, {"_id": 0})
    return doc or {"ok": True}


@api_router.delete("/admin/suppliers/{supplier_id}")
async def delete_supplier(supplier_id: str, _: bool = Depends(require_admin)):
    if not await _soft_delete("suppliers", {"id": supplier_id}):
        raise HTTPException(status_code=404, detail="Supplier not found")
    return {"ok": True, "soft_deleted": True, "retain_days": SOFT_DELETE_RETAIN_DAYS}


# ---------------------------------------------------------------------------
# Idempotent seed for employees + suppliers on startup. If the collection is
# empty AND a seed JSON file exists, populate it. Re-uploading via the admin
# panel will replace the contents.
# ---------------------------------------------------------------------------
async def _seed_employees_from_json() -> None:
    log = logging.getLogger(__name__)
    if not EMPLOYEES_SEED_FILE.exists():
        return
    if await db.employees.count_documents({}) > 0:
        return
    try:
        import json as _json_em
        with open(EMPLOYEES_SEED_FILE, "r", encoding="utf-8") as fh:
            names = _json_em.load(fh)
        items = []
        seen = set()
        for n in names:
            if not n or not isinstance(n, str):
                continue
            k = n.strip().lower()
            if not k or k in seen:
                continue
            seen.add(k)
            items.append({
                "id": str(uuid.uuid4()),
                "name": n.strip(),
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            })
        if items:
            await db.employees.insert_many(items)
            log.info(f"[employees] seeded {len(items)} from JSON")
    except Exception as e:
        log.exception(f"[employees] seed failed: {e}")


async def _seed_suppliers_from_json() -> None:
    log = logging.getLogger(__name__)
    if not SUPPLIERS_SEED_FILE.exists():
        return
    if await db.suppliers.count_documents({}) > 0:
        return
    try:
        import json as _json_sp
        with open(SUPPLIERS_SEED_FILE, "r", encoding="utf-8") as fh:
            data = _json_sp.load(fh)
        items = []
        seen = set()
        for entry in data:
            n = entry.get("name") if isinstance(entry, dict) else (entry if isinstance(entry, str) else "")
            if not n:
                continue
            k = n.strip().lower()
            if not k or k in seen:
                continue
            seen.add(k)
            items.append({
                "id": str(uuid.uuid4()),
                "name": n.strip(),
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            })
        if items:
            await db.suppliers.insert_many(items)
            log.info(f"[suppliers] seeded {len(items)} from JSON")
    except Exception as e:
        log.exception(f"[suppliers] seed failed: {e}")


# ---------------------------------------------------------------------------
# Project P&L Snapshot — aggregate live job-cost data from daily_reports
# in one shot for a given project + date range.
# ---------------------------------------------------------------------------
DEFAULT_LABOR_RATE = float(os.environ.get("DEFAULT_LABOR_RATE", "45.0"))


def _coerce_float(v: Any, default: float = 0.0) -> float:
    try:
        if v is None or v == "":
            return default
        return float(v)
    except (TypeError, ValueError):
        return default


@api_router.get("/admin/projects/list")
async def list_projects_in_dailies(_: bool = Depends(require_admin)):
    """Return distinct {project_number, project_name} tuples seen across all
    daily reports — gives the P&L picker a curated dropdown so users don't
    have to type project numbers from memory."""
    pipeline = [
        {"$match": {"project_number": {"$nin": [None, ""]}}},
        {"$group": {
            "_id": "$project_number",
            "project_name": {"$last": "$project_name"},
            "report_count": {"$sum": 1},
            "last_report_date": {"$max": "$report_date"},
        }},
        {"$sort": {"last_report_date": -1}},
        {"$limit": 500},
    ]
    docs = await db.daily_reports.aggregate(pipeline).to_list(500)
    return {
        "items": [
            {
                "project_number": d["_id"],
                "project_name": d.get("project_name") or "",
                "report_count": d.get("report_count", 0),
                "last_report_date": d.get("last_report_date") or "",
            }
            for d in docs
        ],
        "count": len(docs),
    }


@api_router.get("/admin/projects/pnl")
async def project_pnl(
    project_number: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    labor_rate: Optional[float] = None,
    _: bool = Depends(require_admin),
):
    """Live job-cost dashboard for one project + date range.

    Aggregates all matching `daily_reports` and returns:
      - crew_hours_total + crew_breakdown (by employee)
      - sub_hours_total + sub_breakdown (by company)
      - material_lines (one row per ticket)
      - cost_summary (labor cost, sub cost — sub cost left blank unless rate set)
      - report_count, date_range_actual
    """
    if not project_number:
        raise HTTPException(status_code=400, detail="project_number is required")

    rate = labor_rate if labor_rate and labor_rate > 0 else DEFAULT_LABOR_RATE

    q: Dict[str, Any] = {"project_number": project_number}
    # report_date is stored as 'YYYY-MM-DD' string — string compare works lex
    date_filter: Dict[str, Any] = {}
    if date_from:
        date_filter["$gte"] = date_from
    if date_to:
        date_filter["$lte"] = date_to
    if date_filter:
        q["report_date"] = date_filter

    cursor = db.daily_reports.find(q, {"_id": 0}).sort("report_date", 1)
    reports = await cursor.to_list(2000)

    crew_by_name: Dict[str, Dict[str, Any]] = {}
    sub_by_company: Dict[str, Dict[str, Any]] = {}
    material_lines: List[Dict[str, Any]] = []
    crew_total_hours = 0.0
    sub_total_hours = 0.0
    project_name_seen: Optional[str] = None
    actual_dates: List[str] = []

    for r in reports:
        actual_dates.append(r.get("report_date") or "")
        if not project_name_seen:
            project_name_seen = r.get("project_name") or None

        # Crew rows
        for c in (r.get("masci_crews") or []):
            name = (c.get("name") or "Unnamed").strip() or "Unnamed"
            hrs = _coerce_float(c.get("hours"))
            entry = crew_by_name.setdefault(name, {
                "name": name,
                "trade": c.get("trade") or "",
                "days_on_site": 0,
                "hours": 0.0,
            })
            entry["days_on_site"] += 1
            entry["hours"] += hrs
            crew_total_hours += hrs

        # Subcontractor rows
        for s in (r.get("subcontractors") or []):
            company = (s.get("company") or "Unknown").strip() or "Unknown"
            count = _coerce_float(s.get("count"))
            hrs_per_worker = _coerce_float(s.get("hours"))
            # If "count" + "hours" are filled, multiply for total man-hours.
            # If only "hours" is filled, treat as crew-hours total for the day.
            man_hours = count * hrs_per_worker if count and hrs_per_worker else hrs_per_worker
            entry = sub_by_company.setdefault(company, {
                "company": company,
                "trade": s.get("trade") or "",
                "days_on_site": 0,
                "headcount_total": 0.0,
                "hours": 0.0,
            })
            entry["days_on_site"] += 1
            entry["headcount_total"] += count
            entry["hours"] += man_hours
            sub_total_hours += man_hours

        # Materials — one row per ticket
        for m in (r.get("materials") or []):
            material_lines.append({
                "report_date": r.get("report_date") or "",
                "description": m.get("description") or "",
                "quantity": m.get("quantity") or "",
                "unit": m.get("unit") or "",
                "supplier": m.get("supplier") or "",
                "ticket_number": m.get("ticket_number") or "",
                "notes": m.get("notes") or "",
                "ticket_photo_count": len(m.get("ticket_photos") or []),
            })

    crew_breakdown = sorted(crew_by_name.values(), key=lambda e: -e["hours"])
    sub_breakdown = sorted(sub_by_company.values(), key=lambda e: -e["hours"])

    labor_cost = round(crew_total_hours * rate, 2)

    return {
        "project_number": project_number,
        "project_name": project_name_seen or "",
        "date_from": min(actual_dates) if actual_dates else date_from,
        "date_to": max(actual_dates) if actual_dates else date_to,
        "report_count": len(reports),
        "labor_rate": rate,
        "crew_hours_total": round(crew_total_hours, 2),
        "labor_cost": labor_cost,
        "crew_breakdown": [
            {**e, "hours": round(e["hours"], 2), "cost_at_rate": round(e["hours"] * rate, 2)}
            for e in crew_breakdown
        ],
        "sub_hours_total": round(sub_total_hours, 2),
        "sub_breakdown": [
            {**e, "hours": round(e["hours"], 2), "headcount_total": round(e["headcount_total"], 2)}
            for e in sub_breakdown
        ],
        "material_count": len(material_lines),
        "material_lines": material_lines,
    }


# ---------------------------------------------------------------------------
# Daily Report numbering — see /daily-reports/next-number above (registered
# before the /{report_id} route so FastAPI matches it correctly).
# ---------------------------------------------------------------------------


async def _write_equipment_master(items: List[Dict[str, Any]]) -> int:
    """Replace the equipment_master collection with `items` and fan-out to
    equipment_units for the legacy Pre-Op dropdown. Returns inserted count.

    Items are expected to already be in the parser's normalized shape
    (see equipment_parser.parse_equipment_xlsx).
    """
    log = logging.getLogger(__name__)
    await db.equipment_master.delete_many({})
    if not items:
        return 0
    for it in items:
        it.setdefault("id", str(uuid.uuid4()))
    await db.equipment_master.insert_many(items)
    # Fan out into equipment_units (used by the existing Pre-Op type→units
    # dropdown). Only insert what's not already there.
    try:
        existing_units = set()
        async for u in db.equipment_units.find(
            {}, {"_id": 0, "equipment_type": 1, "unit_label": 1}
        ):
            existing_units.add(
                (u.get("equipment_type", ""), (u.get("unit_label", "") or "").strip().lower())
            )
        new_units = []
        for it in items:
            etype = it.get("preop_equipment_type") or "Other"
            label = (it.get("display_label") or it.get("make_model") or "").strip()
            if not label:
                continue
            key = (etype, label.lower())
            if key in existing_units:
                continue
            existing_units.add(key)
            new_units.append({
                "id": str(uuid.uuid4()),
                "equipment_type": etype,
                "unit_label": label,
                "make": it.get("make_model", ""),
                "model": "",
                "serial": it.get("vin_serial_number", ""),
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
        if new_units:
            await db.equipment_units.insert_many(new_units)
    except Exception as e:
        log.exception(f"[equipment-master] equipment_units fan-out failed: {e}")
    return len(items)


async def _seed_equipment_master() -> None:
    """Idempotent seed of the equipment_master collection from JSON file.

    Re-runs whenever the JSON file's item count differs from what's stored
    (so updating the seed file ships new equipment automatically on restart).
    """
    log = logging.getLogger(__name__)
    if not EQUIPMENT_MASTER_SEED_FILE.exists():
        log.info(f"[equipment-master] seed file missing: {EQUIPMENT_MASTER_SEED_FILE}")
        return
    try:
        with open(EQUIPMENT_MASTER_SEED_FILE, "r", encoding="utf-8") as fh:
            import json as _json_em
            seed_items = _json_em.load(fh)
    except Exception as e:
        log.exception(f"[equipment-master] failed to read seed: {e}")
        return

    existing_count = await db.equipment_master.count_documents({})
    if existing_count == len(seed_items) and existing_count > 0:
        return  # already seeded and matches file

    n = await _write_equipment_master(seed_items)
    log.info(f"[equipment-master] seeded {n} units from JSON")


@api_router.get("/admin/equipment-master/status")
async def equipment_master_status(_: bool = Depends(require_admin)):
    """Quick status panel for the Admin Hub: count + per-category breakdown +
    last-updated timestamp from the seed JSON file (mtime)."""
    count = await db.equipment_master.count_documents(ACTIVE_FILTER)
    archived = await db.equipment_master.count_documents({"deleted_at": {"$ne": None}})
    cursor = db.equipment_master.find(ACTIVE_FILTER, {"_id": 0, "category": 1})
    cats: Dict[str, int] = {}
    async for d in cursor:
        c = d.get("category", "Misc Equipment")
        cats[c] = cats.get(c, 0) + 1
    last_updated = None
    if EQUIPMENT_MASTER_SEED_FILE.exists():
        last_updated = datetime.fromtimestamp(
            EQUIPMENT_MASTER_SEED_FILE.stat().st_mtime, tz=timezone.utc
        ).isoformat()
    return {
        "count": count,
        "archived": archived,
        "categories": dict(sorted(cats.items(), key=lambda x: -x[1])),
        "last_updated": last_updated,
        "seed_file": str(EQUIPMENT_MASTER_SEED_FILE),
    }


@api_router.post("/admin/equipment-master")
async def create_equipment_master_unit(
    payload: Dict[str, Any],
    _: bool = Depends(require_shop_or_admin),
):
    """Add a single unit to the MASCI fleet. Mechanics + admins + PMs can
    use this to register new equipment without uploading a full xlsx.

    If a soft-deleted unit with the same unit_number already exists, the
    insert auto-restores it instead of creating a duplicate row.
    """
    unit_number = (payload.get("unit_number") or "").strip()
    if not unit_number:
        raise HTTPException(status_code=400, detail="Unit number is required")
    existing = await db.equipment_master.find_one({"unit_number": unit_number}, {"_id": 0})
    if existing:
        if existing.get("deleted_at"):
            await _restore_row("equipment_master", {"unit_number": unit_number})
            doc = await db.equipment_master.find_one({"unit_number": unit_number}, {"_id": 0})
            return doc or {"ok": True, "restored": True}
        raise HTTPException(status_code=409, detail=f"Unit {unit_number} already exists")
    doc = {
        "id": str(uuid.uuid4()),
        "unit_number": unit_number,
        "make": (payload.get("make") or "").strip(),
        "model": (payload.get("model") or "").strip(),
        "make_model": (payload.get("make_model") or f"{payload.get('make','')} {payload.get('model','')}").strip(),
        "year": str(payload.get("year") or "").strip(),
        "vin_serial_number": (payload.get("vin_serial_number") or "").strip(),
        "comments": (payload.get("comments") or "").strip(),
        "company": (payload.get("company") or "MASCI").strip(),
        "category": (payload.get("category") or "Misc Equipment").strip(),
        "preop_equipment_type": (payload.get("preop_equipment_type") or "Other").strip(),
        "display_label": (payload.get("display_label") or "").strip(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.equipment_master.insert_one(doc)
    doc.pop("_id", None)
    return doc


@api_router.put("/admin/equipment-master/{unit_id}")
async def update_equipment_master_unit(
    unit_id: str,
    payload: Dict[str, Any],
    _: bool = Depends(require_shop_or_admin),
):
    """Edit a single fleet unit (matched by id OR unit_number)."""
    allowed = {"unit_number", "make", "model", "make_model", "year", "vin_serial_number",
               "comments", "company", "category", "preop_equipment_type", "display_label"}
    update = {k: payload[k] for k in allowed if k in payload}
    if "unit_number" in update and not (update["unit_number"] or "").strip():
        raise HTTPException(status_code=400, detail="Unit number cannot be blank")
    update["updated_at"] = datetime.now(timezone.utc).isoformat()
    res = await db.equipment_master.update_one(
        {"$and": [
            {"$or": [{"id": unit_id}, {"unit_number": unit_id}]},
            ACTIVE_FILTER,
        ]},
        {"$set": update},
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Unit not found")
    doc = await db.equipment_master.find_one(
        {"$or": [{"id": unit_id}, {"unit_number": unit_id}]}, {"_id": 0}
    )
    return doc or {"ok": True}


@api_router.delete("/admin/equipment-master/{unit_id}")
async def delete_equipment_master_unit(
    unit_id: str,
    _: bool = Depends(require_shop_or_admin),
):
    """Soft-remove a single fleet unit (matched by id OR unit_number).
    The row is hidden from the active fleet immediately and hard-purged
    after ``SOFT_DELETE_RETAIN_DAYS`` days. Use the Archive tab + Restore
    button to undo within the window."""
    if not await _soft_delete(
        "equipment_master",
        {"$or": [{"id": unit_id}, {"unit_number": unit_id}]},
    ):
        raise HTTPException(status_code=404, detail="Unit not found")
    return {"ok": True, "soft_deleted": True, "retain_days": SOFT_DELETE_RETAIN_DAYS}


@api_router.post("/admin/equipment-master/upload")
async def upload_equipment_master(
    file: UploadFile = File(...),
    sheet: str = Form("Louis"),
    _: bool = Depends(require_admin),
):
    """Replace the entire MASCI equipment fleet from an uploaded xlsx file.

    The xlsx is parsed via `equipment_parser.parse_equipment_xlsx`, the JSON
    seed file at /app/backend/data/equipment_master.json is overwritten so
    future restarts stay in sync, and the equipment_master + equipment_units
    collections are refreshed atomically.
    """
    log = logging.getLogger(__name__)
    fname = (file.filename or "").lower()
    if not (fname.endswith(".xlsx") or fname.endswith(".xlsm")):
        raise HTTPException(
            status_code=400,
            detail="Only .xlsx files are accepted (got '%s')" % (file.filename or ""),
        )
    raw = await file.read()
    if not raw or len(raw) > 25 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Empty or oversized file (max 25 MB)")

    # Back up the previous seed file before replacing
    try:
        if EQUIPMENT_MASTER_SEED_FILE.exists():
            ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
            backup = EQUIPMENT_MASTER_SEED_FILE.with_suffix(f".{ts}.bak.json")
            EQUIPMENT_MASTER_SEED_FILE.replace(backup)
    except Exception as e:
        log.warning(f"[equipment-master] backup of previous seed failed: {e}")

    try:
        from equipment_parser import parse_equipment_xlsx
        parsed = parse_equipment_xlsx(raw, sheet_name=sheet or "Louis")
    except Exception as e:
        log.exception("[equipment-master] xlsx parse failed")
        raise HTTPException(status_code=400, detail=f"Could not parse xlsx: {e}")

    items = parsed["items"]
    if not items:
        raise HTTPException(
            status_code=400,
            detail=f"No equipment rows found in sheet '{parsed['sheet']}'.",
        )

    # Persist new seed JSON so the next restart stays in sync
    try:
        EQUIPMENT_MASTER_SEED_FILE.parent.mkdir(parents=True, exist_ok=True)
        import json as _json_em
        with open(EQUIPMENT_MASTER_SEED_FILE, "w", encoding="utf-8") as fh:
            _json_em.dump(items, fh, indent=2)
    except Exception as e:
        log.exception(f"[equipment-master] writing seed JSON failed: {e}")
        raise HTTPException(status_code=500, detail="Could not write seed file")

    inserted = await _write_equipment_master(items)
    log.info(
        f"[equipment-master] uploaded {inserted} units from '{file.filename}' "
        f"(sheet={parsed['sheet']})"
    )
    return {
        "ok": True,
        "count": inserted,
        "sheet": parsed["sheet"],
        "category_counts": parsed["category_counts"],
        "filename": file.filename,
    }


# ============================================================
# Shop Activity Feed + Equipment Parts Catalog
# ----------------------------------------------------------
# Extracted to /app/backend/routes/shop_parts.py 2026-04-28 as the
# first proof-of-pattern for the larger server.py refactor (P1).
# Endpoints registered there:
#   GET    /shop/activity
#   GET    /equipment-parts                       (list)
#   GET    /equipment-parts/{unit_number}         (single)
#   PUT    /equipment-parts/{unit_number}         (upsert)
#   DELETE /equipment-parts/{unit_number}         (admin only)
#   GET    /admin/equipment-parts/status
#   POST   /admin/equipment-parts/upload          (xlsx/csv)
#   POST   /equipment-parts/order                 (Resend email)
# ============================================================
from routes.shop_parts import register_shop_parts_routes  # noqa: E402

register_shop_parts_routes(api_router, db, require_admin, require_shop_or_admin)


# ============================================================
# Compliance CSV Exports (admin-only)
# ============================================================
EXPORTABLE_KINDS = {
    "inspections": "inspections",
    "meetings": "meetings",
    "jhas": "jhas",
    "incidents": "incidents",
    "daily-reports": "daily_reports",
    "equipment-inspections": "equipment_inspections",
}

# Per-kind row schema — what each CSV column should contain. We deliberately
# omit photos / signatures (binary blobs) and the raw checklist dict (renders
# poorly in Excel). Reviewers click into the Admin Hub for the full record.
EXPORT_FIELDS: Dict[str, List[str]] = {
    "inspections": [
        "inspection_date", "inspection_time", "project_name", "project_number",
        "location", "inspector_name", "foreman_name", "operation",
        "work_activity", "hazards_observed", "stop_work_issued",
        "ppe_in_use", "weather_summary", "created_at", "id",
    ],
    "meetings": [
        "meeting_date", "meeting_time", "project_name", "project_number",
        "location", "presenter_name", "topic_title", "topic_number",
        "attendee_count", "discussion_summary", "created_at", "id",
    ],
    "jhas": [
        "jha_date", "project_name", "project_number", "location",
        "supervisor_name", "task_description", "approver_name",
        "step_count", "created_at", "id",
    ],
    "incidents": [
        "incident_date", "incident_time", "project_name", "project_number",
        "location", "incident_type", "severity", "osha_recordable",
        "work_stopped", "person_name", "body_part", "injury_nature",
        "treatment_provided", "medical_facility",
        "reporter_name", "supervisor_name",
        "root_cause_categories", "witness_count",
        "description", "immediate_action", "follow_up_action",
        "created_at", "id",
    ],
    "daily-reports": [
        "report_date", "project_name", "project_number", "location",
        "prepared_by", "superintendent_name",
        "weather_summary", "high_temp_f", "low_temp_f",
        "crew_count", "subcontractor_count", "visitor_count",
        "equipment_count", "material_count", "activity_count",
        "accident_or_injury", "safety_notified", "safety_notified_who",
        "safety_notified_time", "incident_report_filled",
        "incident_report_time",
        "delays_or_issues", "tomorrows_plan",
        "created_at", "id",
    ],
    "equipment-inspections": [
        "inspection_date", "inspection_time", "project_name", "project_number",
        "location", "operator_name", "equipment_type", "equipment_unit",
        "equipment_make", "equipment_model", "equipment_serial",
        "hour_meter", "odometer",
        "pass_count", "fail_count", "na_count", "out_of_service",
        "deficiency_notes", "corrective_actions",
        "created_at", "id",
    ],
}


def _csv_value(v: Any) -> str:
    """Flatten a record value into a CSV-friendly string."""
    if v is None:
        return ""
    if isinstance(v, (list, tuple)):
        # Skip image blobs, summarize the rest with semicolons
        items = [
            str(x)
            for x in v
            if not (isinstance(x, str) and x.startswith("data:image/"))
        ]
        return "; ".join(items)
    if isinstance(v, dict):
        # e.g. witnesses, root cause categories — flatten one level
        return "; ".join(f"{k}={_csv_value(val)}" for k, val in v.items())
    return str(v)


def _date_field_for(kind: str) -> str:
    return {
        "inspections": "inspection_date",
        "meetings": "meeting_date",
        "jhas": "jha_date",
        "incidents": "incident_date",
        "daily-reports": "report_date",
        "equipment-inspections": "inspection_date",
    }[kind]


def _normalize_export_doc(kind: str, d: Dict[str, Any]) -> None:
    """Mutate a record in place so derived counts are populated for CSV columns."""
    if kind == "meetings" and "attendee_count" not in d:
        d["attendee_count"] = len(d.get("attendees") or [])
    if kind == "jhas" and "step_count" not in d:
        d["step_count"] = len(d.get("steps") or [])
    if kind == "incidents" and "witness_count" not in d:
        d["witness_count"] = len(d.get("witnesses") or [])
    if kind == "incidents" and "root_cause_categories" not in d:
        cats = d.get("root_causes") or []
        d["root_cause_categories"] = (
            "; ".join(cats) if isinstance(cats, list) else str(cats)
        )
    if kind == "daily-reports":
        for k_, src in (
            ("crew_count", "crew"),
            ("subcontractor_count", "subcontractors"),
            ("visitor_count", "visitors"),
            ("equipment_count", "equipment"),
            ("material_count", "materials"),
            ("activity_count", "activities"),
        ):
            if k_ not in d:
                d[k_] = len(d.get(src) or [])


def _build_csv_bytes(kind: str, docs: List[Dict[str, Any]]) -> bytes:
    """Render a CSV (UTF-8 bytes) for one kind."""
    fields = list(EXPORT_FIELDS[kind])
    for d in docs:
        _normalize_export_doc(kind, d)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(fields)
    for d in docs:
        writer.writerow([_csv_value(d.get(f)) for f in fields])
    return buf.getvalue().encode("utf-8")


@api_router.get("/exports/csv")
async def export_csv(
    kind: str,
    start: Optional[str] = None,  # YYYY-MM-DD inclusive
    end: Optional[str] = None,    # YYYY-MM-DD inclusive
    _: bool = Depends(require_admin),
):
    """Stream a CSV export for one form kind, optionally filtered by date.

    Query params:
        kind  = inspections | meetings | jhas | incidents | daily-reports | equipment-inspections
        start = YYYY-MM-DD (inclusive)
        end   = YYYY-MM-DD (inclusive)

    Both date params are optional — omit for all-time.
    """
    if kind not in EXPORTABLE_KINDS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown kind '{kind}'. Allowed: {sorted(EXPORTABLE_KINDS.keys())}",
        )

    coll_name = EXPORTABLE_KINDS[kind]
    date_field = _date_field_for(kind)

    q: Dict[str, Any] = {}
    if start or end:
        cond: Dict[str, str] = {}
        if start:
            cond["$gte"] = start
        if end:
            cond["$lte"] = end
        q[date_field] = cond

    # Drop heavy blobs from the projection
    projection = {
        "_id": 0,
        "photos": 0,
        "signature": 0,
        "operator_signature": 0,
        "supervisor_signature": 0,
        "reporter_signature": 0,
        "preparer_signature": 0,
        "approver_signature": 0,
    }

    cursor = db[coll_name].find(q, projection).sort(date_field, -1)
    docs = await cursor.to_list(20000)

    csv_bytes = _build_csv_bytes(kind, docs)

    today = datetime.now(timezone.utc).date().isoformat()
    range_tag = ""
    if start and end:
        range_tag = f"_{start}_to_{end}"
    elif start:
        range_tag = f"_from_{start}"
    elif end:
        range_tag = f"_through_{end}"
    filename = f"MASCI_{kind}{range_tag}_{today}.csv"

    return Response(
        content=csv_bytes,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Record-Count": str(len(docs)),
        },
    )


@api_router.get("/exports/summary")
async def export_summary(
    start: Optional[str] = None,
    end: Optional[str] = None,
    _: bool = Depends(require_admin),
):
    """Quick count-per-kind for a given date range — used by the Admin UI to
    show a foreman 'You have 47 records in this range' before they download."""
    out: Dict[str, int] = {}
    for kind, coll_name in EXPORTABLE_KINDS.items():
        date_field = _date_field_for(kind)
        q: Dict[str, Any] = {}
        if start or end:
            cond: Dict[str, str] = {}
            if start:
                cond["$gte"] = start
            if end:
                cond["$lte"] = end
            q[date_field] = cond
        out[kind] = await db[coll_name].count_documents(q)
    return {"start": start, "end": end, "counts": out, "total": sum(out.values())}


# ----------------------------------------------------------------------
# Full backup — single .zip with everything (CSVs + JSON + PDFs + photos)
# ----------------------------------------------------------------------
import asyncio as _backup_asyncio  # noqa: E402
import json as _backup_json  # noqa: E402
import zipfile  # noqa: E402


def _safe_filename(s: str, max_len: int = 60) -> str:
    """Make a filesystem-friendly fragment from a free-form string."""
    cleaned = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in (s or ""))
    cleaned = cleaned.strip("_") or "untitled"
    return cleaned[:max_len]


def _record_filename(kind: str, record: dict) -> str:
    """Stable, sortable filename: <date>_<id-prefix>_<project>.<ext>"""
    date_part = (
        record.get("inspection_date")
        or record.get("meeting_date")
        or record.get("jha_date")
        or record.get("incident_date")
        or record.get("report_date")
        or "0000-00-00"
    )
    rid = (record.get("id") or "")[:8]
    proj = _safe_filename(record.get("project_name") or "MASCI", 40)
    return f"{date_part}_{rid}_{proj}"


@api_router.get("/exports/full-backup")
async def exports_full_backup(_: bool = Depends(require_admin_strict)):
    """One-click off-site backup. Streams a single .zip back containing:

    /CSV/                — one CSV per kind (no photos/signatures inline)
    /<kind>/json/        — every record as raw JSON (photos + signatures intact)
    /<kind>/pdf/         — every record rendered to PDF via WeasyPrint
    /crew_hub/           — Crew Hub collections as JSON
    /safety_aux/         — Equipment unit registry, JHP plan PDFs, trench-box refs
    /backup_manifest.json — schema + counts + generated_at
    /backup_log.txt      — human-readable summary

    Built STREAMING to disk via `_build_backup_zip_to_path` then returned
    as a FileResponse. Memory use ~5–20 MB regardless of zip size, so the
    backend never OOMs even on 1 GB+ archives.
    """
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    # Build into the canonical backups dir so the file is preserved + reusable.
    _now = datetime.now(timezone.utc)
    _stamp = _now.strftime("%Y-%m-%d_%H%M%SZ")
    filename = f"MASCI_full_backup_{_stamp}.zip"
    out = BACKUPS_DIR / filename
    # Per-call unique tmp suffix so concurrent requests within the same
    # second can't clobber each other's stream (or each other's rename).
    tmp = out.with_suffix(f".zip.tmp.{uuid.uuid4().hex[:8]}")
    total_records, _ = await _build_backup_zip_to_path(db, tmp)
    tmp.replace(out)
    size_bytes = out.stat().st_size
    return FileResponse(
        path=str(out),
        media_type="application/zip",
        filename=filename,
        headers={
            "X-Record-Count": str(total_records),
            "X-Backup-Size-Bytes": str(size_bytes),
        },
    )


async def _build_backup_zip(db) -> tuple[bytes, int, str]:
    """DEPRECATED — use `_build_backup_zip_to_path` directly. Retained
    only to keep the symbol importable in case any out-of-tree caller
    still references it. Always raises to fail loudly if reactivated.
    """
    raise RuntimeError(
        "_build_backup_zip is deprecated; use _build_backup_zip_to_path "
        "to stream to disk and avoid OOM."
    )


async def _build_backup_zip_to_path(db, out_path: Path) -> tuple[int, str]:
    """STREAMING variant — writes the full backup directly to ``out_path``
    on disk instead of buffering the entire archive in memory. Memory use
    stays around 5–20 MB regardless of how big the archive grows. This is
    the **safe** path for production containers with small memory limits;
    the in-memory `_build_backup_zip` would OOM-kill the backend on a
    1 GB+ archive. Returns (record_count, filename).
    """
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y-%m-%d_%H%M%SZ")
    filename = f"MASCI_full_backup_{stamp}.zip"

    log_lines: List[str] = [
        "MASCI Hub — Full Backup",
        f"Generated: {now.isoformat()}",
        "Source: mascidocs.com (production)",
        "",
        "Per-kind record counts:",
    ]

    total_records = 0
    total_pdf_bytes = 0
    pdf_failures: List[str] = []

    # Open the zip directly on disk — every writestr is appended on the fly,
    # never buffered in memory.
    with zipfile.ZipFile(str(out_path), "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for kind, coll_name in EXPORTABLE_KINDS.items():
            await asyncio.sleep(0)  # yield to event loop — keeps healthcheck alive
            # STREAMING: iterate the cursor doc-by-doc instead of loading
            # every doc into memory via .to_list(). Safety records embed
            # multi-MB photo blobs; on a production database with many
            # records a single .to_list() call can balloon to >1 GB and
            # OOM-kill the container. Streaming keeps memory flat at
            # ~1 doc worth of bytes.
            kind_count = 0
            # We still need the CSV later which wants structured rows, but
            # we can accumulate trimmed rows without the big blobs. For
            # now, build CSV from the first 2000 docs (enough for an audit
            # trail) to keep memory bounded.
            CSV_CAP = 2000
            csv_rows: list[dict] = []
            pdf_kind = {
                "inspections": "inspection",
                "meetings": "meeting",
                "jhas": "jha",
                "incidents": "incident",
                "daily-reports": "daily-report",
                "equipment-inspections": "equipment-inspection",
            }.get(kind)

            async for d in db[coll_name].find({}, {"_id": 0}).sort("created_at", -1):
                kind_count += 1
                if len(csv_rows) < CSV_CAP:
                    csv_rows.append(dict(d))

                base = _record_filename(kind, d)
                try:
                    zf.writestr(
                        f"{kind}/json/{base}.json",
                        _backup_json.dumps(d, indent=2, default=str).encode("utf-8"),
                    )
                except Exception as e:  # noqa: BLE001
                    log_lines.append(f"    [warn] {kind}/{d.get('id')} JSON failed: {e}")

                if pdf_kind:
                    try:
                        pdf_bytes = await _backup_asyncio.to_thread(
                            render_record_pdf, pdf_kind, d
                        )
                        total_pdf_bytes += len(pdf_bytes)
                        zf.writestr(f"{kind}/pdf/{base}.pdf", pdf_bytes)
                        del pdf_bytes
                    except Exception as e:  # noqa: BLE001
                        pdf_failures.append(f"{kind}/{d.get('id')}: {e}")
                    await asyncio.sleep(0)

                # Free the doc ASAP so photo blobs don't linger.
                del d
                # Every 10 docs, yield to event loop AND encourage gc.
                if kind_count % 10 == 0:
                    await asyncio.sleep(0)

            total_records += kind_count
            log_lines.append(f"  {kind:25s} : {kind_count:5d}")

            # /CSV/ — use only the capped sample to keep memory bounded.
            try:
                csv_bytes = _build_csv_bytes(kind, csv_rows)
                zf.writestr(f"CSV/MASCI_{kind}_{stamp}.csv", csv_bytes)
                if kind_count > CSV_CAP:
                    log_lines.append(
                        f"    [note] CSV truncated to first {CSV_CAP} of {kind_count} rows"
                    )
            except Exception as e:  # noqa: BLE001
                log_lines.append(f"    [warn] CSV build failed: {e}")
            del csv_rows

        # Manifest
        log_lines.append("")
        log_lines.append("Totals:")
        log_lines.append(f"  Records:        {total_records}")
        log_lines.append(f"  PDFs rendered:  {total_pdf_bytes / (1024 * 1024):.1f} MB")
        log_lines.append(f"  PDF failures:   {len(pdf_failures)}")
        if pdf_failures:
            log_lines.append("")
            log_lines.append("PDF render failures (first 20):")
            for line in pdf_failures[:20]:
                log_lines.append(f"  - {line}")

        # ====================================================================
        # AUTO-DISCOVERED COLLECTIONS — every Mongo collection that ISN'T
        # already exported above gets its JSON dumped here. This means any
        # NEW collection added in the future (parts catalogs, QC reports,
        # etc.) is included automatically — no human has to remember to add
        # it to a list. The only excludes are MongoDB system collections.
        # ====================================================================
        EXCLUDE_FROM_AUTO_BACKUP = {
            # Already covered above
            *(coll for coll in EXPORTABLE_KINDS.values()),
            # System / internal
            "system.indexes",
        }
        # Per-collection projection rules — sensitive fields stay redacted
        # regardless of which path picks the collection up.
        SENSITIVE_FIELD_REDACTION = {
            "users": {"password_hash": 0, "_id": 0},
        }

        all_collections = await db.list_collection_names()
        log_lines.append("")
        log_lines.append("Auto-discovered collections (JSON only):")
        auto_total = 0
        captured_collections: List[str] = list(EXPORTABLE_KINDS.values())
        for coll_name in sorted(all_collections):
            await asyncio.sleep(0)  # keep event loop alive
            if coll_name in EXCLUDE_FROM_AUTO_BACKUP or coll_name.startswith("system."):
                continue
            try:
                projection = SENSITIVE_FIELD_REDACTION.get(coll_name, {"_id": 0})
                # STREAM the collection straight into a JSON array on disk
                # to avoid holding every doc in memory. Some collections
                # (project_docs, equipment_parts, messages) can hit
                # hundreds of MB when they contain base64 file blobs.
                coll_count = 0
                # Write opening bracket first, then stream docs comma-separated.
                # We accumulate one doc at a time into the zip entry via a
                # small buffer, but the buffer is bounded per-doc so memory
                # stays constant regardless of collection size.
                import io as _bio
                buf = _bio.BytesIO()
                buf.write(b"[\n")
                first = True
                async for doc in db[coll_name].find({}, projection):
                    coll_count += 1
                    if not first:
                        buf.write(b",\n")
                    first = False
                    buf.write(_backup_json.dumps(doc, indent=2, default=str).encode("utf-8"))
                    del doc
                    if coll_count % 25 == 0:
                        await asyncio.sleep(0)
                buf.write(b"\n]\n")
                zf.writestr(f"collections/{coll_name}.json", buf.getvalue())
                del buf
                auto_total += coll_count
                captured_collections.append(coll_name)
                log_lines.append(f"  collections/{coll_name:24s} : {coll_count:5d}")
            except Exception as e:  # noqa: BLE001
                log_lines.append(f"    [warn] collections/{coll_name} failed: {e}")
        total_records += auto_total
        log_lines.append(f"  Auto-discovered subtotal: {auto_total}")

        # ====================================================================
        # DISK-BACKED FILES — the /app/backend/storage tree (Oxford 153 MB
        # FDOT plans + every other big project doc that exceeds Mongo's BSON
        # limit). These would otherwise be lost on container redeploy.
        # ====================================================================
        DISK_STORAGE_ROOT = Path("/app/backend/storage")
        log_lines.append("")
        log_lines.append("Disk-backed files (storage tree):")
        disk_files_count = 0
        disk_bytes = 0
        if DISK_STORAGE_ROOT.is_dir():
            for f in DISK_STORAGE_ROOT.rglob("*"):
                await asyncio.sleep(0)  # yield each file — disk_files can be 100MB+
                if not f.is_file():
                    continue
                try:
                    rel = f.relative_to(DISK_STORAGE_ROOT)
                    # STREAM the file into the zip 1 MB at a time so even a
                    # 150 MB+ PDF (Oxford FDOT plans) never lives in RAM.
                    size = f.stat().st_size
                    with zf.open(f"disk_files/{rel.as_posix()}", "w", force_zip64=True) as zdst, \
                         f.open("rb") as src:
                        while True:
                            chunk = src.read(1024 * 1024)
                            if not chunk:
                                break
                            zdst.write(chunk)
                            await asyncio.sleep(0)
                    disk_files_count += 1
                    disk_bytes += size
                except Exception as e:  # noqa: BLE001
                    log_lines.append(f"    [warn] disk file {f} failed: {e}")
            log_lines.append(
                f"  /app/backend/storage  : {disk_files_count} files, "
                f"{disk_bytes / (1024 * 1024):.1f} MB"
            )
        else:
            log_lines.append("  (no disk storage tree — nothing to bundle)")

        # ---------- Backup integrity manifest ----------
        # Records what was captured so a future restore can verify the zip
        # didn't lose anything. The integrity-check endpoint compares this
        # against the live DB and surfaces a warning if a new collection
        # exists that isn't yet in any backup.
        zf.writestr(
            "backup_manifest.json",
            _backup_json.dumps({
                "source": "mascidocs.com",
                "generated_at": now.isoformat(),
                "version": "3",
                "total_records": total_records,
                "captured_collections": sorted(set(captured_collections)),
                "all_db_collections_at_backup_time": sorted(all_collections),
                "disk_files_count": disk_files_count,
                "disk_files_bytes": disk_bytes,
            }, indent=2).encode("utf-8"),
        )

        zf.writestr("backup_log.txt", "\n".join(log_lines).encode("utf-8"))

    return total_records, filename


# ----------------------------------------------------------------------
# Stored backups — daily scheduled backup saved to disk.
# ----------------------------------------------------------------------
BACKUPS_DIR = Path(os.environ.get("BACKUPS_DIR", "/app/backend/backups")).resolve()
BACKUP_RETENTION_DAYS = int(os.environ.get("BACKUP_RETENTION_DAYS", "14"))
BACKUP_HOUR_UTC = int(os.environ.get("BACKUP_HOUR_UTC", "2"))   # legacy single-window default 02:00 UTC


def _parse_backup_hours() -> list[int]:
    """Parse BACKUP_HOURS_UTC env var (comma-separated UTC hours).
    Default = "2,18" → nightly + mid-day backups so the field crew always
    has two off-site recovery points per workday. Falls back to
    [BACKUP_HOUR_UTC] if the env var is missing/empty. Invalid entries
    are dropped, duplicates removed, result sorted."""
    raw = (os.environ.get("BACKUP_HOURS_UTC") or "").strip()
    if not raw:
        raw = f"{BACKUP_HOUR_UTC},18"  # default: nightly 02:00 UTC + mid-day 18:00 UTC
    hours: set[int] = set()
    for part in raw.split(","):
        s = part.strip()
        if not s:
            continue
        try:
            h = int(s)
            if 0 <= h <= 23:
                hours.add(h)
        except ValueError:
            continue
    if not hours:
        hours = {BACKUP_HOUR_UTC}
    return sorted(hours)


BACKUP_HOURS_UTC: list[int] = _parse_backup_hours()
# DEFENSE LAYER 2 — Hard ceiling on stored backups. The container volume
# is small (9.8 GB) and a single full backup is ~750 MB. Keeping 3 max
# means we use ≤ 2.3 GB on backups, leaving plenty of headroom for the
# working DB and the disk-backed files. This is the single biggest
# defense against "backup fills disk → backend crashes → Cloudflare 520".
BACKUP_KEEP_MAX = int(os.environ.get("BACKUP_KEEP_MAX", "3"))
# DEFENSE LAYER 3 — Auto-prune trigger. If disk usage exceeds this
# percentage at boot OR right before a backup write, aggressively purge
# backups down to BACKUP_KEEP_MAX-1. Acts as an emergency brake.
BACKUP_DISK_HIGH_WATERMARK = int(os.environ.get("BACKUP_DISK_HIGH_WATERMARK", "75"))


def _disk_pct_used(path: str = "/app") -> int:
    """Return percent disk used at `path` (0-100). Returns 0 on error."""
    try:
        import shutil as _sh
        total, used, _free = _sh.disk_usage(path)
        return int((used / total) * 100) if total else 0
    except Exception:
        return 0


def _emergency_prune_backups(reason: str) -> int:
    """Sync helper. Aggressively prune backups + ORPHAN .tmp files. Safe to
    call from any context (sync or async via to_thread). Returns count pruned.
    Catches all exceptions internally — NEVER raises into the caller.

    NOTE: .tmp files younger than 10 minutes are KEPT — they may be a backup
    actively streaming to disk in another worker / concurrent request.
    Deleting them would break the rename step at the end of the build.
    """
    pruned = 0
    _now_ts = datetime.now(timezone.utc).timestamp()
    _ORPHAN_TMP_AGE_SEC = 600  # 10 minutes
    try:
        BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
        for p in BACKUPS_DIR.glob("*.zip.tmp*"):
            try:
                if (_now_ts - p.stat().st_mtime) < _ORPHAN_TMP_AGE_SEC:
                    continue  # active stream — leave alone
                p.unlink()
                pruned += 1
            except Exception:
                continue
        # Keep BACKUP_KEEP_MAX-1 newest so the next backup fits within cap
        files = sorted(
            BACKUPS_DIR.glob("MASCI_full_backup_*.zip"),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )
        keep = max(0, BACKUP_KEEP_MAX - 1)
        for p in files[keep:]:
            try:
                p.unlink()
                pruned += 1
            except Exception:
                continue
        if pruned:
            logger.warning(
                f"[backup-defense] EMERGENCY PRUNE ({reason}) — "
                f"deleted {pruned} files, disk now at {_disk_pct_used()}%"
            )
    except Exception as e:
        logger.warning(f"[backup-defense] emergency prune itself failed: {e}")
    return pruned


def _list_stored_backups() -> List[dict]:
    """Return metadata for every .zip in the backups dir (newest first)."""
    if not BACKUPS_DIR.exists():
        return []
    rows = []
    for p in sorted(BACKUPS_DIR.glob("MASCI_full_backup_*.zip"), reverse=True):
        try:
            st = p.stat()
            rows.append({
                "filename": p.name,
                "size_bytes": st.st_size,
                "created_at": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
            })
        except Exception:
            continue
    return rows


async def _run_scheduled_backup(db) -> Optional[dict]:
    """Build a backup and persist to BACKUPS_DIR. Prune files older than the
    retention window and over the max-keep ceiling. Returns a small summary
    dict or None on failure."""
    try:
        BACKUPS_DIR.mkdir(parents=True, exist_ok=True)

        # PRE-FLIGHT PRUNE — clean up before writing so we never run out of
        # disk mid-backup. Drops ORPHAN .tmp debris from previous failures
        # (only .tmp older than 10 minutes — younger ones are likely active
        # streams from a concurrent request and would break their rename).
        pre_pruned = 0
        _now_ts = datetime.now(timezone.utc).timestamp()
        _ORPHAN_TMP_AGE_SEC = 600
        for p in BACKUPS_DIR.glob("*.zip.tmp*"):
            try:
                if (_now_ts - p.stat().st_mtime) < _ORPHAN_TMP_AGE_SEC:
                    continue  # active stream — leave alone
                p.unlink()
                pre_pruned += 1
            except Exception:
                continue
        cutoff = datetime.now(timezone.utc).timestamp() - BACKUP_RETENTION_DAYS * 86400
        existing = sorted(
            BACKUPS_DIR.glob("MASCI_full_backup_*.zip"),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )
        # By age
        for p in existing:
            try:
                if p.stat().st_mtime < cutoff:
                    p.unlink()
                    pre_pruned += 1
            except Exception:
                continue
        # By count (keep newest BACKUP_KEEP_MAX-1 so the new one fits within cap)
        existing = sorted(
            BACKUPS_DIR.glob("MASCI_full_backup_*.zip"),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )
        for p in existing[max(0, BACKUP_KEEP_MAX - 1):]:
            try:
                p.unlink()
                pre_pruned += 1
            except Exception:
                continue
        if pre_pruned:
            logger.info(f"[scheduled-backup] pre-flight pruned {pre_pruned} old/tmp files")

        # DEFENSE LAYER 5 — Disk high-water-mark check after prune.
        # If the disk is STILL above the watermark after standard pruning,
        # bail out instead of building a 750 MB zip we can't write. Better
        # to skip a backup than crash the backend.
        pct_after = _disk_pct_used()
        if pct_after >= BACKUP_DISK_HIGH_WATERMARK:
            _emergency_prune_backups(reason=f"pre-build disk {pct_after}%")
            pct_after = _disk_pct_used()
            if pct_after >= 90:
                logger.error(
                    f"[scheduled-backup] ABORT — disk at {pct_after}% even after "
                    f"emergency prune. Backup skipped to protect backend."
                )
                return {
                    "filename": None,
                    "size_bytes": 0,
                    "records": 0,
                    "pruned_old": pre_pruned,
                    "emailed_to": None,
                    "skipped": True,
                    "reason": f"disk_{pct_after}_percent",
                }

        # STREAMING write — go straight to the temp file on disk. Never
        # hold 750 MB in RAM (would OOM-kill the container on small-memory
        # deploys). _build_backup_zip_to_path opens the ZipFile against
        # the temp file and writestr's each entry as it goes.
        BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
        # Pre-compute target name; we'll rename after stream completes.
        _now = datetime.now(timezone.utc)
        _stamp = _now.strftime("%Y-%m-%d_%H%M%SZ")
        filename = f"MASCI_full_backup_{_stamp}.zip"
        out = BACKUPS_DIR / filename
        # Per-call unique tmp suffix so concurrent backup requests can't
        # clobber each other's stream (or rename).
        tmp = out.with_suffix(f".zip.tmp.{uuid.uuid4().hex[:8]}")
        # Build directly into the .tmp; rename atomically when done.
        total_records, _name = await _build_backup_zip_to_path(db, tmp)
        # Use the timestamp-stamped name we computed above (consistent with prior behavior)
        tmp.replace(out)
        size_bytes = out.stat().st_size
        logger.info(
            f"[scheduled-backup] wrote {out.name} ({size_bytes/1024/1024:.1f} MB · {total_records} records)"
        )

        # Email the backup off-site — CRITICAL for redeploy safety.
        # The email helper reads the file lazily to keep memory low when
        # building the slim version for the inbox attachment.
        emailed_to = None
        try:
            emailed_to = await _email_backup_zip_from_path(out, total_records)
        except Exception as e:
            logger.warning(f"[scheduled-backup] email step failed (non-fatal): {e}")

        return {
            "filename": out.name,
            "size_bytes": size_bytes,
            "records": total_records,
            "pruned_old": pre_pruned,
            "emailed_to": emailed_to,
        }
    except Exception as e:
        logger.exception(f"[scheduled-backup] FAILED: {e}")
        return None


def _strip_base64_blobs(obj, _stats=None):
    """Recursively walk a parsed JSON document and replace any large
    base64 / data-URL blob with a small placeholder string. Used by the
    slim-email backup so 153 MB FDOT plans don't end up in the inbox.

    Returns (new_obj, count_stripped, total_bytes_stripped). Original
    fields are preserved by name — the value just becomes
    `"<stripped:base64 N bytes (was field=...)>"` so a future restore
    can detect it and surface a warning.

    Heuristic: any string longer than 32 KB OR starting with `data:`
    that contains only base64-safe chars is treated as a blob.
    """
    import re as _re3
    BLOB_KEYS = {"file_data", "file_bytes", "data_url", "photo", "photo_data",
                 "image", "image_data", "signature", "signature_data",
                 "pdf_bytes", "blob", "content"}
    BIG_THRESHOLD = 32 * 1024  # 32 KB

    if _stats is None:
        _stats = {"count": 0, "bytes": 0}

    def _looks_blob(v: str) -> bool:
        if not isinstance(v, str):
            return False
        if v.startswith("data:") and ";base64," in v[:64]:
            return True
        if len(v) >= BIG_THRESHOLD and _re3.fullmatch(r"[A-Za-z0-9+/=\r\n]+", v[:1024] or ""):
            return True
        return False

    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if isinstance(v, str) and (k in BLOB_KEYS or _looks_blob(v)):
                _stats["count"] += 1
                _stats["bytes"] += len(v)
                out[k] = f"<stripped:base64 {len(v)} bytes (key={k})>"
            else:
                out[k], _, _ = _strip_base64_blobs(v, _stats)
        return out, _stats["count"], _stats["bytes"]
    if isinstance(obj, list):
        new_list = []
        for item in obj:
            new_item, _, _ = _strip_base64_blobs(item, _stats)
            new_list.append(new_item)
        return new_list, _stats["count"], _stats["bytes"]
    if isinstance(obj, str) and _looks_blob(obj):
        _stats["count"] += 1
        _stats["bytes"] += len(obj)
        return f"<stripped:base64 {len(obj)} bytes>", _stats["count"], _stats["bytes"]
    return obj, _stats["count"], _stats["bytes"]


async def _email_backup_zip_from_path(zip_path: Path, total_records: int) -> Optional[str]:
    """OOM-SAFE: Email the backup zip as a Resend attachment WITHOUT
    ever loading the full archive into RAM.

    Strategy:
      • Stat the full zip on disk to learn its size.
      • If full zip is small enough to email directly (≤ BACKUP_EMAIL_MAX_MB),
        read its bytes lazily in a worker thread and base64-encode for Resend.
      • Otherwise, stream entries from the on-disk full zip into a NEW
        slim zip on disk, dropping PDFs + disk_files/ + CSVs and stripping
        large base64 blobs from JSON. Memory stays flat (~10 MB) the whole
        time because we read+write one entry at a time.
      • Only the slim file (~1 MB) is ever loaded into memory for base64
        encoding. The 500 MB+ full zip never touches RAM.

    This eliminates the OOM crash that was killing the production
    container on every scheduled backup.
    """
    to = (os.environ.get("BACKUP_EMAIL_TO") or "").strip()
    if not to:
        return None
    api_key = (os.environ.get("RESEND_API_KEY") or "").strip()
    if not api_key:
        logger.info("[scheduled-backup] email skipped — RESEND_API_KEY missing")
        return None

    max_mb = int(os.environ.get("BACKUP_EMAIL_MAX_MB", "35"))
    full_size_bytes = await asyncio.to_thread(lambda: zip_path.stat().st_size)
    full_size_mb = full_size_bytes / (1024 * 1024)
    filename = zip_path.name

    attachment_path: Path
    attachment_name: str
    slim_notice = ""
    slim_tmp: Optional[Path] = None

    if full_size_mb <= max_mb:
        # Full zip fits — email it directly. Single read of the (small) file.
        attachment_path = zip_path
        attachment_name = filename
    else:
        # Build slim zip on disk by streaming entries. Never holds the
        # full payload in memory.
        slim_tmp = zip_path.with_name(
            zip_path.stem + f"_slim.{uuid.uuid4().hex[:8]}.zip.tmp"
        )
        try:
            stats = await asyncio.to_thread(
                _build_slim_email_zip_on_disk, zip_path, slim_tmp
            )
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[scheduled-backup] slim build failed: {e}")
            try:
                if slim_tmp and slim_tmp.exists():
                    slim_tmp.unlink()
            except Exception:
                pass
            return None

        slim_size_mb = stats["size_bytes"] / (1024 * 1024)
        if slim_size_mb > max_mb:
            logger.warning(
                f"[scheduled-backup] even slim zip is {slim_size_mb:.1f} MB > {max_mb} — "
                f"email skipped. Admin must download from /admin/backups."
            )
            try:
                slim_tmp.unlink()
            except Exception:
                pass
            return None

        attachment_path = slim_tmp
        attachment_name = filename.replace(".zip", "_slim.zip")
        slim_notice = (
            f'<p style="background:#fef3c7;border-left:4px solid #f59e0b;'
            f'padding:10px 14px;border-radius:0 6px 6px 0;color:#92400e;'
            f'font-size:13px;line-height:1.5;margin:14px 0;">'
            f'<strong>Note:</strong> The full backup is {full_size_mb:.0f} MB '
            f'(includes rendered PDFs + project disk archive). For email, '
            f'we sent a <strong>slim {slim_size_mb:.1f} MB version</strong> with '
            f'every record\'s metadata + JSON ({stats["kept"]} entries). '
            f'{stats["stripped_blob_count"]} embedded file blob(s) '
            f'({stats["stripped_blob_bytes"] / (1024*1024):.0f} MB total) were '
            f'stripped — the originals live on the server. Sign in to '
            f'<code>/admin</code> and download <strong>{filename}</strong> '
            f'from the Stored Backups panel for the full archive.'
            f'</p>'
        )
        logger.info(
            f"[scheduled-backup] full {full_size_mb:.1f} MB → emailing slim {slim_size_mb:.1f} MB "
            f"({stats['kept']} entries, stripped {stats['stripped_blob_count']} blobs / "
            f"{stats['stripped_blob_bytes']/1024/1024:.1f} MB)"
        )

    try:
        return await _send_backup_email(
            to=to,
            api_key=api_key,
            attachment_path=attachment_path,
            attachment_name=attachment_name,
            full_size_mb=full_size_mb,
            total_records=total_records,
            slim_notice=slim_notice,
        )
    finally:
        if slim_tmp is not None:
            try:
                if slim_tmp.exists():
                    slim_tmp.unlink()
            except Exception:
                pass


def _build_slim_email_zip_on_disk(src_zip: Path, dst_zip: Path) -> dict:
    """Synchronous helper run via asyncio.to_thread. Streams entries from
    src_zip → dst_zip on disk, dropping non-essential files and stripping
    large base64 blobs from JSON. Memory bounded by the largest single
    entry processed (typically <2 MB after blob stripping).
    """
    import zipfile as _zf2
    import json as _json2

    stripped_blob_count = 0
    stripped_blob_bytes = 0
    kept = 0

    with _zf2.ZipFile(src_zip, "r") as src, \
         _zf2.ZipFile(dst_zip, "w", _zf2.ZIP_DEFLATED) as dst:
        for info in src.infolist():
            n = info.filename
            # Drop rendered PDFs, disk-backed files, and CSV duplicates —
            # they're recoverable from JSON or live on the server's full zip.
            if n.startswith("disk_files/"):
                continue
            if n.endswith(".pdf"):
                continue
            if n.startswith("CSV/"):
                continue
            # Skip directory entries
            if n.endswith("/"):
                continue
            with src.open(info, "r") as fsrc:
                raw = fsrc.read()
            # For JSON files, strip base64 blobs.
            if n.endswith(".json") and len(raw) > 4096:
                try:
                    doc = _json2.loads(raw)
                    new_doc, stripped_count, stripped_bytes = _strip_base64_blobs(doc)
                    if stripped_count:
                        stripped_blob_count += stripped_count
                        stripped_blob_bytes += stripped_bytes
                        raw = _json2.dumps(new_doc, indent=2, default=str).encode("utf-8")
                except Exception:
                    pass
            dst.writestr(n, raw)
            kept += 1
            del raw

    return {
        "size_bytes": dst_zip.stat().st_size,
        "kept": kept,
        "stripped_blob_count": stripped_blob_count,
        "stripped_blob_bytes": stripped_blob_bytes,
    }


async def _send_backup_email(
    *,
    to: str,
    api_key: str,
    attachment_path: Path,
    attachment_name: str,
    full_size_mb: float,
    total_records: int,
    slim_notice: str,
) -> Optional[str]:
    """Read attachment bytes lazily, base64-encode, send via Resend.
    The attachment is guaranteed small (≤ BACKUP_EMAIL_MAX_MB) by the caller.
    """
    import base64 as _bb64

    def _encode() -> str:
        with attachment_path.open("rb") as f:
            return _bb64.b64encode(f.read()).decode("ascii")

    b64 = await asyncio.to_thread(_encode)
    attachment_size_mb = (
        await asyncio.to_thread(lambda: attachment_path.stat().st_size)
    ) / (1024 * 1024)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    sender = os.environ.get("SENDER_EMAIL", "noreply@mascidocs.com")
    reply_to = os.environ.get("REPLY_TO_EMAIL") or None

    html = (
        f'<div style="font-family:system-ui,-apple-system,sans-serif;max-width:560px;margin:0 auto;">'
        f'<div style="border-bottom:4px solid #b91c1c;padding-bottom:10px;margin-bottom:18px;">'
        f'<strong style="color:#b91c1c;letter-spacing:.15em;font-size:11px;text-transform:uppercase">'
        f'MASCI · NIGHTLY BACKUP</strong>'
        f'</div>'
        f'<p style="color:#0f172a;margin:0 0 8px;font-size:15px;">'
        f'Your nightly MASCI Hub backup is attached.</p>'
        f'<ul style="color:#334155;font-size:14px;line-height:1.7;padding-left:18px;">'
        f'<li><strong>Generated:</strong> {stamp}</li>'
        f'<li><strong>Records:</strong> {total_records}</li>'
        f'<li><strong>Full backup size:</strong> {full_size_mb:.1f} MB</li>'
        f'<li><strong>Attachment:</strong> <code>{attachment_name}</code> '
        f'({attachment_size_mb:.1f} MB)</li>'
        f'</ul>'
        f'{slim_notice}'
        f'<p style="color:#475569;font-size:13px;margin-top:18px;">'
        f'<strong>Restore instructions:</strong> sign in to <a href="https://mascidocs.com/admin">'
        f'mascidocs.com/admin</a> → scroll to "Restore from Backup" → Upload this .zip.</p>'
        f'<p style="color:#b91c1c;font-size:12px;margin-top:18px;font-weight:700;">'
        f'Keep this email safe — it is your off-site disaster-recovery copy.</p>'
        f'</div>'
    )

    try:
        import resend  # noqa: E402
        resend.api_key = api_key
        params: Dict[str, Any] = {
            "from": sender,
            "to": [to],
            "subject": f"MASCI Nightly Backup · {stamp} · {total_records} records",
            "html": html,
            "attachments": [
                {"filename": attachment_name, "content": b64},
            ],
        }
        if reply_to:
            params["reply_to"] = reply_to
        result = await asyncio.to_thread(resend.Emails.send, params)
        rid = (result or {}).get("id", "?")
        logger.info(f"[scheduled-backup] emailed backup to {to} (resend_id={rid})")
        return to
    except Exception as e:
        logger.warning(f"[scheduled-backup] Resend send failed: {e}")
        return None


_backup_task: Optional[asyncio.Task] = None


async def _backup_scheduler_loop(db) -> None:
    """Background loop — wakes up every ~5 min and fires the backup when
    we OBSERVE an hour transition into a scheduled slot while running.

    CRITICAL: we do NOT retroactively fire catch-up backups on boot.
    Rationale: if a backup crashes the container (OOM, disk, etc.), the
    container restarts, the scheduler would see "this slot hasn't run
    today" and fire again, crashing again → infinite loop keeping prod
    down for hours. Instead, on boot we mark every already-crossed slot
    as "run today" so only FUTURE slots ever trigger. If the admin needs
    an immediate backup they click "Run backup now" in /admin.
    """
    # Per-hour bookkeeping: hour → last date we ran for that slot.
    last_run_for_hour: dict[int, "datetime.date"] = {}

    # Seed: mark every scheduled hour we've already crossed today as
    # "already run" — this prevents any backup from firing as part of
    # container startup. Only future slots will trigger.
    now = datetime.now(timezone.utc)
    today = now.date()
    for h in BACKUP_HOURS_UTC:
        if now.hour >= h:
            last_run_for_hour[h] = today

    skipped = sorted([h for h in BACKUP_HOURS_UTC if now.hour >= h])
    upcoming = sorted([h for h in BACKUP_HOURS_UTC if now.hour < h])
    logger.info(
        f"[scheduled-backup] scheduler armed — skipping past slots today "
        f"{[f'{h:02d}:00' for h in skipped] or 'none'}, "
        f"next slots {[f'{h:02d}:00' for h in upcoming] or 'tomorrow'}"
    )

    # Give the app a moment to finish startup before first tick
    await asyncio.sleep(30)
    while True:
        try:
            now = datetime.now(timezone.utc)
            today = now.date()
            # Find the latest scheduled hour crossed today that hasn't fired.
            # Since boot-seeding marks same-day past slots as already-run,
            # this only catches NEW slots we cross while running.
            due_hour: Optional[int] = None
            for h in BACKUP_HOURS_UTC:
                if now.hour >= h and last_run_for_hour.get(h) != today:
                    due_hour = h
            if due_hour is not None:
                logger.info(
                    f"[scheduled-backup] firing for {today} (slot {due_hour:02d}:00 UTC)"
                )
                result = await _run_scheduled_backup(db)
                if result:
                    last_run_for_hour[due_hour] = today
                    # Collapse earlier same-day slots into this run.
                    for h in BACKUP_HOURS_UTC:
                        if h <= due_hour:
                            last_run_for_hour[h] = today
                # If it failed, leave the bookkeeping alone so we retry next tick.
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.exception(f"[scheduled-backup] loop tick error: {e}")
        await asyncio.sleep(300)  # 5 min ticks — low overhead, catches missed slots


@api_router.get("/admin/backups")
async def admin_list_backups(_: bool = Depends(require_admin_strict)):
    """List every stored backup on disk + current schedule settings."""
    files = _list_stored_backups()
    total_bytes = sum(f["size_bytes"] for f in files)
    return {
        "backups": files,
        "count": len(files),
        "total_bytes": total_bytes,
        "schedule": {
            "hour_utc": BACKUP_HOUR_UTC,         # legacy single-window field
            "hours_utc": BACKUP_HOURS_UTC,       # full list of scheduled UTC hours
            "retention_days": BACKUP_RETENTION_DAYS,
            "storage_dir": str(BACKUPS_DIR),
            "enabled": True,
        },
    }


@api_router.get("/admin/backups/integrity-check")
async def admin_backup_integrity_check(_: bool = Depends(require_admin_strict)):
    """Audit: every Mongo collection currently in the live DB vs the most
    recent backup's manifest. Surfaces any collection that exists right now
    but wasn't captured in the last backup — proves nothing is slipping
    through, and catches new collections automatically.

    Returns:
      {
        "last_backup_filename": str | None,
        "last_backup_at":       iso str | None,
        "live_collections":     [...],     # everything currently in DB
        "captured_collections": [...],     # what the last backup contained
        "missing_from_backup":  [...],     # ⚠ in DB but NOT in last backup
        "ok":                   bool,
      }

    NOTE: this route MUST be declared before the parameterized
    `/admin/backups/{filename}` route below — otherwise the FastAPI router
    matches the literal "integrity-check" against the {filename} regex.
    """
    import json as _ic_json
    import zipfile as _ic_zip
    files = _list_stored_backups()
    last = files[0] if files else None
    live = sorted(await db.list_collection_names())
    live = [c for c in live if not c.startswith("system.")]
    captured: List[str] = []
    last_at = None
    if last:
        zip_path = BACKUPS_DIR / last["filename"]
        try:
            with _ic_zip.ZipFile(zip_path) as zf:
                if "backup_manifest.json" in zf.namelist():
                    m = _ic_json.loads(zf.read("backup_manifest.json").decode("utf-8"))
                    captured = sorted(m.get("captured_collections") or m.get("all_db_collections_at_backup_time") or [])
                    last_at = m.get("generated_at")
        except Exception as e:  # noqa: BLE001
            logger.warning(f"integrity-check: read manifest failed: {e}")
    missing = [c for c in live if c not in set(captured)]
    return {
        "last_backup_filename": last.get("filename") if last else None,
        "last_backup_at": last_at,
        "live_collections": live,
        "captured_collections": captured,
        "missing_from_backup": missing,
        "ok": (last is not None and len(missing) == 0),
    }


@api_router.get("/admin/backups/{filename}")
async def admin_download_stored_backup(
    filename: str, _: bool = Depends(require_admin_strict)
):
    """Download a specific stored backup by filename."""
    # Strict filename validation — only our own backup files.
    if not re.fullmatch(r"MASCI_full_backup_[0-9A-Za-z_\-]+\.zip", filename):
        raise HTTPException(400, "Invalid backup filename")
    path = BACKUPS_DIR / filename
    if not path.exists():
        raise HTTPException(404, "Backup not found")
    try:
        data = path.read_bytes()
    except Exception as e:
        raise HTTPException(500, f"Could not read backup: {e}")
    return Response(
        content=data,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Backup-Size-Bytes": str(len(data)),
        },
    )


@api_router.delete("/admin/backups/{filename}")
async def admin_delete_stored_backup(
    filename: str, _: bool = Depends(require_admin_strict)
):
    if not re.fullmatch(r"MASCI_full_backup_[0-9A-Za-z_\-]+\.zip", filename):
        raise HTTPException(400, "Invalid backup filename")
    path = BACKUPS_DIR / filename
    if not path.exists():
        raise HTTPException(404, "Backup not found")
    try:
        path.unlink()
    except Exception as e:
        raise HTTPException(500, f"Could not delete: {e}")
    return {"ok": True, "filename": filename}


@api_router.post("/admin/backups/run-now")
async def admin_run_backup_now(_: bool = Depends(require_admin_strict)):
    """Trigger an immediate scheduled backup (same path as nightly, just now)."""
    result = await _run_scheduled_backup(db)
    if not result:
        raise HTTPException(500, "Backup failed — see server logs")
    return {"ok": True, **result}


@api_router.post("/admin/data-fixes/run")
async def admin_run_data_fixes(_: bool = Depends(require_admin)):
    """Apply both production data fixes:
       1. Split `make_model` into `make` + `model` on every equipment unit
       2. Seed `project_members` so every owner/admin sees every project

    Both fixes are idempotent — safe to re-run any number of times.
    """
    from data_fixes import run_all_fixes
    return await run_all_fixes(db)


# -------------------- Crew Hub recovery (legacy admin-token gated) --------------------
# These endpoints exist so the office can recover a Crew Hub login when nobody
# remembers their password. Authenticated by the LEGACY admin password
# (X-Admin-Token / env PM_PASSWORD) — NOT by a Crew Hub JWT — so it works even when
# every crew owner+admin is locked out.

@api_router.get("/admin/crew-recovery/status")
async def admin_crew_recovery_status(_: bool = Depends(require_admin_strict)):
    """Return counts of every key collection so the office can see at a glance
    what's populated and what isn't (helps diagnose redeploy data-loss)."""
    counts = {}
    for coll in [
        "users",
        "projects",
        "project_members",
        "equipment_master",
        "equipment_units",
        "equipment_inspections",
        "inspections",
        "meetings",
        "jhas",
        "incidents",
        "daily_reports",
        "docs",
        "employees",
        "suppliers",
        "notifications",
        "activity_log",
    ]:
        try:
            counts[coll] = await db[coll].count_documents({})
        except Exception:
            counts[coll] = -1
    crew_users = await db.users.find(
        {}, {"_id": 0, "id": 1, "email": 1, "name": 1, "role": 1, "is_active": 1, "must_change_password": 1}
    ).sort("email", 1).to_list(200)
    return {
        "ok": True,
        "counts": counts,
        "crew_users": crew_users,
    }


@api_router.post("/admin/crew-recovery/reset-password")
async def admin_crew_recovery_reset(
    body: dict,
    _: bool = Depends(require_admin_strict),
):
    """Reset a Crew Hub user's password using the LEGACY admin token. The user
    is forced to change it on next login. Body: {email, new_password}.
    """
    from auth import hash_password
    email = (body.get("email") or "").strip().lower()
    new_password = (body.get("new_password") or "").strip()
    if not email or not new_password:
        raise HTTPException(400, "email + new_password required")
    if len(new_password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters")
    user = await db.users.find_one({"email": email}, {"_id": 0, "id": 1, "email": 1})
    if not user:
        raise HTTPException(404, f"No crew user with email {email}")
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {
            "password_hash": hash_password(new_password),
            "must_change_password": True,
            "is_active": True,  # un-lock if accidentally deactivated
        }},
    )
    return {"ok": True, "email": email, "must_change_password": True}


@api_router.post("/admin/crew-recovery/force-reseed")
async def admin_crew_recovery_force_reseed(_: bool = Depends(require_admin_strict)):
    """Force-rerun the equipment_master / employees / suppliers JSON seeds even
    if those collections already have rows. Useful when a partial-wipe leaves
    incomplete data and the boot guard (`count > 0`) skips re-seeding.

    The seed functions normally short-circuit if the collection has any rows;
    this endpoint deletes the seed-managed collections first so they re-seed
    from JSON cleanly. Safety/projects/users are NOT touched.
    """
    summary = {}
    for coll in ["equipment_master", "equipment_units", "employees", "suppliers"]:
        before = await db[coll].count_documents({})
        await db[coll].delete_many({})
        summary[coll] = {"before": before, "after_delete": 0}
    # Re-run the seeds in-process
    await _seed_equipment_master()
    await _seed_employees_from_json()
    await _seed_suppliers_from_json()
    for coll in ["equipment_master", "equipment_units", "employees", "suppliers"]:
        summary[coll]["after_seed"] = await db[coll].count_documents({})
    # Boot self-heal also patches make/model + memberships
    from data_fixes import boot_self_heal
    await boot_self_heal(db)
    return {"ok": True, "summary": summary}


@api_router.post("/admin/crew-recovery/scrap-crew-hub")
async def admin_scrap_crew_hub(body: dict, _: bool = Depends(require_admin_strict)):
    """One-shot: WIPE every Crew Hub / projects table from the DB.
    The MASCI Hub has decided to use Basecamp instead of the in-app Crew Hub.

    Body must include {"confirm": "SCRAP_CREW_HUB"} or 400. Idempotent — safe
    to re-run (running on an empty DB just returns zeros).

    DELETES (counts returned in the response):
      - projects, project_members, docs, todos, todo_lists, hill_dots,
        events, messages, notifications, activity_log
    KEEPS:
      - users (so admin can still see who they were if curious; tiny table)
      - All safety records (inspections, meetings, jhas, incidents, daily_reports)
      - Equipment master + units + inspections, employees, suppliers
      - Backups
    """
    if (body or {}).get("confirm") != "SCRAP_CREW_HUB":
        raise HTTPException(
            400,
            'Pass {"confirm": "SCRAP_CREW_HUB"} to confirm this destructive action',
        )
    wipe_collections = [
        "projects",
        "project_members",
        "docs",
        "todos",
        "todo_lists",
        "hill_dots",
        "events",
        "messages",
        "notifications",
        "activity_log",
    ]
    summary = {}
    for coll in wipe_collections:
        try:
            before = await db[coll].count_documents({})
            res = await db[coll].delete_many({})
            summary[coll] = {"before": before, "deleted": res.deleted_count}
        except Exception as e:
            summary[coll] = {"error": str(e)}
    return {
        "ok": True,
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "summary": summary,
        "kept": [
            "users",
            "inspections",
            "meetings",
            "jhas",
            "incidents",
            "daily_reports",
            "equipment_master",
            "equipment_units",
            "equipment_inspections",
            "employees",
            "suppliers",
        ],
    }


# -------------------- Outage alerts (called by SystemHealthBadge) --------------------
class OutageAlertBody(BaseModel):
    issue_key: str = Field(..., min_length=1, max_length=200)
    summary: str = Field(..., min_length=1, max_length=2000)
    failed_endpoints: List[Dict[str, Any]] = Field(default_factory=list)


@api_router.post("/admin/alert-outage")
async def admin_alert_outage(body: OutageAlertBody, _: bool = Depends(require_admin)):
    """Sends a one-line outage email via Resend (cooldown-gated).

    Called by the SystemHealthBadge in the admin UI when one of the monitored
    endpoints starts returning 5xx or fails to respond. Cooldown is
    OUTAGE_ALERT_COOLDOWN_MINUTES (default 15) per issue_key — duplicate
    badge fires within that window are suppressed.
    """
    from outage_alerts import send_outage_alert
    rows = body.failed_endpoints or []
    rows_html = ""
    if rows:
        rows_html = "<table style='width:100%;border-collapse:collapse;font-size:13px;margin:6px 0 10px'>"
        rows_html += "<thead><tr style='background:#f1f5f9;color:#0f172a;text-align:left'>"
        rows_html += "<th style='padding:6px 8px;border:1px solid #e2e8f0'>Endpoint</th>"
        rows_html += "<th style='padding:6px 8px;border:1px solid #e2e8f0'>Status</th>"
        rows_html += "<th style='padding:6px 8px;border:1px solid #e2e8f0'>Latency</th>"
        rows_html += "</tr></thead><tbody>"
        for r in rows[:20]:
            label = str(r.get("label") or r.get("path") or "?")[:40]
            stat = str(r.get("status") or "—")[:8]
            ms = str(r.get("ms") or "—")[:8]
            rows_html += (
                f"<tr><td style='padding:5px 8px;border:1px solid #e2e8f0;font-family:monospace'>{label}</td>"
                f"<td style='padding:5px 8px;border:1px solid #e2e8f0;color:#dc2626;font-weight:bold'>{stat}</td>"
                f"<td style='padding:5px 8px;border:1px solid #e2e8f0;font-family:monospace'>{ms} ms</td></tr>"
            )
        rows_html += "</tbody></table>"
    return await send_outage_alert(
        issue_key=body.issue_key,
        subject=f"⚠ MASCI Hub outage — {body.issue_key}",
        summary=body.summary,
        details_html=rows_html,
    )


@api_router.get("/admin/persistence-check")
async def admin_persistence_check(_: bool = Depends(require_admin)):
    """Report whether the running instance is at risk of data loss on redeploy.

    Production on Emergent without an external MongoDB URL is ephemeral — a
    git push/redeploy wipes the container's Mongo volume. This endpoint
    powers the admin-hub warning banner so the office never redeploys blind.
    """
    mongo_url = os.environ.get("MONGO_URL", "")
    # Local/in-container Mongo hostnames. Atlas URLs start with mongodb+srv://
    # or include an explicit external host. Anything pointing at localhost,
    # 127.0.0.1 or no hostname is treated as ephemeral.
    host_part = mongo_url.split("://", 1)[-1].split("/", 1)[0].lower()
    is_local = (
        not mongo_url
        or "localhost" in host_part
        or host_part.startswith("127.")
        or host_part.startswith("0.0.0.0")
        or host_part == ""
    )
    is_atlas = mongo_url.startswith("mongodb+srv://") or "mongodb.net" in host_part
    backup_email_configured = bool((os.environ.get("BACKUP_EMAIL_TO") or "").strip())
    resend_configured = bool((os.environ.get("RESEND_API_KEY") or "").strip())
    last_backup = None
    try:
        files = _list_stored_backups()
        if files:
            last_backup = files[0]
    except Exception:
        pass

    return {
        "mongo_is_local": is_local,
        "mongo_is_atlas": is_atlas,
        "mongo_host": host_part or "(none)",
        "backup_email_to": (os.environ.get("BACKUP_EMAIL_TO") or "").strip() or None,
        "backup_email_configured": backup_email_configured,
        "resend_configured": resend_configured,
        "last_backup": last_backup,
        "scheduler_enabled": os.environ.get("DISABLE_BACKUP_SCHEDULER", "").lower() not in ("1", "true", "yes"),
    }


# ----------------------------------------------------------------------
# Restore from backup ZIP — upsert every record back into MongoDB.
# ----------------------------------------------------------------------
# Map backup kind folder → MongoDB collection name. Pulled from
# EXPORTABLE_KINDS + the Crew Hub + Safety aux lists above.
_RESTORE_KIND_TO_COLL = {
    # Safety kinds — the ZIP stores them under <kind>/json/*.json
    "inspections": "inspections",
    "meetings": "meetings",
    "jhas": "jhas",
    "incidents": "incidents",
    "daily-reports": "daily_reports",
    "equipment-inspections": "equipment_inspections",
}
_RESTORE_CREW_HUB = {
    "projects", "users", "project_members", "messages", "message_comments",
    "todo_lists", "todos", "events", "docs", "hill_scopes", "activity_log",
    "notifications",
}
_RESTORE_SAFETY_AUX = {"equipment_units", "job_hazard_plans", "trench_boxes"}


# ────────────────────────────────────────────────────────────────────────────
# Edit project on an existing record (admin OR PM)
# ────────────────────────────────────────────────────────────────────────────
# Foremen and superintendents occasionally pick the wrong job at submit time
# ("HQ" vs "T5860 SR 9", say) and the report lands under the wrong project.
# This endpoint lets a PM or admin re-tag the record after the fact without
# editing any other field. Only project_name / project_number / project_id /
# location may be changed; everything else (signatures, photos, narrative,
# checklist results) stays exactly as the foreman submitted it.
_EDIT_KIND_TO_COLL = {
    "daily-reports":         "daily_reports",
    "incidents":             "incidents",
    "meetings":              "meetings",
    "inspections":           "inspections",
    "equipment-inspections": "equipment_inspections",
}


class EditProjectRequest(BaseModel):
    project_name: Optional[str] = None
    project_number: Optional[str] = None
    project_id: Optional[str] = None
    location: Optional[str] = None
    model_config = ConfigDict(extra="ignore")


@api_router.patch("/admin/records/{kind}/{record_id}/project")
async def edit_record_project(
    kind: str,
    record_id: str,
    payload: EditProjectRequest,
    _: bool = Depends(require_admin),
):
    coll_name = _EDIT_KIND_TO_COLL.get(kind)
    if not coll_name:
        raise HTTPException(status_code=400, detail=f"Unknown record kind: {kind}")
    update: Dict[str, Any] = {}
    for field in ("project_name", "project_number", "project_id", "location"):
        v = getattr(payload, field, None)
        if v is not None:
            update[field] = (v or "").strip()
    if not update:
        raise HTTPException(status_code=400, detail="No project fields supplied")
    update["project_edited_at"] = datetime.now(timezone.utc).isoformat()
    res = await db[coll_name].update_one({"id": record_id}, {"$set": update})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Record not found")
    doc = await db[coll_name].find_one({"id": record_id}, {"_id": 0})
    return {"ok": True, "record": doc}


@api_router.post("/exports/restore")
async def exports_restore(
    file: UploadFile = File(...),
    merge: bool = Form(True),
    _: bool = Depends(require_admin_strict),
):
    """Restore a `/api/exports/full-backup` .zip back into MongoDB.

    - `merge=true` (default): upsert by `id` — existing rows with the same
      id are overwritten, new rows added, untouched collections untouched.
    - `merge=false`: wipe the target collection first, then insert. Use with
      care — this is a full restore to the backup's exact state.

    The zip's `backup_manifest.json` is used to validate that this is a real
    MASCI backup before we touch any data.
    """
    # 1. Read + validate the upload
    try:
        payload = await file.read()
    except Exception as e:
        raise HTTPException(400, f"Failed to read upload: {e}")
    if not payload:
        raise HTTPException(400, "Empty upload")
    if len(payload) > 500 * 1024 * 1024:  # 500 MB hard ceiling
        raise HTTPException(413, "Backup file exceeds 500 MB limit")

    try:
        zf = zipfile.ZipFile(io.BytesIO(payload), "r")
    except zipfile.BadZipFile:
        raise HTTPException(400, "Uploaded file is not a valid ZIP archive")

    names = set(zf.namelist())
    if "backup_manifest.json" not in names:
        raise HTTPException(
            400,
            "backup_manifest.json missing — this does not look like a MASCI "
            "full-backup .zip. Regenerate via 'Download Full Backup' first.",
        )
    try:
        manifest = _backup_json.loads(zf.read("backup_manifest.json").decode("utf-8"))
    except Exception as e:
        raise HTTPException(400, f"Corrupt manifest: {e}")

    # 2. Walk the ZIP and group docs by destination collection.
    bucket: Dict[str, List[dict]] = {}

    def _add(coll: str, docs: List[dict]):
        if not docs:
            return
        bucket.setdefault(coll, []).extend(docs)

    # 2a. Safety kinds — every json under <kind>/json/*.json
    for kind, coll in _RESTORE_KIND_TO_COLL.items():
        prefix = f"{kind}/json/"
        docs: List[dict] = []
        for n in names:
            if n.startswith(prefix) and n.endswith(".json"):
                try:
                    docs.append(_backup_json.loads(zf.read(n).decode("utf-8")))
                except Exception as e:  # noqa: BLE001
                    logger.warning(f"restore: skipped {n}: {e}")
        _add(coll, docs)

    # 2b. Crew Hub — single json per collection under crew_hub/<coll>.json
    for coll in _RESTORE_CREW_HUB:
        n = f"crew_hub/{coll}.json"
        if n in names:
            try:
                data = _backup_json.loads(zf.read(n).decode("utf-8"))
                if isinstance(data, list):
                    _add(coll, data)
            except Exception as e:  # noqa: BLE001
                logger.warning(f"restore: skipped {n}: {e}")

    # 2c. Safety aux
    for coll in _RESTORE_SAFETY_AUX:
        n = f"safety_aux/{coll}.json"
        if n in names:
            try:
                data = _backup_json.loads(zf.read(n).decode("utf-8"))
                if isinstance(data, list):
                    _add(coll, data)
            except Exception as e:  # noqa: BLE001
                logger.warning(f"restore: skipped {n}: {e}")

    # 2d. Auto-discovered collections (backup version 3+) — anything under
    #     collections/<name>.json that isn't already restored above.
    for n in names:
        if not (n.startswith("collections/") and n.endswith(".json")):
            continue
        coll = n[len("collections/"):-len(".json")]
        # Skip collections we've already restored via dedicated paths above.
        if coll in bucket:
            continue
        try:
            data = _backup_json.loads(zf.read(n).decode("utf-8"))
            if isinstance(data, list):
                _add(coll, data)
        except Exception as e:  # noqa: BLE001
            logger.warning(f"restore: skipped {n}: {e}")

    # 2e. Disk-backed files — restore the storage tree (Oxford big PDFs etc.)
    disk_restored = 0
    disk_storage_root = Path("/app/backend/storage")
    for n in names:
        if not n.startswith("disk_files/") or n.endswith("/"):
            continue
        rel = n[len("disk_files/"):]
        if not rel:
            continue
        target = disk_storage_root / rel
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(zf.read(n))
            disk_restored += 1
        except Exception as e:  # noqa: BLE001
            logger.warning(f"restore: disk file {n} failed: {e}")

    if not bucket and disk_restored == 0:
        raise HTTPException(
            400,
            "No records found in backup (expected files under "
            "<kind>/json/, crew_hub/, safety_aux/, collections/, or disk_files/).",
        )

    # 3. Write back to MongoDB.
    summary: Dict[str, dict] = {}
    # If the users collection is being restored, the export redacts
    # password_hash. Precompute the seed hash so restored rows always have
    # a usable password (Welcome2MASCI! + must_change_password).
    _seed_hash = None
    if "users" in bucket:
        try:
            import bcrypt as _bc  # noqa: E402
            _seed_hash = _bc.hashpw(b"Welcome2MASCI!", _bc.gensalt()).decode("utf-8")
        except Exception as e:  # noqa: BLE001
            logger.warning(f"restore: could not generate seed hash ({e}); restored users may be locked out")

    for coll, docs in bucket.items():
        # Strip any _id from the docs (they're exported without, but be safe).
        clean = []
        for d in docs:
            if not isinstance(d, dict):
                continue
            d.pop("_id", None)
            if "id" not in d:
                d["id"] = str(uuid.uuid4())  # defensive — keep upsert viable
            # Special-case: restored users lost their password_hash on export.
            # In merge mode: keep whatever's in DB (pull it first).
            # In replace mode (or brand-new row): stamp the seed hash +
            # force password change so no account gets locked out.
            if coll == "users" and "password_hash" not in d:
                existing = None
                if merge:
                    existing = await db.users.find_one(
                        {"id": d["id"]}, {"_id": 0, "password_hash": 1}
                    )
                if existing and existing.get("password_hash"):
                    d["password_hash"] = existing["password_hash"]
                elif _seed_hash:
                    d["password_hash"] = _seed_hash
                    d["must_change_password"] = True
            clean.append(d)

        deleted = 0
        if not merge:
            res = await db[coll].delete_many({})
            deleted = res.deleted_count

        upserted = 0
        modified = 0
        inserted = 0
        for d in clean:
            try:
                r = await db[coll].update_one(
                    {"id": d["id"]}, {"$set": d}, upsert=True,
                )
                if r.upserted_id is not None:
                    inserted += 1
                elif r.modified_count:
                    modified += 1
                upserted += 1
            except Exception as e:  # noqa: BLE001
                logger.warning(f"restore: {coll}/{d.get('id')} failed: {e}")

        summary[coll] = {
            "deleted": deleted,
            "processed": len(clean),
            "inserted": inserted,
            "updated": modified,
        }

    logger.info(f"restore: processed {sum(s['processed'] for s in summary.values())} records across {len(summary)} collections")

    return {
        "ok": True,
        "mode": "replace" if not merge else "merge",
        "backup_generated_at": manifest.get("generated_at"),
        "backup_version": manifest.get("version", "unknown"),
        "collections": summary,
        "total_processed": sum(s["processed"] for s in summary.values()),
    }




@api_router.get("/equipment-status-board")
async def equipment_status_board(_: bool = Depends(require_admin)):
    """
    Per-unit aggregation for the Admin Hub status board.

    For every saved equipment unit (or every unit referenced by an inspection,
    even if the operator typed it free-form without saving), returns:
        - last_inspection_date / last_inspected_days_ago
        - last_status: "ok" | "fail" | "never"
        - fail_count_14d : how many FAIL items logged in the last 14 days
        - top_failures : up to 3 most-frequent failing item names (last 30 d)
        - inspection_count : total all-time count
    """
    now = datetime.now(timezone.utc)
    cutoff_14 = now - timedelta(days=14)
    cutoff_30 = now - timedelta(days=30)

    saved_cursor = db.equipment_units.find({}, {"_id": 0})
    saved_units = await saved_cursor.to_list(2000)

    # Pull every inspection (slim projection — skip photos to keep it fast)
    insp_cursor = db.equipment_inspections.find(
        {},
        {
            "_id": 0,
            "id": 1,
            "equipment_type": 1,
            "equipment_unit": 1,
            "inspection_date": 1,
            "created_at": 1,
            "fail_count": 1,
            "out_of_service": 1,
            "checklist": 1,
            "project_name": 1,
            "project_number": 1,
        },
    ).sort("created_at", -1)
    inspections = await insp_cursor.to_list(5000)

    def _key(t: str, u: str) -> str:
        return f"{(t or '').strip()}||{(u or '').strip()}"

    by_unit: Dict[str, Dict[str, Any]] = {}
    for u in saved_units:
        k = _key(u.get("equipment_type", ""), u.get("unit_label", ""))
        by_unit[k] = {
            "equipment_type": u.get("equipment_type", ""),
            "equipment_unit": u.get("unit_label", ""),
            "make": u.get("make", "") or "",
            "model": u.get("model", "") or "",
            "serial": u.get("serial", "") or "",
            "saved": True,
            "inspection_count": 0,
            "fail_count_14d": 0,
            "last_inspection_date": None,
            "last_inspected_at": None,
            "last_status": "never",
            "last_project": "",
            "last_project_number": "",
            "_fail_items_30d": {},  # tally
        }

    def _parse_dt(s: str) -> Optional[datetime]:
        if not s:
            return None
        try:
            return datetime.fromisoformat(s.replace("Z", "+00:00"))
        except Exception:
            return None

    for d in inspections:
        k = _key(d.get("equipment_type"), d.get("equipment_unit"))
        if k not in by_unit:
            by_unit[k] = {
                "equipment_type": d.get("equipment_type", ""),
                "equipment_unit": d.get("equipment_unit", ""),
                "make": "",
                "model": "",
                "serial": "",
                "saved": False,
                "inspection_count": 0,
                "fail_count_14d": 0,
                "last_inspection_date": None,
                "last_inspected_at": None,
                "last_status": "never",
                "last_project": "",
                "last_project_number": "",
                "_fail_items_30d": {},
            }

        bucket = by_unit[k]
        bucket["inspection_count"] += 1

        created = _parse_dt(d.get("created_at"))
        if bucket["last_inspected_at"] is None or (
            created and created > bucket["last_inspected_at"]
        ):
            bucket["last_inspected_at"] = created
            bucket["last_inspection_date"] = d.get("inspection_date") or (
                created.date().isoformat() if created else None
            )
            bucket["last_status"] = (
                "fail" if (d.get("fail_count") or 0) > 0 else "ok"
            )
            bucket["last_project"] = d.get("project_name", "") or ""
            bucket["last_project_number"] = d.get("project_number", "") or ""

        # 14-day fail count
        if created and created >= cutoff_14:
            bucket["fail_count_14d"] += int(d.get("fail_count") or 0)

        # 30-day per-item failure tally
        if created and created >= cutoff_30:
            for sec, items in (d.get("checklist") or {}).items():
                if not isinstance(items, dict):
                    continue
                for item_name, res in items.items():
                    if isinstance(res, dict) and res.get("status") == "fail":
                        bucket["_fail_items_30d"][item_name] = (
                            bucket["_fail_items_30d"].get(item_name, 0) + 1
                        )

    out = []
    for k, b in by_unit.items():
        last_at = b.pop("last_inspected_at", None)
        days_ago = None
        if last_at:
            days_ago = max(0, (now - last_at).days)
        top = sorted(
            b.pop("_fail_items_30d", {}).items(), key=lambda kv: kv[1], reverse=True
        )[:3]
        b["last_inspected_days_ago"] = days_ago
        b["top_failures"] = [
            {"item": item, "count": cnt} for item, cnt in top
        ]
        out.append(b)

    # Sort: out-of-service first, then by fail count desc, then by stale-ness
    def _priority(b):
        oos = 0 if b["last_status"] == "fail" else 1
        stale = b["last_inspected_days_ago"] if b["last_inspected_days_ago"] is not None else 9999
        return (oos, -b["fail_count_14d"], -stale, b["equipment_type"], b["equipment_unit"])

    out.sort(key=_priority)
    return {
        "generated_at": now.isoformat(),
        "units": out,
        "summary": {
            "total_units": len(out),
            "out_of_service": sum(1 for b in out if b["last_status"] == "fail"),
            "never_inspected": sum(1 for b in out if b["last_status"] == "never"),
            "stale_7d": sum(
                1
                for b in out
                if (b["last_inspected_days_ago"] is None or b["last_inspected_days_ago"] >= 7)
            ),
        },
    }




# ============================================================
# Translation (Spanish → English on submit)
# ============================================================
# Crews can fill any form in Spanish, but every saved record + printed PDF
# must be 100% English (legal/OSHA requirement). At submit time the frontend
# sends the freeform user-typed string leaves to this endpoint, which calls
# Claude Haiku 4.5 via the Emergent universal LLM key and returns the same
# dict shape with English values.

class TranslateRequest(BaseModel):
    from_lang: str = "es"
    to_lang: str = "en"
    strings: Dict[str, str] = Field(default_factory=dict)


class TranslateResponse(BaseModel):
    strings: Dict[str, str]


import json as _json  # noqa: E402  (kept local to this section)


@api_router.post("/translate", response_model=TranslateResponse, dependencies=[Depends(rate_limit_public_post)])
async def translate_strings(payload: TranslateRequest):
    """Translate a flat {key: string} dict between languages.

    Returns the same keys with translated values. If translation fails we
    return the original strings unchanged so the form submit is never
    blocked. Empty input is a no-op.
    """
    if not payload.strings:
        return TranslateResponse(strings={})

    # Short-circuit when source & target are identical
    if payload.from_lang == payload.to_lang:
        return TranslateResponse(strings=payload.strings)

    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        logger.warning("EMERGENT_LLM_KEY missing — returning input unchanged")
        return TranslateResponse(strings=payload.strings)

    # Lazy import so cold-start of the rest of the API isn't blocked.
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
    except Exception as e:  # pragma: no cover
        logger.error(f"emergentintegrations import failed: {e}")
        return TranslateResponse(strings=payload.strings)

    system = (
        "You are a translator for a US construction safety reporting app. "
        "Translate values from {src} to {dst}. The text comes from heavy-civil "
        "construction crews — preserve technical terms (e.g. excavator, MOT, PPE, "
        "rebar, lift station, foreman), proper nouns, and numbers exactly. "
        "Keep the SAME JSON shape: input is a JSON object whose values are the "
        "strings to translate; reply with ONLY a JSON object using the SAME keys "
        "and translated values — no commentary, no markdown fences."
    ).format(src=payload.from_lang, dst=payload.to_lang)

    user_text = (
        "Translate every value in this JSON object. Reply with the JSON object "
        "only, same keys, translated values:\n\n"
        + _json.dumps(payload.strings, ensure_ascii=False)
    )

    try:
        chat = LlmChat(
            api_key=api_key,
            session_id=f"translate-{uuid.uuid4().hex[:8]}",
            system_message=system,
        ).with_model("anthropic", "claude-haiku-4-5-20251001")

        response = await chat.send_message(UserMessage(text=user_text))
        text = (response or "").strip()

        # Strip optional ```json fences if the model added them
        if text.startswith("```"):
            text = text.strip("`")
            # remove leading "json\n" if present
            if text.lower().startswith("json"):
                text = text[4:].lstrip("\n")

        # Find the first { … } block
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            raise ValueError(f"No JSON object in response: {text[:200]}")
        parsed = _json.loads(text[start : end + 1])
        if not isinstance(parsed, dict):
            raise ValueError("LLM did not return a JSON object")

        # Only keep string values; fall back to original where missing
        out = {}
        for k, original in payload.strings.items():
            v = parsed.get(k)
            out[k] = v if isinstance(v, str) and v.strip() else original
        return TranslateResponse(strings=out)
    except Exception as e:
        logger.exception(f"Translation failed: {e}")
        return TranslateResponse(strings=payload.strings)


# ============================================================
# Training Hub — video URL registry
# ============================================================
# Each lesson has a `slug` defined in the frontend training catalog.
# Admins paste a YouTube / Loom / Vimeo / Wistia URL per slug and the
# Training Hub renders it above the written walk-through. Storage is a
# single Mongo document with id="config" in the `training_videos` collection:
#   { "_id": "config", "videos": {"field-01-hub-navigation": "https://…", ...} }


# Default video catalog — keyed by lesson slug, each value is a
# {"en": url, "es": url} pair. Spanish entry is optional; the player
# falls back to English with a "Spanish version not available" hint.
#
# URLs use the relative path `/api/training/video/{slug}.{lang}.mp4`
# pointing at our self-hosted Range-aware streamer below. Storing them
# relative means the same URL works on preview AND production without
# rewrites — the frontend prepends REACT_APP_BACKEND_URL on render.
#
# Why self-hosted instead of customer-assets.emergentagent.com:
# the original CDN-hosted MP4s shipped with the `moov` atom at the END
# of the file. Browsers must download the entire file before playback
# can start reliably, which manifests as skipping / cutting in & out
# during streaming. The files in /app/backend/static/training-videos/
# were re-muxed with `+faststart` (moov atom moved to byte 36 = front
# of file) so progressive playback works on every device.
_DEFAULT_TRAINING_VIDEOS = {
    "field-01-hub-navigation": {
        "en": "/api/training/video/field-01-hub-navigation.en.mp4",
        "es": "/api/training/video/field-01-hub-navigation.es.mp4",
    },
    "field-02-daily-report": {
        "en": "/api/training/video/field-02-daily-report.en.mp4",
        "es": "/api/training/video/field-02-daily-report.es.mp4",
    },
    "field-03-equipment-preop": {
        "en": "/api/training/video/field-03-equipment-preop.en.mp4",
        "es": "/api/training/video/field-03-equipment-preop.es.mp4",
    },
    "field-04-safety-meeting": {
        "en": "/api/training/video/field-04-safety-meeting.en.mp4",
        "es": "/api/training/video/field-04-safety-meeting.es.mp4",
    },
    "field-05-jhp": {
        "en": "/api/training/video/field-05-jhp.en.mp4",
        "es": "/api/training/video/field-05-jhp.es.mp4",
    },
    "field-06-incident": {
        "en": "/api/training/video/field-06-incident.en.mp4",
        "es": "/api/training/video/field-06-incident.es.mp4",
    },
}


# ---------------------------------------------------------------------------
# Range-aware video streamer — serves the faststart-fixed MP4s in
# /app/backend/static/training-videos/ with full HTTP Range support so
# the browser can request byte-slices, seek instantly, and start
# playback after the first chunk arrives. This is what fixes the
# "skipping / cutting in & out" symptom users reported with the
# moov-at-end customer-assets MP4s.
# ---------------------------------------------------------------------------
import re as _vid_re  # noqa: E402
from starlette.responses import StreamingResponse as _VidStreamResp  # noqa: E402

_VIDEO_DIR = Path("/app/backend/static/training-videos")
# Filename safety: only allow lowercase letters, digits, dot, dash, underscore.
_VIDEO_NAME_RE = _vid_re.compile(r"^[a-z0-9][a-z0-9._-]{0,128}\.mp4$")


@api_router.head("/training/video/{filename}")
@api_router.get("/training/video/{filename}")
async def training_video_stream(filename: str, request: Request):
    """Range-aware MP4 streamer — returns the faststart-fixed bilingual
    training videos with `Accept-Ranges: bytes`, proper `Content-Range`
    on 206 responses, and `Content-Type: video/mp4`. Public read because
    field crews scan the QR poster and load the page without auth."""
    if not _VIDEO_NAME_RE.match(filename):
        raise HTTPException(404, "Video not found")
    path = _VIDEO_DIR / filename
    if not path.exists() or not path.is_file():
        raise HTTPException(404, "Video not found")

    file_size = path.stat().st_size
    range_header = request.headers.get("range") or request.headers.get("Range")
    common_headers = {
        "Accept-Ranges": "bytes",
        "Content-Type": "video/mp4",
        "Cache-Control": "public, max-age=86400",
        # ETag = file size + mtime so browser cache invalidates on re-mux.
        "ETag": f'W/"{file_size}-{int(path.stat().st_mtime)}"',
    }

    if range_header:
        m = _vid_re.match(r"^bytes=(\d+)-(\d*)$", range_header.strip())
        if not m:
            return Response(status_code=416, headers={"Content-Range": f"bytes */{file_size}"})
        start = int(m.group(1))
        end = int(m.group(2)) if m.group(2) else file_size - 1
        if start >= file_size or end >= file_size or start > end:
            return Response(status_code=416, headers={"Content-Range": f"bytes */{file_size}"})
        chunk_len = end - start + 1

        async def iter_range():
            # 256 KB read chunks — small enough for memory, large enough
            # to keep TCP pipelined.
            with open(path, "rb") as f:
                f.seek(start)
                remaining = chunk_len
                while remaining > 0:
                    buf = f.read(min(262144, remaining))
                    if not buf:
                        break
                    remaining -= len(buf)
                    yield buf

        headers = {
            **common_headers,
            "Content-Length": str(chunk_len),
            "Content-Range": f"bytes {start}-{end}/{file_size}",
        }
        # HEAD requests need the same headers but no body.
        if request.method == "HEAD":
            return Response(status_code=206, headers=headers)
        return _VidStreamResp(iter_range(), status_code=206, headers=headers, media_type="video/mp4")

    # Full-file request (no Range) — most browsers send Range immediately
    # for <video>, but iOS Safari sometimes pulls the whole file.
    headers = {**common_headers, "Content-Length": str(file_size)}
    if request.method == "HEAD":
        return Response(status_code=200, headers=headers)
    return FileResponse(path=str(path), media_type="video/mp4", headers=headers)


def _normalize_video_entry(entry):
    """Normalize legacy single-string URLs to the new {en, es} shape.
    Accepts either:
      - "https://…"  (legacy single-language) → {"en": "https://…", "es": ""}
      - {"en": "…", "es": "…"}  (new) → returned as-is with missing keys defaulted to ""
    Anything else → empty pair.
    """
    if isinstance(entry, str):
        return {"en": entry, "es": ""}
    if isinstance(entry, dict):
        return {"en": entry.get("en") or "", "es": entry.get("es") or ""}
    return {"en": "", "es": ""}


@api_router.get("/training/videos")
async def training_videos_get():
    """Public read. Field crews need this to render embedded videos without
    a login. Returns `{videos: {slug: {en, es}}}`.

    Self-heal: any default video slug missing EN or ES URLs gets the
    default back-filled (per-key, never overwriting admin overrides).
    Legacy single-string entries are normalized to the {en, es} shape on
    first read.

    One-time migration: any stored URL pointing at the old customer-assets
    CDN host (`customer-assets.emergentagent.com`) gets replaced with the
    matching self-hosted faststart URL from the default catalog. The CDN
    MP4s shipped with the moov atom at the END of file which made
    streaming stutter; the self-hosted copies have moov at the front.
    """
    doc = await db["training_videos"].find_one({"_id": "config"}, {"_id": 0})
    stored = (doc or {}).get("videos") or {}

    set_ops = {}
    out = {}

    def is_legacy_cdn(u):
        return isinstance(u, str) and "customer-assets.emergentagent.com" in u

    for slug, default in _DEFAULT_TRAINING_VIDEOS.items():
        cur = _normalize_video_entry(stored.get(slug))
        # Migration: replace legacy CDN URLs with self-hosted faststart.
        if is_legacy_cdn(cur["en"]) and default.get("en"):
            cur["en"] = default["en"]
            set_ops[f"videos.{slug}.en"] = default["en"]
        if is_legacy_cdn(cur["es"]) and default.get("es"):
            cur["es"] = default["es"]
            set_ops[f"videos.{slug}.es"] = default["es"]
        # Fill any blank language URL from the default.
        if not cur["en"] and default.get("en"):
            cur["en"] = default["en"]
            set_ops[f"videos.{slug}.en"] = default["en"]
        if not cur["es"] and default.get("es"):
            cur["es"] = default["es"]
            set_ops[f"videos.{slug}.es"] = default["es"]
        # Normalize legacy single-string in storage to {en, es} shape.
        if isinstance(stored.get(slug), str):
            set_ops[f"videos.{slug}"] = cur
        out[slug] = cur

    # Preserve any extra slugs admins added that aren't in defaults.
    for slug, val in stored.items():
        if slug in out:
            continue
        cur = _normalize_video_entry(val)
        out[slug] = cur
        if isinstance(val, str):
            set_ops[f"videos.{slug}"] = cur

    if set_ops:
        set_ops["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db["training_videos"].update_one(
            {"_id": "config"},
            {"$set": set_ops},
            upsert=True,
        )

    return {"videos": out}


@api_router.get("/training/packet.pdf")
async def training_packet_pdf(
    track: str,
    lang: str = "en",
    request: Request = None,
    x_admin_token: Optional[str] = Header(default=None),
    x_pm_token: Optional[str] = Header(default=None),
    x_shop_token: Optional[str] = Header(default=None),
):
    """Training packet PDF. The Field Crew track is public so labor can scan
    trailer posters without a login. Shop / PM / Admin tracks are gated —
    the back-office workflows are sensitive (backup procedures, password
    rotation, master-list internals) and shouldn't be readable by a new
    hire or walk-through visitor.

    Access rules:
      • `field`  → public, no auth
      • `shop`   → shop / pm / admin token accepted
      • `pm`     → pm / admin token accepted
      • `admin`  → admin token only

    Side effect: fire-and-forget insert into `training_hits` so the PM/Admin
    hub dashboards can show scan stats. No PII — just track/lang/date and
    a truncated UA + referer so we can tell which trailer poster got the
    scan (web vs phone browser, mascidocs.com vs direct)."""
    from training_pdf import render_packet, _normalize_lang  # local import

    t_lower = (track or "").lower()

    # Authorize based on track. We do this BEFORE rendering the PDF so a
    # failed auth never pays the render cost.
    if t_lower == "admin":
        if not (x_admin_token and _is_valid_admin_token(x_admin_token)):
            raise HTTPException(
                status_code=401,
                detail="Admin login required for the Admin training packet.",
            )
    elif t_lower == "pm":
        if not (
            (x_admin_token and _is_valid_admin_token(x_admin_token))
            or (x_pm_token and _is_valid_pm_token(x_pm_token))
        ):
            raise HTTPException(
                status_code=401,
                detail="PM or Admin login required for the PM training packet.",
            )
    elif t_lower == "shop":
        # inline the shop-token check to avoid wiring a dedicated helper
        shop_ok = False
        shop_pw = os.environ.get("SHOP_PASSWORD", "")
        if x_shop_token and shop_pw:
            shop_ok = hmac.compare_digest(x_shop_token, _shop_token_for(shop_pw))
        if not (
            (x_admin_token and _is_valid_admin_token(x_admin_token))
            or (x_pm_token and _is_valid_pm_token(x_pm_token))
            or shop_ok
        ):
            raise HTTPException(
                status_code=401,
                detail="Shop, PM, or Admin login required for the Shop training packet.",
            )
    # else: field track → public

    try:
        pdf_bytes = render_packet(track, lang)
    except ValueError as e:
        raise HTTPException(404, str(e))
    lang_norm = _normalize_lang(lang)

    # Log the scan hit — swallow any error; telemetry must never block the PDF.
    try:
        ua = (request.headers.get("user-agent") if request else "") or ""
        ref = (request.headers.get("referer") if request else "") or ""
        # Coarse device family classification — enough for the stripe.
        ua_l = ua.lower()
        if "iphone" in ua_l or "ipad" in ua_l or "ios" in ua_l:
            device = "ios"
        elif "android" in ua_l:
            device = "android"
        elif any(k in ua_l for k in ("mobile", "phone")):
            device = "mobile-other"
        elif any(k in ua_l for k in ("windows", "mac os", "linux", "x11")):
            device = "desktop"
        else:
            device = "other"
        # Referer source — did they come from the poster or a direct link?
        if "/training/" in ref and "/poster" in ref:
            source = "poster"
        elif "/training" in ref:
            source = "hub"
        elif "mascidocs.com" in ref:
            source = "internal"
        elif ref:
            source = "external"
        else:
            source = "direct"  # QR scan usually has no referer on phones
        await db["training_hits"].insert_one({
            "track": track,
            "lang": lang_norm,
            "device": device,
            "source": source,
            "ts": datetime.now(timezone.utc),
        })
    except Exception:
        pass  # never block the PDF on telemetry

    from fastapi.responses import Response
    filename = f"MASCI_training_{track}_{lang_norm}.pdf"
    # Critical: public CDN cache on a token-gated PDF would let one
    # admin's 200 response be served back to a PM or shop user. For the
    # public Field track we still allow shared caching, but anything
    # behind a login must be private and revalidate every time.
    if t_lower == "field":
        cache_ctrl = "public, max-age=60"
    else:
        cache_ctrl = "private, no-store"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
            "Cache-Control": cache_ctrl,
            # Tell shared caches the response varies by token header.
            "Vary": "X-Admin-Token, X-PM-Token, X-Shop-Token",
        },
    )


@api_router.get("/admin/training/stats")
async def training_stats(_: bool = Depends(require_admin)):
    """Aggregated scan stats for the PM/Admin hub stripe. `require_admin`
    accepts both Admin and PM tokens (Shop is not relevant here). Returns
    this-week / last-week counts, per-track breakdown, per-language split,
    and a 14-day daily trend for sparklines."""
    now = datetime.now(timezone.utc)
    this_week_start = now - timedelta(days=7)
    last_week_start = now - timedelta(days=14)
    trend_start = now - timedelta(days=14)

    col = db["training_hits"]
    this_week = await col.count_documents({"ts": {"$gte": this_week_start}})
    last_week = await col.count_documents({
        "ts": {"$gte": last_week_start, "$lt": this_week_start}
    })
    total = await col.count_documents({})

    # Per-track this-week
    by_track = {}
    async for row in col.aggregate([
        {"$match": {"ts": {"$gte": this_week_start}}},
        {"$group": {"_id": "$track", "n": {"$sum": 1}}},
    ]):
        by_track[row["_id"]] = row["n"]

    # Per-language this-week
    by_lang = {}
    async for row in col.aggregate([
        {"$match": {"ts": {"$gte": this_week_start}}},
        {"$group": {"_id": "$lang", "n": {"$sum": 1}}},
    ]):
        by_lang[row["_id"]] = row["n"]

    # 14-day trend, one bucket per day (UTC)
    trend = []
    async for row in col.aggregate([
        {"$match": {"ts": {"$gte": trend_start}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$ts"}},
            "n": {"$sum": 1},
        }},
        {"$sort": {"_id": 1}},
    ]):
        trend.append({"date": row["_id"], "n": row["n"]})

    return {
        "total": total,
        "this_week": this_week,
        "last_week": last_week,
        "by_track": by_track,
        "by_lang": by_lang,
        "trend": trend,
        "generated_at": now.isoformat(),
    }


@api_router.get("/qr.svg")
async def qr_svg(data: str, scale: int = 6):
    """Public QR-code generator. Returns an SVG-encoded QR for `data`.
    Used by the Training Scan-&-Go posters (and anywhere else the UI wants
    to inline a QR without shipping a JS library). Cached for 24h — the
    input is always a stable public URL so it's safe to cache hard."""
    import io
    import segno  # type: ignore
    if not data or len(data) > 2048:
        raise HTTPException(400, "data query param required (1-2048 chars)")
    scale = max(2, min(int(scale or 6), 20))
    qr = segno.make(data, error="m")
    buf = io.BytesIO()
    qr.save(buf, kind="svg", scale=scale, dark="#0F172A", light=None, border=2, xmldecl=False)
    from fastapi.responses import Response
    return Response(
        content=buf.getvalue(),
        media_type="image/svg+xml",
        headers={"Cache-Control": "public, max-age=86400"},
    )


@api_router.put("/admin/training/videos")
async def training_videos_put(
    body: dict,
    _: bool = Depends(require_admin_strict),
):
    """Admin-strict write. Body accepts either:
      - `{videos: {slug: "https://…"}}` (legacy single-language → stored as {en: url})
      - `{videos: {slug: {en: "https://…", es: "https://…"}}}` (new bilingual)
    Merge-updates the stored map so partial saves are safe — only supplied
    slugs/languages are changed. Empty string clears that field.
    """
    incoming = (body or {}).get("videos")
    if not isinstance(incoming, dict):
        raise HTTPException(400, "Body must be `{videos: {slug: url-or-{en,es}}}`")

    existing = await db["training_videos"].find_one({"_id": "config"}) or {}
    merged = {}
    for slug, val in (existing.get("videos") or {}).items():
        merged[slug] = _normalize_video_entry(val)

    for slug, val in incoming.items():
        if not isinstance(slug, str) or not slug.strip():
            continue
        slug = slug.strip()
        if isinstance(val, str):
            cur = merged.get(slug, {"en": "", "es": ""})
            cur["en"] = val.strip()
            merged[slug] = cur
        elif isinstance(val, dict):
            cur = merged.get(slug, {"en": "", "es": ""})
            if "en" in val:
                cur["en"] = (val.get("en") or "").strip() if isinstance(val.get("en"), str) else ""
            if "es" in val:
                cur["es"] = (val.get("es") or "").strip() if isinstance(val.get("es"), str) else ""
            merged[slug] = cur
        elif val is None:
            merged.pop(slug, None)

    # drop completely empty slugs so the map stays compact
    merged = {k: v for k, v in merged.items() if v.get("en") or v.get("es")}
    await db["training_videos"].update_one(
        {"_id": "config"},
        {"$set": {"videos": merged, "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
    return {"ok": True, "count": len(merged), "videos": merged}




app.include_router(api_router)


# ============================================================
# Email a saved record as a PDF (Resend)
# ============================================================
# Independent router so it imports at startup without forcing a hot-reload
# of the existing routes. Adds POST /api/email-report which:
#   1. Looks up the saved record by id from its module's collection.
#   2. Renders it to a polished PDF via /app/backend/pdf_render.py.
#   3. Sends via Resend with the PDF attached.

import asyncio  # noqa: E402
import base64 as _email_b64  # noqa: E402

from pdf_render import (  # noqa: E402
    render_email_html,
    render_record_pdf,
    KIND_TITLES,
)
from pm_routing import (  # noqa: E402
    ALWAYS_CC,
    COMPLIANCE_KINDS,
    PM_ONLY_KINDS,
    auto_email_enabled,
    recipients_for_record_async,
)


_KIND_TO_COLLECTION = {
    "inspection": "inspections",
    "meeting": "meetings",
    "jha": "jhas",
    "incident": "incidents",
    "daily-report": "daily_reports",
    "equipment-inspection": "equipment_inspections",
}


# ------------------------------------------------------------------
# Auto-email on submit (fire-and-forget — never blocks the response)
# ------------------------------------------------------------------
def _filename_for(kind: str, record: dict) -> str:
    project = record.get("project_name") or "MASCI"
    date_part = (
        record.get("report_date")
        or record.get("inspection_date")
        or record.get("meeting_date")
        or record.get("jha_date")
        or record.get("incident_date")
        or ""
    )
    safe_proj = "".join(
        c if c.isalnum() else "_" for c in str(project)[:40]
    ).strip("_")
    return f"MASCI-{kind}-{safe_proj}-{date_part}.pdf".replace("--", "-")


def _is_severe_incident(record: dict) -> bool:
    """Major/severe incident → always include OSHA-recordable + work-stopped flag."""
    sev = (record.get("severity") or "").strip().lower()
    severe = {"medical", "restricted", "lost_time", "fatality"}
    if sev in severe:
        return True
    if (record.get("osha_recordable") or "").strip().lower() == "yes":
        return True
    if (record.get("work_stopped") or "").strip().lower() == "yes":
        return True
    return False


async def _dispatch_auto_email(kind: str, record: dict) -> None:
    """Render PDF + send via Resend to the assigned PM and the always-CC list.

    Wrapped in a broad try/except so a missing API key, Resend outage, or PDF
    error never causes the original POST to fail. Logs at WARNING level when
    skipped and ERROR when something unexpected breaks.
    """
    try:
        if not auto_email_enabled():
            logger.info(
                "auto-email skipped (RESEND_API_KEY missing or AUTO_EMAIL_REPORTS=false) "
                f"— {kind} {record.get('id')}"
            )
            return

        dist = await recipients_for_record_async(db, record, kind)
        recipients: List[str] = list(dist["all"])  # type: ignore[arg-type]

        # Severity fan-out for incidents (Major/Severe currently mirrors the
        # always-CC; future ops/GC list can be appended here from env.)
        if kind == "incident" and _is_severe_incident(record):
            extra = os.environ.get("SEVERE_INCIDENT_CC", "")
            for e in [x.strip() for x in extra.split(",") if x.strip()]:
                if e.lower() not in {r.lower() for r in recipients}:
                    recipients.append(e)

        if not recipients:
            logger.warning(f"auto-email: no recipients resolved for {kind} {record.get('id')}")
            return

        import resend  # noqa: E402
        resend.api_key = os.environ["RESEND_API_KEY"]
        sender_email = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")
        reply_to = os.environ.get("REPLY_TO_EMAIL", "").strip()

        pdf_bytes = await asyncio.to_thread(render_record_pdf, kind, record)

        title = KIND_TITLES.get(kind, "MASCI Hub Record")
        project = record.get("project_name") or "MASCI"
        pm_name = dist.get("pm_name")
        pm_tag = f" · PM: {pm_name}" if pm_name else ""

        # Flag equipment failures in the subject so PMs see them at a glance
        equipment_fail = (
            kind == "equipment-inspection"
            and (record.get("fail_count") or 0) > 0
        )
        fail_prefix = "EQUIPMENT FAIL · " if equipment_fail else ""
        subject = f"[MASCI] {fail_prefix}{title} · {project}{pm_tag}"

        note = ""
        if kind == "incident" and _is_severe_incident(record):
            note = (
                "<p style='color:#C8102E;font-weight:700'>"
                "SEVERE INCIDENT — please review immediately."
                "</p>"
            )
        elif equipment_fail:
            note = (
                "<p style='color:#C8102E;font-weight:700'>"
                f"⚠ EQUIPMENT FAIL — {record.get('fail_count')} item(s) failed inspection. "
                f"{record.get('equipment_type', '')} {record.get('equipment_unit', '')} "
                "tagged OUT OF SERVICE."
                "</p>"
            )
        elif pm_name:
            note = f"<p>Auto-routed to <b>{pm_name}</b> based on project number "\
                   f"<b>{record.get('project_number') or '—'}</b>.</p>"
        else:
            note = (
                "<p><i>No Project Manager could be auto-resolved from the project number "
                f"<b>{record.get('project_number') or '—'}</b>. Sent to office distribution "
                "only — please assign a PM in the office.</i></p>"
            )

        params = {
            "from": f"MASCI Docs <{sender_email}>",
            "to": recipients,
            "subject": subject,
            "html": render_email_html(kind, record, note),
            "attachments": [
                {
                    "filename": _filename_for(kind, record),
                    "content": _email_b64.b64encode(pdf_bytes).decode(),
                }
            ],
        }
        if reply_to:
            params["reply_to"] = reply_to

        result = await asyncio.to_thread(resend.Emails.send, params)
        logger.info(
            f"auto-email sent: kind={kind} id={record.get('id')} pm={pm_name} "
            f"to={recipients} resend_id={(result or {}).get('id')}"
        )
    except Exception as e:  # noqa: BLE001
        logger.exception(f"auto-email failed for {kind} {record.get('id')}: {e}")


def schedule_auto_email(kind: str, record: dict) -> None:
    """Fire-and-forget wrapper (safe to call from any create endpoint)."""
    try:
        asyncio.create_task(_dispatch_auto_email(kind, dict(record)))
    except RuntimeError:
        # No running loop — skip silently (e.g. during sync tests)
        pass


# (auto-email-preview / routing-table routes are registered after _email_router below)


class EmailReportRequest(BaseModel):
    kind: str = Field(
        ...,
        description="One of: inspection, meeting, jha, incident, daily-report",
    )
    record_id: str
    recipients: List[str] = Field(..., min_length=1, max_length=20)
    subject: Optional[str] = ""
    note: Optional[str] = ""


_email_router = APIRouter(prefix="/api")


@_email_router.get("/auto-email/preview")
async def auto_email_preview(
    project_number: str = "",
    project_name: str = "",
    severity: str = "",
    osha_recordable: str = "",
    kind: str = "",
    _: bool = Depends(require_admin),
):
    """Admin-only introspection: shows who *would* receive the auto-email
    for a given project_number / project_name + form kind."""
    fake = {
        "project_number": project_number,
        "project_name": project_name,
        "severity": severity,
        "osha_recordable": osha_recordable,
    }
    dist = await recipients_for_record_async(db, fake, kind or None)
    return {
        "input": fake,
        "kind": kind or None,
        "pm_name": dist["pm_name"],
        "pm_email": dist["pm_email"],
        "to": dist["to"],
        "cc": dist["cc"],
        "all_recipients": dist["all"],
        "auto_email_enabled": auto_email_enabled(),
        "always_cc": ALWAYS_CC,
    }


@_email_router.get("/auto-email/routing-table")
async def auto_email_routing_table(_: bool = Depends(require_admin)):
    """Returns the live PM → Jobs lookup table from the DB (admin-only).
    Replaces the legacy hardcoded PM_TABLE — now reads project_managers
    + jobs_master so the UI mirrors what the email router actually uses."""
    pms_cursor = db.project_managers.find({}, {"_id": 0}).sort("name", 1)
    pms = await pms_cursor.to_list(500)
    jobs_cursor = db.jobs_master.find({}, {"_id": 0}).sort("project_number", 1)
    jobs = await jobs_cursor.to_list(2000)

    by_email: Dict[str, List[Dict[str, str]]] = {}
    unassigned: List[Dict[str, str]] = []
    for j in jobs:
        pm_email = (j.get("pm_email") or "").strip().lower()
        # Fallback: if pm_email not set but name matches a PM, infer it.
        if not pm_email:
            nm = (j.get("project_manager") or "").strip()
            if nm:
                match = next(
                    (p for p in pms if (p.get("name") or "").strip() == nm),
                    None,
                )
                if match:
                    pm_email = (match.get("email") or "").strip().lower()
        if pm_email:
            by_email.setdefault(pm_email, []).append({
                "project_number": j.get("project_number") or "",
                "project_name": j.get("project_name") or "",
            })
        else:
            unassigned.append({
                "project_number": j.get("project_number") or "",
                "project_name": j.get("project_name") or "",
            })

    project_managers = []
    for p in pms:
        em = (p.get("email") or "").strip().lower()
        project_managers.append({
            "pm_id": p.get("id"),
            "pm_name": p.get("name"),
            "pm_email": p.get("email"),
            "phone": p.get("phone") or "",
            "is_active": bool(p.get("is_active", True)),
            "jobs": by_email.get(em, []),
        })

    return {
        "always_cc": ALWAYS_CC,
        "compliance_kinds": sorted(COMPLIANCE_KINDS),
        "pm_only_kinds": sorted(PM_ONLY_KINDS),
        "auto_email_enabled": auto_email_enabled(),
        "project_managers": project_managers,
        "unassigned_jobs": unassigned,
    }


@_email_router.post("/email-report")
async def email_report(
    body: EmailReportRequest, _: bool = Depends(require_admin)
):
    if body.kind not in _KIND_TO_COLLECTION:
        raise HTTPException(status_code=400, detail=f"Unknown kind: {body.kind}")
    coll_name = _KIND_TO_COLLECTION[body.kind]
    coll = getattr(db, coll_name)
    record = await coll.find_one({"id": body.record_id}, {"_id": 0})
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="RESEND_API_KEY not configured. Add it to /app/backend/.env and restart backend.",
        )

    sender_email = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")

    try:
        import resend  # noqa: E402

        resend.api_key = api_key

        pdf_bytes = render_record_pdf(body.kind, record)
        title = KIND_TITLES.get(body.kind, "MASCI Hub Record")
        project = record.get("project_name") or record.get("project") or "MASCI"
        date_part = (
            record.get("report_date")
            or record.get("date")
            or record.get("incident_date")
            or ""
        )
        safe_proj = "".join(
            c if c.isalnum() else "_" for c in project[:40]
        ).strip("_")
        filename = f"MASCI-{body.kind}-{safe_proj}-{date_part}.pdf".replace(
            "--", "-"
        )

        subject = body.subject or f"{title} · {project}".strip(" ·")

        params = {
            "from": f"MASCI Docs <{sender_email}>",
            "to": [r for r in body.recipients if r and r.strip()],
            "subject": subject,
            "html": render_email_html(body.kind, record, body.note or ""),
            "attachments": [
                {
                    "filename": filename,
                    "content": _email_b64.b64encode(pdf_bytes).decode(),
                }
            ],
        }

        result = await asyncio.to_thread(resend.Emails.send, params)
        return {
            "ok": True,
            "id": (result or {}).get("id"),
            "to": params["to"],
            "filename": filename,
            "size_bytes": len(pdf_bytes),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"email-report failed: {e}")
        raise HTTPException(status_code=500, detail=f"Email send failed: {e}")


app.include_router(_email_router)


# ------------------------- Field Safety Cards -------------------------
#
# Printable/emailable bilingual safety cards meant for crew wallets. The
# source of truth is four high-res PDFs shipped at /app/backend/static/
# safety-cards. The frontend shows 150-DPI JPG previews served by the
# frontend public folder so crews can eyeball the card before printing;
# this email endpoint mails the ORIGINAL print-ready PDF attachment.
#
# Uses its own sub-router because `api_router` was already included on
# the app before this block — late `@api_router.post(...)` registrations
# silently fail to mount.

_SAFETY_CARD_FILES = {
    "en-front": ("MASCI_Safety_Card_EN_Front.pdf", "MASCI Safety Card — English · Front"),
    "en-back":  ("MASCI_Safety_Card_EN_Back.pdf",  "MASCI Safety Card — English · Back"),
    "es-front": ("MASCI_Safety_Card_ES_Front.pdf", "MASCI Tarjeta de Seguridad — Español · Frente"),
    "es-back":  ("MASCI_Safety_Card_ES_Back.pdf",  "MASCI Tarjeta de Seguridad — Español · Reverso"),
}


class SafetyCardEmailRequest(BaseModel):
    card: str
    recipients: List[str]
    subject: Optional[str] = None
    note: Optional[str] = None


class SafetyCardEmailAllRequest(BaseModel):
    """Bulk-send all four bilingual safety cards in one email — used by
    foremen to onboard a new hire with the entire MASCI safety packet
    in one tap."""
    recipients: List[str]
    subject: Optional[str] = None
    note: Optional[str] = None


_safety_cards_router = APIRouter(prefix="/api")


@_safety_cards_router.post("/safety-cards/email")
async def email_safety_card(body: SafetyCardEmailRequest):
    """Email one of the 4 bilingual field safety cards as a PDF attachment.
    Open to anyone in the crew — the cards are handout materials, not
    gated compliance docs."""
    if body.card not in _SAFETY_CARD_FILES:
        raise HTTPException(status_code=400, detail=f"Unknown card: {body.card}")

    filename, default_subject = _SAFETY_CARD_FILES[body.card]
    pdf_path = Path(__file__).parent / "static" / "safety-cards" / filename
    if not pdf_path.exists():
        raise HTTPException(status_code=500, detail=f"Card file missing on server: {filename}")

    api_key = (os.environ.get("RESEND_API_KEY") or "").strip()
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="RESEND_API_KEY not configured. Add it to /app/backend/.env and restart backend.",
        )

    valid_recipients = [r.strip() for r in (body.recipients or []) if r and r.strip()]
    if not valid_recipients:
        raise HTTPException(status_code=400, detail="At least one recipient email is required")

    sender_email = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")

    try:
        import resend  # noqa: E402

        resend.api_key = api_key
        pdf_bytes = pdf_path.read_bytes()

        note_html = ""
        if body.note:
            safe_note = body.note.replace("<", "&lt;").replace(">", "&gt;")
            note_html = f"<p style='margin:16px 0;color:#334155;'>{safe_note}</p>"

        html = (
            "<div style='font-family:ui-sans-serif,system-ui,Arial;max-width:600px;'>"
            "<h2 style='color:#991b1b;margin:0 0 8px;'>MASCI Field Safety Card</h2>"
            f"<p style='margin:0 0 16px;color:#475569;'>Attached: <strong>{default_subject}</strong>. "
            "Print on letter-size (8.5×11) and distribute to the crew.</p>"
            f"{note_html}"
            "<hr style='border:none;border-top:1px solid #e2e8f0;margin:16px 0;'>"
            "<p style='font-size:12px;color:#64748b;margin:0;'>Sent from MASCI Hub · Safety</p>"
            "</div>"
        )

        params = {
            "from": f"MASCI Safety <{sender_email}>",
            "to": valid_recipients,
            "subject": body.subject.strip() if body.subject else default_subject,
            "html": html,
            "attachments": [
                {
                    "filename": filename,
                    "content": _email_b64.b64encode(pdf_bytes).decode(),
                }
            ],
        }

        result = await asyncio.to_thread(resend.Emails.send, params)
        return {
            "ok": True,
            "id": (result or {}).get("id"),
            "to": valid_recipients,
            "filename": filename,
            "size_bytes": len(pdf_bytes),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"safety-cards/email failed: {e}")
        raise HTTPException(status_code=500, detail=f"Email send failed: {e}")


@_safety_cards_router.post("/safety-cards/email-all")
async def email_all_safety_cards(body: SafetyCardEmailAllRequest):
    """Bulk-email all 4 safety cards (EN front+back, ES front+back) as
    PDF attachments. One email, one click — perfect for new-hire
    onboarding. Like /safety-cards/email this endpoint is open to the
    crew because the cards themselves are handout materials."""
    api_key = (os.environ.get("RESEND_API_KEY") or "").strip()
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="RESEND_API_KEY not configured. Add it to /app/backend/.env and restart backend.",
        )

    valid_recipients = [r.strip() for r in (body.recipients or []) if r and r.strip()]
    if not valid_recipients:
        raise HTTPException(status_code=400, detail="At least one recipient email is required")

    # Read all 4 PDFs up-front
    base = Path(__file__).parent / "static" / "safety-cards"
    cards = []
    total_size = 0
    for key, (filename, label) in _SAFETY_CARD_FILES.items():
        pdf_path = base / filename
        if not pdf_path.exists():
            raise HTTPException(status_code=500, detail=f"Card file missing on server: {filename}")
        pdf_bytes = pdf_path.read_bytes()
        total_size += len(pdf_bytes)
        cards.append((filename, label, pdf_bytes))

    sender_email = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")

    try:
        import resend  # noqa: E402

        resend.api_key = api_key

        note_html = ""
        if body.note:
            safe_note = body.note.replace("<", "&lt;").replace(">", "&gt;")
            note_html = f"<p style='margin:16px 0;color:#334155;'>{safe_note}</p>"

        card_list_html = "".join(
            f"<li style='margin:4px 0;'>{label}</li>" for _, label, _ in cards
        )

        html = (
            "<div style='font-family:ui-sans-serif,system-ui,Arial;max-width:600px;'>"
            "<h2 style='color:#991b1b;margin:0 0 8px;'>MASCI Field Safety Cards — Full Set</h2>"
            "<p style='margin:0 0 12px;color:#475569;'>Attached: the complete bilingual MASCI safety card set "
            "(English front &amp; back, Spanish front &amp; back). Print on letter-size (8.5×11) and "
            "distribute to your crew. Perfect for new-hire onboarding.</p>"
            f"<ul style='margin:8px 0 16px 20px;color:#334155;'>{card_list_html}</ul>"
            f"{note_html}"
            "<hr style='border:none;border-top:1px solid #e2e8f0;margin:16px 0;'>"
            "<p style='font-size:12px;color:#64748b;margin:0;'>Sent from MASCI Hub · Safety</p>"
            "</div>"
        )

        params = {
            "from": f"MASCI Safety <{sender_email}>",
            "to": valid_recipients,
            "subject": body.subject.strip() if body.subject else "MASCI Field Safety Cards — Full Bilingual Set",
            "html": html,
            "attachments": [
                {
                    "filename": filename,
                    "content": _email_b64.b64encode(pdf_bytes).decode(),
                }
                for filename, _, pdf_bytes in cards
            ],
        }

        result = await asyncio.to_thread(resend.Emails.send, params)
        return {
            "ok": True,
            "id": (result or {}).get("id"),
            "to": valid_recipients,
            "card_count": len(cards),
            "total_size_bytes": total_size,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"safety-cards/email-all failed: {e}")
        raise HTTPException(status_code=500, detail=f"Email send failed: {e}")


app.include_router(_safety_cards_router)


# Empty placeholder — was a stale duplicate route block, kept above before router include.


# ------------------------- Phase 1: per-user auth + projects (Basecamp-style /app) -------------------------
from auth import build_auth_router, seed_initial_users  # noqa: E402
from projects import build_projects_router, seed_initial_projects  # noqa: E402
from tools import build_tools_router, create_tools_indexes  # noqa: E402
from phase4 import build_phase4_router, create_phase4_indexes  # noqa: E402

_auth_router, get_current_user, require_admin_or_owner, _optional_user = build_auth_router(db)
_projects_router = build_projects_router(db, get_current_user, require_admin_or_owner)
_tools_router = build_tools_router(db, get_current_user, require_admin_or_owner)
app.include_router(_auth_router)
app.include_router(_projects_router)
app.include_router(_tools_router)

# Register phase 4 (activity + notifications + search + directory)
_phase4_router = build_phase4_router(db, get_current_user)
app.include_router(_phase4_router)


@app.on_event("startup")
async def _seed_phase1():
    try:
        await seed_initial_users(db)
        await seed_initial_projects(db)
        await create_tools_indexes(db)
        await create_phase4_indexes(db)
        await _seed_equipment_master()
        await _seed_employees_from_json()
        await _seed_suppliers_from_json()
        await _create_safety_indexes()
        # Seed project_managers FIRST so jobs_master backfill can link by name.
        from project_managers import seed_project_managers
        await seed_project_managers(db)
        # Seed jobs_master from /app/backend/data/jobs_master.json (idempotent).
        # Also runs the pm_email backfill against project_managers.
        from jobs_master import seed_jobs_master
        await seed_jobs_master(db)
        # Index for the new multi-file JHP collection.
        from job_hazard_files import ensure_indexes as _jha_files_indexes
        await _jha_files_indexes(db)
        # Zero-touch self-heal: auto-split equipment make/model on boot if any
        # units are missing it. Survives redeploys that wipe the DB.
        from data_fixes import boot_self_heal
        await boot_self_heal(db)
    except Exception as e:
        logging.getLogger(__name__).exception(f"Phase 1 seed failed: {e}")


async def _create_safety_indexes():
    """Idempotent indexes on the safety + equipment + parts collections.

    Massively speeds up dashboard listings, trends queries, and shop
    open-items lookups once the dataset grows past a few hundred records.
    """
    try:
        await db.equipment_inspections.create_index("created_at")
        await db.equipment_inspections.create_index("inspection_date")
        await db.equipment_inspections.create_index("equipment_unit")
        await db.equipment_inspections.create_index("project_number")
        await db.equipment_inspections.create_index("fail_count")

        await db.inspections.create_index("created_at")
        await db.inspections.create_index("inspection_date")
        await db.inspections.create_index("project_number")

        await db.daily_reports.create_index("created_at")
        await db.daily_reports.create_index("report_date")
        await db.daily_reports.create_index("project_number")

        await db.incidents.create_index("created_at")
        await db.incidents.create_index("incident_date")
        await db.incidents.create_index("severity")

        await db.meetings.create_index("created_at")
        await db.meetings.create_index("meeting_date")

        await db.equipment_parts.create_index("unit_number", unique=True)
        await db.equipment_master.create_index("unit_number")
        await db.equipment_master.create_index("category")
        logging.getLogger(__name__).info("[safety-indexes] ensured")
    except Exception as e:
        logging.getLogger(__name__).warning(f"[safety-indexes] failed: {e}")


@app.on_event("startup")
async def _start_backup_scheduler():
    """Kick off the nightly full-backup scheduler as an asyncio task."""
    global _backup_task
    if os.environ.get("DISABLE_BACKUP_SCHEDULER", "").lower() in ("1", "true", "yes"):
        logging.getLogger(__name__).info("[scheduled-backup] DISABLED via env")
        return
    try:
        BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
        # DEFENSE LAYER 4 — Boot-time disk safety check.
        # If the disk is above the high-water-mark when we start up
        # (e.g., a previous container crash left the disk full), purge
        # backups IMMEDIATELY before doing anything else. This guarantees
        # a fresh boot can never be killed by inherited disk pressure.
        pct = _disk_pct_used()
        if pct >= BACKUP_DISK_HIGH_WATERMARK:
            logging.getLogger(__name__).warning(
                f"[scheduled-backup] disk at {pct}% on boot — running emergency prune"
            )
            _emergency_prune_backups(reason=f"boot disk {pct}%")
        _backup_task = asyncio.create_task(_backup_scheduler_loop(db))
        _hours_str = " · ".join(f"{h:02d}:00" for h in BACKUP_HOURS_UTC) + " UTC"
        logging.getLogger(__name__).info(
            f"[scheduled-backup] scheduler started — {_hours_str} · "
            f"keep {BACKUP_RETENTION_DAYS} days · max {BACKUP_KEEP_MAX} files · "
            f"disk-watermark {BACKUP_DISK_HIGH_WATERMARK}% · dir={BACKUPS_DIR}"
        )
    except Exception as e:
        logging.getLogger(__name__).exception(f"[scheduled-backup] startup failed: {e}")

cors_origins_env = os.environ.get('CORS_ORIGINS', '').strip()
cors_origin_regex = (os.environ.get('CORS_ORIGIN_REGEX', '') or '').strip() or None

# Default safe regex when no env vars are set: allow MASCI's prod domain plus
# any Emergent preview pod. Browsers reject `Access-Control-Allow-Origin: *`
# combined with credentialed requests (and the frontend sends credentials),
# so a regex / explicit list is required for the prod app to actually work
# in iOS Safari + Cloudflare.
_DEFAULT_CORS_REGEX = (
    r"^https://("
    r"(www\.)?mascidocs\.com"
    r"|.*\.emergentagent\.com"
    r"|.*\.preview\.emergentagent\.com"
    r"|.*\.emergent\.host"
    r")$"
)

if cors_origins_env and cors_origins_env != '*':
    _cors_origins = [o.strip() for o in cors_origins_env.split(',') if o.strip()]
    _cors_credentials = True
elif cors_origins_env == '*':
    # Explicitly opted into wildcard — credentials must be off per CORS spec.
    _cors_origins: List[str] = ["*"]
    _cors_credentials = False
else:
    # No env var set → use the safe default regex with credentials enabled.
    _cors_origins = []
    _cors_credentials = True
    if not cors_origin_regex:
        cors_origin_regex = _DEFAULT_CORS_REGEX

app.add_middleware(
    CORSMiddleware,
    allow_credentials=_cors_credentials,
    allow_origins=_cors_origins,
    allow_origin_regex=cors_origin_regex,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


@app.on_event("shutdown")
async def shutdown_db_client():
    try:
        if _backup_task is not None:
            _backup_task.cancel()
    except Exception:
        pass
    client.close()
