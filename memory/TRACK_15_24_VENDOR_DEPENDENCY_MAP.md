# TRACK 15.24 — VENDOR DEPENDENCY MAP

**Date:** 2026-06-18
**Scope:** Every third-party service the MASCI platform code/config touches.
**Source-of-truth labels:** 🟢 measured · 🟡 vendor list price · 🟠 model · 🔴 operator-required.

---

## A · ACTIVE vendors (confirmed in code AND configured)

| Service | Purpose | Env(s) | Plan (proven) | Plan (must confirm) | Monthly $ (list) | Annual $ (list) | Limits | Current usage | Headroom | Owner | Criticality | Risk if removed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **MongoDB Atlas** | Primary database (`masci_safety_preview`) | preview + production | Dedicated replica set, Enterprise modules, host pattern `ac-cz4whli-shard-00-XX` → **M10 or higher** | 🔴 exact tier | $57 (M10) · $146 (M20) · $394 (M30) | $684 / $1,752 / $4,728 | M10: 10 GB storage / 2 GB RAM · M20: 20/4 · M30: 40/8 | 🟢 `dataSize` = 184.62 MiB · 504,006 docs · 177 collections · index 51.86 MiB | **≈ 98 %** vs `ATLAS_QUOTA_MB` soft cap | MASCI (operator) | **P0 — system of record** | Total outage. No fallback. |
| **Cloudflare R2** | Object storage — backups + photos | preview + production | Pay-as-you-go | 🔴 confirm | $4.28 / mo at current size | $51.36 | $0.015/GB-mo storage; 1M Class A free; 10M Class B free; $0 egress | 🟢 285.45 GiB total · 9,608 objects | Unlimited | MASCI | **P0 — backups + media** | Loss of backups + JHA photos + drill photos. Catastrophic. |
| **Cloudflare zone** for `mascidocs.com` | DNS, proxy, TLS | production | 🔴 confirm Free / Pro / Business | 🔴 confirm | $0 (Free) / $25 (Pro) / $200 (Biz) | $0 / $300 / $2,400 | per-plan | unknown | unknown | MASCI | **P1 — DNS / TLS** | Domain unreachable. |
| **Domain registration** (`mascidocs.com`) | Domain | production | 🔴 registrar unknown | 🔴 confirm | ~$1 | ~$10–15 | n/a | n/a | renewal date unknown | MASCI | **P0** | Domain expires → total outage at renewal. |
| **Resend** | Transactional email (`noreply@mascidocs.com`) | preview + production (`RESEND_API_KEY` active) | 🔴 confirm (Free 3K/mo or Pro 50K $20) | 🔴 confirm | $0 / $20 / higher | $0 / $240+ | Free 3K, Pro 50K, Scale 100K+ | 🟢 0 email-channel notifications recorded in Mongo (Resend events not captured) — likely low | unknown | MASCI | **P1 — alerts / reports** | Outage alerts + backup emails stop. |
| **Sentry** (BE project ID `4511406478983168`, FE project ID `4511406552383488`, org `o4511406450802688` US) | Error logging | preview + production | 🔴 confirm (Developer free / Team $26 / Business $80+) | 🔴 confirm | $0 / $26+ | $0 / $312+ | Dev: 5K errors/mo; Team: 50K | unknown | unknown | MASCI | P2 | Observability degraded; not customer-facing. |
| **Emergent platform** | Build · deploy · runtime · LLM-key broker | preview + production | 🔴 confirm plan | 🔴 confirm | unknown | unknown | per-plan | 🟢 8 GiB RAM cap / 38.8% used · 2 vCPU · 104 GiB disk / 26% used | RAM 61% free · disk 74% free | MASCI | **P0 — sole runtime** | Total outage. |
| **Emergent Universal LLM Key** (`sk-emergent-162DfE3BbA581E2093`) | OpenAI / Anthropic / Gemini calls | both | usage-based, consumed against workspace credits | 🔴 confirm balance | depends on usage | depends on usage | per-credit | 🟢 no `llm_*` log collection populated → effectively zero detectable LLM use today | unknown | MASCI | P3 today; **rising** | No customer-facing AI right now. |
| **GitHub** (Save-to-Github feature) | Source backup, integrations | both | n/a (Emergent-mediated) | 🔴 confirm | $0 or org-paid | $0+ | n/a | n/a | n/a | MASCI | P3 | None for runtime — affects developer workflow. |

---

## B · CONFIGURED in code but NOT ACTIVE (no API key / disabled)

| Service | SDK installed? | Why inactive | Activation cost when wired | Risk if accidentally enabled |
|---|---|---|---|---|
| **MaintainX** | n/a (HTTP-only in config) | `MAINTAINX_API_KEY=` empty, `MAINTAINX_SYNC_ENABLED=false`, `MAINTAINX_WRITE_ENABLED=false` | Vendor confirms | If `MAINTAINX_SYNC_ENABLED=true` is set without a valid key, sync loop fails noisily. |
| **Stripe** | `stripe==15.0.1` | No `STRIPE_API_KEY` env var; no route imports it | Per-transaction | None — code path dormant. |
| **Twilio** | `twilio==9.10.9` | No `TWILIO_*` creds; zero SMS records in Mongo | SMS metered per-segment | None today. |
| **OpenAI** (direct) | `openai==1.99.9` | Used via Emergent LLM key; no direct `OPENAI_API_KEY` env var | Goes through Emergent | None — usage flows through Emergent meter. |

---

## C · NOT in code, NOT in use (rule-out list)

For each of these the platform has **zero** evidence (no env var, no SDK in `requirements.txt`/`package.json`, no route reference): Plaid, Motive, FleetWatcher, Mapbox, SendGrid, Backblaze, AWS direct (only via R2 S3-compat), Azure, Google Cloud, Vercel, Railway, Render, Pinecone, LaunchDarkly, Segment, Intercom, Amplitude, Mixpanel, Datadog, New Relic, Algolia, Clerk, Auth0, Supabase, Firebase, Anthropic direct.

---

## D · Dependency graph (text rendering)

```
mascidocs.com (domain)
   │
   └── Cloudflare zone (DNS + TLS + proxy)
          │
          ├── Emergent pod (FE + BE runtime · 8 GiB RAM · 2 vCPU)
          │      │
          │      ├── MongoDB Atlas dedicated cluster (atlas-5p2de4)
          │      │      └── DB `masci_safety_preview` (177 collections · 504K docs · 184 MiB)
          │      │
          │      ├── Cloudflare R2 bucket `masci-hub` (285 GiB · 9.6K objects)
          │      │
          │      ├── Resend (email API · sender noreply@mascidocs.com)
          │      │
          │      ├── Sentry (US ingest · 2 projects: BE 4511406478983168 / FE 4511406552383488)
          │      │
          │      └── Emergent Universal LLM Key (OpenAI / Anthropic / Gemini broker)
          │
          └── (browser sessions)
```

---

## E · Single-points-of-failure (SPOFs)

- **Emergent pod** — entire runtime is one pod. Recommended mitigation: confirm Emergent's failover SLA in their dashboard. P0 SPOF.
- **MongoDB Atlas cluster** — the 3-node replica set is HA inside Atlas, but the platform has no cross-region failover. P0 dependency.
- **Cloudflare R2 bucket** — single-region (R2 buckets are auto-replicated, but bucket-level deletion is irreversible). P1.
- **`mascidocs.com` domain registration** — annual renewal. P0 if forgotten.
- **Sentry org `o4511406450802688`** — if disabled, errors silently stop reporting. P3 but should be alerted.
