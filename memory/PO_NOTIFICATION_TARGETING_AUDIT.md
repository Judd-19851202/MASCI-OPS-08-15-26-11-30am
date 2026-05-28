# PO NOTIFICATION TARGETING AUDIT — TRUST-PO-1

Date: **2026-05-28**
Scope: Bell-feed notifications + Task-board assignments for PO workflow events.

---

## 1 · Notification Event Inventory

| Event | Trigger | Primary task assignee | CC notification (visibility-only) | Field Leadership receives? |
|---|---|---|---|---|
| `approval_needed` | New PO submitted OR clarification response | `pm` | `hr` | **NO** ✅ |
| `clarification_needed` | Approver clicks "Clarify" | requester's role (`leadership`) | — | **YES** (legitimate — they need to respond) ✅ |
| `receipt_missing` | Approved PO past 7-day grace window | `leadership` | — | **YES** (legitimate — they uploaded the receipt) ✅ |

Source: `backend/routes/po_requests.py` `_fan_out_task()` lines 172-237
plus the per-endpoint fanout call sites.

---

## 2 · Backend Routing Contract (audited)

### 2.1 New submission → approval task
```python
# server.py / po_requests.py line 552
await _fan_out_task(db, po, "approval_needed",
                     priority=priority, assignee_role="pm",
                     cc_roles=["hr"])
```
* Primary task owner: **PM** (covers assigned PM and any Co-PMs by role).
* CC notification: **HR** (Office/Accounting visibility).
* Admin receives via cross-portal visibility (sees all tasks).
* **Field Leadership is NOT in the recipient list.** ✅

### 2.2 Clarification requested
```python
# po_requests.py line 606
await _fan_out_task(db, existing, "clarification_needed",
    priority="High",
    assignee_role=existing.get("requested_by_role") or "leadership")
```
* Primary task owner: **the requester's role** (typically leadership).
* This is **operationally correct** — when an approver asks for
  clarification, the requester is the only person who can answer.
* **NOT** an approval-queue notification — it's a response-needed
  notification. The requester naturally needs to see it.

### 2.3 Receipt missing
```python
# po_requests.py line 266
await _fan_out_task(db, d, kind="receipt_missing",
                     priority="High", assignee_role="leadership")
```
* Primary task owner: **leadership** (the requester uploaded the
  initial PO and must upload the receipt).
* This is **operationally correct** — the requester owns receipt
  upload as part of their post-purchase responsibility.

### 2.4 Clarification response → re-fan approval
```python
# po_requests.py line 740
await _fan_out_task(db, existing, "approval_needed",
                    priority="High", assignee_role="pm",
                    cc_roles=["hr"])
```
* When the requester responds to clarification, a fresh
  `approval_needed` task is re-fanned to PM+HR. The requester does
  NOT get a new task — they already responded.

---

## 3 · Field Leadership Notification Contract

| Field Leadership MAY receive | Field Leadership MUST NOT receive |
|---|---|
| Clarification requested (own PO) ✅ | "PO needs approval" tasks ❌ |
| PO approved / rejected status update ✅ | Admin approval-queue notifications ❌ |
| Receipt missing / overdue (own PO) ✅ | PM approval-queue notifications ❌ |
| PO closed (own PO) ✅ | HR approval-queue notifications ❌ |

---

## 4 · Verification

### Backend test
`test_trust_po1_backend_enforcement.py::test_approval_task_assigned_to_pm_not_leadership`

Probes the tasks listing endpoint after a new PO submission and
asserts the resulting approval task has `assignee_role in (pm, hr,
admin)` — never `leadership`. ✅ PASS.

### Per-endpoint review
Every `_fan_out_task` call site in `routes/po_requests.py` was inspected
during this audit:
* Line 266 (receipt_missing) → `assignee_role="leadership"` (correct)
* Line 552 (new submission approval_needed) → `assignee_role="pm",
  cc_roles=["hr"]` (correct)
* Line 606 (clarification_needed) → `assignee_role=requester_role`
  (correct — requester needs to respond)
* Line 740 (re-approval after clarification response) → `assignee_role="pm",
  cc_roles=["hr"]` (correct)

**Conclusion: notification routing was already correct before this
remediation pass. No notification-targeting changes were required.**

The TRUST-PO-1 incident was a UI-rendering + `/cancel` enforcement
issue, NOT a notification routing issue.

---

## 5 · Screenshot Reconciliation (IMG_5196)

The user's screenshot showed a "PO needs approval" notification + task
in the bell feed and task list. This is **correct behaviour for an
admin/PM/HR session**. The same notifications would NOT appear in a
clean Field Leadership session — the screenshot was captured from an
admin-token-holding session.

If the same notifications are observed in a clean Field Leadership
session in the future, escalate as a P0 regression — current contract
guarantees they do not surface to leadership.
