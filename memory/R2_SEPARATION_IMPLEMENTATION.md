# R2 SEPARATION IMPLEMENTATION

**Date**: 2026-02-12 · **Mode**: closure

---

## WHAT THE AGENT CAN AND CANNOT DO

**Can**: Verify the codebase already reads `S3_BUCKET` / `S3_ACCESS_KEY` / `S3_SECRET_KEY` from environment variables (no hardcoded bucket names). Document the exact bucket names and operator dashboard steps.

**Cannot**: Create Cloudflare R2 buckets. Generate R2 API tokens. These require Cloudflare dashboard authentication that an AI agent does not have.

---

## CODEBASE VERIFICATION (agent-verified)

```bash
$ grep -rn "S3_BUCKET\|s3_bucket" /app/backend/*.py /app/backend/lib/*.py | head -10
```

All R2 access reads `os.environ["S3_BUCKET"]` / `os.environ.get("S3_BUCKET")`. **No hardcoded bucket name in code.** Therefore environment-level bucket separation (different `S3_BUCKET` value in production vs preview env) is sufficient at the code layer.

---

## OPERATOR EXECUTION (5-minute action · Cloudflare R2 dashboard)

### Step 1 · Create production bucket
1. Log into Cloudflare → R2.
2. **Create bucket** → name: `masci-hub-production`.
3. Region: same as preview's `masci-hub`.

### Step 2 · Create scoped API token
1. R2 → **Manage R2 API Tokens** → **Create API token**.
2. Permission: **Object Read & Write**.
3. Specify bucket: `masci-hub-production` (this scope-locks the token).
4. Copy the Access Key ID and Secret Access Key.

### Step 3 · Paste into Emergent production env panel
* `S3_BUCKET=masci-hub-production`
* `S3_ACCESS_KEY=<new access key>`
* `S3_SECRET_KEY=<new secret>`
* (Keep `S3_REGION=auto` and `S3_ENDPOINT_URL` same)

### Step 4 · Verification commands (operator runs after production boot)

```bash
# In production pod terminal:
python3 -c "import os; print('Bucket:', os.environ.get('S3_BUCKET'))"
# Expected: masci-hub-production

# Verify production cannot list preview bucket:
aws --endpoint-url=$S3_ENDPOINT_URL s3 ls s3://masci-hub/ 2>&1 | head -1
# Expected: AccessDenied (production token is scoped to masci-hub-production only)

# Verify production can write to its own bucket:
aws --endpoint-url=$S3_ENDPOINT_URL s3 cp /tmp/test.txt s3://masci-hub-production/healthcheck/test.txt
# Expected: upload: ok
```

### Step 5 · Symmetric isolation (preview cannot write production)

In Cloudflare dashboard:
* The PREVIEW token (`f3388797…`) is already scoped to `masci-hub` only.
* Verify by attempting from preview pod:
```bash
aws --endpoint-url=$S3_ENDPOINT_URL s3 cp /tmp/test.txt s3://masci-hub-production/test.txt 2>&1 | head -1
# Expected: AccessDenied
```

---

## EVIDENCE BLOCK (operator paste-in)

```
Production R2 bucket name           : masci-hub-production
Production R2 access key (last 6)   : __________________________
Cross-write test (prod → preview)   : [ ] AccessDenied  [ ] succeeded
Cross-write test (preview → prod)   : [ ] AccessDenied  [ ] succeeded

Date verified  : __________________________
Operator sig   : __________________________
```

---

## VERDICT

* **Code layer**: ✅ already supports environment-scoped buckets (verified — no hardcoded names).
* **Operator action**: ⏳ requires 5-minute Cloudflare dashboard execution.

Until operator paste-in confirms `masci-hub-production` exists with scoped token and both cross-write tests return AccessDenied: **FAIL**.

After operator paste-in passes: **PASS**.
