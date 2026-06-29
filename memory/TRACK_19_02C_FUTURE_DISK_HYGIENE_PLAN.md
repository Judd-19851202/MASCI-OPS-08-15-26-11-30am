# Track 19.02C · Future Disk Hygiene Plan

## Recurring cleanup recommendations

### Daily / per-deploy

* **Pre-deploy disk gate**: enforce `/app` utilization < 70% before
  promoting a release. Add to deployment checklist.
* **Alert threshold**: monitor `/app` utilization. Warn at **70%**,
  page at **80%**.
* **Emergency-prune threshold**: backup runner already has this
  (server.py line 5837). Keep `BACKUP_KEEP_MAX=3`.

### Weekly

* `find /app -type d -name __pycache__ -not -path '*/node_modules/*' -not -path '*/.git/*' -prune -exec rm -rf {} +`
  — strip Python bytecode caches.
* `find /app -type d -name .pytest_cache -not -path '*/node_modules/*' -not -path '*/.git/*' -prune -exec rm -rf {} +`
  — strip pytest caches.

### Monthly / per release

* Clear `/app/frontend/node_modules/.cache` before tagging a release
  build. Webpack regenerates this automatically.
* `find /app/test_reports/playwright -type f -mtime +14 -delete && find /app/test_reports/playwright -type d -empty -delete`
  — trim Playwright artifacts older than 14 days.

### Quarterly

* Audit `/app/memory/_archived/`. Anything older than 90 days that has
  a copy in R2 should be removed from local storage.
* Consider running `git gc` on `/app/.git` if the platform-managed
  store has grown materially. Coordinate with platform team — the
  `.git` directory carries deployment-critical history.

## Artifact retention windows (recommended defaults)

| Artifact | Retain |
| --- | --- |
| Playwright screenshots / videos | **14 days** |
| Test report JSONs in `/app/test_reports/iteration_*.json` | **Last 5 iterations + current track** |
| Pytest XML in `/app/test_reports/pytest/` | **Last 30 days** |
| Local backup zips in `/app/backend/backups/` | **BACKUP_KEEP_MAX (default 3, with retention days)** |
| Memory archives in `/app/memory/_archived/` | **R2-only after R2 upload verified** |

## Monitoring thresholds (alerting)

| Filesystem | WARN at | PAGE at | EMERGENCY PRUNE at |
| --- | ---: | ---: | ---: |
| `/app` | 70% | 80% | already implemented (backup runner) |
| `/var/log` rootfs | 70% | 80% | n/a |
| MongoDB Atlas storage | per Atlas-managed alerts | — | — |

## Architectural recommendation — R2-only archives

Currently `/app/memory/_archived/` carries stale archives on the
application volume. **Future state**: after a successful R2 upload of
any archive, the local copy should be removed (or symlinked). This
eliminates the "DR migration backups from 8 months ago still on disk"
class of issue we just resolved.

Suggested approach (low complexity):
1. R2 upload helper records the archive's R2 key in a manifest
   (`/app/memory/_archived/_r2_manifest.json`).
2. A daily cron task removes any local file whose R2 key is present in
   the manifest and whose mtime is > 30 days.
3. The manifest is the operator-facing inventory.

## CI / cleanup hooks (optional)

If a CI pipeline is wired up in the future:
* Pre-build step: clear `node_modules/.cache` and `__pycache__`.
* Post-test step: tar-up Playwright artifacts and upload as a build
  artifact, then remove from `/app/test_reports/playwright/`.
* Post-deploy step: emit disk-usage metric to monitoring.

## Operator commands cheatsheet

```bash
# Quick safe cleanup (reclaims ~1.5 G):
rm -rf /app/frontend/node_modules/.cache
find /app -type d -name __pycache__ -not -path '*/node_modules/*' \
  -not -path '*/.git/*' -prune -exec rm -rf {} +
find /app -type d -name .pytest_cache -not -path '*/node_modules/*' \
  -not -path '*/.git/*' -prune -exec rm -rf {} +

# Trim old Playwright artifacts (>14 days):
find /app/test_reports/playwright -type f -mtime +14 -delete
find /app/test_reports/playwright -type d -empty -delete

# Quick disk check:
df -h /app && du -sh /app/* | sort -hr | head -10
```

Run after each major track or before a deployment gate.
