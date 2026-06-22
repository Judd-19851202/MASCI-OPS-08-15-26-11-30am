# TRACK 15.64 — Email Inventory (Phase 1)

**Date:** 2026-06-22  
**Mode:** AUDIT-ONLY · no code modified  
**Scope:** every email address / recipient / distribution list / sender / Resend call across backend, frontend, scripts, and operational config

## 1. Headline counts

| Population | Count |
|---|---|
| Hardcoded `@mascigc.com` / `@mascidocs.com` occurrences in **production** backend code (excluding tests, seeds, archived, `_pycache_`) | **91** |
| Hardcoded `@mascigc.com` / `@mascidocs.com` occurrences in **production** frontend code | **51** |
| Email-routing env-var lookups in backend (`os.environ.get("..._EMAIL/_MAIL_TO/_RECIPIENT/_ALERT/_DIGEST")`) | **83** |
| Distinct email-routing env-var keys | **16** (`unique_env_email_keys.txt`) |
| Distinct hardcoded business email addresses surfaced | **26** (`unique_emails.txt`) |
| Resend send-call sites (`resend.Emails.send`) | **40** |
| Routes already exposed through DB-overridable layer (`email_routing.py`) | **6** of ~14 logical routes |
| Routes that still go directly to env-var with no DB override | **~8** (severe gap) |

Anchor files in `/app/memory/track_15_64_data/`:
* `backend_hardcoded_emails.txt` · `frontend_hardcoded_emails.txt`
* `backend_env_email_lookups.txt`
* `unique_emails.txt` · `unique_env_email_keys.txt`

## 2. Distinct hardcoded business emails surfaced (production)

```
RamonRodriguez@mascigc.com       chris.wright@mascigc.com
carlos.martinez@mascigc.com      chriswright@mascigc.com
david.jewett@mascigc.com         davidjewett@mascigc.com
dispatch@mascigc.com             fieldleader@mascigc.com
hrmanager@mascigc.com            jaymn.judd@mascigc.com
joe.spiker@mascigc.com           lennywitkowski@mascigc.com
maria.reyes@mascigc.com          noreply@mascidocs.com
ops@mascigc.com                  pm.demo@mascigc.com
ramon.rodriguez@mascigc.com      richsanchez@mascigc.com
safety@mascigc.com               shopmanager@mascigc.com
```
Plus placeholders / examples in form fields and help text:
```
email@mascigc.com · first.last@mascigc.com · johndoe@mascigc.com
name@mascigc.com  · you@mascigc.com · yourname@mascigc.com
```

## 3. Email-routing env keys in use

```
ADMIN_DEAD_LETTER_EMAIL          BACKUP_EMAIL_TO
DISPATCH_EMAIL                   HEALTH_ALERT_RECIPIENTS
MASCI_ADMIN_EMAIL                OPERATOR_DIGEST_RECIPIENTS
PAYROLL_VARIANCE_EMAIL_TO        REPLY_TO_EMAIL
SAFETY_DIGEST_TO_EMAIL           SAFETY_FORMS_EMAIL_TO  (DB-overridable)
SENDER_EMAIL                     SEVERE_INCIDENT_CC    (DB-overridable)
SHOP_MANAGER_EMAIL  (DB-overridable)
SUPER_ADMIN_EMAIL                LEADERSHIP_ALWAYS_TO_1/2 (DB-overridable)
AUTO_EMAIL_REPORTS               (boolean kill-switch)
PAYROLL_VARIANCE_EMAIL_HOUR_UTC  PAYROLL_VARIANCE_EMAIL_DOW
BACKUP_EMAIL_MAX_MB
```

DB-overridable routes (via `backend/email_routing.py`): `always_cc`, `safety_forms_to`, `leadership_always_to`, `shop_manager_fallback`, `severe_incident_cc`, `backup_email_to`.

**Env-only routes (gap to close):** `health_alert_recipients`, `operator_digest_recipients`, `safety_digest_to`, `outage_alert_to`, `payroll_variance_email_to`, `admin_dead_letter_email`, `dispatch_email`, `super_admin_email`.

## 4. Inventory table — production backend (representative rows; full list at `/tmp/be_prod_emails.txt`)

| File | Line | Email / Env key | Purpose | Workflow | Severity | Currently used? | Dead code? | MASCI-specific? |
|---|---|---|---|---|---|---|---|---|
| `backend/email_routing.py` | 14-87 (12 hits) | `jaymn.judd@mascigc.com` · `safety@mascigc.com` · `shopmanager@mascigc.com` | env_defaults() fallback for 6 routing keys | every email workflow | P0 | YES | NO | YES — MASCI specific defaults |
| `backend/auth.py` | 35-39 | 5 owner emails | OWNER_SEED super-admin bootstrap | one-time admin seeding | P0 | YES (idempotent seed) | NO | YES |
| `backend/pm_routing.py` | 28-31, 40-41, 216, 293 | PM lookup + always_cc + admin fallback | PM auto-email routing | every PM-driven workflow (inspections, meetings, JHAs, daily reports, incidents, equipment) | P0 | YES | NO | YES |
| `backend/safety_users.py` | 72 | `safety@mascigc.com` | Seed safety user | one-time portal seeding | P1 | YES (idempotent seed) | NO | YES |
| `backend/shop_users.py` | 73 | `shopmanager@mascigc.com` | Seed shop user | one-time portal seeding | P1 | YES (idempotent) | NO | YES |
| `backend/hr_users.py` | 1 | `hrmanager@mascigc.com` | Seed HR user | one-time portal seeding | P1 | YES | NO | YES |
| `backend/safety_digest.py` | 10, 83 | `safety@mascigc.com` | Weekly safety digest fallback recipient | scheduled digest | P1 | YES | NO | YES |
| `backend/health_monitor.py` | 45 | `safety@mascigc.com` | Health alert fallback recipient | platform health alerts | P0 | YES | NO | YES |
| `backend/outage_alerts.py` | 129 | `noreply@mascidocs.com` | Sender default | outage alert email | P0 | YES | NO | YES — `mascidocs.com` domain |
| `backend/phase4.py` | 175 | `noreply@mascidocs.com` | Sender default | mention emails | P1 | YES | NO | YES |
| `backend/backup_verification.py` | 519 | `noreply@mascidocs.com` | Sender default | backup verification emails | P1 | YES | NO | YES |
| `backend/server.py` | 2380, 3714, 6463, 7426, 9979, 10019, 10311, 10390, 10426, 11455, 12331, ... (16 hits) | `noreply@mascidocs.com` · `onboarding@resend.dev` | Sender default across welcome / PDF / report emails | platform-wide | P1 | YES | NO | YES |
| `backend/training_pdf.py` | 4 hits | `safety@mascigc.com` | Contact email in PDF footer | rendered training PDFs | P1 | YES | NO | YES — appears in printed PDFs |
| `backend/ops_manual.py` | 2 hits | contact emails in dev ops manual | Dev-facing platform docs | dev portal | P2 | YES | NO | YES |
| `backend/project_managers.py` | 4 hits | PM directory fixture defaults | seeding PM directory | one-time PM seeding | P1 | YES | NO | YES |
| `backend/lib/operator_digest.py` | 325 | `OPERATOR_DIGEST_RECIPIENTS` env + fallback | Operator daily digest | scheduled digest | P0 | YES | NO | NO — env only, but no DB override |
| `backend/lib/field_submitter_identity.py` | 176 | `ADMIN_DEAD_LETTER_EMAIL` env | Dead-letter for unresolved submitter identities | error-path alerting | P1 | YES | NO | NO — env only |
| `backend/routes/trench_safety/notifications.py` | 229-234 | Role→env map (safety/shop/dispatch/admin) | Trench-safety pulse fan-out | safety pulse | P1 | YES | NO | parallel routing layer outside `email_routing.py` |
| `backend/routes/safety_forms.py` | 804-812 | `SAFETY_FORMS_EMAIL_TO` env (DB-overridable) | Safety forms recipient list | equipment issuance + training + return | P0 | YES | NO | **NO** — already configurable via DB |
| `backend/routes/admin_digest_config.py` | 63 | `SAFETY_DIGEST_TO_EMAIL` env | Admin digest config | scheduled safety digest | P1 | YES | NO | env only |
| `backend/routes/field_leadership.py` | 768, 803 | LEADERSHIP_ALWAYS_TO_1/2 + dynamic FL user list | FL form fan-out | 10 FL forms | P0 | YES | NO | **NO** — already DB-overridable |
| `backend/guidance/tips.py` + `tips_es.py` | 2 hits | hrmanager + jaymn emails embedded in tip text | Help text shown to users | help/tips | P2 | YES | NO | YES — needs templating |

## 5. Inventory table — production frontend (representative rows; full list at `/tmp/fe_prod_emails.txt`)

| File | Count | Type |
|---|---|---|
| `pages/AdminGuide.jsx` | 8 | Hardcoded references in admin help guide |
| `data/training.js` + `_es.js` | 9 | Training content text mentions of `safety@mascigc.com` |
| `lib/i18n.js` | 4 | i18n strings containing email examples |
| `lib/companyInfo.js` | 1 | Company contact email constant |
| Login placeholders (8 login pages: Admin, PM, Shop, HR, Safety, FL, Dispatch, SignIn) | 16 | `placeholder="you@mascigc.com"` attributes only (cosmetic) |
| `pages/V2Compare.jsx` | 2 | Static comparison content |
| `components/AdminShopUsersPanel.jsx` | 2 | Empty-state copy referencing shop manager email |
| `components/TrenchBoxPosterCard.jsx` | 1 | Contact email rendered on printable poster |
| `pages/SafetyDigest.jsx` | 2 | Default digest recipient display |
| `pages/HrPayrollVariance.jsx` | 1 | Default payroll variance recipient display |
| `pages/admin/AdminDigestConfig.jsx` | 1 | Admin config UI shows current default |

## 6. Resend send-site inventory
40 distinct `resend.Emails.send(...)` call sites across:
* `routes/pm_admin.py` (PM welcome, set-password notify)
* `routes/safety_forms.py` (issuance, training, return)
* `routes/shop_parts.py` (parts shop welcome)
* `routes/safety_portal/digest.py` (weekly safety digest)
* `routes/admin_digest_config.py` (digest preview send)
* `routes/field_leadership.py` (FL forms fan-out)
* `routes/dispatch_command_center.py` (dispatch board alerts)
* `routes/trench_safety/{notifications,excavations,pulse,report_distribution}.py`
* `server.py` (welcome, password-reset, backup, PDF-by-email, payroll-variance, generic notify, …)
* `phase4.py`, `safety_digest.py`, `outage_alerts.py`, `backup_verification.py`, `health_monitor.py`, `operator_digest.py`

## 7. Dead-code / scope exclusions
* All `backend/tests/` references — auditing fixture data only, not production.
* All `backend/scripts/seed_*` and `track_15_*_synthetic_*` — preview-only seeds; refuse to run with `APP_ENV=production`.
* All `_archived` directories.
* Login placeholder attributes (`placeholder="you@mascigc.com"`) — purely cosmetic; do not influence routing. Replacing them is a P2 white-label polish item.

## 8. Top-line evidence statement
The platform already has an `email_routing` module + admin UI for **6** of its logical routes. **8 additional logical routes** still go straight to env vars with no DB override. Defaults are hardcoded to `@mascigc.com` / `@mascidocs.com` across env_defaults, seed users, owner bootstrap, sender lines, PDF contact text, and i18n help text. **No route currently supports multi-tenant per-customer recipient resolution.** This audit is the foundation for the Phase 4 routing-architecture redesign.

## 9. Hard-rule compliance (Phase 1)
* ✅ No code modified.
* ✅ Inventory is grep-anchored — every count reproducible by re-running the commands in `/app/memory/track_15_64_data/`.
* ✅ Tests / seeds / archived files excluded explicitly.
* ✅ Per-row purpose and severity assigned.
