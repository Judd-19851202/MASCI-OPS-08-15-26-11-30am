"""DR-ROI-001F · Platform UI Consistency Lock (Phase 1-2, 10, 11).

Enforces that the Daily Report V2 shell, sections, and panels stay
platform-aligned in look, feel, and language. Blocks drift back to the
dark AI-looking chrome, and blocks re-introduction of the PM Intelligence
panel inside the field form.
"""
from __future__ import annotations
import re
from pathlib import Path


ROOT = Path("/app/frontend/src/pages/daily-report-v2")

SHELL_FILE = ROOT / "DailyReportV2.jsx"
UI_FILE = ROOT / "_ui.jsx"

ALL_V2_FILES = list(ROOT.glob("**/*.jsx"))

# Absolutely-not-in-UI phrases: AI-branded field language. Case-insensitive.
FORBIDDEN_UI_STRINGS = [
    "claude", "anthropic", "gpt-", "gpt5", "gpt 5",
    "openai", "gemini", "nano banana", "sonnet ", "opus ",
    "llm", "model:", "provider:", "token cost", "tokens used",
    "cost per token", "ai agent", "prompt tokens",
    "ai dashboard", "raw model", "raw prompt",
]

# Approved-terms list — appearances allowed only inside these phrases.
ALLOWED_TERMS = {
    "daily operational summary",
    "operational summary",
    "items to verify",
    "supervisor is the source of truth",
    "you remain the source of truth",
}

# Dark-theme classes that MUST NOT appear on the V2 field surface.
FORBIDDEN_DARK_CLASSES = [
    "bg-neutral-950",
    "bg-neutral-900",
    "text-neutral-100",
    "border-neutral-800",
    "border-neutral-700",
    "bg-neutral-900/60",
    "bg-neutral-950/60",
    "bg-neutral-950/40",
]


def _scan_forbidden_strings(text: str, path: Path) -> list[str]:
    hits: list[str] = []
    lower = text.lower()
    for word in FORBIDDEN_UI_STRINGS:
        if word in lower:
            # Whitelist appearances contained inside an allowed phrase.
            if any(word in a for a in ALLOWED_TERMS):
                continue
            hits.append(f"{path.name}: forbidden UI string '{word}'")
    return hits


def _scan_dark_classes(text: str, path: Path) -> list[str]:
    hits: list[str] = []
    for cls in FORBIDDEN_DARK_CLASSES:
        # Look for the exact class name as a whitespace/quote-bounded token.
        if re.search(rf'(?:^|[\s"\'`]){re.escape(cls)}(?:[\s"\'`]|$)', text):
            hits.append(f"{path.name}: dark-theme class '{cls}' present")
    return hits


def test_no_ai_branding_in_field_form():
    hits: list[str] = []
    for p in ALL_V2_FILES:
        hits.extend(_scan_forbidden_strings(p.read_text(encoding="utf-8"), p))
    assert not hits, "AI branding leaked into Daily Report V2:\n" + "\n".join(hits)


def test_no_dark_theme_classes_in_field_form():
    hits: list[str] = []
    for p in ALL_V2_FILES:
        hits.extend(_scan_dark_classes(p.read_text(encoding="utf-8"), p))
    assert not hits, "Dark-theme drift in Daily Report V2:\n" + "\n".join(hits)


def test_shell_uses_platform_light_theme():
    text = SHELL_FILE.read_text(encoding="utf-8")
    assert "bg-slate-50" in text, "Shell must use bg-slate-50 canvas"
    assert "text-slate-900" in text, "Shell must use slate-900 body text"
    assert 'data-testid="dr-v2-savebar"' in text
    assert 'data-testid="dr-v2-preview-pdf-btn"' in text
    assert 'data-testid="dr-v2-download-pdf-btn"' in text


def test_pm_intelligence_panel_removed_from_field_form():
    """PM Intelligence stays in the /pm/operational-intelligence dashboard,
    not in the field form. The panel file must not exist and the shell
    must not import it.
    """
    pm_panel = ROOT / "panels" / "PmIntelligencePanel.jsx"
    assert not pm_panel.exists(), "PmIntelligencePanel.jsx must not exist"
    text = SHELL_FILE.read_text(encoding="utf-8")
    assert "PmIntelligencePanel" not in text, "Shell must not import PmIntelligencePanel"


def test_ui_primitives_export_platform_grammar():
    text = UI_FILE.read_text(encoding="utf-8")
    for name in ("SectionCard", "PlaceholderPane", "FieldLabel",
                 "inputCls", "selectCls", "primaryBtn", "secondaryBtn",
                 "ghostBtn", "addItemBtn", "StatusChip"):
        assert name in text, f"_ui.jsx must export {name}"
    # Ensure the primitive card uses light theme.
    assert "bg-white" in text and "border-slate-200" in text


def test_v1_daily_report_untouched_reference_lines():
    """V1 Daily Report and V1 daily_reports.py must remain untouched by
    Phase 1-2. Spot check by size and the presence of key V1 imports."""
    v1_page = Path("/app/frontend/src/pages/NewDailyReport.jsx")
    assert v1_page.exists(), "V1 NewDailyReport.jsx must exist"
    v1_text = v1_page.read_text(encoding="utf-8")
    # A few V1 anchors that must remain.
    for anchor in ("import { Button } from \"@/components/ui/button\"",
                   "import { JobPicker } from \"@/components/JobPicker\"",
                   "import { PhotoUpload } from \"@/components/PhotoUpload\""):
        assert anchor in v1_text, f"V1 anchor missing: {anchor}"


def test_dr_v2_flag_still_gates_the_shell():
    text = SHELL_FILE.read_text(encoding="utf-8")
    assert "isDailyReportV2Enabled" in text
    assert 'data-testid="dr-v2-disabled"' in text, "Disabled state must render"
