# DR-ROI-001E · Executive Dashboard + Brief Specification

## Route
`GET /executive/ods-intelligence`

## Data Sources
- `GET /api/ods/admin/dashboard?preset=…` (company totals)
- `GET /api/ods/executive/health?preset=…` (top-at-risk projects, top 10)
- `GET /api/ods/admin/attention?preset=…&limit=15` (attention buckets)
- (Optional caller-driven) `GET /api/ods/executive/brief?preset=…`

## Layout — Three Horizons

### Horizon 1 · What Happened
Four portfolio-level KPI tiles: Total labor · Total equipment · Projects
reporting · Photos captured.

### Horizon 2 · What Is Happening
Single table: **Top-at-risk projects** (max 10), sorted by
(delay desc, safety desc). Columns: Project · Delay hrs · Safety ·
Blockers · Labor hrs · Days.

### Horizon 3 · What Needs Attention
Four evidence lists (safety · quality · delay · readiness), rate-limited
to 15 items per bucket to keep the surface scannable at portfolio scale.

## Executive Brief (server-side)
`GET /api/ods/executive/brief` returns `{narrative, confidence,
evidence_refs, sources_used, uncertainties}` produced by the AI Provider
Gateway `executive_brief` task. The brief is **cache-first** — keyed by
a deterministic SHA-256 of the input evidence payload — so a repeat
request for the same range never hits the LLM again.

The brief is **not surfaced on the SPA landing page in this phase**;
Phase F (PDF Redesign) is the primary consumer. The SPA can request the
brief on demand and render `narrative` + `confidence` — but never the
model/provider name or token count.

## Invisible Intelligence
- The word `Claude`, `Anthropic`, `LLM`, `Sonnet`, `token`, `provider`
  never appears in the executive UI.
- Errors from the gateway degrade gracefully — the dashboard remains
  fully functional without the brief.
