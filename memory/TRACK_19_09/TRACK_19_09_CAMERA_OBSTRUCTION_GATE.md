# Track 19.09 · Camera Obstruction Gate — Design & Behaviour Specification

Applies to Equipment Pre-Op AND DVIR. Same doctrine on both forms.

## Doctrine

Camera obstruction is safety-critical. Operating a machine with a blocked camera is functionally the same as operating without a working brake indicator: the vehicle is safety-compromised. Therefore:

1. Every operator must **answer the camera-system question** before submit.
2. If the machine has cameras, the operator must **confirm those cameras are clear**.
3. If the cameras are NOT clear, **submit is hard-blocked** until the operator clears the obstruction. There is no override.

## Flow

```
STEP 1  · "Does this <equipment|truck> have a camera system?"
         ┌── Yes  ── go to STEP 2
         ├── No   ── record answer, allow submit path to continue
         └── Not sure  ── record answer, allow submit path to continue

STEP 2 (only if STEP 1 = Yes) · "Are the front-facing and interior-facing
         cameras free and clear of obstructions?"
         ┌── Yes — clear    ── record answer, allow submit to continue
         └── No — obstruction present
             ┌── show hard-block panel (red border, bold copy)
             ├── require operator to CLEAR the obstruction physically
             ├── operator may optionally document the obstruction
             │   in the text area (captured for shop record)
             └── submit stays blocked; operator must return to the
                 gate and flip STEP 2 to "Yes — clear" once cameras
                 are actually clear
```

## Persisted payload

Three additive keys land in the inspection record. All three are optional in the backend model (free-form Dict on both `equipment_inspections` and `fleet_audit`), so this is a superset — no schema break.

| Field | Values | Notes |
| --- | --- | --- |
| `camera_system_present` | `"yes"` / `"no"` / `"unsure"` / `""` | Required non-empty at submit |
| `camera_obstructions_clear` | `"yes"` / `"no"` / `""` | Only relevant when `camera_system_present === "yes"` |
| `camera_obstruction_note` | free text | Cleared when the operator flips to `"yes — clear"` |

Downstream:
* PDF template renders new fields when present (existing template already iterates over payload dict).
* Email routing unchanged.
* Fleet OOS / shop routing unchanged — the gate is a UI hard-block; if the operator physically clears the obstruction it never becomes a defect. If they choose to leave it, they cannot submit at all.

## Why a hard block, not a fail-cascade branch?

Per the user's Phase 3 decision (option **i**): camera obstruction is treated as a *pre-submit gate*, not as a defect. Rationale:
* An obstructed camera is trivially fixable in the field (wipe the lens, remove the tape).
* Making it a defect would consume shop bandwidth on a five-second physical action.
* The hard-block wording ("Clear the obstruction before operating") is direct enough that a foreman corrects the issue in seconds.

If a camera obstruction cannot be cleared in the field (broken housing, cracked lens), the operator's next action is:
* Mark the appropriate DVIR / Pre-Op checklist item as FAIL (which IS a defect — fail-cascade fires).
* The camera gate then becomes moot because the vehicle is OOS anyway.

## Bilingual coverage

Every new English string has a Spanish translation in `frontend/src/lib/i18n.js`. Verified by `test_spanish_translation_exists[…]` (25 assertions covering the new strings).

## Test-IDs

Equipment Pre-Op:
* `equipment-camera-gate` (container)
* `camera-system-yes` / `camera-system-no` / `camera-system-unsure`
* `equipment-camera-followup` (only when `yes`)
* `camera-clear-yes` / `camera-clear-no`
* `camera-obstruction-block` (only when `no — obstruction present`)
* `camera-obstruction-note`

DVIR:
* `dvir-camera-gate` (container)
* `dvir-camera-system-yes` / `dvir-camera-system-no` / `dvir-camera-system-unsure`
* `dvir-camera-followup` (only when `yes`)
* `dvir-camera-clear-yes` / `dvir-camera-clear-no`
* `dvir-camera-obstruction-block` (only when `no — obstruction present`)
* `dvir-camera-obstruction-note`

## Success criteria (all met)

* Camera question appears on both forms ✅
* Progressive disclosure — follow-up only renders on Yes ✅
* Hard-block message present + red styling ✅
* Submit rejects when unanswered or obstructed ✅
* Bilingual parity — 25 lock assertions ✅
* Zero schema drift ✅
* Zero route drift ✅
* Existing PASS/FAIL/N-A behaviour untouched ✅
* Historical records untouched ✅
