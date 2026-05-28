# Observation Ledger — Integrity Report

**Phase V-Prelude · Observation Ledger**
**Status:** 🟢 **INTEGRITY PROTECTED · preview env**
**Date:** 2026-05-28

---

## Protection model

The ledger inherits the Wave 1.1B append-only governance memory
machinery without any new infrastructure being added. It joins the
existing `TRENDLINES` inventory inside
`scripts/trendline_integrity_probe.py` as the **third protected
file**:

```python
TRENDLINES = [
    {"name": "TIMELINE_LOUDNESS_TRENDLINE", ...},   # Wave 1.1A
    {"name": "LOUDNESS_TRENDLINE",          ...},   # IV-BETA.2
    {"name": "OBSERVATION_LEDGER",          ...},   # ← this directive
]
```

This gives the ledger the SAME defenses already certified for the
two calmness trendlines:

| Defense | Inherited from |
|---|---|
| List-shape enforcement | Wave 1.1B |
| Malformed JSON detection | Wave 1.1B |
| Required-key enforcement | Wave 1.1B |
| Z-suffix timestamp regex | Wave 1.1B |
| Monotonic chronology check | Wave 1.1B |
| Silent overwrite detection (snapshot count floor) | Wave 1.1B |
| Historical mutation detection (snapshot prefix checksum) | Wave 1.1B |
| Snapshot tampering detection | Wave 1.1B |

## Required-keys specification

The probe registry for the ledger declares:

```python
"required_keys": (
    "timestamp", "scenario", "reviewer",
    "answers", "freeze_trigger_observed",
),
```

Any future entry missing one of these keys → probe violation →
deploy blocked.

## Duplicate detection — composite key

The ledger's duplicate detection uses a **composite identifier** to
preserve the (scenario, reviewer, timestamp) uniqueness contract
without conflating two different reviewers who happened to capture at
the same millisecond:

```python
if id_key == "_dedup_composite":
    ident = f"{entry['scenario']}|{entry['reviewer']}"
```

Combined with the timestamp, the integrity probe rejects any pair
where `(scenario|reviewer, timestamp)` appears twice. The capture
script itself ALSO rejects this in `append_entry()` — two layers of
defense.

## Live integrity sweep

```
== TIMELINE_LOUDNESS_TRENDLINE  · 5 entries · clean
== LOUDNESS_TRENDLINE           · 1 entry  · clean
== OBSERVATION_LEDGER           · 0 entries · clean
→ scanned=3 violations=0 warnings=0
```

The ledger starts at zero entries by design. As real walkthroughs
land, the trendline integrity probe will lock in the floor on the
next clean run.

## Regression coverage

`backend/tests/test_walkthrough_capture.py`:

| Test | What it proves |
|---|---|
| `test_integrity_probe_accepts_live_ledger` | live `OBSERVATION_LEDGER.json` passes the existing probe |
| `test_integrity_probe_rejects_ledger_with_non_z_timestamp` | non-Z timestamp → violation |
| `test_integrity_probe_rejects_ledger_duplicate_composite` | duplicate `(scenario|reviewer, timestamp)` → violation |
| (plus 9 capture-script tests) | per `WALKTHROUGH_CAPTURE_CERTIFICATION.md` |

12 ledger-scoped tests + 16 inherited trendline integrity tests =
**28 governance-memory tests** all green in 0.08 s.

## Operator playbook for ledger anomalies

### "Probe says OBSERVATION_LEDGER missing entries"
→ Someone deleted entries without using `--refresh-snapshot`. Triage
the file. Restore from `git` history if needed. NEVER refresh the
snapshot until the root cause is clear.

### "Probe says historical mutation"
→ A reviewer's answer was edited after the fact. Doctrine forbids
this: corrections take the form of a NEW entry that supersedes the
prior one (operator practice — not a software check).

### "Two reviewers want the same timestamp"
→ Adjust one reviewer's capture by a second. The capture script's
`_utc_iso()` includes millisecond precision so genuine simultaneous
captures will not collide in practice.

### "Ledger reached size N — should we archive?"
→ Not yet. Append-only doctrine + small entry size means the ledger
will stay tiny indefinitely. Revisit only if entry count exceeds
10,000.

---

— certified by E1 · V-Prelude Observation Ledger · 2026-05-28
