# Approval / Rejection Architecture

_Phase V.4 · 2026-05-29 · Architecture & governance · NOT implementation._

> **Operator authorization (verbatim):** _"Begin Approval / Rejection Foundation Architecture. This is a governance and workflow phase. Build the foundation correctly before a single approval button is created."_

## 1 · Lifecycle (single source of truth)

```
              ┌──────────────────────────────────────────────────────┐
              │            DAILY REPORT LIFECYCLE                    │
              │              (Phase V.4 doctrine)                    │
              └──────────────────────────────────────────────────────┘

  DRAFT ───► SUBMITTED ───► UNDER_REVIEW ───► APPROVED ───► LOCKED_RECORD
    │            │              │                              │
    │            │              └────────────┐                  │
    │            │                           ▼                  │
    │            │                       REJECTED               │
    │            │                           │                  │
    │            │                           ▼                  │
    │            └◄─────── RETURNED_FOR_REVISION                │
    │                                                           │
    ▼                                                           ▼
  (autosave           (Wave-2 idempotent              (M1 Option C
   substrate)          submission · 24h dedup)        Frozen Archive)
                                                      DELETE = 410
```

| State | Owner | Mutable? | Photo upload allowed? | Approval surface |
|---|---|---|---|---|
| DRAFT | foreman | ✅ | ✅ | hidden |
| SUBMITTED | foreman | ❌ | ❌ | visible to reviewer |
| UNDER_REVIEW | reviewer | ❌ | ❌ | active |
| RETURNED_FOR_REVISION | foreman | ✅ (limited) | ✅ | hidden until re-submitted |
| REJECTED | reviewer | ❌ | ❌ | terminal but auditable |
| APPROVED | reviewer | ❌ | ❌ | locked |
| LOCKED_RECORD | nobody | ❌ (only amendments) | ❌ | locked |

## 2 · State-transition contract

| From | To | Allowed actor (canonical role) | Side effects |
|---|---|---|---|
| DRAFT | SUBMITTED | foreman (creator) | mints `report_number` if not yet · `submitted_at` + `submitted_by` stamped |
| SUBMITTED | UNDER_REVIEW | superintendent (project-scoped) · sr_superintendent (region-scoped) · admin (full) | `review_started_at` stamped |
| UNDER_REVIEW | APPROVED | same | `approved_at` + `approved_by` + `approved_by_role` + `approved_version` stamped · IDB removes nothing · audit envelope frozen |
| UNDER_REVIEW | REJECTED | same | `rejected_at` + `rejected_by` + `rejected_by_role` + `rejection_reason` (non-empty) stamped |
| REJECTED | RETURNED_FOR_REVISION | foreman taps Acknowledge · superintendent can also kick it back proactively | `returned_at` stamped · foreman regains DRAFT-style edit surface (limited) |
| RETURNED_FOR_REVISION | SUBMITTED | foreman | `resubmitted_at` stamped · cycle counter increments · `review_events[]` accumulates |
| APPROVED | LOCKED_RECORD | system (24 h grace · or immediately on operator-configured value) | DR is now immutable · DELETE returns 410 · only amendments allowed |
| LOCKED_RECORD | LOCKED_RECORD (+amendment) | admin · sr_superintendent w/ amendment scope | new `daily_report_amendments` record · ORIGINAL DR untouched · audit footer hash re-computes to include amendment digest |

## 3 · Append-only event log (single forensic source of truth)

A new collection — **`daily_report_review_events`** — append-only.

```jsonc
{
  "id": "uuid4",
  "daily_report_id": "fk",
  "action": "submit | start_review | approve | reject | return_for_revision | resubmit | amend",
  "actor_id": "fk",
  "actor_role_value": "sr_superintendent | superintendent | foreman | leadman | admin",
  "actor_role_label": "Sr. Superintendent | …",
  "actor_name_snapshot": "string",                 // captured at action time
  "occurred_at_utc": "ISO with tz (TRUST-TIME-1)",
  "project_number": "string · denormalized",
  "report_version": "int · monotonically increasing per DR",
  "reason": "string · non-empty for reject ≥ 8 chars · null otherwise",
  "audit_envelope_sha256_before": "hex 64",        // hash at time of transition
  "audit_envelope_sha256_after":  "hex 64",        // post-transition hash
  "ip_hash": "sha256 of remote IP · NOT raw IP",
  "device_id_hash": "sha256 of `masci.device-id`",
  "user_agent_short": "≤ 80 char redacted"
}
```

| Property | Doctrine |
|---|---|
| Append-only | no PATCH · no DELETE · ever |
| Mirror to `operational_links` | `relationship = "review-event"` · evidence chain visible in unified projector |
| Backward-compatible | DRs that never had a review event (legacy) project unchanged |
| Hash continuity | `audit_envelope_sha256_after` is the next attempt's `_before` · drift = tamper |

## 4 · API surface (planned · NOT implemented today)

```
POST   /api/daily-reports/{id}/review/start         # transitions SUBMITTED → UNDER_REVIEW
POST   /api/daily-reports/{id}/review/approve       # transitions UNDER_REVIEW → APPROVED
POST   /api/daily-reports/{id}/review/reject        # transitions UNDER_REVIEW → REJECTED  · body {reason}
POST   /api/daily-reports/{id}/review/return        # transitions REJECTED → RETURNED_FOR_REVISION (foreman ack or super proactive)
POST   /api/daily-reports/{id}/resubmit             # transitions RETURNED_FOR_REVISION → SUBMITTED
GET    /api/daily-reports/{id}/review-events        # full append-only history
POST   /api/daily-reports/{id}/amendment            # post-lock change (admin/sr_super only · NEW record)
GET    /api/daily-reports/{id}/amendments           # list amendments
```

All endpoints:
- `Idempotency-Key` honored (Wave-2 contract continued).
- 24 h dedup window.
- `X-Actor-Role` resolved from FL token at request time (never trusted from client).
- Project-scope check via `compute_fl_scope(actor)` (per `FL_DASHBOARD_VISIBILITY_PREP.md`).
- Optimistic-concurrency check via `If-Match: <audit_envelope_sha256>` header (rejects with 409 if the DR has moved since the reviewer loaded it).

## 5 · UI surface (planned · NOT implemented today)

| Surface | Visibility |
|---|---|
| Foreman view of own DR | Status pill (Draft / Submitted / Under Review / Rejected / Approved) · NO approval controls · NO reviewer name surfaced (privacy) — only the action and rejection reason |
| Superintendent review screen | Read-only DR · Approve / Reject buttons · Reject modal requiring reason ≥ 8 chars · "Start review" auto-fires on entry |
| Sr. Superintendent multi-project queue | Filterable list of UNDER_REVIEW + REJECTED DRs across region · same Approve / Reject affordances |
| Admin override | Same surface + an "Amend" button on LOCKED_RECORD |
| Foreman after rejection | Acknowledge banner + reason · tapping resumes DRAFT-edit mode (auto-fills `resubmitted_at` cycle counter on save) |
| Anyone | Audit footer continues to show `Official Record · DR-YYYY-NNNNN · sha256=<16> · rendered <UTC>` |

## 6 · What does NOT change

- ❌ Foreman fill-in experience (9-step contract, Doctrine Lock #1) — still simple, no new fields, no new mandatory captures.
- ❌ DRAFT autosave + idempotent submit (Wave-2 reliability engine) — unchanged.
- ❌ Existing reports (pre-V.4) — auto-projected to `LOCKED_RECORD` status (frozen archive). DELETE still 410.
- ❌ PDF audit footer — unchanged contract, but the canonical envelope now incorporates `review_events_digest` so the footer hash drifts on every approve / reject / amendment.
- ❌ ChartConstraint / production / weather / delay / FL role pickers — unchanged.
- ❌ PM Exposure Tile routing — still NOT in scope.
- ❌ Pilot · RFI · Schedule · P6 — still NOT in scope.

## 7 · Doctrine compliance

- ✅ **Append-only · forever auditable** — `daily_report_review_events` is the forensic source of truth.
- ✅ **No silent edits** — every state change is an event row.
- ✅ **No silent deletes** — DELETE remains 410 · M1 Option C continues.
- ✅ **Hash continuity** — `audit_envelope_sha256_before / _after` chain proves no tampering.
- ✅ **Project scope** — superintendents see only their scope · `compute_fl_scope` gate.
- ✅ **Optimistic concurrency** — `If-Match` prevents the "two reviewers see different snapshots" failure mode.
- ✅ **Doctrine Lock #1 (Simplicity)** — foreman 9-step contract preserved · no new mandatory captures.
- ✅ **Doctrine Lock #2 (Inheritance)** — reuses idempotency · audit footer · `operational_links` substrate.

## 8 · Stop condition

🛑 Architecture only. No endpoint coded. No UI built. Implementation begins only after operator review of this doc + the 6 sibling deliverables.

_End of APPROVAL_REJECTION_ARCHITECTURE.md._
