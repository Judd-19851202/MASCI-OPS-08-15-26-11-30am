# Final Emergency Rollback Plan

## Pre-deploy rollback anchor
- Production commit: `bd9bdd2012c4f2e31b57d7390218b20c361c6dcc`
- Latest fresh backup observed in this pass: `MASCI_complete_backup_2026-08-04_160401Z.zip`

## Rollback triggers
1. Preview-validated Daily Report submit clarity regresses in production
2. Branded Daily Report email/PDF path fails after deploy
3. Notification truth stages silently stop or duplicate
4. Backup freshness/integrity regresses
5. New auth or role-scope regression appears
6. Atlas alert materially worsens after deploy

## Rollback steps
1. Revert application release to production commit above.
2. Restart backend, frontend, workers, and schedulers on rollback revision.
3. Re-verify identity, Daily Report create/submit, notification health, and backup health.
4. Evaluate any newly created indexes for forward-repair vs removal rather than blind removal.

## Readiness
- Fresh backup: **Yes**
- Direct restore proof in this pass: **No**
- Rollback concept: **Ready**
- Rollback fully re-proven end-to-end in this pass: **No**
