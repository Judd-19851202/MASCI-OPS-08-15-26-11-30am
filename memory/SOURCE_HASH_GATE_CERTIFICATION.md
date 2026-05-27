# Source-Hash Gate · Certification
## iter437 · Phase IV-BETA.5A-P7 · 2026-05-27

> Adds the early "did we already deploy this?" visibility check to
> `pre_deploy_check.sh`. Informational (non-blocking). Doctrine-locked.

---

## 1 · Purpose

Prevent the **"we thought we deployed it"** failure mode. After the
2026-05-27 post-deploy review (`POST_DEPLOY_LIVE_CERTIFICATION.md`),
the operator surfaced a recurring risk: a future change might pass
every regression gate locally, but a Save-to-Github / Deploy step is
quietly skipped — leaving production behind preview. The first sign of
trouble would be a test failure on production days later.

This gate flips that asymmetry. **Before** the expensive validation
stages run, you see the two live hashes side-by-side with a
human-readable verdict.

---

## 2 · What the Gate Does

The new stage `stage_source_hash_drift_report` runs as the **first**
stage in `pre_deploy_check.sh`. It:

1. Reads the preview URL from `frontend/.env` (`REACT_APP_BACKEND_URL`).
2. Reads the production URL from `PRODUCTION_URL` env var (default:
   `https://mascidocs.com`).
3. Fetches `/api/version` from each.
4. Extracts `source_hash`.
5. Prints both hashes and a verdict.

### Sample output

```
════════════════════════════════════════════════════════════════
  STAGE: Source-hash drift report (preview vs production · informational)
════════════════════════════════════════════════════════════════
  preview (https://safety-audit-mobile-1.preview.emergentagent.com)
    source_hash = 0f5d997dffba4e95fefa9a58c7f02780
  production (https://mascidocs.com)
    source_hash = 0f5d997dffba4e95fefa9a58c7f02780
  ✓ production already current
    (preview_hash == prod_hash · nothing to ship · safe to skip Deploy)
```

---

## 3 · Three Branches · Three Verdicts

| Condition | Verdict line | Operator inference |
|---|---|---|
| `preview_hash == prod_hash` | `✓ production already current` | No new commits to ship · skip Deploy · pre-deploy gate continues |
| `preview_hash != prod_hash` | `▸ preview_hash=<a> · prod_hash=<b> · production behind preview` | This is the **expected pre-deploy state** · run Deploy after gate passes |
| preview unreachable / no source_hash | `⚠ preview /api/version unreachable or missing source_hash · soft warn` | Likely pod / network issue · investigate before deploying |
| production unreachable / no source_hash | `⚠ production /api/version unreachable or missing source_hash · soft warn` | Likely DNS / CDN issue · investigate before deploying |

---

## 4 · Doctrine Decisions

### 4.1 — Why informational (non-blocking)

This gate **never fails** the script. Reasons:

- The normal pre-deploy state IS "production behind preview". A blocker
  on that condition would prevent every legitimate deploy.
- Identical hashes is also a valid state (safe to skip Deploy · gate continues).
- Network blips are operationally common; the downstream identity
  stages (Sigma-III preview identity proof + post-deploy
  `verify_production_identity.sh`) do the hard env-mismatch
  enforcement. This gate's job is **visibility**, not enforcement.

### 4.2 — Why FIRST stage

Placing the report at position 0 means the operator sees the hash
delta **before** committing to a 10-15 minute test run. Catches the
"production already current" case in 2 seconds, not 15 minutes.

### 4.3 — Why no destructive action

The stage:
- ❌ Does NOT touch any database.
- ❌ Does NOT modify auth or session state.
- ❌ Does NOT change portal logic.
- ❌ Does NOT mutate any environment variable.
- ❌ Does NOT trigger a deploy (operator-owned platform action).
- ✅ ONLY reads two `/api/version` payloads via HTTPS.

---

## 5 · Configuration

| Knob | Where | Default |
|---|---|---|
| Preview URL | `frontend/.env` · `REACT_APP_BACKEND_URL` | inherited from existing platform doctrine |
| Production URL | env var `PRODUCTION_URL` | `https://mascidocs.com` |
| HTTP timeout | hard-coded in stage | 8 seconds per fetch |

Override example (one-shot · for a staging-style preview that targets
a different prod URL):
```
PRODUCTION_URL=https://staging.mascidocs.com bash scripts/pre_deploy_check.sh
```

---

## 6 · Tests

A dedicated test script proves all three branches behave as documented:

`/app/scripts/test_source_hash_gate.sh`

Run:
```
bash /app/scripts/test_source_hash_gate.sh
```

### 6.1 — Test methodology

- Spins up two ephemeral python `http.server` fixtures on `127.0.0.1`
  with auto-assigned ports.
- Each fixture returns a controlled `source_hash` on `/api/version`.
- Invokes the stage function in isolation against the fixtures.
- Asserts the expected text patterns appear in the output.

### 6.2 — Test results (live)

```
════════════════════════════════════════════════════════════════
  source-hash gate · branch test (IV-BETA.5A-P7)
════════════════════════════════════════════════════════════════

── Branch 1: preview_hash == prod_hash ─────────
  ✓ reports preview hash
  ✓ reports prod hash equal
  ✓ reports 'already current'

── Branch 2: preview_hash != prod_hash ─────────
  ✓ reports preview hash
  ✓ reports prod hash different
  ✓ reports 'production behind preview'
  ✓ reports both hashes inline

── Branch 3: production unreachable ─────────
  ✓ preview ok
  ✓ prod marked <unreachable>
  ✓ soft warn surfaced

════════════════════════════════════════════════════════════════
  Passed: 10    Failed: 0
  ✓ source-hash gate · all 3 branches behave as documented
```

### 6.3 — Live in-stage proof (against real preview + production)

```
════════════════════════════════════════════════════════════════
  STAGE: Source-hash drift report (preview vs production · informational)
════════════════════════════════════════════════════════════════
  preview (https://safety-audit-mobile-1.preview.emergentagent.com)
    source_hash = 0f5d997dffba4e95fefa9a58c7f02780
  production (https://mascidocs.com)
    source_hash = 0f5d997dffba4e95fefa9a58c7f02780
  ✓ production already current
    (preview_hash == prod_hash · nothing to ship · safe to skip Deploy)
```

---

## 7 · Shell Syntax Validation

```
$ bash -n /app/scripts/pre_deploy_check.sh
$ echo $?
0
```

🟢 `bash -n` exits cleanly · script parses without syntax errors.

---

## 8 · Change Summary

| File | Change |
|---|---|
| `scripts/pre_deploy_check.sh` | Added `stage_source_hash_drift_report` function · wired as first stage · updated header docstring |
| `scripts/test_source_hash_gate.sh` | NEW · 10-assertion branch test using ephemeral http.server fixtures |
| `memory/SOURCE_HASH_GATE_CERTIFICATION.md` | NEW · this document |

No other file modified. No backend code touched. No database touched.
No auth touched. No portal logic touched.

---

## 9 · Stop Condition

🟢 **Source-hash drift gate complete. E1 stops here.**

The operator's standing directive is unchanged:

> "After this is done and green, we can start V.1 with a clean platform
> baseline."

V.1 (RFI MVP build) begins **only** on an explicit operator command in
a fresh message.

---

## 10 · Sign-off

- **Author:** E1 · iter437 IV-BETA.5A-P7
- **Status:** 🟢 Doctrine-grade · live + synthetic both green
- **Production deploy:** None this pass · preview-only file changes
- **Next gate:** Operator-issued "start V.1" command
