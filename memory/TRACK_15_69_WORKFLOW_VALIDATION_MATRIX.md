# TRACK 15.69 · Workflow Validation Matrix (Phase 4)

_Generated 2026-06-22 · Preview cluster, flag-ON dry-run_

**Pass: 23 / 23 workflows · Fail: 0 / 23**

Persisted JSON: `/app/test_reports/track_15_69_workflow_matrix.json`

## Method

The 12 required workflows from the directive (plus 11 supplementary
routes that have their own production code paths) were resolved live
through `email_routing_v2.resolve()` with `EMAIL_ROUTING_V2=true`.

For each workflow we captured:
1. **Route key** — derived from grep of the production source.
2. **Code reference** — file:line that invokes the route.
3. **Sender** — via `branding_resolver.resolve_sender(route_key=…)`.
4. **Recipients** — the resolved `to`/`cc`/`bcc` lists.
5. **Source** — `db` (V2 ✓), `legacy`, `disabled`, or `error`.
6. **Audit shape** — confirmed via FM6 in the failure-mode tests.
7. **Delivery target** — Resend HTTP API (key `re_CfH...A8kW` present).
8. **Verdict** — PASS if resolution succeeded with the expected source.

## Matrix

| Workflow | route_key | source | to | sender | code_ref | Verdict |
|---|---|:-:|:-:|---|---|:-:|
| Safety Digest | `SAFETY_DIGEST_TO` | db | 1 | `noreply@mascidocs.com` | `safety_digest.py:89` | ✅ PASS |
| Health Monitor | `HEALTH_ALERTS` (🔴) | db | 1 | `noreply@mascidocs.com` | `health_monitor.py:67` | ✅ PASS |
| Operator Digest | `OPERATOR_DIGEST_RECIPIENTS` | db | 1 | `noreply@mascidocs.com` | `lib/operator_digest.py:336` | ✅ PASS |
| Daily Report Notification | `SAFETY_FORMS_TO` | db | 2 | `noreply@mascidocs.com` | `routes/safety_forms.py:817` (legacy alias `safety_forms_to`) | ✅ PASS |
| Incident Notification | `SAFETY_FORMS_TO` | db | 2 | `noreply@mascidocs.com` | `routes/safety_forms.py:817` | ✅ PASS |
| Incident Severe CC | `INCIDENT_SEVERE_CC` | db | 0 | `noreply@mascidocs.com` | `server.py:12884` (legacy alias `severe_incident_cc`) | ✅ PASS (env-driven; empty in DB by design) |
| QAQC Notification | `SAFETY_FORMS_TO` | db | 2 | `noreply@mascidocs.com` | `routes/qaqc.py` | ✅ PASS |
| Inspection Notification | `SAFETY_FORMS_TO` | db | 2 | `noreply@mascidocs.com` | `routes/site_inspection_lifecycle.py` | ✅ PASS |
| Safety Meeting Notification | `SAFETY_FORMS_TO` | db | 2 | `noreply@mascidocs.com` | safety meeting chain | ✅ PASS |
| Equipment Notification | `DISPATCH_ROLE_TO` | db | 1 | `noreply@mascidocs.com` | dispatch chain (`routes/equipment.py`) | ✅ PASS |
| Backup Alert | `BACKUP_ALERTS` (🔴) | db | 1 | `noreply@mascidocs.com` | `server.py:6448, 6534, 7277` | ✅ PASS |
| Dead Letter Route | `ADMIN_DEAD_LETTER_TO` | db | 1 | `noreply@mascidocs.com` | `pm_routing.py:370`, `lib/field_submitter_identity.py:189` | ✅ PASS |
| Outage Alert | `OUTAGE_ALERTS` (🔴) | db | 1 | `noreply@mascidocs.com` | `outage_alerts.py:108` | ✅ PASS |
| Field Leadership Always-To | `FIELD_LEADERSHIP_ALWAYS_TO` | db | 2 | `noreply@mascidocs.com` | `routes/field_leadership.py:769` | ✅ PASS |
| Compliance Always-CC | `COMPLIANCE_ALWAYS_CC` | db | 2 | `noreply@mascidocs.com` | `pm_routing.py:277` | ✅ PASS |
| Pre-Op Fail Fallback | `PRE_OP_FAIL_FALLBACK` | db | 1 | `noreply@mascidocs.com` | pre-op chain | ✅ PASS |
| Trench Safety Pulse (Safety) | `TRENCH_SAFETY_PULSE_SAFETY` | db | 1 | `noreply@mascidocs.com` | trench pulse digest | ✅ PASS |
| Trench Safety Pulse (Shop) | `TRENCH_SAFETY_PULSE_SHOP` | db | 1 | `noreply@mascidocs.com` | trench pulse digest | ✅ PASS |
| Payroll Variance Alert | `PAYROLL_VARIANCE_TO` | db | 1 | `noreply@mascidocs.com` | payroll variance | ✅ PASS |
| Account Invites Sender | `ACCOUNT_INVITES_FROM` | db | 0 | `noreply@mascidocs.com` | `routes/auth_directory_routes.py` | ✅ PASS (sender-only, no recipients by design) |
| Executive Digest | `EXECUTIVE_DIGEST` | db | 1 | `noreply@mascidocs.com` | executive digest | ✅ PASS |
| Super Admin Alerts | `SUPER_ADMIN_TO` (🔴) | db | 1 | `noreply@mascidocs.com` | super-admin escalation | ✅ PASS |
| Password Reset Monitor | `PASSWORD_RESET_MONITORING_TO` | disabled | 0 | `noreply@mascidocs.com` | observation route (DISABLED by design) | ✅ PASS (correctly disabled) |

## Critical Workflows — All 4 GREEN

| Critical workflow | Route | to count | source |
|---|---|:-:|:-:|
| Health Monitor | `HEALTH_ALERTS` | 1 | db ✅ |
| Backup Alert | `BACKUP_ALERTS` | 1 | db ✅ |
| Outage Alert | `OUTAGE_ALERTS` | 1 | db ✅ |
| Super Admin Alerts | `SUPER_ADMIN_TO` | 1 | db ✅ |

Zero critical-empty. Zero critical-disabled.

## What Happens On Cutover (per workflow)

For every workflow above, the only change after the flag flip is:
- **Resolution source: `legacy` → `db`** (proven identical recipients
  via parity test).
- **Sender identity: unchanged** (`branding_resolver` is consulted
  identically in both modes).
- **Audit row: now written to `email_routing_audit_v2` per send**
  (V2 emits one row per resolution; legacy did not).
- **Delivery: unchanged** (still Resend HTTP API; same SMTP envelope).

## Verdict

✅ **PASS 23/23 — every workflow resolves correctly under V2.**
Zero workflow regressions. Zero critical-route failures. Zero
silent fallbacks.
