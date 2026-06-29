# Track 19.02C · Disk Baseline (BEFORE)

Captured: 2026-06-29

## Filesystem snapshot

```
Filesystem      Size  Used Avail Use% Mounted on
overlay         104G   34G   70G  33% /
/dev/nvme0n11   9.8G  7.2G  2.6G  74% /app   ← APP VOLUME (THE ONE THAT MATTERS)
/dev/nvme0n1p1  104G   34G   70G  33% /etc/hosts
tmpfs            64M     0   64M   0% /dev/shm
tmpfs            16G     0   16G   0%
```

**The application volume `/app` is at 74% utilization.** This is the disk
that triggered prior emergency-prune behavior. The overlay rootfs is at
33% and is not a concern.

## Inode usage

```
/dev/nvme0n11   655360  162337  493023   25% /app
```

Inode pressure is healthy at 25%.

## /app top-level breakdown

| Path | Size | Category |
| --- | ---: | --- |
| `/app/frontend/node_modules` | 2.0 G | dependency · KEEP |
| `/app/frontend/node_modules/.cache` (subset of above) | **1.5 G** | webpack dev cache · regenerated |
| `/app/.git` | 1.3 G | rollback critical · KEEP (platform-managed) |
| `/app/backend/storage/project_docs/24-12` | 533 M | customer uploads · PROTECTED |
| `/app/backend/static/training-videos` | 281 M | production media · PROTECTED |
| `/app/memory/_archived` | **217 M** | stale archives · CANDIDATE |
| `/app/backend/static/safety-cards` | 14 M | production media · PROTECTED |
| `/app/backend/static` (other) | 5 M | production assets · PROTECTED |
| `/app/backend/backups` | 7.9 M | local backups (4 files, retention=3+1) · KEEP |
| `/app/backend/tests/__pycache__` | 21 M | bytecode cache · CANDIDATE |
| `/app/test_reports/playwright` | 21 M | test artifacts · CANDIDATE |
| `/app/memory` (excluding _archived) | 55 M | docs + screenshots · KEEP |
| `/app/test_reports` (other) | 15 M | recent reports · KEEP |
| `/app/walkthrough_reports` | 4.9 M | walkthrough findings · KEEP |
| Other (all `__pycache__` aggregate) | 29 M | bytecode · CANDIDATE |
| Other (all `.pytest_cache` aggregate) | 2 M | pytest cache · CANDIDATE |

## /var/log (NOT on /app filesystem — informational only)

```
51M  /var/log/mongodb.out.log.2     (rotated)
51M  /var/log/mongodb.out.log.1     (rotated)
37M  /var/log/supervisor
23M  /var/log/mongodb.out.log       (active)
11M  /var/log/e1_agent.log.2        (rotated)
11M  /var/log/e1_agent.log.1        (rotated)
6.4M /var/log/e1_agent.log          (active)
5.2M /var/log/monitor.log
```

`/var/log` lives on the 33%-used overlay rootfs and does NOT contribute
to `/app` pressure. Excluded from this track's cleanup actions.

## Initial summary

- `/app` filesystem: **7.2 GB used / 9.8 GB total = 74%**
- Distance to 55% target: must reclaim **~1.81 GB**
- Distance to 60% target: must reclaim **~1.32 GB**
- Identified safe cleanup envelope: ~1.77 GB (webpack cache 1.5 G +
  stale archives 217 M + `__pycache__` 29 M + Playwright 21 M)
- Expected post-cleanup utilization: **~55%** (right at lower target)

## Protected paths (NEVER delete)

* `/app/backend/storage/project_docs/**` — customer project documents
* `/app/backend/static/training-videos/**` — production training videos
* `/app/backend/static/safety-cards/**` — production safety media
* `/app/backend/static/masci-*.png|b64` — production brand assets
* `/app/backend/backups/*.zip` — local backups (retention managed by `BACKUP_KEEP_MAX=3`)
* `/app/.git/**` — platform commit history + rollback artifacts
* `/app/memory/PRD.md`, `CHANGELOG.md`, `_INDEX.md`, all current track records
* `/app/backend/.env`, `/app/frontend/.env` — environment config
* `/app/backend/server.py`, all source files
* All `/app/backend/tests/test_*.py` source (tests themselves, not cache)
* All MongoDB collections (managed by `MONGO_URL`, NOT on this filesystem)
