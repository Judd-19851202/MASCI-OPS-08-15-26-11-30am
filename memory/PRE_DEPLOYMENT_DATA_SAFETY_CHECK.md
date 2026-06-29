PRE-DEPLOYMENT DATA SAFETY CHECK
================================

DATE: 2026-02-15
SCOPE: Verify nothing in the Track 18 release will mutate, drop, or
       overwrite production data. Track 18 was a frontend + auth-gate
       release — there are NO migrations, NO collection drops, and NO
       seed-overwrites in scope.

────────────────────────────────────────────────────────────────────────────
1 · DESTRUCTIVE MIGRATION CHECK
────────────────────────────────────────────────────────────────────────────
| Item                                                                  | Status |
|-----------------------------------------------------------------------|--------|
| Pending migration scripts                                             | NONE   |
| `drop_collection` / `db.drop()` calls added                           | NONE   |
| `delete_many({})` calls added against production-shape collections    | NONE   |
| Collection renames                                                    | NONE   |
| Schema changes (BSON shape)                                           | NONE   |
| TTL index changes                                                     | NONE   |
| New indexes                                                           | NONE   |
| Existing indexes touched                                              | NONE   |

────────────────────────────────────────────────────────────────────────────
2 · PRODUCTION DATA WIPE LOGIC
────────────────────────────────────────────────────────────────────────────
None. The release contains no `cleanup_production_*` invocation tied
to the deploy path. The existing helper script
`scripts/cleanup_production_contamination.py` is preserved as-is and
remains a manual-run operator tool.

────────────────────────────────────────────────────────────────────────────
3 · SEED / DEMO DATA
────────────────────────────────────────────────────────────────────────────
- No preview-only seed overwrites added.
- No demo accounts created in this track.
- Existing test credentials (`/app/memory/test_credentials.md`)
  reference dispatch/admin accounts that already exist in production.
- No test-only data injection on the production path.

────────────────────────────────────────────────────────────────────────────
4 · CRITICAL COLLECTIONS (must be preserved through deploy)
────────────────────────────────────────────────────────────────────────────
- `directory_users` (multi-login)
- `dispatch_users`
- `transport_carriers`
- `transport_persons` (drivers)
- `transport_trucks`
- `transport_orientation_modules`
- `transport_orientation_assignments`
- `transport_orientation_certificates`
- `transport_documents`
- `transport_inspections`
- `transport_rate_schedules`
- `transport_audit_timeline`
- `automation_action_items`
- `automation_run_log`
- `automation_digest_runs`
- `audit_ledger` (global)
- `hr_employees`, `hr_*`
- `safety_*`
- `pm_*`
- `shop_*`
- `field_leadership_*`
- `intelligence_cleanup_signals_cache` (read-through)

────────────────────────────────────────────────────────────────────────────
5 · BACKUP PLAN
────────────────────────────────────────────────────────────────────────────
| Step                                                                  | Status |
|-----------------------------------------------------------------------|--------|
| Hourly R2 backup configured (`BACKUP_R2_HOURLY=true`)                 | ON     |
| Twice-daily snapshot scheduled (`BACKUP_HOURS_UTC=2,18`)              | ON     |
| Backup mailbox set (`BACKUP_EMAIL_TO=jaymn.judd@mascigc.com`)         | ON     |
| Atlas point-in-time recovery                                          | Available on Atlas cluster |

Recommended **immediately before deploy**:
  1. Trigger a fresh Atlas snapshot of the production database.
  2. Capture the snapshot ID into the deployment ticket.
  3. Verify the latest R2 hourly export object timestamp < 1 hour old.

────────────────────────────────────────────────────────────────────────────
6 · RESTORE / ROLLBACK PLAN
────────────────────────────────────────────────────────────────────────────
| Step                                                                  | How                                       |
|-----------------------------------------------------------------------|-------------------------------------------|
| Rollback frontend                                                     | Redeploy previous frontend build artefact |
| Rollback backend                                                      | `git checkout <prev SHA> && supervisorctl restart backend` |
| Rollback DB if corruption                                              | Atlas point-in-time restore from snapshot ID captured pre-deploy |
| Rollback object storage (R2)                                          | R2 versioning enabled — restore object via Cloudflare console |
| Audit trail integrity                                                 | `audit_ledger` is append-only; no rollback action required |

────────────────────────────────────────────────────────────────────────────
7 · OPERATIONAL RECORD PRESERVATION (smoke checks)
────────────────────────────────────────────────────────────────────────────
| Record class                                                          | Pre-deploy count expected to match post-deploy |
|-----------------------------------------------------------------------|------------------------------------------------|
| Carriers                                                              | ~200 |
| Drivers (persons)                                                     | ~159 |
| Trucks                                                                | ~6   |
| Orientation modules                                                   | ~21  |
| Orientation certificates                                              | ~42  |
| Dispatch users                                                        | unchanged |
| Audit ledger row count                                                | monotonically increasing — never decreases |

The deploy script must NOT call any destructive endpoint. After
deploy, run a `count_documents({})` smoke against each of the above
and confirm parity (allowing for new audit rows generated during
smoke).

────────────────────────────────────────────────────────────────────────────
OVERALL DATA SAFETY STATUS
────────────────────────────────────────────────────────────────────────────
SAFE — no destructive operation in scope, backups in place, restore
path documented, critical collections enumerated, no schema drift.
