# WHITE-LABEL · DATA ISOLATION MATRIX

**Phase 5 deliverable.** For each surface, is per-customer isolation achievable today?

## Current state — single-tenant MASCI deploy

The platform is built as one customer per deployment. Customer-#2 would need an entirely separate deployment OR a tenant model. Current isolation primitives only separate **environments** (preview vs production), not **customers**.

| Surface | Per-environment isolation today | Per-customer isolation (in shared deploy)? | Notes |
|---------|--------------------------------|--------------------------------------------|-------|
| Database | 🟢 STRONG (RC1 cert: `DB_NAME` per env · Atlas credentials separated · ENFORCE_DB_ISOLATION=true) | ❌ no — would need either separate DB per tenant OR row-level `tenant_id` everywhere | DB-per-customer is the lowest-risk path |
| User directory | 🟢 separated by DB | ❌ no — `user_directory` collection has no `tenant_id` | DB-per-customer solves trivially |
| Auth tokens | 🟢 separated by DB (token stored with user record) | ❌ no — no tenant binding on tokens | DB-per-customer solves trivially |
| File storage (R2) | 🟡 shared bucket `masci-hub`, but keys timestamped + env-tagged | ❌ no — would need per-customer prefix `{customer_slug}/...` | trivial: customer_slug env var |
| PDF generation | 🟡 streamed inline (not persisted to shared storage by default) | 🟡 PDFs reference hardcoded MASCI logo from `frontend/public/` | per-customer asset deployment fixes this |
| Backups | 🟡 R2 keys include `db_name` | ❌ no — customer #2's backup would land in same bucket without prefix | per-customer prefix fixes this |
| Audit log | 🟢 in DB · isolated by DB | ❌ no — events have no `tenant_id` | DB-per-customer solves |
| Notifications | 🟢 in DB · isolated by DB | ❌ no — would leak between tenants in shared DB | DB-per-customer solves |
| Email send | 🟢 gated by `AUTO_EMAIL_REPORTS` per env | ❌ no — Resend account would be shared; sender domain hardcoded to MASCI | per-customer Resend account + sender domain config required |
| Integration credentials (Motive · FleetWatcher · MaintainX) | 🟢 env-driven | ❌ no — only one set of credentials per deploy | per-customer deploy OR per-customer credential vault |
| Sentry | 🟢 env-driven `SENTRY_DSN` | ❌ no — one project shared | per-customer Sentry project fixes this |
| Cron / scheduler (backups, digests) | 🟢 runs in each pod | ❌ no — would fire for "all customers" in shared deploy | per-customer deploy OR tenant loop in scheduler |
| Cache (no Redis used) | n/a | n/a | no shared cache layer to worry about |

## Comparison of isolation models

### Model A — One deployment per customer (recommended for Customer #2)
- **Isolation**: 🟢 STRONGEST. Same primitives as preview/prod isolation already proven. No data path can cross.
- **Effort**: Provision Atlas DB · provision R2 bucket · provision Resend domain · provision Sentry project · deploy with customer-specific env vars · run BrandConfig clone-rebrand.
- **Drawback**: One Kubernetes deploy per customer. Costs scale linearly.
- **Verdict**: This is what RC1 already proves works (preview vs prod) — just extended to N customers.

### Model B — One database per customer, shared app
- **Isolation**: 🟢 STRONG. Per-request DB router (`db = client[get_tenant_db_name(request)]`).
- **Effort**: Tenant resolver middleware · DB router · per-tenant credential store · BrandConfig per request.
- **Drawback**: Single shared app pod is a blast radius. One bug can leak between tenants. Requires tenant-aware routing on every endpoint.
- **Verdict**: Possible but riskier than A.

### Model C — Shared database, `tenant_id` scoping (true multi-tenant SaaS)
- **Isolation**: 🟡 MEDIUM. Every query must include `tenant_id={resolved_tenant}`. Forgetting one query = cross-tenant leak.
- **Effort**: tenant_id on EVERY collection · MongoDB compound indexes · scope helper on every read/write path · audit log tenant-scoped · notifications tenant-scoped · backups tenant-aware.
- **Drawback**: Highest engineering risk. Smallest hosting cost.
- **Verdict**: Only worth it at 10+ customers.

## Recommendation

🟢 **Model A** for Customer #2. It re-uses the exact RC1 isolation pattern (which is already proven). Customer #2 = "third deployment after preview and prod" rather than "first multi-tenant tenant." This decision is **reversible** later (can migrate to Model B/C when customer count justifies the engineering risk).
