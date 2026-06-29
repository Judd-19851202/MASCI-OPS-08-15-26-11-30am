# Track 19.02C · Final Disk Report

## BEFORE vs AFTER

| Metric | BEFORE | AFTER | Change |
| --- | ---: | ---: | ---: |
| `/app` size | 9.8 G | 9.8 G | — |
| `/app` used | **7.2 G** | **5.6 G** | **−1.6 G** |
| `/app` available | 2.6 G | 4.2 G | +1.6 G |
| `/app` utilization | **74%** | **57%** | **−17 pp** |
| `/app` inodes used | 162,337 | 153,512 | −8,825 |
| `/app` inode utilization | 25% | 24% | −1 pp |

## Reclaimed by category

| Category | Reclaim |
| --- | ---: |
| Webpack / babel dev cache (`/app/frontend/node_modules/.cache`) | ~1.50 G |
| Stale archive — DR migration (8 months old) | 197 M |
| Python `__pycache__` (20 dirs across /app) | ~29 M |
| Stale archive — Track 13.4 evidence | 21 M |
| Old Playwright artifacts (>14 days) | ~9 M |
| `.pytest_cache` (3 dirs) | ~2 M |
| **TOTAL** | **~1.76 G** |

## Target result

| Target | Status |
| --- | --- |
| Preferred (55–60% utilization) | **✓ ACHIEVED — 57%** |
| Stretch (lower than 55%) | Not pursued — would require touching protected categories |

## Remaining largest directories (after)

| Path | Size | Class |
| --- | ---: | --- |
| `/app/.git` | 1.3 G | KEEP (platform-managed) |
| `/app/frontend/node_modules` | 537 M | KEEP (runtime dependencies; `.cache` removed) |
| `/app/backend/storage/project_docs/24-12` | 533 M | KEEP (customer uploads) |
| `/app/backend/static/training-videos` | 281 M | KEEP (production media) |
| `/app/memory` | 55 M | KEEP (documentation + evidence) |
| `/app/test_reports` | 28 M | KEEP (current reports + cleaned playwright) |
| `/app/backend/static/safety-cards` | 14 M | KEEP (production media) |
| `/app/backend/backups` | 7.9 M | KEEP (within retention) |
| `/app/walkthrough_reports` | 4.9 M | KEEP |

## Protected directories — confirmed intact

* `/app/backend/storage/project_docs/24-12/*.pdf` — 13 files, 533 M (UNCHANGED)
* `/app/backend/static/training-videos/*.mp4` — 10 files (UNCHANGED)
* `/app/backend/static/safety-cards/*.pdf` — 2 files (UNCHANGED)
* `/app/backend/backups/*.zip` — 4 files (UNCHANGED)
* `/app/.git/` — 1.3 G (UNCHANGED)
* MongoDB collections — off-filesystem, UNCHANGED
* Atlas backups, R2 references — off-platform, UNCHANGED

## Why not lower than 57%?

To go below 55% would require touching one of:

* `/app/.git` (1.3 G) — platform-managed; rollback-critical. Running
  `git gc --aggressive` could reclaim some — left for future hygiene.
* `/app/frontend/node_modules` (537 M after `.cache` removal) —
  runtime-required dependencies. Cannot delete.
* `/app/backend/storage/project_docs` (533 M) — customer data.
  **NEVER delete.**
* `/app/backend/static/training-videos` (281 M) — production media.
  **NEVER delete.**

All four are correctly classified DO NOT DELETE. The 57% achieved
floor is the **safe minimum** for this filesystem given the production
content present.

## GO / NO-GO

**GO.** Disk posture meets the 55–60% target band safely. No
production data, customer uploads, audit logs, or rollback assets
were touched. All services running. All transportation test suites
GREEN. Inode pressure healthy (24%). Ready for the next production
deployment gate.
