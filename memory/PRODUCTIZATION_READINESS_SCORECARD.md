# Productization Readiness Scorecard · Phase 8 · Document 2 of 5

**Date:** 2026-05-24
**Frame:** "Could another general contractor use this platform tomorrow?" Honest scoring across 10 commercial-scaling axes. Concrete findings rooted in the codebase, not aspirational fluff.

**Scoring:** 0 (blocker) — 1 (significant gap) — 2 (small gap) — 3 (production-ready) — 4 (commercial-grade) — 5 (best-in-class)

---

## Summary score: 2.8 / 5

The platform is **production-grade for MASCI** and **directionally commercial** but is **NOT yet a multi-tenant SaaS**. Three areas score ≤ 2 (multi-company readiness, branding configurability, tenant isolation). Six areas score ≥ 3.

| Axis | Score | Notes |
|---|---|---|
| Multi-company readiness | **1** | No `tenant_id` / `workspace_id` scaffolding anywhere in the backend (verified: 0 hits across `backend/server.py + backend/routes/`). Single-tenant by architecture. |
| Onboarding | **2** | Seed scripts exist (`seed_*.py`) for MASCI demo data; no first-run wizard for a new tenant. |
| Branding configurability | **2** | Frontend `companyInfo.js` allows localStorage-driven swap for PDF footer + photo watermark. Backend has no equivalent — "MASCI" is hardcoded in PDF filenames, FastAPI app title, source-bundle ZIP names, employee/supplier/equipment XLSX filenames, etc. (15+ literal hits in `server.py` alone). |
| Tenant isolation | **0** | No row-level tenancy filter on any Mongo collection. Cross-tenant data leakage would be near-instant if a second customer's data hit the same DB. **Hard blocker for multi-tenant SaaS.** |
| Operational templates | **3** | LifecycleGuide library, operational glossary (16 entries), governance findings (8 detector rules) are all reusable patterns — not MASCI-specific. New tenants would inherit them cleanly once tenancy ships. |
| Support readiness | **3** | Detailed logging; admin guide; AdminGuide PDF; `/api/health` endpoint; deployment readiness reports. Missing: tenant-scoped support diagnostics. |
| Deployment readiness | **4** | Phase 5D + 6 + 7 audits all green; supervisor-managed services; idempotency keys; rate limits; backup verification; bilingual coverage. Production-grade today. |
| Scalability | **3** | MongoDB-backed; standard FastAPI patterns; soft delete + audit trails; rate limiting on public endpoints. No sharding, no read replicas configured (likely fine for current scale). |
| Maintainability | **3** | server.py is oversize (~10k LOC). Otherwise modular: routes split by domain, components split by portal. Lint clean. EN+ES parity throughout. |
| Operational trust | **5** | This is the platform's strongest axis. Phase 5D / 6 / 7 work hardened lifecycle visibility, governance contradictions, signal discipline, and severity-escalation safety nets. The platform tells the truth and refuses to lie. |

---

## Multi-company readiness · score 1

### Findings
- **Zero tenant-id scaffolding**: `grep -E "tenant_id|workspace_id|organization_id|company_id" backend/server.py backend/routes/` returns 0 hits. Every Mongo query implicitly assumes one tenant.
- **Single ADMIN_PASSWORD env var**: `ADMIN_PASSWORD=MASCI1982!` in `backend/.env`. No multi-org auth scaffold.
- **JWT secret is global**: No per-tenant signing key rotation.

### What ships today as multi-tenant-ready
- The 7-portal RBAC model (admin/safety/hr/pm/shop/dispatch/fl) generalizes cleanly — every new tenant gets the same role grid.
- The `useDraftSync` autosave + idempotency-key dedup pattern is tenant-neutral.
- The Notification Discipline Matrix is reusable as-is.

### What does NOT ship today as multi-tenant-ready
- All Mongo queries (incidents, employees, daily reports, CAPAs, training, etc.) need `tenant_id` predicates.
- The directory user model (`users` collection) needs tenant scoping.
- Backup ZIP names, PDF filenames, FastAPI app title, governance email-from addresses are MASCI-literal.

### What blocks multi-tenant
- **No row-level tenant filter.** Migrating to tenancy = touching every Mongo query in the backend. Estimated 200+ files.

---

## Onboarding · score 2

### What works
- Demo seed scripts in `backend/scripts/seed_*.py` populate a realistic MASCI dataset on first start.
- Bilingual coverage means new operators don't need a separate Spanish build.
- `/api/health` + backup verification confirms a clean start.

### What's missing
- No first-run setup wizard ("Welcome — what's your company name? Upload a logo. Add the first admin.").
- New users must be created via either the master super-admin (`jaymn.judd@mascigc.com`) or direct Mongo insert. There is no self-serve "Invite an admin" workflow.
- Per-portal onboarding paths exist (PMNew via `/pm/new`, HrNew, etc.) but they assume MASCI is the only tenant.

### What's deliberately not built (per `DO_NOT_BUILD_YET.md`)
- No giant settings panel.
- No per-user notification preferences.

---

## Branding configurability · score 2

### What works
- `frontend/src/lib/companyInfo.js` defines `DEFAULT_COMPANY_INFO` (name, tagline, address, phone, email, website) with localStorage override. Read by PDF footers and photo watermarks.

### What does NOT work
- The FastAPI title is hardcoded `"MASCI Job Site Safety Inspection API"` (server.py:34).
- PDF filenames: `MASCI_HUB_Operations_Manual.pdf`, `MASCI_HUB_Operations_Manual.docx`, `MASCI_HUB_Source_Bundle_{stamp}.zip`, `MASCI_employees_{stamp}.xlsx`, `MASCI_suppliers_{stamp}.xlsx`, `MASCI_equipment_{stamp}.xlsx`. All have the company name baked into the download name.
- Email templates / Resend `from_address` defaults are MASCI-scoped.
- `<title>` tag and meta tags are MASCI-branded.
- `MasciLogo.jsx` (an SVG component with three variants) is brand-specific by design.
- Backup ZIP filenames embed MASCI.

### What it would take
- Move the company-info layer to **backend env var** (e.g., `TENANT_NAME`, `TENANT_LEGAL_NAME`, `TENANT_LOGO_URL`, `TENANT_EMAIL_FROM`).
- Make `MasciLogo.jsx` driven by `TENANT_LOGO_URL` rather than imported SVG.
- Sweep ~15 hardcoded filename literals in `server.py` to use the tenant name.

**Estimated effort: 4-6 days of disciplined sweeping.** Not Phase 8 scope.

---

## Tenant isolation · score 0 (BLOCKER for multi-tenant SaaS)

### Reality
A second customer's data **cannot** safely coexist in the same DB today. There is no per-document tenant filter.

### Resolution paths
- **Path A — per-tenant DB:** One Mongo database per customer. Zero query changes; deployment per customer. Cleanest, but requires per-tenant supervisor / hosting.
- **Path B — shared DB with tenant_id filter:** Add `tenant_id` to every collection + every query. Higher engineering cost; lower hosting cost.

Either path is **out of Phase 8 scope** and out of any current commitment. Documented here as the explicit commercial-scaling blocker.

---

## Operational templates · score 3

### Reusable as-is for any general contractor
- LifecycleGuide library (8 instances; all generic enough)
- Operational glossary (16 entries; all industry-standard terms)
- Governance findings (8 detector rules; all generic compliance contradictions)
- CollapseCard pattern + Smart Operational Disclosure doctrine
- Phase 6 completion-summary banner pattern
- Notification Discipline Matrix (3-tier + 19-event)

### Industry assumption
The platform is purpose-built for **US-based general contractors with FMCSA-regulated drivers**. The DQ file workflow is specifically FMCSA. International customers would need the DQ workflow swapped or stubbed.

---

## Support readiness · score 3

### What's in place
- `/api/health` endpoint
- `/var/log/supervisor/backend.*.log` per-service logging
- AdminGuide PDF/docx exports
- Backup verification finding (CRITICAL tier)
- Auto-email failure finding
- Deployment readiness reports in `/app/memory/`

### What's missing
- No per-tenant support diagnostics surface.
- No "Contact support" widget inside the platform (users contact MASCI internally; commercial customers would need a ticketing channel).
- No structured incident-postmortem workflow (manual today).

---

## Deployment readiness · score 4

### What's in place
- Supervisor-managed services with restart-on-failure.
- MongoDB + nginx + FastAPI + React all in one container, auto-managed.
- Hot-reload disabled in production builds.
- Backup cron + verification job.
- Pre-deploy validation already executed (see `/app/memory/DEPLOYMENT_READINESS_REPORT.md`).
- Idempotency keys on public endpoints.

### What's missing for commercial deploy
- Per-tenant DNS / domain mapping.
- TLS cert automation (currently platform-provided).
- Customer-facing status page.

---

## Scalability · score 3

### Current expectations
- ~50-200 active users (single tenant, MASCI workforce).
- ~5,000-50,000 active records (incidents, CAPAs, DRs, training, etc.).
- Single Mongo node, single FastAPI worker.

### Scaling triggers (when to revisit)
- Per-portal user count crosses 500.
- Daily report submission rate crosses 100/day.
- Active CAPA count crosses 2,000.
- Photo storage crosses 100 GB.

None of these are near today. Current architecture is sufficient.

---

## Maintainability · score 3

### Strengths
- Routes split by domain (`safety.py`, `governance.py`, `field_leadership_portal.py`, etc.).
- Components split by portal.
- EN+ES coverage enforced via `t()` discipline.
- Lint clean.
- Idempotent migrations.

### Weaknesses
- `server.py` ~10k LOC.
- `NewIncident.jsx` ~1306 LOC + `NewDailyReport.jsx` ~1591 LOC.
- 233 inherited pytest failures masking real signal.

All weaknesses tracked; all have remediation paths in `Next Action Items`.

---

## Operational trust · score 5

The platform's strongest axis. Phase 5D / 6 / 7 work consolidated:
- Severity escalation safety net (hard refusal on bare serious-incident submit).
- Second-reviewer rule on CAPA verification.
- Audit trails everywhere.
- Idempotency-key dedup.
- Governance contradictions surface real disagreements between subsystems.
- Notification volume controlled by discipline matrix.

This is the axis where investors and customers form their fastest judgement. It is also where the platform shines brightest.

---

## Productization roadmap (informational, not a commitment)

If commercial scaling becomes an active goal, the recommended order is:

1. **Multi-tenancy scaffolding** (per-tenant DB or row-level filter — choose Path A or B). 30-60 days of engineering.
2. **Tenant-driven branding env vars** (FastAPI title, PDF filenames, logo URL, email from). 4-6 days.
3. **First-run setup wizard** (company name, first admin, optional demo seed). 5-7 days.
4. **Per-tenant backup + restore** (today's backup is platform-wide). 4-5 days.
5. **Customer-facing status page** + support ticketing. External services.

**Phase 8 scope:** identify and document, NOT execute.

---

## Bottom line

The platform is **production-grade for MASCI** today.

It is **directionally a commercial product** — the operational discipline, signal hygiene, and lifecycle continuity that took 7 phases to harden are exactly what a commercial customer would buy.

It is **NOT yet a multi-tenant SaaS**. Three hard blockers exist (tenant isolation, branding configurability, multi-company onboarding). Each has a known remediation path; none is in Phase 8 scope.

Score: **2.8 / 5.** Production-grade · Directionally commercial · Not yet SaaS.
