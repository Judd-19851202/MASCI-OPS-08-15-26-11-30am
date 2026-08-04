# Final Release Rollback Plan

## Pre-deploy baseline
- Production commit: `bd9bdd2012c4f2e31b57d7390218b20c361c6dcc`
- Production source hash: `665ea6071d75dd046905a35dfe8dcea4`
- Latest fresh backup at audit time: `MASCI_complete_backup_2026-08-04_160401Z.zip`

## Rollback trigger conditions
Rollback immediately if any of the following fail after deploy:
1. release identity cannot be proven
2. Daily Report save or success UX regresses
3. branded Daily Report email/PDF path fails
4. notification truth stages stop or duplicate
5. backup health regresses outside freshness contract
6. new high-severity auth/permission regression appears

## Rollback steps
1. restore application release to commit `bd9bdd2012c4f2e31b57d7390218b20c361c6dcc`
2. restart backend + all worker/scheduler processes on the rollback image
3. verify email routing mode, scheduler ownership, backup health, and auth
4. if any new index build began, decide on forward-repair vs removal only after confirming impact

## Rollback readiness assessment
- Backup freshness at audit time: within contract
- Verified fresh backup exists
- Application rollback is conceptually ready
- Database/index rollback is **not fully rehearsed for the entire accumulated bundle**

## Rollback decision
- Adequate for controlled release only.
- Not enough to justify unrestricted full-bundle deploy today.
