# OPS8 restore drill 6a5388ee4a68

- Archive: `MASCI_complete_backup_2026-07-31_021836Z.zip`
- Outcome: **FAILED**
- Namespace prefix: `ops8_drill_20260731_122910`
- Duration: 10.918 min
- Records restored: 2332127
- Photos rehydrated: 0

## Axes

| Axis | Result | Detail |
|---|---|---|
| A1_archive_available | PASS | downloaded backups/preview/auto-90d/MASCI_complete_backup_2026-07-31_021836Z.zip |
| A2_archive_integrity | PASS | manifest.total_records=2332127 |
| A3_record_count_parity | PASS | restored=2332127 manifest=2332127 mismatches=0 |
| A4_namespace_isolation | PASS | restored into collection prefix ops8_drill_20260731_122910__* within masci_safety_preview |
| A5_photo_refs_reconcile | FAIL | photo_state=FAIL |
| A6_photo_rehydration | PASS | uploaded=0 skipped=3363 failed=0 |
