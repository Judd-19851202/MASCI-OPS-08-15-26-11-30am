# TRACK 19.49 · Test Report

## Isolated lock test
`pytest /app/backend/tests/test_track_19_49_bulk_and_groups_and_directory_picker.py -q`

## Test list (22 assertions)

### Bulk import
1. `test_bulk_import_panel_present`
2. `test_bulk_paste_mode_wires_bulk_import_endpoint`
3. `test_bulk_paste_validates_emails_and_shows_summary`
4. `test_bulk_import_shows_duplicate_and_inserted_counts`
5. `test_bulk_import_has_active_toggle`

### Copy from product
6. `test_copy_from_product_tab_present_and_wired`
7. `test_copy_from_product_prevents_same_source_and_target`

### Platform directory picker
8. `test_directory_picker_tab_present`
9. `test_directory_picker_uses_canonical_k4_endpoint` — HR / user mutations grep-banned.
10. `test_directory_picker_has_search_portal_and_multiselect`
11. `test_directory_picker_dedupes_against_existing_recipients`
12. `test_directory_picker_stores_source_reference`
13. `test_directory_picker_preserves_manual_entry_path`
14. `test_directory_picker_never_creates_platform_users_or_hr_records`

### Group create + members
15. `test_group_create_panel_present_and_wired`
16. `test_group_member_editor_present_and_wired`
17. `test_group_member_editor_shows_existing_members_readonly`

### Safety
18. `test_no_live_send_path_in_page`
19. `test_dry_run_safety_note_still_present_in_bulk_panel`
20. `test_delete_language_still_absent`

### Documentation / regression
21. `test_all_track_19_49_docs_present`
22. `test_zero_drift_matrix_covers_all_categories`
23. `test_prd_updated`
24. `test_changelog_updated`
25. `test_backend_recipient_engine_unchanged` — exactly one `recipients*.py` in the engine.

## Regression run
- Track 19.48 lock test: GREEN.
- Track 19.47 lock test: GREEN.
- Tracks 19.40–19.46 lock tests: GREEN.

## Live smoke plan
1. Admin opens Recipient page → "Bulk / Directory" button visible.
2. Clicks Bulk / Directory → panel opens with directory tab active by default.
3. Types "safety" in search → K4 users filtered live.
4. Picks 2 users, target product = safety_morning_digest → click Add → toast shows inserted count.
5. Switch to "Paste email list" tab → paste 3 emails including 1 invalid → summary shows 2 valid / 1 invalid, invalid row listed.
6. Switch to "Copy from another product" tab → pick source = safety_morning_digest, target = weekly_operations_digest → toast shows N recipients copied.
7. Groups panel → New group → create group_id / name / products → row appears.
8. Group row → Members → editor opens → add member → row appears in Current Members.
9. Unauth user opens URL → redirected to Admin Sign In.

No live email sent during any smoke step.
