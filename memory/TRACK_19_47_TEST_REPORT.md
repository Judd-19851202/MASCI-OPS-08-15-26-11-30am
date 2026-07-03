# TRACK 19.47 · Test Report

## Isolated lock test
`pytest /app/backend/tests/test_track_19_47_cockpit_and_summary.py -q`

## Test list (Summary endpoint · backend)
1. `test_summary_endpoint_registered_read_only` — GET-only, no POST/PATCH/DELETE mirrors.
2. `test_summary_endpoint_admin_only` — `require_admin` dependency present.
3. `test_summary_endpoint_never_returns_rendered_html` — grep-locked strip.
4. `test_summary_payload_shape_and_partial_failure_safe` — 11 products compose without raising against an empty DB.
5. `test_summary_endpoint_strips_no_sensitive_fields_but_stays_safe` — no `token`/`secret`/`password`/`api_key` string literals in the summary block.

## Test list (Frontend · Cockpit)
6. `test_cockpit_page_file_exists`.
7. `test_cockpit_route_registered_in_app_js` — route + lazy import present.
8. `test_cockpit_admin_shell_nav_entry_present` — nav entry present.
9. `test_cockpit_wires_expected_backend_endpoints` — summary, preview, dispatch, history, audit all wired.
10. `test_cockpit_dry_run_default_no_live_send` — `dry_run: true` present, `dry_run: false` absent.
11. `test_cockpit_has_expected_test_ids` — 13 required `data-testid` values present for testing agents.
12. `test_cockpit_preview_uses_sandboxed_iframe` — `sandbox=""` present.
13. `test_cockpit_no_hardcoded_fake_scores` — no hardcoded score/attention literals in JSX.

## Test list (Documentation)
14. `test_all_track_19_47_docs_present` — 9 required docs.
15. `test_zero_drift_matrix_covers_all_categories`.
16. `test_prd_updated`.
17. `test_changelog_updated`.

## Regression run
Prior tracks (19.40 → 19.46) all run isolated and remain GREEN.

## Live smoke plan
1. `GET /api/operational-intelligence/summary` (admin) → HTTP 200 · 11 products · `attention_buckets` populated.
2. `GET /api/operational-intelligence/summary` (safety) → HTTP 401 JSON.
3. `GET /api/operational-intelligence/summary` (unauth) → HTTP 401 JSON.
4. Browser opens `/admin/operational-intelligence` → 11 product cards render · top strip shows counts.
5. Click Preview on any product → sandboxed iframe renders 14 sections.
6. Click Dry-run send → HTTP 200 · `send_status: "dry_run"` · recipient list shown · no live email sent.
7. Click History → drawer opens · rows fetched from `/history?product_id=X`.
8. Click Audit → drawer opens · rows fetched from `/audit?product_id=X`.
