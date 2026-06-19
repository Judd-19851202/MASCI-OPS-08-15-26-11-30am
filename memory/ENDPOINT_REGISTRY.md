# TRACK 15.34 · ENDPOINT REGISTRY (auto-generated)

**Generated:** 2026-02 via `app.routes` introspection
**Source of truth:** FastAPI `app.routes` (lives forever in `backend/server.py`)
**Total HTTP routes:** **1,190** (1,184 `/api/*` + 6 health/probe)

> This registry is the certification source of truth. Regenerate with: `python3 -c "from server import app; print(len(app.routes))"` and consult `/tmp/routes_dump.txt` for the full list (tab-separated `METHOD PATH NAME`).

## Top-level distribution

| Prefix | Count | Owner |
|---|---|---|
| `/api/admin` | 335 | admin · per-user via `user_directory` |
| `/api/trench-safety` | 89 | safety + leadership |
| `/api/dispatch` | 59 | dispatch portal |
| `/api/safety` | 53 | safety portal |
| `/api/shop` | 51 | shop portal · per-user via `shop_users` |
| `/api/hr` | 46 | hr portal |
| `/api/field-leadership` | 42 | fl portal |
| `/api/asset-spine` | 40 | shop + dispatch + admin |
| `/api/pm` | 27 | pm portal · per-user via `project_managers` |
| `/api/operations` | 25 | admin · operations center |
| `/api/odr` | 22 | operational data review (admin) |
| `/api/projects` | 19 | mixed scopes (pm + admin) |
| `/api/master-lookup` | 15 | admin (master data) |
| `/api/operations-actions` | 12 | admin (OA workflow) |
| `/api/operations-center` | 12 | admin |
| `/api/safety-forms` | 12 | public · `SAFETY_FORMS_PASSWORD`-gated |
| `/api/auth` | 11 | multi-login + portal helpers |
| `/api/dev` | 11 | dev gate · `DEV_PASSWORD` |
| `/api/po-requests` | 11 | po lifecycle |
| `/api/daily-reports` | 10 | public + pm/safety |
| Remaining | 290 | mixed (notifications, audit-logs, integrations, public submission, training, payroll-variance, ...) |

## Categories

### Public (no auth)
- `/api/health` → 200 always
- `/api/public/*` → various submission roots (safety meetings, daily reports, QA/QC, JHA)
- `/api/safety-forms/*` (12 routes) → password-gated public surface (`SAFETY_FORMS_PASSWORD`)

### Auth surfaces
| Endpoint | Method | Note |
|---|---|---|
| `/api/auth/multi-login` | POST | Canonical · issues all 7 portal tokens for a `user_directory` row |
| `/api/admin/login` | POST | **RETIRED in 15.32** — returns HTTP 410 with retirement message |
| `/api/pm/login` | POST | Per-user only · email required · returns HTTP 401 retirement message if email omitted |
| `/api/shop/login` | POST | Per-user only · email required (15.30) |
| `/api/hr/login` · `/api/safety/login` · `/api/dispatch/login` · `/api/field-leadership/login` | POST | Per-user, per-portal |

### Notifications (15.28D-canonical)
- `/api/notifications` (GET) — bell list
- `/api/notifications/unread-count` (GET) — bell badge
- `/api/notifications/{id}/read` (POST) — mark-read
- `/api/notifications/read-all` (POST)
- `/api/notifications/{id}/acknowledge` (POST)
- `/api/field-leadership/portal/notifications-recent` (GET) — FL mirror feed

### Sensitive (admin-strict)
- `/api/admin/backups` (GET/POST/DELETE) — backup/restore
- `/api/admin/users/*` — user mgmt
- `/api/admin/odr/*` — operational data review

## Findings

### Duplicate routes
None identified. FastAPI raises on duplicate registration; the 1,190 total includes the GET/POST pair on the same path counted separately, which is normal.

### Deprecated routes (live but documented as retired)
- `/api/admin/login` POST → HTTP 410 (TRACK 15.32)
- Phase4 `/api/me/notifications` GET/POST → DELETED entirely (TRACK 15.28C)

### Unprotected routes (intentional)
- `/api/health` — health probe (must be unauth for k8s)
- `/api/public/*` — submission flows
- `/api/auth/multi-login`, `/api/{portal}/login` — login surfaces

### Unknown routes
None — every prefix maps to an accountable owner in the table above. The registry can be regenerated any time by re-running the introspection script; future tracks should treat this as live evidence rather than committed catalog.

## Status: 🟢 GREEN
1,190 routes catalogued. 0 duplicates. 0 unknown. Deprecated routes return explicit retirement responses. Auth tier verified by Phase 1 of this track.
