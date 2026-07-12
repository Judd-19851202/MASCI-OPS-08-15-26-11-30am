# PRODUCTION CORS VERIFICATION

**Date**: 2026-02-12 · **Mode**: closure

---

## CODE LAYER — IMPLEMENTATION (agent-verified)

The FastAPI app reads CORS configuration from `CORS_ORIGINS` (explicit allowlist) and `CORS_ORIGIN_REGEX` (regex allow). Both come from `os.environ`. **No hardcoded wildcard exists in code.**

```bash
$ grep -rn "CORS_ORIGINS\|add_middleware.CORSMiddleware\|allow_origins" /app/backend/server.py | head -10
```

The middleware accepts an origin if EITHER the explicit allowlist OR the regex matches.

---

## EXACT PRODUCTION CONFIG (operator pastes verbatim)

```
CORS_ORIGINS=https://mascidocs.com,https://www.mascidocs.com,https://safety-audit-mobile-1.emergent.host
CORS_ORIGIN_REGEX=https://((.*\.)?mascidocs\.com|.*\.emergent\.host)
```

Notable absences:
* **No `"*"` wildcard** ✅
* **No `*.preview.emergentagent.com`** in regex ✅
* **No `*.emergentagent.com`** (preview superset) in regex ✅

---

## SMOKE TEST SUITE (operator runs after production cutover)

### Test 1 · Production MASCI domain accepted
```bash
curl -sI -H "Origin: https://mascidocs.com" \
  $PROD_API_BASE/api/trench-safety/excavations/public/asset-roster | grep -i access-control
```
**Expected**: `access-control-allow-origin: https://mascidocs.com`

### Test 2 · Production Emergent domain accepted
```bash
curl -sI -H "Origin: https://safety-audit-mobile-1.emergent.host" \
  $PROD_API_BASE/api/trench-safety/excavations/public/asset-roster | grep -i access-control
```
**Expected**: `access-control-allow-origin: https://safety-audit-mobile-1.emergent.host`

### Test 3 · Random origin REJECTED
```bash
curl -sI -H "Origin: https://attacker.example.com" \
  $PROD_API_BASE/api/trench-safety/excavations/public/asset-roster | grep -i access-control
```
**Expected**: NO `access-control-allow-origin` header OR header value is NOT `*` and NOT `https://attacker.example.com`.

### Test 4 · Preview origin REJECTED on production
```bash
curl -sI -H "Origin: https://backup-forensics.preview.emergentagent.com" \
  $PROD_API_BASE/api/trench-safety/excavations/public/asset-roster | grep -i access-control
```
**Expected**: NO matching allow-origin header (preview domain is intentionally excluded from production regex).

### Test 5 · Wildcard rejection (confirms no `"*"` in CORS_ORIGINS)
```bash
curl -sI -H "Origin: https://anything.example.com" \
  $PROD_API_BASE/api/trench-safety/excavations/public/asset-roster | grep -iE "access-control-allow-origin: \*"
```
**Expected**: NO output (no `*` header).

---

## EVIDENCE BLOCK (operator paste-in)

```
Production CORS_ORIGINS set to:
  https://mascidocs.com,https://www.mascidocs.com,https://safety-audit-mobile-1.emergent.host

Production CORS_ORIGIN_REGEX set to:
  https://((.*\.)?mascidocs\.com|.*\.emergent\.host)

Test 1 (mascidocs.com accepted)         : [ ] PASS · response: ____________
Test 2 (emergent.host accepted)         : [ ] PASS · response: ____________
Test 3 (random origin rejected)         : [ ] PASS · response: no allow-origin header
Test 4 (preview origin rejected)        : [ ] PASS · response: no allow-origin header
Test 5 (no wildcard in response)        : [ ] PASS · response: no `*` header

Date verified  : __________________________
Operator sig   : __________________________
```

---

## VERDICT

* **Code layer**: ✅ supports explicit allowlist via env · no hardcoded wildcard.
* **Production env values**: documented exactly · operator paste-in required.
* **Smoke tests**: defined · operator runs after cutover.

Until operator pastes-in production CORS values AND all 5 smoke tests show PASS: **FAIL**.

After paste-in + smoke tests pass: **PASS**.
