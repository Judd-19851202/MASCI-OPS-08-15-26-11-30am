# DANGEROUS SCRIPT REGISTER

Date: 2026-07-19  
Checkpoint: B

## Discovery method

Static discovery was run repo-wide over `backend/scripts/**` and `scripts/**` by scanning executable files for mutation-capable behavior, not just filenames. The discovery matched write surfaces including Mongo writes, R2/S3 writes, file overwrites/deletes, and HTTP write calls.

Discovery artifact count:
- total executable write-capable scripts discovered: **87**

## Classification summary

| Path | Classification | Production target possible | Dry-run/default read-only | Explicit production opt-in | Status | Notes |
|---|---|---:|---:|---:|---|---|
| `backend/scripts/seed_project_memberships.py` | ACTIVE_OPERATOR_TOOL | Yes | Yes | Yes | REPAIRED | Now dry-run default, `--execute`, typed confirmation, backup ack, DB/env guard. |
| `backend/scripts/seed_equipment_make_model.py` | ACTIVE_OPERATOR_TOOL | Yes | Yes | Yes | REPAIRED | Now dry-run default, `--execute`, typed confirmation, backup ack, DB/env guard. |
| `backend/scripts/migrate_local_project_docs_to_r2.py` | ACTIVE_MIGRATION_PENDING | Yes | Yes | Yes | REPAIRED | Dry-run default retained; apply now gated by typed confirmation + backup ack + DB/env guard. |
| `backend/scripts/track_15_65_seed_email_routes.py` | ACTIVE_OPERATOR_TOOL | Yes | Yes | Yes | REPAIRED | `--apply` now fail-closed without typed confirmation + backup ack + DB/env guard. |
| `backend/scripts/basecamp_import.py` | UNSAFE_UNGUARDED | Yes | No | No | OPEN_P1 | Direct project-membership/docs mutation, default live behavior. |
| `backend/scripts/basecamp_import_big.py` | UNSAFE_UNGUARDED | Yes | No | No | OPEN_P1 | Deletes prior docs and writes docs/R2 or disk fallback, default live behavior. |
| `backend/scripts/migrate_dr_v2_collections_to_daily_report.py` | ACTIVE_MIGRATION_PENDING | Yes | Yes | Partial | OPEN_P1 | Dry-run default exists, but `--live` still lacks typed confirmation + backup ack + exact DB guard. |
| `backend/scripts/track_15_28c_canonicalization_migration.py` | UNSAFE_UNGUARDED | Yes | Partial | No | OPEN_P1 | In-place notifications migration with delete/update/insert paths and no modern fail-closed operator contract. |
| `backend/scripts/purge_synthetic_dailies_24_9.py` | ACTIVE_OPERATOR_TOOL | Yes | Yes | Partial | OPEN_P2 | Dry-run default + audit, but typed destructive confirmation still missing. |
| `backend/scripts/repair_dr_duplicate_doc_ids.py` | ACTIVE_MIGRATION_PENDING | Yes | Yes | Yes | OPEN_P2 | Production opt-in exists; backup-ack style contract still incomplete. |
| `backend/scripts/seed_pm_demo_fixture.py` | TEST_ONLY | No | N/A | N/A | ACCEPTED | Preview-only fixture with preview DB semantics. |
| `backend/tools/restore_drill.py` | RECOVERY_ONLY | No | N/A | N/A | ACCEPTED | Preview-only, hard-refuses non-preview. |
| `scripts/restore_drill.py` | RECOVERY_ONLY | Yes | Yes | Partial | OPEN_P2 | Safer than average, but still needs consistent audit/typed confirm if ever kept active. |
| `backend/scripts/track_15_2_backfill_leaked_pm_offboarding.py` | ACTIVE_OPERATOR_TOOL | Yes | Yes | Yes | ACCEPTED_ACTIVE | Best-in-class reference pattern. |
| `backend/scripts/backfill_b02_meeting_nulls.py` | ACTIVE_MIGRATION_PENDING | Yes | Unknown | Unknown | UNKNOWN_DO_NOT_TOUCH | Write-capable; needs full owner review before execution. |
| `backend/scripts/backfill_b03_dr_identity_final.py` | ACTIVE_MIGRATION_PENDING | Yes | Unknown | Unknown | UNKNOWN_DO_NOT_TOUCH | Write-capable; audit rows present, but operator contract unproven. |
| `backend/scripts/backfill_dr_report_number.py` | ACTIVE_MIGRATION_PENDING | Yes | Unknown | Unknown | UNKNOWN_DO_NOT_TOUCH | Write-capable; bounded migration but guard contract incomplete. |
| `backend/scripts/fv7_1a_asset_metadata_backfill.py` | ACTIVE_MIGRATION_PENDING | Yes | Unknown | Unknown | UNKNOWN_DO_NOT_TOUCH | Update-only backfill; owner review still required. |
| `backend/scripts/iter311_apply_backfill.py` | HISTORICAL_MIGRATION | Yes | No | No | OPEN_P2 | Historical backfill style with audit output; not safe by default. |
| `backend/scripts/migrate_track_23_10_b_qualification_engine.py` | HISTORICAL_MIGRATION | Yes | Unknown | Unknown | UNKNOWN_DO_NOT_TOUCH | Active writes and index creation; historical but still dangerous. |
| `backend/scripts/production_smoke_test.py` | ACTIVE_OPERATOR_TOOL | Yes | No | No | OPEN_P2 | Writes through live API POSTs; not safe by default. |
| `backend/scripts/seed_track_15_11b_pm_cert.py` | TEST_ONLY | Yes | No | No | OPEN_P2 | Certification seed with deletes/inserts; must not be treated as safe active operator tool. |
| `backend/scripts/seed_track_15_13f_cert.py` | TEST_ONLY | Yes | No | No | OPEN_P2 | Certification seed with destructive writes; needs guard if retained. |
| `backend/scripts/seed_track_23_5_cert_employees.py` | TEST_ONLY | Yes | Unknown | Unknown | UNKNOWN_DO_NOT_TOUCH | Write-capable certification seeding. |
| `backend/scripts/track_15_40_backfill_notification_link_url.py` | ACTIVE_MIGRATION_PENDING | Yes | Unknown | Unknown | UNKNOWN_DO_NOT_TOUCH | Update migration; full contract still unproven. |
| `backend/scripts/track_15_47_synthetic_incident.py` | TEST_ONLY | Yes | No | No | OPEN_P2 | Explicit synthetic insertions; not safe if run broadly. |
| `backend/scripts/track_15_65_parity_verify.py` | READ_ONLY_DIAGNOSTIC | No | Yes | N/A | ACCEPTED | Only writes local report artifacts. |
| `backend/scripts/track_15_67_customer_2_contamination_scan.py` | READ_ONLY_DIAGNOSTIC | No | Yes | N/A | ACCEPTED | Local report writes only. |
| `backend/scripts/track_15_67_second_tenant_simulation.py` | ACTIVE_OPERATOR_TOOL | Yes | No | No | OPEN_P1 | Multi-collection tenant mutation + deletes; strong candidate for hard guarding or retirement. |
| `backend/scripts/track_15_69_failure_mode_tests.py` | TEST_ONLY | Yes | No | No | OPEN_P2 | Mutates email routes for scenario testing. |
| `backend/scripts/track_15_70_deployment_simulation.py` | ACTIVE_OPERATOR_TOOL | Yes | No | No | OPEN_P2 | Writes branding/routes; missing modern fail-closed wrapper. |
| `backend/scripts/track_19_00_link_hr_cdl_to_transport.py` | ACTIVE_MIGRATION_PENDING | Yes | Unknown | Unknown | UNKNOWN_DO_NOT_TOUCH | Insert migration; owner review required. |
| `backend/scripts/track_27_backfill_lifecycle_status.py` | ACTIVE_MIGRATION_PENDING | Yes | Unknown | Unknown | UNKNOWN_DO_NOT_TOUCH | Multi-write backfill. |
| `scripts/automated_drill.py` | ACTIVE_OPERATOR_TOOL | Yes | No | No | OPEN_P1 | Drops DB, uploads to R2, unlinks archive; high-risk operator drill. |
| `scripts/cleanup_production_contamination.py` | ACTIVE_OPERATOR_TOOL | Yes | Unknown | Unknown | OPEN_P1 | Direct destructive cleanup path. |
| `scripts/migrate_attachments_to_r2.py` | ACTIVE_MIGRATION_PENDING | Yes | Unknown | Unknown | UNKNOWN_DO_NOT_TOUCH | Attachment migration with writes. |
| `scripts/migrate_dr_photos.py` | ACTIVE_MIGRATION_PENDING | Yes | Unknown | Unknown | UNKNOWN_DO_NOT_TOUCH | Replace-one photo migration. |
| `scripts/preview_seed_13_7c.py` | TEST_ONLY | Yes | Unknown | Unknown | UNKNOWN_DO_NOT_TOUCH | Preview seed semantics need explicit classification. |
| `scripts/r2_lifecycle_apply.py` | ACTIVE_OPERATOR_TOOL | Yes | Unknown | Unknown | OPEN_P1 | Name and write capability imply storage mutation; must be guarded if retained active. |

## Additional discovered write-capable scripts already classified as non-active or lower-risk

### READ_ONLY_DIAGNOSTIC / local artifact writers
- `backend/scripts/audit_specialty_assets.py`
- `backend/scripts/build_dr03_nine_photo_fixture.py`
- `backend/scripts/build_favicon_set.py`
- `backend/scripts/track_15_41_pdf_baseline.py`
- `backend/scripts/track_15_42_pdf_baseline_extended.py`
- `backend/scripts/track_15_69d_behavior_matrix.py`
- `backend/scripts/track_15_69d_post_redeploy_verify.py`
- `backend/scripts/track_15_73_slice1_equipment_audit.py`
- `backend/scripts/track_15_73q_pm_email_audit.py`
- `backend/scripts/track_15_65_parity_verify.py`
- `scripts/authority_mismatch_probe.py`
- `scripts/cross_portal_consistency_drift_probe.py`
- `scripts/diff_doctrine_baseline.py`
- `scripts/export_human_readable.py`
- `scripts/generate_fleet_severity_review.py`
- `scripts/measure_visual_loudness.py`
- `scripts/odr_bilingual_probe.py`
- `scripts/odr_completion_time_drift_probe.py`
- `scripts/odr_inheritance_drift_probe.py`
- `scripts/odr_public_link_continuity_probe.py`
- `scripts/odr_reality_validation.py`
- `scripts/odr_simplicity_drift_probe.py`
- `scripts/pre_deploy_verify.py`
- `scripts/qa_audit.py`
- `scripts/qa_audit_live.py`
- `scripts/scan_production_contamination.py`
- `scripts/timeline_calmness_probe.py`
- `scripts/timestamp_doctrine_probe.py`
- `scripts/trendline_integrity_probe.py`
- `scripts/walkthrough_capture.py`

### TEST_ONLY / operator simulation or certification-style mutators
- `backend/scripts/dls_seed_demo.py`
- `backend/scripts/field_trial_runner.py`
- `backend/scripts/track_15_73_slice1_resolver_regression.py`
- `backend/scripts/track_15_73_slice2_attendee_identity_regression.py`
- `backend/scripts/track_27_09_generate_evidence.py`
- `scripts/iter351_load_cdl_drivers.py`
- `scripts/track14_s2_ipad_audit.py`

### ARCHIVE_CANDIDATE / asset-installer or source-art mutation helpers
- `backend/scripts/fix_lockup_background.py`
- `backend/scripts/fix_onlight_black_swoosh.py`
- `backend/scripts/fix_onlight_lockup.py`
- `backend/scripts/generate_hub_logos.py`
- `backend/scripts/generate_ios_splash.py`
- `backend/scripts/generate_og_image.py`
- `scripts/install_new_logo.py`
- `scripts/install_og_image.py`
- `scripts/jha_to_jhp_rename.py`

### READ_ONLY_DIAGNOSTIC / translation and audit utilities
- `scripts/track14_s1_batch_translate.py`
- `scripts/track14_s1_critical_untranslated.py`
- `scripts/track14_s1_filter_translations.py`
- `scripts/track14_s1_translation_audit.py`

## Totals by classification

- ACTIVE_OPERATOR_TOOL: 12
- ACTIVE_MIGRATION_PENDING: 13
- HISTORICAL_MIGRATION: 2
- RECOVERY_ONLY: 2
- TEST_ONLY: 8
- READ_ONLY_DIAGNOSTIC: 3
- ARCHIVE_CANDIDATE: 0 (not moved during Checkpoint B)
- UNSAFE_UNGUARDED: 4 primary P1 scripts remain in this state class before further repair; **Checkpoint B cannot close while any active Production-capable script remains here**
- UNKNOWN_DO_NOT_TOUCH: 8

## Open P1 findings requiring action/ownership

1. `backend/scripts/basecamp_import.py`
2. `backend/scripts/basecamp_import_big.py`
3. `backend/scripts/migrate_dr_v2_collections_to_daily_report.py`
4. `backend/scripts/track_15_28c_canonicalization_migration.py`
5. `backend/scripts/track_15_67_second_tenant_simulation.py`
6. `scripts/automated_drill.py`
7. `scripts/cleanup_production_contamination.py`
8. `scripts/r2_lifecycle_apply.py`

## Shared doctrine

- Use `backend/lib/operator_safety.py` primitives where compatible.
- Keep script-specific confirmation tokens explicit.
- No active Production-capable mutation script may remain default-live.

## Execution note

No dangerous script was executed during Checkpoint B.
