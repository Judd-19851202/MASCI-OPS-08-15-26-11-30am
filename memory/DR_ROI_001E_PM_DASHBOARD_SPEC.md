# DR-ROI-001E · PM Dashboard Specification

## Route
`GET /pm/operational-intelligence` (SPA route)
Consumes:
- `GET /api/ods/pm/dashboard?preset=…&project_ids=…`
- `GET /api/ods/pm/attention?preset=…&project_ids=…`
- `GET /api/ods/admin/delays?preset=…` (for the delay-category card;
  scoped client-side to the PM's active project set)

## Layout — Three Horizons

### Horizon 1 · What Happened
Four KPI tiles:
- Labor hours (`labor_fact`)
- Equipment hours (`equipment_fact`)
- Photos (`photo_evidence_fact`)
- Days reported (Σ `days_reported`, footnote: N projects)

### Horizon 2 · What Is Happening
Two side-by-side panels:
- **Production by cost code** — top 8, sorted desc by qty, from
  `kpis.production_by_cost_code`.
- **Delay categories** — top 8, sorted desc by hours, from
  `delays.by_category`.

Plus a project roll-up table:
- Columns: Project · Labor · Equip · Delay hrs · Safety · Blockers · Days.
- Rows: one per project, sorted by delay + safety (backend-sorted).

### Horizon 3 · What Needs Attention
Four evidence-linked lists (safety · quality · delay · readiness). Each row shows:
- Severity chip
- One-line summary (from `payload.description`/`reason`/`blocker`)
- `date · project_id · source_type · #source_item_id[:8]`

## Data Freshness
- Snapshots are (re)computed by the DR emission pipeline when a Daily
  Report is submitted / edited.
- The dashboard shows whatever is in `operational_kpi_snapshots` +
  `operational_facts` at fetch time. No client polling.

## Filters
- Date preset picker (`Today / Yesterday / This week / Last week / This
  month / Last month / Quarter / Year`).
- Custom `date_from`/`date_to` supported by the API for future UI use.

## Access Control
- Route mounted under the standard PM route tree (existing PM guard
  chain in `AppRoutes.jsx`).
- Backend endpoints are read-only; scoping to project set is enforced
  by whichever guard fronts the route in the future — Phase E ships the
  additive read surface; role gating is inherited from the outer app.

## Design Rules
- Font: system stack, `text-2xl` for KPI values, `text-[10px]` for micro-labels.
- Palette: neutral gray + red-600 preset-active accent (matches the
  operational-recovery visual language). No purple, no gradients.
- No chart libraries. Tables + KPI tiles only.
- Every tile carries a `footnote` that names the underlying fact type.

## data-testid inventory
`pm-intel-page`, `pm-intel-preset-picker`, `pm-intel-preset-{key}`,
`pm-intel-kpis`, `pm-kpi-labor`, `pm-kpi-equipment`, `pm-kpi-photos`,
`pm-kpi-days`, `pm-horizon-1`, `pm-horizon-2`, `pm-horizon-3`,
`pm-intel-production`, `pm-intel-delays`, `pm-intel-projects`,
`pm-project-row-{id}`, `pm-attention-safety`, `pm-attention-quality`,
`pm-attention-delay`, `pm-attention-readiness`.
