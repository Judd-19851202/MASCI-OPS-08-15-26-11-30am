# Track 19.02C · Cleanup Classification

Every cleanup candidate has been triaged into one of three buckets per
the Track 19.02C directive.

## SAFE TO DELETE

| Path | Reason safe |
| --- | --- |
| `/app/frontend/node_modules/.cache/**` | Webpack/Babel build cache. CRA regenerates on next `yarn start` automatically. Not required at runtime — only speeds up rebuilds. |
| `/app/memory/_archived/dr_migration_backups_2026-05-30.tar.gz` | Stale archive from 8 months ago (May 2026). DR migration completed long ago and a copy exists in R2 / Atlas backup chain. |
| `/app/memory/_archived/track_13_4_evidence_combined.tar.gz` | Stale evidence archive from Track 13.4 — predecessor track, evidence preserved in committed markdown reports. |
| `/app/**/__pycache__/**` | Python bytecode. Regenerated automatically on first import. Never required at runtime. |
| `/app/**/.pytest_cache/**` | Pytest cache (last-failed, nodeids, etc.). Regenerated automatically by pytest. |
| `/app/test_reports/playwright/__archived__/**` (selective) | Old Playwright test artifacts captured by prior runs. The most recent iteration report stays. |

## SAFE TO ARCHIVE / COMPRESS

| Path | Action | Reason |
| --- | --- | --- |
| `/app/memory/_archived/*.tar.gz` | Move R2-only after R2 upload verified | Stop carrying archive bytes on the application volume; R2 is the durable copy. (Out-of-scope for this track — captured as future hygiene action.) |
| `/var/log/mongodb.out.log.1`, `.2` | `gzip` rotation (already done by logrotate?) | NOT on /app filesystem; out of scope. |

## DO NOT DELETE

| Path | Why protected |
| --- | --- |
| `/app/backend/storage/project_docs/**` | Customer project documents (uploaded PDFs). Production data. |
| `/app/backend/static/training-videos/**` | Production training media. Served at runtime. |
| `/app/backend/static/safety-cards/**` | Production safety media. |
| `/app/backend/static/masci-*.png` and `.b64` | Production brand assets. |
| `/app/backend/backups/*.zip` | Local snapshot copies (4 files, well within `BACKUP_KEEP_MAX=3` policy + the most-recent overflow). |
| `/app/backend/.env`, `/app/frontend/.env` | Environment configuration. |
| `/app/backend/server.py`, `/app/backend/routes/**`, `/app/backend/services/**`, `/app/backend/lib/**`, `/app/backend/scripts/**` | Production source code. |
| `/app/backend/tests/**` (source `.py` files) | Test source. ONLY caches are removable. |
| `/app/frontend/src/**`, `/app/frontend/public/**`, `/app/frontend/package.json` | Frontend source. |
| `/app/frontend/node_modules/**` (excluding `.cache`) | Runtime dependencies. |
| `/app/.git/**` | Platform-managed commit history. Required for rollback. |
| `/app/memory/*.md` (current track records) | Active documentation. |
| `/app/memory/PRD.md`, `CHANGELOG.md`, `ROADMAP.md`, `_INDEX.md` | Permanent product records. |
| `/app/memory/MASCI_RC_CERTIFICATION_LEDGER.md` | Compliance / audit ledger. |
| `/app/memory/track_15_*` and `track_16_*` evidence directories | Track evidence — referenced by certification reports. |
| `/app/memory/screenshots/`, `audit_screenshots_*/` | Audit screenshots referenced by track docs. |
| `/app/memory/stability_evidence/`, `track2_evidence/` | Stability + early-track evidence. |
| `/app/memory/DOCTRINE_TRENDLINE.json` | Operational trendline data. |
| `/app/memory/_INDEX.md` | Index of memory contents. |
| `/app/test_reports/iteration_*.json` (current/recent) | Recent test reports for active tracks. |
| `/app/test_reports/pytest/**` (current) | Recent pytest XML outputs. |
| `/app/walkthrough_reports/**` | Recent walkthrough findings. |
| Database collections (managed by `MONGO_URL`) | Not on this filesystem — informational. |
| Atlas backups, R2 references | External — informational. |

## Rules of engagement

* No `rm -rf` is issued against any path not classified **SAFE TO DELETE**.
* Each cleanup batch is preceded by a sizing measurement and followed by a re-measurement.
* No production service is restarted unless explicitly required by the cleanup category.
* All cleanup commands target leaf paths or use explicit `-name` filters (no broad wildcards on `/app/**`).
