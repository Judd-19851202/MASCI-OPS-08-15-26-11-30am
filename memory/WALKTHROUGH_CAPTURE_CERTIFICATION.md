# Walkthrough Capture — Certification

**Phase V-Prelude · Observation Ledger**
**Status:** 🟢 **CERTIFIED · preview env**
**Date:** 2026-05-28

---

## Script identity

| Field | Value |
|---|---|
| Script | `scripts/walkthrough_capture.py` |
| Mode | manual invocation (interactive or `--non-interactive` for tests) |
| Output target | `/app/memory/OBSERVATION_LEDGER.json` (append-only) |
| Operator surface | NONE (CLI only) |
| Integrity protection | `trendline_integrity_probe.py` (Wave 1.1B reuse) |
| Pre-deploy gate stage | already covered by `stage_trendline_integrity` |
| Footprint | ~250 LOC pure Python · no dependencies beyond stdlib |

## Validation contract

The script's `build_entry()` and `append_entry()` functions enforce:

| Rule | Check | Test |
|---|---|---|
| Scenario in closed enum | `if scenario not in SCENARIOS` → `ValueError` | `test_build_entry_invalid_scenario_rejected` |
| Reviewer non-empty | `if not reviewer.strip()` → `ValueError` | `test_build_entry_requires_reviewer` |
| All 4 answers present | per-key sweep against PROMPTS | `test_build_entry_requires_all_four_answers` |
| Answer ≤ 500 chars | `[:MAX_ANSWER_LEN]` truncation | `test_build_entry_truncates_long_answers` |
| `freeze_trigger_observed` is bool | `bool(...)` coercion | `test_build_entry_freeze_trigger_coerced_to_bool` |
| Timestamp Z-suffix | `_utc_iso()` returns canonical Z form | `test_build_entry_valid` regex match |
| List-shaped ledger | rejects object / null root | `test_append_rejects_object_shaped_ledger` |
| No duplicate replay | `(timestamp, scenario, reviewer)` tuple uniqueness | `test_append_rejects_duplicate_tuple` |
| Creates ledger if missing | initialises with `[]` | `test_append_creates_ledger_if_missing` |

12/12 regression tests pass in **< 0.1 s**.

## Side-effect surface

The script writes to EXACTLY one file: `OBSERVATION_LEDGER.json`. It
never:
- Reads or writes Mongo.
- Calls any backend route.
- Renders any UI.
- Triggers any notification.
- Mutates any other governance file.

If `append_entry()` fails (shape error, duplicate, etc.) the ledger
file is **not touched**.

## CLI reference

```
python3 scripts/walkthrough_capture.py \
  --scenario <utility-conflict|FAA-delay|MOT-sequencing|drainage-conflict
              |survey-discrepancy|QC-failure|owner-delay|field-conflict
              |custom> \
  --reviewer <initials or short tag, ≤80 chars> \
  [--freeze-trigger-observed] \
  [--notes "optional ≤1000 char free-text"] \
  [--non-interactive
    --worked "..."
    --friction "..."
    --chronology-helped "..."
    --would-help-real-ops "..."]
```

Exit codes:
- `0` — entry appended.
- `2` — validation error (scenario / reviewer / answers).
- `3` — append error (duplicate / malformed ledger).

## What this script is NOT

- ❌ A query tool. (Reading the ledger is a one-liner with `jq` or
  Python — no read endpoint exists.)
- ❌ A reporting tool. (Aggregation happens nowhere; the ledger is
  raw verbatim memory.)
- ❌ A protocol enforcer. (It does not require operators to capture
  every walkthrough — capture is opt-in.)
- ❌ A Wave 2 search precursor.

---

— certified by E1 · V-Prelude Observation Ledger · 2026-05-28
