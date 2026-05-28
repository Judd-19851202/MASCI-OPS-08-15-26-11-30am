# Timestamp Utility Standard

_Phase TRUST-TIME-1 · 2026-05-28._

## Doctrine (one paragraph)

The platform STORES every operational timestamp in UTC. It
TRANSMITS them as ABSOLUTE (tz-aware) ISO strings — every value
ends with `Z` or `+HH:MM`. The frontend RENDERS them in the
operator's LOCAL browser timezone using the shared helpers in
`lib/dateUtils.js`. When a surface is explicitly an admin / audit
view that needs UTC for cross-timezone comparison, it uses
`formatUtcForAudit()` which ALWAYS suffixes the string with
" UTC".

## Helpers (canonical)

```js
import {
  formatLocalDateTime,   // "5/28/2026, 9:43 AM" — primary
  formatLocalDate,       // "5/28/2026"
  formatLocalTime,       // "9:43 AM"
  formatLocalShort,      // "5/28 9:43 AM" — compact lists
  formatRelativeTime,    // "3m ago" · "2h ago" · "yesterday"
  formatUtcForAudit,     // "2026-05-28 13:43 UTC" — audit-only
  todayLocalIso,         // "2026-05-28" — today in local tz
  toLocalIso,            // accepts any Date-able, returns date-only
} from "@/lib/dateUtils";
```

## Coercion contract

`_coerce(ts)` (internal, exposed via `__TESTING__`) handles four
input shapes:

| Input | Behavior |
|---|---|
| `null` / `""` / `undefined` | returns `null` (helpers render `""`) |
| `Date` instance | returns as-is |
| ISO with `Z` or `±HH:MM` | parses as UTC, JS converts to local |
| ISO **without** tz (`"2026-05-28T13:43"`) | **tagged as UTC** (the bug fix) |
| Date-only `"2026-05-28"` | parsed as that calendar day in **local** time |
| Any other Date-able | passed to `new Date()` |

The naive-ISO branch is **the core fix**. Backend stores UTC but
older serializations dropped the tz suffix; the frontend defensively
treats those as UTC instead of LOCAL.

## Backend contract

`_iso(dt)` helpers (one in each route module) MUST:

```python
def _iso(dt) -> Optional[str]:
    if not dt:
        return None  # or "" depending on route convention
    if isinstance(dt, str):
        return dt
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)   # ← the doctrine line
    return dt.replace(microsecond=0).isoformat()
```

The `AsyncIOMotorClient` MUST be instantiated with `tz_aware=True`
so reads from Mongo come back as aware datetimes. This is set
globally in `server.py`.

## When to use which helper

| Surface | Helper | Example |
|---|---|---|
| PO submit/approve/upload time (operator-facing) | `formatLocalDateTime` | "Submitted 5/28/2026, 9:43 AM" |
| Daily report metadata line | `formatLocalDate` | "Reported 5/28/2026" |
| Notifications "last seen" | `formatLocalShort` | "5/28 9:43 AM" |
| Tasks "Created" | `formatRelativeTime` | "3m ago" |
| System health "Checked" / Audit timeline footer | `formatUtcForAudit` | "2026-05-28 13:43 UTC" |
| Date picker default | `todayLocalIso` | "2026-05-28" |

## Rules

1. **Never** use `.slice(0, 16).replace("T", " ")` on an ISO
   string for display. That displays UTC clock numbers as local
   time. This is the documented anti-pattern.
2. **Never** use `new Date(...).toISOString().slice(...)` for
   display — that's a UTC string regardless of operator timezone.
3. **Never** display a UTC value without the literal " UTC" suffix.
4. **Always** use the canonical helpers above. If a surface needs
   a format the helpers don't provide, add a new helper to
   `dateUtils.js` rather than rolling a one-off `toLocaleDateString({...})`.
5. Backend writes use `datetime.now(timezone.utc)` — never
   `datetime.utcnow()` (which returns naive).

## Regression coverage

- `test_trust_time_1_backend_contract.py` (5/5)
- `test_trust_time_1_frontend_localization.py` (7/7 across 4
  CONUS timezones)
- Authority Mismatch Probe must remain green (it cannot detect
  timestamp bugs but it catches authority-pattern drift that
  often accompanies hasty refactors).

## Owner

This standard is enforced via the regression suites above and
via the `_iso()` helper template in each route module. Any new
route module that introduces a timestamp serializer MUST follow
the same template.
