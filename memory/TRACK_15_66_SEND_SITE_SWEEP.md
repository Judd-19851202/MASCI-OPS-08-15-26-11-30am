# TRACK 15.66 — Send-Site Sweep (Phase 1)

**Date:** 2026-06-22 (Phase 1 of 2)  
**Tracker:** every Resend send site classified · operational sites either migrated (5/25) or scheduled for Phase 2 (with rationale).

## 1. Inventory (25 sites)

| # | File | Function | Current recipient source | Route key | Status |
|---|------|----------|--------------------------|-----------|--------|
| 1 | `backend/safety_digest.py:83` | weekly safety digest cron | `SAFETY_DIGEST_TO_EMAIL` env | `SAFETY_DIGEST_TO` | ✅ migrated (Track 15.65) |
| 2 | `backend/health_monitor.py:_send_alert` | platform health alert | `HEALTH_ALERT_RECIPIENTS` env | `HEALTH_ALERTS` (critical) | ✅ migrated (Track 15.65) |
| 3 | `backend/outage_alerts.py:send_outage_alert` | outage alert | `OUTAGE_ALERT_TO` env | `OUTAGE_ALERTS` (critical) | ✅ migrated (Track 15.66 Phase 1) |
| 4 | `backend/lib/field_submitter_identity.py:_dead_letter_email` | submitter-identity dead-letter | `ADMIN_DEAD_LETTER_EMAIL` env | `ADMIN_DEAD_LETTER_TO` | ✅ migrated (Track 15.66 Phase 1) |
| 5 | `backend/lib/operator_digest.py:recipients` | daily operator digest | `OPERATOR_DIGEST_RECIPIENTS` env | `OPERATOR_DIGEST_RECIPIENTS` | ✅ migrated (Track 15.66 Phase 1) |
| 6 | `backend/routes/safety_forms.py:806` | equipment forms fan-out | `email_routing.get_value("safety_forms_to")` (already DB-aware) | `SAFETY_FORMS_TO` | ✅ legacy-alias migrated (Track 15.65 — works via `legacy_get_value` shim when flag ON) |
| 7 | `backend/routes/field_leadership.py:768, 803` | FL form fan-out | `email_routing.get_value("leadership_always_to")` + dynamic FL users | `FIELD_LEADERSHIP_ALWAYS_TO` | ✅ legacy-alias migrated |
| 8 | `backend/pm_routing.py:fanout` (called from inspections, meetings, JHA, daily reports, incidents, qaqc, equipment inspections) | PM fan-out · always-CC | `email_routing.get_value("always_cc")` + collection-driven PM lookup | `COMPLIANCE_ALWAYS_CC` | ✅ legacy-alias migrated for the always-CC layer. PM-resolution layer (collection-driven) intentionally untouched. |
| 9 | `backend/routes/safety.py` severe-incident emit | severe incident fan-out | `email_routing.get_value("severe_incident_cc")` | `INCIDENT_SEVERE_CC` | ✅ legacy-alias migrated |
| 10 | `backend/server.py:6440-7430` backup-pipeline email | daily auto-backup + manual backup | `email_routing.get_value("backup_email_to")` | `BACKUP_ALERTS` (critical) | ✅ legacy-alias migrated |
| 11 | `backend/server.py` Pre-Op fail fallback | Pre-Op fail / OOS recipient | `email_routing.get_value("shop_manager_fallback")` | `PRE_OP_FAIL_FALLBACK` | ✅ legacy-alias migrated |
| 12 | `backend/server.py` Resend test endpoint (legacy V1) | admin sanity check | direct admin input | n/a | ✅ already controlled — admin-only with required `to` |
| 13 | `backend/server.py` admin V2 test endpoint (new this track) | controlled route test | DB doc + safe test inbox | (per route) | ✅ new — never blasts production recipients |
| 14 | `backend/routes/pm_admin.py` PM welcome / set-password | single per-user target | `users` collection | (per-user) | 🟢 not a routing concern — sender migration only · Phase 2 sender via branding |
| 15 | `backend/routes/shop_parts.py` shop welcome | single per-user target | `users` collection | (per-user) | 🟢 not a routing concern · Phase 2 sender via branding |
| 16 | `backend/routes/pm_routes.py` PM email | PM-only target | `project_managers` collection | (per-user) | 🟢 collection-driven · Phase 2 sender via branding |
| 17 | `backend/lib/fsi_email_sender.py` shared utility | dynamic per call | caller-provided | n/a | 🟡 shared utility — sender argument flows through it. Phase 2: sender pulled from branding doc when caller passes `tenant_key`. |
| 18 | `backend/backup_verification.py:519` | verification probe email | env override + body param | covered by `BACKUP_ALERTS` | 🟢 already env-overridable + body-overridable. Phase 2 wraps the resolver around the env lookup. |
| 19-24 | `backend/server.py` welcomes (Shop · HR · Safety · Dispatch · FL · misc) | per-user welcome | `users` / portal collections | (per-user) | 🟢 not routing — per-user sends. Sender swap only (Phase 2). |
| 25 | `backend/server.py` Payroll Variance | weekly digest | `PAYROLL_VARIANCE_EMAIL_TO` env | `PAYROLL_VARIANCE_TO` | 🟡 Phase 2 wrap (low risk — already env-driven, defaults to super admin) |

## 2. Migration progress
* **Through resolver:** 5 / 25 send sites directly call `email_routing_v2.resolve_and_audit(...)`.
* **Through legacy alias shim:** 6 / 25 sites use `email_routing.get_value(...)` which is mapped onto the new catalog via `LEGACY_TO_NEW` and transparently honoured by the V2 engine.
* **Per-user sends (not routing-decisions):** 8 / 25 sites — they target a single specific user; routing-engine N/A. Phase 2 still touches them for the sender / reply-to swap to `tenant_branding`.
* **Phase 2 wrap candidates (env-only digest/verification with low blast radius):** 4 sites (payroll, backup verification, executive digest emit, trench safety pulse).
* **Admin tooling (test endpoints):** 2 sites — these never blast production lists.

## 3. Preservation guarantees honoured
For every migrated site:
* Subject, body, attachment behaviour preserved verbatim.
* CC / BCC semantics preserved.
* Sender / reply-to unchanged (Phase 2 will move sender to branding doc).
* Failure handling unchanged — every wrapper carries a try/except so the resolver can't break a real send.
* Legacy provider returns the EXACT recipient list used pre-Track-15.65, so `EMAIL_ROUTING_V2=false` is a no-op.

## 4. Why some sites are not migrated in Phase 1

| Site | Reason |
|---|---|
| Per-user welcomes (PM, Shop, HR, Safety, Dispatch, FL) | Not a routing decision — target is a single user from a portal collection. Phase 2 touches them only for sender swap. |
| `pm_admin.py` PM welcome | Same as above. |
| Backup verification | Already env-overridable + body-overridable; risk profile is low; Phase 2 wraps. |
| Payroll variance | Already env-only with safe super-admin default; Phase 2 wraps. |
| `lib/fsi_email_sender.py` | Shared utility — sender argument flows through. Phase 2 hooks it to branding. |

## 5. Parity confirmation
`scripts/track_15_65_parity_verify.py` final run on 2026-06-22 reports `match: 19 · mismatch: 0 · critical_empty: 0` after all Phase 1 migrations.

## 6. Hard-rule compliance (Phase 1)
* ✅ Every send site classified.
* ✅ Operational routing sites migrated or via legacy alias.
* ✅ No subject / body / attachment / CC / BCC / sender behaviour changed.
* ✅ No live blast testing.
* ✅ No silent fallback added.
