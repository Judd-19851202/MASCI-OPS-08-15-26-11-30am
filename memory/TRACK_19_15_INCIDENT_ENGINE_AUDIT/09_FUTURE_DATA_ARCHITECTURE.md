# Track 19.15 · 09 · Future Data Architecture

## Decision: extend existing collection, DO NOT split

The current `incidents` collection carries all field data and is included in every audit / notification pipeline. Splitting it would create a destructive migration risk.

**Recommendation:** keep `incidents` as the single source-of-truth document. Add sub-collections for the new *case-management* domain only. Historical records remain identical to today.

## Collections

### Existing (untouched)
- `incidents` — primary field-submitted incident record. Every existing field key preserved.

### New sub-collections (additive · Track 19.16)
- `incident_case_state` — per-incident case-lifecycle status + owner + assignment history. Keyed on `incident_id`.
- `incident_investigation_notes` — Safety-authored narrative + structured findings. `incident_id`, `author`, `note`, `created_at`.
- `incident_corrective_actions` — CA list with owner, due date, status, close-out signature. `incident_id`, `owner`, `description`, `due_at`, `status`, `closed_at`.
- `incident_evidence` — evidence catalog metadata (upload metadata already lives in R2; this indexes it with class/kind/hash/retention). `incident_id`, `kind`, `class`, `storage_url`, `hash`, `uploaded_by`, `retention_flag`.
- `incident_regulatory_log` — agency contact log (OSHA / EPA / DOT / state / utility owner). `incident_id`, `agency`, `contact`, `contacted_at`, `outcome`.
- `incident_case_timeline` — reconstructed timeline events (both auto and manually added). `incident_id`, `event_at`, `event_kind`, `description`.

### Reused (unchanged)
- Existing state-event log (server.py:2532 endpoint) — provides audit trail; no schema changes required, just new event kinds.
- `email_routing_v2` config — extended with per-type routing rules, no new collection.

## Preservation guarantees

- Every field currently written to `incidents` — preserved.
- Historical incident PDFs render from `incidents` alone (sections 1–9 + 14). New sub-collections enable sections 10–13.
- No destructive migration. No renames. No deletes.
- `X-Safety-Token` scope (server.py:2520) — extended to cover new sub-collections.

## Migration plan

- Track 19.16 CREATES sub-collections (empty).
- Every new incident from Track 19.17 onward writes to both `incidents` (field data) and the sub-collections (as Safety / Management fill them in over the case lifetime).
- Historical incidents show sections 1–9 + 14 in the new PDF; sections 10–13 render "Not investigated in this system" placeholder + link to any legacy investigation record.
