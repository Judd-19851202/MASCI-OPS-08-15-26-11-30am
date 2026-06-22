# TRACK 15.61 — Executive Dashboard Trace (Phase 7)

**Method:** probe every endpoint that could plausibly serve "executive dashboard" data on production. Identify which Daily-Report metrics reach Exec-tier consumers.

## Endpoints probed

| Endpoint | Result |
|---|---|
| `GET /api/admin/executive-dashboard` | 404 |
| `GET /api/admin/dashboard` | 404 |
| `GET /api/admin/exec/overview` | 404 |
| `GET /api/leadership/dashboard` | 404 |
| `GET /api/admin/operations/overview` | 404 |

**No dedicated executive dashboard endpoint exists on production.** Executive consumers (Jaymn, owners, leadership) read the same Admin Command Center / Ops Center / PM Command Center surfaces that operators read, plus the Operations Center Command view, plus the weekly digest emails.

## What "executive reporting" actually means today

The closest surfaces:

| Surface | Source | Daily-Report metrics it shows |
|---|---|---|
| Admin Command Center (`/admin`) | aggregates across `db.incidents`, `db.meetings`, `db.daily_reports` via the standard list endpoints | counts ONLY (number of reports submitted per day) — no per-report metric roll-up |
| Operations Center Command (`/operations`) | dispatch + motive_events + asset master | does NOT consume Daily Report material/haul rows |
| PM Command Center | already audited in Phase 6 | as documented in Phase 6 |
| Safety Digest email (`safety@mascigc.com`) | weekly cron | counts only |

## Missing executive metrics

The exec layer cannot answer any of these questions from current production endpoints:

| Question an exec would ask | Currently answerable? |
|---|---|
| How many loads of dirt did we move across the company yesterday? | **No** — outbound_materials are not aggregated above per-day per-project |
| Which projects produced the most this week? | **No** — `production[]` is empty on 97 % of reports |
| Where did we have schedule delays? | **No** — `schedule_delays_notes` is 0 % populated |
| Who hauled for us this month and how much? | **No** — hauler field is free-text "Masci"/"MASCI"; no roll-up |
| How many subcontractor man-hours? | **No** — subcontractor field is structured but no roll-up endpoint |
| What major events constrained work this week? | **No** — `constraints[]` is 6.5 % populated and not aggregated |

## What IS available to exec

- Total report counts per project per day (via the list endpoint).
- Audit-grade per-report PDFs (downloadable in backup ZIPs).
- Safety dashboards (incidents, meetings) — these DO aggregate to the Safety Hub.
- Motive event volume (vehicle telemetry).

## Conclusion

There is **no executive-grade roll-up of Daily Report business data** on production. The Daily Report system is functioning as a record-keeping and PDF-distribution platform, NOT as an aggregation platform. Executives must consume the underlying data manually (open one PDF at a time) to answer cross-job questions.

This is the largest gap surfaced by Track 15.61. Recommendation rank: **R-EXEC** (very high impact, medium complexity) in `TRACK_15_61_RECOMMENDATIONS.md`.
