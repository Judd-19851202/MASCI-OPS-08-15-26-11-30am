# ASSET REFERENCE INVENTORY

Date: 2026-07-19  
Checkpoint: C (in progress)

Machine-readable working source:
- `/tmp/asset_inventory.json`

## Current totals

- inventoried assets: 61
- exact duplicate hash groups identified: 3

## Exact duplicate groups

### Group 1 — ForgedOps logo
- `frontend/public/forgedops-logo.png`
- `frontend/src/assets/forgedops-logo.png`
- Classification: `EXACT_REDUNDANT_DUPLICATE` candidate, pending consumer proof.

### Group 2 — MASCI full lockup onlight
- `frontend/public/masci-full-lockup-onlight.png`
- `backend/static/masci-logo-email.png`
- `backend/static/masci-logo.png`
- Classification: `BACKEND_PDF_REQUIRED` + `FRONTEND_REQUIRED` multi-consumer group for now.

### Group 3 — MASCI mark
- `frontend/public/masci-mark-onlight.png`
- `frontend/public/masci-mark.png`
- `backend/static/masci-mark.png`
- Classification: `FRONTEND_REQUIRED` + `BACKEND_PDF_REQUIRED` multi-consumer group for now.

## Source artwork

- `assets/source/**` is now the canonical owner for source/master/demo artwork that should not ship publicly.

## Current removal decision

- No duplicate asset deleted in this pass.
- Additional consumer proof is required before removing any exact duplicate with backend/static or frontend/public consumers.
