"""iter317-C Part 2 · HR Portal Visual-Hierarchy Refinement.

Locks the grouped-card visual refinement on HrHub.jsx so future
edits don't accidentally revert the calm, grouped layout. Bounded:
4 operational groups · all 14 tiles preserved · testids preserved ·
left-edge stripe pattern in place · no sidebar introduced.
"""
from pathlib import Path

HR_HUB = Path(__file__).resolve().parent.parent.parent / "frontend/src/pages/HrHub.jsx"


def _src():
    assert HR_HUB.exists(), "HrHub.jsx must exist"
    return HR_HUB.read_text()


def test_iter317c2_hr_hub_has_four_named_groups():
    src = _src()
    assert "TILE_GROUPS" in src, "HrHub must define TILE_GROUPS structure"
    for heading in (
        "Primary HR Actions",
        "Compliance & Accountability",
        "Payroll / Time",
        "Integrations & Systems",
    ):
        assert heading in src, f"HR Hub must surface group heading: {heading}"


def test_iter317c2_all_existing_tiles_preserved():
    """All 14 prior tile destinations must still render — no tile lost
    in the refinement."""
    src = _src()
    required_routes = [
        "/hr/employees",
        "/tasks",
        "/document-expirations",
        "/po-requests",
        "/hr/field-leadership",
        "/hr/field-leadership-users",
        "/hr/time-off",
        "/hr/employee-accountability",
        "/hr/time-verification",
        "/hr/payroll-variance",
        "/hr/training-records",
        "/hr/driver-qualification",
        "/hr/safety-records",
        "/guidance",
    ]
    for route in required_routes:
        # iter322 — guidance route may carry a `?from=hr` suffix for
        # portal-continuity. Accept either form.
        assert f'"{route}"' in src or f'"{route}?from=' in src, (
            f"HR Hub must preserve tile route {route}"
        )


def test_iter317c2_left_edge_stripe_pattern_in_place():
    """Calm visual: tiles use border-l-4 stripe + neutral border, NOT
    the legacy hot border-2 + colored bg combination."""
    src = _src()
    assert "border-l-4" in src, "Tiles must use left-edge accent stripe"
    # Legacy hot-border pattern must be gone from the tile renderer.
    assert "border-2 ${tile.accent}" not in src
    assert "bg-emerald-50" not in src or "stripe" in src  # no bg-emerald-50 as tile fill


def test_iter317c2_no_sidebar_introduced():
    """Operator mandate: do NOT convert to a sidebar layout."""
    src = _src()
    # Common sidebar markers — none should appear in the HR Hub.
    for marker in ("<aside", "Sidebar", "sidebar-nav", "drawer-nav"):
        assert marker not in src, f"HR Hub must not introduce {marker}"


def test_iter317c2_testids_preserved():
    """All tile testids must remain so iter314/iter315 regressions pass."""
    src = _src()
    assert 'data-testid={`hr-tile-${tile.to.split' in src
    assert 'data-testid={`hr-tile-badge-${tile.to.split' in src
    # Group testids added (new invariant — surfaced for future regression).
    assert 'data-testid={`hr-group-${group.key}`}' in src


def test_iter317c2_integrations_section_visually_demoted():
    """Integrations & Systems section must visually feel lower-priority
    via the `muted` flag and a top-border separator."""
    src = _src()
    assert "muted: true" in src
    assert "border-t border-slate-200" in src


def test_iter317c2_hover_translate_preserved():
    """Muscle-memory contract — hover micro-interaction must remain."""
    src = _src()
    assert "hover:-translate-y-0.5" in src
    assert "hover:shadow-md" in src


def test_iter317c2_bilingual_t_calls_preserved():
    """All tile labels, descriptions, group headings and the OPEN
    button must still flow through t() for ES parity."""
    src = _src()
    assert "{t(tile.label)}" in src
    assert "{t(tile.desc)}" in src
    assert "{t(group.heading)}" in src
    assert "{t(group.sub)}" in src
    assert '{t("OPEN →")}' in src
