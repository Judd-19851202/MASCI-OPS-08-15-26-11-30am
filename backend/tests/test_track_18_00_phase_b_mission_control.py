"""TRACK 18.00 · Phase B · Mission Control regression.

Phase B delivers the operator-facing landing experience for
Transportation Operations. The mandate: every card answers one
of these 8 operational questions, composed entirely from
existing engines.

This regression locks the contract:

  1. ``MissionControl`` component exists and is mounted inside
     ``TransportationDashboard`` (so the Track 16.15A regression
     contract — TopCleanupOpportunityCard inside dashboard —
     still holds).
  2. Exactly eight question-driven cards are present, each with
     the required testid surface and an action link.
  3. Mission brief renders the calm one-sentence summary.
  4. Mission Control composes ONLY existing engines (no new
     backend endpoints, no new scoring, no new collections).
  5. Dispatch is linked, NEVER embedded. The Dispatch card
     links to the Dispatch bridge / portal — it does not render
     the dispatch board / map / ledger components.
  6. Phase A nav + workspace shell remain intact.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path("/app")
FRONTEND_TX = ROOT / "frontend" / "src" / "pages" / "transportation"
MC = FRONTEND_TX / "MissionControl.jsx"
VIEWS = FRONTEND_TX / "_views.jsx"
APP = FRONTEND_TX / "TransportationApp.jsx"
SHARED = FRONTEND_TX / "_shared.jsx"
SHELL = FRONTEND_TX / "TransportationWorkspaceShell.jsx"
GATE = ROOT / "scripts" / "deployment_gate.py"


# ===========================================================================
# 1 — MissionControl.jsx exists and exports the default component.
# ===========================================================================
def test_01_mission_control_file_exists():
    assert MC.exists(), "Phase B must ship MissionControl.jsx"
    src = MC.read_text()
    assert "export default function MissionControl()" in src


# ===========================================================================
# 2 — Mission Control is mounted inside TransportationDashboard
#      (preserves Track 16.15A contract).
# ===========================================================================
def test_02_mission_control_mounted_in_dashboard():
    src = VIEWS.read_text()
    # Function must still be exported with the same name.
    assert "export function TransportationDashboard(" in src
    # And must mount <MissionControl /> inside it.
    dash_idx = src.find("export function TransportationDashboard(")
    next_export = src.find("export function ", dash_idx + 1)
    body = src[dash_idx:(next_export if next_export > 0 else len(src))]
    assert "<MissionControl" in body, (
        "TransportationDashboard must mount <MissionControl />")
    # And keep TopCleanupOpportunityCard mounted (Track 16.15A).
    assert "<TopCleanupOpportunityCard" in body, (
        "Phase B must preserve the Track 16.15A "
        "<TopCleanupOpportunityCard /> mount inside dashboard")


# ===========================================================================
# 3 — All eight operator-facing cards are present with their testids.
# ===========================================================================
def test_03_eight_operational_cards_present():
    src = MC.read_text()
    required_cards = (
        "mc-card-fleet",        # Card 1 · Fleet Ready?
        "mc-card-drivers",      # Card 2 · Drivers Ready?
        "mc-card-carriers",     # Card 3 · Carriers Ready?
        "mc-card-dispatch",     # Card 4 · Dispatch Healthy?
        "mc-card-blocking",     # Card 5 · Anything Blocking?
        "mc-card-recent",       # Card 6 · What Changed Today?
        "mc-card-attention",    # Card 7 · What Needs Attention?
        "mc-card-next",         # Card 8 · What Should We Do Next?
    )
    for tid in required_cards:
        assert tid in src, f"Mission Control missing card {tid!r}"


# ===========================================================================
# 4 — Every card carries the eight question labels.
# ===========================================================================
def test_04_card_questions_present():
    src = MC.read_text()
    for q in (
        "Fleet Ready?",
        "Drivers Ready?",
        "Carriers Ready?",
        "Dispatch Healthy?",
        "Anything Blocking?",
        "What Changed Today?",
        "What Needs Attention?",
        "What Should We Do Next?",
    ):
        assert q in src, f"Mission Control missing question {q!r}"


# ===========================================================================
# 5 — Mission brief banner exists with a one-sentence summary.
# ===========================================================================
def test_05_mission_brief_present():
    src = MC.read_text()
    assert 'data-testid="mc-mission-brief"' in src
    assert 'data-testid="mc-mission-brief-line"' in src
    # The 3 calm copy lines must all be present (healthy · watch ·
    # immediate attention).
    for line in (
        "Transportation Operations is healthy",
        "Transportation Operations operating with watch items",
        "Transportation Operations requires immediate attention",
    ):
        assert line in src, f"Mission brief missing copy {line!r}"


# ===========================================================================
# 6 — Mission Control composes from existing endpoints only.
# ===========================================================================
def test_06_only_existing_endpoints_consumed():
    src = MC.read_text()
    # MUST use the existing Track 16.16 readiness hook.
    assert "useTransportationReadiness" in src
    # MUST reuse the existing audit-timeline endpoint.
    assert "/admin/transportation/audit-timeline" in src
    # MUST NOT call any new endpoint that does not already exist.
    forbidden_new_endpoints = (
        "/mission-control",
        "/operations/mission-control",
        "/admin/transportation/mission",
        "/admin/transportation/landing",
    )
    for ep in forbidden_new_endpoints:
        assert ep not in src, (
            f"Mission Control must not call new endpoint {ep!r}")


# ===========================================================================
# 7 — Each card has a primary action with deep link.
# ===========================================================================
def test_07_each_card_has_action():
    src = MC.read_text()
    for tid in (
        "mc-card-fleet", "mc-card-drivers", "mc-card-carriers",
        "mc-card-dispatch", "mc-card-blocking", "mc-card-recent",
        "mc-card-attention", "mc-card-next",
    ):
        action_marker = f'data-testid={{`${{testid}}-action`}}'  # interpolation form
        # We assert the McCard helper renders an action testid suffix.
        assert action_marker in src or f'{tid}-action' in src, (
            f"Card {tid!r} missing action affordance")
    # Helper-level pattern (single source of truth for action testid).
    assert "${testid}-action" in src


# ===========================================================================
# 8 — Dispatch card is link-only (never embeds dispatch components).
# ===========================================================================
def test_08_dispatch_card_is_link_only():
    src = MC.read_text()
    # The Dispatch card must point to the dispatch bridge route. Per
    # Track 18.12, Mission Control links are now prefix-aware
    # (`${prefix}/dispatch`) so dispatch users stay inside
    # `/transportation-operations/*` while admin users stay inside
    # `/admin/transportation/*`. Either literal admin reference OR
    # the prefix-aware variant is acceptable.
    assert "/admin/transportation/dispatch" in src or "${prefix}/dispatch" in src, (
        "Mission Control's Dispatch card must link to the dispatch "
        "bridge route (literal admin reference or prefix-aware "
        "variant)."
    )
    # And must NOT embed any dispatch live component.
    for forbidden in (
        "<DispatchBoard",
        "<DispatchCommandCenter",
        "<DispatchOperationsMapPage",
        "<DispatchHaulLedger",
        "/api/dispatch/assignments",
        "dispatch_state_events",
    ):
        assert forbidden not in src, (
            f"Mission Control must not embed dispatch logic "
            f"(found {forbidden!r})")


# ===========================================================================
# 9 — Zero new backend route added in Phase B.
# ===========================================================================
def test_09_no_new_backend_route_in_phase_b():
    routes_dir = ROOT / "backend" / "routes"
    forbidden_markers = (
        "transportation_mission_control",
        "transportation_phase_b",
        "transportation_operations_2_phase_b",
        "mission_control",
    )
    for marker in forbidden_markers:
        for p in routes_dir.glob(f"*{marker}*.py"):
            raise AssertionError(
                f"Phase B must not introduce a new backend route: {p}")


# ===========================================================================
# 10 — Phase A nav + shell remain intact (no regression).
# ===========================================================================
def test_10_phase_a_artifacts_intact():
    nav_src = SHARED.read_text()
    assert "TX_OPS_NAV_GROUPS" in nav_src
    shell_src = SHELL.read_text()
    assert "TransportationWorkspaceShell" in shell_src


# ===========================================================================
# 11 — Phase B regression file wired into the deployment gate.
# ===========================================================================
def test_11_wired_into_deployment_gate():
    src = GATE.read_text()
    assert "test_track_18_00_phase_b_mission_control.py" in src, (
        "Phase B regression must be wired into "
        "/app/scripts/deployment_gate.py")


# ===========================================================================
# 12 — Refresh affordance exists.
# ===========================================================================
def test_12_refresh_affordance_present():
    src = MC.read_text()
    assert 'data-testid="mc-refresh"' in src


# ===========================================================================
# 13 — Source attribution callout (transparency for operators).
# ===========================================================================
def test_13_source_attribution_present():
    src = MC.read_text()
    assert "composed from Tracks" in src.lower() or "Source · composed" in src
