# Governance Memory Integrity — Report

**Phase V-Prelude · Wave 1.1B**
**Status:** 🟢 **MEMORY HARDENED · preview env**
**Date:** 2026-05-28

---

## Memory inventory (post-Wave-1.1B)

| File | Shape | Append-only | Snapshot? | Protective probe |
|---|---|---|---|---|
| `memory/TIMELINE_LOUDNESS_TRENDLINE.json` | list | ✓ | ✓ | trendline_integrity_probe |
| `memory/LOUDNESS_TRENDLINE.json` | list | ✓ | ✓ | trendline_integrity_probe |
| `memory/AUTHORITY_MISMATCH_REPORT.md` | report | report-replaced | — | authority_mismatch_probe |
| `memory/TIMESTAMP_DOCTRINE_PROBE_REPORT.md` | report | report-replaced | — | timestamp_doctrine_probe |
| `memory/AUTHORITY_MISMATCH.json` | report | report-replaced | — | authority_mismatch_probe |
| `memory/DOCTRINE_BASELINE.md` | curated | manual | — | diff_doctrine_baseline |

Two append-only trendlines are now under integrity protection. Report-
style files (regenerated each probe run) are intentionally NOT
protected — they're meant to be overwritten.

## Live snapshot state

### `TIMELINE_LOUDNESS_TRENDLINE.snapshot.json`
```json
{
  "entry_count": 3,
  "checksum_prefix": "<sha256 of first 3 entries>",
  "newest_ts": "2026-05-28T19:31:00.123Z",
  "oldest_ts": "2026-05-28T19:06:13.135Z",
  "refreshed_at": "2026-05-28T19:31:00.500Z",
  "trendline": "TIMELINE_LOUDNESS_TRENDLINE"
}
```

### `LOUDNESS_TRENDLINE.snapshot.json`
```json
{
  "entry_count": 1,
  "checksum_prefix": "6726ae67396d5bc4814e2b94302fd45b2844c9f47c6f9aa4ccf0ce8d3756753b",
  "newest_ts": "2026-05-27T19:13:55.482556Z",
  "oldest_ts": "2026-05-27T19:13:55.482556Z",
  "refreshed_at": "2026-05-28T19:25:55.341Z",
  "trendline": "LOUDNESS_TRENDLINE"
}
```

## Integrity guarantees (verified)

| Guarantee | Status | Verification |
|---|---|---|
| List-shaped root | ✓ | `test_object_shape_rejected`, `test_null_root_rejected` |
| Valid JSON | ✓ | `test_malformed_json_rejected` |
| All entries dicts | ✓ | per-entry isinstance check |
| Required keys present | ✓ | `test_missing_required_key_rejected` |
| Z-suffixed timestamps | ✓ | `test_non_z_timestamp_rejected`, `test_naive_timestamp_rejected`, `test_non_string_timestamp_rejected` |
| Monotonic chronology | ✓ | `test_chronology_violation_caught` |
| No (iter, ts) duplicates | ✓ | `test_duplicate_iteration_timestamp_rejected` |
| Append-only count | ✓ | `test_silent_overwrite_detected` |
| Stable history checksum | ✓ | `test_historical_mutation_detected` |
| Clean run refreshes snapshot | ✓ | `test_snapshot_refreshes_on_clean_run` |
| Corruption preserves snapshot | ✓ | `test_snapshot_not_refreshed_when_violations_present` |
| Operator override works | ✓ | `test_refresh_snapshot_flag_re_baselines_even_with_violations` |
| Live files clean | ✓ | `test_live_trendlines_are_clean` |

## One-time TRUST-TIME-1 conformance

The pre-existing `LOUDNESS_TRENDLINE.json` carried a single entry with
a `+00:00` timestamp suffix from before TRUST-TIME-1 was strict. The
suffix was normalised to `Z` (same UTC moment) so the trendline can
be protected going forward. This is the **only** historical content
change Wave 1.1B made.

Receipts:
- Before: `2026-05-27T19:13:55.482556+00:00`
- After:  `2026-05-27T19:13:55.482556Z`
- Score / portal_average_loudness / iteration: unchanged.

## What "memory hardened" means in practice

Six months from now, if any agent attempts to:
- Replace `TIMELINE_LOUDNESS_TRENDLINE.json` with `{"history": [...]}` →
  caught (shape regression).
- Delete entries to "clean up" the trendline → caught (silent
  overwrite via snapshot count check).
- Edit a historical entry's score "because it looked wrong" → caught
  (historical mutation via prefix-checksum diverge).
- Append an entry with a JavaScript `toISOString()` lacking the Z →
  caught (non-Z timestamp).
- Reorder entries by score / iteration → caught (chronology
  violation).
- Replay a deploy with the same `(iter, timestamp)` → caught
  (duplicate deployment).

…the pre-deploy gate fails. The trendline cannot silently lie.

---

— issued by E1 · 2026-05-28
