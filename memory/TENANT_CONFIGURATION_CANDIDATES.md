# Tenant Configuration Candidates · Phase 10 · Document 4 of 5

**Date:** 2026-05-24
**Purpose:** For every MASCI-specific surface area, define what becomes per-tenant config in a future SaaS deployment. This is the **specification**, not the implementation.

---

## Configuration tier model

| Tier | Description | Examples |
|---|---|---|
| **Tier 1 · Env var** | Single string per tenant; default value preserves current behavior | tenant name, brand color, sender email |
| **Tier 2 · Per-tenant config doc** | JSON / Mongo doc per tenant; overrides defaults | full company info, holiday calendar, email signatures |
| **Tier 3 · Per-tenant content collection** | Mongo collection scoped by tenant_id; tenant authors content | guidance copy, training catalog, glossary additions |
| **Tier 4 · Per-tenant asset** | File-storage per tenant; admin upload | logo SVG, hero images, custom PDF letterheads |
| **Tier 5 · Per-tenant legal doc** | Authored per tenant (cannot be templated) | Terms of Service, Privacy Policy |

---

## Configuration candidate inventory

### Tier 1 · Env vars (the cheap & easy bucket)

| Proposed env var | Today's value | Default behavior |
|---|---|---|
| `TENANT_NAME` | "MASCI" | Used by FastAPI title + HTML `<title>` + email subject prefixes |
| `TENANT_LEGAL_NAME` | "MASCI General Contractors Inc." | Used in PDF footers + email signatures |
| `TENANT_FILENAME_PREFIX` | "MASCI_HUB" | Used in PDF / DOCX / ZIP / XLSX / CSV Content-Disposition filenames |
| `TENANT_PHONE` | "386-322-4500" | Used in PDF footers + JhaPlansPosterCard |
| `TENANT_ADDRESS_LINE_1` | "5752 South Ridgewood Avenue" | Used in PDF footers |
| `TENANT_ADDRESS_LINE_2` | "Port Orange, FL 32127-6442" | Used in PDF footers |
| `TENANT_EMAIL_DOMAIN` | "mascigc.com" | Used in placeholder text on EmployeeMaster + AdminPM panels |
| `TENANT_WEBSITE` | "mascigc.com" | Used in PDF footers + sign-in greetings |
| `TENANT_SENDER_EMAIL` | "noreply@mascidocs.com" | Resend email From: |
| `TENANT_REPLY_TO_EMAIL` | "jaymn.judd@mascigc.com" | Resend Reply-To: |
| `TENANT_SAFETY_INBOX` | "safety@mascigc.com" | Hardcoded fallback in `email_routing.py` |
| `TENANT_SHOP_INBOX` | "shopmanager@mascigc.com" | Hardcoded fallback in `email_routing.py` |
| `TENANT_BACKUP_ALERT_TO` | "jaymn.judd@mascigc.com" | Backup verification alert recipient |
| `TENANT_OUTAGE_ALERT_TO` | "jaymn.judd@mascigc.com" | Outage alert recipient |
| `TENANT_SUPER_ADMIN_EMAIL` | "jaymn.judd@mascigc.com" | Bootstrap super-admin email |
| `TENANT_SUPER_ADMIN_BOOTSTRAP_PASSWORD` | "Maddix123!" | Bootstrap super-admin password |
| `TENANT_ADMIN_BOOTSTRAP_PASSWORD` | "MASCI1982!" | Admin password for legacy single-secret pages |
| `TENANT_DEFAULT_LOCALE` | "en" | Default UI language (en or es) |

**Total Tier 1 candidates: ~18 env vars.**

### Tier 2 · Per-tenant config document (richer per-tenant state)

A Mongo collection `tenants` with one document per tenant:

```json
{
  "tenant_id": "masci",
  "company_info": {
    "name": "MASCI",
    "legal_name": "MASCI General Contractors Inc.",
    "address": { ... },
    "phone": "386-322-4500",
    "website": "mascigc.com",
    "email": "safety@mascigc.com"
  },
  "branding": {
    "primary_color": "#991b1b",
    "logo_url": "/assets/tenants/masci/logo.svg",
    "logo_lockup_url": "/assets/tenants/masci/lockup.svg",
    "favicon_url": "/assets/tenants/masci/favicon.png"
  },
  "email_routing": {
    "safety": ["safety@mascigc.com", "jaymn.judd@mascigc.com"],
    "shop": ["shopmanager@mascigc.com"],
    "backup_alerts": ["jaymn.judd@mascigc.com"],
    "outage_alerts": ["jaymn.judd@mascigc.com"]
  },
  "auto_email_reports": false,
  "rate_limiting": "off",
  "public_post_limit_per_hour": 30,
  "login_max_fails": 10,
  "login_lockout_seconds": 900,
  "session_timeouts_enabled": true,
  "backup_hours_utc": [2, 18],
  "holiday_calendar_id": "us_construction_2026",
  "feature_flags": {
    "fmcsa_dq_files": true,
    "spanish_ui": true,
    "field_leadership_portal": true
  }
}
```

**Treatment:** Replaces `companyInfo.js` defaults + `email_routing.py` fallbacks + most of `backend/.env` tenant-scoped vars.

### Tier 3 · Per-tenant content collections

| Collection | Today's source | Per-tenant treatment |
|---|---|---|
| `tenant_guidance_content` | `backend/guidance/content.py` (52 MASCI hits) + `tips.py` (24) + `translations_es.py` (47) + `tips_es.py` (23) | Mongo collection scoped by tenant_id; admin-editable via Admin Console |
| `tenant_training_catalog` | `frontend/src/data/training.js` (23 hits) | Mongo collection; admin-editable |
| `tenant_safety_topic_library` | `routes/safety_topic_library.py` | Already a Mongo collection; just add tenant_id filter |
| `tenant_glossary_extensions` | `AdminOperationalLanguage.jsx` (16 hardcoded entries) | Mongo collection of additional entries per tenant; canonical 16 remain in code |
| `tenant_holiday_banners` | i18n.js hardcoded strings | Mongo collection of date-gated banners per tenant |

**Note:** The canonical 16 glossary entries stay in code (industry-standard). Per-tenant additions go in the collection.

### Tier 4 · Per-tenant assets (file storage)

| Asset | Today's location | Per-tenant treatment |
|---|---|---|
| Logo SVG (mark) | `frontend/src/components/MasciLogo.jsx` (inline) | `/assets/tenants/{tenant_slug}/logo.svg` |
| Logo SVG (lockup) | (inline) | `/assets/tenants/{tenant_slug}/lockup.svg` |
| Brand favicon | `frontend/public/favicon.ico` | `/assets/tenants/{tenant_slug}/favicon.ico` |
| PDF letterhead images | embedded in `pdf_render.py` | per-tenant uploads |
| Hero / banner images | `/assets/` | per-tenant uploads |

**Treatment:** A CDN-style assets bucket organized by tenant slug. `MasciLogo.jsx` becomes `TenantLogo.jsx` reading from the tenant config.

### Tier 5 · Per-tenant legal documents

| Doc | Today's location | Per-tenant treatment |
|---|---|---|
| Terms of Service | `frontend/src/pages/legal/TermsOfService.jsx` (45 MASCI hits) | Authored per tenant; **cannot be templated** (legal language must be specific) |
| Privacy Policy | `frontend/src/pages/legal/PrivacyPolicy.jsx` (30 hits) | (same) |
| End User License Agreement | not yet a doc | (would be created per tenant) |

**Treatment:** A simple per-tenant `tenant_legal_docs` collection containing rendered HTML, with per-tenant authoring required.

---

## Configuration loading strategy

### Backend
1. On startup: read `TENANT_ID` env var (`MASCI` default for current single-tenant deploy).
2. Load tenant config document from `tenants` collection.
3. Cache in memory; reload on `SIGHUP` or admin trigger.
4. Inject into FastAPI dependency for routes that need tenant info.

### Frontend
1. On first load: fetch `GET /api/tenant/config` → returns brand + locale + feature_flags subset.
2. Cache in localStorage with a tenant-config-version key.
3. Use a `<TenantProvider>` context wrapping the app.
4. Components read from context (e.g., `<TenantLogo />` replaces `<MasciLogo />`).

### Multi-tenant (future)
1. Tenant resolved from subdomain (`masci.platform.com`) or path (`/t/masci/...`) or header (`X-Tenant-Id`).
2. All Mongo queries gain `tenant_id` filter (Path B) OR per-tenant DB switch (Path A).
3. JWT signing key rotated per tenant for cross-tenant token isolation.

**This document specifies the WHAT, not the HOW. The HOW belongs to a future productization-execution phase.**

---

## What is NOT a tenant config candidate

These items should **stay in code** even after productization, because they are platform-level decisions, not tenant-level:

- The 7-portal RBAC matrix (admin/safety/hr/pm/shop/dispatch/fl).
- The 8 governance detector rules.
- The 19-row notification discipline matrix.
- The 16-entry canonical glossary (industry-standard terms).
- The CAPA status pipeline (Open → In Progress → Pending Review → Verified → Closed).
- The severity-escalation safety net (Tier-2 lock on serious incidents).
- LifecycleGuide instances.
- The Smart Operational Disclosure UX pattern.
- The Phase 6 completion-banner derivation logic.
- The `useDraftSync` autosave pattern.

These are the platform's intellectual property. They are tenant-neutral by design and must NOT be made configurable — configurability would dilute the operational discipline that took 9 phases to harden.

---

## What COULD become a tenant config but should NOT (yet)

These items are configuration-shaped but would create more harm than good if exposed to tenant admins:

| Tempting toggle | Why not (yet) |
|---|---|
| "Skip Tier-2 lock on serious incidents" | Compromises the platform's most important safety net |
| "Disable second-reviewer rule on CAPA verification" | Compromises audit integrity |
| "Custom severity scale" | Breaks cross-tenant comparability + governance findings logic |
| "Per-tenant glossary that overrides canonical 16" | Defeats the platform's operational language consistency |
| "Disable governance findings" | Defeats the platform's core differentiation |
| "Per-tenant notification tiers" | Breaks the discipline matrix |
| "Custom CAPA status pipeline" | Breaks downstream lifecycle logic |
| "Per-tenant role names" (rename "Safety" to "EHS") | Breaks UI + RBAC + glossary continuity |

These are the boundaries beyond which configuration becomes platform fragmentation. Productization must respect these.

---

## Approximate productization effort estimate

Given the candidate inventory:

| Tier | Effort | Notes |
|---|---|---|
| Tier 1 (env vars) | 4-6 days | Sweep ~50 literals across server.py + email templates + frontend public/ |
| Tier 2 (per-tenant config doc) | 5-7 days | New collection + loader + admin UI |
| Tier 3 (content collections) | 8-12 days | Migrate 6 content surfaces from code to Mongo + admin authoring UI |
| Tier 4 (per-tenant assets) | 4-6 days | Asset bucket + upload flow + `<TenantLogo />` swap |
| Tier 5 (per-tenant legal docs) | 2-3 days | Loader + admin authoring UI (no template work) |

**Total productization effort: ~25-35 engineer-days of disciplined work.**

This is the work to reach a "rebrandable, single-tenant, per-deploy-customizable" platform. Multi-tenancy (shared DB, per-tenant rows) adds another 30-60 days on top of this baseline.

---

## Conclusion

The tenant configuration candidates are well-bounded and stratifiable across 5 tiers. The platform's intellectual property is properly excluded from configurability. The estimated 25-35 days of productization work would deliver a fully rebrandable single-tenant deploy; multi-tenancy is a separate program above this baseline.

Detailed in `COMMERCIALIZATION_BLOCKERS.md`.
