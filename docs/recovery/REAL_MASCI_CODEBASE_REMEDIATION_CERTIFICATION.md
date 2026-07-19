# REAL MASCI CODEBASE REMEDIATION CERTIFICATION

Date: 2026-07-19  
Checkpoint: C (in progress)

## Scope completed in this iteration

- Repository baseline captured
- Mandatory candidate inventory created
- Reference proof performed for initial clutter groups
- Canonical archive structure defined
- First bounded cleanup batch executed

## First bounded cleanup batch

Moved/copied into canonical archive/source locations before removal from original locations:
- `deploy_reports/**` → `docs/archive/deployments/`
- `test_reports/**` → `docs/archive/testing-evidence/`
- `test_result.md` → `docs/archive/testing-evidence/test_result.md`
- `image_testing.md` → `docs/archive/testing-evidence/image_testing.md`
- `frontend/public/_logo_source_2026-05-03.png` → `assets/source/logo_source_2026-05-03.png`
- `frontend/public/_icon_master_1024.png` → `assets/source/icon_master_1024.png`
- `frontend/public/_splash_links.html` → `assets/source/splash_links.html`
- `frontend/public/_demo_tor_*.png` → `assets/source/demo_*`
- `scripts/source/red_m_master.png` → `assets/source/red_m_master.png`

Deleted from original tracked locations after preservation/reference updates:
- `deploy_reports/**`
- `test_reports/**`
- `test_result.md`
- `image_testing.md`
- `frontend/public/_demo_*`
- `frontend/public/_logo_source_2026-05-03.png`
- `frontend/public/_icon_master_1024.png`
- `frontend/public/_splash_links.html`
- `scripts/source/red_m_master.png`
- `tmp_real_photos/TC_00031.jpeg`

## Runtime/reference updates completed

- `backend/export_pdf_fallback.py`
- `scripts/install_new_logo.py`
- `backend/scripts/generate_ios_splash.py`
- `backend/scripts/generate_icons.py`
- `scripts/install_icons.py`
- `scripts/install_og_image.py`
- `scripts/install_mark.py`

## Ignore governance updates completed

- `.gitignore` simplified stale webpack-cache exact entries to wildcard rules
- Added local artifact/platform-local ignore rules for preview metadata and generated evidence
- `.dockerignore` updated to exclude `assets/source/` while preserving runtime requirements

## Safety accounting

- No deployment
- No production/external access
- No mutation script execution
- Atlas reads/writes: 0/0
- R2 reads/writes: 0/0
- Provider/email calls: 0

## Current status

Checkpoint C remains in progress. Classification, first bounded cleanup batch, and second bounded cleanup batch are complete; full clean-checkout verification and final independent review still pending.

## Second bounded cleanup batch

- Untracked/preserved locally:
  - `.emergent/cron/applied.hash`
  - `.emergent/cron/webhook-crons`
- Archived runtime-adjacent backup artifacts:
  - `backend/data/equipment_master.*.bak.json` → `docs/archive/incidents/backend-data-backups/`
