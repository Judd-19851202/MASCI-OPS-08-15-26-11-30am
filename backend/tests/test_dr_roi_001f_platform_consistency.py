"""DR-ROI-001F-FINAL-REPAIR · Platform-native Daily Job Report V2.

Enforces the correct product direction: DR-V2 is a subtle enhancement of
V1 Daily Job Report, NOT a new form, NOT an AI product, NOT a dashboard.
The only major new field concept is the Daily Operational Summary at
the bottom.
"""
from __future__ import annotations
import re
from pathlib import Path


ROOT = Path("/app/frontend/src/pages/daily-report-v2")
SHELL_FILE = ROOT / "DailyReportV2.jsx"
UI_FILE = ROOT / "_ui.jsx"
ALL_V2_FILES = list(ROOT.glob("**/*.jsx"))

FORBIDDEN_UI_STRINGS = [
    "claude", "anthropic", "gpt-", "gpt5", "gpt 5",
    "openai", "gemini", "nano banana", "sonnet ", "opus ",
    "llm", "model:", "provider:", "token cost", "tokens used",
    "cost per token", "ai agent", "prompt tokens", "raw model",
]
ALLOWED_TERMS = {
    "daily operational summary",
    "operational summary",
    "items to verify",
    "you remain the source of truth",
}

FORBIDDEN_DARK_CLASSES = [
    "bg-neutral-950", "bg-neutral-900", "text-neutral-100",
    "border-neutral-800", "border-neutral-700",
    "bg-neutral-900/60", "bg-neutral-950/60", "bg-neutral-950/40",
]

# FINAL-REPAIR: PDF affordances must NOT appear on the field form.
FORBIDDEN_PDF_TESTIDS_ON_FIELD = [
    "dr-v2-preview-pdf-btn",
    "dr-v2-download-pdf-btn",
]


def test_no_ai_branding_in_field_form():
    hits = []
    for p in ALL_V2_FILES:
        text = p.read_text(encoding="utf-8").lower()
        for word in FORBIDDEN_UI_STRINGS:
            if word in text and not any(word in a for a in ALLOWED_TERMS):
                hits.append(f"{p.name}: forbidden UI string '{word}'")
    assert not hits, "AI branding leaked into DR-V2:\n" + "\n".join(hits)


def test_no_dark_theme_classes_in_field_form():
    hits = []
    for p in ALL_V2_FILES:
        text = p.read_text(encoding="utf-8")
        for cls in FORBIDDEN_DARK_CLASSES:
            if re.search(rf'(?:^|[\s"\'`]){re.escape(cls)}(?:[\s"\'`]|$)', text):
                hits.append(f"{p.name}: '{cls}'")
    assert not hits, "Dark-theme drift in DR-V2:\n" + "\n".join(hits)


def test_no_pdf_buttons_on_field_form():
    """FINAL-REPAIR: PDF buttons must NOT appear on the supervisor's
    Daily Job Report. PDF belongs in PM/Admin/Document Center AFTER
    submit."""
    hits = []
    for p in ALL_V2_FILES:
        text = p.read_text(encoding="utf-8")
        for tid in FORBIDDEN_PDF_TESTIDS_ON_FIELD:
            if tid in text:
                hits.append(f"{p.name}: forbidden PDF button '{tid}'")
        for phrase in ("Preview PDF", "Download PDF"):
            if phrase in text:
                hits.append(f"{p.name}: forbidden PDF phrase '{phrase}'")
    assert not hits, "PDF buttons must not be on the field form:\n" + "\n".join(hits)


def test_shell_uses_masci_platform_header():
    """FINAL-REPAIR: shell must render the MASCI navy top banner that
    matches V1's Daily Job Report shell (bg-slate-900 · red-700 hazard
    stripe · sticky top-0), NOT just a small white header card."""
    text = SHELL_FILE.read_text(encoding="utf-8")
    assert "DailyReportTopBanner" in text, \
        "Shell must import + render the shared DailyReportTopBanner"
    assert "New Daily Report" not in text, \
        "'New Daily Report' phrasing is not V1-native — use 'Daily Job Report'"
    banner_path = Path("/app/frontend/src/components/DailyReportTopBanner.jsx")
    assert banner_path.exists(), "Shared banner component must exist"
    banner = banner_path.read_text(encoding="utf-8")
    # Byte/style equivalence with V1's banner classes (see NewDailyReport.jsx:1260).
    for cls in ("bg-slate-900", "border-b-4", "border-red-700",
                "sticky", "top-0", "z-10", "max-w-4xl"):
        assert cls in banner, f"Banner must use V1 class '{cls}'"
    assert "MasciLogo" in banner, "Banner must render MasciLogo"


def test_legacy_v1_shell_removed_after_containment():
    v1 = Path("/app/frontend/src/pages/NewDailyReportV3.jsx")
    assert not v1.exists(), "legacy V1 shell should be removed after DR-03 containment"


def test_pm_intelligence_panel_removed():
    pm = ROOT / "panels" / "PmIntelligencePanel.jsx"
    assert not pm.exists(), "PmIntelligencePanel.jsx must not exist"
    assert "PmIntelligencePanel" not in SHELL_FILE.read_text(encoding="utf-8")


def test_confidence_and_approval_panels_removed_from_shell():
    """FINAL-REPAIR: confidence/readiness scoreboards and audit-log
    approval panel are downstream concerns — they must not dominate the
    field form. The Daily Operational Summary section carries a simple
    Accept / Edit / Regenerate flow instead."""
    text = SHELL_FILE.read_text(encoding="utf-8")
    assert "ConfidencePanel" not in text, \
        "ConfidencePanel must not be rendered on the field shell"
    assert "SupervisorApprovalPanel" not in text, \
        "SupervisorApprovalPanel must not be rendered on the field shell"


def test_platform_native_components_wired():
    checks = {
        "DaySetupSection.jsx": ["JobPicker", "fetchDailyWeather", "getCurrentPosition"],
        "CrewTimeSection.jsx": ["EmployeeCombo"],
        "EquipmentSection.jsx": ["EquipmentCombo", "EmployeeCombo"],
        "PhotosSection.jsx": ["PhotoUpload"],
        "SafetyQualitySection.jsx": ["YesNo", "DailyReportExcavationActivity"],
        "SignatureSubmitSection.jsx": ["SignaturePad"],
        "ConstraintChipsSection.jsx": ["SupplierCombo"],
    }
    for fname, needles in checks.items():
        path = ROOT / "sections" / fname
        assert path.exists(), f"missing section: {fname}"
        text = path.read_text(encoding="utf-8")
        for needle in needles:
            assert needle in text, f"{fname} must reference {needle}"


def test_all_sections_use_platform_section_component():
    for p in (ROOT / "sections").glob("*.jsx"):
        text = p.read_text(encoding="utf-8")
        assert 'from "@/components/Section"' in text, \
            f"{p.name} must import Section from @/components/Section"
        assert re.search(r"<Section[\s\n>]", text), \
            f"{p.name} must render <Section number=... />"


def test_photo_min_six_rule_still_enforced():
    text = (ROOT / "sections" / "PhotosSection.jsx").read_text(encoding="utf-8")
    assert re.search(r"\b6\b", text), "Photos section must enforce the 6-photo minimum"
    assert "min-warning" in text or "min-6" in text.lower() or "required" in text.lower(), \
        "Photos section must show the required-photo affordance"


def test_daily_operational_summary_section_exists_at_bottom():
    """AI Summary section is the only major new field concept. It must
    exist AND come after all data-entry sections in the shell."""
    text = SHELL_FILE.read_text(encoding="utf-8")
    idx_photos = text.find("<PhotosSection")
    idx_ai = text.find("<AISummarySection")
    idx_signature = text.find("<SignatureSubmitSection")
    assert idx_photos > 0 and idx_ai > 0 and idx_signature > 0, \
        "shell must render Photos, AI Summary, and Signature sections"
    assert idx_photos < idx_ai < idx_signature, \
        "AI Summary must come AFTER data entry and BEFORE signature"

    ai_file = (ROOT / "sections" / "AISummarySection.jsx").read_text(encoding="utf-8")
    for needle in ("Daily Operational Summary",
                   "dr-v2-ai-accept",
                   "dr-v2-ai-edit",
                   "dr-v2-ai-regenerate"):
        assert needle in ai_file, f"AISummarySection missing '{needle}'"


def test_ui_primitives_still_export_platform_grammar():
    text = UI_FILE.read_text(encoding="utf-8")
    for name in ("SectionCard", "PlaceholderPane", "FieldLabel",
                 "inputCls", "selectCls", "primaryBtn", "secondaryBtn",
                 "ghostBtn", "addItemBtn", "StatusChip"):
        assert name in text, f"_ui.jsx must export {name}"


def test_canonical_v3_shell_preserves_platform_component_anchors():
    v3 = Path("/app/frontend/src/pages/NewDailyReportV3.jsx")
    v3_text = v3.read_text(encoding="utf-8")
    for anchor in (
        'import { DailyReportTopBanner } from "@/components/DailyReportTopBanner"',
        'import { SectionProjectConditions } from "@/components/daily-report-v3/SectionProjectConditions"',
        "useFormDraft",
        'import { fetchDailyWeather } from "@/lib/weather"',
    ):
        assert anchor in v3_text, f"V3 anchor missing: {anchor}"


def test_dr_v2_flag_still_gates_the_shell():
    text = SHELL_FILE.read_text(encoding="utf-8")
    assert "isDailyReportV2Enabled" in text
    assert 'data-testid="dr-v2-disabled"' in text


def test_supervisor_terminology_is_daily_job_report():
    """FINAL-REPAIR: the disabled/preview state must also use platform
    terminology ('Daily Job Report'), not the invented 'New Daily
    Report'."""
    text = SHELL_FILE.read_text(encoding="utf-8")
    assert "Daily Job Report" in text
