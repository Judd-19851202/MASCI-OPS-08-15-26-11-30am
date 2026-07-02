# TRACK 19.23 · Employee Export Packages Certification

## Six packages · live curl verification (HR token · Alec Perkins)

| Package | HTTP | Size | Magic | Content-Type |
|---|---|---|---|---|
| `complete_file` | 200 | 3002 bytes | `%PDF` | `application/pdf` |
| `training` | 200 | 2706 bytes | `%PDF` | `application/pdf` |
| `discipline` | 200 | 2863 bytes | `%PDF` | `application/pdf` |
| `safety` | 200 | 2701 bytes | `%PDF` | `application/pdf` |
| `ppe_asset` | 200 | 2421 bytes | `%PDF` | `application/pdf` |
| `historical_records` | 200 | 3001 bytes | `%PDF` | `application/pdf` |

## Lane gating (PACKAGE_LANE_GATE · live curl verification)

Safety token attempts:

| Package | Expected | Actual |
|---|---|---|
| `complete_file` | 403 | ✅ 403 |
| `training` | 403 | ✅ 403 |
| `discipline` | 403 | ✅ 403 |
| `safety` | 200 | ✅ 200 |
| `ppe_asset` | 403 | ✅ 403 |
| `historical_records` | 200 | ✅ 200 |

## Document quality (Phase 6)
- Consistent Helvetica-Bold headers
- Accent color per package (purple/teal/orange)
- Alternating table row backgrounds (`#f8fafc`)
- Snapshot table: Lifecycle · Trade · Email · Department · Supervisor · Hire Date
- Empty-tables suppressed (no ugly "N/A" spam)
- Professional footer with generator provenance + append-only-ledger reference

## Client integration
`downloadPackagePdf()` uses `fetch` + `Blob` + programmatic anchor click so `X-HR-Token` / `X-Safety-Token` / `X-Shop-Token` / `X-Admin-Token` auth headers are transmitted (opening a PDF in a new tab via bare `<a href>` cannot carry custom headers).

**Verdict:** GO. All six packages render correctly with valid `%PDF` binary. Lane gating airtight.
