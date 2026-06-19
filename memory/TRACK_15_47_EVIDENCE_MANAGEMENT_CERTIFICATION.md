# TRACK 15.47 · Evidence Management Certification (G7)

**Status:** ✅ CERTIFIED · live-rendered on synthetic incident INC-2026-00488.

## Problem
Pre-15.47, ALL evidence collapsed into one path: `photos: List[str]` (base64 data URLs). A police report PDF, a medical record, a witness statement, a dashcam video — all uploaded as "photos." Six months later in court, MASCI could not show "the police report" without manually picking through a slideshow.

## What G7 delivers
Additive `attachments: List[{kind, label, data_url, uploaded_at}]` field on every incident. Backend (`backend/routes/safety.py`) accepts and stores. Frontend constant `ATTACHMENT_KINDS` (in `lib/incidentSchema.js`) enumerates the seven kinds:

| Kind | UI label | Use case |
|---|---|---|
| `photo` | Photo | Site photos, license plates, injuries |
| `video` | Video | Dashcam, body cam, witness video |
| `witness_statement` | Witness Statement | Signed PDFs from witnesses |
| `police_report` | Police Report | The PDF or photo from the responding agency |
| `medical` | Medical Documentation | Discharge notes, clinic invoices |
| `insurance` | Insurance Documentation | Claim forms, adjuster correspondence |
| `other` | Other Document | Anything not in the six above |

Legacy `photos[]` continues to work for backward compatibility (existing 69 incidents render unchanged). New incidents may use either path; PDF renderer reads both.

## PDF rendering · verified
`pdf_render._render_generic` now emits a dedicated "Evidence Attachments" section grouping rows by `kind`, with columns: Kind · Label · Uploaded · Attached.

INC-2026-00488 carries 5 attachments — photo, witness_statement, police_report, medical, video. All 5 are visible on the rendered PDF in the dedicated "EVIDENCE ATTACHMENTS" section (verified via PDF content analysis).

## Field-preservation diff
Before:
- 1 path (`photos[]`)
- No type, no label, no upload-time
After:
- 2 paths (`photos[]` + `attachments[]`) — both render
- 7 valid kinds
- Per-attachment label
- Per-attachment upload timestamp
- Universal-PDF-Foundation compliant (no V2 PDF system)

## Sign-off
G7 is delivered, additive, and Universal-PDF-Foundation compliant. Field preservation `AFTER ⊇ BEFORE` confirmed against INC-2026-00002 (legacy) and INC-2026-00488 (synthetic, all kinds).
