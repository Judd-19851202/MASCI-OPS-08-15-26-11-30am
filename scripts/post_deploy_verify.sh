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

# 1 · /api/health must return 200.
http=$(curl -s -o /tmp/health.json -w "%{http_code}" "$BASE_URL/api/health" || echo 000)
if [[ "$http" != "200" ]]; then
  echo "  ✖ /api/health returned $http — rollback recommended."
  exit 4
fi
echo "  ✓ /api/health 200"

# 2 · Resolve admin token for trust endpoints.
if [[ -n "${OPS_ADMIN_TOKEN:-}" ]]; then
  TOK="$OPS_ADMIN_TOKEN"
elif [[ -n "${OPS_ADMIN_EMAIL:-}" && -n "${OPS_ADMIN_PASSWORD:-}" ]]; then
  TOK=$(curl -s -X POST "$BASE_URL/api/auth/multi-login" \
    -H "Content-Type: application/json" \
    -H "User-Agent: post-deploy-verify/15.79" \
    -d "{\"email\":\"$OPS_ADMIN_EMAIL\",\"password\":\"$OPS_ADMIN_PASSWORD\"}" \
    | python3 -c "import sys,json;print((json.load(sys.stdin).get('portal_tokens') or {}).get('admin') or '')")
else
  echo "  ✖ no admin credentials provided (OPS_ADMIN_TOKEN or OPS_ADMIN_EMAIL/PASSWORD)"
  exit 5
fi
if [[ -z "$TOK" ]]; then
  echo "  ✖ unable to resolve admin token — auth degraded?"
  exit 5
fi
echo "  ✓ admin token resolved"

# 3 · Deployment readiness MUST be decision=pass.
gate_body=$(curl -s -H "X-Admin-Token: $TOK" \
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

# 4 · Operations Trust Center must be reachable.
http=$(curl -s -o /tmp/otc.json -w "%{http_code}" \
  -H "X-Admin-Token: $TOK" \
  "$BASE_URL/api/admin/operations-trust-center")
if [[ "$http" != "200" ]]; then
  echo "  ✖ /api/admin/operations-trust-center returned $http"
  exit 6
fi
score=$(python3 -c "import json;d=json.load(open('/tmp/otc.json'));print(d.get('trust_score'))")
band=$(python3 -c "import json;d=json.load(open('/tmp/otc.json'));print(d.get('score_band'))")
echo "  ✓ operations-trust-center 200 · score=$score · band=$band"

# 5 · Append the post-deploy verification to the ledger.
curl -s -X POST "$BASE_URL/api/admin/deployment-readiness/snapshot" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Token: $TOK" \
  -H "User-Agent: post-deploy-verify/15.79" \
  -d "{\"decision\":\"pass\",\"exit_code\":0,\"environment\":\"post-deploy\",\"trust_score\":$score,\"trust_band\":\"$band\",\"operator\":\"${OPS_ADMIN_EMAIL:-ci}\"}" \
  > /dev/null
echo "  ✓ deployment ledger updated"

echo ""
echo "  ✅ POST-DEPLOY VERIFICATION PASSED"
exit 0
