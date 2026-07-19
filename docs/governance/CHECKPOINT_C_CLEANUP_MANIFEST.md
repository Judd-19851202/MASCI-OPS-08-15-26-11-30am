# CHECKPOINT C CLEANUP MANIFEST

Date: 2026-07-19  
Checkpoint: C (second bounded batch)

## Proposed actions

| Old path | Action | Classification | References | Reason | Risk | Rollback | Tests required |
|---|---|---|---|---|---|---|---|
| `.emergent/cron/applied.hash` | untrack, preserve local | `GENERATED_APPLIED_STATE` | no runtime/CI consumer beyond inventory | pod-local generated state | low | re-create file locally | compile/import + focused suites |
| `.emergent/cron/webhook-crons` | untrack, preserve local | `GENERATED_APPLIED_STATE` | no portable source consumer | generated applied cron state | low | regenerate from platform | compile/import + focused suites |
| `backend/data/equipment_master.20260428-*.bak.json` and `backend/data/equipment_master.20260719-133111.bak.json` | move to `docs/archive/incidents/backend-data-backups/` | `GENERATED_BACKUP` | no runtime refs | stale tracked backup copies mixed with runtime source | medium | restore archived copies | compile/import + focused suites + data path checks |

## Exclusions from this batch

- Active root `backend_test_*.py` files
- `.emergent/emergent.yml`
- generated cron wrapper scripts under `.emergent/cron/*.sh`
- exact duplicate public/static logo groups
- any `UNKNOWN_DO_NOT_TOUCH` file

## Execution note

Only the actions above may be executed in the next bounded cleanup batch.
