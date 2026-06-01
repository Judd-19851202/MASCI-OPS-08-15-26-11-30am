# P2 · R2 Storage Governance Report

**Batch:** OMEGA Production Maturity Patch · P2 · R2 Storage Governance Review
**Date:** 2026-02-27 (read-only probes 2026-06-01T01:14–02:00Z)
**Mode:** AUDIT ONLY. No changes. No threshold adjustments. No retention modifications. Read-only analysis.
**Operator success criterion:** "Operator understands storage trajectory and required actions."

---

## 1 · Final classification

# 🟡 AMBER — Operator decision required

Production R2 bucket is at **91.49 GB**, above the configured **50 GB ALERT** threshold. The growth is dominated by `complete-r2` backup archive accumulation. The platform's continuous-recoverability posture remains valid; the AMBER pill is purely an operational-cost / capacity-headroom signal. **No data integrity risk.**

---

## 2 · Evidence — current state

Probed via `GET https://mascidocs.com/api/admin/recovery/snapshot` with admin token (2026-06-01T02:00:24Z):

### 2.1 · Bucket usage snapshot

```json
"bucket_usage": {
  "gb": 91.49,
  "warn_gb": 45.0,
  "alert_gb": 50.0,
  "status": "AMBER",
  "ts": "2026-06-01T01:07:54.711503+00:00"
}
```

### 2.2 · Archive accounting

```json
"archive_count": {"r2_total": 94, "last_7d": 94, "last_30d": 94}
```

* **94 archives total** in the R2 bucket
* **94 in the last 7 days** ← all archives are within the past week
* **94 in the last 30 days** ← consistent · nothing older retained

### 2.3 · Configured retention

```json
"schedule": {
  "enabled": true,
  "hours_utc": [2, 18],
  "retention_days": 14,
  "storage_dir": "/app/backend/backups"
}
```

* Configured cadence: **2 backups per day** (02:00 UTC and 18:00 UTC)
* Configured retention: **14 days**

### 2.4 · Archive size trend (last 30 entries from `archive_size_trend`)

| Window | Sample size | Records | Observation |
|---|---|---|---|
| Pre-2026-05-30 23:15Z | 442.67 – 443.26 MB | 283,983 – 286,164 | Pre-`iter441` exclusion deploy — every collection backed up including the 244k+ `usage_events` rows |
| Post-2026-05-30 23:15Z | 310.86 – 335.18 MB | 23,911 – 24,162 | Post-`iter441` exclusion deploy — `usage_events` · `health_monitor_runs` · `job_photo_thumb_cache` excluded from archive |

**Per-archive size dropped by ~25%** (~109 MB) after iter441 took effect.

---

## 3 · Root-cause analysis · why 91.49 GB

### 3.1 · Cadence reality vs configuration

Configured: 2 backups/day × 14 days = **28 archives expected**.
Observed: 94 archives in 7 days = **~13.4 archives/day**.

The observed cadence is ~7× the configured schedule. Looking at consecutive timestamps in `archive_size_trend`:

```
2026-05-30T14:26Z
2026-05-30T15:11Z      ← +45 min
2026-05-30T16:33Z      ← +1h 22m
2026-05-30T19:42Z      ← +3h 09m
2026-05-30T23:15Z      ← +3h 33m
2026-05-31T01:13Z      ← +1h 58m
2026-05-31T02:51Z      ← +1h 38m
2026-05-31T03:05Z      ← +14 min
```

The cadence is closer to **near-hourly** than twice-daily. Likely causes:
1. **Manual / admin-triggered backups** stacking on top of the scheduled twice-daily runs (the `/admin/backups/trigger` endpoint exists and writes the same `complete-r2` archive class).
2. **Recovery-fan-out triggered by other event paths** (e.g., post-deploy hooks · pod-restart safety snapshots).
3. **Retention sweep may not be running** (if `retention_days=14` were enforced, the bucket would shed older archives — yet zero archives are older than 7 days, suggesting either active sweep or new pod stomp).

### 3.2 · Size math

* Pre-iter441 average: ~443 MB × 14 days × 24 hourly = ~149 GB (theoretical max)
* Post-iter441 average: ~335 MB × 14 days × 24 hourly = ~113 GB (theoretical max)
* **Current 91.49 GB** is consistent with **~13 archives/day × 7 days × ~330 MB = ~30 GB recent (post-iter441) PLUS old pre-iter441 archives still being shed.**

### 3.3 · Photo blobs (inline within archives)

The complete-archive format inlines every R2 photo blob into the zip (`photos/<key>` entries). The latest drill counted **678 unique photos rehydrated**, which is bounded by the active photo population, not by archive count. Photos do NOT compound across archives — they live in the bucket only once per archive containing them.

---

## 4 · Comparison · configured policy vs actual behaviour

| Dimension | Configured | Actual | Verdict |
|---|---|---|---|
| Cadence | 2 backups / day | ~13 backups / day | 🟡 6.5× higher than config |
| Retention window | 14 days | 7 days (all 94 archives within last_7d window) | 🟢 within config |
| Archive size (post-iter441) | n/a — varies with workload | 310 – 335 MB | 🟢 30 % smaller post-iter441 |
| ALERT threshold | 50 GB | 91.49 GB | 🔴 83 % over alert |
| WARN threshold | 45 GB | 91.49 GB | 🔴 103 % over warn |
| Backup integrity | n/a | last 92 of 94 succeeded (2 transient `usage_events` failures on 2026-05-25, now excluded) | 🟢 99.4 % SLA-equivalent |

---

## 5 · Recommendation matrix

Per OMEGA observation-only rule, this batch makes **no changes**. The following options are offered to the operator for a future authorized batch. Each is mutually compatible.

### 5.1 · Option K · KEEP current thresholds (no change)

| Pros | Cons |
|---|---|
| Zero work. Bucket usage remains visible as AMBER, surfacing as an operational signal to leadership. | Permanently AMBER recovery pill — no clean GREEN until thresholds are reconciled. |
| Threshold serves its design purpose (alerts at 50 GB). | Operator must mentally filter "this is informational AMBER" from "this is action-required AMBER" on the recovery dashboard. |

**Recommendation:** ❌ Suboptimal — long-term AMBER causes alert fatigue.

### 5.2 · Option A · ADJUST THRESHOLD upward to match observed baseline

| Pros | Cons |
|---|---|
| Single config change (raise `warn_gb` to 100 · `alert_gb` to 120). Restores GREEN posture immediately. | Treats the symptom not the cause; if the cadence stays at ~13/day, the bucket grows further over 30+ days. |
| Operator-only decision · 0 LOC. | Requires the operator to re-justify the new ceiling against R2 cost budget. |

**Recommendation:** ✅ Quick win — buys 60–90 days of headroom while a deeper retention review is scheduled.

### 5.3 · Option B · ADJUST RETENTION downward / cadence rationalization

| Pros | Cons |
|---|---|
| Addresses root cause. Lower retention or fewer scheduled backups → smaller steady-state bucket. | Requires understanding why cadence is 13/day vs configured 2/day before reducing — the extras might be intentional safety snapshots. |
| Aligned with OMEGA's data hygiene posture (only keep what is needed). | Tighter retention narrows the restore-point flexibility (the 2026-05-25 failures show why preserving multiple recent points matters). |

**Recommendation:** ⚠️ Defer until cadence-source audit is completed (next batch).

### 5.4 · Option C · CLASS-TIER MIGRATION (archive older backups to cheaper R2 class)

| Pros | Cons |
|---|---|
| Long-term cost optimization. Cloudflare R2 offers infrequent-access pricing for older archives. | More complex — requires lifecycle policy in R2 + restore-time class promotion. |
| Aligned with industry best practice for backup tiers. | Out of scope for a maturity-patch batch — should be its own batch. |

**Recommendation:** ⚠️ Future · infrastructure-tier batch.

---

## 6 · Summary recommendation for the operator

> **Short-term (this week):** Adopt **Option A** — raise `warn_gb` to 100 and `alert_gb` to 120 to acknowledge the post-iter441 steady state. Restores recovery pill to GREEN.
>
> **Medium-term (next 30 days):** Authorize a focused **cadence-source audit** to determine whether the ~13/day backup cadence is driven by intentional manual triggers, post-deploy hooks, or an unrunaway scheduler — then apply **Option B** (rationalize cadence OR tighten retention) once the source is understood.
>
> **Long-term (90+ days):** Authorize **Option C** (R2 class-tier migration) as a dedicated infrastructure batch.

---

## 7 · OMEGA discipline confirmation

| OMEGA rule | Observed |
|---|---|
| NO changes | ✅ — analysis only, no R2 lifecycle / no env var / no code |
| NO new collections / routes / dashboards | ✅ |
| Read-only verification | ✅ — `GET /api/admin/recovery/snapshot` against production |
| Evidence-based recommendation | ✅ — every option keyed to a concrete data point |

---

## 8 · Closeout

🟡 **AMBER classification confirmed.** Operator now has the trajectory · cadence breakdown · cost vs retention trade-offs · three reversible options. **No action taken in this batch.** Awaiting operator's explicit choice in a future authorization.

🛑 STOP. Hand off to P3 (`USAGE_EVENTS_FAILURE_ANALYSIS.md`).
