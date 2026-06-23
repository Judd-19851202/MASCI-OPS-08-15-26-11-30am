# TRACK 15.69 · Route Inventory (Phase 1)

_Generated 2026-06-22 · Preview cluster_

## All 19 Routes — Recipients, Senders, Critical Status

Pulled live from `email_routes` collection (tenant_key=`masci`).
Persisted JSON: `/app/test_reports/track_15_69_route_inventory.json`.

| # | route_key | crit | enabled | to count | cc | bcc | from_email | Notes |
|---|---|:-:|:-:|:-:|:-:|:-:|---|---|
| 1 | `ACCOUNT_INVITES_FROM` | · | ✅ | 0 | 0 | 0 | `noreply@mascidocs.com` | Sender-identity only; no recipients (correct by design) |
| 2 | `ADMIN_DEAD_LETTER_TO` | · | ✅ | 1 | 0 | 0 | (default `noreply@mascidocs.com`) | Catch-all for unresolved PM routing |
| 3 | `BACKUP_ALERTS` | 🔴 | ✅ | 1 | 0 | 0 | (default) | Daily backup success/failure |
| 4 | `COMPLIANCE_ALWAYS_CC` | · | ✅ | 2 | 0 | 0 | (default) | Always-CC compliance recipients |
| 5 | `DISPATCH_ROLE_TO` | · | ✅ | 1 | 0 | 0 | (default) | Dispatch role-based recipients |
| 6 | `EXECUTIVE_DIGEST` | · | ✅ | 1 | 0 | 0 | (default) | Executive summary digest |
| 7 | `FIELD_LEADERSHIP_ALWAYS_TO` | · | ✅ | 2 | 0 | 0 | (default) | FL ops always-to |
| 8 | `HEALTH_ALERTS` | 🔴 | ✅ | 1 | 0 | 0 | (default) | Health monitor critical alerts |
| 9 | `INCIDENT_SEVERE_CC` | · | ✅ | 0 | 0 | 0 | (default) | Severe-incident CC (env-driven; empty in DB) |
| 10 | `OPERATOR_DIGEST_RECIPIENTS` | · | ✅ | 1 | 0 | 0 | (default) | Operator daily digest |
| 11 | `OUTAGE_ALERTS` | 🔴 | ✅ | 1 | 0 | 0 | (default) | Platform outage alerts |
| 12 | `PASSWORD_RESET_MONITORING_TO` | · | ❌ | 0 | 0 | 0 | (default) | DISABLED (intentional — observation route) |
| 13 | `PAYROLL_VARIANCE_TO` | · | ✅ | 1 | 0 | 0 | (default) | Payroll variance alerts |
| 14 | `PRE_OP_FAIL_FALLBACK` | · | ✅ | 1 | 0 | 0 | (default) | Pre-Op fail → shop manager fallback |
| 15 | `SAFETY_DIGEST_TO` | · | ✅ | 1 | 0 | 0 | (default) | Safety digest daily summary |
| 16 | `SAFETY_FORMS_TO` | · | ✅ | 2 | 0 | 0 | (default) | All safety-form submissions (daily reports, incidents, inspections, meetings, QAQC) |
| 17 | `SUPER_ADMIN_TO` | 🔴 | ✅ | 1 | 0 | 0 | (default) | Super-admin escalation |
| 18 | `TRENCH_SAFETY_PULSE_SAFETY` | · | ✅ | 1 | 0 | 0 | (default) | Trench pulse → safety team |
| 19 | `TRENCH_SAFETY_PULSE_SHOP` | · | ✅ | 1 | 0 | 0 | (default) | Trench pulse → shop team |

## Aggregate

| Metric | Value |
|---|---:|
| Total routes | **19** |
| Critical routes | **4** (BACKUP_ALERTS, HEALTH_ALERTS, OUTAGE_ALERTS, SUPER_ADMIN_TO) |
| Disabled routes | **1** (PASSWORD_RESET_MONITORING_TO — intentional) |
| Routes with at least one recipient | 17 |
| Routes intentionally empty | 2 (ACCOUNT_INVITES_FROM — sender-only; INCIDENT_SEVERE_CC — env-driven cc, picked up at send-time) |
| Routes with admin-customised `from_email` | 1 (ACCOUNT_INVITES_FROM = `noreply@mascidocs.com`) |
| Routes using tenant-branding default sender | 18 |

## Templates / Workflow Sources

See `TRACK_15_69_ROUTE_OWNERSHIP_AUDIT.md` for the route → workflow mapping.

## Verdict

✅ **PASS** — full route inventory present, no unknown recipients, no
unknown senders, no orphan routes.
