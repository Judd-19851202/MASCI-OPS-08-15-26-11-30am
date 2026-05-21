#!/usr/bin/env bash
# Platform Family Contract Pre-Deploy Hook · iter321
#
# Purpose: anti-drift protection only.
#
# Runs the single canonical platform-family invariant suite before a
# deploy. Exits non-zero on any contract violation so a calmified hub
# can't silently regress to hot-bordered SectionTile chrome, public-hero
# H1 leaks, or ad-hoc section-heading styles.
#
# Operator mandate (iter321):
#   - tiny
#   - deterministic
#   - stabilization-safe
#   - governance-focused
#
# NOT in scope:
#   - screenshot testing
#   - visual diff
#   - giant CI
#   - style micromanagement
#   - unrelated tests
#
# Usage:
#   /app/.deploy_checks/run_family_contract.sh
#
# Wire into your deploy pipeline (e.g. before `git push` to production
# or before mascidocs.com redeploy) — exits 0 on pass, 1 on violation.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "── Platform Family Contract · pre-deploy gate ──"
python -m pytest \
  backend/tests/test_platform_family_contract.py \
  -q --tb=short

echo "── Contract green · safe to deploy ──"
