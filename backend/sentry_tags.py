"""sentry_tags.py · iter430 · Phase 28.2 · Operational tag enrichment.

Auto-attach high-signal operational tags to every Sentry event so a
production exception immediately tells the operator:

    • portal   — which surface emitted the failure (admin/dispatch/
                 shop/safety/hr/field/pm/driver/public)
    • role     — the authenticated actor role (admin/dispatch_user/
                 hr_user/safety_user/shop/field_leadership/pm/driver/
                 public). NOT identity-bearing — just the RBAC class.
    • route    — the FastAPI route template (e.g. `/api/dispatch/
                 assignments/{assignment_id}`), NOT the live path.
                 This lets Sentry group by endpoint, not by random ID.
    • device   — coarse platform inference (`ios`, `android`, `mac`,
                 `windows`, `linux`, `bot`, `unknown`) derived from
                 the User-Agent. NO fingerprinting, NO unique IDs.
    • browser  — coarse browser family (`safari`, `chrome`, `edge`,
                 `firefox`, `unknown`). Same UA-coarsen logic.
    • language — `en` or `es` based on `X-Lang` header (frontend
                 always sends this) or `Accept-Language`.
    • tenant   — `X-Tenant-Id` header value (defaults to `masci`).

No PII. No identifiers. Just operational context.

This is the missing half of Sentry observability: the DSN plumbing and
PII scrubber already ship in `sentry_init.py`; this middleware adds
the operational TAGS so a failure card in Sentry tells you which
portal/role/device combination broke without needing to read the
request payload.
"""
from __future__ import annotations

import re
from typing import Awaitable, Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

try:
    import sentry_sdk
except ImportError:  # Sentry not installed → middleware becomes a no-op
    sentry_sdk = None  # type: ignore[assignment]


# Coarse UA matching — kept intentionally tiny and stable so we never
# have to maintain a UA parser library. We only need bucket names good
# enough to filter Sentry issue lists.
_UA_DEVICE = (
    (re.compile(r"iphone|ipad|ipod", re.I), "ios"),
    (re.compile(r"android", re.I),             "android"),
    (re.compile(r"mac os x|macintosh", re.I),  "mac"),
    (re.compile(r"windows", re.I),             "windows"),
    (re.compile(r"linux", re.I),               "linux"),
    (re.compile(r"bot|crawler|spider", re.I),  "bot"),
)
_UA_BROWSER = (
    # Order matters · Edge identifies itself as "Edg" AND "Chrome" in UA.
    (re.compile(r"edg/", re.I),                "edge"),
    (re.compile(r"firefox/|fxios", re.I),      "firefox"),
    (re.compile(r"chrome/|crios", re.I),       "chrome"),
    (re.compile(r"safari/", re.I),             "safari"),
)


def _coarse_device(ua: str) -> str:
    for pat, name in _UA_DEVICE:
        if pat.search(ua):
            return name
    return "unknown"


def _coarse_browser(ua: str) -> str:
    for pat, name in _UA_BROWSER:
        if pat.search(ua):
            return name
    return "unknown"


# Header → portal classification. Order matters (admin wins if both
# admin + dispatch tokens are present, which would be rare/abusive).
_PORTAL_HEADERS = (
    ("x-admin-token",            "admin"),
    ("x-field-leadership-token", "field"),
    ("x-dispatch-token",         "dispatch"),
    ("x-pm-token",               "pm"),
    ("x-shop-token",             "shop"),
    ("x-safety-token",           "safety"),
    ("x-hr-token",               "hr"),
    ("x-dev-token",              "dev"),
)


def _classify_portal(request: Request) -> str:
    h = request.headers
    for hdr, portal in _PORTAL_HEADERS:
        if h.get(hdr):
            return portal
    # Path-based hints for unauthenticated public flows.
    path = request.url.path
    if path.startswith("/api/driver/") or path.startswith("/api/public/"):
        return "driver"
    if path.startswith("/api/admin-strict/") or path.startswith("/api/admin/"):
        # Hit admin path without a token — still useful to bucket as
        # admin so 401s show up under that portal in Sentry.
        return "admin"
    return "public"


def _normalize_role(portal: str) -> str:
    # Same as portal except dispatch/hr/safety carry the *_user suffix
    # in the actor dicts the routes return. Keep tag string short and
    # stable so Sentry filters don't fragment.
    return portal


def _coarse_language(request: Request) -> str:
    lang = (request.headers.get("x-lang")
            or request.headers.get("accept-language", "")
            or "").lower()
    if lang.startswith("es"):
        return "es"
    return "en"


def _route_template(request: Request) -> Optional[str]:
    """Try to recover the FastAPI route template from the request
    scope so Sentry groups `/dispatch/assignments/<id>` requests into
    one bucket rather than one bucket per UUID."""
    try:
        route = request.scope.get("route")
        if route is not None and getattr(route, "path", None):
            return route.path
    except Exception:  # noqa: BLE001
        pass
    return None


class SentryOperationalTagsMiddleware(BaseHTTPMiddleware):
    """Per-request middleware that pushes operational tags onto the
    Sentry scope. Becomes a no-op when sentry_sdk is not installed
    or no DSN was configured (`init_sentry_if_configured()` returned
    False)."""

    async def dispatch(  # noqa: D401
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        # If Sentry isn't initialised we still want the middleware to
        # be cheap — short-circuit before doing any tagging work.
        if sentry_sdk is None or not getattr(sentry_sdk, "Hub", None):
            return await call_next(request)

        try:
            portal = _classify_portal(request)
            role = _normalize_role(portal)
            ua = request.headers.get("user-agent", "")
            device = _coarse_device(ua)
            browser = _coarse_browser(ua)
            lang = _coarse_language(request)
            tenant = (request.headers.get("x-tenant-id") or "masci").lower()[:64]

            with sentry_sdk.configure_scope() as scope:
                scope.set_tag("portal", portal)
                scope.set_tag("role", role)
                scope.set_tag("device", device)
                scope.set_tag("browser", browser)
                scope.set_tag("language", lang)
                scope.set_tag("tenant", tenant)
                # Mark this as auto-tagged so we can audit coverage.
                scope.set_tag("tagged_by", "sentry_tags.middleware")
        except Exception:  # noqa: BLE001
            # Tagging must never break the request pipeline.
            pass

        response = await call_next(request)

        # The FastAPI route is only resolvable AFTER routing — set the
        # `route` tag at the tail of the request so exceptions raised
        # by the handler get the right template attached via Sentry's
        # transaction context.
        try:
            tmpl = _route_template(request)
            if tmpl and sentry_sdk is not None:
                with sentry_sdk.configure_scope() as scope:
                    scope.set_tag("route", tmpl)
        except Exception:  # noqa: BLE001
            pass

        return response
