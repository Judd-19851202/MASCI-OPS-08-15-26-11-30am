# TRACK 15.67 — Sender Identity Foundation (Phase 1)

**Date:** 2026-06-22  
**Files shipped:** `backend/branding_resolver.py`

## 1. Resolver

`resolve_sender(db, tenant_key=None, route_key=None)` returns a `SenderIdentity(from_email, reply_to, from_display_name, source)`. Source is one of `route | branding | env_masci_only | error`.

Precedence:
1. Per-route `from_email` / `reply_to` on the `email_routes` doc.
2. Tenant `tenant_branding.from_email` / `reply_to` / `sender_name`.
3. **MASCI tenant only:** env vars `SENDER_EMAIL` / `REPLY_TO_EMAIL` (this is the *only* place those env vars are honoured for sender resolution after Phase 2 completes).
4. **Non-MASCI tenant with no branding:** raises `UnconfiguredSenderError`.

## 2. Why env fallback is gated to MASCI

The single most dangerous Customer #2 leakage path is `os.environ.get("SENDER_EMAIL", "noreply@mascidocs.com")` — a tenant onboarded without explicit branding would silently inherit MASCI's sender. The resolver makes this impossible: **env fallback only fires when `is_masci(tk) == True`**. A second-tenant simulation that removed branding and tried to send raised the exception as expected (proof in `track_15_67_second_tenant_simulation.json`).

## 3. Phase 1 wiring

The resolver is in place and proven. The 20 historical send sites that still call `os.environ.get("SENDER_EMAIL", ...)` directly are scheduled for Phase 2 migration — wrapping each with `await resolve_sender(db)` and substituting the returned `from_email` / `reply_to` in the Resend payload. Until Phase 2 lands those sites continue to work exactly as today for MASCI.

## 4. Proof points (second-tenant simulation, 2026-06-22)

| Check | Result |
|---|:-:|
| `sender_identity_from_branding` (`from=noreply@demo-co.example`, `source=branding`) | ✅ |
| `sender_no_masci_leak` (returned from_email contains no `mascigc`/`mascidocs`/`jaymn`/`MASCI`/`masci`) | ✅ |
| `non_masci_tenant_refuses_env_fallback` (resolver raised `UnconfiguredSenderError` with MASCI env vars set) | ✅ |

## 5. Hard-rule compliance
* ✅ No hidden noreply fallbacks for non-MASCI tenants.
* ✅ No hidden mascidocs.com fallbacks for non-MASCI tenants.
* ✅ Sender error surfaces loudly, never silently sends from MASCI.
* ✅ Customer #2 cannot inherit MASCI sender unless explicitly configured.
