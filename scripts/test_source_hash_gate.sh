#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# test_source_hash_gate.sh — Phase IV-BETA.5A-P7 · proves all three branches
#                              of the source-hash drift report stage in
#                              pre_deploy_check.sh fire correctly.
#
# Branches tested:
#   1. preview_hash == prod_hash       →  "production already current"
#   2. preview_hash != prod_hash       →  "production behind preview"
#   3. production unreachable          →  "⚠ ... unreachable ... soft warn"
#
# No network. No production calls. Uses two ephemeral python http.servers
# bound to localhost on free ports. Port is captured via mkfifo from the
# fixture's stdout (no lsof / ss dependency).
# ─────────────────────────────────────────────────────────────────────────────
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT="$REPO_ROOT/scripts/pre_deploy_check.sh"

PASS=0
FAIL=0
PV_PID=""
PR_PID=""

cleanup() {
  [[ -n "${PV_PID:-}" ]] && kill "$PV_PID" 2>/dev/null
  [[ -n "${PR_PID:-}" ]] && kill "$PR_PID" 2>/dev/null
  rm -rf /tmp/shgate_test_*
  return 0
}
trap cleanup EXIT

# Fixture: starts a python http.server returning the given JSON on
# /api/version. Writes the bound port to /tmp/shgate_test_$tag/port.
start_fixture() {
  local hash="$1" tag="$2"
  local workdir="/tmp/shgate_test_$tag"
  mkdir -p "$workdir"
  rm -f "$workdir/port"
  python3 -u -c "
import http.server, socketserver, json
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != '/api/version':
            self.send_response(404); self.end_headers(); return
        body = json.dumps({'source_hash': '$hash'}).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, *a, **k): pass
with socketserver.TCPServer(('127.0.0.1', 0), H) as s:
    with open('$workdir/port', 'w') as f:
        f.write(str(s.server_address[1]))
    s.serve_forever()
" >/dev/null 2>&1 &
  local pid=$!
  # Wait for port file to appear
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    [[ -s "$workdir/port" ]] && break
    sleep 0.2
  done
  if [[ ! -s "$workdir/port" ]]; then
    echo "FATAL: fixture failed to bind" >&2
    kill "$pid" 2>/dev/null
    return 1
  fi
  printf '%s %s' "$pid" "$(cat "$workdir/port")"
}

# Invoke the stage directly with controlled inputs.
run_stage_with_env() {
  local preview_url="$1" prod_url="$2"
  local sandbox="/tmp/shgate_test_run"
  rm -rf "$sandbox"
  mkdir -p "$sandbox/frontend"
  echo "REACT_APP_BACKEND_URL=$preview_url" > "$sandbox/frontend/.env"
  # Extract just the function definition
  awk '/^stage_source_hash_drift_report\(\) \{/,/^\}$/' "$SCRIPT" > "$sandbox/stage_fn.sh"
  bash -c "
    set -uo pipefail
    cd '$sandbox'
    source './stage_fn.sh'
    PRODUCTION_URL='$prod_url' stage_source_hash_drift_report
  " 2>&1
}

assert_contains() {
  local label="$1" haystack="$2" needle="$3"
  if printf '%s' "$haystack" | grep -qF -- "$needle"; then
    echo "  ✓ $label"
    PASS=$((PASS+1))
  else
    echo "  ✗ $label"
    echo "    expected to contain: $needle"
    echo "    actual output:"
    printf '%s\n' "$haystack" | sed 's/^/      /'
    FAIL=$((FAIL+1))
  fi
}

echo "════════════════════════════════════════════════════════════════"
echo "  source-hash gate · branch test (IV-BETA.5A-P7)"
echo "════════════════════════════════════════════════════════════════"

# ── Branch 1: equal hashes → "production already current"
echo ""
echo "── Branch 1: preview_hash == prod_hash ─────────"
HASH1="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
read -r PV_PID PV_PORT <<< "$(start_fixture "$HASH1" pv1)"
read -r PR_PID PR_PORT <<< "$(start_fixture "$HASH1" pr1)"
out=$(run_stage_with_env "http://127.0.0.1:$PV_PORT" "http://127.0.0.1:$PR_PORT")
assert_contains "reports preview hash"      "$out" "source_hash = $HASH1"
assert_contains "reports prod hash equal"   "$out" "source_hash = $HASH1"
assert_contains "reports 'already current'" "$out" "production already current"
kill "$PV_PID" "$PR_PID" 2>/dev/null
PV_PID=""; PR_PID=""

# ── Branch 2: preview ahead of production
echo ""
echo "── Branch 2: preview_hash != prod_hash ─────────"
HASH_PV="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
HASH_PR="cccccccccccccccccccccccccccccccc"
read -r PV_PID PV_PORT <<< "$(start_fixture "$HASH_PV" pv2)"
read -r PR_PID PR_PORT <<< "$(start_fixture "$HASH_PR" pr2)"
out=$(run_stage_with_env "http://127.0.0.1:$PV_PORT" "http://127.0.0.1:$PR_PORT")
assert_contains "reports preview hash"            "$out" "source_hash = $HASH_PV"
assert_contains "reports prod hash different"     "$out" "source_hash = $HASH_PR"
assert_contains "reports 'production behind preview'" "$out" "production behind preview"
assert_contains "reports both hashes inline"      "$out" "preview_hash=$HASH_PV · prod_hash=$HASH_PR"
kill "$PV_PID" "$PR_PID" 2>/dev/null
PV_PID=""; PR_PID=""

# ── Branch 3: production unreachable
echo ""
echo "── Branch 3: production unreachable ─────────"
HASH_PV="dddddddddddddddddddddddddddddddd"
read -r PV_PID PV_PORT <<< "$(start_fixture "$HASH_PV" pv3)"
out=$(run_stage_with_env "http://127.0.0.1:$PV_PORT" "http://127.0.0.1:1")
assert_contains "preview ok"                "$out" "source_hash = $HASH_PV"
assert_contains "prod marked <unreachable>" "$out" "<unreachable>"
assert_contains "soft warn surfaced"        "$out" "soft warn"
kill "$PV_PID" 2>/dev/null
PV_PID=""

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  Passed: $PASS    Failed: $FAIL"
if [[ "$FAIL" -gt 0 ]]; then
  echo "  ❌ source-hash gate test FAILED"
  exit 1
fi
echo "  ✓ source-hash gate · all 3 branches behave as documented"
exit 0
