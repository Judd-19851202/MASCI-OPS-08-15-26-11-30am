# ODS-001 · Canonical Fact Model

Every spine record is a **fact**: a single normalized observation of one operational thing on one day for one project. Facts are additive, derived, versioned, and traceable.

## Envelope — fields on EVERY fact

| Field | Type | Notes |
| --- | --- | --- |
| `fact_id` | uuid str | primary key |
| `fact_type` | enum str | see 11 types below |
| `tenant_id` | str | mirrors project.tenant if present, defaults to `"masci"` (single-tenant today) |
| `project_id` | str | required for every fact |
| `date` | ISO date (YYYY-MM-DD) | operational date, not `created_at` |
| `source_type` | enum | `daily_report_v1`, `daily_report_v2`, `hr_time`, `equipment_checkout`, `safety_form`, `qa_form`, `job_photo`, `dispatch_event`, `manual_ingest`, `mobile_submission` |
| `source_id` | str | id of the source document |
| `source_item_id` | str | id of the item within the source (e.g. row_id on production, activity_card id on V2) |
| `source_version` | int | source doc `updated_at` monotonic counter (rerun = new version) |
| `source_status` | enum | `full`, `partial`, `regenerated`, `superseded` |
| `is_current` | bool | true iff latest regeneration for `(source_type, source_id, source_item_id)` |
| `submitted_by` | str \| None | supervisor user id or free string |
| `verified_identity` | bool | true if `submitted_by` resolved to a directory user |
| `confidence` | float 0..1 | 1.0 for supervisor-entered facts, lower for AI-derived |
| `trace_id` | uuid str | ingestion run this fact came from |
| `ingestion_run_id` | uuid str | FK to `operational_ingestion_runs` |
| `created_at` | ISO datetime UTC | |
| `updated_at` | ISO datetime UTC | |
| `payload` | dict | fact-type-specific structured body |

## 11 fact types + payload schema

### 1. `labor_fact`
```
{ employee_id?, person_name, company, role?, hours: float, overtime_hours?: float,
  cost_code?, activity_link?: fact_id, verified_identity: bool }
```

### 2. `equipment_fact`
```
{ equipment_id, equipment_label, operator?: str,
  hours_used: float, idle_hours?: float, breakdown: bool, maintenance: bool,
  cost_code?, activity_link?: fact_id }
```

### 3. `production_fact`
```
{ cost_code?, activity, work_area?,
  quantity: float, unit: str,
  crew_links?: [fact_id], equipment_links?: [fact_id],
  photo_evidence_links?: [str] }
```

### 4. `delay_fact`
```
{ delay_category: enum (weather|material|equipment|permit|design|labor|utility|other),
  duration_hours?: float, reason: str, responsible_party?: str,
  impact: enum (low|med|high|blocker),
  cost_risk: bool, schedule_risk: bool,
  needed_action?: str, evidence_links?: [str] }
```

### 5. `material_fact`
```
{ material, quantity: float, unit: str,
  loads_in?: int, loads_out?: int, supplier?: str, haul_direction?: enum (in|out|internal),
  activity_link?: fact_id, cost_code? }
```

### 6. `safety_fact`
```
{ safety_type: enum (observation|near_miss|incident|jha_ack),
  severity: enum (info|low|med|high|critical),
  linked_workflow?: str, employee_link?: fact_id, equipment_link?: fact_id, activity_link?: fact_id,
  narrative?: str, evidence_links?: [str] }
```

### 7. `quality_fact`
```
{ quality_type: enum (inspection|nonconformance|rework|acceptance),
  status: enum (open|closed|resolved),
  responsible_party?: str, activity_link?: fact_id, cost_code?,
  narrative?: str, evidence_links?: [str] }
```

### 8. `photo_evidence_fact`
```
{ photo_ref, storage_url?, thumb_url?,
  linked_activity?: fact_id, linked_delay?: fact_id, linked_equipment?: fact_id,
  linked_safety?: fact_id, linked_quality?: fact_id,
  ai_tags?: [str], caption?: str }
```

### 9. `weather_fact`
```
{ temperature_f?: float, precipitation_in?: float, wind_mph?: float, condition?: str,
  weather_impact?: str, delay_linkage?: fact_id, source_dataset?: str }
```

### 10. `readiness_fact`
```
{ readiness_area: enum (crew|materials|equipment|permits|schedule|weather),
  status: enum (ready|at_risk|blocker),
  need?: str, blocker?: str, responsible_party?: str, needed_by?: ISO date }
```

### 11. `intelligence_fact`
```
{ audience: enum (supervisor|pm|admin|executive),
  insight: str, sources_facts: [fact_id],
  model?: str (hidden from field UI), provider?: str,
  confidence: float, approved_by?: str, approved_at?: ISO datetime }
```

## Uniqueness constraint (dedupe key)

Composite index: `(tenant_id, project_id, source_type, source_id, source_item_id, fact_type)`
+ partial filter `is_current=true`.

Regenerating a source updates all matching facts to `is_current=false` and inserts new ones as `is_current=true` in the same ingestion run.

## Invariants

- A `labor_fact` with `verified_identity=true` MAY inform payroll; unverified rows MAY NOT.
- Every `production_fact.quantity >= 0`.
- Every fact with `confidence < 1.0` MUST be an AI-derived fact and MUST reference source facts.
- `intelligence_fact` MAY NOT be a source for another `intelligence_fact` (no recursion).
