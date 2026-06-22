# TRACK 15.64 — Multi-Tenant Blockers (Phase 3)

**Date:** 2026-06-22  
**Mode:** AUDIT-ONLY · documents the MASCI-specific assumptions that block white-label expansion

A multi-tenant blocker is any code path that (a) hard-codes a MASCI email address as a default, (b) embeds the MASCI brand into a sender/contact string, or (c) assumes the existence of a fixed list of MASCI personnel.

## 1. Severity classification

* **P0 — Blocking:** ships customer-specific data to MASCI email addresses; cannot deploy a second tenant without code edits.
* **P1 — Visible to end user:** customer would see "MASCI" or `@mascigc.com` in a UI string, PDF footer, or help text.
* **P2 — Operational / cosmetic:** development tools or login placeholders.

## 2. P0 blockers (must be tenant-aware before white-label launch)

| # | File | Line | Blocker | Why it blocks multi-tenant |
|---|------|------|---------|---------------------------|
| 1 | `backend/email_routing.py` | 72, 75-76, 83, 87 | `env_defaults()` returns `safety@mascigc.com` / `jaymn.judd@mascigc.com` / `shopmanager@mascigc.com` literally when env vars are unset | A second tenant deploy without explicit env override would silently route their safety forms to MASCI. Defaults must be tenant-resolved, not hardcoded. |
| 2 | `backend/pm_routing.py` | 28-41, 216, 293 | Hardcoded PM dictionary with 4 named MASCI executives + always-CC + admin-fallback to `jaymn.judd@` | Second tenant's PM directory and admin fallback would inherit MASCI names + emails. PM directory must come exclusively from `project_managers` collection. |
| 3 | `backend/auth.py` | 35-39 | `OWNER_SEED` list of 5 MASCI executive emails seeded at bootstrap | Second tenant deployment would seed MASCI owners into their `user_directory`. Owner seed must be tenant-configurable. |
| 4 | `backend/safety_users.py` · `shop_users.py` · `hr_users.py` | (1-2 per file) | Seed lists include MASCI personnel emails | Same as above — second tenant gets MASCI's seed users. |
| 5 | `backend/safety_digest.py` | 10, 83 | `safety@mascigc.com` fallback when `SAFETY_DIGEST_TO_EMAIL` unset | Second tenant's weekly digest would email MASCI. |
| 6 | `backend/health_monitor.py` | 45 | `safety@mascigc.com` fallback when `HEALTH_ALERT_RECIPIENTS` and `BACKUP_EMAIL_TO` both unset | Second tenant platform-alert recipient would be MASCI. **Highest privacy risk** because health alerts surface backup status, scheduler state, and DB connectivity. |
| 7 | `backend/server.py` | 16 sender lines | `SENDER_EMAIL` default `noreply@mascidocs.com` | Second tenant emails would appear to come from `mascidocs.com`. Sender domain must be tenant-resolved. |
| 8 | `backend/outage_alerts.py` | 129 | Sender default `noreply@mascidocs.com` | Same — outage alerts would be branded MASCI. |
| 9 | `backend/phase4.py` | 175 | Sender default `noreply@mascidocs.com` | Same — mention emails branded MASCI. |
| 10 | `backend/backup_verification.py` | 519 | Sender default `noreply@mascidocs.com` | Same. |
| 11 | Env-only routes (no DB override) | various | `HEALTH_ALERT_RECIPIENTS`, `OPERATOR_DIGEST_RECIPIENTS`, `SAFETY_DIGEST_TO_EMAIL`, `OUTAGE_ALERT_TO`, `PAYROLL_VARIANCE_EMAIL_TO`, `ADMIN_DEAD_LETTER_EMAIL`, `DISPATCH_EMAIL`, `SUPER_ADMIN_EMAIL` | Each of these is per-deploy env config. A multi-tenant single-deploy serves N tenants from one container — env vars cannot vary per request. Routes need tenant-aware resolution. |
| 12 | `backend/routes/trench_safety/notifications.py` | 229-234 | Parallel role→env map (`SAFETY_DIGEST_TO_EMAIL`, `SHOP_MANAGER_EMAIL`, `DISPATCH_EMAIL`, `SUPER_ADMIN_EMAIL`) | Trench-safety pulse fan-out lives outside `email_routing.py`. Duplicates the same hardcoding pattern. |
| 13 | `backend/lib/operator_digest.py` | 325 | Operator digest recipient chain falls back to `SAFETY_DIGEST_TO_EMAIL` | Single MASCI digest target. |

## 3. P1 blockers (visible to end user)

| # | File | Issue |
|---|------|-------|
| 14 | `backend/training_pdf.py` | 4 hits of `safety@mascigc.com` baked into rendered training PDFs |
| 15 | `backend/ops_manual.py` | 2 hits of MASCI contact emails in the dev portal ops manual |
| 16 | `backend/guidance/tips.py` + `tips_es.py` | help-text strings reference `hrmanager@mascigc.com` and `jaymn.judd@mascigc.com` verbatim |
| 17 | `frontend/src/data/training.js` + `training_es.js` | 9 hits of `safety@mascigc.com` in training content |
| 18 | `frontend/src/lib/i18n.js` | 4 hits of MASCI emails in i18n strings |
| 19 | `frontend/src/lib/companyInfo.js` | Single hardcoded company-contact email |
| 20 | `frontend/src/pages/AdminGuide.jsx` | 8 hits of MASCI emails in admin guide content |
| 21 | `frontend/src/components/TrenchBoxPosterCard.jsx` | Contact email rendered onto a printable poster |
| 22 | `frontend/src/pages/V2Compare.jsx` | 2 hits in static comparison content |
| 23 | `frontend/src/components/AdminShopUsersPanel.jsx` | empty-state copy references shop manager email |
| 24 | `frontend/src/pages/{SafetyDigest, HrPayrollVariance, admin/AdminDigestConfig}.jsx` | UI shows the current default recipient (would mislead a second tenant's admin) |

## 4. P2 blockers (cosmetic / dev-only)

| # | File | Issue |
|---|------|-------|
| 25 | 8 login pages (Admin, PM, Shop, HR, Safety, FL, Dispatch, SignIn) | `placeholder="you@mascigc.com"` attributes — purely cosmetic |
| 26 | `backend/scripts/track_15_47_synthetic_incident.py` (7 hits) | Test scripts referencing MASCI emails — refuse to run on production; not a real blocker |
| 27 | `backend/scripts/iter348_fl_bulk_create.py` (3 hits) | Same — preview-only seed script |
| 28 | `backend/tests/**` | Excluded from production by definition |

## 5. White-label readiness summary

| Concept | State today | Required for multi-tenant |
|---|---|---|
| **Sender domain** | `noreply@mascidocs.com` hardcoded as fallback in ~25 sender lines | Tenant-resolved `branding.sender_email` |
| **Reply-to** | `REPLY_TO_EMAIL` env (single value) | Per-tenant `branding.reply_to` |
| **Safety digest recipient** | `SAFETY_DIGEST_TO_EMAIL` env + MASCI fallback | DB-overridable per tenant |
| **Operator digest recipients** | `OPERATOR_DIGEST_RECIPIENTS` env | DB-overridable per tenant |
| **Health alert recipients** | env + MASCI fallback | DB-overridable per tenant + tenant-scoped |
| **Outage alert recipient** | env (single value) | DB-overridable per tenant + audit row |
| **Payroll variance recipient** | env | DB-overridable per tenant |
| **Admin dead-letter** | env | DB-overridable per tenant |
| **Trench safety role map** | parallel role→env layer | Merge into the unified routing module |
| **PM directory** | `project_managers` collection (already tenant-scopable) + hardcoded fallback | Remove hardcoded fallback; require collection seed per tenant |
| **Owner seed** | `OWNER_SEED` in `auth.py` | Empty by default; tenant supplies via env or admin bootstrap form |
| **Seed user lists** | per-portal `*_users.py` hardcoded | Drop hardcoded entries; use admin "create first user" path |
| **PDF footer contact** | hardcoded `safety@mascigc.com` | Resolve from tenant branding |
| **Help / tip text** | hardcoded MASCI emails in tips.py + frontend i18n | Resolve via `{{tenant.support_email}}` template placeholders |
| **Login placeholders** | `placeholder="you@mascigc.com"` | Generic `you@yourcompany.com` |

## 6. Multi-tenant routing architecture choices (cross-references Phase 4)

The cleanest path forward is to:

1. **Promote the `email_routing` module to a tenant-scoped router** — every read takes a `tenant_id` (or implicitly the current tenant resolved from the request).
2. **Add 8 new routing keys** (health, outage, operator digest, safety digest, payroll variance, admin dead-letter, dispatch role, super admin) to fill the env-only gap.
3. **Add a `branding` document** (`branding_config` collection) per tenant with `sender_email`, `reply_to`, `from_display_name`, `support_email`, `support_phone`, `logo_url`. Resolve from this doc inside the small wrapper around every `resend.Emails.send` call (only 40 sites).
4. **Audit row at every send site** (`db.email_audit` already covers ~70 %; close the gap on outage / health / trench-safety so no notification is silent).
5. **Test-route endpoint per route** (the existing `/api/admin/email-routing/test` covers the 6 DB routes; expand to all 14).

## 7. Hard-rule compliance (Phase 3)
* ✅ Audit-only — no code changed.
* ✅ Every claim is anchored to a file:line in Phase 1.
* ✅ MASCI-specific defaults explicitly named, not glossed over.
* ✅ White-label gap quantified per concept (14 rows in §5).
