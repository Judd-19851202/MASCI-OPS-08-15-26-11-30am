# PROD-STABILIZE-001 · Phase 1 · Live Motive Validation

**Mode:** Read-only · External probes only
**Date:** 2026-06-09

| # | Item | Result | Evidence |
|---|---|---|---|
| 1 | Production Motive credentials exist | ✅ **CONFIRMED via code path** | Webhook POST with bad signature returns `401 "Invalid webhook signature"` — the secret-present branch (`webhooks.py:82-89`) executes. If credentials were absent, the response would be the 503 `"awaiting_credentials"` shape (proven by MaintainX, see Phase 2). |
| 2 | Production webhook secret exists | ✅ **CONFIRMED** | Same as #1 — secret-present is the only branch that returns 401 on bad signature. |
| 3 | Production integration status = Connected | 🟡 **Operator-required** | This data lives behind `GET /api/admin/integrations/overview` which returns 401 to unauthenticated probes (✅ correct gate). Operator to capture and attach. |
| 4 | Last successful sync timestamp | 🟡 **Operator-required** | Behind `GET /api/admin/integrations/sync-logs` (401 to unauthed). |
| 5 | Vehicle count | 🟡 **Operator-required** | Behind admin asset list / Motive panel. |
| 6 | Driver count | 🟡 **Operator-required** | Same. |
| 7 | Geofence count | 🟡 **Operator-required** | Same. |
| 8 | Event count | 🟡 **Operator-required** | Behind admin event list. |
| 9 | Latest webhook received | 🟡 **Operator-required** | Behind admin sync-logs. |
| 10 | Latest webhook accepted | 🟡 **Operator-required** | Behind admin sync-logs. |

## Raw evidence

```
$ curl -sk -X POST -H "Content-Type: application/json" \
  -H "X-Motive-Signature: sha256=0000...000" \
  -d '{"event_type":"ignition_on"}' \
  https://mascidocs.com/api/integrations/motive/webhook
HTTP 401 · 0.186s
{"detail":"Invalid webhook signature"}
```

```
$ curl -sk -X POST -H "Content-Type: application/json" -d '{}' \
  https://mascidocs.com/api/integrations/motive/webhook
HTTP 401 · 0.265s
{"detail":"Invalid webhook signature"}
```

```
$ curl -sk https://mascidocs.com/api/admin/integrations/overview
HTTP 401 · 0.313s
{"detail":"Admin login required"}
```

## Conclusion

**Phase 1 partial PASS — 2/2 verifiable externally are GREEN.** The remaining 8 items are operator-required (which is by design and a security feature). See Section 8 of the main certification for the operator runbook to close items 3–10.
