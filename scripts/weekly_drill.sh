#!/bin/bash
# weekly_drill.sh — Phase 2 · Continuous Recoverability cron entry point
#
# Purpose: cron-friendly wrapper that runs ONE automated drill cycle against
# the latest healthy production archive.
#
# Design intent (per CONTINUOUS_RECOVERABILITY_CERTIFICATION.md):
#   * Zero scheduler logic change inside the backend
#   * Operator controls cadence via external cron (or Emergent's scheduled
#     job feature) — drill is cadence-agnostic by code
#   * Idempotent · safe to re-run
#   * Failures exit non-zero so cron can route to alerting
#
# Required env (inherited from /app/backend/.env or shell):
#   MONGO_URL              · Atlas connection
#   DB_NAME                · live source DB (drill_runs lands here)
#   S3_ENDPOINT_URL · S3_BUCKET · S3_ACCESS_KEY · S3_SECRET_KEY
#
# Operator activation example (paste into Emergent platform scheduled job
# or external cron):
#
#   # Weekly · Sundays 04:00 UTC · output captured for audit trail
#   0 4 * * 0  /bin/bash /app/scripts/weekly_drill.sh \
#               >> /var/log/masci/weekly_drill.log 2>&1
#
# That single line is the entire activation. NO backend code change.
# NO scheduler logic change. NO new internal cron registered inside
# server.py / singleton_scheduler.py.

set -euo pipefail

LOG_DIR=${MASCI_DRILL_LOG_DIR:-/tmp}
mkdir -p "$LOG_DIR"
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
LOG="$LOG_DIR/weekly_drill_${STAMP}.log"

# Resolve repo root from this script's location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=== MASCI weekly drill · ${STAMP} ===" | tee -a "$LOG"
echo "repo_root: ${REPO_ROOT}" | tee -a "$LOG"

# Load .env (best-effort · prod cron may inject env directly)
if [ -f "${REPO_ROOT}/backend/.env" ]; then
  set -a
  # shellcheck disable=SC1090
  source <(sed 's/\r$//' "${REPO_ROOT}/backend/.env" | grep -E '^[A-Z_]+=' | sed 's/^/export /')
  set +a
fi

# Sanity check required env
: "${MONGO_URL:?MONGO_URL not set}"
: "${S3_BUCKET:?S3_BUCKET not set}"

# Invoke the drill (auto-pick latest healthy archive)
echo "[$(date -u +%FT%TZ)] launching automated_drill.py --auto" | tee -a "$LOG"
if python3 "${REPO_ROOT}/scripts/automated_drill.py" --auto 2>&1 | tee -a "$LOG"; then
  RC=0
else
  RC=$?
fi

echo "[$(date -u +%FT%TZ)] drill exited with code ${RC}" | tee -a "$LOG"

# Exit codes from automated_drill.py:
#   0 = PASS · all 10 axes green
#   9 = drill ran but ≥ 1 axis red (regression/drift detected)
#   1 = bad invocation
#   2 = env misconfigured
exit "$RC"
