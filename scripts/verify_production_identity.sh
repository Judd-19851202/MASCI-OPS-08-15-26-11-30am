#!/usr/bin/env bash
# verify_production_identity.sh — iter437 · P0-incident learning
#
# Run this IMMEDIATELY after every production redeploy on mascidocs.com.
# It proves the new container came up with the correct env identity.
#
# This script is the post-deploy half of the doctrine added after the
# 2026-02 production crash-loop:
#
#   Doctrine:
#     Before any future deploy, production must prove:
#       APP_ENV = production
#       DB_NAME = masci_safety
#     Preview must prove:
#       APP_ENV = preview
#       DB_NAME = masci_safety_preview
#
# Companion:
#   - `pre_deploy_check.sh` proves preview identity BEFORE the deploy.
#   - This script proves production identity AFTER the deploy.
#
# Usage:
#   ./verify_production_identity.sh
#
# It polls `https://mascidocs.com/api/version` for up to 5 minutes
# (the typical Emergent deploy window). When the new container comes
# up, it asserts app_env=production AND db_name=masci_safety.
#
# Exit codes:
#   0   production came up healthy with correct identity
#   1   production came up but identity mismatch (DEPLOY BAD — investigate or rollback)
#   2   production never came up within timeout (deploy still in flight or crashed)
#
# Note: the previous source_hash MAY be supplied as $1 — if so, the
# script will refuse to declare success until the hash flips (i.e.,
# the new build is actually running, not just the old one still alive).
set -uo pipefail

PROD_URL="${PROD_URL:-https://mascidocs.com}"
EXPECTED_APP_ENV="${EXPECTED_APP_ENV:-production}"
EXPECTED_DB_NAME="${EXPECTED_DB_NAME:-masci_safety}"
MAX_WAIT_SECONDS="${MAX_WAIT_SECONDS:-300}"
POLL_INTERVAL_SECONDS=10
PREV_HASH="${1:-}"

start_epoch=$(date +%s)
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  Production identity verification"
echo "    target          : $PROD_URL"
echo "    expected APP_ENV: $EXPECTED_APP_ENV"
echo "    expected DB_NAME: $EXPECTED_DB_NAME"
echo "    expecting hash  : $( [[ -n "$PREV_HASH" ]] && echo "anything != $PREV_HASH" || echo "(any)" )"
echo "    max wait        : ${MAX_WAIT_SECONDS}s"
echo "════════════════════════════════════════════════════════════════"

while true; do
  now=$(date +%s)
  elapsed=$(( now - start_epoch ))

  if [[ $elapsed -ge $MAX_WAIT_SECONDS ]]; then
    echo ""
    echo "❌ TIMEOUT after ${elapsed}s — production never came up healthy." >&2
    echo "   Action: open Emergent deploy dashboard, pull startup logs," >&2
    echo "   look for the MASCI-HUB ENVIRONMENT SAFETY CHECK banner OR" >&2
    echo "   a startup traceback, fix the env mismatch, redeploy." >&2
    exit 2
  fi

  resp=$(curl -fsS -m 10 "$PROD_URL/api/version" 2>/dev/null || true)
  if [[ -z "$resp" ]]; then
    printf "\r  ⏳ %3ds elapsed · /api/version unreachable (520/timeout) ..." "$elapsed"
    sleep "$POLL_INTERVAL_SECONDS"
    continue
  fi

  # Parse three fields.
  read -r got_env got_db got_hash uptime_s <<< "$(python3 -c "
import sys, json
d = json.loads(sys.stdin.read() or '{}')
print(d.get('app_env','<MISSING>'), d.get('db_name','<MISSING>'), d.get('source_hash','<MISSING>'), d.get('uptime_s','<MISSING>'))
" <<< "$resp")"

  if [[ -n "$PREV_HASH" && "$got_hash" == "$PREV_HASH" ]]; then
    printf "\r  ⏳ %3ds elapsed · still on OLD build (%s) — waiting for redeploy ..." "$elapsed" "$got_hash"
    sleep "$POLL_INTERVAL_SECONDS"
    continue
  fi

  # New container is up. Lock in the verdict.
  echo ""
  echo ""
  if [[ "$got_env" == "$EXPECTED_APP_ENV" && "$got_db" == "$EXPECTED_DB_NAME" ]]; then
    echo "✅ PRODUCTION IDENTITY VERIFIED"
    echo "   source_hash : $got_hash"
    echo "   app_env     : $got_env"
    echo "   db_name     : $got_db"
    echo "   uptime_s    : $uptime_s"
    echo ""
    echo "   Safe to direct user traffic. Proceed with post-deploy"
    echo "   smoke (multi-login + 7-portal sweep)."
    exit 0
  fi

  echo "❌ PRODUCTION IDENTITY MISMATCH — DEPLOY MUST BE ROLLED BACK" >&2
  echo "   source_hash : $got_hash" >&2
  echo "   app_env     : expected=$EXPECTED_APP_ENV  got=$got_env" >&2
  echo "   db_name     : expected=$EXPECTED_DB_NAME  got=$got_db" >&2
  echo "   uptime_s    : $uptime_s" >&2
  echo "" >&2
  echo "   Action: open Emergent deploy dashboard, correct the env" >&2
  echo "   var on the production deployment, save, redeploy. Do NOT" >&2
  echo "   send user traffic to this build." >&2
  exit 1
done
