# TRACK 15.50 · Training Defensibility Audit (Phase 1)

**Status:** ✅ AUDIT COMPLETE · existing infrastructure adequate · ONE additive field shipped.

## Audit findings · existing infrastructure
| Capability | Where it lives | Pre-15.50 status |
|---|---|:---:|
| Assign retraining (as a CAPA / task) | `corrective_actions` + `tasks` collections | ✅ |
| Track completion | `safety_training_records` collection · `completed_date` field | ✅ |
| Verify completion | `safety_training_records.created_by_name` / `created_by` / `created_by_role` (iter353a) | ✅ |
| Show completion on PDFs | `training_pdf.py` exists for certificate rendering | ✅ |
| Tie completion to an incident | **MISSING** — no link field on `safety_training_records` | 🔴 GAP |

## What 15.50 added (smallest additive solution)
ONE new field on `safety_training_records`: `source_incident_id` + `source_incident_doc_id` + `topic_keys` (optional list of safety-topic keys delivered).

That field closes the loop. Now a training record CAN be traced back to the incident that mandated it.

## Files touched
| File | Change |
|---|---|
| `routes/safety_portal/_models.py` | Added 3 optional fields to `TrainingRecordCreate` + `TrainingRecordUpdate` |
| `routes/safety_portal/training.py` | `POST /api/safety/training-records` accepts the new fields, persists them |
| `lib/incident_pdf_enrichment.py` | Loads training records bound to incident, exposes as `_training_records` |
| `pdf_render.py` | NEW PDF section "Recurrence Prevention · Training Requalification" |
| `routes/safety.py` | Added 4th aftercare task `incident.aftercare.training_14d` to the WV/PI fan-out |

## Backward compatibility
- Legacy 10 training records continue to work unchanged · `source_incident_id=None` simply means "not incident-driven".
- HR portal endpoints unchanged.
- PDF block GATED on field presence — legacy incidents render without it.

## Five-question scorecard
| # | Question | Answer | Evidence |
|---|---|:---:|---|
| 1 | Can an employee be assigned retraining? | ✅ | Existing tasks + CAPAs · 14d aftercare task created automatically on WV/PI |
| 2 | Can completion be tracked? | ✅ | `safety_training_records.completed_date` |
| 3 | Can completion be verified? | ✅ | `created_by_name` + `created_by_role` (iter353a) |
| 4 | Can completion be shown on PDFs? | ✅ | NEW "Recurrence Prevention · Training Requalification" block on incident PDF |
| 5 | Can completion be tied to an incident? | ✅ | NEW `source_incident_id` field on training record |

## Sign-off
GREEN. Training defensibility is now end-to-end. Whether an employee was actually retrained after Incident Y is a single MongoDB query AND a single line on the printable PDF.
