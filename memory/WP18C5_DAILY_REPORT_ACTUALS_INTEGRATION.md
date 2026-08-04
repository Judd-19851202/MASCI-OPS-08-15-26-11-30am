# WP-18C5 Daily Report Actuals Integration

## Governing requirement satisfied

Daily Reports remain the **operational fact source**. They do not become schedule authority automatically.

## Implemented chain

1. Daily Report submit preserves field facts in `daily_reports`.
2. Existing WP-18C2 work-block logic remains the field-fact packaging layer.
3. New C5 service `sync_schedule_actual_candidates_for_report` derives review-only candidates into `project_schedule_actual_candidates`.
4. PM review route decides `approve / reject / defer / needs_review`.
5. Only **approved** candidates update `schedule_activities.actual_state` and the forecast view.

## Code evidence

- `backend/routes/daily_reports.py`
  - submit flow now calls `sync_schedule_actual_candidates_for_report`
  - detail flow attaches `schedule_actual_candidates` and `schedule_actual_candidate_summary`
- `backend/services/project_schedule_actuals_spine.py`
  - candidate creation
  - PM review handling
  - activity actual-state aggregation

## Preserved no-drift rules

- Original Daily Report facts are not overwritten by PM approval.
- Candidate approval is stored separately in `approved_actual`.
- Ambiguous mappings remain governed review items instead of being guessed.

## Runtime evidence

- `/app/backend/tests/test_wp18c5_schedule_actuals_api.py`
  - imported a governed schedule row
  - submitted a Daily Report
  - observed candidate creation
  - approved the candidate
  - verified Daily Report detail still exposes candidate summary
- `/app/test_reports/iteration_115.json`
  - confirms Daily Reports remain fact source and PM review remains the authority gate

## Governing decision

**PASS** — Daily Reports feed C5 actuals as preserved fact evidence, not as silent schedule authority.
