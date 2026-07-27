# OPS8 restore drill cb4a78c91997

- Archive: `MASCI_complete_backup_2026-07-25_230328Z.zip`
- Outcome: **OK**
- Namespace prefix: `ops8_drill_20260726_235949`
- Duration: 41.035 min
- Records restored: 1902489
- Photos rehydrated: 3206

## Axes

| Axis | Result | Detail |
|---|---|---|
| A1_archive_available | PASS | downloaded backups/auto-90d/MASCI_complete_backup_2026-07-25_230328Z.zip |
| A2_archive_integrity | PASS | manifest.total_records=1902489 |
| A3_record_count_parity | PASS | restored=1902489 manifest=1902489 mismatches=0 |
| A4_namespace_isolation | PASS | restored into collection prefix ops8_drill_20260726_235949__* within masci_safety_preview |
| A5_photo_refs_reconcile | PASS | photo_state=PASS |
| A6_photo_rehydration | PASS | uploaded=3206 skipped=0 failed=0 |
