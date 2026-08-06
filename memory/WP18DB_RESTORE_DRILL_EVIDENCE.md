# WP-18DB Restore Drill Evidence

## Certified drill

- Drill id: `18f83aaa665a`
- Report: `/app/memory/OPS8_DRILL_18f83aaa665a_REPORT.md`
- Archive: `MASCI_complete_backup_2026-08-06_142739Z.zip`
- Archive key: `backups/preview/auto-90d/MASCI_complete_backup_2026-08-06_142739Z.zip`
- Outcome: `OK`
- Namespace prefix: `ops8_drill_20260806_144726`
- Duration: `11.485 min`
- Records restored: `2,819,024`
- Cleanup complete: `true`

## Axis results

| Axis | Result | Detail |
|---|---|---|
| A1_archive_available | PASS | downloaded `backups/preview/auto-90d/MASCI_complete_backup_2026-08-06_142739Z.zip` |
| A2_archive_integrity | PASS | `manifest.total_records=2819024` |
| A3_record_count_parity | PASS | `restored=2819024 manifest=2819024 mismatches=0` |
| A4_namespace_isolation | PASS | restored into `ops8_drill_20260806_144726__*` inside `masci_safety_preview` |
| A5_photo_refs_reconcile | PASS | `photo_state=PASS` |
| A6_photo_rehydration | PASS | `uploaded=0 skipped=3451 failed=0` |

## Operational meaning

- The latest preview complete archive is restorable.
- Namespace isolation worked; no live canonical collections were overwritten.
- Record-count parity matched the archive manifest exactly.
- Inline photo/document reference degradation did not break restore integrity.

## RTO evidence

- Observed end-to-end isolated restore drill duration: `11.485 minutes`
- This is the strongest current preview-runtime RTO proof captured in-workspace for WP-18DB.

## Conclusion

The latest preview complete archive has fresh isolated restore proof and may be treated as the current authoritative recovery point for preview certification evidence.