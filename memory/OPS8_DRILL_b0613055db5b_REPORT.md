# OPS8 restore drill b0613055db5b

- Archive: `MASCI_complete_backup_2026-07-20_230322Z.zip`
- Outcome: **OK**
- Namespace prefix: `ops8_drill_20260726_045217`
- Duration: 0.146 min
- Records restored: 3428
- Photos rehydrated: 6

## Axes

| Axis | Result | Detail |
|---|---|---|
| A1_archive_available | PASS | downloaded backups/auto-90d/MASCI_complete_backup_2026-07-20_230322Z.zip |
| A2_archive_integrity | PASS | manifest.total_records=3428 |
| A3_record_count_parity | PASS | restored=3428 manifest=3428 mismatches=0 |
| A4_namespace_isolation | PASS | restored into collection prefix ops8_drill_20260726_045217__* within masci_safety_preview |
| A5_photo_refs_reconcile | PASS | unique_refs=6 archive_photos=6 missing=0 |
| A6_photo_rehydration | PASS | uploaded=6 skipped=0 failed=0 |
