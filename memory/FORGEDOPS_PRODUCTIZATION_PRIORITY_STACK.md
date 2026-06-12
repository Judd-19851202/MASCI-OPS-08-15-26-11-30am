# ForgedOps Productization — Priority Stack (Track 13.4C · Deliverable #2)

**Lens:** "What prevents Customer #2 from going live tomorrow?"  
**Out of scope:** anything that improves MASCI today but does not unlock multi-tenant operation. Those live in `MASCI_OPERATIONAL_RECOVERY_PRIORITY_STACK.md`.  
**Mode:** decision framework only · no implementation · no architecture.

---

## P-1 · Tenant Model

| Finding | Status |
|---|---|
| **W-01 No `tenants` / `customers` / `workspaces` / `organizations` / `tenant_settings` / `branding` collection in Mongo** | EXISTENTIAL |
| **W-02 No tenant scoping in production routes** | EXISTENTIAL |

Without these, every other ForgedOps priority is impossible. All 167 collections, 750 API paths, and 174 route files implicitly assume one tenant = MASCI.

## P-2 · Branding Engine

| Finding | Status |
|---|---|
| **W-06 / V-04 `tokens.css` declared "PROPOSAL — NOT YET WIRED"** | Retheming infrastructure exists in name only |
| **W-07 `portalPalette.js` static** | Colors hardcoded across 7 portals |
| **W-10 PDFs / outage alerts inline-branded** | Every server-generated artifact says MASCI |
| **W-15 Public surfaces share single brand chrome** | Public Safety Tile, QR landings, asset lookup all MASCI-styled |
| **W-19 Single i18n / palette / token files — no overlay model** | No per-tenant override layer exists |
| **W-16 `forgedops-logo.png` exists but no surface uses it** | Parent brand asset is dormant |

## P-3 · Tenant Settings & Configuration

| Finding | Status |
|---|---|
| **W-12 No tenant onboarding surface** | No admin path exists to create Customer #2 |
| **W-13 Per-workflow status engines hardcoded** | Workflow customisation impossible without code |
| **W-20 Email templates Python-coded** | Customer cannot edit email body without engineering |

## P-4 · Terminology Controls

| Finding | Status |
|---|---|
| **W-03 497 source files reference "MASCI"** | "MASCI" literal embedded across UI, PDF, email, Excel |
| **W-04 52 source files reference `mascigc.com`** | Default email routing baked in |
| Hardcoded role nouns: "Project Manager", "Foreman", "Superintendent", "Safety", "Daily Report", "JHA", "Training" | Customer cannot rename roles or work products |

## P-5 · Notification Controls

| Finding | Status |
|---|---|
| **W-08 Hardcoded recipient emails** (`jaymn.judd@`, `safety@`, `shopmanager@`) with platform-level env override only | Customer #2 emails go to MASCI staff by default |
| **W-18 Digest cadence partially tenant-ready** (`digest_settings`) | Positive — partial baseline exists |
| Sender identity is a single `RESEND_FROM` env var | Single sender per platform, not per tenant |

## P-6 · Customer Isolation

| Finding | Status |
|---|---|
| **W-14 8 auth flows × 0 tenant scope** | Customer #2 logins literally mingle with MASCI's |
| MFA / Passkey domain (`mfa_audit_events`, `user_passkeys`, `webauthn_challenges`) — single global domain | All challenges share one origin |
| Background jobs (Motive webhook, Resend webhook, backups) — single platform queue | No per-tenant scheduling or quotas |

## P-7 · Tenant Reports

| Finding | Status |
|---|---|
| **W-09 Hardcoded MASCI legal text inside equipment-issuance acknowledgement (EN + ES)** | LEGAL EXPOSURE — Customer #2 employees would sign documents legally naming MASCI as owner |
| **W-11 Excel export filenames prefix `MASCI_`** | `MASCI_jobs.xlsx`, `MASCI_pms.xlsx`, etc. |
| PDF builders inline MASCI brand and copy | Every PDF leaks brand |

## P-8 · Tenant Onboarding

| Finding | Status |
|---|---|
| No "Create Tenant" admin surface (W-12) | Manual ops project required per customer |
| No tenant-scoped seeding | Backfilling jobs / employees / equipment per tenant is undefined today |
| No custom domain / subdomain hook | Every tenant shares `safety-audit-mobile-1.preview.emergentagent.com` |
| No tenant-scoped public URLs | `/cheatsheet`, `/jha`, public-form paths are global |

---

## Productization tier mapping

| Priority block | Tier |
|---|---|
| P-1 Tenant Model · P-2 Branding Engine | **Tier 1 (foundational — nothing else works without them)** |
| P-3 Tenant Settings · P-4 Terminology · P-5 Notifications · P-6 Customer Isolation | **Tier 2 (operationally required for any second customer)** |
| P-7 Tenant Reports · P-8 Tenant Onboarding | **Tier 3 (required for self-service onboarding; sales/manual workaround is possible until then)** |

This stack is intentionally **separate** from the MASCI Operational Recovery Stack. The two roadmaps will share work in places (e.g., wiring `tokens.css` benefits both), but their priority orders are **independent** and must remain so.
