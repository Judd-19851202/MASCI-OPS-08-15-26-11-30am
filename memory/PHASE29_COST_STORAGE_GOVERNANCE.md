# PHASE 29 · Cost + Storage Governance
## iter431 · 2026-05-25

## Weekly Operator Digest (NEW)
Plain-text "is the platform alive?" summary emailed Monday mornings.

### Endpoints
- `GET /api/admin/digest/weekly?format=text` — admin-gated; default
  returns plain text rendered output.
- `GET /api/admin/digest/weekly?format=json` — same payload as raw
  JSON so downstream tooling (or testing) can re-render.

### Render (canonical example)
```
MASCI Operations · Weekly Digest · 2026-05-26T14:00:00+00:00

Atlas:                  GREEN (mongo 8.0.23 · 121 collections)
Last backup:            3h ago (ok=true · size=14.2 MB · → r2)
Attachments:            70 · 100.0% R2-backed
Storage growth (30d):   1.2 MB · projected 90d: 3.6 MB
Evidence accesses (7d): 12
Drift warnings:         none

All systems calm.
```

If any of {Atlas RED · last_backup not ok · attachments < 99 % R2 ·
drift warnings} is true, the final line becomes:
`Operator review recommended.`

### Cron
- Scheduler in `backend/lib/operator_digest.py` ·
  `operator_digest_scheduler_loop(db, send_email_fn)`.
- Default Monday 14:00 UTC (overridable via `OPERATOR_DIGEST_HOUR_UTC`,
  `OPERATOR_DIGEST_WEEKDAY`).
- Recipients: `OPERATOR_DIGEST_RECIPIENTS` (comma-separated) →
  `SAFETY_DIGEST_TO_EMAIL` → `safety@mascigc.com`.
- Toggle: `OPERATOR_DIGEST_ENABLED` (default `true`).
- Reuses the existing Resend wrapper (`_safety_send_email`) — no new
  SDK plumbing.

### Data sources (all existing endpoints)
| Field                        | Source                                          |
|------------------------------|-------------------------------------------------|
| `atlas.*`                    | `db.command('buildInfo')` + `list_collection_names()` |
| `last_backup`                | `backup_runs.find_one(ok=true sort=ts -1)`      |
| `attachments.*`              | mirror of `/api/admin/operational-attachments/storage-summary` aggregation |
| `growth_30d.*`               | `operational_attachments.aggregate` 30-day window |
| `evidence_accesses_7d`       | `legacy_import_audit.count` `action=evidence_accessed` |
| `drift_warnings`             | `backup_drift_watch.find_one(ts >= cutoff)` heartbeat |

## Storage Summary (Phase 28.2 → 29)
Already shipped at `GET /api/admin/operational-attachments/storage-summary`.
Phase 29 didn't change its contract — just consumes it inside the digest.

## What this phase did NOT add
- ❌ Charts
- ❌ Graphs
- ❌ Dashboards
- ❌ Analytics centre
- ❌ Admin portal page
- ❌ Performance scoring
- ❌ Productivity tracking

## Verification
- `tests/test_iter431_phase29.py::test_iter431_digest_renders_required_lines`
- `tests/test_iter431_phase29.py::test_iter431_digest_renders_review_when_red`
- Live curl against preview: `/api/admin/digest/weekly` returns the
  rendered text successfully.

## Operator runbook (paste into a calendar reminder)
```bash
API_URL="https://mascidocs.com"
TOKEN=$(curl -s -X POST "$API_URL/api/admin/login" \
  -H "Content-Type: application/json" \
  -d '{"password":"…"}' | jq -r '.token')
curl -s "$API_URL/api/admin/digest/weekly" -H "X-Admin-Token: $TOKEN"
```
That is the whole operator surface. Nothing more is needed.
