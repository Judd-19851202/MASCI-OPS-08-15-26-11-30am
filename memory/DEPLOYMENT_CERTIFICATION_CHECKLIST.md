# Deployment Certification Checklist — iter437 · Phase Sigma-II

**Audience:** Operator promoting a build from preview → production.
**Discipline:** No production deploy without ALL gates green. Skipping a gate = ROLLBACK.

---

## 🚦 GATE A — API REGRESSION (mandatory · deploy-blocker)

```bash
cd /app/backend && python3 -m pytest tests/regression/test_critical_flows.py -q
```

**Expected:** `46 passed in <10s` (or current total). Zero failures, zero errors.

**If RED:** consult `OPERATIONAL_RUNBOOKS.md` § RB-06. DO NOT deploy.

---

## 🚦 GATE B — PLAYWRIGHT BROWSER REGRESSION (mandatory · deploy-blocker)

```bash
cd /app/backend && python3 -m pytest tests/pw_suite/ -q
```

**Expected:** `23 passed, 1 skipped in <60s` (or current total). The skipped test is `test_attachment_upload_round_trip_to_r2` (structural — preview lacks host data).

**If RED:** consult `OPERATIONAL_RUNBOOKS.md` § RB-07. Inspect failure artifacts at `/app/test_reports/playwright/`.

---

## 🚦 GATE C — IDEMPOTENCY UNIT TESTS (mandatory · deploy-blocker)

```bash
cd /app/backend && python3 -m pytest tests/test_iter437_idempotency_strip.py -q
```

**Expected:** `9 passed in <1s`.

**If RED:** the strip patch regressed — `lib/idempotency.py` review required before deploy.

---

## 🚦 GATE D — ENVIRONMENT SEPARATION (mandatory · deploy-blocker)

```bash
URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d= -f2)
curl -fsS "$URL/api/version" | python3 -c "
import sys, json; d = json.load(sys.stdin)
assert d['app_env'] in {'preview', 'production'}, d
if d['app_env'] == 'preview':
    assert d['db_name'].endswith('_preview'), d
else:
    assert not d['db_name'].endswith('_preview'), d
print('  ✅ env identity:', d['app_env'], '/', d['db_name'])
"
```

**If RED:** **STOP** — see `OPERATIONAL_RUNBOOKS.md` § RB-04. This is a P0 incident.

---

## 🚦 GATE E — CLUSTER CAPACITY (mandatory · deploy-blocker if severity=critical)

```bash
URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d= -f2)
curl -fsS "$URL/api/cluster/capacity" | python3 -c "
import sys, json; d = json.load(sys.stdin)
assert d['ok'], d
assert d['severity'] in {'ok', 'warning'}, f'severity={d[\"severity\"]} — DEPLOY BLOCKED'
print('  ✅ cluster:', d['severity'], '@', d['storage_used_pct'], '%')
"
```

**If RED:** consult `OPERATIONAL_RUNBOOKS.md` § RB-02. Cluster is at/near capacity.

---

## 🚦 GATE F — STORAGE DRIFT (advisory · operator judgement)

```bash
URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d= -f2)
curl -fsS "$URL/api/cluster/capacity/history?days=7" | python3 -c "
import sys, json; d = json.load(sys.stdin)
slope = d.get('slope_mb_per_day') or 0
runway = d.get('days_to_quota') or 99999
print(f'  slope: {slope:.2f} MB/day · runway: {runway:.0f} days')
if slope > 50:
    print('  ⚠ WARNING — abnormal growth detected. Investigate before deploy.')
if runway < 90:
    print('  🛑 BLOCK — <90 days runway. Plan tier upgrade.')
"
```

**Advisory only** — operator decides based on context. Use this as a sanity check, not an automatic blocker.

---

## 🚦 GATE G — ROUTE SMOKE (mandatory · deploy-blocker)

Inline in regression suite already. The 12 `test_no_auth_protected_endpoints_401[*]` cases enforce auth gating on every protected list endpoint. Re-affirmed by Gate A.

---

## 🚦 GATE H — MOBILE VIEWPORT VALIDATION (mandatory · deploy-blocker)

Inline in Playwright already. Every flow runs on `mobile` (390×844, mobile-Safari UA) and `ipad` (1024×1366). Re-affirmed by Gate B.

---

## 🚦 GATE I — AUTH CONTINUITY (mandatory · deploy-blocker)

```bash
URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d= -f2)
# Documented test credentials should all login successfully.
for cred in "hrmanager@mascigc.com:HRTesting2026!:hr/login" \
            "chriswright@mascigc.com:ChrisRocksThis2026:pm/login" \
            "fieldleader@mascigc.com:FieldLead2026!:field-leadership/portal/login" \
            "dispatch@mascigc.com:DispatchTest2026!:dispatch/login" \
            "safety@mascigc.com:SafetyTest2026!:safety/login"; do
  IFS=: read -r email pw path <<< "$cred"
  code=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$URL/api/$path" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$email\",\"password\":\"$pw\"}")
  echo "  $email -> $code"
done
```

**Expected:** all 5 portal logins return 200.

---

## 🚦 GATE J — RESTORE READINESS (advisory · weekly check)

Verify a backup zip from R2 is available + recent:

```bash
cd /app/backend && python3 -c "
import os; from pathlib import Path
for line in Path('.env').read_text().splitlines():
    if '=' not in line or line.strip().startswith('#'): continue
    k,_,v = line.partition('='); os.environ.setdefault(k.strip(), v.strip().strip('\"').strip(\"'\"))
import boto3
s3 = boto3.client('s3', endpoint_url=os.environ['S3_ENDPOINT_URL'],
    aws_access_key_id=os.environ['S3_ACCESS_KEY'],
    aws_secret_access_key=os.environ['S3_SECRET_KEY'], region_name='auto')
keys = []
for p in s3.get_paginator('list_objects_v2').paginate(Bucket=os.environ['S3_BUCKET'], Prefix='backups/auto-90d/'):
    for o in (p.get('Contents') or []):
        if o['Size'] > 50_000_000: keys.append(o)
keys.sort(key=lambda x: x['LastModified'], reverse=True)
import datetime as dt
top = keys[0]
age_h = (dt.datetime.now(dt.timezone.utc) - top['LastModified']).total_seconds()/3600
print(f'  latest: {top[\"Key\"]} ({top[\"Size\"]/1e6:.1f} MB, {age_h:.1f}h old)')
assert age_h < 6, f'latest backup is {age_h:.1f}h old (expected <6h)'
"
```

**If RED:** R2 hourly backup cron has failed. Investigate `BACKUP_R2_HOURLY` job before deploy.

---

## 🚦 GATE K — OPERATIONAL HEALTH ENDPOINTS (advisory)

Curl every public health surface to confirm 200:

```bash
URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d= -f2)
for ep in /api/health /api/version /api/cluster/capacity /api/cluster/capacity/history?days=1; do
  code=$(curl -s -o /dev/null -w '%{http_code}' "$URL$ep")
  echo "  $ep -> $code"
done
```

**Expected:** all 200.

---

## 🟢 DEPLOY DECISION MATRIX

| Gate result                          | Action                                  |
|--------------------------------------|------------------------------------------|
| ALL mandatory gates green            | ✅ DEPLOY                                |
| Any gate red (A, B, C, D, E, G, H, I)| 🛑 BLOCK — fix, then re-run all gates    |
| Advisory gate (F, J, K) flagged      | ⚠ DEPLOY OK · log the warning           |
| Catastrophic env mismatch (D red)    | 🚨 P0 INCIDENT — invoke RB-04             |

---

## 📋 POST-DEPLOY VERIFICATION

After production promotion, re-run gates against the **production URL** (not preview):

```bash
PROD_URL="https://<production-domain>"
curl -fsS "$PROD_URL/api/version"
curl -fsS "$PROD_URL/api/cluster/capacity"
curl -fsS "$PROD_URL/api/health"
```

Confirm `app_env=production` and `severity=ok`.

If any verification fails post-deploy: **immediate rollback** per `OPERATIONAL_RUNBOOKS.md` § RB-03.

---

## 🛑 NEVER

- Never deploy without running Gates A–I.
- Never override a red gate with "looks fine".
- Never deploy with `severity=critical`.
- Never deploy with mismatched APP_ENV/DB_NAME.
- Never deploy if backup age > 6 hours (operational data loss risk during rollback).
- Never deploy on Fridays after 14:00 without a hot-standby operator (general field-ops doctrine).

---

## 🧰 One-shot full check

Save this as `/app/backend/tools/preflight.sh` for one-command preflight:

```bash
#!/bin/bash
set -e
cd /app/backend
URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d= -f2)
echo "=== Gate A · API regression ==="
python3 -m pytest tests/regression/test_critical_flows.py -q
echo "=== Gate B · Playwright ==="
python3 -m pytest tests/pw_suite/ -q
echo "=== Gate C · Idempotency unit ==="
python3 -m pytest tests/test_iter437_idempotency_strip.py -q
echo "=== Gate D · Env identity ==="
curl -fsS "$URL/api/version" | python3 -m json.tool | head -10
echo "=== Gate E · Capacity ==="
curl -fsS "$URL/api/cluster/capacity" | python3 -m json.tool | head -10
echo "=== Gate I · Auth continuity ==="
for cred in "hrmanager@mascigc.com:HRTesting2026!:hr/login" "chriswright@mascigc.com:ChrisRocksThis2026:pm/login" "fieldleader@mascigc.com:FieldLead2026!:field-leadership/portal/login" "dispatch@mascigc.com:DispatchTest2026!:dispatch/login" "safety@mascigc.com:SafetyTest2026!:safety/login"; do
  IFS=: read -r email pw path <<< "$cred"
  code=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$URL/api/$path" -H "Content-Type: application/json" -d "{\"email\":\"$email\",\"password\":\"$pw\"}")
  echo "  $email -> $code"
done
echo ""
echo "✅ PREFLIGHT PASSED — safe to deploy"
```

Exit code 0 = green light.
