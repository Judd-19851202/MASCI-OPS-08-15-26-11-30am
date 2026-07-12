# PRODUCTION CORS LOCKDOWN CERTIFICATION

**Date**: 2026-02-12

---

## EVIDENCE — CURRENT PREVIEW VALUES

```
/app/backend/.env (line 4) : CORS_ORIGINS="*"
/app/backend/.env (line 5) : CORS_ORIGIN_REGEX=https://((.*\.)?mascidocs\.com|.*\.(preview\.emergentagent\.com|emergent\.host|emergentagent\.com))
```

`"*"` wildcard is **acceptable for preview only** per the directive.

---

## REQUIRED PRODUCTION VALUES

```
CORS_ORIGINS="https://mascidocs.com,https://www.mascidocs.com,https://safety-audit-mobile-1.emergent.host"
CORS_ORIGIN_REGEX=https://((.*\.)?mascidocs\.com|.*\.emergent\.host)
```

**No wildcard.** **No preview domain.** **Explicit MASCI + Emergent production hosts only.**

---

## EVIDENCE — PRODUCTION (operator-managed)

Operator must set the production env in the Emergent deployment dashboard. Operator paste-in:

```
PRODUCTION CORS_ORIGINS       : __________________________
PRODUCTION CORS_ORIGIN_REGEX  : __________________________

After flip, operator verifies cross-origin request from:
  https://mascidocs.com           → 200 ✓
  https://www.mascidocs.com        → 200 ✓
  https://*.emergent.host          → 200 ✓
  https://backup-forensics.preview.emergentagent.com → CORS error ✗  (must be blocked from production)
  https://random.example.com       → CORS error ✗
```

---

## PASS RULES

| Rule | Pass condition |
|---|---|
| No wildcard | `CORS_ORIGINS` does NOT contain `"*"` |
| MASCI domain allowed | `CORS_ORIGINS` includes `https://mascidocs.com` AND `https://www.mascidocs.com` |
| Production Emergent domain allowed | `CORS_ORIGINS` includes the production hostname (typically `https://<app>.emergent.host`) |
| Preview domain NOT allowed | `CORS_ORIGINS` does NOT include any `*.preview.emergentagent.com` host |
| Cross-origin smoke test | `curl -H "Origin: https://random.example.com" -I <prod-api>/api/health` returns no `Access-Control-Allow-Origin: *` header |

---

## VERDICT

# **OPERATOR-PENDING** → defaults to FAIL until operator sets production CORS_ORIGINS to the explicit allowlist.

Operator paste-in block:

```
PRODUCTION CORS_ORIGINS set to     : __________________________
Smoke test cross-origin rejected   : [ ] yes / [ ] no
Smoke test MASCI domain accepted   : [ ] yes / [ ] no

Operator signature : __________________________
Date               : __________________________
```

Until paste-in: **FAIL**.
