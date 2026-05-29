# Production UI · Certification

_Phase V.2 · Wave-1B · 2026-05-29._

> Structured production rows surfaced inside the existing Daily
> Report form. **No new form. No new page. No new wizard. Same step
> 4 of the existing 9-step flow.**

---

## 1 · UI placement

`/app/frontend/src/pages/NewDailyReport.jsx` — new `CollapseCard`
titled **"Production Quantities"** inserted immediately after the
existing **"Activity / Production Log"** card. Same visual grouping,
same RepeatBlock pattern, same auto-save semantics.

`data-testid="dr-production"` for governance probes.

## 2 · Per-row fields (operator-approved)

| Field | Input shape | Default |
|---|---|---|
| Description | text · full width · placeholder "e.g. RCP install, Type S-III mat, MH set" | empty |
| Quantity | numeric | empty (keypad opens on focus) |
| Unit | select · 7-unit closed enum (`LF`, `SY`, `CY`, `TON`, `EA`, `ACRE`, `OTHER`) | `OTHER` |
| Custom Unit Label | text · only meaningful when unit == OTHER | empty |
| Station / Loc From | text · placeholder "12+50" | empty |
| Station / Loc To | text · placeholder "13+00" | empty |
| Notes | textarea · full width | empty |

Each row carries an auto-generated `row_id` (uuid) once submitted.

## 3 · Mobile-friendly behavior

- **Large touch targets** — inherits the existing `inputCls` padding
  from `NewDailyReport.jsx` (h-12 / px-4 / text-base).
- **Add Row button** — RepeatBlock's `+ Add` affordance · single tap
- **Repeat as needed** — no upper limit · auto-save fires on every keystroke
- **Auto-save compatible** — uses `useList` setter pattern same as crews / equipment / materials

## 4 · Closed enum enforcement (defense in depth)

- **Frontend select** — only 7 valid options rendered (operator
  cannot pick an invalid string)
- **Backend Pydantic Literal** — invalid units rejected at POST with
  HTTP 422 (Wave-1A test `test_production_unit_closed_enum_rejected` 🟢)

## 5 · Backward compatibility

Existing Daily Reports without a `production` field render as
"Optional" with zero rows — no migration required. The legacy
free-text `activities[]` card is untouched and continues to work.

## 6 · Field simplicity verdict (Doctrine Lock #1)

| Test | Answer |
|---|---|
| Can a foreman complete this in mud / gloves / 5:30 PM? | YES · select + numeric keypad + textarea · ~15–20 s per row |
| Time-to-complete impact | +15–30 s per row · 1–3 rows typical · still inside the 5-min target |
| Forbidden patterns introduced | None |
| 9-step contract preserved | YES · production card sits in step 4 |
| Required-field count introduced | 0 (all fields optional) |

PASS · production UI ships.

## 7 · Frontend lint

`/app/frontend/src/pages/NewDailyReport.jsx` · ESLint **0 issues**.

## 8 · Operator-facing one-liner

> **Foremen tap "+ Production", pick a unit, enter the qty, and
> move on.** The structured data lands in the backend automatically.
> The form looks and feels the same as it always has.

---

_End of PRODUCTION_UI_CERTIFICATION.md._
