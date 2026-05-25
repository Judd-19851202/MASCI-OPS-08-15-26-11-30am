# CURRENT_OPERATING_COST_BREAKDOWN.md
## MASCI Operations Platform · Phase 27 · Today's True Operating Cost
## iter428 · 2026-05-25

---

## Snapshot date: 2026-05-25

This is what the platform costs **today**, with **real measurements** from the live production-target Atlas cluster and the preview pod.

---

## Today's burn — all-in monthly

| Vendor | Plan | $ / mo | $ / yr |
|---|---|---|---|
| MongoDB Atlas | M0 free | $0.00 | $0.00 |
| Cloudflare R2 | free | $0.00 | $0.00 |
| Cloudflare DNS / CDN / TLS | free | $0.00 | $0.00 |
| Resend | free | $0.00 | $0.00 |
| Sentry | free | $0.00 | $0.00 |
| WebAuthn / passkeys | open standard | $0.00 | $0.00 |
| Stripe | provisioned · inactive | $0.00 | $0.00 |
| Universal LLM key (Emergent) | meter · no AI features active today | $0.00 | $0.00 |
| `mascidocs.com` domain | annual | $1.25 | $15.00 |
| `forgedopshq.com` domain | annual | $1.25 | $15.00 |
| Emergent runtime (preview + prod) | account-tier | (see Emergent dashboard) | (see Emergent dashboard) |
| **Total non-Emergent** | | **$2.50** | **$30.00** |

---

## Today's utilization (real numbers)

### MongoDB Atlas

| Axis | Reading | M0 ceiling | % used |
|---|---|---|---|
| Storage | 96.6 MB | 512 MB | 10.6 % |
| Connections | 23 | 500 | 4.6 % |
| Collections | 121 | unlimited | n/a |
| Documents | 237,243 | unlimited | n/a |
| Indexes | 327 | unlimited | n/a |

### Cloudflare R2

| Axis | Reading | Free ceiling | % used |
|---|---|---|---|
| Storage (1 archive at a time after iter427 prune) | ~90 MB | 10,000 MB (10 GB) | < 1 % |
| Class A ops / mo (write archive) | ~720 / mo (~24 / day) | 1,000,000 / mo | < 0.1 % |
| Class B ops / mo (read archive for restore drills) | < 50 / mo | 10,000,000 / mo | < 0.001 % |

### Resend

| Axis | Reading | Free ceiling | % used |
|---|---|---|---|
| Emails / mo | < 100 | 3,000 | < 4 % |
| Emails / day | < 5 | 100 | < 5 % |

### Sentry

| Axis | Reading | Free ceiling | % used |
|---|---|---|---|
| Errors / mo | < 200 | 5,000 | < 4 % |

### Pod disk

| Axis | Reading | Available | % used |
|---|---|---|---|
| `/app` | 6.0 GB / 9.8 GB | 3.8 GB free | 62 % |

---

## Operational activity (real, last 30 days)

| Metric | Last 30 days |
|---|---|
| `usage_events` written | 182,463 (18,198 / day) |
| Distinct active actors | 1 (admin testing only) |
| Field crews logging operational work | 0 (pilot has not landed yet) |
| New employees onboarded to platform | 0 |
| New dispatch assignments created | 0 (operational pilot pending) |
| Photo uploads (operational_attachments) | 0 (real photo flow not started) |
| Backup archives produced + uploaded to R2 | ~720 (24/day hourly cadence) |
| Backup archive size mean | ~90 MB |
| Total R2 archive bytes pushed in 30 days | ~64 GB written, ~270 MB retained (prune working) |
| Outbound emails sent | < 50 |

---

## Pre-paid / sunk costs

| Item | Amount | When paid |
|---|---|---|
| `mascidocs.com` annual registration | ≈ $15 | annual cycle (registrar-dependent) |
| `forgedopshq.com` annual registration | ≈ $15 | annual cycle |
| Emergent platform subscription | Emergent dashboard | per-cycle |

---

## What this number does NOT include

Honest scope-of-audit declaration:

- **Operator labor** (your time configuring + auditing) — this is your call, not a platform line item
- **Apple Developer ID / Google Play ID** (only if a native mobile app is ever published — $99/yr + $25 one-time)
- **Cyber insurance / E&O policy** (operator concern, NOT a platform line)
- **OSHA training subscription credits** for content embedded in the training portal (operator-procured outside platform)
- **MASCI's existing accounting / ERP** (the platform doesn't touch HCSS / Vista / etc., so no overlap charge)

---

## Honest "what could break this number" notes

1. **Emergent monthly subscription tier** — this is the only line I cannot measure from inside the platform. The Emergent dashboard is authoritative.

2. **Universal LLM key meter** — currently $0. The moment you turn on any AI-assisted feature (OCR for legacy historical imports, AI insights, etc.), this becomes the next-biggest line item in front of Atlas / Resend cliffs.

3. **R2 if lifecycle policy is not configured** — Cloudflare R2 storage will grow at ~64 GB / month if no bucket-level lifecycle rule purges old archives. A 30-day expiration rule keeps it at ~64 GB steady-state = $0.96 / mo. Worth setting now (operator action in Cloudflare R2 console).

---

## Verdict

🟢 **Real burn rate today: $2.50 / month outside of Emergent runtime.** Every measurable axis is at < 11 % of its free-tier ceiling. The platform has months-to-years of runway before any vendor line crosses a paid tier.

---

End of Current Operating Cost Breakdown.
