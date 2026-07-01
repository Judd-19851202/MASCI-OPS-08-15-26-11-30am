# Track 19.15 · 05 · Case Lifecycle Architecture

## Status ladder

```
NEW
  ↓ (auto on submit)
INITIAL_FIELD_REPORT
  ↓ (Safety opens)
SAFETY_REVIEW
  ↓ (Safety escalates as needed)
INVESTIGATION_OPEN
  ↓
EVIDENCE_COLLECTION
  ↓
REGULATORY_REVIEW  (only if OSHA / DOT / EPA implicated)
  ↓
CORRECTIVE_ACTIONS
  ↓
MANAGEMENT_REVIEW
  ↓
CLOSED
  ↺ REOPENED (if new evidence surfaces)
```

## Per-status contract

| Status | Owner | Required fields to enter | Allowed actions | Dashboard bucket | Notifications | PDF behavior | Audit events |
|---|---|---|---|---|---|---|---|
| NEW | platform | none | auto-transitions on submit | none | none | not generated yet | `incident.created` |
| INITIAL_FIELD_REPORT | field / supervisor | field facts + reporter sig | supervisor sign | Field Inbox | Safety + PM | draft PDF (sections 1-9) | `incident.field_submitted` |
| SAFETY_REVIEW | Safety | field data complete | classify, escalate | Safety Queue | HR (if injury), Ops (if visible) | draft PDF v2 | `incident.safety_opened` |
| INVESTIGATION_OPEN | Safety | investigation lead assigned | add notes, request evidence | Safety Active Cases | monthly digest to Exec | investigation appendix appears | `incident.investigation_opened` |
| EVIDENCE_COLLECTION | Safety | evidence checklist | upload evidence | Safety Evidence | none | evidence section renders | `incident.evidence_added` |
| REGULATORY_REVIEW | Safety | agency contact log | agency notifications | Safety Regulatory | Exec + Legal | regulatory subsection renders | `incident.regulatory_review` |
| CORRECTIVE_ACTIONS | Safety + Management | CA list with owners + dates | assign / track CAs | CA Dashboard | Owners + PM | CA section renders | `incident.corrective_action_created` |
| MANAGEMENT_REVIEW | Management | management review notes | approve / reopen | Exec Queue | Exec | approval sig required | `incident.management_review` |
| CLOSED | platform | all above complete | reopen | Closed Archive | Safety + PM | final PDF locked | `incident.closed` |
| REOPENED | Safety | reopen reason | reset to Safety Review | Safety Queue | Original stakeholders | draft PDF re-issued | `incident.reopened` |

## Permissions

- Only Safety can advance from `SAFETY_REVIEW` onward.
- Only Management can advance from `MANAGEMENT_REVIEW` to `CLOSED`.
- Field and PM see read-only case status after `INITIAL_FIELD_REPORT`.
- HR gains read access when incident type is Injury / Illness or Workplace Violence.

## Preservation

The existing `POST /incidents/{id}/transition` and `GET /incidents/{id}/lifecycle` endpoints (server.py:2532-2533) already scaffold this. Track 19.16 extends the state machine without new routes.
