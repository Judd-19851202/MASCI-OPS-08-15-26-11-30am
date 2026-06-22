# TRACK 15.67 · Phase 3 · Sender Swap Completion

_Status: ✅ SHIPPED · 2026-06-22_

## Goal
Replace every direct `os.environ.get("SENDER_EMAIL", …)` call site with
`branding_resolver.resolve_sender_email(db, …)` so that no email
delivery path can leak the MASCI sender to a non-MASCI tenant.

## New helper (`branding_resolver.py`)
```python
async def resolve_sender_email(db, *, route_key=None,
                               safe_fallback="onboarding@resend.dev") -> str:
    """Tenant-safe sender. Never raises. Logs WARNING when a
    non-MASCI tenant falls back."""
async def resolve_reply_to_email(db) -> str: ...
```

The compat wrapper:
- Resolves through `resolve_sender(db)` (route doc → tenant_branding → env_masci_only → hard fail).
- Returns the `safe_fallback` when the resolver hard-fails on a
  non-MASCI tenant (logs a clear WARNING line — never silently
  delivers to a MASCI sender).

## Migrated call sites (30 total)

| File | Sites |
|---|---|
| `backend/server.py` | 19 (shop-portal forgot-password, pm-portal forgot-password, backup-watchdog email, R2 verification, route test endpoint, all admin-route route-test sites, all branded-email send wrappers including the `(SENDER_EMAIL or "noreply@mascidocs.com")` family) |
| `backend/phase4.py` | 1 (`_dispatch_email` — now takes `db`) |
| `backend/outage_alerts.py` | 1 |
| `backend/health_monitor.py` | 1 (`_send_alert`, via `_resolve_sender_email_safe(db)`) |
| `backend/backup_verification.py` | 1 |
| `backend/routes/pm_routes.py` | 1 (PM forgot-password) |
| `backend/routes/safety_forms.py` | 1 (FSI dispatch) |
| `backend/routes/shop_parts.py` | 1 (parts order email) |
| `backend/routes/pm_admin.py` | 1 (PM welcome email) |
| `backend/lib/fsi_email_sender.py` | 1 (`fsi_send_email` — now takes optional `db`) |

Remaining literal `os.environ.get("SENDER_EMAIL", …)` lookups:
- `server.py:13491` — the **admin branding GET endpoint** that returns
  env defaults to the admin UI for a fresh MASCI tenant. Now gated on
  `tenant_context.is_masci(tk)` — non-MASCI tenants get a blank doc to
  populate. **Intentional, customer-safe.**
- Internal safe-fallback strings inside `branding_resolver`,
  `outage_alerts`, `health_monitor`, `phase4`, `fsi_email_sender` —
  only reached when `db is None` or when the resolver throws.
  **Intentional, defensive.**
- `backend/scripts/track_15_65_seed_email_routes.py` — one-time
  MASCI-only seed script. **Intentional.**
- `backend/scripts/track_15_67_second_tenant_simulation.py:128` —
  explicitly sets `SENDER_EMAIL=noreply@mascidocs.com` to PROVE the
  resolver refuses it on a non-MASCI tenant. **Intentional.**
- `backend/ops_manual.py` — operator runbook text. **Internal-only.**

## Proof
Second-tenant simulation:

```
sender_identity_from_branding             PASS  (source=branding)
sender_no_masci_leak                      PASS  (from=noreply@demo-co.example)
resolve_sender_email_returns_demo         PASS
resolve_sender_email_no_masci_leak        PASS
sender_swap_ignores_env_for_non_masci     PASS  (env SENDER_EMAIL=noreply@mascidocs.com IGNORED)
non_masci_tenant_refuses_env_fallback     PASS  (UnconfiguredSenderError raised)
```

MASCI parity: **19/19** — sender identity unchanged on MASCI tenant.
