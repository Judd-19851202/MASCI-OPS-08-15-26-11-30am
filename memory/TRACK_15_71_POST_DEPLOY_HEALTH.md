# TRACK 15.71 · Post-Deploy Health Check

_2026-06-23 · Pre-deploy baseline; operator re-runs post-deploy_

## Pre-Deploy Health Baseline (this pod, fresh boot)

| Probe | Result |
|---|---|
| Preview backend uptime | 0:01:24 (fresh boot after env reload) |
| `/api/health` | `{"ok": true, "service": "masci-hub"}` ✅ |
| Supervisor `backend` | RUNNING ✅ |
| Supervisor `frontend` | RUNNING ✅ |
| Supervisor `mongodb` | RUNNING ✅ |
| Production `/api/health` (mascidocs.com) | HTTP 200 · 165ms ✅ |
| Production root | HTTP 200 · 474ms ✅ |

## Post-Deploy Operator Checklist (T+0 to T+5 min)

```bash
# At T+30s after deploy push:
curl -s https://mascidocs.com/api/health
curl -s https://mascidocs.com/api/health/full | jq .

# Expected:
#   /api/health → 200 · {"ok": true, "service": "masci-hub"}
#   /api/health/full → 200 · mongo healthy · scheduler healthy · backup recent
```

## Failure Decision Matrix

| Probe | If FAIL → |
|---|---|
| `/api/health` non-200 | rollback within 5 min |
| `/api/health/full` mongo unhealthy | investigate Atlas; rollback if Mongo recovery > 5 min |
| `/api/health/full` scheduler unhealthy | investigate scheduler logs; rollback if persistent |
| Backend restart loop (3+ restarts in 5 min) | rollback immediately |
| Frontend 5xx on root | rollback |
| Critical backend log spike | investigate; rollback if cascading |

## Additional Post-Deploy Smoke

```bash
# Admin login page loads
curl -s -o /dev/null -w "%{http_code}\n" https://mascidocs.com/admin/login
# expect: 200

# Branding endpoint
curl -s https://mascidocs.com/api/branding/current | jq '.tenant_key'
# expect: "masci"

# Email routing V2 endpoint (admin token required)
TOK=<admin_token>
curl -s https://mascidocs.com/api/admin/email-routing/v2/routes \
  -H "X-Admin-Token: $TOK" | jq '.count'
# expect: 19
```

## Verdict

🟡 **Pre-deploy baseline GREEN · Post-deploy verification is operator-driven (T+0 to T+5 min after deploy push).**
