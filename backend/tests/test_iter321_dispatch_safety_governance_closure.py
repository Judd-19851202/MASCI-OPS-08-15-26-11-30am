"""iter321 · Dispatch Hub Convergence + Safety Tile Governance Closure + Deploy Hook.

Locks the iter321 platform-convergence pass:
- DispatchHub: blueprint-bg + caution-stripe · header bg-slate-900 (was 950)
  · max-w-7xl → max-w-6xl · iter132 kicker leak removed · title card
  converted from hot `border-2 border-slate-300` to calm left-edge stripe
  · H1 `text-2xl` → `text-3xl sm:text-4xl` · iter203 mobile collapse
  applied to PortalSwitcher / GlobalSearch / Transfers / Fleet / Guides.
- SafetySection: full calm rewrite · SectionTile removed · H1 toned ·
  CTAs uppercased · matched section heading style.
- SafetyFormsHub: inline FormTile converted to calm pattern · H1 toned.
- Deploy hook: `/app/.deploy_checks/run_family_contract.sh` present and
  executable.
"""
from pathlib import Path
import os
import stat

ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND = ROOT / "frontend/src"
DISPATCH = FRONTEND / "pages/DispatchHub.jsx"
SAFETY_SEC = FRONTEND / "pages/SafetySection.jsx"
SAFETY_FORMS = FRONTEND / "pages/SafetyFormsHub.jsx"
DEPLOY_HOOK = ROOT / ".deploy_checks/run_family_contract.sh"


# ─── Dispatch Hub invariants ─────────────────────────────────────────────

def test_iter321_dispatch_blueprint_bg():
    src = DISPATCH.read_text()
    assert "blueprint-bg" in src
    assert "caution-stripe" in src
    # Legacy slate-50 bg gone.
    assert "bg-slate-50 flex flex-col" not in src


def test_iter321_dispatch_header_slate_900():
    """Header dropped from slate-950 outlier to canonical slate-900."""
    src = DISPATCH.read_text()
    assert "bg-slate-900 text-white" in src
    assert "bg-slate-950" not in src


def test_iter321_dispatch_max_w_6xl():
    """Container width converged to family canonical."""
    src = DISPATCH.read_text()
    assert "max-w-6xl" in src
    assert "max-w-7xl" not in src


def test_iter321_dispatch_iter132_kicker_dropped():
    """Stale iter132 kicker leak removed."""
    src = DISPATCH.read_text()
    assert "iter132" not in src


def test_iter321_dispatch_title_card_calm():
    """Title block converted from hot `border-2 border-slate-300` to
    calm left-edge orange stripe (family contract Rule 1)."""
    src = DISPATCH.read_text()
    assert "border border-slate-200 border-l-4 border-l-orange-500" in src
    # The legacy hot block must not return.
    assert "bg-white border-2 border-slate-300 rounded-md p-5" not in src


def test_iter321_dispatch_h1_toned():
    """H1 raised from `text-2xl` to interior-hub `text-3xl sm:text-4xl`."""
    src = DISPATCH.read_text()
    assert "text-3xl sm:text-4xl" in src
    # Legacy undersized H1 must not return.
    assert "font-display text-2xl font-black tracking-tight mt-0.5" not in src


def test_iter321_dispatch_iter203_mobile_collapse():
    """iter203 collapse applied — PortalSwitcher + GlobalSearch hidden
    on <sm; Transfers + Fleet + Guides hidden on <sm. Bell + Offline +
    SignOut stay visible."""
    src = DISPATCH.read_text()
    # The collapse wrappers / classes are present.
    assert 'hidden sm:flex items-center gap-2' in src
    # The Transfers / Fleet / Guides Links pick up `hidden sm:inline-flex`.
    assert 'data-testid="dispatch-asset-transfers-link"' in src
    assets_pos = src.find('data-testid="dispatch-asset-transfers-link"')
    assets_block = src[max(0, assets_pos - 400):assets_pos + 50]
    assert "hidden sm:inline-flex" in assets_block


def test_iter321_dispatch_all_testids_preserved():
    """All Dispatch testids preserved (regression contract)."""
    src = DISPATCH.read_text()
    for tid in (
        "dispatch-hub",
        "dispatch-nav-home",
        "dispatch-nav-back",
        "dispatch-asset-transfers-link",
        "dispatch-fleet-link",
        "dispatch-training-link",
        "dispatch-logout",
        "dh-tab-overview",
        "dh-tab-utilization",
        "dh-tab-idle",
        "dh-tab-transfers",
        "dh-tab-holds",
        "dh-tab-integrations",
    ):
        assert f'"{tid}"' in src, f"Dispatch must preserve testid {tid}"


# ─── Safety tile governance closure ──────────────────────────────────────

def test_iter321_safety_section_calm():
    """SafetySection (`/safety` public landing) on family contract."""
    src = SAFETY_SEC.read_text()
    assert "border-l-4" in src
    assert "text-3xl sm:text-4xl" in src
    assert 'tracking-[0.22em]' in src
    assert 'from "@/components/SectionTile"' not in src
    assert "<SectionTile" not in src
    # All 7 safety-tile testids preserved (regression).
    for tid in (
        "safety-tile-inspections",
        "safety-tile-meetings",
        "safety-tile-incidents",
        "safety-tile-jha",
        "safety-tile-trench",
        "safety-tile-cards",
        "safety-tile-forms",
    ):
        assert f'"{tid}"' in src, f"SafetySection must preserve testid {tid}"
    # New section heading testid surfaced.
    assert 'data-testid="safety-section-heading"' in src
    # CTAs uppercased.
    assert 't("START FORM")' in src
    assert 't("OPEN PLANS")' in src
    assert 't("OPEN LIBRARY")' in src
    assert 't("OPEN CARDS")' in src
    assert 't("OPEN FORMS")' in src
    assert 't("Start Form")' not in src


def test_iter321_safety_forms_calm():
    """SafetyFormsHub FormTile converted to calm pattern."""
    src = SAFETY_FORMS.read_text()
    assert "border-l-4" in src
    assert "text-3xl sm:text-4xl" in src
    # 2 form-tile testids preserved.
    assert '"safety-forms-tile-issuance"' in src
    assert '"safety-forms-tile-training"' in src
    # CTAs uppercased.
    assert 't("START FORM")' in src
    assert 't("Start Form")' not in src
    # Legacy hot FormTile chrome gone.
    assert "border-2 border-slate-300 rounded-md p-6 sm:p-8" not in src


# ─── Deploy hook ─────────────────────────────────────────────────────────

def test_iter321_deploy_hook_present_and_executable():
    """Pre-deploy contract hook lives at /app/.deploy_checks/ and is
    executable. Runs only `test_platform_family_contract.py`."""
    assert DEPLOY_HOOK.exists(), "Deploy hook must exist"
    mode = os.stat(DEPLOY_HOOK).st_mode
    assert mode & stat.S_IXUSR, "Deploy hook must be executable"
    body = DEPLOY_HOOK.read_text()
    assert "test_platform_family_contract.py" in body
    # Hook must remain tiny (operator mandate: stabilization-safe,
    # governance-focused). Allow some headroom for comments but cap.
    assert len(body) < 2000, "Deploy hook must remain small"


def test_iter321_deploy_hook_readme_present():
    readme = DEPLOY_HOOK.parent / "README.md"
    assert readme.exists(), "Deploy checks dir must have a README"


# ─── Family contract still passes for all hubs ─────────────────────────

def test_iter321_family_contract_runs_clean():
    """Smoke check that the platform family contract test file is
    runnable from this iteration's perspective — the actual run lives
    in test_platform_family_contract.py and is verified by the
    combined-regression pytest run."""
    contract = ROOT / "backend/tests/test_platform_family_contract.py"
    assert contract.exists()
    assert "FAMILY_HUBS" in contract.read_text()
