# MASCI Hub — Backup Restore Drill Procedure

> Status: **DRAFT — pending first execution**
> Owner: MASCI Operations
> Last updated: 2026-02-XX (Phase 2 hardening, Round 1)

A backup that has never been restored is a Schrödinger backup. It is both
working and not working until you prove otherwise.

This document defines how we prove our R2 backups are actually restorable
to a working Mongo instance, end-to-end.

---

## Cadence

- **First drill:** within 14 days of this document landing
- **Subsequent drills:** quarterly, on the 15th of the first month of each quarter
- **Ad-hoc drill triggers:**
  - Any change to `_backup_scheduler_loop` or related helpers
  - Any change to Mongo collection names or schema
  - After an actual incident requiring a real restore
  - Any change to R2 credentials or bucket configuration

---

## Pre-flight (operator checklist)

1. Identify the backup to restore. Use the most recent **full** (not lite)
   backup unless drilling a specific incident:
   ```bash
   # list R2 backups (newest first)
   python3 scripts/restore_drill.py --list
   ```
2. Provision an ephemeral Mongo target. Two acceptable options:
   - **(A) Local docker:** `docker run -d --rm -p 27018:27017 mongo:7`
   - **(B) Preview container's MongoDB on a side database** — set
     `RESTORE_TARGET_DB=masci_restore_drill_<date>` so the live `DB_NAME`
     stays untouched.
3. Verify operator credentials:
   - Cloudflare R2 access (read-only is sufficient)
   - Mongo write access to the ephemeral target
4. Notify Ops on the #ops channel so any in-flight backup alarms aren't
   misread as a real incident.

---

## Drill procedure

```bash
# 1. Dry-run the restore plan (no writes)
python3 scripts/restore_drill.py --backup <key-from-step-1> --target mongodb://localhost:27018 --target-db masci_drill --dry-run

# 2. Execute the restore against the ephemeral target
python3 scripts/restore_drill.py --backup <key-from-step-1> --target mongodb://localhost:27018 --target-db masci_drill

# 3. Verify integrity — see "Integrity checks" below

# 4. Drop the ephemeral target when done
mongosh "mongodb://localhost:27018" --eval 'db.getSiblingDB("masci_drill").dropDatabase()'
```

---

## Integrity checks (must all pass)

After restore, the ephemeral DB must show:

- ✅ Core collections present and non-empty:
  - `inspections`, `jhas`, `incidents`, `daily_reports`, `meetings`,
    `equipment`, `employees`, `user_directory`, `role_templates`,
    `backup_health`
- ✅ Document counts within 5% of the source's counts at backup time
       (manifest in the backup archive lists expected counts)
- ✅ Latest `backup_health` row's `ts` is within 24h of the backup's manifest `ts`
- ✅ A representative `daily_reports` document still has its `attachments`
       array intact (no Mongo BSON corruption)
- ✅ `user_directory` has the same number of `mirrored=false` (managed)
       users as the source at backup time

---

## Recording the result

After every drill, append to the log below and commit. A drill that wasn't
recorded didn't happen.

| Date | Operator | Backup key | Source size | Restored size | Integrity | Notes |
|------|----------|------------|-------------|---------------|-----------|-------|
| **2026-02-XX (SCHEDULED — first drill, due within 14 days)** | _TBD_ | _newest full nightly under `backups/auto-90d/` once one exists, else newest legacy `backups/MASCI_complete_backup_*.zip`_ | _TBD_ | _TBD_ | _TBD_ | First-ever drill. Operator must document actual archive layout so `restore_drill.py` can be promoted from manual to auto-restore. |
| _subsequent drills logged below_ | | | | | | |

---

## Known caveats

- **Lite backups (hourly)** contain only collections deemed safe to roll
  forward — they will NOT pass the integrity check above. Drill only with
  full nightly backups.
- **R2 lifecycle:** once the 90-day rule is active, backups older than
  90 days will not be restorable. The oldest restorable backup is
  `min(now - 90d, oldest_R2_object_ts)`.
- **Schema drift:** if the restore is from a backup taken before a
  collection rename / schema migration, the integrity check thresholds
  must be relaxed for that specific drill and the deviation noted.

---

## Failure response

If a drill fails:

1. **DO NOT** modify the source `backup_health` or scheduler config.
2. Capture: backup manifest, restore log, integrity-check output.
3. Open a P0 ticket: "Restore drill failed — backups not provably recoverable."
4. Hold all destructive R2 lifecycle changes (don't expire anything) until
   a successful drill is recorded.
