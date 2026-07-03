# TRACK 19.40 · PDF ENGINE

**One PDF renderer. WeasyPrint via `incident_engine.report_render.html_to_pdf_bytes`.**

The Operational Intelligence engine's `render_html(digest)` output is the exact input WeasyPrint accepts. A PDF endpoint at `/api/operational-intelligence/{product_id}/report.pdf` is a Phase 2 addition; the underlying helper already exists (used by Track 19.36 boardroom PDF and Track 19.16 Phase E PDF).

No second PDF engine may be introduced. Lock test greps for `weasyprint\|reportlab` imports outside the two certified sites.
