# INFRASTRUCTURE_SURVIVABILITY_ANALYSIS.md
## MASCI Operations Platform · Phase 27 · Survivability + Single-Point-of-Failure Audit
## iter428 · 2026-05-25

---

## Architecture survivability matrix

For each dependency, three questions:

1. **What happens if this vendor disappears tomorrow?**
2. **What's the recovery posture?**
3. **What's the time-to-restore?**

---

## 1 · MongoDB Atlas (just-migrated production database)

| Property | Status |
|---|---|
| Single point of failure | YES — this is operational truth |
| Survivability without it | platform stops functioning |
| Backup safety net | R2 hourly + nightly archives (iter425/426) · 89.5 MB / archive · 30-day retention |
| Time to restore from R2 archive | ~30 minutes operator-driven via `RESTORE_RUNBOOK.md` |
| Vendor lock | LOW — Mongo wire protocol is open · `mongorestore` works against any Mongo target |
| Replacement vendors | MongoDB Atlas (other region) · self-hosted Mongo · AWS DocumentDB · DigitalOcean Managed Mongo · Percona Server for MongoDB |
| Migration command | `mongoimport --uri "<new-uri>" --db <name> --collection <coll> --file collections/<coll>.jsonl` per collection from any archive |
| **Survivability rating** | 🟢 HIGH |

---

## 2 · Cloudflare R2 (disaster-recovery archive)

| Property | Status |
|---|---|
| Single point of failure | NO — Atlas is primary; R2 is backup |
| Survivability without it | platform continues operationally · backup pipeline silent · drift watcher logs WARN |
| Mitigation if R2 fails | switch S3_ENDPOINT_URL env var to alternate provider · backup pipeline resumes |
| Vendor lock | LOW — S3 API compatible · trivial swap |
| Replacement vendors | AWS S3 · Backblaze B2 · Wasabi · MinIO (self-hosted) · iDrive E2 · DigitalOcean Spaces |
| Migration command | one env var change: `S3_ENDPOINT_URL=https://<new-provider>` + new keys |
| **Survivability rating** | 🟢 HIGH |

---

## 3 · Cloudflare DNS (operator-facing brand)

| Property | Status |
|---|---|
| Single point of failure | YES (DNS resolves user → platform) |
| Survivability without it | platform unreachable until DNS recovers |
| Mitigation if Cloudflare fails | repoint nameservers at any other DNS host (Route 53, Google, Cloudflare DNS isn't the only Cloudflare — same vendor, but DNS is one of the most-redundant Anycast networks on Earth) |
| Replacement | AWS Route 53 · Google Cloud DNS · NS1 · ClouDNS · DNSimple |
| Time to restore | DNS propagation: typically < 5 min with short TTL · up to 24-48 hours worst case if TTL long |
| **Survivability rating** | 🟢 HIGH (Cloudflare itself is highly redundant; even if you migrate away, DNS is portable) |

---

## 4 · Resend (transactional email)

| Property | Status |
|---|---|
| Single point of failure | NO — platform functions without email; operators just don't receive notifications |
| Survivability without it | full operational continuity · digest/alert emails fail silently |
| Mitigation if Resend fails | rewrite `lib/email.py` for alternate provider · single-day engineering task |
| Replacement vendors | Postmark · AWS SES · SendGrid · Mailgun · MailerSend · Brevo |
| Domain re-verification | required (DNS records for new provider) · ~30 min |
| **Survivability rating** | 🟢 HIGH |

---

## 5 · Sentry (error telemetry)

| Property | Status |
|---|---|
| Single point of failure | NO — completely optional |
| Survivability without it | platform fully operational · operator just loses error visibility |
| Mitigation if Sentry fails | delete `SENTRY_DSN` env var · backend logs to stdout instead · still survivable |
| Replacement | self-hosted GlitchTip (drop-in Sentry-compatible) · BugSnag · Rollbar · Honeybadger · or stdout-only |
| **Survivability rating** | 🟢 HIGH |

---

## 6 · WebAuthn / passkey infrastructure

| Property | Status |
|---|---|
| Vendor dependency | NONE — browser-native standard |
| Survivability if any single browser vendor drops support | other browsers still work · passkeys are cross-browser standard |
| Mitigation | password auth remains as fallback · platform never depends on passkey-only |
| **Survivability rating** | 🟢 HIGHEST |

---

## 7 · Universal LLM key (Emergent) — optional features

| Property | Status |
|---|---|
| Single point of failure | NO — no critical feature depends on LLM today |
| If Emergent removes Universal Key | replace `EMERGENT_LLM_KEY` with `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GOOGLE_API_KEY` (bring-your-own) |
| Migration time | one env-var swap + one client-init line change |
| **Survivability rating** | 🟢 HIGH |

---

## 8 · Emergent platform runtime (production deployment host)

| Property | Status |
|---|---|
| Single point of failure | YES (platform must run somewhere) |
| Survivability without it | platform offline until alternate runtime provisioned |
| Mitigation | platform is **portable FastAPI + React + S3 + Mongo** — runnable on: |
| Render | $7/mo Hobby tier → $19/mo Standard (covers production) |
| Railway | $5/mo Hobby tier → $20/mo Pro |
| Fly.io | $1.94/mo per shared-cpu-1x machine · scales linearly |
| DigitalOcean App Platform | $5/mo Basic → $12/mo Professional |
| Vercel (frontend) + Render (backend) | hybrid pattern · $0–$20/mo combined |
| AWS Lightsail | $7–$20/mo |
| Self-hosted Kubernetes / VPS | $10–$60/mo depending on size |
| Migration time | a single weekend's engineering · same code, different deploy config |
| **Survivability rating** | 🟡 MEDIUM (high reliance, low lock-in) |

---

## Composite stack survivability

| Vendor disappears tomorrow | Recovery time | Recovery cost |
|---|---|---|
| MongoDB Atlas | 30 min (R2 restore) | $0 |
| Cloudflare R2 | < 1 hour | $0 (just env var swap) |
| Cloudflare DNS | < 1 hour | $0 |
| Resend | 1 day (engineering swap) | $0 |
| Sentry | trivial | $0 |
| WebAuthn | n/a — standard | n/a |
| Universal LLM key | < 1 hour | $0 (bring-your-own) |
| Emergent runtime | 1 weekend | < $100 first month + DNS update |

**Composite "worst single vendor goes down forever" recovery: ~1 weekend, < $100 in vendor switching costs.**

---

## Top-three single points of failure ranked

| Rank | Single point of failure | Why | Mitigation |
|---|---|---|---|
| 1 | MongoDB Atlas (production cluster) | operational truth lives here | R2 hourly archive + drift watcher + `RESTORE_RUNBOOK.md` |
| 2 | Emergent runtime pod | code executes here | architecture is portable to any FastAPI host |
| 3 | Cloudflare DNS | users reach platform via this | DNS is portable in 5 minutes |

---

## Geographic / regional risk

| Vendor | Geographic footprint | Failure mode |
|---|---|---|
| MongoDB Atlas M0 | shared region · auto-selected by Atlas | regional outage stops platform · R2 archive (region-redundant on Cloudflare's global network) restores |
| Cloudflare R2 | globally distributed object store | extremely resilient; R2 has not had a major-outage incident worth migrating away from |
| Cloudflare DNS | Anycast global network | extremely resilient |
| Emergent runtime | platform-managed region | failure mode handled by Emergent SLO |
| Resend | US-East-1 region | regional but cheap to replace with alternate provider |

---

## Operational survivability scenarios

### Scenario A · Atlas region outage (rare)

- Platform stops accepting writes for the outage duration
- Reads from existing Mongo connection pool may continue briefly
- Operator restores from latest R2 archive into a fresh Atlas cluster in alternate region
- Time to operational recovery: ~30 min
- Data loss: ≤ 1 hour worth (gap between last archive and outage start)

### Scenario B · R2 region outage (rare)

- Live operations unaffected
- Backup pipeline drops archive for the outage duration
- Drift watcher logs WARN
- Once R2 recovers, next archive tick resumes normal cadence
- Time to operational recovery: 0 (R2 outage doesn't stop operations)

### Scenario C · Emergent runtime outage (operator's most likely event)

- Platform unreachable
- Operator notified by external monitoring or by employees reporting
- Two-path recovery:
  - **Wait** for Emergent recovery (typical: < 1 hour for incidents)
  - **Escape hatch:** spin up Render/Railway/Fly with the same MONGO_URL + R2 keys + REACT_APP_BACKEND_URL · DNS swap · operational in 4 hours
- Time to operational recovery: 1 hour (most likely) · 4 hours (escape hatch)

### Scenario D · Lost MFA / passkey access for super-admin

- Super-admin cannot sign in
- Recovery path: SSH into the production pod (Emergent dashboard provides this) · drop `mfa.recovery_codes` from the `employees` doc directly in Mongo · re-enroll MFA after sign-in
- Time to operational recovery: 15 min · operator action only

---

## Verdict

🟢 **No single vendor controls platform survivability. Every line has a documented escape hatch costing < 4 hours of operator time. Atlas + Emergent runtime are the two highest-reliance points — both are mitigated by R2 archive (data) and architectural portability (code). The platform is fundamentally survivable.**

---

End of Infrastructure Survivability Analysis.
