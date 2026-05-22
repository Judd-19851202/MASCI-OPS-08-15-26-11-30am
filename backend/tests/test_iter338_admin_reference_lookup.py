"""
test_iter338_admin_reference_lookup.py — Regression lock for iter338.

Asserts:
  - Backend GET /api/admin/lookup route exists in admin_ops.py
  - LOOKUP_MAP covers all 9 expected collections
  - Route is admin-gated (uses require_admin)
  - Frontend AdminReferenceLookup component exists with required testids
  - AdminSystem mounts the component
  - i18n contains the 7 ES keys
"""
from pathlib import Path

ROOT = Path("/app")
ADMIN_OPS = ROOT / "backend/routes/admin_ops.py"
COMP = ROOT / "frontend/src/components/AdminReferenceLookup.jsx"
ADMIN_SYSTEM = ROOT / "frontend/src/pages/admin/AdminSystem.jsx"
I18N = ROOT / "frontend/src/lib/i18n.js"


def test_backend_route_present():
    src = ADMIN_OPS.read_text()
    assert '@router.get("/lookup", dependencies=[Depends(require_admin)])' in src
    assert "async def admin_lookup_ref" in src
    assert "LOOKUP_MAP = [" in src


def test_lookup_map_covers_nine_collections():
    src = ADMIN_OPS.read_text()
    expected = [
        ("incidents", "incident_number"),
        ("daily_reports", "report_number"),
        ("inspections", "inspection_number"),
        ("meetings", "meeting_number"),
        ("equipment_inspections", "inspection_number"),
        ("jhas", "jha_number"),
        ("safety_equipment_issuances", "issuance_number"),
        ("safety_training_records", "training_number"),
        ("field_leadership_records", "record_number"),
    ]
    for coll, field in expected:
        assert f'"{coll}"' in src and f'"{field}"' in src, f"missing {coll}/{field}"


def test_uuid_fallback_present():
    src = ADMIN_OPS.read_text()
    # the fallback loop iterates LOOKUP_MAP and looks up by raw `id`
    assert 'await coll.find_one({"id": ref.strip()}' in src


def test_graceful_miss_response():
    src = ADMIN_OPS.read_text()
    assert '{"found": False, "ref": needle}' in src


def test_frontend_component_exists_with_testids():
    src = COMP.read_text()
    for tid in (
        'data-testid="admin-reference-lookup"',
        'data-testid="admin-lookup-input"',
        'data-testid="admin-lookup-submit"',
        'data-testid="admin-lookup-error"',
    ):
        assert tid in src, f"missing {tid}"
    # Uses real API client + navigate
    assert 'api.get("/admin/lookup"' in src
    assert "useNavigate" in src and "navigate(r.data.path)" in src


def test_admin_system_mounts_lookup():
    src = ADMIN_SYSTEM.read_text()
    assert 'import AdminReferenceLookup from "@/components/AdminReferenceLookup"' in src
    assert "<AdminReferenceLookup />" in src


def test_es_translations_present():
    src = I18N.read_text()
    for key in (
        '"Admin Utility": "Utilidad de Admin"',
        '"Find Record by Ref": "Buscar Registro por Ref."',
        '"Paste a canonical reference to jump straight to the record."',
        '"Paste Ref · INC-2026-0517-002"',
        '"Find": "Buscar"',
        '"No active record matches Ref": "Ningún registro activo coincide con Ref."',
        '"Lookup unavailable. Try again in a moment."',
    ):
        assert key in src, f"missing ES key: {key}"


def test_no_public_lookup_route_in_app_js():
    """Guard rail — no public /lookup or /track route was sneaked in."""
    app_js = (ROOT / "frontend/src/App.js").read_text()
    for forbidden in ('path="/lookup"', 'path="/track"', 'path="/reference/'):
        assert forbidden not in app_js, f"forbidden public route: {forbidden}"
