# Commercialization Blockers · Phase 10 · Document 5 of 5

**Date:** 2026-05-24
**Purpose:** The honest, ordered list of what would have to be true before this platform can be sold to a second contractor. Not "what would be nice"; **what is structurally required.**

This builds on `PRODUCTIZATION_READINESS_SCORECARD.md` (Phase 8) with concrete, code-grounded findings from Phase 10.

---

## Blocker severity legend

| Severity | Meaning |
|---|---|
| 🛑 **STRUCTURAL** | Cannot deploy a second customer without solving this |
| 🟠 **MAJOR** | Customer would experience MASCI branding/copy as broken; deal-blocking |
| 🟡 **MEDIUM** | Customer would see MASCI naming in places that look unprofessional |
| 🟢 **MINOR** | Customer might notice; not deal-blocking |

---

## 🛑 STRUCTURAL · 1 · Multi-tenant data isolation (THE blocker)

**Finding:** Zero `tenant_id` / `workspace_id` / `organization_id` / `company_id` scaffolding across `backend/server.py` + `backend/routes/`. Every Mongo query implicitly assumes one tenant.

**Why it's structural:** A second customer's data cannot safely share the deployment. There is no row-level tenant filter; cross-tenant data leakage would be instant if tenant B's incidents flowed into the same `incidents` collection as tenant A's.

**Resolution paths:**
- **Path A — per-tenant DB:** One Mongo database per customer. Zero query changes; deployment per customer. Cleanest, but requires per-tenant supervisor / hosting infrastructure.
- **Path B — shared DB with `tenant_id` filter:** Add `tenant_id` to every collection + every query. Higher engineering cost; lower hosting cost.

**Effort:** Path A: ~20-30 days (infrastructure-heavy). Path B: ~40-60 days (touches 200+ files).

**Status:** No code path exists today. **Productization cannot begin without addressing this.**

---

## 🛑 STRUCTURAL · 2 · No tenant resolution layer

**Finding:** There is no concept of "current tenant" in the request context. JWT tokens, session helpers, and route dependencies all assume singularity.

**Why it's structural:** Even if data were isolated, the platform has no way to know which tenant a request belongs to.

**Resolution paths:**
- Subdomain-based (`masci.platform.com` vs `acme.platform.com`)
- Path-based (`/t/masci/...` vs `/t/acme/...`)
- Header-based (`X-Tenant-Id`)
- Most SaaS platforms use subdomain; it's the cleanest UX.

**Effort:** ~5-8 days (middleware + token-claim addition + dev-tool subdomain mapping).

**Depends on:** Resolution of Blocker 1.

---

## 🛑 STRUCTURAL · 3 · JWT signing key is global

**Finding:** `JWT_SECRET` in `backend/.env` is a single global value.

**Why it's structural:** Two customers signing tokens against the same secret means a token forged on one tenant validates on another.

**Resolution:** Per-tenant signing key, rotated per tenant deploy.

**Effort:** ~3-5 days (token issuance + validation update + key rotation flow).

**Depends on:** Resolution of Blocker 2.

---

## 🟠 MAJOR · 4 · ~890 MASCI literal references across code + content

**Finding:** Per `HARDCODED_COMPANY_REFERENCES.md`:
- 473 `@mascigc.com` / `@mascidocs.com` email domain references
- 134 MASCI hits in `i18n.js`
- 108 MASCI hits in `server.py`
- 8 hardcoded `MASCI_HUB_*` Content-Disposition filenames
- 1 FastAPI app title
- 1 HTML `<title>` tag
- 1 `MasciLogo.jsx` component
- ~150 MASCI references in `backend/guidance/`

**Why it's major:** A customer named "Acme Construction" would experience the platform telling them their incident report was "Sent from MASCI Hub." Deal-blocking at first deploy.

**Resolution paths (in order):**

### Phase A · Env-driven brand swap (Tier 1 from `TENANT_CONFIGURATION_CANDIDATES.md`)
~18 new env vars. Sweep ~50 literals across server.py + frontend public/index.html + critical email templates. **4-6 days.**

### Phase B · Per-tenant config doc (Tier 2)
New `tenants` collection + config loader + admin UI for brand fields. **5-7 days.**

### Phase C · Content collection migration (Tier 3)
Move `backend/guidance/content.py` + `tips.py` + `translations_es.py` + `frontend/src/data/training.js` from code into Mongo collections scoped by tenant_id. **8-12 days.**

### Phase D · Per-tenant assets (Tier 4)
`/assets/tenants/{slug}/` bucket + `<TenantLogo>` component swap. **4-6 days.**

### Phase E · Per-tenant legal docs (Tier 5)
Replace per-tenant. **2-3 days.**

**Total Phase A-E effort:** ~25-35 days.

**Status:** Not started. Most of this work is volumetric sweeping, not architectural.

---

## 🟠 MAJOR · 5 · No first-run setup wizard

**Finding:** New tenant onboarding today requires:
- Manual MongoDB database creation
- Manual env var configuration
- Manual seed script execution
- Manual super-admin creation
- Manual brand asset upload (post Phase D above)

**Why it's major:** A SaaS customer expects "sign up → fill out company name → log in." Today it requires an engineer to spend a day.

**Resolution:**
- Self-serve account creation flow.
- First-login wizard: company name → first admin user → optional demo seed data → done.

**Effort:** ~5-7 days.

**Depends on:** Resolution of Blockers 1-4.

---

## 🟠 MAJOR · 6 · No customer-facing support model

**Finding:** Today's support model is:
- Direct contact via `safety@mascigc.com` (the customer's own inbox)
- Direct contact via `jaymn.judd@mascigc.com` (the founder)

**Why it's major:** A commercial customer cannot share an inbox with the platform vendor. Need a separated support channel (e.g., `support@platform.com`) and a ticketing system.

**Resolution:**
- External service (Zendesk / HelpScout / Linear) wired to a support inbox.
- In-platform "Contact Support" widget.
- Per-tenant scoped support diagnostics (logs, recent errors, current convergence score) accessible to support staff.

**Effort:** External service ~3-5 days + per-tenant diagnostics ~5-7 days.

**Depends on:** Resolution of Blockers 1-4.

---

## 🟠 MAJOR · 7 · Per-tenant backup + restore + retention

**Finding:** `backend/backup_verification.py` runs platform-wide. Backup ZIPs are named `MASCI_full_backup_*.zip`. There is no tenant-scoped backup or restore.

**Why it's major:** A commercial customer needs a defensible backup retention policy + the ability to restore from a per-tenant backup. Platform-wide backup hands one customer's data to another in a restore operation.

**Resolution:**
- Per-tenant backup ZIPs (per Mongo DB if Path A; or scoped export queries if Path B).
- Per-tenant retention policy.
- Per-tenant restore flow.

**Effort:** ~4-5 days (Path A; trivial because each tenant has own DB) or ~7-9 days (Path B; complex export logic).

**Depends on:** Resolution of Blocker 1.

---

## 🟡 MEDIUM · 8 · FMCSA-specific DQ file workflow

**Finding:** The DQ file workflow (`routes/hr_portal/driver_qualification.py`) is hardcoded for FMCSA regulations (US Department of Transportation rules).

**Why it's medium:** A non-trucking contractor (e.g., commercial finish carpentry) doesn't need DQ files. An international contractor needs different regulations entirely.

**Resolution paths:**
- **Path 1 — feature flag:** Add `feature_flags.fmcsa_dq_files: true/false` per tenant; hide the surface entirely if disabled.
- **Path 2 — pluggable compliance:** More ambitious; the platform supports multiple compliance modules. Out of scope for early productization.

**Effort:** Path 1 ~2 days. Path 2 ~30+ days.

**Recommendation:** Path 1 for first commercial deploy. Path 2 only if a non-trucking deal materializes.

---

## 🟡 MEDIUM · 9 · Bilingual hardcoded to EN+ES

**Finding:** `i18n.js` and translations are EN + ES only. Adding French / Portuguese / etc. would touch every translation key.

**Why it's medium:** Limits the platform to North American customers (and even some of those expect French Canadian).

**Resolution:** Move translation dictionary to a per-locale Mongo collection; admin UI for translation management.

**Effort:** ~8-12 days.

**Recommendation:** Defer until a non-EN/ES customer signs.

---

## 🟡 MEDIUM · 10 · No tenant-scoped audit logs surface

**Finding:** Audit trails exist on every record (`created_by_name`, `updated_by_name`, etc.), but there is no consolidated tenant-scoped audit log surface for compliance reviews.

**Why it's medium:** Some commercial customers require SOC2-style audit log export.

**Resolution:** New endpoint `GET /api/admin/audit-log?from=...&to=...` returning a unified change log across collections, paged and CSV-exportable.

**Effort:** ~3-5 days.

---

## 🟢 MINOR · 11 · No platform-level status page

**Finding:** No public-facing status page at `status.platform.com`.

**Why it's minor:** Operational nicety; not deal-blocking.

**Resolution:** External service (Statuspage.io / Better Uptime / Atlassian Statuspage) + webhook integration.

**Effort:** ~1-2 days (external service config).

---

## 🟢 MINOR · 12 · No per-tenant DNS / TLS automation

**Finding:** Today the platform is served on `safety-audit-mobile-1.preview.emergentagent.com` (preview hosting). For commercial deploy, each tenant needs a subdomain + TLS cert.

**Why it's minor:** Standard SaaS plumbing (Let's Encrypt + Caddy / Cloudflare).

**Effort:** ~3-5 days (DNS + TLS automation for new tenant onboarding).

---

## 🟢 MINOR · 13 · No metered billing / subscription management

**Finding:** Zero billing scaffolding.

**Why it's minor:** Can be deferred; first customers can be billed manually / via Stripe Checkout one-off.

**Effort:** ~15-30 days for full metered billing; ~3-5 days for Stripe Checkout single-payment.

---

## Total commercialization effort (ordered)

| Order | Blocker | Severity | Effort | Cumulative |
|---|---|---|---|---|
| 1 | Multi-tenant data isolation | 🛑 STRUCTURAL | 20-30d (Path A) | 25d |
| 2 | Tenant resolution layer | 🛑 STRUCTURAL | 5-8d | 33d |
| 3 | Per-tenant JWT signing key | 🛑 STRUCTURAL | 3-5d | 38d |
| 4 | MASCI literal sweep (Phase A-E) | 🟠 MAJOR | 25-35d | 68d |
| 5 | First-run setup wizard | 🟠 MAJOR | 5-7d | 74d |
| 6 | Support model | 🟠 MAJOR | 8-12d | 84d |
| 7 | Per-tenant backup + restore | 🟠 MAJOR | 4-5d (Path A) | 89d |
| 8 | FMCSA feature flag | 🟡 MEDIUM | 2d | 91d |
| 9 | Bilingual scaling | 🟡 MEDIUM | 8-12d (deferred) | — |
| 10 | Tenant-scoped audit logs | 🟡 MEDIUM | 3-5d | 96d |
| 11 | Status page | 🟢 MINOR | 1-2d | 97d |
| 12 | DNS / TLS automation | 🟢 MINOR | 3-5d | 102d |
| 13 | Billing | 🟢 MINOR | 3-5d (basic) | 107d |

**Minimum-viable productization: ~90-100 engineer-days** to reach a state where a second customer can deploy and use the platform without confusion.

**That is the honest answer.** It is large but bounded.

---

## What the platform should NOT do during productization

Per `DO_NOT_BUILD_YET.md` and `FINAL_RESTRAINT_RECOMMENDATIONS.md`, the productization sprint must resist:
- ❌ Adding features (productization is plumbing, not features).
- ❌ Redesigning the UI.
- ❌ Changing lifecycle logic.
- ❌ Adding AI gimmicks.
- ❌ Restructuring the RBAC matrix.
- ❌ Adding analytics.
- ❌ Adding new portals.

Productization is purely the act of separating platform from tenant. Nothing else.

---

## Recommended strategic sequence

If the operator decides to pursue commercial scaling:

1. **Validate first commercial deal exists** before starting work. Productization is too expensive to pursue speculatively.
2. **Choose Path A vs Path B for multi-tenancy.** Path A (per-tenant DB) is recommended for first 5-10 customers; switch to Path B when hosting cost becomes meaningful.
3. **Sweep MASCI layer in parallel with multi-tenancy work.** The two are independent and can run on separate tracks.
4. **Ship to second customer in beta** before formal commercial launch. Use that customer's friction to inform the setup wizard.
5. **Resist scope creep** during productization. Every "wouldn't it be great if…" adds 5x time to commercial launch.

---

## Bottom line

**Commercialization is possible. It is not cheap.**

The platform's intellectual property (operational discipline, lifecycle continuity, governance findings, signal hygiene) is well-preserved in product core (`PRODUCT_CORE_BOUNDARY_MAP.md`). The MASCI layer is well-bounded (`MASCI_LAYER_AUDIT.md`). The configuration candidates are stratifiable (`TENANT_CONFIGURATION_CANDIDATES.md`).

The structural blockers (multi-tenancy, tenant resolution, JWT) are real and require ~38 engineer-days of focused work. The MASCI sweep is another ~25-35 days. Setup wizard + support + backup add another ~17-24 days. Total realistic minimum: **~90-100 days.**

That assessment matches the Phase 8 productization scorecard (2.8/5.0). Phase 10 narrows it to specific, gradable blockers.

The operator now has the data to make the strategic decision: pursue commercial scaling, or remain best-in-class for MASCI?

Either answer is honorable. This document removes ambiguity from the choice.
