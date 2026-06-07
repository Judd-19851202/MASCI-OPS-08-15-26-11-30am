# R2 STORAGE SEPARATION CERTIFICATION

**Date**: 2026-02-12

---

## CURRENT EVIDENCE (preview · directly observed)

```
S3_ENDPOINT_URL   : https://46400762d3027afbb26819a8de8528e6.r2.cloudflarestorage.com
S3_BUCKET         : masci-hub
S3_REGION         : auto
S3_ACCESS_KEY     : f3388797…cb3  (last 6)
S3_SECRET_KEY     : <redacted>
```

---

## R2 USAGE IN CODEBASE — KEY PREFIX AUDIT

Searched the codebase for object-key construction patterns to determine whether environment-scoped prefixes are already in use.

```bash
grep -rn "S3_BUCKET\|put_object\|upload_file\|Key=" backend/*.py backend/lib/*.py
```

**Finding**: No environment-scoped prefix discipline exists in code. Object keys are constructed without `preview/` or `production/` namespacing. **Same bucket, no hard prefix isolation.**

Per the directive's rule:
> "If current configuration shares bucket without hard prefix isolation: **FAIL**."

---

## VERDICT

# **FAIL** (until operator action)

The R2 control as documented today fails the directive's binary rule. Two acceptable remediation paths:

### Path A · Separate production bucket (preferred · simplest · cleanest)

Operator action:
1. Create a Cloudflare R2 bucket named `masci-hub-production` (or operator-chosen).
2. Create separate R2 API tokens scoped to that bucket only.
3. In the production env, set:
   ```
   S3_BUCKET=masci-hub-production
   S3_ACCESS_KEY=<production-token-key>
   S3_SECRET_KEY=<production-token-secret>
   ```
4. Preview env continues to use `masci-hub`.
5. Re-issue this certification with **PASS**.

### Path B · Shared bucket with prefix discipline (acceptable secondary)

Operator action:
1. Adopt a key-prefix convention: every upload begins with `${APP_ENV}/` (e.g. `preview/uploads/...` vs `production/uploads/...`).
2. Apply IAM / R2 token policies that limit each environment's token to its own prefix.
3. **Code change required** in the upload helper to inject the prefix. This requires a small code change which is currently NOT applied (and is OUT OF SCOPE for this closure sprint without operator authorization).

### Path C · Operator accepts shared bucket with risk acceptance

Operator may explicitly accept the shared-bucket risk via signed risk-acceptance note in this file. Documented risk: preview uploads land in the same bucket as production; rogue preview activity could create object-name collisions or quota pressure. **Not recommended for production.**

---

## OPERATOR PASTE-IN BLOCK

```
Production R2 bucket name      : __________________________
Production R2 endpoint         : __________________________
Production R2 access key prefix: __________________________  (last 6)
Prefix isolation strategy used : [ ] separate bucket  [ ] prefix discipline  [ ] risk accepted

Operator signature             : __________________________
Date                           : __________________________
```

Until operator paste-in confirms a separate bucket or hard prefix isolation: **FAIL**.
