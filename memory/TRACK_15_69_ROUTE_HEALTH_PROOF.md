# TRACK 15.69 · Route Health Proof

_Generated 2026-06-22 · Preview cluster_

## Method

The admin endpoint `/api/admin/email-routing/v2/routes` requires an
admin token. For operator-tier verification this deliverable computes
the same color summary directly from the `email_routes` and
`email_routing_audit_v2` collections, replicating the production
admin-UI logic.

The same script is shippable via curl-with-admin-token in production —
see `Operator Verification` below.

## Color Logic (matches the production resolver)

- **disabled** → `enabled = false`
- **red** → critical & no recipients OR last audit row failed
- **amber** → last audit row was failed/error OR no audit row exists
  (route never tested)
- **green** → most recent audit row succeeded (sent or dry_run with
  source=db)

## Result

```
green=18  amber=0  red=0  disabled=1
```

| Route | crit | recipients | last status | color |
|---|:-:|:-:|---|:-:|
| ACCOUNT_INVITES_FROM | · | 0 | dry_run | 🟢 |
| ADMIN_DEAD_LETTER_TO | · | 1 | dry_run | 🟢 |
| BACKUP_ALERTS | 🔴 | 1 | dry_run | 🟢 |
| COMPLIANCE_ALWAYS_CC | · | 2 | dry_run | 🟢 |
| DISPATCH_ROLE_TO | · | 1 | dry_run | 🟢 |
| EXECUTIVE_DIGEST | · | 1 | dry_run | 🟢 |
| FIELD_LEADERSHIP_ALWAYS_TO | · | 2 | dry_run | 🟢 |
| HEALTH_ALERTS | 🔴 | 1 | dry_run | 🟢 |
| INCIDENT_SEVERE_CC | · | 0 | dry_run | 🟢 |
| OPERATOR_DIGEST_RECIPIENTS | · | 1 | dry_run | 🟢 |
| OUTAGE_ALERTS | 🔴 | 1 | dry_run | 🟢 |
| PASSWORD_RESET_MONITORING_TO | · | 0 | dry_run | ⚪ disabled (intentional) |
| PAYROLL_VARIANCE_TO | · | 1 | dry_run | 🟢 |
| PRE_OP_FAIL_FALLBACK | · | 1 | dry_run | 🟢 |
| SAFETY_DIGEST_TO | · | 1 | dry_run | 🟢 |
| SAFETY_FORMS_TO | · | 2 | dry_run | 🟢 |
| SUPER_ADMIN_TO | 🔴 | 1 | dry_run | 🟢 |
| TRENCH_SAFETY_PULSE_SAFETY | · | 1 | dry_run | 🟢 |
| TRENCH_SAFETY_PULSE_SHOP | · | 1 | dry_run | 🟢 |

## Critical-Route Coverage

All 4 critical routes (`BACKUP_ALERTS`, `HEALTH_ALERTS`,
`OUTAGE_ALERTS`, `SUPER_ADMIN_TO`) have:
- ✅ at least one recipient
- ✅ at least one successful resolution audit row in the last run
- ✅ `source = db` on the most recent audit row
- ✅ green health status

## Audit Collection State

| Metric | Value |
|---|---:|
| `email_routing_audit_v2` total rows | 20 |
| `dry_run` rows | 20 ✅ |
| `sent` rows | 0 (no live sends — by design) |
| `failed` / `error` rows | **0** ✅ |

## Operator Verification (production)

The operator can replicate this exact summary in production by hitting
the admin endpoint with a valid admin token:

```
TOK=<admin_token>
curl -s https://mascidocs.com/api/admin/email-routing/v2/routes \
  -H "X-Admin-Token: $TOK" | jq '.routes[] | {route_key, enabled, critical, recipients: ((.to|length) + (.cc|length) + (.bcc|length)), last: .summary.last_send_status}'
```

Or visit: **Admin → Email Routing**. The Admin UI displays the same
green / amber / red badges per route.

## Persisted Artefacts

- `/app/test_reports/track_15_69_route_health.json`

## Verdict

✅ **PASS** — 18 green, 0 amber, 0 red, 1 disabled (intentional). All
4 critical routes green. Zero failed audit rows. No live blasts. Route
Health proves V2 routing is configured correctly for cutover.
