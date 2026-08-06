# WP-18DB Backup Architecture Certification

## Certification scope

- Package: `WP-18DB — High Availability, Disaster Recovery & Platform Continuity Certification`
- Evidence class: `preview runtime evidence`
- Environment: `preview`
- Archive type: `complete-r2`

## Current authoritative archive

- Archive filename: `MASCI_complete_backup_2026-08-06_142739Z.zip`
- Archive key: `backups/preview/auto-90d/MASCI_complete_backup_2026-08-06_142739Z.zip`
- Backup window:
  - started: `2026-08-06T14:27:39.058779+00:00`
  - completed: `2026-08-06T14:39:47.993719+00:00`
- Archive size: `2,920,430,532 bytes`
- Manifest record count: `2,819,024`
- Storage provider: `R2 / S3-compatible`
- Bucket: `masci-hub`
- Database identity in manifest: `masci_safety_preview`
- Runtime source identity in manifest: `masci_preview_user`
- Release identity in manifest: `40e4b0ceecaec5834f2a503c139aa594`

## Verified controls

- Preview-scoped archive path is enforced under `backups/preview/auto-90d/`.
- Release-gate source authority is passing for the current preview workspace.
- WP-18DA performance budget register is now wired into the permanent release gate.
- Duplicate ZIP member collisions for JSON records were repaired before the latest certified archive was generated.
- Fresh archive upload completed successfully after the collision fix.

## Observed residual warnings

- Some legacy photo/document references still point to missing or invalid object keys/buckets.
- These warnings did **not** prevent archive completion and did **not** prevent the namespace-isolated restore drill from passing.
- Recovery truth therefore treats these as degraded inline-asset references, not as archive-integrity failure.

## Recovery posture after fresh archive

- Recovery snapshot pill: `AMBER`
- Backup trust score: `78`
- Current amber reason from runtime truth: `Hourly complete R2 remains disabled by safety lock`
- Additional trust penalty from runtime truth: `2 backup failure event(s) in last 7d`

## Conclusion

Preview backup architecture is now evidenced with a fresh complete archive, preview-scoped storage lineage, validated manifest identity, and a passing isolated restore drill against the latest archive.