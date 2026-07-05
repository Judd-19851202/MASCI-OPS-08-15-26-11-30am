# ODS-001 · Current-State Audit

Read-only audit performed before any code changes. Snapshot at start of ODS-001.

## Backend — operational data surfaces

| Surface | Route module | Primary collection(s) | Structured facts today | Status |
| --- | --- | --- | --- | --- |
| Daily Reports V1 | `routes/daily_reports.py` | `daily_reports` | `production[]`, `constraints[]`, `activities[]`, `equipment[]`, `materials[]`, `masci_crews[]`, `subcontractors[]`, `weather_snapshots[]`, `photos[]` (photo:// refs), `safety_topic_ack`, `linked_excavation_ids[]` | LEGALLY CRITICAL · untouched |
| Daily Report V2 (DR-ROI-001 A/B/C) | `routes/dr_v2.py` | `dr_v2_drafts`, `dr_v2_ai_cache`, `dr_v2_ai_approvals`, `dr_v2_ai_audit_entries` | `activity_cards[]`, `constraint_cards[]`, `masci_crews[]`, `equipment_used[]`, `tomorrow_readiness{}`, `safety{}`, `photos[]`, `weather{}` | PREVIEW · feature-flag gated |
| HR portal | `routes/hr_portal.py` + `hr_portal_deps.py` | `hr_time_entries`, employees | crew time, employee identity, roles | untouched |
| Safety | `routes/safety.py`, `safety_forms.py`, `safety_exports.py`, `safety_portal/*`, `trench_safety/*` | `safety_incidents`, `safety_observations`, `jha_records` | incidents, near misses, JHA acks | untouched |
| Equipment | `routes/equipment.py`, `equipment_detection.py` | `equipment_master`, `equipment_checkout_records`, `equipment_hours_log` | equipment usage, checkout, breakdowns | untouched |
| Job Photos | `routes/job_photos.py`, `photo_governance.py` | `job_photos`, `photo_storage` (R2) | photo refs, project link | untouched |
| Payroll | `routes/payroll_variance.py`, `payroll_variance_lifecycle.py` | `payroll_variance_records` | variance reconciliation | untouched |
| Dispatch | `routes/dispatch_*.py` (13 modules) | `dispatch_orders`, `dispatch_haul_ledger`, `dispatch_events` | driver/route/haul events | untouched |
| Projects | `routes/project_health.py`, `project_identity_governance.py`, `project_team_assignments.py`, `projects.py` | `projects`, `project_health_scores` | project master, team roster | may add operational-config alongside |
| Weather | `weather_snapshots[]` on daily_reports; no dedicated collection | inline weather within V1 reports | source snapshot | reuse as-is |

## Cross-surface facts currently DUPLICATED

- **Crew hours** — appear in `daily_reports.masci_crews[]` AND `hr_time_entries` AND `dr_v2_drafts.masci_crews[]`.
- **Equipment usage** — appear in `daily_reports.equipment[]`, `dr_v2_drafts.equipment_used[]`, and `equipment_checkout_records`.
- **Photos** — appear as `photo://` refs inside `daily_reports.photos[]` and independently in `job_photos` mirror.
- **Weather** — inline `weather_snapshots[]` on daily reports only; no normalized weather fact.
- **Delays / constraints** — narrative in V1 `constraints[]`, structured in V2 `constraint_cards[]`, and various dispatch/safety threads mention delay text.
- **Production quantities** — `daily_reports.production[]` and `dr_v2_drafts.activity_cards[]`.

## Sources of truth today

- **Crew hours** — HR time entries are canonical for payroll; DR crew rows for daily context.
- **Equipment usage** — `equipment_checkout_records` for checkout window; daily reports for utilization narrative.
- **Photos** — `job_photos` collection is the mirror of record; DR photo lists are per-report copies.
- **Production quantities** — V1 `daily_reports.production[]` is the authoritative row today.
- **Safety facts** — safety collections are canonical.
- **Project master** — `projects` is canonical.

## Downstream consumers

- PDF generator (V1 daily_report pdf), email routers, PM dashboards, admin dashboards, Employee 360°, dispatch dashboards, safety exports, executive rollups.

## Missing / partially-captured facts

- Cost-code linkage on activities is not standardized. `dr_v2_drafts.activity_cards[]` has `cost_code?` but no project blueprint.
- Delay category taxonomy is freeform (`constraint_cards[].type` is a string).
- Material load-in/out is inline (`daily_reports.materials[]`) with no normalized quantity+unit+direction record.
- Weather impact linkage to delays is not modeled explicitly.
- Photo → activity linkage is not enforced (any photo id is a string).
- Readiness blockers (V2 has this; nothing else).
- Executive intelligence insights are stored only as `dr_v2_ai_audit_entries` and Claude cache — no reusable fact.

## Safe integration points

- Additive collections `operational_facts`, `operational_ingestion_runs`, `operational_kpi_snapshots`, `project_operational_config` behind feature flag `ODS_ENABLED`.
- DR-V2 emission triggered by `POST /api/dr-v2/drafts` save AND `POST /api/dr-v2/ai/approve` (action=accept) — both already run through `routes/dr_v2.py`, safe to hook.
- Read APIs mounted at `/api/ods/*` — new prefix, no collision.

## Risk areas

- V1 daily report POST is legally critical → do not touch.
- Payroll variance and HR time entries are trusted for pay → spine reads only, no writes.
- Job photos mirror is used by mobile → do not remove.
- Ingestion loop must be idempotent → use `(source_type, source_id, source_item_id, source_version)` as canonical dedupe key.

## What must not break

V1 daily-reports POST/GET/PDF/email, HR time queries, safety gates (excavation JHA, trench, silica), Job Photos mirror, DR-V2 shell + feature flag, all existing OpenAPI paths (1447 route baseline post-Phase-C).
