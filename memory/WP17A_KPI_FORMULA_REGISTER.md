# WP-17A KPI Formula Register

Date opened: 2026-07-31
Status: ACTIVE

## Initial formula items under remediation

### FR-001 — Daily Report Draft Health
- Current formula: raw count of append-only `draft_telemetry` events by event name + time bucket
- Problem: counts events, not proven distinct logical drafts
- Required direction: derive canonical draft identity or relabel metric as telemetry activity

### FR-002 — Backup Health Check (OCC)
- Current formula: local backup directory existence + local file count
- Problem: does not represent canonical production backup truth in an R2-first recovery model
- Required direction: consume unified backup truth service; local cache may remain secondary only

### FR-003 — Security & Deployment Posture / CORS pinned
- Current formula: `CORS_ORIGINS` env string inspection
- Problem: may misrepresent effective middleware policy when regex fallback is authoritative
- Required direction: inspect effective middleware/runtime policy instead of only raw env string

### FR-004 — Governance Convergence
- Current formula: weighted deduction from persisted open findings
- Problem: no explicit freshness state / scan confidence model
- Required direction: separate findings inventory, scan freshness, and scan execution health

### FR-005 — R2 Lifecycle Health
- Current formula: weighted blend of capacity, ownership, orphan, retention, backup, lifecycle, freshness
- Problem: stale inventory and ownership uncertainty are blended into one score
- Required direction: separate freshness, ownership coverage, and confirmed orphan risk

### FR-006 — Master Binding Coverage
- Current formula: eligible records with canonical binding present or at least one source field populated
- Problem repaired: prior gap view used total-row denominator and hid remediation metadata
- Current direction: expose eligible denominator, source fields, canonical field, backfill endpoint, and review queue endpoint

### FR-007 — Local Disk Pressure Audit
- Current formula: `/app` used percent + largest consumers + safe cleanup reclaim projection
- Problem repaired: prior truth surface lacked thresholds, retention classes, protected evidence disclosure, and cleanup history context
- Current direction: keep point-in-time truth explicit until local trend history is implemented

### FR-008 — Production Certification Freshness Policy
- Current formula: per-workflow freshness SLA and terminal success policy
- Problem repaired: prior truth model exposed a single global freshness window without workflow-specific operational rationale
- Current direction: classify each workflow by evidence type, acceptable execution frequency, stale threshold, failure threshold, and not-applicable behavior

### FR-009 — Executive Overview Canonical Open Incident / CA Truth
- Current formula: executive rollup tiles now use the same canonical semantics as downstream operational dashboards
- Problem repaired: executive attention counts previously used open-status strings while other dashboards used `resolution_status != Closed` / open-CA exclusion rules
- Current direction: keep executive tile formulas pinned to canonical open incident and open corrective-action match clauses and expose them in `kpi_metadata`

### FR-010 — Project Health Status Ladder Metadata
- Current formula: red / amber / green summary cards backed by explicit indicator formulas and role-scoped active projects
- Problem repaired: summary states were deterministic but not self-describing, allowing semantic drift between source, API, and UI
- Current direction: emit page / summary / indicator metadata with the authoritative formulas directly from `/api/project-health`

### FR-011 — HR Queue / Expiration Truth
- Current formula: active employees from canonical HR roster, pending requests from `employee_requests`, pending time-off from FL stats, training due soon from `counts.in_30 + counts.in_60`, docs expired from `counts.expired`
- Problem repaired: prior UI read the wrong endpoints and flat response keys, silently converting live risk into fake-green zeros
- Current direction: keep shared HR surfaces consuming the same canonical endpoints and surface per-endpoint metadata for provenance

### FR-012 — Safety Company Band / Grouped Card Provenance
- Current formula: company band from shared safety rollup (`red` on escalation gaps or injuries, `amber` on incidents or near misses, else `green`) with totals summed from the shared per-project spine
- Problem repaired: grouped card totals were visible but their provenance and band semantics were not explicit to operators
- Current direction: emit card-level metadata and preserve one shared operational spine for company + project safety views

### FR-013 — Production Lock Gate
- Current formula: WP-17A may only lock when the live production build exposes `/api/admin/wp17a/*`, reconciliation passes with zero blockers, and certification reports truthful live success
- Problem repaired: preview certification alone cannot be mistaken for production completion
- Current direction: fail lock when production still serves an older build or missing governance routes
