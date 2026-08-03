# WP18C2 · Migration and Compatibility Report

## Scope of Compatibility Work

WP-18C2 introduced governed work-block and work-ledger contracts without rebuilding Daily Reports.

Compatibility work therefore had two parts:

1. **Derived governed linkage where safe evidence already existed**
2. **Version stamping untouched history without fabricating links**

## Runtime Results

Final verified closeout counts:

- Total Daily Reports: **3367**
- Reports already carrying governed version before final compatibility stamp: **644**
- Historical reports compatibility-stamped in final closeout: **2723**
- Reports carrying `work_blocks_version = wp18c2.v1` after closeout: **3367 / 3367**
- Work ledger rows present: **178**
- Crew observations present: **2**

Recorded closeout run record:

- Collection: `project_controls_authority_runs`
- `run_id = wp18c2-backfill-manual-compatibility`
- `mode = compatibility_zero_block_for_untouched_history`
- `ran_at = 2026-08-03T22:09:39.842595+00:00`

## Why the final compatibility stamp used zero-block mode for untouched history

The user’s binding instruction was explicit:

- do not guess
- do not silently normalize
- do not fabricate relationships
- preserve the original record
- create a reviewable governed result

For many historical Daily Reports, the source record did not contain enough deterministic project-pay-item / schedule / work-package evidence to create a safe governed block without inventing relationships.

Therefore WP18C2 applied the smallest safe repair:

- keep the original report intact
- attach the governed contract fields
- attach zero-block summary when no safe link could be derived
- preserve all future operator visibility and downstream compatibility

## Protected-System Preservation

The following systems were preserved rather than rebuilt:

- Daily Reports operator journey
- AI summaries
- photos
- signatures
- attachments
- historical report records
- project identity
- team assignments
- Asset Spine
- payroll variance
- auth / permission infrastructure

## Known Closeout Limitation

The closeout run does **not** claim that every historical report now has a non-empty governed work block.

It **does** claim, factually, that every historical report now carries the WP18C2 governed compatibility contract and that non-empty governed ledger rows were only created where safe evidence already existed.
