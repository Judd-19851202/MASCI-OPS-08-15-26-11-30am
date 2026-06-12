# ForgedOps — White-Label Readiness Audit (Track 13.4B · Phase 2C)

**Mode:** Discovery only. No scoring. No recommendations. No fixes.  
**Generated:** 2026-02 (Track 13.4B Phase 2C)  
**Evidence basis:** Live source tree + DB + Phase 1 inventory + Phase 2A/2B.

> **Core question this audit answers:** *If ForgedOps signs Customer #2
> tomorrow, what breaks?*  
> This document records facts. It does not propose architecture.

---

## A. Tenant Model

### A.1 Mongo collections that would indicate multi-tenancy
| Collection name probed | Present? |
|---|---|
| `tenants` | ❌ missing |
| `customers` | ❌ missing |
| `workspaces` | ❌ missing |
| `organizations` | ❌ missing |
| `tenant_settings` | ❌ missing |
| `branding` | ❌ missing |

**Result:** the platform has **no tenant model at all**. Every Mongo collection (167 of them — Phase 1 §A) belongs to a single implicit tenant.

### A.2 Code grep for tenant-scoping fields
`grep -rln "tenant_id|customer_id|workspace_id|organization_id" /app/backend --include="*.py"` returns matches only inside `/app/backend/tests/*` (test fixture names — not actual scoping). **No production route enforces tenant scoping.**

### A.3 Implied tenant
Where a tenant identity is implied today, the implicit value is **MASCI General Contractors Inc.** Evidence is in §B–§I below.

---

## B. Branding hardcoding — measured

`grep -rin "masci" /app/frontend/src /app/backend --include="*.py" --include="*.jsx" --include="*.js" -l` (excluding `test_*` files):

| Metric | Count |
|---|---|
| Source files containing `"MASCI"` literal | **497** |
| Source files containing the email domain `mascigc.com` | **52** |
| Source files containing `"ForgedOps"` (parent brand) | **73** |

### B.1 Logo / image assets
| Asset | Location |
|---|---|
| `forgedops-logo.png` | `/app/frontend/src/assets/forgedops-logo.png` (parent brand) |
| MASCI logo image(s) | embedded inline in components; no single `masci-logo.png` asset found in `/app/frontend/src/assets/` |

### B.2 Hardcoded brand text in UI (sample, observed via grep)
```
"MASCI Operations Platform — No Guesswork. No Missed Steps. No Excuses."
"MASCI Employee Roster"
"MASCI equipment"
"MASCI employee"
"MASCI count"
"MASCI_jobs.xlsx"
"MASCI_pms.xlsx"
"MASCI_Inspection_abc12345"
"MASCI"  (× many)
```

### B.3 Hardcoded brand text in server-rendered output
```
"MASCI Dispatch"                            (server.py)
"MASCI HQ"                                  (server.py)
"MASCI Operations Platform Record"          (server.py PDF title)
"MASCI Hub — Outage detected."              (outage_alerts.py)
"MASCI General Contractors Inc."            (safety_forms.py — legal text, EN + ES)
```

### B.4 Color palette
- `portalPalette.js` is a single JS object exported as a constant. **Not** sourced from a tenant config.
- `tokens.css` is a CSS variable layer marked "PROPOSAL — NOT YET WIRED" — so even the *plumbing* for retheming exists in name only today.
- All portal accents (admin slate / pm indigo / hr violet / shop orange / safety cyan / dispatch orange / FL red / leadership red) are hardcoded in the palette.

**White-label verdict (factual):** branding is **hardcoded**. No tenant-config layer exists.

---

## C. Contact info (emails, phones, addresses)

### C.1 Hardcoded "From / To / CC" email addresses in code (sample from grep)
```
"jaymn.judd@mascigc.com"
"safety@mascigc.com"
"shopmanager@mascigc.com"
```
All three appear as **default recipient lists** inside Python route files (e.g., `safety_forms.py` ~lines 14–31, 72; field leadership routes line 75–76). Each is overridable by env vars (e.g., `LEADERSHIP_ALWAYS_TO_1`) — partial configurability, NOT tenant-modeled.

### C.2 Hardcoded legal phrases that include the company name
```
"Office phone, address, and after-hours contact for MASCI General Contractors Inc."
"… this equipment remains the property of MASCI General Contractors Inc. …"
"… ha sido devuelto a MASCI General Contractors Inc. …"
"… the equipment listed above has been returned to MASCI General Contractors Inc. …"
```

### C.3 Hardcoded phone / address strings
Grep found `407-`, `813-`, `321-`, `863-`, `352-` area code patterns. Mostly inside test fixtures (e.g., `email_routing.py`) and form-default text. No central "tenant phone" config exists.

**Verdict:** contact info is **hardcoded with partial env-var override**. Not tenant-modeled.

---

## D. Terminology (PM · Foreman · Supervisor · Safety · DR · JHP · Training)

| Term | Where used | Configurable? |
|---|---|---|
| "Project Manager" / "PM" | All portals, navs, form titles, emails | hardcoded in source strings |
| "Foreman" | Field-side forms, FL records | hardcoded |
| "Superintendent" | governance language, admin pages | hardcoded |
| "Safety" / "Safety Manager" | Safety portal, recipient lists | hardcoded |
| "Daily Report" | UI strings + email subjects + PDF titles | hardcoded |
| "JHP" / "JHA" | UI strings + collections (`jhas`, `job_hazard_plans`) | hardcoded |
| "Training" / "Training Center" | UI + DB collections | hardcoded |
| Status verbs (`active`, `closed`, `submitted` etc.) | engine literals + UI helper renderers | hardcoded |

→ **Terminology cannot be customised per tenant today.** Even with the
800+ orphan `t()` strings replaced, the underlying *concepts* are
literal strings in source.

---

## E. Workflow Configuration

### E.1 Workflows
~25 named workflows (Phase 1 §E / Phase 2B §B). Each workflow is implemented as:
- a route handler (per-workflow file in `/app/backend/routes/`)
- one or more Mongo collections
- per-workflow status-engine logic embedded in Python code (no central state machine)

### E.2 Departments
There is **no "department" concept** in the data model — only role-named portals (Safety, Shop, HR, etc.). No `departments` collection.

### E.3 Roles
- `role_templates` collection exists (per Phase 1 §J — observed in collection listing) → some role customization is *possible* in principle.
- `user_directory` carries portal token columns (`portal_tokens.admin`, `.dispatch`, `.pm`, etc.) — fixed schema: a tenant cannot add a portal without code.
- The 9 portals are hardcoded in `App.js` routing.

### E.4 Approval paths
- Per-workflow only (e.g., Time Off has its own approve/deny; Asset Transfer has its own approve flow). No generic "approvals engine".

**Verdict:** different customers **cannot** run different statuses /
workflows / departments / roles / approval paths without code changes.

---

## F. Notifications & Email branding

### F.1 Recipients
- Configurable via env vars (e.g., `LEADERSHIP_ALWAYS_TO_1`, `LEADERSHIP_ALWAYS_TO_2`, `SHOP_MANAGER_EMAIL`) — **per-platform**, not per-tenant.
- Default values are MASCI email addresses (`jaymn.judd@`, `safety@`, `shopmanager@`).

### F.2 Sender identity
- Resend "From" address is set by env var (e.g., `RESEND_FROM`), single value, not per-tenant.
- Sender name strings often hardcoded in templates (e.g., "MASCI Operations Platform").

### F.3 Templates
- `branded_portal_emails.py` — single template file for all portals. Edits require code changes.
- `email_routing.py` — routing rules in code.
- `role_templates.py` — role-specific templates in code.

### F.4 Digests
- `admin_digest_config.py` exists — config is collection-backed (`digest_settings`). **Configurability without code-change exists** (frequency, cohort), but tenant-scoping does not.

**Verdict:** customers **cannot** control recipients / branding / sender / templates without development. Digest cadence is the lone partial exception.

---

## G. Public Surfaces (Public Safety Tile, QR pages, Asset Lookup, Public forms, Public references)

| Surface | Logo source | Color source | Brand string source | Tenant-configurable? |
|---|---|---|---|---|
| Hub home `/` | inline `<MasciLogo>` ref | hardcoded Tailwind | "MASCI Operations Platform" | no |
| Cheatsheet `/cheatsheet` | inline | hardcoded | "MASCI" | no |
| JHA viewer `/jha` | inline | hardcoded | "MASCI" | no |
| Trench Boxes `/trench-boxes` | inline | hardcoded | "MASCI" | no |
| Trench Safety public QR landing | inline | hardcoded | "MASCI Trench Safety" | no |
| Public forms (`/inspect/new`, `/meetings/new`, `/incidents/new`, `/daily/new`, `/equipment/new`, `/constraints/new`, `/odr/new`) | inline | hardcoded | inline brand | no |
| Public Safety Tile + Public references | inline | hardcoded | inline brand | no |
| Asset Lookup deep link | inline | hardcoded | inline brand | no |

**Verdict:** zero public surface is tenant-brandable today.

---

## H. Reporting (PDFs, exports)

### H.1 PDFs
- `pm_welcome_pdf.py`, `field_leadership_pdf.py`, `training_pdf.py`,
  `hub_banners_pdf.py`, `safety_forms.py` (PDF builders), Trench Safety
  report PDFs, ODR PDFs — all reference "MASCI" branding **inline**.
- No PDF builder reads a `tenant_branding` config.

### H.2 Exports
- Excel filenames include hardcoded brand: `"MASCI_jobs.xlsx"`, `"MASCI_pms.xlsx"`, `"MASCI_Inspection_..."`. → tenant cannot rebrand exports.

### H.3 QR codes
- QR posters embed MASCI branding inline.

**Verdict:** PDFs / exports / QR are not tenant-brandable.

---

## I. Configuration (could a customer onboard without engineering?)

| Configuration item | Customer-editable today? |
|---|---|
| Company name | ❌ — would require ≥ 497 source-file edits + 4 hardcoded-string surfaces (UI · PDF · email · legal text) |
| Logo | ❌ — assets are inline; no upload UI for brand assets |
| Colors | ❌ — `portalPalette.js` + `portal-system.css` are static; `tokens.css` is unwired |
| Terminology (PM/Foreman/etc.) | ❌ — see §D |
| Roles | ❌ — 9 portals + routing hardcoded |
| Departments | ❌ — no concept exists |
| Training catalog | ✅ partially — `training_guides` / `training_videos` collections are admin-editable via `AdminTraining` / `AdminTrainingVideos` UIs |
| Notifications cadence | ✅ partially — `admin_digest_config.py` → `digest_settings` collection |
| Notification recipients | ❌ partial only — env-var overrides at platform level |
| Email templates | ❌ — Python code |
| Branding (per-public-surface) | ❌ — see §G |
| Tenant isolation | ❌ — no tenant model |

**Headline:** **0 of 12** customer-onboarding-relevant items are
end-to-end customer-configurable. 2 of 12 are partially admin-editable
(training catalog, digest cadence) — both still platform-scoped, not
tenant-scoped.

---

## J. If ForgedOps signs Customer #2 tomorrow — what breaks?

### J.1 Breaks immediately (no workaround)
1. The same Mongo database serves both tenants → Customer #2's daily reports / employees / assets would mingle with MASCI's data. (**No tenant model**.)
2. Every PDF / email / Excel export shipped to Customer #2 says "MASCI" or "MASCI General Contractors Inc.".
3. The Hub homepage tagline `"MASCI Operations Platform — No Guesswork. No Missed Steps. No Excuses."` is hardcoded.
4. The Safety equipment issuance legal text identifies MASCI as the owning entity (both English and Spanish) — legal exposure.
5. Outage alerts say "MASCI Hub — Outage detected." in every customer's incident channel.
6. Hardcoded default recipient lists (`safety@mascigc.com`, `jaymn.judd@mascigc.com`, `shopmanager@mascigc.com`) — Customer #2 would email MASCI staff by default.
7. Excel exports filenames begin with `MASCI_`.
8. QR posters embed MASCI branding inline.
9. The 9 portals are routing-hardcoded → a customer that doesn't need (say) Dispatch cannot have the route hidden.
10. The `forgedops-logo.png` exists but no surface uses it as the *primary* brand mark — every page uses MASCI brand.

### J.2 Blocks onboarding (no tenant onboarding UI)
- No "Create Tenant" admin surface.
- No tenant-scoped data backfill / seeding.
- No tenant-isolated background jobs (Motive webhook, Resend webhook, backups would mix).
- No tenant-scoped MFA / Passkey domains.
- No tenant-scoped public URLs (e.g., everyone shares `/cheatsheet`, `/jha`, public form paths).

### J.3 Requires code changes (manual customization)
- Branding: 497 files mention "MASCI" + 52 mention `mascigc.com` + a number of PDF/email senders.
- Terminology: every literal "Project Manager", "Daily Report", "JHA", etc.
- Status engine vocabularies (~12 engines).
- Role / department / approval-path differences.
- Public surface chrome (each public surface has its own header).

### J.4 What IS tenant-ready (or "close to ready") today
- `digest_settings` collection — supports cadence customization.
- `training_guides` and `training_videos` collections — admin-editable training catalogs.
- `role_templates` collection — *some* role customization plumbing exists.
- Env-var override for select recipient lists (Leadership · Shop · Safety) — works at platform level, not tenant level.
- `tokens.css` exists as a CSS-variable retheme layer **in name only** (status: PROPOSAL — not wired).

### J.5 What is NOT tenant-ready
- Everything else listed above.

---

## K. Findings index (Phase 2C)

| # | Finding type | Where | Status |
|---|---|---|---|
| W-01 | No tenant model | Mongo (no tenants / customers / workspaces / branding collections) | observed |
| W-02 | No tenant scoping in route code (production routes) | all 174 route files | observed |
| W-03 | 497 source files reference "MASCI" literal | grep | measured |
| W-04 | 52 source files reference `mascigc.com` domain | grep | measured |
| W-05 | 73 source files reference "ForgedOps" | grep | measured |
| W-06 | `tokens.css` declares itself "PROPOSAL — NOT YET WIRED" | file header | observed |
| W-07 | `portalPalette.js` is a static JS module — no tenant config layer | source | observed |
| W-08 | Hardcoded recipient emails (`jaymn.judd@`, `safety@`, `shopmanager@`) with only platform-level env override | `safety_forms.py`, leadership routes | observed |
| W-09 | Hardcoded legal phrases identify MASCI as owning entity (EN + ES) | `safety_forms.py` lines 189/195/493/498 | observed |
| W-10 | PDF builders / outage alerts embed brand string inline | server.py 251/257/2183/2402, outage_alerts.py 159 | observed |
| W-11 | Excel export filenames prefix `MASCI_` | server.py exports | observed |
| W-12 | No tenant onboarding surface exists | Admin module audit | observed |
| W-13 | Status engines hardcoded per workflow — no per-tenant customization possible | 12 per-workflow engines | observed |
| W-14 | 8 auth-flow variations × 0 tenant scope = customer-#2 auth would mingle with MASCI | per-portal `/login` | observed |
| W-15 | Public surfaces share a single brand chrome family — no tenant isolation | public surfaces in Phase 1 §C | observed |
| W-16 | `forgedops-logo.png` asset exists but is not the primary brand mark on any surface | `/app/frontend/src/assets/` | observed |
| W-17 | Training catalog (`training_guides`, `training_videos`) IS admin-editable — partial tenant-readiness | Phase 1 §G | observed |
| W-18 | Digest cadence (`digest_settings`) IS admin-editable — partial tenant-readiness | `admin_digest_config.py` | observed |
| W-19 | 1 token system, 1 palette file, 1 i18n file — no per-tenant overlay possible without code | core layout | observed |
| W-20 | Email templates Python-coded — customer cannot customise without code | `branded_portal_emails.py`, `email_routing.py` | observed |

---

## L. What this audit did NOT do
- Did not score the severity of any finding.
- Did not propose a multi-tenant architecture.
- Did not propose a token-system rollout plan.
- Did not propose a branding-config schema.
- Did not estimate effort for any change.
- Did not test any potential tenant isolation strategy.
- Did not enumerate every individual MASCI mention (only counted files and quoted representatives).

All deferred to a later track once discovery is operator-approved.
