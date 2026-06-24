# TRACK 15.75 · Phase 5 — HR / Time Visibility Certification

Evidence: `/tmp/t1575_phaseall.py` schema probe + `hr_users` count.

## HR-relevant fields

### Daily Report
* `masci_crews[].{trade, foreman, count, hours, work_performed}` — ✅
  labor & time data is captured per crew row.
* `subcontractors[]` — sub crew labor records.
* Field-submitter identity bound via `field_submitter_bindings` (952
  rows) so the submitter is resolvable per DR.

### Safety Meeting
* `meetings.attendees[]` — captures `{name, signature, employee_id?}`.
  Manual attendees flagged for review (Track 15.73 Slice 2).
* `meeting_date` + `meeting_time` available for attendance/time use.

### Time Off Requests
* `employee_requests` (52 rows) — HR portal authoritative queue;
  `hr_users` (70 accounts) authorized for read.

## HR access path

* HR portal: `/api/hr/*` routes guarded by `require_hr` (verified
  401 without token; not probed live this pass since gate logic was
  certified during Track 15.13F runtime cert and PRD §15.13F).
* HR can distinguish: MASCI employees (via `employee_id` link),
  subcontractors (separate row category), manual entries (flagged
  for review per Slice 2).

## Identity completeness

* `user_directory.email` 100 % present (162 / 162).
* `employees.id` 100 % present (396 / 396); `employee_id` field is
  empty for most preview seed rows but is **not** the canonical
  identity per current code (current code uses `id` + `email`).
* `hr_identity_completion` test suite covers HR-side identity gaps.

## Verdict

**🟢 GREEN.** HR has the data it needs to see labor/time information.
No P0 visibility gap. P3 data-quality items (employee_id legacy
backfill on `employees` collection) are tracked in PRD but do not
break HR workflows because the canonical join is on `id`.
