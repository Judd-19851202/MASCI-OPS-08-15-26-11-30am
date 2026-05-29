# Approval Permission Matrix

_Phase V.4 · 2026-05-29 · governance · NOT implementation._

## 1 · The matrix (canonical · locked)

| Action | Leadman | Foreman | Superintendent | Sr. Superintendent | Admin |
|---|---|---|---|---|---|
| Create DRAFT (own) | ✅ if authorized | ✅ | ✅ | ✅ | ✅ |
| Submit own DR | (if authorized) | ✅ | ✅ | ✅ | ✅ |
| Edit own DRAFT | ✅ | ✅ | ✅ | ✅ | ✅ |
| Edit own RETURNED_FOR_REVISION | ✅ | ✅ | ✅ | ✅ | ✅ |
| Edit another user's DRAFT | ❌ | ❌ | ❌ | ❌ | ✅ |
| Start review (SUBMITTED → UNDER_REVIEW) | ❌ | ❌ | ✅ (project) | ✅ (region) | ✅ |
| Approve (UNDER_REVIEW → APPROVED) | ❌ | ❌ | ✅ (project) | ✅ (region) | ✅ |
| Reject (UNDER_REVIEW → REJECTED) · reason required | ❌ | ❌ | ✅ (project) | ✅ (region) | ✅ |
| Return for revision (REJECTED → RETURNED_FOR_REVISION) | ❌ (only ack on own DR) | ✅ (ack on own) | ✅ proactive | ✅ proactive | ✅ |
| Resubmit (RETURNED_FOR_REVISION → SUBMITTED) | ✅ on own | ✅ on own | ✅ on own | ✅ on own | ✅ |
| Amend a LOCKED_RECORD | ❌ | ❌ | ❌ | ✅ (region) | ✅ |
| Override an approve / reject decision | ❌ | ❌ | ❌ | ❌ | ✅ (admin only · audit row stamped) |
| Read review-events for own DR | ✅ | ✅ | ✅ in scope | ✅ in scope | ✅ |
| Read review-events for any DR | ❌ | ❌ | ❌ | ❌ | ✅ |
| Bulk export of review-events | ❌ | ❌ | ❌ | ❌ | ✅ |

## 2 · Scoping primitive

```python
def can_approve(actor: dict, dr: dict) -> bool:
    role = actor.get("role_value")
    if role == "admin":
        return True
    if role not in {"sr_superintendent", "superintendent"}:
        return False
    if role == "sr_superintendent":
        return _project_in_region(dr["project_number"], actor.get("assigned_region"))
    if role == "superintendent":
        return dr["project_number"] in (actor.get("assigned_projects") or [])
    return False
```

| Property | Doctrine |
|---|---|
| Fail-closed | empty `assigned_projects` for a super = no approval authority anywhere |
| No transitive trust | a super-tier user does NOT inherit approval authority simply by viewing the DR |
| Region beats project | sr_super with a region claim can approve any DR whose project is in the region · does NOT need to be in `assigned_projects` |
| Admin override | always returns true · but ALWAYS writes an audit row |

## 3 · UI capability surface (planned · NOT implemented today)

A new frontend primitive — `lib/dailyReportReviewCapabilities.js` — modeled after `poCapabilities.js`:

```js
getDailyReportReviewCapabilities(actor, dr) => {
  "dr.draft.create":   bool,
  "dr.draft.edit":     bool,
  "dr.submit":         bool,
  "dr.review.start":   bool,
  "dr.review.approve": bool,
  "dr.review.reject":  bool,
  "dr.review.return":  bool,
  "dr.resubmit":       bool,
  "dr.amend":          bool,
  "dr.override":       bool,
}
```

UI surfaces gate buttons on these capabilities. Authority Mismatch Probe baseline will be extended to allowlist the same vocabulary so unauthorized buttons never render even on stale tokens.

## 4 · Endpoint enforcement (planned)

| Endpoint | Authentication required | Authorization gate |
|---|---|---|
| `POST /api/daily-reports/{id}/review/start` | FL token | `can_review_start(actor, dr)` |
| `POST /api/daily-reports/{id}/review/approve` | FL token | `can_approve(actor, dr)` |
| `POST /api/daily-reports/{id}/review/reject` | FL token | `can_approve(actor, dr)` + non-empty `reason` ≥ 8 chars |
| `POST /api/daily-reports/{id}/review/return` | FL token | `can_return(actor, dr)` |
| `POST /api/daily-reports/{id}/resubmit` | FL token | `actor_id == dr.created_by OR admin` |
| `POST /api/daily-reports/{id}/amendment` | admin OR sr_super w/ region | full audit row stamped |
| `GET /api/daily-reports/{id}/review-events` | FL token | `can_read_review_events(actor, dr)` |

Each gate refuses with **403 + structured body** (see `APPROVAL_REJECTION_ARCHITECTURE.md §4`).

## 5 · Concurrency · `If-Match`

Every state-transition endpoint requires `If-Match: <audit_envelope_sha256>`. If the header is missing OR does not match the current envelope hash on disk, the server returns **409 Conflict**:

```json
{ "ok": false, "code": "envelope_changed", "current_sha256": "..." }
```

This is the contract that prevents two reviewers from racing to approve / reject the same DR with stale data.

## 6 · Read scope (passive · no transition)

| Surface | Leadman | Foreman | Super (project) | Sr. Super (region) | Admin |
|---|---|---|---|---|---|
| Own DR (any state) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Other DR · same project | ❌ | ❌ | ✅ | ✅ if in region | ✅ |
| Other DR · other project | ❌ | ❌ | ❌ | ❌ unless in region | ✅ |
| `LOCKED_RECORD` PDF (any DR · audit footer carries integrity) | external auditors (CEI · DOT · FAA · owner) consume via signed link · NO PII surface · audit footer ensures integrity | | | | |

## 7 · Doctrine compliance

- ✅ **No transitive trust** — every endpoint re-checks `can_approve` against the DR snapshot.
- ✅ **Fail-closed** — missing or empty scope = no authority.
- ✅ **Admin override is auditable** — always writes an event row.
- ✅ **Reject requires reason** — server-enforced ≥ 8 chars.
- ✅ **Concurrency-safe** — `If-Match` envelope hash.
- ✅ **Foreman experience unchanged** — buttons hidden by capability primitive · no new clicks.

## 8 · Stop condition

🛑 Matrix only. No code touched. Implementation begins only after operator review.

_End of APPROVAL_PERMISSION_MATRIX.md._
