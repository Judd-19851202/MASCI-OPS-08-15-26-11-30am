# HIDDEN_COST_AND_SCALING_RISK_REPORT.md
## MASCI Operations Platform · Phase 27 · Hidden Cost & Scaling Risk Audit
## iter428 · 2026-05-25

---

## The eight hidden-cost vectors

This audit hunts for cost surprises that would NOT be obvious from looking at the vendor pricing pages. Each section ranks: severity · probability · mitigation status.

---

## 1 · Operational photo upload explosion 🟡

| Severity | Probability | Today's status |
|---|---|---|
| MEDIUM (cost-wise) HIGH (storage-wise) | HIGH (will land Year 1) | Architecture supports it · cold-storage optimization NOT yet implemented |

**The pattern:** iter417 stores photos as base64 `data_b64` inside `db.operational_attachments`. Each MASCI active crew is projected to upload ~30 photos/day × ~600 KB raw ≈ 18 MB/day. At 10 crews × 365 days, the year-1 raw photo footprint is **~65 GB**. Inflated to base64 in Mongo, it's **~86 GB**.

**Why this matters:** Atlas M10 free includes 10 GB. M20 is $148/mo, M30 is $336/mo. If you let photos accumulate inline in Mongo, you cliff-jump tier every 12 months purely on photo volume.

**Mitigation (P1 engineering work — Phase 27.1 recommended):**
- Phase 27.1 — store photos in R2 by `r2://` reference (key path), keep only `r2_key + mime + thumb_b64` inline in Mongo
- Result: Atlas Mongo size stays ~1.5–3 GB at full adoption indefinitely
- R2 storage cost: $0.015/GB-mo × 80 GB year 1 = **$1.20/mo** instead of M20 cliff at $148/mo
- **Savings: ~$1,700/yr by year 2 forward**

---

## 2 · Cloudflare R2 egress 🟢

| Severity | Probability | Today's status |
|---|---|---|
| LOW | LOW | R2's structural pricing wedge — **egress is free forever** |

**The pattern:** Every "cloud storage" cost lecture starts with "egress is the killer." R2's selling point is that egress is **always free**. This is not a trial offer — it's R2's market position vs S3.

**Why this matters:** If your operations team uses the platform from cell-tethered iPads in the field — and they will — every photo download / dispatch detail / training video stream is bandwidth out of R2. On AWS S3, this would dominate the bill. On R2, it costs zero.

**Mitigation:** None needed. Stay on R2. **Do not migrate to S3.**

---

## 3 · `usage_events` collection growth ⚠ → mitigated

| Severity | Probability | Today's status |
|---|---|---|
| HIGH if untreated | HIGH | **MITIGATED** by 90-day TTL index |

**The pattern:** `usage_events` writes ~18k/day today, projects to ~50k/day at full adoption. Without TTL, this becomes 18M docs/year ≈ 2.5 GB. **With** the 90-day TTL (already in place), it's bounded at ~4.5M docs ≈ 720 MB.

**Mitigation:** TTL already armed in `server.py` (`expireAfterSeconds=7776000` on `at_1`). Verify by running `db.usage_events.getIndexes()` periodically.

---

## 4 · Resend volume cliff 🟢

| Severity | Probability | Today's status |
|---|---|---|
| LOW | MEDIUM | Free tier ample today; daily-digest feature is the trip wire |

**The pattern:** Free Resend is 3,000/mo. Weekly digests for 258 employees + alerts/resets = ~1,250/mo. **Safe.** But if you turn on daily digests, that becomes ~8,000/mo → Resend Pro $20/mo.

**Mitigation:** Audit `routes/digests.py` quarterly. Don't enable daily digests unless operationally needed.

---

## 5 · Backup archive accumulation in R2 ⚠ → operator action required

| Severity | Probability | Today's status |
|---|---|---|
| MEDIUM | HIGH if not configured | Backup retention is local-only (iter427); R2-side lifecycle is NOT configured by code |

**The pattern:** Hourly + nightly archives push 24 × 30 = 720 archives/mo to R2. At ~90 MB each that's 64 GB/mo. If left uncleaned, **R2 free tier (10 GB) is breached in Week 2 of any real operational activity.**

**Mitigation (operator action · ~3 min in Cloudflare R2 console):**
1. Cloudflare dashboard → R2 → bucket `masci-hub` → Settings → **Object lifecycle rules**
2. Create rule:
   - Name: `backup-30day-purge`
   - Prefix filter: `backups/`
   - Action: **Delete objects after 30 days**
3. Save

After this rule lands, R2 stays at ~64 GB steady-state cost = $0.96/mo. Without it, R2 cost grows linearly forever.

---

## 6 · Audit retention pressure 🟢

| Severity | Probability | Today's status |
|---|---|---|
| LOW | LOW | TTL coverage on critical audit collections is already armed |

| Collection | Today | TTL armed? |
|---|---|---|
| `usage_events` | 182k | ✅ 90 days |
| `audit_events` | 10,320 | ✅ 30 days |
| `r2_degraded_events` | small | ✅ 30 days |
| `digest_runs` | small | ✅ 30 days |
| `health_monitor_runs` | 9,307 | ✅ 30 days |
| `system_health_events` | small | ✅ 30 days |
| `session_activity` | small | ✅ 30 days |
| `admin_audit` | 1,956 | ✅ 365 days |
| `webauthn_challenges` | small | ✅ challenge-expiration TTL |

No retention drift today. **Risk LOW.**

---

## 7 · LLM scope creep 🟡

| Severity | Probability | Today's status |
|---|---|---|
| LOW–MEDIUM | MEDIUM | Universal Key meter is at $0 today · easy to enable features that compound |

**The pattern:** Universal Key billing is per-token. A single AI-driven feature can run $5–$50/mo. Two or three "let's also do X" features can become $100–$200/mo without anyone noticing.

**Mitigation:**
- Cap auto-top-up at $25/mo on the Universal Key (Emergent dashboard → Profile → Universal Key)
- Audit Universal Key meter monthly
- Treat any new AI feature as a budget decision, not a feature decision

---

## 8 · SMS / MFA-via-SMS (if ever enabled) 🟡

| Severity | Probability | Today's status |
|---|---|---|
| MEDIUM if enabled | LOW (currently disabled) | Platform uses TOTP (authenticator app) + WebAuthn passkeys — no SMS cost |

**The pattern:** Twilio SMS is $0.0079 per message + $1.15/mo per active phone number. If MFA-via-SMS gets enabled for 258 employees, every sign-in burns SMS budget.

**Mitigation:** WebAuthn passkeys (iter422) **already removed the operational need for SMS MFA**. Stay on TOTP + passkeys. Resist the temptation to add SMS.

---

## Less-obvious hidden costs

### Mobile-app distribution (if ever native)

| Item | One-time | Recurring |
|---|---|---|
| Apple Developer Program | $0 | $99 / yr |
| Google Play Console | $25 one-time | $0 |
| Code-signing certificate management labor | several hours / yr | operator labor only |

Today's PWA-only posture costs $0. Native is only worth it if push notifications or offline-camera become operational blockers.

### Insurance / compliance creep

| Item | Annual range |
|---|---|
| Cyber liability rider | $500–$2,500 (operator-procured) |
| SOC 2 readiness (if a client demands it) | $15,000–$30,000 first audit · ~$10,000 / yr maintenance |
| OSHA-content licensing inside the training portal | ~$0–$500 / yr depending on content provider |

None of these are platform vendor costs — but they are operationally adjacent.

### Disaster-recovery drill labor

| Item | Frequency | Cost |
|---|---|---|
| Quarterly DR drill (`RESTORE_RUNBOOK.md`) | 4× / year | ~2 hours of operator time per drill |
| Annual full-platform restore validation | 1× / year | ~4 hours |
| Annual passkey re-enrollment audit | 1× / year | ~1 hour |

Operator labor, NOT platform vendor cost — but worth budgeting.

### Restore testing cost

| Test | Cost |
|---|---|
| Pull latest R2 archive to laptop | $0 (R2 egress free) |
| Run `mongorestore` into a temporary local Mongo | $0 |
| Verify byte-for-byte sample of operational_attachments | $0 (manual operator time, ~30 min) |

DR drills cost **zero in vendor fees** thanks to R2 egress-free pricing. Pure operator-labor expense.

---

## Pricing-cliff vendor scorecard

| Vendor | Cliff visibility | Cliff predictability | Mitigation difficulty |
|---|---|---|---|
| MongoDB Atlas | 🟢 transparent | 🟢 storage-driven, predictable | 🟢 click M0 → M10 in console |
| Cloudflare R2 | 🟢 transparent | 🟢 per-GB-mo | 🟢 lifecycle rule fixes accumulation |
| Resend | 🟢 transparent | 🟢 emails-per-mo | 🟢 free → Pro one-click |
| Sentry | 🟢 transparent | 🟢 events-per-mo | 🟢 free → Team one-click |
| Cloudflare DNS / CDN | 🟢 no metered axis | 🟢 forever-free | n/a |
| Universal LLM key | 🟢 transparent meter | 🟡 LLM costs vary | 🟢 cap auto-top-up |
| Emergent platform tier | 🟡 visible only on Emergent dashboard | 🟡 audit cannot see directly | 🟢 operator monitors monthly |
| Twilio (if ever) | 🟢 per-message metering | 🟢 highly predictable | 🟢 don't enable |
| Stripe (if ever) | 🟢 per-transaction metering | 🟢 predictable | 🟢 don't enable |

---

## Single top recommendation

🟢 **Add the R2 bucket lifecycle rule today.** It's a 3-minute operator action in Cloudflare that prevents the most likely hidden-cost surprise in the platform.

Without it: R2 grows ~64 GB/month from backup archives forever.
With it: R2 stays at 64 GB steady-state ≈ $0.96/mo permanently.

---

## Verdict

🟢 **One hidden cost is real (photo upload growth → P1 engineering work in Phase 27.1).
One requires operator action (R2 lifecycle rule).
Six others are well-mitigated or low-probability.
No surprise vendor lines are waiting.**

---

End of Hidden Cost & Scaling Risk Report.
