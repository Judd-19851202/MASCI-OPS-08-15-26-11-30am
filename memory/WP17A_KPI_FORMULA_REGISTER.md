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
