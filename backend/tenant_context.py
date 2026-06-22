"""
tenant_context.py — Track 15.67 Phase 1 · Tenant resolution helper
==================================================================

Single source of truth for "what tenant is this request for?". Used by:
  * email_routing_v2.resolve(...)
  * branding resolvers
  * audit row writes
  * route testing
  * future onboarding flows

Resolution order (highest precedence first):
  1. Explicit `tenant_key` argument passed by the caller (used by
     synthetic-tenant simulation and admin tooling).
  2. `request.state.tenant_key` set by FastAPI middleware from one of:
        - JWT/admin token's `tenant_key` claim (Wave 3 token rotation)
        - `X-Tenant-Key` request header (admin tooling only)
        - host subdomain (`acme.mascidocs.com` → `acme`)
  3. Environment default `EMAIL_ROUTING_TENANT` (preview + production
     today resolve to `masci`).
  4. Hard-coded final fallback `masci` ONLY when no other resolution
     succeeded AND `STRICT_TENANT_RESOLUTION=false` (default). With
     `STRICT_TENANT_RESOLUTION=true` set in env, the helper RAISES
     `UnresolvedTenantError` instead of silently defaulting — this is
     the mode used by the second-tenant simulation to prove the
     resolver never silently falls back to MASCI.

Future tenants are first-class: passing a `tenant_key` argument or
setting the header / claim / subdomain produces a clean, MASCI-free
resolution path with no hidden defaults.
"""
from __future__ import annotations

import os
from contextvars import ContextVar
from typing import Optional

DEFAULT_TENANT_KEY = "masci"

# Request-scoped tenant context. Middleware sets this; resolvers read it.
_current_tenant: ContextVar[Optional[str]] = ContextVar("masci_current_tenant", default=None)


class UnresolvedTenantError(RuntimeError):
    """Raised when STRICT_TENANT_RESOLUTION=true AND no tenant could be
    resolved. Surfaced to the second-tenant simulation as proof that the
    routing engine never silently inherits MASCI when a tenant is
    expected to be explicit."""


def set_current_tenant(tenant_key: Optional[str]) -> None:
    """Middleware-only entry point. Called once per request."""
    if tenant_key:
        _current_tenant.set(tenant_key.strip().lower() or None)
    else:
        _current_tenant.set(None)


def resolve_tenant_key(explicit: Optional[str] = None) -> str:
    """Return the active tenant for the current call site. Order
    documented at top of file. Raises UnresolvedTenantError when
    STRICT_TENANT_RESOLUTION=true and no resolution succeeds."""
    if explicit:
        s = str(explicit).strip().lower()
        if s:
            return s
    ctx = _current_tenant.get()
    if ctx:
        return ctx
    env_default = (os.environ.get("EMAIL_ROUTING_TENANT") or "").strip().lower()
    if env_default:
        return env_default
    strict = (os.environ.get("STRICT_TENANT_RESOLUTION") or "").strip().lower()
    if strict in ("1", "true", "yes", "on"):
        raise UnresolvedTenantError(
            "No tenant resolved (no explicit arg, no request context, no env default) "
            "and STRICT_TENANT_RESOLUTION is enabled."
        )
    return DEFAULT_TENANT_KEY


def is_masci(tenant_key: Optional[str] = None) -> bool:
    """Convenience: did the resolver pick MASCI? Used by sender swap to
    decide whether a MASCI env fallback may be honoured."""
    return resolve_tenant_key(tenant_key) == DEFAULT_TENANT_KEY
