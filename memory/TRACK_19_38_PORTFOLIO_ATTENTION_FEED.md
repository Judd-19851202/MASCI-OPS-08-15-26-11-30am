# TRACK 19.38 · PORTFOLIO ATTENTION FEED

**Date:** 2026-07-03 · **Anchor:** `TRACK_19_38_CROSS_PORTAL_READ_FANOUT.md`

## Endpoint
`GET /api/incident-intelligence/portfolio-attention?limit=<int>` (default 50 · max 200).

## Auth
Safety **or** Admin (`make_require_safety_or_admin`). Same gate as write-side Safety-Admin surfaces — read here, write elsewhere.

## Response
```json
{
  "model_version":  "1.0.0",
  "generated_at":   "…ISO…",
  "actor_role":     "safety" | "admin",
  "view":           "portfolio",
  "cases":          [ … see per-case shape below … ],
  "count":          <int>,
  "sorted_by":      "attention_score_desc"
}
```

## Per-case shape (portfolio view)
| Key | Meaning | Source |
|---|---|---|
| `case_id` | Case UUID | `incident_cases.id` |
| `case_number` | Human case number | `incident_cases.case_number` |
| `state` | Case state | `incident_cases.state` |
| `incident_type` | Field-declared type | `incident_cases.field_block.incident_type` |
| `job_number` | Field-declared job | `incident_cases.field_block.job_number` |
| `location_label` | Field-declared location | `incident_cases.field_block.location_label` |
| `occurred_at` | When it happened | `incident_cases.field_block.occurred_at` |
| `submitted_at` | When submitted | `incident_cases.submitted_at || created_at` |
| `days_open` | Days between submit and closed/now | derived |
| `capa_open` | Open corrective actions | `corrective_actions` |
| `capa_total` | Total corrective actions | `corrective_actions` |
| `tasks_open` | Open case tasks | `case_tasks` |
| `readiness_band` | `low` / `medium` / `high` | derived |
| `attention_level` | `low` / `medium` / `high` | Track 19.37 scorer |
| `attention_score` | 0–100 | Track 19.37 scorer |
| `top_signals` | Top 3 firing signals with full rationale + source_fields | Track 19.37 scorer |

Sort order: `attention_score` DESC, then `days_open` DESC as tiebreak.

## Why this feed matters
The Safety Manager's first 60 seconds every morning used to be "which of these 47 open cases should I open first?" — a linear scan of a case list. The Portfolio Attention Feed re-orders that list by *presence-based* attention signals (injury · utility · delayed closeout · overdue CAPA · executive review needed) so that the cases most likely to need Safety attention float to the top.

It is **not** a triage decision. Every row's rationale is visible, every source field is cited, and the Safety Manager still opens the case, reads the immutable field record (Track 19.35), and makes the actual investigation calls.

## UI surface
Added as a section inside `/safety/executive-intelligence` (`ExecutiveIntelligence.jsx`). Renders up to 12 rows; each row is a button that navigates to `/safety/cases/{case_id}/executive-report` (Track 19.36). Bilingual · neutral wording · read-only.

## Zero-drift
- Existing Phase D aggregation endpoints (`/api/incident-intelligence/home`, `.../root-causes`, `.../corrective-actions`, `.../projects`, `.../fleet`, `.../learning`, `.../brief`) are unchanged.
- Reuses `compute_presence_score` from Track 19.37 — no duplicate scoring logic.
- No new decisions surfaced.

## Rollback
Delete the section block in `ExecutiveIntelligence.jsx` and the aggregator + route registration in the backend. Consumers that used the existing Phase D surface continue to work unchanged.
