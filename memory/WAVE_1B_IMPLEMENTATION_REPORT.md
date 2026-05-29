# Wave-1B · Implementation Report

_Phase V.2 · 2026-05-29 · Daily Report UI Enhancement closure._

> **Operator authorization (verbatim):** _"PHASE V.2 · WAVE-1B + 1C
> AUTHORIZATION · Begin Wave-1B and Wave-1C. Enhance the existing
> Daily Report only. Foremen should feel: same report, better
> report."_

---

## 1 · Authorized scope — what shipped

| # | Move | Status |
|---|---|---|
| 1 | Production UI inside the existing Daily Report form | ✅ Shipped |
| 2 | Constraint UI (chip selector) inside the existing Daily Report form | ✅ Shipped |
| 3 | PM exposure tile + aggregator endpoint | ✅ Shipped |
| 4 | NO new form, no new wizard, no new page | ✅ Enforced |

## 2 · Files changed

| File | Lines added | Lines removed | Net |
|---|---|---|---|
| `frontend/src/pages/NewDailyReport.jsx` | +145 | -2 | +143 |
| `frontend/src/components/pm/PmExposureTile.jsx` (new) | +175 | 0 | +175 |
| `backend/routes/daily_reports.py` (exposure aggregator) | +75 | 0 | +75 |
| `backend/tests/odr/test_wave_1bc.py` (new · shared with Wave-1C) | +175 | 0 | +175 |
| **Total** | **+570** | **-2** | **+568** |

## 3 · Production UI surface

Lives inside the **existing** `NewDailyReport.jsx` form. New
`CollapseCard` titled "Production Quantities" placed immediately
after "Activity / Production Log" — same visual grouping, same
RepeatBlock pattern, zero new component.

Per row fields:
- **Description** (text · full width)
- **Quantity** (numeric keypad)
- **Unit** (select · 7-unit closed enum: LF / SY / CY / TON / EA / ACRE / OTHER)
- **Custom Unit Label** (text · only when unit == OTHER)
- **Station / Loc From** (text · placeholder "12+50")
- **Station / Loc To** (text · placeholder "13+00")
- **Notes** (textarea · full width)

Auto-save compatible via the existing `useList` + draft pattern.
Empty state shows "Optional" badge; presence of rows flips to an
emerald "N rows" badge.

## 4 · Constraint UI surface

Lives inside the **existing** `NewDailyReport.jsx` form. New
`CollapseCard` titled "Issues / Delays · Structured" placed after
the production card.

Mobile-first **chip grid** with 11 chips (Weather, Utility, Survey,
Material, Equipment, Trucking, MOT, CEI/Inspection, Owner/Engineer,
Safety, Other). One tap inserts a row of the chosen type and opens
the row for editing. Each row exposes:

- **Type** (select · 11 closed enum) — pre-set by the chip tap
- **Hours Impact** (numeric · optional)
- **Notes** (textarea · full width · placeholder "What happened and where")

Server-side advisory derivation (Wave-1A) sets `may_require_rfi` +
`may_affect_schedule` on submit — UI does not edit those flags.

A 2-line helper above the chips: _"Tap a chip to log a constraint.
One-tap. Signal only — never creates an RFI or schedule entry."_
Calm, factual, non-punitive.

## 5 · PM exposure tile

`/app/frontend/src/components/pm/PmExposureTile.jsx` (new · 175 lines).

| Element | Rendering |
|---|---|
| Header | "PM Signals · Last N days · advisory only" |
| RFI signal count | Large tabular number · slate-50 cell |
| Schedule signal count | Large tabular number · slate-50 cell |
| Top constraint types | Vertical list with counts (top 5) |
| Recent trend | Date · count (top 7 days) |
| Subhead | "Signal only · no actions taken" |

Consumes `GET /api/daily-reports/exposure-signals?days=14` (new ·
admin-gated · PM-scope filtered).

The tile is **drop-in**: it can be embedded inside the existing
PM Hub or anywhere a PM-facing surface wants a calm signal column.
Not wired into a route yet — operator may decide placement.

## 6 · Backend endpoint added

```
GET /api/daily-reports/exposure-signals?days=14
→ 200 OK
{
  "window_days": 14,
  "reports_with_constraints": N,
  "rfi_signal_count":     N,
  "schedule_signal_count":N,
  "top_constraint_types":  [{"constraint_type": "utility", "count": 6}, ...],
  "recent_trend":          [{"date": "2026-05-29", "count": 4}, ...],
  "top_projects":          [{"project_number": "T5860", "count": 8}, ...],
  "doctrine": "PM_EXPOSURE_TILE_CERTIFICATION.md",
  "kind": "signal_only"
}
```

Read-only · zero database mutation · PM-scope filter applied.

## 7 · 9-step contract preserved (Doctrine Lock #1)

| Step | Pre-Wave-1B | Post-Wave-1B |
|---|---|---|
| 1 Project | unchanged | unchanged |
| 2 Crew | unchanged | unchanged |
| 3 Equipment | unchanged | unchanged |
| 4 Production | Activity / Production Log card | + **Production Quantities card** (optional · same step) |
| 5 Photos | unchanged | unchanged |
| 6 Issues / Delays | schedule_delays Y/N + notes | + **Issues / Delays · Structured card** (optional · same step) |
| 7 Safety | unchanged | unchanged |
| 8 Sign | unchanged | unchanged |
| 9 Submit | unchanged | unchanged |

**No 10th step.** Both new cards are optional · default skip
behavior preserves < 3 min stretch goal.

## 8 · Forbidden actions (per directive · all NOT done)

- ❌ NO new ODR form
- ❌ NO Daily Report rename
- ❌ NO pilot
- ❌ NO RFI module
- ❌ NO Schedule module
- ❌ NO P6 integration
- ❌ NO new navigation
- ❌ NO dashboard clutter
- ❌ NO foreman burden increase
- ❌ NO new page · NO new route · NO new wizard

## 9 · Test surface

3 new cases in `tests/odr/test_wave_1bc.py` cover Wave-1B:

| # | Test | Verifies |
|---|---|---|
| 1 | `test_exposure_signals_endpoint_returns_calm_envelope` | Endpoint shape · `kind:signal_only` |
| 2 | `test_exposure_signals_reflects_advisory_derivation` | Counts reflect Wave-1A advisory flags |
| 3 | `test_exposure_signals_clamps_days` | Out-of-range days never crash |

All 🟢.

## 10 · Stop condition

🛑 Wave-1B closure flows into the Wave-1C closure (see sibling
report). HALTED at end of Wave-1B/1C combined; awaiting operator
review before pilot.

---

_End of WAVE_1B_IMPLEMENTATION_REPORT.md._
