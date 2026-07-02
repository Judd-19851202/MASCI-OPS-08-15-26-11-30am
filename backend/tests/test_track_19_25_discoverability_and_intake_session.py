"""Track 19.25 · Historical Records Intake Discoverability + Intake Session

Locks the additive nav wiring across HR / Safety / Shop hubs, the human
guidance on the intake landing page, and the Intake Session provenance
that reduces repetitive typing during bulk historical imports.

Zero drift:
- No new backend routes (session fields are additive on existing models).
- No new pages.
- No OCR / AI / fuzzy imports anywhere in Track 19.25 code.
- Employee source of truth untouched.
"""
from __future__ import annotations

from pathlib import Path


HR_SIDEBAR = Path("/app/frontend/src/components/hr/sidebar/HrSideNavV2.jsx")
SAFETY_SIDEBAR = Path("/app/frontend/src/components/safety/sidebar/SafetySideNavV2.jsx")
SHOP_HUB = Path("/app/frontend/src/pages/ShopHubV2.jsx")
INTAKE = Path("/app/frontend/src/pages/HistoricalRecordsIntake.jsx")
BATCHES = Path("/app/frontend/src/pages/HistoricalRecordsBatches.jsx")
BATCH_DETAIL = Path("/app/frontend/src/pages/HistoricalRecordsBatchDetail.jsx")
EMP_PROFILE = Path("/app/frontend/src/pages/EmployeeProfile.jsx")
BACKEND = Path("/app/backend/routes/employee_records.py")


# ── Phase 2 · HR nav ─────────────────────────────────────────────────
def test_hr_nav_has_bulk_intake_entry():
    src = HR_SIDEBAR.read_text(encoding="utf-8")
    assert "/hr/historical-records/batches" in src
    assert "Bulk Historical Intake" in src


def test_hr_nav_bulk_intake_within_compliance_group():
    src = HR_SIDEBAR.read_text(encoding="utf-8")
    ix = src.index('id: "compliance-records"')
    end = src.index('id: "guidance"')
    body = src[ix:end]
    assert "/hr/historical-records/intake" in body
    assert "/hr/historical-records/queue" in body
    assert "/hr/historical-records/batches" in body


# ── Phase 3 · Safety nav ─────────────────────────────────────────────
def test_safety_nav_has_historical_records_entries():
    src = SAFETY_SIDEBAR.read_text(encoding="utf-8")
    ix = src.index('id: "compliance-records"')
    body = src[ix:ix + 2500]
    assert "Safety Records Intake" in body
    assert "Safety Records Queue" in body
    assert "Bulk Historical Intake" in body
    assert "/hr/historical-records/intake" in body
    assert "/hr/historical-records/queue" in body
    assert "/hr/historical-records/batches" in body


# ── Phase 4 · Asset Administrator surface (Shop hub) ─────────────────
def test_shop_hub_v2_has_asset_records_section():
    src = SHOP_HUB.read_text(encoding="utf-8")
    assert 'data-testid="shop-hub-v2-section-asset-records"' in src
    # HubCard forwards `testid` prop → data-testid on the anchor.
    for tid in ("shop-hub-v2-asset-intake", "shop-hub-v2-asset-queue",
                "shop-hub-v2-asset-batches"):
        assert f'testid="{tid}"' in src, f"Missing HubCard testid: {tid}"
    # Human-facing labels — no IT jargon.
    assert 'Asset Records Intake' in src
    assert 'Asset Records Queue' in src


# ── Phase 5 · Intake landing page clarity ────────────────────────────
def test_intake_page_declares_what_you_can_upload_chips():
    src = INTAKE.read_text(encoding="utf-8")
    assert 'data-testid="intake-what-you-can-upload"' in src
    # A handful of the human-language chips MUST be present.
    for chip in ("Employee Write-Up", "Training Certificate", "Incident Report",
                 "PPE Issue Record", "Tool Issue Record",
                 "Phone / Tablet / iPad", "Survey Equipment",
                 "Driver Qualification", "Policy Acknowledgement",
                 "Termination"):
        assert f'"{chip}"' in src, f"Missing upload-type chip: {chip}"


def test_intake_page_declares_three_step_how_it_works():
    src = INTAKE.read_text(encoding="utf-8")
    assert 'data-testid="intake-how-it-works"' in src
    for step in ("Upload", "Link", "Approve"):
        assert f"<b>{{t(\"{step}\")}}</b>" in src, f"Missing step label: {step}"


# ── Phase 6 · Intake Session foundation ──────────────────────────────
def test_backend_batch_model_declares_session_fields():
    src = BACKEND.read_text(encoding="utf-8")
    assert "class CreateBatchBody(BaseModel):" in src
    body_ix = src.index("class CreateBatchBody(BaseModel):")
    body = src[body_ix:body_ix + 800]
    assert "source_name" in body
    assert "source_type" in body
    assert "source_location" in body


def test_backend_batch_upload_inherits_session_provenance_onto_records():
    src = BACKEND.read_text(encoding="utf-8")
    # Every uploaded record must inherit intake_source_name/type/location
    # + intake_batch_label so provenance is preserved end-to-end.
    for key in ("intake_source_name", "intake_source_type",
                "intake_source_location", "intake_batch_label"):
        assert f'"{key}"' in src, f"Missing session field: {key}"


def test_batches_page_collects_session_provenance():
    src = BATCHES.read_text(encoding="utf-8")
    for tid in ("batches-new-session-provenance",
                "batches-new-source-name",
                "batches-new-source-type",
                "batches-new-source-location"):
        assert f'data-testid="{tid}"' in src, f"Missing form field: {tid}"


def test_batch_detail_surfaces_session_provenance():
    src = BATCH_DETAIL.read_text(encoding="utf-8")
    assert 'data-testid="batch-detail-provenance"' in src


def test_employee_profile_doc_card_surfaces_intake_source():
    src = EMP_PROFILE.read_text(encoding="utf-8")
    assert "intake_source_name" in src


# ── Phase 8 · Zero-drift · no OCR/AI/fuzzy in any Track 19.25 code ───
def test_track_19_25_touches_no_ml_libraries():
    for p in (INTAKE, BATCHES, BATCH_DETAIL, HR_SIDEBAR, SAFETY_SIDEBAR,
              SHOP_HUB, EMP_PROFILE, BACKEND):
        src = p.read_text(encoding="utf-8").lower()
        for banned in ("tesseract", "rapidfuzz", "litellm", "opencv"):
            assert banned not in src, f"{p.name} references {banned!r}"


def test_employee_records_still_does_not_mutate_employees_or_incidents():
    src = BACKEND.read_text(encoding="utf-8")
    for banned in ("db.employees.insert", "db.employees.update_one",
                   "db.employees.delete", "db.incident_cases.insert",
                   "db.incident_cases.update", "db.incident_cases.delete"):
        assert banned not in src


def test_employee_records_audit_ledger_remains_append_only():
    src = BACKEND.read_text(encoding="utf-8")
    for banned in ("db.employee_record_audit.update",
                   "db.employee_record_audit.delete",
                   "db.employee_record_audit.replace"):
        assert banned not in src
