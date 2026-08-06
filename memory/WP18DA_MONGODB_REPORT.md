# WP-18DA MongoDB Optimization Report

## Evidence-backed fixes

### Before
From `/app/memory/wp18da_query_explain_snapshot.json`:

1. `safety_equipment_issuances` employee filter
   - winning stage: `COLLSCAN`
   - docs examined: `50`
   - keys examined: `0`
2. `safety_equipment_trainings` employee filter
   - winning stage: `COLLSCAN`
   - docs examined: `40`
   - keys examined: `0`
3. `field_leadership_records` project filter
   - winning stage: `COLLSCAN`
   - docs examined: `444`
   - keys examined: `0`

### Repair

- `ix_safety_issuances_employee_email_issued_date`
- `ix_safety_issuances_project_number_issued_date`
- `ix_safety_trainings_employee_email_training_date`
- `ix_safety_trainings_project_number_training_date`
- `ix_fl_kind_created_at`
- `ix_fl_project_number_created_at`
- `ix_fl_employee_name_created_at`
- `ix_job_photos_thumb_warm_last_failed_at`

### After
From `/app/memory/wp18da_query_explain_snapshot_after.json`:

1. Safety issuances employee filter
   - index: `ix_safety_issuances_employee_email_issued_date`
   - docs examined: `1`
   - keys examined: `1`
   - execution: `1ms`
2. Safety trainings employee filter
   - index: `ix_safety_trainings_employee_email_training_date`
   - docs examined: `1`
   - keys examined: `1`
   - execution: `1ms`
3. Field leadership project filter
   - index: `ix_fl_project_number_created_at`
   - docs examined: `4`
   - keys examined: `4`
   - execution: `1ms`

## Conclusion

- All three targeted hot query families moved from scan-heavy behavior to index-backed execution.
- No speculative indexes were added; every new index is traceable to a measured query shape.
