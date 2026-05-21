"""
iter310 · Incident/Safety-record PDF single-footer invariant.

Bounded operational-trust fix following operator-reported visual clutter
on multi-page incident PDFs (FDOT / OSHA / insurance / attorney-bound
documents). Root cause: `pdf_render.py` had TWO active footer renderers:

  1. The canonical `@page @bottom-left` CSS rule (correct mechanism · once
     per page in page margin).
  2. A redundant HTML `<div class="ftr">` with `position: fixed; bottom:
     0.25in`. WeasyPrint treats `position: fixed` as fixed-per-page, so
     the same footer text rendered AGAIN inside content area on every
     page, producing visible double-footer artifacts on multi-page PDFs.

Verified on the operator's sample PDF: original had `count=2` on every
page (12 total renders across 6 pages). After fix: `count=1` per page.

This test locks the invariant so the redundant footer can never be
re-added without surfacing the regression in CI.

Scope discipline (operator-bounded · stabilization-phase):
  - NO PDF redesign · NO new layout engine · NO branding change.
  - Footer language untouched: "Generated through MASCI Operations
    Platform — Powered by ForgedOps™ | © 2026 ForgedOps™"
  - Page-numbering untouched: "Page N of M"
  - @page margins untouched: 0.5in 0.5in 0.85in 0.5in
  - Last-page legal disclaimer untouched (still in body flow with
    `page-break-inside:avoid` added to prevent split mid-paragraph).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PDF_RENDER = REPO_ROOT / "backend/pdf_render.py"

sys.path.insert(0, str(REPO_ROOT / "backend"))


def test_iter310_no_fixed_position_footer_div_in_pdf_render():
    """The redundant `.ftr` rule with `position: fixed; bottom: ...` must
    not be present. The canonical per-page footer is the `@page
    @bottom-left` CSS rule."""
    text = PDF_RENDER.read_text()
    # Detect the buggy pattern.
    BAD = re.search(r"\.ftr\s*\{\{[^}]*position:\s*fixed[^}]*bottom:", text)
    assert BAD is None, (
        "iter310 regression: `.ftr` style block with `position: fixed; "
        "bottom` re-introduced in pdf_render.py. WeasyPrint treats this "
        "as fixed-per-page → footer text renders TWICE on every page of "
        "multi-page PDFs (FDOT/OSHA/insurance documents)."
    )


def test_iter310_no_redundant_ftr_div_emitted():
    """The `<div class="ftr">` HTML fragment that previously rendered the
    second footer must not be emitted by the record-PDF template."""
    text = PDF_RENDER.read_text()
    # Strip HTML comments (`<!-- ... -->`) before checking — the
    # explanatory note about why the div was removed legitimately
    # mentions the buggy fragment by name.
    no_comments = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    assert '<div class="ftr">' not in no_comments, (
        "iter310 regression: `<div class=\"ftr\">` HTML fragment "
        "re-introduced in pdf_render.py. This div carries the duplicate "
        "footer text on every page when combined with WeasyPrint's "
        "fixed-per-page positioning semantics."
    )


def test_iter310_canonical_page_footer_preserved():
    """The `@page @bottom-left` footer with the canonical legal string
    MUST remain in place — this is the only legitimate per-page footer."""
    text = PDF_RENDER.read_text()
    # Look for the @page @bottom-left rule with the ForgedOps legal string.
    assert "@bottom-left" in text, "iter310 lost: @page @bottom-left rule"
    assert "Generated through MASCI Operations Platform" in text, (
        "iter310 lost: canonical 'Generated through MASCI Operations Platform' "
        "footer language"
    )
    assert "ForgedOps" in text, "iter310 lost: ForgedOps brand language"


def test_iter310_page_numbering_preserved():
    """`Page N of M` page numbering must remain on the right side."""
    text = PDF_RENDER.read_text()
    assert "counter(page)" in text and "counter(pages)" in text, (
        "iter310 lost: page-numbering counter() rules"
    )


def test_iter310_last_page_legal_disclaimer_preserved():
    """The platform-disclaimer + mascidocs ownership note must remain in
    body flow with `page-break-inside:avoid` so they don't get split."""
    text = PDF_RENDER.read_text()
    assert "last-page-legal" in text, "iter310 lost: last-page-legal disclaimer block"
    assert "documentation and" in text and "regulatory compliance" in text, (
        "iter310 lost: safety-disclaimer language in last-page-legal block"
    )
    assert "mascidocs.com is a customer-branded deployment" in text, (
        "iter310 lost: mascidocs ownership clarification"
    )
    # The disclaimer must carry page-break-inside:avoid so it doesn't
    # split across the bottom of one page and the top of the next.
    last_legal_idx = text.find("last-page-legal")
    block = text[last_legal_idx:last_legal_idx + 800]
    assert "page-break-inside:avoid" in block, (
        "iter310 last-page-legal block missing page-break-inside:avoid"
    )


@pytest.fixture
def rendered_multipage_pdf(tmp_path):
    """Render a multi-page incident PDF using inflated content so we
    exercise the footer-per-page rendering across at least 4 pages."""
    from pdf_render import render_record_pdf
    record = {
        "id": "iter310-regression-record",
        "doc_id": "INC-2026-TEST",
        "project_name": "iter310 PDF Footer Regression",
        "report_date": "2026-05-21",
        "description": "Multi-page filler. " * 200,
        "root_cause_notes": "Root cause narrative. " * 150,
        "immediate_actions": "Immediate actions. " * 100,
        "corrective_actions": "Corrective actions. " * 100,
        "responsible_party": "PM",
    }
    pdf = render_record_pdf("incident", record)
    out = tmp_path / "iter310_regression.pdf"
    out.write_bytes(pdf)
    return out


def test_iter310_runtime_one_footer_per_page(rendered_multipage_pdf):
    """End-to-end render verification: after fix, the canonical footer
    text must appear EXACTLY ONCE per page (not twice as it did with the
    buggy `.ftr` div)."""
    pytest.importorskip("pypdf")
    from pypdf import PdfReader
    reader = PdfReader(str(rendered_multipage_pdf))
    page_count = len(reader.pages)
    assert page_count >= 2, (
        f"iter310 test setup: expected ≥2 pages to exercise multi-page "
        f"footer rendering; got {page_count}"
    )
    marker = "GENERATED THROUGH MASCI"
    for i, page in enumerate(reader.pages, 1):
        text = (page.extract_text() or "").upper()
        count = text.count(marker)
        assert count == 1, (
            f"iter310 RUNTIME REGRESSION on page {i}: footer marker "
            f"'{marker}' appeared {count} times (expected exactly 1). "
            f"This means either the @page footer is missing OR the "
            f"redundant `.ftr` div was re-introduced."
        )


def test_iter310_runtime_page_numbering_renders(rendered_multipage_pdf):
    """The 'Page N of M' counter must render visibly on every page."""
    pytest.importorskip("pypdf")
    from pypdf import PdfReader
    reader = PdfReader(str(rendered_multipage_pdf))
    n = len(reader.pages)
    for i, page in enumerate(reader.pages, 1):
        text = (page.extract_text() or "").upper()
        # Pattern flexible to handle 'PAGE 1 OF 7' or '1 OF 7' variations.
        assert re.search(rf"\b{i}\s+OF\s+{n}\b", text), (
            f"iter310 page {i}: expected 'PAGE {i} OF {n}' style counter "
            f"to render on this page; got text excerpt: {text[-200:]!r}"
        )
