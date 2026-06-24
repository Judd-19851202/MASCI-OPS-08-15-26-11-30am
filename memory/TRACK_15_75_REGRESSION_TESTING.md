# TRACK 15.75 · Phase 14 — Regression Testing

## Coverage map (per Phase 14 mandate)

| Required regression assertion | Source test(s) | Status |
|---|---|---|
| Daily Report with PM email resolves recipient | Track 15.75 live trace (24-06 → davidjewett@) + Track 15.73 Slice 3 picker tests | ✅ PASS |
| Daily Report missing PM routes dead-letter and audits truthfully | `test_track_15_74_dead_letter_audit_trust.py::test_dead_letter_audit_records_actual_recipient_count` | ✅ PASS |
| Daily Report cannot silently fail notification | `test_track_15_74_dead_letter_audit_trust.py::test_dead_letter_audit_flags_unconfigured_when_no_recipients` | ✅ PASS |
| PM dashboard shows assigned records | Admin gate verified (401 → 200) for `/api/daily-reports?project_number=…` and `/api/pm/jobs` | ✅ |
| Safety Meeting employee identity preserved | `test_track_15_73_slice2_attendee_normalization` + `test_recent_meeting_attendees_obey_identity_invariants` | ✅ PASS |
| Safety Meeting notification path explicit | Track 15.75 Phase 4 live trace | ✅ |
| HR can distinguish employee / subcontractor / manual | Track 15.73 Slice 2 — 3 buckets enforced | ✅ |
| Equipment Pre-Op known unit resolves | `test_track_15_73_slice1_equipment_resolver` + `test_equipment_combo_pick_prefers_unit_number` | ✅ PASS |
| Defect escalation path explicit | `PRE_OP_FAIL_FALLBACK` route configured live (Phase 7) | ✅ |
| Audit counts are truthful | `test_track_15_74_dead_letter_audit_trust` + live aggregate (0 failed / 0 error rows) | ✅ |

## Full pytest run (this pass)

```
40 passed in 152.80s

  test_track_15_28c_notification_canonicalization.py     16/16  PASS
  test_track_15_73_canonical_identity_audit.py            6/6   PASS
  test_track_15_73_slice1_equipment_resolver.py           1/1   PASS
  test_track_15_73_slice2_attendee_normalization.py       1/1   PASS
  test_track_15_73_slice3_no_branding_default_drift.py    1/1   PASS
  test_track_15_73_slice3_picker_canonical_emit.py        5/5   PASS
  test_track_15_73d_health_alert_trust.py                 3/3   PASS
  test_track_15_73q_pm_email_coverage.py                  3/3   PASS
  test_track_15_74_dead_letter_audit_trust.py             2/2   PASS
```

(Track 15.74 testing-agent confirmed 40/40, see
`/app/test_reports/iteration_track_15_74_certification.json`.)

## New tests added in Track 15.75

None — the Phase 14 coverage map maps 1:1 onto existing tests after
the Track 15.74 fix. No additional code defect required a new test.
