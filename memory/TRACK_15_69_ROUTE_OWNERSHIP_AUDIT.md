# TRACK 15.69 · Route Ownership Audit (Phase 2)

_Generated 2026-06-22_

For every route: business owner, workflow source, criticality, and the
production code path that resolves the route.

## Ownership Table

| Route Key | Current Recipients | Sender Identity | Workflow Sources (code) | Business Owner | Critical |
|---|---|---|---|---|:-:|
| `ACCOUNT_INVITES_FROM` | none (sender-only) | `noreply@mascidocs.com` | `routes/auth_directory_routes.py` (account invite emails) | IT Admin | N |
| `ADMIN_DEAD_LETTER_TO` | `safety@mascigc.com` | `noreply@mascidocs.com` | `pm_routing.py:370`, `lib/field_submitter_identity.py:189` (any unroutable PM event) | Safety Lead | N |
| `BACKUP_ALERTS` | `jaymn.judd@mascigc.com` | `noreply@mascidocs.com` | `server.py:6448, 6534, 7277` (daily backup verify/fail/missing) | Operations Manager | **Y** |
| `COMPLIANCE_ALWAYS_CC` | `safety@mascigc.com`, `compliance@mascigc.com` | `noreply@mascidocs.com` | `pm_routing.py:277` (all PM emails CC compliance) | Compliance Officer | N |
| `DISPATCH_ROLE_TO` | dispatch role-distro | `noreply@mascidocs.com` | dispatch chain (driver assignments) | Dispatch Lead | N |
| `EXECUTIVE_DIGEST` | executive distro | `noreply@mascidocs.com` | scheduled executive digest job | Executive Sponsor | N |
| `FIELD_LEADERSHIP_ALWAYS_TO` | superintendent distro | `noreply@mascidocs.com` | `routes/field_leadership.py:769` (FL daily ops) | Field Leadership | N |
| `HEALTH_ALERTS` | `safety@mascigc.com` | `noreply@mascidocs.com` | `health_monitor.py:67` (every backend health failure) | Operations Manager | **Y** |
| `INCIDENT_SEVERE_CC` | env-driven, currently empty | `noreply@mascidocs.com` | `server.py:12884` (severe-incident escalation CC) | Safety Lead | N |
| `OPERATOR_DIGEST_RECIPIENTS` | `jaymn.judd@mascigc.com` | `noreply@mascidocs.com` | `lib/operator_digest.py:336` (hourly operator digest) | Operations Manager | N |
| `OUTAGE_ALERTS` | `jaymn.judd@mascigc.com` | `noreply@mascidocs.com` | `outage_alerts.py:108` (platform outage detection) | Operations Manager | **Y** |
| `PASSWORD_RESET_MONITORING_TO` | (disabled) | `noreply@mascidocs.com` | observation route (not currently subscribed) | IT Admin | N |
| `PAYROLL_VARIANCE_TO` | payroll role | `noreply@mascidocs.com` | payroll variance alerts | HR / Payroll | N |
| `PRE_OP_FAIL_FALLBACK` | shop manager | `noreply@mascidocs.com` | pre-op fail chain (legacy: `shop_manager_fallback`) | Shop Manager | N |
| `SAFETY_DIGEST_TO` | `safety@mascigc.com` | `noreply@mascidocs.com` | `safety_digest.py:89` (daily safety digest) | Safety Lead | N |
| `SAFETY_FORMS_TO` | `safety@mascigc.com`, super-admin | `noreply@mascidocs.com` | `routes/safety_forms.py:817` (daily reports, incidents, inspections, meetings, QAQC) | Safety Lead | N |
| `SUPER_ADMIN_TO` | `jaymn.judd@mascigc.com` | `noreply@mascidocs.com` | super-admin escalation chain | Super Admin | **Y** |
| `TRENCH_SAFETY_PULSE_SAFETY` | `safety@mascigc.com` | `noreply@mascidocs.com` | trench safety pulse digest | Safety Lead | N |
| `TRENCH_SAFETY_PULSE_SHOP` | shop manager | `noreply@mascidocs.com` | trench safety pulse digest | Shop Manager | N |

## Verification

| Check | Result |
|---|:-:|
| No unknown route owner | ✅ |
| No unknown recipient | ✅ (every address resolves to a mascigc.com domain person or role distro) |
| No unknown sender | ✅ (all senders resolve via `branding_resolver.resolve_sender`; current source = `env_masci_only` because tenant_branding doesn't override) |
| No orphan route | ✅ (every route in the inventory has a documented workflow source) |

## Sender Identity Resolution Chain (verified per Phase 6 / FM3 test)

For each route, sender is resolved in this priority:

1. Route doc `from_email` (admin override) — currently only
   `ACCOUNT_INVITES_FROM`.
2. Tenant branding `from_email` — not currently set for MASCI.
3. Env `SENDER_EMAIL` (MASCI-tenant fallback only) → `noreply@mascidocs.com`.
4. Hard-fail for any other tenant (refuses to send without a sender).

Verified live: `FM3_sender_resolution` PASS in
`/app/test_reports/track_15_69_failure_modes.json`.

## Verdict

✅ **PASS** — every route has a named owner, a documented workflow
source, a verified sender, and a recipient list (or is intentionally
empty / disabled with explanation).
