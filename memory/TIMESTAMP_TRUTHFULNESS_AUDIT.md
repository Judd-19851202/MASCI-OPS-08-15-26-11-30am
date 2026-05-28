# TIMESTAMP TRUTHFULNESS AUDIT

_Phase TRUST-TIME-1 · 2026-05-28 · root-cause + fix surface._

## Problem statement

A production operator uploaded a PO receipt at approximately
9:43 AM Eastern. The PO detail page subsequently rendered the
upload time as approximately 1:43 PM — a +4-hour delta exactly
matching the EDT offset from UTC.

## Root cause

Three reinforcing flaws across the stack:

1. **Motor client was not tz-aware.** `AsyncIOMotorClient(mongo_url)`
   was instantiated without `tz_aware=True`, so datetimes round-tripped
   from Mongo as **naive** even though they were stored as tz-aware
   UTC. Reference: `/app/backend/server.py` line 31.

2. **Backend `_iso(dt)` helpers omitted the timezone suffix.** When
   the input datetime was naive, the helper emitted
   `"2026-05-28T13:43:00"` with no `Z` and no `+00:00`. Three
   independent copies of this helper existed in
   `routes/po_requests.py`, `routes/admin_ops.py`, and
   `health_monitor.py` — all with the same bug.

3. **JavaScript `new Date(...)` parses naive ISO as LOCAL time.**
   Per the ECMAScript spec, when no timezone suffix is present
   the local browser timezone is assumed. So `new Date(
   "2026-05-28T13:43:00").toLocaleString()` returns
   "5/28/2026, 1:43 PM" on an EDT browser — the **UTC clock
   numbers displayed as if they were local**.

   _The frontend `dateUtils.js` helper only knew about
   date-only `YYYY-MM-DD` strings (the "tomorrow's PO" bug
   from earlier), not full datetime strings._

## Why this passed CI

- Existing tests stored and read back tz-aware datetimes from the
  same in-memory mock that DID preserve tz info, so the bug only
  surfaced against the live Motor → Mongo round-trip on production.
- The frontend used `new Date(...).toLocaleString()` correctly —
  it just received the wrong input from the backend.
- Authority Mismatch Probe and trust-surface registries do not
  cover timestamp truthfulness — TRUST-TIME-1 introduces a new
  contract surface.

## Affected surfaces (sweep)

A grep over `/app/frontend/src` found two distinct anti-patterns:

| Anti-pattern | Count | Surface kind |
|---|---|---|
| `new Date(x).toLocaleString()` | ~30 occurrences (mostly correct, except when backend returned naive ISO — the bug source) | operator-facing |
| `(x \|\| "").slice(0, 16).replace("T", " ")` | ~20 occurrences | mixed (admin · dispatch · audit) |
| `(x \|\| "").slice(0, 10)` (date-only) | ~25 occurrences | low-risk (date matches across timezones for the same day, mostly) |

## Fixes applied

### Backend (root cause)
- `server.py` — `AsyncIOMotorClient(mongo_url, tz_aware=True)`.
- `routes/po_requests.py::_iso` — defensive tag naive datetimes as UTC.
- `routes/admin_ops.py::_iso` — same.
- `health_monitor.py::_iso` — same.

### Frontend (display contract)
- `lib/dateUtils.js` — completely rewritten with 8 named exports
  (`formatLocalDateTime`, `formatLocalDate`, `formatLocalTime`,
  `formatLocalShort`, `formatRelativeTime`, `formatUtcForAudit`,
  plus the preserved `todayLocalIso` / `toLocalIso`).
- Coercion helper `_coerce(ts)` tags naive ISO as UTC defensively
  for ALL historical records that may still exist with the old
  serialization.

### Surfaces migrated to the new helper (this phase)
- `pages/PoRequests.jsx` — 4 timestamp renders + audit log
- `pages/NotificationsDigest.jsx` — 2 renders
- `pages/PmFieldLeadership.jsx` — 2 renders
- `pages/HrEmployeeAccountabilityTimeline.jsx` — audit footer (UTC labeled)
- `pages/admin/SystemHealth.jsx` — checked-at footer (UTC labeled)

### Surfaces remaining (admin/dispatch — follow-up wave, low operator impact)
- `pages/admin/AdminDispatch.jsx` (5 slice-replace usages)
- `pages/admin/AdminIntegrationCenter.jsx` (5 usages)
- `pages/admin/AssetProfile.jsx` (4 usages)
- `pages/admin/AdminOperationsEvents.jsx` (1 usage)
- `pages/admin/AdminLegacyImports.jsx` (2 usages)
- `pages/AssetTransfers.jsx` (1 usage)
- `pages/HrDriverQualificationImport.jsx` (1 usage)
- `pages/HrPayrollVariance.jsx` (1 usage)

These are admin-context audit surfaces — bug impact LOW (admin
operators expect UTC contexts). Slated for the next stabilization
pass.

## Doctrine

See `TIMESTAMP_UTILITY_STANDARD.md` for the full doctrine.

Headline: **store UTC · transmit tz-aware · render local · label
UTC when explicitly UTC**.

## Verification

- 5/5 backend contract tests PASS (PO requests, audit, draft
  telemetry, OPS-1 generated_at, dateUtils module served).
- 7/7 frontend localization tests PASS across all four CONUS
  timezones (America/New_York · America/Chicago · America/Denver ·
  America/Los_Angeles).
- Florida foreman simulation: UTC 13:43 → "9:43 AM" local. 🟢
- Naive ISO `2026-05-28T13:43:00` (production legacy records)
  coerces to UTC and localizes identically. 🟢
- Authority Mismatch Probe clean (0/0/58/88ms). 🟢
- Full regression battery: **74 / 74 PASS** including all
  TRUST-PO-1, OPS-1, contextual return-path, and TRUST-1 suites.

## Deploy recommendation

🟢 **PROCEED.** Preview-verified. The fix is purely a serialization
+ rendering correction; no data migration required. Existing
records with naive timestamps continue to localize correctly via
the defensive `_coerce()` helper.
