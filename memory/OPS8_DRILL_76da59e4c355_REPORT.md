# OPS8 restore drill 76da59e4c355

- Archive: `MASCI_complete_backup_2026-08-06_124031Z.zip`
- Outcome: **OK**
- Namespace prefix: `ops8_drill_20260806_131254`
- Duration: 12.237 min
- Records restored: 2799986
- Photos rehydrated: 0

## Axes

| Axis | Result | Detail |
|---|---|---|
| A1_archive_available | PASS | downloaded backups/preview/auto-90d/MASCI_complete_backup_2026-08-06_124031Z.zip |
| A2_archive_integrity | PASS | manifest.total_records=2799986 |
| A3_record_count_parity | PASS | restored=2799986 manifest=2799986 mismatches=0 |
| A4_namespace_isolation | PASS | restored into collection prefix ops8_drill_20260806_131254__* within masci_safety_preview |
| A5_photo_refs_reconcile | PASS | photo_state=PASS |
| A6_photo_rehydration | PASS | uploaded=0 skipped=3451 failed=0 |
