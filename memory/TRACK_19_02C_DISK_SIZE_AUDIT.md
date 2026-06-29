# Track 19.02C · Disk Size Audit

Comprehensive walkthrough of every category on the `/app` filesystem.

## Top 30 largest directories on /app

| Rank | Path | Size | Classification |
| ---: | --- | ---: | --- |
| 1 | `/app/frontend/node_modules` | 2.0 G | KEEP (runtime dependency) |
| 2 | `/app/frontend/node_modules/.cache` | **1.5 G** | SAFE TO DELETE (webpack dev cache) |
| 3 | `/app/.git` | 1.3 G | KEEP (platform commit history) |
| 4 | `/app/backend/storage` | 533 M | KEEP (`project_docs` = customer uploads) |
| 5 | `/app/backend/static` | 300 M | KEEP (training videos + safety cards + brand) |
| 6 | `/app/backend/static/training-videos` | 281 M | KEEP (production media) |
| 7 | `/app/memory` | 272 M | MIXED (see breakdown) |
| 8 | `/app/memory/_archived` | **217 M** | SAFE TO DELETE (stale archives) |
| 9 | `/app/backend` (excl. storage/static/tests) | ~30 M | KEEP (source + routes + services) |
| 10 | `/app/test_reports/playwright` | 21 M | SAFE (after current track validated) |
| 11 | `/app/backend/tests/__pycache__` | 21 M | SAFE TO DELETE (bytecode) |
| 12 | `/app/backend/tests` (source) | ~8 M | KEEP (test source) |
| 13 | `/app/backend/backups` | 7.9 M | KEEP (4 files; retention=3+1 respected) |
| 14 | `/app/memory/track2_evidence` | 5.0 M | KEEP (evidence archive) |
| 15 | `/app/walkthrough_reports` | 4.9 M | KEEP (recent walkthrough findings) |
| 16 | `/app/memory/track_15_61_data` | 4.3 M | KEEP (historical evidence) |
| 17 | `/app/memory/screenshots` | 3.5 M | KEEP (referenced from track docs) |
| 18 | `/app/memory/track_15_59_screenshots` | 2.2 M | KEEP |
| 19 | `/app/backend/__pycache__` | 2.1 M | SAFE TO DELETE (bytecode) |
| 20 | `/app/backend/guidance` | 2.1 M | KEEP (production guidance content) |
| 21 | `/app/backend/lib` | 1.6 M | KEEP (source) |
| 22 | `/app/scripts` | 1.5 M | KEEP (operator scripts) |
| 23 | `/app/test_reports` (other) | ~1 M | KEEP (recent reports) |
| 24 | `/app/backend/data` | 1.8 M | KEEP (seed data) |
| 25 | `/app/backend/services` | 0.5 M | KEEP (source) |
| 26 | All `__pycache__` aggregate | 29 M | SAFE TO DELETE |
| 27 | All `.pytest_cache` aggregate | 2 M | SAFE TO DELETE |
| 28 | `/app/docs` | 40 K | KEEP |
| 29 | `/app/deploy_reports` | 132 K | KEEP |
| 30 | `/app/tests` (project-root) | 148 K | KEEP |

## Top 20 largest files on /app

| Rank | Path | Size | Class |
| ---: | --- | ---: | --- |
| 1 | `/app/.git/objects/pack/pack-d09…7.pack` | 619 M | KEEP (.git) |
| 2 | `/app/.git/objects/pack/pack-60f…7.pack` | 343 M | KEEP (.git) |
| 3 | `/app/frontend/node_modules/.cache/default-development/155.pack` | 306 M | DELETE (webpack cache) |
| 4 | `/app/frontend/node_modules/.cache/default-development/102.pack` | 250 M | DELETE (webpack cache) |
| 5 | `/app/memory/_archived/dr_migration_backups_2026-05-30.tar.gz` | **197 M** | DELETE (stale 8-month-old archive) |
| 6 | `/app/backend/storage/project_docs/24-12/0d0e9933-…pdf` | 154 M | KEEP (customer upload) |
| 7 | `/app/.git/objects/29/35f52749aaa9a511…` | 150 M | KEEP (.git) |
| 8 | `/app/backend/storage/project_docs/24-12/58e0c5bf-…pdf` | 84 M | KEEP (customer upload) |
| 9 | `/app/backend/storage/project_docs/24-12/9ea3683b-…pdf` | 65 M | KEEP (customer upload) |
| 10 | `/app/.git/objects/pack/pack-ba08935a…pack` | 58 M | KEEP (.git) |
| 11 | `/app/frontend/node_modules/.cache/default-development/89.pack` | 41 M | DELETE (webpack cache) |
| 12 | `/app/backend/storage/project_docs/24-12/39ab93f6-…pdf` | 41 M | KEEP (customer upload) |
| 13 | `/app/backend/storage/project_docs/24-12/650ff120-…pdf` | 38 M | KEEP (customer upload) |
| 14 | `/app/backend/static/training-videos/field-06-incident.es.mp4` | 36 M | KEEP (production media) |
| 15 | `/app/backend/static/training-videos/field-06-incident.en.mp4` | 32 M | KEEP (production media) |
| 16 | `/app/backend/storage/project_docs/24-12/3b87cb31-…pdf` | 31 M | KEEP (customer upload) |
| 17 | `/app/backend/static/training-videos/field-02-daily-report.es.mp4` | 25 M | KEEP (production media) |
| 18 | `/app/backend/static/training-videos/field-03-equipment-preop.es.mp4` | 24 M | KEEP (production media) |
| 19 | `/app/backend/static/training-videos/field-05-jhp.es.mp4` | 23 M | KEEP (production media) |
| 20 | `/app/backend/static/training-videos/field-04-safety-meeting.es.mp4` | 23 M | KEEP (production media) |
| 21 | `/app/memory/_archived/track_13_4_evidence_combined.tar.gz` | **21 M** | DELETE (stale evidence) |

## Cleanup candidates summary

| Category | Path(s) | Estimated reclaim |
| --- | --- | ---: |
| Webpack dev cache | `/app/frontend/node_modules/.cache` | ~1.5 G |
| Stale archives | `/app/memory/_archived/*.tar.gz` (2 files) | ~217 M |
| Python bytecode | All `__pycache__` dirs on /app | ~29 M |
| Pytest cache | All `.pytest_cache` dirs | ~2 M |
| Playwright artifacts (older than current) | `/app/test_reports/playwright/old_*` (selective) | ~21 M |
| **TOTAL SAFE** | | **~1.77 GB** |

## Unknown directories — decided KEEP

* `/app/walkthroughs` (224 K) — recent walkthrough JSON, referenced by ops.
* `/app/deploy_reports` (132 K) — deployment history.
* `/app/.emergent` (preserved by platform contract).

## Protected categories (confirmed by directory inspection)

* `/app/backend/storage/project_docs/24-12/*.pdf` — 13 PDFs ranging
  3–154 MB. Each has a UUID filename — these are MASCI customer
  project documents.
* `/app/backend/static/training-videos/*.mp4` — 10 production training
  videos used by the Training pages.
* `/app/backend/static/safety-cards/*.pdf` — production safety cards.
* `/app/backend/backups/*.zip` — 4 backup zips (Mongo lite snapshots).
* `/app/.git/**` — platform-managed git store.
