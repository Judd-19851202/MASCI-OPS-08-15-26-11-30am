"""
email_routing.py — DB-backed email distribution-list overrides
==============================================================

Lets the admin edit who-gets-what email straight from the admin console
without a redeploy. Falls back to env vars when the DB has no override
so existing deploys keep working.

Routing keys (all optional in DB; env-derived defaults shown):

    always_cc              List[str]   — office CC on compliance kinds
                                          (inspection, meeting, JHA, incident,
                                          QA/QC). Default:
                                          ["jaymn.judd@mascigc.com",
                                           "safety@mascigc.com"]

    safety_forms_to        List[str]   — full To: list for Safety Forms
                                          (issuance, training, return).
                                          Env: SAFETY_FORMS_EMAIL_TO.
                                          Default: ["safety@mascigc.com",
                                                    "jaymn.judd@mascigc.com"]

    leadership_always_to   List[str]   — CC list for the 10 Field Leadership
                                          forms. Env: LEADERSHIP_ALWAYS_TO_1/2.
                                          Default: ["jaymn.judd@mascigc.com",
                                                    "safety@mascigc.com"]

    shop_manager_fallback  str         — single fallback email when shop_users
                                          collection is empty (Pre-Op fail
                                          fan-out). Env: SHOP_MANAGER_EMAIL.
                                          Default: "shopmanager@mascigc.com"

    severe_incident_cc     List[str]   — extra CCs appended for incidents
                                          flagged as Severe. Env:
                                          SEVERE_INCIDENT_CC (comma sep).
                                          Default: []

    backup_email_to        List[str]   — destination for daily auto-backups
                                          and manual "backup + email NOW".
                                          Env: BACKUP_EMAIL_TO. Default: []

Storage
-------
Mongo collection ``email_routing_config``. Single doc with ``_id="default"``.
Created on first write. Reads merge DB doc onto env-derived defaults so
unset keys always resolve to a sensible value.

Caching
-------
Per-process 60-second TTL cache so high-throughput email sends don't slam
Mongo. ``invalidate()`` is called immediately on every PUT so admin edits
take effect within one request, not after a 60-second delay.
"""
from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _env_list(key: str) -> List[str]:
    raw = (os.environ.get(key) or "").strip()
    return [e.strip() for e in raw.split(",") if e.strip()]


def env_defaults() -> Dict[str, Any]:
    """Build the env-derived default config — what the platform falls back
    to when no DB override exists."""
    safety_to = _env_list("SAFETY_FORMS_EMAIL_TO")
    if not safety_to:
        safety_to = ["safety@mascigc.com", "jaymn.judd@mascigc.com"]

    lead_always = [
        os.environ.get("LEADERSHIP_ALWAYS_TO_1", "jaymn.judd@mascigc.com").strip(),
        os.environ.get("LEADERSHIP_ALWAYS_TO_2", "safety@mascigc.com").strip(),
    ]
    lead_always = [e for e in lead_always if e]

    backup_to = _env_list("BACKUP_EMAIL_TO")

    return {
        "always_cc": ["jaymn.judd@mascigc.com", "safety@mascigc.com"],
        "safety_forms_to": safety_to,
        "leadership_always_to": lead_always,
        "shop_manager_fallback": os.environ.get(
            "SHOP_MANAGER_EMAIL", "shopmanager@mascigc.com"
        ).strip(),
        "severe_incident_cc": _env_list("SEVERE_INCIDENT_CC"),
        "backup_email_to": backup_to,
    }


_CACHE: Dict[str, Any] = {"value": None, "ts": 0.0}
_CACHE_TTL_SECONDS = 60


def invalidate() -> None:
    """Force the next ``load`` call to hit Mongo. Call from any PUT
    that mutates the routing doc."""
    _CACHE["value"] = None
    _CACHE["ts"] = 0.0


async def load(db) -> Dict[str, Any]:
    """Return the merged routing config (env defaults overlaid with the
    DB override doc, if any). Uses a 60s per-process cache."""
    now = time.time()
    if _CACHE["value"] is not None and (now - _CACHE["ts"]) < _CACHE_TTL_SECONDS:
        return _CACHE["value"]

    cfg = env_defaults()
    try:
        doc = await db.email_routing_config.find_one({"_id": "default"})
    except Exception:
        doc = None
    if doc:
        for key in (
            "always_cc",
            "safety_forms_to",
            "leadership_always_to",
            "severe_incident_cc",
            "backup_email_to",
        ):
            v = doc.get(key)
            if isinstance(v, list):
                # Treat empty list as "use the DB override of empty" — admins
                # may legitimately want to silence a list (e.g. severe_incident_cc=[])
                cfg[key] = [str(x).strip() for x in v if str(x).strip()]
        if isinstance(doc.get("shop_manager_fallback"), str):
            cfg["shop_manager_fallback"] = doc["shop_manager_fallback"].strip()
        cfg["_meta"] = {
            "updated_at": doc.get("updated_at"),
            "updated_by": doc.get("updated_by"),
            "source": "db",
        }
    else:
        cfg["_meta"] = {"source": "env"}

    _CACHE["value"] = cfg
    _CACHE["ts"] = now
    return cfg


async def get_value(db, key: str) -> Any:
    """Convenience accessor for a single routing key."""
    cfg = await load(db)
    return cfg.get(key)


# Sync env-only fallbacks — use these from sync code paths or import-time
# defaults that can't await. The dynamic admin overrides are NOT visible
# to these; everything that wants live admin overrides must be async.
def env_fallback(key: str) -> Any:
    return env_defaults().get(key)


_VALID_KEYS = {
    "always_cc",
    "safety_forms_to",
    "leadership_always_to",
    "shop_manager_fallback",
    "severe_incident_cc",
    "backup_email_to",
}

_LIST_KEYS = {
    "always_cc",
    "safety_forms_to",
    "leadership_always_to",
    "severe_incident_cc",
    "backup_email_to",
}


def _normalize_value(key: str, value: Any) -> Any:
    """Coerce inputs to the right shape. Lists are stripped + de-duped
    case-insensitively."""
    if key in _LIST_KEYS:
        if isinstance(value, str):
            value = [v.strip() for v in value.split(",")]
        if not isinstance(value, list):
            return []
        out: List[str] = []
        seen: set = set()
        for v in value:
            s = str(v).strip()
            if not s:
                continue
            k = s.lower()
            if k in seen:
                continue
            seen.add(k)
            out.append(s)
        return out
    if key == "shop_manager_fallback":
        return str(value or "").strip()
    return value


async def save(db, updates: Dict[str, Any], updated_by: str = "admin") -> Dict[str, Any]:
    """Merge ``updates`` into the routing config doc. Only valid keys are
    stored. Returns the freshly-merged config (with `_meta`)."""
    set_doc: Dict[str, Any] = {
        "_id": "default",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "updated_by": updated_by,
    }
    for k, v in (updates or {}).items():
        if k not in _VALID_KEYS:
            continue
        set_doc[k] = _normalize_value(k, v)
    await db.email_routing_config.update_one(
        {"_id": "default"}, {"$set": set_doc}, upsert=True
    )
    invalidate()
    return await load(db)
