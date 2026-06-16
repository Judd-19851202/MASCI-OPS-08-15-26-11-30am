# WHITE-LABEL RISK REGISTER

**Phase 16 deliverable.** Risks of Customer #2 onboarding before / during / after the white-label work.

## Risk scale
- **Severity**: 1 (cosmetic) → 5 (catastrophic, data leak or regulatory event)
- **Likelihood**: 1 (very unlikely) → 5 (near-certain without mitigation)
- **Score** = severity × likelihood (1-25)

## Risk register

### R-1 — Customer data leak across tenants (Score 25)
**Severity 5 · Likelihood 5 if shared-DB · Likelihood 1 if per-customer-DB**
- One customer reads or modifies another customer's data via missing `tenant_id` scope.
- **Mitigation**: Use Model A (one deploy per customer) until ≥10 customers. Each customer gets own Atlas DB with credential-scoped isolation — same pattern RC1 already proves.

### R-2 — MASCI branding leak into Customer #2 PDFs / emails (Score 16)
**Severity 4 · Likelihood 4 if rushed clone**
- Customer #2's daily report PDF shows MASCI logo or "MASCI Hauling" section title.
- **Mitigation**: Phase 4 (Email/PDF templates) must complete BEFORE first external customer deploy. Skip-this risk = customer churn within first week.

### R-3 — Wrong email links / wrong domain in password reset (Score 20)
**Severity 5 · Likelihood 4 if not parameterized**
- Customer #2 user clicks password reset, lands at `mascidocs.com` login screen.
- **Mitigation**: Email body URLs must read `REACT_APP_BACKEND_URL` / `PUBLIC_BASE_URL` from BrandConfig. Verified in Phase 4.

### R-4 — Wrong PDF logo / cover page (Score 12)
**Severity 4 · Likelihood 3 if asset path hardcoded**
- Customer #2 PDFs reference `/masci-mark.png` because `pdf_render.py:31-32` ship hardcoded.
- **Mitigation**: BrandConfig drives `LOGO_PATH` / `WATERMARK_PATH`. Per-customer asset files in `frontend/public/`. Phase 4.

### R-5 — Wrong R2 storage prefix → backup collision (Score 12)
**Severity 4 · Likelihood 3 if shared bucket**
- Customer #2 backup file overwrites MASCI backup with same name (filename includes `db_name` so partial mitigation already exists).
- **Mitigation**: Per-customer R2 bucket recommended. If shared, enforce `{customer_slug}/...` key prefix everywhere.

### R-6 — Resend account contamination (Score 16)
**Severity 4 · Likelihood 4 if shared Resend account**
- Customer #2 hits MASCI's Resend rate limit OR Customer #2 sender domain reputation affects MASCI.
- **Mitigation**: Each customer gets OWN Resend account with their own verified domain. Per-customer `RESEND_API_KEY` env var.

### R-7 — Hardcoded PM roster fallback fires for wrong customer (Score 9)
**Severity 3 · Likelihood 3**
- `pm_routing.py:28-29` Chris Wright / David Jewett dict serves as fallback if DB empty. Customer #2 with empty PM dict could route notifications to MASCI PMs.
- **Mitigation**: Remove `pm_routing.py` fallback dict OR guard it behind `if BrandConfig.company_slug == "masci"`. Phase 1.

### R-8 — i18n bundle pollution (Score 6)
**Severity 2 · Likelihood 3**
- Customer #2 user toggles Spanish and sees "Centro MASCI" because the translation value hardcodes MASCI.
- **Mitigation**: Phase 3 — migrate i18n VALUES to interpolated templates with BrandConfig.company_name.

### R-9 — Legal page brand confusion (Score 10)
**Severity 5 · Likelihood 2**
- Customer #2's TermsOfService still names MASCI General Contracting as data controller — opens regulatory/legal exposure.
- **Mitigation**: Per-customer legal page content driven by BrandConfig.legal.* (entity, address, jurisdiction). Phase 3.

### R-10 — Support burden — divergent codebases (Score 16)
**Severity 4 · Likelihood 4 in Model 1 clone-and-rebrand**
- Each cloned customer codebase drifts from the source over time. Bug fixes don't propagate.
- **Mitigation**: Skip Model 1 — go straight to Model 2 (config-driven) so a single codebase serves all customers. Defer until Phase 2-4 complete.

### R-11 — Deployment complexity creep (Score 9)
**Severity 3 · Likelihood 3**
- Per-customer infra (Atlas + R2 + Resend + Sentry + domain + DNS) is 5 separate provisioning steps. Without automation, onboarding consumes engineer time linearly.
- **Mitigation**: Phase 5 — build `seed_customer.py` automation. Long-term Phase 7 — self-serve onboarding portal.

### R-12 — Audit log mixing in shared DB (Score 20)
**Severity 5 · Likelihood 4 if shared DB chosen**
- A regulator subpoena for Customer A's audit log returns Customer B's records too.
- **Mitigation**: Per-customer DB (Model A) — same isolation guarantee as preview/prod separation. **Strong recommendation: never run a customer audit log in a shared collection.**

### R-13 — MaintainX tag mapping mismatch (Score 6)
**Severity 2 · Likelihood 3**
- `services/maintainx_asset_sync.py` has hardcoded MASCI tag prefixes and location names. Customer #2's MaintainX has different tags.
- **Mitigation**: Per-customer mapping file (clone-rebrand) OR per-customer mapping config in BrandConfig. Phase 4-5.

### R-14 — RC1 production destabilization from white-label work (Score 20)
**Severity 5 · Likelihood 4 if rushed**
- Phase 1-4 work runs against a production system. Risk of breaking MASCI's daily operations.
- **Mitigation**: 
  - DO NOT begin Phase 1 until RC1 has 7+ days of clean production uptime.
  - Run all Phase 1-4 work in preview first; require 64+ existing regression tests + new BrandConfig contract tests green before merge.
  - Defaults preserve MASCI behavior 100%; no MASCI-visible changes.

### R-15 — Underestimate of customer-visible string count (Score 12)
**Severity 3 · Likelihood 4**
- "It's just 200 strings" — but discovery reveals 600-800 once Phase 1 starts.
- **Mitigation**: Phase 1 effort estimate already includes a 2-week buffer. If discovery exceeds, extend Phase 3 not Phase 1.

## Risk summary

- **High-score risks (≥16)**: R-1, R-3, R-6, R-10, R-12, R-14 — six items.
- **Common mitigation**: Choose Model A (per-customer deploy + per-customer DB) and complete Phase 1-4 BEFORE any external customer.
- **Single biggest risk to avoid**: starting white-label work BEFORE RC1 is stable in production.

## Recommendation

Do not green-light Customer #2 onboarding until:
- ✅ RC1 has 7+ days clean production uptime
- ✅ Phase 1-4 complete (BrandConfig wired through email + PDF + i18n + legal pages)
- ✅ Phase 5 dry-run customer (fictional brand) deployed and tested
- ✅ All 12 risks above have a documented mitigation enabled (not just planned)
