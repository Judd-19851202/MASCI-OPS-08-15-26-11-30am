# D7/D8 Performance Baseline

## Scope
- Canonical workspace-only baseline for backend, frontend, PDF/file, scheduler, backup-workload, and workspace-resource surfaces.
- Preview probes intentionally fail-closed under D1; 502 responses are captured as evidence, not regressions.
- No Atlas index mutation, no production mutation, no deployment activity.

## Baseline Highlights
- Backend dependency count: 169 Python packages.
- Frontend dependency count: 72 packages.
- Frontend build artifact footprint: 52,671,395 bytes total.
- Workspace footprint: backend 121,450,458 bytes, frontend 2,208,055,527 bytes, docs 7,373,458 bytes, /tmp 2,448,030 bytes.
- Scheduler inventory: 17 registered long-running or scheduled tasks.

## Query-Targeting Outcomes
- `operational_facts` one-row trench KPI read was traced to project-scoped latest-fact queries in `backend/services/safety_portal_trench/trench_kpi_lift.py`; repair adds explicit `project_id` targeting and aligns trench readers to the existing tenant-aware hot query pattern.
- Definitively empty PM scope now short-circuits in the read-heavy routes documented in `ATLAS_ALERT_EVIDENCE_REGISTER.md`, returning empty payloads before MongoDB is touched.

## Governing Thresholds
- API health/ready target: <= 1.0s when the service is live.
- Frontend workspace ceiling: 2.5 GB.
- Frontend bundle ceiling: 55,000,000 bytes.
- `/tmp` ceiling: 50,000,000 bytes.
- Disk fail threshold for bounded cleanup: 92%.

## Safe Self-Healing Foundation
- Runtime authority remains `backend/lib/runtime_reliability.py`.
- D7/D8 adds bounded workspace cleanup under resource distress, persisted incident evidence, and explicit admin access to the canonical baseline.
- D9 can expand remediation sophistication, but D7/D8 already establishes bounded, governed, evidence-first resilience.