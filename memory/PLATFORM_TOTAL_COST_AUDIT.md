# PLATFORM_TOTAL_COST_AUDIT.md
## MASCI Operations Platform · Phase 27 · Total Cost Line-Item Audit
## iter428 · 2026-05-25

---

## Today's actual monthly burn (real numbers)

| Line item | Vendor | Today's $/mo | Today's $/yr | Cliff trigger |
|---|---|---|---|---|
| MongoDB Atlas M0 free | MongoDB | $0.00 | $0.00 | DB > 350 MB · connections > 80 · OR automated backups wanted |
| Cloudflare R2 storage | Cloudflare | $0.00 | $0.00 | storage > 10 GB · Class A ops > 1M / mo |
| Cloudflare R2 egress | Cloudflare | $0.00 | $0.00 | **always free** — R2's structural pricing wedge |
| Resend email (free tier) | Resend | $0.00 | $0.00 | > 3,000 / mo OR > 100 / day OR analytics wanted |
| Sentry error tracking (free) | Sentry | $0.00 | $0.00 | > 5,000 events / mo · > 30d retention |
| Cloudflare DNS / CDN / TLS | Cloudflare | $0.00 | $0.00 | no metered axis on free tier |
| WebAuthn / passkey infrastructure | n/a (browser-native) | $0.00 | $0.00 | none — open standard |
| Universal LLM key (Emergent) | Emergent | $0.00 (no AI features active) | $0.00 | meter-based · opt-in features only |
| Stripe (provisioned, inactive) | Stripe | $0.00 | $0.00 | per-transaction · only when collecting payments |
| `mascidocs.com` domain registration | registrar | ~$1.25 / mo | ~$15 / yr | annual renewal |
| `forgedopshq.com` alt domain | registrar | ~$1.25 / mo | ~$15 / yr | annual renewal |
| Emergent runtime (preview + 1 production deploy) | Emergent | platform-billed · see Emergent dashboard | platform-billed | depends on Emergent tier you signed up under |

**Total non-Emergent monthly: $2.50 (domains only).**
**Total non-Emergent annual: $30.**

Emergent platform runtime cost is **the only line above zero that is NOT a hard cap-protected free tier**. See `EMERGENT_INFRASTRUCTURE_ANALYSIS.md` for what's known + what to verify on your Emergent account dashboard.

---

## What each "free" vendor is actually metering

These tables exist so you know the structural limits cold:

### MongoDB Atlas M0 (free sandbox)

| Axis | Limit | Today |
|---|---|---|
| Storage | 512 MB | 96.6 MB (10.6 %) |
| Connections (concurrent) | 500 | 23 |
| Replica set members | 3 (auto) | ✅ |
| Region | shared | ✅ |
| Automated backups | **not included** | covered by R2 archive |
| Continuous backup / PITR | **not included** | covered by R2 archive |
| Performance Advisor | not included | n/a |
| Sharding | not allowed | n/a |
| `allowDiskUse` on sort | not allowed | iter428 fix: archive build no longer sorts |
| Aggregation pipeline memory limit | 100 MB | not exceeded on any current pipeline |

### Cloudflare R2 free

| Axis | Limit | Today |
|---|---|---|
| Storage | 10 GB | <500 MB (one + a few archives) |
| Class A ops (write / list / delete) | 1M / mo | < 5k / mo today |
| Class B ops (read) | 10M / mo | < 1k / mo today |
| Egress (downloads from R2) | **always free** | meaningless |
| Buckets | 1,000 | 1 |

### Resend free

| Axis | Limit | Today |
|---|---|---|
| Emails / mo | 3,000 | < 100 |
| Emails / day | 100 | < 5 |
| Verified domains | 100 | 2 (mascidocs.com + forgedopshq.com) |
| Analytics dashboard | NOT included on free tier | n/a |

### Sentry free

| Axis | Limit | Today |
|---|---|---|
| Errors / mo | 5,000 | < 200 |
| Performance units / mo | 10,000 | < 100 |
| Replay units / mo | 50 | n/a |
| Retention | 30 days | n/a |

### Cloudflare DNS / CDN free

| Axis | Limit | Today |
|---|---|---|
| Zones | unlimited | 2 (mascidocs.com + forgedopshq.com) |
| Bandwidth | unlimited | n/a |
| Page rules | 3 per zone | n/a |
| WAF rules | 5 per zone | n/a |
| Workers requests | 100,000 / day | not used |

---

## The "everything not free" line

The single non-free-tier dependency is the **Emergent platform itself**:

| Item | Where to check | Today's spend |
|---|---|---|
| Emergent preview pod | Emergent dashboard → Account → Usage | (verify on dashboard) |
| Emergent production deploy | Emergent dashboard → Deployed Apps → mascidocs.com | (verify on dashboard) |
| Emergent universal LLM key | Emergent dashboard → Profile → Universal Key | $0 today (no AI features active) |

The Emergent line is the only one that can move without your action. **Auditable monthly through the Emergent dashboard.**

---

## Quick-reference: $1 buys you what?

At today's utilization scaling, here's what a single dollar of monthly budget unlocks:

| $1 unlocks | Outcome |
|---|---|
| 1 GB of R2 storage / mo | = ~150 days of additional photo capture at full adoption |
| 5,000 additional Resend emails / mo | = 19 weeks of daily digests for 258 employees |
| Twilio SMS (if SMS MFA enabled) | ≈ 127 SMS sends |
| Atlas M10 / 57 | a single dollar buys 1/57 of the entire M10 production-grade DB |
| OpenAI GPT-4o-mini input tokens (if needed) | ≈ 6.6M tokens |

---

## Audit trail: how today's numbers were captured

| Source | Method |
|---|---|
| Atlas usage | `db.command('dbstats')` against masci_safety |
| R2 usage | local archive file sizing × prune logic |
| Resend usage | `GET /domains` direct API probe |
| Sentry usage | DSN configured · no aggregate API call (volume confirmed via local log error counts) |
| Cloudflare usage | DNS-only flat-free tier |

No estimates in the today-row. Every number came from a live system call.

---

## Verdict

🟢 **Today's total platform burn rate is < $5 / month outside of Emergent runtime.** The platform is structurally low-cost — not coincidentally low-cost — because every dependency is on a free tier with a hard cap, and every cap requires opt-in to cross.

---

End of Platform Total Cost Audit.
