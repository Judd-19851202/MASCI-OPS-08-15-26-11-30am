# TRACK 15.24 — CAPACITY FORECAST MODEL

**Date:** 2026-06-18
**Trust mode:** 🟢 measured baselines · 🟠 modeled assumptions stated inline · 🔴 operator-only metrics flagged.

This document is the spreadsheet that backs the cost forecast in `TRACK_15_24_PLATFORM_COST_AND_SCALING_AUDIT.md`. It lists every multiplier, every assumption, and every measured baseline so an operator can challenge any number and re-derive the result.

---

## 1 · Measured baselines (🟢 from running pod, 2026-06-18)

### 1.1 Population

| Symbol | Meaning | Value |
|---|---|---|
| `U₀` | Portal user accounts (across user_directory + FL + shop + safety + dispatch) | 228 |
| `E₀` | Employee roster (`employees` collection) | 395 |
| `E_active` | Active employees only | 383 |
| `A₀` | Current adoption (per operator) | **0.225** (midpoint 20–25 %) |
| `E_target` | Eventual full employee count at 100 % adoption | `E₀ / A₀` = **1,756** |
| `U_target` | Eventual portal accounts at 100 % | `U₀ / A₀` = **1,013** |

### 1.2 Data volumes

| Symbol | Meaning | Value |
|---|---|---|
| `Mongo₀` | Atlas `dataSize` | 184.62 MiB |
| `MongoStorage₀` | Atlas `storageSize` (compressed) | 268.53 MiB |
| `MongoIdx₀` | Atlas index size | 51.86 MiB |
| `R2₀` | R2 bucket total | 285.45 GiB |
| `R2_backups₀` | R2 backups prefix | 283.06 GiB |
| `R2_photos₀` | R2 photos + drill-photos | 2.39 GiB |
| `Docs₀` | Total Mongo documents | 504,006 |
| `DR_total` | Lifetime daily_reports | 1,032 |
| `DR_30d` | DRs created in last 30 d | 977 |
| `Photos_mongo₀` | `job_photos` rows | 2,348 |
| `Photos_r2₀` | R2 photo objects | 7,610 |

### 1.3 Daily rates (🟢, computed from 7-day window)

| Symbol | Meaning | Value |
|---|---|---|
| `r_DR` | Daily reports created per day | **27 / day** |
| `r_notif` | Notifications created per day | 321 / day |
| `r_usage` | usage_events / day | 14,571 / day |
| `r_audit` | audit_events / day | 107 / day |
| `r_health` | health_monitor_runs / day | 892 / day |
| `r_session` | directory_sessions / day | 175 / day |
| `r_backup_growth` | R2 backup GiB / day (recent 7 d) | **14.5 GiB / day** |

### 1.4 Pod (Emergent) actuals

| Symbol | Meaning | Value |
|---|---|---|
| `RAM_cap` | cgroup memory hard cap | 8.00 GiB |
| `RAM_used` | cgroup memory current | 3.10 GiB (38.8 %) |
| `CPU_cap` | cgroup CPU quota | 2.00 vCPUs |
| `Disk_used` | overlay disk used | 27 GiB / 104 GiB (26 %) |

---

## 2 · Scaling multipliers (🟠 model assumptions, stated explicitly)

### 2.1 Adoption multiplier `M_adopt(stage)`

| Stage | Adoption % | `M_adopt` = stage / `A₀` |
|---|---:|---:|
| Today | 22.5 | 1.000 |
| 50 % | 50 | 2.222 |
| 75 % | 75 | 3.333 |
| 100 % | 100 | **4.444** |

### 2.2 Feature-engagement multiplier `M_feature(surface)` (on top of adoption)

Rationale: when a tool stops being optional and becomes the system of record, per-user activity rises. Multipliers below are the *additional* uplift beyond simply having more users.

| Surface | `M_feature` | Why |
|---|---:|---|
| daily_reports | 1.7 | Today: 6 active filers @ 22 % adoption. Tomorrow: every super, PM, foreman files daily. |
| photos (R2) | 1.5 | More JHAs, drills, incident photos as the platform becomes default. |
| notifications | 1.5 | Per-user threshold settings + cross-portal awareness rises. |
| usage_events | 1.3 | Already aggressive instrumentation today. |
| audit_events | 1.0 | Strictly user-action-driven; linear with users. |
| sessions | 1.0 | One session per user per day. |
| Mongo dataSize (composite) | 1.7 | Dominated by daily_reports + incidents (inline photos). |
| R2 backups | follows dataSize | Zip = DB + R2 manifest; grows with both. |
| LLM consumption | **🔴 operator decides** | Zero today. If AI features ship → wildcard. |

### 2.3 Combined scaling factor `S(surface, stage)`

`S = M_adopt(stage) × M_feature(surface)`

| Surface | 50 % | 75 % | **100 %** |
|---|---:|---:|---:|
| daily_reports | 3.78 | 5.67 | **7.55** |
| photos | 3.33 | 5.00 | **6.67** |
| notifications | 3.33 | 5.00 | **6.67** |
| usage_events | 2.89 | 4.33 | **5.78** |
| audit_events | 2.22 | 3.33 | **4.44** |
| Mongo dataSize | 3.78 | 5.67 | **7.55** |

---

## 3 · Projected workload at each adoption stage

### 3.1 Daily reports

| Stage | DR/day | DR/year | DR cumulative over 3 yrs (assume year 1 at stage, year 2+3 at next stage) |
|---|---:|---:|---:|
| Today (22 %) | 27 | 9,855 | — |
| 50 % | 102 | 37,230 | — |
| 75 % | 153 | 55,845 | — |
| 100 % | **204** | **74,460** | ~223,000 over 3 yrs if 100 % all 3 |

### 3.2 Mongo dataSize (assuming current avg doc sizes hold)

| Stage | `dataSize` | vs 10 GiB soft cap | vs M10 disk (10 GB) |
|---|---:|---:|---:|
| Today | 0.180 GiB | 1.8 % | 1.8 % |
| 50 % | 0.681 GiB | 6.8 % | 6.8 % |
| 75 % | 1.021 GiB | 10.2 % | 10.2 % |
| 100 % | **1.395 GiB** | 14.0 % | 14.0 % |
| 100 % + 3 yr accumulation | ~4.5 GiB | 45 % | **45 %** |
| 100 % + 5 yr accumulation | ~6.5 GiB | 65 % | 65 % |

**Verdict:** Atlas storage is **not the binding constraint for at least 3 years**, even at 100 % adoption. The binding constraint is working-set RAM (see §4).

### 3.3 R2 backups (the real cost driver)

Current rate: 14.5 GiB / day. **This is the source of cost runaway.**

**Best case** = retention capped at 30 days × 24 backups/day × 539 MB/zip:

```
30 d × 24 backups × 0.539 GiB = 388 GiB steady state (capped)
$/mo = 388 × $0.015 = $5.82 / month  ← bounded
```

**Expected case** = current policy (keep everything, ~90 d), growth driven by Mongo+R2 zipped:

```
Year 1 = 14.5 × 365 = 5,293 GiB (+5.29 TiB)
$/mo at end of year 1 = (285 + 5,293) × $0.015 = ~$84 / month
```

**High-growth case** = 100 % adoption + 1.7× zip size from increased Mongo dataSize:

```
14.5 × 1.7 = 24.65 GiB/day  →  9,000 GiB/year
$/mo at year 1 = $135. By year 3 cumulative = ~$400/mo just for backups.
```

**Recommendation (P0):** retention policy.

### 3.4 R2 photos (operational media)

| Stage | Photo objects | Photo GiB |
|---|---:|---:|
| Today | 7,610 | 2.39 |
| 100 % adoption (year 0) | 50,750 | 16.0 |
| 100 % + 3 yrs | 153,000 | 48.0 |
| 100 % + 5 yrs | 254,000 | 80.0 |

Even at 5-yr cumulative, photo storage = 80 GiB × $0.015 = **$1.20 / month**. Photos are not the cost story; backups are.

### 3.5 usage_events (index pressure)

Today: 411,686 docs · 12.34 MiB data · **27.45 MiB indexes**. Index already > data — the index posture is the risk.

At 100 % adoption: `r_usage × M_adopt × M_feature` = 14,571 × 4.444 × 1.3 = **84,200 / day = 2.53 M / month = 30.7 M / year**.

```
Index growth ≈ 27.45 MiB × (30.7M / 0.412M) = 2.05 GiB indexes
```

**This is the value most likely to pressure Atlas working-set RAM** (rule of thumb: indexes should fit in RAM). M10 = 2 GiB RAM. **2.05 GiB of usage_events index alone will exceed M10 RAM at 100 % adoption running for 1 year.**

**Therefore Atlas M10 → M20 step likely required at:** ≈ 100 % adoption + 9 months **OR** ≈ 75 % adoption + 12 months. Approximately **18–24 months from today** at the Expected case.

### 3.6 Pod RAM

Today: 3.10 GiB / 8 GiB used.

Modeled scaling: backend RSS roughly tracks (a) concurrent connections × ~20 MiB each + (b) cache working set × ~0.3× of Atlas working set.

```
Connections at 100 %: ~1,000 users × 0.05 avg concurrent = 50 sustained. × 20 MiB = 1.0 GiB.
Cache working set ≈ 0.3 × Atlas indexes (5.6 GiB at scale) = 1.68 GiB.
Plus current 3.10 GiB baseline (libraries, schedulers, etc.).
Projected: ~5.8 GiB / 8 GiB at 100% scale.
```

**Verdict:** **Pod stays inside 8 GiB cap at 100 % adoption for the first ~12 months.** Forced upgrade probably at **18 months from today**, coincident with Atlas M10 → M20.

---

## 4 · Capacity-trigger calendar (🟠 model)

| Trigger | When (best) | When (expected) | When (high) | What forces it |
|---|---|---|---|---|
| R2 backup retention cap should be set | **NOW** | NOW | NOW | Already growing $5/mo and accelerating |
| Atlas M10 → M20 | 36 mo | **24 mo** | 12 mo | usage_events index size exceeds M10 RAM |
| Emergent pod 8 → 16 GiB RAM | 30 mo | 18 mo | 9 mo | backend RSS sustained > 6 GiB |
| Resend Free → Pro | n/a (no email sends today) | only when email channel is wired in | same | volume crossing 3,000/mo |
| Sentry Developer → Team | 🔴 unknown (operator monitor) | unknown | unknown | event volume crossing 5,000/mo |
| Cloudflare zone Free → Pro | never likely needed | never | never | Pro is for WAF / image resizing — not currently required |
| Atlas M20 → M30 | 60 mo | 48 mo | 24 mo | working set > 4 GiB |

---

## 5 · Headroom & risk summary

| Surface | Today | 100 % adoption | First binding constraint |
|---|:--:|:--:|:--:|
| Atlas storage | 1.8 % | 14 % | M10 OK; M20 OK; M30 overkill |
| Atlas index RAM | low | ~95 % of M10 RAM | **M10 → M20 forced** |
| R2 storage | unlimited | unlimited | cost, not capacity |
| R2 ops | well within free tier | well within | cost only |
| Pod RAM | 38.8 % | 72 % | room remains for ≈ 1 year past 100 % |
| Pod CPU | 🔴 (no telemetry from inside) | 🔴 | unknown |
| Pod disk | 26 % | likely ~50 % | comfortable |
| Resend | n/a | ≈ 5K/mo if wired | Pro tier ($20/mo) at most |
| Sentry | 🔴 | 🔴 | Team ($26/mo) if ever |
| LLM | 0 | wildcard | operator decision |

---

## 6 · Sensitivity table (what changes the bill the most)

| Variable | Today | If doubled | If halved | Bill impact at 100 % |
|---|---|---|---|---|
| Photos per DR (inline in Mongo) | ~3 | 6 | 1 | ±40 % on Atlas dataSize, ±10 % on Atlas tier-step timing |
| Backup retention days | ~90 (keep all so far) | 180 | 30 | **±$50/mo at 12 months** |
| Hourly backup cadence | 24×/day | 48×/day | 4×/day | Linear with backup count |
| usage_events instrumentation | every UI event | every event + props | only KPI events | ±50 % on Atlas index size → tier step timing ±6 months |
| AI features launched | none | one Gemini chat | none | wildcard — typically $0.10–$1/user/day if heavy |
| Cross-portal notifications volume | 321/day | 642/day | 160/day | Negligible $ ; large Mongo growth |

---

## 7 · How to refresh this model

Every metric in §1 is reproducible from inside the pod. The audit doc lists the exact Python snippets used. Run them monthly and re-paste into §1. The multipliers in §2 should be revisited every 6 months as actual adoption climbs.
