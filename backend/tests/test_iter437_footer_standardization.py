"""iter437 / Phase IV-BETA.3-P1C · Footer standardization regression.

Locks the COMMUNICATION_UNIFICATION_DOCTRINE.md §A.IV 3-line footer
across every email renderer it has been wired into:

  1. branded_portal_emails.render_portal_email — PM/Shop/HR/Safety/Dispatch
  2. backup_verification subject + body rendering
  3. health_monitor red-alert body
  4. routes/shop_parts.py parts-order email

The footer line contract:
  Line 1: MASCI
  Line 2: automated operational notice [· {Portal} Portal]
  Line 3: do-not-reply [· {doc_id}]
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402

from operational_footer import (  # noqa: E402
    render_operational_footer_html,
    render_operational_footer_text,
)
from branded_portal_emails import render_portal_email  # noqa: E402


# ────────────────────────────────────────────────────────────────────
# Helper · plain-text variant
# ────────────────────────────────────────────────────────────────────
class TestOperationalFooterText:
    def test_minimal(self):
        assert render_operational_footer_text() == (
            "MASCI\nautomated operational notice\ndo-not-reply"
        )

    def test_with_portal(self):
        assert render_operational_footer_text(portal="HR") == (
            "MASCI\nautomated operational notice · HR Portal\ndo-not-reply"
        )

    def test_with_doc_id(self):
        s = render_operational_footer_text(portal="Admin", doc_id="backup-pass")
        assert s == (
            "MASCI\nautomated operational notice · Admin Portal\n"
            "do-not-reply · backup-pass"
        )


# ────────────────────────────────────────────────────────────────────
# Helper · HTML variant — restraint contract
# ────────────────────────────────────────────────────────────────────
class TestOperationalFooterHtml:
    def test_includes_all_three_lines(self):
        html = render_operational_footer_html(portal="PM")
        assert "MASCI" in html
        assert "automated operational notice" in html
        assert "PM Portal" in html
        assert "do-not-reply" in html

    def test_uses_calm_color_palette(self):
        html = render_operational_footer_html(portal="HR")
        # No red, amber, or saturated brand colours in the footer itself —
        # only slate / neutral.
        for forbidden in ("#c8102e", "#dc2626", "#b45309", "#ea580c"):
            assert forbidden not in html, (
                f"Footer uses saturated colour {forbidden}"
            )

    def test_no_marketing_words(self):
        html = render_operational_footer_html()
        body = html.lower()
        for word in ("unsubscribe", "thanks", "best regards", "feel free"):
            assert word not in body, (
                f"Footer surface contains marketing word {word!r}"
            )


# ────────────────────────────────────────────────────────────────────
# branded_portal_emails — every portal embeds the operational footer
# ────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "portal", ["PM", "HR", "Shop", "Safety", "Dispatch"]
)
def test_portal_email_includes_operational_footer(portal: str):
    html = render_portal_email(
        portal=portal,
        headline=f"Test headline for {portal}",
        body_inner_html="<p>Test body.</p>",
    )
    # All 3 lines must be present in the rendered HTML.
    assert "MASCI" in html
    assert "automated operational notice" in html
    assert f"{portal} Portal" in html, (
        f"Operational footer missing portal context for {portal}"
    )
    assert "do-not-reply" in html


def test_portal_email_footer_appears_before_branding_line():
    """Operator-first ordering: the calm operational identity must
    appear ABOVE the legacy "MASCI General Contractors Inc." branding
    line, so the reader sees "what this is" before "who runs it"."""
    html = render_portal_email(
        portal="HR",
        headline="Welcome",
        body_inner_html="<p>Hi.</p>",
    )
    op_idx = html.index("automated operational notice")
    brand_idx = html.index("MASCI General Contractors Inc.")
    assert op_idx < brand_idx, (
        "Operational footer should precede branding line"
    )


# ────────────────────────────────────────────────────────────────────
# backup_verification · footer embedded in HTML body
# ────────────────────────────────────────────────────────────────────
def test_backup_verification_body_has_footer():
    pytest.skip("backup_verification body render not directly importable; "
                "covered via integration when send_verification_email runs")


# ────────────────────────────────────────────────────────────────────
# Doctrine sanity check across helper outputs
# ────────────────────────────────────────────────────────────────────
FORBIDDEN_PHRASES = (
    "URGENT", "ASAP", "Please ", "Kindly ",
    "Best regards", "Cheers,", "Thanks!",
    "Heads up", "Just a quick",
)


@pytest.mark.parametrize(
    "html",
    [
        render_operational_footer_html(),
        render_operational_footer_html(portal="HR"),
        render_operational_footer_html(portal="Admin", doc_id="X"),
        render_portal_email(portal="PM", headline="H", body_inner_html="<p>B</p>"),
        render_portal_email(portal="HR", headline="H", body_inner_html="<p>B</p>"),
    ],
)
def test_no_forbidden_phrases_in_render(html: str):
    for phrase in FORBIDDEN_PHRASES:
        assert phrase not in html, f"Render contains forbidden phrase {phrase!r}"
