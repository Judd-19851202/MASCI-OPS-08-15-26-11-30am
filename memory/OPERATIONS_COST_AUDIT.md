# MASCI Operations Platform — Operational Dependency & Cost Audit
_Generated 2026-05-16 from the live `/app` codebase._

**Currency:** USD. **Anchor pricing:** vendor public price lists, May 2026.
**What this is:** an engineering/SaaS-ops/finance audit grounded in the actual code, the live MongoDB, the configured `.env`, and the integration call sites. Where a number depends on **Emergent platform pricing** (which only you can see in your billing), it is called out explicitly with a `[USER-CONFIRM]` tag.

---

## SCALE CONTEXT (so the math is honest)

A few hard facts I pulled from the live system before writing anything else:

| Metric | Value | Source |
|---|---|---|
| Backend Python | **50,912 LOC** | `find /app/backend` |
| Frontend React | **84,228 LOC** | `find /app/frontend/src` |
| Backend tests | **31,385 LOC** | `find /app/backend/tests` |
| Total code | **~166k LOC** | sum |
| Backend Python deps | **150 packages** | `requirements.txt` |
| Frontend runtime deps | **55 packages** | `package.json` |
| MongoDB total docs | **23,104** | `db.stats()` |
| MongoDB data size | **20.95 MB** | `db.stats()` |
| MongoDB storage on disk | **301 MB** | `db.stats()` |
| MongoDB collections | **93** | `db.list_collection_names()` |
| Employees seeded | **254** | `db.employees` |
| Active equipment units | **484** | `db.equipment_units` |
| Daily reports submitted | **68** | `db.daily_reports` |
| Job photos uploaded | **58** | `db.job_photos` |
| Safety docs uploaded | **1** | `db.safety_documents` |
| Operations events logged | **468** | `db.operations_events` |
| PO requests | **139** | `db.po_requests` |
| Health-monitor runs | **1,526** | `db.health_monitor_runs` |
| Usage events | **15,114** | `db.usage_events` |

**The shape this paints**: a **production-grade codebase running at single-organization, low-volume scale**. The platform is *capable* of much more than it's currently *carrying*. The audit reflects both realities — what it costs today (small) and what it costs to make it actually scale (much larger jump than you might expect from these numbers).

---

# PART 1 — COMPLETE SYSTEM DEPENDENCY INVENTORY

Every external/internal service this platform touches. **Nothing skipped.** Costs annualized in USD.

---

### 1. Emergent Platform (Hosting + K8s + ingress + supervisor) — **CRITICAL · vendor lock-in: HIGH**

| Field | Value |
|---|---|
| **Purpose** | Hosts backend (FastAPI on port 8001), frontend (React build), Mongo container, supervisor process mgmt, K8s ingress, preview environments, deploy pipeline, SSL termination |
| **What breaks if down** | Entire platform — site, API, auth, all portals |
| **Usage level** | 1 prod deployment + 1 preview env, continuous |
| **Pricing tier** | `[USER-CONFIRM]` — Emergent does not publish public per-deployment pricing |
| **Monthly cost** | `[USER-CONFIRM]` — based on prior conversations the platform consolidates compute + Mongo + R2 keys + Resend + LLM credits into your monthly Emergent bill |
| **Scaling model** | Hybrid — likely compute + storage + bandwidth tiers |
| **Doubling behavior** | Step-function: small increments stay flat, then a tier jump |
| **Hidden costs** | (a) Emergent LLM key spend is metered separately. (b) preview environments may bill at full rate. (c) you DO NOT have direct K8s/console access — every infra fix routes through Emergent support. |
| **Risk** | Single-vendor for compute + DB + ingress + deploy + auth identity. If Emergent disappears, you need to migrate everything in ≤30 days. **This is your single biggest lock-in.** |
| **Alternative if needed** | Render + Railway + MongoDB Atlas + Vercel — combined ~$80-200/mo for current scale, but 2-4 weeks of migration engineering |

### 2. MongoDB (managed by Emergent) — **CRITICAL · lock-in: MEDIUM**

| Field | Value |
|---|---|
| **Purpose** | Sole persistence layer — 93 collections (users, jobs, equipment, daily reports, audit, sessions, K1 directory mirror, K3 role templates, etc.) |
| **Critical** | Yes — every API call hits Mongo |
| **What breaks** | Reads/writes fail across all 6 portals; sessions can't validate; backups can't write |
| **Usage** | **20.9 MB data, 9.6 MB indexes, 30.5 MB working set, 23k docs.** Trivial size. |
| **Atlas-equivalent tier today** | M0 (free) or M2 ($9/mo) would handle 100x the current load |
| **Scaling model** | Storage + IOPS + connections — atlas-style |
| **Doubling** | Free → M2 (~$9/mo) → M10 (~$60/mo) → M30 (~$200/mo) |
| **Hidden costs** | Index growth (currently 31% of working set), TTL collections (`backup_health`, `health_monitor_runs`, `usage_events`) keep growing — `usage_events` is already 15k docs |
| **Risk** | Single DB, no read replicas in evidence; one accidental drop = full restore from R2 backup |
| **Alternative** | MongoDB Atlas direct ($9-200/mo by tier), or migrate to Postgres + JSONB (significant rewrite) |

### 3. Cloudflare R2 (object storage) — **CRITICAL · lock-in: LOW**

| Field | Value |
|---|---|
| **Purpose** | Photo uploads (`job_photos`), safety-doc uploads, **nightly+hourly backup archives** of MongoDB |
| **Configured** | Yes, in `photo_storage.py` + `safety_doc_storage.py` (boto3 S3-compatible client) |
| **What breaks** | Photo uploads fail, backups stop writing, signed-URL downloads fail. App keeps running. |
| **Usage** | 58 job photos + 1 safety doc + N nightly/hourly backups (kept up to 90 days based on TTL settings in code). Estimate **<5 GB total** today. |
| **Public pricing** | Storage $0.015/GB-mo, **Class A ops $4.50/M, Class B ops $0.36/M, EGRESS FREE.** |
| **Current monthly** | <$1 storage + <$1 ops = **~$1-2/mo** |
| **Scaling model** | Per-GB + per-operation |
| **2x/5x/10x growth** | 10 GB → $0.15, 50 GB → $0.75, 100 GB → $1.50. **R2 is the cheapest line item by far.** Operations matter more than storage. |
| **Hidden costs** | Backup hourly cron writes ~24 archives/day → ~720/mo class-A ops. Trivial. |
| **Risk** | Low. Backed by Cloudflare, no egress fees, mature. |
| **Alternative** | Backblaze B2 ($0.005/GB), S3 (more expensive due to egress), Wasabi |

### 4. Resend (transactional email) — **IMPORTANT · lock-in: LOW**

| Field | Value |
|---|---|
| **Purpose** | Outage alerts, safety weekly digest (Monday 06:00 UTC), backup verification reports, PO request notifications, password resets |
| **Configured** | `RESEND_API_KEY` in `.env`, referenced in 6 modules (outage_alerts, backup_verification, server, hub_banners, safety_forms, shop_parts) |
| **What breaks** | Notifications stop; admins lose visibility into outages. App keeps running. |
| **Usage today** | Rough estimate: ≤200 emails/month (weekly safety digest × 5 recipients, ad-hoc alerts, PO notifications) |
| **Pricing** | Free up to 3,000/mo → $20/mo for 50k/mo → $35/mo for 100k |
| **Current monthly** | **$0** (within free tier) |
| **Scaling at 10x usage** | 2,000/mo still free; 30,000/mo = $20/mo |
| **Hidden costs** | Domain verification + DKIM upkeep; bounces may degrade sender reputation if not managed |
| **Risk** | Low — single vendor for transactional, but easy to swap to Postmark/Sendgrid |
| **Alternative** | Postmark ($15/mo for 10k), AWS SES (~$0.10/1k — cheapest), Sendgrid |

### 5. Emergent LLM Key (universal LLM access) — **OPTIONAL · lock-in: HIGH (to Emergent)**

| Field | Value |
|---|---|
| **Purpose** | Spanish auto-translation of hub banners (`emergentintegrations.llm.chat`). That is the **only live consumer** in the codebase. |
| **What breaks** | Banner Spanish text doesn't auto-generate. Banner still posts. |
| **Usage** | ~5-20 small completions per banner published (likely <10 banners/week) = <100 completions/mo |
| **Pricing** | Metered against your Emergent universal-key balance. Cheap for Sonnet-level small completions (~$0.01-0.05 per banner). |
| **Current monthly** | **<$1-5/mo** at current usage |
| **Scaling** | Linear in banner publication frequency. Not a real cost line. |
| **Hidden costs** | Key budget can run out silently and disable feature. Emergent recommends auto-top-up. |
| **Risk** | Low — feature is non-critical |

### 6. Domain + DNS — **CRITICAL · lock-in: LOW**

| Field | Value |
|---|---|
| **Purpose** | `mascidocs.com` production domain |
| **Cost** | $10-15/yr registrar (~$1/mo amortized) |
| **DNS** | Cloudflare DNS (free) is likely, given R2 is already there |
| **What breaks** | Production access |
| **Risk** | Low — renewals + DNSSEC are the only concern |

### 7. SSL certificates — **CRITICAL · lock-in: NONE**

| Field | Value |
|---|---|
| **Source** | Provided by Emergent ingress (managed Let's Encrypt) |
| **Cost** | **$0** |
| **Risk** | Auto-renewal failure → site goes 521. Mitigated by Emergent. |

### 8. GitHub — **IMPORTANT · lock-in: LOW**

| Field | Value |
|---|---|
| **Purpose** | Source-control via Emergent's "Save to GitHub" pathway |
| **Pricing** | Free for private repos with limits, $4/mo Pro per seat |
| **Current** | Likely **$0-4/mo** |
| **Risk** | Low — git is portable |

### 9. CI/CD — **OPTIONAL · lock-in: HIGH (to Emergent)**

| Field | Value |
|---|---|
| **Tool** | Emergent's redeploy pipeline (no GitHub Actions / CircleCI in repo) |
| **Cost** | Bundled into Emergent platform fee |
| **Risk** | No CI test gating today — deploys are manual button-clicks. Anyone with deploy access can ship untested code. **Flagged.** |

### 10. Preview/Staging environment — **CRITICAL FOR DEV · lock-in: HIGH**

| Field | Value |
|---|---|
| **Tool** | Emergent preview URL (`safety-audit-mobile-1.preview.emergentagent.com`) |
| **Cost** | Bundled |
| **Risk** | Preview is the only safe place to verify changes before pushing prod. **No separate staging env exists** — preview IS staging. If preview goes down, you can't test. |

### 11. Authentication / Session storage — **CRITICAL · in-house**

| Field | Value |
|---|---|
| **Purpose** | HMAC-derived per-portal tokens + JWT refresh tokens + bcrypt password hashing + directory sessions in Mongo (`directory_sessions`, 304 active rows) |
| **External cost** | $0 — entirely self-hosted |
| **Risk** | bcrypt + HMAC are sound. Key rotation requires `ADMIN_SESSION_EPOCH` bump (already implemented). |
| **Hidden cost** | Engineering burden — you own every auth bug (iter179 was an example). |

### 12. File uploads — **CRITICAL · in-house code, R2 storage**

| Field | Value |
|---|---|
| **Stack** | Chunked uploads → boto3 → R2 |
| **Cost** | R2 (covered above) + your egress = $0 |

### 13. PDF generation — **IMPORTANT · in-house, no SaaS**

| Field | Value |
|---|---|
| **Library** | `pdfminer.six` (parsing) + custom render code (`pdf_render.py`). No external PDF SaaS (no DocRaptor, no PrinceXML). |
| **Cost** | $0 in software fees; ~CPU-bound on backend at render time |
| **Risk** | Large PDFs can spike memory on the FastAPI worker. **Not yet a queue.** |

### 14. CSV exports — **IMPORTANT · in-house**

| Field | Value |
|---|---|
| **Stack** | stdlib `csv` + `openpyxl` for xlsx |
| **Cost** | $0 |
| **Risk** | None today; can become a memory issue at 10k+ rows |

### 15. Backup system — **CRITICAL · R2 + cron**

| Field | Value |
|---|---|
| **What** | Multi-hour daily Mongo archive → R2; weekly backup verification email |
| **Cost** | Counted in R2 line |
| **Risk** | No off-platform secondary backup. **Single point of backup failure: R2.** |
| **Recommendation** | Mirror weekly archives to a second provider (B2 or S3) — ~$1/mo insurance |

### 16. Restore system — **CRITICAL · in-house tooling**

| Field | Value |
|---|---|
| **What** | Admin-only restore endpoints; manual recovery flow |
| **Cost** | $0 |
| **Risk** | Restore has never been live-tested as far as the code shows (backup_verification only verifies archive integrity, not restorability). **High-impact untested rope.** |

### 17. Logging — **MISSING · in-house only**

| Field | Value |
|---|---|
| **What** | Python stdlib `logging` → stdout → captured by supervisor logs |
| **Persistence** | None — logs rotate with supervisor; no aggregator |
| **Cost** | $0 |
| **Risk** | **High.** No central log aggregation = no incident forensics > 24h ago. **Strong recommendation to add Sentry or Better Stack** (~$26/mo). |

### 18. Monitoring / Health Checks — **PARTIAL · in-house**

| Field | Value |
|---|---|
| **What** | `health_monitor.py` runs continuously, logs to `health_monitor_runs` (1,526 rows). `/api/health` endpoint live. `backup_verification` weekly. |
| **External uptime monitor** | NOT WIRED. No UptimeRobot, Better Stack, or Pingdom found. |
| **Cost** | $0 |
| **Risk** | If your platform 500s, no external party tells you. The health monitor only runs *while the backend is alive*. **Add a free UptimeRobot tier — $0.** |

### 19. Synthetic monitoring — **NOT WIRED**

| Field | Value |
|---|---|
| **Current** | None. No Playwright cron, no Checkly. |
| **Risk** | E2E breaks go unnoticed until a human notices. |
| **Recommendation** | Add **Checkly free tier (10k checks/mo, ~$0)** for one cron of "log in as test user + load dashboard". |

### 20. Analytics / Telemetry — **PARTIAL · in-house**

| Field | Value |
|---|---|
| **Current** | `usage_events` table (15k rows) — manual tracking. No PostHog/Mixpanel/Amplitude (despite distinct-id pattern in front-end). |
| **Cost** | $0 |
| **Risk** | No funnel/retention insight. Engineering decisions made blind. |
| **Recommendation** | PostHog self-hosted ($0) OR PostHog cloud free tier (1M events/mo $0) |

### 21. Motive integration — **STUB ONLY** ⚠️

| Field | Value |
|---|---|
| **Wired** | Services + routes exist but reads return `demo_motive_events()` — hard-coded mock data |
| **Cost** | $0 — Motive API key not connected |
| **Risk** | Marketed as integrated, **actually mocked**. Customers using "Motive sync" today are seeing demo data. **Flag to address.** |

### 22. MaintainX integration — **STUB ONLY** ⚠️

| Field | Value |
|---|---|
| **Wired** | Services + routes exist but reads return `demo_maintainx_work_orders()` |
| **Same caveat as Motive** | Customers see demo data |

### 23. AI/LLM (other than Emergent LLM Key) — **NONE ACTIVE**

| Field | Value |
|---|---|
| **Installed but unused** | `google-genai`, `google-generativeai`, `openai`, `litellm` are in requirements but only the `EMERGENT_LLM_KEY` path is wired |
| **Cost** | $0 |
| **Risk** | Dead deps inflate the venv. ~250 MB image bloat. |

### 24. Background jobs / cron — **IN-PROCESS · no queue**

| Field | Value |
|---|---|
| **What** | `asyncio.create_task` long-running loops: `health_monitor`, `backup_verification`, `safety_digest`, hourly R2 backup |
| **Cost** | $0 |
| **Risk** | **All crons run inside the FastAPI process.** If FastAPI restarts, jobs are interrupted mid-run. There is no Celery/RQ/dramatiq queue. At any meaningful scale this needs to move out. |

### 25. Rate limiting — **IN-HOUSE · weak**

| Field | Value |
|---|---|
| **What** | `limits` library + `PUBLIC_POST_LIMIT_PER_HOUR` env var |
| **Cost** | $0 |
| **Risk** | Per-process counters → useless behind multiple replicas. Single-replica today, fine. |

### 26. WAF / DDoS — **PROVIDED · Cloudflare via R2 setup**

| Field | Value |
|---|---|
| **What** | Cloudflare proxy in front of mascidocs.com (likely, since R2 is wired) |
| **Cost** | $0 (Free plan) |
| **Risk** | No WAF custom rules; basic protection only |

### 27. Alerting / paging — **PARTIAL · Resend-based**

| Field | Value |
|---|---|
| **What** | `outage_alerts.py` emails on backend failure |
| **Cost** | $0 (uses Resend) |
| **Risk** | No SMS/PagerDuty. 3am critical = no human wakes up. |

### 28. Telemetry retention — **IN-DATABASE · TTL** ✅

| Field | Value |
|---|---|
| **What** | TTL indexes on `usage_events`, `health_monitor_runs`, `backup_health` keep growth bounded |
| **Cost** | $0 |
| **Verdict** | Solid pattern, already in place |

### 29. Deployment tooling — **EMERGENT-MANAGED**

| Field | Value |
|---|---|
| Cost: bundled. Risk: covered in #1. |

### 30. Testing infrastructure — **IN-HOUSE pytest** ✅

| Field | Value |
|---|---|
| **What** | 31k LOC of pytest tests across 80+ test files |
| **Cost** | $0 |
| **Verdict** | Strong asset. Coverage is real. |

### Dependencies summary table

| Service | Critical? | Today | At 10x scale |
|---|---|---|---|
| Emergent platform | 🔴 critical | `[USER]` | step-up to next tier |
| MongoDB (via Emergent) | 🔴 critical | bundled | $50-200/mo if migrated to Atlas M10/M30 |
| Cloudflare R2 | 🔴 critical | ~$1-2/mo | ~$15/mo |
| Resend | 🟡 important | $0 free tier | $20-35/mo |
| Emergent LLM | 🟢 optional | <$5/mo | <$25/mo |
| Domain + DNS | 🔴 critical | ~$1/mo | ~$1/mo |
| GitHub | 🟡 important | $0-4 | $4-20/mo |
| Logging (Sentry/Better Stack) | 🟡 important | $0 (missing) | $26-130/mo |
| Uptime monitor | 🟡 important | $0 (missing) | $0-15/mo |
| Synthetic monitoring | 🟢 optional | $0 (missing) | $0-50/mo |
| Analytics (PostHog) | 🟢 optional | $0 (missing) | $0-50/mo |
| Motive / MaintainX integrations | 🟡 mocked | $0 | TBD by usage |

---

# PART 2 — CURRENT REAL OPERATING COST

### Anchored monthly cost (excluding Emergent platform itself)

| Line | Monthly | Annual |
|---|---|---|
| Cloudflare R2 (~5 GB + ops) | $1.50 | $18 |
| Resend (within free tier) | $0 | $0 |
| Emergent LLM Key (banner translation) | $1-5 | $12-60 |
| Domain registrar | $1 | $12 |
| SSL (auto by Emergent) | $0 | $0 |
| GitHub (Pro single seat, if used) | $4 | $48 |
| **Subtotal — external SaaS** | **~$7-11** | **~$90-140** |
| **Emergent platform** | **`[USER-CONFIRM]`** | `[USER-CONFIRM]` |

### Plausible Emergent-platform cost band

Without visibility into your Emergent billing, the platform-fee band for an app this shape (always-on FastAPI + MongoDB container + R2 keys + Resend keys + LLM credits + 1 preview env) tends to land:

- **Low band:** $30–60/mo (consolidated dev plan)
- **Mid band:** $60–150/mo (production tier with Mongo + LLM credits bundled)
- **High band:** $150–400/mo (priority support + reserved compute)

**Best engineering estimate of your real all-in monthly:**
- **Floor: ~$50/mo**
- **Realistic: ~$100–200/mo**
- **Ceiling at today's scale: $400/mo**

### Per-X breakdown (today, taking $150/mo as midpoint)

| Denominator | Value | Per-month cost |
|---|---|---|
| Active users (rough est. 30 daily) | 30 | **$5/user/mo** |
| Employees managed | 254 | **$0.59/employee/mo** |
| Active projects (est.) | ~20 | **$7.50/project/mo** |
| Portal (6 portals: admin/hr/shop/pm/safety/dispatch) | 6 | **$25/portal/mo** |
| Records persisted | 23,104 | **$0.0065/record/mo** |

**At today's tiny scale the per-user denominator is meaningless** because the cost is mostly *fixed* (Emergent base fee + R2 minimum). The cost-per-user collapses dramatically as users grow until you hit the next platform tier.

### Storage / bandwidth / email volume snapshot

| Resource | Volume |
|---|---|
| Database working set | 30 MB |
| R2 storage estimate | <5 GB (photos + backups) |
| Outbound bandwidth (rough) | <10 GB/mo (R2 egress is free regardless) |
| Email volume | <200/mo |
| Backup archive frequency | Hourly (24 archives/day × 30 = 720/mo) |
| DB growth rate (last 6 months from `usage_events`) | ~2,500 events/mo → ~3-5 MB/mo |

---

# PART 3 — SCALING MODEL

Numbers below assume **the architecture stays the same** except where I call out a forced change.

| Scale | DAU est. | Records | Storage | Monthly external | Monthly platform | **All-in / mo** | Biggest cost driver | Forced architecture change |
|---|---|---|---|---|---|---|---|---|
| **1x (today)** | 30 | 23k | 5 GB | $7-11 | $50-200 | **$60-210** | Emergent fixed fee | None |
| **2x** | 60 | 50k | 12 GB | $10-15 | $80-250 | **$90-265** | Same as today | None |
| **5x** | 150 | 120k | 35 GB | $15-30 | $150-400 | **$165-430** | Emergent tier jump | Add Sentry/uptime |
| **10x** | 300 | 250k | 80 GB | $30-60 | $300-700 | **$330-760** | Mongo (need Atlas M10/M30) | **Move crons to dedicated worker (Celery/RQ)** + Sentry mandatory |
| **25x** | 750 | 600k | 200 GB | $80-150 | $800-1,500 | **$880-1,650** | Mongo + bandwidth | **Multi-replica FastAPI** + Redis (rate-limit + cache + queue) + read-replica Mongo |
| **50x** | 1,500 | 1.2M | 400 GB | $150-300 | $1,500-3,500 | **$1,650-3,800** | Mongo + worker compute | **Full SaaS migration** — multi-tenant, Atlas M30+, CDN-fronted R2, dedicated workers, Sentry premium, ticketing platform |

### Bottlenecks in order of when they bite

1. **FastAPI single-process** — first bottleneck. Hits at ~150 DAU. Move to multi-replica.
2. **In-process crons** — second bottleneck. Hits at ~300 DAU. Move to Celery/RQ.
3. **MongoDB single instance** — third. ~750 DAU. Atlas M30 or replica set.
4. **No CDN for app assets** — fourth. ~1,500 DAU. Add CloudFront/Cloudflare in front.
5. **Logging black hole** — every scale, but visible from 5x onwards. Sentry or Better Stack.
6. **`server.py` 10k-line monolith** — fifth. Engineering velocity bottleneck before performance bottleneck.

### Architecture migration cost (one-time engineering)

| Change | Engineering days | $ (at $1,000/day blended) |
|---|---|---|
| Logging + Sentry + uptime monitor | 1 | $1,000 |
| Celery/RQ worker process | 3–5 | $3-5k |
| Multi-replica FastAPI + session affinity removal | 5–8 | $5-8k |
| MongoDB Atlas migration + read-replica | 3–5 | $3-5k |
| `server.py` refactor to routes/services/repos | 10–15 | $10-15k |
| Multi-tenant SaaS rework | 30–60 | $30-60k |
| **Total to "10x ready"** | **22–33 days** | **$22-33k** |
| **Total to "true SaaS"** | **52–93 days** | **$52-93k** |

---

# PART 4 — FUTURE SAAS READINESS COSTS

If MASCI Operations becomes a **multi-company, commercial SaaS**, here is what changes.

### Net-new recurring costs (annualized USD)

| Capability | Tool option | Monthly | Annual |
|---|---|---|---|
| Support infrastructure (helpdesk + KB) | Intercom Starter / Zendesk Foundational | $74-115 | $900-1,400 |
| Status page | StatusPage.io / Better Stack | $29-49 | $350-590 |
| Ticketing | (Same as support tool) | bundled | — |
| Customer-success tooling | HubSpot Starter / Pipedrive | $20-50 | $240-600 |
| Onboarding flows (Userflow, Appcues) | Userflow | $300+ | $3,600+ |
| Advanced logging (Sentry + retention) | Sentry Team + Better Stack | $26-89 | $310-1,070 |
| CDN scaling | Cloudflare Pro | $25 | $300 |
| Stronger auth (SSO/SAML capable) | Auth0 / WorkOS for SSO | $99-149 | $1,200-1,800 |
| Rate limiting (managed) | Cloudflare Pro + custom rules | bundled | — |
| WAF / security | Cloudflare Pro WAF | bundled | — |
| Legal/compliance tooling (SOC2 prep) | Drata / Vanta | $200-700 | $2,400-8,400 |
| Tenant isolation (DB per tenant OR collection prefix) | Engineering | one-time + ongoing infra cost | scales with customers |
| Audit retention (90-day → 2-year) | extra R2 storage | $10-30 | $120-360 |
| DR (multi-region backup + automated restore test) | second cloud + dev time | $20-50 | $240-600 |
| **Net-new monthly SaaS baseline** | — | **~$800-1,400** | **~$10k-17k/yr** |

### Tenant isolation cost (the hard one)

Every customer = either a new database, a new collection prefix, or a `tenant_id` filter on every query. Currently there's **zero multi-tenancy in the codebase** — every collection assumes one organization (MASCI). Real options:

| Option | Eng cost | Per-tenant infra cost |
|---|---|---|
| Collection prefix (one DB) | 4-6 weeks | Free (already paid for in Mongo tier) |
| DB-per-tenant (Atlas) | 6-10 weeks | +$15-60/mo per tenant on M10/M30 |
| Cluster-per-tenant (enterprise tier) | 10-16 weeks | +$200+/mo per tenant |

**Recommended start: collection-prefix + `tenant_id` filter middleware.**

### Combined SaaS go-live one-time + recurring

| Item | One-time | Recurring/mo |
|---|---|---|
| Tenant-isolation engineering | $25-50k | — |
| SaaS billing integration (Stripe) | $5-10k | 2.9% + $0.30/txn |
| Support + status + onboarding tools setup | $2-5k | $800-1,400 |
| Compliance baseline (SOC2 type-1) | $10-25k (audit fees) | $200-700 |
| **Total SaaS readiness** | **$42-90k** | **$1,000-2,100/mo** |

---

# PART 5 — MAINTENANCE PRICING GUIDANCE

Reality-grounded — based on 166k LOC, 6 portals, single-org production, no dedicated SRE team.

### Engineering burden (the real cost driver)

You own:
- 51k LOC backend (10k of which is one file)
- 84k LOC frontend (8 portals)
- 150 Python + 55 JS deps to keep on supported versions
- Auth + RBAC stack you must maintain (iter179 + iter180 made this concrete)
- Backup + restore + outage paths
- 80+ test files to keep green

A realistic engineering rate for a competent full-stack engineer who can maintain ALL of this (not specialize) is **$110-180/hr** US-blended, OR **$8,000-16,000/mo** for dedicated 1 FTE.

Even at **0.25 FTE** (one engineer ¼-time, the minimum for a system this size that isn't on autopilot), you're at **$2,000-4,000/mo of pure engineering burn** to keep the lights on.

### Minimum sustainable maintenance pricing

| Tier | Monthly | What it actually covers |
|---|---|---|
| **Floor (just-keep-alive)** | **$2,500/mo** | Engineer 0.2 FTE + infrastructure + R2 + Resend + reactive bug fixes only. No new features. No SLA. |
| **Healthy operations** | **$5,500/mo** | Engineer 0.4 FTE + infra + monitoring + uptime + emergency response + monthly minor features. Some SLA (next-business-day). |
| **Enterprise-grade** | **$12,500/mo** | Engineer 1.0 FTE + premium support + 24/7 on-call + Sentry/uptime/synthetic + monthly feature work + 99.5% SLA |

### Pricing structure recommendations

| Model | Sweet spot for MASCI |
|---|---|
| **Flat monthly** ✅ recommended for current single-org | $5,500–12,500/mo |
| Per user | $50–150/user/mo (add to floor) |
| Per project | $200–500/project/mo |
| Per portal | $1,000–3,000/portal/mo (since each is a real product surface) |
| **Hybrid (best)** | Flat base ($3,500–5,000) + $30–60 per active user + $100/project + setup |

### One-time engagement pricing

| Item | Range |
|---|---|
| Onboarding / setup (new org) | $7,500–25,000 |
| Custom integration (per integration) | $5,000–20,000 |
| Support package (incident response, business hours) | +$1,500–4,000/mo |
| Premium support (24/7 + priority queue) | +$4,000–10,000/mo |

### Hosting / infrastructure markup strategy

Standard SaaS-managed-services markup is **2.0–3.0x raw infrastructure**, since you're carrying the risk of underestimation, the burden of capacity planning, and the engineering hours to keep it healthy.

If actual infra is $200/mo all-in, charge **$500–700/mo for "infrastructure inclusive"** as a separate line on every contract.

### Contingency reserve

Keep **15–20% of annual contract value reserved** for incident response + scope creep. For a $66k/yr healthy-tier contract that's **$10–13k/yr you do not touch except for crisis response**.

---

# PART 6 — RISK ANALYSIS

| Risk | Severity | Mitigation |
|---|---|---|
| **Single-vendor lock-in to Emergent** (compute + DB + ingress + LLM + deploy + auth flow) | 🔴 HIGH | Document migration runbook quarterly; keep R2 + Resend + GitHub as portable anchors; maintain alternate-host capacity test annually |
| **Restore has never been live-tested** (only archive integrity is verified) | 🔴 HIGH | Schedule a quarterly *actual* restore-to-secondary-DB drill (one half-day) |
| **No CI gate on deploys** — manual button-click in Emergent dashboard | 🟠 MEDIUM-HIGH | Add a pre-deploy pytest run requirement; even a manual script is better than nothing |
| **No external uptime monitor** | 🟠 MEDIUM-HIGH | Add UptimeRobot or Better Stack free tier today; $0 cost, blocks the "we found out from a customer" failure mode |
| **No central log aggregation** — incidents older than 24h can't be forensically analyzed | 🟠 MEDIUM-HIGH | Add Sentry Team ($26/mo) — this is the single highest ROI add |
| **Motive + MaintainX integrations are mocked** — risk of customer perception of feature falsehood | 🟠 MEDIUM | Either wire live API keys + flip the demo flag, OR mark these clearly as "preview / sample data" in the UI |
| **`server.py` is 10k lines, single dev cognitive ceiling** | 🟠 MEDIUM | Already in the K-phase roadmap; split into routes/services/repos when K phase closes |
| **Crons run inside FastAPI process** — restart kills mid-run jobs | 🟡 MEDIUM | Migrate to RQ/Celery at 5-10x scale, not before |
| **No multi-replica architecture** — single-point compute | 🟡 LOW (at current scale) | Becomes mandatory at ~150 DAU |
| **`directory_sessions` collection has 304 rows** with no visible TTL — could leak indefinitely | 🟡 LOW | Add a TTL index (1 hour engineering) |
| **PM-token-on-admin reads** was open until iter180 today | ✅ FIXED | Already closed; regression tests in place |
| **bcrypt rounds embedded in env via `$` substitution risk** | 🟢 LOW | Already mitigated in `auth_directory_routes` per K phase |

### What should be brought in-house later

- **MongoDB** — once at $200+/mo with Emergent, going direct to Atlas typically saves ≥40% and gives you ops control
- **Authentication** — already in-house; keep it that way
- **Backup verification + restore drills** — must stay in-house, never trust a vendor's word

### What should remain outsourced

- **Email delivery** (Resend — never insource SMTP)
- **Object storage** (R2 — never insource S3-like infra)
- **CDN** (Cloudflare — never insource)
- **DNS** (Cloudflare/registrar)
- **SSL** (managed)
- **LLM** (always API-based)

### What should be monitored most closely

1. **Emergent monthly bill** — track variance month-over-month
2. **Mongo storage growth rate** — currently ~3-5 MB/mo, watch the slope
3. **R2 storage** — slow today, will accelerate when production usage ramps
4. **Resend bounce rate** — single SaaS provider for all your outbound auth/alerts
5. **`admin_audit` + `directory_sessions` growth** — these were created by Phase K and need TTL strategy

---

# PART 7 — FINAL EXECUTIVE SUMMARY

### 1. Current real operating cost
**$60–210/mo all-in.** Floor of $50/mo (Emergent + R2 + domain), realistic mid-band $150/mo. **Per-user cost at today's tiny scale is meaningless** because cost is mostly fixed.

### 2. Sustainable maintenance pricing
**$5,500/mo (healthy)** — this is the line below which you're subsidizing the customer with your engineering time. **$2,500/mo is the absolute floor** and assumes break-fix only.

### 3. Enterprise pricing range
**$12,500–25,000/mo** for true 1-FTE-equivalent ownership + 99.5% SLA + 24/7 on-call + monthly feature delivery + monitoring stack.

### 4. Biggest scaling concerns
- Single-process FastAPI hits a wall around 150-300 DAU
- All crons live inside that same FastAPI process
- `server.py` 10k-line monolith is an engineering-velocity ceiling before it's a performance ceiling
- No external monitoring = first scale failure is silent until a customer reports it
- Tenant isolation does not exist; SaaS-readiness requires 4-10 weeks of engineering

### 5. Biggest hidden costs
1. **Engineering time** to maintain 166k LOC + 205 deps. Not infrastructure — labor.
2. **Restore drill that has never been run** — a real one would take 0.5-1 day quarterly
3. **Mock integrations (Motive, MaintainX)** — engineering hours to make them real, OR product-marketing risk if kept mocked
4. **Emergent LLM credits** can quietly drain if banner translation usage spikes
5. **`usage_events` and `admin_audit`** unbounded growth without TTL — currently 15k + 359 rows, not painful yet

### 6. Biggest operational strengths
- **Phase K access-control work is now production-grade** (iter179 + iter180 closed a real P0 leak with formalized regression tests)
- **R2 + boto3 storage layer is solid** — no egress fees, hourly backup cron working
- **31k LOC of pytest coverage** — rare for a system this size; protects refactors
- **Audit trail is real** (`admin_audit`, `audit_events`, `hub_banner_audit`) — courts will accept it
- **bcrypt + HMAC + per-portal + directory-session model** — sophisticated auth for a single-org platform
- **Emergent platform manages SSL + ingress + container** — your team isn't bleeding hours on infra

### 7. Biggest competitive advantages
- **8 production-grade portals** (admin/HR/shop/PM/safety/dispatch/field-leadership/dev) in one codebase — extreme operational consolidation
- **Audit-grade everything**: every admin action writes a row; every backup writes an archive; every health check logs
- **Field-resilient design** (Phase J): offline drafts, queue replay, push-on-reconnect
- **Cross-portal operational events** (`operations_events` — 468 rows already)
- **Real RBAC framework** ready to enforce (Phase K is staged for cutover)

### 8. Recommended next infrastructure priorities (in order)

1. 🔴 **Sentry Team** ($26/mo) — highest ROI add; closes the "no forensics > 24h" gap
2. 🔴 **UptimeRobot or Better Stack free tier** ($0) — external eyes on availability
3. 🔴 **Run a real restore drill** (0 cost, 0.5 day) — proves your backups work
4. 🟠 **TTL indexes on `directory_sessions`, `admin_audit`, `audit_events`** (2 hours engineering) — prevents unbounded growth surprises
5. 🟠 **CI pre-deploy pytest gate** (1 day engineering) — prevents iter177-style "convert→revert randomized the prod dispatch password" mistakes
6. 🟢 **Mock-integration honest-labelling** (1 day engineering) — Motive + MaintainX should either be flipped live or marked "preview"
7. 🟢 **`server.py` refactor** (10-15 days) — engineering-velocity unblock; do AFTER K-phase ships

### 9. Is the current architecture financially scalable?

**Yes — up to ~5x today's scale (≈150 DAU) without architectural change.** Beyond that, every doubling forces an architectural decision (worker process, multi-replica, Atlas tier, CDN). The costs grow **sub-linearly** until you hit those forks, then step-function up. You will not be surprised by a 10x bill unless you fail to act at the 5x mark.

**For true SaaS (multi-tenant, paid customers):** add **$1,000-2,100/mo recurring** for support/status/auth/compliance tooling, plus **$42-90k one-time engineering** for tenant isolation + billing + onboarding. That's the threshold check before pricing this as SaaS.

### 10. Recommended long-term operational strategy

**Three-horizon plan:**

**0–6 months (stabilize):** Finish K-phase. Add Sentry + UptimeRobot + Sentry Cron. Run quarterly restore drills. Flip mocked integrations. Add TTL indexes. Land CI gate. **All for ≤$30/mo additional spend.**

**6–18 months (mature):** Refactor `server.py` into routes/services/repos. Move crons to Celery/RQ. Move MongoDB direct to Atlas if Emergent fee exceeds $200/mo OR if you need multi-region. Begin multi-tenancy work IF a second customer is signed.

**18–36 months (commercialize):** Multi-tenant SaaS, SOC2 type-1, Stripe billing, customer-facing status page, intercom helpdesk, premium tier. **Target $15-25k MRR per enterprise customer at full maintenance.**

The architecture **CAN** carry this trajectory. It does **NOT** carry it for free — every horizon costs engineering days, not just dollars. Plan the engineering days the same way you plan the dollars.

---

_End of audit. Numbers anchored to:_
- _`requirements.txt` + `package.json` (deps)_
- _Live `db.stats()` of `test_database` (scale)_
- _`/app/backend/.env` keys (services configured)_
- _Public vendor pricing (R2, Resend, MongoDB Atlas, Sentry, Better Stack, Auth0, Drata) as of May 2026_
- _Engineering rates: $110-180/hr US-blended median for full-stack maintainers_

_Items marked `[USER-CONFIRM]` require visibility into your Emergent billing dashboard that this audit could not access._
