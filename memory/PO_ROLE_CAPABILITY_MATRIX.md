# PO ROLE CAPABILITY MATRIX — TRUST-PO-1

Date: **2026-05-28** · capability-scoped rendering doctrine

---

## Capability Definitions

| Capability | What it gates (UI) | What it gates (backend) |
|---|---|---|
| `po.request.create` | "Request PO" button + form dialog | `POST /api/po-requests` (any portal token) |
| `po.request.view` | PO list + drawer (read-only access) | `GET /api/po-requests*` (scoped by role) |
| `po.request.receipt_upload` | Receipt upload form | `POST /api/po-requests/{id}/receipt` |
| `po.request.respond_clarify` | Clarification response textarea | `POST /api/po-requests/{id}/respond-clarification` |
| `po.approve` | Approve button | `POST /api/po-requests/{id}/approve` with action=approve |
| `po.reject` | Reject button | `POST /api/po-requests/{id}/approve` with action=reject |
| `po.clarify` | Clarify button | `POST /api/po-requests/{id}/approve` with action=clarify |
| `po.issue_number` | Manual PO # input | `po_number_manual` body field on approve |
| `po.set_approved_amount` | Approved amount input | `approved_amount` body field on approve |
| `po.close` | Mark Closed button | `POST /api/po-requests/{id}/close` |
| `po.cancel` | Cancel button | `POST /api/po-requests/{id}/cancel` |

---

## Matrix · Portal Context × Role × Capability

Legend: ✅ allowed · ❌ denied · — N/A (role cannot be in that context)

### Field Leadership context (`portal-context = "field-leadership"`)

| Capability | Leadership token only | Super Admin in FL context |
|---|---|---|
| po.request.create | ✅ | ✅ |
| po.request.view | ✅ | ✅ |
| po.request.receipt_upload | ✅ | ✅ |
| po.request.respond_clarify | ✅ | ✅ |
| po.approve | ❌ | ❌ ← surgical fix |
| po.reject | ❌ | ❌ ← surgical fix |
| po.clarify | ❌ | ❌ ← surgical fix |
| po.issue_number | ❌ | ❌ ← surgical fix |
| po.set_approved_amount | ❌ | ❌ ← surgical fix |
| po.close | ❌ | ❌ ← surgical fix |
| po.cancel | ❌ | ❌ ← surgical fix |

Doctrine: **Field Leadership context locks approver caps OFF regardless
of which tokens happen to coexist in browser storage.**

### PM context (`portal-context = "pm"`)

| Capability | PM token | Admin in PM context |
|---|---|---|
| po.request.create | ✅ | ✅ |
| po.request.view | ✅ | ✅ |
| po.request.receipt_upload | ✅ | ✅ |
| po.request.respond_clarify | ✅ | ✅ |
| po.approve | ✅ | ✅ |
| po.reject | ✅ | ✅ |
| po.clarify | ✅ | ✅ |
| po.issue_number | ✅ | ✅ |
| po.set_approved_amount | ✅ | ✅ |
| po.close | ❌ (admin only) | ❌ (must be admin context) |
| po.cancel | ❌ (admin only) | ❌ (must be admin context) |

### HR / Office context (`portal-context = "hr"`)

| Capability | HR token | Admin in HR context |
|---|---|---|
| po.request.create | ✅ | ✅ |
| po.request.view | ✅ | ✅ |
| po.request.receipt_upload | ✅ | ✅ |
| po.approve | ✅ | ✅ |
| po.reject | ✅ | ✅ |
| po.clarify | ✅ | ✅ |
| po.issue_number | ✅ | ✅ |
| po.set_approved_amount | ✅ | ✅ |
| po.close | ❌ | ❌ |
| po.cancel | ❌ | ❌ |

### Admin context (`portal-context = "admin"`)

| Capability | Admin token |
|---|---|
| po.request.create | ✅ |
| po.request.view | ✅ |
| po.request.receipt_upload | ✅ |
| po.approve | ✅ |
| po.reject | ✅ |
| po.clarify | ✅ |
| po.issue_number | ✅ |
| po.set_approved_amount | ✅ |
| po.close | ✅ |
| po.cancel | ✅ |

### Unknown context (deep-link to `/po-requests` before any hub mount)

Conservative fallback: submitter caps granted if any token; approver
caps **OFF until the user explicitly enters an approver portal hub**.

---

## Why portal context is the FIRST gate

Token-presence is a necessary but **not sufficient** condition. The
operator's *current operational mode* — which portal they entered, what
chrome they see, what mental model they're in — determines what
controls should be exposed. The capability layer encodes this:

1. **Portal context** filters out actions that don't belong to the
   current operator stance (Field Leadership stance never approves).
2. **Token presence** further filters within the allowed set
   (an HR token cannot close even in HR context — close is admin-only).
3. **Workflow state** (the PO's current status) gates the final visibility
   (you can't approve a PO that's already Closed).
4. **Backend** is the ultimate authoriser — UI caps are a TRUST surface,
   not a SECURITY surface.

---

## Capability source location

* `frontend/src/lib/poCapabilities.js` — derives the bundle
* `frontend/src/lib/portalContext.js` — declares the context
* `frontend/src/pages/PoRequests.jsx` — consumes the bundle
* `backend/routes/po_requests.py` `_can_approve()` — backend ground truth

---

## Future capabilities (reserved · NOT yet implemented)

* `po.request.split` — split a PO across multiple line items (future)
* `po.budget.override` — exceed project budget cap (future · Phase V+)
* `po.vendor.create` — register a new vendor inline (future)

These are listed here so future implementers know the slot is named.
