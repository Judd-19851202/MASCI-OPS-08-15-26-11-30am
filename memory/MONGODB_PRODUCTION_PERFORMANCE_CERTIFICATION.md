# WP-16A — MongoDB Production Performance Certification

Date: 2026-07-31
Status: PASS WITH MONITORED EXCEPTIONS

## Scope

Production-readiness database review performed using:

- uploaded MongoDB Atlas Query Shape Performance screenshot evidence
- local MongoDB `explain("executionStats")`
- live API timing
- code-path tracing
- index inspection
- query-shape reproduction where possible

## Atlas Evidence Reviewed

Uploaded Atlas screenshot identified repeated high-cost query shapes concentrated in `masci_safety_preview.operational_facts` and one healthy notifications query.

Visible Atlas findings:

| Shape ID | Namespace | Avg latency | Docs examined | Docs returned | Ratio |
| --- | --- | ---: | ---: | ---: | ---: |
| `0E6EA0FE..` | `masci_safety_preview.operational_facts` | 993 ms | 837,805 | 1,130 | ~741:1 |
| `AD7B2190..` | `masci_safety_preview.operational_facts` | 1,995 ms | 158,158 | 282 | ~561:1 |
| `415DC237..` | `masci_safety_preview.operational_facts` | 8,857 ms | 20,889 | 50 | ~418:1 |
| `AB262DE3..` | `masci_safety_preview.operational_facts` | 1,230 ms | 61,171,370 | 283 | ~216,153:1 |
| `7410F...` | `masci_safety_preview.notifications` | 112 ms | 1 | 2,671 | healthy |

## Query Inventory / Code-Path Mapping

### 1. `operational_facts` — trench safety company KPI workflow

- **Endpoint:** `/api/safety/company/trench-safety-kpis?window=30d`
- **Page/workflow:** company trench safety card / intelligence surfaces
- **Service:** `backend/services/safety_portal_trench/trench_kpi_lift.py`
- **Collection:** `operational_facts`
- **Operational classification:** user-facing, blocking
- **Observed pre-fix latency:** ~13.0s live API
- **Root cause:** `_top_projects_by_attention()` streamed a large in-window fact set into Python and performed per-project ranking there
- **Repair:**
  - added targeted index `ods_facts_source_window`
  - rewrote `_top_projects_by_attention()` to aggregate project counters in MongoDB
- **Observed post-fix latency:** ~1.04s live API
- **Operational result:** moved from production defect to investigated/acceptable range for current workload

### 2. `operational_facts` — safety KPI / project-window fact scans

- **Endpoint family:** company/project safety KPI and ODS fact readers
- **Page/workflow:** safety KPI dashboards and executive intelligence reads
- **Service:** `backend/routes/operational_kpis.py`, `backend/services/operational_kpis/aggregator.py`
- **Collection:** `operational_facts`
- **Operational classification:** user-facing and dashboard-backed
- **Explain findings:** existing `ods_facts_hot_query` index is used for project/date/fact-type/current windows; explain results were materially healthier than the Atlas worst-case screenshot after current repairs
- **Current live timing:** `/api/safety/company/safety-kpis?window=30d` ~1.7s
- **Disposition:** investigated; no speculative redesign applied

### 3. `notifications`

- **Endpoint family:** notifications read/unread flows
- **Atlas evidence:** ~112 ms, docs examined ≈ 1, healthy
- **Disposition:** accepted as healthy; no repair needed

## Explain Plan Findings

### Verified efficient / acceptable paths

- `notifications` latest-recipient query remained well targeted and low latency
- `operational_facts` project/date/current windows used existing hot-query index paths after repair set
- `transport_cleanup_companion` no longer relied on repeated per-entity Mongo lookups for packet/orientation/inspection loaders

### Verified inefficient path repaired

- `company_trench_safety_kpis_total` dominant subquery pre-fix:
  - `_top_projects_by_attention`: ~9.64s
  - post-fix: ~0.32s
- endpoint total:
  - pre-fix: ~13.02s
  - post-fix: ~1.04s

## Index Audit

Collections reviewed directly:

- `operational_facts`
- `notifications`
- `daily_reports`
- `equipment_inspections`
- `jobs_master`

### Index changes applied

Added:

- `operational_facts` → `ods_facts_source_window`
  - keys: `(tenant_id, source_type, source_id, fact_type, is_current, date)`
  - justification: measured user-facing trench-safety fact windows and Atlas evidence concentrated on `operational_facts`

No index removals were applied during this pass.

## API Performance Review

Measured live preview API timings after repairs:

| Endpoint | Result |
| --- | --- |
| `/api/admin/transportation/intelligence/cleanup-signals?days=30` | improved from ~24–25s to ~0.89s |
| `/api/safety/company/trench-safety-kpis?window=30d` | improved from ~13.02s to ~1.04s |
| `/api/admin/integrations/health` | ~0.47s |
| `/api/admin/recovery/snapshot` | sub-second to low-second range depending on backup state |

## Accepted Exceptions

- `operational_facts` remains a very large multi-domain fact collection (~1M+ docs in preview). Some analytical and dashboard-shaped reads are still heavier than simple OLTP lookups; they are acceptable when non-blocking or after the current user-facing bottlenecks are removed.
- Safety KPI company endpoint remains above the 500 ms healthy target, but no longer sits in the >5s production-defect range. Current post-repair latency is acceptable for pre-deployment certification with continued monitoring.

## Monitoring Recommendations

1. Continue watching Atlas query shapes for `operational_facts`, especially new shapes diverging from the repaired trench-safety pattern.
2. Track the company safety KPI endpoint if latency rises above ~2s sustained under real concurrency.
3. Keep `notifications` query behavior as the model example for tight filter/index alignment.

## Certification Verdict

MongoDB production performance review completed.

- Every visible high-cost Atlas query family was investigated.
- A confirmed user-facing bottleneck was repaired with measurable benefit.
- No speculative architectural rewrite was performed.
- Remaining heavier analytical behavior is documented and currently acceptable.

**Verdict: DATABASE PERFORMANCE CERTIFICATION PASS**