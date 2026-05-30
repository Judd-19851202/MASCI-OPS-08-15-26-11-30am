# Platform Truth Map — README

**Date:** 2026-02-01  
**Authorization:** Operator directive "PLATFORM TRUTH MAP PHASE 1 AUTHORIZATION" (2026-02-01).  
**Mission:** Document exactly what happens at every route, workflow, form, action, API, record, dashboard, notification, and owner across the MASCI Ops Platform. **No guessing.** Everything is either KNOWN GOOD, KNOWN GAP, BROKEN, UNKNOWN, or OPERATOR DECISION NEEDED.

---

## Deliverable index

| # | File | Purpose |
|---|------|---------|
| 1 | `PLATFORM_ROUTE_MAP.md` | Every frontend route → component → auth wrapper → portal → classification |
| 2 | `API_DEPENDENCY_MAP.md` | Every backend endpoint → method → file → auth dep → collections touched |
| 3 | `WORKFLOW_LIFECYCLE_MAP.md` | Per-workflow lifecycle answering the 16 required questions (create / route / API / collection / owner / view / edit / notify / channel / surface / dashboard / status / next / no-action / feeds / should-feed-but-doesn't) |
| 4 | `NOTIFICATION_DELIVERY_MAP.md` | Email routing rules (ALWAYS_CC, COMPLIANCE_KINDS, PM_ONLY_KINDS) · in-app bell · task fan-out · digests · cron alerts |
| 5 | `DASHBOARD_DESTINATION_MAP.md` | For every record kind, which dashboard(s) it lands on, in which portal, with which counters |
| 6 | `ORPHAN_AND_GAP_REGISTER.md` | Consolidated orphans + 18 gaps from previous P0 trust audit, re-validated 2026-02-01 |
| 7 | `SYSTEM_TALK_MAP.md` | Inter-system data flow: which subsystem feeds which downstream consumer |

Raw extracted evidence (machine-generated, do not hand-edit):

| File | Contents |
|------|----------|
| `truth_map_data/frontend_routes.csv` | 249 routes, 3 cols (path, component, auth_wrapper) |
| `truth_map_data/route_domains.json` | Routes bucketed by domain (admin / pm / hr / shop / safety / etc.) |
| `truth_map_data/backend_endpoints.csv` | 816 endpoints, 6 cols (method, path, file, fn, auth, collections) |
| `truth_map_data/auth_gate_summary.json` | Auth dependency distribution across all endpoints |
| `truth_map_data/collections.txt` | 143 MongoDB collections referenced anywhere in `/app/backend` |
| `truth_map_data/notification_calls.csv` | Locations of every `send_email` / `_send_alert` / `schedule_auto_email` helper in the backend |

> The raw CSV/JSON/TXT files are **the source of truth**. The 7 narrative docs synthesize and classify them. If a discrepancy is found, the CSV wins and the narrative is wrong.

---

## Classification legend (applied throughout)

| Tag | Meaning |
|-----|---------|
| 🟢 **KNOWN GOOD** | Mechanism wired end-to-end. Evidence: code path traced from trigger → record → owner → notification → dashboard. |
| 🟡 **KNOWN GAP** | Workflow functions but visibility/owner/notification is incomplete in a defined, documented way. |
| 🔴 **BROKEN** | Component exists but does not work as intended (e.g. dead button, blocked dependency, crashed scheduler). |
| ⚪ **UNKNOWN** | Code present but lifecycle cannot be 100% verified from static analysis alone. Requires runtime trace or operator confirmation. |
| ⚫ **OPERATOR DECISION NEEDED** | Intentionality cannot be inferred — operator must decide whether the current behaviour is desired. |

---

## Scope & method

- **Static analysis only**: grep / AST-style parsing of `/app/frontend/src` and `/app/backend`. No runtime tracing in this pass.
- **Inputs**: `App.js` (250 `<Route>` declarations), 838 FastAPI endpoint decorators across 118 files, 143 MongoDB collection references, the existing audit corpus in `/app/memory/` (esp. `NOTIFICATION_GAP_REGISTER.md`, `ORPHAN_WORKFLOW_REPORT.md`, `EMAIL_TEMPLATE_STANDARD.md`, `pm_routing.py`, `lib/event_fanout.py`).
- **Outputs**: 7 narrative docs + 6 raw evidence files + index updates.

---

## How to use this map

1. Operator opens `PLATFORM_TRUTH_MAP_README.md` (this file).
2. To trace a workflow end-to-end → `WORKFLOW_LIFECYCLE_MAP.md`.
3. To audit who can hit a given API → `API_DEPENDENCY_MAP.md` (rows filtered by `auth` column).
4. To audit who sees a given URL → `PLATFORM_ROUTE_MAP.md` (rows filtered by `auth_wrapper` column).
5. To audit "what happens after submit" → `NOTIFICATION_DELIVERY_MAP.md` + `DASHBOARD_DESTINATION_MAP.md`.
6. To find what is broken or missing → `ORPHAN_AND_GAP_REGISTER.md`.
7. To trace data flow between subsystems (Daily Report → Project Health, Dispatch → Asset Holds, etc.) → `SYSTEM_TALK_MAP.md`.

---

## What this map is NOT

- ❌ It is **not** a remediation plan. Operator picks the next authorized batch.
- ❌ It is **not** a runtime audit. Static analysis cannot prove cron alarms fire, only that the cron-registration code path exists.
- ❌ It does **not** include user-facing copy, translation tables, or UX language audit (that lives in `OPERATIONAL_VERBIAGE_DOCTRINE.md`).

---

## Stop condition

Truth Map is read-only documentation. No code changes were made for the map itself. Operator review pending before any remediation.
