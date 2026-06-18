#!/usr/bin/env bash
# tools/verify-production.sh — iter436 · Phase 32 · Production Health Smoke
#
# Run this AFTER every production deploy. Returns exit 0 if every probed
# endpoint is healthy, exit 1 otherwise. Designed to be readable at a
# glance by a non-coder.
#
# Usage:
#   ./tools/verify-production.sh               # uses mascidocs.com
#   PROD_URL=https://other.host ./tools/verify-production.sh
#
# What it checks:
#   1. /api/health                                  (any 5xx → backend is down)
#   2. /api/passkeys/login/options                  (any 5xx → passkeys broken)
#   3. /api/admin-strict/diag/persistence-health    (admin-only · sanity probe)
#   4. /api/field-memory/recent                     (any portal token shape)
#
# It does NOT run the full test suite — that runs in CI / pytest. This is
# a 5-second smoke that catches the EXACT class of failure that caused
# the iter435 production incident (preview was green · production was 520).

set -u
PROD_URL="${PROD_URL:-https://mascidocs.com}"
GOOD="\033[0;32m✅\033[0m"
BAD="\033[0;31m❌\033[0m"
DIM="\033[0;90m"
RESET="\033[0m"

FAIL_COUNT=0
START=$(date +%s)

probe() {
  local label="$1" ; shift
  local expect="$1" ; shift   # 'ok' for 200, 'auth' for 200|401, 'route' for any non-5xx
  local code
  # TRACK 15.26 · iter440 · two-retry buffer for transient runner-side
  # network blips. The 15-minute monitor should only ring when the
  # platform is genuinely down, not when a GitHub-hosted runner has a
  # 1-second DNS hiccup mid-probe.
  code=$(curl -sS -m 8 --retry 2 --retry-all-errors --retry-delay 1 \
              -o /dev/null -w "%{http_code}" "$@" 2>/dev/null || echo "000")
  local ok=0
  case "$expect" in
    ok)    [[ "$code" == "200" ]] && ok=1 ;;
    auth)  [[ "$code" == "200" || "$code" == "401" || "$code" == "403" ]] && ok=1 ;;
    route) [[ "$code" != "000" && "$code" -lt 500 ]] && ok=1 ;;
  esac
  if [[ $ok -eq 1 ]]; then
    printf "  ${GOOD} %-45s ${DIM}HTTP %s${RESET}\n" "$label" "$code"
  else
    printf "  ${BAD} %-45s ${DIM}HTTP %s${RESET}\n" "$label" "$code"
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
}

echo ""
echo "  Production health smoke @ ${PROD_URL}"
echo "  ────────────────────────────────────────────────────────────"

probe "GET  /api/health" ok \
  "${PROD_URL}/api/health"

probe "POST /api/passkeys/login/options" route \
  -X POST -H "Content-Type: application/json" \
  -d '{"email":"smoke@example.com"}' \
  "${PROD_URL}/api/passkeys/login/options"

probe "GET  /api/admin-strict/diag/persistence-health" auth \
  "${PROD_URL}/api/admin-strict/diag/persistence-health"

probe "GET  /api/field-memory/recent" auth \
  "${PROD_URL}/api/field-memory/recent"

probe "GET  /api/dispatch/operational-moments/by-assignment/test" auth \
  "${PROD_URL}/api/dispatch/operational-moments/by-assignment/test"

ELAPSED=$(( $(date +%s) - START ))
echo "  ────────────────────────────────────────────────────────────"
if [[ $FAIL_COUNT -eq 0 ]]; then
  printf "  ${GOOD} All %d probes healthy in %ds.\n\n" 5 "$ELAPSED"
  exit 0
else
  printf "  ${BAD} %d probe(s) failed in %ds.\n" "$FAIL_COUNT" "$ELAPSED"
  echo "      → Check the Emergent deploy dashboard:"
  echo "        1. Is the production deployment 'Running' (not 'Failed' or 'CrashLoop')?"
  echo "        2. Are MONGO_URL + DB_NAME current?"
  echo "        3. Does the deploy log show 'Authentication failed' or 'MongoServerSelectionError'?"
  echo ""
  exit 1
fi
