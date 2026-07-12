# Track 27.08 · Smallest Fact-Based Operator Retention Decision

Based on the authenticated production evidence bundle collected on 2026-07-12:

- Total bucket size is ~350.12 GB
- `backups` accounts for ~347.30 GB (~99.19%)
- `VERIFIED_ORPHAN = 0`
- `verified_orphan_bytes = 0`
- `unresolved_refs_present = true`

## Decision

Do **not** approve any object-level cleanup from this certification.

If storage reduction is required, treat it strictly as a **backup-retention review** problem, because the certified evidence shows the bucket is overwhelmingly backup lineage and does **not** show any fact-based deletable orphan population.

## What this decision does NOT do

- does not delete anything
- does not alter retention rules
- does not invent a threshold
- does not certify any object as safe to remove
