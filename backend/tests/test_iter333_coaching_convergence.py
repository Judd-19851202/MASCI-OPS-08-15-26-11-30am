"""
iter333 · Final Operational Coaching Convergence

Bounded refinements to Tier-1 forms — anchored to the iter327 homepage
capability-forward voice. The pass replaces weak/generic wording with
field-proven operational coaching WITHOUT bloating any surface.

Categories audited:
  1. Submit-success toasts → continuity messaging
  2. Form intro sub-headers → operational expectations
  3. High-impact placeholder helpers → "what good looks like"
  4. Empty states → next-action guidance
  5. EN/ES parity for every refined string
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


# ─────────────────────────────────────────────────────────────────────
# 1 · Submit-success continuity toasts
# ─────────────────────────────────────────────────────────────────────
def test_incident_form_continuity_toast():
    src = (ROOT / "frontend" / "src" / "pages" / "NewIncident.jsx").read_text(encoding="utf-8")
    assert "Incident report filed · Safety + PM notified · visible under Incidents" in src
    # The old generic toast must be gone.
    assert '"Incident report saved"' not in src


def test_daily_report_continuity_toast():
    src = (ROOT / "frontend" / "src" / "pages" / "NewDailyReport.jsx").read_text(encoding="utf-8")
    assert "Daily report filed · PM distribution sent · visible under Daily Reports" in src
    assert '"Daily report saved"' not in src


def test_inspection_continuity_toast():
    src = (ROOT / "frontend" / "src" / "pages" / "NewInspection.jsx").read_text(encoding="utf-8")
    assert "Inspection filed · graded · visible under Audits & Inspections" in src
    assert '"Inspection saved"' not in src


def test_safety_forms_issuance_continuity_toast():
    src = (ROOT / "frontend" / "src" / "pages" / "NewSafetyEquipmentIssuance.jsx").read_text(encoding="utf-8")
    assert "Issuance filed · PDF emailed to Safety · visible in Safety Forms Records" in src


def test_safety_forms_training_continuity_toast():
    src = (ROOT / "frontend" / "src" / "pages" / "NewSafetyEquipmentTraining.jsx").read_text(encoding="utf-8")
    assert "Training filed · PDF emailed to Safety · visible in Safety Forms Records" in src


# ─────────────────────────────────────────────────────────────────────
# 2 · Operational form intro sub-headers
# ─────────────────────────────────────────────────────────────────────
def test_incident_form_has_iter327_voice_intro():
    src = (ROOT / "frontend" / "src" / "pages" / "NewIncident.jsx").read_text(encoding="utf-8")
    assert "Every detail filed here protects the crew, the project, and the company." in src


def test_daily_report_has_iter327_voice_intro():
    src = (ROOT / "frontend" / "src" / "pages" / "NewDailyReport.jsx").read_text(encoding="utf-8")
    assert "One report per crew, per day." in src


def test_inspection_has_iter327_voice_intro():
    src = (ROOT / "frontend" / "src" / "pages" / "NewInspection.jsx").read_text(encoding="utf-8")
    assert "A walking record of what's safe, what isn't, and what was fixed today." in src


def test_dvir_has_iter327_voice_intro():
    src = (ROOT / "frontend" / "src" / "pages" / "NewFleetDVIR.jsx").read_text(encoding="utf-8")
    assert "Walk it before you roll it." in src
    # Old generic intro must be gone.
    assert "Walk around your truck before you roll." not in src


# ─────────────────────────────────────────────────────────────────────
# 3 · "What good looks like" placeholder helpers
# ─────────────────────────────────────────────────────────────────────
def test_incident_description_placeholder_sharpened():
    src = (ROOT / "frontend" / "src" / "pages" / "NewIncident.jsx").read_text(encoding="utf-8")
    assert "Write it like you'd brief the Safety Manager on a phone call." in src


def test_incident_corrective_placeholder_sharpened():
    src = (ROOT / "frontend" / "src" / "pages" / "NewIncident.jsx").read_text(encoding="utf-8")
    assert "Specific changes that prevent this from happening again" in src
    # Old generic version must be gone.
    assert 'placeholder="Training, procedure changes, engineering controls..."' not in src


def test_inspection_corrective_placeholder_sharpened():
    src = (ROOT / "frontend" / "src" / "pages" / "NewInspection.jsx").read_text(encoding="utf-8")
    assert "Specific beats general — name the location, the trade, the action." in src


def test_dvir_defect_placeholder_sharpened():
    src = (ROOT / "frontend" / "src" / "pages" / "NewFleetDVIR.jsx").read_text(encoding="utf-8")
    assert "Be specific so Shop knows what to grab." in src
    # Old short placeholder must be gone.
    assert "(10+ chars)" not in src


# ─────────────────────────────────────────────────────────────────────
# 4 · Empty-state guidance
# ─────────────────────────────────────────────────────────────────────
def test_incidents_dashboard_empty_state_sharpened():
    src = (ROOT / "frontend" / "src" / "pages" / "IncidentsDashboard.jsx").read_text(encoding="utf-8")
    assert "Nothing filed yet today." in src
    assert "No incidents on file yet" not in src


def test_hr_daily_reports_empty_state_sharpened():
    src = (ROOT / "frontend" / "src" / "pages" / "HrDailyReports.jsx").read_text(encoding="utf-8")
    assert "Try a wider date range or clear all filters to see everything on file." in src


# ─────────────────────────────────────────────────────────────────────
# 5 · EN/ES parity for every refined string
# ─────────────────────────────────────────────────────────────────────
def test_es_translations_for_iter333_coaching():
    src = (ROOT / "frontend" / "src" / "lib" / "i18n.js").read_text(encoding="utf-8")
    es_keys = (
        '"Incident report filed · Safety + PM notified · visible under Incidents":',
        '"Daily report filed · PM distribution sent · visible under Daily Reports":',
        '"Inspection filed · graded · visible under Audits & Inspections":',
        '"Issuance filed · PDF emailed to Safety · visible in Safety Forms Records":',
        '"Training filed · PDF emailed to Safety · visible in Safety Forms Records":',
        '"Every detail filed here protects the crew, the project, and the company. Write it the way you\'d want to read it six months from now.":',
        '"One report per crew, per day. Capture labor, subs, materials, weather, and photos so payroll and PM coordination run clean tomorrow.":',
        '"A walking record of what\'s safe, what isn\'t, and what was fixed today. Honest grades drive better jobs.":',
        '"Walk it before you roll it. Mark every item honestly. A FAIL today is a downed truck — and a tomorrow you can plan for, not one that surprises you.":',
        '"What happened, who was involved, what equipment or materials were present, and what was done in the moment. Write it like you\'d brief the Safety Manager on a phone call.":',
        '"Specific changes that prevent this from happening again — training, procedure updates, equipment fixes, supervision changes.":',
        '"What was the issue, where on site, what was done about it, and who owns the follow-up. Specific beats general — name the location, the trade, the action.":',
        '"Describe the defect — what you saw, heard, or felt. Where on the unit. When it started. Be specific so Shop knows what to grab.":',
        '"No daily reports match these filters. Try a wider date range or clear all filters to see everything on file.":',
    )
    for k in es_keys:
        assert k in src, f"Missing ES key: {k[:60]}..."


# ─────────────────────────────────────────────────────────────────────
# 6 · Scope discipline · NO new features added
# ─────────────────────────────────────────────────────────────────────
def test_no_giant_onboarding_panel_added():
    """The refinement must not add LMS/tutorial/walkthrough panels."""
    for f in ["NewIncident.jsx", "NewDailyReport.jsx", "NewInspection.jsx", "NewFleetDVIR.jsx"]:
        src = (ROOT / "frontend" / "src" / "pages" / f).read_text(encoding="utf-8")
        for forbidden in ("OnboardingWalkthrough", "TutorialModal", "WelcomeTour", "FormGuideOverlay"):
            assert forbidden not in src, f"Forbidden onboarding component found in {f}: {forbidden}"
