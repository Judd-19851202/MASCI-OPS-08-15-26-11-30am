#!/usr/bin/env bash
# TRACK 15.79 · Post-Deploy Verification
#
# Runs immediately AFTER a production deploy completes. Verifies the
# live environment is actually healthy by hitting the canonical
# admin endpoints. If anything is RED, this script exits non-zero,
# which the operator's deploy runner MUST surface as a failed deploy.
#
# Usage:
#   OPS_ADMIN_EMAIL=… OPS_ADMIN_PASSWORD=… \
#     bash scripts/post_deploy_verify.sh https://mascidocs.com
#
# Exit codes:
#   0  ✅ Post-deploy health green.
#   4  ❌ /api/health unreachable (rollback recommended).
#   5  ❌ /api/admin/deployment-readiness returns decision=fail.
#   6  ❌ /api/admin/operations-trust-center 5xx.
set -euo pipefail

BASE_URL="${1:-${REACT_APP_BACKEND_URL:-}}"
if [[ -z "$BASE_URL" ]]; then
  echo "❌ usage: $0 https://your.host  (or set REACT_APP_BACKEND_URL)"
  exit 4
fi

echo "════════════════════════════════════════════════════════════"
echo "  TRACK 15.79 · POST-DEPLOY VERIFICATION"
echo "  base: $BASE_URL"
echo "  ts:   $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "════════════════════════════════════════════════════════════"

# 1 · /api/health and /api/version must return 200.
http=$(curl -s -o /tmp/health.json -w "%{http_code}" "$BASE_URL/api/health" || echo 000)
if [[ "$http" != "200" ]]; then
  echo "  ✖ /api/health returned $http — rollback recommended."
  exit 4
fi
echo "  ✓ /api/health 200"

http=$(curl -s -o /tmp/version.json -w "%{http_code}" "$BASE_URL/api/version" || echo 000)
if [[ "$http" != "200" ]]; then
  echo "  ✖ /api/version returned $http"
  exit 4
fi
backend_commit=$(python3 -c "import json;d=json.load(open('/tmp/version.json'));print(d.get('commit') or '')")
frontend_commit=$(python3 -c "import json;d=json.load(open('/tmp/version.json'));print(d.get('frontend_build_commit') or '')")
match=$(python3 -c "import json;d=json.load(open('/tmp/version.json'));print(str(bool(d.get('frontend_backend_release_match'))).lower())")
match_reason=$(python3 -c "import json;d=json.load(open('/tmp/version.json'));print(d.get('frontend_backend_release_match_reason') or '')")
build_version=$(python3 -c "import json;d=json.load(open('/tmp/version.json'));print(d.get('frontend_build_version') or '')")
build_timestamp=$(python3 -c "import json;d=json.load(open('/tmp/version.json'));print(d.get('frontend_build_built_at') or '')")
intended_commit=$(python3 -c "import json;d=json.load(open('/tmp/version.json'));print(d.get('intended_release_commit') or '')")
source_hash=$(python3 -c "import json;d=json.load(open('/tmp/version.json'));print(d.get('source_hash') or '')")
dependency_hash=$(python3 -c "import json;d=json.load(open('/tmp/version.json'));print(d.get('frontend_build_dependency_manifest_hash') or '')")
governance_hash=$(python3 -c "import json;d=json.load(open('/tmp/version.json'));print(d.get('frontend_build_release_gate_manifest_hash') or '')")
instance_fp=$(python3 -c "import json;d=json.load(open('/tmp/version.json'));print(d.get('instance_fingerprint') or '')")
app_env=$(python3 -c "import json;d=json.load(open('/tmp/version.json'));print(d.get('app_env') or '')")
verification_id=$(INSTANCE_FP="$instance_fp" FRONTEND_COMMIT="$frontend_commit" BUILD_TS="$build_timestamp" APP_ENV_VALUE="$app_env" python3 - <<'PY'
import hashlib, os
raw='|'.join([
    os.environ.get('INSTANCE_FP',''),
    os.environ.get('FRONTEND_COMMIT',''),
    os.environ.get('BUILD_TS',''),
    os.environ.get('APP_ENV_VALUE',''),
])
print(hashlib.sha256(raw.encode()).hexdigest()[:40])
PY
)
echo "  ✓ /api/version 200 · backend=${backend_commit:0:12} frontend=${frontend_commit:0:12} match=$match"

# 2 · Resolve admin token for trust endpoints.
if [[ -n "${OPS_ADMIN_TOKEN:-}" ]]; then
  TOK="$OPS_ADMIN_TOKEN"
  DIR_TOK="${OPS_DIRECTORY_TOKEN:-}"
elif [[ -n "${OPS_ADMIN_EMAIL:-}" && -n "${OPS_ADMIN_PASSWORD:-}" ]]; then
  curl -s -X POST "$BASE_URL/api/auth/multi-login" \
    -H "Content-Type: application/json" \
    -H "User-Agent: post-deploy-verify/15.79" \
    -d "{\"email\":\"$OPS_ADMIN_EMAIL\",\"password\":\"$OPS_ADMIN_PASSWORD\"}" \
    > /tmp/post_deploy_login.json
  TOK=$(python3 -c "import json;print((json.load(open('/tmp/post_deploy_login.json')).get('portal_tokens') or {}).get('admin') or '')")
  DIR_TOK=$(python3 -c "import json;print(json.load(open('/tmp/post_deploy_login.json')).get('session_token') or '')")
else
  echo "  ✖ no admin credentials provided (OPS_ADMIN_TOKEN or OPS_ADMIN_EMAIL/PASSWORD)"
  exit 5
fi
if [[ -z "$TOK" || -z "${DIR_TOK:-}" ]]; then
  echo "  ✖ unable to resolve admin token — auth degraded?"
  exit 5
fi
echo "  ✓ admin + directory tokens resolved"

# 3 · /api/health/full must be fully healthy.
health_full_http=$(curl -s -o /tmp/health_full.json -w "%{http_code}" "$BASE_URL/api/health/full" || echo 000)
if [[ "$health_full_http" != "200" ]]; then
  echo "  ✖ /api/health/full returned $health_full_http"
  cat /tmp/health_full.json
  exit 4
fi
echo "  ✓ /api/health/full 200"

# 4 · Deployment readiness MUST be decision=pass.
gate_body=$(curl -s -H "X-Admin-Token: $TOK" -H "X-Directory-Token: $DIR_TOK" \
  "$BASE_URL/api/admin/deployment-readiness")
decision=$(echo "$gate_body" | python3 -c "import sys,json;d=json.load(sys.stdin);print(d.get('decision',''))" || true)
if [[ "$decision" != "pass" ]]; then
  echo "  ✖ deployment-readiness decision=$decision (expected pass)"
  echo "$gate_body" | python3 -c "
import sys, json
d = json.load(sys.stdin)
for g in d.get('blocking_gates', [])[:5]:
    print(f\"    BLOCK [{g['category']}] {g['summary']}\")
"
  exit 5
fi
echo "  ✓ deployment-readiness decision=pass"

# 5 · Frontend/backend release parity MUST be true.
if [[ "$match" != "true" ]]; then
  echo "  ✖ frontend/backend release parity failed: $match_reason"
  exit 5
fi
intended_match=$(INTENDED_COMMIT="$intended_commit" BACKEND_COMMIT="$backend_commit" SOURCE_HASH="$source_hash" python3 - <<'PY'
import os

intended = (os.environ.get('INTENDED_COMMIT') or '').strip()
backend = (os.environ.get('BACKEND_COMMIT') or '').strip().lower()
source_hash = (os.environ.get('SOURCE_HASH') or '').strip().lower()

def commits_match(left: str, right: str):
    if not left or not right:
        return None
    left = left.lower()
    right = right.lower()
    return left.startswith(right) or right.startswith(left)

matched = None
if intended and backend:
    if intended.startswith('PRE_SAVE_CANDIDATE:'):
        parts = intended.split(':', 2)
        if len(parts) == 3 and parts[1] != 'UNPROVEN':
            matched = commits_match(parts[1], backend) is True and (not parts[2] or source_hash.startswith(parts[2]))
        else:
            matched = False
    else:
        matched = commits_match(intended, backend)
print('true' if matched is True else 'false')
PY
)
if [[ "$intended_match" != "true" ]]; then
  echo "  ✖ backend runtime commit does not match intended release commit"
  exit 5
fi
frontend_intended_match=$(INTENDED_COMMIT="$intended_commit" FRONTEND_COMMIT="$frontend_commit" SOURCE_HASH="$source_hash" python3 - <<'PY'
import os

intended = (os.environ.get('INTENDED_COMMIT') or '').strip()
frontend = (os.environ.get('FRONTEND_COMMIT') or '').strip().lower()
source_hash = (os.environ.get('SOURCE_HASH') or '').strip().lower()

def commits_match(left: str, right: str):
    if not left or not right:
        return None
    left = left.lower()
    right = right.lower()
    return left.startswith(right) or right.startswith(left)

matched = None
if intended and frontend:
    if intended.startswith('PRE_SAVE_CANDIDATE:'):
        parts = intended.split(':', 2)
        if len(parts) == 3 and parts[1] != 'UNPROVEN':
            matched = commits_match(parts[1], frontend) is True and (not parts[2] or source_hash.startswith(parts[2]))
        else:
            matched = False
    else:
        matched = commits_match(intended, frontend)
print('true' if matched is True else 'false')
PY
)
if [[ "$frontend_intended_match" != "true" ]]; then
  echo "  ✖ frontend artifact commit does not match intended release commit"
  exit 5
fi
echo "  ✓ release parity matches intended commit"

# 6 · Operations Trust Center must be reachable.
http=$(curl -s -o /tmp/otc.json -w "%{http_code}" \
  -H "X-Admin-Token: $TOK" \
  -H "X-Directory-Token: $DIR_TOK" \
  "$BASE_URL/api/admin/operations-trust-center")
if [[ "$http" != "200" ]]; then
  echo "  ✖ /api/admin/operations-trust-center returned $http"
  exit 6
fi
score=$(python3 -c "import json;d=json.load(open('/tmp/otc.json'));print(d.get('trust_score'))")
band=$(python3 -c "import json;d=json.load(open('/tmp/otc.json'));print(d.get('score_band'))")
echo "  ✓ operations-trust-center 200 · score=$score · band=$band"

# 7 · Append the post-deploy verification to the ledger and verify read-back.
curl -s -X POST "$BASE_URL/api/admin/deployment-readiness/snapshot" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Token: $TOK" \
  -H "X-Directory-Token: $DIR_TOK" \
  -H "User-Agent: post-deploy-verify/15.79" \
  -d "{\"verification_id\":\"$verification_id\",\"decision\":\"pass\",\"exit_code\":0,\"environment\":\"$app_env\",\"trust_score\":$score,\"trust_band\":\"$band\",\"operator\":\"${OPS_ADMIN_EMAIL:-ci}\",\"commit\":\"$backend_commit\",\"backend_runtime_commit\":\"$backend_commit\",\"frontend_build_commit\":\"$frontend_commit\",\"intended_release_commit\":\"$intended_commit\",\"build_version\":\"$build_version\",\"build_timestamp\":\"$build_timestamp\",\"parity_result\":true,\"parity_reason\":\"match\",\"health_ok\":true,\"health_status_code\":200,\"go_no_go\":\"GO\",\"source_hash\":\"$source_hash\",\"dependency_manifest_hash\":\"$dependency_hash\",\"governance_hash\":\"$governance_hash\",\"verification_source\":\"post_deploy_verify.sh\",\"script_version\":\"15.79\"}" \
  > /tmp/post_deploy_snapshot.json
curl -s -H "X-Admin-Token: $TOK" -H "X-Directory-Token: $DIR_TOK" "$BASE_URL/api/admin/deployment-readiness/history?limit=10" > /tmp/post_deploy_history.json
history_ok=$(VERIFY_ID="$verification_id" python3 - <<'PY'
import json, os
d=json.load(open('/tmp/post_deploy_history.json'))
target=os.environ['VERIFY_ID']
print(str(any((e.get('verification_id') == target) for e in (d.get('events') or []))).lower())
PY
)
if [[ "$history_ok" != "true" ]]; then
  echo "  ✖ deployment ledger read-back failed for verification_id=$verification_id"
  exit 6
fi
echo "  ✓ deployment ledger updated + read back"

# 8 · Trust/C2 deployment outcome must be readable via OCC trust events.
trust_http=$(curl -s -o /tmp/trust_events.json -w "%{http_code}" \
  -H "X-Admin-Token: $TOK" \
  -H "X-Directory-Token: $DIR_TOK" \
  "$BASE_URL/api/admin/occ/trust-events?limit=50")
if [[ "$trust_http" != "200" ]]; then
  echo "  ✖ /api/admin/occ/trust-events returned $trust_http"
  exit 6
fi
trust_ok=$(VERIFY_ID="$verification_id" python3 - <<'PY'
import json, os
events=(json.load(open('/tmp/trust_events.json')).get('events') or [])
target=os.environ['VERIFY_ID']
found=False
for ev in events:
    diff=((ev.get('evidence') or {}).get('diff') or {})
    if diff.get('verification_id') == target:
        found=True
        break
print(str(found).lower())
PY
)
if [[ "$trust_ok" != "true" ]]; then
  echo "  ✖ OCC trust-events missing deployment outcome for verification_id=$verification_id"
  exit 6
fi
echo "  ✓ OCC trust-events exposes deployment outcome"

echo ""
echo "  ✅ POST-DEPLOY VERIFICATION PASSED"
exit 0
