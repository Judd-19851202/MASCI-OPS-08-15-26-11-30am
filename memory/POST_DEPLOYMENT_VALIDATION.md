# WP-16A — Post-Deployment Validation Checklist

Date: 2026-07-31
Status: PREPARED / NOT YET EXECUTED

Run this immediately after authorized deployment.

## Critical validations

1. Runtime identity and health
   - `GET /api/health` → `200`
   - `GET /api/ready` → `200`
   - `GET /api/health/full` → `200`
2. Recovery / backup truth
   - `/api/admin/recovery/snapshot` coherent
   - `/api/admin/backups-complete-r2-state` coherent
3. Production reliability smoke
   - Daily Reports restore behavior
   - Equipment Pre-Operations public lookup
   - Transportation cleanup auth + performance
4. Platform / integrations
   - `/api/admin/integrations/health`
   - scheduler / background jobs truth
5. Security / session continuity
   - admin login continuity
   - representative PM / HR / Safety / Dispatch portal logins

## Evidence package to capture

- deployment timestamp
- production URLs exercised
- PASS / FAIL for each critical validation
- screenshots or curl outputs for any failure
- final GO / rollback decision

Use `/app/memory/PRODUCTION_VERIFICATION_CHECKLIST.md` as the broader live sweep companion.