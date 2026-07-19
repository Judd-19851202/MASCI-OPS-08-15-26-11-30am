# DESTRUCTIVE OPERATION REGISTER

Date: 2026-07-19  
Checkpoint: B

## Summary

- Total destructive operations reviewed: 9 primary runtime blank/full-reset paths
- Intentional full-reset paths: 7
- Unsafe paths found before repair: 5
- Repaired in this checkpoint: 4
- Deferred/owned: 2 script-level families, 1 runtime admin import path

## Register

| ID | File:Line | Surface | Filter shape | Current risk | Status |
|---|---|---|---|---|---|
| DOP-001 | `backend/server.py:4943-4955` | `/api/admin/jobs/bulk-replace` | full collection replace | P1 before fix | REPAIRED |
| DOP-002 | `backend/jobs_master.py:223-235` | helper for jobs bulk replace | literal `delete_many({})` | P1 before fix | REPAIRED |
| DOP-003 | `backend/routes/cost_codes.py:159-168` | `/api/cost-codes/registry/bulk-replace` | literal `delete_many({})` | P1 before fix | REPAIRED |
| DOP-004 | `backend/server.py:10768-10792` | `/api/admin/crew-recovery/force-reseed` | literal `delete_many({})` over seeded collections | P1 before fix | REPAIRED |
| DOP-005 | `backend/server.py:10795-10840` | `/api/admin/crew-recovery/scrap-crew-hub` | literal `delete_many({})` across Crew Hub collections | P1 before fix | REPAIRED |
| DOP-006 | `backend/server.py:11051-11394` | `/api/exports/restore` replace mode | literal `delete_many({})` before restore | P1 before fix | REPAIRED |
| DOP-007 | `backend/server.py:5741-5802` | supplier import replace-all | literal `delete_many({})` | P1 before fix | REPAIRED |
| DOP-008 | `backend/routes/job_photos.py:304-329` | photo reindex | literal `delete_many({})` | P2 | ACCEPTED_INTENTIONAL_ADMIN_RESET |
| DOP-009 | `backend/services/r2_lifecycle/references.py:174-188` | R2 reference scan refresh | literal `delete_many({})` | P2 | ACCEPTED_INTENTIONAL_EPHEMERAL_RESET |

## Repairs completed

### DOP-001 / DOP-002 — jobs bulk replace
- Added required confirmation token: `REPLACE_ALL_JOBS_MASTER`
- Added required `backup_ack=true`
- Added runtime DB assertion through shared operator safety helper
- Added helper refusal when replacement rows are empty

### DOP-003 — cost-code registry bulk replace
- Added required confirmation token: `REPLACE_COST_CODE_REGISTRY`
- Added required `backup_ack=true`
- Added runtime DB assertion through shared operator safety helper

### DOP-004 — crew recovery force-reseed
- Added required confirmation token: `FORCE_RESEED_CREW_COLLECTIONS`
- Added required `backup_ack=true`
- Added runtime DB assertion through shared operator safety helper

### DOP-005 — scrap crew hub
- Added required confirmation token: `SCRAP_CREW_HUB`
- Added required `backup_ack=true`
- Added runtime DB assertion through shared operator safety helper

### DOP-006 — exports restore replace mode
- Added required confirmation token: `RESTORE_REPLACE_ALL_COLLECTIONS`
- Added required `backup_ack=true`
- Added runtime DB assertion through shared operator safety helper
- Added dry-run support in-route
- Added explicit empty-collection refusal for replace mode
- Added per-collection preflight counts and partial-failure honesty

### DOP-007 — supplier replace-all import
- Added explicit `replace_all` mode gate
- Default upload now returns preflight only
- Added required confirmation token: `REPLACE_ALL_SUPPLIERS`
- Added required `backup_ack=true`
- Added runtime DB assertion through shared operator safety helper
- Added preflight counts for current/incoming/duplicates

## Deferred / owned

### Remaining open destructive path ownership
- None in the previously open DOP-006 / DOP-007 pair.

## Guard doctrine proven this checkpoint

- Route auth alone is not enough for full-reset behavior.
- Full-reset admin paths now require:
  - privileged caller
  - typed confirmation token
  - backup acknowledgement
  - runtime DB assertion
