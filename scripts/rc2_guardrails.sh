#!/usr/bin/env bash
# RC-2 GUARDRAIL SUITE — permanent pre-deploy protection.
#
# Runs every guardrail that protects against the M-3 · M-15 · M-18 ·
# Track 3 (route inventory) · Track 4 (contamination) · Track 6
# (operations-map contract) · iter183 (/api/health/full contract)
# defect classes RC-1 + RC-2 + RC-2.1 closed.
#
# Exit non-zero on ANY failure. Never silences errors. Never
# uses || true. Never skips. Never xfails.
#
# Usage:
#   ./scripts/rc2_guardrails.sh
#
# Required runtime:
#   - REACT_APP_BACKEND_URL set in /app/frontend/.env
#   - super-admin credentials in /app/memory/test_credentials.md
#   - chromium for playwright: PLAYWRIGHT_BROWSERS_PATH=/pw-browsers
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT/backend"

export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-/pw-browsers}"

echo "════════════════════════════════════════════════════════════"
echo " RC-2 GUARDRAIL SUITE — pre-deploy protection"
echo "════════════════════════════════════════════════════════════"
echo " Runtime: PLAYWRIGHT_BROWSERS_PATH=$PLAYWRIGHT_BROWSERS_PATH"
echo ""

# Backend (fast) — auth, routes, contamination, ops-map, iter183 health.
echo "── Backend guardrails (auth · routes · contamination · ops-map · iter183) ──"
python -m pytest \
  tests/test_rc2_route_inventory.py \
  tests/test_rc2_auth_guardrail.py \
  tests/test_rc2_contamination_scan.py \
  tests/test_rc2_ops_map_contract.py \
  tests/test_iter183_health_full_endpoint.py \
  -v --tb=short
echo ""

# Playwright (slower) — touch targets + translation bleed.
echo "── Playwright guardrails (M-15 touch targets · M-18 ES bleed · EN⇄ES round-trip) ──"
python -m pytest \
  tests/pw_suite/test_rc2_m15_touch_targets.py \
  tests/pw_suite/test_rc2_m18_translation_bleed.py \
  -v --tb=short
echo ""

echo "════════════════════════════════════════════════════════════"
echo " 🟢 RC-2 GUARDRAIL SUITE PASS"
echo "════════════════════════════════════════════════════════════"
