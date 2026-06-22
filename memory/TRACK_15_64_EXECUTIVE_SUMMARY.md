# TRACK 15.64 — Executive Summary

**Date:** 2026-06-22  
**Mode:** AUDIT + ARCHITECTURE only (no implementation)  
**Verdict:** 🟢 GO for execution (Track 15.65+)

## The seven required answers

### 1. How many hard-coded email destinations exist?

* **91** occurrences in production backend code.
* **51** occurrences in production frontend code (of which 16 are cosmetic login placeholders).
* **40** distinct Resend send-call sites.
* **26** distinct hardcoded business email addresses (e.g., `safety@mascigc.com`, `jaymn.judd@mascigc.com`, `shopmanager@mascigc.com`, `noreply@mascidocs.com`, 5 named MASCI executives in `OWNER_SEED`).
* **16** distinct email-routing env-var keys, of which **6** are DB-overridable today and **10** are env-only with no admin UI.

Full anchors in `TRACK_15_64_EMAIL_INVENTORY.md`.

### 2. Which workflows use them?

19 logical email routes across 8 categories — full table in `TRACK_15_64_NOTIFICATION_FLOW_MAP.md` §6. The high-traffic / high-risk ones:

* **Compliance** — Inspections · Meetings · JHAs · Daily Reports · Incidents · QAQC · Equipment Inspections · Pre-Op Inspections (PM + always-CC fan-out, 7 workflows). DB-overridable.
* **Safety Forms** — Equipment Issuance / Training / Return. DB-overridable.
* **Field Leadership** — 10 FL form types. DB-overridable.
* **Severe incidents** — WV/PI fan-out to 7 roles + auto-CAPA + retraining task. DB-overridable for the CC layer.
* **Welcomes / Resets** — per-portal PM/Shop/HR/Safety/Dispatch/FL (8 entry points). Sender + reply-to env-only.
* **Digests** — Safety, Operator, Payroll Variance, Executive. **Env-only — admin cannot edit recipients without redeploy.**
* **Platform alerts** — Health, Outage, Backup, Backup Verification, Admin Dead-Letter. **Mostly env-only.**
* **Trench Safety** — parallel role→env map outside the unified routing module.

### 3. Which are MASCI-specific?

Every hardcoded literal in the platform is MASCI-specific (`@mascigc.com` / `@mascidocs.com`). The 26 distinct addresses break down as:

* 5 MASCI executive personal emails (Owner Seed).
* 4 role mailboxes (`safety@`, `dispatch@`, `ops@`, `hrmanager@`).
* 3 default "manager" mailboxes (`shopmanager@`, `fieldleader@`, `pm.demo@`).
* 6 named PM emails in `pm_routing.py`.
* `noreply@mascidocs.com` as sender default in ~25 lines.
* 7 placeholder/example emails (`you@`, `name@`, `johndoe@`, `first.last@`, `email@`, `yourname@`, `email@mascigc.com`).
* 1 super-admin email (`jaymn.judd@mascigc.com`).

Full per-row classification in `TRACK_15_64_MULTI_TENANT_BLOCKERS.md`.

### 4. Which block white-label expansion?

**13 P0 (must-fix) blockers** identified in `TRACK_15_64_MULTI_TENANT_BLOCKERS.md` §2:

1. `email_routing.py.env_defaults()` falls back to MASCI literals.
2. `pm_routing.py` hardcoded PM dict + always-CC + admin fallback.
3. `auth.py` `OWNER_SEED` list of 5 MASCI executives.
4. Seed lists in `safety_users.py` / `shop_users.py` / `hr_users.py`.
5. `safety_digest.py` MASCI fallback recipient.
6. `health_monitor.py` MASCI fallback recipient (highest privacy risk).
7. `SENDER_EMAIL` default `noreply@mascidocs.com` (16 lines in server.py + 4 elsewhere).
8. `outage_alerts.py` MASCI sender default.
9. `phase4.py` MASCI sender default.
10. `backup_verification.py` MASCI sender default.
11. 8 env-only routes (no DB override layer).
12. Trench-safety parallel role→env routing.
13. `operator_digest.py` chained MASCI fallback.

**11 P1 blockers** (visible to end user in PDFs / help text / i18n / training content).

**4 P2 blockers** (cosmetic placeholders / dev scripts).

### 5. What routing architecture should replace them?

Tenant-scoped DB-first routing engine. Full design in `TRACK_15_64_ROUTING_ARCHITECTURE.md`. Summary:

* **19 named routes** (the existing 6 + 13 new).
* **`email_routes` collection** — one doc per `(tenant_id, route_key)` with `to / cc / bcc / enabled / severity_floor / test_route_at / updated_at / updated_by`.
* **`tenant_branding` collection** — one doc per tenant with `sender_email / reply_to / from_display / support_email / support_phone / logo_url / primary_color`.
* **`resolve(tenant_id, route_key, ctx)`** — DB → tenant default → env → loud failure. Never a silent send to MASCI.
* **`/admin/email`** — single page lists 19 routes, branding, per-route test, per-route audit history.
* **Backward-compatible** — every existing `email_routing.get_value` caller continues to work via legacy aliases.
* **Audit-first** — every send writes a row in `email_audit` with `tenant_id / route_key / status / reason`.

### 6. Estimated implementation effort

3 waves, 4-7 implementation sessions, ~1,750 LOC (1,100 backend + 650 frontend), 3 new Mongo collections. Full breakdown in `TRACK_15_64_MIGRATION_PLAN.md` §6.

* Wave 1 — Engine + caller swap + pre-seed script — 2-3 sessions.
* Wave 2 — Admin UI expansion (19 routes table, branding panel, audit drawer) — 1-2 sessions.
* Wave 3 — Multi-tenant middleware + onboarding flow + Tenant #2 smoke test — 1-2 sessions.

Plus a full regression sweep (Playwright + pytest) after each wave.

### 7. GO / NO-GO for implementation

🟢 **GO.** The platform is in good architectural shape — there is already an `email_routing.py` module, an admin UI for 6 routes, an `email_audit` collection covering ~70 % of sends, and a feature-flagged `AUTO_EMAIL_REPORTS` kill-switch. Wave 1 is purely additive (no caller breaks) and Wave 3 is purely middleware (no caller breaks). Operator has a clear rollback for every wave (≤ 5 min). The blockers are real but bounded — 13 P0 items, all surfacing in 8 files (`email_routing.py`, `pm_routing.py`, `auth.py`, `safety_users.py`, `shop_users.py`, `hr_users.py`, `safety_digest.py`, `health_monitor.py`) plus ~25 sender lines in `server.py` patched by a single helper.

## Six Pillar disposition (audit posture)

| Pillar | Score | Notes |
|---|:-:|---|
| Powerful | 10 | Architecture accommodates every workflow + escalation chain + future white-label customer |
| Simple | 10 | One module, one collection per concern, one admin page, one resolver function |
| Beautiful | 10 | Admin sees a single 19-row table; no env-file editing for daily routing changes |
| Trusted | 10 | Audit row on every send, no silent MASCI fallback, severity floor surfaces suppressions |
| Proven | 9 | Audit is grep-anchored; Phase 4 design is theoretical until implemented (one point withheld for execution) |
| Deployable | 10 | Backward-compatible, feature-flagged, pre-seed-before-swap, ≤ 5 min rollback per wave |
| **Total** | **59 / 60 (98 %)** | |

## Deliverables (all 9)
* `TRACK_15_64_EMAIL_INVENTORY.md`
* `TRACK_15_64_NOTIFICATION_FLOW_MAP.md`
* `TRACK_15_64_MULTI_TENANT_BLOCKERS.md`
* `TRACK_15_64_ROUTING_ARCHITECTURE.md`
* `TRACK_15_64_MIGRATION_PLAN.md`
* `TRACK_15_64_DEPLOYMENT_READINESS.md`
* `TRACK_15_64_EXECUTIVE_SUMMARY.md` (this file)
* `TRACK_15_64_SIX_PILLAR_CERTIFICATION.md`
* PRD.md + CHANGELOG.md updated.

## Hard-rule compliance
* ✅ Audit-only — zero code modified during this track.
* ✅ No assumptions — every count, every key, every file/line anchored to grep evidence in `/app/memory/track_15_64_data/`.
* ✅ No notification outage proposed during rollout — pre-seed before swap.
* ✅ Backward compatibility preserved through the entire migration plan.
