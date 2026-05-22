"""
iter335 · Submission Tracking Reference Continuity

Verifies the new tracking-reference line on /thank-you and that every
public-submitting form now passes a canonical record identifier through
router state (graceful fallback when backend has no per-formType number).

Scope discipline:
  • Display-only continuity refinement — NO new pages, NO tracking
    portal, NO public lookup, NO QR systems, NO email/notification.
  • Reference line ONLY renders when a stable identifier exists.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
THANK_YOU = ROOT / "frontend" / "src" / "pages" / "ThankYou.jsx"
I18N = ROOT / "frontend" / "src" / "lib" / "i18n.js"


# ─────────────────────────────────────────────────────────────────────
# ThankYou.jsx · reference line wiring
# ─────────────────────────────────────────────────────────────────────
def test_thank_you_reads_record_id_from_state():
    src = THANK_YOU.read_text(encoding="utf-8")
    assert 'state?.recordId' in src, "Thank-you must read recordId from router state"


def test_thank_you_renders_reference_line_when_present():
    src = THANK_YOU.read_text(encoding="utf-8")
    # The conditional must be present — line should only render when recordId is truthy.
    assert '{recordId && (' in src, (
        "Reference line must be conditionally rendered (no placeholder when missing)"
    )


def test_thank_you_reference_has_testid():
    src = THANK_YOU.read_text(encoding="utf-8")
    assert 'data-testid="thank-you-reference"' in src


def test_thank_you_reference_uses_ref_label():
    src = THANK_YOU.read_text(encoding="utf-8")
    # The visual format is `Ref · <ID>`
    assert 't("Ref")' in src
    # Subdued styling — font-mono uppercase low-saturation tracking
    assert 'font-mono' in src
    assert 'tracking-[0.18em]' in src


def test_thank_you_reference_is_selectable_for_screenshot():
    """`select-all` ensures field crews can tap-and-hold to copy on mobile."""
    src = THANK_YOU.read_text(encoding="utf-8")
    assert 'select-all' in src, "Reference ID must be select-all for mobile copy"


# ─────────────────────────────────────────────────────────────────────
# Every form that lands on /thank-you must now pass recordId
# ─────────────────────────────────────────────────────────────────────
FORM_SOURCES = {
    "NewIncident.jsx":            "r.data?.incident_number || r.data?.id",
    "NewDailyReport.jsx":         "r.data?.report_number || r.data?.id",
    "NewInspection.jsx":          "res.data?.inspection_number || res.data?.id",
    "NewEquipmentInspection.jsx": "res.data?.inspection_number || res.data?.id",
    "NewMeeting.jsx":             "res.data?.meeting_number || res.data?.id",
}


def test_all_thank_you_forms_pass_record_id():
    for filename, fallback_expr in FORM_SOURCES.items():
        path = ROOT / "frontend" / "src" / "pages" / filename
        src = path.read_text(encoding="utf-8")
        assert "recordId:" in src, f"{filename} must add recordId to /thank-you state"
        assert fallback_expr in src, (
            f"{filename} must use fallback chain `{fallback_expr}` for recordId"
        )


def test_all_thank_you_forms_use_canonical_id_chain():
    """No form may emit a random/client-side ID — only canonical
    backend-issued identifiers + UUID fallback."""
    for filename in FORM_SOURCES:
        path = ROOT / "frontend" / "src" / "pages" / filename
        src = path.read_text(encoding="utf-8")
        # Forbidden patterns that would indicate a fabricated ID system.
        for forbidden in (
            "Math.random",
            "uuid()",
            "Date.now()",
            "crypto.randomUUID",
        ):
            # Allow these elsewhere in the file (idempotency keys, etc.)
            # but NOT in the recordId line itself.
            # Pull the recordId line and check it specifically.
            lines = [l for l in src.split("\n") if "recordId:" in l]
            for line in lines:
                assert forbidden not in line, (
                    f"{filename} recordId line uses forbidden client-side ID source: {forbidden}"
                )


# ─────────────────────────────────────────────────────────────────────
# ES parity
# ─────────────────────────────────────────────────────────────────────
def test_es_translation_for_ref_label():
    src = I18N.read_text(encoding="utf-8")
    assert '"Ref": "Ref."' in src, (
        "Missing ES translation for Ref → Ref. (period form)"
    )


# ─────────────────────────────────────────────────────────────────────
# Scope discipline · NO new pages or systems
# ─────────────────────────────────────────────────────────────────────
def test_no_tracking_portal_added():
    """iter335 must NOT introduce a /track or /lookup or /reference route."""
    app_js = (ROOT / "frontend" / "src" / "App.js").read_text(encoding="utf-8")
    for forbidden in (
        '"/track"',
        '"/lookup"',
        '"/reference/"',
        '"/claim/"',
        '"/proof/"',
    ):
        assert forbidden not in app_js, (
            f"iter335 added a forbidden tracking-portal route: {forbidden}"
        )


def test_thank_you_remains_lightweight():
    """The thank-you page must stay under 150 LOC (was 117 before iter335)."""
    src = THANK_YOU.read_text(encoding="utf-8")
    loc = len(src.splitlines())
    assert loc < 150, (
        f"ThankYou.jsx grew to {loc} LOC — iter335 must remain a lightweight refinement"
    )
