# TRACK 15.70 · Customer Clone Inventory (Phase 1)

_Generated 2026-06-22_

The complete inventory of items required to clone the MASCI platform
into a new customer deployment.

## 1 · MongoDB Atlas Cluster

| Item | MASCI | Customer #2 (required) |
|---|---|---|
| Provider | MongoDB Atlas | MongoDB Atlas |
| Cluster | dedicated `masci-production` | dedicated `customer2-production` (must be a SEPARATE cluster — see Phase 2) |
| Region | us-east-1 (per current env) | customer-chosen |
| Tier | per current MASCI contract | per Customer #2 contract |
| Backup | continuous + PIT enabled | continuous + PIT enabled |

## 2 · MongoDB Collections (per cluster)

MASCI database contains **181 collections** total. Of those:

| Tenant-aware | Count |
|---|---:|
| Yes (have `tenant_key` field) | **3** (`tenant_branding`, `email_routes`, `email_routing_audit_v2`) |
| No (no tenant scoping) | **178** |

Critical implication: **A new customer cannot share the MASCI database.** The customer must get its own cluster. See `TRACK_15_70_ISOLATION_CERTIFICATION.md` and `TRACK_15_70_CONFIGURATION_AUDIT.md`.

## 3 · Cloudflare R2 Buckets

| Item | MASCI | Customer #2 (required) |
|---|---|---|
| Bucket | `mascidocs-backups` (per `server.py` R2 logic) | `customer2-backups` (separate bucket) |
| API token | MASCI-scoped | Customer-2-scoped |
| Off-site backup mirror | enabled | enabled |

## 4 · Resend Domain

| Item | MASCI | Customer #2 (required) |
|---|---|---|
| Sending domain | `mascidocs.com` | `customer2.example` (or actual customer domain) |
| SPF / DKIM / DMARC | configured | must be configured per customer |
| Verified status | verified in Resend dashboard | must be verified before go-live |

## 5 · Resend API Keys

| Item | MASCI | Customer #2 (required) |
|---|---|---|
| Key | `re_CfH...A8kW` (env `RESEND_API_KEY`) | separate `re_xxx...` per customer |
| Scope | sending only | sending only |

## 6 · Branding Configuration

Per-tenant doc in `tenant_branding` collection:

```jsonc
{
  "_id": "<tenant_key>",
  "tenant_key": "<tenant_key>",
  "slug": "<url-slug>",
  "company_name": "Customer #2 Construction LLC",
  "platform_display_name": "Customer #2 Operations Platform",
  "platform_short_name": "C2 Hub",
  "primary_color": "#0F766E",
  "accent_color": "#14B8A6",
  "logo_url": "<https URL>",
  "marketing_url": "https://customer2.example",
  "support_email": "support@customer2.example",
  "safety_email": "safety@customer2.example",
  "hr_email": "hr@customer2.example",
  "operations_email": "ops@customer2.example",
  "from_email": "noreply@customer2.example",
  "reply_to": "support@customer2.example",
  "sender_name": "Customer #2 Operations Platform"
}
```

Schema verified live: provisioned `customer_2_deploy_test` + `customer_3_deploy_test` (see `track_15_70_deployment_simulation.json`).

## 7 · Logos

| Item | Requirement |
|---|---|
| Hosting | customer-provided HTTPS URL or upload to R2 |
| Format | SVG (preferred) or PNG ≥ 256×256 |
| Variants | header mark (~80×80) + optional wide logo |
| Fallback | `<GenericMonogram>` derived from `company_name.charAt(0)` (proven in 15.68D walkthrough) |

## 8 · Route Definitions

Per-tenant docs in `email_routes` collection. **All 19 production routes** must be seeded:

```
ACCOUNT_INVITES_FROM     ADMIN_DEAD_LETTER_TO     BACKUP_ALERTS (crit)
COMPLIANCE_ALWAYS_CC     DISPATCH_ROLE_TO         EXECUTIVE_DIGEST
FIELD_LEADERSHIP_ALWAYS_TO  HEALTH_ALERTS (crit)  INCIDENT_SEVERE_CC
OPERATOR_DIGEST_RECIPIENTS  OUTAGE_ALERTS (crit)  PASSWORD_RESET_MONITORING_TO
PAYROLL_VARIANCE_TO      PRE_OP_FAIL_FALLBACK     SAFETY_DIGEST_TO
SAFETY_FORMS_TO          SUPER_ADMIN_TO (crit)    TRENCH_SAFETY_PULSE_SAFETY
TRENCH_SAFETY_PULSE_SHOP
```

Seed script `backend/scripts/track_15_65_seed_email_routes.py` is **idempotent** but currently seeds the MASCI tenant only. For Customer #2 deployment, a **per-customer seed manifest** (YAML or JSON) is required — gap captured in `TRACK_15_70_PROVISIONING_RUNBOOK.md`.

## 9 · Environment Variables

| Variable | MASCI | Customer #2 | Notes |
|---|---|---|---|
| `MONGO_URL` | masci cluster | customer-2 cluster | per-deploy |
| `DB_NAME` | `masci_safety` | `customer2_safety` | per-deploy |
| `APP_ENV` | `production` | `production` | same |
| `EMAIL_ROUTING_V2` | `false` until cutover | `true` from day one | per-deploy |
| `RESEND_API_KEY` | MASCI Resend key | C2 Resend key | per-deploy |
| `SENDER_EMAIL` | `noreply@mascidocs.com` | `noreply@customer2.example` | per-deploy |
| `REPLY_TO_EMAIL` | `jaymn.judd@mascigc.com` | C2 ops email | per-deploy |
| `BACKUP_EMAIL_TO` | `jaymn.judd@mascigc.com` | C2 ops email | per-deploy |
| `SUPER_ADMIN_EMAIL` | `jaymn.judd@mascigc.com` | C2 super admin | per-deploy |
| `OUTAGE_ALERT_TO` | `jaymn.judd@mascigc.com` | C2 ops email | per-deploy |
| `SAFETY_FORMS_EMAIL_TO` | `safety@mascigc.com` | C2 safety email | per-deploy |
| `ADMIN_DEAD_LETTER_EMAIL` | `safety@mascigc.com` | C2 dead-letter | per-deploy |
| `LEADERSHIP_ALWAYS_TO_1/_2` | MASCI distros | C2 distros | per-deploy |
| `HEALTH_ALERT_RECIPIENTS` | MASCI | C2 | per-deploy |
| `COMPLIANCE_ALWAYS_CC` | MASCI compliance | C2 compliance | per-deploy |
| `OPERATOR_DIGEST_RECIPIENTS` | MASCI | C2 | per-deploy |
| `SAFETY_DIGEST_TO_EMAIL` | MASCI | C2 | per-deploy |
| `PUBLIC_APP_URL` | `https://mascidocs.com` | `https://customer2.example` | per-deploy — drives invite links |
| `R2_*` (account_id, bucket, access_key, secret_key) | MASCI R2 | C2 R2 | per-deploy |
| `SAFETY_SEED_USERS` | unset (uses MASCI default) | required to non-empty | per-deploy — refusal doctrine from 15.68C |
| `SHOP_SEED_USERS` / `HR_SEED_USERS` / `PM_SEED_DIRECTORY` | as above | as above | per-deploy |
| `BACKUP_HOURS_LOCAL` / `BACKUP_TIMEZONE` | MASCI | per-customer | per-deploy |

## 10 · Seed Users

| User type | MASCI | Customer #2 |
|---|---|---|
| Super admin | `jaymn.judd@mascigc.com` | customer-designated |
| Safety leads | MASCI safety roster (5 users, hardcoded in `auth.py:59-63`) | **gap — see Phase 2 audit** |
| Shop users | env-driven | env-driven |
| HR users | env-driven | env-driven |
| Field leadership | env-driven | env-driven |

**Gap**: `auth.py:59-63` hardcodes MASCI owner emails as seed users. For Customer #2, this seed would inject MASCI accounts into Customer #2's user table — a HARD ISOLATION BREACH if not guarded. Mitigation: refusal doctrine from 15.68C (auth seed already refuses for non-MASCI tenants OR needs env override). Verification: see `TRACK_15_70_CONFIGURATION_AUDIT.md`.

## 11 · Module Configuration

| Module | Currently | Customer-configurable? |
|---|---|---|
| Core | all customers | **No** (always on) |
| PM | all customers | **No** (always on) |
| Safety | all customers | **No** (always on) |
| Shop | all customers | **No** (always on) |
| Dispatch | all customers | **No** (always on) |
| HR | all customers | **No** (always on) |

**Gap**: No runtime module enable/disable. All modules ship enabled. See `TRACK_15_70_MODULE_CERTIFICATION.md`.

## 12 · Portal Configuration

| Portal | Currently | Customer-configurable? |
|---|---|---|
| Hub (`/`) | always on | always on |
| Safety (`/safety`) | always on | always on |
| Field (`/field`) | always on | always on |
| Shop (`/shop`) | always on | always on |
| PM (`/pm`) | always on | always on |
| HR (`/hr`) | always on | always on |
| Dispatch (`/dispatch`) | always on | always on |
| Admin (`/admin/*`) | always on | always on |

## 13 · Authentication Configuration

| Item | MASCI | Customer #2 |
|---|---|---|
| Auth mechanism | JWT-based custom auth (server.py-managed) | same | 
| Token store (frontend) | localStorage key `masci.admin.token` (admin), per-role keys (`safetyToken`, `shopToken`, etc.) | **same keys** — see audit |
| Passkey support | enabled | enabled |
| Super admin email | `jaymn.judd@mascigc.com` (env) | customer-designated |

**Gap**: localStorage keys are not tenant-prefixed. A user with MASCI and C2 cookies in the same browser would have token collision — not a deployment blocker (different domains) but a UX gotcha. Captured in Tier-2 backlog.

## 14 · Backup Configuration

| Item | MASCI | Customer #2 |
|---|---|---|
| Daily zip backup | `_backup_scheduler_loop` (server.py:5702) | same — runs per deploy |
| Backup storage | local disk + R2 mirror | per-customer R2 bucket |
| Backup email | "MASCI Hub — Full Backup" (server.py:5437) **hardcoded** | gap — see audit |
| Backup schedule | env `BACKUP_HOURS_LOCAL` | env override |

## Inventory Summary

| Category | Items | Per-customer config? | Hardcoded leak? |
|---|---:|:-:|:-:|
| Atlas | 1 cluster | ✅ via `MONGO_URL` | — |
| R2 | 1 bucket | ✅ via `R2_*` env | — |
| Resend | 1 domain + 1 key | ✅ via env | — |
| Branding | 1 `tenant_branding` doc | ✅ DB insert | — |
| Email routes | 19 docs | ✅ DB insert (script needed) | — |
| Env vars | ~20 keys | ✅ per-deploy | — |
| Seed users | 5 hardcoded + N env-driven | ⚠️ MASCI defaults in auth.py:59-63 | YES |
| Module config | — | ❌ not runtime-configurable | YES |
| Portal config | — | ❌ not runtime-configurable | YES |
| Auth config | JWT + passkey | ✅ shared codepath | — |
| Backup config | scheduler | ✅ env-driven | ⚠️ email subject hardcoded |
| **Business-data isolation** | 178 collections | ❌ NO `tenant_key` field | **YES — see Phase 5** |

## Verdict

✅ Tenant chrome (branding, routing, email) is **fully config-driven**.
⚠️ Business data (users, daily_reports, incidents, equipment, dispatch, …) is NOT tenant-scoped — Customer #2 MUST use a separate cluster.
⚠️ 3 hardcoded blockers in deployment path (auth.py seed, backup email subject, Hub.jsx eyebrow caches sometimes).
❌ Module enablement is not runtime-configurable — all modules ship enabled.

Customer #2 deployment is **feasible via the separate-cluster model**. Single-cluster multi-tenant is **NOT supported** and is out of 15.70 scope.
