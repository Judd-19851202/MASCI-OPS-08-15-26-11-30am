# Weather Impact Cleanup — Certification

_Phase V.2 · Daily Report Field-Logic · 2026-05-29._

## 1 · Issue

Section 03 of the Daily Report had two questions that overlapped operationally:

| Question | Source of truth |
|---|---|
| **Weather Impact Today?** | Triggered the legacy "Detail any 'Yes' answers" free-text amber box. |
| **Delays / Extra Work Today?** | Wave-1B structured Delays / Extra Work card (already supports a `Weather` chip). |

Result: foremen were asked to describe weather impact in narrative form AND in the structured card, producing duplicate entry and a muddy workflow.

## 2 · Fix

Three surfaces touched · all in `frontend/src/pages/NewDailyReport.jsx`.

### 2.1 · Legacy detail-box trigger
```diff
- (data.safety_incidents_today === "Yes" ||
-  data.injuries_reported === "Yes" ||
-  data.weather_impact === "Yes")
+ (data.safety_incidents_today === "Yes" ||
+  data.injuries_reported === "Yes")
```
Weather YES no longer surfaces the legacy free-text box. Accidents and injuries continue to use it (the operator confirmed these still need their narrative box).

Placeholder copy updated: _"Describe accidents or injuries…"_.

### 2.2 · validate() — Weather gate added
```js
if (
  data.weather_impact === "Yes" &&
  !(data.constraints || []).some(
    (r) => (r?.constraint_type || "").toLowerCase() === "weather"
  )
) {
  toast.error(
    "Add a Delay / Extra Work row with cause = Weather before submitting"
  );
  return false;
}
```
Runs immediately after the existing Delays gate. The merged predicate honors all 4 cases in the directive.

### 2.3 · Delays card — merged-gate status pill + attentionOpen
The CollapseCard now reads two derived flags:

```js
const hasWeatherRow = rows.some(
  (r) => (r?.constraint_type || "").toLowerCase() === "weather"
);
const delaysGateUnmet =
  data.schedule_delays === "Yes" && rows.length === 0;
const weatherGateUnmet =
  data.weather_impact === "Yes" && !hasWeatherRow;
const gateUnmet = delaysGateUnmet || weatherGateUnmet;
```

Status pill precedence (most-specific wins):

| State | Pill | Tone |
|---|---|---|
| At least one row AND no gate unmet | "{N} logged" | emerald |
| Weather YES + no Weather row (any row count) | "Add a row with cause = Weather (required)" | amber |
| Delays YES + 0 rows | "Add at least one delay (required)" | amber |
| Otherwise | "No delays today" | slate |

`attentionOpen` auto-expands the card after a blocked submit when either gate is unmet.

## 3 · Behavior matrix (verbatim against the directive)

| Section 03 selections | Required row | Submit blocked when missing | Legacy detail box | Live-verified |
|---|---|---|---|---|
| Weather YES · Delays NO | ≥ 1 row with `constraint_type === "weather"` | ✅ | ❌ hidden | ✅ A |
| Weather YES · Weather row present | satisfied | submit ok | ❌ hidden | ✅ B |
| Weather NO · Delays NO | none | submit ok | ❌ hidden | ✅ C |
| Weather YES + Delays YES + 0 rows | ≥ 1 weather row | ✅ blocked on weather first | ❌ hidden | ✅ D |
| Weather YES + Delays YES + Utility row only | ≥ 1 weather row (delays gate already met) | ✅ still blocked on weather | ❌ hidden | ✅ E |
| Weather YES + Delays YES + Weather row + Utility row | both gates met | submit ok | ❌ hidden | ✅ F |
| Accidents YES (any path) | unchanged | unchanged | ✅ legacy free-text box | unchanged |
| Injuries YES (any path) | unchanged | unchanged | ✅ legacy free-text box | unchanged |

## 4 · Doctrine compliance

- ✅ **Signal-only.** No RFI, no schedule entry, no notification, no auto-row creation. The user always chooses which chip to insert. The validator only blocks submit; the foreman drives the row.
- ✅ **Doctrine Lock #1 (Simplicity).** Foreman 9-step contract intact. The merged-gate logic surfaces one clear pill, not a wall of warnings.
- ✅ **Doctrine Lock #2 (Inheritance).** Reused `CollapseCard.attentionOpen`, the existing Weather chip, `useList`, `RepeatBlock`, `toast.error`. No new components, no new deps.
- ✅ **Backend stability.** `ConstraintRow`, `ConstraintType`, `weather_impact`, `schedule_delays`, `incident_notes`, advisory derivation — all preserved. **89 / 89 ODR tests still pass.**
- ✅ **Historical compatibility.** Existing reports with weather narrative in `incident_notes` continue to render the box on the PDF / projector. No data mutation. No deletion.

## 5 · What stayed off-limits

- ❌ NO new endpoint, no new collection, no new advisory flag derivation.
- ❌ NO mutation of existing Weather narrative on legacy reports.
- ❌ NO pilot · NO RFI · NO Schedule · NO P6 · NO PM Hub wiring · NO approval/rejection workflow · NO role-standardization beyond the prior pass.

## 6 · Verification

| Probe | Result |
|---|---|
| Weather YES alone → no legacy box · amber Weather-required pill | 🟢 |
| Weather YES + Weather row → emerald "N logged" | 🟢 |
| Weather NO → no Weather requirement | 🟢 |
| Both YES + Utility row only → still blocked on Weather gate | 🟢 |
| Both YES + Weather row + Utility row → submit allowed | 🟢 |
| Accidents YES / Injuries YES → legacy detail box still appears | 🟢 |
| Existing reports render legacy weather text | 🟢 (no schema change) |
| 89 / 89 ODR tests | 🟢 |
| ESLint clean | 🟢 |

## 7 · Stop condition

🛑 **HALTED after this cleanup as directed.**

- ❌ NO Pilot · NO RFI · NO Schedule · NO P6
- ❌ NO PM Hub wiring (PM Exposure Tile remains a drop-in)
- ❌ NO new role standardization beyond the prior pass
- ❌ NO approval / rejection workflow implementation
- ✅ Awaiting **Internal Superintendent Validation Review**.

---

_End of WEATHER_IMPACT_CLEANUP_CERTIFICATION.md._
