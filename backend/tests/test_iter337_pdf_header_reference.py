"""
iter337 · PDF Header Reference Continuity

Verifies the canonical record identifier (iter335/336 chain) is now
surfaced in the header of every generated PDF — closing the operational
continuity loop digitally and physically.

Scope discipline:
  • Same canonical chain as iter335/336 (no parallel numbering)
  • Graceful absence when no canonical ID present
  • NO new QR / NO tracking / NO redesign of templates
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def test_pdf_render_computes_canonical_ref_chain():
    """Main render path (pdf_render.py) builds the unified canonical_ref."""
    src = (BACKEND / "pdf_render.py").read_text(encoding="utf-8")
    assert "canonical_ref" in src, "pdf_render.py must compute canonical_ref"
    # All iter335/336 chain members must be considered.
    chain_members = (
        'record.get("incident_number")',
        'record.get("report_number")',
        'record.get("inspection_number")',
        'record.get("meeting_number")',
        'record.get("issuance_number")',
        'record.get("training_number")',
        'record.get("jha_number")',
    )
    for m in chain_members:
        assert m in src, f"pdf_render.py canonical_ref missing chain member: {m}"


def test_pdf_render_header_uses_ref_continuity_label():
    """Header must render `Ref · <ID>` (using HTML middot entity)."""
    src = (BACKEND / "pdf_render.py").read_text(encoding="utf-8")
    assert "Ref &middot; " in src, (
        "pdf_render.py must use 'Ref · <ID>' continuity label in header"
    )
    # Old plain doc_id-only rendering must be replaced
    assert "escape(canonical_ref)" in src


def test_pdf_render_graceful_absence_in_header():
    """The header `Ref · ` line must only render if canonical_ref is truthy."""
    src = (BACKEND / "pdf_render.py").read_text(encoding="utf-8")
    # Conditional ternary check for canonical_ref
    assert "if canonical_ref else ''" in src, (
        "pdf_render.py must conditionally render the Ref line (graceful absence)"
    )


def test_safety_forms_issuance_pdf_uses_canonical_ref():
    src = (BACKEND / "routes" / "safety_forms.py").read_text(encoding="utf-8")
    # Issuance template — canonical chain ordered by per-formType preference
    assert 'rec.get("issuance_number")' in src
    assert "Ref &middot; " in src
    # Legacy "Form Ref:" wording must be gone from this file
    assert "Form Ref:" not in src, (
        "safety_forms.py templates must replace legacy 'Form Ref:' with the iter337 Ref · pattern"
    )


def test_safety_forms_training_pdf_uses_canonical_ref():
    src = (BACKEND / "routes" / "safety_forms.py").read_text(encoding="utf-8")
    assert 'rec.get("training_number")' in src


def test_field_leadership_pdf_uses_canonical_ref():
    src = (BACKEND / "field_leadership_pdf.py").read_text(encoding="utf-8")
    # Header line must surface the Ref · prefix
    assert "Ref &middot; " in src, (
        "field_leadership_pdf.py header must render the iter337 Ref · pattern"
    )
    # Chain must consider record_number first, then fall back through doc_id and id
    assert "rec.get('record_number')" in src
    assert "rec.get('doc_id')" in src


def test_field_leadership_pdf_graceful_absence():
    """The FL PDF header `Ref · ` block must only render when an ID exists."""
    src = (BACKEND / "field_leadership_pdf.py").read_text(encoding="utf-8")
    # The conditional must wrap the entire Ref line
    assert "if (rec.get('record_number') or rec.get('doc_id') or rec.get('id'))" in src


# ─────────────────────────────────────────────────────────────────────
# Scope discipline · no fake fallback IDs, no parallel numbering
# ─────────────────────────────────────────────────────────────────────
def test_no_fake_pending_ref_in_pdf_templates():
    """Forbid placeholder labels like 'REF-PENDING' or 'NO-REF-YET'."""
    for f in (BACKEND / "pdf_render.py", BACKEND / "field_leadership_pdf.py", BACKEND / "routes" / "safety_forms.py"):
        src = f.read_text(encoding="utf-8")
        for forbidden in ("REF-PENDING", "NO-REF-YET", "PENDING-ID", "PLACEHOLDER-REF"):
            assert forbidden not in src, (
                f"{f.name} introduced fake placeholder ID: {forbidden}"
            )


def test_pdf_render_doc_id_legacy_preserved():
    """`doc_id` variable retained for backward compat with email subject + audit logs."""
    src = (BACKEND / "pdf_render.py").read_text(encoding="utf-8")
    # The legacy variable assignment must still exist (used by callers via record dict)
    assert 'doc_id = (record.get("doc_id") or "").strip()' in src
