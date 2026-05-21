"""iter318 · Safety Hub Calm Pass invariants.

Locks the iter318 visual refinement so future edits don't accidentally
revert the calm grouped layout. Bounded:
- All 15 prior tile destinations preserved
- All 15 tile testids preserved
- 4 grouped sections present (primary · compliance · output · systems)
- Calm tile pattern in place (border-l-4 left-edge stripe)
- KPI chrome neutralized (no border-2 hot fills)
- Integration cards demoted to the Systems group (bottom)
- Bilingual `t()` calls preserved
- No sidebar introduced
"""
from pathlib import Path

SAFETY_HUB = Path(__file__).resolve().parent.parent.parent / "frontend/src/pages/SafetyHub.jsx"


def _src():
    assert SAFETY_HUB.exists(), "SafetyHub.jsx must exist"
    return SAFETY_HUB.read_text()


def test_iter318_safety_hub_has_four_named_groups():
    src = _src()
    for heading in (
        "Primary Safety Operations",
        "Compliance & Records",
        "Operational Output",
        "Guidance & Systems",
    ):
        assert heading in src, f"Safety Hub must surface group heading: {heading}"


def test_iter318_all_existing_tile_routes_preserved():
    """All 15 prior tile destinations must still render — no tile lost
    in the refinement (regression contract)."""
    src = _src()
    required_routes = [
        "/tasks",
        "/document-expirations",
        "/safety-portal/corrective-actions",
        "/safety-portal/incidents",
        "/safety-portal/audits",
        "/safety-portal/training",
        "/safety-portal/employees",
        "/safety-portal/fire-extinguishers",
        "/safety-portal/documents",
        "/safety-portal/digest",
        "/safety-portal/reports",
        "/safety-portal/fleet",
        "/safety-portal/library",
        "/guidance",
        "/safety-portal/change-password",
    ]
    for route in required_routes:
        # iter322 — guidance route may carry a `?from=safety` suffix
        # for portal-continuity. Accept either form.
        assert f'"{route}"' in src or f'"{route}?from=' in src, (
            f"Safety Hub must preserve tile route {route}"
        )


def test_iter318_all_tile_testids_preserved():
    """Every prior `safety-tile-*` testid must remain (regression
    contract with iter120/iter192 tests)."""
    src = _src()
    required_testids = [
        "safety-tile-tasks",
        "safety-tile-expirations",
        "safety-tile-ca",
        "safety-tile-incidents",
        "safety-tile-audits",
        "safety-tile-training",
        "safety-tile-employees",
        "safety-tile-extinguishers",
        "safety-tile-docs",
        "safety-tile-digest",
        "safety-tile-reports",
        "safety-tile-fleet",
        "safety-tile-topic-library",
        "safety-tile-training-center",
        "safety-tile-changepw",
    ]
    for tid in required_testids:
        assert f'"{tid}"' in src, f"Safety Hub must preserve testid {tid}"


def test_iter318_group_testids_surfaced():
    """New group + heading testids surfaced for downstream regression."""
    src = _src()
    for tid in (
        "safety-group-primary",
        "safety-group-compliance",
        "safety-group-output",
        "safety-group-systems",
        "safety-group-heading-primary",
        "safety-group-heading-compliance",
        "safety-group-heading-output",
        "safety-group-heading-systems",
    ):
        assert f'"{tid}"' in src, f"Safety Hub must surface group testid {tid}"


def test_iter318_calm_tile_pattern_in_place():
    """Tiles use the calm left-edge-stripe pattern; legacy hot
    `border-2 border-slate-300` SectionTile chrome is gone from this
    file (SectionTile is still allowed elsewhere — just not Safety Hub)."""
    src = _src()
    assert "border-l-4" in src, "Safety tiles must use left-edge accent stripe"
    # Legacy hot SectionTile import must be gone — Safety Hub now
    # renders calm tiles inline (mirrors HrHub's approach).
    assert "from \"@/components/SectionTile\"" not in src, (
        "Safety Hub should no longer import the hot SectionTile component"
    )
    # No bg-<accent>-50 tile fills.
    for forbidden in ("bg-cyan-50", "bg-red-50", "bg-amber-50", "bg-emerald-50"):
        # Cyan/red/amber/emerald in `bg-50` form must not appear as TILE
        # fill. They may appear on warning banners outside this file —
        # that's fine — but not inside SafetyHub's tile renderer.
        # We assert their absence in the file body entirely (Safety Hub
        # tiles never use a colored bg in the calm pass).
        assert forbidden not in src, (
            f"Safety Hub tile chrome must not use {forbidden}"
        )


def test_iter318_kpi_chrome_neutralized():
    """KPI block must use `border border-slate-200` (Rule 5) — not the
    legacy `border-2 border-<accent>-700` hot chrome."""
    src = _src()
    assert "border border-slate-200 rounded-md p-4" in src, (
        "KPI must use Rule 5 neutral chrome"
    )
    # No `border-2 border-cyan-700` etc. on the KPI element.
    for legacy in (
        "border-2 border-cyan-700",
        "border-2 border-red-700",
        "border-2 border-amber-600",
        "border-2 border-emerald-700",
    ):
        assert legacy not in src, f"KPI chrome must not use legacy {legacy}"


def test_iter318_integrations_demoted_to_systems_group():
    """Integration cards must live inside the Systems group, NOT above
    the tile grid (Rule 6 — integrations support, do not compete)."""
    src = _src()
    primary_pos = src.find("safety-group-primary")
    integrations_pos = src.find("safety-integrations-strip")
    systems_pos = src.find("safety-group-systems")
    assert primary_pos > 0 and integrations_pos > 0 and systems_pos > 0
    assert systems_pos < integrations_pos, (
        "Integrations strip must be rendered inside the Systems section"
    )
    assert primary_pos < integrations_pos, (
        "Integrations strip must appear AFTER Primary Operations section"
    )
    # And the demoted Systems section must carry the top-border separator.
    assert "border-t border-slate-200" in src, (
        "Systems section must use a top-border separator (demoted)"
    )


def test_iter318_no_sidebar_introduced():
    """Operator mandate: do NOT convert to a sidebar layout."""
    src = _src()
    for marker in ("<aside", "Sidebar", "sidebar-nav", "drawer-nav"):
        assert marker not in src, f"Safety Hub must not introduce {marker}"


def test_iter318_bilingual_t_calls_preserved():
    """All tile labels, group headings, KPI labels must flow through t()."""
    src = _src()
    # Spot-check that t() is wrapping the new group headings and titles.
    for phrase in (
        't("Primary Safety Operations")',
        't("Compliance & Records")',
        't("Operational Output")',
        't("Guidance & Systems")',
        't("Tasks & Actions")',
        't("Corrective Actions")',
        't("Incidents & Near Misses")',
        't("Fire Extinguishers")',
    ):
        assert phrase in src, f"Safety Hub must wrap {phrase} through t()"


def test_iter318_safety_shell_chrome_preserved():
    """SafetyShell wraps the hub (header / nav / sign-out chrome
    unchanged). Iter203 mobile-collapse lives in the shell, not here."""
    src = _src()
    assert "import SafetyShell" in src
    assert "<SafetyShell" in src
    assert 'title="Safety Operations Dashboard"' in src


def test_iter318_es_translations_present():
    """Bilingual gate (Rule 8): every new group heading + subtitle must
    have an ES dictionary entry so no English leaks on the ES surface."""
    i18n_path = SAFETY_HUB.parent.parent / "lib" / "i18n.js"
    src = i18n_path.read_text()
    required_es = [
        '"Primary Safety Operations": "Operaciones Principales de Seguridad"',
        '"Day-to-day safety workflows": "Flujos diarios de seguridad"',
        '"Compliance & Records": "Cumplimiento y Registros"',
        '"Operational Output": "Producción Operacional"',
        '"Guidance & Systems": "Guía y Sistemas"',
    ]
    for entry in required_es:
        assert entry in src, f"i18n.js missing ES entry: {entry}"


def test_iter318_hr_group_headings_es_present():
    """iter317-C HR group headings must also have ES entries (bilingual
    parity was previously missing — closed as part of iter318)."""
    i18n_path = SAFETY_HUB.parent.parent / "lib" / "i18n.js"
    src = i18n_path.read_text()
    for entry in (
        '"Primary HR Actions": "Acciones Principales de RH"',
        '"Compliance & Accountability": "Cumplimiento y Rendición de Cuentas"',
        '"Payroll / Time": "Nómina / Tiempo"',
        '"Integrations & Systems": "Integraciones y Sistemas"',
    ):
        assert entry in src, f"i18n.js missing iter317-C ES entry: {entry}"
