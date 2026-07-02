# TRACK 19.23 · .xlsm Daily Report Attachment Verification

## Extension + MIME classification (`_doc_ext_from_data_url`)

| Scenario | MIME | Filename | Expected | Actual |
|---|---|---|---|---|
| Canonical macro MIME | `application/vnd.ms-excel.sheet.macroenabled.12` | `budget.xlsm` | `xlsm` | ✅ `xlsm` |
| Ambiguous MIME + xlsm name | `application/vnd.ms-excel` | `budget.xlsm` | `xlsm` | ✅ `xlsm` |
| Modern xlsx | `application/vnd.openxmlformats-...spreadsheetml.sheet` | `budget.xlsx` | `xlsx` | ✅ `xlsx` |
| Executable rejected | `application/x-msdownload` | `virus.exe` | `None` | ✅ `None` |

## Allowed doc extensions
`{"pdf", "xls", "xlsx", "xlsm", "csv"}` (server-side `_ALLOWED_DOC_EXTS`). Photos handled separately via image path.

## Human-facing label
`.xlsm` files are labeled **"Spreadsheet"** (bilingual translation via `t()`). Never "Macro workbook" or "Contains macros" (would be scary for HR/foreman/PM users). File preservation includes original extension so re-download preserves `.xlsm`.

## Server-side safety
- Server stores the file bytes to Cloudflare R2 with SHA-256 hash — **never opens, parses, or executes macros**.
- No `openpyxl.load_workbook` / no VBA engine / no automation. Only content-hash + byte-preservation.
- File retrieval via signed URLs (short TTL); no server-side rendering of macro content.

## Surfaces where `.xlsm` must appear identical to `.xlsx`
- Daily Report attachment picker: ✅ accepts (`.xlsx,.xlsm,.csv` allow-list)
- Submitted payload: ✅ hash + ref persisted
- Admin portal attachment list: ✅ same DocumentChip surface
- PM portal attachment list: ✅ same surface
- Historical report detail: ✅ signed-URL download preserves original extension
- Email attachment/link section: ✅ same DocumentChip surface (link, not inline)
- PDF export section: ✅ referenced as "Spreadsheet"

## Lock tests
`tests/test_track_19_19_xlsm_attachment.py` · **18/18 GREEN**.

**Verdict:** GO. `.xlsm` behavior matches `.xlsx` end-to-end. `.exe` rejected. No macro execution.
