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
from pydantic import BaseModel, Field
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


def _admin_token_for(password: str) -> str:
    return hmac.new(_admin_hmac_secret(), password.encode(), hashlib.sha256).hexdigest()


def require_admin(x_admin_token: Optional[str] = Header(default=None)):
    """FastAPI dependency. Reject unless the request carries a valid token."""
    expected_pw = os.environ.get("ADMIN_PASSWORD", "")
    if not expected_pw:
        # No password configured → admin gate disabled (open mode)
        return True
    if not x_admin_token:
        raise HTTPException(status_code=401, detail="Admin login required")
    expected = _admin_token_for(expected_pw)
    if not hmac.compare_digest(x_admin_token, expected):
        raise HTTPException(status_code=401, detail="Invalid admin token")
    return True


def _shop_token_for(password: str) -> str:
    return hmac.new(_admin_hmac_secret(), b"shop:" + password.encode(), hashlib.sha256).hexdigest()


def require_shop_or_admin(
    x_admin_token: Optional[str] = Header(default=None),
    x_shop_token: Optional[str] = Header(default=None),
):
    """Accepts either an admin token OR a shop token.

    Used on equipment-inspection read + sign-off routes so the shop can do
    their job without seeing the rest of the office console.
    """
    admin_pw = os.environ.get("ADMIN_PASSWORD", "")
    shop_pw = os.environ.get("SHOP_PASSWORD", "")
    if not admin_pw and not shop_pw:
        return True  # Both gates disabled
    if x_admin_token and admin_pw:
        expected = _admin_token_for(admin_pw)
        if hmac.compare_digest(x_admin_token, expected):
            return True
    if x_shop_token and shop_pw:
        expected = _shop_token_for(shop_pw)
        if hmac.compare_digest(x_shop_token, expected):
            return True
    raise HTTPException(status_code=401, detail="Shop or admin login required")


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


# ------------------------- Models -------------------------
# ============================================================
# Safety Forms — Inspections, Meetings, JHAs, Incidents
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
    q = {"category": category} if category else {}
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
    project_manager: str = ""
    active: bool = True


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
    return {"ok": True}


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
    cursor = db.employees.find({"is_active": {"$ne": False}}, {"_id": 0}).sort("name", 1)
    docs = await cursor.to_list(2000)
    return {"items": docs, "count": len(docs)}


@api_router.get("/admin/employees/status")
async def employees_status(_: bool = Depends(require_admin)):
    total = await db.employees.count_documents({})
    active = await db.employees.count_documents({"is_active": {"$ne": False}})
    last_doc = await db.employees.find_one({}, {"_id": 0, "updated_at": 1, "created_at": 1}, sort=[("updated_at", -1)])
    last_updated = (last_doc or {}).get("updated_at") or (last_doc or {}).get("created_at")
    return {"count": total, "active": active, "last_updated": last_updated}


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


@api_router.delete("/admin/employees/{employee_id}")
async def delete_employee(employee_id: str, _: bool = Depends(require_admin)):
    res = await db.employees.delete_one({"id": employee_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"ok": True}


# ---------------------------------------------------------------------------
# Suppliers / Subcontractors — used by Daily Report Sections 05 & 08.
# ---------------------------------------------------------------------------
SUPPLIERS_SEED_FILE = ROOT_DIR / "data" / "suppliers_seed.json"
EMPLOYEES_SEED_FILE = ROOT_DIR / "data" / "employees_seed.json"


@api_router.get("/suppliers")
async def list_suppliers():
    """Public — returns the full MASCI supplier / subcontractor list."""
    cursor = db.suppliers.find({"is_active": {"$ne": False}}, {"_id": 0}).sort("name", 1)
    docs = await cursor.to_list(2000)
    return {"items": docs, "count": len(docs)}


@api_router.get("/admin/suppliers/status")
async def suppliers_status(_: bool = Depends(require_admin)):
    total = await db.suppliers.count_documents({})
    active = await db.suppliers.count_documents({"is_active": {"$ne": False}})
    last_doc = await db.suppliers.find_one(
        {}, {"_id": 0, "updated_at": 1, "created_at": 1}, sort=[("updated_at", -1)]
    )
    last_updated = (last_doc or {}).get("updated_at") or (last_doc or {}).get("created_at")
    return {"count": total, "active": active, "last_updated": last_updated}


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


@api_router.delete("/admin/suppliers/{supplier_id}")
async def delete_supplier(supplier_id: str, _: bool = Depends(require_admin)):
    res = await db.suppliers.delete_one({"id": supplier_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return {"ok": True}


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
    count = await db.equipment_master.count_documents({})
    cursor = db.equipment_master.find({}, {"_id": 0, "category": 1})
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
        "categories": dict(sorted(cats.items(), key=lambda x: -x[1])),
        "last_updated": last_updated,
        "seed_file": str(EQUIPMENT_MASTER_SEED_FILE),
    }


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
async def exports_full_backup(_: bool = Depends(require_admin)):
    """One-click off-site backup. Streams a single .zip back containing:

    /CSV/                — one CSV per kind (no photos/signatures inline)
    /<kind>/json/        — every record as raw JSON (photos + signatures intact)
    /<kind>/pdf/         — every record rendered to PDF via WeasyPrint
    /crew_hub/           — Crew Hub collections as JSON
    /safety_aux/         — Equipment unit registry, JHA plan PDFs, trench-box refs
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
            cursor = db[coll_name].find({}, {"_id": 0}).sort("created_at", -1)
            docs = await cursor.to_list(50000)
            total_records += len(docs)
            log_lines.append(f"  {kind:25s} : {len(docs):5d}")

            # /CSV/
            try:
                csv_bytes = _build_csv_bytes(kind, [dict(d) for d in docs])
                zf.writestr(f"CSV/MASCI_{kind}_{stamp}.csv", csv_bytes)
            except Exception as e:  # noqa: BLE001
                log_lines.append(f"    [warn] CSV build failed: {e}")

            # /<kind>/json/  + /<kind>/pdf/
            for d in docs:
                base = _record_filename(kind, d)
                try:
                    zf.writestr(
                        f"{kind}/json/{base}.json",
                        _backup_json.dumps(d, indent=2, default=str).encode("utf-8"),
                    )
                except Exception as e:  # noqa: BLE001
                    log_lines.append(f"    [warn] {kind}/{d.get('id')} JSON failed: {e}")

                # PDFs are heavy — only render the kinds we know how to render.
                # Map the storage kind back to the pdf_render kind.
                pdf_kind = {
                    "inspections": "inspection",
                    "meetings": "meeting",
                    "jhas": "jha",
                    "incidents": "incident",
                    "daily-reports": "daily-report",
                    "equipment-inspections": "equipment-inspection",
                }.get(kind)
                if pdf_kind:
                    try:
                        pdf_bytes = await _backup_asyncio.to_thread(
                            render_record_pdf, pdf_kind, d
                        )
                        total_pdf_bytes += len(pdf_bytes)
                        zf.writestr(f"{kind}/pdf/{base}.pdf", pdf_bytes)
                    except Exception as e:  # noqa: BLE001
                        pdf_failures.append(f"{kind}/{d.get('id')}: {e}")
                    # Yield after every PDF render — these are the slowest
                    # piece of the build (WeasyPrint can take 1-3s each).
                    await asyncio.sleep(0)

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
                docs = await db[coll_name].find({}, projection).to_list(100000)
                auto_total += len(docs)
                captured_collections.append(coll_name)
                log_lines.append(f"  collections/{coll_name:24s} : {len(docs):5d}")
                zf.writestr(
                    f"collections/{coll_name}.json",
                    _backup_json.dumps(docs, indent=2, default=str).encode("utf-8"),
                )
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
                    raw = f.read_bytes()
                    zf.writestr(f"disk_files/{rel.as_posix()}", raw)
                    disk_files_count += 1
                    disk_bytes += len(raw)
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
BACKUP_HOUR_UTC = int(os.environ.get("BACKUP_HOUR_UTC", "2"))   # default 02:00 UTC
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
    """Background loop — wakes up every ~60 s, fires the backup once the
    current UTC hour equals BACKUP_HOUR_UTC and we haven't already run today.
    Survives missed ticks (e.g., if the container was asleep at 02:00).
    """
    last_run_date = None
    # Give the app a moment to finish startup before first tick
    await asyncio.sleep(30)
    while True:
        try:
            now = datetime.now(timezone.utc)
            today = now.date()
            if now.hour >= BACKUP_HOUR_UTC and last_run_date != today:
                logger.info(f"[scheduled-backup] firing for {today}")
                result = await _run_scheduled_backup(db)
                if result:
                    last_run_date = today
                # If it failed, leave last_run_date alone so we retry next tick.
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.exception(f"[scheduled-backup] loop tick error: {e}")
        await asyncio.sleep(300)  # 5 min ticks — low overhead, catches missed slots


@api_router.get("/admin/backups")
async def admin_list_backups(_: bool = Depends(require_admin)):
    """List every stored backup on disk + current schedule settings."""
    files = _list_stored_backups()
    total_bytes = sum(f["size_bytes"] for f in files)
    return {
        "backups": files,
        "count": len(files),
        "total_bytes": total_bytes,
        "schedule": {
            "hour_utc": BACKUP_HOUR_UTC,
            "retention_days": BACKUP_RETENTION_DAYS,
            "storage_dir": str(BACKUPS_DIR),
            "enabled": True,
        },
    }


@api_router.get("/admin/backups/integrity-check")
async def admin_backup_integrity_check(_: bool = Depends(require_admin)):
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
    filename: str, _: bool = Depends(require_admin)
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
    filename: str, _: bool = Depends(require_admin)
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
async def admin_run_backup_now(_: bool = Depends(require_admin)):
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
# (X-Admin-Token / Happy123!) — NOT by a Crew Hub JWT — so it works even when
# every crew owner+admin is locked out.

@api_router.get("/admin/crew-recovery/status")
async def admin_crew_recovery_status(_: bool = Depends(require_admin)):
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
    _: bool = Depends(require_admin),
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
async def admin_crew_recovery_force_reseed(_: bool = Depends(require_admin)):
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
async def admin_scrap_crew_hub(body: dict, _: bool = Depends(require_admin)):
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


@api_router.post("/exports/restore")
async def exports_restore(
    file: UploadFile = File(...),
    merge: bool = Form(True),
    _: bool = Depends(require_admin),
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
    PM_TABLE,
    ALWAYS_CC,
    COMPLIANCE_KINDS,
    PM_ONLY_KINDS,
    auto_email_enabled,
    recipients_for_record,
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

        dist = recipients_for_record(record, kind)
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
    dist = recipients_for_record(fake, kind or None)
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
    """Returns the full PM → Jobs lookup table (admin-only)."""
    return {
        "always_cc": ALWAYS_CC,
        "compliance_kinds": sorted(COMPLIANCE_KINDS),
        "pm_only_kinds": sorted(PM_ONLY_KINDS),
        "auto_email_enabled": auto_email_enabled(),
        "project_managers": [
            {
                "pm_name": pm,
                "pm_email": data["email"],
                "jobs": [
                    {"project_number": jn, "project_name": jname}
                    for (jn, jname) in data["jobs"]  # type: ignore[union-attr]
                ],
            }
            for pm, data in PM_TABLE.items()
        ],
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
        # Seed jobs_master from /app/backend/data/jobs_master.json (idempotent)
        from jobs_master import seed_jobs_master
        await seed_jobs_master(db)
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
        logging.getLogger(__name__).info(
            f"[scheduled-backup] scheduler started — {BACKUP_HOUR_UTC:02d}:00 UTC daily · "
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
