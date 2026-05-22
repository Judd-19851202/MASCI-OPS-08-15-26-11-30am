"""
iter330 · Final Pre-Deploy Hard-Use Verification — Dispatch KPI Calm Pass

Anti-drift regression for the one defect surfaced during the pre-deploy
sweep: AdminDispatch.jsx KPI strip (8 cards) was rendering with heavy
`border-2 border-<accent>-300` chrome, violating the family-contract
Rule-5 neutral KPI pattern (see UX_PLATFORM_FAMILY_REFERENCE.md).

Fix applied in /app/frontend/src/pages/admin/AdminDispatch.jsx:
   bg-white border-2 ${c.cls} rounded-md p-4   →
   bg-white border border-slate-200 border-l-4 ${c.stripe} rounded-md p-4

This test asserts the fix is present and the legacy chrome is absent.
"""
from pathlib import Path

DISPATCH_OVERVIEW = Path(__file__).resolve().parents[2] / "frontend" / "src" / "pages" / "admin" / "AdminDispatch.jsx"


def test_dispatch_kpi_file_exists():
    assert DISPATCH_OVERVIEW.exists(), f"Missing {DISPATCH_OVERVIEW}"


def test_dispatch_kpi_strip_uses_calm_pattern():
    """KPI cards must render with neutral `border border-slate-200` +
    `border-l-4` left-edge stripe — the family-contract Rule-5 pattern."""
    src = DISPATCH_OVERVIEW.read_text(encoding="utf-8")
    assert "border border-slate-200 border-l-4" in src, (
        "Dispatch KPI strip missing calm left-edge stripe pattern"
    )


def test_dispatch_kpi_strip_no_heavy_chrome():
    """Forbid the legacy `border-2 ${c.cls}` template inside the KPI grid."""
    src = DISPATCH_OVERVIEW.read_text(encoding="utf-8")
    # The full forbidden template (avoid false-positives on input fields).
    assert "border-2 ${c.cls}" not in src, (
        "AdminDispatch.jsx still uses legacy `border-2 ${c.cls}` KPI chrome"
    )


def test_dispatch_kpi_uses_stripe_keys():
    """Every KPI card declaration must carry a `stripe:` key matching the
    family-contract palette."""
    src = DISPATCH_OVERVIEW.read_text(encoding="utf-8")
    expected_stripes = (
        "border-l-slate-500",
        "border-l-emerald-500",
        "border-l-blue-500",
        "border-l-cyan-500",
        "border-l-violet-500",
        "border-l-red-500",
        "border-l-amber-500",
    )
    for s in expected_stripes:
        assert s in src, f"Missing expected stripe color: {s}"


def test_dispatch_kpi_colored_value_text():
    """Values use colored text classes (`text-<color>-700`) per family pattern."""
    src = DISPATCH_OVERVIEW.read_text(encoding="utf-8")
    for cls in ("text-emerald-700", "text-blue-700", "text-cyan-700",
                "text-violet-700", "text-red-700", "text-amber-700"):
        assert cls in src, f"Missing colored value class: {cls}"
