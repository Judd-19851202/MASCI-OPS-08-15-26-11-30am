# Rejection Workflow — Certification

_Phase V.4 · 2026-05-29 · governance · NOT implementation._

## 1 · Rejection contract

A rejection is a **first-class audit event**. It must:

1. Require a non-empty reason ≥ 8 characters (server-enforced).
2. Stamp `rejected_by_user_id`, `rejected_by_role_value`, `rejected_by_role_label`, `rejected_at_utc`, `rejection_reason`, `report_version_at_rejection`.
3. Append an entry to `daily_report_review_events` with `action="reject"`.
4. Recompute `audit_envelope_sha256` (next event's `_before` matches this event's `_after`).
5. Surface the reason to the foreman via the next mount of `/daily/new` for that DR (recovery banner style).
6. Stay forever readable to the foreman (own DR) and to any super-tier user in scope.
7. Never delete the report. Never overwrite previously saved fields.

## 2 · Reason catalog (operator-curated · suggested baseline)

| Reason ID | Display label | Example use |
|---|---|---|
| `missing_production` | Missing production rows | Foreman submitted with no production captured but the DR shows paving activity |
| `missing_photos` | Missing photos | Photo count below project-required minimum |
| `incorrect_manpower` | Manpower count looks wrong | Headcount mismatch with sign-in sheet |
| `missing_delay_detail` | Delay detail incomplete | Weather YES but no Weather row OR Lost Hours not filled |
| `safety_documentation_incomplete` | Safety documentation incomplete | JHA / Toolbox / Pre-Op missing |
| `wrong_project_or_date` | Wrong project or date | Foreman picked the wrong job from the picker |
| `other` | Other (use the notes field) | Free-text reason · still ≥ 8 chars |

UI presents these as a select + a notes field. The notes field is what gets stored as `rejection_reason`. The reason ID is stored separately as `rejection_reason_id` for future analytics.

## 3 · Foreman recovery flow

```
foreman opens /daily/new for the rejected DR
↓
recovery banner renders:
  ┌────────────────────────────────────────────────────────────┐
  │ ⚠ Returned for revision · {reviewer_name} · {reviewer_role}│
  │                                                            │
  │   "Add a Weather delay row with the rain start/stop times"│
  │                                                            │
  │   [ Acknowledge & Fix ]     [ View Review History ]        │
  └────────────────────────────────────────────────────────────┘
↓
foreman taps Acknowledge & Fix
↓
DR transitions REJECTED → RETURNED_FOR_REVISION
↓
limited DRAFT-edit surface unlocks (per REPORT_LIFECYCLE_DOCTRINE §3)
↓
foreman fixes the cited deficiency · adds the missing row · taps Submit
↓
DR transitions RETURNED_FOR_REVISION → SUBMITTED
↓
report_version += 1 · resubmitted_at stamped · new event row appended
```

## 4 · Server-side validation on reject

```python
def validate_rejection(payload: dict) -> tuple[bool, str | None]:
    reason = (payload.get("reason") or "").strip()
    if len(reason) < 8:
        return False, "rejection_reason_too_short"
    if len(reason) > 2000:
        return False, "rejection_reason_too_long"
    reason_id = payload.get("reason_id")
    if reason_id and reason_id not in CATALOG:
        return False, "rejection_reason_id_unknown"
    return True, None
```

Returns `400 Bad Request` with code in the error body on failure.

## 5 · What rejection does NOT do (forbidden behaviors)

| Forbidden | Why |
|---|---|
| Delete the DR | Frozen Archive doctrine (M1 Option C) |
| Auto-create an RFI | RFI module out of scope for V.4 |
| Auto-create a Schedule entry | Schedule module out of scope for V.4 |
| Notify the foreman by email / SMS | Operator scope: notifications NOT in V.4 |
| Lock the DR permanently | Rejection is a returnable state, not a terminal state |
| Overwrite any previously-stored field | The DR's payload is preserved verbatim |
| Reveal the reviewer's identity beyond name + role | No reviewer phone / email surfaced to foreman |
| Allow re-rejection without a re-submission in between | State machine enforces SUBMITTED → UNDER_REVIEW → REJECTED, never REJECTED → REJECTED |
| Allow rejection by a non-super-tier role | `APPROVAL_PERMISSION_MATRIX.md §1` gate |

## 6 · Repeated rejection cycles

The state machine permits an unlimited number of revision cycles. Each cycle:

- Bumps `report_version`.
- Appends a fresh `{action:"reject"}` event row.
- Appends a fresh `{action:"resubmit"}` event row.
- Recomputes the envelope hash.

For pilot, the operator may want to add a soft warning to the reviewer surface after the 3rd rejection cycle ("This DR has been returned 3 times — consider a phone call before another reject"). That UX is **NOT in scope today** but is documented here so the future implementer doesn't forget the analytics hook.

## 7 · Reading the rejection history

`GET /api/daily-reports/{id}/review-events` returns the full append-only timeline:

```jsonc
[
  { "action": "submit",  "occurred_at_utc": "...", "actor_name_snapshot": "John Foreman", "actor_role_label": "Foreman", ... },
  { "action": "start_review", "occurred_at_utc": "...", "actor_name_snapshot": "Mary Super", "actor_role_label": "Superintendent", ... },
  { "action": "reject", "occurred_at_utc": "...", "actor_name_snapshot": "Mary Super", "actor_role_label": "Superintendent", "reason": "Add a Weather delay row with the rain start/stop times", ... },
  { "action": "return_for_revision", "occurred_at_utc": "...", "actor_name_snapshot": "John Foreman", "actor_role_label": "Foreman", ... },
  { "action": "resubmit", "occurred_at_utc": "...", "actor_name_snapshot": "John Foreman", "actor_role_label": "Foreman", ... },
  { "action": "approve", "occurred_at_utc": "...", "actor_name_snapshot": "Mary Super", "actor_role_label": "Superintendent", ... }
]
```

PDFs of LOCKED_RECORD DRs that went through one or more revision cycles MUST include a "Review History" appendix listing the same timeline (operator-readable format) so external auditors (CEI · DOT · FAA · owner) can see the full chain.

## 8 · Doctrine compliance

- ✅ **Append-only · forever auditable** — every action is an event row.
- ✅ **No silent deletion** — DR never destroyed.
- ✅ **No silent edit** — fields preserved · hash continuity proves no tampering.
- ✅ **Reason required · server-enforced** — minimum 8 chars.
- ✅ **No notification side effect** — operator scope.
- ✅ **Foreman 9-step contract preserved** — RETURNED_FOR_REVISION surface uses the same form.
- ✅ **External-auditor visibility** — Review History appendix on the PDF.

## 9 · Stop condition

🛑 Certification only. No endpoint coded. Implementation begins only after operator review.

_End of REJECTION_WORKFLOW_CERTIFICATION.md._
