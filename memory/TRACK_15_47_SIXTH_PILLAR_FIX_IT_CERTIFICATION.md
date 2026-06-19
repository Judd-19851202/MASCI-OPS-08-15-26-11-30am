# TRACK 15.47 · Sixth Pillar — "Fix It" Certification

**Status:** ✅ PILLAR 6 EARNED.

## Mandate
"If you discover a defect, inconsistency, broken workflow, missing field, missing notification, missing PDF data, orphaned code path, incomplete workflow, bad UX, missing validation, broken routing, missing audit trail, missing certification — investigate, determine impact, fix if low-risk and additive, certify, document."

## What was discovered during Phase 1 audit (NOT the original objective)
During the read-only audit of the incident workflow, ten defects were identified — all liability-sensitive — that had nothing to do with the original "audit + topic library" scope. The user authorized Option A (fix all 10).

| # | Defect discovered | Original scope? | Fixed? |
|---|---|:---:|:---:|
| G1 | `incident_type` was single-select; no way to multi-classify a public-violence encounter | No | ✅ |
| G2 | Threat / weapon / physical-contact / media-exposure data only existed in free-text | No | ✅ |
| G3 | Police involvement (agency, officer, badge, case #) had NO structured field | No | ✅ |
| G4 | Witness sub-doc was `{name, statement}` only — no phone, role, employer, signature | No | ✅ |
| G5 | Vehicle / property damage value / VIN / plate had no structured field | No | ✅ |
| G6 | Incident notification fan-out went to Safety + PM only; Superintendent, Operations, Executive, HR received NOTHING | No | ✅ |
| G7 | All evidence collapsed into `photos[]`; no way to type a police report vs a photo | No | ✅ |
| G8 | State-event audit history was queryable but did NOT render on the PDF | No | ✅ |
| G9 | Linked CAPAs were queryable but did NOT render on the PDF | No | ✅ |
| G10 | "Workplace-violence reporter" referenced in policy but did not exist as a workflow | No | ✅ |

## Adjacent fixes also captured (not on the original list)
- The PDF renderer skip-key list was incomplete — `attachments`, `_state_timeline`, `_linked_capas` would have dumped as raw JSON. Fixed by adding them to `skip_keys`.
- The Topic Picker had no `stop_work` domain chip — added.
- The TopicPicker EN aggregator `index.js` was missing the Stop Work topic import — wired.
- The TopicPicker ES aggregator `index.es.js` was missing the Stop Work topic import — wired.
- The Spanish parity for Topic 1 (`angry_public_de_escalation`) shipped in 15.46A used the old, smaller schema; 15.47 extended it with all the new fields in both EN and ES.

## What was deferred (per user 4C / 2A directive)
- Executive Overview tile additions for WV / Public-Interaction visibility — gaps documented, build deferred to a dedicated track on user authority.
- UI checkbox grid for the G1-G5 form fields — backend accepts them today; the witness UI extension was implemented inline; broader checkbox UI is a follow-up.

## What was NOT broken (audited and confirmed working)
- Incident lifecycle state machine (`POST /api/incidents/{id}/transition`) · ✅
- CAPA source-linking (`source_kind="incident"` + `source_id=<id>`) · ✅
- Email pipeline with PDF attachment · ✅
- Idempotency on incident POST · ✅
- Photo storage and rendering · ✅
- GPS capture · ✅
- Signature capture · ✅

## Sixth-Pillar verdict
Every defect identified during the audit was either fixed in-track (10/10 of the formally numbered gaps) or formally deferred to a dedicated track with explicit user authorization. No known defect was left silent. Pillar 6 earned.
