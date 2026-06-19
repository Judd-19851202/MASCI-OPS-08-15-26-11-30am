# TRACK 15.49 · Witness Follow-Up Certification

**Status:** ✅ CERTIFIED with one documented backlog item.

## The witness lifecycle question
Can MASCI prove the following six months after an incident?
| Question | Answer | Evidence |
|---|:---:|---|
| Witness contacted | ✅ YES (via task chain) | `incident.aftercare.witness_72h` task owned by Safety with T+72h due date |
| Witness statement received | ✅ YES | Statement is captured in the witness sub-doc on the incident; updates write to the same record |
| Witness statement updated | ✅ YES | Witness sub-doc is mutable via `PUT /api/incidents/{id}` (existing endpoint) |
| Witness unavailable | 🟡 PARTIAL | No dedicated field. Documented as backlog B-02 below. |
| Witness declined participation | 🟡 PARTIAL | Same. Documented as backlog B-02. |

## What 15.49 delivers
- **`incident.aftercare.witness_72h`** task auto-issues to Safety on every WV/PI incident.
- Due date: T+72 hours from incident creation.
- Description prompts Safety to: confirm phone/email still reaches each witness · obtain signed statements where not yet collected · mark unavailable/declined witnesses · update the witness rows on the incident.
- Tasks linked via `source_module=safety.incidents` + `source_record_id=<incident_id>`.
- Surfaces on the PDF Aftercare Follow-Up Actions block.

## What the existing platform already supports (Track 15.47 G4 · NOT new)
- Witness sub-doc carries: name, role, witness_type (employee/subcontractor/public/police/other), phone, email, employer, statement, signature.
- PDF renders multi-column witness table including all contact info.

## Backlog item B-02 · Witness status enum
**Gap:** No structured field for `witness_status` ∈ {pending · contacted · statement_received · unavailable · declined}. Today the foreman/safety adds this in free-text statement.
**Smallest additive solution:** add `status` to the witness sub-doc (one string field), surface as a dropdown in the witness UI row, render as a small chip in the PDF witness table.
**Estimate:** ~30 minutes build + cert.
**Why deferred:** This track's directive was "smallest additive solution" — the task chain alone closes the operational gap by ensuring Safety actually does the follow-up. The status enum is a useful classification but not a defensibility-blocker (the witness phone/email captured per 15.47 G4 is the chain-of-custody piece). Recommend Track 15.50.

## Sign-off
GREEN with documented backlog. The witness follow-up chain is provably enforced because the 72-hour Safety task is auto-issued, due-dated, and surfaced on the defensibility PDF. Witness contact info (phone/email/employer) captured at incident creation is preserved indefinitely.
