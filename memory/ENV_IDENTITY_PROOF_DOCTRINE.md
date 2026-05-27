# Environment Identity Proof — Doctrine + Tooling

**Phase:** SIGMA-III · P0 incident learning
**Iteration:** iter437 · 2026-02 (post-prod-crashloop)
**Status:** 🟢 DOCTRINE ENFORCED · TOOLING SHIPPED

---

## The doctrine (operator-issued · 2026-02)

> Before any future deploy, **production must prove**:
> &nbsp;&nbsp;&nbsp;`APP_ENV=production`
> &nbsp;&nbsp;&nbsp;`DB_NAME=masci_safety`
>
> **Preview must prove**:
> &nbsp;&nbsp;&nbsp;`APP_ENV=preview`
> &nbsp;&nbsp;&nbsp;`DB_NAME=masci_safety_preview`

This is non-negotiable. It is now enforced at three layers of the stack.

---

## Why this doctrine was added

On 2026-02 the production deploy entered a hard crash-loop for ~25 minutes:

- Pre-incident state: production was on a build that predated iter437 Phase Sigma-II, so `/api/version` did not expose `app_env` / `db_name` fields. Mongo connectivity was already broken from that build (30 s server-selection timeouts → 500s).
- Operator triggered a redeploy to ship Sigma-II + Sigma-III work.
- The new container was unable to come up. Cloudflare returned 520 across every path including `/api/health`.
- **Root cause was unknowable from outside the cluster.** The pre-deploy gate had verified preview was fine, but there was no way to prove what env vars the production container had been handed.
- 8+ minutes of forensic guessing were spent before the operator pulled startup logs from the Emergent dashboard.

The post-mortem doctrine: **identity must be provable from a single HTTP probe, both before AND after every deploy, on both environments.**

---

## Three-layer enforcement

### Layer 1 · Runtime (`server.py:_verify_env_db_alignment`)
Already shipped in iter437 Phase Sigma-II. The container REFUSES to start if `APP_ENV` and `DB_NAME` are misaligned (e.g. `APP_ENV=production` paired with `DB_NAME=masci_safety_preview`). Raises `RuntimeError` at module load time.

### Layer 2 · Pre-deploy gate (`/app/scripts/pre_deploy_check.sh`)
New stage added in this iteration:

```
STAGE: Sigma-III preview env identity proof
   url        : https://safety-audit-mobile-1.preview.emergentagent.com
   app_env    : preview
   db_name    : masci_safety_preview
   source_hash: 45e66bd7a89e16894ba55dff064ce456
✅ IDENTITY MATCH
```

The pre-deploy gate now refuses to pass if preview is currently running with the wrong env identity. Operator cannot click Deploy until preview proves itself.

### Layer 3 · Post-deploy gate (`/app/scripts/verify_production_identity.sh`)
New script. Operator runs this IMMEDIATELY after every production redeploy. It polls `https://mascidocs.com/api/version` for up to 5 minutes, refuses to declare success until:

- The container is reachable (no 520)
- `source_hash` differs from the previous build (if previous hash supplied as `$1`)
- `app_env == production` AND `db_name == masci_safety`

Exit codes are meaningful:
- `0` — production came up healthy with correct identity
- `1` — production came up with WRONG identity → rollback required
- `2` — production never came up within timeout → crash-loop, check logs

---

## How to use (operator runbook)

### Before any deploy
```bash
bash /app/scripts/pre_deploy_check.sh
# Expected last line: "✅ GATE PASSED — safe to click Emergent Deploy."
```

If the new "Sigma-III preview env identity proof" stage fails, **stop**. The preview pod is misconfigured — fix preview's env vars first.

### After triggering a production redeploy
```bash
# Capture the OLD source hash so we know when the new build is up
OLD=$(curl -s https://mascidocs.com/api/version | python3 -c "import sys,json;print(json.load(sys.stdin).get('source_hash',''))")
echo "Pre-deploy hash: $OLD"

# Click Deploy in Emergent dashboard. Then:
bash /app/scripts/verify_production_identity.sh "$OLD"
```

Three outcomes:

1. **`✅ PRODUCTION IDENTITY VERIFIED`** — safe to direct user traffic. Run the standard 7-portal post-deploy smoke and you're done.
2. **`❌ PRODUCTION IDENTITY MISMATCH`** — the new build came up but with wrong env vars. **Do NOT send user traffic.** Fix the env var in Emergent deploy dashboard, redeploy, re-run this script.
3. **`❌ TIMEOUT after 300s`** — the new build never came up. Either crash-looping (check Emergent logs for the `MASCI-HUB ENVIRONMENT SAFETY CHECK` banner) or stuck on Cloudflare. If crash-loop, fix env vars + redeploy. If Cloudflare, contact Emergent Support.

### Spot-check at any time (no deploy in flight)
```bash
# Preview
/app/scripts/verify_env_identity.sh https://safety-audit-mobile-1.preview.emergentagent.com preview masci_safety_preview

# Production
/app/scripts/verify_env_identity.sh https://mascidocs.com production masci_safety
```

Returns 0 on match, 1 on mismatch with a clear diff.

---

## Live verification (2026-02 incident close-out)

After the incident was resolved, the doctrine was tested end-to-end:

```
$ /app/scripts/verify_env_identity.sh https://mascidocs.com production masci_safety
✅ IDENTITY MATCH
   url        : https://mascidocs.com
   app_env    : production
   db_name    : masci_safety
   source_hash: 45e66bd7a89e16894ba55dff064ce456
   uptime_s   : 375

$ bash /app/scripts/pre_deploy_check.sh --auth-only
✅ GATE PASSED — safe to click Emergent Deploy.
   (7/7 stages green · including Sigma-III preview env identity proof)
```

Same image on both environments (`45e66bd…`). Different env identity per environment. Doctrine satisfied.

---

## Files

### New
- `/app/scripts/verify_env_identity.sh` — generic verifier (URL + expected env + expected DB)
- `/app/scripts/verify_production_identity.sh` — production-specific polling verifier (post-deploy)
- `/app/memory/ENV_IDENTITY_PROOF_DOCTRINE.md` — this document

### Modified
- `/app/scripts/pre_deploy_check.sh` — added "Sigma-III preview env identity proof" stage

### Pre-existing (unchanged)
- `/app/backend/server.py:_verify_env_db_alignment` — startup-time runtime guard (Layer 1)

---

## What this incident proved

| Failure mode | Detection layer |
|---|---|
| Wrong env vars on preview | Layer 2 (pre-deploy gate) catches before any code ships |
| Wrong env vars on production at startup | Layer 1 (runtime guard) refuses to start the container |
| Wrong env vars on production but container started anyway | Layer 3 (post-deploy verifier) catches via HTTP probe within 5 minutes |
| Stale build still running with mongo broken | Layer 3 detects via source_hash mismatch |
| Container crash-loop blocking all traffic | Layer 3 reports timeout → operator pulls Emergent logs |

No single layer is sufficient. Together they form a tight contract: **the operator can never again be in the position of guessing what env vars production is running.**

---

# 🟢 ENV IDENTITY PROOF · DOCTRINE LOCKED · TOOLING SHIPPED
