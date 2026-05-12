"""
hub_banners.py — Site-wide Hub Banner Messaging System
======================================================

Admin can post a banner that appears as a sticky strip at the top of
every page in the platform (Hub home, all forms, admin, PM, shop). Use
cases: Heat Advisory, Hurricane Watch / Warning, Lightning, Flood,
Stand-Down notices, OSHA visit alerts, holiday / shutdown announcements.

Key design choices
------------------
1. Four severity tiers — INFO (blue) · ADVISORY (amber) · WARNING (red) ·
   CRITICAL (dark red, pulsing). Each maps to a color + icon on the
   frontend.

2. Per-banner "require_ack" flag. When set, the frontend shows a hard
   gate — a full-screen modal that blocks navigation until the user
   clicks "I acknowledge". CRITICAL templates default ack=True.

3. Optional `expires_at` (ISO datetime, UTC). The active feed excludes
   banners whose expiration has passed — heat advisories auto-clear at
   the end of the workday, hurricane warnings 36h later, etc.

4. Auto-Spanish translation via the same EMERGENT_LLM_KEY +
   claude-haiku-4-5 pipeline the `/api/translate` route uses. Admin
   types ENG title + body; on save we ask Claude to translate and
   store both. Field users see ENG or ESP based on their `LangToggle`
   setting.

5. Acknowledgment tracking uses a **device id** (UUID stored in
   localStorage on first page load) instead of a real auth identity.
   The site is partially unauthenticated (any crew member can submit
   a daily report without logging in), so we can't rely on PM/shop
   tokens for ack tracking. The device-id approach gives admins a
   useful "X devices have acknowledged" stat without forcing logins.

6. Audit log — every create / edit / delete writes a row to
   `hub_banner_audit` with `actor`, `action`, `banner_id`, `ts`.

Endpoints (mounted under /api)
------------------------------
Public:
    GET  /banners/active                  — current non-expired banners
    POST /banners/{id}/acknowledge        — body {device_id}
    POST /banners/{id}/dismiss            — body {device_id}  (soft hide)

Admin-only (require X-Admin-Token):
    GET    /admin/banners                 — list all (incl expired)
    POST   /admin/banners                 — create
    PATCH  /admin/banners/{id}            — edit
    DELETE /admin/banners/{id}            — delete
    POST   /admin/banners/translate       — utility: translate {title,body}
    GET    /admin/banners/{id}/audit      — audit log for a banner
"""
from __future__ import annotations

import json as _json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────
# Pydantic models
# ─────────────────────────────────────────────────────────────────────
SEVERITY_VALUES = {"info", "advisory", "warning", "critical"}


class BannerIn(BaseModel):
    """Payload for create / edit. All optional on PATCH; required on POST."""
    title_en: str = Field(..., min_length=1, max_length=200)
    body_en: str = Field(default="", max_length=2000)
    title_es: Optional[str] = Field(default=None, max_length=200)
    body_es: Optional[str] = Field(default=None, max_length=2000)
    severity: str = Field(default="advisory")
    require_ack: bool = Field(default=False)
    expires_at: Optional[str] = Field(default=None)  # ISO 8601 UTC
    template_id: Optional[str] = Field(default=None)
    auto_translate: bool = Field(default=True)  # auto-call Claude if title_es/body_es missing


class BannerPatch(BaseModel):
    title_en: Optional[str] = Field(default=None, max_length=200)
    body_en: Optional[str] = Field(default=None, max_length=2000)
    title_es: Optional[str] = Field(default=None, max_length=200)
    body_es: Optional[str] = Field(default=None, max_length=2000)
    severity: Optional[str] = None
    require_ack: Optional[bool] = None
    expires_at: Optional[str] = None  # pass empty string to clear


class AckPayload(BaseModel):
    device_id: str = Field(..., min_length=4, max_length=80)
    # Optional client-supplied context — used to give the admin audit
    # trail something more useful than "device-abc123 acknowledged".
    path: Optional[str] = Field(default=None, max_length=200)
    lang: Optional[str] = Field(default=None, max_length=10)
    actor_name: Optional[str] = Field(default=None, max_length=120)


class TranslatePayload(BaseModel):
    title_en: str = ""
    body_en: str = ""


# ─────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────
def _now() -> datetime:
    return datetime.now(timezone.utc)


def _serialize(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Strip Mongo `_id` and return a JSON-safe dict."""
    if not doc:
        return doc
    out = {k: v for k, v in doc.items() if k != "_id"}
    return out


def _validate_severity(s: Optional[str]) -> str:
    if not s:
        return "advisory"
    s = s.lower().strip()
    if s not in SEVERITY_VALUES:
        raise HTTPException(400, f"severity must be one of {sorted(SEVERITY_VALUES)}")
    return s


def _parse_iso(s: Optional[str]) -> Optional[datetime]:
    """Parse an ISO 8601 string into a UTC datetime. Returns None on
    blank input. Raises HTTPException on bad input."""
    if not s or not s.strip():
        return None
    try:
        # Accept Z suffix
        v = s.strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(v)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception as e:
        raise HTTPException(400, f"expires_at must be ISO 8601: {e}")


async def _translate_to_spanish(title_en: str, body_en: str) -> Dict[str, str]:
    """Mirror /api/translate but tailored for banner copy. Returns
    {"title_es": "...", "body_es": "..."}. Best-effort — returns the
    English text unchanged on any failure so banner creation is never
    blocked by translation flakiness."""
    api_key = (os.environ.get("EMERGENT_LLM_KEY") or "").strip()
    if not api_key:
        logger.warning("[hub-banners] EMERGENT_LLM_KEY missing — skipping translation")
        return {"title_es": title_en, "body_es": body_en}

    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
    except Exception as e:  # pragma: no cover
        logger.error(f"[hub-banners] emergentintegrations import failed: {e}")
        return {"title_es": title_en, "body_es": body_en}

    system = (
        "You translate emergency / safety notices for a US heavy-civil "
        "construction company that employs Spanish-speaking field crews. "
        "Translate from English to Spanish (es-MX dialect, plain wording, "
        "no formal vosotros). Preserve technical terms (excavator, MOT, PPE, "
        "rebar, foreman, OSHA) when they're industry-standard. Keep numbers, "
        "times, and proper nouns EXACTLY. Reply with ONLY a JSON object: "
        '{"title_es": "...", "body_es": "..."}. No commentary, no fences.'
    )

    user_text = _json.dumps({"title_en": title_en, "body_en": body_en}, ensure_ascii=False)

    try:
        chat = LlmChat(
            api_key=api_key,
            session_id=f"banner-translate-{uuid.uuid4().hex[:8]}",
            system_message=system,
        ).with_model("anthropic", "claude-haiku-4-5-20251001")

        response = await chat.send_message(UserMessage(text=user_text))
        text = (response or "").strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].lstrip("\n")
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            raise ValueError(f"No JSON object in response: {text[:200]}")
        parsed = _json.loads(text[start : end + 1])
        return {
            "title_es": str(parsed.get("title_es") or title_en).strip() or title_en,
            "body_es": str(parsed.get("body_es") or body_en).strip() or body_en,
        }
    except Exception as e:
        logger.warning(f"[hub-banners] auto-translate failed: {e}")
        return {"title_es": title_en, "body_es": body_en}


# ─────────────────────────────────────────────────────────────────────
# Router factory
# ─────────────────────────────────────────────────────────────────────
def build_hub_banners_router(db, require_admin_dep: Callable) -> APIRouter:
    """Build the banners router. `db` is the motor database handle and
    `require_admin_dep` is the FastAPI dependency that enforces admin
    auth (passed in to avoid a circular import with server.py)."""
    router = APIRouter(prefix="/api", tags=["hub-banners"])

    banners = db["hub_banners"]
    audit = db["hub_banner_audit"]

    async def _audit_log(action: str, banner_id: str, actor: str, extra: Optional[Dict[str, Any]] = None) -> None:
        try:
            await audit.insert_one({
                "id": uuid.uuid4().hex,
                "banner_id": banner_id,
                "action": action,
                "actor": actor or "admin",
                "ts": _now().isoformat(),
                "extra": extra or {},
            })
        except Exception as e:
            logger.warning(f"[hub-banners] audit insert failed ({action} {banner_id}): {e}")

    # ─── Public ───────────────────────────────────────────────────
    @router.get("/banners/active")
    async def list_active_banners(device_id: Optional[str] = Query(default=None)):
        """Return all currently-active banners. A banner is active when
        it exists and `expires_at` is either null or in the future. The
        `device_id` query param is optional — when supplied we annotate
        each banner with `acknowledged: true/false` and `dismissed: true/
        false` so the frontend can suppress soft-dismissed banners.

        Sorted by severity (critical → info) then created_at desc so the
        most urgent appears on top when multiple are active."""
        now = _now()
        cursor = banners.find({}, {"_id": 0})
        out: List[Dict[str, Any]] = []
        async for b in cursor:
            exp = b.get("expires_at")
            if exp:
                try:
                    exp_dt = datetime.fromisoformat(exp.replace("Z", "+00:00"))
                    if exp_dt.tzinfo is None:
                        exp_dt = exp_dt.replace(tzinfo=timezone.utc)
                    if exp_dt < now:
                        continue
                except Exception:
                    pass
            if b.get("disabled"):
                continue
            if device_id:
                acks = b.get("acks") or []
                dsm = b.get("dismisses") or []
                b["acknowledged"] = device_id in acks
                b["dismissed"] = device_id in dsm
            else:
                b["acknowledged"] = False
                b["dismissed"] = False
            # Drop the raw ack/dismiss lists from the public payload —
            # they're admin-stats only.
            b.pop("acks", None)
            b.pop("dismisses", None)
            out.append(b)

        sev_rank = {"critical": 0, "warning": 1, "advisory": 2, "info": 3}
        # Single-pass sort: highest severity first, then newest first.
        # (negating the str is awkward — use a tuple of (rank, -ts_int)
        # by reverse-sorting on created_at since Python sort is stable.)
        out.sort(key=lambda x: x.get("created_at") or "", reverse=True)
        out.sort(key=lambda x: sev_rank.get(x.get("severity", "info"), 9))
        return {"ok": True, "banners": out, "now": now.isoformat()}

    def _client_meta(req: Request, payload: AckPayload) -> Dict[str, Any]:
        """Pull whatever audit-useful context we can off the request +
        payload. Stored verbatim in the per-banner ack_log / dismiss_log
        arrays so the admin "Audit Trail" panel can show a meaningful
        timeline ("acked at 3:42 PM from 24.x.x.x via /daily/new")."""
        try:
            ip = req.client.host if req.client else None
        except Exception:
            ip = None
        # FastAPI may sit behind the Emergent ingress — prefer the
        # forwarded-for header when present (first hop = real client).
        fwd = req.headers.get("x-forwarded-for") or req.headers.get("x-real-ip")
        if fwd:
            ip = fwd.split(",")[0].strip()
        ua = (req.headers.get("user-agent") or "")[:200]
        return {
            "device_id": payload.device_id.strip(),
            "ts": _now().isoformat(),
            "ip": ip,
            "ua": ua,
            "path": (payload.path or "")[:200] or None,
            "lang": payload.lang or None,
            "actor_name": (payload.actor_name or "")[:120] or None,
        }

    @router.post("/banners/{banner_id}/acknowledge")
    async def acknowledge_banner(banner_id: str, payload: AckPayload, request: Request):
        """Record an acknowledgment from a device. Always appends a row
        to `ack_log` (timestamped audit trail). The legacy `acks` set is
        kept for fast O(1) "has this device acked?" lookups by the
        public list endpoint."""
        device_id = payload.device_id.strip()
        if not device_id:
            raise HTTPException(400, "device_id required")
        entry = _client_meta(request, payload)
        res = await banners.update_one(
            {"id": banner_id},
            {
                "$addToSet": {"acks": device_id},
                "$push": {"ack_log": entry},
                "$set": {"last_ack_at": entry["ts"]},
            },
        )
        if res.matched_count == 0:
            raise HTTPException(404, "banner not found")
        return {"ok": True}

    @router.post("/banners/{banner_id}/dismiss")
    async def dismiss_banner(banner_id: str, payload: AckPayload, request: Request):
        """Soft-dismiss — same dual-write pattern as acknowledge_banner.
        `dismisses` set drives the public ack-status check; `dismiss_log`
        feeds the admin Audit Trail panel."""
        device_id = payload.device_id.strip()
        if not device_id:
            raise HTTPException(400, "device_id required")
        entry = _client_meta(request, payload)
        res = await banners.update_one(
            {"id": banner_id},
            {
                "$addToSet": {"dismisses": device_id},
                "$push": {"dismiss_log": entry},
            },
        )
        if res.matched_count == 0:
            raise HTTPException(404, "banner not found")
        return {"ok": True}

    # ─── Admin only ───────────────────────────────────────────────
    @router.get("/admin/banners", dependencies=[Depends(require_admin_dep)])
    async def list_all_banners():
        """List every banner including expired + dismissed counts. Used
        by the AdminBannersPanel."""
        out: List[Dict[str, Any]] = []
        async for b in banners.find({}, {"_id": 0}).sort("created_at", -1):
            b["ack_count"] = len(b.get("acks") or [])
            b["dismiss_count"] = len(b.get("dismisses") or [])
            # Don't return the full device lists to the admin UI — they
            # can balloon. Stats are enough.
            b.pop("acks", None)
            b.pop("dismisses", None)
            out.append(b)
        return {"ok": True, "banners": out}

    @router.post("/admin/banners", dependencies=[Depends(require_admin_dep)])
    async def create_banner(payload: BannerIn):
        """Create a new banner. If title_es/body_es are blank AND
        `auto_translate` is True, we call Claude Haiku to fill them in.
        The response includes the saved doc so the admin UI can show
        the rendered Spanish copy immediately."""
        severity = _validate_severity(payload.severity)
        exp_dt = _parse_iso(payload.expires_at) if payload.expires_at else None

        title_en = payload.title_en.strip()
        body_en = (payload.body_en or "").strip()
        title_es = (payload.title_es or "").strip()
        body_es = (payload.body_es or "").strip()

        if payload.auto_translate and (not title_es or not body_es):
            tr = await _translate_to_spanish(title_en, body_en)
            if not title_es:
                title_es = tr.get("title_es") or title_en
            if not body_es:
                body_es = tr.get("body_es") or body_en

        doc = {
            "id": uuid.uuid4().hex,
            "title_en": title_en,
            "body_en": body_en,
            "title_es": title_es or title_en,
            "body_es": body_es or body_en,
            "severity": severity,
            "require_ack": bool(payload.require_ack),
            "expires_at": exp_dt.isoformat() if exp_dt else None,
            "template_id": payload.template_id,
            "created_at": _now().isoformat(),
            "updated_at": _now().isoformat(),
            "disabled": False,
            "acks": [],
            "dismisses": [],
        }
        await banners.insert_one(doc)
        # `doc` now has `_id` from Mongo — strip before returning.
        await _audit_log("create", doc["id"], "admin", {"severity": severity})
        return {"ok": True, "banner": _serialize(doc)}

    @router.patch("/admin/banners/{banner_id}", dependencies=[Depends(require_admin_dep)])
    async def update_banner(banner_id: str, payload: BannerPatch):
        existing = await banners.find_one({"id": banner_id}, {"_id": 0})
        if not existing:
            raise HTTPException(404, "banner not found")

        updates: Dict[str, Any] = {}
        if payload.title_en is not None:
            updates["title_en"] = payload.title_en.strip()
        if payload.body_en is not None:
            updates["body_en"] = payload.body_en.strip()
        if payload.title_es is not None:
            updates["title_es"] = payload.title_es.strip()
        if payload.body_es is not None:
            updates["body_es"] = payload.body_es.strip()
        if payload.severity is not None:
            updates["severity"] = _validate_severity(payload.severity)
        if payload.require_ack is not None:
            updates["require_ack"] = bool(payload.require_ack)
        if payload.expires_at is not None:
            # empty string -> clear expiration
            if payload.expires_at.strip() == "":
                updates["expires_at"] = None
            else:
                exp_dt = _parse_iso(payload.expires_at)
                updates["expires_at"] = exp_dt.isoformat() if exp_dt else None

        if not updates:
            return {"ok": True, "banner": existing}

        updates["updated_at"] = _now().isoformat()
        await banners.update_one({"id": banner_id}, {"$set": updates})
        await _audit_log("update", banner_id, "admin", {"fields": list(updates.keys())})
        fresh = await banners.find_one({"id": banner_id}, {"_id": 0, "acks": 0, "dismisses": 0})
        return {"ok": True, "banner": fresh}

    @router.delete("/admin/banners/{banner_id}", dependencies=[Depends(require_admin_dep)])
    async def delete_banner(banner_id: str):
        res = await banners.delete_one({"id": banner_id})
        if res.deleted_count == 0:
            raise HTTPException(404, "banner not found")
        await _audit_log("delete", banner_id, "admin")
        return {"ok": True}

    @router.post("/admin/banners/translate", dependencies=[Depends(require_admin_dep)])
    async def translate_only(payload: TranslatePayload):
        """Utility endpoint — translate a draft to Spanish without
        creating a banner. Lets the admin compose UI show a live
        preview of the translation before clicking Save."""
        tr = await _translate_to_spanish(payload.title_en, payload.body_en)
        return {"ok": True, **tr}

    @router.get("/admin/banners/{banner_id}/audit", dependencies=[Depends(require_admin_dep)])
    async def banner_audit(banner_id: str):
        """Combined timeline of every interaction with a banner: admin
        create/update/delete actions PLUS every per-device ack and
        dismiss with timestamp + IP + browser + page. Used by the
        AdminBannersPanel "Audit Trail" peek for legal-cover proof
        ("foreman acked the stand-down at 4:42 PM from the job-site
        IP before leaving").

        IMPORTANT: still returns admin actions even after the banner is
        deleted — that's the whole point of an audit log. Only the per-
        device ack/dismiss timelines disappear with the parent doc.

        Returns newest-first, capped at 500 rows total.
        """
        b = await banners.find_one({"id": banner_id}, {"_id": 0})

        rows: List[Dict[str, Any]] = []
        async for r in audit.find({"banner_id": banner_id}, {"_id": 0}).sort("ts", -1).limit(200):
            rows.append({**r, "kind": "admin"})

        if b is not None:
            for entry in (b.get("ack_log") or []):
                rows.append({
                    "kind": "ack",
                    "ts": entry.get("ts"),
                    "device_id": entry.get("device_id"),
                    "ip": entry.get("ip"),
                    "ua": entry.get("ua"),
                    "path": entry.get("path"),
                    "lang": entry.get("lang"),
                    "actor_name": entry.get("actor_name"),
                })
            for entry in (b.get("dismiss_log") or []):
                rows.append({
                    "kind": "dismiss",
                    "ts": entry.get("ts"),
                    "device_id": entry.get("device_id"),
                    "ip": entry.get("ip"),
                    "ua": entry.get("ua"),
                    "path": entry.get("path"),
                    "lang": entry.get("lang"),
                    "actor_name": entry.get("actor_name"),
                })

        # Newest first. Missing ts goes to the bottom.
        rows.sort(key=lambda x: x.get("ts") or "", reverse=True)

        banner_meta = (
            {
                "id": b.get("id"),
                "title_en": b.get("title_en"),
                "severity": b.get("severity"),
                "require_ack": b.get("require_ack"),
                "created_at": b.get("created_at"),
                "ack_count": len(b.get("acks") or []),
                "dismiss_count": len(b.get("dismisses") or []),
            }
            if b is not None
            else {"id": banner_id, "deleted": True}
        )
        return {"ok": True, "banner": banner_meta, "audit": rows[:500]}

    return router
