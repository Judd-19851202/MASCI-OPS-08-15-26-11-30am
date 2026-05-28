# Observation Ledger — System

**Phase V-Prelude · Observation Window**
**Status:** 🟢 **LIVE · preview env**
**Date:** 2026-05-28
**Authorization:** Operator command "PHASE V-PRELUDE · OBSERVATION LEDGER"
(2026-05-28).
**Scope:** microscopic institutional-memory tool. Zero UI. Zero
dashboards. Zero analytics. Zero scoring.

---

## Purpose

The platform now has an append-only **operator walkthrough ledger**
that captures lived operational judgment during the Wave 1 observation
window. Each entry records what a real reviewer thought of one
walkthrough scenario — in their own words, in exactly four short
answers — without forcing them into a UI or scoring rubric.

This is **institutional trust memory**. Nothing else.

## Components

| Component | Path |
|---|---|
| Capture script | `scripts/walkthrough_capture.py` |
| Ledger | `memory/OBSERVATION_LEDGER.json` |
| Integrity protection | extension of `scripts/trendline_integrity_probe.py` (Wave 1.1B) |
| Regression | `backend/tests/test_walkthrough_capture.py` (12 tests) |

No new probe was created. The ledger is registered as the **third
trendline** in the existing `trendline_integrity_probe.py` inventory,
re-using the Wave 1.1B append-only · Z-suffix · shape · snapshot
machinery.

## Closed scenario enum

```
utility-conflict
FAA-delay
MOT-sequencing
drainage-conflict
survey-discrepancy
QC-failure
owner-delay
field-conflict
custom
```

`custom` is the operator escape hatch for anything that doesn't fit
the eight canonical scenarios.

## Entry shape

```json
{
  "timestamp": "2026-05-28T22:00:32.519Z",
  "scenario": "utility-conflict",
  "reviewer": "JJ",
  "answers": {
    "worked": "sidecar mounted instantly on mobile",
    "friction": "none observed",
    "chronology_helped": "yes — reconstruction in <10s",
    "would_help_real_ops": "yes"
  },
  "freeze_trigger_observed": false,
  "notes": ""
}
```

Every answer is capped at 500 chars. Notes capped at 1000 chars.
Reviewer capped at 80 chars. No PII required. No screenshot required.

## Usage

### Standard interactive capture
```bash
python3 scripts/walkthrough_capture.py \
  --scenario utility-conflict \
  --reviewer JJ
```
The script prompts for four short answers and appends a single ledger
entry. Each prompt is ≤ 500 chars; empty answers are allowed.

### Non-interactive (for tests / CI)
```bash
python3 scripts/walkthrough_capture.py \
  --scenario QC-failure \
  --reviewer CW \
  --non-interactive \
  --worked "calm chronology surface" \
  --friction "none" \
  --chronology-helped "yes" \
  --would-help-real-ops "yes"
```

### Marking a freeze-trigger observation
If the reviewer observed ANY of the 18 freeze triggers during the
walkthrough, pass `--freeze-trigger-observed`. The ledger entry
records the flag; the script also prints a STOP warning.

## Doctrine guarantees

| Rule | Mechanism |
|---|---|
| Append-only | `append_entry()` never mutates / removes prior entries |
| Z-suffixed UTC timestamps | `_utc_iso()` always emits Z form |
| Closed scenario set | `build_entry()` rejects unknown scenarios |
| JSON-list shape | Rejects object / null root before append |
| No duplicate replay | `(timestamp, scenario, reviewer)` tuple uniqueness |
| Integrity-probe-protected | `trendline_integrity_probe.py` covers the ledger |

## What this system is NOT

- ❌ A dashboard.
- ❌ A scoring rubric.
- ❌ An analytics tool.
- ❌ An operator-facing surface.
- ❌ A notification mechanism.
- ❌ A Wave 2 feature in disguise.

It is one Python script and one JSON file.

---

— certified by E1 · V-Prelude Observation Ledger · 2026-05-28
