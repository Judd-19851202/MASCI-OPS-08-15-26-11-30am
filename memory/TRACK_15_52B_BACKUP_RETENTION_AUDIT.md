# TRACK 15.52B · Backup Retention Audit

**Status:** Read-only · evidence-only · captured 2026-06-19 ~21:05 UTC against live production R2 bucket `masci-hub`.

## SECTION A · Current production truth

| # | Item | Value | Evidence |
|---|---|---|---|
| 1 | Current production backup cadence | **HOURLY** | `mascidocs.com/api/admin/backups-complete-r2-state` returns `r2_hourly: true · nightly_last_hour: "2026-06-19T20"`. Live R2 inter-backup deltas: 58.1, 58.2, 58.5, 59.0, 61.9, 63.1, 63.4, 63.6 min (samples from 2026-06-19 10:06 → 21:06 UTC). |
| 2 | Current scheduler configuration | **`_backup_scheduler_loop`** singleton-locked via `scheduler_locks` collection. `SCHEDULER_ENABLED=true` on prod (inferred from active `nightly_last_hour`). | `backend/server.py:7624` + `backend/lib/singleton_scheduler.py`. |
| 3 | Current backup trigger mechanism | 5-minute scheduler tick. Fires `_run_complete_archive_to_r2` when the configured UTC hour matches OR `BACKUP_R2_HOURLY=true`. | `backend/server.py:7840-7849`. |
| 4 | Current backup code path | `_build_complete_archive_zip` → R2 `put_object` under `backups/auto-90d/MASCI_complete_backup_YYYY-MM-DD_HHMMSSZ.zip` → tiered retention prune → audit row `mode=complete-r2 ok=true`. | `backend/server.py:7100-7240`. |
| 5 | Current backup destination | Cloudflare R2 bucket `masci-hub` · prefix `backups/auto-90d/` · `S3_ENDPOINT_URL` resolved. | `backend/.env` (preview mirror) confirms `S3_BUCKET=masci-hub · S3_REGION=auto`. |
| 6 | Current retention system | **TWO layers, conflicting** (see §3): (a) App-side `lib/r2_retention.py` tiered policy 14d/90d/365d. (b) Cloudflare R2 bucket lifecycle rule `masci-backups-auto-90d` · Prefix `backups/auto-90d/` · **`Expiration: 90 days`**. | Live `s3.get_bucket_lifecycle_configuration` returned both rules. |
| 7 | Current backup object count | **854 objects in `backups/` total** · split: `backups/auto-90d/` = 354 · legacy `backups/*.zip` = 500. | Live `list_objects_v2` paginator walk. |
| 8 | Current backup storage utilization | **193.5 GB total** · split: `auto-90d/` = 171.04 GB · legacy = 22.51 GB. Newest auto-90d = 0.63 GB, mean = 0.48 GB. | Live aggregate `Size` field across all 854 objects. |
| 9 | Current backup growth rate | Net steady-state. Auto-90d holds 14 d of hourly + ~30 d of daily survivors = 354 objects today. Adds ~580 MB/hour created, prunes ~580 MB/hour at the 14-day boundary. Legacy prefix is **frozen** at 22.5 GB (no writes since 2026-05-17). | Cohort histogram (§2). |

## SECTION B · Retention truth — what's actually preserved

### App-side intent (`backend/lib/r2_retention.py`)
| Tier | Range | Policy |
|---|---|---|
| 1 | Day 0 — Day 14 | Keep ALL hourly zips |
| 2 | Day 14 — Day 90 | Keep newest per calendar day |
| 3 | Day 90 — Day 365 | Keep newest per calendar month |
| 4 | > Day 365 | DELETE |

### Cloudflare-side lifecycle (live)
| Rule ID | Filter | Action |
|---|---|---|
| `masci-backups-auto-90d` | Prefix `backups/auto-90d/` | **Expiration: 90 days · ENABLED** |
| `Default Multipart Abort Rule` | None | Enabled |

### Live cohort distribution in `backups/auto-90d/` (354 objects, 171 GB)
| Cohort | Count | Storage | What's there |
|---|---:|---:|---|
| 0 – 14 d | 337 | 167.92 GB | Tier 1: hourly archives preserved by app + R2 |
| 14 – 30 d | 14 | 3.11 GB | Tier 2: daily survivors (≈ 1/day · matches policy) |
| 30 – 60 d | 3 | 0.003 GB | Tier 2: only 3 tiny survivors — gap |
| 60 – 90 d | 0 | 0 | **EMPTY · should have ~60 daily survivors** |
| > 90 d | 0 | 0 | **R2 lifecycle deletes everything at 90 days regardless of app policy** |

### Lifecycle map (live MASCI values)
```
Day 0 ────────────────────► Day 14:  337 hourly objects · ~168 GB · ✅ matches app intent
Day 14 ─────────────────► Day 30:   14 daily objects ·   ~3 GB · ✅ matches app intent
Day 30 ─────────────────► Day 60:    3 tiny objects · 0.003 GB · ⚠ should be ~30 daily survivors
Day 60 ─────────────────► Day 90:    0 objects ·     0 GB · 🔴 should be ~30 daily survivors
Day 90 ─────────────────► Day 365:   0 objects ·     0 GB · 🔴 NEVER ARRIVES — R2 lifecycle kills the prefix at 90 days
Day 365+ :                            0 objects ·     0 GB · 🔴 Tier 4 (annual archive) never reachable
```

### Hourly / daily / weekly / monthly / annual / permanent verdicts
| Tier | Retained? | For how long? | How many exist (live)? |
|---|:---:|---|---:|
| Hourly | ✅ YES | 0 – 14 days (app · matches live) | 337 |
| Daily | ✅ partial | 14 – 30 days (live shows daily survivors); 30 – 60 days deeply incomplete (3 only); 60 – 90 days completely empty | 14 (14-30 d) + 3 (30-60 d) + 0 (60-90 d) |
| Weekly | ❌ NO | App policy does not implement weekly tier | 0 |
| Monthly | ❌ NO (app intent says 90 – 365 d; live shows zero past 90 d) | App says 90 – 365 d preserved; R2 lifecycle (Expiration: 90 d) **silently overrides this and deletes everything past 90 d** | 0 |
| Annual | ❌ NO | App policy says delete at Day 365 (Tier 4); cannot reach due to 90-d R2 lifecycle | 0 |
| Permanent archive | ❌ NO | Not configured anywhere · no separate prefix · no glacier · no immutable storage | 0 |

## Critical finding — retention gap

The app's `lib/r2_retention.py` says monthly survivors are preserved 90-365 days. **They are not.** The Cloudflare-side lifecycle rule `masci-backups-auto-90d` deletes every object in `backups/auto-90d/` at 90 days, regardless of what the app code intended. Effective retention ceiling on the active backup prefix is **90 days, not 365 days**.

Recovery posture today is therefore: **any data older than ~90 days exists only in Atlas backup, not in R2.**

## SECTION B summary

- Tier 1 (hourly · 0-14 d): **working as designed.** 337 objects, 168 GB.
- Tier 2 (daily survivors · 14-90 d): **partially working.** 17 objects, 3.1 GB. Should be ~76 (1/day × 76 days). Gap likely because:
  - Daily survivors only survive past 14 d when the bucket has a continuous 14-d window of hourly archives. The bucket activated `auto-90d/` on 2026-05-17 — that's **only 33 days ago**, so the 30-60 d cohort is naturally light.
  - As the bucket matures, this gap will fill in (will reach steady-state Tier 2 saturation around 2026-08-15).
- Tier 3 (monthly · 90-365 d): **structurally broken.** Cannot work as long as the R2 lifecycle rule deletes at 90 days.
- Tier 4+ (annual · permanent): **does not exist.**
- Legacy prefix `backups/*.zip`: **frozen at 22.5 GB · no cleanup configured · costs ~$0.34/month indefinitely.**
