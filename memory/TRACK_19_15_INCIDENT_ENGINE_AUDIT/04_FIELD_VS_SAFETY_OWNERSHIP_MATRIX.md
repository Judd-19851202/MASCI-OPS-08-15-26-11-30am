# Track 19.15 · 04 · Field vs Safety Ownership Matrix

## Doctrine

**Field captures facts. Safety investigates. Management decides. Platform routes.**

Field operators must NEVER be asked to make regulatory, legal, or compliance determinations.

## Ownership classification

### FIELD-OWNED (facts observed at scene)
- Date / time of incident
- Location (project + specific site coordinates)
- People involved (names, roles)
- Immediate observation of what happened
- Photos / video evidence
- Witness list + contact info
- Immediate actions taken by the field (called 911, moved equipment, cleared area)
- Weather / lighting / ground conditions at time of incident
- Equipment / vehicle unit numbers
- Utility ticket number (transcribed from ticket)

### SAFETY-OWNED (investigation)
- OSHA recordability determination
- OSHA reportability determination (fatal, hospitalization, amputation, loss of eye)
- Root cause classification
- Contributing factors
- Corrective actions (drafting + assigning + tracking)
- Investigation findings narrative
- Regulatory contact log (OSHA / EPA / DOT / state agency)
- Insurance claim ID + adjuster contact
- Workers Comp claim ID
- Police follow-up (report number, officer, disposition)
- Utility company follow-up (repair confirmation, invoice)
- Witness statement collection (Safety takes formal statements)
- Case closure determination

### MANAGEMENT-OWNED (decisions)
- Preventability determination
- Disciplinary decisions
- Operational changes (SOP updates, training requirements)
- Policy changes
- Final approval on high-visibility incidents

### PLATFORM-OWNED (system)
- Notification routing (Safety, PM, HR, Shop, Fleet, Exec)
- Audit trail (Trust Spine event log)
- Case status tracking + lifecycle transitions
- PDF generation per incident type
- Timeline reconstruction from timestamps
- Dashboards + analytics
- Historical record preservation

## What changes for the field operator

**REMOVED from the field flow** (moved to Safety case workspace):
- ❌ OSHA recordability checkbox
- ❌ Root cause classification
- ❌ Corrective action drafting
- ❌ Regulatory notification checkboxes (agency-notified? — moved to safety follow-up)

**KEPT in the field flow:**
- ✅ Immediate actions the field took
- ✅ Notifications the field made in the moment (called 911, called supervisor)

The field can flag observations ("I think this needs OSHA review") but does not make the determination.

## Legal defensibility

By separating field facts from safety determinations, MASCI defends against:
- Discovery challenges ("the field checkbox said not recordable, so you thought it wasn't recordable?" — the field is only ever asked to observe, not judge)
- Untrained-determination risk (an operator marking OSHA recordability without training)
- Inconsistent classification across projects

## Enforcement

Track 19.17 (field UI) MUST NOT render OSHA / regulatory / root-cause questions to the field operator. Track 19.18 (Safety case workspace) is the ONLY place these questions live.
