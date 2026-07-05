# DR-UNIFY-004 · Safety Certification

**Claim:** Safety fields, incident/injury reporting, JHA/JHP, and
excavation gates behave identically.

## Preserved surfaces

- `safety_incidents_today`, `injuries_reported`, `incident_notes`,
  `safety_notified` — all preserved on `daily_reports`.
- Excavation activity gate — unchanged.
- JHA / JHP fields — unchanged.
- CAPA and investigation workflows — unchanged (no changes this
  session).
- Safety Portal admin surface — unchanged (no changes this session).

## Composer behaviour

- DR-CUTOVER-002 composer **reads** safety flags to decide whether to
  **mention** safety in the summary. It never writes them.
- Lock test `test_composer_never_invents_a_safety_incident` — asserts
  no safety mention when both flags say "No".
- Lock test verifies safety appears in the summary only when at least
  one flag says "Yes".

## Regression suite

- `test_safety_context_cert.py`, `test_safety_escalation_fields.py`,
  `test_safety_meeting_cert.py`, `test_safety_forms_iter37.py`,
  `test_safety_portal_iter*.py` — untouched by this session's tracks
  (verified via grep for `safety` in changed files: no matches).

## No new safety fields required

- The summary section adds no safety-relevant fields.
- The Admin AI Configuration page does not touch safety data.

**Verdict:** Safety subsystem certified.
