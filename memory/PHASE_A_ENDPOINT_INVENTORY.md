# Phase A · Endpoint Inventory

**Classification:** OMEGA Pillar 2 · Phase A · Endpoint Surface
**Generated:** 2026-05-31 UTC

---

## 1 · The five new endpoints

All are read-only or configuration-write. All require admin-strict authentication (`X-Admin-Token` header).

| # | Method | Path | Auth | Purpose | Body / Query | Response shape |
|---|---|---|---|---|---|---|
| 1 | GET | `/api/admin/command-center/snapshot` | admin-strict | Full RAG snapshot · 5 cards · Pulse Strip | none | `{pill, computed_at, pulse{}, cards[{card_id, title, pill, headline_counts, warnings[], items[]}], calendar, cached}` |
| 2 | GET | `/api/admin/command-center/thresholds` | admin-strict | Read current scoring config | none | `{version, rules{rule_id: {amber, red, predicate, operational_risk, leadership_action, owner_role, expected_resolution, ...}}}` |
| 3 | PATCH | `/api/admin/command-center/thresholds` | admin-strict | Tune any rule's thresholds · audit-logged | `{rules: {rule_id: {amber, red, ...partial}}}` | `{ok, version, rules_count}` |
| 4 | GET | `/api/admin/command-center/calendar` | admin-strict | Read working-day / holiday config | none | `{version, timezone_offset_hours, working_weekdays, working_hour_start, working_hour_end, holidays}` |
| 5 | PATCH | `/api/admin/command-center/calendar` | admin-strict | Update calendar fields · audit-logged | `{timezone_offset_hours?, working_weekdays?, working_hour_start?, working_hour_end?, holidays?}` | `{ok, version}` |
| 6 | GET | `/api/admin/command-center/drilldown/{card_id}/{item_id}` | admin-strict | Per-item drilldown returning the 5-question payload + source doc | path params | `{card_id, item_id, source_doc, actions_underway, owner, expected_resolution}` |

---

## 2 · Auth gate verification

| Probe | Expected | Actual |
|---|---|---|
| `GET /snapshot` without token | 401 | **401** ✅ |
| `GET /snapshot` with admin token | 200 | **200** ✅ |
| `GET /thresholds` with admin token | 200 | **200** ✅ |
| `GET /calendar` with admin token | 200 | **200** ✅ |

---

## 3 · Snapshot response anatomy (top-level keys)

```text
computed_at              ISO timestamp (datetime.now UTC) — freshness stamp
pill                     "GREEN" | "AMBER" | "RED" — composite of all 5 cards
pulse                    { pill, red_warnings, amber_warnings, red_items, amber_items, headline }
cards[]                  5 card objects (jobs, safety, equipment, accountability, approvals)
calendar                 active calendar config (read-only inside snapshot)
cached                   bool — true if served from the 15-sec server cache
```

Each card object:
```text
card_id                  "jobs" | "safety" | "equipment" | "accountability" | "approvals"
title                    human-readable card title
pill                     "GREEN" | "AMBER" | "RED"
headline_counts          { domain-specific count map (e.g., dr_missing, oos_red, ca_overdue) }
warnings[]               array of { kind, severity, message, item_count, rule_id, owner, drill_to }
items[]                  array of { what_wrong, why_red, owner, current_status, eta, drill_to, rule_id, severity }
```

---

## 4 · Caching

- Snapshot is cached server-side for **15 seconds** (mirrors `recovery_dashboard`).
- Threshold or calendar PATCH **invalidates the cache** (`_CACHE["snapshot"] = None`) so the next read recomputes.
- Frontend polls every 30 seconds (intentional gap above the server TTL).

---

## 5 · Audit trail

Every PATCH on thresholds or calendar writes an immutable row to `admin_audit`:
```text
{
  ts:           ISO timestamp,
  kind:         "command_center.thresholds.update" | "command_center.calendar.update",
  version:      new doc version,
  changed_keys: [...]
}
```
This is the platform's standard audit collection (already used by other admin operations).

---

## 6 · MongoDB collections touched

### Read-only (existing collections — never mutated)
- `jobs_master`
- `daily_reports`
- `incidents`
- `corrective_actions`
- `fleet_defects`
- `tasks`
- `po_requests`

### Read + write (NEW config docs — only writes are the operator-driven PATCH)
- `command_center_thresholds` (one doc, `_id: command_center_thresholds`)
- `command_center_calendar` (one doc, `_id: command_center_calendar`)

### Write-only on operator action (audit)
- `admin_audit` (existing platform-wide collection; same shape as other admin writes)

**No** other collections are written. **No** schema migration. **No** index addition.

---

## 7 · OMEGA freeze respect

- `routes/recovery_dashboard.py`: **untouched** (verified by `git diff`)
- `lib/singleton_scheduler.py`: **untouched**
- `routes/safety.py` / `fleet_ops.py` / `tasks_notifications.py`: **read-only consumers**, no edits
- Backup archive code paths: **untouched**
- Notification fan-out helpers: **never invoked** from `command_center.py`

---

## 8 · Future endpoint candidates (Phase B/C · NOT IMPLEMENTED)

For traceability only:
- `GET /api/admin/command-center/snapshot.csv` — CSV export (Phase B)
- `GET /api/admin/command-center/recommender/top` — recommender ranking (Phase B)
- `GET /api/admin/command-center/expirations` — document expirations card (Phase B · gated on data audit)
- `GET /api/pm/command-center/snapshot` — PM-scoped lens (Phase C)
- `GET /api/safety-portal/command-center/snapshot` — Safety-scoped lens (Phase C)

These do **not** exist in Phase A.
