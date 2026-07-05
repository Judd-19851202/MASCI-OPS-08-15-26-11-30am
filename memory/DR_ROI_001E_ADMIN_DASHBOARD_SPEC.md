# DR-ROI-001E · Admin Dashboard Specification

## Route
`GET /admin/ods-intelligence` (SPA)
Consumes:
- `GET /api/ods/admin/dashboard?preset=…`
- `GET /api/ods/admin/delays?preset=…`
- `GET /api/ods/admin/attention?preset=…`

## Layout — Three Horizons

### Horizon 1 · What Happened
Company-wide KPI tiles: Labor hours · Equipment hours · Photos · Projects reporting.
Every tile footnoted with the underlying `*_fact` type from the ODS.

### Horizon 2 · What Is Happening
- **Project health table** — every project reporting in range, sorted by
  (delay desc, safety desc). Columns: Project · Labor · Equip · Delay hrs
  · Safety · Blockers · Days.
- **Top delay categories** — up to 8, sorted by hours desc, with event count.

### Horizon 3 · What Needs Attention
Four evidence-linked lists (safety · quality · delay · readiness), each row
carrying severity + summary + `date · project · source_type · #item_id`.

## Read-only Contract
- Zero writes to V1 collections. Only writes allowed: the
  `ods_briefs_cache` upsert for the executive brief cache.
- No modifications to `daily_reports` or `job_photos`.

## Access Control
- Existing `/admin` guard chain in `AppRoutes.jsx` covers the outer
  route tree; this page inherits admin-only visibility.

## Rollback
- Route mount: 1 line in `AppRoutes.jsx`.
- Page + primitives: `AdminOperationalIntelligence.jsx` +
  `HorizonPrimitives.jsx`.
- Removing all three restores prior state; no data mutation required.
