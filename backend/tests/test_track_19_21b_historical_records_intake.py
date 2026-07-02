"""Track 19.21b · Historical Records Intake — lock tests.

Locks the additive intake+review surface without spinning up a live
FastAPI test client. Focus: source-level guarantees + route wiring +
frontend surface presence + audit contract.

Deliberately does NOT test the ML lanes (OCR / AI / fuzzy matching)
— those are Track 19.22+ and must remain absent.
"""
from __future__ import annotations

from pathlib import Path


MODULE = Path("/app/backend/routes/employee_records.py")
INTAKE_PAGE = Path("/app/frontend/src/pages/HistoricalRecordsIntake.jsx")
QUEUE_PAGE = Path("/app/frontend/src/pages/HistoricalRecordsQueue.jsx")
API_CLIENT = Path("/app/frontend/src/lib/employeeRecordsApi.js")
APP_JS = Path("/app/frontend/src/App.js")
EMP_PROFILE = Path("/app/frontend/src/pages/EmployeeProfile.jsx")
SERVER = Path("/app/backend/server.py")


# ── Backend: dedicated auth gate accepts HR + Safety + Asset + Admin ──
def test_gate_factory_declared():
    src = MODULE.read_text(encoding="utf-8")
    assert "def make_employee_records_actor_gate(" in src, \
        "Track 19.21b must expose its own actor gate (HR + Safety + Asset + Admin)."


def test_gate_accepts_hr_safety_shop_admin_headers():
    src = MODULE.read_text(encoding="utf-8")
    for header in ('"X-HR-Token"', '"X-Safety-Token"', '"X-Shop-Token"', '"X-Admin-Token"'):
        assert header in src, f"Gate must inspect {header}"


def test_gate_only_promotes_shop_users_with_asset_admin_flag():
    src = MODULE.read_text(encoding="utf-8")
    # Asset admin promotion must gate on the explicit flag; otherwise
    # ordinary mechanics could reach Track 19.21b surfaces.
    assert 'u.get("is_asset_admin")' in src
    assert '"asset_admin"' in src


def test_server_registers_new_gate():
    src = SERVER.read_text(encoding="utf-8")
    # The server must use the new gate — not the old safety_admin_or_pm one.
    assert "make_employee_records_actor_gate(" in src
    # Old wiring line must be gone from this call site.
    ix_reg = src.index("build_employee_records_router(")
    call_body = src[ix_reg: ix_reg + 400]
    assert "make_require_safety_admin_or_pm" not in call_body, \
        "Employee records router must use the dedicated gate (HR-inclusive)."


# ── Backend: upload endpoint preserves the original file ────────────
def test_upload_route_registered():
    src = MODULE.read_text(encoding="utf-8")
    assert '@router.post("/uploads")' in src
    assert "async def upload_original_file(" in src


def test_upload_route_computes_sha256_hash():
    src = MODULE.read_text(encoding="utf-8")
    assert "_sha256(raw)" in src
    assert "source_file_hash" in src


def test_upload_route_enforces_size_limit():
    src = MODULE.read_text(encoding="utf-8")
    assert "MAX_UPLOAD_BYTES" in src
    assert "raise HTTPException(413" in src


def test_upload_route_extension_allowlist_includes_office_and_pdf():
    src = MODULE.read_text(encoding="utf-8")
    # From the tuple/set literal.
    for ext in ("pdf", "docx", "xlsm", "csv", "jpg"):
        assert f'"{ext}"' in src, f"Extension {ext!r} must be in the allowlist"


def test_upload_route_falls_back_to_base64_when_r2_unconfigured():
    src = MODULE.read_text(encoding="utf-8")
    # The fallback path preserves records on dev/test envs without R2.
    assert "base64.b64encode(raw)" in src


def test_file_download_route_registered():
    src = MODULE.read_text(encoding="utf-8")
    assert '@router.get("/records/{record_id}/file")' in src
    assert "async def download_record_file(" in src


def test_file_download_uses_presigned_redirect():
    src = MODULE.read_text(encoding="utf-8")
    # No proxying bytes through FastAPI; use short-TTL presigned redirect.
    assert "RedirectResponse" in src
    assert "presigned_get_url(" in src


# ── Backend: vocabulary endpoint exposes lanes/types to the client ──
def test_vocabulary_route_registered():
    src = MODULE.read_text(encoding="utf-8")
    assert '@router.get("/vocabulary")' in src
    assert "allowed_lanes_for_actor" in src


def test_vocabulary_never_leaks_lanes_actor_cannot_read():
    # Safety actor calling vocabulary must only see the safety lane in
    # `allowed_lanes_for_actor` — the doctrine is enforced by
    # `_actor_can_read_lane`. This test locks the source contract.
    src = MODULE.read_text(encoding="utf-8")
    assert "_actor_can_read_lane(actor, lane)" in src


# ── Frontend: intake page ───────────────────────────────────────────
def test_intake_page_exists_and_declares_manual_only():
    src = INTAKE_PAGE.read_text(encoding="utf-8")
    assert 'data-testid="historical-records-intake"' in src
    # Explicit banner language: NO OCR / NO AI / NO fuzzy matching.
    assert "No OCR" in src
    assert "No AI" in src
    assert "No fuzzy matching" in src


def test_intake_page_uses_manual_employee_link():
    src = INTAKE_PAGE.read_text(encoding="utf-8")
    assert "EmployeeCombo" in src


def test_intake_page_calls_upload_then_create():
    src = INTAKE_PAGE.read_text(encoding="utf-8")
    # Both API calls must be present so the original bytes are
    # preserved before the record is staged for approval.
    assert "uploadOriginalFile" in src
    assert "createRecord" in src


def test_intake_page_forwards_incident_case_and_asset_links():
    src = INTAKE_PAGE.read_text(encoding="utf-8")
    assert "related_incident_case_id" in src
    assert "related_asset_id" in src


# ── Frontend: queue page ────────────────────────────────────────────
def test_queue_page_exists():
    src = QUEUE_PAGE.read_text(encoding="utf-8")
    assert 'data-testid="historical-records-queue"' in src


def test_queue_page_supports_approve_reject_reassign():
    src = QUEUE_PAGE.read_text(encoding="utf-8")
    for fn in ("approveRecord", "rejectRecord", "reassignRecord"):
        assert fn in src, f"Queue must expose {fn}"


def test_queue_page_blocks_approval_when_prerequisites_missing():
    src = QUEUE_PAGE.read_text(encoding="utf-8")
    # Client-side guard mirrors backend server guard.
    assert "rec.employee_id && !!rec.record_type" in src or \
           "rec.employee_id" in src and "rec.record_type" in src
    assert "Employee link and record type" in src


def test_queue_page_requires_reason_to_reject():
    src = QUEUE_PAGE.read_text(encoding="utf-8")
    assert "Reason is required to reject" in src


def test_queue_page_lane_tabs_only_show_allowed_lanes():
    src = QUEUE_PAGE.read_text(encoding="utf-8")
    assert "allowed_lanes_for_actor" in src


# ── Employee 360° · deep links to intake + queue ────────────────────
def test_employee_profile_has_add_historical_record_link():
    src = EMP_PROFILE.read_text(encoding="utf-8")
    assert 'data-testid="employee-profile-add-historical-record"' in src
    assert "/hr/historical-records/intake" in src


def test_employee_profile_has_view_intake_queue_link():
    src = EMP_PROFILE.read_text(encoding="utf-8")
    assert 'data-testid="employee-profile-view-intake-queue"' in src
    assert "/hr/historical-records/queue" in src


def test_employee_profile_uses_portal_token_headers():
    src = EMP_PROFILE.read_text(encoding="utf-8")
    # The bug that blocked Phase A visual verification was the wrong
    # token keys / Bearer scheme. Lock the fix.
    assert 'getHrToken' in src
    assert '"X-HR-Token"' in src
    # And the old wrong pattern must be gone.
    assert 'localStorage.getItem("safetyToken")' not in src
    assert 'localStorage.getItem("adminToken")' not in src


# ── Routing ─────────────────────────────────────────────────────────
def test_app_js_mounts_both_new_routes():
    src = APP_JS.read_text(encoding="utf-8")
    assert '/hr/historical-records/intake' in src
    assert '/hr/historical-records/queue' in src


# ── API client shape ────────────────────────────────────────────────
def test_api_client_declares_all_endpoints():
    src = API_CLIENT.read_text(encoding="utf-8")
    for fn in ("fetchVocabulary", "fetchQueue", "listRecords",
               "fetchEmployeeRecords", "uploadOriginalFile",
               "createRecord", "approveRecord", "rejectRecord",
               "reassignRecord"):
        assert f"export async function {fn}(" in src, f"Missing API fn: {fn}"


def test_api_client_forwards_every_portal_token():
    src = API_CLIENT.read_text(encoding="utf-8")
    for hdr in ('"X-HR-Token"', '"X-Safety-Token"', '"X-Shop-Token"', '"X-Admin-Token"'):
        assert hdr in src


# ── Zero-drift sentinels ────────────────────────────────────────────
def test_intake_does_not_reference_ml_libraries():
    for path in (INTAKE_PAGE, QUEUE_PAGE, API_CLIENT):
        src = path.read_text(encoding="utf-8")
        for banned in ("tesseract", "openai", "rapidfuzz", "litellm"):
            assert banned not in src.lower(), \
                f"{path.name} must not reference {banned!r} in Track 19.21b."


def test_backend_route_module_has_no_second_employee_source_of_truth():
    src = MODULE.read_text(encoding="utf-8")
    # This module must READ employees only. It must not INSERT into
    # `db.employees` — the roster is owned by HR portal writes.
    for banned in ("db.employees.insert", "db.employees.update_one",
                   "db.employees.delete"):
        assert banned not in src, \
            f"Track 19.21 must not mutate db.employees. Found: {banned}"
