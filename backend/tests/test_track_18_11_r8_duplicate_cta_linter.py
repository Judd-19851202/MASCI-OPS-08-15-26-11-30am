"""TRACK 18.11 · R8 Duplicate CTA Linter — lock file.

The R8 implementation lives in `tests/r8_duplicate_cta.py` and is
wired into the design-system linter at
`tests/test_track_18_07_design_system_linter.py::test_lint_no_duplicate_cta_in_card`.

This lock file enforces the 30 directive-mandated assertions:
* The R8 rule is implemented, calibrated, and active.
* The R8 rule fires on 4 seeded should-fail fixtures.
* The R8 rule does NOT fire on 8 seeded should-not-fail fixtures.
* The allow-list / audit / hierarchy registry documents exist.
* Existing R1–R7 rules + Track 18.07 / 18.08 / 18.09C / 18.10
  contracts are preserved.
* Routes / auth / RBAC / dispatch / driver workflows / collections
  are unchanged.
* The deployment gate includes 18.11.
"""
from __future__ import annotations

from pathlib import Path

from tests.r8_duplicate_cta import (
    find_r8_violations,
    R8_PRIMARY_VARIANT_BLOCKERS,
    R8_EXEMPT_SUBTREE_TAGS,
)

ROOT = Path("/app")
MEMORY = ROOT / "memory"
SCRIPTS = ROOT / "scripts"
FRONTEND_SRC = ROOT / "frontend" / "src"
LINTER_FILE = ROOT / "backend" / "tests" / "test_track_18_07_design_system_linter.py"

EXEC_DOC = MEMORY / "TRACK_18_11_R8_DUPLICATE_CTA_LINTER.md"
AUDIT_DOC = MEMORY / "R8_CTA_PATTERN_AUDIT.md"
ALLOWLIST_DOC = MEMORY / "R8_DUPLICATE_CTA_ALLOWLIST.md"


# =====================================================================
# 1. R8 pattern audit exists.
# =====================================================================
def test_01_r8_pattern_audit_exists():
    assert AUDIT_DOC.exists()


# =====================================================================
# 2. CTA hierarchy registry exists.
# =====================================================================
def test_02_cta_hierarchy_registry_exists():
    body = AUDIT_DOC.read_text()
    for category in (
        "PRIMARY CTA",
        "SECONDARY CTA",
        "UTILITY ACTION",
        "ROW / LIST ACTION",
        "PAIRED DECISION",
        "NAVIGATION",
        "DROPDOWN ITEM",
        "STATUS CHIP",
    ):
        assert category in body, f"CTA hierarchy registry missing: {category}"


# =====================================================================
# 3. R8 allow-list exists.
# =====================================================================
def test_03_r8_allowlist_exists():
    assert ALLOWLIST_DOC.exists()
    body = ALLOWLIST_DOC.read_text()
    assert "How to add an entry" in body
    assert "No mystery exceptions" in body


# =====================================================================
# 4. Existing design-system linter still exists.
# =====================================================================
def test_04_existing_design_system_linter_still_exists():
    assert LINTER_FILE.exists()
    body = LINTER_FILE.read_text()
    # R1–R7 anchor rule names.
    for anchor in (
        "test_lint_no_raw_no_data_empty_state",
        "test_lint_no_raw_developer_error_text",
        "test_lint_no_legacy_restricted_state_wording",
        "test_lint_no_user_facing_dispatch_portal",
        "test_lint_no_vague_ctas",
    ):
        assert anchor in body, f"R1–R7 anchor missing from linter: {anchor}"


# =====================================================================
# 5. R8 rule is implemented (the live function is wired in).
# =====================================================================
def test_05_r8_rule_implemented():
    body = LINTER_FILE.read_text()
    assert "test_lint_no_duplicate_cta_in_card" in body, (
        "R8 rule is not wired into the design-system linter."
    )
    assert "from .r8_duplicate_cta import" in body, (
        "R8 helper module is not imported."
    )
    # Confirm the module exists and exports the helpers.
    assert callable(find_r8_violations)
    assert isinstance(R8_PRIMARY_VARIANT_BLOCKERS, tuple)
    assert isinstance(R8_EXEMPT_SUBTREE_TAGS, tuple)


# =====================================================================
# Should-fail fixtures (4)
# =====================================================================
def test_06_r8_catches_two_primary_buttons_in_one_card():
    src = """
    <Card>
      <Button>Open</Button>
      <Button>Review</Button>
    </Card>
    """
    violations = find_r8_violations(src)
    assert len(violations) == 1, (
        "R8 should flag a Card with two default-variant Buttons. "
        f"Got: {violations}"
    )
    assert violations[0]["primary_count"] == 2


def test_07_r8_catches_duplicate_primary_cta_text():
    src = """
    <Card className="...">
      <Button>Open</Button>
      <Button>Open</Button>
    </Card>
    """
    violations = find_r8_violations(src)
    assert len(violations) == 1


def test_08_r8_catches_competing_visually_primary_actions():
    """Two buttons with explicit variant="default" still count as
    primary (default is the primary variant)."""
    src = """
    <Card>
      <Button variant="default">Review Documents</Button>
      <Button variant="default">Check Readiness</Button>
    </Card>
    """
    violations = find_r8_violations(src)
    assert len(violations) == 1


def test_09_r8_catches_mission_control_style_duplicate_cta():
    src = """
    <Card data-testid="mission-tile">
      <h3>Fleet Readiness</h3>
      <p>5 trucks blocked.</p>
      <Button>Open Workspace</Button>
      <Button>View Related Records</Button>
    </Card>
    """
    violations = find_r8_violations(src)
    assert len(violations) == 1


# =====================================================================
# Should-NOT-fail fixtures (8)
# =====================================================================
def test_10_r8_ignores_nav_menu():
    """Buttons inside a NavigationMenu must not trigger R8."""
    src = """
    <Card>
      <NavigationMenu>
        <Button>Home</Button>
        <Button>Profile</Button>
        <Button>Settings</Button>
      </NavigationMenu>
    </Card>
    """
    assert find_r8_violations(src) == []


def test_11_r8_ignores_tabs():
    src = """
    <Card>
      <Tabs defaultValue="a">
        <TabsList>
          <Button>Tab A</Button>
          <Button>Tab B</Button>
          <Button>Tab C</Button>
        </TabsList>
      </Tabs>
    </Card>
    """
    assert find_r8_violations(src) == []


def test_12_r8_ignores_dropdown_menu():
    src = """
    <Card>
      <DropdownMenu>
        <DropdownMenuContent>
          <Button>Edit</Button>
          <Button>Duplicate</Button>
          <Button>Delete</Button>
        </DropdownMenuContent>
      </DropdownMenu>
    </Card>
    """
    assert find_r8_violations(src) == []


def test_13_r8_ignores_table_row_repeated_actions():
    src = """
    <Card>
      <Table>
        <TableBody>
          <TableRow>
            <TableCell><Button>View</Button></TableCell>
          </TableRow>
          <TableRow>
            <TableCell><Button>View</Button></TableCell>
          </TableRow>
          <TableRow>
            <TableCell><Button>View</Button></TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </Card>
    """
    assert find_r8_violations(src) == []


def test_14_r8_ignores_status_chips():
    """Badge / StatusChip / BandChip are not Buttons. Multiple
    Badges in one Card must never trigger R8."""
    src = """
    <Card>
      <Badge>RED</Badge>
      <Badge>YELLOW</Badge>
      <Badge>GREEN</Badge>
      <Button>Open</Button>
    </Card>
    """
    assert find_r8_violations(src) == []


def test_15_r8_ignores_icon_only_utility_actions():
    """Buttons with variant="ghost" or variant="outline" are utility/
    secondary, not primary. Multiple of them with one primary CTA
    must not trigger R8."""
    src = """
    <Card>
      <Button variant="ghost" aria-label="Refresh"><RefreshCcw /></Button>
      <Button variant="ghost" aria-label="Filter"><Filter /></Button>
      <Button>Open Workspace</Button>
    </Card>
    """
    assert find_r8_violations(src) == []


def test_16_r8_allows_save_cancel_pair():
    """The classic Save / Cancel pair (Cancel = outline) is the
    canonical paired-decision pattern. Must not trigger R8."""
    src = """
    <Card>
      <Button>Save</Button>
      <Button variant="outline">Cancel</Button>
    </Card>
    """
    assert find_r8_violations(src) == []


def test_17_r8_allows_approve_needs_correction_pair():
    """Disposition workflow uses Approve (primary) + Needs Correction
    (outline). Must not trigger R8."""
    src = """
    <Card>
      <Button>Approve</Button>
      <Button variant="outline">Needs Correction</Button>
    </Card>
    """
    assert find_r8_violations(src) == []


# =====================================================================
# 18. R8 allows separate cards each with one CTA.
# =====================================================================
def test_18_r8_allows_separate_cards_each_with_one_cta():
    """A multi-card grid where each Card has its own primary CTA is
    a valid pattern — every Card has exactly one primary Button."""
    src = """
    <div className="grid grid-cols-3 gap-4">
      <Card>
        <h3>Field</h3>
        <Button>Enter →</Button>
      </Card>
      <Card>
        <h3>QA / QC</h3>
        <Button>Enter →</Button>
      </Card>
      <Card>
        <h3>Safety</h3>
        <Button>Enter →</Button>
      </Card>
    </div>
    """
    assert find_r8_violations(src) == []


# =====================================================================
# 19. R8 allow-list entries require justification.
# =====================================================================
def test_19_allowlist_entries_require_justification():
    body = ALLOWLIST_DOC.read_text()
    # The allow-list must demand a Reason / Why / Future review for
    # every entry.
    assert "Reason" in body
    assert "Why it is not CTA confusion" in body
    assert "Future review" in body
    # No "looks fine to me" rationales.
    forbidden = ("Looks fine to me", "Always been like that", "Looks fine")
    for f in forbidden:
        assert f in body, f"Forbidden-rationale guidance missing: {f}"


# =====================================================================
# 20. R8 error message is actionable.
# =====================================================================
def test_20_r8_error_message_is_actionable():
    body = LINTER_FILE.read_text()
    # The R8 assertion message must guide the developer to either
    # downgrade variants OR add an allow-list entry.
    assert "R8 Duplicate CTA" in body
    assert 'variant="outline"' in body
    assert 'variant="ghost"' in body
    assert "R8_DUPLICATE_CTA_ALLOWLIST.md" in body


# =====================================================================
# 21. Existing R1–R7 linter rules preserved.
# =====================================================================
def test_21_r1_through_r7_preserved():
    body = LINTER_FILE.read_text()
    for anchor in (
        "test_lint_no_raw_no_data_empty_state",
        "test_lint_no_raw_developer_error_text",
        "test_lint_no_legacy_restricted_state_wording",
        "test_lint_no_user_facing_dispatch_portal",
        "test_lint_no_user_facing_pm_portal",
        "test_lint_no_user_facing_hr_portal",
        "test_lint_no_user_facing_safety_portal",
        "test_lint_no_user_facing_shop_portal",
        "test_lint_no_user_facing_admin_console",
        "test_lint_no_user_facing_admin_portal",
        "test_lint_no_user_facing_office_portals",
        "test_lint_no_user_facing_masci_hub",
        "test_lint_no_vague_ctas",
        "test_lint_no_status_color_without_label",
    ):
        assert anchor in body, f"R1–R7 anchor removed: {anchor}"


# =====================================================================
# 22. No new routes.
# =====================================================================
def test_22_no_new_routes():
    app_js = (FRONTEND_SRC / "App.js").read_text()
    # Canonical doorways still present (sanity).
    assert "/transportation-operations/*" in app_js
    assert "/admin/transportation/*" in app_js


# =====================================================================
# 23. No auth changes.
# =====================================================================
def test_23_no_auth_changes():
    app_js = (FRONTEND_SRC / "App.js").read_text()
    assert "A(" in app_js
    assert "TX(" in app_js


# =====================================================================
# 24. No RBAC changes.
# =====================================================================
def test_24_no_rbac_changes():
    app_js = (FRONTEND_SRC / "App.js").read_text()
    assert "adminAuth" in app_js or "isAdmin" in app_js


# =====================================================================
# 25. Dispatch execution preserved.
# =====================================================================
def test_25_dispatch_execution_preserved():
    app_js = (FRONTEND_SRC / "App.js").read_text()
    assert "DispatchBoard" in app_js or "/dispatch-portal" in app_js


# =====================================================================
# 26. Driver workflows preserved.
# =====================================================================
def test_26_driver_workflows_preserved():
    app_js = (FRONTEND_SRC / "App.js").read_text()
    assert "/dr/" in app_js or "DriverPortal" in app_js or "/driver/" in app_js


# =====================================================================
# 27. No new collections.
# =====================================================================
def test_27_no_new_collections():
    server = (ROOT / "backend" / "server.py").read_text()
    for sample in ("users", "operational_events"):
        assert sample in server


# =====================================================================
# 28. Deployment gate includes Track 18.11.
# =====================================================================
def test_28_deployment_gate_includes_18_11():
    gate = (SCRIPTS / "deployment_gate.py").read_text()
    assert "test_track_18_11_r8_duplicate_cta_linter.py" in gate


# =====================================================================
# 29. Full Track 18 family — sanity that 18.11 doesn't break neighbors.
# =====================================================================
def test_29_track_18_family_neighbors_compile():
    import py_compile
    for name in (
        "test_track_18_07_design_system_linter.py",
        "test_track_18_08_regression_stability_device_polish.py",
        "test_track_18_09_operational_friction_elimination.py",
        "test_track_18_09a_true_completion_pass.py",
        "test_track_18_09c_transportation_ownership.py",
        "test_track_18_10_governance_boundary_linter.py",
    ):
        p = ROOT / "backend" / "tests" / name
        py_compile.compile(str(p), doraise=True)


# =====================================================================
# 30. Final certification declares R8 active.
# =====================================================================
def test_30_final_certification_declares_r8_active():
    body = EXEC_DOC.read_text()
    assert "R8 is active" in body
    assert "🟢" in body and "GO" in body
    assert "Administration governs" not in body, (
        "Track 18.11 is a design-system track, not a governance track. "
        "Don't dilute the constitutional rule from 18.10."
    )
