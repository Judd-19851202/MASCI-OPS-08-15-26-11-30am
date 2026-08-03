# WP18C2 · Crew Intelligence Foundation

## Human-Control Principle Implemented

WP-18C2 implemented **two distinct crew layers**:

1. **Observed crew patterns**
   - Collection: `project_controls_crew_observations`
   - Derived from Daily Report crew evidence only
   - Explainable, non-authoritative, advisory

2. **Confirmed crews**
   - Collection: `project_controls_confirmed_crews`
   - Human-confirmed only through PM project controls authority
   - Stable ID + lifecycle + audit history

## Implemented Observation Model

Observation fields include:

- `observation_id`
- `project_number`
- `source_record_id`
- `source_report_number`
- `observed_on`
- `leader`
- `members[]`
- `member_count`
- `equipment_units[]`
- `signature`
- `confidence_score`, `confidence`
- `explainability`

Current runtime evidence:

- Observation count: **2**

## Implemented Confirmed Crew Model

Confirmed crew fields include:

- `crew_id`
- `project_number`
- `crew_name`
- `leader`
- `members[]`
- `member_count`
- `effective_start`, `effective_end`
- `facility_scope`
- `project_scope`
- `lifecycle_status`
- `source`
- `confirmation_authority`
- `confidence`
- `signature`
- `history[]`
- `created_at`, `created_by`, `updated_at`, `updated_by`

Current runtime evidence:

- Confirmed crew count: **1**
- Confirmed sample:
  - `crew_name = Runtime Crew`
  - `leader = Cert Lead`
  - `members = Worker A, Worker B`
  - `confirmation_authority = cert.pm@example.com`

## Explicit Non-authority Guardrails

WP-18C2 does **not** allow crew intelligence to silently alter:

- HR reporting lines
- employment records
- timekeeping authority
- disciplinary authority
- confirmed crew membership

Any future recurring suggestion must be accepted, rejected, edited, or deferred by a human.
