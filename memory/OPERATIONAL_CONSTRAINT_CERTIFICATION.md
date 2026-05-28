# Operational Constraints — Certification

**Phase V-Prelude · Wave 1 · Substrate**
**Status:** 🟢 **CERTIFIED · preview env**
**Date:** 2026-05-28

---

## Doctrine reference

- `/app/memory/OPERATIONAL_CONSTRAINT_FOUNDATION.md`
- `/app/memory/OPERATIONAL_LINKING_RULES.md`

## Files

| File | Purpose |
|---|---|
| `backend/routes/operational_constraints.py` | API surface + Pydantic models + index ensure |
| `frontend/src/lib/constraintCapabilities.js` | Portal-context-scoped capability bundle |
| `frontend/src/lib/operationalApi.js` | Thin axios client |
| `frontend/src/pages/Constraints.jsx` | List view |
| `frontend/src/pages/NewConstraint.jsx` | Create form |
| `frontend/src/pages/ConstraintDetail.jsx` | Detail + chronology + resolve |
| `frontend/src/components/operational/SeverityPill.jsx` | Single-red doctrine pill |
| `backend/tests/test_v_prelude_wave1_substrate.py` | 19 regression tests |

## API surface (live in preview)

```
POST   /api/constraints
GET    /api/constraints?project_id=...&status=...&severity=...&discipline=...
GET    /api/constraints/:id
PATCH  /api/constraints/:id
POST   /api/constraints/:id/resolve            { resolution_note }
POST   /api/constraints/:id/chronology         { action, note }
```

Returns Pydantic models — no Mongo `_id` ever leaks.

## Closed enums

| Field | Members |
|---|---|
| `discipline` | utilities · access · MOT · survey · QC · FAA · subcontractor · other |
| `kind` | utility-conflict · owner-hold · access · MOT · survey · QC-fail · FAA-closure · sub-delay · other |
| `severity` | low · medium · high (high renders red — single-red doctrine) |
| `status` | open · monitoring · resolved · void |

## Chronology

Every state change appends a row to the constraint's `chronology` list.
First row is `created`. Resolution appends `resolved`. Operator notes
append via `POST /:id/chronology`. **History is never overwritten.**

## Visual doctrine

- Calm, text-first list. No charts, no gantt, no badges-of-engagement.
- `SeverityPill` is the ONLY coloured surface (high = rose, medium =
  amber, low = slate).
- Aging surfaces as `3d` / `8d` — calm, never panic copy.
- Mobile-safe: filters and form collapse to single column < 640 px.

## Capability matrix

| Context | view | create | edit | resolve | chrono note | link photo |
|---|---|---|---|---|---|---|
| Admin | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| PM | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Safety | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Field Leadership | ✓ | ✓ | — | — | ✓ | ✓ |
| HR | ✓ | — | — | — | — | — |
| Unknown | ✓ | — | — | — | — | — |

Backend is the source of truth — the capability layer only decides
what to RENDER. The backend role-check (`_can_write`) still gates
mutations server-side.

## Test result

19/19 passing — see `WAVE1_IMPLEMENTATION_SUMMARY.md`.

— certified by E1 · 2026-05-28
