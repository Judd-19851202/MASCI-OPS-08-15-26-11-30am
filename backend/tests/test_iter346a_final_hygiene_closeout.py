"""
test_iter346a_final_hygiene_closeout.py — Regression lock for iter346-A.

FINAL OPTIONAL CLOSEOUT · Part A:
  1. Shared `operationalError()` sanitizer applied to the 27 admin-internal
     catch blocks (19 files / 30 sites). No raw FastAPI-detail leakage.
  2. EDIT PROJECT English leak in ES fixed — EditProjectDialog wraps every
     visible string in `t()` and 8 new ES keys present.
  3. Admin Access Control quick-stats tile mounted on `/admin/people`,
     reads existing `/api/admin/directory` (no new backend endpoint),
     surfaces total users / total grants / cross-portal / disabled.
"""
from pathlib import Path

ROOT = Path("/app")
FRONTEND_SRC = ROOT / "frontend/src"
I18N = FRONTEND_SRC / "lib/i18n.js"
ERRORS_LIB = FRONTEND_SRC / "lib/errors.js"
EDIT_PROJ = FRONTEND_SRC / "components/EditProjectDialog.jsx"
ACCESS_STATS = FRONTEND_SRC / "components/AdminAccessStatsTile.jsx"
ADMIN_PEOPLE = FRONTEND_SRC / "pages/admin/AdminPeople.jsx"

# 19 admin-internal files that previously leaked raw `e.response.data.detail`
ADMIN_FILES = [
    "components/AdminJobMasterPanel.jsx",
    "components/CrewRecoveryPanel.jsx",
    "components/PreDeploySnapshotPanel.jsx",
    "components/AdminSafetyFormsPanel.jsx",
    "components/CloudArchivesPanel.jsx",
    "components/AdminPMPanel.jsx",
    "components/BackupHeroPanel.jsx",
    "components/PersistenceHealthBanner.jsx",
    "components/DateAuditPanel.jsx",
    "components/StoredBackupsPanel.jsx",
    "components/EquipmentMasterPanel.jsx",
    "components/MasterListPanel.jsx",
    "pages/admin/AdminDigestConfig.jsx",
    "pages/admin/AdminIntegrationCenter.jsx",
    "pages/admin/AdminAuditLog.jsx",
    "pages/admin/SystemHealth.jsx",
    "pages/admin/AdminSessions.jsx",
    "pages/admin/DeployRecovery.jsx",
    "pages/AdminTrainingVideos.jsx",
]


def test_no_raw_detail_leak_in_admin_panels():
    """Every admin-internal `toast.error(e?.response?.data?.detail ...)` is gone."""
    for rel in ADMIN_FILES:
        src = (FRONTEND_SRC / rel).read_text()
        assert "toast.error(e?.response?.data?.detail" not in src, (
            f"{rel} still leaks raw FastAPI detail"
        )


def test_admin_files_import_operational_error():
    """Each admin file now routes through the shared sanitizer."""
    for rel in ADMIN_FILES:
        src = (FRONTEND_SRC / rel).read_text()
        assert 'import { operationalError } from "@/lib/errors"' in src, (
            f"{rel} missing operationalError import"
        )
        assert "operationalError(e," in src, (
            f"{rel} not using operationalError() in catch blocks"
        )


def test_shared_errors_lib_intact():
    """The shared sanitizer is still the single source of truth."""
    src = ERRORS_LIB.read_text()
    assert "export function operationalError" in src
    assert "RAW_FASTAPI_DEFAULTS" in src
    for raw in (
        "Not Found",
        "Method Not Allowed",
        "Internal Server Error",
        "Unprocessable Entity",
    ):
        assert f'"{raw}"' in src


# ── iter346-A · Part 2 · EDIT PROJECT ES leak ────────────────────────


def test_edit_project_dialog_uses_t():
    """Every visible string in EditProjectDialog now flows through t()."""
    src = EDIT_PROJ.read_text()
    # Hook wired
    assert 'import { useT } from "@/lib/i18n"' in src
    assert "const { t } = useT();" in src
    # Wrapped strings
    for key in [
        '{t("Edit Project")}',
        '{t("Re-tag this report")}',
        '{t("Currently filed under")}',
        '{t("Move to")}',
        '{t("Cancel")}',
        ': t("Save")',
        't("Project name is required")',
        't("Project updated")',
        't("Failed to update project — try again")',
    ]:
        assert key in src, f"EditProjectDialog missing wrapped key: {key}"
    # No raw English leak in JSX for the previously bare strings
    assert "> Edit Project\n" not in src
    assert "Re-tag this report\n" not in src
    # Sanitizer wired here too
    assert "operationalError(e," in src


def test_edit_project_es_keys_present():
    """8 new ES translations for EditProjectDialog landed in i18n.js."""
    src = I18N.read_text()
    pairs = [
        ('"Edit Project":', '"Editar Proyecto"'),
        ('"Re-tag this report":', '"Re-etiquetar este reporte"'),
        ('"Currently filed under":', '"Actualmente archivado bajo"'),
        ('"Move to":', '"Mover a"'),
        ('"Project name is required":', '"Se requiere el nombre del proyecto"'),
        ('"Project updated":', '"Proyecto actualizado"'),
        ('"Failed to update project — try again":', '"No se pudo actualizar el proyecto — intenta de nuevo"'),
    ]
    for k, v in pairs:
        assert k in src and v in src, f"i18n missing pair {k} → {v}"


# ── iter346-A · Part 3 · Access Control quick-stats tile ─────────────


def test_access_stats_tile_component_exists():
    """AdminAccessStatsTile.jsx mounted with required testids."""
    assert ACCESS_STATS.exists()
    src = ACCESS_STATS.read_text()
    assert 'data-testid="admin-access-stats-tile"' in src
    assert 'testid="admin-access-stat-total"' in src
    assert 'testid="admin-access-stat-grants"' in src
    assert 'testid="admin-access-stat-crossportal"' in src
    assert 'testid="admin-access-stat-disabled"' in src
    # Reads the existing endpoint (no new backend)
    assert 'api.get("/admin/directory")' in src
    # Uses shared sanitizer
    assert "operationalError(e," in src
    # Uses t() for ES parity
    assert 'useT' in src and 't("Access Control · Quick Stats")' in src


def test_access_stats_tile_mounted_on_admin_people():
    """The tile is rendered above AdminAccessControlPanel on /admin/people."""
    src = ADMIN_PEOPLE.read_text()
    assert 'import AdminAccessStatsTile' in src
    assert "<AdminAccessStatsTile />" in src
    # Order check — stats tile renders BEFORE the access control panel
    stats_idx = src.index("<AdminAccessStatsTile />")
    panel_idx = src.index("<AdminAccessControlPanel />")
    assert stats_idx < panel_idx, "stats tile must render above access control panel"


def test_access_stats_es_keys_present():
    """6 new ES keys for the stats tile landed in i18n.js."""
    src = I18N.read_text()
    pairs = [
        ('"Access Control · Quick Stats":', '"Control de Acceso · Estadísticas Rápidas"'),
        ('"Total Users":', '"Usuarios Totales"'),
        ('"Total Grants":', '"Permisos Totales"'),
        ('"Cross-Portal":', '"Multi-Portal"'),
        ('"Disabled":', '"Deshabilitados"'),
        ('"Access stats temporarily unavailable.":', '"Estadísticas de acceso no disponibles temporalmente."'),
    ]
    for k, v in pairs:
        assert k in src and v in src, f"i18n missing pair {k} → {v}"


def test_no_new_admin_directory_endpoint():
    """No new backend endpoint added — tile uses existing /api/admin/directory."""
    auth_dir = (ROOT / "backend/routes/auth_directory_routes.py").read_text()
    # Existing GET endpoint must still be there
    assert '@router.get("/api/admin/directory"' in auth_dir
    # No new "stats" endpoint snuck in
    assert '@router.get("/api/admin/directory/stats"' not in auth_dir
    assert '@router.get("/api/admin/access-stats"' not in auth_dir
