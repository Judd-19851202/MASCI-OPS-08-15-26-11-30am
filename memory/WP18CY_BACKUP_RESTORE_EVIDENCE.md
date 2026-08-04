# WP18CY Backup Restore Evidence

## Latest Proven Preview Restore Drill
- `drill_runs.state=done` latest row
- Archive: `MASCI_complete_backup_2026-07-31_021836Z.zip`
- Outcome: `ok`
- Duration: `10.958 min`
- Checksum validated: `true`
- Cleanup complete: `true`

## Axis Results
- `A1_archive_available` = PASS
- `A2_archive_integrity` = PASS
- `A3_record_count_parity` = PASS (`restored=2332127`, `manifest=2332127`, `mismatches=0`)
- `A4_namespace_isolation` = PASS (restored into isolated drill namespace)
- `A5_photo_refs_reconcile` = PASS
- `A6_photo_rehydration` = PASS (`uploaded=0 skipped=3363 failed=0`)

## Sidecar Evidence
- Manifest key present: `backups/preview/auto-90d/manifests/MASCI_complete_backup_2026-07-31_021836Z.zip.manifest.json`
- Checksum key present: `backups/preview/auto-90d/checksums/MASCI_complete_backup_2026-07-31_021836Z.zip.sha256`
- Manifest database identity: `masci_safety_preview`
- Manifest generated at: `2026-07-31T03:12:08.688098+00:00`

## Limitation
- This is preview restore evidence, not direct production restore evidence.
