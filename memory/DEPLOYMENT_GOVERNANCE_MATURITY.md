# DEPLOYMENT_GOVERNANCE_MATURITY

Status: governance artefact restored for Sigma-III deployment gate.

## Purpose
- Captures that this repository uses a two-stage deployment governance model:
  1. Static GitHub gate
  2. Live preview operator gate

## Current doctrine
- GitHub Actions checks static contracts and required artefacts.
- `scripts/pre_deploy_check.sh` covers preview-connected runtime checks.
- Production deploy should proceed only after both stages pass.
