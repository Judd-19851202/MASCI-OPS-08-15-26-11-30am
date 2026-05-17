# MASCI Hub — Backup Restore Drill Procedure

> Status: **ACTIVE — first end-to-end drill executed and recorded**
> Owner: MASCI Operations
> Last updated: 2026-02-XX (Phase 2 hardening, post first-drill reconciliation)

A backup that has never been restored is a Schrödinger backup. It is both
working and not working until you prove otherwise. This document defines
how we prove our R2 backups are actually restorable end-to-end. The first
drill was executed on **2026-05-17**; this doc reflects what is true today,
not what we hope is true.

---

## 1. Current validated state

| Field | Value |
|---|---|
| **Drill date** | 2026-05-17 (UTC) |
| **Drill type** | Side-database restore (Mongo only — no R2 write, no live DB touched) |
| **Source backup** | `backups/auto-90d/MASCI_complete_backup_2026-05-17_140408Z.zip` (R2) |
| **Source kind** | Lite backup (6 operational collections only — `inspections`, `daily_reports`, `jhas`, `incidents`, `meetings`, `equipment_inspections`) |
| **Source size** | 111 KB |
| **Side-DB target** | `masci_restore_drill_2026_05_17_144307` on the preview Mongo instance (NOT the live `DB_NAME`) |
| **Records restored** | 160 across the 6 lite-mode collections |
| **Verdict** | **PASS** — see § 3 for the integrity checks that were exercised |
| **Side-DB cleanup** | Dropped immediately after verification |
| **Operator** | E1 agent (Phase 2 Initiative 2) |
| **Limitations exposed** | Lite backups do not contain `user_directory`, `employees`, `equipment` master, audit log, or role templates — so a lite-drill cannot validate identity-mirror integrity or non-ops collection counts. **Next drill must target a full nightly backup.** |
| **Next drill due** | 2026-08-15 (quarterly cadence — see § 5) |

---

## 2. Cadence

- **First drill (executed):** 2026-05-17
- **Subsequent drills:** quarterly, on the 15th of the first month of each quarter (next: **2026-08-15**)
- **Ad-hoc drill triggers:**
  - Any change to `_backup_scheduler_loop` or related helpers in `server.py`
  - Any change to Mongo collection names or schema
  - Any change to R2 credentials, bucket configuration, or lifecycle scope
  - After an actual incident requiring a real restore

---

## 3. Verification steps (must all pass — exercised on every drill)

The `restore_drill.py` script performs these checks automatically and
prints a `VERDICT:` line. A drill is only PASS if **every** check below
either succeeded or was skipped with a documented reason.

1. **Mongo connectivity** — the script can `db.command("ping")` the
   target instance.
2. **Per-collection insert counts** — every collection present in the
   backup zip has `count_documents` ≥ 1 after restore. Reported per
   collection. Lite backups expose only 6 collections by design;
   missing collections in a lite drill are documented, not failed.
3. **`daily_reports` attachment integrity** — a representative
   `daily_reports` doc retains its `attachments` array (proves BSON
   round-trip didn't strip embedded structures).
4. **`user_directory` split (full backups only)** — the count of
   `mirrored=false` (managed) users matches what the backup manifest
   claims at backup time. **Skipped for lite drills** (no
   `user_directory` in lite backups — this is a known limitation, not a
   failure).
5. **Side-DB safety** — script refuses to run if `--target-db` does
   not start with `masci_restore_drill_`, or if it equals live
   `DB_NAME`. The 2026-05-17 drill confirmed both rails fire.
6. **No source modification** — the script never writes to R2 and never
   modifies the source backup zip. Verified by comparing R2 ETag /
   last-modified before and after the drill.

The 2026-05-17 drill exercised checks 1, 2, 3, 5, 6. Check 4 was
deliberately skipped because the source was a lite backup. Future drills
against a full nightly backup MUST exercise check 4.

---

## 4. Success criteria

A drill is **PASS** iff:

- `VERDICT: PASS` printed by `restore_drill.py`, AND
- Every verification step in § 3 either succeeded or was explicitly
  skipped with a reason logged in this doc, AND
- The side-DB was dropped (no leftover `masci_restore_drill_*` databases
  on the preview Mongo instance after the drill completes).

A drill is **FAIL** if any of the above is false. On FAIL, the failure
response in § 7 is binding.

---

## 5. Known limitations (current implementation)

| Limitation | Mitigation |
|---|---|
| Lite backups (hourly) contain only the 6 ops collections. A lite-only drill cannot validate non-ops collection integrity. | Always target the most recent **complete** nightly backup unless drilling a specific lite-only scenario. The 2026-05-17 first drill was a lite-source PASS by design; the next drill must be full-source. |
| R2 lifecycle (90-day rule, when activated) means backups older than 90 days are not restorable. | Schedule drills well within the 90-day window. Legacy backups under `backups/*.zip` are NOT subject to lifecycle and remain restorable indefinitely until manual cleanup. |
| Schema drift: if the restore is from a backup taken before a collection rename or schema migration, integrity counts may diverge from current expectations. | Drill operator must document the deviation in this file's drill log (§ 6) — relaxed thresholds are acceptable when called out explicitly. |
| The drill writes to the same Mongo cluster as the live preview DB. A bug in the side-DB safety rail would be catastrophic. | Two independent rails enforce side-DB-only writes (name prefix + live-DB-name check). Both were exercised on 2026-05-17. The production cutover plan includes a future option to drill against a fully independent Mongo (docker or separate cluster) — not in scope today. |
| The drill does NOT restore object storage (R2 photos / attachments). Only Mongo records are exercised. | Restoring R2 in a drill would require write access to a side bucket and is deferred until R2 lifecycle is active. Mongo-side `attachments` array integrity (step 3) is the proxy. |
| The drill produces no automated alert if a future scheduled drill fails to run. | The quarterly cadence relies on an operator running the script. A scheduled CI job is a Phase 3+ item, NOT live today. |

---

## 6. Drill log (append-only)

| Date | Operator | Backup key | Source kind | Records | Verdict | Limitations encountered |
|---|---|---|---|---|---|---|
| **2026-05-17** | E1 agent | `backups/auto-90d/MASCI_complete_backup_2026-05-17_140408Z.zip` | Lite (6 collections) | 160 | **PASS** | Check 4 skipped — lite source has no `user_directory`. Side-DB `masci_restore_drill_2026_05_17_144307` dropped post-verification. |

A drill that is not recorded here did not happen.

---

## 7. Failure response

If a drill fails:

1. **DO NOT** modify the source `backup_health`, scheduler config, or R2 bucket.
2. Capture: the backup manifest, the full `restore_drill.py` log, and
   the integrity-check output.
3. Open a P0 ticket: "Restore drill failed — backups not provably recoverable."
4. **Hold all destructive R2 lifecycle changes** (don't expire anything)
   until a successful drill is recorded.
5. Do not deploy production changes that touch the backup pipeline or
   the affected collections until the drill is PASS again.

---

## 8. Pre-flight (operator checklist)

1. Identify the backup to restore. For routine drills, use the most
   recent **full** (not lite) backup unless drilling a specific
   incident:
   ```bash
   python3 /app/scripts/restore_drill.py --list --limit 10
   ```
2. Provision an ephemeral Mongo target. Two acceptable options:
   - **(A) Preview container's MongoDB on a side database** — set
     `--target-db masci_restore_drill_<date>` so live `DB_NAME` stays
     untouched. **This is what the 2026-05-17 drill used.**
   - **(B) Local docker:** `docker run -d --rm -p 27018:27017 mongo:7`.
     Slower to set up; appropriate for incident-specific drills where
     preview Mongo is unsuitable.
3. Verify operator credentials:
   - Cloudflare R2 access (read-only is sufficient — the drill never
     writes to R2)
   - Mongo write access to the ephemeral target
4. Notify Ops on the #ops channel so any in-flight backup alarms aren't
   misread as a real incident.

---

## 9. Drill procedure

```bash
# 1. Dry-run the restore plan (no writes anywhere)
python3 /app/scripts/restore_drill.py \
    --backup <key-from-step-1> \
    --target $MONGO_URL \
    --target-db masci_restore_drill_$(date +%Y_%m_%d) \
    --dry-run

# 2. Execute the restore against the side DB
python3 /app/scripts/restore_drill.py \
    --backup <key-from-step-1> \
    --target $MONGO_URL \
    --target-db masci_restore_drill_$(date +%Y_%m_%d)

# 3. Validation prints automatically. Verdict line at the end must say PASS.

# 4. Drop the side DB when done
mongosh "$MONGO_URL" --eval \
    'db.getSiblingDB("masci_restore_drill_<date>").dropDatabase()'
```

The script accepts both `MASCI_complete_backup_*.zip` (full) and the
hourly lite backups. **Lite backups intentionally include only 6 core
operational collections.** For full integrity coverage, drill against
the newest **complete** nightly backup, not a lite hourly.

---

## 10. What this drill does NOT prove

In the interest of honesty, the 2026-05-17 PASS verdict proves only:

- Cloudflare R2 will return the requested backup key.
- The zip is readable end-to-end.
- The 6 lite-mode collections can be re-inserted into a fresh Mongo DB.
- The `daily_reports` BSON round-trip preserves `attachments`.
- The side-DB safety rails work.

It does **NOT** prove:

- That a **full** nightly backup is restorable (next drill).
- That R2 photo objects survive a restore (out of scope until R2
  lifecycle is active and we have a side bucket).
- That a restore can be completed within any specific RTO/RPO target
  (no time-bound objective is in force yet).
- That the platform is functional after restore (only that the data is
  in Mongo — booting the app against a restored side-DB is a separate,
  manual exercise).

These are the honest limits of the current drill. They are documented
here so future operators do not over-trust this PASS.
