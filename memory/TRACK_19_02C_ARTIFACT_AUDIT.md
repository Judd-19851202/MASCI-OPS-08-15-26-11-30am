# Track 19.02C · Artifact Audit

Generated artifacts on /app (test reports, screenshots, PDFs, build
outputs).

## /app/test_reports — 28 MB after cleanup (was 36 MB)

| Path | Size | Action |
| --- | ---: | --- |
| `/app/test_reports/playwright/` | 12 M (was 21 M) | Cleaned: files older than 14 days removed |
| `/app/test_reports/pytest/` | 3 M | KEEP — current pytest XML outputs |
| `/app/test_reports/iteration_*.json` | small | KEEP — current iteration test reports |
| Static smoke PDFs (`uxs11g_*`, `SAFETY_MEETING_CERT_smoke.pdf`) | 5 M total | KEEP — referenced by Track 11 / Track 14 certifications |

## /app/walkthrough_reports — 4.9 MB

KEEP. Contains operator-walkthrough findings for dispatcher / foreman /
HR / laborer / operator roles. Recent and referenced.

## /app/memory screenshots & evidence — 55 MB total after cleanup

All retained. These are evidence files referenced by certification
reports in `/app/memory/MASCI_RC_CERTIFICATION_LEDGER.md` and the
track-specific markdown reports:

* `screenshots/`, `audit_screenshots_2026-02-01/`
* `track_15_*_screenshots/`, `track_15_61_data/`, `track_15_62_screenshots/`, …
* `track2_evidence/`, `stability_evidence/`

## Build artifacts

* `/app/frontend/build/` — none currently (CRA dev mode in this env).
* `/app/frontend/node_modules/.cache/` — REMOVED (Action 1, 1.5 GB reclaimed).
* `/app/backend` has no compiled artifacts (Python source only).

## Old downloaded zip/tar artifacts

| Path | Status |
| --- | --- |
| `/app/memory/_archived/dr_migration_backups_2026-05-30.tar.gz` | REMOVED (Action 2) |
| `/app/memory/_archived/track_13_4_evidence_combined.tar.gz` | REMOVED (Action 3) |
| Any other `*.tar.gz`, `*.zip`, `*.tar` in /app | Only `/app/backend/backups/*.zip` (4 protected backup zips) and `/app/frontend/yarn.lock` — none deletable. |

## Duplicate generated files

Verified by `find -name "*.png" -size +100k` and `find -name "*.pdf" -size +1M`:
* All large PDFs are customer documents under `project_docs/` (PROTECTED).
* All large PNGs are evidence screenshots referenced by markdown reports.
* No duplicate generated files identified.

## Conclusion

Artifact cleanup reclaimed ~9 MB from old Playwright artifacts.
Combined with archive cleanup (217 MB) and bytecode cleanup (29 MB), the
total non-cache reclaim was 255 MB. The remaining 1.5 GB came from the
webpack dev cache.
