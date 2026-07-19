# MIGRATION COMPATIBILITY REGISTER

Date: 2026-07-19  
Checkpoint: D6

Production deployment is blocked whenever migration state is unknown or rollback compatibility is unproven. No migrations executed in D5/D6.

| Migration ID | File | Change summary | Backward compatibility | Forward compatibility | Required order | Dry-run | Idempotency | Rollback | Backup prerequisite | Owner | Gate status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| MIG-001 | `backend/photo_migration.py` | photo/document data shape migration helper | UNKNOWN | UNKNOWN | manual only | unproven | unproven | manual only | required | jaymn.judd@mascigc.com | BLOCK_PRODUCTION_UNTIL_OWNER_REVIEW |
| MIG-002 | `backend/routes/signature_migration.py` | signature migration route surface | UNKNOWN | UNKNOWN | manual only | unproven | unproven | manual only | required | jaymn.judd@mascigc.com | BLOCK_PRODUCTION_UNTIL_OWNER_REVIEW |
| MIG-003 | `backend/scripts/track_15_28c_canonicalization_migration.py` | daily-report canonicalization migration | PARTIAL | PARTIAL | explicit operator order | script-level only | unknown | manual only | required | jaymn.judd@mascigc.com | BLOCK_PRODUCTION_UNTIL_OWNER_REVIEW |
