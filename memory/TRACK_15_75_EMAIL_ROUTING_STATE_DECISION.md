# TRACK 15.75 · Phase 11 — Email Routing State Decision

Evidence: `/tmp/t1575_phase1_state.py` env + `email_routes` snapshot.

## Current State (preview)

| Variable / Item | Value | Comment |
|---|---|---|
| `EMAIL_ROUTING_V2` | **`true`** | V2 is **ACTIVE** — not dormant |
| `AUTO_EMAIL_REPORTS` | `true` | Auto dispatch enabled |
| `RESEND_API_KEY` | present | Resend wired |
| `ADMIN_DEAD_LETTER_EMAIL` | `safety@mascigc.com` | masci env fallback |
| `APP_ENV` | `preview` | not production |
| `TENANT_KEY` | _(unset)_ | resolved per-request via `tenant_context.resolve_tenant_key()` |
| `email_routes` collection | 31 rows | masci × 19 + customer_2_deploy_test × 6 + customer_3_deploy_test × 6 |
| Critical routes for masci | 4 / 4 populated | `ADMIN_DEAD_LETTER_TO`, `BACKUP_ALERTS`, `HEALTH_ALERTS`, `OUTAGE_ALERTS` all configured |
| `route_counts.critical_empty` (live API) | 0 | proven by `/api/admin/email-routing/v2/status` |
| `audit_counters.errors_last_24h` | 0 | no V2 send errors |

## Legacy vs V2

* The V2 routing engine (`email_routing_v2.resolve_and_audit`,
  `write_audit`) is the **active path** for the
  `RouteResolution`-style routes (BACKUP / HEALTH / OUTAGE / digest
  / etc.).
* Workflow auto-emails (DR / meeting / inspection / incident / jha /
  qaqc / equipment-inspection) flow through
  `pm_routing.recipients_for_record_async`, then are dispatched
  through the shared send path which itself writes a V2 audit row.
* There is **no purely legacy / V2-bypassing path** in production
  use today. Track 15.32 retired the shared-PM HMAC token path.
  Track 15.30 retired the static Shop HMAC.

## Workflow → routing engine map

| Workflow | Resolver | Send path | Audit |
|---|---|---|---|
| Daily Report | `recipients_for_record_async` (PM_ONLY) | `schedule_auto_email("daily-report", …)` | V2 audit row |
| Meeting / Inspection / JHA / Incident / QAQC | `recipients_for_record_async` (compliance) | `schedule_auto_email(kind, …)` | V2 audit row |
| Equipment Pre-Op | `recipients_for_record_async` (PM_ONLY) + `PRE_OP_FAIL_FALLBACK` | `schedule_auto_email("equipment-inspection", …)` | V2 audit row |
| Backup / Health / Outage | `email_routing_v2.resolve_and_audit` | direct | V2 audit row |
| Operator Digest | DB route `OPERATOR_DIGEST_RECIPIENTS` | scheduler | V2 audit row |

## Decision

**KEEP V2 ON.** No action required.

* All 4 critical routes are populated for `masci`.
* Tenants 2 + 3 have their own dead-letter / safety / backup /
  health / outage / super-admin route rows in place
  (`customer_2_deploy_test::*`, `customer_3_deploy_test::*`).
* Audit truth is restored (Track 15.74 fix).
* `errors_last_24h = 0`.

**No flip / toggle needed in this track.** This is the **certified
intentional state**.

If a future track wishes to flip OFF: prerequisite is to populate
the legacy `PM_TABLE` fallback (env `PM_SEED_DIRECTORY`) for the
masci tenant — currently relied on only as a safety net.
