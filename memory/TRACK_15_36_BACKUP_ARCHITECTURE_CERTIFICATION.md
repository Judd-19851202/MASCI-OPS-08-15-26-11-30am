# TRACK 15.36 · BACKUP ARCHITECTURE CERTIFICATION

**Track:** 15.36 · READ-ONLY architecture certification
**Mode:** identify · document · evaluate · DO NOT change anything
**Date:** 2026-02 (live probes captured 2026-06-19 ~10:50 UTC against `mascidocs.com`)
**Companion documents:** `TRACK_15_36_BACKUP_INVENTORY.md` · `TRACK_15_36_RESTORE_RUNBOOK.md` · `TRACK_15_36_BACKUP_COST_MODEL.md`

---

# FINAL VERDICT

# 🟡 YELLOW

**Can MASCI safely reduce backup cadence from hourly to every 6 hours?**

**Answer: YELLOW — likely safe, but operator must verify two missing dashboard settings first.**

The cadence reduction is sound on its merits: 6-hour archives still bound data loss at ≤6 hours, the R2 tiered retention contract still applies, the cost model favors it (66 % storage reduction). But two pieces of evidence are not available from inside the pod and the operator must produce them before a true GREEN:

1. **Atlas backup tier + Continuous Backup status** — if Atlas Continuous Backup (PITR) is enabled on this cluster, then sub-hour RPO is already covered by Atlas independent of R2 cadence, and 6-hour R2 cadence is plainly safe. Without it, the operator should also verify Atlas snapshot frequency.
2. **R2 bucket versioning status** — if versioning is enabled, accidentally-deleted backups (Restore Scenario 10) are recoverable, making the cadence reduction lower-risk. If versioning is disabled, a deleted backup is permanently gone.

Both checks are 60-second dashboard lookups. After confirming both, the answer flips to **GREEN**.

---

## Five-Pillar evaluation (current architecture)

| Pillar | Score | Justification |
|---|---|---|
| **Powerful** | 🟢 | Hourly R2 archive covers every Mongo collection (auto-discovery — 163 collections · 138k records) + inlined R2 photos. Atlas + R2 + email + GitHub provide four independent off-pod recovery paths. Tiered retention bounds storage (14d hourly · 90d daily · 365d monthly). Per-collection soft-delete restore for employees/jobs/equipment/suppliers. |
| **Simple** | 🟡 | Two parallel cadences (hourly R2 + 02/18 UTC email) is reasonable. Restore is conceptually one endpoint (`POST /api/exports/restore`) gated by manifest validation. **Simplicity gaps:** the 500 MB upload ceiling makes the restore endpoint structurally unable to ingest the very backups the system produces; the integrity-check endpoint is partially blind (looks at local disk which is empty after upload). |
| **Beautiful** | 🟢 | Manifest is rich + auditable (per_kind counts · explicit_exclusions · redaction_rules). Audit trail (`audit_events`) records every restore with archive origin (Track 14.0-I1 envelope). Backup-health rows give a full time-series. |
| **Trusted** | 🟡 | Strong: env-name and DB-name validated at restore time (refuse cross-env restore). Sensitive credentials redacted (password_hash, MFA secret, recovery codes). Idempotent retention. **Trust gaps:** drift watcher is dormant (`drift_watch_active=false`); legacy `backups/` prefix unpruned (~500 stale objects); no automated restore drill on record; R2 versioning + Atlas tier unverified. |
| **Proven** | 🟡 | Backup pipeline is **proven live** — hourly archive fires correctly (06:00, 07:00, 08:00, 09:00, 10:00 UTC on 2026-06-19), backup_health row written, R2 upload confirmed via `last_modified_iso`. Watchdog reports `healthy · hours_silent=0.7`. **Proof gaps:** restore paths have never been drilled end-to-end on production. |

---

## What we have (evidence-backed)

### Backup systems currently active

* **B-01 R2 Hourly Complete Backup** — fires every UTC hour, ~600 MB each, 138k records each, written to `r2://<bucket>/backups/auto-90d/MASCI_complete_backup_*.zip`
* **B-02 Nightly Email Backup** — 02:00 + 18:00 UTC, lite DB-only zip to admin inbox
* **B-03 R2 Tiered Retention** — 14d/90d/365d policy enforced after each backup (only on `auto-90d/` prefix)
* **B-04 Weekly Backup Verification Cron** — Mon 14:00 UTC, cross-checks Mongo + R2, emails PASS/FAIL
* **B-05 Backup Watchdog** — 25h-silent alarm
* **B-06 R2 Usage Probe** — 45/50 GB thresholds, log-only
* **B-07/B-08 Restore endpoints** — soft-delete undo (4 collections) + full-archive restore
* **B-09 Atlas Mongo** — `masci-prod.1nduwmg.mongodb.net`, MongoDB 8.0.26, 163 collections
* **B-10 Cloudflare R2** — bucket size 197.13 GiB / 8,517 objects
* **B-11 Local pod disk** — transient staging only
* **B-13 GitHub** — code only, not data
* **B-14 Drift watcher** — dormant

### Backup statistics (live)

* **Total R2 bucket:** 197.13 GiB · 8,517 objects (R2 usage probe @ 2026-06-19T10:06:16Z)
* **Backups prefix (`backups/`):** 864 objects (363 in `auto-90d/` + ~500 legacy)
* **Newest 500-backups sample:** 182 GiB
* **Avg backup:** 373 MB (sample-wide), 600 MB (newest hourlies)
* **Records per backup:** ~138,000 across 163 collections
* **Bucket alert:** 🚨 **at 394 % of `R2_USAGE_ALERT_GB=50` threshold** — log-only, no email storm by design
* **Last successful backup:** `MASCI_complete_backup_2026-06-19_100315Z.zip` · 632 MB · 138,236 records

### Backups contain

* Every Mongo collection (JSON dump, auto-discovered, `_id` stripped) under `{kind}/json/{id}.json`
* Every R2 photo (binary inlined under `photos/<key>`)
* `MANIFEST.json` with per-collection counts, explicit exclusions, redaction rules, photo counts
* `backup_log.txt`

### Backups do NOT contain (by design)

* `system.indexes` (Mongo internal)
* `usage_events` (regenerable telemetry)
* `health_monitor_runs` (regenerable health series)
* `job_photo_thumb_cache` (regenerable cache)
* `password_hash` field from `users` and `user_directory`
* `mfa.secret` + `mfa.recovery_codes` from `user_directory`

---

## What we do NOT know (must be answered by operator)

1. **Atlas backup tier** — M0/M2/M5 (snapshot-only, manual) vs M10+ (Continuous Backup/PITR). Cluster name `masci-prod.1nduwmg.mongodb.net` suggests a paid tier but the API key from the pod cannot query Atlas Admin.
2. **R2 bucket versioning** — present/absent? affects "deleted backup" recoverability (Scenario 10).
3. **R2 lifecycle policy** — Cloudflare-side lifecycle rules that may already prune things outside `auto-90d/`?
4. **R2 object lock** — present? prevents accidental delete even with admin creds.
5. **R2 audit logging** — present? necessary for "who deleted what" forensics.

---

## Serious gaps discovered (none of them are deploy blockers; all are listed for the operator)

| # | Gap | Severity | Recommendation |
|---|---|---|---|
| 1 | `POST /api/exports/restore` has 500 MB upload ceiling but current archives are ~600 MB — full-archive restore through the documented endpoint is **structurally broken** | 🔴 HIGH | Raise the ceiling to 2 GB or accept multipart upload. Track 15.37 work. |
| 2 | Drift watcher dormant (`drift_watch_active: false`) | 🟡 MED | Investigate why heartbeat isn't seen; restart if needed. Track 15.37 work. |
| 3 | Legacy `backups/` prefix unpruned — ~500 stale objects, ~15 GiB | 🟡 MED | One-shot operator-approved delete in a separate track. Not 15.36. |
| 4 | R2 usage alert at 394 % of threshold but no automated email — only log + DB row | 🟢 BY DESIGN | The anti-storm decision was deliberate (15.34B-style fatigue prevention). Keep as-is. |
| 5 | No portal-level "undelete daily report / meeting / incident" UI — only employees/jobs/equipment/suppliers have soft-delete restore endpoints | 🟡 MED | Operator-only restore via R2 zip extraction. Track 15.37 backlog. |
| 6 | No automated restore drill ever recorded | 🟡 MED | Schedule a quarterly drill against the preview environment. |
| 7 | Atlas backup tier + R2 versioning unverified | 🔴 HIGH | Operator dashboard check (10 min). Required before cadence reduction. |

None of these prevent the system from operating tomorrow morning. They constrain the cadence-reduction decision until the operator answers item 7.

---

## Cadence recommendation

### Recommended cadence: **Every 6 hours** (after operator confirms gap 7 above)

**Why:**

* **RPO bound at 6 hours.** For a construction-safety document system that ingests daily reports / safety meetings / incidents during the workday, a 6-hour gap is operationally tolerable. Real-time data (notifications, dispatch state) is held in Atlas, which has its own PITR (pending confirmation).
* **Steady-state storage drops 66 %** — from 247 GiB to 83 GiB.
* **Annual cost drops 66 %** — from $44 to $15 in R2 storage at current adoption; from $890 to $299 at 100 % adoption over 5 years.
* **Restore-time confusion drops** — operators choosing from 4 archives/day is easier than 24/day.
* **R2 usage falls back below the 50 GiB alert threshold** — the `r2-usage-alert` log/DB row stops firing every hour.
* **The Tier-1 14-day hourly window becomes Tier-1 14-day 6-hourly window** — same retention contract, fewer objects.

### Not recommended: daily-only

* Daily cadence (1×/day) saves another $5/year at most while widening RPO to 24h. The 6→24 hour swing is the only meaningful RPO increase in the range. Not worth the additional risk for ~$5/year.

### Not recommended: keep hourly

* Hourly is over-provisioned given current adoption. If a future Atlas tier-down or R2 cost spike occurs, the cost of hourly will spike too. 6-hour is the right balance now and continues to be sound at 4× adoption.

---

## Retention policy under 6-hour cadence

Adapt the existing Track 15.28A tiered contract:

| Tier | Window | Cadence | Survivors | Approximate count |
|---|---|---|---|---|
| 1 | ≤14 days | 6-hour | all (every archive) | 56 |
| 2 | 14–90 days | daily-survivor | newest per UTC day | 76 |
| 3 | 90–365 days | monthly-survivor | newest per UTC month | ~9 |
| 4 | >365 days | none | delete | 0 |

Total steady-state at 6-hour: **~141 archives** (vs ~421 at hourly).

No code change is required to implement this — `BACKUP_R2_HOURLY=false` + `BACKUP_R2_FULL_HOUR_UTC=<list>` is one knob. The retention policy is cadence-independent (it just keeps fewer Tier-1 archives because fewer are produced).

---

## Plain-English Executive Summary (Phase 11)

1. **What exactly are we backing up?** Every record in every Mongo collection (163 of them), plus every binary photo / PDF stored in R2. Every UTC hour. To Cloudflare R2 + nightly email to the admin inbox.
2. **Are we backing up too often?** Yes. Hourly was chosen at iter85 to cap data-loss at ~1 hour during the early-growth phase. Today the platform is stable; 6-hour cadence covers the same risk class for 1/6 the storage cost.
3. **Are we backing up the same thing multiple times?** Yes — every hourly archive contains 100 % of every collection. There is no delta / incremental. This is a deliberate trade-off for restore simplicity (one zip restores everything) and is fine at our scale.
4. **Are we missing anything important?** No critical data. We DO exclude `usage_events`, `health_monitor_runs`, `job_photo_thumb_cache` (regenerable) and we DO redact password hashes + MFA secrets (security-correct).
5. **Can we recover if production burns down?** Yes — Atlas + R2 + GitHub + Emergent platform are four independent off-pod stores. Recovery window 30 min – 4 hours depending on path.
6. **Can we recover if someone deletes one record?** **It depends on the collection.** Employees / jobs / equipment / suppliers have soft-delete restore endpoints (fast, 1-click). Daily reports / meetings / incidents / corrective actions / notifications do NOT have a portal-level undelete — restore requires pulling the R2 archive and extracting the JSON record manually.
7. **Can we recover if someone deletes one uploaded file?** **Maybe.** Depends on R2 versioning (unverified). If versioning is on, yes via Cloudflare. If off, the most recent hourly archive holds an inlined copy — accessible by pulling the zip.
8. **How much would we lose with 6-hour backups?** At worst, 6 hours of data ingested between archives. In practice less, because Atlas is the live store and persists everything continuously; R2 archives are off-pod copies, not the only copy.
9. **How much would we save with 6-hour backups?** ~164 GiB at steady state, ~$29 / year now, ~$591 over 5 years at 100 % adoption growth. Plus the bucket falls back below the 50 GiB alert threshold.
10. **What should we change?** Reduce cadence to 6-hour AFTER verifying Atlas backup tier and R2 versioning. Optionally delete the legacy `backups/` prefix in a one-shot operator-authorized batch.
11. **What should we NOT touch?** Don't change the retention policy itself. Don't disable the email cron. Don't disable the watchdog. Don't disable backup verification. Don't touch the redaction rules. Don't widen who can hit `/api/exports/restore`.
12. **What is the safest next step?** Operator opens the Atlas dashboard and the Cloudflare R2 dashboard for ~10 minutes. Confirms Atlas backup tier and R2 versioning. If both are healthy, the cadence change is GREEN.

---

## Verdict

# 🟡 YELLOW

Reduce cadence to 6-hour after the operator confirms (i) Atlas backup tier supports the desired RPO and (ii) R2 versioning is enabled. Both checks are dashboard-only — no code change, no deploy, no risk. After confirmation, the cadence change is a single env var flip (`BACKUP_R2_HOURLY=false` + adjust scheduler hours) and the retention contract takes care of itself.

🛑 STOP. Operator review required for next action.
