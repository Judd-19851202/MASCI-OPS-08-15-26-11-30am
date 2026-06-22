"""
email_routing_v2.py — Track 15.65 DB-first email routing resolver
==================================================================

Wave 1 of the multi-tenant email routing migration. Adds a single
resolver function `resolve(db, route_key, legacy_provider=None)` that:

  * When EMAIL_ROUTING_V2=false (default) → returns exactly what
    `legacy_provider()` returns. Zero behaviour change. Every call site
    that wraps its legacy logic through this resolver is safe to ship
    BEFORE the flag is flipped on.

  * When EMAIL_ROUTING_V2=true → consults `db.email_routes` for the
    requested route_key under the active tenant (`masci` by default).
    Falls back to `legacy_provider()` ONLY if the route doc is missing
    or disabled. For routes flagged `critical=true`, an empty
    resolution raises `UnconfiguredCriticalRouteError` instead of
    silently returning no recipients.

The 6 legacy routes already exposed by `email_routing.py` (always_cc,
safety_forms_to, leadership_always_to, shop_manager_fallback,
severe_incident_cc, backup_email_to) are aliased to the canonical Track
15.65 route keys so the new resolver is the single source of truth
without breaking any existing import.

Audit
-----
Every call to `resolve_and_audit(...)` writes a row in
`db.email_routing_audit_v2` describing the route, the source
(`db | env | legacy | disabled | error`), and the resolved recipient
counts. No body content is logged.

Storage
-------
Collection ``email_routes``. One doc per ``(tenant_key, route_key)``:

  {
    "_id":           "masci::SAFETY_FORMS_TO",
    "tenant_key":    "masci",
    "route_key":     "SAFETY_FORMS_TO",
    "display_name":  "Safety Forms Distribution",
    "description":   "Equipment Issuance / Training / Return.",
    "category":      "compliance",
    "severity":      "info",
    "to":            ["safety@mascigc.com", "jaymn.judd@mascigc.com"],
    "cc":            [],
    "bcc":           [],
    "from_email":    null,
    "reply_to":      null,
    "enabled":       true,
    "critical":      false,
    "owner_role":    "Safety Manager",
    "fallback_env_keys": ["SAFETY_FORMS_EMAIL_TO"],
    "legacy_key":    "safety_forms_to",
    "source":        "seed",
    "version":       1,
    "created_at":    "...",
    "updated_at":    "...",
    "updated_by":    "seed",
    "last_tested_at": null,
    "last_test_status": null
  }

The audit collection ``email_routing_audit_v2`` is APPEND-ONLY. No
mutation of historical rows occurs in Track 15.65.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional


# --- Tenant resolution (Wave 3 will replace with middleware) ---------------
DEFAULT_TENANT_KEY = "masci"


def current_tenant_key() -> str:
    """Resolve the active tenant. Track 15.67 · uses the shared
    tenant_context resolver so future-tenant code paths see consistent
    behaviour. Wave 3 will replace the env default with request-scoped
    middleware."""
    try:
        from tenant_context import resolve_tenant_key  # noqa: PLC0415
        return resolve_tenant_key()
    except Exception:
        return (os.environ.get("EMAIL_ROUTING_TENANT") or DEFAULT_TENANT_KEY).strip().lower() or DEFAULT_TENANT_KEY


# --- Feature flag ----------------------------------------------------------
def routing_v2_enabled() -> bool:
    """When false, every resolver call short-circuits to its legacy
    provider — exact pre-15.65 behaviour. Production stays OFF until
    operator approval."""
    raw = (os.environ.get("EMAIL_ROUTING_V2") or "").strip().lower()
    return raw in ("1", "true", "yes", "on")


# --- Errors ----------------------------------------------------------------
class UnconfiguredCriticalRouteError(RuntimeError):
    """Raised when a route flagged ``critical=true`` resolves to an empty
    recipient list under V2. Never silently drops a critical send."""


# --- Resolution result -----------------------------------------------------
@dataclass
class RouteResolution:
    route_key: str
    tenant_key: str
    to: List[str] = field(default_factory=list)
    cc: List[str] = field(default_factory=list)
    bcc: List[str] = field(default_factory=list)
    from_email: Optional[str] = None
    reply_to: Optional[str] = None
    source: str = "legacy"   # db | env | legacy | disabled | error
    warnings: List[str] = field(default_factory=list)
    error: Optional[str] = None
    critical: bool = False
    enabled: bool = True
    legacy_recipients: Optional[List[str]] = None  # for parity logs

    def is_empty(self) -> bool:
        return not (self.to or self.cc or self.bcc)


# --- Legacy alias map ------------------------------------------------------
# Maps old `email_routing.get_value(...)` keys to the canonical Track 15.65
# route keys. Used by the back-compat shim so existing imports keep working
# even after the new engine is in place.
LEGACY_TO_NEW = {
    "always_cc":             "COMPLIANCE_ALWAYS_CC",
    "safety_forms_to":       "SAFETY_FORMS_TO",
    "leadership_always_to":  "FIELD_LEADERSHIP_ALWAYS_TO",
    "shop_manager_fallback": "PRE_OP_FAIL_FALLBACK",
    "severe_incident_cc":    "INCIDENT_SEVERE_CC",
    "backup_email_to":       "BACKUP_ALERTS",
}


# --- Cache -----------------------------------------------------------------
_ROUTE_CACHE: Dict[str, Any] = {"value": {}, "ts": 0.0}
_ROUTE_CACHE_TTL = 60.0


def invalidate_cache() -> None:
    _ROUTE_CACHE["value"] = {}
    _ROUTE_CACHE["ts"] = 0.0


async def _get_route_doc(db, tenant_key: str, route_key: str) -> Optional[Dict[str, Any]]:
    """Read a single route doc with a 60-s in-process cache."""
    now = time.time()
    if (now - _ROUTE_CACHE["ts"]) > _ROUTE_CACHE_TTL:
        _ROUTE_CACHE["value"] = {}
        _ROUTE_CACHE["ts"] = now
    cache_key = f"{tenant_key}::{route_key}"
    if cache_key in _ROUTE_CACHE["value"]:
        return _ROUTE_CACHE["value"][cache_key]
    try:
        doc = await db.email_routes.find_one({"_id": cache_key})
    except Exception:
        doc = None
    _ROUTE_CACHE["value"][cache_key] = doc
    return doc


# --- Resolver --------------------------------------------------------------
async def resolve(
    db,
    route_key: str,
    legacy_provider: Optional[Callable[[], Any]] = None,
    *,
    tenant_key: Optional[str] = None,
    fallback_env_keys: Optional[List[str]] = None,
    critical: Optional[bool] = None,
) -> RouteResolution:
    """Resolve a route to a concrete RouteResolution.

    Behaviour:
      * `EMAIL_ROUTING_V2=false` → always return what `legacy_provider()`
        returns (or an empty resolution if none provided). Zero
        behaviour change.
      * `EMAIL_ROUTING_V2=true`  → try DB doc → env fallback → legacy.
        Raise on critical+empty.

    Args:
      legacy_provider: zero-arg callable returning the legacy recipient
        list (str | List[str] | dict-with-to/cc/bcc).
      fallback_env_keys: env var names to try if the DB doc is missing
        AND legacy_provider returned nothing.
      critical: when True, an empty resolution raises
        UnconfiguredCriticalRouteError. When None, fall back to the
        `critical` flag on the DB doc.
    """
    tk = (tenant_key or current_tenant_key()).lower()
    legacy_to = _normalize_legacy(legacy_provider() if legacy_provider else None)

    if not routing_v2_enabled():
        # Flag OFF — return legacy exactly, no DB read, no audit pressure.
        return RouteResolution(
            route_key=route_key,
            tenant_key=tk,
            to=legacy_to.get("to", []),
            cc=legacy_to.get("cc", []),
            bcc=legacy_to.get("bcc", []),
            from_email=legacy_to.get("from_email"),
            reply_to=legacy_to.get("reply_to"),
            source="legacy",
            critical=bool(critical),
            enabled=True,
            legacy_recipients=legacy_to.get("to", []) + legacy_to.get("cc", []) + legacy_to.get("bcc", []),
        )

    # V2 path — consult DB doc.
    doc = await _get_route_doc(db, tk, route_key)
    if doc and isinstance(doc, dict):
        if not doc.get("enabled", True):
            return RouteResolution(
                route_key=route_key,
                tenant_key=tk,
                source="disabled",
                enabled=False,
                critical=bool(doc.get("critical", critical)),
                legacy_recipients=legacy_to.get("to", []),
            )
        res = RouteResolution(
            route_key=route_key,
            tenant_key=tk,
            to=[str(x).strip() for x in (doc.get("to") or []) if str(x).strip()],
            cc=[str(x).strip() for x in (doc.get("cc") or []) if str(x).strip()],
            bcc=[str(x).strip() for x in (doc.get("bcc") or []) if str(x).strip()],
            from_email=(doc.get("from_email") or None),
            reply_to=(doc.get("reply_to") or None),
            source="db",
            critical=bool(doc.get("critical", critical)),
            enabled=True,
            legacy_recipients=legacy_to.get("to", []) + legacy_to.get("cc", []) + legacy_to.get("bcc", []),
        )
        if res.is_empty():
            res = _try_fallbacks(res, fallback_env_keys, legacy_to)
        if res.critical and res.is_empty():
            raise UnconfiguredCriticalRouteError(
                f"Critical route {tk}::{route_key} resolved to empty recipient list."
            )
        return res

    # No DB doc — env / legacy fallback.
    res = RouteResolution(
        route_key=route_key,
        tenant_key=tk,
        source="env",
        critical=bool(critical),
        enabled=True,
    )
    res = _try_fallbacks(res, fallback_env_keys, legacy_to)
    if res.is_empty() and legacy_provider is not None:
        res.to = legacy_to.get("to", [])
        res.cc = legacy_to.get("cc", [])
        res.bcc = legacy_to.get("bcc", [])
        res.from_email = legacy_to.get("from_email")
        res.reply_to = legacy_to.get("reply_to")
        if res.to or res.cc or res.bcc:
            res.source = "legacy"
            res.warnings.append("DB route missing — fell back to legacy provider")
    if res.critical and res.is_empty():
        raise UnconfiguredCriticalRouteError(
            f"Critical route {tk}::{route_key} resolved to empty recipient list."
        )
    return res


def _try_fallbacks(
    res: RouteResolution,
    fallback_env_keys: Optional[List[str]],
    legacy_to: Dict[str, Any],
) -> RouteResolution:
    if res.to or res.cc or res.bcc:
        return res
    for k in fallback_env_keys or []:
        v = (os.environ.get(k) or "").strip()
        if v:
            res.to = [e.strip() for e in v.split(",") if e.strip()]
            res.source = "env"
            return res
    if legacy_to.get("to") or legacy_to.get("cc") or legacy_to.get("bcc"):
        res.to = legacy_to.get("to", [])
        res.cc = legacy_to.get("cc", [])
        res.bcc = legacy_to.get("bcc", [])
        res.from_email = legacy_to.get("from_email")
        res.reply_to = legacy_to.get("reply_to")
        res.source = "legacy"
        res.warnings.append("DB+env missing — fell back to legacy provider")
    return res


def _normalize_legacy(value: Any) -> Dict[str, Any]:
    """Coerce a legacy provider return value into {to, cc, bcc, from_email, reply_to}."""
    if value is None:
        return {"to": [], "cc": [], "bcc": []}
    if isinstance(value, str):
        return {"to": [e.strip() for e in value.split(",") if e.strip()], "cc": [], "bcc": []}
    if isinstance(value, list):
        return {"to": [str(e).strip() for e in value if str(e).strip()], "cc": [], "bcc": []}
    if isinstance(value, dict):
        return {
            "to":  [str(e).strip() for e in (value.get("to") or []) if str(e).strip()],
            "cc":  [str(e).strip() for e in (value.get("cc") or []) if str(e).strip()],
            "bcc": [str(e).strip() for e in (value.get("bcc") or []) if str(e).strip()],
            "from_email": (value.get("from_email") or None),
            "reply_to":   (value.get("reply_to") or None),
        }
    return {"to": [], "cc": [], "bcc": []}


# --- Audit -----------------------------------------------------------------
async def write_audit(
    db,
    *,
    route_key: str,
    tenant_key: str,
    source: str,
    to_count: int,
    cc_count: int,
    bcc_count: int,
    subject: Optional[str] = None,
    sender_email: Optional[str] = None,
    resend_message_id: Optional[str] = None,
    status: str = "ok",
    error: Optional[str] = None,
    calling_module: Optional[str] = None,
    dry_run: bool = False,
) -> None:
    """Append-only audit row. Best-effort — never raises."""
    try:
        await db.email_routing_audit_v2.insert_one({
            "route_key": route_key,
            "tenant_key": tenant_key,
            "source": source,
            "resolved_to_count": int(to_count),
            "resolved_cc_count": int(cc_count),
            "resolved_bcc_count": int(bcc_count),
            "subject": (subject or "")[:240],
            "sender_email": sender_email,
            "resend_message_id": resend_message_id,
            "status": status,
            "error": (error or None),
            "calling_module": calling_module,
            "dry_run": bool(dry_run),
            "ts": datetime.now(timezone.utc).isoformat(),
        })
    except Exception:
        # Audit must never break a real send.
        pass


# --- Resolve + audit convenience -------------------------------------------
async def resolve_and_audit(
    db,
    route_key: str,
    legacy_provider: Optional[Callable[[], Any]] = None,
    *,
    tenant_key: Optional[str] = None,
    fallback_env_keys: Optional[List[str]] = None,
    critical: Optional[bool] = None,
    subject: Optional[str] = None,
    calling_module: Optional[str] = None,
    dry_run: bool = False,
) -> RouteResolution:
    res = await resolve(
        db, route_key, legacy_provider,
        tenant_key=tenant_key,
        fallback_env_keys=fallback_env_keys,
        critical=critical,
    )
    await write_audit(
        db,
        route_key=res.route_key,
        tenant_key=res.tenant_key,
        source=res.source,
        to_count=len(res.to),
        cc_count=len(res.cc),
        bcc_count=len(res.bcc),
        subject=subject,
        status=("disabled" if res.source == "disabled" else "resolved"),
        error=res.error,
        calling_module=calling_module,
        dry_run=dry_run,
    )
    return res


# --- Back-compat shim for `email_routing.get_value(db, legacy_key)` --------
async def legacy_get_value(db, legacy_key: str) -> Any:
    """Drop-in replacement for `email_routing.get_value` that consults the
    new route catalog when the flag is on. Returns the same shape the old
    callers expect (list for list routes, str for `shop_manager_fallback`).
    """
    from email_routing import get_value as _legacy_get
    if not routing_v2_enabled():
        return await _legacy_get(db, legacy_key)
    new_key = LEGACY_TO_NEW.get(legacy_key)
    if not new_key:
        return await _legacy_get(db, legacy_key)
    res = await resolve(db, new_key, legacy_provider=lambda: None)
    if res.source in ("db",) and not res.is_empty():
        if legacy_key == "shop_manager_fallback":
            return res.to[0] if res.to else ""
        if legacy_key == "always_cc":
            return res.to + res.cc
        return res.to or res.cc or res.bcc
    # Empty DB doc → defer to the legacy resolver (preserves env defaults
    # exactly as Track 15.62 / 15.63 production runs).
    return await _legacy_get(db, legacy_key)
