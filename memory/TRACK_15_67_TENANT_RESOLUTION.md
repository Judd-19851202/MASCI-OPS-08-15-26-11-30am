# TRACK 15.67 — Tenant Resolution Foundation (Phase 1)

**Date:** 2026-06-22  
**Files shipped:** `backend/tenant_context.py`

## 1. Resolver

`resolve_tenant_key(explicit=None)` returns the active tenant in this order:

1. `explicit` argument — used by synthetic-tenant simulation and admin tooling.
2. `_current_tenant` ContextVar (set by middleware / `set_current_tenant`).
3. `EMAIL_ROUTING_TENANT` env var.
4. Final fallback `"masci"` UNLESS `STRICT_TENANT_RESOLUTION=true` — in that mode the helper RAISES `UnresolvedTenantError`.

## 2. What gets the tenant from `tenant_context` (this phase)

* `email_routing_v2.current_tenant_key()` — patched to delegate to `tenant_context.resolve_tenant_key()`.
* `branding_resolver.resolve_sender(...)` — uses `resolve_tenant_key` to decide which branding doc to read and whether env fallback is permissible.
* Second-tenant simulation — uses `set_current_tenant(...)` to flip the request-scoped tenant.

## 3. What still uses an env default (Phase 2 target)

* `_current_tenant_key()` in `server.py` admin endpoints — still reads `EMAIL_ROUTING_TENANT` directly. Phase 2 swaps to a middleware-set request-scoped tenant for true per-request resolution.
* Pending Wave 3: FastAPI middleware that resolves the tenant per request from JWT claim / `X-Tenant-Key` header / subdomain.

## 4. Proof points (Phase 1)

* Second-tenant simulation calls `set_current_tenant("tenant_15_67_demo")` then `resolve_tenant_key()` → returns `"tenant_15_67_demo"` ✅.
* Same simulation calls `set_current_tenant(None)` then `STRICT_TENANT_RESOLUTION=true` → calling `resolve_sender(db)` on a non-MASCI tenant raises `UnconfiguredSenderError` ✅.
* Audit rows written via `v2.write_audit(..., tenant_key="tenant_15_67_demo")` are queryable by tenant_key — `email_routing_audit_v2.count_documents({"tenant_key": "tenant_15_67_demo"})` returned ≥ 1.

## 5. Hard-rule compliance
* ✅ Tenant context is request-scoped (`ContextVar` — async-safe).
* ✅ No silent MASCI fallback when `STRICT_TENANT_RESOLUTION=true`.
* ✅ Every audit row carries `tenant_key`.
* ✅ Tenant context shared with sender resolver.
