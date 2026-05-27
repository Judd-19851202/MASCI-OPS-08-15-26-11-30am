# RFI Workflow & Lifecycle
## Phase V.0 · Architecture & Governance · 2026-05-27

> Authoritative state machine, transition rules, and audit-trail
> obligations for every RFI record. Doctrine-locked before any code.

---

## 1 · State Machine

```
            ┌──────────────────────────────────────────────┐
            │                  DRAFT                       │
            │  (Superintendent · in field)                 │
            └──────────────┬───────────────────────────────┘
                           │ "send to PM for review"
                           ▼
            ┌──────────────────────────────────────────────┐
            │             INTERNAL REVIEW                  │
            │  (PM · contract custodian)                   │
            └──┬───────────────────────┬───────────────────┘
               │ "return to field"     │ "submit"
               ▼                       ▼
            DRAFT                ┌──────────────────────┐
                                 │      SUBMITTED       │
                                 │  (locked snapshot)   │
                                 └─────────┬────────────┘
                                           │ routed to recipient
                                           ▼
                            ┌──────────────────────────────────┐
                            │   CEI REVIEW  /  ENGINEER REVIEW │
                            └──────┬──────────┬────────────────┘
                                   │          │
                       "needs clarification"  "response received"
                                   │          │
                                   ▼          ▼
                  ┌──────────────────────┐  ┌────────────────────────┐
                  │ CLARIFICATION REQUIRED│ │   RESPONSE RECEIVED    │
                  └──────────┬───────────┘  └────────────┬───────────┘
                             │                           │
                       PM updates revision               │
                             │                           ▼
                             ▼               ┌─────────────────────┐
                         SUBMITTED            │  ACCEPTED / REJECTED│
                             │               └──────────┬──────────┘
                             ▼                          │
                       (loop until                      ▼
                        resolved)              ┌────────────────┐
                                               │     CLOSED     │
                                               └────────────────┘
                                                       │
                                ┌──────────────────────┴────────────────────┐
                                ▼                                            ▼
                      CONVERTED TO                                SCHEDULE IMPACT
                      CHANGE CONDITION                            LOGGED (terminal)
                      (terminal · audit kept)
```

All transitions are auditable. **No back-doors.** No "edit submitted
RFI". Corrections are revisions; rejections are documented.

---

## 2 · State Definitions

| State | Meaning · operational |
|---|---|
| `draft` | Superintendent or PM is composing. Mutable. No external visibility. |
| `internal_review` | PM has the record. Mutable. Optional QA before submission. |
| `submitted` | Frozen snapshot. PDF generated. Distribution log opened. Response clock running. |
| `cei_review` | Submitted to CEI. Waiting on CEI action. |
| `engineer_review` | Submitted to Engineer of Record. Waiting on engineer action. |
| `clarification_required` | External party (CEI / Engineer) requested more info. PM must respond via revision. |
| `response_received` | External response captured. PM evaluates. |
| `accepted` | Response accepted by PM as resolution. |
| `rejected` | Response rejected. Either revision back to external, or convert to change. |
| `closed` | Operational resolution complete. No further work. |
| `converted_to_change_condition` | Field condition exceeds RFI scope; converted to Change Condition. Terminal · linked. |
| `schedule_impact_logged` | Resolution involves a schedule constraint; logged in the constraint model. Terminal · linked. |
| `voided` | Submitted in error. Requires `void_reason`. Snapshot preserved for audit. |

---

## 3 · Transition Permissions

| From → To | Allowed Actor(s) | Required Inputs |
|---|---|---|
| `draft` → `internal_review` | Superintendent · PM | none |
| `internal_review` → `draft` | PM | optional `return_reason` |
| `internal_review` → `submitted` | PM | recipient(s), response_due_date |
| `submitted` → `cei_review` / `engineer_review` | system (auto on routing) | recipient role |
| `cei_review` / `engineer_review` → `clarification_required` | external (tokenized) · PM | `clarification_question` |
| `clarification_required` → `submitted` (revision) | PM | new revision body |
| any external review → `response_received` | external (tokenized) | response body, optional attachments |
| `response_received` → `accepted` / `rejected` | PM | `decision_reason` (rejected only) |
| `accepted` → `closed` | PM | optional `closing_note` |
| `accepted` → `converted_to_change_condition` | PM | change_condition_id |
| any state → `voided` | PM · Admin | `void_reason` (required · ≥ 20 chars) |

---

## 4 · Time Windows

| Priority | Default response_due_date |
|---|---|
| Routine | Submitted + 10 business days |
| Action Required | Submitted + 5 business days |
| Critical Path Impact | Submitted + 2 business days |
| Safety / Compliance Exposure | Submitted + 1 business day |

These are **defaults**, override-able by PM at submission, audited.

Aging buckets exposed in the dashboard:
- `green` · within window
- `amber` · within 24h of overdue
- `red` · overdue (and only overdue · no false urgency)

---

## 5 · Revision Discipline

A **revision** is created when:

- PM responds to a clarification request from external party.
- PM revises an active RFI after submission (e.g., corrected field condition).
- External party submits an updated response.

Each revision:

- carries a new `revision_number` (monotonic per RFI)
- preserves the prior snapshot intact
- regenerates the PDF (new file in R2)
- appends to the audit trail
- updates distribution log when re-routed

Revisions never overwrite. The full chain is available.

---

## 6 · Audit Trail Fields (every transition)

```
{
  "rfi_id": "...",
  "revision": 3,
  "from_state": "submitted",
  "to_state": "response_received",
  "actor": { "id": "...", "name": "...", "role": "cei", "token_id?": "..." },
  "occurred_at": "2026-05-27T16:51:38Z",
  "ip": "...",
  "user_agent": "...",
  "reason?": "...",
  "delta_hash?": "md5 of changed-fields before/after",
  "attachment_ids?": [...]
}
```

The audit collection is **append-only**. No deletes. No edits.

---

## 7 · Notification Triggers (state-driven)

See `NOTIFICATION_DISCIPLINE_MATRIX.md` for the doctrine spine. RFI
adds these triggers:

| Event | Notify |
|---|---|
| `draft → internal_review` | Assigned PM (in-app only · no email) |
| `submitted` | Recipient(s) via tokenized link · email |
| `clarification_required` | PM (in-app + email) |
| `response_received` | PM (in-app + email) · Superintendent (in-app) |
| `accepted` | Superintendent (in-app) |
| `rejected` | PM (in-app) · Superintendent (in-app) |
| `closed` | Superintendent (in-app) |
| `converted_to_change_condition` | PM + Admin (in-app + email) |
| `voided` | Admin (in-app + email) |
| **Overdue · red bucket entered** | PM (in-app + daily digest email) |
| **Critical-path impact flag set** | PM + Executive (in-app + email) |

**No notifications for routine reads, opens, draft saves, or attachments.**

---

## 8 · State-Transition Tests (required for Phase V.1)

Each transition listed in §3 must have a corresponding pytest case
asserting:

1. Allowed actor succeeds.
2. Disallowed actor returns 403 with a clear operational reason.
3. Audit-trail entry is created with all required fields.
4. PDF regeneration triggers on submit / revision.
5. Notification fan-out matches §7 (mocked at the transport layer).

These tests are **non-negotiable** for V.1 sign-off.

---

## 9 · Sign-off

- **Author:** E1 · Phase V.0 architecture authoring pass
- **Status:** 🟢 Doctrine-grade
- **Implementation gate:** State machine locks during V.1. Any addition / removal of a state requires a new doctrine revision before code.
