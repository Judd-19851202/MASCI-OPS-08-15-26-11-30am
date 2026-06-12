# ForgedOps — Customer #2 Blocker Matrix (Track 13.4B · Phase 3)

**Mode:** Discovery + ranked classification. No remediation plan, no architecture proposal.  
**Generated:** 2026-02 (Track 13.4B Phase 3)  
**Sister docs:** `FORGEDOPS_WHITE_LABEL_READINESS_AUDIT.md`, `MASCI_PLATFORM_MASTER_FINDINGS_REGISTRY.md`.

---

## A. Core question

**If ForgedOps signs Customer #2 tomorrow — what stops them from going live?**

This document classifies every white-label and tenant-readiness finding by
how it blocks onboarding, then ranks them.

---

## B. Blocker categories

### B.1 Blocks immediately (no workaround possible without code)

| Blocker | Symptom | Master ID |
|---|---|---|
| Single shared Mongo DB · no tenant model | Customer #2 daily reports / employees / assets mingle with MASCI's | **W-01 · W-02** |
| Hub homepage tagline hardcoded | `"MASCI Operations Platform — No Guesswork. No Missed Steps. No Excuses."` baked into source | **W-03** |
| Hardcoded MASCI legal text inside equipment-issuance acknowledgement (EN + ES) | Customer #2 employees sign forms that legally identify MASCI as owner | **W-09** |
| PDFs identify MASCI in titles and captions | "MASCI Operations Platform Record", "MASCI Dispatch", "MASCI HQ" hard-coded | **W-10** |
| Outage alerts say "MASCI Hub — Outage detected." | Every customer's incident channel sees MASCI brand | **W-10** |
| Hardcoded default recipient emails | `safety@mascigc.com`, `jaymn.judd@mascigc.com`, `shopmanager@mascigc.com` baked into route handlers | **W-08** |
| Excel exports prefix `MASCI_` | Customer #2 office staff download `MASCI_jobs.xlsx` | **W-11** |
| QR posters embed MASCI branding inline | Public field surfaces show MASCI brand | **W-03 · W-15** |
| 9 portals are routing-hardcoded | Customer that doesn't need Dispatch can't have route hidden | **W-13 · W-14** |
| `forgedops-logo.png` exists but no surface uses it as the primary brand | The parent brand can't even be foregrounded | **W-16** |

### B.2 Brand leak (functional but smells of MASCI)

| Brand leak | Where | Master ID |
|---|---|---|
| 497 source files reference "MASCI" literal | grep-measured | **W-03** |
| 52 source files reference `mascigc.com` | grep-measured | **W-04** |
| `tokens.css` "PROPOSAL — NOT YET WIRED" | retheming infrastructure exists in name only | **V-04 · W-06** |
| `portalPalette.js` static | colors hardcoded | **W-07** |
| Single global `i18n.js` | no per-tenant string overrides | **W-19** |
| Email templates Python-coded | tenant can't change template body | **W-20** |
| Public surface chrome shared across tenants | each public form has MASCI-styled header | **V-14 · W-15** |
| Per-portal hub files diverge (145 → 668 lines · 4.6×) | hard to template for tenant-specific layout | **V-05 · V-06** |
| 8 distinct `*CommandCenter` pages | cloning a portal for a tenant means cloning 8 pages | **V-09** |
| 15 status-chip components | tenant theme overrides hit 15 places | **V-07** |
| `MotiveDrivers` cleanup tile, integration health card (now removed from HR) | OPS plumbing leaking into roles | **R-06 · V-08** |

### B.3 Legal / Compliance leaks

| Leak | Risk | Master ID |
|---|---|---|
| MASCI General Contractors Inc. named as owning entity in equipment-issuance acknowledgement (EN + ES) | Customer #2 employees sign documents legally referencing MASCI as the property owner — exposes both parties | **W-09** |
| Spanish version of legal text also hardcoded | identical exposure for Spanish-speaking employees | **W-09** |
| OSHA-related guidance strings in safety bucket are MASCI-curated content | acceptable as content but rebranding requires editing strings | **T-01** |

### B.4 Routing & email leaks

| Leak | Where | Master ID |
|---|---|---|
| `safety@mascigc.com` is default safety recipient | `safety_forms.py` lines 14–31, 72 | **W-08** |
| `jaymn.judd@mascigc.com` is default leadership recipient | leadership routes lines 75–76 | **W-08** |
| `shopmanager@mascigc.com` is default shop recipient | `safety_forms.py` line 31 | **W-08** |
| Resend "From" address is a single env var | platform-level only, not per-tenant | **W-08 · W-20** |
| Outage alert recipient list is hardcoded | `outage_alerts.py` | **W-10** |

### B.5 Data-assumption leaks

| Assumption | Symptom for Customer #2 | Master ID |
|---|---|---|
| Single `jobs_master` collection scoped to MASCI projects | Customer #2 projects co-exist in same table | **W-01** |
| Single `equipment_master` collection | Same | **W-01** |
| Single `employees` collection | Same | **W-01** |
| Single `user_directory` collection | Customer #2 logins mingle with MASCI | **W-01 · W-14** |
| All 167 collections lack a tenant-scoping field | Backend route filters do not partition by tenant | **W-02** |
| Geofences (`motive_geofences`) are MASCI Florida service area | Customer #2 geofences would have to coexist | **W-01 · D-06** |
| Motive webhook posts into single collection | Customer #2 telematics would mingle | **W-01** |

### B.6 Workflow & terminology leaks

| Leak | Where | Master ID |
|---|---|---|
| "Project Manager" / "PM" / "Daily Report" / "JHA" hardcoded in UI + email + PDF | global | **W-13** |
| 12 per-workflow status engines hardcoded | tenant can't customize statuses | **W-13** |
| 9 portals + ~25 workflows + ~30 forms hardcoded | tenant can't subset modules | **W-13 · W-14** |
| Field Leadership 10 record kinds hardcoded | tenant can't add an 11th kind without code | **W-13** |

### B.7 Onboarding-flow blockers

| Blocker | Master ID |
|---|---|
| No "Create Tenant" admin surface | **W-12** |
| No tenant-scoped seeding (jobs, employees, equipment) | **W-12** |
| No tenant-scoped background jobs (Motive · Resend · backups would mix) | **W-01 · W-12** |
| No tenant-scoped MFA / Passkey domains | **W-12** |
| Public URLs shared (`/cheatsheet`, `/jha`, public-form paths) | **W-15** |
| No subdomain / custom-domain hook | **W-12 · W-15** |

---

## C. Ranked blocker list

Composite blocker ranking = `(immediate-break severity) + (legal exposure) + (count of files touched) + (architectural depth)`.

| Rank | Blocker | Why this rank |
|---|---|---|
| 1 | **W-01 No tenant model** | Existential — without it, every other tenant feature is impossible |
| 2 | **W-02 No tenant scoping in routes** | Pair with W-01; without it, data leaks across tenants by default |
| 3 | **W-09 Hardcoded MASCI legal text** | Legal exposure for both parties; affects Spanish AND English |
| 4 | **W-12 No tenant onboarding surface** | Without it, onboarding is a manual ops project per customer |
| 5 | **W-03 497 files reference "MASCI"** | Surface-level brand leak everywhere |
| 6 | **W-08 Hardcoded recipient emails** | Customer #2 emails go to MASCI staff by default |
| 7 | **W-13 Per-workflow status engines hardcoded** | Blocks workflow customization at the architectural level |
| 8 | **W-14 8 auth flows × 0 tenant scope** | Customer #2 logins literally cannot be isolated today |
| 9 | **W-15 Public surfaces single brand chrome** | Public Safety Tile, QR pages, asset lookup, all public references |
| 10 | **V-04 / W-06 `tokens.css` PROPOSAL — not wired** | The retheming layer doesn't exist yet; tenant theming impossible |
| 11 | **W-19 Single i18n / palette / token files — no overlay** | Tenant-specific string/color overrides not possible |
| 12 | **W-20 Email templates Python-coded** | Customer cannot customize emails without engineering |
| 13 | **W-10 PDFs / outage alerts inline-branded** | Every server-generated artifact leaks brand |
| 14 | **W-04 52 files reference `mascigc.com`** | Default routing leaks |
| 15 | **W-11 Excel filenames prefix `MASCI_`** | Office-facing brand leak |

---

## D. Positives (counter-balance for completeness)

These items partially or wholly support white-label readiness today; they are NOT blockers:

- **W-17** Training catalog is admin-editable (`training_guides`, `training_videos`).
- **W-18** Digest cadence is admin-editable (`digest_settings`).
- Selected recipient lists have **env-var override** (Leadership, Shop, Safety) — works platform-wide, can be customised at deploy time per customer (clunky but possible).
- `role_templates` collection exists → some role personalisation plumbing exists.
- `forgedops-logo.png` exists in assets — parent brand mark is ready to ship if a UI layer reads it.

---

## E. Onboarding-impact roll-up

If ForgedOps signs Customer #2 tomorrow:

| Domain | Status |
|---|---|
| Data isolation | ❌ none |
| Brand isolation | ❌ none |
| Email routing isolation | ❌ none (platform-level env override only) |
| PDF / Excel branding | ❌ MASCI-baked |
| Public surface branding | ❌ MASCI-baked |
| Status / verb customisation | ❌ none |
| Workflow / role customisation | ❌ none |
| Notification template control | ❌ none |
| Training catalog control | ✅ partial (admin-editable) |
| Digest cadence control | ✅ partial (admin-editable) |
| Authentication isolation | ❌ none |
| Custom domain / subdomain | ❌ none |
| Legal text isolation | ❌ MASCI-baked (EN + ES) |
| Onboarding UI | ❌ none |

**0 of 12 "must-have for onboarding" dimensions are end-to-end customer-self-service today.**

---

## F. Cross-reference

- Detailed white-label findings: `FORGEDOPS_WHITE_LABEL_READINESS_AUDIT.md` (`W-01 … W-20`).
- Master registry (all 77 findings across all audits): `MASCI_PLATFORM_MASTER_FINDINGS_REGISTRY.md`.
- Tier assignment: `MASCI_PLATFORM_PRIORITY_MATRIX.md`.
- Translation gap by audience bucket: `MASCI_TRANSLATION_REALITY_AUDIT.md`.
- Dispatch Data Integrity findings (`D-01 … D-09`) live in the registry plus Track 13.4A §7 for original context.

---

## G. What this matrix did NOT do
- Did not propose a tenant-model schema.
- Did not propose a branding-config schema.
- Did not propose an onboarding-UI design.
- Did not estimate effort for any blocker.
- Did not order the rank list as a remediation sequence.

All deferred to Track 13.4C+ post-operator-authorization.
