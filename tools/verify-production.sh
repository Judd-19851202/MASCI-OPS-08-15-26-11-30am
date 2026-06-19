#!/usr/bin/env bash
# tools/verify-production.sh — Production Health Smoke
#
# Run this AFTER every production deploy. Returns exit 0 if every probed
# endpoint is healthy, exit 1 otherwise. Designed to be readable at a
# glance by a non-coder.
#
# Usage:
#   ./tools/verify-production.sh               # uses mascidocs.com
#   PROD_URL=https://other.host ./tools/verify-production.sh
#   SOAK_SECONDS=30 ./tools/verify-production.sh   # override soak window
#   STRICT_NO_SOAK=1 ./tools/verify-production.sh  # disable double-take (post-deploy use)
#
# What it checks:
#   1. /api/health                                  (any non-200 → backend is down)
#   2. /api/passkeys/login/options                  (any 5xx → passkeys broken)
#   3. /api/admin-strict/diag/persistence-health    (admin-only · sanity probe)
#   4. /api/field-memory/recent                     (any portal token shape)
#   5. /api/dispatch/operational-moments/by-assignment/test
#
# It does NOT run the full test suite — that runs in CI / pytest. This is
# a 5-second smoke that catches the EXACT class of failure that caused
# the iter435 production incident (preview was green · production was 520).
#
# TRACK 15.34B (2026-02) — added double-take soak + diagnostic output.
# A single 25-second blip on a GitHub-hosted runner no longer triggers an
# alert; the workflow must show red on BOTH passes (default 30s apart)
# before the job exits non-zero. Real outages (>60s) still fail and alert.

set -u
PROD_URL="${PROD_URL:-https://mascidocs.com}"
SOAK_SECONDS="${SOAK_SECONDS:-30}"
STRICT_NO_SOAK="${STRICT_NO_SOAK:-0}"

# ANSI colors only when stdout is a TTY (CI logs render escape sequences
# literally otherwise — confusing in failure emails).
if [[ -t 1 ]]; then
  GOOD="\033[0;32m✅\033[0m"
  BAD="\033[0;31m❌\033[0m"
  WARN="\033[0;33m⚠️\033[0m"
  DIM="\033[0;90m"
  BOLD="\033[1m"
  RESET="\033[0m"
else
  GOOD="OK   "
  BAD="FAIL "
  WARN="WARN "
  DIM=""
  BOLD=""
  RESET=""
fi

# Probe table: each row = "label | expect | method | extra_args | url"
# expect:
#   ok     → must be exactly 200
#   auth   → must be 200, 401, or 403 (auth gate live = healthy)
#   route  → must be 100-499 (route exists, no 5xx, no network failure)
PROBES=(
  "GET  /api/health|ok|GET||${PROD_URL}/api/health"
  "POST /api/passkeys/login/options|route|POST|-H|Content-Type: application/json|-d|{\"email\":\"smoke@example.com\"}|${PROD_URL}/api/passkeys/login/options"
  "GET  /api/admin-strict/diag/persistence-health|auth|GET||${PROD_URL}/api/admin-strict/diag/persistence-health"
  "GET  /api/field-memory/recent|auth|GET||${PROD_URL}/api/field-memory/recent"
  "GET  /api/dispatch/operational-moments/by-assignment/test|auth|GET||${PROD_URL}/api/dispatch/operational-moments/by-assignment/test"
)

# ---------------------------------------------------------------------------
# probe_once: run one HTTP probe with full diagnostic capture.
# Returns 0 if healthy, 1 if unhealthy.
# Side effects: sets PROBE_CODE, PROBE_EXITCODE, PROBE_ERRMSG, PROBE_DNS,
#               PROBE_CONNECT, PROBE_TOTAL, PROBE_BODY_EXCERPT.
# ---------------------------------------------------------------------------
probe_once() {
  local label="$1"; local expect="$2"; local method="$3"; shift 3
  # Remaining positional args = extra headers / body + final URL.
  # The URL is always the LAST argument.
  local url="${@: -1}"
  local extra_args=("${@:1:$#-1}")

  local body_file
  body_file=$(mktemp)
  local writeout="code=%{http_code}|exitcode=%{exitcode}|errormsg=%{errormsg}|dns=%{time_namelookup}|connect=%{time_connect}|total=%{time_total}"

  local raw
  # NOTE: NO --retry here. We do the retry ourselves via the double-take
  # soak (see main loop). Single-attempt -w output is then unambiguous.
  raw=$(curl -sS -m 8 \
              -X "$method" \
              "${extra_args[@]}" \
              -o "$body_file" \
              -w "$writeout" \
              "$url" 2>/dev/null || true)

  PROBE_CODE=$(echo "$raw" | sed -n 's/.*code=\([0-9]\{3\}\).*/\1/p')
  PROBE_EXITCODE=$(echo "$raw" | sed -n 's/.*exitcode=\([0-9]\+\).*/\1/p')
  PROBE_ERRMSG=$(echo "$raw" | sed -n 's/.*errormsg=\([^|]*\)|dns=.*/\1/p')
  PROBE_DNS=$(echo "$raw" | sed -n 's/.*dns=\([0-9.]\+\).*/\1/p')
  PROBE_CONNECT=$(echo "$raw" | sed -n 's/.*connect=\([0-9.]\+\).*/\1/p')
  PROBE_TOTAL=$(echo "$raw" | sed -n 's/.*total=\([0-9.]\+\)$/\1/p')
  PROBE_BODY_EXCERPT=$(head -c 200 "$body_file" 2>/dev/null | tr '\n' ' ')
  rm -f "$body_file"

  # Defaults in case sed missed anything
  PROBE_CODE="${PROBE_CODE:-000}"
  PROBE_EXITCODE="${PROBE_EXITCODE:-0}"
  PROBE_ERRMSG="${PROBE_ERRMSG:-}"
  PROBE_DNS="${PROBE_DNS:-0}"
  PROBE_CONNECT="${PROBE_CONNECT:-0}"
  PROBE_TOTAL="${PROBE_TOTAL:-0}"

  # Strict status code evaluation — regex-based, no bash arithmetic on
  # possibly-empty/non-numeric strings.
  case "$expect" in
    ok)
      [[ "$PROBE_CODE" == "200" ]] && return 0 ;;
    auth)
      [[ "$PROBE_CODE" =~ ^(200|401|403)$ ]] && return 0 ;;
    route)
      # Route exists, no 5xx, no network failure (000 = curl failure).
      [[ "$PROBE_CODE" =~ ^[1-4][0-9][0-9]$ ]] && return 0 ;;
  esac
  return 1
}

# ---------------------------------------------------------------------------
# render_probe: pretty-print one probe result.
# ---------------------------------------------------------------------------
render_probe() {
  local label="$1"; local healthy="$2"; local detail_on_fail="$3"
  if [[ "$healthy" == "1" ]]; then
    printf "  ${GOOD} %-58s ${DIM}HTTP %s · ${PROBE_TOTAL}s${RESET}\n" "$label" "$PROBE_CODE"
  else
    printf "  ${BAD} %-58s ${DIM}HTTP %s · curl_exit=%s${RESET}\n" "$label" "$PROBE_CODE" "$PROBE_EXITCODE"
    if [[ "$detail_on_fail" == "1" ]]; then
      printf "        ${DIM}└─ DNS=${PROBE_DNS}s  connect=${PROBE_CONNECT}s  total=${PROBE_TOTAL}s${RESET}\n"
      if [[ -n "$PROBE_ERRMSG" ]]; then
        printf "        ${DIM}└─ curl: %s${RESET}\n" "$PROBE_ERRMSG"
      fi
      if [[ -n "$PROBE_BODY_EXCERPT" ]]; then
        printf "        ${DIM}└─ body: %s${RESET}\n" "${PROBE_BODY_EXCERPT:0:180}"
      fi
    fi
  fi
}

# ---------------------------------------------------------------------------
# run_pass: run all probes once. Records per-probe healthy/unhealthy in
# PASS_RESULTS[]. Returns number of failures.
# ---------------------------------------------------------------------------
PASS_RESULTS=()
run_pass() {
  local pass_label="$1"; local show_detail="$2"
  local fails=0
  PASS_RESULTS=()
  echo ""
  echo "  ${BOLD}${pass_label}${RESET} @ ${PROD_URL}"
  echo "  ────────────────────────────────────────────────────────────────────"
  for probe_def in "${PROBES[@]}"; do
    IFS='|' read -ra parts <<< "$probe_def"
    local label="${parts[0]}"
    local expect="${parts[1]}"
    local method="${parts[2]}"
    local rest=("${parts[@]:3}")
    if probe_once "$label" "$expect" "$method" "${rest[@]}"; then
      PASS_RESULTS+=("1")
      render_probe "$label" 1 0
    else
      PASS_RESULTS+=("0")
      fails=$((fails + 1))
      render_probe "$label" 0 "$show_detail"
    fi
  done
  echo "  ────────────────────────────────────────────────────────────────────"
  return $fails
}

# ---------------------------------------------------------------------------
# Main: first pass; if any failures and soak enabled, sleep then re-probe
# ONLY the failed probes; only count failures that persist on both passes.
# ---------------------------------------------------------------------------
START=$(date +%s)

run_pass "Pass 1 · production health smoke" 0 || true
FIRST_PASS_RESULTS=("${PASS_RESULTS[@]}")
first_pass_fails=0
for r in "${FIRST_PASS_RESULTS[@]}"; do
  [[ "$r" == "0" ]] && first_pass_fails=$((first_pass_fails + 1))
done

if [[ $first_pass_fails -eq 0 ]]; then
  ELAPSED=$(( $(date +%s) - START ))
  printf "\n  ${GOOD} All %d probes healthy in %ds.\n\n" ${#PROBES[@]} "$ELAPSED"
  exit 0
fi

# Soak path — only if not explicitly disabled.
if [[ "$STRICT_NO_SOAK" == "1" ]]; then
  ELAPSED=$(( $(date +%s) - START ))
  echo ""
  printf "  ${BAD} %d probe(s) failed in %ds (soak disabled via STRICT_NO_SOAK=1).\n" "$first_pass_fails" "$ELAPSED"
  echo "      → Check the Emergent deploy dashboard:"
  echo "        1. Is the production deployment 'Running' (not 'Failed' or 'CrashLoop')?"
  echo "        2. Are MONGO_URL + DB_NAME current?"
  echo "        3. Does the deploy log show 'Authentication failed' or 'MongoServerSelectionError'?"
  echo ""
  exit 1
fi

echo ""
printf "  ${WARN} %d probe(s) red on pass 1. Soaking %ds before pass 2…\n" "$first_pass_fails" "$SOAK_SECONDS"
sleep "$SOAK_SECONDS"

# Pass 2 — re-run ALL probes (cheap + simpler than tracking which ones
# failed). Print full diagnostic detail on any pass-2 failure.
run_pass "Pass 2 · soak re-verify" 1 || true
SECOND_PASS_RESULTS=("${PASS_RESULTS[@]}")

# A probe is a "real" failure only if it failed on BOTH passes.
real_fails=0
flaky_recoveries=0
for i in "${!FIRST_PASS_RESULTS[@]}"; do
  first="${FIRST_PASS_RESULTS[$i]}"
  second="${SECOND_PASS_RESULTS[$i]}"
  if [[ "$first" == "0" && "$second" == "0" ]]; then
    real_fails=$((real_fails + 1))
  elif [[ "$first" == "0" && "$second" == "1" ]]; then
    flaky_recoveries=$((flaky_recoveries + 1))
  fi
done

ELAPSED=$(( $(date +%s) - START ))

if [[ $real_fails -eq 0 ]]; then
  echo ""
  printf "  ${GOOD} All probes healthy on pass 2 (had %d flaky recovery transient(s) on pass 1).\n" "$flaky_recoveries"
  printf "  ${DIM}    Total runtime: %ds. Treated as healthy — no alert.${RESET}\n\n" "$ELAPSED"
  exit 0
fi

echo ""
printf "  ${BAD} %d probe(s) RED on both passes (real outage signal) in %ds.\n" "$real_fails" "$ELAPSED"
if [[ $flaky_recoveries -gt 0 ]]; then
  printf "  ${DIM}     (%d additional probes were transient — recovered on pass 2 — not counted.)${RESET}\n" "$flaky_recoveries"
fi
echo "      → Check the Emergent deploy dashboard:"
echo "        1. Is the production deployment 'Running' (not 'Failed' or 'CrashLoop')?"
echo "        2. Are MONGO_URL + DB_NAME current?"
echo "        3. Does the deploy log show 'Authentication failed' or 'MongoServerSelectionError'?"
echo ""
exit 1
