# BCSS Release 2 · Program 2 · Checkpoint 5
## Surface Adoption Matrix

The Operational Truth Spine is a MASCI OPS platform architecture.  
BCSS is Domain 01 and the first implementation domain.  
The artifact does not establish a separate BCSS-only truth architecture.

Date: 2026-07-25

Status: IMPLEMENTATION COMPLETE

---

| Surface Family | Producers | Consumers Updated | Canonical Truth Subject(s) | OTS adoption action |
|---|---|---|---|---|
| Platform Data Truth | `/api/platform/data-truth` | public shell / banner consumers | `bcss_runtime_state_authority` | canonical truth card + projection added |
| Recovery Snapshot | `/api/admin/recovery/snapshot` | `/admin/recovery` | `bcss_recovery_posture` | claim ceiling bound to `CORRELATED`; compact disclosure added |
| Backup Verification | `/api/admin/backup-verification/state`, `/preview`, report/email | Admin Backup Verification panel, report/email | `bcss_backup_archive_lineage` | state separated from validation; report/email bound to OTS truth card |
| Backup Trust | `/api/admin/backup-trust-score` | Recovery UI + downstream aggregators | `bcss_recovery_trust` | derived confidence bounded to `CORRELATED` |
| Deployment Readiness | `/api/admin/deployment-readiness`, `/history`, `/api/admin/deploy-recovery` | `/admin/deploy-recovery` and deploy history consumers | `bcss_recovery_certification` (bounded deployment scope only) | deployment-vs-recovery boundary preserved with OTS truth card |
