"""Platform Family Contract Lock · iter320 deliverable.

Single read-only invariant suite that mechanically prevents visual-
governance drift across every hub refined under the Platform UX
Governance roadmap (iter317-C / iter318 / iter319 / iter320 / future).

Scope is intentionally narrow per operator mandate:
> "Verify canonical platform-family anchors:
>   - border-l-4
>   - approved H1 scale
>   - approved section-heading pattern
>   - mono kicker typography
>   - approved calm-card patterns
>  DO NOT create screenshot testing, pixel-diff systems, snapshot suites,
>  style bureaucracy, animation enforcement, or layout micromanagement."

These tests are anti-drift protection only. They do NOT enforce style
beyond the four anchors. They do NOT block legitimate UX evolution.
"""
from pathlib import Path

FRONTEND = Path(__file__).resolve().parent.parent.parent / "frontend/src"
PAGES = FRONTEND / "pages"

# The hubs that have been refined under the Platform UX Governance
# roadmap. Each must satisfy the family contract. Add to this list
# only after a hub completes a calm-pass iteration (iter322, iter323…).
FAMILY_HUBS = [
    ("HrHub.jsx",              "iter317-C"),
    ("SafetyHub.jsx",          "iter318"),
    ("FieldLeadershipHub.jsx", "iter319"),
    ("FieldSection.jsx",       "iter319"),
    ("ShopHub.jsx",            "iter320"),
    ("QaqcSection.jsx",        "iter320"),
]


def _src(name: str) -> str:
    p = PAGES / name
    assert p.exists(), f"Family hub {name} must exist"
    return p.read_text()


# ─── Anchor 1 · calm card pattern (left-edge stripe) ─────────────────────

def test_family_anchor_calm_card_left_stripe_present():
    """Every family hub must render the calm tile chrome (`border-l-4`
    left-edge stripe). This anchor catches reverts to the legacy hot
    `border-2 border-<accent>-500` SectionTile pattern."""
    failures = []
    for hub, iter_tag in FAMILY_HUBS:
        if "border-l-4" not in _src(hub):
            failures.append(f"{hub} ({iter_tag})")
    assert not failures, (
        f"Family contract violation — missing `border-l-4` calm card anchor in: {failures}"
    )


def test_family_anchor_no_hot_section_tile_import():
    """Refined family hubs must not import the shared SectionTile
    component (its chrome is hot — `border-2 border-slate-300` + colored
    top-bar — and a reintroduction is a drift signal). Hub.jsx (public
    home) and other unrefined surfaces are still allowed to use it."""
    failures = []
    for hub, iter_tag in FAMILY_HUBS:
        src = _src(hub)
        if 'from "@/components/SectionTile"' in src or "<SectionTile" in src:
            failures.append(f"{hub} ({iter_tag})")
    assert not failures, (
        f"Family contract violation — hot SectionTile reintroduced in: {failures}"
    )


# ─── Anchor 2 · approved H1 scale (interior hub) ─────────────────────────

def test_family_anchor_interior_h1_scale_present():
    """Every family hub renders the interior-hub H1 size
    (`text-3xl sm:text-4xl`). This anchor catches reverts to the
    public-hero `text-4xl sm:text-5xl lg:text-6xl` or oversized
    `text-4xl sm:text-5xl` H1s that bleed marketing tone into
    operational interior surfaces."""
    failures = []
    for hub, iter_tag in FAMILY_HUBS:
        if "text-3xl sm:text-4xl" not in _src(hub):
            failures.append(f"{hub} ({iter_tag})")
    assert not failures, (
        f"Family contract violation — interior-hub H1 size missing in: {failures}"
    )


def test_family_anchor_no_public_hero_h1():
    """Legacy public-hero H1 size (`text-4xl sm:text-5xl lg:text-6xl`)
    must not appear inside any refined interior hub."""
    failures = []
    legacy = "font-display text-4xl sm:text-5xl lg:text-6xl"
    for hub, iter_tag in FAMILY_HUBS:
        if legacy in _src(hub):
            failures.append(f"{hub} ({iter_tag})")
    assert not failures, (
        f"Family contract violation — public-hero H1 leaked into: {failures}"
    )


# ─── Anchor 3 · approved section-heading pattern ─────────────────────────

def test_family_anchor_mono_kicker_section_heading():
    """Every family hub uses the canonical section-heading style:
    `font-mono text-xs uppercase tracking-[0.22em]`. This anchor catches
    reverts to ad-hoc heading styles (text-lg/font-display/3xl, etc.)
    inside grouped hubs."""
    failures = []
    for hub, iter_tag in FAMILY_HUBS:
        src = _src(hub)
        # The canonical pattern: mono + uppercase + tight tracking 0.22em.
        # All four refined-hub families pass this. We require the exact
        # `tracking-[0.22em]` tracker class — any deviation (0.18em,
        # 0.25em, 0.3em) signals drift in the section-heading pattern.
        if 'tracking-[0.22em]' not in src:
            failures.append(f"{hub} ({iter_tag})")
    assert not failures, (
        f"Family contract violation — canonical mono kicker tracking-[0.22em] missing in: {failures}"
    )


# ─── Anchor 4 · KPI / stat-block chrome (where applicable) ──────────────

def test_family_anchor_kpi_chrome_neutral_when_present():
    """Hubs with KPI strips must use Rule-5 neutral chrome
    (`border border-slate-200 rounded-md p-4`), NOT the legacy
    `border-2 border-<accent>-<700>` hot chrome.

    Only enforced for hubs that have a KPI strip — others are NA."""
    failures = []
    legacy_kpi_chrome_signals = (
        "border-2 border-cyan-700",
        "border-2 border-red-700",
        "border-2 border-amber-600",
        "border-2 border-emerald-700",
        "border-2 border-slate-200 rounded-md px-4 py-3",  # legacy Shop KPI
    )
    for hub, iter_tag in FAMILY_HUBS:
        src = _src(hub)
        for legacy in legacy_kpi_chrome_signals:
            if legacy in src:
                failures.append(f"{hub} ({iter_tag}) → '{legacy}'")
    assert not failures, (
        f"Family contract violation — legacy hot KPI chrome detected in: {failures}"
    )


# ─── Meta · the contract itself ─────────────────────────────────────────

def test_family_contract_membership_documented():
    """Each hub in FAMILY_HUBS must have a corresponding closure mention
    in the contract docs — keeps the membership list audit-traceable."""
    audit_doc = (FRONTEND.parent.parent / "memory/UX_PLATFORM_FAMILY_REFERENCE.md")
    assert audit_doc.exists(), "Family reference doc must exist"
    body = audit_doc.read_text()
    # Lightweight check — the reference doc lists each member by hub file.
    for hub, _ in FAMILY_HUBS:
        stem = hub.replace(".jsx", "")
        assert stem in body, (
            f"Family contract violation — {hub} not documented in "
            f"UX_PLATFORM_FAMILY_REFERENCE.md (membership must be auditable)"
        )
