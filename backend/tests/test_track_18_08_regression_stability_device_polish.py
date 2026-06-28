"""TRACK 18.08 · Regression Stability + Device Polish Closure
regression lock.

Verifies the foundation-trust deliverables of Track 18.08:
* Deployment Gate Trust Report exists with the 3-run evidence.
* Flake root-cause investigation documented.
* Live Map mobile + admin table mobile dispositions documented.
* Design System Linter expanded with R6 (status color without label)
  and R7 (hardcoded mobile-breaking widths).
* No new collections / routes / auth / RBAC changes.
* Track 18.07 linter rules preserved.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path("/app")
MEMORY = ROOT / "memory"
BACKEND = ROOT / "backend"
GATE = ROOT / "scripts" / "deployment_gate.py"

CERT = MEMORY / "TRACK_18_08_REGRESSION_STABILITY_DEVICE_POLISH.md"
TRUST_REPORT = MEMORY / "DEPLOYMENT_GATE_TRUST_REPORT.md"
DESIGN_SYSTEM = MEMORY / "OPERATIONAL_DESIGN_SYSTEM.md"
LINTER_RULES = MEMORY / "DESIGN_SYSTEM_LINTER_RULES.md"
LINTER = BACKEND / "tests" / "test_track_18_07_design_system_linter.py"


# ===========================================================================
# 1–5 · Deliverable docs present.
# ===========================================================================
def test_01_certification_doc_exists():
    assert CERT.exists()


def test_02_deployment_gate_trust_report_exists():
    assert TRUST_REPORT.exists()


def test_03_design_system_doc_intact():
    assert DESIGN_SYSTEM.exists()


def test_04_linter_rules_doc_intact():
    assert LINTER_RULES.exists()


def test_05_linter_file_intact():
    assert LINTER.exists()


# ===========================================================================
# 6–10 · Flake investigation documented.
# ===========================================================================
def test_06_trust_report_documents_three_run_evidence():
    src = TRUST_REPORT.read_text()
    assert "1440 passed" in src
    # All three runs documented.
    assert src.count("1440 passed") >= 3 or "3 consecutive" in src.lower()


def test_07_15_76_flake_root_cause_documented():
    src = CERT.read_text()
    assert "test_emit_stage_writes_event" in src or "15_76_trust_spine" in src
    assert "transient" in src.lower() or "root cause" in src.lower()


def test_08_15_79e_flake_root_cause_documented():
    src = CERT.read_text()
    assert "15_79e" in src or "15.79E" in src or "not_yet_exercised" in src
    assert "transient" in src.lower() or "root cause" in src.lower()


def test_09_trust_report_documents_containment_plan():
    src = TRUST_REPORT.read_text()
    assert "Containment plan" in src or "containment plan" in src.lower()


def test_10_trust_report_declares_deterministic():
    src = TRUST_REPORT.read_text()
    assert "deterministic" in src.lower()


# ===========================================================================
# 11–14 · Device polish dispositions documented.
# ===========================================================================
def test_11_live_map_mobile_documented():
    src = CERT.read_text()
    assert "Live Map" in src or "live map" in src.lower()
    for px in ("390", "430", "768"):
        assert px in src, f"Live Map breakpoint {px} missing from cert doc"


def test_12_admin_table_mobile_documented():
    src = CERT.read_text()
    assert "Admin table" in src or "admin table" in src.lower()


def test_13_disposition_explicit():
    src = CERT.read_text()
    assert "No code change required" in src or "Disposition" in src


def test_14_deferrals_documented():
    src = CERT.read_text()
    assert "Deferral" in src or "deferral" in src.lower()


# ===========================================================================
# 15–22 · Linter expansion R6 + R7.
# ===========================================================================
def test_15_linter_defines_r6_status_color_without_label():
    src = LINTER.read_text()
    assert "test_lint_no_status_color_without_label" in src
    assert "R6" in src or "Status color without label" in src


def test_16_linter_defines_r7_hardcoded_widths():
    src = LINTER.read_text()
    assert "test_lint_no_hardcoded_mobile_breaking_widths" in src
    assert "R7" in src or "Hardcoded mobile" in src


def test_17_r7_uses_negative_lookbehind_for_max_w():
    """R7 must NOT match `max-w-[Npx]` (different Tailwind primitive)."""
    src = LINTER.read_text()
    assert "(?<!max-)" in src


def test_18_r7_allows_overflow_wrapped_files():
    src = LINTER.read_text()
    assert "overflow-x-auto" in src or "overflow-x-scroll" in src


def test_19_linter_r4_legacy_workspace_rules_preserved():
    src = LINTER.read_text()
    # All 9 banned workspace tokens still scanned.
    for token in ("Dispatch Portal", "PM Portal", "HR Portal",
                  "Safety Portal", "Shop Portal", "Admin Portal",
                  "Admin Console", "Office Portals", "MASCI Hub"):
        assert token in src


def test_20_linter_r1_empty_state_preserved():
    src = LINTER.read_text()
    assert "test_lint_no_raw_no_data_empty_state" in src


def test_21_linter_r2_error_state_preserved():
    src = LINTER.read_text()
    assert "test_lint_no_raw_developer_error_text" in src


def test_22_linter_r3_restricted_state_preserved():
    src = LINTER.read_text()
    assert "test_lint_no_legacy_restricted_state_wording" in src


# ===========================================================================
# 23–28 · Carve-outs preserved.
# ===========================================================================
def test_23_no_new_collections():
    src = (BACKEND / "server.py").read_text()
    assert "db.track_18_08_" not in src


def test_24_dispatch_token_alias_preserved():
    src = (BACKEND / "server.py").read_text()
    assert "X-Dispatch-Token" in src


def test_25_admin_route_prefix_preserved():
    src = (BACKEND / "routes" / "transportation_relationships.py").read_text()
    assert 'prefix="/api/admin/transportation"' in src


def test_26_dispatch_login_route_preserved():
    src = (BACKEND / "routes" / "dispatch_portal_auth.py").read_text()
    assert "/dispatch/login" in src


def test_27_rbac_admin_strict_guard_intact():
    src = (BACKEND / "routes" / "transportation_experience.py").read_text()
    assert "require_admin_dep" in src


def test_28_track_18_07_lock_files_intact():
    """Track 18.07 enforcement files must still exist."""
    for f in (BACKEND / "tests" / "test_track_18_07_design_system_linter.py",
              BACKEND / "tests" / "test_track_18_07_design_system_enforcement.py"):
        assert f.exists()


# ===========================================================================
# 29–30 · Deployment gate + certification.
# ===========================================================================
def test_29_track_wired_into_deployment_gate():
    src = GATE.read_text()
    assert "test_track_18_08_regression_stability_device_polish.py" in src


def test_30_certification_declares_go():
    src = CERT.read_text()
    assert "GO" in src
    assert "trusted" in src.lower() or "trust" in src.lower()
