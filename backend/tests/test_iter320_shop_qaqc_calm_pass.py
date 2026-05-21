"""iter320 · Shop Hub + QA/QC Section Calm Pass + Safety validation.

Locks the iter320 platform-convergence pass:
- Shop Hub: H1 toned to interior size · KPI chrome neutralized ·
  Fleet banner converted to calm left-edge stripe card · tabs active
  state demoted from hot `bg-amber-50` to no-fill underline.
- QA/QC Section: full calm rewrite · SectionTile removed · H1 toned ·
  CTA uppercased · matched section heading style.
- Safety Hub: validated as already-on-contract (no code change).
"""
from pathlib import Path

FRONTEND = Path(__file__).resolve().parent.parent.parent / "frontend/src"
SHOP_HUB = FRONTEND / "pages/ShopHub.jsx"
QAQC = FRONTEND / "pages/QaqcSection.jsx"
SAFETY_HUB = FRONTEND / "pages/SafetyHub.jsx"
I18N = FRONTEND / "lib/i18n.js"


# ─── Shop Hub invariants ─────────────────────────────────────────────────

def test_iter320_shop_hub_h1_toned():
    src = SHOP_HUB.read_text()
    assert "text-3xl sm:text-4xl" in src
    # Legacy hero H1 size must not return.
    assert "font-display text-4xl sm:text-5xl font-black" not in src


def test_iter320_shop_hub_kpi_calmed():
    """Shop KPI chrome neutralized to Rule 5."""
    src = SHOP_HUB.read_text()
    # New calm chrome present.
    assert "bg-white border border-slate-200 rounded-md p-4" in src
    # Legacy hot chrome gone from the Kpi component.
    assert "border-2 border-slate-200 rounded-md px-4 py-3" not in src


def test_iter320_shop_hub_fleet_banner_calmed():
    """Fleet banner now uses calm left-edge stripe pattern, no hot
    amber-300 border + amber-50 hover fill."""
    src = SHOP_HUB.read_text()
    fleet_pos = src.find('data-testid="shop-fleet-link"')
    assert fleet_pos > 0
    # The calm pattern signature should appear at/near the fleet link.
    block = src[fleet_pos:fleet_pos + 800]
    assert "border-l-4 border-l-amber-500" in block
    assert "bg-white" in block
    assert "border-2 border-amber-300" not in block
    assert "hover:bg-amber-50" not in block


def test_iter320_shop_hub_tabs_active_state_calmed():
    """Tab active state must not use the legacy `bg-amber-50` hot fill."""
    src = SHOP_HUB.read_text()
    # The exact legacy active-state string must not reappear.
    assert "text-amber-700 border-amber-600 bg-amber-50" not in src
    # The new calm pattern is text+underline only.
    assert "text-amber-700 border-amber-600" in src


def test_iter320_shop_hub_all_testids_preserved():
    """All Shop testids preserved (regression contract)."""
    src = SHOP_HUB.read_text()
    # Static testids — must appear literally.
    for tid in (
        "shop-nav-home",
        "shop-training-link",
        "shop-change-pw-link",
        "shop-logout-btn",
        "shop-kpi-strip",
        "shop-fleet-link",
        "shop-integrations-tab",
    ):
        assert f'"{tid}"' in src, f"Shop must preserve testid {tid}"
    # Tab testids rendered via template literal — verify all 7 tab keys
    # are still in the tab array AND the template-literal testid pattern
    # is intact.
    assert "`shop-tab-${s.key}`" in src
    for key in ("open", "activity", "trends", "recent", "equipment", "parts", "integrations"):
        assert f'key: "{key}"' in src, f"Shop must preserve tab key {key}"


# ─── QA/QC invariants ────────────────────────────────────────────────────

def test_iter320_qaqc_calm_tile_pattern():
    src = QAQC.read_text()
    assert "border-l-4" in src
    assert "function QaqcTile" in src
    assert 'from "@/components/SectionTile"' not in src
    assert "<SectionTile" not in src


def test_iter320_qaqc_h1_toned():
    src = QAQC.read_text()
    assert "text-3xl sm:text-4xl" in src
    assert "font-display text-4xl sm:text-5xl font-black" not in src


def test_iter320_qaqc_cta_uppercased():
    """Family contract uses UPPERCASE CTA labels."""
    src = QAQC.read_text()
    assert 't("START FORM")' in src
    assert 't("Start Form")' not in src


def test_iter320_qaqc_section_heading_present():
    """Single-group section heading matches family pattern."""
    src = QAQC.read_text()
    assert 'data-testid="qaqc-section-heading"' in src
    assert 'tracking-[0.22em] text-slate-700' in src


def test_iter320_qaqc_all_tile_testids_preserved():
    src = QAQC.read_text()
    # QaqcTile receives a `testId` prop (not `data-testid` directly).
    # Verify the template-literal testId is wired correctly.
    assert "testId={`qaqc-tile-${kind.slug}`}" in src


# ─── Safety Hub validation (no change · just contract verification) ─────

def test_iter320_safety_hub_still_on_contract():
    """Safety Hub iter318 work must continue to satisfy the family
    contract — this guards against drift."""
    src = SAFETY_HUB.read_text()
    assert "border-l-4" in src
    assert "border border-slate-200 rounded-md p-4" in src  # KPI Rule 5
    assert "tracking-[0.22em]" in src
    # No legacy hot SectionTile import on Safety.
    assert 'from "@/components/SectionTile"' not in src


# ─── Bilingual gate ──────────────────────────────────────────────────────

def test_iter320_es_translations_present():
    src = I18N.read_text()
    for entry in (
        '"Inspection Forms": "Formularios de Inspección"',
        '"Routed, signed, photographed, and stored": "Enrutado, firmado, fotografiado y almacenado"',
    ):
        assert entry in src, f"i18n.js missing ES entry: {entry}"
