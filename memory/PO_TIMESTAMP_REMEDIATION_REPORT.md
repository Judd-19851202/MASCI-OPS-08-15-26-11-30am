# PO Timestamp Remediation Report

_Phase TRUST-TIME-1 · 2026-05-28._

## Reported issue

Production operator uploaded a PO receipt at approximately
9:43 AM Eastern. The PO detail page rendered the upload time
as approximately 1:43 PM. Delta: +4 hours = EDT offset from UTC.

## Root cause (recap)

1. `AsyncIOMotorClient` was not tz-aware → reads return naive datetimes.
2. `_iso(dt)` emitted naive ISO strings (no Z suffix).
3. JS `new Date("2026-05-28T13:43:00")` parses naive ISO as LOCAL.
4. Result: UTC clock numbers shown as local clock → +4h delta.

## Before / After

### Backend response (PO detail · `receipt_uploaded_at`)
```
BEFORE  → "2026-05-28T13:43:00.092000"          (naive)
AFTER   → "2026-05-28T13:43:00.092000Z"         (tz-aware)
```

### Frontend render
```
Operator timezone: America/New_York · EDT (UTC-4)
Backend stored UTC: 13:43

BEFORE  → "5/28/2026, 1:43 PM"        ⚠ WRONG (+4h)
AFTER   → "5/28/2026, 9:43 AM"        🟢 CORRECT
```

### Across all CONUS timezones (verified by regression suite)

| Timezone | Local hour | Expected | Result |
|---|---|---|---|
| `America/New_York` (EDT · UTC-4) | 9:43 AM | hour `9` | 🟢 |
| `America/Chicago` (CDT · UTC-5) | 8:43 AM | hour `8` | 🟢 |
| `America/Denver` (MDT · UTC-6) | 7:43 AM | hour `7` | 🟢 |
| `America/Los_Angeles` (PDT · UTC-7) | 6:43 AM | hour `6` | 🟢 |

## Files changed (exact list)

### Backend
1. `/app/backend/server.py` line 31
   - `AsyncIOMotorClient(mongo_url)` → `AsyncIOMotorClient(mongo_url, tz_aware=True)`
2. `/app/backend/routes/po_requests.py` lines 99-126
   - `_iso(dt)` defensive: tag naive datetimes as UTC before serializing
3. `/app/backend/routes/admin_ops.py` lines 32-40
   - Same fix
4. `/app/backend/health_monitor.py` lines 34-38
   - Same fix

### Frontend
5. `/app/frontend/src/lib/dateUtils.js` — full rewrite
   - 8 named exports + `_coerce()` helper
   - Naive ISO defensively tagged as UTC
6. `/app/frontend/src/pages/PoRequests.jsx` — 4 timestamp renders + audit log
7. `/app/frontend/src/pages/NotificationsDigest.jsx` — 2 renders
8. `/app/frontend/src/pages/PmFieldLeadership.jsx` — 2 renders
9. `/app/frontend/src/pages/HrEmployeeAccountabilityTimeline.jsx` — audit footer (UTC labeled via `formatUtcForAudit`)
10. `/app/frontend/src/pages/admin/SystemHealth.jsx` — checked-at footer (UTC labeled)

### Probe baseline
11. `/app/scripts/authority_pattern_baseline.json`
    - Line 30: shifted from line 113 → 114 (import insertion in `HrEmployeeAccountabilityTimeline.jsx`)

### Tests
12. `/app/backend/tests/pw_suite/test_trust_time_1_backend_contract.py` (NEW · 5/5 PASS)
13. `/app/backend/tests/pw_suite/test_trust_time_1_frontend_localization.py` (NEW · 7/7 PASS)

## Live verification (preview)

```
$ curl -s "$URL/api/po-requests?limit=3" -H "X-Admin-Token: $TOK"
{
  "items": [
    {"id":"7dc2...","created_at":"2026-05-28T09:55:12.092000Z",...},
    {"id":"df43...","created_at":"2026-05-28T09:55:06.124000Z",...},
    {"id":"6988...","created_at":"2026-05-28T09:55:00.184000Z",...}
  ]
}
```

🟢 Every `created_at` now ends with `Z`. JS `new Date(...).toLocaleString()`
will produce correct local time on every operator's browser.

## Data migration: NOT REQUIRED

No historical PO records are altered. The backend now SERIALIZES
with the Z suffix (via tz-aware Motor); the frontend additionally
COERCES any naive ISO as UTC via `_coerce()` in `dateUtils.js`.

This means:
- New PO uploads: render correctly (backend-side fix).
- Old PO records that may still have naive serialization in cache
  or other endpoints: render correctly (frontend-side defensive
  coerce).

## Regression coverage

- Backend contract: 5/5 PASS
- Frontend localization across 4 CONUS timezones: 7/7 PASS
- Naive-ISO coercion equivalent to UTC-tagged ISO in all 4 timezones
- Audit helper always labels output with " UTC"
- `formatRelativeTime` minute-grained accuracy

## Deploy recommendation

🟢 **PROCEED.** Preview-verified, regression-locked, no data migration.

The fix lands cleanly in production after the next deploy. Once
deployed, any operator hitting `/po-requests` will see correct
local times on all PO records — both newly uploaded and
historical.
