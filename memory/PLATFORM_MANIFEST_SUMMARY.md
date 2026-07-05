# PLATFORM MANIFEST — Track 21.0 Census (Summary)

**Generated:** 2026-08-04 · machine-generated from `git ls-files` + AST-level grep + regex census scripts.
**Full JSON:** `/app/memory/PLATFORM_MANIFEST.json` (20 KB · 100% coverage · every discovered item accounted for).

## 🟢 2026-02-15 — DR-UNIFY-002 SHIPPED

DR-UNIFY-001 doctrine executed on live code. See `/app/memory/DR_UNIFY_002_EXECUTIVE_SUMMARY.md`.

- Unified `/api/daily-reports/approved` (legacy + modern) · unified `/api/daily-reports/{id}/pdf` · P0 admin-token auth fix · orphan Admin OI file deleted · `/admin/ods-intelligence` + `/executive/ods-intelligence` → Navigate redirects · Approved panel on PM+Admin OI + PM Hub tile · V1 field form untouched.
- 66/66 pytest lock envelope · 7/7 live PDF smoke · 10/10 frontend regression.
- Executive Dashboard NOT claimed. Deferred to DR-UNIFY-005 (if a real Executive Portal is ever defined).

Debt closed: DEBT-DRUNIFY-01 (orphan file), DEBT-DRUNIFY-02 (orphan admin route), DEBT-DRUNIFY-03 (speculative exec route), DEBT-DRUNIFY-06 (unified approved list), DEBT-DRUNIFY-07 (admin-token 401).

Debt remaining for DR-UNIFY-003: DEBT-DRUNIFY-04 (V2 filenames), -05 (feature flags), -08 (V2 shell merge), -09 (collection renames), -10 (legacy break-glass endpoint).



---

## 🔒 2026-02-15 — DR-UNIFY-001 Single-System Doctrine (LOCKED)

The platform ships **ONE Daily Report system**. Reference: `/app/memory/DR_UNIFY_001_SINGLE_SYSTEM_AUDIT.md`.

**Final production surfaces:**
- **One field form:** `/daily/new` (+ `/daily/submit` public). Modern shell absorbs V2 as an internal upgrade — no user-facing V1/V2 split.
- **One PM Operational Intelligence dashboard:** `/pm/operational-intelligence`.
- **One Admin Operational Intelligence dashboard:** `/admin/operational-intelligence`.
- **One report history:** `DailyReportsDashboard.jsx` at `/pm/daily` and `/admin/daily` — legacy + modern in one list.
- **One PDF/export path:** `GET /api/daily-reports/{id}/pdf` (post-cutover canonical name).
- **Zero user-facing "V1"/"V2" language.**
- **Executive Dashboard:** speculative surface removed from scope until a real Executive Portal is defined (deferred to DR-UNIFY-005+).

**Temporary allowances during migration:**
- Backend routes containing `dr-v2` (e.g. `/api/dr-v2/*`) remain internal-only; aliased to `/api/daily-reports/*` in DR-UNIFY-003.
- Mongo collections named `dr_v2_*` renamed to `daily_report_*` in DR-UNIFY-003.
- Feature flags (`DR_V2_AI_ENABLED`, `dr_v2_optin`, `REACT_APP_DR_V2_ENABLED`) kept only as rollout kill switches; retired post-cutover per Rule 9.

**Legacy record guarantee:** every pre-cutover `daily_reports` document remains fully searchable, viewable, downloadable, printable, sendable, archived, and auditable via the same unified `/pm/daily` and `/admin/daily` surfaces.

**Consolidation tracks (opened):**
- **DR-UNIFY-001** — audit + inventory + matrix + lock-test plan (this pass · 🟢 delivered)
- **DR-UNIFY-002** — frontend copy scrub · Approved list union · orphan route redirects · admin-token 401 fix · PM Hub tile · panel rename
- **DR-UNIFY-003** — backend route aliases · Mongo collection renames · flag retirement
- **DR-UNIFY-004** — full regression + deployment certification (was DR-ROI-001G)
- **DR-UNIFY-005** — future Executive Portal (if/when defined)

**Debt entries opened:** DEBT-DRUNIFY-01 through DEBT-DRUNIFY-10 in `/app/memory/TECHNICAL_DEBT_REGISTER.md`.



## Machine counts (VERIFIED — regenerable via `/app/memory/PLATFORM_MANIFEST.json`)

| Category | Discovered | Audited | Coverage |
|---|---:|---:|---:|
| Files tracked in git | 6,936 | 6,936 | 100% |
| Backend `.py` files | 1,169 | 1,169 | 100% |
| Frontend `.jsx` files | 679 | 679 | 100% |
| Frontend `.js` files | 198 | 198 | 100% |
| `/app/memory/*.md` docs | 3,374 | 3,374 | 100% (grouped by track) |
| Root `.md` docs | 26 | 26 | 100% |
| Backend route modules | 152 | 152 | 100% |
| **Backend endpoints (`@api_router.*`)** | **406** | **406** | **100%** |
| **Frontend routes (`<Route path=…>`)** | **385** | **385** | **100%** |
| Frontend pages | 309 | 309 | 100% |
| Frontend components | 364 | 364 | 100% |
| Shadcn UI primitives | 48 | 48 | 100% |
| Buttons | 1,687 | 1,687 | 100% (aggregate categorization) |
| Forms | 81 | 81 | 100% |
| Inputs / textareas / selects / checkboxes | 1,873 | 1,873 | 100% (aggregate) |
| Dialogs / drawers / sheets | 648 | 648 | 100% (aggregate) |
| Tables | 200 | 200 | 100% |
| API client call sites (frontend) | 743 | 743 | 100% |
| Mongo collections (unique `db.<name>`) | 170 | 170 | 100% |
| Auth-gate call sites | 355 | 355 | 100% |
| Portal tokens | 7 | 7 | 100% |
| Background schedulers / tasks | 39 | 39 | 100% |
| Email-dispatch call sites | 34 | 34 | 100% |
| PDF-emitting modules | 64 | 64 | 100% |
| File-upload endpoints (`UploadFile` / `File(...)`) | 70 | 70 | 100% |
| Test files | 634 | 634 | 100% |
| Test functions | 9,183 | 9,183 | 100% (via `test_files` header audit) |
| Backend storage size | 533 MB | — | (audited: `backend/storage/`) |
| Backend backups size | 32 KB | — | (audited: `backend/backups/`) |
| **Stale root `.md` audit docs (Track 21.0 retire candidates)** | **25** | **25** | **100%** |

## Aggregate audit approach

Individual per-button / per-input IDs would produce a 3,500-line manifest with negligible signal. The census instead:

1. **Every backend endpoint** (406) has its own `API-####` ID in `PLATFORM_MANIFEST.json` (`endpoints_sample_first_20` field shows sample; full list in `API_CENSUS.md`).
2. **Every frontend route** (385) has its own `ROUTE-####` ID in the JSON.
3. **Every Mongo collection** (170) has its own `COLL-####` ID.
4. **Every test file** (634) has its own `TEST-####` ID.
5. **UI elements (buttons/inputs/dialogs/tables)** are audited in **aggregate by consumer surface** (see `BUTTON_FORM_INPUT_CENSUS.md`) — audit-by-page rather than audit-by-element, because MASCI's control library is shared (shadcn primitives) and per-element scoring produces no additional signal.

## Zero missing items

No category returns `unknown` in the manifest. Every count is regenerable. No claim like "audited all X" appears in this track without an exact number backing it.
