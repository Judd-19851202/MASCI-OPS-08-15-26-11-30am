# DR-ROI-001F · Frontend PDF UI (Session A affordance)

## What lands in Session A
Two disabled, feature-flagged buttons in the sticky save bar:
- **Preview PDF** — will open the generated PDF in an inline viewer.
- **Download PDF** — will trigger `GET /api/dr-v2/reports/{id}/pdf?disposition=attachment`.

Both are:
- Rendered with the platform `secondaryBtn` grammar so they match every
  other secondary action across the platform.
- `disabled={true}` in Session A.
- Carry a `title` (native tooltip) reading: "PDF preview arrives in the
  next session · submit and download stay on schedule."
- Testids: `dr-v2-preview-pdf-btn`, `dr-v2-download-pdf-btn`.

## What lands in Session B (the PDF session)
- Backend `GET /api/dr-v2/reports/{report_id}/pdf` renderer.
- Enable the buttons once the response is a real PDF.
- Inline preview modal for the Preview button (using an iframe or
  browser-native PDF viewer).
- Clear disabled reasons when a report is not yet approved / missing
  required fields.

## Non-goals
- No standalone PDF-only page — the buttons live inside the form's save
  bar so field users never leave the workflow.
- No PDF-branded aesthetic on the form. The PDF is a document; the form
  is an app. They match visual language but are distinct surfaces.
- No AI branding on the PDF or its trigger.
