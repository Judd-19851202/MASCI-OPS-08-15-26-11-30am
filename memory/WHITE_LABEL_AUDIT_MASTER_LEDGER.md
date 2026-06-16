# WHITE-LABEL AUDIT · MASTER LEDGER

**Date:** 2026-02-16 (fork session)
**Track:** 16.0 — WHITE-LABEL / MULTI-TENANT READINESS AUDIT (audit-first · no code changes)
**Status:** 🔴 **NOT WHITE-LABEL READY** (customer-clone-with-rebrand-work-ready only)

---

## Honest Score

| Readiness tier | Status | Why |
|----------------|--------|-----|
| Not white-label ready | ❌ no — it IS partially configurable | env-based isolation primitives exist |
| **Partially white-label ready** | 🟡 **THIS IS WHERE WE ARE** | env vars work; brand strings are baked in copy/PDFs/i18n |
| Customer #2 manually clone-ready | 🟡 with 2-3 weeks of rebrand work | feasible but rebrand cost is high (3,000+ touchpoints to evaluate) |
| Config-driven single-tenant ready | ❌ no | no central branding/config object exists |
| Multi-tenant SaaS ready | ❌ no | no tenant model · no row-level isolation · no per-customer DB router |

**Verdict**: The platform is a single-tenant MASCI-specific deployment with strong env-based environment isolation (preview/production). It is **NOT** ready to host a second customer in the same database OR to be cloned as-is without rebrand work.

## Five Pillars

| Pillar | Score | Justification |
|--------|-------|---------------|
| POWERFUL | 8.0 | Full operational depth (RC1 GO) but locked to one customer. |
| SIMPLE | 5.0 | Customer #2 onboarding today = manual fork + global search-and-replace + Atlas/R2/DNS provisioning · NOT one-click. |
| BEAUTIFUL | 4.0 | Branding is baked into copy strings, holiday banners, OSHA banners, leadership templates, legal docs, PDF headers, email signatures. Customer #2 chrome would feel like MASCI's chrome with their logo on top. |
| TRUSTED | 9.0 | Excellent environment isolation (RC1 addendum proved DB-level credential separation). What's trusted is the boundary BETWEEN environments — what's NOT yet trusted is the boundary BETWEEN customers. |
| PROVEN | 9.0 | Every claim in this audit is backed by `grep -rn` counts and code samples. |

**Composite: 7.0** — but this is a DIFFERENT scale from RC1 readiness. Composite for RC1 (single MASCI deploy) remains 9.78.

## Reference matrices (delivered alongside this ledger)

1. `MASCI_HARDCODED_SURFACE_MATRIX.md` — every MASCI/Massey/mascigc.com touchpoint categorized
2. `WHITE_LABEL_CONFIGURABILITY_MATRIX.md` — what's already env-driven vs hardcoded
3. `WHITE_LABEL_DATA_ISOLATION_MATRIX.md` — DB · auth · storage · audit · email isolation by surface
4. `WHITE_LABEL_BRANDING_MATRIX.md` — every visible brand surface
5. `WHITE_LABEL_EMAIL_MATRIX.md` — every email template / sender / footer
6. `WHITE_LABEL_PDF_REPORT_MATRIX.md` — every PDF / export with brand wiring
7. `WHITE_LABEL_INTEGRATION_MATRIX.md` — Motive / FleetWatcher / MaintainX / Resend / Sentry / R2 / Atlas
8. `CUSTOMER_ONBOARDING_REQUIREMENTS.md` — what Customer #2 onboarding must collect
9. `CUSTOMER_2_ROADMAP.md` — Phase 0-8 plan
10. `WHITE_LABEL_RISK_REGISTER.md` — risks · severity · likelihood · mitigation
11. `WHITE_LABEL_EFFORT_ESTIMATE.md` — Model 1 / 2 / 3 effort + cost

## Executive Summary — answers to the 12 required questions

1. **How white-label ready today?** 🟡 Partially. Strong env isolation; weak brand isolation.
2. **Can Customer #2 be onboarded tomorrow?** ❌ No. Minimum 2-3 weeks of rebrand work + provisioning.
3. **If not, why not?**
   - No central brand config object · no per-customer DB router · no per-customer email sender registry · no tenant-aware audit log
   - 3,016 MASCI/Massey references in code (1,486 backend + 1,530 frontend), of which ~600-800 are customer-visible strings that would need parameterization
   - Logo/favicon assets at fixed paths (`/masci-mark.png`, `/masci-wordmark.png`, `/masci-full-lockup.png`)
   - Email senders default to `@mascigc.com` (some env-overridable, many hardcoded)
   - Privacy policy + Terms of Service hardcode "MASCI General Contracting" and `mascidocs.com`
   - Holiday/OSHA/leadership banner templates have MASCI baked into operational copy
   - PDF render uses "MASCI Hauling" / "MASCI Crews" as semantic section headers
4. **What would break for Customer #2?**
   - Emails would arrive from `@mascigc.com`
   - PDFs would have MASCI logo + "MASCI Hauling" headers
   - Legal docs would name MASCI as data controller
   - Login screen would say "MASCI HUB"
   - i18n strings would render "Centro MASCI" / "MASCI Safety Hub"
   - Hardcoded employee names (`pm_routing.py`: Chris Wright, David Jewett) drive notification routing
5. **What MASCI leaks exist?** Backend: 1,486 references (top files: server.py · maintainx_asset_sync · integrations/cleanup · guidance/content · training_pdf · pdf_render). Frontend: 1,530 references (top: i18n.js · TermsOfService · training · PrivacyPolicy · AdminIntegrationCenter · AdminGuide · NewMeeting · MasciLogo).
6. **What needs to become configurable?** Single source of truth `BrandConfig` object resolved per-request (or per-deploy for clone model) containing: company_name · platform_name · logos · favicons · color palette · domain · email_sender · support_contact · legal_entity · physical_address · phone · timezone · default_language · enabled_modules.
7. **Safest Customer #2 model?** **Model 2 — Config-driven single-tenant clone** (separate deployment per customer, single brand config object drives everything). One database per customer (strong isolation, simple).
8. **Fastest Customer #2 model?** **Model 1 — Manual clone deploy** (fork repo, find-replace MASCI strings, deploy, separate Atlas DB). Fast but technical-debt-heavy and not repeatable.
9. **Best long-term SaaS model?** **Model 3 — True multi-tenant SaaS** with tenant_id row-level scoping + per-tenant brand config in DB + tenant-aware audit/notifications. 8-12 weeks of work; only worth it if 5+ customers.
10. **Recommended roadmap?** See `CUSTOMER_2_ROADMAP.md` — 8-phase plan starting with no-leak cleanup and a centralized BrandConfig provider.
11. **Expected effort?** See `WHITE_LABEL_EFFORT_ESTIMATE.md` — Model 1 (~1 week + ongoing maintenance), Model 2 (~3 weeks for Customer #2, then ~3 days/new customer), Model 3 (~10 weeks).
12. **What must NOT be touched before RC1 production is stable?** Authentication · permission gates · database isolation failsafe · `_verify_env_db_alignment` · audit log writes · existing MASCI users/projects/equipment data. Hard rules enforced throughout this audit — zero code changes during this track.

## Recommendation

🟡 **Path forward**: After RC1 production stabilizes (≥ 1 week of clean uptime), open a "Track 17 — White-Label Phase 1: No-Leak Cleanup" track. That track ONLY centralizes the BrandConfig provider and migrates the top 200 customer-visible strings to read from it. No tenant model, no architecture changes. Once Phase 1 ships safely, decide Model 2 vs Model 3 based on actual customer pipeline.

**🔴 DO NOT begin white-label conversion work this week.** RC1 just deployed. Let it stabilize before touching anything customer-visible.
