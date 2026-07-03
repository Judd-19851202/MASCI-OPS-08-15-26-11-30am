# TRACK 19.45B · Test Report

## Isolated lock test
`pytest /app/backend/tests/test_track_19_45b_shop_corporate_intelligence.py -q`

## Test list
### Shop Intelligence
1. `test_shop_intelligence_is_implemented` — status IMPLEMENTED, role safety_or_admin.
2. `test_shop_insufficient_data_when_empty` — empty DB → confidence insufficient_data, attention CRITICAL, all 14 sections.
3. `test_shop_score_with_real_signals` — populated DB → confidence medium/high, top-5 table populated, score < 100.
4. `test_shop_top5_preference_order` — safety holds precede aging critical defects precede OOS units in top-5.
5. `test_shop_has_expected_deep_links` — `/shop`, `/fleet`, `/fleet/holds`, `/fleet/defects`, `/safety/cases` present.
6. `test_shop_no_auto_decision_notice_present` — notice explicitly refuses to determine mechanic/operator fault, preventability, liability.

### Corporate Intelligence
7. `test_corporate_intelligence_is_implemented` — status IMPLEMENTED, role admin_only.
8. `test_corporate_insufficient_data_when_all_domains_empty` — empty DB → confidence insufficient_data, 14 sections.
9. `test_corporate_weighted_rollup_with_populated_domains` — populated DB → confidence medium/high, overall_score in [0,100], top-5 domain table populated, "Domains scored" in exec summary.
10. `test_corporate_weight_model_covers_every_implemented_product` — weight table covers every IMPLEMENTED product; sum == 100.
11. `test_corporate_has_expected_deep_links` — `/safety/cases`, `/pm/projects`, `/fleet`, `/shop`, `/hr/employees`, `/hr/training-records` present.
12. `test_corporate_no_auto_decision_notice_present` — notice refuses to declare compliant, legal, liability, discipline.

### Registry integrity
13. `test_registry_implemented_count_now_ten` — 10 IMPLEMENTED products (added shop + corporate).
14. `test_registry_contract_registered_only_weekly_operations` — only `weekly_operations_digest` remains contract.
15. `test_registry_total_product_count_is_eleven` — 11 total products in registry.

### Zero-drift proof
16. `test_no_new_email_provider_or_scheduler_in_track_19_45b` — no resend/sendgrid/smtplib/apscheduler drift.
17. `test_one_engine_only` — all seven engine files present · no duplication.

### Documentation
18. `test_all_track_19_45b_docs_present` — 11 required docs present.
19. `test_zero_drift_matrix_covers_all_categories` — ZDM covers Schemas · Routes · Emails · Scheduler · Recipients · Audit · Rollback.
20. `test_prd_updated` / `test_changelog_updated`.

## Regression run
Prior tracks (19.40, 19.41, 19.42, 19.43, 19.44, 19.45A) all run
isolated and remain GREEN.

## Live smoke plan
1. `GET /api/operational-intelligence/products` → assert count=11.
2. `GET /api/operational-intelligence/shop_intelligence/preview` with
   safety-or-admin token → HTTP 200 · all 14 sections.
3. `GET /api/operational-intelligence/corporate_intelligence/preview`
   with admin token → HTTP 200 · all 14 sections.
4. `GET /api/operational-intelligence/corporate_intelligence/preview`
   with safety-only token → HTTP 403 (admin_only).
5. No live email — dry-run default preserved.
