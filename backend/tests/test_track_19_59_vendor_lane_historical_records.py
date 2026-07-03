"""Track 19.59 · Vendor Lane on Historical Records Intake — lock test.

Verifies the small foundation extension that unlocks the Track 19.60
Vendor Operational Thread promotion.

Run in isolation:
    pytest /app/backend/tests/test_track_19_59_vendor_lane_historical_records.py -v
"""
from pathlib import Path
import sys

REPO = Path("/app")
MEM = REPO / "memory"
FE = REPO / "frontend/src"
BE = REPO / "backend"
FE_INTAKE = FE / "pages/HistoricalRecordsIntake.jsx"

# Load the extended module directly.
sys.path.insert(0, str(BE))
from routes import employee_records as er  # noqa: E402

REQUIRED_DOCS = [
    "TRACK_19_59_EXECUTIVE_SUMMARY.md",
    "TRACK_19_59_VENDOR_LANE_IMPLEMENTATION.md",
    "TRACK_19_59_ENTITY_KIND_DISCRIMINATOR.md",
    "TRACK_19_59_VENDOR_DOCUMENT_TYPE_CATALOG.md",
    "TRACK_19_59_PERMISSION_CERTIFICATION.md",
    "TRACK_19_59_EMPLOYEE_SAFETY_SENTINELS.md",
    "TRACK_19_59_VENDOR_THREAD_READINESS_CONTRACT.md",
    "TRACK_19_59_ZERO_DRIFT_MATRIX.md",
    "TRACK_19_59_TEST_REPORT.md",
]


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


# ── Doctrine ────────────────────────────────────────────────────────
def test_docs_present():
    missing = [d for d in REQUIRED_DOCS if not (MEM / d).exists()]
    assert not missing, f"missing Track 19.59 docs: {missing}"


def test_entity_kind_discriminator_exists():
    assert hasattr(er, "ENTITY_KINDS"), "ENTITY_KINDS constant must exist"
    # Track 19.59 requires `employee` + `vendor` to be present. Track 19.61
    # additively introduces `asset` as a third discriminator — the 19.59
    # doctrine still holds (vendor is a first-class entity_kind), so
    # this assertion is a superset check to remain additive-safe.
    assert {"employee", "vendor"} <= set(er.ENTITY_KINDS), \
        f"unexpected entity kinds: {er.ENTITY_KINDS}"
    assert er.DEFAULT_ENTITY_KIND == "employee", \
        "DEFAULT_ENTITY_KIND must be 'employee' for backwards compatibility"


def test_vendor_lane_added():
    assert "vendor" in er.OWNERSHIP_LANES, \
        "vendor lane must be present in OWNERSHIP_LANES"
    for original in ("hr", "safety", "asset", "corporate_import"):
        assert original in er.OWNERSHIP_LANES, \
            f"original lane {original!r} must still be present"


def test_vendor_approvers_hr_admin_only():
    approvers = er.LANE_APPROVERS.get("vendor")
    assert approvers == {"hr", "admin"}, \
        f"vendor lane approvers must be HR/Admin only, got {approvers}"


def test_vendor_document_types_catalogued():
    types = er.LANE_RECORD_TYPES.get("vendor") or []
    required = {
        "w9", "certificate_of_insurance", "contract_agreement",
        "subcontract", "rental_agreement", "service_agreement",
        "business_license", "prequalification", "vendor_packet",
        "quote_proposal", "pricing_sheet", "safety_document",
        "material_certification", "correspondence",
        "other_vendor_document",
    }
    missing = required - set(types)
    assert not missing, f"vendor catalog missing types: {missing}"


def test_vendor_types_do_not_include_legal_wording():
    types = er.LANE_RECORD_TYPES.get("vendor") or []
    banned = {"approved_to_use", "osha_ready", "compliance_ready",
              "legally_defensible", "court_ready"}
    for t in types:
        assert t not in banned, \
            f"vendor catalog must not include legal-conclusion slug: {t!r}"


# ── Payload models ─────────────────────────────────────────────────
def test_create_record_body_accepts_vendor_fields():
    src = _read(BE / "routes/employee_records.py")
    for token in ("entity_kind:", "vendor_id:", "vendor_name:",
                  "vendor_display_name:"):
        assert token in src, f"CreateRecordBody must expose {token}"


def test_create_batch_body_accepts_entity_kind():
    src = _read(BE / "routes/employee_records.py")
    assert "class CreateBatchBody" in src
    body_start = src.index("class CreateBatchBody")
    body_end = src.index("class CreateRecordBody", body_start)
    body_src = src[body_start:body_end]
    assert "entity_kind:" in body_src, \
        "CreateBatchBody must accept entity_kind"


# ── Route behavior ─────────────────────────────────────────────────
def test_vocabulary_exposes_entity_kinds():
    src = _read(BE / "routes/employee_records.py")
    assert '"entity_kinds"' in src, \
        "vocabulary response must include entity_kinds"
    assert '"default_entity_kind"' in src, \
        "vocabulary response must include default_entity_kind"


def test_list_records_supports_entity_kind_filter():
    src = _read(BE / "routes/employee_records.py")
    for token in ("entity_kind: Optional[str]",
                  "vendor_id: Optional[str]",
                  "vendor_name: Optional[str]"):
        assert token in src, f"list_records must accept {token}"


def test_list_records_defaults_to_employee_scope():
    """Backwards-compatible sentinel: vendor records never leak into
    existing employee queries."""
    src = _read(BE / "routes/employee_records.py")
    # The default-employee branch must exist somewhere in list_records.
    assert 'q_mongo["entity_kind"] = {"$in": ["employee", None]}' in src, \
        "list_records must default to employee scope when entity_kind absent"


def test_create_record_rejects_cross_lane_entity_kind():
    src = _read(BE / "routes/employee_records.py")
    assert "entity_kind='vendor' is only permitted in the 'vendor' lane" in src
    assert "'vendor' lane requires entity_kind='vendor'" in src


def test_approve_record_requires_vendor_identity_for_vendor_lane():
    src = _read(BE / "routes/employee_records.py")
    assert "Cannot approve — vendor_id or vendor_name is required" in src


def test_audit_records_entity_kind():
    src = _read(BE / "routes/employee_records.py")
    # `entity_kind` and vendor identity must be preserved in the audit
    # ledger detail dict on record_created.
    assert '"entity_kind": entity_kind' in src, \
        "audit must record entity_kind"
    assert '"vendor_id": rec.get("vendor_id")' in src, \
        "audit must preserve vendor identity"


# ── Frontend ───────────────────────────────────────────────────────
def test_frontend_intake_supports_vendor_lane():
    src = _read(FE_INTAKE)
    for token in ("intake-vendor-block", "intake-vendor-name-input",
                  "intake-vendor-id-input", "intake-vendor-owner-note",
                  'vendor: "Vendor (HR/Admin)"'):
        assert token in src, f"intake page must expose vendor UI: {token}"


def test_frontend_intake_sends_entity_kind_and_vendor_fields():
    src = _read(FE_INTAKE)
    assert 'entity_kind: lane === "vendor" ? "vendor" : "employee"' in src
    assert 'vendor_name: lane === "vendor"' in src
    assert 'vendor_id: lane === "vendor"' in src


def test_frontend_intake_hides_employee_picker_for_vendor():
    src = _read(FE_INTAKE)
    assert 'lane !== "vendor" && (' in src, \
        "employee picker must be hidden for vendor lane"


# ── Zero drift ─────────────────────────────────────────────────────
def test_no_new_backend_upload_engine():
    """No new upload engine or storage system. All extensions live in
    the existing employee_records.py router."""
    # No new route files introduced.
    routes_dir = BE / "routes"
    for banned in ("vendor_records.py", "vendor_documents.py",
                   "vendor_intake.py", "vendor_lane.py"):
        assert not (routes_dir / banned).exists(), \
            f"forbidden new module was created: {banned}"


def test_no_new_vendor_collection():
    """No new vendor collection introduced. All records go to the
    existing employee_records collection with the new discriminator."""
    src = _read(BE / "routes/employee_records.py")
    for banned in ("db.vendor_records", "db.vendor_documents",
                   "db.vendors_master", "db.ap_invoices",
                   "db.vendor_intelligence"):
        assert banned not in src, \
            f"forbidden collection reference introduced: {banned}"


def test_no_new_ap_invoice_payment_contract_engine():
    src = _read(BE / "routes/employee_records.py")
    for banned in ("class InvoiceBody", "class PaymentBody",
                   "class ContractDraftBody", "def sign_contract"):
        assert banned not in src, \
            f"forbidden AP/invoice/payment/contract engine addition: {banned}"


def test_no_oi_or_scheduler_touched():
    """No OI product / scheduler / email pipeline was touched by 19.59."""
    from pathlib import Path
    oi_dir = REPO / "backend/operational_intelligence"
    expected = {"__init__.py", "engine.py", "registry.py", "products.py",
                "score_model.py", "product_layout.py", "recipients.py",
                "routes.py", "scheduler.py"}
    actual = {f.name for f in oi_dir.glob("*.py")}
    assert actual == expected, f"OI inventory drifted: {actual ^ expected}"


def test_prior_track_docs_preserved():
    for name in (
        "TRACK_20_4_FINAL_RECOMMENDATION.md",
        "TRACK_20_4_EXECUTIVE_AUDIT.md",
        "TRACK_20_3_EXECUTIVE_AUDIT.md",
        "TRACK_20_2_EXECUTIVE_AUDIT.md",
        "TRACK_19_58_EXECUTIVE_SUMMARY.md",
        "TRACK_19_57_EXECUTIVE_SUMMARY.md",
    ):
        assert (MEM / name).exists(), f"prior track doc missing: {name}"


def test_prd_updated():
    assert "TRACK 19.59" in _read(MEM / "PRD.md")


def test_changelog_updated():
    assert "TRACK 19.59" in _read(MEM / "CHANGELOG.md")
