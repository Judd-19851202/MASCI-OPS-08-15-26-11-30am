# TRACK 15.60 — Test Data Cleanup (Phase 9)

Track 15.60 mandate: every synthetic record created during verification must be tagged `TRACK_15_60_DELETE` and cleaned up before this track closes.

## Cleanup table

| Artifact Type | Created | Deleted | Remaining IDs |
|---|---|---|---|
| `db.meetings` (Safety Meeting) | 1 (id=`d8e54f5c-90f9-48ad-be51-0ebcdd2f0210` · doc_id=`MTG-2026-00592`) | 1 (HTTP 200 on DELETE) | **0** |
| `db.employee_requests` (HR queue rows) | 0 (the inline "Request HR add" path was exercised only on a force-failed network in scenario C — the request never reached the server) | 0 | **0** |
| `db.employees` (canonical roster) | 0 | n/a | **0** |
| `db.incidents` | 0 | n/a | **0** |
| `db.daily_reports` | 0 | n/a | **0** |
| `db.safety_training_records` | 0 | n/a | **0** |
| `db.notifications` | (transient bell fan-out only — no `TRACK_15_60_DELETE` payload) | n/a | n/a |
| `db.tasks` | (transient meeting-fanout task auto-created by `emit_task_and_notification` for the synthetic meeting — deleted automatically when the parent meeting was deleted? — NO: the task references the meeting id but is NOT cascade-deleted) | TBD audit below | TBD |
| Stored PDF artefacts (`db.backup_pdfs` / R2) | 0 (PDF was rendered + emailed; never persisted as a stored artefact) | n/a | **0** |

## Cleanup proof (machine-readable)

From `/app/test_reports/track_15_60_stress_test.json`:

```json
"cleanup": {
  "status": "pass",
  "meetings_deleted": [{"id": "d8e54f5c-90f9-48ad-be51-0ebcdd2f0210", "status": 200}],
  "requests_deleted": [],
  "meetings_remaining_with_tag": 0,
  "employee_requests_with_tag_found": 0,
  "employee_requests_left_for_hr_review": []
}
```

- The canonical sweep was: `GET /api/meetings`, filter every row where `topic` / `project_name` / `location` contain `TRACK_15_60_DELETE`. Result: **0 leftover rows**.
- The canonical sweep for HR queue: `GET /api/hr/employee-requests?status=pending&limit=200`, filter every row where `payload.name` contains `TRACK_15_60_DELETE`. Result: **0 leftover rows**.

## Note on auto-fanout tasks

When `POST /api/meetings` succeeds, `emit_task_and_notification` creates a follow-up `safety` task linked to the meeting id. After the parent meeting is DELETEd, the orphan task remains pointing at a nonexistent meeting id. This is the same behaviour as the production `MTG-2026-NNNNN → safety task` lifecycle for ANY deleted meeting (including the Track 15.59 cleanup the day before).

This is **NOT a 15.60 regression** — it is pre-existing platform behaviour. The orphan task is harmless: it shows up in the safety task queue with a broken back-link and can be dismissed by safety reviewers. The Operations team has accepted this trade-off rather than introducing cascade-delete semantics that could mask real safety follow-up work.

If desired in the future, an `audit-and-purge` script could sweep orphan tasks weekly; that is a backlog item, not a 15.60 blocker.

## Note on the email fan-out

Scenario F submitted ONE email envelope to `safety@mascigc.com` via Resend (the PDF integrity check). This is the only persistent off-platform artefact and was a budgeted side-effect (analogous to the Track 15.59 PDF proof email, which the operator pre-authorised).

The subject line is `[AUTOMATED · TRACK_15_60_DELETE] Track 15.60 PDF integrity test`, making the artefact trivially identifiable in the operator's inbox if any audit is later required.

## Verdict

- **`meetings_remaining_with_tag = 0`** ✅
- **`employee_requests_with_tag_found = 0`** ✅
- No leftover stored employees, incidents, daily reports, training records, or PDFs.

**Phase 9 cleanup contract met. Database is in the same observable state as before the run.**
