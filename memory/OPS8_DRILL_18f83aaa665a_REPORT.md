# OPS8 restore drill 18f83aaa665a

- Archive: `MASCI_complete_backup_2026-08-06_142739Z.zip`
- Outcome: **OK**
- Namespace prefix: `ops8_drill_20260806_144726`
- Duration: 11.485 min
- Records restored: 2819024
- Photos rehydrated: 0

## Axes

| Axis | Result | Detail |
|---|---|---|
| A1_archive_available | PASS | downloaded backups/preview/auto-90d/MASCI_complete_backup_2026-08-06_142739Z.zip |
| A2_archive_integrity | PASS | manifest.total_records=2819024 |
| A3_record_count_parity | PASS | restored=2819024 manifest=2819024 mismatches=0 |
| A4_namespace_isolation | PASS | restored into collection prefix ops8_drill_20260806_144726__* within masci_safety_preview |
| A5_photo_refs_reconcile | PASS | photo_state=PASS |
| A6_photo_rehydration | PASS | uploaded=0 skipped=3451 failed=0 |
