#!/usr/bin/env bash
# verify_env_identity.sh — iter437 · Sigma-III · P0 incident learning
#
# Probes a backend URL's `/api/version` endpoint and asserts that the
# running container reports the expected `app_env` AND `db_name`. This
# is the LAST LINE of doctrine enforcement, after `pre_deploy_check.sh`
# and the in-process `_verify_env_db_alignment()` startup guard.
#
# Why this exists:
#   On 2026-05-26, the production deployment crash-looped for 10+ minutes
#   because the operator could not prove which env vars the running
#   container was actually using. The Emergent dashboard reported one
#   thing; the container's runtime identity was unknowable from outside.
#   This script makes the runtime identity provable in ONE curl command,
#   so any future deploy can be smoke-checked against doctrine in <1s.
#
# Usage:
#   ./verify_env_identity.sh <url> <expected_app_env> <expected_db_name>
#
# Examples:
#   # Production must report APP_ENV=production · DB_NAME=masci_safety
#   ./verify_env_identity.sh https://mascidocs.com production masci_safety
#
#   # Preview must report APP_ENV=preview · DB_NAME=masci_safety_preview
#   ./verify_env_identity.sh https://backup-forensics.preview.emergentagent.com preview masci_safety_preview
#
# Exit codes:
#   0   identity matches
#   1   identity mismatch (with diff printed to stderr)
#   2   /api/version unreachable
#   3   /api/version returned but missing `app_env` or `db_name` (stale build)
#   4   bad arguments

set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "usage: $0 <url> <expected_app_env> <expected_db_name>" >&2
  exit 4
fi

URL="$1"
EXP_ENV="$2"
EXP_DB="$3"

VERSION_JSON="$(curl -fsS -m 10 "$URL/api/version" 2>/dev/null || true)"
if [[ -z "$VERSION_JSON" ]]; then
  echo "❌ ${URL}/api/version unreachable" >&2
  exit 2
fi

# Parse with python3 to keep this script dependency-free of jq.
parse() {
  python3 -c "
import sys, json
d = json.loads(sys.stdin.read() or '{}')
print(d.get('$1', '<MISSING>'))
" <<< "$VERSION_JSON"
}

GOT_ENV="$(parse app_env)"
GOT_DB="$(parse db_name)"
GOT_HASH="$(parse source_hash)"
GOT_UPTIME="$(parse uptime_s)"

if [[ "$GOT_ENV" == "<MISSING>" || "$GOT_DB" == "<MISSING>" || "$GOT_ENV" == "None" || "$GOT_DB" == "None" ]]; then
  echo "❌ /api/version returned but did NOT report app_env/db_name." >&2
  echo "   This is a STALE build that predates iter437 Phase Sigma-II." >&2
  echo "   Cannot prove identity. Block the deploy and force a rebuild." >&2
  exit 3
fi

ok=true
if [[ "$GOT_ENV" != "$EXP_ENV" ]]; then ok=false; fi
if [[ "$GOT_DB" != "$EXP_DB" ]]; then ok=false; fi

if [[ "$ok" == "true" ]]; then
  echo "✅ IDENTITY MATCH"
  echo "   url        : $URL"
  echo "   app_env    : $GOT_ENV"
  echo "   db_name    : $GOT_DB"
  echo "   source_hash: $GOT_HASH"
  echo "   uptime_s   : $GOT_UPTIME"
  exit 0
fi

echo "❌ IDENTITY MISMATCH — DEPLOY MUST NOT PROCEED" >&2
echo "   url        : $URL" >&2
echo "   app_env    : expected=$EXP_ENV  got=$GOT_ENV" >&2
echo "   db_name    : expected=$EXP_DB   got=$GOT_DB" >&2
echo "   source_hash: $GOT_HASH" >&2
echo "   uptime_s   : $GOT_UPTIME" >&2
echo "" >&2
echo "Fix the wrong env var in the Emergent deploy dashboard for this" >&2
echo "environment, save, redeploy, then re-run this check before allowing" >&2
echo "any other write traffic." >&2
exit 1
