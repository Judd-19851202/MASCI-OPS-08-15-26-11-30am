#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# pre_deploy_check.sh — MASCI Hub mandatory pre-deploy gate.
#
# Run this BEFORE clicking the Emergent "Deploy" button on mascidocs.com.
# It is the discipline enforcement layer that prevents shipping a build
# with a broken auth gate, broken RBAC isolation, or frontend lint failures.
#
# Exits non-zero on ANY failure. CI / human operators MUST treat non-zero
# as a hard stop — DO NOT redeploy until every stage passes.
#
# Stages:
#   0. Source-hash drift report (preview vs production · informational)
#   1. Backend syntax check (python compile)
#   2. Backend lint (ruff) — fail on errors only
#   3. Frontend lint (eslint via CRA) — fail on errors
#   4. Frontend production build smoke (CI=true)
#   5. Auth + RBAC critical-path integration tests (Phase K + iter179/180)
#   6. Full backend pytest suite
#
# Usage:
#   bash /app/scripts/pre_deploy_check.sh            # full sweep
#   bash /app/scripts/pre_deploy_check.sh --fast     # skip frontend build
#   bash /app/scripts/pre_deploy_check.sh --auth-only # only stages 1,5
# ─────────────────────────────────────────────────────────────────────────────
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

MODE="full"
for arg in "$@"; do
  case "$arg" in
    --fast) MODE="fast" ;;
    --auth-only) MODE="auth-only" ;;
    *) echo "Unknown arg: $arg" ; exit 64 ;;
  esac
done

PASS=0
FAIL=0
declare -a RESULTS

run_stage() {
  local name="$1"; shift
  echo ""
  echo "════════════════════════════════════════════════════════════════"
  echo "  STAGE: $name"
  echo "════════════════════════════════════════════════════════════════"
  if "$@"; then
    PASS=$((PASS+1))
    RESULTS+=("  ✅ $name")
  else
    FAIL=$((FAIL+1))
    RESULTS+=("  ❌ $name")
  fi
}

stage_backend_syntax() {
  python3 -m compileall -q backend/server.py backend/routes 2>&1
}

stage_backend_lint() {
  if ! command -v ruff >/dev/null 2>&1; then
    echo "ruff not installed — skipping (install: pip install ruff)"
    return 0
  fi
  # Fail only on actual errors (E9, F63, F7, F82); style warnings tolerated.
  ruff check backend/server.py backend/routes --select=E9,F63,F7,F82 --no-cache
}

# ─── Phase IV-BETA.5A-P7 · Source-hash drift report (2026-05-27) ──────
# After the 2026-05-27 post-deploy review the operator added a doctrine:
# every pre-deploy run MUST report the live preview vs. live production
# `source_hash` BEFORE the expensive stages start. This prevents the
# "we thought we deployed it" failure mode — you'll catch a stale
# production build (or an already-deployed identical build) in seconds.
#
# Always returns 0. This is a REPORT stage, not a blocker:
#   • The normal pre-deploy state IS "production behind preview". That's
#     exactly why you're running this script.
#   • Identical hashes is also a valid state ("already current").
#   • Only the network unreachable / malformed response case is worth
#     flagging — and even then, just as a soft warning. The downstream
#     identity stages do the hard env-mismatch enforcement.
#
# Configuration:
#   • Preview URL  ← REACT_APP_BACKEND_URL in frontend/.env
#   • Prod URL     ← env var PRODUCTION_URL (default: https://mascidocs.com)
stage_source_hash_drift_report() {
  local preview_url prod_url preview_hash prod_hash
  preview_url=$(grep '^REACT_APP_BACKEND_URL=' frontend/.env | cut -d= -f2 | tr -d '"' | tr -d "'")
  prod_url="${PRODUCTION_URL:-https://mascidocs.com}"

  if [[ -z "$preview_url" ]]; then
    echo "  ⚠ preview URL unavailable (REACT_APP_BACKEND_URL missing) — skipping drift report"
    return 0
  fi

  preview_hash=$(curl -fsS --max-time 8 "$preview_url/api/version" 2>/dev/null \
    | python3 -c "import sys,json;print(json.load(sys.stdin).get('source_hash','?'))" 2>/dev/null)
  prod_hash=$(curl -fsS --max-time 8 "$prod_url/api/version" 2>/dev/null \
    | python3 -c "import sys,json;print(json.load(sys.stdin).get('source_hash','?'))" 2>/dev/null)

  echo "  preview ($preview_url)"
  echo "    source_hash = ${preview_hash:-<unreachable>}"
  echo "  production ($prod_url)"
  echo "    source_hash = ${prod_hash:-<unreachable>}"

  if [[ -z "$preview_hash" || "$preview_hash" == "?" ]]; then
    echo "  ⚠ preview /api/version unreachable or missing source_hash · soft warn"
    return 0
  fi
  if [[ -z "$prod_hash" || "$prod_hash" == "?" ]]; then
    echo "  ⚠ production /api/version unreachable or missing source_hash · soft warn"
    return 0
  fi
  if [[ "$preview_hash" == "$prod_hash" ]]; then
    echo "  ✓ production already current"
    echo "    (preview_hash == prod_hash · nothing to ship · safe to skip Deploy)"
  else
    echo "  ▸ preview_hash=$preview_hash · prod_hash=$prod_hash · production behind preview"
    echo "    (expected when you are ABOUT to deploy · click Deploy to ship preview to prod)"
  fi
  return 0
}

stage_frontend_lint() {
  cd "$REPO_ROOT/frontend"
  CI=true yarn -s lint 2>/dev/null || CI=true npx -y eslint src --max-warnings=0 || return 1
}

stage_frontend_build() {
  cd "$REPO_ROOT/frontend"
  CI=true yarn -s build
}

# Auth + RBAC critical-path tests. These MUST pass on every deploy.
stage_auth_rbac_tests() {
  cd "$REPO_ROOT"
  python3 -m pytest -q --tb=short \
    backend/tests/test_admin_auth.py \
    backend/tests/test_iter126_dispatch_auth.py \
    backend/tests/test_iter155_admin_pm.py \
    backend/tests/test_iter172_phase_k1_identity_mirror.py \
    backend/tests/test_iter174_phase_k2_rbac_service.py \
    backend/tests/test_iter175_phase_k3_role_templates.py \
    backend/tests/test_iter176_login_regression.py \
    backend/tests/test_iter176_phase_k4a_directory_read.py \
    backend/tests/test_iter177_phase_k4b_directory_mutations.py \
    backend/tests/test_iter179_admin_access_control_gate.py \
    backend/tests/test_iter180_pm_token_admin_namespace_lockdown.py
}

stage_full_pytest() {
  cd "$REPO_ROOT"
  python3 -m pytest -q --tb=short backend/tests
}

# ─── Sigma-III gates (iter437) ────────────────────────────────────────
# These three stages enforce the operational-trust contract layer added
# in Phase Sigma-III. They must ALL pass before a deploy is allowed.

stage_sigma3_regression() {
  cd "$REPO_ROOT/backend"
  python3 -m pytest -q --tb=line \
    tests/regression/test_critical_flows.py \
    tests/test_iter437_magic_link_hardening.py
}

stage_sigma3_playwright() {
  cd "$REPO_ROOT/backend"
  python3 -m pytest -q --tb=line tests/pw_suite/
}

stage_sigma3_cluster_severity() {
  # Block any deploy where cluster capacity is critical. Warnings are
  # tolerated (operator's call), critical is a hard stop.
  cd "$REPO_ROOT"
  local url
  url=$(grep '^REACT_APP_BACKEND_URL=' frontend/.env | cut -d= -f2 | tr -d '"' | tr -d "'")
  if [[ -z "$url" ]]; then
    echo "REACT_APP_BACKEND_URL missing — cannot probe cluster capacity"
    return 1
  fi
  curl -fsS "$url/api/cluster/capacity" | python3 -c "
import sys, json
d = json.load(sys.stdin)
assert d.get('ok'), 'cluster capacity probe not ok'
sev = d.get('severity')
print(f'cluster severity = {sev} (usage {d.get(\"usage_mb\")}/{d.get(\"quota_mb\")} MB)')
assert sev in {'ok', 'warning'}, f'CRITICAL severity blocks deploy: {sev}'
"
}

# ─── iter437 P0-incident learning · 2026-02 ──────────────────────────
# After the production crash-loop incident (the new container refused
# to start because env vars on the production deploy could not be
# proven aligned), the operator added a doctrine: every deploy MUST
# prove env identity before AND after the deploy ships.
#
# This stage proves the PREVIEW side (the side we have access to from
# the pod). The PRODUCTION side cannot be proven from the preview pod
# until after the prod redeploy completes — it has its own dedicated
# script: `verify_production_identity.sh`.

stage_sigma3_preview_identity() {
  cd "$REPO_ROOT"
  local url
  url=$(grep '^REACT_APP_BACKEND_URL=' frontend/.env | cut -d= -f2 | tr -d '"' | tr -d "'")
  if [[ -z "$url" ]]; then
    echo "REACT_APP_BACKEND_URL missing — cannot probe preview identity"
    return 1
  fi
  bash "$REPO_ROOT/scripts/verify_env_identity.sh" \
    "$url" preview masci_safety_preview
}

# ─── iter437 P0 cleanup learning · 2026-02 ──────────────────────────
# After the production contamination cleanup, the operator demanded a
# permanent probe so the same junk can never silently re-accumulate.
# Probes the production DB (masci_safety) for the exact patterns that
# were cleaned up. Exits non-zero if any has re-appeared, blocking
# the deploy.

stage_sigma3_prod_contamination() {
  cd "$REPO_ROOT"
  python3 scripts/verify_no_contamination.py --target masci_safety
}

# ─── iter437 P0 Auth Routing — 2026-02 ───────────────────────────────
# Lightweight, fast-running guard against the regression documented in
# /app/memory/PORTAL_AUTH_TOKEN_AUDIT.md: non-Admin portals must NEVER
# leak /api/admin/* calls. Re-runs the dedicated Playwright suite that
# walks every PM sidebar entry and asserts zero admin-namespace calls.
# Cheaper than the full pw_suite/ pass — runs only the auth-routing
# tests, useful as a `--auth-only` mode pre-check.

stage_portal_auth_routing() {
  cd "$REPO_ROOT/backend"
  python3 -m pytest -q --tb=short tests/pw_suite/test_portal_token_routing.py
}

# ─── Phase IV-BETA.4 · Governance instrument wiring (2026-02-27) ──────
# Per operator directive (iter437 follow-up): first-pass governance
# scripts run as WARNING-ONLY stages. They report violations and trend
# data but DO NOT block the deploy. Only the P0 classes already
# enforced above stay deploy-blocking:
#   • admin-token leaks    → stage_portal_auth_routing
#   • preview contamination → stage_sigma3_prod_contamination
#   • env mismatch          → stage_sigma3_preview_identity
#   • broken auth routing   → stage_portal_auth_routing
#
# When a governance gate is ready to escalate to deploy-blocking, drop
# the `|| true` from its body and the stage will fail on regression.

stage_governance_coaching_sublines() {
  cd "$REPO_ROOT"
  echo "Mode: WARNING-ONLY (does not fail deploy)"
  python3 scripts/verify_coaching_sublines.py || {
    echo ""
    echo "⚠  Coaching subline drift detected — NOT blocking deploy."
    echo "   Operator: review violations above and clean up in next pass."
  }
  return 0
}

stage_governance_admin_copy() {
  cd "$REPO_ROOT"
  echo "Mode: WARNING-ONLY (does not fail deploy)"
  python3 scripts/verify_admin_copy.py || {
    echo ""
    echo "⚠  Operational verbiage drift detected — NOT blocking deploy."
    echo "   Operator: review violations above and clean up in next pass."
  }
  return 0
}

stage_governance_visual_loudness() {
  cd "$REPO_ROOT"
  echo "Mode: WARNING-ONLY (trend-recording only — does not fail deploy)"
  local url
  url=$(grep '^REACT_APP_BACKEND_URL=' frontend/.env | cut -d= -f2 | tr -d '"' | tr -d "'")
  if [[ -z "$url" ]]; then
    echo "REACT_APP_BACKEND_URL missing — skipping loudness measurement"
    return 0
  fi
  # Iteration label = short git SHA (stable per deploy)
  local iter
  iter=$(git -C "$REPO_ROOT" rev-parse --short HEAD 2>/dev/null || echo "unknown")
  python3 scripts/measure_visual_loudness.py \
    --base-url "$url" \
    --routes /admin /pm /pm/jobs /hr /hr/time-verification?hrSidebarV2=1 \
    --iteration "deploy-$iter" || {
    echo ""
    echo "⚠  Visual loudness measurement reported issues — NOT blocking deploy."
    echo "   Operator: review /app/memory/LOUDNESS_TRENDLINE.json for trend."
  }
  return 0
}

# iter437 IV-BETA.4A · doctrine baseline drift intelligence — warning-only.
stage_governance_doctrine_drift() {
  cd "$REPO_ROOT"
  echo "Mode: WARNING-ONLY (operator-readable drift summary — does not fail deploy)"
  python3 scripts/diff_doctrine_baseline.py || true
  return 0
}

# iter437 IV-BETA.5A-P1D · governance maturity aggregates — warning-only.
stage_governance_doctrine_maturity() {
  cd "$REPO_ROOT"
  echo "Mode: WARNING-ONLY (calmness ranking + hierarchy consistency + escalation noise)"
  python3 scripts/diff_doctrine_baseline.py --summary || true
  return 0
}

# ─── TRUST-1 Wave 1 · TF-018 · 2026-05-27 ─────────────────────────────
# Visibility-of-visibility gate. The /api/draft-telemetry layer exists
# specifically so field-incident failures stay diagnosable. If a future
# deploy drops that route (config drift, router-build regression), the
# platform still LOOKS healthy — pill stays green, autosave still
# writes locally — but the observability surface is silently dead.
# This stage hits the public health endpoint and asserts a 200 + ok=true.
# Hard-blocks the deploy on regression. Cheap (<1s) and idempotent.
stage_trust1_draft_telemetry_health() {
  cd "$REPO_ROOT"
  local url
  url=$(grep '^REACT_APP_BACKEND_URL=' frontend/.env | cut -d= -f2 | tr -d '"' | tr -d "'")
  if [[ -z "$url" ]]; then
    echo "REACT_APP_BACKEND_URL missing — cannot probe draft-telemetry health"
    return 1
  fi
  local admin_pw
  admin_pw=$(grep '^ADMIN_PASSWORD=' backend/.env | cut -d= -f2 | tr -d '"' | tr -d "'")
  if [[ -z "$admin_pw" ]]; then
    echo "ADMIN_PASSWORD missing — cannot acquire admin token for health probe"
    return 1
  fi
  local tok
  tok=$(curl -fsS --max-time 8 -X POST "$url/api/admin/login" \
    -H "Content-Type: application/json" \
    -d "{\"password\":\"$admin_pw\"}" 2>/dev/null \
    | python3 -c "import sys,json;print(json.load(sys.stdin).get('token',''))" 2>/dev/null)
  if [[ -z "$tok" ]]; then
    echo "admin login failed — could not acquire token for draft-telemetry health probe"
    return 1
  fi
  curl -fsS --max-time 8 "$url/api/draft-telemetry/health" \
    -H "X-Admin-Token: $tok" \
    | python3 -c "
import sys, json
d = json.load(sys.stdin)
assert d.get('ok') is True, f'draft-telemetry health not ok: {d}'
assert 'recent_events_60s' in d, f'health response missing recent_events_60s: {d}'
print(f'  ✓ draft-telemetry route live · recent_events_60s={d[\"recent_events_60s\"]}')
"
}

echo "MASCI Hub Pre-Deploy Gate — mode: $MODE"
echo "Repo: $REPO_ROOT"

# IV-BETA.5A-P7 · early visibility · "did we already deploy this?" check
run_stage "Source-hash drift report (preview vs production · informational)" stage_source_hash_drift_report

run_stage "Backend syntax compile" stage_backend_syntax
run_stage "Backend lint (ruff errors)" stage_backend_lint

if [[ "$MODE" != "auth-only" ]]; then
  run_stage "Frontend lint" stage_frontend_lint
  if [[ "$MODE" != "fast" ]]; then
    run_stage "Frontend production build" stage_frontend_build
  fi
fi

run_stage "Auth + RBAC critical tests" stage_auth_rbac_tests
run_stage "Portal auth-routing (iter437 P0 · /api/admin/* leak guard)" stage_portal_auth_routing
# Governance instruments (Phase IV-BETA.4) — warning-only first pass.
run_stage "Governance · coaching sublines (warning-only)" stage_governance_coaching_sublines
run_stage "Governance · admin copy doctrine (warning-only)" stage_governance_admin_copy
# Visual loudness needs Playwright + a live preview URL; skip in auth-only mode
if [[ "$MODE" != "auth-only" ]]; then
  run_stage "Governance · visual loudness trend (warning-only)" stage_governance_visual_loudness
fi
run_stage "Governance · doctrine baseline drift (warning-only)" stage_governance_doctrine_drift
run_stage "Governance · doctrine maturity aggregates (warning-only)" stage_governance_doctrine_maturity

# Sigma-III enforceable gates — run on every mode (these are the
# minimum operational-trust contract the platform now ships under).
run_stage "Sigma-III preview env identity proof" stage_sigma3_preview_identity
run_stage "Sigma-III prod contamination probe" stage_sigma3_prod_contamination
run_stage "Sigma-III regression contract" stage_sigma3_regression
run_stage "Sigma-III Playwright browser suite" stage_sigma3_playwright
run_stage "Sigma-III cluster severity probe" stage_sigma3_cluster_severity
# TRUST-1 Wave 1 · TF-018 — observability route must be reachable.
run_stage "TRUST-1 · draft-telemetry route health (visibility gate)" stage_trust1_draft_telemetry_health

if [[ "$MODE" == "full" ]]; then
  run_stage "Full backend pytest suite" stage_full_pytest
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  PRE-DEPLOY GATE RESULT"
echo "════════════════════════════════════════════════════════════════"
for line in "${RESULTS[@]}"; do echo "$line"; done
echo ""
echo "  Passed: $PASS    Failed: $FAIL"

if [[ "$FAIL" -gt 0 ]]; then
  echo ""
  echo "  ❌ GATE FAILED — DO NOT DEPLOY."
  exit 1
fi

echo ""
echo "  ✅ GATE PASSED — safe to click Emergent Deploy."

# iter437 IV-BETA.5A-P5A · Auto-deploy checkpoint.
# Append a quiet `auto · deploy {sha}` checkpoint so every gate-passing
# build becomes a retrievable governance reference. Operator-blessed
# checkpoints are preserved (last-write-wins per portal); deploy
# checkpoints serve as operational breadcrumbs between them.
# Filesystem-only · no DB writes · no notifications · no UI surface.
if [[ -f "$REPO_ROOT/scripts/diff_doctrine_baseline.py" ]]; then
  DEPLOY_SHA=$(cd "$REPO_ROOT" && git rev-parse --short HEAD 2>/dev/null || echo "unknown")
  python3 "$REPO_ROOT/scripts/diff_doctrine_baseline.py" --append \
    --checkpoint "auto · deploy $DEPLOY_SHA" 2>/dev/null \
    && echo "  ✓ auto-deploy checkpoint appended (sha=$DEPLOY_SHA)" \
    || true
fi

exit 0
