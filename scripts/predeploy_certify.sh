#!/usr/bin/env bash
# RC-2 PRE-DEPLOY CERTIFY — full pre-Save-to-GitHub gate.
#
# Runs the RC-2 guardrail suite plus a curated backend
# health/security regression slice. This is the command the
# operator should run before clicking "Save to GitHub" and "Deploy".
#
# Exit non-zero on ANY failure. No bypass, no skip, no xfail,
# no `|| true`.
#
# Usage:
#   ./scripts/predeploy_certify.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-/pw-browsers}"

echo "════════════════════════════════════════════════════════════"
echo " RC-2 PRE-DEPLOY CERTIFY"
echo "════════════════════════════════════════════════════════════"
echo ""

# 1. Live health surfaces — fail fast if backend isn't up.
echo "── Phase 1 · Live health surface smoke ──"
API_URL=$(grep REACT_APP_BACKEND_URL "$REPO_ROOT/frontend/.env" | cut -d '=' -f2 | tr -d '"' | tr -d "'")
for path in /api/health /api/health/full /api/version /api/platform/data-truth; do
  status=$(curl -sS -o /dev/null -w "%{http_code}" "${API_URL}${path}")
  echo "  ${path}: ${status}"
  if [ "$status" != "200" ]; then
    echo "  ✗ ${path} returned ${status} — aborting pre-deploy gate"
    exit 1
  fi
done
echo ""

# 2. The full RC-2 guardrail suite (calls the dedicated script).
echo "── Phase 2 · RC-2 guardrail suite ──"
bash "$REPO_ROOT/scripts/rc2_guardrails.sh"
echo ""

# 3. Targeted backend health/security regression slice (no Playwright re-run).
echo "── Phase 3 · Backend health · auth · admin-strict regression slice ──"
cd "$REPO_ROOT/backend"
python -m pytest \
  tests/test_iter183_health_full_endpoint.py \
  tests/test_rc2_auth_guardrail.py \
  tests/test_rc2_route_inventory.py \
  -v --tb=short

# 4. Track 13.4A visual render guardrail — catches the original failure
#    class (DOM exists but map is blank/clipped/zero-sized). Reads the
#    actual MapLibre canvas pixel buffer, not just selectors.
echo ""
echo "── Phase 4 · Track 13.4A Dispatch map visual render guardrail ──"
python -m pytest tests/test_track_13_4a_dispatch_map_visual_guardrail.py -v --tb=short

echo ""
echo "════════════════════════════════════════════════════════════"
echo " 🟢 PRE-DEPLOY CERTIFY PASS — ready to Save to GitHub + Deploy"
echo "════════════════════════════════════════════════════════════"
