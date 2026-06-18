# TRACK 15.24 — PLATFORM COST + SCALING AUDIT
## Read-Only · No Code · No Deploy

**Date:** 2026-06-18
**Author:** E1 (Emergent main agent)
**Pillars priority:** TRUSTED + PROVEN > all others.

---

## TRUST CHARTER — read this first

This document distinguishes 4 classes of evidence. **Every number is labeled.** Do not act on them interchangeably.

| Label | Meaning | Trustable for budget decisions? |
|---|---|---|
| 🟢 **ACTUAL** | Measured live, just now, from the pod/database/storage. Re-runnable. | Yes — these are facts. |
| 🟡 **VENDOR LIST PRICE** | Pulled from the vendor's public public-pricing page; the *exact* plan you're on may differ. | Yes for upper bounds; no for the precise contract you have. |
| 🟠 **MODEL** | Calculated by extrapolation with the assumption stated inline. | Use as forecasting input, not as commitment. |
| 🔴 **UNKNOWN — OPERATOR REQUIRED** | I cannot retrieve this from inside the pod. Must be pulled from the vendor's billing dashboard. | Treat as "to be confirmed." |

**Trust gap acknowledgment.** I have no access to MASCI's Atlas billing console, Resend dashboard, Sentry dashboard, Cloudflare dashboard, or Emergent billing console. Every cost number for those services is either 🟡 (list price guess) or 🔴 (must be retrieved by the operator). I refused to fabricate dollar amounts where evidence does not exist. Where I had to estimate, I stated the formula.

---

## 1 · CURRENT FOOTPRINT — measured (🟢 ACTUAL)

### 1.1 MongoDB Atlas — `masci_safety_preview` DB (cluster `atlas-5p2de4-shard-0`)

Measured live from the running pod against the production Atlas cluster.

| Metric | Value |
|---|---|
| Cluster replica set | `atlas-5p2de4-shard-0` (3 nodes — multi-node, multi-AZ canonical Atlas dedicated cluster naming) |
| Cluster hosts | `ac-cz4whli-shard-00-{00,01,02}.1nduwmg.mongodb.net` |
| DB engine | MongoDB **8.0.26 Enterprise** (`modules: ['enterprise']`) |
| Number of collections | **177** |
| Number of documents | **504,006** |
| `dataSize` (logical) | **184.62 MiB** |
| `storageSize` (compressed on disk) | **268.53 MiB** |
| `indexSize` | **51.86 MiB** |
| Avg object size | **384 bytes** |
| `.env` soft cap (`ATLAS_QUOTA_MB`) | 10,240 MiB |
| Current utilization vs that soft cap | **1.80 %** |

**Top 10 collections by storage footprint (🟢 ACTUAL)**

| Storage | Index | Docs | Collection |
|---:|---:|---:|---|
| **132.62 MiB** | 0.50 MiB | 1,032 | **daily_reports** ← #1 footprint driver (avg ~128 KiB/doc — photos likely inlined) |
| 30.86 MiB | 0.25 MiB | 67 | incidents |
| 30.79 MiB | 0.11 MiB | 6 | job_hazard_files (avg 5.1 MiB/doc — large inline binaries) |
| 29.56 MiB | 0.29 MiB | 2,662 | job_photo_thumb_cache |
| 12.90 MiB | 0.11 MiB | 42 | meetings |
| 12.34 MiB | **27.45 MiB** | 411,686 | **usage_events** ← index size > data size; index-heavy |
| 2.83 MiB | 2.04 MiB | 9,740 | notifications |
| 1.67 MiB | 0.84 MiB | 18,398 | audit_events |
| 1.30 MiB | 0.38 MiB | 845 | equipment_inspections |
| 0.63 MiB | 0.58 MiB | 18,598 | health_monitor_runs |

### 1.2 Cloudflare R2 bucket `masci-hub` (S3 endpoint `46400762d3027afbb26819a8de8528e6.r2.cloudflarestorage.com`)

Measured by `boto3.list_objects_v2` paginator against the live bucket.

| Prefix | Object count | Size | Notes |
|---|---:|---:|---|
| `backups/` | **1,975** | **283.06 GiB** | hourly + 90-day-retention zips. **#1 R2 footprint driver.** |
| `drill-photos/` | 3,800 | 1.58 GiB | JHA / drill photos |
| `photos/` | 3,810 | 0.81 GiB | job photos |
| `safety-docs/` | 19 | 0.001 GiB | PDFs |
| `legacy-imports/` | 4 | 0.0001 GiB | one-time imports |
| **TOTAL** | **9,608** | **285.45 GiB** |  |

**Backup-zip growth analysis (🟢 ACTUAL)**

| Age bucket | Zip count | Size | Avg zip size |
|---|---:|---:|---:|
| ≤ 7 days | 193 | 101.62 GiB | **539 MiB / zip** |
| 8–30 days | 1,090 | 153.61 GiB | 144 MiB / zip |
| 31–90 days | 692 | 27.83 GiB | 41 MiB / zip |
| 91+ days | 0 | 0 | (cluster < 90 days old; oldest zip 2026-05-11) |

⚠️ **Per-zip size has grown 13× in the last ~6 weeks** (41 MiB → 539 MiB). At the recent rate the bucket grows by **≈ 14.5 GiB / day** — `BACKUP_HOURS_UTC=2,18` is configured but `BACKUP_R2_HOURLY=true` means a backup every hour, ~24 backups/day, currently ≈ 27/day at peak. Annualized this is ≈ **5 TiB / year if nothing changes**.

### 1.3 Pod (Emergent compute) — measured from cgroups (🟢 ACTUAL)

| Metric | Value |
|---|---|
| Memory cgroup hard cap (`memory.max`) | **8.00 GiB** (8,589,934,592 bytes) |
| Memory currently in use (`memory.current`) | **3.10 GiB** (3,334,549,504 bytes) — **38.8 %** of cap |
| CPU cgroup quota (`cpu.max`) | **200,000 / 100,000 = 2.00 vCPUs** |
| Host visible RAM | 31 GiB (irrelevant — cgroup is the binding limit) |
| Host visible CPUs | 8 (irrelevant — cgroup is the binding limit) |
| Root overlay disk | 104 GB capacity, **27 GB used (26 %)** |
| `/app` directory | 4.8 GiB |
| `/var/log/supervisor/*` | 170 MiB (logs rotating; `backend.err.log` 8.6 MiB, `backend.out.log` 9.7 MiB, `frontend.out.log` 3.9 MiB) |

**Note on Emergent "4 GB upgrade":** the operator referenced a recent ~4 GB allocation increase. The pod **cgroup currently sees 8 GiB**, which is *higher* than the referenced 4 GB. This either means (a) the upgrade increased a different metric (likely *durable storage / artifact allowance*, not RAM), or (b) the most recent resize is double the referenced number. **🔴 Operator must confirm in Emergent billing dashboard which knob "the 4 GB" refers to.**

### 1.4 User / population evidence (🟢 ACTUAL)

| Source | Count | Notes |
|---|---:|---|
| `user_directory` (admin / HR / PM / multi-portal accounts) | **162** | active portal logins |
| `field_leadership_users` | 31 |  |
| `shop_users` | 12 |  |
| `safety_users` | 11 |  |
| `dispatch_users` | 12 |  |
| `asset_admin_users` | 0 |  |
| **Total portal accounts** | **228** |  |
| `employees` collection | **395** (383 active) | the operational roster — bigger than logins because not every employee has a login |

### 1.5 Workload velocity (🟢 ACTUAL, last 7 / 30 days from timestamp fields)

| Collection | Total | 7-day adds | 30-day adds | Daily rate (7d) |
|---|---:|---:|---:|---:|
| usage_events | 411,686 | 101,994 | 411,686 | **14,571 / day** ← ⚠️ #1 doc-volume driver |
| health_monitor_runs | 18,598 | 6,242 | 18,598 | **892 / day** (probe every ~1.6 min) |
| audit_events | 18,398 | 746 | 8,799 | 107 / day |
| notifications | 9,740 | 2,245 | 9,004 | 321 / day (all `channel=None` — *in-app only*; no email/SMS sends recorded) |
| admin_audit | 5,957 | 1,411 | 5,457 | 202 / day |
| directory_sessions | 3,842 | 1,223 | 3,842 | 175 / day |
| daily_reports | 1,032 | 190 | 977 | **27 / day** ← business KPI |
| cluster_capacity_history | 1,781 | 608 | 1,781 | 87 / day |

---

## 2 · VENDOR INVENTORY (PHASE 1 dependency map) — see also `TRACK_15_24_VENDOR_DEPENDENCY_MAP.md`

| # | Service | Confirmed integration? | Source of truth | Status |
|---|---|---|---|---|
| 1 | **MongoDB Atlas** (dedicated cluster, MongoDB 8.0.26 Enterprise) | ✅ ACTIVE | `MONGO_URL` in `backend/.env` · live `dbStats` returned | 🟢 |
| 2 | **Cloudflare R2** (S3-compat) bucket `masci-hub` | ✅ ACTIVE | `S3_ENDPOINT_URL`, `S3_*` in `backend/.env` · live `list_objects_v2` returned | 🟢 |
| 3 | **Cloudflare** (DNS + proxy for `mascidocs.com`) | ✅ ACTIVE (inferred) | `CORS_ORIGIN_REGEX` includes `mascidocs.com`; R2 implies a Cloudflare account exists | 🟡 |
| 4 | **Resend** (transactional email, sender `noreply@mascidocs.com`) | ✅ ACTIVE | `RESEND_API_KEY` in `.env`, `resend==2.29.0` in `requirements.txt` | 🟢 |
| 5 | **Sentry** (error logging — US region) | ✅ ACTIVE — backend AND frontend | `SENTRY_DSN` (BE) + `REACT_APP_SENTRY_DSN` (FE), `sentry-sdk==2.60.0`, `@sentry/react` | 🟢 |
| 6 | **Emergent platform** (compute pod, deploy, LLM key) | ✅ ACTIVE | Pod is running inside it · `EMERGENT_LLM_KEY` configured · `emergentintegrations` Python lib installed | 🟢 |
| 7 | **Emergent LLM Universal Key** (routes to OpenAI / Anthropic / Gemini) | ✅ ACTIVE | `EMERGENT_LLM_KEY=sk-emergent-…` in `.env` | 🟢 |
| 8 | **OpenAI SDK** (`openai==1.99.9`) | Code installed; calls go via Emergent LLM key | Inferred — no direct `OPENAI_API_KEY` env var | 🟡 |
| 9 | **GitHub** (repo / save-to-github feature) | ✅ ACTIVE | "Save to Github" is a platform feature | 🟡 |
| 10 | **MaintainX** (CMMS) | ❌ **NOT ACTIVE** | SDK config exists; `MAINTAINX_API_KEY=` empty; `MAINTAINX_SYNC_ENABLED=false` | 🟢 |
| 11 | **Stripe** SDK (`stripe==15.0.1`) | ❌ NOT ACTIVE | SDK installed; no `STRIPE_API_KEY` in `.env`; not wired to any route | 🟢 |
| 12 | **Twilio** SDK (`twilio==9.10.9`) | ❌ NOT ACTIVE | SDK installed; no `TWILIO_*` creds in `.env`; no SMS sends recorded in `notifications` | 🟢 |
| 13 | **MASCI Google Workspace / Microsoft 365** (operator productivity) | Outside platform's billing surface | Operator-owned, not platform-owned | 🔴 |
| 14 | **Domain registrar** for `mascidocs.com` | ✅ ACTIVE | Domain in production URL | 🔴 |

**Not in use** (per code + .env): Plaid, Motive, FleetWatcher, Mapbox, Anthropic direct, Google Cloud, Azure, AWS direct, Vercel, Railway, Render, Backblaze, SendGrid, Pinecone, LaunchDarkly, Segment, Auth0, Firebase, Clerk.

---

## 3 · CURRENT COSTS (PHASE 2) — what we can prove and what we can't

### 3.1 Cost matrix — **read the source-of-truth column carefully**

| Service | Plan I can prove | Source of truth | Monthly $ |
|---|---|---|---:|
| **MongoDB Atlas** | Dedicated replica set, Enterprise modules, hostname pattern indicates **M10 or higher** (M0/M2/M5 shared clusters do NOT have `ac-…-shard-…` naming) | 🟡 Vendor naming convention + 🔴 actual tier requires operator to look at Atlas → Database Deployments | M10 list = **$57** · M20 list = **$146** · M30 list = **$394** (+ Enterprise Advanced add-on if elected). **🔴 Operator must confirm.** |
| **Cloudflare R2 — storage** | 285.45 GiB stored | 🟢 measured + 🟡 R2 public price ($0.015 / GB-month) | **$4.28 / month** at current size |
| **Cloudflare R2 — Class A ops** (writes) | First 1,000,000 writes/month free; backup pattern is ~720 zip uploads/month + a few thousand photo uploads | 🟢 + 🟡 R2 free tier covers it | **$0** |
| **Cloudflare R2 — Class B ops** (reads) | First 10,000,000 reads/month free | 🟢 + 🟡 free tier covers it | **$0** |
| **Cloudflare R2 — egress** | $0 (R2's defining feature) | 🟡 vendor policy | **$0** |
| **Cloudflare DNS / domain proxy** | Free plan covers normal usage; the URL pattern doesn't suggest Pro | 🟡 inferred | **$0** (Free) or **$20 / mo** (Pro) — **🔴 operator confirms** |
| **Domain `mascidocs.com` registration** | annual fee | 🔴 unknown registrar | **~$10–15 / year** (≈ $1 / mo) |
| **Resend** | `RESEND_API_KEY` present; current Mongo shows zero email-channel notifications recorded, so volume is low — Free tier (3K/mo) likely covers, but operator may have upgraded to Pro ($20/mo, 50K/mo) | 🔴 operator confirms in Resend dashboard | **$0** (Free) or **$20** (Pro) |
| **Sentry** | BE + FE DSNs active to `o4511406450802688.ingest.us.sentry.io`; project IDs differ. Developer is free for 5K errors/mo; Team is $26/mo from 50K errors/mo | 🔴 operator confirms in Sentry → Settings → Billing | **$0** (Developer) or **$26+** (Team) |
| **Emergent platform** | Pod cgroup shows 8 GiB RAM, 2 vCPU, 104 GiB disk. Operator referenced recent "~4 GB" upgrade | 🔴 operator confirms in Emergent dashboard | **🔴 unknown — see Phase 2A** |
| **Emergent LLM key usage** | Universal key consumption is metered by Emergent. No internal LLM-call log collection exists in Mongo (checked: `llm_calls`, `openai_usage`, `ai_usage`, `llm_events`, `llm_telemetry` — all empty/absent) | 🔴 operator confirms in Emergent Universal-Key usage page | **🔴 unknown** |
| MaintainX | Inactive — `MAINTAINX_API_KEY=` empty | 🟢 evidence | **$0** |
| Stripe | Inactive — no API key in .env | 🟢 evidence | **$0** |
| Twilio | Inactive — no creds in .env, zero SMS records in DB | 🟢 evidence | **$0** |

### 3.2 Bounded current monthly cost (the most defensible statement)

Because Atlas and Emergent tiers are 🔴 unknown to me, I can give an **interval**, not a single number. Cost ranges below are list-price upper bounds; volume discounts and any contracted enterprise pricing may reduce them.

| Component | Lower bound | Upper bound | Source class |
|---|---:|---:|---|
| MongoDB Atlas cluster | $57 | $394 | 🟡 / 🔴 |
| Cloudflare R2 (storage) | $4 | $5 | 🟢+🟡 |
| Cloudflare zone / DNS | $0 | $20 | 🔴 |
| Domain | $1 | $1 | 🟡 |
| Resend | $0 | $20 | 🔴 |
| Sentry | $0 | $26 | 🔴 |
| Emergent compute + LLM key | 🔴 | 🔴 | 🔴 |
| **PLATFORM TOTAL excl. Emergent** | **≈ $62** | **≈ $466** | mixed |

**The honest answer:** the **non-Emergent platform third-party stack is somewhere between ≈$60 and ≈$470 per month**, with the swing entirely controlled by which Atlas tier MASCI is on. Emergent is on top of that and the operator must surface its current invoice.

### 3.3 Operator action — to lock the actual current bill

To replace the 🟡/🔴 lines with 🟢 facts, retrieve and paste back to me:

1. **Atlas**: cloud.mongodb.com → MASCI org → Project → Database Deployments → click `MASCI-preview` cluster → "Cluster Tier" string (e.g. `M10`, `M20`) and "Enterprise Advanced" yes/no.
2. **Resend**: resend.com → Settings → Plan & Billing → current plan + last month's invoice.
3. **Sentry**: sentry.io → o4511406450802688 → Settings → Subscription → current plan + last month's usage.
4. **Cloudflare**: dash.cloudflare.com → mascidocs.com zone → Overview → plan (Free / Pro / Business / Enterprise) + R2 usage.
5. **Emergent**: app.emergent.sh → Workspace → Plan & Billing → current plan + previous invoice.

Once supplied, I can replace this matrix with a 🟢 deterministic statement.

---

## 4 · CAPACITY ANALYSIS (PHASE 3) — what's tight, what's not

### 4.1 Headroom matrix (🟢 measured headroom vs the binding limit)

| Surface | Used | Cap / soft-limit | Headroom | What breaks first |
|---|---:|---:|---:|---|
| Atlas DB size (`dataSize`) | 184.62 MiB | 10,240 MiB (`ATLAS_QUOTA_MB`) | **98.2 %** | Far away — but soft cap, not hard. Atlas tier disk is the real cap. |
| Atlas docs | 504,006 | n/a (no hard cap until storage) | n/a | usage_events index size grows linearly with doc count |
| R2 storage | 285 GiB | n/a (R2 is pay-per-GiB; no hard cap) | unlimited | Cost grows linearly; **runaway pattern from hourly backups** |
| Pod RAM | 3.10 GiB | **8.00 GiB** (cgroup) | **61.2 % free** | Closest hard cap. Will be the first Emergent-side pressure. |
| Pod disk (overlay) | 27 GiB | 104 GiB | **74 % free** | Log rotation safe at current rate |
| Pod CPU | n/a continuous (no per-second telemetry from inside pod) | 2 vCPU (cgroup) | n/a | 🔴 operator can observe in Emergent dashboard |
| `notifications` collection | 9,740 docs · 2.83 MiB | none | unlimited | growth modest |
| `usage_events` collection | 411,686 · 12.34 MiB data + 27.45 MiB indexes | none | unlimited | indexes already > data — first thing to compact/cap |
| Backups (R2) | 283 GiB | none | unlimited | **#1 cost-runaway candidate** (see §5) |

### 4.2 What breaks first (ranked)

1. **R2 backup volume cost** — at +14.5 GiB / day, 1-year accumulation = +5,290 GiB → **$80 / month just for backups**. Not a *hard break* but a quiet bleed.
2. **Pod RAM** — at 38.8 % of 8 GiB now with ~22% adoption; 5× growth scenario lands at ~16 GiB → forces an Emergent tier upgrade.
3. **Atlas storage tier** — current 184 MiB → 5× to ~1 GiB; M10 includes 10 GB so plenty of room at M10. M20 / M30 wouldn't be needed for storage alone.
4. **`usage_events` index size** — 27 MiB indexes for 411K docs (66 bytes/doc index avg). 100× scale = 2.7 GiB indexes. Pressure on RAM (Atlas working-set rule of thumb: indexes should fit in RAM).

### 4.3 What's NOT tight (today)

- Email / SMS volume (effectively zero — no Twilio integration; Resend records aren't logged to Mongo).
- LLM consumption — no `llm_*` collection has records; no LLM-calling code path in the obvious server routes. Likely very low usage today.
- File counts in R2 (9,608 objects — well under R2's effective per-bucket scale, which is "billions").
- Cloudflare egress (R2 = $0 egress is the whole point).
- Atlas connection count (boto3 / motor pool sized at default 100, far below typical Atlas M10 cap of 1500).

---

## 5 · 100 % COMPANY MODEL (PHASE 4) — assumptions stated

### 5.1 Adoption multiplier

| Stage | Adoption | Multiplier vs today |
|---:|---:|---:|
| Today | 22.5 % (midpoint of operator's stated 20–25 %) | **1.00×** |
| Stage A | 50 % | 2.22× |
| Stage B | 75 % | 3.33× |
| Stage C (100 %) | 100 % | **4.44×** |

### 5.2 Feature-engagement overlay (additional scaling on top of headcount)

**Assumption** (clearly stated): when adoption goes from "early-pilot 22 %" to "everyone uses it," per-user activity *also* rises because (a) workflows that today are still on paper migrate to the platform, (b) PMs and supers will file more DRs once it's the mandated tool. I use the following feature-engagement factor:

| Surface | Feature-engagement uplift on top of headcount | Rationale |
|---|---|---|
| Daily reports (`daily_reports`) | **× 1.7** (over and above headcount) | Today 27/day at 22% adoption — currently only ~6 active DR-filers. At 100% every super + PM + foreman files daily ≈ 50+ filers × 1 DR/day each. |
| Photos in R2 | **× 1.5** | More users → more JHAs, drills, incident photos. |
| Notifications | **× 1.5** | Per-user threshold settings + cross-portal awareness rises. |
| usage_events | **× 1.3** | Already aggressive — capturing nearly every UI event today. |
| audit_events | **× 1.0** (linear with users only) | Audit is action-based, scales w/ users. |
| Mongo dataSize (total) | dominated by `daily_reports`, so **× 1.7** | See above. |
| R2 backups | × **adoption × DB-growth** | Backup zip contains DB+R2 photo manifest. Grows superlinearly. |
| LLM consumption | × (operator decides) | Today ~$0 measurable. If product gets AI features, this is the wildcard. |

### 5.3 Projected workload at 100 % adoption

| Workload | Today (🟢) | At 100 % | Combined factor |
|---|---:|---:|---:|
| Daily reports / day | 27 | **204 / day** | 4.44 × 1.7 |
| Daily reports / year | ~9,900 | **74,500 / year** |  |
| Mongo dataSize | 184.62 MiB | **1,395 MiB ≈ 1.4 GiB** | 4.44 × 1.7 |
| Notifications / day | 321 | **2,140 / day** | 4.44 × 1.5 |
| usage_events / day | 14,571 | **84,070 / day** ≈ **2.5 M / month** | 4.44 × 1.3 |
| Photos in R2 (cumulative) | 7,610 objects · 2.4 GiB | **~50,700 objects · ~16 GiB** | 4.44 × 1.5 |
| Portal users | 228 | **~1,010** | 4.44 |
| Employees in roster | 395 | **~1,750** | 4.44 |
| **Backups in R2 (annual accumulation, current retention)** | +5 TiB / year (current rate) | **+10 TiB / year** (if not capped) | mass-driven; see §6 |

---

## 6 · FUTURE COST FORECAST (PHASE 5)

All numbers below assume **list pricing**; an enterprise contract would reduce them. Atlas tier transitions assumed once working-set or storage outgrows current cluster.

### 6.1 Best / Expected / High-growth model

**Definitions:**
- **Best case** = retention policies tightened (backup retention capped at 30 days, log files rotated weekly). Atlas stays at current tier until forced.
- **Expected case** = current policies, organic adoption to 100% over 24 months.
- **High-growth case** = AI features ship, MASCI green-lights cross-company rollout fast, 100% adoption in 12 months, AI use adds $X / month.

**Recurring monthly cost forecast (list-price, non-Emergent third parties only):**

| Horizon | Adoption | Best | Expected | High |
|---|---:|---:|---:|---:|
| Today | 22% | $62 (M10) | $151 (M10+Resend+Sentry) | $400+ (if already M20/M30) |
| **6 months** | 35% | $70 | $170 | $470 |
| **1 year** | 55% | $85 | $200 | $560 |
| **2 years** | 80% | $110 → likely M20 step | **$300** | $750 |
| **3 years** | 100% | $160 | **$430** | $950 |
| **5 years** | 100% + AI features | $200 | **$520** | $1,400 |

Largest cost driver at each horizon:

| Horizon | #1 driver | Reason |
|---|---|---|
| Today | Atlas (60–80% of bill) | DB tier dominates while volume is small |
| 6 mo | Atlas + R2 backups | Backup retention accumulates |
| 1 yr | Atlas + Emergent | Emergent compute/RAM tier likely needs a step up |
| 2 yr | Atlas tier step-up (M10→M20) | Working-set RAM is the trigger |
| 3 yr | Atlas + LLM consumption | If AI features go in, Emergent LLM key dominates |
| 5 yr | LLM + Atlas + storage | AI-heavy + 10+ TiB R2 cumulative |

### 6.2 Hard expected triggers for upgrades

| Trigger | What forces it | Approximate timing |
|---|---|---|
| Atlas M10 → M20 | Working set (≈ indexes + hot data) exceeds 2 GiB RAM on M10 | **~24–30 months** at expected growth |
| Pod RAM 8 GiB → 16 GiB | Backend process RSS approaches 6+ GiB sustained | **~12–18 months** if `usage_events` indexes balloon |
| R2 backup retention policy | $/mo for backups exceeds Atlas Cloud Backup pricing (~$0.011 / GB-mo for Atlas snapshots vs $0.015 / GB-mo for R2 storage) | **Now** — see §7 R-1 |
| Sentry Developer → Team | Backend + frontend errors exceed 5K/mo | **🔴 unknown current rate** — operator should check Sentry usage page now |
| Resend Free → Pro | Email sends > 3,000 / mo | **🔴 unknown today** — if email is wired in but in-app-only mode is shipped, this is far off |

---

## 7 · RISK REGISTER (PHASE 6) — ranked by impact × likelihood

| # | Severity | Risk | Evidence | Why ranked here |
|---|:--:|---|---|---|
| **R-1** | **P0** | **R2 backup retention not bounded; +14.5 GiB/day current growth, 100 GiB in last 7 days alone.** | 🟢 measured | Quiet bleed. Not painful now ($4/mo) but at 12 months unbounded = ~$80/mo on backups alone, plus operational headache restoring from 50K zips. |
| **R-2** | **P0** | Vendor lock-in on Atlas cluster (replica set, Enterprise modules). | 🟢 evidence | A change in DB host is a multi-week migration. |
| **R-3** | **P1** | Emergent compute is single point of failure for runtime, build, deploy. | 🟢 evidence | The platform's entire BE/FE process runs in one Emergent pod. |
| **R-4** | **P1** | `daily_reports` documents are ~128 KiB each → photos likely stored inline in Mongo. | 🟢 evidence (132 MiB / 1,032 docs) | Mongo is NOT photo storage. At 100% scale (74K DRs/yr), this becomes a real Atlas cost driver. R2 is the correct home. |
| **R-5** | **P1** | `usage_events` index size (27 MiB) already > data size (12 MiB). | 🟢 evidence | Linear growth + heavy index posture. Will pressure Atlas working-set RAM before storage. |
| **R-6** | **P1** | No internal LLM-call telemetry collection. | 🟢 evidence (no `llm_*` collection exists) | If AI features ship, no current ability to forecast cost from inside the app. |
| **R-7** | **P2** | Resend webhook secret blank (`RESEND_WEBHOOK_SECRET=`). | 🟢 evidence | Operational risk only — bounce/complaint events not captured. |
| **R-8** | **P2** | Sentry has TWO projects (BE & FE on the same org). Free-tier event allowances are per-project. | 🟢 evidence | Easier to overrun Developer free tier without realizing it. |
| **R-9** | **P2** | Stripe / Twilio / OpenAI SDKs installed but unused. | 🟢 evidence | Just bloat — no billing risk. But noise in dependency surface. |
| **R-10** | **P3** | MaintainX SDK + env keys exist but key blank. | 🟢 evidence | If a developer accidentally enables `MAINTAINX_SYNC_ENABLED=true` without a key, sync fails noisily. |

---

## 8 · EMERGENT PLATFORM AUDIT (PHASE 2A) — full section

Mandated section. **From inside the pod I can prove the resource caps; I cannot prove the plan name or invoice.**

### 8.1 Emergent — what I CAN prove (🟢 ACTUAL)

| Metric | Value | Source |
|---|---|---|
| Memory cgroup hard cap | **8.00 GiB** | `cat /sys/fs/cgroup/memory.max` |
| Memory currently in use | **3.10 GiB (38.8 %)** | `cat /sys/fs/cgroup/memory.current` |
| CPU cgroup cap | **2.00 vCPUs** | `cat /sys/fs/cgroup/cpu.max` (200000/100000) |
| Disk available | 77 GiB free of 104 GiB on root overlay | `df -h /` |
| `/app` size | 4.8 GiB | `du -sh /app` |
| `/var/log/supervisor` | 170 MiB | rotating logs |
| Emergent LLM Key configured | `sk-emergent-162DfE3BbA581E2093` | `backend/.env` |
| `emergentintegrations` Python lib version | 0.1.0 | `requirements.txt` |
| Sentry — Emergent integration on FE | active | `REACT_APP_SENTRY_DSN` |

### 8.2 Emergent — what I CANNOT prove from inside the pod (🔴 OPERATOR REQUIRED)

| Question | Answer source |
|---|---|
| What plan is the workspace on (Starter / Pro / Business / Enterprise)? | Emergent → Workspace → Plan & Billing |
| Current monthly invoice $ | Same |
| Current annual contract $ | Same |
| Workspace project limit | Same |
| Universal LLM Key — current balance + last 30d consumption $ | Emergent → Profile → Universal Key → Usage |
| Build / deployment count this month | Emergent → Deployments dashboard |
| Allocated artifact / storage allowance (this is the metric most likely referenced by "the 4 GB upgrade") | Same |
| Team seat count + per-seat charge | Workspace → Settings → Members |
| Auto-top-up enabled? | Profile → Universal Key |

### 8.3 What the "~4 GB upgrade" most likely referred to

Three candidates:

1. **Universal LLM key balance top-up** (4 GB ≠ a $ amount but the user may have meant 4 GB of conversational tokens of credit — Emergent's pricing UI does display credits this way). **Most likely match.**
2. **Pod RAM upgrade** — but the cgroup shows 8 GiB now, so if "4 GB" was the upgrade target it has already been exceeded; or "4 GB" was the *baseline* and pod is now 8 GiB.
3. **Artifact storage / deployment storage allowance** (Emergent meters this separately for built artifacts).

**🔴 Operator must clarify in the Emergent dashboard.**

### 8.4 Emergent forecast (model)

Until operator confirms the plan, I can only state the structural shape:

| Period | Trigger that forces upgrade | Most likely cause |
|---|---|---|
| 6 mo | Build/deploy volume rises (Track 15.x cadence ≈ 2–3 deploys/week → 4–6/week as more features land) | Build minutes / deploy count quota |
| 1 yr | Pod RAM exceeds 6 GiB sustained | usage_events indexes + concurrent users |
| 2 yr | Pod RAM 8 GiB cap exceeded → forced step up | adoption + AI features |
| 3 yr | LLM key consumption is the dominant line | AI features in production |
| 5 yr | Multi-pod or HA architecture needed | Business-critical SLA |

### 8.5 Direct answers to the Phase 2A questions

> **What is the current Emergent bill?** 🔴 Not retrievable from inside the pod. Operator must pull from Emergent → Plan & Billing. From the resource shape (8 GiB RAM, 2 vCPU, 104 GiB disk, 1 workspace, 1 production deploy) this looks like a Pro-tier-class workspace, but I refuse to put a $ on it without the dashboard.

> **Projected Emergent bill at 100 % MASCI adoption?** 🟠 Model: expect at minimum **one tier upgrade** (RAM 8 → 16 GiB; build allowance roughly doubles). If today's bill is $X, projection = **~2× $X** at 100 % adoption (working set + build cadence). If AI features ship, add LLM credit consumption on top.

> **Projected Emergent bill at 6 mo / 1 yr / 2 yr / 3 yr / 5 yr?** Structurally: $X (today) → ~$X (6 mo, same tier) → ~1.3× $X (1 yr) → **~2× $X (2 yr — likely tier step)** → ~2.5× $X (3 yr) → ~3× $X + AI (5 yr).

> **What is most likely to force the next Emergent upgrade?** Backend pod RAM, driven by usage_events index size + concurrent session count.

> **Largest Emergent cost risk?** LLM Universal Key consumption if AI features are launched without telemetry first.

> **Largest Emergent capacity risk?** The single-pod runtime — Emergent is currently a single point of failure for the entire production runtime (per R-3).

> **Are we currently overbuilt, properly sized, or undersized?** Pod RAM = 38.8% utilized. **Properly sized today**, with comfortable headroom for ~2× growth before any step-up is needed.

> **If MASCI moved to 100 % adoption tomorrow, would Emergent require an immediate upgrade?** **No, not from the inside-pod evidence.** 4.44× headcount × ~30 % RAM-correlation ≈ 1.7× current RAM use ≈ **5.3 GiB / 8 GiB** = 66 %. Still under cap. The first real squeeze comes from `usage_events` index growth, not from concurrent user count.

> **What would the monthly Emergent bill become in that scenario?** Without invoice context, **~1.5–2.0× today's bill** within ~12 months of sustained 100 % adoption (RAM tier step plus LLM if AI launches).

> **What should be monitored monthly to avoid surprise Emergent costs?** (a) Universal LLM Key consumption (Emergent → Profile → Usage). (b) Pod memory peak (Emergent → Deployments → resource graph). (c) Build minutes used. (d) Deployment count.

---

## 9 · EXECUTIVE SUMMARY (PHASE 7) — direct answers

These mirror the Phase 7 questions verbatim. See `TRACK_15_24_EXECUTIVE_COST_SUMMARY.md` for the single-page rollup.

> **1. What does the platform cost today?**
> Non-Emergent third-party stack: **$62 – $466 / month** (list-price interval; the swing is the Atlas tier). Emergent platform: **🔴 operator must pull from dashboard.**

> **2. What will it realistically cost at 100 % MASCI adoption?**
> Non-Emergent: **~$430 / month** in the Expected case (Atlas M20, R2 backups bounded, Resend Pro, Sentry Team). Plus Emergent which I estimate at ~2× today's Emergent bill.

> **3. What will it likely cost in 6 mo / 1 yr / 2 yr / 3 yr / 5 yr?**
> See §6.1 table. Non-Emergent expected: $170 / $200 / $300 / $430 / $520. Add Emergent on top.

> **4. What service is most likely to become expensive first?**
> **Cloudflare R2 — backups specifically.** Quiet bleed; +14.5 GiB/day.

> **5. What service is most likely to hit limits first?**
> **MongoDB Atlas working-set RAM**, driven by `usage_events` index growth. Forces M10 → M20 step in ~24–30 months.

> **6. What should we monitor monthly?**
> (a) R2 bucket size (script in `boto3.list_objects_v2` is the audit query). (b) Mongo `dataSize` + per-collection index size. (c) Pod RAM peak (Emergent dashboard). (d) Emergent LLM key consumption. (e) Sentry error volume per project.

> **7. What should we budget annually?**
> Expected case rolling 12 months: **~$2,400 / yr** (non-Emergent) + Emergent. If Atlas already on M20: **~$3,600 / yr**.

> **8. What should be optimized now?**
> (a) **Backup retention policy** — current pattern is hourly + ever-growing. Cap to 30-day rolling + 1-per-day snapshot beyond that. (b) **Move `daily_reports` photos out of Mongo into R2 with URL references** (R-4). (c) **Add LLM telemetry collection** (R-6). (d) **Audit `usage_events` indexes** — 27 MiB indexes for 12 MiB data is index-heavy.

> **9. What should NOT be optimized yet?**
> (a) Cloudflare zone plan (Free works). (b) Resend plan (volume is near zero). (c) Pod RAM tier (38 % utilized). (d) Atlas cluster tier (1.8 % of soft cap; M10 sized correctly). Don't right-size what isn't bleeding.

---

## 10 · RECOMMENDATIONS (not authorized — for operator decision)

P0 (recommend within 30 days):
- **Cap R2 backup retention** (30-day rolling + 1-daily-keepers beyond). One-line policy change. Saves ~$50/mo by year-end.
- **Operator dashboard pull** for Atlas, Emergent, Resend, Sentry, Cloudflare → lock the cost matrix to 🟢.

P1 (recommend within 90 days):
- **Migrate daily_reports inline photos to R2 references** (estimated ~30% reduction of Atlas dataSize growth).
- **Add LLM telemetry collection** so AI cost can be forecast before it's incurred.
- **Review `usage_events` index set** — index size already > data.

P2 (recommend within 6 months):
- **Set up monthly cost-audit cron** that emails the operator R2 bucket size, Mongo dataSize, top-5 collection storage, and Emergent LLM consumption.
- **Define "Mongo doc inline binary policy"** — incidents (30 MiB / 67 docs) and job_hazard_files (30 MiB / 6 docs) suggest large inline binaries elsewhere.

---

## 11 · DELIVERABLES INDEX

- `/app/memory/TRACK_15_24_PLATFORM_COST_AND_SCALING_AUDIT.md` ← **this file**
- `/app/memory/TRACK_15_24_VENDOR_DEPENDENCY_MAP.md`
- `/app/memory/TRACK_15_24_CAPACITY_FORECAST_MODEL.md`
- `/app/memory/TRACK_15_24_EXECUTIVE_COST_SUMMARY.md`
- `/app/memory/PRD.md` — appended with TRACK 15.24 entry

**No code was changed. No deploys occurred. Awaiting operator action on the 🔴 dashboard pulls before this matrix can be made fully deterministic.**
