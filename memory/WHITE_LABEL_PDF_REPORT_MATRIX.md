# WHITE-LABEL · PDF / REPORT MATRIX

**Phase 8 deliverable.** Every PDF generator + brand wiring.

## PDF generators inventoried

| File | Generates | Key brand touchpoints | White-label readiness |
|------|-----------|------------------------|------------------------|
| `pdf_render.py` | Daily reports · Safety meetings · Incidents · CAs · JHAs · ODRs · Field-leadership records · cross-record exports | `LOGO_PATH = masci-mark-onlight.png` (line 31) · `WATERMARK_PATH = masci-mark.png` (line 32) · "MASCI Hauling" section (line 1101) · "MASCI Crews on Site" (line 755) · `non_masci` flag handling (1190 · 1201) · "MASCI Hub" footer | 🔴 hardcoded |
| `training_pdf.py` | Training cards · matrices · audit exports | "MASCI HUB" brand strings in tips/text (lines 724-725) · MASCI logo | 🔴 hardcoded |
| `safety_digest.py` | Weekly safety digest | uses `pdf_render.py` infrastructure | 🔴 inherits |
| `po_digest.py` | Weekly PO digest | uses `pdf_render.py` infrastructure | 🔴 inherits |
| Backup/audit exports | Compliance bundle ZIPs | filename `masci-*-{timestamp}.zip` in some places | 🔴 partial |
| QR generator (`safety_qr.py`, others) | Inspection / equipment QR cards | brand label baked in | 🔴 hardcoded |

## Brand surfaces inside PDFs

| Surface | Where | Risk for Customer #2 |
|---------|-------|----------------------|
| Header logo | Top-left of every PDF page | Customer #2's PDFs would show MASCI mark |
| Watermark | Background of every page | Customer #2's PDFs would show MASCI watermark |
| Section labels — "MASCI Crews on Site", "MASCI Hauling" | Daily report PDF | Customer #2's daily report would say "MASCI" |
| Cover page company name | Most PDFs | Customer #2 cover would say MASCI |
| Filename prefix | Download filenames | Customer #2 downloads named `masci_*.pdf` |
| Footer disclaimer | Bottom of every page | Customer #2 footer would say "MASCI Hub" |
| Signature block | Various forms | "MASCI representative" wording |
| QR label text | QR-based field cards | "MASCI Safety" branding |
| Color accents | Cover bars, section dividers | MASCI red |
| `non_masci` field semantic | Field-leadership employee classification | Field name itself contains "MASCI" |

## Existing isolation

- 🟢 PDFs are streamed inline to the requesting client (HTTP body); none are persisted to shared storage for downstream readers.
- 🟢 PDF generation happens on the requesting pod — per-customer deploy means per-customer PDFs trivially.
- 🔴 The CONTENT of every PDF is MASCI-branded.

## Fix path (per-customer deploy model)

For Customer #2:
1. Ship customer-specific asset files in `frontend/public/` (logos, watermark).
2. Wire `pdf_render.py` to read from `BrandConfig` (logo path, watermark path, company name, footer html).
3. Rename `masci_crews` field semantically → `company_crews`; render label from `BrandConfig.company_name + " Crews on Site"`.
4. Rename `non_masci` semantic field → `non_company` with migration script for existing records.
5. Filename prefix from `BrandConfig.filename_slug` (e.g. `bobs-`).
6. Section labels parameterized via `BrandConfig.t()` keys.

**Effort**: ~3-5 days for `pdf_render.py` parameterization · ~1 day each for `training_pdf` and `safety_digest`. Total: ~1 week.

## Customer #2 implication

Every PDF Customer #2's platform generates today would be MASCI-branded. This is the **second-highest-leak surface** after email. Customer #2 onboarding without PDF white-label = unusable for external sharing.
