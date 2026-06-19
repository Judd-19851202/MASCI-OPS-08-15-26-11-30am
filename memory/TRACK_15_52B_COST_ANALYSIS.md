# TRACK 15.52B · Cost Analysis

**Status:** Evidence-based projection. Storage rates from Cloudflare R2 public pricing page (last verified by code 2026-06-19; user should confirm by inspecting the Cloudflare billing console).

## Current state (HOURLY · live, 2026-06-19)

| Component | Quantity | Unit price | Monthly cost | Annual cost |
|---|---:|---|---:|---:|
| R2 storage · `auto-90d/` active | 171.04 GB | $0.015/GB/mo | $2.566 | $30.79 |
| R2 storage · legacy frozen prefix | 22.51 GB | $0.015/GB/mo | $0.338 | $4.05 |
| R2 Class-A ops (PUT) | ~720/mo | $4.50/M ops | $0.003 | $0.04 |
| R2 Class-B ops (GET/HEAD, mostly retention prune) | ~3,500/mo | $0.36/M ops | $0.001 | $0.02 |
| Egress (Cloudflare-unique advantage) | n/a | **$0.00** | $0.00 | $0.00 |
| Atlas backup add-on | UNVERIFIED — depends on cluster tier and whether continuous backup is enabled; M10 tier base is ~$57/mo before backup; PITR add-on is ~$0.40/GB/mo of source data | n/a | n/a | n/a |
| **TOTAL R2 monthly** | | | **$2.91** | **$34.90** |

Note: Track 15.37 projected $44/year. The actual $34.90/year is lower because the average backup size (488 MB) is smaller than what was assumed at proposal time (650 MB) and because the legacy prefix is dominated by small / corrupted stub objects (mean ~45 MB) rather than full archives.

## Proposed state (6-HOURLY · 4 backups/day)

Steady-state storage = (4 backups/day × 14 days × 580 MB avg) + (Tier 2 daily survivors 14-90 d × 580 MB)
                    ≈ 32.5 GB + 44.0 GB = **76.5 GB**.

Hourly current = (24 × 14 × 580 MB) + Tier 2 daily survivors as today = **171 GB.**

| Component | Quantity | Monthly cost | Annual cost |
|---|---:|---:|---:|
| R2 storage · `auto-90d/` active | 76.5 GB | $1.148 | $13.77 |
| R2 storage · legacy frozen prefix | 22.51 GB (unchanged unless swept) | $0.338 | $4.05 |
| R2 Class-A ops | ~120/mo | $0.001 | $0.01 |
| R2 Class-B ops | ~600/mo | $0.000 | $0.00 |
| Egress | n/a | $0.00 | $0.00 |
| **TOTAL R2 monthly** | | **$1.49** | **$17.83** |

## Delta · hourly → 6-hourly

| Metric | Hourly (current) | 6-hourly (proposed) | Delta |
|---|---:|---:|---:|
| Active prefix size | 171.0 GB | 76.5 GB | **−94.5 GB · −55%** |
| Total bucket size | 193.5 GB | 99.0 GB | **−94.5 GB · −49%** |
| Class-A PUT ops/month | ~720 | ~120 | **−600 ops/month · −83%** |
| Class-B GET ops/month | ~3,500 | ~600 | **−2,900 ops/month · −83%** |
| Annual cost · `auto-90d/` only | $30.79 | $13.77 | **−$17.02/yr** |
| Annual cost · including legacy | $34.90 | $17.83 | **−$17.07/yr** |
| Cost reduction % | — | — | **−49%** |
| Backups created per year | 8,760 | 1,460 | **−7,300** |

## Sensitivity

If MASCI grows and backup size doubles (1.2 GB average), the picture stays similar:
- Hourly → ~342 GB → $5.13/mo → $61.6/yr.
- 6-hourly → ~153 GB → $2.30/mo → $27.6/yr.
- Saving: ~$34/yr.

If MASCI grows 5× (backup size = 2.9 GB), the absolute saving grows to ~$170/yr.

## Cost recommendations (information only · no action)

| Action | Saving | Risk |
|---|---:|---|
| Switch hourly → 6-hourly | **$17/yr** | Worst-case RPO grows from 60 min → 360 min (mitigated by Atlas PITR if enabled) |
| Sweep legacy `backups/*.zip` prefix (frozen 22.5 GB) | **$4/yr** | Zero — these are pre-Track-15.28A archives + 30 corrupted stubs (Track 15.37 documented) |
| Enable R2 versioning (extra deletion-protection) | **+$0.50/mo · –$6/yr** | Extra cost is trivial; gain is real protection against accidental delete |
| Remove the conflicting R2-side `Expiration: 90 d` lifecycle rule and let the app-side `r2_retention.py` enforce 365-d monthlies | **+$0 → +$0.20/mo** | Marginal storage increase (~12 monthly survivors × 580 MB ≈ 7 GB ≈ $0.10/mo) |

## SECTION E summary

The 6-hourly cadence change saves approximately **$17/year** at current scale. The financial argument by itself is modest. The decision should be made on **recovery posture** (Section F) and **infrastructure-hardening** (Section D), not on cost alone.
