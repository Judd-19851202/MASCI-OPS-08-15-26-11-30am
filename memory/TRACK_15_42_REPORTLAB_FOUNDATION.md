# TRACK 15.42 · ReportLab Foundation — Architecture

**Date:** 2026-06-19
**Module:** `backend/pdf_branding_rl.py`
**Status:** 🟢 LIVE — used by 5 ReportLab generators

---

## 1 · Why a separate file

`pdf_branding.py` is a pure-HTML / CSS helper module — it returns
HTML strings consumable by WeasyPrint. ReportLab's Canvas+Platypus
API needs Python objects (Flowables, canvas operations), not HTML.
A separate `pdf_branding_rl.py` keeps the two engines' code paths
clean while sharing the same env-driven `WhiteLabelConfig` and the
same `PDF_FOUNDATION_VERSION` constant.

---

## 2 · Public API

| Symbol | Purpose |
|---|---|
| `draw_audit_block_flowable(record_id, source_module, project=None, document_version=None, generated_by=None, generated_at=None) -> Flowable` | KeepTogether table containing the universal audit block. Caller appends to `story` before `doc.build(story)`. |
| `draw_metadata_block_flowable(document_type, document_id=None, project_number=None, extra=None) -> Flowable` | Single-paragraph monospace metadata strip Flowable. |
| `draw_universal_footer(canvas, doc) -> None` | `onPage` callback emitting `<tagline> · Page X` along the bottom. Pair with `SimpleDocTemplate(onFirstPage=..., onLaterPages=...)`. |
| `PageNumCanvas(_rl_canvas.Canvas)` | Two-pass canvas that injects `Page X of Y` on every page. Pass to `doc.build(..., canvasmaker=PageNumCanvas)` for total-page-aware footers. |
| `build_brand_header_flowable(title, kicker="") -> Flowable` | Brand bar Flowable mirroring the HTML foundation's `brand_header()`. |
| `_xml_safe(s) -> str` | Escape for ReportLab's Paragraph XML subset. |

---

## 3 · Cross-engine parity

| Feature | WeasyPrint (`pdf_branding.py`) | ReportLab (`pdf_branding_rl.py`) |
|---|---|---|
| White-label config | `get_white_label()` | `get_white_label()` (imported) |
| Foundation version | `PDF_FOUNDATION_VERSION` | `PDF_FOUNDATION_VERSION` (imported) |
| Environment tag | `_env_tag()` | `_env_tag()` (imported) |
| Audit block | `build_audit_block_html()` | `draw_audit_block_flowable()` |
| Metadata block | `build_metadata_block_html()` | `draw_metadata_block_flowable()` |
| Footer | `@page @bottom-left/@bottom-right` | `draw_universal_footer` callback + `PageNumCanvas` |
| Brand header | `brand_header()` | `build_brand_header_flowable()` |
| Customer color | `wl.brand_color` (CSS hex) | `colors.HexColor(f"#{wl.brand_color}")` (RL) |

Same record_id / source_module / project / generated_by / generated_at
semantics across both engines, so any PDF — regardless of engine — is
parseable by the same audit-discovery tool.

---

## 4 · Adoption pattern

### 4.1 · Existing ReportLab generator (additive, no rewrite)

```python
# Before doc.build(story):
try:
    from pdf_branding_rl import draw_audit_block_flowable
    story.append(draw_audit_block_flowable(
        record_id="...",
        source_module="...",
        project="...",
        generated_by="...",
    ))
except Exception:
    pass  # never fail render on foundation chrome

doc.build(story)
```

### 4.2 · Footers (optional upgrade)

Existing ReportLab generators that already have an `onPage` callback
keep it. New generators (or refactors) can wire
`PageNumCanvas` and `draw_universal_footer` to get `Page X of Y` in
the brand color/tagline automatically.

---

## 5 · Adopters live today

| Generator | File | Method |
|---|---|---|
| ODR PDF | `routes/odr/pdf.py::_render_pdf` | `story.append(draw_audit_block_flowable(...))` before `doc.build(story)` |
| Trench Safety Export | `routes/trench_safety/report_export.py::render_pdf` | same pattern |
| Fleet Severity Reference | `routes/fleet_ops.py::severity_reference_card_pdf` | same pattern |
| HR Employee Compliance Brief | `routes/hr_portal.py::hr_employee_compliance_brief_pdf` | same pattern |

All four were extended in this track with **3 lines of code each**
(the try/import/append block). Operational story content untouched.

---

## 6 · Hard rules respected

* No body content rewritten.
* No flowables removed.
* No on-page callbacks replaced.
* No PageTemplates modified.
* No font registration changes.
* No image embedding changes.
* No signature flow changes.

🟢 **ReportLab foundation live · feature-parity with WeasyPrint achieved · 4 adopters live.**
