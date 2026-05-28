# Trendline Self-Protection Probe — Certification

**Phase V-Prelude · Wave 1.1B**
**Status:** 🟢 **CERTIFIED · preview env**
**Date:** 2026-05-28

---

## Probe identity

| Field | Value |
|---|---|
| Script | `scripts/trendline_integrity_probe.py` |
| Mode | BLOCKING (`--gate` exits 1 on any violation) |
| Runtime | sub-second (16-test suite runs in 0.06 s) |
| Snapshot companions | `*.snapshot.json` next to each protected file |
| Operator surface | NONE (passive protective probe) |
| Pre-deploy hook | `stage_trendline_integrity` in `pre_deploy_check.sh` |

## Protected governance assets

| Asset | Doctrine source | Required keys |
|---|---|---|
| `memory/TIMELINE_LOUDNESS_TRENDLINE.json` | V-Prelude Wave 1.1A | iteration · timestamp · score · aggregate |
| `memory/LOUDNESS_TRENDLINE.json` | IV-BETA.2 | iteration · timestamp · portal_average_loudness |

Future Wave 2+ trendlines add an entry to the `TRENDLINES` table at the
top of the probe.

## 8-axis violation matrix

| # | Violation | Detection mechanism |
|---|---|---|
| 1 | Shape regression | `json.loads` + `isinstance(data, list)` |
| 2 | Malformed JSON | `json.loads` raises `JSONDecodeError` |
| 3 | Missing required key | Per-entry key sweep against `required_keys` |
| 4 | Non-Z timestamp | Regex `Z_ISO_RE` rejects `+00:00`, naive, non-string |
| 5 | Chronology violation | Monotonic non-decreasing check over parsed `datetime` |
| 6 | Duplicate deployment | `(iteration, timestamp)` pair seen twice |
| 7 | Silent overwrite | Snapshot `entry_count` > current count |
| 8 | Historical mutation | Snapshot `checksum_prefix` ≠ live prefix-checksum |

## Snapshot mechanism

For each protected trendline, the probe maintains a sibling file
named `<trendline>.snapshot.json`:

```json
{
  "entry_count": 1,
  "checksum_prefix": "6726ae67…",
  "newest_ts": "2026-05-27T19:13:55.482556Z",
  "oldest_ts": "2026-05-27T19:13:55.482556Z",
  "refreshed_at": "2026-05-28T19:25:55.341Z",
  "trendline": "LOUDNESS_TRENDLINE"
}
```

Doctrine:
- The snapshot is refreshed ONLY when the probe run is clean (or when
  `--refresh-snapshot` is passed for an explicit operator rebaseline).
- A corrupted trendline NEVER auto-updates its snapshot — the anchor
  must remain stable for triage.
- The snapshot is itself an append-friendly format and is included
  in the regression suite to guard against snapshot-format drift.

## Adversarial regression coverage

`backend/tests/test_trendline_integrity_probe.py` — 16 tests:

| Test | Asserts |
|---|---|
| `test_clean_trendline_returns_no_violations` | happy path returns snapshot |
| `test_object_shape_rejected` | dict at root → violation |
| `test_null_root_rejected` | `null` → violation |
| `test_malformed_json_rejected` | parse error → violation |
| `test_missing_required_key_rejected` | absent key → violation |
| `test_non_z_timestamp_rejected` | `+00:00` → violation |
| `test_naive_timestamp_rejected` | no tz → violation |
| `test_non_string_timestamp_rejected` | numeric ts → violation |
| `test_chronology_violation_caught` | older-after-newer → violation |
| `test_duplicate_iteration_timestamp_rejected` | pair seen twice → violation |
| `test_silent_overwrite_detected` | count drops → violation |
| `test_historical_mutation_detected` | prefix checksum diverges → violation |
| `test_snapshot_refreshes_on_clean_run` | clean run rotates anchor |
| `test_snapshot_not_refreshed_when_violations_present` | corruption keeps anchor frozen |
| `test_refresh_snapshot_flag_re_baselines_even_with_violations` | operator override works |
| `test_live_trendlines_are_clean` | live files pass on every PR |

🟢 16/16 green · 0.06 s runtime.

## What the probe is NOT

- ❌ A backup system. (Snapshots are integrity anchors, not data
  copies — they store only checksums + counts + bounding timestamps.)
- ❌ A repair tool. (Corruption is surfaced; remediation is operator
  responsibility — usually via `--refresh-snapshot` after triage.)
- ❌ An operator-facing alert. (Failures surface only inside the
  pre-deploy gate and the test suite.)
- ❌ A drift detector. (`timeline_calmness_probe` does that;
  this one only protects the memory of those measurements.)

---

— certified by E1 · 2026-05-28
