"""TRACK 14.0-DISCOVERABILITY-FINALIZATION

Regression-lock tests for the final discoverability cleanup pass:
  · D-A15 — Operational Records + Operations Actions in Admin V1 sidebar
  · D-A16 — Field Leadership Portal Dashboard exposes leadership launchers
  · D-A20 — HR Hub + KPI strip no longer shell-hop to /safety-portal/...
  · Spanish synonyms (registros, acciones, liderazgo, vencimientos)
"""
from __future__ import annotations

from pathlib import Path


# ─── Paths ───────────────────────────────────────────────────────────

FRONTEND = Path("/app/frontend/src")
BACKEND = Path("/app/backend")

ADMIN_SHELL = FRONTEND / "components" / "AdminShell.jsx"
HR_HUB = FRONTEND / "pages" / "HrHubV2.jsx"
HR_KPI = FRONTEND / "components" / "HrKpiStrip.jsx"
FL_DASH = FRONTEND / "pages" / "FieldLeadershipPortalDashboard.jsx"
GLOBAL_SEARCH = BACKEND / "routes" / "global_search.py"


# ─── D-A15 Admin V1 sidebar parity ──────────────────────────────────

def test_admin_v1_sidebar_has_operational_records():
    src = ADMIN_SHELL.read_text()
    assert 'to: "/operational-records"' in src, (
        "D-A15: Admin V1 sidebar SECTIONS must include /operational-records "
        "so admins can reach Phase V.1 records without typing the URL."
    )
    assert "Operational Records" in src


def test_admin_v1_sidebar_has_operations_actions():
    src = ADMIN_SHELL.read_text()
    assert 'to: "/operations-actions"' in src, (
        "D-A15: Admin V1 sidebar must include /operations-actions."
    )
    assert "Operations Actions" in src


def test_admin_v1_section_keys_unique():
    src = ADMIN_SHELL.read_text()
    # Extract every "key: \"...\"" inside the SECTIONS array.
    import re
    keys = re.findall(r'\{\s*key:\s*"([^"]+)"', src)
    assert keys, "Could not parse Admin sidebar SECTIONS"
    duplicates = [k for k in set(keys) if keys.count(k) > 1]
    assert not duplicates, f"Admin sidebar has duplicate section keys: {duplicates}"


# ─── D-A16 FL Portal launchers ──────────────────────────────────────

REQUIRED_FL_LEADERSHIP_KINDS = (
    "recognition", "write_up", "verbal_coaching",
    "attendance", "equipment_checkout", "new_employee_eval",
    "crew_eval", "promotion_recommendation", "training_deficiency",
)


def test_fl_portal_exposes_leadership_launcher_card():
    src = FL_DASH.read_text()
    assert 'data-testid="fl-leadership-launchers"' in src, (
        "D-A16: FL Portal Dashboard must surface a Leadership submissions "
        "launcher card so foremen don't need to leave the portal."
    )


def test_fl_portal_has_each_leadership_form_launcher():
    src = FL_DASH.read_text()
    for kind in REQUIRED_FL_LEADERSHIP_KINDS:
        assert f"/leadership/{kind}/new" in src, (
            f"D-A16: FL Portal Dashboard missing launcher for /leadership/{kind}/new"
        )
        assert f'"fl-launch-{kind}"' in src, (
            f"D-A16: FL Portal launcher missing data-testid for {kind}"
        )


# ─── D-A20 HR cross-portal canonical link target ────────────────────

def test_hr_hub_v2_uses_canonical_document_expirations_route():
    src = HR_HUB.read_text()
    assert "/safety-portal/document-expirations" not in src, (
        "D-A20: HR Hub V2 must NOT link to /safety-portal/document-expirations "
        "(forces shell hop). Use /document-expirations (cross-portal canonical)."
    )
    assert 'to="/document-expirations"' in src, (
        "D-A20: HR Hub V2 must link to /document-expirations"
    )


def test_hr_kpi_strip_uses_canonical_document_expirations_route():
    src = HR_KPI.read_text()
    assert "/safety-portal/document-expirations" not in src, (
        "D-A20: HrKpiStrip must NOT link to /safety-portal/document-expirations"
    )
    assert 'to="/document-expirations"' in src, (
        "D-A20: HrKpiStrip must link to /document-expirations"
    )


# ─── Spanish synonyms — finalization terms ──────────────────────────

def test_spanish_synonyms_for_records_actions_leadership_expirations():
    from routes.global_search import ES_EN_SYNONYMS  # noqa: WPS433
    required = {
        "registros": "record",
        "acciones": "action",
        "liderazgo": "leadership",
        "vencimientos": "expiration",
        "expiraciones": "expiration",
        "certificaciones": "certification",
        "capacitacion": "training",
        "entrenamiento": "training",
    }
    for es, en in required.items():
        assert es in ES_EN_SYNONYMS, (
            f"Spanish synonym '{es}' missing from ES_EN_SYNONYMS (D-A15/16/20 search certification)"
        )
        assert any(en in alt for alt in ES_EN_SYNONYMS[es]), (
            f"Synonym '{es}' must expand to '{en}'; got {ES_EN_SYNONYMS[es]}"
        )
