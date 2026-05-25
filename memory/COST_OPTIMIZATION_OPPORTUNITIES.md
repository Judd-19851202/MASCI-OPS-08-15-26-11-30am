# COST_OPTIMIZATION_OPPORTUNITIES.md
## MASCI Operations Platform · Phase 27 · Safe Cost Optimization Catalog
## iter428 · 2026-05-25

---

## Doctrine

Every optimization in this catalog must satisfy:

- ✅ does NOT reduce operational continuity
- ✅ does NOT reduce disaster-survivability
- ✅ does NOT reduce field usability
- ✅ does NOT reduce backup integrity
- ✅ does NOT reduce restore integrity
- ✅ does NOT add ERP-style features or admin UI

If an optimization fails any of those, it's not in this catalog. Cost is the goal; integrity is the floor.

---

## TIER 1 — Operator actions (zero engineering · do this week)

### 1.1 · Set R2 bucket lifecycle rule 🟢 highest-leverage

**Action:** Cloudflare R2 dashboard → bucket `masci-hub` → Settings → Object lifecycle rules → add rule:
- Name: `backup-30day-purge`
- Prefix: `backups/`
- Action: Delete after 30 days

**Saves:** ~$0.50/mo today · up to $50/mo at full adoption (prevents R2 storage from growing unbounded).

**Risk:** zero — the 30-day window matches the existing operational doctrine that local backup retention is 14 days. R2's 30-day window is generous.

**Time:** 3 minutes.

---

### 1.2 · Set Universal LLM key auto-top-up cap

**Action:** Emergent dashboard → Profile → Universal Key → set auto-top-up to $25/mo cap (or whatever budget is comfortable).

**Saves:** prevents AI-feature scope-creep from silently consuming $100+/mo.

**Risk:** zero — if you ever need more, you raise the cap manually.

**Time:** 2 minutes.

---

### 1.3 · Verify Atlas IP allowlist post-migration

**Action:** Atlas dashboard → Security → Database & Network Access → Network Access → replace `0.0.0.0/0` with the **Emergent egress IPs only**.

**Saves:** $0 in direct cost but eliminates the single biggest security/cost-incident risk (compromised key + open allowlist = adversary-driven egress).

**Risk:** Emergent egress IPs need to be sourced from the Emergent deployment dashboard. Until that's verified, keeping `0.0.0.0/0` temporarily is fine (admin + password protect the cluster).

**Time:** 5 minutes once IPs are in hand.

---

### 1.4 · Atlas database-user password rotation

**Action:** Atlas dashboard → Security → Database & Network Access → Database Users → edit `admin_db_user` → autogenerate new password → copy → update MONGO_URL env var in **both** preview `.env` and Emergent production env vars → redeploy production.

**Why:** the original password was shared in chat / pasted in scripts.

**Saves:** $0 direct cost · prevents the cost of a credential-leak incident.

**Risk:** very low — just be sure the new password lands in both preview and production env vars before the redeploy.

**Time:** 10 minutes.

---

## TIER 2 — Targeted engineering (1–2 days · highest financial leverage)

### 2.1 · 🟢 PHASE 27.1 · Operational attachment R2 cold-storage offload

**The biggest single financial optimization in the platform's life.**

**The problem:** today's iter417 design stores photo bytes inline as `data_b64` inside Mongo. At full MASCI adoption (~240 photos/day), Mongo grows ~5.7 GB/month. M10 (10 GB) is breached in Month 3–4 of full adoption.

**The fix:** for each new operational_attachment:
1. Upload raw bytes to R2 at `attachments/{uuid}/{filename}`
2. Store only `{r2_key, mime, sha256, thumb_b64}` in the Mongo doc (thumb_b64 is a small 200×200 preview · ~20 KB)
3. On render, frontend fetches photo bytes via signed R2 URL (egress is free)
4. Existing iter417 + iter418 + iter426 byte-round-trip tests adapt to assert `r2_key` round-trip instead of `data_b64` round-trip

**Net effect on Atlas Mongo size at full adoption:** **~3 GB instead of ~85 GB**. Atlas stays on M10 ($57/mo) **indefinitely** instead of cliff-jumping to M20 ($148/mo) in Year 1, M30 ($336/mo) by Year 2.

**6-year savings: ~$15,000–$20,000.**

**Engineering complexity:** 1–2 days · one route file + one upload helper + one frontend tweak + one migration script for existing 68 placeholder docs.

**Risk:** zero — R2 round-trip is already proven by the backup pipeline (iter425/426). This optimization just promotes R2 from "backup-only" to "primary attachment store."

---

### 2.2 · 🟢 Tighten `usage_events` TTL (90 days → 30 days)

**Today:** 90-day TTL keeps ~4.5M docs steady-state ≈ 720 MB at full adoption.

**Optimized:** 30-day TTL keeps ~1.5M docs steady-state ≈ 240 MB at full adoption.

**Net effect:** ~480 MB less Atlas storage at full adoption. Comfortable headroom on M10.

**Engineering complexity:** trivial — change `expireAfterSeconds=7776000` to `2592000` in the `usage_events` TTL setup line.

**Risk:** lose the ability to look back > 30 days at API usage for analytics. Operationally negligible — the platform doesn't currently use historical usage_events for any operational decision.

**Time:** 1 line change · 1 redeploy.

---

### 2.3 · 🟡 Add a stale `dispatch_driver_sessions` reaper

**Today:** 128 docs (low). At full adoption, ~250/year accumulating without TTL.

**Optimized:** add 90-day TTL OR a daily cron that deletes sessions where `last_seen_at < now - 90d`.

**Net effect:** prevents a low-volume collection from accumulating forever.

**Engineering complexity:** trivial — add TTL index in the dispatch driver session bootstrap.

**Risk:** zero · operational sessions don't need to live forever.

**Time:** 1 line change.

---

### 2.4 · 🟡 Compress backup archive at higher zip level

**Today:** archive is built with `zipfile.ZIP_DEFLATED` default compression level (`-1` ≈ level 6).

**Optimized:** level 9 (`zlib.Z_BEST_COMPRESSION`).

**Net effect:** ~5–10 % smaller archives (typical) — saves ~5–9 MB per 90 MB archive. Trade-off: ~2× CPU during compression.

**Engineering complexity:** trivial — pass `compresslevel=9` to `zipfile.ZipFile`.

**Risk:** zero · backup-restore is unaffected.

**Time:** 1 line change.

**Verdict: NOT WORTH IT.** Savings are 5–10 GB/mo × $0.015 = $0.07–$0.15/mo. Not worth the CPU. **Skip this one.**

---

## TIER 3 — Architectural patience (DO NOT do prematurely)

### 3.1 · ❌ Don't migrate off Cloudflare R2 to S3

R2's egress-free pricing is unique in the market. Migrating would cost $50–$100/mo just in S3 egress at full adoption.

### 3.2 · ❌ Don't downgrade Atlas from M10 → M0 to save $57

At full adoption M0 is structurally insufficient (512 MB cap). The $57 saved is overwhelmed by the productivity loss of constant DB pressure incidents.

### 3.3 · ❌ Don't add a "tiny cron job" service for one job

Background work runs in-process via FastAPI. Adding any cron-as-a-service (Cron-job.org, EasyCron, etc.) introduces a new vendor for no operational gain.

### 3.4 · ❌ Don't add a CDN in front of `mascidocs.com`

You're already on Cloudflare CDN. Adding another CDN (Fastly, CloudFront) doubles costs for zero gain.

### 3.5 · ❌ Don't migrate off Emergent runtime "to save money" today

The cost gain over Render/Railway/Fly is marginal ($20–$50/mo). The migration time would be at least one weekend of engineering. Wait until the platform itself outgrows Emergent's tier (which it has not).

---

## Tier 4 — Future-state optimizations (after Year 2 full adoption)

### 4.1 · Archive operational_attachments older than 18 months to R2 Glacier-tier equivalent

R2 doesn't have a Glacier tier today (single price band). But Cloudflare has announced cold-storage tiers in development. If/when they ship, photos older than 18 months are cold-archive candidates — saves ~50 % R2 cost at year-3+ scale.

### 4.2 · Compress training videos to lower bitrate

Today `/app/backend/static/training-videos` is 300 MB. At higher compression with the same operational readability, this drops to ~150 MB. Saves nothing on R2 (free tier covers it) but reduces every backup archive by ~150 MB.

### 4.3 · Move `__pycache__` and `node_modules` out of the backup zip

Already excluded — verify by checking the archive contents.

---

## Estimated annualized savings if Tier 1 + 2.1 + 2.2 are adopted

| Optimization | Savings / yr |
|---|---|
| R2 lifecycle rule | ~$200–$600 / yr at full adoption |
| Universal Key cap | prevents $500–$1,500 / yr in scope-creep risk |
| Photo cold-storage (Phase 27.1) | $1,000–$2,000 / yr starting Year 2 · scales to ~$3,500 / yr by Year 5 |
| Tighter usage_events TTL | $0 direct · delays Atlas tier cliff by ~6 months |
| **Combined annualized savings (Year 2+)** | **~$1,200–$2,600 / yr** |

---

## Recommendation priority order

1. 🟢 **R2 bucket lifecycle rule** (operator · 3 min · do this week)
2. 🟢 **Universal Key auto-top-up cap** (operator · 2 min · do this week)
3. 🟢 **Atlas database-user password rotation** (operator · 10 min · do this week)
4. 🟢 **Atlas IP allowlist tightening** (operator · 5 min · once Emergent egress IPs are sourced)
5. 🟡 **Phase 27.1 photo R2 cold-storage** (engineering · 1–2 days · do before MASCI photo flow lands in production)
6. 🟡 **Tighter usage_events TTL** (engineering · 1 line · bundle with Phase 27.1)

---

## Verdict

🟢 **Five operator actions and one engineering pass (Phase 27.1) capture the entire material cost optimization surface.** Everything beyond that is premature or counter-productive. The platform is optimization-efficient by architecture, not by accident.

---

End of Cost Optimization Opportunities.
