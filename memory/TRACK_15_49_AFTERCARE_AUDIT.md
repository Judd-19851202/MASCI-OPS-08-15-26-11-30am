# TRACK 15.49 · Phase 1 · Incident Aftercare Audit

**Status:** ✅ AUDIT COMPLETE · gaps closed in-track.

## The five timing checkpoints — pre-15.49 vs post-15.49

| When | Pre-15.49 (what happened automatically) | Post-15.49 |
|---|---|---|
| At incident creation (T+0) | Safety + PM notification. WV/PI also Superintendent + Operations + Executive + HR notifications + WV review CAPA (from 15.47). | Same · unchanged. |
| **T+24h** | ❌ Nothing automated. Welfare check left to memory. | ✅ Auto-task to HR · `incident.aftercare.welfare_24h` · Critical priority. |
| **T+72h** | ❌ Nothing automated. Witness contact lost if not chased manually. | ✅ Auto-task to Safety · `incident.aftercare.witness_72h` · High priority. |
| **T+7 days** | ❌ Nothing automated. CAPA progress + police-report chase + insurance/legal hand-off left to memory. | ✅ Auto-task to Safety · `incident.aftercare.investigator_7d` · High priority. |
| After CAPA completion | Manual closure. | Same · unchanged (CAPA closure is owner-responsibility). |
| After incident closure | State transition logged in `incident_state_events`. PDF carries closure timestamp + actor + reason. | Same · unchanged. |

## Implementation
- File: `backend/routes/safety.py` · the existing G6/G10 fan-out block extended with a 3-task aftercare loop.
- Tasks created via existing `emit_task_and_notification` (reuses certified path · no new collection).
- Tasks carry `source_module="safety.incidents"`, `source_record_id=<incident_id>`, and a NEW optional `task_key` field (added to `_TaskService.create` for surfacing on the PDF).
- PDF enrichment helper `lib/incident_pdf_enrichment.py` extended to load these tasks.
- PDF renderer `_render_generic` extended with "Aftercare Follow-Up Actions" block.

## Trigger conditions
The aftercare chain fires ONLY when the incident carries Public-Interaction or Workplace-Violence flags — same gating as the G6/G10 fan-out:
- Any of `classifications` ∈ {Workplace Violence, Physical Assault, Weapon Displayed, Weapon Used} → WV-grade aftercare
- Any of `classifications` ∈ {Public Interaction, Verbal Confrontation, Threat, Harassment, Physical Contact} → PI-grade aftercare
- Or boolean flags: `physical_assault`, `weapon_displayed`, `weapon_used`, `arrest_made`, `threat_made`, `physical_contact`

For a typical injury or property damage report (not violence-related), the chain does NOT fire — no operator-effort cost on routine incidents.

## Best-effort guarantee
Each of the 3 aftercare task emits is wrapped in `try/except`. A misconfigured assignee_role does NOT block the incident write or any of the other 9 notifications. The system fails open for safety.

## Verified live · synthetic test incident
- 3 NEW aftercare tasks created with correct due-date offsets (+24h HR · +72h Safety · +7d Safety).
- 6 NEW notifications fan-out (3 task.assigned + 3 topical: `incident.aftercare.welfare_24h` / `incident.aftercare.witness_72h` / `incident.aftercare.investigator_7d`).
- PDF rendered with "Aftercare Follow-Up Actions" block · 3 new rows visible · all kinds and due dates correct (verified via AI content extraction).

## Sign-off
GREEN. The aftercare chain closes the gap between "incident reported" and "incident truly closed."
