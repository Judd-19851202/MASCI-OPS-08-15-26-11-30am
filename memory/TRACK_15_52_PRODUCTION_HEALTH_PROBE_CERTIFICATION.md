# TRACK 15.52 · Production Health-Probe Certification

**Status:** ✅ GREEN · all probes pass · no false alerts.
**Measurement window:** 2026-06-19 20:39 – 20:42 UTC.
**Target:** `https://safety-audit-mobile-1.preview.emergentagent.com`

## 1 · Direct contract — `/api/health/full`

| Field | Before | After |
|---|---|---|
| HTTP status | **503** | **200** ✅ |
| `ok` | `false` | **`true`** |
| `mongo` | `true` | `true` |
| `scheduler` | `false` → promoted to `true` only when `backup_recent` was true | **`true`** (now consistently true because R2 truth flows through) |
| `backup_recent` | `false` (used stale DB audit row) | **`true`** (uses R2 bucket directly, newest object 17 min old at fix time) |

Live evidence (curl, captured 20:39:55 UTC, immediately after `sudo supervisorctl restart backend`):

```
$ curl -s https://safety-audit-mobile-1.preview.emergentagent.com/api/health/full -w "\nHTTP: %{http_code}\n"
{"ok":true,"mongo":true,"scheduler":true,"backup_recent":true}
HTTP: 200
```

## 2 · Pytest contract — `test_iter183_health_full_endpoint.py`

```
tests/test_iter183_health_full_endpoint.py::test_api_health_full_contract PASSED [ 33%]
tests/test_iter183_health_full_endpoint.py::test_api_health_full_no_leak PASSED [ 66%]
tests/test_iter183_health_full_endpoint.py::test_api_health_still_lightweight PASSED [100%]

============================== 3 passed in 0.59s ===============================
```

Schema is preserved: only the four contract keys (`ok · mongo · scheduler · backup_recent`) are returned. Status code 200 when ok=true; 503 when ok=false. No timestamps, no internal state names, no error messages leaked.

## 3 · Latency

| Run | HTTP | Total |
|---|:---:|---:|
| 1 (cold after restart) | 200 | 0.142 s |
| 2 (warm cache hit) | 200 | 0.159 s |
| 3 (warm cache hit) | 200 | 0.163 s |
| 4 (warm cache hit) | 200 | 0.156 s |

The 5-minute cache means the first call per process pays the R2 list cost (~200 ms in the worst case; ~140 ms here). Subsequent calls return from the in-process cache in `< 200 ms`. Well inside the contract budget for an UptimeRobot probe.

## 4 · Negative test — stale-backup scenario

Verified by injecting a 27-hour-old R2 age into the cache and re-calling the endpoint handler in-process:

```python
server._R2_BACKUP_AGE_CACHE.update({"ts": time.time(), "age_s": 27 * 3600.0})
# -> {'ok': False, 'mongo': True, 'scheduler': False, 'backup_recent': False} · status=503

server._R2_BACKUP_AGE_CACHE.update({"ts": time.time(), "age_s": 1800.0})  # 30 min
# -> {'ok': True, 'mongo': True, 'scheduler': True, 'backup_recent': True}  · status=200
```

✅ Stale R2 → unhealthy. Fresh R2 → healthy. The 26-hour SLO is enforced symmetrically.

## 5 · GitHub Actions workflow

`/.github/workflows/production-health-probe.yml` was inspected. Its probes (`tools/verify-production.sh`) hit:
- `/api/health` (must be 200) — unaffected.
- `/api/passkeys/login/options` (auth/route gate) — unaffected.
- `/api/admin-strict/diag/persistence-health` (auth gate) — unaffected.
- `/api/field-memory/recent` (auth gate) — unaffected.
- `/api/dispatch/operational-moments/by-assignment/test` (auth gate) — unaffected.

This workflow itself **does not consult `/api/health/full`**, so the file requires no change. The false-alert email path runs through:
- **UptimeRobot** (external monitor) → `/api/health/full` → email on 503.
- **`scripts/predeploy_certify.sh` Phase 1** → `curl /api/health/full` expecting 200 → blocks deploys.

Both now see 200. Both stop alerting / blocking.

## 6 · Predeploy certify gate

```
$ for path in /api/health /api/health/full /api/version /api/platform/data-truth; do
    code=$(curl -sS -o /dev/null -w "%{http_code}" "${API_URL}${path}")
    echo "  ${path}: ${code}"
  done
```

Result against fixed backend:
- `/api/health` → **200** ✅
- `/api/health/full` → **200** ✅
- `/api/version` → 200 (Track 15.51 evidence captured this earlier)
- `/api/platform/data-truth` → 200 (route still mounted)

Predeploy Phase 1 passes.

## 7 · "Did this stop false GitHub alert emails without masking real outages?"

**Yes.**

| Question | Evidence |
|---|---|
| Are the false-positive emails stopped? | ✅ `/api/health/full` now returns 200 against the live system. UptimeRobot will not page; `predeploy_certify.sh` Phase 1 passes. |
| Are real outages still surfaced? | ✅ Stale-R2 simulation (27-hour old newest backup) returns 503 with `backup_recent=false`. The 26-hour SLO is unchanged. |
| Are any pre-existing checks weakened? | ✅ No. Pytest contract `test_iter183_health_full_endpoint.py` still passes. The DB audit row is still consulted as fallback when R2 is unreachable. Mongo ping and scheduler heartbeat still gate `ok`. |
| Are new failure modes introduced? | One: if R2 itself is unreachable AND the DB audit row is stale, the probe correctly returns 503 (this is a real degraded condition — both backup paths down). |

## 8 · Verdict

🟢 **GREEN — production-health-probe is reliable. Track 15.52 closes the Track 15.51 Phase 8 YELLOW finding.**
