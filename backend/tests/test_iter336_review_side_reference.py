"""
iter336 · Review-Side Reference Continuity

Closes the operational communication loop. The canonical record
identifier (report_number / incident_number / etc.) that field crews
see on the iter335 thank-you page now ALSO appears at the top of the
detail/review page for the same record — so Safety/PM/HR can
spot-match a verbal reference instantly.

Scope discipline:
  • Display-only · reuses the iter335 RefKicker component
  • Same canonical ID chain as iter335 (no parallel numbering)
  • Graceful absence when no stable identifier exists
  • NO new pages, NO backend, NO search/lookup/QR/tracking
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
PAGES = ROOT / "frontend" / "src" / "pages"
COMP = ROOT / "frontend" / "src" / "components"


# ─────────────────────────────────────────────────────────────────────
# Reusable RefKicker component exists + correctly shaped
# ─────────────────────────────────────────────────────────────────────
def test_ref_kicker_component_exists():
    p = COMP / "RefKicker.jsx"
    assert p.exists(), "RefKicker component must exist"


def test_ref_kicker_returns_null_when_no_id():
    src = (COMP / "RefKicker.jsx").read_text(encoding="utf-8")
    assert "if (!recordId) return null;" in src, (
        "RefKicker must gracefully omit when no recordId provided"
    )


def test_ref_kicker_uses_calm_subdued_styling():
    src = (COMP / "RefKicker.jsx").read_text(encoding="utf-8")
    # Calm-family subdued mono kicker
    for expected in (
        "font-mono",
        "uppercase",
        "tracking-[0.18em]",
        "text-slate-500",
        "select-all",
    ):
        assert expected in src, f"RefKicker missing calm-family class: {expected}"


def test_ref_kicker_uses_t_for_label():
    src = (COMP / "RefKicker.jsx").read_text(encoding="utf-8")
    assert 't("Ref")' in src, "RefKicker must use t() for the Ref label (EN/ES parity)"


# ─────────────────────────────────────────────────────────────────────
# Every detail/review page mounts the RefKicker
# ─────────────────────────────────────────────────────────────────────
VIEWS = {
    "ViewIncident.jsx":           ("view-incident-ref",       "data.incident_number || data.report_number || data.id"),
    "ViewDailyReport.jsx":        ("view-daily-ref",          "data.report_number || data.id"),
    "ViewInspection.jsx":         ("view-inspection-ref",     "data.inspection_number || data.id"),
    "ViewMeeting.jsx":            ("view-meeting-ref",        "data.meeting_number || data.id"),
    "ViewEquipmentInspection.jsx":("view-equip-inspection-ref","data.inspection_number || data.id"),
    "ViewSafetyForm.jsx":         ("view-safety-form-ref",    "doc.issuance_number || doc.training_number || doc.id"),
    "HrDailyReports.jsx":         ("hr-dr-detail-ref",        "doc.report_number || doc.id"),
}


def test_all_review_surfaces_import_ref_kicker():
    for filename in VIEWS:
        src = (PAGES / filename).read_text(encoding="utf-8")
        assert "RefKicker" in src, f"{filename} must import RefKicker"
        assert "from \"@/components/RefKicker\"" in src, (
            f"{filename} must import RefKicker from canonical path"
        )


def test_all_review_surfaces_mount_ref_kicker_with_canonical_chain():
    for filename, (testid, expected_chain) in VIEWS.items():
        src = (PAGES / filename).read_text(encoding="utf-8")
        assert f'testId="{testid}"' in src, (
            f"{filename} must mount RefKicker with testId={testid}"
        )
        assert expected_chain in src, (
            f"{filename} must use canonical chain `{expected_chain}` for recordId"
        )


def test_legacy_form_ref_line_removed_from_safety_form():
    """ViewSafetyForm.jsx had a legacy `Form Ref: {doc.id}` line. iter336
    replaces it with the unified RefKicker."""
    src = (PAGES / "ViewSafetyForm.jsx").read_text(encoding="utf-8")
    assert 't("Form Ref")' not in src, (
        "Legacy Form Ref label must be replaced by RefKicker"
    )


# ─────────────────────────────────────────────────────────────────────
# Scope discipline · NO new pages or systems
# ─────────────────────────────────────────────────────────────────────
def test_no_new_review_routes_added():
    app_js = (ROOT / "frontend" / "src" / "App.js").read_text(encoding="utf-8")
    for forbidden in ('"/lookup/', '"/track/', '"/reference/', '"/claim/', '"/proof/'):
        assert forbidden not in app_js, (
            f"iter336 must not add tracking/lookup routes: {forbidden}"
        )


def test_no_new_backend_endpoints_added():
    """iter336 must NOT touch backend. Verify no new backend file was
    created carrying the iter336 marker (the only iter336 backend artifact
    allowed is the test file itself)."""
    backend = ROOT / "backend"
    iter336_files = [
        p for p in backend.rglob("*.py")
        if "iter336" in p.name.lower() and p.name != "test_iter336_review_side_reference.py"
    ]
    assert not iter336_files, f"iter336 must not add backend files: {iter336_files}"


def test_ref_kicker_keeps_lightweight_component():
    src = (COMP / "RefKicker.jsx").read_text(encoding="utf-8")
    loc = len(src.splitlines())
    assert loc < 50, f"RefKicker grew to {loc} LOC — must remain minimal"


# ─────────────────────────────────────────────────────────────────────
# Symmetry · review-side ID chain matches submit-side
# ─────────────────────────────────────────────────────────────────────
SUBMIT_SIDE = {
    "NewIncident.jsx":            "r.data?.incident_number || r.data?.id",
    "NewDailyReport.jsx":         "r.data?.report_number || r.data?.id",
    "NewInspection.jsx":          "res.data?.inspection_number || res.data?.id",
    "NewEquipmentInspection.jsx": "res.data?.inspection_number || res.data?.id",
    "NewMeeting.jsx":             "res.data?.meeting_number || res.data?.id",
}


def test_submit_side_id_chains_unchanged():
    """Verify iter335 submit-side chains are still present (no drift)."""
    for filename, expected_chain in SUBMIT_SIDE.items():
        src = (PAGES / filename).read_text(encoding="utf-8")
        assert expected_chain in src, (
            f"{filename} submit-side recordId chain drifted from iter335"
        )
