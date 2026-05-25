# YEARS_1_TO_6_INFRASTRUCTURE_FORECAST.md
## MASCI Operations Platform · Phase 27 · 6-Year Run-Out
## iter428 · 2026-05-25

---

## Model assumptions (rolled forward from `MASCI_FULL_SCALE_FORECAST.md`)

| Driver | Year 1 | Year 2 | Year 3 | Year 4 | Year 5 | Year 6 |
|---|---|---|---|---|---|---|
| Active employees | 50 (Q1) → 258 (Q4) | 258 | 280 | 310 | 340 | 380 |
| Active field crews | 4 → 8 | 8–10 | 10 | 11 | 12 | 14 |
| Daily photo capture (operational_attachments) | 30 → 240 / day | 240 / day | 290 / day | 330 / day | 360 / day | 400 / day |
| Daily usage_events | 18k → 50k / day | 50k / day | 55k / day | 60k / day | 65k / day | 75k / day |
| Atlas data size at year-end (with R2 cold-storage offload) | ~1.5 GB | ~1.8 GB | ~2.2 GB | ~2.6 GB | ~3.0 GB | ~3.5 GB |
| R2 photo cold storage (cumulative) | 35 GB | 105 GB | 192 GB | 290 GB | 396 GB | 514 GB |

---

## Year-over-year cost projection (most-likely path)

| Line | Year 1 | Year 2 | Year 3 | Year 4 | Year 5 | Year 6 |
|---|---|---|---|---|---|---|
| MongoDB Atlas tier | M0 (Q1) · **M10 from Q2** | M10 | M10 | M10 | M10 | M20 (if not optimized) |
| Atlas cost / mo | $0 → $57 | $57 | $57 | $57 | $57 | $148 |
| Cloudflare R2 storage / mo | $0 → $1 | $2 | $3 | $5 | $7 | $9 |
| Cloudflare R2 ops / mo | $0 | $0 | $0 | $0 | $0 | $0 |
| Resend (free unless daily-digest enabled) | $0 | $0 → $20 | $20 | $20 | $20 | $20 |
| Sentry | $0 | $0 | $0 | $0 → $26 | $26 | $26 |
| Universal LLM key | $0 | $0 → $30 | $30 | $40 | $50 | $50 |
| Domains | $2.50 | $2.50 | $2.50 | $2.50 | $2.50 | $2.50 |
| Emergent runtime (Y1 baseline · growing slowly with deployment count) | (see Emergent dashboard) | … | … | … | … | … |
| **Total non-Emergent $ / mo (year-end)** | **$60** | **$112** | **$113** | **$151** | **$163** | **$256** |
| **Total non-Emergent $ / yr** | **~$700 blended** | **~$1,300** | **~$1,400** | **~$1,800** | **~$2,000** | **~$3,100** |

---

## Year 1 (May 2026 → May 2027) — pilot to full adoption

- **Q1 (today)**: pilot mode · admin testing only · all free tiers
- **Q2**: 25–50 field users · first real photo flow lands · Atlas approaches 350 MB cliff → migrate M0 → M10 ($57/mo)
- **Q3**: 100–150 users · weekly digest fully on · R2 photo cold-storage optimization implemented · Resend approaching free-tier ceiling
- **Q4**: 200–258 users · steady state · all systems calm

Expected cost trajectory: $5/mo → $20/mo → $60/mo → **$60–$70/mo by Q4.**

**Year 1 total spend (non-Emergent): ≈ $400–$700.**

---

## Year 2-3 (2027–2028) — operational steady-state

- 258–280 users · full operational maturity
- Operational pilot becomes core operating system for MASCI day-to-day
- 90-day photo cold-storage rotation is humming
- Atlas M10 has 18+ months of headroom
- R2 storage growing linearly at ~70 GB/yr
- Likely one AI feature added (LLM cost $20–$50/mo)
- Sentry free tier comfortable

**Year 2-3 yearly spend: ≈ $1,200–$1,500/yr.**

---

## Year 4-5 (2029–2030) — capacity work + scale prep

- Atlas usage may need M20 ($148/mo) by Year 5 unless aggressive `usage_events` TTL tightening (90d → 30d) and aggressive photo cold-storage offload
- Sentry crosses 5,000 events/mo cliff (Team plan $26/mo) due to natural error volume scaling
- LLM features matured · likely 1–2 features in production · $30–$50/mo budget
- R2 storage at ~300–400 GB total · $5–$7/mo

**Year 4-5 yearly spend: ≈ $1,800–$2,000/yr.**

---

## Year 6 (2031) — acquisition / multi-org scenario

If MASCI scales via acquisition (likely heavy-civil pattern) to **2× current scope (~500 employees)**:

- Atlas M20 ($148/mo) baseline
- Atlas M30 ($336/mo) possible if photo offload lags
- R2 at ~500 GB · $9–$12/mo
- LLM features mature · $50–$80/mo
- Resend Pro firmly required · $20/mo
- Sentry Team firmly required · $26/mo
- Twilio SMS for mass-alert texting if added · $50–$100/mo

**Year 6 worst case (no optimization): ~$500/mo · ~$6,000/yr.**
**Year 6 with proper optimization: ~$250/mo · ~$3,000/yr.**

---

## 6-year cumulative spend (best-case · worst-case)

| Path | 6-yr total cost (non-Emergent) |
|---|---|
| Optimized (R2 cold storage + TTL tightening + delayed AI) | **~$8,000–$10,000** total over 6 years |
| Worst case (no optimization · all AI features on · maximum data growth) | **~$25,000–$35,000** total over 6 years |

For context: that "worst case" 6-year total is **less than one year of a single Vista seat × 258 users.**

---

## Migration / upgrade timeline (best estimate)

| Date | Event | Action required |
|---|---|---|
| Today (May 2026) | Atlas M0 live · platform on free tier | None |
| Q2 2026 | Atlas DB approaches 350 MB | Click M0 → M10 in Atlas console · ~5 min · +$57/mo |
| Q2 2026 | First real photo flow lands | Set R2 bucket lifecycle (30-day expiration) — operator action |
| Q3 2026 | Resend volume approaches 3,000 / mo | Click free → Pro in Resend dashboard · +$20/mo (only if daily-digest enabled) |
| Q3 2026 | First R2 paid GB | Auto-billed at $0.015/GB-mo · stay under $5/mo for ~12 months |
| Q4 2026 → Q1 2027 | Implement Atlas photo cold-storage optimization | One Phase 27.1 engineering pass · saves M20 cliff |
| Year 2 | Sentry approaches 5,000 events / mo | Click free → Team · +$26/mo |
| Year 3-4 | First AI feature in production | Universal Key meter activates · plan $20–$50/mo budget |
| Year 5 | Atlas M10 (10 GB) approaching ceiling | M10 → M20 ($148/mo) IF cold-storage optimization deferred; else stay on M10 indefinitely |

---

## Risk-adjusted forecast (where things could go wrong)

| Risk | Probability | Cost impact if hit |
|---|---|---|
| Photo cold-storage optimization deferred → Atlas grows unbounded | medium | +$90/mo from Year 2 (M20 instead of M10) |
| LLM feature scope creep | medium | +$50–$200/mo |
| MASCI acquires another company → 2× scale earlier than expected | low-medium | +$50–$150/mo earlier than year 6 |
| Cloudflare changes R2 egress pricing model | low | up to $30–$50/mo if egress becomes metered |
| Atlas raises M10 pricing | low | $57 → $65–$80/mo would be a typical drift |
| Emergent platform repricing | unknowable | n/a (audit cannot reach Emergent dashboard) |

**Headline:** even all risks compounded, year-end 6 monthly cost stays **under $500/mo** — half a percent of an equivalent ERP rollout.

---

## Verdict

🟢 **Six-year forecast shows a calm, gentle, well-bounded cost curve.** Every paid-tier cliff is opt-in, every cliff is documented, and the optimization levers exist to keep the entire 258-employee operational nervous system under $200/mo indefinitely.

---

End of Years 1-6 Infrastructure Forecast.
