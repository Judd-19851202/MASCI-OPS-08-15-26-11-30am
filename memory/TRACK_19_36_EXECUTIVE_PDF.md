# TRACK 19.36 · EXECUTIVE PDF

**Date:** 2026-07-03 · **Anchor:** `TRACK_19_36_EXECUTIVE_INTELLIGENCE.md`

## Endpoint
`GET /api/incident-cases/{case_id}/executive-report.pdf` (additive · Safety-gated).

The existing Track 19.16 Phase E PDF endpoint `/api/incident-cases/{case_id}/reports/{report_type}.pdf` is **untouched**. Consumers may continue to use it; Track 19.36 adds a new **boardroom-grade** endpoint that reads from the unified Executive Intelligence Model.

## Renderer
`backend/incident_engine/executive_report_render.py` → `render_executive_report_html(model) -> str`. Converted to PDF via the existing `html_to_pdf_bytes(html)` helper (WeasyPrint).

## Section order
1. Hero — headline · severity chip · case number · state.
2. Why It Matters (executive briefing).
3. Executive Summary (facts).
4. Timeline (traceable).
5. Evidence Chain (append-only custody).
6. Corrective Actions (CAPA).
7. Regulatory · Insurance · Legal · Executive Review.
8. Operational Intelligence (time-to-* + days open).
9. Readiness Score (explainable, 6 sub-scores).
10. Decision Records.
11. Lessons Learned · Forward Prevention.

Every section is derived from the corresponding branch of the Executive Intelligence Model — no bespoke queries, no side reads.

## Print constraints
- Letter size (`@page { size: Letter; margin: 0.75in; }`).
- Executive-grade typography (Helvetica Neue stack, 10.5pt body, 20pt hero title).
- Slate + emerald palette. No decorative gradients.
- Table borders 0.5pt.
- Page-break-avoid on rows.
- Print-ready without browser overrides.

## Missing-value protocol
When a value is empty or missing, the renderer emits `<span class="muted">Not documented yet.</span>` — never fabricates or infers. The `missing_fields` array of the model gives consumers a machine-readable ledger of the same gaps.

## Filename
`executive-report-<case_number>.pdf` (falls back to `case_id` if the case number is missing).

## Headers
- `Content-Type: application/pdf`
- `Content-Disposition: inline; filename="executive-report-<n>.pdf"`
- `X-Content-Type-Options: nosniff`

## Zero drift
- No mutation of any collection.
- No email or notification triggered.
- No permission change; Safety/Admin/PM read gate applies (same gate as every other `/api/incident-cases/*` endpoint).
- Existing Phase E PDF preserved bit-for-bit.

## Rollback
Remove the 4-line `_register_ie_executive_report_routes(...)` block in `server.py`. Delete `executive_report_render.py` and `executive_report_routes.py`. Rollback confidence: HIGH.
