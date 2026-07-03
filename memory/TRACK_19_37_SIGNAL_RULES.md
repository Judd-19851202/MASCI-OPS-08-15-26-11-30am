# TRACK 19.37 · SIGNAL RULES

**Date:** 2026-07-03 · **Anchor:** `TRACK_19_37_PASSIVE_INCIDENT_PRESENCE_SCORING.md`

Every rule below is **deterministic**. No AI. No inference beyond documented field presence.

Field-name detection is **presence-based** (Track 19.35 doctrine): a field counts if it is a non-empty string, non-empty list/dict, positive number, or literal `True`.

## Owner routing
`recommended_review_owner` is set from the signal's semantic domain:
- **safety** for injury · utility · vehicle/equipment · environmental · property · public · agency · evidence gap · delayed closeout · overdue CAPA.
- **executive** for executive-review-needed.

## Rules

### 1. `possible_injury_presence`
- **Owner:** safety.
- **Triggers if any of:**
  - Field block has any of: `injured_person`, `injured_person_name`, `injury_description`, `injury_body_part`, `injury_type`, `first_aid_given`, `ambulance_called`, `medical_treatment`, `medical_needed`.
  - `case_medical` collection has ≥1 entry.
  - `field_block.incident_type` ∈ { `employee_injury`, `near_miss_injury`, `workplace_violence` }.
- **Score:** 0.85 when any trigger fires; else 0.0.
- **Confidence:** high when field triggers + medical entries both present; else medium; else high (definitive absence).
- **Source fields:** listed field_block keys · `case_medical[]` · `field_block.incident_type`.

### 2. `possible_utility_involvement`
- **Owner:** safety.
- **Triggers if any of:**
  - Field block has any of: `utility_type`, `utility_owner`, `utility_marked`, `ticket_number`, `one_call_ticket`, `eight_one_one_ticket`, `utility_damage_description`.
  - `field_block.incident_type` = `utility_strike`.
- **Score:** 0.9 (incident type) · 0.7 (field only) · 0.0 (absent).
- **Source fields:** listed field_block keys · `field_block.incident_type`.

### 3. `possible_vehicle_equipment_involvement`
- **Owner:** safety.
- **Triggers if any of:**
  - Vehicle fields: `vehicle_ids`, `unit_numbers`, `vehicle_description`, `driver_name`, `driver_role`, `vehicle_operator`.
  - Equipment fields: `equipment_ids`, `equipment_description`, `operator_name`, `equipment_operator`.
  - `field_block.incident_type` ∈ { `vehicle_accident`, `equipment_accident` }.
- **Score:** 0.85 (incident type) · 0.7 (field only) · 0.0 (absent).

### 4. `possible_environmental_involvement`
- **Owner:** safety.
- **Triggers if any of:**
  - Field block has any of: `environmental_impact`, `spill_reported`, `material_released`, `material_type`, `gallons_released`.
  - `field_block.incident_type` ∈ { `environmental`, `spill`, `release` }.
- **Score:** 0.85 (incident type) · 0.65 (field only) · 0.0 (absent).

### 5. `possible_property_damage`
- **Owner:** safety.
- **Triggers if any of:**
  - Field block has any of: `property_damage_description`, `property_owner`, `estimated_property_damage_usd`.
  - `field_block.incident_type` = `property_damage`.
- **Score:** 0.75 (incident type) · 0.6 (field only) · 0.0 (absent).

### 6. `possible_public_exposure`
- **Owner:** safety.
- **Triggers if any of:**
  - Field block has any of: `public_involved`, `public_injuries`, `public_witnesses`, `third_party_present`, `third_party_name`.
- **Score:** 0.7 when any trigger fires; else 0.0.

### 7. `possible_police_agency_involvement`
- **Owner:** safety.
- **Triggers if any of:**
  - Field block has any of: `police_called`, `police_department`, `police_report_number`, `agency_notified`, `agency_name`.
  - `case_agency_contacts` collection has ≥1 entry.
- **Score:** 0.85 (agency entries) · 0.6 (field only) · 0.0 (absent).

### 8. `possible_open_evidence_gap`
- **Owner:** safety.
- **Triggers if:**
  - Any of signals 1–4 fired AND `incident_case_evidence` has 0 non-withdrawn items.
- **Score:** 0.9 when the gap exists; else 0.0.
- **Source fields:** `incident_case_evidence[]` · `field_block.incident_type`.

### 9. `possible_delayed_closeout`
- **Owner:** safety.
- **Triggers if:**
  - `incident_cases.state` is not `CLOSED` AND `days_since(submitted_at || created_at) > 30`.
- **Score:** `min(1.0, 0.5 + (days_open - 30) / 60.0)` while triggered; else 0.0.
- **Source fields:** `incident_cases.state` · `incident_cases.submitted_at` · `incident_cases.created_at`.

### 10. `possible_overdue_capa`
- **Owner:** safety.
- **Triggers if:**
  - Any `corrective_actions` document has `due_at < now` AND `state ∈ { OPEN, IN_PROGRESS, "" }`.
- **Score:** `min(1.0, 0.5 + 0.1 * overdue_count)` when triggered; else 0.0.
- **Source fields:** `corrective_actions.due_at` · `corrective_actions.state`.

### 11. `possible_executive_review_needed`
- **Owner:** executive.
- **Triggers if:**
  - `incident_cases.state ∈ { READY_FOR_REVIEW, APPROVED, PENDING_EXEC_REVIEW }` AND `safety_block.executive_reviewer` is empty.
- **Score:** 0.8 when triggered; else 0.0.
- **Source fields:** `incident_cases.state` · `incident_cases.safety_block.executive_reviewer`.

## Overall aggregation
```
overall_attention_score = round(100 * sum(signal.score) / 11)
attention_level         = "high"   if overall >= 60
                         "medium"  if overall >= 30
                         "low"     otherwise
```

## Determinism guarantees
- No calls to any LLM, external service, or model.
- No randomness. No timestamp-based tie-breaking (except the deterministic "days since" calculation).
- Same inputs → same outputs, forever.
- The `generated_at` field is the only time-varying output — it is the assembly timestamp only, not an input to any score.

## Vocabulary discipline
No signal label, rationale, or source_field name contains: `osha_recordable`, `liability`, `liable`, `discipline`, `disciplinary`, `fault`, `blame`, `preventability`, `root_cause_conclusion`. Enforced by the Track 19.37 lock test.
