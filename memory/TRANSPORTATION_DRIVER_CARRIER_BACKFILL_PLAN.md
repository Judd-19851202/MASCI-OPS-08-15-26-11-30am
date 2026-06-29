TRANSPORTATION DRIVER + CARRIER BACKFILL PLAN
==============================================

Backfill script:
    `/app/backend/scripts/track_19_00_link_hr_cdl_to_transport.py`

Purpose: link every HR CDL driver (`employees.cdl_holder = true`)
into Transportation as an operational shell record
(`transport_persons` with `kind = masci_employee`), idempotently.

────────────────────────────────────────────────────────────────────────────
SAFETY POSTURE
────────────────────────────────────────────────────────────────────────────
  · Default mode is DRY-RUN — no writes unless `--commit` is passed.
  · Idempotent — re-running the script never creates a duplicate.
  · Reads `employees` and WRITES only to `transport_persons`.
  · Refuses any employee where `cdl_holder` is not truthy.
  · Soft-deleted HR rows (`deleted_at != null`) are skipped.
  · NEVER overwrites an existing `transport_persons` row.
  · NOT wired to the FastAPI boot path. Operator-run only.
  · Uses python-dotenv to read `/app/backend/.env` so it works from
    either the preview pod or any operator-controlled host with the
    same env file.

────────────────────────────────────────────────────────────────────────────
COMMAND REFERENCE
────────────────────────────────────────────────────────────────────────────
Dry-run (preview, default — recommended first step):
    cd /app/backend && python3 scripts/track_19_00_link_hr_cdl_to_transport.py

Dry-run, with the per-row action plan printed:
    cd /app/backend && python3 scripts/track_19_00_link_hr_cdl_to_transport.py --show-actions

Dry-run for a single HR employee:
    cd /app/backend && python3 scripts/track_19_00_link_hr_cdl_to_transport.py \
        --employee-id c9d7ebc3-a292-4d7a-8765-0ce2739c6029

Commit (writes happen — only after a dry-run review):
    cd /app/backend && python3 scripts/track_19_00_link_hr_cdl_to_transport.py --commit

Commit, capped to 25 inserts (useful for staged rollout):
    cd /app/backend && python3 scripts/track_19_00_link_hr_cdl_to_transport.py --commit --limit 25

────────────────────────────────────────────────────────────────────────────
OUTPUT SUMMARY
────────────────────────────────────────────────────────────────────────────
Every run prints a single block:

    TRACK 19.00 backfill · mode=DRY-RUN | COMMIT
      HR CDL employees scanned     : N
      already linked (no-op)       : N
      would create / created       : N / N
      skipped (missing emp_id)     : N
      skipped (cdl_holder false)   : N

With `--show-actions`, each candidate is printed with its action
(`skip_already_linked` or `create`). With `--commit`, the same actions
become real `transport_persons` inserts.

Exit code 0 = clean. Exit code 1 = at least one row errored during a
commit run (the report lists the per-row error).

────────────────────────────────────────────────────────────────────────────
PRODUCTION ROLLOUT
────────────────────────────────────────────────────────────────────────────
This script is intentionally manual. To run against production:

  1. Set `MONGO_URL` + `DB_NAME` to the PRODUCTION cluster (operator
     side; not auto-resolved from the preview pod). Use a one-shot
     shell so the production creds never get persisted in the pod.
  2. `python3 track_19_00_link_hr_cdl_to_transport.py --show-actions`
     to print the dry-run plan.
  3. Review the plan with the dispatch lead.
  4. `python3 track_19_00_link_hr_cdl_to_transport.py --commit`.
  5. Capture stdout (the report) into the deployment log.

There is NO auto-run on boot. There is NO scheduler. The script is
not imported anywhere from `server.py`. The Track 19.00 tests assert
this explicitly so a future track cannot wire it without breaking the
test gate.

────────────────────────────────────────────────────────────────────────────
ROLLBACK
────────────────────────────────────────────────────────────────────────────
Each created row carries `linked_from_hr_at` and
`linked_from_hr_by="track_19_00_backfill_script"`. To roll back a
backfill:

    db.transport_persons.delete_many({
      "kind": "masci_employee",
      "linked_from_hr_by": "track_19_00_backfill_script"
    })

That query is safe because:
  · It only deletes rows the backfill created.
  · It cannot delete drivers added through the modal flow (different
    actor label).
  · It does NOT touch any HR data.

If you only want to roll back specific employees, add an
`employee_id: {$in: [...]}` clause.

────────────────────────────────────────────────────────────────────────────
PRE-FLIGHT CHECKS (operator)
────────────────────────────────────────────────────────────────────────────
  [ ] Atlas snapshot taken before commit run.
  [ ] Dry-run reviewed with the dispatch lead.
  [ ] No competing migration in flight against `transport_persons`.
  [ ] Backend version pin matches the Track 19.00 release SHA.
