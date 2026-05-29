# Report Lifecycle Doctrine

_Phase V.4 · 2026-05-29 · governance · NOT implementation._

## 1 · Canonical states

```
DRAFT  →  SUBMITTED  →  UNDER_REVIEW  →  APPROVED  →  LOCKED_RECORD
                  ↓             ↓                            ↑
                  └─── REJECTED ─── RETURNED_FOR_REVISION ───┘
                              (back to SUBMITTED on resubmit)
```

| State | Semantic |
|---|---|
| **DRAFT** | Foreman is composing the report on the iPad. Lives in IDB. Server may have a partial / never-submitted shell only after the first explicit submit attempt. |
| **SUBMITTED** | Foreman has tapped Submit. Server holds the canonical envelope. Wave-2 idempotent submit guarantees at-most-once creation. |
| **UNDER_REVIEW** | A reviewer (super-tier) opened the report from their queue. `review_started_at` is stamped. Other reviewers still see it but cannot stomp the start event. |
| **APPROVED** | Reviewer affirmed the record. Approver name + role + UTC timestamp + report_version stamped. Audit envelope hash recomputed. |
| **REJECTED** | Reviewer returned the record with a reason. Foreman sees the reason in the recovery banner. |
| **RETURNED_FOR_REVISION** | Foreman acknowledges rejection. Resumes DRAFT-style editing on the SAME DR record (same `id`, same `report_number`). Cycle counter increments. |
| **LOCKED_RECORD** | Final immutable state. M1 Option C continues — DELETE returns 410. Amendments are the only way to change anything, and amendments create NEW records linked via `operational_links.relationship = "amends"`. |

## 2 · Immutability contract per state

| State | DR fields editable | Photos editable | Production/Constraints editable | Review fields editable |
|---|---|---|---|---|
| DRAFT | ✅ | ✅ | ✅ | n/a |
| SUBMITTED | ❌ | ❌ | ❌ | ❌ |
| UNDER_REVIEW | ❌ | ❌ | ❌ | reviewer can fill `review_notes_draft` (server-side scratchpad · not on the audit envelope) |
| REJECTED | ❌ | ❌ | ❌ | reviewer's `rejection_reason` is appended once and cannot be edited |
| RETURNED_FOR_REVISION | ✅ (limited · see §3) | ✅ | ✅ | ❌ |
| APPROVED | ❌ | ❌ | ❌ | ❌ |
| LOCKED_RECORD | ❌ ever | ❌ ever | ❌ ever | ❌ ever (only amendment) |

## 3 · RETURNED_FOR_REVISION · limited edit surface

When a DR is returned, the foreman regains an edit surface to fix the cited deficiency. But the edit surface is **deliberately limited** so the foreman cannot rewrite the entire report (which would defeat the audit trail).

| Field family | Editable on revision? |
|---|---|
| Project · Date · Crew · Manpower | ❌ (audit-locked at first submit) |
| Production rows | ✅ (most common rejection reason) |
| Constraint / Delay rows | ✅ |
| Photos | ✅ (foreman can ADD only · no delete) |
| Notes · narratives | ✅ |
| Approval fields | ❌ ever |
| `submitted_at` | ❌ (preserved · `resubmitted_at` is the new timestamp) |
| `report_version` | system-only · increments by 1 on each resubmit |

If a reviewer needs the foreman to fix a non-editable field (e.g., wrong date), the doctrine is: **reject with reason → admin amends from the LOCKED_RECORD side after approval, OR reject and ask foreman to file a separate corrected DR for the wrong date.**

## 4 · Version semantics

| Field | Semantic |
|---|---|
| `report_version` | Increments on every resubmit (and only on resubmit). Initial submit is v1. |
| `audit_envelope_sha256` | Recomputes on every state transition. Drift between two PDF prints proves a transition happened between them. |
| `report_number` | Mints on first submit only. Never changes. |
| `created_at` | Original first-submit timestamp. Never changes. |
| `submitted_at` | First submit timestamp. Never changes after v1. |
| `resubmitted_at` | Last resubmit timestamp. Updates on each cycle. |

## 5 · Multi-reviewer contention

| Scenario | Behavior |
|---|---|
| Two supers open the same SUBMITTED DR | Both transitions UNDER_REVIEW but only the first stamps `review_started_at`. Both see the same data. |
| First super taps Approve · second super taps Reject 200 ms later | Optimistic-concurrency `If-Match` header on the second call fails with 409. Second super gets a "report already approved · refresh to view" banner. |
| Super taps Approve while admin is amending | Amendment is structurally a different record. Approve still succeeds on the base DR. The amendment audit row reflects both transitions in order. |

## 6 · Legacy DR projection

DRs created before Phase V.4 (no review events) project as:

```
status: LOCKED_RECORD
approved_by_role_value: null   ← was never reviewed
approved_at: null
review_events: []              ← empty list (not missing)
```

This preserves M1 Option C frozen-archive doctrine. Reviewers cannot approve a legacy DR retroactively (no review surface offered on `approved_at == null` legacy rows).

## 7 · Doctrine compliance

| Doctrine | Honored |
|---|---|
| Append-only after lock | ✅ DELETE 410 · amendments only |
| Forever auditable | ✅ `daily_report_review_events` append-only |
| No silent state transitions | ✅ every transition stamps an event row |
| Hash continuity | ✅ before/after sha256 on each event |
| Foreman 9-step contract preserved | ✅ DRAFT and RETURNED_FOR_REVISION surfaces use the same form · no new mandatory captures |
| Reviewer scoping | ✅ `compute_fl_scope(actor)` gate |
| Project number stays stable | ✅ never re-minted on resubmit |

## 8 · Stop condition

🛑 Doctrine only. Implementation begins only after operator review.

_End of REPORT_LIFECYCLE_DOCTRINE.md._
