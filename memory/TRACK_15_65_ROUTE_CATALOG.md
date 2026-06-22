# TRACK 15.65 — Route Catalog (Phase 2)

**Date:** 2026-06-22  
**Mode:** definitive Wave-1 catalog · used by the seed script · backed by live DB rows.

## 1. The 19 routes (one row per `(tenant_key='masci', route_key)`)

| # | route_key | display_name | category | severity | critical | enabled | TO sources | legacy_key | env fallback | live `to` count |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `COMPLIANCE_ALWAYS_CC` | Compliance Always-CC | compliance | info | no | yes | hard catalog default `[jaymn, safety]` | `always_cc` | — | 2 |
| 2 | `SAFETY_FORMS_TO` | Safety Forms Distribution | compliance | info | no | yes | `SAFETY_FORMS_EMAIL_TO` env or default `[safety, jaymn]` | `safety_forms_to` | `SAFETY_FORMS_EMAIL_TO` | 2 |
| 3 | `FIELD_LEADERSHIP_ALWAYS_TO` | Field Leadership Always-CC | leadership | info | no | yes | `LEADERSHIP_ALWAYS_TO_1/2` env or `[jaymn, safety]` | `leadership_always_to` | `LEADERSHIP_ALWAYS_TO_1/2` | 2 |
| 4 | `PRE_OP_FAIL_FALLBACK` | Pre-Op Fail Fallback | shop | warn | no | yes | `SHOP_MANAGER_EMAIL` env or default `shopmanager@` | `shop_manager_fallback` | `SHOP_MANAGER_EMAIL` | 1 |
| 5 | `INCIDENT_SEVERE_CC` | Severe Incident CC | safety | critical | no (extension layer) | yes | `SEVERE_INCIDENT_CC` env | `severe_incident_cc` | `SEVERE_INCIDENT_CC` | 0 |
| 6 | `BACKUP_ALERTS` | Backup Pipeline Alerts | platform | warn | **YES** | yes | `BACKUP_EMAIL_TO` env (jaymn) | `backup_email_to` | `BACKUP_EMAIL_TO` | 1 |
| 7 | `HEALTH_ALERTS` | Platform Health Alerts | platform | critical | **YES** | yes | `HEALTH_ALERT_RECIPIENTS` env or backup fallback | — | `HEALTH_ALERT_RECIPIENTS`, `BACKUP_EMAIL_TO` | 1 |
| 8 | `OUTAGE_ALERTS` | Platform Outage Alerts | platform | critical | **YES** | yes | `OUTAGE_ALERT_TO` env | — | `OUTAGE_ALERT_TO` | 1 |
| 9 | `SAFETY_DIGEST_TO` | Weekly Safety Digest | digest | info | no | yes | `SAFETY_DIGEST_TO_EMAIL` env or default | — | `SAFETY_DIGEST_TO_EMAIL` | 1 |
| 10 | `OPERATOR_DIGEST_RECIPIENTS` | Daily Operator Digest | digest | info | no | yes | `OPERATOR_DIGEST_RECIPIENTS` env or safety digest | — | `OPERATOR_DIGEST_RECIPIENTS`, `SAFETY_DIGEST_TO_EMAIL` | 1 |
| 11 | `PAYROLL_VARIANCE_TO` | Payroll Variance Digest | digest | info | no | yes | `PAYROLL_VARIANCE_EMAIL_TO` env or super admin | — | `PAYROLL_VARIANCE_EMAIL_TO` | 1 |
| 12 | `ADMIN_DEAD_LETTER_TO` | Admin Dead-Letter | platform | warn | no | yes | `ADMIN_DEAD_LETTER_EMAIL` env | — | `ADMIN_DEAD_LETTER_EMAIL` | 1 |
| 13 | `DISPATCH_ROLE_TO` | Dispatch Role Alerts | operations | warn | no | yes | `DISPATCH_EMAIL` env or super admin | — | `DISPATCH_EMAIL`, `SUPER_ADMIN_EMAIL` | 1 |
| 14 | `SUPER_ADMIN_TO` | Super Admin Escalation | platform | critical | **YES** | yes | `SUPER_ADMIN_EMAIL` env | — | `SUPER_ADMIN_EMAIL` | 1 |
| 15 | `EXECUTIVE_DIGEST` | Executive Digest | digest | info | no | yes | super admin | — | — | 1 |
| 16 | `ACCOUNT_INVITES_FROM` | Account Invites Sender | branding | info | no | yes | `SENDER_EMAIL` / `REPLY_TO_EMAIL` env | — | `SENDER_EMAIL`, `REPLY_TO_EMAIL` | 0 (sender-only) |
| 17 | `PASSWORD_RESET_MONITORING_TO` | Password Reset Monitoring | security | info | no | **no (off by default)** | optional CC | — | — | 0 |
| 18 | `TRENCH_SAFETY_PULSE_SAFETY` | Trench Safety Pulse · safety | safety | warn | no | yes | safety digest or super admin | — | `SAFETY_DIGEST_TO_EMAIL`, `SUPER_ADMIN_EMAIL` | 1 |
| 19 | `TRENCH_SAFETY_PULSE_SHOP` | Trench Safety Pulse · shop | safety | warn | no | yes | shop manager fallback | — | `SHOP_MANAGER_EMAIL` | 1 |

## 2. Critical routes (the resolver hard-fails on empty resolution)
* `BACKUP_ALERTS` — daily auto-backup destination.
* `HEALTH_ALERTS` — scheduler dead / backup stale / DB unreachable.
* `OUTAGE_ALERTS` — platform-wide outage.
* `SUPER_ADMIN_TO` — platform-admin escalation.

Live verification shows all 4 critical routes resolved to ≥ 1 recipient during the apply seed run. The seed script refuses to write a critical route with empty `to`.

## 3. Default sender / reply-to (for `ACCOUNT_INVITES_FROM`)
* `from_email`: env `SENDER_EMAIL` (current: `noreply@mascidocs.com`).
* `reply_to`: env `REPLY_TO_EMAIL` (current: `jaymn.judd@mascigc.com`).

## 4. Naming conventions honoured
* `ALL_CAPS_SNAKE_CASE` route keys.
* No tenant prefix in the key (tenant lives on `tenant_key`).
* Legacy alias map (`LEGACY_TO_NEW` in `email_routing_v2.py`) preserves the 6 existing keys.

## 5. Hard-rule compliance (Phase 2)
* ✅ Route catalog matches the Track 15.64 architecture exactly — 19 routes, 4 critical.
* ✅ No ad-hoc names. Every key documented and seeded.
* ✅ Defaults preserve current MASCI behaviour (proven by Phase 8 parity harness — 19/19 match).
