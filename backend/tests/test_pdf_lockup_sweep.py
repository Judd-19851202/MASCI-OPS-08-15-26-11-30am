"""
tests/test_pdf_lockup_sweep.py — Track 14.0-P1 PDF Lockup Sweep
regression guard.

Locks the MASCI/ForgedOps PDF output contract so future PRs cannot
silently regress the platform's PDF branding, filename standard, or
operator-friendly behaviour. These are static-analysis assertions —
no live API traffic, so they run anywhere.

Closure ledger: /app/memory/TRACK_14_0_P1_PDF_LOCKUP_SWEEP_CLOSURE.md
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path("/app")
PDF_BRANDING = REPO / "backend/pdf_branding.py"
SERVER = REPO / "backend/server.py"


# ── Shared branding module contract ────────────────────────────────


def test_pdf_branding_module_exists_and_exposes_contract():
    """pdf_branding.py is the canonical MASCI PDF chrome. Every backend
    generator that produces operational PDFs imports BRAND_CSS,
    brand_header, or wrap_pdf_html from this module. Removing or
    renaming the contract breaks every PDF that relies on it."""
    text = PDF_BRANDING.read_text()
    for name in ("BRAND_CSS", "brand_header", "wrap_pdf_html"):
        assert name in text, (
            f"pdf_branding.py no longer exports {name!r} — the shared "
            "MASCI PDF chrome contract is broken. Restore the symbol or "
            "open Track 14.0-P1 PDF Lockup Sweep again.")
    # Brand bar must contain the MASCI mark and red rule.
    assert 'class="brand-mark">MASCI' in text, (
        "pdf_branding.brand_header no longer emits the MASCI brand mark. "
        "PDFs will render without the platform logo wordmark.")
    assert "#b91c1c" in text, (
        "pdf_branding lost the MASCI red brand color — branding parity "
        "with the UI top chrome (border-red-700) breaks.")
    # Footer chrome — must include generated timestamp + page numbers.
    assert "counter(page)" in text and "counter(pages)" in text, (
        "pdf_branding.BRAND_CSS no longer emits page-of-pages counters "
        "in the footer — printed records lose pagination context.")
    assert "Generated" in text, (
        "pdf_branding lost the 'Generated <timestamp>' footer line.")


@pytest.mark.parametrize("generator_file", [
    "backend/routes/master_history.py",
    "backend/routes/training_center.py",
    "backend/routes/safety_portal/fire_ext_attachments.py",
])
def test_certified_generators_use_shared_pdf_branding(generator_file):
    """These three generators are the canonical wrap_pdf_html consumers
    audited in the PDF Lockup Sweep. They must continue importing the
    shared branding helper so visual parity is preserved with the
    rest of the PDF surface."""
    path = REPO / generator_file
    text = path.read_text()
    assert "from pdf_branding import" in text or "import pdf_branding" in text, (
        f"{generator_file} no longer imports pdf_branding — it will "
        "render PDFs without the shared MASCI chrome. Restore the "
        "import or update the closure ledger.")
    assert "wrap_pdf_html" in text, (
        f"{generator_file} no longer calls wrap_pdf_html(...). "
        "Reverting to ad-hoc HTML breaks branding consistency.")


# ── Filename standard ──────────────────────────────────────────────


def test_backend_pdf_filenames_use_masci_prefix():
    """Every Content-Disposition filename emitted for a downloadable
    PDF must start with `MASCI_` (or the audited per-record prefixes
    like `fe_<unit>_history.pdf` and `trench_safety_<id>_<stamp>.pdf`
    documented in the closure ledger). Random/UUID-only filenames are
    not professional for shareable operational records."""
    backend_routes = (REPO / "backend/routes").rglob("*.py")
    backend_files = [SERVER] + list(backend_routes)
    audited_non_masci_prefixes = {
        # Documented exceptions in the closure ledger (operator-keyed).
        "asset-history-",          # master_history (admin-only)
        "employee-history-",       # master_history (admin-only)
        "fe_",                     # fire extinguisher history
        "trench_safety_",          # trench safety reports
        "HR_Compliance_Brief_",    # HR brief
    }
    pattern = re.compile(r'filename\s*=\s*["\']?\s*f?["\']([^"\']*?\.pdf)')
    for fp in backend_files:
        if any(skip in str(fp) for skip in ("guidance/", "/tests/", "/test_")):
            continue
        text = fp.read_text(errors="ignore")
        for m in pattern.finditer(text):
            fname = m.group(1).strip()
            # Skip dynamic / parameter-only references (no literal prefix).
            if not fname or fname.startswith("{") or fname.startswith("$"):
                continue
            ok = (
                fname.startswith("MASCI_")
                or any(fname.startswith(p) for p in audited_non_masci_prefixes)
            )
            assert ok, (
                f"{fp.name} emits non-standard PDF filename: {fname!r}. "
                "Operational record PDFs must start with MASCI_ (or one "
                "of the audited per-record prefixes listed in "
                "/app/memory/TRACK_14_0_P1_PDF_LOCKUP_SWEEP_CLOSURE.md)."
            )


# ── Frontend print contract ────────────────────────────────────────


@pytest.mark.parametrize("view_file", [
    "frontend/src/pages/ViewInspection.jsx",
    "frontend/src/pages/ViewIncident.jsx",
    "frontend/src/pages/ViewDailyReport.jsx",
    "frontend/src/pages/ViewMeeting.jsx",
])
def test_operational_view_pages_use_printreport_helper(view_file):
    """Operational record View pages MUST go through the shared
    printReport / maybeAutoPrint helper so the iframe-aware print
    path works inside the Emergent preview AND saves cleanly as PDF
    from the browser print dialog. Direct window.print() in these
    pages breaks the preview iframe path."""
    text = (REPO / view_file).read_text()
    assert "printReport" in text, (
        f"{view_file} no longer wires through the printReport helper. "
        "Direct window.print() can fail inside the Emergent preview "
        "iframe — operators get a blank PDF when they Save as PDF.")
    assert "no-print" in text, (
        f"{view_file} no longer applies `no-print` to app chrome — "
        "browser-printed PDFs will include the top bar + sidebar.")
    # Sectioned print blocks must exist so page-breaks behave.
    assert ("print-section" in text or "print-page" in text or
            "print:break-inside-avoid" in text), (
        f"{view_file} lost its print page-break hints — printed PDFs "
        "may break mid-section.")


def test_print_report_helper_handles_iframe_preview():
    """lib/printReport.js must keep its dual-path implementation
    (top-window AND parent-message-based path for the Emergent
    preview iframe). Without both branches the print dialog fails
    silently when developers iframe the app for debugging."""
    text = (REPO / "frontend/src/lib/printReport.js").read_text()
    assert "window.print" in text, "printReport must call window.print() in the top-window path."
    assert "postMessage" in text or "parent" in text or "top" in text, (
        "printReport must handle the iframe path (top/parent/postMessage). "
        "Without it, Emergent preview iframe loses the print dialog.")
