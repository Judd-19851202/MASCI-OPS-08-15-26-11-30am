# TRACK 15.49 · Employee Welfare Follow-Up Certification

**Status:** ✅ CERTIFIED with one documented backlog item.

## What 15.49 delivers for employee welfare tracking
At incident creation for any WV/PI-classified event, an HR-owned task auto-issues:
- **`incident.aftercare.welfare_24h`** — "24-hour welfare check-in with affected employee"
- Priority: Critical (WV) or High (PI)
- Due: T+24 hours
- Carries `source_module=safety.incidents` + `source_record_id=<incident_id>` so the task is anchored to the incident record forever.
- Description prompts HR to confirm: physical condition · psychological well-being · medical follow-up scheduled · employee preferences for next-day attendance · and to document outcome on the incident as a state-event note.

## What the existing platform already supports (verified, NOT new)
| Capability | Already exists | Where |
|---|:---:|---|
| Employee condition (initial) | ✅ | `treatment_provided`, `injury_nature`, `body_part`, `sent_home` on incident schema |
| Return-to-work status | ✅ | `sent_home` boolean + state-event transitions on lifecycle |
| Medical restrictions | ✅ (free text) | `treatment_provided` field |
| Continuing concerns | ✅ | Description + state-event notes via `POST /api/incidents/{id}/transition` |
| Additional statements | ✅ | Witness sub-doc supports updates · medical attachments via G7 |
| Additional evidence | ✅ | `attachments[]` supports kind=`medical` + others (G7) |

## What 15.49 adds on top
1. **Time-fused 24-hour task** ensures the welfare check is owned, due-dated, and tracked.
2. **PDF surface** — the Aftercare Follow-Up Actions block now shows the welfare check status (Open / In Progress / Completed) on the printed incident PDF.
3. **Notification chain** — HR receives both a `task.assigned` and a `incident.aftercare.welfare_24h` event in the bell.

## What is NOT built (and why)
- Dedicated "welfare check note" sub-doc on the incident → NOT BUILT.
  - Reason: existing `state_events` already supports note-with-actor-and-timestamp via the lifecycle endpoint. HR documents outcome there. Adding a dedicated sub-doc would duplicate state.
- Dedicated "return-to-work medical clearance form" → NOT BUILT.
  - Reason: existing attachments[] with `kind=medical` covers it.

## Backlog item documented
- **B-01 · Welfare note convenience UI**: today HR must open the lifecycle endpoint to add a note. A 1-line "add welfare note" inline action on the incident view would close a usability gap. NOT BUILT this track per smallest-additive directive — documented as a Track 15.50 candidate.

## Sign-off
GREEN with documented backlog. Employee welfare is now provably tracked because the 24-hour HR task is auto-issued, due-dated, and surfaced on the defensibility PDF. Whether HR ACTS on it remains an organizational discipline question, not a platform gap.
