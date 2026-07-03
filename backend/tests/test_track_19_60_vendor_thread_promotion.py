"""Track 19.60 · Vendor Operational Thread PROMOTION — lock test.

Verifies the frontend-only promotion over the certified supplier
master + Track 19.59 vendor-lane endpoints.

Run in isolation:
    pytest /app/backend/tests/test_track_19_60_vendor_thread_promotion.py -v
"""
from pathlib import Path

REPO = Path("/app")
MEM = REPO / "memory"
FE = REPO / "frontend/src"
FE_PAGES = FE / "pages"
FE_COMP_OI = FE / "components/operational_intelligence"
BE_OI = REPO / "backend/operational_intelligence"

THREAD_PAGE = FE_PAGES / "AdminVendorThread.jsx"
APP_JS = FE / "App.js"

REQUIRED_DOCS = [
    "TRACK_19_60_EXECUTIVE_SUMMARY.md",
    "TRACK_19_60_VENDOR_THREAD_PROMOTION.md",
    "TRACK_19_60_SOURCE_OF_TRUTH.md",
    "TRACK_19_60_PERMISSION_CERTIFICATION.md",
    "TRACK_19_60_VENDOR_HEALTH_CERTIFICATION.md",
    "TRACK_19_60_DOCUMENTS_SECTION_CERTIFICATION.md",
    "TRACK_19_60_ZERO_DRIFT_MATRIX.md",
    "TRACK_19_60_TEST_REPORT.md",
]


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_docs_present():
    missing = [d for d in REQUIRED_DOCS if not (MEM / d).exists()]
    assert not missing, f"missing Track 19.60 docs: {missing}"


def test_thread_page_exists():
    assert THREAD_PAGE.exists()


def test_thread_uses_universal_shell():
    src = _read(THREAD_PAGE)
    assert "OperationalThreadPage" in src
    assert "@/components/operational_intelligence/OperationalThreadPage" in src


def test_thread_consumes_only_certified_endpoints():
    src = _read(THREAD_PAGE)
    assert "/suppliers" in src, "thread must consume /api/suppliers"
    assert "/employee-records/records" in src, \
        "thread must consume Track 19.59 vendor-lane records endpoint"
    assert 'entity_kind: "vendor"' in src, \
        "thread must scope employee-records reads to entity_kind=vendor"


def test_thread_writes_limited_to_admin_supplier_endpoint():
    """Track 19.60 amendment: the ONLY write allowed from the vendor
    thread is a PUT to /api/admin/suppliers/{id} for HR/Admin edit.
    No other writes are permitted."""
    src = _read(THREAD_PAGE)
    # No other write patterns.
    for banned in ("axios.post(", "axios.patch(", "axios.delete(",
                   'method: "POST"', 'method: "PATCH"',
                   'method: "DELETE"'):
        assert banned not in src, f"thread must not include {banned!r}"
    # PUT exists — must target admin/suppliers only.
    assert "axios.put(" in src, "amendment · thread must expose vendor edit PUT"
    assert "/admin/suppliers/${encodeURIComponent(vid)}" in src, \
        "the only PUT must target /admin/suppliers/{id}"


def test_thread_permission_admin_only():
    src = _read(THREAD_PAGE)
    assert "isAdmin()" in src, "thread must gate on isAdmin()"
    assert "AccessDenied" in src, "thread must render AccessDenied when unauthorised"
    app_src = _read(APP_JS)
    assert "A(<AdminVendorThread />)" in app_src, \
        "route must be wrapped by RequireAdmin (A)"


def test_thread_never_exposes_pm_safety_shop_paths():
    """This initial track must not create a PM / Safety / Shop route
    for the vendor thread."""
    app_src = _read(APP_JS)
    for banned in ("/pm/vendors/", "/safety/vendors/", "/shop/vendors/",
                   "/fleet/vendors/", "/dispatch/vendors/"):
        assert banned not in app_src, \
            f"forbidden consumer-role route registered: {banned}"


def test_route_registered():
    src = _read(APP_JS)
    assert '"/admin/vendors/:vendorId/thread"' in src
    assert "AdminVendorThread" in src


def test_vendor_health_is_qualitative_not_score():
    src = _read(THREAD_PAGE)
    for label in ('"Excellent"', '"Good"', '"Attention Needed"', '"Restricted"'):
        assert label in src, f"vendor health must expose {label}"
    # Must not compute a percentage or a numeric score.
    for banned in ("score:", "compliance_percent", "readinessScore",
                   "vendorScore", "toFixed(2) + '%'"):
        assert banned not in src, f"vendor thread must not compute {banned!r}"


def test_no_legal_or_osha_language():
    src = _read(THREAD_PAGE)
    for banned in ("OSHA ready", "legally defensible", "court-ready",
                   "approved for all work", "Chain of Custody"):
        assert banned not in src, \
            f"vendor thread must not use legal language: {banned!r}"


def test_documents_deep_link_reuses_original_download_endpoint():
    src = _read(THREAD_PAGE)
    assert "/employee-records/records/${encodeURIComponent(d.id)}/file" in src, \
        "documents must deep-link to the certified original-file endpoint"


def test_photos_and_history_and_audit_honest_empty():
    """Track 20.4 mandates honest-empty for photos and no vendor OI
    product. The thread must NOT pass any oiProduct/guidanceProduct
    that would fabricate a signal."""
    src = _read(THREAD_PAGE)
    assert "guidanceProduct={null}" in src
    assert "oiProduct={null}" in src


def test_upload_cross_link_present():
    src = _read(THREAD_PAGE)
    assert "admin-vendor-thread-upload-link" in src
    assert "/hr/historical-records/intake" in src


# ── Track 19.60 AMENDMENT · HR/Admin vendor management ─────────────
def test_thread_exposes_hr_admin_edit_ui():
    """Track 19.60 amendment · HR/Admin must be able to add/edit
    vendors from the Vendor Thread."""
    src = _read(THREAD_PAGE)
    for testid in ("admin-vendor-thread-edit-button",
                   "admin-vendor-thread-edit-panel",
                   "admin-vendor-thread-edit-save",
                   "admin-vendor-thread-edit-cancel",
                   "admin-vendor-thread-edit-${key}",
                   "admin-vendor-thread-edit-is-active",
                   "admin-vendor-thread-edit-do-not-use",
                   "admin-vendor-thread-queue-link"):
        assert testid in src, f"amendment · missing edit testid: {testid}"


def test_edit_writes_to_certified_supplier_source():
    """The edit call must PUT to the same certified admin/suppliers
    endpoint Admin already uses today — no duplicate vendor system."""
    src = _read(THREAD_PAGE)
    assert 'axios.put(' in src, "edit must use PUT"
    assert "/admin/suppliers/${encodeURIComponent(vid)}" in src, \
        "edit must hit the existing /admin/suppliers/{id} endpoint"


def test_edit_button_only_renders_when_admin():
    """The whole thread page is Admin-gated. Amendment satisfied by
    the existing `isAdmin()` guard + AccessDenied render for non-Admin
    roles — PM / Safety / Shop / Fleet / Field never see the edit
    button because they never reach the page in the first place."""
    src = _read(THREAD_PAGE)
    assert "if (!allowed) return <AccessDenied" in src, \
        "AccessDenied fallback must gate the entire thread page"
    # Sanity — no PM/Safety/Shop wrapper is present anywhere.
    for banned in ("isPm()", "isSafety()", "isFleet()", "isShop()"):
        assert banned not in src, \
            f"edit UI must not be reachable via {banned}"


def test_backend_supplier_endpoint_extended():
    """Amendment · POST/PUT /api/admin/suppliers must accept richer
    fields additively — no duplicate vendor system, no new collection."""
    import pathlib
    src = pathlib.Path("/app/backend/server.py").read_text(encoding="utf-8")
    assert '"vendor_type"' in src, "extended supplier endpoint must accept vendor_type"
    assert '"primary_contact"' in src, "extended supplier endpoint must accept primary_contact"
    assert '"dba"' in src, "extended supplier endpoint must accept dba"
    assert '"do_not_use"' in src, "extended supplier endpoint must accept do_not_use flag"
    assert '"updated_by"' in src, "extended supplier endpoint must persist updated_by"


def test_no_new_backend_module():
    expected = {"__init__.py", "engine.py", "registry.py", "products.py",
                "score_model.py", "product_layout.py", "recipients.py",
                "routes.py", "scheduler.py"}
    actual = {f.name for f in BE_OI.glob("*.py")}
    assert actual == expected, \
        f"OI engine inventory drifted: {actual ^ expected}"


def test_oi_component_inventory_frozen():
    expected_jsx = {"OiAttentionStrip.jsx", "GuidanceCard.jsx",
                    "AttentionChip.jsx", "TrendChip.jsx",
                    "OperationalThread.jsx",
                    "OperationalThreadPage.jsx",
                    "RelationshipGraph.jsx"}
    expected_js = {"guidanceMap.js"}
    actual_jsx = {f.name for f in FE_COMP_OI.glob("*.jsx")}
    actual_js  = {f.name for f in FE_COMP_OI.glob("*.js")}
    assert actual_jsx == expected_jsx
    assert actual_js == expected_js


def test_no_new_ap_invoice_payment_contract_engine():
    """The promotion must not sneak in new AP/invoice/payment/contract
    engine references."""
    src = _read(THREAD_PAGE)
    for banned in ("/api/ap/", "/api/invoices", "/api/payments",
                   "/api/contracts", "vendor_intelligence",
                   "signContract", "vendorScoreEngine"):
        assert banned not in src, f"forbidden reference: {banned}"


def test_prior_track_docs_preserved():
    for name in (
        "TRACK_19_59_VENDOR_THREAD_READINESS_CONTRACT.md",
        "TRACK_19_59_EXECUTIVE_SUMMARY.md",
        "TRACK_20_4_FINAL_RECOMMENDATION.md",
        "TRACK_20_3_EXECUTIVE_AUDIT.md",
        "TRACK_19_58_EXECUTIVE_SUMMARY.md",
        "TRACK_19_57_EXECUTIVE_SUMMARY.md",
    ):
        assert (MEM / name).exists(), f"prior track doc missing: {name}"


def test_prd_updated():
    assert "TRACK 19.60" in _read(MEM / "PRD.md")


def test_changelog_updated():
    assert "TRACK 19.60" in _read(MEM / "CHANGELOG.md")
