"""Track 19.35 · Safety Case Workspace · Investigation Upgrades · lock test.

Frontend-only feature track. Backend contract preserved byte-for-byte.
This lock enforces:
- Field Facts + Closeout tabs present in TABS, first and last respectively;
- All 10 pre-19.35 investigation tab keys preserved;
- Default tab is field_facts;
- Lock + CheckCircle2 icons imported from lucide-react;
- Doctrine wording present in the field_facts render block;
- No edit affordances (<input, <textarea, <select, type="submit") inside the
  field_facts render block (immutability grep);
- Closeout panel test-ids present, 5 required checklist items rendered,
  guidance references the Executive header;
- Bilingual (useT + t(...)) in both new panels;
- 6 required Track 19.35 docs exist and declare GO · Six Pillars · Rollback;
- Zero-Drift Matrix covers required categories;
- Track 19.34 field-facing grep invariant still holds;
- PRD + CHANGELOG updated.
"""
from pathlib import Path
import re

APP = Path("/app")
FE = APP / "frontend/src"
MEM = APP / "memory"

WORKSPACE = FE / "pages/SafetyCaseWorkspace.jsx"
INCIDENT_REPORT = FE / "pages/IncidentReport.jsx"
SCHEMA = FE / "lib/incidentReportSchema.js"


# ---------- Helpers ----------


def _read_workspace() -> str:
    assert WORKSPACE.exists(), f"Missing {WORKSPACE}"
    return WORKSPACE.read_text(encoding="utf-8")


def _extract_panel(source: str, tab_key: str) -> str:
    """Grab the JSX rendered when tab === tab_key. Returns the inner block."""
    needle = f'tab === "{tab_key}"'
    idx = source.find(needle)
    assert idx != -1, f"tab === {tab_key!r} not found in workspace"
    # Walk from the opening ( after `&& (` to the matching close paren.
    open_idx = source.find("(", idx)
    assert open_idx != -1, f"opening ( not found after tab === {tab_key!r}"
    depth = 0
    end = None
    for i in range(open_idx, len(source)):
        ch = source[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                end = i
                break
    assert end is not None, f"unbalanced parens for panel {tab_key}"
    return source[open_idx : end + 1]


# ---------- File existence ----------


def test_safety_case_workspace_exists():
    assert WORKSPACE.exists(), f"Missing {WORKSPACE}"


# ---------- TABS array shape ----------


def test_tabs_contains_field_facts_entry():
    text = _read_workspace()
    assert '{ key: "field_facts"' in text, "TABS is missing the field_facts entry"


def test_tabs_contains_closeout_entry():
    text = _read_workspace()
    assert '{ key: "closeout"' in text, "TABS is missing the closeout entry"


def _tabs_array(text: str) -> str:
    m = re.search(r"const TABS = \[(.*?)\];", text, re.DOTALL)
    assert m, "Cannot locate TABS array in workspace"
    return m.group(1)


def test_field_facts_is_first_tab():
    tabs = _tabs_array(_read_workspace())
    keys = re.findall(r'key:\s*"([^"]+)"', tabs)
    assert keys, "No tab keys extracted from TABS"
    assert keys[0] == "field_facts", (
        f"First tab must be field_facts, got {keys[0]!r} (full order: {keys})"
    )


def test_closeout_is_last_tab():
    tabs = _tabs_array(_read_workspace())
    keys = re.findall(r'key:\s*"([^"]+)"', tabs)
    assert keys, "No tab keys extracted from TABS"
    assert keys[-1] == "closeout", (
        f"Last tab must be closeout, got {keys[-1]!r} (full order: {keys})"
    )


PRESERVED_TABS = [
    "timeline",
    "evidence",
    "witnesses",
    "medical",
    "agency",
    "rca",
    "capa",
    "communications",
    "tasks",
    "linked",
]


def test_all_pre_19_35_tabs_preserved():
    tabs = _tabs_array(_read_workspace())
    keys = re.findall(r'key:\s*"([^"]+)"', tabs)
    missing = [k for k in PRESERVED_TABS if k not in keys]
    assert not missing, f"Pre-19.35 tabs removed (zero-drift violation): {missing}"


# ---------- Default tab ----------


def test_default_tab_is_field_facts():
    text = _read_workspace()
    assert 'useState("field_facts")' in text, (
        "Default tab must be field_facts (useState(\"field_facts\"))"
    )


# ---------- Icon imports ----------


def test_lock_icon_imported():
    text = _read_workspace()
    m = re.search(r"from\s+\"lucide-react\"", text)
    assert m, "lucide-react import block not found"
    # find the import block that ends before the "lucide-react" module string
    block_m = re.search(r"import\s*\{([^}]+)\}\s*from\s*\"lucide-react\"", text, re.DOTALL)
    assert block_m, "Cannot locate lucide-react import braces"
    names = {n.strip() for n in block_m.group(1).replace("\n", ",").split(",") if n.strip()}
    assert "Lock" in names, f"Lock icon must be imported from lucide-react (got {names})"


def test_check_circle_icon_imported():
    text = _read_workspace()
    block_m = re.search(r"import\s*\{([^}]+)\}\s*from\s*\"lucide-react\"", text, re.DOTALL)
    assert block_m, "Cannot locate lucide-react import braces"
    names = {n.strip() for n in block_m.group(1).replace("\n", ",").split(",") if n.strip()}
    assert "CheckCircle2" in names, (
        f"CheckCircle2 icon must be imported from lucide-react (got {names})"
    )


# ---------- Field Facts panel ----------


def test_field_facts_panel_has_doctrine_banner_locked_record():
    panel = _extract_panel(_read_workspace(), "field_facts")
    assert "Original Field Report — locked record." in panel, (
        "Field Facts doctrine banner must contain the 'Original Field Report — "
        "locked record.' sentence."
    )


def test_field_facts_panel_has_doctrine_banner_not_editable():
    panel = _extract_panel(_read_workspace(), "field_facts")
    assert "Cannot be edited from the Safety workspace." in panel, (
        "Field Facts doctrine banner must state 'Cannot be edited from the "
        "Safety workspace.'"
    )


FORBIDDEN_EDIT_TOKENS = [
    "<input",
    "<textarea",
    "<select",
    'type="submit"',
]


def test_field_facts_panel_has_no_edit_affordances():
    """Immutability grep — no input/textarea/select/submit inside the panel."""
    panel = _extract_panel(_read_workspace(), "field_facts")
    hits = [tok for tok in FORBIDDEN_EDIT_TOKENS if tok in panel]
    assert not hits, (
        f"Field Facts panel contains forbidden edit affordances: {hits}. "
        "The original field report must be immutable from the Safety workspace."
    )


def test_field_facts_panel_uses_lock_icon():
    panel = _extract_panel(_read_workspace(), "field_facts")
    assert "<Lock " in panel or "<Lock/" in panel or "<Lock>" in panel, (
        "Field Facts panel must render the <Lock /> icon."
    )


def test_field_facts_panel_has_testid():
    panel = _extract_panel(_read_workspace(), "field_facts")
    assert 'data-testid="case-field-facts"' in panel, (
        "Field Facts panel must expose data-testid=\"case-field-facts\"."
    )


# ---------- Closeout panel ----------


def test_closeout_panel_has_root_testid():
    panel = _extract_panel(_read_workspace(), "closeout")
    assert 'data-testid="case-closeout"' in panel, (
        "Closeout panel must expose data-testid=\"case-closeout\"."
    )


def test_closeout_panel_has_checklist_testid():
    panel = _extract_panel(_read_workspace(), "closeout")
    assert 'data-testid="case-closeout-checklist"' in panel, (
        "Closeout panel must expose data-testid=\"case-closeout-checklist\"."
    )


CLOSEOUT_CHECKLIST_ITEMS = [
    "Evidence collected",
    "Witness statements recorded",
    "Root cause / findings documented",
    "Corrective actions assigned",
    "Regulatory / agency contacts logged",
]


def test_closeout_checklist_has_all_five_items():
    panel = _extract_panel(_read_workspace(), "closeout")
    missing = [item for item in CLOSEOUT_CHECKLIST_ITEMS if item not in panel]
    assert not missing, f"Closeout checklist missing items: {missing}"


def test_closeout_panel_references_executive_header():
    panel = _extract_panel(_read_workspace(), "closeout")
    assert "Executive header" in panel, (
        "Closeout panel must remind the Safety Manager that final closure is "
        "set from the Executive header."
    )


# ---------- Bilingual ----------


def test_workspace_uses_useT():
    text = _read_workspace()
    assert "useT" in text, "Workspace must import/use useT() for bilingual copy."


def test_field_facts_panel_is_bilingual():
    panel = _extract_panel(_read_workspace(), "field_facts")
    assert 't("' in panel or "t('" in panel, (
        "Field Facts panel must wrap copy in t(...) for bilingual support."
    )


def test_closeout_panel_is_bilingual():
    panel = _extract_panel(_read_workspace(), "closeout")
    assert 't("' in panel or "t('" in panel, (
        "Closeout panel must wrap copy in t(...) for bilingual support."
    )


# ---------- Documentation ----------


REQUIRED_DOCS = [
    "TRACK_19_35_CASE_WORKSPACE_INVESTIGATION_UPGRADES.md",
    "TRACK_19_35_FIELD_FACTS_IMMUTABILITY.md",
    "TRACK_19_35_REGULATORY_REVIEW_ARCHITECTURE.md",
    "TRACK_19_35_CAPA_CLOSEOUT_WORKFLOW.md",
    "TRACK_19_35_ZERO_DRIFT_MATRIX.md",
    "TRACK_19_35_QUALITY_GATE_CLOSEOUT.md",
    "TRACK_19_35_TEST_REPORT.md",
]


def test_all_track_19_35_docs_present():
    missing = [d for d in REQUIRED_DOCS if not (MEM / d).exists()]
    assert not missing, f"Missing Track 19.35 docs: {missing}"


def test_closeout_declares_go():
    text = (MEM / "TRACK_19_35_QUALITY_GATE_CLOSEOUT.md").read_text(encoding="utf-8")
    assert "🟢 GO" in text or "🟢 **GO" in text


def test_closeout_includes_six_pillar_score():
    text = (MEM / "TRACK_19_35_QUALITY_GATE_CLOSEOUT.md").read_text(encoding="utf-8")
    for pillar in ["Powerful", "Simple", "Beautiful", "Trusted", "Proven", "Operational"]:
        assert pillar in text, f"Six-Pillar score missing pillar: {pillar}"
    assert "/ 60" in text or "/60" in text, "Six-Pillar aggregate band missing"


def test_closeout_includes_rollback_path():
    text = (MEM / "TRACK_19_35_QUALITY_GATE_CLOSEOUT.md").read_text(encoding="utf-8")
    assert "Rollback" in text
    assert "delete" in text.lower() or "revert" in text.lower()


ZERO_DRIFT_CATEGORIES = [
    "Schemas",
    "Backend routes",
    "Payloads",
    "PDFs",
    "Emails",
    "Notifications",
    "Permissions",
    "Trust Spine",
    "Audit events",
    "Rollback",
]


def test_zero_drift_matrix_covers_all_categories():
    text = (MEM / "TRACK_19_35_ZERO_DRIFT_MATRIX.md").read_text(encoding="utf-8")
    for cat in ZERO_DRIFT_CATEGORIES:
        assert cat in text, f"Zero-drift matrix missing category: {cat}"


# ---------- Track 19.34 field-vs-safety grep invariant preserved ----------


FORBIDDEN_FIELDS = [
    "osha_recordable",
    "recordable_case",
    "osha_reportable",
    "root_cause",
    "preventability",
    "preventable_by",
    "workers_comp",
    "insurance_liable",
    "liability_determination",
    "disciplinary_action",
    "disciplinary_conclusion",
]


def test_track_19_34_field_intake_invariant_preserved():
    schema = SCHEMA.read_text(encoding="utf-8")
    report = INCIDENT_REPORT.read_text(encoding="utf-8")
    for field in FORBIDDEN_FIELDS:
        assert field not in schema, (
            f"Track 19.34 invariant broken: forbidden field {field!r} appeared "
            f"in {SCHEMA.name}"
        )
        assert field not in report, (
            f"Track 19.34 invariant broken: forbidden field {field!r} appeared "
            f"in {INCIDENT_REPORT.name}"
        )


# ---------- PRD + CHANGELOG governance ----------


def test_prd_updated_for_19_35():
    prd = (MEM / "PRD.md").read_text(encoding="utf-8")
    assert "TRACK 19.35" in prd


def test_changelog_updated_for_19_35():
    changelog = (MEM / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "TRACK 19.35" in changelog
