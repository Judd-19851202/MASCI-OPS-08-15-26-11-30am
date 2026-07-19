# REPOSITORY CONTENT CLASSIFICATION

Date: 2026-07-19  
Checkpoint: C (in progress)

## Classification methodology

This checkpoint uses evidence-first classification only:

1. Baseline the working tree and tracked file set.
2. Build candidate inventory for mandatory clutter groups.
3. Prove references through runtime code, scripts, tests, docs, CI, Docker inclusion, and asset usage.
4. Classify each candidate before any move/delete/untrack action.
5. Do not touch `UNKNOWN_DO_NOT_TOUCH` until evidence improves.

Machine-readable inventory source:
- `docs/governance/repository_content_inventory.json`

## Initial classification totals (current candidate set)

- `MOVE_EVIDENCE_ARCHIVE`: 53
- `KEEP_OPERATOR_TOOL`: 15
- `KEEP_TEST`: 15
- `MOVE_SOURCE_ASSET_ARCHIVE`: 8
- `PLATFORM_LOCAL_NOT_PRODUCT`: 6
- `KEEP_GOVERNANCE`: 6
- `KEEP_RUNTIME`: 4
- `UNKNOWN_DO_NOT_TOUCH`: 3
- `KEEP_ACTIVE_MIGRATION`: 1
- `UNTRACK_PRESERVE_LOCALLY`: 1

## Mandatory candidate group findings

### 1. `deploy_reports/**`
- Classification: `MOVE_EVIDENCE_ARCHIVE`
- Evidence: referenced by `walkthroughs/pre_deploy_verification.md` and self-referential report chains; no runtime imports.
- Proposed action: move into canonical archive under deployment evidence.

### 2. `test_reports/**`
- Classification: `MOVE_EVIDENCE_ARCHIVE`
- Evidence: referenced by test/audit scripts and current PRD evidence only; `.dockerignore` excludes it from runtime image.
- Proposed action: archive as generated evidence, keep out runtime contract.

### 3. `walkthroughs/**`
- Classification: `KEEP_OPERATOR_TOOL`
- Evidence: referenced by scripts, tests, and deployment verification docs; active operator tooling.
- Proposed action: keep in active source for now.

### 4. `.emergent/**`
- Classification: `PLATFORM_LOCAL_NOT_PRODUCT`
- Evidence: pod/platform-local metadata and cron wrappers; `.dockerignore` excludes the directory.
- Proposed action: classify more granularly before untracking anything. `UNKNOWN`/portable elements remain untouched for now.

### 5. `memory/**`
- Mixed classifications:
  - `memory/PRD.md`, governance/certification docs → `KEEP_GOVERNANCE`
  - runtime histories / generated evidence → likely `MOVE_EVIDENCE_ARCHIVE` or `UNTRACK_PRESERVE_LOCALLY`
- Evidence: runtime must not depend on these; many scripts/docs still reference them as doctrine/evidence.
- Proposed action: preserve current files until archive policy and reference updates are finalized.

### 6. `backend/data/**`
- `employees_seed.json`, `suppliers_seed.json`, `jobs_master.json`, `equipment_master.json`
  - Classification: `KEEP_RUNTIME` / `KEEP_ACTIVE_MIGRATION`
  - Evidence: directly referenced by `backend/server.py`, `backend/jobs_master.py`, tests, and seed/migration tools.
- `equipment_master.*.bak.json`
  - Classification: `MOVE_EVIDENCE_ARCHIVE`
  - Evidence: no direct runtime references found; historical backup snapshots only.

### 7. `scripts/source/**`
- Classification: `MOVE_SOURCE_ASSET_ARCHIVE`
- Evidence: used by asset-generation installer scripts, not by runtime.

### 8. `frontend/public/_demo_*`, `_logo_source_*`, `_icon_master_*`, `_splash_links.html`
- Classification: `MOVE_SOURCE_ASSET_ARCHIVE`
- Evidence:
  - `_logo_source_2026-05-03.png` is referenced by backend PDF fallback and install script.
  - `_icon_master_1024.png` and `_splash_links.html` are referenced only by asset-generation scripts.
  - `_demo_*` images show no live runtime references from current search.
- Proposed action: move out of public runtime paths only after updating script/runtime references (`export_pdf_fallback.py`, install scripts) and verifying build.

### 9. Root `backend_test_*.py`
- Classification: `KEEP_TEST`
- Evidence: referenced in `test_result.md`; not yet proven safe to relocate without affecting process evidence and ad hoc certification usage.
- Proposed action: defer relocation until a bounded test/tool move pass.

### 10. `test_result.md` / `image_testing.md`
- Classification: `MOVE_EVIDENCE_ARCHIVE`
- Evidence: process/testing evidence only; no runtime use.

## Current high-confidence keep set

- `frontend/src/buildVersion.generated.js` → `KEEP_RUNTIME`
- `backend/data/jobs_master.json` → `KEEP_RUNTIME`
- `backend/data/employees_seed.json` → `KEEP_RUNTIME`
- `backend/data/suppliers_seed.json` → `KEEP_RUNTIME`
- `backend/data/equipment_master.json` → `KEEP_ACTIVE_MIGRATION`
- `walkthroughs/**` → `KEEP_OPERATOR_TOOL`

## Current unknown / do-not-touch set

- selected `.emergent/**` portable config until granular review completes
- a few mixed-use `memory/**` evidence files still referenced by scripts/docs
- root test helpers pending relocation proof

## Bounded cleanup manifest status

Not executed yet. This document records classification only. No move/delete/untrack has occurred in this Checkpoint C pass so far.
