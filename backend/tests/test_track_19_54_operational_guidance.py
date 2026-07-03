"""Track 19.54 · Operational Guidance System (OGS) — lock test.

Run in isolation:
    pytest /app/backend/tests/test_track_19_54_operational_guidance.py -v
"""
from pathlib import Path

REPO = Path("/app")
MEM = REPO / "memory"
FE_COMP_OI = REPO / "frontend/src/components/operational_intelligence"
BE_OI = REPO / "backend/operational_intelligence"

REQUIRED_DOCS = [
    "TRACK_19_54_EXECUTIVE_SUMMARY.md",
    "TRACK_19_54_GUIDANCE_CARD_SPEC.md",
    "TRACK_19_54_UNIVERSAL_LANGUAGE.md",
    "TRACK_19_54_OPERATIONAL_THREAD_SPEC.md",
    "TRACK_19_54_HUMAN_WALKTHROUGH.md",
    "TRACK_19_54_ZERO_DRIFT_MATRIX.md",
    "TRACK_19_54_TEST_REPORT.md",
]

GUIDANCE = FE_COMP_OI / "GuidanceCard.jsx"
ATTN = FE_COMP_OI / "AttentionChip.jsx"
TREND = FE_COMP_OI / "TrendChip.jsx"
THREAD = FE_COMP_OI / "OperationalThread.jsx"
GMAP = FE_COMP_OI / "guidanceMap.js"
STRIP = FE_COMP_OI / "OiAttentionStrip.jsx"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


# ─── Docs present ───────────────────────────────────────────────
def test_track_19_54_docs_present():
    missing = [d for d in REQUIRED_DOCS if not (MEM / d).exists()]
    assert not missing, f"missing Track 19.54 docs: {missing}"


# ─── Primitives exist ───────────────────────────────────────────
def test_guidance_card_component_exists():
    assert GUIDANCE.exists(), "GuidanceCard.jsx must be the universal primitive"


def test_attention_chip_component_exists():
    assert ATTN.exists(), "AttentionChip.jsx must exist"


def test_trend_chip_component_exists():
    assert TREND.exists(), "TrendChip.jsx must exist"


def test_operational_thread_component_exists():
    assert THREAD.exists(), "OperationalThread.jsx must exist"


def test_guidance_map_exists():
    assert GMAP.exists(), "guidanceMap.js must exist"


# ─── Guidance Card enforces the 10 mandated sections ────────────
def test_guidance_card_has_all_ten_sections():
    src = _read(GUIDANCE)
    for testid in [
        "guidance-card-title",
        "guidance-card-summary",
        "guidance-card-why",
        "guidance-card-drivers",
        "guidance-card-actions",
        "guidance-card-roles",
        "guidance-card-deep-links",
        "guidance-card-guidance",
        "guidance-card-decision-boundary",
    ]:
        assert testid in src, f"GuidanceCard missing section testid {testid!r}"
    # Evidence is conditional but must be authored:
    assert "guidance-card-evidence" in src, \
        "GuidanceCard must render Supporting Evidence when available"


def test_guidance_card_enforces_max_five_actions():
    src = _read(GUIDANCE)
    assert ".slice(0, 5)" in src, \
        "GuidanceCard must cap recommended actions at 5"


def test_guidance_card_includes_decision_boundary_copy():
    src = _read(GUIDANCE)
    assert "platform never makes operational decisions" in src.lower(), \
        "GuidanceCard must display the Track 19.54 decision-boundary statement"


# ─── Universal language chips ───────────────────────────────────
def test_attention_chip_uses_four_universal_levels():
    src = _read(ATTN)
    for level, hint in [
        ("CRITICAL", "Immediate action required"),
        ("HIGH",     "Address today"),
        ("MEDIUM",   "Plan"),
        ("LOW",      "Healthy"),
    ]:
        assert level in src, f"AttentionChip missing level {level}"
        assert hint in src, \
            f"AttentionChip missing universal hint for {level}: {hint!r}"


def test_trend_chip_uses_universal_language():
    src = _read(TREND)
    for word in ("Improving", "Stable", "Declining", "▲", "→", "▼"):
        assert word in src, f"TrendChip missing universal token {word!r}"


# ─── Zero-drift guarantees ─────────────────────────────────────
def test_guidance_card_no_writes():
    """Guidance Card is a read-only aggregator. No POST/PUT/PATCH/DELETE."""
    src = _read(GUIDANCE)
    for banned in ('method: "POST"', 'method: "PUT"', 'method: "PATCH"',
                   'method: "DELETE"', "/api/email/", "sendEmail("):
        assert banned not in src, f"GuidanceCard must not include {banned!r}"


def test_guidance_card_consumes_only_existing_endpoints():
    src = _read(GUIDANCE)
    assert "/api/operational-intelligence/history" in src, \
        "GuidanceCard must consume the certified history endpoint"
    # It must NOT talk to any per-domain endpoint.
    for banned in ("/api/safety/", "/api/hr/", "/api/shop/", "/api/fleet/",
                   "/api/dispatch/", "/api/pm/", "/api/projects/"):
        assert banned not in src, \
            f"GuidanceCard must not query domain endpoint {banned!r}"


def test_operational_thread_is_read_only():
    """OperationalThread renders a caller-provided event array; it must
    not fetch."""
    src = _read(THREAD)
    assert "fetch(" not in src, \
        "OperationalThread must not fetch — read-only rendering primitive only"


def test_no_new_backend_module_added_by_1954():
    """Backend engine inventory frozen (Track 19.50 baseline)."""
    expected = {"__init__.py", "engine.py", "registry.py", "products.py",
                "score_model.py", "product_layout.py", "recipients.py",
                "routes.py", "scheduler.py"}
    actual = {f.name for f in BE_OI.glob("*.py")}
    assert actual == expected, \
        f"engine file inventory drifted: {actual ^ expected}"


def test_oi_component_directory_inventory():
    """The OI component folder now contains exactly the Track 19.54 set
    plus the shared strip. If new consumers appear the doctrine has
    drifted."""
    expected_jsx = {"OiAttentionStrip.jsx", "GuidanceCard.jsx",
                    "AttentionChip.jsx", "TrendChip.jsx",
                    "OperationalThread.jsx"}
    expected_js = {"guidanceMap.js"}
    actual_jsx = {f.name for f in FE_COMP_OI.glob("*.jsx")}
    actual_js  = {f.name for f in FE_COMP_OI.glob("*.js")}
    assert actual_jsx == expected_jsx, \
        f"OI JSX inventory drifted: {actual_jsx ^ expected_jsx}"
    assert actual_js == expected_js, \
        f"OI JS inventory drifted: {actual_js ^ expected_js}"


# ─── Attention Strip wired to Guidance Card ────────────────────
def test_strip_opens_guidance_card_on_tile_click():
    src = _read(STRIP)
    assert "import GuidanceCard" in src, \
        "OiAttentionStrip must import GuidanceCard"
    assert "onOpen" in src, "Strip tiles must expose onOpen handler"
    assert 'type="button"' in src, \
        "Tile must be a button (no navigation)"


# ─── Prior track regressions unbroken ──────────────────────────
def test_prior_p1_p2_mounts_preserved():
    """Track 19.52 + 19.53 mounts still intact."""
    fe_pages = REPO / "frontend/src/pages"
    for page, testid in [
        (fe_pages / "SafetyHubV2.jsx",                 "safety-hub-v2-oi-strip"),
        (fe_pages / "HrHubV2.jsx",                      "hr-hub-v2-oi-strip"),
        (fe_pages / "PmCommandCenter.jsx",              "pm-cc-oi-strip"),
        (fe_pages / "ShopHubV2.jsx",                    "shop-hub-v2-oi-strip"),
        (fe_pages / "FleetVisibility.jsx",              "fleet-visibility-oi-strip"),
        (fe_pages / "AdminHubV2.jsx",                   "admin-hub-v2-oi-strip"),
        (fe_pages / "DispatchCommandCenter.jsx",        "dcc-oi-strip"),
        (fe_pages / "admin/AdminAssetAdmin.jsx",        "asset-admin-oi-strip"),
    ]:
        src = _read(page)
        assert f'testId="{testid}"' in src, \
            f"prior mount on {page.name} was regressed"


def test_track_19_51_docs_preserved():
    for name in ("TRACK_19_51_EXECUTIVE_SUMMARY.md",
                 "TRACK_19_51_COMMAND_CENTER_STANDARD.md",
                 "TRACK_19_51_REMEDIATION_ROADMAP.md"):
        assert (MEM / name).exists(), f"Track 19.51 doc missing: {name}"


def test_prd_updated():
    assert "TRACK 19.54" in _read(MEM / "PRD.md")


def test_changelog_updated():
    assert "TRACK 19.54" in _read(MEM / "CHANGELOG.md")
