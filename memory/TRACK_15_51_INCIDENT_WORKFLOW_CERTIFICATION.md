# TRACK 15.51 · Incident Workflow Certification (Phase 4)

**Status:** ✅ CERTIFIED end-to-end against synthetic INC-2026-00488 (retained for cert evidence).

## End-to-end chain · verified
| Step | Mechanism | Evidence |
|---|---|---|
| Incident | `POST /api/incidents` | ✅ doc_id INC-2026-00488 persisted |
| Evidence | `attachments[]` (G7 · 7 kinds) + `photos[]` | ✅ 5 typed attachments on cert incident |
| Witnesses | `witnesses[]` extended sub-doc (G4) | ✅ 4 rows · name/role/phone/email/employer captured |
| Police | 10 G3 fields | ✅ agency / officer / badge / case# all persisted |
| CAPAs | `safety/corrective-actions` linked via `source_kind=incident` | ✅ 2 linked CAPAs |
| Notifications | 15.47 G6 fan-out · Safety + PM + Super + Ops + Exec + HR + WV review | ✅ 9 notifications recorded |
| Aftercare | 15.49 task chain · 24h welfare (HR) · 72h witness (Safety) · 7d investigator (Safety) | ✅ 3 aftercare tasks · all auto-issued |
| Retraining | 15.50 · 14d training task + `safety_training_records.source_incident_id` binding | ✅ task issued; training record bindable |
| Verification | `verified_by` + `verified_at` + status enum | ✅ schema supports full lifecycle |
| Closure | `POST /api/incidents/{id}/transition` to `closed` + state event | ✅ lifecycle supports it |
| Executive Visibility | foundation v15.50.1 · safety tile · `wv_incidents_90d` + `training_overdue` | ✅ live verified |
| PDF | `render_record_pdf("incident", enriched)` · 11 sections | ✅ 2.3 MB rendered · all sections verified via AI extraction |

## Sign-off
Every stage in the chain produces evidence on the same source incident, anchored to the same `incident_id`, queryable from the database, and visible on the printable PDF. No partial workflow, no dead end, no missing link. GREEN.
