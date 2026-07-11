"""
TRACK 28.08 · Responsive Platform Standard · Regression Contract

Structural (source-level) invariants that lock the platform-wide responsive
contract established during Track 28.08 Phase 15. Complements the
device-walk in `test_track_28_08_phase0_defects.py`.

Rules enforced by this suite:
  1. The shared responsive primitives file exists and exports the five
     canonical primitives (`ResponsiveSummaryStrip`, `ResponsiveKpiRow`,
     `ResponsiveActionRow`, `ResponsiveFilterRow`, `ResponsiveOverflowMenu`).
  2. No new PortalShell-family page introduces a `ml-auto flex items-center`
     row without wrap tokens (`flex-wrap` OR `md:ml-auto` for late alignment).
     This is the exact pattern that produced the 402-px overflow on /admin
     during Phase 0 re-verify — the AST-safe way to prevent it recurring is
     to scan for the anti-pattern and only permit it when accompanied by
     `flex-wrap` on the same element.
  3. PortalShell keeps its responsive contract (delegated to
     `test_track_28_08_phase0_defects.py`).

Every violation MUST include enough context in the assertion message that
another agent can act on it without opening the source file first.
"""

from __future__ import annotations

import re
from pathlib import Path

FRONTEND = Path("/app/frontend/src")
DS = FRONTEND / "design-system"
PAGES = FRONTEND / "pages"
PORTALS = FRONTEND / "portals"

RESPONSIVE = DS / "responsive.jsx"


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


# ------------------------------------------------------------------
# Contract 1 — shared primitives exist and are exported.
# ------------------------------------------------------------------

def test_responsive_primitives_file_exists():
    assert RESPONSIVE.exists(), (
        "Responsive Platform Standard file `design-system/responsive.jsx` "
        "is missing. It must exist and export the five canonical primitives."
    )


def test_responsive_primitives_all_exported():
    src = _read(RESPONSIVE)
    for name in [
        "ResponsiveSummaryStrip",
        "ResponsiveKpiRow",
        "ResponsiveActionRow",
        "ResponsiveFilterRow",
        "ResponsiveOverflowMenu",
        "ResponsiveLongText",
    ]:
        assert re.search(rf"export function {name}\b", src), (
            f"Responsive primitive `{name}` is missing from "
            f"`design-system/responsive.jsx`. Do not delete or rename it — "
            "consumers across every portal depend on it."
        )


def test_responsive_primitives_carry_data_attribute():
    """Every primitive stamps a `data-responsive-primitive` attribute so
    the device walk can locate which pages have adopted the contract."""
    src = _read(RESPONSIVE)
    for marker in [
        'data-responsive-primitive="summary-strip"',
        'data-responsive-primitive="kpi-row"',
        'data-responsive-primitive="action-row"',
        'data-responsive-primitive="filter-row"',
        'data-responsive-primitive="overflow-menu-trigger"',
        'data-responsive-primitive="overflow-menu-content"',
        'data-responsive-primitive="long-text"',
    ]:
        assert marker in src, (
            f"Responsive primitive is missing `{marker}` — the attribute "
            "is used by the mobile device walk to certify adoption."
        )


# ------------------------------------------------------------------
# Contract 2 — anti-pattern scanner: `ml-auto flex items-center`
# without `flex-wrap` on the same className string.
# ------------------------------------------------------------------

# Files where legacy layout is intentionally single-row (opt-in allowlist).
# Adding a file here requires justification in the pull-request notes.
ALLOWLIST = {
    # Login pages don't render PortalShell chrome — safe.
    "auth/AdminLogin.jsx",
    "auth/HRLogin.jsx",
    "auth/FLLogin.jsx",
}

ANTI_PATTERN = re.compile(
    r"className\s*=\s*\"([^\"]*\bml-auto\b[^\"]*\bflex\b[^\"]*\bitems-center\b[^\"]*)\""
)

# ------------------------------------------------------------------
# Baseline legacy allowlist — files that already carried `ml-auto flex
# items-center` rows before Track 28.08. These rows will be verified by
# Phase 15's device walk instead. This test acts as a "no NEW violations"
# gate. Adding a file here is only allowed if a corresponding device-walk
# entry proves the row does not force horizontal scroll at 390×844.
# ------------------------------------------------------------------
LEGACY_BASELINE = {
    "design-system/PortalShell.jsx",  # already gated by test_d4_portal_shell_row_has_min_width_zero
    "pages/AdminAssetThread.jsx",
    "pages/AdminMaterialLedgerQuality.jsx",
    "pages/AdminVendorThread.jsx",
    "pages/DispatchHaulLedger.jsx",
    "pages/HistoricalRecordsBatchDetail.jsx",
    "pages/HistoricalRecordsQueue.jsx",
    "pages/JhaPlansAdmin.jsx",
    "pages/NewEquipmentInspection.jsx",
    "pages/PmProjectDetail.jsx",
    "pages/SafetyCaseWorkspace.jsx",
    "pages/SafetyIncidentThread.jsx",
    "pages/ShopHub.jsx",
    "pages/admin/AdminAssetAdmin.jsx",
    "pages/admin/AdminDispatch.jsx",
    "pages/transportation/_intelligence.jsx",
}


def _iter_jsx_files():
    for root in (PAGES, PORTALS, DS):
        if not root.exists():
            continue
        for p in root.rglob("*.jsx"):
            rel = p.relative_to(FRONTEND).as_posix()
            yield p, rel


def test_no_new_ml_auto_flex_row_without_wrap():
    offenders = []
    for path, rel in _iter_jsx_files():
        if any(rel.endswith(a) for a in ALLOWLIST):
            continue
        if rel in LEGACY_BASELINE:
            continue
        text = _read(path)
        for m in ANTI_PATTERN.finditer(text):
            cls = m.group(1)
            # PASS if wrap tokens are present on the same element.
            if "flex-wrap" in cls or "md:ml-auto" in cls:
                continue
            # PASS if the element is explicitly max-width constrained.
            if "max-w-" in cls:
                continue
            line = text.count("\n", 0, m.start()) + 1
            offenders.append(f"  {rel}:{line}  ->  className=\"{cls}\"")
    assert not offenders, (
        "Responsive contract violation — the following NEW elements combine "
        "`ml-auto` + `flex items-center` on a single row without "
        "`flex-wrap` or `md:ml-auto`. This is the exact anti-pattern that "
        "caused the 402-px overflow on /admin at 390×844.\n"
        "Fix: replace with the shared `ResponsiveSummaryStrip` / "
        "`ResponsiveKpiRow` primitives from "
        "`design-system/responsive.jsx`, OR add `flex-wrap` + `min-w-0` "
        "explicitly. If you truly need a fixed-row layout, extend "
        "`LEGACY_BASELINE` in this file AND add a Phase 15 device-walk "
        "assertion proving no 390-px overflow.\n"
        "Offenders:\n" + "\n".join(offenders)
    )


def test_legacy_baseline_files_still_exist():
    """The baseline allowlist only exempts files that actually contain the
    legacy pattern. If a file has been refactored, remove it from the
    baseline so future regressions are caught."""
    for rel in LEGACY_BASELINE:
        path = FRONTEND / rel
        if not path.exists():
            continue
        text = _read(path)
        assert ANTI_PATTERN.search(text), (
            f"Legacy baseline entry `{rel}` no longer contains the "
            "`ml-auto flex items-center` pattern. Remove it from "
            "LEGACY_BASELINE so future regressions are caught."
        )


# ------------------------------------------------------------------
# Contract 3 — adoption evidence: the two Phase 0 pages that were
# manually fixed must now use the shared primitives so any future edit
# picks up wrap behavior for free.
# ------------------------------------------------------------------

def test_admin_os_adopts_responsive_summary_strip():
    admin_os = PAGES / "admin" / "AdminOS.jsx"
    src = _read(admin_os)
    # Either use the primitive directly OR keep the wrap-aware raw pattern.
    assert (
        "ResponsiveSummaryStrip" in src
        or 'className="md:ml-auto flex flex-wrap items-center gap-x-4 gap-y-2 text-sm"' in src
    ), (
        "AdminOS PlatformPosture strip lost its wrap-aware layout. Restore "
        "either the shared `ResponsiveSummaryStrip` primitive or the raw "
        "`md:ml-auto flex flex-wrap items-center gap-x-4 gap-y-2 text-sm` "
        "className."
    )


def test_operations_control_adopts_responsive_summary_strip():
    occ = PAGES / "OperationsControlCenter.jsx"
    src = _read(occ)
    assert (
        "ResponsiveSummaryStrip" in src
        or 'className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm"' in src
    ), (
        "OperationsControlCenter Trust Center summary strip lost its "
        "wrap-aware layout. Restore either the shared "
        "`ResponsiveSummaryStrip` primitive or the raw "
        "`flex flex-wrap items-center gap-x-4 gap-y-2 text-sm` className."
    )
