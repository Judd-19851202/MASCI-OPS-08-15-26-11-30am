"""
iter334 · Public Submission Thank-You Continuity Refinement

Verifies the rewritten /thank-you confirmation page:
  1. Headline collapsed to single-word "Filed." (iter327 voice)
  2. Per-formType continuity messaging map present for all 9 supported types
  3. Anonymous default fallback messaging present
  4. ES translations for every new string
  5. Original generic "Thank you." headline + "Stay safe out there." text
     are gone (no soft-positivity SaaS fallback wording)
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
THANK_YOU = ROOT / "frontend" / "src" / "pages" / "ThankYou.jsx"
I18N = ROOT / "frontend" / "src" / "lib" / "i18n.js"


# ─────────────────────────────────────────────────────────────────────
# Headline collapse to iter327 voice
# ─────────────────────────────────────────────────────────────────────
def test_thank_you_headline_is_filed():
    src = THANK_YOU.read_text(encoding="utf-8")
    assert 't("Filed.")' in src, "Headline must collapse to 'Filed.'"


def test_thank_you_removes_generic_thank_you():
    src = THANK_YOU.read_text(encoding="utf-8")
    assert 't("Thank you.")' not in src, "Old generic 'Thank you.' headline must be removed"


def test_thank_you_removes_stay_safe_softline():
    src = THANK_YOU.read_text(encoding="utf-8")
    assert "Stay safe out there." not in src, "Old soft-positivity fallback must be removed"


def test_thank_you_button_says_file_another():
    src = THANK_YOU.read_text(encoding="utf-8")
    assert 't("File Another")' in src
    assert 't("Submit Another")' not in src, "Old 'Submit Another' must be replaced"


# ─────────────────────────────────────────────────────────────────────
# Continuity message map covers all 9 supported formTypes
# ─────────────────────────────────────────────────────────────────────
def test_continuity_map_covers_all_formtypes():
    src = THANK_YOU.read_text(encoding="utf-8")
    required_keys = (
        '"Incident Report":',
        '"Daily Report":',
        '"Inspection":',
        '"Equipment Issuance":',
        '"Equipment Training":',
        '"Equipment Pre-Op Inspection":',
        '"Site Safety Meeting":',
        '"DVIR":',
        '"Toolbox Meeting":',
        '"JHA":',
    )
    for key in required_keys:
        assert key in src, f"Missing continuity entry: {key}"


def test_continuity_default_fallback_present():
    src = THANK_YOU.read_text(encoding="utf-8")
    assert "The right people have visibility. You're done unless contacted." in src, (
        "Default fallback for unmapped formType must be present"
    )


# ─────────────────────────────────────────────────────────────────────
# ES parity for every new string
# ─────────────────────────────────────────────────────────────────────
def test_es_translations_for_iter334():
    src = I18N.read_text(encoding="utf-8")
    es_keys = (
        '"Filed.":',
        '"On file":',
        '"File Another":',
        '"Safety has it. If additional information is needed, the team will follow up.":',
        '"Operations, payroll, and project leadership can now review today\'s activity.":',
        '"Findings and corrective actions are now visible in Safety Review.":',
        '"Issuance recorded. Equipment accountability and return status are now tracked.":',
        '"Training recorded. Use and care accountability is now tracked.":',
        '"Defect log filed. Shop has visibility for tomorrow\'s planning.":',
        '"Meeting recorded. Attendance and topics are now on file.":',
        '"JHA filed. The plan is available for the crew and Safety review.":',
        '"Pre-op log filed. Shop and supervision have visibility for the day\'s run.":',
        '"The right people have visibility. You\'re done unless contacted.":',
        # formType label translations
        '"Incident Report":',
        '"Daily Report":',
        '"Equipment Issuance":',
        '"Equipment Training":',
        '"Toolbox Meeting":',
    )
    for k in es_keys:
        assert k in src, f"Missing ES translation: {k[:60]}..."


# ─────────────────────────────────────────────────────────────────────
# Scope discipline · no new feature components added
# ─────────────────────────────────────────────────────────────────────
def test_no_progress_tracker_added():
    src = THANK_YOU.read_text(encoding="utf-8")
    for forbidden in ("ProgressTracker", "Timeline", "OnboardingFlow", "MarketingFooter", "ConfettiBurst"):
        assert forbidden not in src, f"Forbidden component added: {forbidden}"


def test_thank_you_keeps_existing_visual_contract():
    """Card chrome must remain calm-family — single card, no redesign."""
    src = THANK_YOU.read_text(encoding="utf-8")
    # Calm card pattern preserved
    assert "bg-white border border-slate-200 rounded-md" in src
    # Caution stripe preserved (platform-family decoration)
    assert "caution-stripe" in src
    # Header bar preserved
    assert "bg-slate-900 border-b-4 border-red-700" in src


# ─────────────────────────────────────────────────────────────────────
# Test ids for downstream automation
# ─────────────────────────────────────────────────────────────────────
def test_thank_you_testids_present():
    src = THANK_YOU.read_text(encoding="utf-8")
    for tid in ('thank-you-card', 'thank-you-kicker', 'thank-you-headline', 'thank-you-continuity'):
        assert f'data-testid="{tid}"' in src, f"Missing testid: {tid}"
