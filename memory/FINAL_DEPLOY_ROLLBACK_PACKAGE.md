# FINAL_DEPLOY_ROLLBACK_PACKAGE

## Rollback authority

If the user deploys this bundle and wants to roll back afterward, the prepared rollback authority is the exact authoritative archive already proven by restore drill.

## Rollback asset

- Archive: `MASCI_complete_backup_2026-08-04_210447Z.zip`
- Object key: `backups/preview/auto-90d/MASCI_complete_backup_2026-08-04_210447Z.zip`
- Restore proof: `/app/memory/OPS8_DRILL_ae94d9a8ff5f_REPORT.md`

## Prepared rollback steps (user-run / operator-run only)

1. Confirm deploy regression and stop further write traffic.
2. Select the authoritative archive above.
3. Run the isolated restore procedure proved in the OPS8 drill.
4. Execute the post-restore smoke checks from `FINAL_DEPLOY_POST_DEPLOY_CERTIFICATION.md`.
5. Re-open traffic only after smoke checks pass.

## Important boundary

This rollback package is prepared and evidence-backed. It is **not** a claim that a live production rollback has already been performed.