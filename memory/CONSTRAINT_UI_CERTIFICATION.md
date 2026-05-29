# Constraint UI · Certification

_Phase V.2 · Wave-1B · 2026-05-29._

> Structured constraint rows surfaced inside the existing Daily
> Report form via a **chip selector**. One-tap. Calm. Signal only.

---

## 1 · UI placement

`/app/frontend/src/pages/NewDailyReport.jsx` — new `CollapseCard`
titled **"Issues / Delays · Structured"** inserted after the
production card. Same step 6 of the existing 9-step flow.

`data-testid="dr-constraints"` for governance probes.

## 2 · Chip grid (one-tap selection · 11 types)

| Chip label | constraint_type |
|---|---|
| Weather | `weather` |
| Utility | `utility` |
| Survey | `survey` |
| Material | `material` |
| Equipment | `equipment` |
| Trucking | `trucking` |
| MOT | `mot` |
| CEI / Inspection | `cei_inspection` |
| Owner / Engineer | `owner_engineer` |
| Safety | `safety` |
| Other | `other` |

Each chip is a `data-testid="constraint-chip-<type>"` button.
Tapping a chip:

1. Inserts a new `ConstraintRow` of the chosen type
2. Pre-fills the row's Type select with that value
3. Opens the row for hours/notes editing

## 3 · Per-row fields after chip tap

| Field | Input shape | Required? |
|---|---|---|
| Type | select · 11 closed enum (pre-set by chip tap) | yes (defaulted) |
| Hours Impact | numeric · placeholder "0.0" | no |
| Notes | textarea · full width · placeholder "What happened and where" | no |

Server-side advisory flags (`may_require_rfi`, `may_affect_schedule`)
are derived at submit · UI never exposes them on the foreman path.

## 4 · Mobile-first contract

- **11 chips · single horizontal row** (`flex-wrap`) — every chip
  reachable with thumb
- **Border radius `rounded-full`** for chip target affordance
- **Hover state** lifts the border (`hover:border-slate-400`) — calm
- **Transition `transition-colors`** — no animation that draws eye
- **One-tap add** — no modal, no dialog, no second-step confirmation

## 5 · Calm copy contract

Helper line above the chips:

> _"Tap a chip to log a constraint. One-tap. Signal only — never
> creates an RFI or schedule entry."_

Status badge on the section header:
- 0 rows: "No issues today" (slate)
- ≥1 rows: "N logged" (emerald)

No alarm. No urgency. No exclamation marks. No red.

## 6 · Closed enum enforcement (defense in depth)

- **Frontend chip set** — only 11 valid types rendered
- **Frontend select on each row** — only 11 valid options
- **Backend Pydantic Literal** — invalid types rejected at POST with
  HTTP 422 (Wave-1A test `test_constraint_type_closed_enum_rejected` 🟢)

## 7 · Advisory flag derivation (Wave-1A · server-side)

| constraint_type | may_require_rfi | may_affect_schedule |
|---|---|---|
| `weather` | ❌ | ✅ |
| `utility` | ✅ | ✅ |
| `survey` | ✅ | ❌ |
| `material` | ❌ | ✅ |
| `equipment` | ❌ | ✅ |
| `trucking` | ❌ | ❌ |
| `mot` | ❌ | ✅ |
| `cei_inspection` | ✅ | ❌ |
| `owner_engineer` | ✅ | ❌ |
| `safety` | ❌ | ❌ |
| `other` | ❌ | ❌ |

The flags surface in the PM Exposure Tile (see
`PM_EXPOSURE_TILE_CERTIFICATION.md`) — never on the foreman path.

## 8 · Backward compatibility

Existing Daily Reports without a `constraints` field render as "No
issues today" (zero rows). The legacy `schedule_delays: Y/N` string
remains and is unchanged. Both coexist.

## 9 · Field simplicity verdict (Doctrine Lock #1)

| Test | Answer |
|---|---|
| Can a foreman complete this in mud / gloves / 5:30 PM? | YES · single chip tap · ~10 s per constraint |
| Time-to-complete impact | +10–15 s per constraint · 0–1 typical · still inside the 5-min target |
| Forbidden patterns introduced | None |
| 9-step contract preserved | YES · constraint card sits in step 6 |
| Required-field count introduced | 0 (all rows optional) |
| Punitive copy introduced | NONE (helper line is calm + factual) |

PASS · constraint UI ships.

## 10 · Operator-facing one-liner

> **A foreman taps "Utility," types "FPL conflict at sta 11+25,"
> and moves on.** The system knows that's a potential RFI candidate
> and that it might affect the schedule. The PM sees the signal.
> Nobody is forced to act. Everyone is informed.

---

_End of CONSTRAINT_UI_CERTIFICATION.md._
