"""iter219 — Portal <title> persona-tagging + foreman discoverability refinement.

Two small operational-polish items surfaced by iter217 walkthroughs:

  1. Portal <title> tags were all the generic "MASCI Operations
     Platform" — orientation friction for browser-tab swaps, QR-poster
     previews, screen readers, and supers walking up to someone's
     desk. Persona-tag every portal hub.
  2. The foreman walkthrough's discoverability check expected direct
     /equipment/submit / /daily/submit links on the public hub, but
     the legitimate IA uses /field as the aggregator. Refine the
     check to recognize the aggregator pattern.

This test verifies the static side (the title-tag wiring) so the
self-validating loop doesn't have to drive Playwright every CI run.
"""
from pathlib import Path

import pytest


FRONTEND = Path("/app/frontend/src")


def test_use_page_title_hook_exists():
    """The usePageTitle hook must exist and expose the canonical API."""
    p = FRONTEND / "lib" / "usePageTitle.js"
    assert p.exists(), f"missing {p}"
    src = p.read_text()
    assert "export function usePageTitle" in src or "export default function usePageTitle" in src
    assert "document.title" in src
    # Must restore the previous title on unmount (orientation hygiene).
    assert "return ()" in src or "return function" in src


# Persona ↔ expected <title> tag. Each portal must persona-tag.
EXPECTED_TITLES = {
    "FieldLeadershipHub.jsx": "Field Leadership · MASCI",
    "HrHub.jsx":              "HR · MASCI",
    "SafetyHub.jsx":          "Safety · MASCI",
    "PmHub.jsx":              "PM · MASCI",
    "ShopHub.jsx":            "Shop · MASCI",
    "DispatchHub.jsx":        "Dispatch · MASCI",
    "AdminHub.jsx":           "Admin Console · MASCI",
}


@pytest.mark.parametrize("hub_file,expected_title", sorted(EXPECTED_TITLES.items()))
def test_portal_hub_persona_tags_its_title(hub_file, expected_title):
    p = FRONTEND / "pages" / hub_file
    assert p.exists(), f"missing portal hub: {p}"
    src = p.read_text()
    # Must import + call usePageTitle with the canonical string.
    assert "usePageTitle" in src, f"{hub_file}: missing usePageTitle import/call"
    assert f'usePageTitle("{expected_title}")' in src, (
        f"{hub_file}: expected `usePageTitle(\"{expected_title}\")` call"
    )


def test_no_persona_tagging_on_public_hub():
    """The public Hub.jsx is intentionally not persona-tagged — it IS
    the platform. The static index.html <title>MASCI Operations
    Platform</title> should remain authoritative there."""
    p = FRONTEND / "pages" / "Hub.jsx"
    src = p.read_text()
    assert "usePageTitle" not in src, (
        "public Hub.jsx must NOT persona-tag itself — it is the canonical "
        "platform landing page."
    )


def test_index_html_keeps_generic_platform_title():
    """The base <title> in index.html must stay generic. Persona-tagged
    portal pages override at runtime; the base is the safe fallback."""
    p = Path("/app/frontend/public/index.html")
    src = p.read_text()
    assert "<title>MASCI Operations Platform</title>" in src


def test_foreman_walkthrough_recognizes_field_aggregator():
    """The iter217 foreman walkthrough's discoverability check was a
    false positive because it looked for direct /equipment/submit
    deeplinks. iter219 refines the check to recognize /field as the
    legitimate aggregator IA pattern."""
    p = Path("/app/walkthroughs/foreman.py")
    src = p.read_text()
    # Check refinement landed.
    assert "/field" in src, "foreman walkthrough must check the /field aggregator"
    assert "aggregator" in src.lower(), (
        "foreman walkthrough must document the aggregator-IA recognition"
    )
    # And the original false-positive selectors must NOT be the primary
    # check anymore.
    assert "/equipment/submit" not in src.split("tiles = page.evaluate")[1].split("}\"\"\")")[0], (
        "foreman walkthrough's first-screen-reach check must use /field, "
        "not the deeplink /equipment/submit"
    )


def test_superintendent_walkthrough_accepts_persona_tagged_title():
    """Once iter219 lands the portal title-tags, the super walkthrough's
    title check should accept 'Field Leadership · MASCI' as positive,
    not flag it as unclear-wording."""
    p = Path("/app/walkthroughs/superintendent.py")
    src = p.read_text()
    assert '"field leadership"' in src.lower() or "'field leadership'" in src.lower(), (
        "superintendent walkthrough must check for 'field leadership' in "
        "the persona-tagged <title>"
    )
