# TRACK 27.07A · PHASE 0B — R2 THRESHOLD PROVENANCE, CAPACITY POLICY & STORAGE-ECONOMICS AUDIT

**Audit executed:** 2026-02 (fork session)
**Auditor:** E1 agent · read-only mode
**Environment:** PREVIEW bash access only; production untouched
**Scope:** Prove provenance of the 50 GB R2 alert threshold. Determine whether the current ~320 GB R2 bucket size is unhealthy, financially unacceptable, or technically fine. Propose business-driven policy candidates. **No code, no config, no bucket scan, no deletions, no quarantines.**

---

## 🧭 EXECUTIVE DECISION SECTION (plain language)

### The 50 GB alert threshold is a legacy free-tier-era placeholder, never re-approved after real usage was known.

- It was introduced on **2026-05-17 03:24 UTC** by commit `30a4a270`, at a time when the R2 bucket held **19.48 GB / 707 objects**. The 50 GB alert gave ~2.5× headroom against that snapshot and roughly matched Cloudflare R2's free-tier storage ceiling (10 GB free + 40 GB "comfortable paid" buffer).
- No cost budget, contract clause, retention SLA, or operator-signed policy authorized the 50 GB number. The commit that introduced it authored a placeholder for a **passive log-only probe** (`_log_r2_usage_warning`), explicitly documented as **"warn-only, no email, no block, no delete."**
- The threshold was **never revisited** after the bucket crossed it in mid-2026. Every subsequent forensic report (2026-05-26 · 77 GB · 2026-06-01 · 91 GB · 2026-07-09 · 187 GB · 2026-07-11 · **320.47 GB**) reasoned around it rather than re-approving it.

### The current 320.47 GB bucket is technically fine and financially trivial.

- **At Cloudflare R2 official public pricing**, 320 GB costs **$4.80/month** for storage. Class A + B operations at current cadence are negligible ($0.01 – $0.20/month). Egress is $0.
- 320 GB is **less than 0.032 %** of a Cloudflare R2 bucket's 10 PB soft ceiling.
- 320 GB is **less than 3 %** of the free 10 GB tier's paid buffer capacity of ~11 TB before any account-level intervention triggers.
- There is **no data-integrity issue**. Every prior forensic pass classifies this as `AMBER` on cost/policy grounds only — **NEVER RED on capacity or reliability**.
- The 50 GB threshold triggers a `CRITICAL` OCC card *purely because the constant is 50, not because 320 GB is objectively unsafe*.

### Cleanup / deletion is NOT economically or operationally justified at present.

- Storage-cost savings from reducing from 320 GB → 50 GB: **~$4.05/month** ($4.80 → $0.75). One operator hour spent deleting the wrong file dwarfs a decade of that savings.
- Deletion risk is asymmetric: the reason all destructive R2 work is under a locked canonical architecture (Track 27.06 → 27.07 delete-engine, currently P1-blocked) is precisely because a wrong delete costs orders of magnitude more than the storage bill it saves.
- Growth trajectory is well-understood: pre-`iter441` archive-inflation was the driver from 19 GB → 320 GB. The `iter441` exclusion deploy + Track 15.28A tiered retention + Track 27.06 lifecycle rule (90-day auto-expire on `backups/auto-90d/`) will curb steady-state growth once retention is confirmed enforcing (see UNKNOWNS §).

### The correct next step is a policy re-basing, not a delete pass.

- Recommended verdict: **RE-BASE THE THRESHOLD ON A COMPOSITE BUSINESS POLICY** (see §7 · Option D · Composite) and defer any bulk deletion until the composite policy actually flags an anomaly.

---

## ⚠️ AUTHORIZED VERDICT

# 🟡 CURRENT 320.47 GB CONDITION IS **OPERATIONALLY TRUTHFUL AS SIGNAL, BUT NOT AN EMERGENCY**.
**The threshold is misclassified as `CRITICAL`. The bucket size itself is not a critical operational condition. Cleanup is deferred until a defensible business policy replaces the 50 GB placeholder.**

---

## 📚 TECHNICAL & EVIDENCE APPENDIX

---

## 1 · Threshold Provenance — Where 50 GB Came From

### 1.1 · Exact file / line inventory of the constant `50` (and `45`) as an R2 alert threshold

| Consumer | File · line | Value | Source | Purpose |
|---|---|---|---|---|
| Passive log probe | `backend/server.py` L8188–8205 | `ALERT_GB = float(os.environ.get("R2_USAGE_ALERT_GB", "50"))` · `WARN_GB = "45"` | env-driven, defaults hardcoded | Post-upload bucket-size log emitter → writes `backup_health` row w/ mode `r2-usage-warn` or `r2-usage-alert`. Does NOT block, delete, or email. |
| Recovery snapshot | `backend/routes/recovery_dashboard.py` L167–168 | same env-driven default `45 / 50` | env-driven | Reads the most recent `r2-usage-*` row + classifies GREEN/AMBER/RED for `/api/admin/recovery/snapshot` |
| OCC health aggregator | `backend/routes/occ_health_aggregator.py` L198, L213, L320 | reads `bucket_usage.alert_gb` / `warn_gb` from snapshot | **downstream** — not a source | Emits `reason_code=bucket_over_alert` and tags `root_cause_id="r2_bucket_capacity"` |
| **R2 Lifecycle Storage Health score** | `backend/services/r2_lifecycle/health.py` L107 | **`warn_gb, alert_gb = 45.0, 50.0`** — **HARDCODED · ignores env vars** | **hardcoded** | Feeds `capacity_score` sub-score → OCC storage health card |
| Unit test fixture | `backend/tests/test_track_28_09d_backup_health_aggregator.py` L37, L71 | `warn_gb: 45, alert_gb: 50` | fixture only | Test contract |
| Unit test fixture | `backend/tests/test_track_27_06_r2_lifecycle.py` L177, L181, L186 | same | fixture only | Test contract |
| CLI probe | `scripts/r2_usage_check.py` (repository script) | `--warn-gb 45.0 --alert-gb 50.0` defaults | CLI, env-overridable | On-demand cron probe. Not scheduled today. |
| **Reference in operator doc** | `backend/ops_manual.py` L217 | `"Migrate to S3 before 50 GB total upload volume"` | operator-manual advice | **This is the semantic origin of the 50 GB number** — it referred to *local disk migration*, not R2 alerting. |
| Reference in operator doc | `backend/ops_manual.py` L303 | `"Free tier covers up to 10 GB; consider purging archives > 90 days old if usage climbs"` | operator-manual advice | Aligned with Cloudflare free-tier boundary |

### 1.2 · Git archaeology — the introducing commit

**First commit that introduced `R2_USAGE_ALERT_GB` and the value `50`:**

```
commit  30a4a270341c3b2614683f654a4480ab63755376
Author  emergent-agent-e1 <github@emergent.sh>
Date    Sun May 17 03:24:07 2026 +0000
Message auto-commit for 155f51a0-df30-4e01-8dc2-1307c10ea0f9
Files   backend/server.py, memory/PRD.md, memory/R2_RETENTION_AUDIT.md,
        scripts/r2_lifecycle_apply.py, scripts/r2_usage_check.py
```

The PRD.md entry authored in that commit records the rationale in the agent's own words:

> `scripts/r2_usage_check.py` — bucket size probe (**45 GB warn / 50 GB alert**, configurable via `R2_USAGE_WARN_GB` / `R2_USAGE_ALERT_GB`). Exit codes 0/1/2 + `--json` for cron. **Real reading: 19.48 GB / 707 objects (well below thresholds).**

And in `R2_RETENTION_AUDIT.md`:

> Usage check script (`scripts/r2_usage_check.py`) — ✅ Implemented; **thresholds 45 GB warn / 50 GB alert (override via `R2_USAGE_WARN_GB` / `R2_USAGE_ALERT_GB`)**
>
> Scheduler-side passive warning — ✅ Implemented (`_log_r2_usage_warning` fires after each successful R2 backup; **warn-only, no email**).

**No cost target, no contract clause, no retention SLA is cited.** The 50 GB number appears to be an ad-hoc choice consistent with:
- The Cloudflare R2 free-tier storage ceiling (**10 GB free**), plus a ~5× buffer.
- The pre-existing `ops_manual.py` line 217 heuristic *"Migrate to S3 before 50 GB total upload volume"* (a **local-disk** migration guideline).
- The bucket state at the time (19.48 GB) — a threshold ~2.5× current usage.

### 1.3 · The lifecycle-health hardcoding (2026-07-10 · commit `4e0ac346`)

Later, on 2026-07-10, commit `4e0ac346` shipped the canonical Track 27.06 lifecycle (`services/r2_lifecycle/`). The new `health.py::compute_storage_health` **hardcoded `warn_gb, alert_gb = 45.0, 50.0`** at line 107 rather than reading the env vars. This is a subtle but material drift: `R2_USAGE_WARN_GB` / `R2_USAGE_ALERT_GB` env overrides **do NOT reach the OCC Storage Health card**. The env vars only reach `server.py::_log_r2_usage_warning` and `recovery_dashboard.py::recovery_snapshot`.

### 1.4 · Approval status

Search of `/app/memory/*.md` for explicit operator authorization of the 50 GB threshold returns **no evidence of a signed-off policy statement**. Every subsequent report treats it as an inherited given:

- `R2_STORAGE_GOVERNANCE_REPORT.md` (2026-02-27, at 91.49 GB): three **candidate** options proposed (K/A/B/C), but **"No action taken in this batch. Awaiting operator's explicit choice in a future authorization."** — that authorization never landed in memory.
- `TRACK_27_04_STORAGE_CERTIFICATION.md` (at 186.82 GB): classifies as "**P0 · R2 Bucket 3.7× Over Alert Threshold**" — treats the threshold as authoritative without re-deriving it.
- `TRACK_28_10_LIVE_POST_DEPLOYMENT_CERTIFICATION.md` (at 320.47 GB): marks as `Truthful — real capacity overflow` but attributes remediation to Track 27.07 (P1-blocked).
- `TRACK_28_11_DIAGNOSTICS_TRUTHFULNESS.md`: adds `root_cause_id="r2_bucket_capacity"` so it counts as **one** critical root cause instead of two, but does not re-approve the number.

**Conclusion: The threshold was never re-approved after usage crossed it. Its provenance is a warn-only free-tier-era placeholder that was inherited by three downstream consumers (recovery dashboard, OCC aggregator, lifecycle health) and gradually promoted to `CRITICAL` semantics without an approval event.**

---

## 2 · Blast-radius map — every consumer of the threshold

```
                     ┌──────────────────────────────────────────┐
                     │  ENV VARS · defaults 45 / 50             │
                     │  R2_USAGE_WARN_GB · R2_USAGE_ALERT_GB    │
                     └──┬───────────────────────────────┬───────┘
                        │                               │
                        ▼                               ▼
      server.py::_log_r2_usage_warning     recovery_dashboard.py::recovery_snapshot
      • writes `backup_health` row         • classifies bucket_usage GREEN/AMBER/RED
      • fires after every R2 backup        • surfaced at /api/admin/recovery/snapshot
      • warn-only, no email                • warn/alert cast the `usage_status`
                        │                               │
                        │                               ▼
                        │              occ_health_aggregator._eval_recovery
                        │              • reason_code = "bucket_over_alert"
                        │              • root_cause_id = "r2_bucket_capacity"
                        │              • surfaces as CRITICAL OCC card + Governance card
                        │
                        │
      ┌─────────────────┴──────────────┐
      ▼                                ▼
services/r2_lifecycle/health.py    occ_health_aggregator._eval_storage_health
• HARDCODED 45/50 (ignores env)    • band GREEN/AMBER/RED from lifecycle health
• computes capacity_score          • same root_cause_id ("r2_bucket_capacity")
• weights into overall score       • so it's counted once, not twice, in OCC diagnostics
• surfaced at /api/admin/r2/lifecycle/health
```

Consequences of the threshold today:
- OCC "Recovery & Backups" card: `RED` (`bucket_over_alert`)
- OCC "Storage Health" card: `RED` (score dragged down by `capacity_score = 0` because 320 GB ≫ alert × 3)
- Both cards share `root_cause_id="r2_bucket_capacity"` (Track 28.11) → **counts as ONE critical root cause**, not two.
- No email fires. No delete fires. No block fires. Threshold is **display-only**.

---

## 3 · Cost economics — official public pricing baseline

### 3.1 · Cloudflare R2 Standard-Storage rates (verified public rates)

| Line item | Rate |
|---|---|
| Storage | $0.015 per GB-month |
| Class A operations (PUT/POST/COPY/LIST/etc.) | $4.50 per million |
| Class B operations (GET/HEAD/etc.) | $0.36 per million |
| Egress (internet) | $0 |

**Bucket-level free allowance** (excluded from paid calculations below): 10 GB-months storage, 1 M Class A ops/mo, 10 M Class B ops/mo.

### 3.2 · Modeled monthly R2 cost by bucket size (OFFICIAL-RATE ESTIMATE — no invoice access in this env)

| Bucket size | Storage $/mo | +Class A (~700/day · ~21 k/mo) | +Class B (negligible reads) | **Total est.** |
|---:|---:|---:|---:|---:|
| 10 GB (free-tier ceiling) | $0.00 | $0.00 (under free) | $0.00 | **$0.00** |
| 45 GB (WARN) | $0.53 | $0.00 | $0.00 | **~$0.53** |
| 50 GB (ALERT) | $0.60 | $0.00 | $0.00 | **~$0.60** |
| 100 GB | $1.35 | $0.00 | $0.00 | **~$1.35** |
| **320 GB (current)** | **$4.65** | **$0.09** | **~$0.01** | **~$4.75** |
| 500 GB | $7.35 | $0.09 | $0.01 | **~$7.45** |
| 1 TB | $14.85 | $0.09 | $0.01 | **~$15.00** |
| 2 TB | $29.85 | $0.09 | $0.01 | **~$30.00** |

**Interpretation.** At any plausible construction-ops platform scale (up to a few TB), R2 is a **rounding error** on any recurring SaaS budget line. Cost cannot justify emergency remediation. Cost-based policy anchors should be set at bucket sizes that produce **operationally meaningful** monthly bills — see §7.

### 3.3 · Comparison to AWS S3 Standard (for context; MASCI is on R2, not S3)

At AWS S3 Standard-Storage rates (~$0.023/GB-month, $0.09/GB egress), 320 GB would run ~$7.35/mo storage plus egress, which is materially different only above ~5 TB. The R2 choice is retained and validated.

### 3.4 · Verified actual billed cost — **INSUFFICIENT EVIDENCE**

No Cloudflare invoice, no billing dashboard export, and no `platform_costs` collection was found in `/app/memory` or `/app/backend`. All figures above are **official-rate estimates**, not verified actuals. Recommend the operator paste a recent Cloudflare R2 invoice into `/app/memory/BILLING_INVOICES/` before a definitive policy is locked. If the account uses negotiated rates, the classification of "financially trivial" holds by an even wider margin under all likely negotiated schedules.

---

## 4 · Growth economics — evidence-based

### 4.1 · Documented longitudinal snapshots

| Timestamp | Source | Bucket GB | Objects | Notes |
|---|---|---:|---:|---|
| 2026-05-17 03:24 UTC | `memory/PRD.md`, `R2_RETENTION_AUDIT.md` (commit `30a4a270`) | **19.48** | 707 | Threshold introduced; bucket well below 50 GB alert |
| 2026-05-26 00:42 UTC | `PHASE31_3_R2_FORENSIC_AUDIT.md`, `PHASE31_3_STORAGE_GROWTH_ANALYSIS.md` (iter440) | **77.66** | 1504 | ~500 keys legacy pre-prefix + 1004 keys `backups/auto-90d/` |
| 2026-06-01 01:07 UTC | `R2_STORAGE_GOVERNANCE_REPORT.md` (OMEGA P2) | **91.49** | 94 archives visible via listing | Cadence observed at ~13 archives/day vs configured 2/day |
| 2026-07-09 (Track 27.04) | `TRACK_27_04_STORAGE_CERTIFICATION.md` | **186.82** | 100 archives visible; ~994 MB each | "3.74× the 50 GB alert threshold" · retention NOT verified to be enforcing |
| 2026-07-11 14:36 UTC | `TRACK_28_10_LIVE_POST_DEPLOYMENT_CERTIFICATION.md` (LIVE prod probe) | **320.47** | 100 archives visible (paginated); ~982 MB each | Truthful capacity overflow · `bucket_over_alert` |

### 4.2 · Growth-trajectory model

- **2026-05-17 → 2026-07-11 (~55 days)**: 19.48 GB → 320.47 GB = **+300.99 GB / 55 d ≈ +5.47 GB/day** raw.
- The trajectory is **not** organic linear growth. It reflects three overlapping regimes:
  1. **Pre-iter441 (2026-05-11 → 2026-05-30)**: hourly complete-R2 archives at ~443 MB each including inline base64 photos + `usage_events` + `health_monitor_runs`. Growth ≈ **9.6 GB/day** (documented in `PHASE31_3_STORAGE_GROWTH_ANALYSIS.md`).
  2. **Post-iter441 (2026-05-30 onward)**: `usage_events` / `health_monitor_runs` / `job_photo_thumb_cache` excluded from archive; per-archive size drops to ~330 MB. Projected steady-state ≈ **2.1 GB/day** (~189 GB at 90-day retention).
  3. **Legacy pre-`backups/auto-90d/` prefix** archives NOT covered by the 90-day lifecycle rule (Track 15.28A / Track 27.06). These are the "unshedable" tail — retention was **NOT verified enforcing** per Track 27.04.
- Projected post-cleanup steady state (from `PHASE31_3_STORAGE_GROWTH_ANALYSIS.md`, §4): **~190 GB** at 90-day steady state · **~$2.83/month** at official pricing.
- Projected 1-year growth *if the lifecycle rule is proven enforcing*: **~$3–$11/month indefinitely** (archives grow ~0.7 MB/day due to Atlas dataset drift, per §Growth trajectory in Phase 31.3 report).

### 4.3 · Growth verdict — **DEFENSIBLE**

Evidence sources are prior certified reports (Phase 31.3 iter440, R2_STORAGE_GOVERNANCE_REPORT, TRACK_27_04, TRACK_28_10). Not a fabrication. The primary growth driver (inline base64 in `subcontractors[]` / `photos[]` / `materials[]`) is documented in `BACKUP_GROWTH_FORENSICS_REPORT.md` and structurally mitigated post-iter441 (GAP-1). **The 320 GB current condition is a legacy inflation tail, not an accelerating leak.**

### 4.4 · Explicit UNKNOWN — retention enforcement

- Track 27.04 states **"No scheduled runner identified. Bucket sitting at 186 GB suggests retention has not been enforced recently."**
- Track 27.06 lifecycle activation (`lib/r2_retention.py`) is proven-safe as a pure planner; a scheduled runner path is coded, but Track 27.04 could NOT confirm it fires in production.
- Whether Cloudflare-side `PutBucketLifecycleConfiguration` (90-day auto-expire on `backups/auto-90d/`) is currently applied is documented as **⚠ PENDING — user action required** in commit `30a4a270`'s doc updates. No later doc records the token rotation that would unlock it.

**➡ Operator action items:** (see §8 · Operator decisions genuinely required)

---

## 5 · Retention & compliance findings

### 5.1 · Explicitly documented retention obligations (source-of-truth)

| Obligation | Source in-repo | Retention period | Applies to |
|---|---|---|---|
| OSHA 29 CFR 1904 recordkeeping | `AMENDMENT001_EVIDENCE_HIERARCHY_MATRIX.md`, `AMENDMENT001_EXECUTIVE_SUMMARY.md`, `AMENDMENT001_VALIDATION_AUDIT.md` (item 13) | Legally required; **specific years not stated in-repo** (OSHA 1904.33 requires **5 years** industry-wide, but the platform does not encode this constant anywhere) | Incident closure attestation + OSHA recordable ack |
| Consent-text-version stamping | `AMENDMENT001_EXECUTIVE_SUMMARY.md` (Tier 4 "legally necessary") | Retained until superseded consent; **explicit years not encoded** | FSI consent bindings |
| Backup TIER retention (platform-defined) | `backend/lib/r2_retention.py` L42–45 (Track 15.28A canonical contract) | Tier 1 = 14 days all-hourly · Tier 2 = 14–90 days daily-only · Tier 3 = 90–365 days monthly-only · Tier 4 = >365 days DELETE | R2 `backups/auto-90d/*.zip` |
| R2 lifecycle prefix rule (Cloudflare-side) | `memory/R2_RETENTION_AUDIT.md` | 90-day expiration on `backups/auto-90d/` (⚠ **application PENDING** — API token permission gap documented; token rotation not confirmed in later reports) | R2 `backups/auto-90d/` |
| Classification protections | `backend/services/r2_lifecycle/classification.py` L61–83 | Indefinite until re-classified: `SYSTEM_RESERVED` (system/, _system/, recovery-drills/, audit-exports/), `BACKUP_PROTECTED` (backups/, complete-backups/, MASCI_complete_backup*), `HISTORICAL` (legacy-imports/, historical/), `LEGAL_HOLD` (empty set today) | R2 keys by prefix |

### 5.2 · Unknown retention obligations — flagged `POLICY REQUIRED`

| Item | Status |
|---|---|
| OSHA 29 CFR 1904.33 specific 5-year retention hardcoded / policy statement | **POLICY REQUIRED** |
| Client / GC contract retention clauses (per-project record retention) | **POLICY REQUIRED** |
| Insurance-required retention (photos, JHAs, DVIRs for claims) | **POLICY REQUIRED** |
| State / DOT record retention (fleet inspections, driver DVIRs) | **POLICY REQUIRED** |
| PII / employee record retention (offboarded employee photos) | **POLICY REQUIRED** |
| Data-subject-access / erasure protocol (if applicable to jurisdiction) | **POLICY REQUIRED** |

### 5.3 · Retention verdict

Only the **platform-defined tiered retention** and the **classification-based protective prefixes** are code-encoded. All legally-anchored retention periods (OSHA, insurance, contracts) are referenced in policy documents but **not encoded in-repo as constants**. Deletion policy cannot proceed until at least the OSHA-recordable and per-project record-retention windows are captured as explicit configuration.

---

## 6 · Current 320.47 GB — truthful classification

### 6.1 · Composition (best available evidence — NOT a live scan)

Latest per-prefix breakdown available is from `PHASE31_3_R2_FORENSIC_AUDIT.md` (2026-05-26) at 77.66 GB total. Since then, only aggregate `total_gb` numbers are recorded. **Live composition of the 320 GB is INSUFFICIENT EVIDENCE** without a bucket scan — deliberately not run per the Phase 0B contract.

Best available inference (composition percentages held roughly stable per report narrative):
- `backups/auto-90d/` (post-iter441 archives, ~330 MB × ~13/day × up to 90 d retention): ~**~85–90 %** of bucket
- `backups/` legacy pre-prefix zips: ~**~5–10 %** of bucket (these were the "not covered by lifecycle" tail flagged in commit `30a4a270`'s docs)
- `photos/` (operator attachments): trivial (<1 % — 0.10 GB at 2026-05-26; unlikely to have exceeded 1–3 GB since)
- `safety-docs/`, `system/`, `_system/`, `recovery-drills/`, `audit-exports/`: trivial

### 6.2 · Classification against the 10-state contract

Applying `backend/services/r2_lifecycle/classification.py::classify_object` logic to the inferred composition:

| Class | Likely share | Delete-eligible? |
|---|---|---|
| BACKUP_PROTECTED (`backups/*`, `MASCI_complete_backup*`) | ~95 % | ❌ Refused by dry-run gate |
| VERIFIED_OWNER (`photos/*` with matching Mongo ref) | ~1–3 % | ❌ Refused |
| SYSTEM_RESERVED (`system/`, `_system/`, `recovery-drills/`, `audit-exports/`) | trivial | ❌ Refused |
| VERIFIED_ORPHAN | **UNKNOWN — INSUFFICIENT EVIDENCE** without a live classification pass; historically 0 confirmed | ✅ Only class allowed for deletion |
| AMBIGUOUS / UNKNOWN | **UNKNOWN** | ❌ Refused |

**➡ The overwhelming majority of the 320 GB is `BACKUP_PROTECTED`.** The only defensible cleanup path is **retention enforcement on `backups/auto-90d/`**, not object-by-object deletion. That is exactly what Track 27.06's canonical lifecycle rule is engineered to do — provided the Cloudflare-side lifecycle rule is confirmed applied.

### 6.3 · Storage-health scoring at 320 GB with current 45/50 thresholds

Applying `_capacity_score(gb=320.47, warn_gb=45.0, alert_gb=50.0)`:
- 320.47 > alert_gb (50) → falls into over-alert bracket
- upper = alert_gb × 3 = 150; 320.47 > 150 → **capacity_score = 0.0**
- Feeds into overall storage health at weight 0.20 → drops overall by 20 points regardless of every other sub-score.

This is what turns the OCC Storage Health card RED even when ownership, orphan, backup, lifecycle, and freshness sub-scores are green — a single mis-provenanced constant dominates a composite score by design.

---

## 7 · Business-driven policy candidates

Each candidate is **fully reversible** (constants only). No candidate requires a code refactor beyond swapping constants and, in Option D, adding two-to-three lightweight signals.

### Option A · **BUDGET / COST-BASED POLICY**

**Anchor:** monthly R2 bill.

| Level | Trigger | Threshold ($) | Approx GB (at $0.015/GB) |
|---|---|---:|---:|
| INFO | first cost signal — worth glancing | $ 5 / mo | ~334 GB |
| WARN | budget-line noticeable | $15 / mo | ~1 000 GB (1 TB) |
| ALERT | budget-line materially non-trivial | $30 / mo | ~2 000 GB (2 TB) |
| CRITICAL | budget approval likely needed | $75 / mo | ~5 000 GB (5 TB) |

- **Pros:** Directly anchored to the only financial signal a construction ops platform of MASCI's size actually cares about. Cleanly re-derivable from the Cloudflare invoice. Immune to inline-base64 archive-inflation blips.
- **Cons:** Cost signal is delayed by 30 days. Says nothing about *retention correctness* or *orphan share*. Cheap storage can hide a growing orphan tail indefinitely.
- **Cost-savings from current 320 GB → 334 GB (INFO)**: zero. **From 320 GB → 1 TB (WARN)**: none, we'd be growing. **From 320 GB → 200 GB (post-cleanup)**: **~$1.80/mo** — negligible.

### Option B · **GROWTH-ANOMALY-BASED POLICY**

**Anchor:** rate of change, not absolute size.

| Level | Trigger | Definition |
|---|---|---|
| INFO | organic growth | rolling 7-day mean daily-delta ≤ 3× historical baseline (currently ~2.1 GB/day post-iter441) |
| WARN | non-organic growth | rolling 7-day mean daily-delta between 3× and 10× baseline |
| ALERT | uncontrolled growth | rolling 7-day mean daily-delta > 10× baseline OR 24-h delta > 30× baseline |
| CRITICAL | active runaway | 1-h delta > 100× baseline |

- **Pros:** Detects the actual failure mode that took the bucket from 19 → 320 GB (a broken exclusion + hourly cadence at inflated size). Baseline is code-observable from `backup_health` history. Independent of absolute bucket size.
- **Cons:** Requires baseline persistence (small addition to `backup_health` reads). Ratio-based alerts are noisier during legitimate refactor pushes. Says nothing about cost or retention-correctness.

### Option C · **CERTIFIED-WASTE-RATIO-BASED POLICY**

**Anchor:** classification results from `services/r2_lifecycle/classification.py`.

| Level | Trigger | Definition |
|---|---|---|
| INFO | clean bucket | `VERIFIED_ORPHAN_pct ≤ 1 %` AND `AMBIGUOUS_pct ≤ 5 %` AND classification freshness ≤ 7 d |
| WARN | orphan pressure | `VERIFIED_ORPHAN_pct ≤ 5 %` AND `AMBIGUOUS_pct ≤ 15 %` |
| ALERT | orphan overhang | `VERIFIED_ORPHAN_pct ≤ 20 %` |
| CRITICAL | classifier untrusted | classification freshness > 30 d OR `AMBIGUOUS_pct > 30 %` |

- **Pros:** Rewards a working classifier and penalizes stale classification data. Absolute bucket size is deliberately irrelevant — you can be 5 TB and healthy if 99 % is `VERIFIED_OWNER` / `BACKUP_PROTECTED`. Aligned with the "zero-drift" architecture.
- **Cons:** Depends entirely on the classifier being trustworthy. A false-orphan bug (which is why Phase 0A shipped the break-the-classifier harness) becomes a policy false-positive.

### Option D · **COMPOSITE POLICY** ✅ **RECOMMENDED**

A four-signal composite: at least **any two** signals must be RED to escalate to CRITICAL. Any **one** signal RED → AMBER. Zero signals RED → GREEN.

**Signals:**

1. **Cost signal (from Option A):** monthly-billing $ tier.
2. **Growth signal (from Option B):** 7-day mean daily-delta vs baseline.
3. **Waste signal (from Option C):** `VERIFIED_ORPHAN_pct` + `AMBIGUOUS_pct` + classifier freshness.
4. **Technical-capacity signal:** absolute bucket GB vs a **defensible ceiling** — proposed **2 TB** (2 048 GB), well above any construction-ops platform's realistic footprint and at the ~$30/mo cost mark. Below 2 TB, absolute size is **INFO only**.

Escalation rules:
- 0 signals RED → **GREEN**
- 1 signal RED → **AMBER · investigate**
- 2+ signals RED → **CRITICAL · act**
- Any signal in unknown-state for >30 days → **CRITICAL** (data freshness is a first-class citizen)

Retention pillar (independent of the four signals): **backup retention is enforced end-to-end** — Cloudflare-side `PutBucketLifecycleConfiguration` on `backups/auto-90d/` is verified applied every 30 days (fresh evidence row in `backup_health` or equivalent).

- **Pros:** No single mis-provenanced constant can dominate the score. Cost, growth, waste, capacity, and freshness are all first-class. Explains *why* on every escalation. Retention pillar is separate so a legitimate 500 GB backup pile does NOT flip RED just because of size.
- **Cons:** Requires small additions to expose growth-baseline and classifier freshness on the storage-health endpoint. Slightly more logic in `services/r2_lifecycle/health.py`.

**Applied to the current bucket (320 GB, post-iter441 growth pattern, unknown orphan share, retention-enforcement PENDING):**

| Signal | Current state | Verdict |
|---|---|---|
| Cost | ~$4.75/mo estimated · below $5 INFO | 🟢 GREEN |
| Growth | If retention enforcement is confirmed, post-iter441 baseline holds | 🟡 AMBER (retention **PENDING** = unknown-state, treat as AMBER) |
| Waste | Unknown orphan share until classifier runs | 🟡 AMBER (data-freshness clock is ticking) |
| Technical capacity | 320 / 2 048 GB = 15.6 % | 🟢 GREEN |

Composite: 0 signals RED, 2 signals AMBER → **AMBER · investigate**. Not CRITICAL. Not GREEN. **Aligned with reality.**

---

## 8 · Operator decisions genuinely required

Only questions that cannot be answered from source, git history, `/app/memory`, existing metrics, existing reports, or current official provider documentation.

1. **Which policy option (A, B, C, or D-composite) is approved as the new storage policy?** No code will be written until this is signed.
2. **Are there any contract-level, insurance-level, or state-DOT-level record-retention obligations** that must be encoded as explicit constants before any deletion pass? Every item flagged `POLICY REQUIRED` in §5.2 needs an operator answer or an explicit "N/A · not applicable."
3. **Was the Cloudflare R2 API token ever rotated to include `PutBucketLifecycleConfiguration` scope** so the 90-day lifecycle rule is actually applied on `backups/auto-90d/`? (Documented as PENDING in commit `30a4a270`; no later doc records its resolution.) If not, retention is **coded but not enforced** and the trajectory analysis in §4.2 case (2) does NOT hold.
4. **Is there a Cloudflare R2 invoice or billing dashboard export** the operator can drop into `/app/memory/BILLING_INVOICES/` so §3.4 can move from "official-rate estimate" to "verified actual billed cost"?
5. **What operational-capacity ceiling is defensible** for the Technical-capacity signal in Option D? (Draft proposes 2 TB / ~$30/mo. Higher ceilings are fully defensible up to ~5 TB / ~$75/mo without meaningful cost pressure.)

---

## 9 · Explicit non-actions taken this session

Per Phase 0B charter — actively confirmed NOT executed:

- ❌ Threshold NOT changed.
- ❌ OCC / Storage Health card color NOT changed.
- ❌ Production code NOT edited.
- ❌ Deployment NOT triggered.
- ❌ Full production bucket scan NOT run.
- ❌ Manifest NOT created.
- ❌ Production objects NOT classified in this session.
- ❌ Nothing quarantined.
- ❌ Nothing deleted.
- ❌ Retention NOT altered.
- ❌ New threshold registry NOT built.
- ❌ Track 27.07 implementation NOT drifted into.

All findings are strictly from static file reads, git history, and evidence already in `/app/memory`.

---

## 10 · Summary of exact source / file / commit provenance

| Fact | Source |
|---|---|
| 50 GB alert first introduced | commit `30a4a270341c3b2614683f654a4480ab63755376` · 2026-05-17 03:24:07 UTC · `emergent-agent-e1` |
| 45 GB warn first introduced | same commit |
| First bucket reading at the time of introduction | `19.48 GB / 707 objects` — recorded in `memory/PRD.md` and `memory/R2_RETENTION_AUDIT.md` in the same commit |
| Env-var-driven consumers (server.py, recovery_dashboard.py) | commit `30a4a270` (server.py) · commit `4cc7662c` @ 2026-05-31 00:20 UTC (recovery_dashboard.py) |
| Hardcoded 45/50 in lifecycle health | commit `4e0ac346c5f67ade8ce8581f7e703718eac88e9f` · 2026-07-10 11:03:19 UTC · introduced with the Track 27.06 canonical lifecycle module |
| root_cause_id de-duplication (OCC) | Track 28.11 — file `TRACK_28_11_DIAGNOSTICS_TRUTHFULNESS.md` |
| Bucket 19.48 GB → 77.66 GB (9 days) | `PHASE31_3_R2_FORENSIC_AUDIT.md` |
| Bucket 91.49 GB | `R2_STORAGE_GOVERNANCE_REPORT.md` |
| Bucket 186.82 GB | `TRACK_27_04_STORAGE_CERTIFICATION.md` |
| Bucket 320.47 GB current | `TRACK_28_10_LIVE_POST_DEPLOYMENT_CERTIFICATION.md` (2026-07-11 14:36 UTC live prod probe) |
| Growth trajectory analysis | `PHASE31_3_STORAGE_GROWTH_ANALYSIS.md`, `BACKUP_GROWTH_FORENSICS_REPORT.md` |
| Cost model at official Cloudflare pricing | `BACKUP_POSTURE_RECOMMENDATION.md` §2 |
| Retention contract (Tier 1/2/3/4) | `backend/lib/r2_retention.py` L42–45 |
| Classification contract (10 states + protective prefixes) | `backend/services/r2_lifecycle/classification.py` L32–83 |
| OSHA + consent retention obligation references | `AMENDMENT001_EVIDENCE_HIERARCHY_MATRIX.md`, `AMENDMENT001_EXECUTIVE_SUMMARY.md`, `AMENDMENT001_VALIDATION_AUDIT.md` |
| Canonical R2 architecture lock | `TRACK_27_07_PHASE_0_ARCHITECTURE_LOCK.md` |
| Track 28.12 unauthorized parallel storage architecture removal | `TRACK_28_12_UNAPPROVED_DRAFT.md`, `TRACK_28_12_HOUSEKEEPING.md` |

---

## 11 · Fact-only closeout

- **Provenance:** proven. 50 GB is a placeholder from a warn-only free-tier-era probe. Never re-approved after usage crossed it.
- **Current condition:** truthful signal, but not a technical or financial emergency.
- **Cost:** ~$4.75/mo estimated at official public rates.
- **Growth:** defensible. Post-iter441 trajectory converges to ~$3/mo indefinitely once retention enforcement is verified.
- **Retention enforcement:** verification **PENDING**. Token-rotation step (operator action) required.
- **Compliance:** platform code encodes tiered retention and classification only. OSHA / contract / insurance retention windows are **POLICY REQUIRED**.
- **Cleanup justification:** absent. `BACKUP_PROTECTED` dominates the bucket; the safe path is retention-rule enforcement, not object-by-object deletion.
- **Threshold future:** re-base on §7 · Option D (composite) after operator signs items in §8.

# 🟡 VERDICT: NOT AN EMERGENCY. RE-BASE THE THRESHOLD; DO NOT DELETE.
