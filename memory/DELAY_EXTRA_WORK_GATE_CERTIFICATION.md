# Delay / Extra Work Gate — Certification

_Phase V.2 · Daily Report Field-Logic Refinement · Fix 3 of 4 · 2026-05-29._

## 1 · Issue

Section 03 of the Daily Report exposed a YES/NO question reading
**"Schedule Delays Today?"**. Two problems:

1. The label spoke software / scheduling jargon, not construction
   language ("delays · impacts · extra work · changed conditions").
2. When YES was chosen, nothing operational happened — the
   foreman could still ship a report without any structured delay
   row, leaving PM intelligence (the Wave-1B advisory flags +
   PM Exposure Tile aggregator) blind to the actual cause.

## 2 · Fix

### 2.1 · Label

```diff
- {t("Schedule Delays Today?")}
+ {t("Delays / Extra Work Today?")}
```

The underlying field name **`schedule_delays`** is preserved
server-side (no schema change · existing reports render unchanged).

### 2.2 · Submit-gate

`validate()` in `NewDailyReport.jsx`:

```js
if (
  data.schedule_delays === "Yes" &&
  (data.constraints?.length || 0) === 0
) {
  toast.error(
    "Add at least one Delay / Extra Work row (Type + Notes) before submitting"
  );
  return false;
}
```

- Triggers BEFORE the photo / signature checks so the foreman sees
  the structured-row prompt first.
- Returns the existing `setAttemptedSubmit(true)` codepath so the
  Smart Operational Disclosure cards open automatically.

### 2.3 · CollapseCard attentionOpen + status pill

```jsx
<CollapseCard
  title={t("Delays / Extra Work")}
  testId="dr-constraints"
  attentionOpen={
    attemptedSubmit &&
    data.schedule_delays === "Yes" &&
    (data.constraints?.length || 0) === 0
  }
  statusLabel={
    (data.constraints?.length || 0) > 0
      ? `${data.constraints.length} ${t("logged")}`
      : data.schedule_delays === "Yes"
        ? t("Add at least one delay (required)")
        : t("No delays today")
  }
  statusTone={
    (data.constraints?.length || 0) > 0
      ? "emerald"
      : data.schedule_delays === "Yes"
        ? "amber"
        : "slate"
  }
>
```

| State | Pill | Tone | Card |
|---|---|---|---|
| YES + 0 rows + submit not attempted | "Add at least one delay (required)" | amber | collapsed (user can still expand) |
| YES + 0 rows + submit attempted | "Add at least one delay (required)" | amber | **auto-expanded** via `attentionOpen` |
| YES + ≥ 1 row | "N logged" | emerald | user-controlled |
| NO + 0 rows | "No delays today" | slate | collapsed |
| NO + ≥ 1 row (rare · user changed mind) | "N logged" | emerald | user-controlled |

## 3 · What the gate is NOT

| Forbidden by operator directive | Honored |
|---|---|
| Create an RFI when YES is chosen | ✅ never |
| Create a schedule entry | ✅ never |
| Notify anyone | ✅ never |
| Open a "ticket" workflow | ✅ never |
| Charge anyone | ✅ never |

This stays **signal-only**. The advisory flags already derived
server-side (`may_require_rfi`, `may_affect_schedule`) are the only
downstream artifact and they remain informational.

## 4 · NO path preserved (operator-mandated)

> _"If user selects NO: Delays / Extra Work section remains
> optional. No delay row required. Existing behavior remains
> simple."_

The validate-gate predicate is anchored to
`schedule_delays === "Yes"` only. Selecting NO (or leaving it
blank) does not require any delay row. The CollapseCard reverts
to the calm "No delays today" pill.

## 5 · Existing behavior preserved

- The legacy narrative `schedule_delays_notes` textarea (when
  YES surfaces the broader stop-the-line block) remains in place.
- Existing reports keep their `schedule_delays` value verbatim
  (Yes / No / blank).
- The legacy free-text path is the canonical fallback for
  historical-record rendering.

## 6 · Verification

| Probe | Result |
|---|---|
| Section 03 label = "Delays / Extra Work Today?" | 🟢 |
| Old label gone | 🟢 |
| YES + 0 rows → "Add at least one delay (required)" amber pill | 🟢 |
| YES + 0 rows + submit → toast + form stays put (no navigation) | 🟢 |
| YES + 1 delay row → emerald "1 logged" pill | 🟢 |
| NO + 0 rows → slate "No delays today" · submission permitted | 🟢 |
| 89 / 89 ODR backend tests | 🟢 |

## 7 · Stop condition

🛑 No further gating work. Photo-min / signature gates already
existed and are unchanged. Constraint-row gating is the ONLY new
submit gate from this refinement pass.

---

_End of DELAY_EXTRA_WORK_GATE_CERTIFICATION.md._
