# OPS8 restore drill ec1a3776843d

- Archive: `MASCI_complete_backup_2026-08-04_210447Z.zip`
- Outcome: **OK**
- Namespace prefix: `ops8_drill_20260804_220557`
- Duration: 10.747 min
- Records restored: 2599434
- Photos rehydrated: 0

## Axes

| Axis | Result | Detail |
|---|---|---|
| A1_archive_available | PASS | downloaded backups/preview/auto-90d/MASCI_complete_backup_2026-08-04_210447Z.zip |
| A2_archive_integrity | PASS | manifest.total_records=2599434 |
| A3_record_count_parity | PASS | restored=2599434 manifest=2599434 mismatches=0 |
| A4_namespace_isolation | PASS | restored into collection prefix ops8_drill_20260804_220557__* within masci_safety_preview |
| A5_photo_refs_reconcile | PASS | photo_state=PASS |
| A6_photo_rehydration | PASS | uploaded=0 skipped=3451 failed=0 |
