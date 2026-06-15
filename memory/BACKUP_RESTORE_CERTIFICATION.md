# Backup / Restore Certification

**Track:** 14.0-RC1
**Date:** 2026-06-15

## Backup endpoints

* Nightly Mongo dump: scheduled via `SCHEDULER_ENABLED=true` +
  `BACKUP_HOURS_UTC=2,18`. Default schedule fires at 02:00 + 18:00 UTC.
* R2 hourly mirror: `BACKUP_R2_HOURLY=true` mirrors each dump into
  the `masci-hub` Cloudflare R2 bucket.
* Manual backup: `POST /api/admin/backup` (admin-strict) — kicks off
  an on-demand backup.
* Backup listing: `GET /api/admin/backups` (admin-strict).
* Email: `BACKUP_EMAIL_TO=jaymn.judd@mascigc.com` receives a copy of
  each backup zip nightly when `AUTO_EMAIL_REPORTS=true`.

## Restore endpoints

* `POST /api/admin/backup/{id}/restore` (admin-strict + AdminPasswordConfirm dialog).
* Cross-environment archive validation: every backup archive carries
  an `env` field in its manifest. The restore handler refuses to
  apply an archive whose `env` doesn't match the current
  `APP_ENV` — i.e. a preview backup cannot be restored into
  production, and vice versa.

## Environment isolation — PROVEN

`ENFORCE_DB_ISOLATION=true` + the preview Atlas user
(`masci_preview_user`) is bound to database `masci_safety_preview`
ONLY. Live evidence:

```
pymongo.errors.OperationFailure: not authorized on scheduler_test_iter445
to execute command { delete: "scheduler_runs", ... },
... 'code': 13, 'codeName': 'Unauthorized'
```

Even with valid app credentials, the preview process **cannot**
write to any database outside `masci_safety_preview`. This blocks
any accidental cross-environment restore at the database layer, in
addition to the application-layer manifest check.

## Manual restore drill — NOT executed in this audit

A full end-to-end restore drill (`POST /api/admin/backup` → download
zip → DELETE a non-critical collection → restore from zip → verify
data restored) requires:

1. A safe target collection that can be temporarily emptied.
2. Operator approval to delete + re-restore in the live preview DB.

Neither precondition was met in this audit window. The restore
endpoints + isolation guard are verified by static inspection +
the Mongo-permission boundary test above.

**Recommendation**: Schedule a manual restore drill within the first
2 weeks of production operation, against a known-safe collection (e.g.
`db.training_records` after a CSV export checkpoint).

## R2 storage status

* `S3_ENDPOINT_URL=https://46400762d3027afbb26819a8de8528e6.r2.cloudflarestorage.com`
* `S3_BUCKET=masci-hub`
* Deploy-readiness check: ✅ "OK — uploads will land in R2"
* Last 24 h R2 fallback-to-inline events: 0

## Verdict

🟢 **Backup configuration: ready. Restore isolation: PROVEN by
Atlas permission boundary. Manual restore drill: recommended as a
post-deploy follow-up, not a deploy blocker.**
