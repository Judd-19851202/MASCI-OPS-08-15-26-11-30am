# WP-18DB Backup Architecture Certification

## Certification scope

- Package: `WP-18DB — High Availability, Disaster Recovery & Platform Continuity Certification`
- Evidence class: `preview runtime evidence`
- Environment: `preview`
- Archive type: `complete-r2`

## Current authoritative archive

- Archive filename: `MASCI_complete_backup_2026-08-06_210529Z.zip`
- Archive key: `backups/preview/auto-90d/MASCI_complete_backup_2026-08-06_210529Z.zip`
- Backup window:
  - started: `2026-08-06T21:05:29.605725+00:00`
  - completed: `2026-08-06T21:21:46.602841+00:00`
- Archive size: `2,966,521,367 bytes`
- Storage provider: `R2 / S3-compatible`
- Bucket: `masci-hub`
- Database identity in manifest: `masci_safety_preview`
- Runtime source identity in manifest: `masci_preview_user`
- Release identity in manifest: `431bf0ffcebe49b931e52b2187e31a87`

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

- Recovery snapshot pill in the final gate window: `GREEN`
- Backup trust score in the final gate window: `90 / green`
- Remaining non-blocking evidence note: `2 backup failure event(s) in last 7d`
- Preview-only hourly complete-R2 safety lock is no longer penalized in trust scoring.

## Conclusion

Preview backup architecture is certified with a fresh complete archive, green recovery posture, preview-scoped storage lineage, validated manifest identity, green trust score, and a passing isolated restore drill within the final release-gate window.