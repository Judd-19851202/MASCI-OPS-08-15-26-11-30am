# WP18CY.2 Complete-R2 Repair and Restore Proof

## Fresh backup proof (production)
- Latest valid recoverable artifact:
  - `MASCI_complete_backup_2026-08-04_150445Z.zip`
  - object key: `backups/production/auto-90d/MASCI_complete_backup_2026-08-04_150445Z.zip`
  - authoritative recovery point: `2026-08-04T15:18:21.082460+00:00`
  - archive size: `1467462216 bytes`
- `/api/admin/backups-complete-r2-state` lineage truth:
  - `integrity_status=PASS`
  - `completeness_status=COMPLETE`
  - `availability_status=AVAILABLE`
  - `valid_recoverable=true`
  - `freshness_age_minutes≈29.46`

## Integrity proof (production)
- `/api/admin/backups/integrity-check` returned:
  - `ok=true`
  - `integrity_result=PASS`
  - `classification=PASS`
  - `classification_reason_code=verification_pass`
  - `verification_timestamp=2026-08-04T15:58:04.926988+00:00`
  - `captured_collection_count=230`
  - `document_count=157588`
  - `missing_from_backup=[]`
  - evidence source: `r2:MASCI_complete_backup_2026-08-04_150445Z.zip.manifest.json`

## Restore proof
- **Direct production restore-drill evidence was not exposed by the available production admin routes in this pass.**
- The strongest directly available production proof was manifest/integrity verification against the newest live complete-r2 artifact.
- This means fresh-backup proof is direct; restore proof remains blocked on production restore-drill visibility.
