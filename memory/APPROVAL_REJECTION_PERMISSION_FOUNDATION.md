# Approval / Rejection Permission Foundation

_Phase V.2 · 2026-05-29 · permission foundation only · no workflow implementation._

> **Operator directive (verbatim):** _"Prepare permission foundation
> only. Do not implement approval/rejection workflow unless
> separately authorized."_

This document is a **foundation specification**. No backend route, frontend capability, or audit collection changes today.

## 1 · Permission matrix (future)

| Role (canonical) | Create draft | Submit DR | Review / Approve | Review / Reject | Override |
|---|---|---|---|---|---|
| `leadman` | (if authorized) | ❌ | ❌ | ❌ | ❌ |
| `foreman` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `superintendent` | ✅ | ✅ | ✅ (assigned projects) | ✅ (assigned projects · reason required) | ❌ |
| `sr_superintendent` | ✅ | ✅ | ✅ (assigned region / portfolio) | ✅ (assigned region · reason required) | ❌ |
| `admin` | ✅ | ✅ | ✅ | ✅ | ✅ (full override) |

## 2 · Audit contract (future)

Every approve / reject action must:

1. Append (not overwrite) to a new `daily_report_review_events` collection · append-only.
2. Stamp `reviewer_user_id`, `reviewer_role_value`, `reviewer_role_label`, `reviewed_at_utc`, `action ∈ {approve, reject}`, `project_number`, `daily_report_id`.
3. For `reject`: require non-empty `reason` (min ≥ 8 chars · operator can refine threshold).
4. Never delete prior events.
5. Never silently edit the Daily Report.
6. Mirror to `operational_links` so the timeline projector picks it up.

## 3 · Audit hash continuity (alignment with Wave-1C audit footer)

The DR PDF audit footer (`sha256` of the canonical envelope) MUST continue to drift on every approve / reject event so any rendered PDF carries a hash that proves the review state at time of print.

Approach (future implementation):
- Approve / Reject appends an event row but does **not** mutate the DR envelope.
- The PDF render-time hash should already incorporate the review event log via a deterministic `review_events_digest` sub-hash so the footer changes after each approve/reject event.

## 4 · Frontend capability primitive (future)

New file `lib/dailyReportReviewCapabilities.js` modeled after `poCapabilities.js`:

```js
getDailyReportReviewCapabilities(actor, project) => {
  "dr.draft.create":   true | false,
  "dr.submit":         true | false,
  "dr.review.approve": true | false,
  "dr.review.reject":  true | false,
  "dr.override":       true | false,
}
```

- Portal context FIRST gate.
- Canonical `role_value` SECOND gate.
- Project scope (`compute_fl_scope(actor)`) THIRD gate.
- Authority Mismatch Probe baseline extended on implementation day.

## 5 · Backend endpoints (future · placeholders)

```
POST /api/daily-reports/{id}/review/approve
POST /api/daily-reports/{id}/review/reject       (body: {reason})
GET  /api/daily-reports/{id}/review-events
```

All admin-or-super-tier gated. All append-only. All audit-logged.

## 6 · Forbidden behaviors (must NEVER occur)

- ❌ Silent edit of a Daily Report's content during review.
- ❌ Hard delete of a Daily Report.
- ❌ Reject without a reason.
- ❌ Approve / reject by Leadman or Foreman.
- ❌ Approve / reject crossing project scope without admin override.
- ❌ Skipping the operational_links bridge entry.
- ❌ Workflow changes that increase foreman burden (Doctrine Lock #1).

## 7 · What is NOT in scope today

- ❌ No backend endpoint additions.
- ❌ No frontend capability primitive yet.
- ❌ No collection creation.
- ❌ No portal hub UI changes.
- ❌ No PM Exposure Tile wiring.

## 8 · Stop condition

🛑 This document is preparation only. Implementation begins only after operator authorization in a future directive.

_End of APPROVAL_REJECTION_PERMISSION_FOUNDATION.md._
