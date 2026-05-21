"""iter319 · Field Leadership Hub + Field Hub Calm Pass invariants.

Locks the iter319 platform-convergence pass so the FL Hub and Field Hub
continue to match the iter317-C / iter318 calm pattern. Bounded:
- Calm tile chrome in place (left-edge stripe · no SectionTile import)
- H1 toned to interior-hub size (Rule 3)
- iter203 mobile header collapse on FL Hub
- 3 lightweight Field Hub operational groups
- Bilingual ES entries for all new strings
- All prior tile testids preserved
"""
from pathlib import Path

FRONTEND = Path(__file__).resolve().parent.parent.parent / "frontend/src"
FL_HUB = FRONTEND / "pages/FieldLeadershipHub.jsx"
FIELD_HUB = FRONTEND / "pages/FieldSection.jsx"
I18N = FRONTEND / "lib/i18n.js"


# ─── FL Hub invariants ──────────────────────────────────────────────────

def test_iter319_fl_hub_calm_tile_pattern():
    """FL Hub uses inline calm `LeadershipTile`, NOT shared SectionTile."""
    src = FL_HUB.read_text()
    assert "border-l-4" in src
    assert "function LeadershipTile" in src
    # SectionTile import removed.
    assert 'from "@/components/SectionTile"' not in src
    # No legacy hot SectionTile JSX usage in this hub.
    assert "<SectionTile" not in src


def test_iter319_fl_hub_h1_toned_down():
    """H1 sized for interior hub (Rule 3): `text-3xl sm:text-4xl`.
    The legacy public-hero `text-4xl sm:text-5xl lg:text-6xl` is gone."""
    src = FL_HUB.read_text()
    assert "text-3xl sm:text-4xl" in src
    # Locked: the legacy hero H1 size must not return on this hub.
    legacy_hero = 'font-display text-4xl sm:text-5xl lg:text-6xl'
    # Restrict the assertion to the live FieldLeadershipHub H1 region.
    # The `PasswordGate` block has its own modest H1 (text-2xl) so we
    # only need to assert the legacy giant size never reappears.
    assert legacy_hero not in src, (
        "FL Hub H1 must use the interior-hub size, not the public-hero size"
    )


def test_iter319_fl_hub_calm_legal_banner():
    """Legal-compliance banner toned to slate-50 + slate-200 (Rule 1)
    instead of the previous amber-50 + amber-300 hot chrome."""
    src = FL_HUB.read_text()
    assert "bg-slate-50 border border-slate-200" in src
    assert "bg-amber-50 border border-amber-300" not in src


def test_iter319_fl_hub_mobile_header_collapse():
    """iter203 collapse: Guides + Records + CompanyInfo + GlobalSearch
    hidden below sm: on the FL Hub header (parity with HR / Safety / Shop)."""
    src = FL_HUB.read_text()
    # The 4 collapsing items are wrapped in `hidden sm:flex` or `hidden sm:inline-flex`.
    assert "hidden sm:inline-flex" in src
    assert 'data-testid="leadership-training-link"' in src
    assert 'data-testid="leadership-records-link"' in src


def test_iter319_fl_hub_all_tile_testids_preserved():
    """Every prior `leadership-tile-*` testid must remain."""
    src = FL_HUB.read_text()
    required = [
        "leadership-tile-verbal_coaching",
        "leadership-tile-write_up",
        "leadership-tile-attendance",
        "leadership-tile-recognition",
        "leadership-tile-new_employee_eval",
        "leadership-tile-crew_eval",
        "leadership-tile-promotion_recommendation",
        "leadership-tile-training_deficiency",
        "leadership-tile-equipment_checkout",
        "leadership-tile-equipment_return",
        "leadership-tile-safety_equipment_issuance",
        "leadership-tile-time_off_request",
        "leadership-tile-employee_termination",
        "leadership-tile-po_requests",
    ]
    for tid in required:
        # The testid is built as `leadership-tile-${kind}`; verify the
        # `kind` literal appears in the GROUPS structure.
        kind = tid.replace("leadership-tile-", "")
        assert f'"{kind}"' in src, f"FL Hub must preserve tile kind {kind}"


def test_iter319_fl_hub_group_testids_surfaced():
    """Group sections expose testids for future regression."""
    src = FL_HUB.read_text()
    assert 'data-testid={`leadership-group-${group.kicker}`}' in src


# ─── Field Hub invariants ──────────────────────────────────────────────

def test_iter319_field_hub_calm_tile_pattern():
    """Field Hub uses inline calm tile (no SectionTile import)."""
    src = FIELD_HUB.read_text()
    assert "border-l-4" in src
    assert "function FieldTile" in src
    assert 'from "@/components/SectionTile"' not in src
    assert "<SectionTile" not in src


def test_iter319_field_hub_h1_toned_down():
    """Rule 3: interior-hub H1 size."""
    src = FIELD_HUB.read_text()
    assert "text-3xl sm:text-4xl" in src
    assert "font-display text-4xl sm:text-5xl font-black" not in src


def test_iter319_field_hub_three_groups():
    """Field Hub now renders 3 lightweight operational groups."""
    src = FIELD_HUB.read_text()
    for heading in ("Daily Operations", "Weekly Checks", "Calculators & Tools"):
        assert heading in src, f"Field Hub must surface group: {heading}"
    for tid in (
        "field-group-daily",
        "field-group-weekly",
        "field-group-tools",
        "field-group-heading-daily",
        "field-group-heading-weekly",
        "field-group-heading-tools",
    ):
        assert f'"{tid}"' in src, f"Field Hub must surface group testid {tid}"


def test_iter319_field_hub_tools_group_demoted():
    """Tools section is visually demoted (top-border separator like
    the Integrations group on HR / Safety)."""
    src = FIELD_HUB.read_text()
    assert "pt-6 border-t border-slate-200" in src


def test_iter319_field_hub_all_tile_testids_preserved():
    """All 6 prior `field-tile-*` testids preserved."""
    src = FIELD_HUB.read_text()
    for tid in (
        "field-tile-daily",
        "field-tile-equipment",
        "field-tile-calculators",
        "field-tile-dvir",
        "field-tile-weekly-lead",
        "field-tile-weekly-emergency",
    ):
        assert f'"{tid}"' in src, f"Field Hub must preserve testid {tid}"


# ─── Bilingual gate (Rule 8) ────────────────────────────────────────────

def test_iter319_es_translations_present():
    """All new iter319 group headings + CTAs have ES entries."""
    src = I18N.read_text()
    for entry in (
        '"Daily Operations": "Operaciones Diarias"',
        '"Weekly Checks": "Inspecciones Semanales"',
        '"Calculators & Tools": "Calculadoras y Herramientas"',
        '"START FORM": "INICIAR FORMULARIO"',
        '"START DVIR": "INICIAR DVIR"',
        '"OPEN": "ABRIR"',
    ):
        assert entry in src, f"i18n.js missing ES entry: {entry}"
