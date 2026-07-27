# OPS8 restore drill 3cc22f5f0c04

- Archive: `MASCI_complete_backup_2026-07-25_230328Z.zip`
- Outcome: **FAILED**
- Namespace prefix: `ops8_drill_20260726_225905`
- Duration: 38.3 min
- Records restored: 1902489
- Photos rehydrated: 3206

## Axes

| Axis | Result | Detail |
|---|---|---|
| A1_archive_available | PASS | downloaded backups/auto-90d/MASCI_complete_backup_2026-07-25_230328Z.zip |
| A2_archive_integrity | PASS | manifest.total_records=1902489 |
| A3_record_count_parity | PASS | restored=1902489 manifest=1902489 mismatches=0 |
| A4_namespace_isolation | PASS | restored into collection prefix ops8_drill_20260726_225905__* within masci_safety_preview |
| A5_photo_refs_reconcile | FAIL | photo_state=FAIL |
| A6_photo_rehydration | PASS | uploaded=3206 skipped=0 failed=0 |
