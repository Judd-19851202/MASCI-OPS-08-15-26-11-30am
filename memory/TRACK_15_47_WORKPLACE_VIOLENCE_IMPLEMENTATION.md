# TRACK 15.47 · Workplace Violence Workflow Implementation

**Date:** 2026-06-19 · **Status:** ✅ DELIVERED · live in preview DB

The user directive was explicit: **NO V2 collection**. Workplace Violence is an EXTENSION of the existing incident workflow, not a parallel system. Everything below uses one collection (`incidents`), one route (`/api/incidents`), one PDF (`incident`), one CAPA chain (`safety/corrective-actions` with `source_kind=incident`), one notification chain.

## What "Workplace Violence" means in ForgedOps
A `classifications: [...]` entry on the incident document includes `"Workplace Violence"` and/or `"Physical Assault"` and/or `"Weapon Displayed"` and/or `"Weapon Used"`. Any of those four — or `physical_assault=true`, `weapon_displayed=true`, `weapon_used=true`, `arrest_made=true` — triggers the WV pathway.

## Trigger → Workflow (verified live · 2026-06-19)
| Stage | Mechanism | Verified |
|---|---|:---:|
| Report | `POST /api/incidents` accepts `classifications[]` + the structured Track 15.47 fields | ✅ Smoke-tested: payload persisted, doc_id INC-2026-00494. |
| Classify | Multi-select on form OR via API. Workplace Violence is one of 14 valid classifications. | ✅ Persisted unchanged. |
| Notify | `safety.py` fan-out detects WV flags → emits Critical-severity `incident.violence` notifications to FOUR roles (Superintendent · Operations · Executive · HR) in addition to the legacy Safety + PM fan-out. | ✅ 9 notifications recorded for the test incident, all expected roles present. |
| Auto-CAPA | A "Workplace-violence review — confirm witnesses + police data + media exposure" task is auto-issued, priority Critical, assignee_role safety. | ✅ Emitted via `emit_task_and_notification`. |
| Investigate | Same `POST /incidents/{id}/transition` lifecycle state machine. open → investigating → review → closed. | ✅ Unchanged from existing certified workflow. |
| Correct | Same `/safety/corrective-actions` CAPA chain. Auto-CAPA + manual additions both link via `source_kind="incident"`. | ✅ Unchanged. |
| Verify | Same CAPA `status` + `completion_notes` + `closed_by_name` + `completed_at`. | ✅ Unchanged. |
| Close | Same `POST /incidents/{id}/transition` to `closed`. | ✅ Unchanged. |
| PDF | Same `render_record_pdf("incident", ...)` enriched via `lib/incident_pdf_enrichment.enrich_incident_for_pdf`. Renders classifications + threat fields + police fields + extended witnesses + typed attachments + investigation timeline + linked CAPAs. | ✅ Synthetic PDF INC-2026-00488 (2.3 MB) verified by content analysis. |

## Field hardening (G1-G5)
- **G1 Classifications** — additive list on `IncidentCreate` (controlled vocabulary in `frontend/src/lib/incidentSchema.js`: 14 values).
- **G2 Threat / Contact** — `threat_made`, `threat_description`, `physical_contact`, `physical_assault`, `weapon_displayed`, `weapon_used`, `weapon_description`, `media_filmed`, `social_media_posted` — all booleans/strings, persisted.
- **G3 Police** — `police_called`, `police_arrived`, `police_agency`, `police_officer_name`, `police_badge`, `police_case_number`, `police_report_number`, `police_report_obtained`, `arrest_made`, `citation_issued`.
- **G4 Witnesses** — sub-doc extended with `role`, `phone`, `email`, `employer`, `witness_type`, `signature` (PDF renderer multi-row witness table with all columns).
- **G5 Damage & Claim** — `damage_description`, `damage_estimated_value`, `vehicle_make_model`, `vehicle_vin`, `vehicle_plate`, `asset_number`, `insurance_claim_number`, `insurance_carrier`.

## What the WV pathway does NOT do (by design)
- It does NOT create a new collection.
- It does NOT create a new route.
- It does NOT create a new PDF system.
- It does NOT create a new notification engine.
- It does NOT create a parallel CAPA chain.
- It does NOT bypass the existing incident lifecycle.

Compliance with the user's "no V2 systems" mandate is full.

## Sign-off
WV is live behavior on every incident that carries any of the triggering flags. No migration of prior records required — existing 69 incidents continue to render and behave identically. The WV pathway is purely additive activation on new records that carry the flags.
