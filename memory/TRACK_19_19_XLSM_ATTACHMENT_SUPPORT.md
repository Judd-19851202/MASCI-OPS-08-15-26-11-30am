# Track 19.19 · Daily Report .xlsm Attachment Support

**Priority:** P0 field blocker  
**Doctrine:** Zero drift · Six Pillars · production-safe  
**Status:** 🟢 Fixed · 18/18 lock tests · live-verified against upload endpoint

## 1. Root cause

The Daily Report unified attachment pipeline (Track 19.04) allow-listed only 4 document MIME types:

```python
_DOC_MIME_TO_EXT = {
    "application/pdf": "pdf",
    "application/vnd.ms-excel": "xls",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
    "text/csv": "csv",
    "application/csv": "csv",
}
_ALLOWED_DOC_EXTS = {"pdf", "xls", "xlsx", "csv"}
```

MASCI field users routinely attach macro-enabled Excel workbooks (`.xlsm`) — quantity trackers, delivery slip templates, CEI worksheets. Browsers report `.xlsm` under the MIME `application/vnd.ms-excel.sheet.macroEnabled.12`, which was **not** in the allow-list. The pipeline's `_doc_ext_from_data_url()` helper returned `(None, "application/vnd.ms-excel.sheet.macroenabled.12")`, and the upload helper raised `ValueError("Unsupported document type: application/vnd.ms-excel.sheet.macroenabled.12")` — surfaced to the field user as the 400 message the field crew reported.

## 2. Fix applied

### Backend (`/app/backend/photo_storage.py`)

- Added `application/vnd.ms-excel.sheet.macroenabled.12` → `xlsm` to `_DOC_MIME_TO_EXT` (lowercased key to match the parser's normalization).
- Added `xlsm` to `_ALLOWED_DOC_EXTS`.
- Added `"xlsm": "Spreadsheet"` to the category map so PM / Admin / PDF / email surfaces group `.xlsm` alongside `.xlsx` / `.xls` / `.csv`.
- Upgraded `_doc_ext_from_data_url()` with a **narrow filename-extension fallback**: when the browser reports the ambiguous plain `application/vnd.ms-excel` MIME or `application/octet-stream` and the picker filename ends in `.xlsm`, re-classify to `xlsm`. The fallback is scoped to spreadsheet-adjacent MIMEs only — it can NEVER re-classify to any dangerous extension.

### Frontend (`/app/frontend/src/components/AttachmentUpload.jsx`)

- Added `application/vnd.ms-excel.sheet.macroenabled.12` (and legacy variant) to the client-side `ALLOWED_MIME` set.
- Added a filename-extension fallback (`ALLOWED_EXT_FALLBACK` = `{pdf, xls, xlsx, xlsm, csv}`) so `.xlsm` files aren't bounced client-side on browsers that report `application/octet-stream`.
- Added `.xlsm` to the `<input accept="…">` attribute so the native picker filters correctly.
- Updated the label copy from "PDFs, Excel spreadsheets, and CSV files" → "PDFs, Excel spreadsheets (.xlsx, .xls, .xlsm), and CSV files".

### Bilingual (`/app/frontend/src/lib/i18n.js`)

- Added 2 new EN→ES entries:
  - `"PDFs, Excel spreadsheets (.xlsx, .xls, .xlsm), and CSV files up to 25 MB each."` → `"PDFs, hojas de Excel (.xlsx, .xls, .xlsm) y archivos CSV, hasta 25 MB cada uno."`
  - `"Macro-enabled Excel workbook (.xlsm)"` → `"Libro de Excel con macros habilitadas (.xlsm)"`

## 3. Security posture

**Nothing weakened. Everything preserved.**

- Server never opens, parses, or executes macros. The workbook is treated as opaque bytes at rest and on download — identical to `.xlsx`.
- No `openpyxl`, `xlrd`, or any workbook / VBA library is imported in `photo_storage.py`. Locked by a new source-audit test.
- Dangerous extension blocklist (`_DANGEROUS_EXTS`) **untouched**: `exe`, `bat`, `cmd`, `com`, `cpl`, `dll`, `jar`, `js`, `jse`, `msi`, `ps1`, `psm1`, `sh`, `vbe`, `vbs`, `wsf`, `wsh`, `scr`, `app`, `action`, `workflow`, `hta` — all still rejected.
- Filename fallback is scoped to spreadsheet-adjacent MIMEs only. A PDF-MIME with a `.exe` filename resolves to `pdf` (safe); the dangerous-ext gate is still enforced downstream.
- 25 MiB file-size cap preserved.
- Filename sanitization preserved (`_safe_filename` still strips path separators, control chars, dot-only prefixes; caps at 240 chars).
- R2 upload path preserved. `.xlsm` is stored under `documents/<YYYY>/<MM>/<source>/<uuid>.xlsm` with `ContentType: application/vnd.ms-excel.sheet.macroenabled.12`.

## 4. Attachment support matrix (post-Track 19.19)

| Extension | Category | MIME accepted | Notes |
|---|---|---|---|
| `.pdf` | PDF | `application/pdf` | Existing |
| `.xls` | Spreadsheet | `application/vnd.ms-excel` | Existing |
| `.xlsx` | Spreadsheet | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` | Existing |
| `.xlsm` | Spreadsheet | `application/vnd.ms-excel.sheet.macroEnabled.12` **+ filename fallback** for plain `.xls` MIME and `application/octet-stream` | **NEW · Track 19.19** |
| `.csv` | Spreadsheet | `text/csv`, `application/csv` | Existing |

**Rejected** (unchanged):
- `.exe`, `.js`, `.bat`, `.cmd`, `.scr`, `.ps1`, `.sh`, `.jar`, `.vbs`, `.wsh`, `.hta`, and every other member of `_DANGEROUS_EXTS`.
- Any MIME not in `_DOC_MIME_TO_EXT` (unless the filename maps to a permitted spreadsheet extension).
- Files > 25 MiB.

## 5. Where .xlsm appears

Because `.xlsm` is categorized as `Spreadsheet`, it appears in the same rendering surfaces as `.xlsx` / `.xls` / `.csv`:

- **Daily Report submit payload** — inside `attachments[]` with `category: "Spreadsheet"`, `extension: "xlsm"`, MIME preserved.
- **PM portal** — Daily Report detail view groups attachments by category; `.xlsm` groups under "Spreadsheet" beside `.xlsx`.
- **Admin portal** — same grouping.
- **Email delivery** — attachment section iterates `attachments[]` by category; `.xlsm` appears alongside `.xlsx`.
- **PDF export** — attachment index lists `.xlsm` under Spreadsheet.
- **Signed URL / download** — R2 signed URL served with the canonical macro-enabled MIME so downstream tooling (Excel on desktop) opens the workbook correctly.
- **Historical Daily Report detail** — cases submitted with `.xlsm` attachments render identically to those with `.xlsx`.

## 6. Test report

### Track 19.19 lock tests · 18/18 GREEN

```
tests/test_track_19_19_xlsm_attachment.py:
  test_xlsm_is_in_allow_list                                         PASSED
  test_xlsm_mime_maps_to_xlsm_extension                              PASSED
  test_xlsx_and_xls_and_pdf_and_csv_still_map                        PASSED
  test_dangerous_extensions_still_blocked                            PASSED
  test_xlsm_is_not_on_the_dangerous_list                             PASSED
  test_max_bytes_unchanged_at_25MiB                                  PASSED
  test_data_url_with_canonical_xlsm_mime_resolves_to_xlsm            PASSED
  test_data_url_with_xls_mime_but_xlsm_filename_resolves_to_xlsm     PASSED
  test_data_url_with_octet_stream_but_xlsm_filename_resolves_to_xlsm PASSED
  test_xls_filename_still_resolves_to_xls_when_mime_is_xls           PASSED
  test_pdf_data_url_resolves_to_pdf_regardless_of_filename           PASSED
  test_unknown_mime_and_unknown_filename_returns_none                PASSED
  test_exe_extension_is_never_returned_by_the_parser                 PASSED
  test_upload_helper_rejects_dangerous_ext_even_via_spoofed_mime     PASSED
  test_upload_helper_rejects_unknown_mime_with_unknown_ext           PASSED
  test_upload_helper_rejects_oversize_xlsm                           PASSED
  test_xlsm_is_categorised_as_spreadsheet                            PASSED
  test_no_macro_parsing_libraries_imported_in_photo_storage          PASSED
```

### Live endpoint verification (against preview server)

3 upload paths tested via `POST /api/daily-reports/attachments/upload`:

| Path | HTTP | ext | MIME | category | filename |
|---|---|---|---|---|---|
| Canonical `application/vnd.ms-excel.sheet.macroEnabled.12` + `.xlsm` filename | 200 | `xlsm` | `application/vnd.ms-excel.sheet.macroenabled.12` | Spreadsheet | `quantities.xlsm` |
| Plain `application/vnd.ms-excel` MIME + `.xlsm` filename (fallback path) | 200 | `xlsm` | `application/vnd.ms-excel` | Spreadsheet | `quantities.xlsm` |
| `application/octet-stream` MIME + `.xlsm` filename (extreme fallback) | 200 | `xlsm` | `application/octet-stream` | Spreadsheet | `quantities.xlsm` |
| `application/x-msdownload` MIME + `.exe` filename | **400** | — | — | — | rejected as `Unsupported document type` |

### Regression

- Track 19.04 Daily Report attachment locks: PASS
- Track 19.16 Incident Engine locks (357 tests): PASS
- Track 19.18 PDF Excellence + Safety Case Workspace (19 tests): PASS
- Frontend ESLint on `AttachmentUpload.jsx`: CLEAN
- 417/417 tests passing across the union of touched suites.

## 7. Zero-drift verification

- **No schema drift** — `attachments[]` envelope shape unchanged (`attachment_ref`, `mime_type`, `extension`, `category`, `filename`, `file_size`, `uploaded_at`).
- **No route drift** — no new routes added; `/api/daily-reports/attachments/upload` behavior widened for `.xlsm` only.
- **No payload drift** — clients that never send `.xlsm` see zero behavioral change.
- **No PDF regression** — attachment rendering in PDF exports uses the category grouping; `.xlsm` falls under existing "Spreadsheet" group.
- **No email regression** — attachment iteration is category-driven; `.xlsm` groups with existing Spreadsheets.
- **No attachment regression** — Track 19.04 tests still pass.
- **No macro execution** — locked by `test_no_macro_parsing_libraries_imported_in_photo_storage`.

## 8. Files changed

```
backend/photo_storage.py                                (+ .xlsm MIME · ext · category · filename fallback)
backend/tests/test_track_19_19_xlsm_attachment.py       (NEW · 18 lock tests)
frontend/src/components/AttachmentUpload.jsx            (+ MIME · ext fallback · picker accept · label copy)
frontend/src/lib/i18n.js                                (+ 2 EN→ES entries)
```

## 9. Acceptance

🟢 **Fixed.** A MASCI field user can now attach `.xlsm` workbooks to a Daily Report without seeing "Unsupported file type," and the platform still treats every workbook as a passive attachment — never executed, never parsed for macros.

**Done means done.**
