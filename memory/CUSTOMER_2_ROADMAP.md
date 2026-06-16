# CUSTOMER #2 ROADMAP

**Phase 15 deliverable.** 8-phase plan from RC1 stable → repeatable customer onboarding.

## Phase 0 — Audit complete ✅
**Status**: DONE. This track produced 12 deliverables documenting the gap.

## Phase 1 — No-MASCI-Leak Cleanup (Track 17 candidate)
**Goal**: Centralize the 200 most customer-visible MASCI strings into a single source of truth so the rebrand becomes diff-able instead of grep-able.
**Scope**: ~2 weeks
**Work**:
- Build `BrandConfig` provider (backend: `brand_config.py` reading from env + DB; frontend: `lib/brand.js` reading from `/api/brand` once on app load).
- Migrate top-20 surfaces: login title · sidebar header · email subject prefix · email footer · PDF header logo path · PDF watermark path · PDF cover company name · favicon · primary color · OSHA banner template · holiday banner template · TermsOfService entity · PrivacyPolicy entity · support contact · legal address · phone · MasciLogo component → `BrandLogo` component · pdf_render `LOGO_PATH`/`WATERMARK_PATH` → BrandConfig · email_routing fallback recipients → all env-driven.
- Keep MASCI behavior 100% backward compatible (BrandConfig defaults to MASCI in MASCI's deploy).
- 0 customer-facing changes for MASCI production.
- Regression: existing 393 tests + new BrandConfig contract tests.

**Risk**: Low. Defaults preserved. RC1 unaffected.
**Output**: Top-20 surfaces are now env-configurable for Customer #2.

## Phase 2 — Customer Config Object
**Goal**: A single `BrandConfig` schema + per-deploy env file that drives every visible surface.
**Scope**: ~1 week
**Work**:
- Define `BrandConfig` schema (pydantic model): `company_name`, `platform_name`, `logos` (3 variants), `favicon_url`, `primary_color`, `secondary_color`, `accent_color`, `domain`, `email` (sender, reply_to, footer_html, subject_prefix), `support` (email, phone), `legal` (entity, address, jurisdiction), `tz`, `default_lang`, `modules_enabled` (list).
- Wire `BrandConfig.load()` to env + optional DB override.
- Document the env-var contract.
- `BrandConfig` defaults for MASCI (so MASCI doesn't have to set every env var).

**Risk**: Low.
**Output**: `BrandConfig` is the source of truth.

## Phase 3 — Branding Provider (frontend + backend)
**Goal**: Every component reads brand from `BrandConfig`, not from hardcoded strings.
**Scope**: ~2 weeks
**Work**:
- Backend: refactor every email/pdf helper to take `brand: BrandConfig` arg.
- Frontend: `BrandProvider` React context wrapping the app.
- Migrate i18n keys: `"MASCI Safety Hub"` → `t("brand.platform_name")` reading from BrandConfig.
- Migrate hub banner templates: `"MASCI"` → `{{brand.company_name}}`.
- Migrate legal pages to BrandConfig-driven content.

**Risk**: Medium. Touches every portal. Heavy testing.
**Output**: ~80% of brand surfaces parameterized.

## Phase 4 — Email / PDF Templates
**Goal**: Email + PDF outputs are 100% brand-clean.
**Scope**: ~1 week
**Work**:
- Email helpers: subject prefix, sender, footer, logo all from BrandConfig.
- PDF helpers: logo path, watermark, header, footer, section labels from BrandConfig.
- Field renames: `masci_crews` → `company_crews`, `non_masci` → `non_company` (with migration script + backward-compat read).
- Regression: render a sample PDF for "MASCI" deploy and verify it matches baseline.

**Risk**: Medium. Field renames touch persisted data.
**Output**: Customer #2 PDFs and emails would be on-brand if BrandConfig swapped.

## Phase 5 — Deployment / Onboarding Checklist
**Goal**: Repeatable Customer #2 onboarding runbook.
**Scope**: ~1 week
**Work**:
- Document `CUSTOMER_ONBOARDING_RUNBOOK.md` (extends Phase 11 doc) — checklist of provisioning steps in order.
- Build `seed_customer.py` script — given a customer slug + admin email, seeds initial admin, employee master CSV, project CSV, equipment CSV.
- Build automation for Atlas DB provisioning + R2 bucket + Resend domain setup.
- Pilot with a "dry-run" customer: deploy a "Demo Customer" pod with fictional brand to validate the end-to-end flow.

**Risk**: Low.
**Output**: 4-day onboarding capability proven via dry-run.

## Phase 6 — Customer #2 Pilot
**Goal**: First real customer onboarded.
**Scope**: ~1 week including hand-holding
**Work**:
- Pick a friendly first customer (Bob's Excavating type — smaller, willing to be a pilot).
- Provision infra + brand config + assets.
- Run CSV imports.
- 1-week pilot with daily check-ins.

**Risk**: Medium (first real external user).
**Output**: Customer #2 live. Lessons learned doc.

## Phase 7 — Repeatable Onboarding Package
**Goal**: Onboard Customer #3 onwards with no MASCI-side custom work.
**Scope**: ~2 weeks
**Work**:
- Take lessons from Pilot, harden the runbook.
- Build a self-serve onboarding portal (admin uploads logos, picks colors, fills CSVs → auto-provisions).
- Pricing/billing decision (out of scope of this roadmap).

**Risk**: Low.
**Output**: Onboarding is a product feature, not a service.

## Phase 8 — True SaaS / Multi-Tenant Decision
**Goal**: Decide whether to consolidate per-customer deploys into a multi-tenant SaaS.
**Scope**: TBD based on customer count
**Trigger**: 10+ customers OR per-customer cloud cost exceeds revenue.
**Work** (if green-lit):
- Migrate to shared-app + per-tenant DB (Model B) first.
- Eventually shared-DB with `tenant_id` (Model C) only if customer count > 50.
- 8-12 weeks of focused architecture work.

**Risk**: HIGH. Don't do this until forced.

## Roadmap timeline

- Phase 1 → ~2 weeks (Track 17)
- Phases 2-4 → ~4 weeks (Track 18-20)
- Phase 5 → ~1 week
- Phase 6 → 1 week (real customer)
- Phase 7 → ~2 weeks
- **Total time to repeatable Customer #N**: ~10 weeks of engineering
- **Customer #2 alone via clone-rebrand without Phase 1-4**: ~3 weeks of one-off heroics (NOT recommended — creates two divergent codebases to maintain)

## What NOT to touch before RC1 stable

- Authentication / permission gates
- Database isolation failsafe + `_verify_env_db_alignment`
- Audit log writes
- Existing MASCI users / projects / equipment data
- The 393 production tests
- The `_PREVIEW_DB` / `_PROD_DB` constants in server.py

Track 17 may start the moment RC1 has 7+ days of clean production uptime.
