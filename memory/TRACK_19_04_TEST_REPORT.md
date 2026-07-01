# Track 19.04 · Test Report

**Date:** 2026-06-29 → 2026-07-01
**Environment:** preview (`safety-audit-mobile-1.preview.emergentagent.com` · DB `masci_safety_preview`)

## Backend pytest — GREEN

```
cd /app/backend && python -m pytest \
  tests/test_track_19_04_form_session_isolation.py \
  tests/test_track_19_04_daily_report_attachments.py

===================== 33 passed in 28.99s =====================
```

### Session isolation (17/17)

| # | Test | Result |
| --- | --- | --- |
| 1–7 | `test_required_report_exists[...]` × 7 | ✅ |
| 8 | `test_prd_mentions_track_19_04` | ✅ |
| 9 | `test_recent_context_contract_v19_04` | ✅ |
| 10 | `test_recent_context_empty_project_returns_empty_shape` | ✅ |
| 11 | `test_recent_context_accepts_foreman_query` | ✅ |
| 12 | `test_no_global_latest_draft_endpoint` | ✅ |
| 13 | `test_save_draft_stamps_saved_by_actor` | ✅ |
| 14 | `test_useformdraft_gates_restore_by_actor` | ✅ |
| 15 | `test_actorid_exposes_auth_fingerprint` | ✅ |
| 16 | `test_smart_prefill_is_explicit_offer_not_auto_apply` | ✅ |
| 17 | `test_default_data_is_pure_and_carries_attachments_field` | ✅ |

### Attachments (16/16)

| # | Test | Result |
| --- | --- | --- |
| 1 | `test_pdf_upload_returns_v19_04_envelope` | ✅ |
| 2 | `test_xlsx_upload_returns_spreadsheet_category` | ✅ |
| 3 | `test_csv_upload_returns_spreadsheet_category` | ✅ |
| 4 | `test_xls_upload_accepted` | ✅ |
| 5 | `test_image_png_rejected_as_document` | ✅ |
| 6 | `test_dangerous_extension_rejected` | ✅ |
| 7 | `test_oversized_upload_rejected` | ✅ |
| 8 | `test_empty_pdf_body_rejected_at_upload` | ✅ |
| 9 | `test_malformed_data_url_returns_400` | ✅ |
| 10 | `test_filename_traversal_neutralised` | ✅ |
| 11 | `test_filename_length_capped` | ✅ |
| 12 | `test_daily_report_model_has_attachments_field` | ✅ |
| 13 | `test_frontend_attachment_upload_component_exists` | ✅ |
| 14 | `test_new_daily_report_mounts_attachment_upload` | ✅ |
| 15 | `test_attachment_endpoint_declared_in_server` | ✅ |
| 16 | `test_photo_storage_has_document_helper` | ✅ |

## Regression — GREEN

Track 19.03 HR roster golden source: **27/27 PASS**.

## Live smoke on /daily/new

* Compile: clean (no `Compiled with problems` overlay).
* AttachmentUpload testid presence: `daily-attachments` = 1, `daily-attachments-picker-input` = 1.
* Zero JavaScript page errors, zero React error boundary, zero raw 401/403 in DOM.

## Backend endpoint contract smoke

```
GET /api/jobs/UNKNOWN-PROJECT/recent-context →
  { contract_version: "19.04",
    source: "daily_reports.most-recent (project-scoped)",
    actor_scoped: false,
    superintendent: "", masci_crews: [], equipment: [],
    source_report_date: "" }

POST /api/daily-reports/attachments/upload
  · PNG → 400 "Unsupported document type: image/png"
  · .exe → 400 "Unsupported document type: application/octet-stream"
  · Valid PDF → 200 envelope with attachment_ref = photo://<bucket>/documents/2026/07/dr_attachment/<uuid>.pdf
```

## Verdict

**GO** — production deployment safe.
