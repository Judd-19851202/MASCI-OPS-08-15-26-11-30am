# Operational Constraint Foundation

_Phase V-Prelude · Priority #1 · doctrine + scope · 2026-05-28._

## Mission

Capture the kinds of operational blockers that delay field work
TODAY, **before** RFI + Schedule systems exist. A constraint is
an item that is blocking, will block, or could block forward
operational progress on a project — captured cleanly, surfaced
calmly, resolved deliberately.

This is **operational blocker memory**, not scheduling. No CPM
math. No critical-path analysis. No predecessor/successor logic.

## In scope (Phase V-Prelude)

- A single `constraints` collection with the schema below.
- Manual creation by FL / PM / Safety operators.
- Manual linkage to existing artifacts (project, photos, reports,
  incidents, inspections).
- Severity + aging + status surface.
- Field-first mobile create flow (one form, photo attach, save).
- Calm read surface (`/constraints` list · `/constraints/:id` detail).

## Out of scope (V.1+)

- ⛔ Schedule linkage / activity binding
- ⛔ CPM math / float calculations
- ⛔ P6 import / sync
- ⛔ External-party portal (V.2)
- ⛔ Constraint → RFI auto-link (V.1+)
- ⛔ Constraint analytics dashboard

## Schema (draft · `constraints` collection)

```jsonc
{
  "id":              "uuid4",
  "project_id":      "fk → projects",
  "title":           "string · ≤ 140 chars",
  "discipline":      "enum: utilities · access · MOT · survey · QC · FAA · subcontractor · other",
  "kind":            "enum: utility-conflict · owner-hold · access · MOT · survey · QC-fail · FAA-closure · sub-delay · other",
  "severity":        "enum: low · medium · high",       // NOT a stoplight chart
  "status":          "enum: open · monitoring · resolved · void",
  "owner":           "responsible party · free text + optional employee_id",
  "operational_impact": "string · ≤ 500 chars · what stops working",
  "notes":           "string · ≤ 4000 chars · markdown allowed",
  "photo_ids":       "array of photo_id · linked via PHOTO_GOVERNANCE",
  "report_ids":      "array of daily_report_id",
  "incident_ids":    "array of incident_id",
  "inspection_ids":  "array of inspection_id",
  "chronology":      "array of { at, by, action, note }",
  "created_by":      "actor_id",
  "created_at":      "tz-aware ISO (TRUST-TIME-1)",
  "updated_at":      "tz-aware ISO",
  "resolved_at":     "tz-aware ISO · nullable",
  "age_days":        "computed · server-side",
}
```

## Severity doctrine

| Level | Meaning | Visual |
|---|---|---|
| `low` | annoyance, not blocking | slate pill |
| `medium` | partial block · workaround exists | amber pill |
| `high` | hard stop · crew idle | rose pill |

Single-red doctrine: only `high` shows red. `medium` is amber.
No gradient stoplight charts.

## Aging doctrine

`age_days` surfaces calmly:
- 0-2 days: no decoration
- 3-7 days: subtle muted "3d" indicator
- 8+ days: bolder "8d" indicator + on the OPS-1 page count of
  stale-but-open constraints (informational, never panic copy)

## API surface (planned)

| Method | Endpoint | Role |
|---|---|---|
| GET | `/api/constraints` | list (capability-gated by portal context) |
| GET | `/api/constraints/:id` | detail |
| POST | `/api/constraints` | FL / PM / Safety + Admin |
| PATCH | `/api/constraints/:id` | owner OR PM/Admin (capability primitive) |
| POST | `/api/constraints/:id/resolve` | owner OR PM/Admin |
| POST | `/api/constraints/:id/photos` | append photo_id |

Capability primitive: `lib/constraintCapabilities.js` (follows
`poCapabilities.js` doctrine VERBATIM).

## Governance hooks

- TRUST-TIME-1 compliant (all timestamps tz-aware).
- Mongo `_id` excluded from every response (existing contract).
- Authority Mismatch Probe scans `constraintCapabilities.js` (new
  primitive registers in baseline).
- Timestamp Doctrine Probe scans the new pages.
- Self-Protection page adds `constraints` stanza to
  `trust_surfaces.json` registry (count of open / aging / resolved).

## Field-first UX commitments

1. Create form fits one mobile screen without scrolling on iPad.
2. Photo attach uses the existing TRUST-1 IDB queue (offline-safe).
3. No "rich text editor" — plain markdown via textarea.
4. Status changes from a single tap on the detail page.
5. "Resolved" action requires a 1-line resolution note (caps at
   500 chars).

## Stop condition

This document is doctrine. Implementation begins on operator
"start V-Prelude wave 1" command (see
`PHASE_V_PRELUDE_IMPLEMENTATION_PLAN.md`).
