"""Track 19.22 · P1 Operational Completion — lock tests.

Locks the additive Track 19.22 surface: search filters on `list_records`,
bulk batch operations (upload/apply/approve-all), and the six PDF
export packages. Front-end sentinels: Documents tab + all six package
buttons + Batches routes.

Zero drift: NO OCR, NO AI, NO fuzzy matching — all still absent.
"""
from __future__ import annotations

from pathlib import Path


MODULE = Path("/app/backend/routes/employee_records.py")
API_CLIENT = Path("/app/frontend/src/lib/employeeRecordsApi.js")
EMP_PROFILE = Path("/app/frontend/src/pages/EmployeeProfile.jsx")
BATCHES_PAGE = Path("/app/frontend/src/pages/HistoricalRecordsBatches.jsx")
BATCH_DETAIL = Path("/app/frontend/src/pages/HistoricalRecordsBatchDetail.jsx")
APP_JS = Path("/app/frontend/src/App.js")


# ── Phase 2 · Search filters on list_records ─────────────────────────
def test_list_records_supports_structured_search_filters():
    src = MODULE.read_text(encoding="utf-8")
    for filt in ("q:", "department:", "uploader_email:", "reviewer_email:",
                 "tag:", "date_from:", "date_to:",
                 "related_asset_id:", "related_incident_case_id:",
                 "related_project_id:", "related_training_id:"):
        assert filt in src, f"list_records must accept `{filt}` filter"


def test_search_query_only_hits_structured_fields():
    src = MODULE.read_text(encoding="utf-8")
    # Structured only — no OCR / no external index.
    assert '"record_type": pat' in src
    assert '"notes": pat' in src
    assert '"source_file_name": pat' in src
    assert '"employee_name_snapshot": pat' in src
    for banned in ("elasticsearch", "opensearch", "text_extract", "tesseract"):
        assert banned not in src.lower(), f"No OCR/index dependency allowed ({banned})"


# ── Phase 4 · Bulk batch operations ──────────────────────────────────
def test_batch_upload_endpoint_registered():
    src = MODULE.read_text(encoding="utf-8")
    assert '@router.post("/batches/{batch_id}/uploads")' in src
    assert "async def batch_upload(" in src


def test_batch_upload_creates_pending_classification_records():
    src = MODULE.read_text(encoding="utf-8")
    # Every file must land as pending_classification (unclassified) so
    # a human classifies it before approval.
    assert '"approval_status": "pending_classification"' in src


def test_batch_upload_preserves_original_file_and_hash():
    src = MODULE.read_text(encoding="utf-8")
    # The uploader path must compute _sha256 and stamp source_file_ref.
    ix = src.index("async def batch_upload(")
    body = src[ix: ix + 5000]
    assert "_sha256(raw)" in body
    assert 'rec["id"]' in body


def test_batch_bulk_apply_endpoint_registered():
    src = MODULE.read_text(encoding="utf-8")
    assert '@router.post("/batches/{batch_id}/apply")' in src
    assert "async def batch_bulk_apply(" in src


def test_batch_bulk_apply_writes_audit_events():
    src = MODULE.read_text(encoding="utf-8")
    ix = src.index("async def batch_bulk_apply(")
    body = src[ix: ix + 3000]
    assert '_write_audit(' in body
    assert '"record_batch_apply"' in body


def test_batch_bulk_apply_recomputes_state_per_record():
    src = MODULE.read_text(encoding="utf-8")
    # State must flip to pending_approval only when both employee AND
    # record_type end up populated after the patch is applied.
    ix = src.index("async def batch_bulk_apply(")
    body = src[ix: ix + 2500]
    assert 'if new_emp and new_type:' in body
    assert '"pending_approval"' in body


def test_batch_approve_all_endpoint_registered():
    src = MODULE.read_text(encoding="utf-8")
    assert '@router.post("/batches/{batch_id}/approve-all")' in src


def test_batch_approve_all_requires_lane_approver():
    src = MODULE.read_text(encoding="utf-8")
    ix = src.index("async def batch_approve_all(")
    body = src[ix: ix + 2000]
    # HR / admin / Safety(safety) / asset_admin(asset) — enforced via
    # _actor_can_approve which uses LANE_APPROVERS.
    assert '_actor_can_approve(actor, lane)' in body


def test_batch_approve_all_skips_records_missing_prereqs():
    src = MODULE.read_text(encoding="utf-8")
    ix = src.index("async def batch_approve_all(")
    body = src[ix: ix + 2000]
    # Server-side mirror of the UI guard: no employee or no type ⇒ skip.
    assert 'if not r.get("employee_id") or not r.get("record_type"):' in body


# ── Phase 3 · Export packages ────────────────────────────────────────
def test_all_six_packages_declared():
    src = MODULE.read_text(encoding="utf-8")
    for pkg in ("complete_file", "training", "discipline", "safety",
                "ppe_asset", "historical_records"):
        assert f'"{pkg}"' in src, f"Missing package {pkg}"


def test_package_titles_are_human_readable():
    src = MODULE.read_text(encoding="utf-8")
    for title in ("Complete Employee File", "Training Package",
                  "Discipline Package", "Safety Package",
                  "PPE / Asset Package", "Historical Records Package"):
        assert f'"{title}"' in src, f"Missing title {title!r}"


def test_package_endpoint_registered():
    src = MODULE.read_text(encoding="utf-8")
    assert '@router.get("/employees/{emp_id}/exports/{package}.pdf")' in src
    assert "async def employee_package_pdf(" in src


def test_package_endpoint_lane_gated():
    src = MODULE.read_text(encoding="utf-8")
    # HR + admin can always. Safety can only pull safety + historical.
    # Asset admin can only pull ppe_asset + historical.
    assert '"safety":' in src and '"safety"' in src
    # Look at PACKAGE_LANE_GATE literal:
    assert 'PACKAGE_LANE_GATE' in src
    # Discipline package is restricted to HR + admin.
    ix = src.index("PACKAGE_LANE_GATE = {")
    body = src[ix: ix + 700]
    assert '"discipline":       {"hr", "admin"}' in body \
        or '"discipline":' in body and '"safety"' not in body[body.index('"discipline"'): body.index('"discipline"') + 60]


def test_package_pdf_helper_uses_reportlab_and_is_self_contained():
    src = MODULE.read_text(encoding="utf-8")
    assert "def _render_employee_package_pdf(" in src
    ix = src.index("def _render_employee_package_pdf(")
    body = src[ix: ix + 8000]
    # Reuses existing reportlab (no new dependency).
    assert "reportlab.platypus" in body
    # Signature line for trust.
    assert "MASCI Operations Platform" in body


# ── Frontend · Documents tab + search + export dropdown ──────────────
def test_employee_profile_declares_documents_tab():
    src = EMP_PROFILE.read_text(encoding="utf-8")
    # Tab list literal declaration.
    assert '{ key: "documents"' in src
    # The rendered testid is a template literal (`tab-${key}`), so
    # we assert the DocumentsPane rendered container instead.
    assert 'data-testid="employee-profile-documents"' in src


def test_employee_profile_documents_has_search_and_lane_filter():
    src = EMP_PROFILE.read_text(encoding="utf-8")
    assert 'data-testid="employee-profile-documents-search"' in src
    assert 'data-testid="employee-profile-documents-lane-filter"' in src


def test_employee_profile_declares_all_six_export_packages():
    src = EMP_PROFILE.read_text(encoding="utf-8")
    for pkg in ("complete_file", "training", "discipline", "safety",
                "ppe_asset", "historical_records"):
        # Package keys appear as string literals in the button map.
        assert f'key: "{pkg}"' in src, f"Missing package button {pkg}"
    # And the dynamic testid template exists too.
    assert 'employee-profile-package-${key}' in src


def test_employee_profile_documents_uses_read_only_api():
    src = EMP_PROFILE.read_text(encoding="utf-8")
    # Uses fetchEmployeeRecords with include_pending=false so only
    # approved records surface. Approval / mutation live in the queue.
    assert "fetchEmployeeRecords" in src
    assert "include_pending: false" in src


def test_employee_profile_has_bulk_batches_deep_link():
    src = EMP_PROFILE.read_text(encoding="utf-8")
    assert 'data-testid="employee-profile-view-batches"' in src
    assert '/hr/historical-records/batches' in src


# ── Frontend · Bulk Batches pages ────────────────────────────────────
def test_batches_list_page_declared():
    src = BATCHES_PAGE.read_text(encoding="utf-8")
    assert 'data-testid="historical-records-batches"' in src
    assert 'data-testid="batches-create"' in src


def test_batch_detail_page_declared():
    src = BATCH_DETAIL.read_text(encoding="utf-8")
    assert 'data-testid="historical-records-batch-detail"' in src
    # Must expose upload + apply + approve-all controls.
    assert 'data-testid="batch-file-input"' in src
    assert 'data-testid="batch-apply-submit"' in src
    assert 'data-testid="batch-approve-all"' in src


def test_batch_detail_uses_employee_combo_and_no_ml():
    src = BATCH_DETAIL.read_text(encoding="utf-8")
    assert "EmployeeCombo" in src
    for banned in ("tesseract", "openai", "rapidfuzz", "litellm"):
        assert banned not in src.lower()


def test_app_js_mounts_batch_routes():
    src = APP_JS.read_text(encoding="utf-8")
    assert '/hr/historical-records/batches' in src
    assert '/hr/historical-records/batches/:batchId' in src


# ── API client ───────────────────────────────────────────────────────
def test_api_client_declares_batch_and_export_helpers():
    src = API_CLIENT.read_text(encoding="utf-8")
    for fn in ("createBatch", "listBatches", "fetchBatch",
               "batchUpload", "batchApply", "batchApproveAll",
               "packageDownloadUrl", "downloadPackagePdf"):
        assert f"export {'function ' if 'function' in src.split(fn)[0][-25:] else 'async function ' if 'async function ' + fn in src else 'function '}{fn}(" in src \
            or f"function {fn}(" in src, f"Missing API fn: {fn}"


# ── Zero-drift sentinels · Track 19.22 additions ─────────────────────
def test_track_19_22_does_not_reference_ml_libraries():
    for path in (MODULE, API_CLIENT, EMP_PROFILE, BATCHES_PAGE, BATCH_DETAIL):
        src = path.read_text(encoding="utf-8")
        for banned in ("tesseract", "rapidfuzz", "litellm"):
            assert banned not in src.lower(), \
                f"{path.name} must not reference {banned!r} in Track 19.22."


def test_track_19_22_module_still_does_not_mutate_employees():
    src = MODULE.read_text(encoding="utf-8")
    for banned in ("db.employees.insert", "db.employees.update_one",
                   "db.employees.delete"):
        assert banned not in src


def test_track_19_22_audit_ledger_still_append_only():
    src = MODULE.read_text(encoding="utf-8")
    assert "db.employee_record_audit.insert_one" in src
    for banned in ("db.employee_record_audit.update",
                   "db.employee_record_audit.delete"):
        assert banned not in src, f"Audit must stay append-only ({banned})"
