"""Track 19.52 · P1 Command Center Remediation Execution — lock test.

Run in isolation:
    pytest /app/backend/tests/test_track_19_52_command_center_p1.py -v
"""
from pathlib import Path

REPO = Path("/app")
MEM = REPO / "memory"
FE_PAGES = REPO / "frontend/src/pages"
FE_COMP = REPO / "frontend/src/components/operational_intelligence"
BE_OI = REPO / "backend/operational_intelligence"

REQUIRED_DOCS = [
    "TRACK_19_52_EXECUTIVE_SUMMARY.md",
    "TRACK_19_52_P1_REMEDIATION_EXECUTION.md",
    "TRACK_19_52_PORTAL_FIX_MATRIX.md",
    "TRACK_19_52_HUMAN_WALKTHROUGH_REPORT.md",
    "TRACK_19_52_MOBILE_IPAD_REVIEW.md",
    "TRACK_19_52_ZERO_DRIFT_MATRIX.md",
    "TRACK_19_52_TEST_REPORT.md",
]

STRIP_FILE = FE_COMP / "OiAttentionStrip.jsx"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_track_19_52_docs_present():
    missing = [d for d in REQUIRED_DOCS if not (MEM / d).exists()]
    assert not missing, f"missing Track 19.52 docs: {missing}"


def test_oi_attention_strip_component_exists():
    assert STRIP_FILE.exists(), f"missing shared consumer at {STRIP_FILE}"


def test_oi_attention_strip_reuses_summary_endpoint():
    src = _read(STRIP_FILE)
    assert "/api/operational-intelligence/summary" in src, \
        "OiAttentionStrip must consume the certified OI summary endpoint"
    # No client-side scoring / attention-level derivation.
    assert "computeScore" not in src and "deriveAttention" not in src, \
        "OiAttentionStrip must not re-derive scores or attention levels"


def test_oi_attention_strip_no_new_backend():
    src = _read(STRIP_FILE)
    # Zero-drift: pure GET consumer.
    for banned in ('method: "POST"', 'method: "PUT"', 'method: "PATCH"',
                   'method: "DELETE"', "/api/email/", "sendEmail("):
        assert banned not in src, f"OiAttentionStrip must not include {banned!r}"


def _assert_mount(page_path: Path, product_ids, testid_root):
    src = _read(page_path)
    assert "OiAttentionStrip" in src, \
        f"{page_path.name} must import OiAttentionStrip"
    assert "@/components/operational_intelligence/OiAttentionStrip" in src, \
        f"{page_path.name} must import from the canonical path"
    assert f'testId="{testid_root}"' in src, \
        f"{page_path.name} must use testId {testid_root!r}"
    for pid in product_ids:
        assert f'"{pid}"' in src, \
            f"{page_path.name} must reference product_id {pid!r}"


def test_safety_hub_mounts_oi_strip():
    _assert_mount(FE_PAGES / "SafetyHubV2.jsx",
                  ["safety_morning_digest"], "safety-hub-v2-oi-strip")


def test_hr_hub_mounts_oi_strip():
    _assert_mount(FE_PAGES / "HrHubV2.jsx",
                  ["hr_intelligence", "training_intelligence"],
                  "hr-hub-v2-oi-strip")


def test_pm_command_center_mounts_oi_strip():
    _assert_mount(FE_PAGES / "PmCommandCenter.jsx",
                  ["project_intelligence"], "pm-cc-oi-strip")


def test_shop_hub_mounts_oi_strip():
    _assert_mount(FE_PAGES / "ShopHubV2.jsx",
                  ["shop_intelligence"], "shop-hub-v2-oi-strip")


def test_fleet_visibility_mounts_oi_strip():
    _assert_mount(FE_PAGES / "FleetVisibility.jsx",
                  ["fleet_intelligence"], "fleet-visibility-oi-strip")


def test_pm_landing_redirects_to_command_center():
    redirect = FE_PAGES / "PmHomeRedirect.jsx"
    assert redirect.exists(), "PmHomeRedirect.jsx must exist"
    src = _read(redirect)
    assert '/pm/command-center' in src, \
        "PmHomeRedirect must redirect /pm to /pm/command-center"


def test_no_new_command_center_framework_added_by_1952():
    """Backend engine module inventory frozen · Track 19.50 baseline
    preserved. scheduler.py is pre-existing (baseline)."""
    expected = {"__init__.py", "engine.py", "registry.py", "products.py",
                "score_model.py", "product_layout.py", "recipients.py",
                "routes.py", "scheduler.py"}
    actual = {f.name for f in BE_OI.glob("*.py")}
    assert actual == expected, \
        f"engine file inventory drifted: {actual ^ expected}"


def test_track_19_51_lock_still_green():
    """Track 19.51 audit doc set still present."""
    for name in [
        "TRACK_19_51_EXECUTIVE_SUMMARY.md",
        "TRACK_19_51_PORTAL_HOME_INVENTORY.md",
        "TRACK_19_51_NOISE_AUDIT.md",
        "TRACK_19_51_COMMAND_CENTER_STANDARD.md",
        "TRACK_19_51_REMEDIATION_ROADMAP.md",
    ]:
        assert (MEM / name).exists(), f"Track 19.51 doc missing: {name}"


def test_prd_updated():
    assert "TRACK 19.52" in _read(MEM / "PRD.md"), \
        "PRD.md must include a TRACK 19.52 entry"


def test_changelog_updated():
    assert "TRACK 19.52" in _read(MEM / "CHANGELOG.md"), \
        "CHANGELOG.md must include a TRACK 19.52 entry"
