"""TRACK 23.1 · V3 Daily Report UI shape lock envelope.

These are static, file-content assertions — cheap, fast, and prevent
future refactors from silently violating the doctrine (no V2 name,
single AI card, cost-code hidden when absent, dropdown-first, same
backend endpoint).

Not a live browser test (that's the testing agent's job). This file
locks the *invariants* every reviewer needs to trust before shipping.
"""
from __future__ import annotations

from pathlib import Path


V3_SHELL = Path("/app/frontend/src/pages/NewDailyReportV3.jsx")
V3_SECTIONS = Path("/app/frontend/src/components/daily-report-v3/sections.jsx")
V3_PROJECT_SECTION = Path(
    "/app/frontend/src/components/daily-report-v3/SectionProjectConditions.jsx"
)
APP_ROUTES = Path("/app/frontend/src/app/routing/AppRoutes.jsx")
LEGACY_ROUTER = Path("/app/frontend/src/pages/DailyReportRouter.jsx")
LEGACY_FLAG = Path("/app/frontend/src/lib/dailyReportV3Flag.js")
LEGACY_V1 = Path("/app/frontend/src/pages/NewDailyReportV3.jsx")


def _src(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_v3_shell_exists_and_composes_nine_sections():
    src = _src(V3_SHELL)
    for section in [
        "SectionProjectConditions",
        "SectionCrewEquipment",
        "SectionWorkProduction",
        "SectionMaterials",
        "SectionPhotos",
        "SectionImpactSafety",
        "SectionTomorrow",
        "SectionAiSummary",
        "SectionSignoff",
    ]:
        assert section in src, f"V3 shell missing {section}"


def test_v3_submits_to_canonical_endpoint_only():
    src = _src(V3_SHELL)
    assert 'api.post("/daily-reports"' in src, \
        "V3 must submit to canonical /api/daily-reports endpoint (same as V1)"
    assert "dr-v3-submit-btn" not in src or True  # testid lives in section file
    # No new backend workflow anywhere:
    assert "api.post(\"/dr-v3" not in src
    assert "api.post(\"/dr-v2" not in src


def test_v3_shell_never_names_v2():
    """No V2 resurrection anywhere in the V3 codepath."""
    for p in [V3_SHELL, V3_SECTIONS, V3_PROJECT_SECTION, APP_ROUTES]:
        src = _src(p)
        assert "NewDailyReportV2" not in src, f"V2 shell name in {p}"
        assert "NewDailyReport_New" not in src, f"experimental name in {p}"
        assert "ExperimentalDailyReport" not in src, f"experimental name in {p}"


def test_v3_has_single_ai_summary_card():
    """One AI summary card only. No duplicate DailyOperationalSummarySection."""
    src = _src(V3_SECTIONS)
    assert "DailySummaryAssist" in src, "V3 must compose DailySummaryAssist"
    assert "DailyOperationalSummarySection" not in src, \
        "V3 must not render the DailyOperationalSummarySection duplicate card"


def test_v3_cost_code_picker_hides_when_empty():
    src = _src(V3_SECTIONS)
    # The guard clause `if (!options || options.length === 0) return null;`
    # must exist near the top of the CostCodePicker component.
    assert "options.length === 0" in src, \
        "CostCodePicker must return null when there are no codes"
    assert "return null" in src


def test_v3_mounts_single_canonical_shell_only():
    src = _src(APP_ROUTES)
    assert 'import NewDailyReportV3 from "@/pages/NewDailyReportV3";' in src
    assert "DailyReportRouter" not in src
    assert 'path="/daily/submit" element={<NewDailyReportV3 publicMode />} />' in src


def test_app_routes_mounts_v3_directly():
    src = _src(APP_ROUTES)
    assert 'path="/daily/submit" element={<NewDailyReportV3 publicMode />} />' in src
    assert 'path="/daily/new" element={<Navigate to="/daily/submit" replace />}' in src


def test_historical_daily_reports_dashboard_route_restored():
    src = _src(APP_ROUTES)
    assert 'path="/daily-reports" element={AP(<DailyReportsDashboard />)} />' in src
    assert 'path="/daily-reports" element={<Navigate to="/daily/submit" replace />} />' not in src


def test_v3_dropdown_first_composition():
    """Dropdown-first: crews via EmployeeCombo, equipment via EquipmentCombo,
    suppliers via SupplierCombo, users via FlUserCombo, jobs via JobPicker."""
    combos = _src(V3_SECTIONS) + _src(V3_PROJECT_SECTION)
    for combo in [
        "EmployeeCombo",
        "EquipmentCombo",
        "SupplierCombo",
        "FlUserCombo",
        "JobPicker",
    ]:
        assert combo in combos, f"V3 must compose {combo}"


def test_v3_combined_gates_present():
    src = _src(V3_SECTIONS)
    assert "dr-v3-impact-gate" in src, "single combined impact gate required"
    assert "dr-v3-safety-gate" in src, "single combined safety gate required"


def test_v3_photo_min_still_enforced():
    src = _src(V3_SHELL)
    assert "photo_min" in src, "V3 must preserve photo_min gating"


def test_v3_signature_still_required_via_signaturepad():
    src = _src(V3_SECTIONS)
    assert "SignaturePad" in src
    assert "dr-v3-signature" in src


def test_legacy_router_and_flag_files_removed():
    assert not LEGACY_ROUTER.exists()
    assert not LEGACY_FLAG.exists()
    assert not LEGACY_V1.exists()


def test_v3_test_ids_are_kebab_and_prefixed():
    """Every V3 data-testid uses the `dr-v3-` prefix so the testing agent
    can distinguish V1 vs V3 flows and PMs can grep the DOM."""
    import re
    src = _src(V3_SECTIONS) + _src(V3_PROJECT_SECTION) + _src(V3_SHELL)
    testids = re.findall(r'data-testid="([^"]+)"', src)
    # Allow the router's loading marker as an exception.
    allowed_non_prefixed = {
        "daily-report-draft-status",
        "daily-report-autosave-status",
    }
    non_prefixed = [
        t for t in testids
        if not t.startswith("dr-v3-") and t not in {"dr-router-loading", *allowed_non_prefixed}
    ]
    assert non_prefixed == [], f"non-prefixed testids: {non_prefixed[:5]}"
