# MASCI_FULL_SCALE_FORECAST.md
## MASCI Operations Platform · Phase 27 · Full-Adoption Cost Forecast
## iter428 · 2026-05-25

---

## Sizing model — heavy civil construction operational reality

This model is built on the real shape of MASCI's operating profile. NOT generic SaaS assumptions.

| Anchor variable | Reality |
|---|---|
| Total employees | **258** (live count in `employees` collection today) |
| Field crews (drivers + operators + foremen + truck bosses) | ≈ 180 |
| Office staff (PM · safety · HR · admin · accounting · dispatch · shop) | ≈ 78 |
| Active jobsites at peak season | ≈ 8–15 simultaneous |
| Daily DVIRs / pre-ops / equipment-issuance / inspection forms | ≈ 1 per active driver per shift = ~180 |
| Daily field reports filed | ≈ 1 per foreman per day = ~25 |
| Daily breakdowns + recovery events | ≈ 1–3 |
| Daily photo proofs captured (DVIRs + breakdowns + jobsite docs) | ≈ 30 per active crew × 8 active crews = ~240 photos |
| Average mobile-captured photo size (iOS / Android default) | ≈ 600 KB |
| Daily dispatch assignments created | ≈ 30 |
| Daily training-record / signoff events | ≈ 20 |
| Auth events per day (sign-ins + passkey + session refreshes) | ≈ 1,500 (most users sign in once + passkey re-auth + token refresh × 258 employees) |
| Operational shift hours / day | 12 |
| Workdays per year | 250 |

---

## Daily operational write volume at full adoption

| Class | Per day | Per month | Per year |
|---|---|---|---|
| DVIR / pre-op / inspections | 180 docs | 5,400 | 64,800 |
| Field reports (FL records) | 25 docs | 750 | 9,000 |
| Operational attachments (photos) | 240 docs / day | 7,200 / month | **86,400 / year** |
| Operational attachment bytes (raw) | 240 × 600 KB ≈ 144 MB / day | 4.3 GB / mo | **51.5 GB / year** |
| Operational attachment bytes (base64 in Mongo) | ≈ 192 MB / day | 5.7 GB / mo | **68.6 GB / year** |
| Dispatch assignments | 30 docs / day | 900 / mo | 10,800 / yr |
| Continuity events | ~100 / day | 3,000 / mo | 36,000 / yr |
| Audit events | ~150 / day | 4,500 / mo | 54,000 / yr (TTL 30 days = steady-state ~4,500) |
| usage_events at full adoption | ~50,000 / day (250×observed scale-up factor) | 1.5M / mo | 90-day TTL → steady-state ~4.5M docs ≈ 720 MB |
| Sign-in / auth events | ~1,500 / day | 45,000 / mo | n/a (no persistence — token-based) |

---

## MongoDB Atlas — projected size at full adoption

| Component | Steady-state size at full adoption | Notes |
|---|---|---|
| `usage_events` (90-day TTL) | ~720 MB | dominant raw size · TTL-bounded |
| `operational_attachments` (no TTL — operational truth) | ~5.7 GB / month accumulation · ~68 GB / year | base64 inflation 4/3 vs raw bytes |
| `dispatch_assignments` (permanent) | ~30 MB / year | small text records |
| `audit_events` (30-day TTL) | ~25 MB | TTL-bounded |
| `field_leadership_records` | ~150 MB / year | structured text + photo refs |
| `notifications` (per-doc TTL) | ~10 MB steady-state | self-cleaning |
| `tasks` | ~30 MB / year | operational record |
| Other 100+ small collections | ~50 MB | misc operational truth |
| **Total Atlas size at year 1 full adoption** | **~70–75 GB** | |

→ Atlas M0 (512 MB) cliff lands around **Day 30–60** of full adoption.
→ Atlas M10 (10 GB) cliff lands around **Month 4–5** of full adoption.
→ Atlas M20 (20 GB · $148/mo) cliff lands around **Month 10–12**.
→ Atlas M30 (40 GB · $336/mo) needed by **Year 1.5**.

**Mitigation**: 90-day archival rotation of `operational_attachments` to R2 cold storage (with `r2:` reference in Mongo doc, photo bytes in R2). This keeps Atlas size to **~1.5–3 GB** steady-state. Cost: M10 forever ($57/mo). See `COST_OPTIMIZATION_OPPORTUNITIES.md`.

---

## Cloudflare R2 — projected storage at full adoption

| Stream | Per month | Per year |
|---|---|---|
| Hourly archives (24 × 30 = 720 / mo · ~150 MB each at full adoption) | ~108 GB / mo if no lifecycle rule | ~1.3 TB / yr if no rule |
| With 30-day lifecycle rule | **~108 GB steady-state** | $1.65 / mo |
| Cold-storage photo backing (if Atlas optimization above is adopted) | growth ~5.7 GB / mo · ~68 GB / year | $1 / mo year 1 · scaling linear |

R2 cost at full adoption with both lifecycle rules and photo cold-storage: **~$3–$5 / mo**.

---

## Resend — projected email volume at full adoption

| Stream | Per month |
|---|---|
| Weekly safety digest × 78 office + 8 foreman = 86 recipients × 4 weeks | 344 |
| Weekly PO digest × 6 recipients × 4 weeks | 24 |
| Daily AM-roll-call digest (if enabled later · 25 recipients × 30 days) | 750 |
| Password resets / forgot password | ~50 |
| Alert / outage notifications | ~20 |
| Backup-email after manual archive | ~30 |
| Per-user welcome / onboarding emails | ~30 |
| **Total / mo at full adoption** | **~1,250** — well within Resend free 3,000 / mo |

If daily-digest is fully rolled out for all 258 employees, that bumps to ~8,000 / mo and crosses into Resend Pro = **$20 / mo**.

---

## Sentry — projected error volume at full adoption

| Stream | Per month |
|---|---|
| 258 active employees × low error rate (~5 per user per month at steady state) | ~1,290 |
| Plus background backend errors (~50 / mo) | ~50 |
| **Total / mo at full adoption** | **~1,340** — within Sentry free 5,000 |

Sentry remains $0 at full adoption.

---

## Universal LLM key (if AI features stay opt-in)

Today: **$0** (no AI features active).

If MASCI elects to enable any of:

| Feature | Estimated monthly LLM cost |
|---|---|
| Phase B OCR for legacy paper-form imports (one-time historical, mostly done) | < $20 — one-off |
| AI-assisted dispatch suggestions | $20–$50 / mo (gpt-4o-mini routing) |
| AI safety-report summarization (weekly digest helper) | $5–$15 / mo (claude-haiku) |
| AI translation real-time (EN ↔ ES) for free-text fields | $10–$30 / mo |
| AI image categorization (label DVIRs by defect type) | $30–$80 / mo |

**Maximum reasonable LLM budget at full adoption (if every AI feature is enabled): ~$200 / mo.**
**Current realistic LLM budget: $0–$30 / mo for one or two helpful features.**

---

## Full-adoption monthly cost model

| Scenario | $ / mo | $ / yr | Notes |
|---|---|---|---|
| **Full adoption · no AI · base hardening** (Atlas M10 + Resend free + R2 paid + Sentry free) | **$60–$70** | $720–$840 | Atlas $57 + R2 $1–$3 + Sentry $0 + Resend $0 + domains $2.50 |
| **Full adoption + daily-digest mode** (Resend Pro at $20) | $80–$90 | $960–$1,080 | + $20 Resend |
| **Full adoption + one helpful AI feature** | $90–$110 | $1,080–$1,320 | + $20–$30 LLM |
| **Full adoption + every AI feature** | $200–$280 | $2,400–$3,360 | + $150–$200 LLM |

**Most likely operating cost at full MASCI adoption: $60–$120 / mo · $720–$1,440 / yr.**

---

## Operational cost normalized

| Lens | Today | Pilot stage | Full adoption |
|---|---|---|---|
| $ / month | $2.50 | $5 | $60–$120 |
| Annual run rate | $30 | $60 | $720–$1,440 |
| $ / active user / mo | $2.50 (denom = 1) | $0.20 (25 users) | $0.23–$0.47 (258 users) |
| Cost vs single ERP seat ($150 / mo industry benchmark) | 0.017 % | 0.13 % | 0.16–0.31 % of one seat |
| **Cost as fraction of typical heavy-civil ERP spend ($150 × 258 = $38,700 / mo)** | 0.006 % | 0.013 % | **0.15–0.31 %** |

---

## Comparison with industry equivalents

| Platform | Per-user-per-month | Annual at MASCI scale (258 users) |
|---|---|---|
| HCSS HeavyJob / HeavyBid | $80–$150 | $248k–$465k |
| Vista by Viewpoint | $100–$200 | $310k–$619k |
| Procore | $100–$200 | $310k–$619k |
| Acumatica Construction Edition | $150–$300 | $465k–$929k |
| **MASCI Operations Platform (full adoption)** | **$0.23–$0.47** | **$720–$1,440** |

**Order-of-magnitude savings is real, but only because:**
1. The architecture is calm-doctrine (no ERP feature bloat) → no per-feature licensing
2. Every dependency is on a hard-cap free or low-tier paid plan
3. The platform is **owned**, not rented per seat
4. R2 egress-free architecture eliminates the typical scaling-bandwidth tax

---

## Verdict

🟢 **Even at full 258-employee adoption, the platform costs less than a single Vista seat. The financial leverage of this architecture is extraordinary, and it does not degrade with scale.**

---

End of Full-Scale Forecast.
