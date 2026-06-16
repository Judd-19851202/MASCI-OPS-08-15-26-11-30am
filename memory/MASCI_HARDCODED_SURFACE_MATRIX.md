# MASCI HARDCODED SURFACE MATRIX

**Phase 2 deliverable. Audit-only.**

Total raw count (case-insensitive, code only — excludes `.pyc`, venv, node_modules):
- **Backend code**: 1,486 hits across ~120 files
- **Frontend code**: 1,530 hits across ~110 files
- **Grand total**: 3,016 references

Not every reference is a leak. Three categories:

## Category A — Operational doctrine (KEEP as-is during white-label)

These references describe MASCI-specific business rules. For Customer #2, the rule still applies in shape but the WORD MASCI is wrong.

| Term | Where | Example | Why "keep semantically, rename per tenant" |
|------|-------|---------|---------------------------------------------|
| `non_masci` flag on field-leadership records | `pdf_render.py:1190` · `pdf_render.py:1201` | distinguishes own-forces crew from subcontractors | Rename to `non_company` and read company name from BrandConfig |
| `masci_crews[]` field on daily reports | `pdf_render.py:327 · 671` | section "04 · MASCI Crews on Site" | Rename field to `company_crews`; section label reads from BrandConfig |
| `MASCI Hauling` section header in PDFs | `pdf_render.py:389 · 755 · 1101` | "MM-001B Section 09d (MASCI Hauling Today)" | Section is "company hauling vs outsourced"; rebrand the noun, keep the structure |

## Category B — Environment & isolation primitives (DO NOT rename)

These are env/DB naming constants. They are CORRECT to be MASCI-named because they identify the MASCI deployment. Customer #2's deployment would have its own constants (`bobs_excavating_preview`, etc.).

| Term | Where | Purpose |
|------|-------|---------|
| `masci_safety` · `masci_safety_preview` | env var values · `db_isolation_failsafe.py:31-32` · `server.py:47-48` | Atlas DB names for THIS customer |
| `masci_preview_user` · `masci_prod_user` | `server.py:45-46` | Atlas usernames |
| `masci-hub` (Sentry service · S3 bucket) | various | tenant-scoped infra identifiers |
| File paths `/masci-mark.png` etc | `pdf_render.py:31 · 32` · `frontend/public/` | physical asset paths; tenant deploy ships its own assets |

**Customer #2 deploy gets its own equivalents** (`bobs_safety_preview`, `bobs_preview_user`, `bobs-mark.png`). NOT a code-level leak.

## Category C — Customer-visible copy (PARAMETERIZE — this is the white-label work)

Estimated ~600-800 of the 3,016 references fall here. Examples below; full list would require per-file audit (out of scope this track).

### Backend
| File | Hits | Surface |
|------|------|---------|
| `server.py` | 162 | FastAPI title (`MASCI Job Site Safety Inspection API`) · error messages (`contact MASCI safety`) · admin-route doctrine comments · seeded user emails |
| `services/maintainx_asset_sync.py` | 67 | tenant naming in MaintainX integration · sync logs |
| `routes/integrations/cleanup.py` | 55 | integration cleanup logs |
| `guidance/content.py` | 54 | onboarding/help text · "MASCI" appears in operator-facing copy |
| `training_pdf.py` | 49 | training PDF headers/footers · "MASCI HUB" branding |
| `guidance/translations_es.py` | 47 | Spanish help text mentioning MASCI |
| `pdf_render.py` | 42 | mix of operational (Cat A) and pure brand strings |
| `routes/integrations/imports_exports.py` | 41 | integration UI copy |
| `email_routing.py` | many | seed routing defaults `safety@mascigc.com` · `jaymn.judd@mascigc.com` · `shopmanager@mascigc.com` — some env-overridable |
| `pm_routing.py:28-29` | many | hardcoded PM email roster (Chris Wright · David Jewett etc.) drives notification routing |
| `safety_users.py:72` | 1 | bootstrap safety user seed `safety@mascigc.com` |
| `ops_manual.py` | 26 | operator's manual text |

### Frontend
| File | Hits | Surface |
|------|------|---------|
| `lib/i18n.js` | 177 | bilingual translation values include "MASCI Safety Hub" → "Centro MASCI" · 172 entries reference MASCI/MASCI Hub |
| `pages/legal/TermsOfService.jsx` | 46 | legal entity name · `mascidocs.com` domain · contact addresses |
| `data/training.js` · `data/training_es.js` | 53 total | training module copy ("All MASCI personnel must…") |
| `pages/legal/PrivacyPolicy.jsx` | 31 | data controller name · contact email |
| `pages/admin/AdminIntegrationCenter.jsx` | 29 | integration UI copy |
| `pages/AdminGuide.jsx` | 23 | admin guide text |
| `pages/NewMeeting.jsx` | 21 | meeting form copy |
| `design-system/PortalShell.jsx` | 19 | shell chrome — "MASCI HUB" page title · breadcrumb |
| `lib/hubBannerTemplates.js` | 18 | OSHA / holiday / leadership banner templates baked with MASCI in English+Spanish copy |
| `components/MasciLogo.jsx` | 18 | the logo component itself — file name + 3 asset constants (`mark` / `wordmark` / `lockup`) |
| `pages/ViewDailyReport.jsx` | 14 | DR view labels |
| `lib/topics/{general, office}.js` | 30+ | help topic copy with MASCI baked in |

## Summary

| Category | Approx count | Action |
|----------|--------------|--------|
| A — Operational doctrine (semantic) | ~200 | Rename field/section names; read entity from BrandConfig |
| B — Environment/isolation (infra) | ~2,000 | Keep as-is (each customer has their own equivalents) |
| C — Customer-visible copy | ~600-800 | Parameterize via BrandConfig.t({key}) · ~3 weeks of careful work |

**Verdict**: The MASCI imprint is dense (every operator-facing surface contains it) but largely structural rather than gratuitous. Parameterizing ~700 strings + swapping ~20 asset files + writing 1 BrandConfig provider is the bulk of the lift.
