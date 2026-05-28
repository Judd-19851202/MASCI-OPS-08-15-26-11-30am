# PROCUREMENT AUTHORITY AUDIT — TRUST-PO-1

Date: **2026-05-28**
Iteration: **TRUST-PO-1** (post-TRUST-1 Final Hardening)
Status: **REMEDIATED** — preview only · awaiting validation sweep
Scope: Procurement (PO Request) authority boundaries across all portals.

---

## 1 · Triggering Incident

A field user observed (screenshots IMG_5195 + IMG_5196 attached to the
fork brief) that the **PO detail drawer rendered approval / issue /
reject controls inside what appeared to be a Field Leadership
context**, including:

* `Approval action` panel header
* `Approval / rejection notes` textarea
* `Manual PO # (optional)` input
* `Approved amount` input
* `Approve` / `Clarify` / `Reject` buttons
* `Cancel` button

The platform's stated procurement policy (visible in the page's own
"Authority & Visibility" banner) is unambiguous:

> Field Leadership submits purchase **requests**. The assigned PM,
> any Co-PMs on the job, HR, and Admin issue the official PO and
> assign the PO number. After purchase, the requester uploads
> receipts here.

The platform was **rendering authority that Field Leadership does not
hold**.

---

## 2 · Classification

| Layer | Status | Severity |
|---|---|---|
| UI authority leak (component renders restricted controls) | **PRESENT** | **High** — operator-trust failure |
| Backend authority leak (token can actually call action) | **PRESENT for `/cancel`** · absent for `/approve`, `/reject`, `/clarify`, `/close` | **High** — true authorisation bypass |
| Notification targeting (FL receives approval-queue notifications) | Not present | — |
| Task assignment (FL receives approval tasks) | Not present | — |

**Both issues are surgical**. No schema rewrite, no workflow redesign.

---

## 3 · Root Cause

### 3.1 UI authority leak
`frontend/src/pages/PoRequests.jsx` derived its render-gate from raw
browser-storage token presence:

```js
// pre-remediation
const canApprove = isPm() || isHr() || isAdmin();
```

Each of `isPm()`, `isHr()`, `isAdmin()` simply asks "is there a token
with this key in localStorage / sessionStorage?". Because Super Admin
sessions hold an admin token while ALSO holding a Field Leadership
session, the gate evaluates `true` regardless of which portal the
operator is currently inside. The shared `/po-requests` page therefore
rendered the approval block under both portal sidebars.

### 3.2 Backend authority leak
`backend/routes/po_requests.py` `cancel_po()` was the only
state-mutating PO endpoint **with no `_can_approve()` gate**:

```python
# pre-remediation
@router.post("/api/po-requests/{po_id}/cancel")
async def cancel_po(po_id, actor=Depends(require_any_portal_token)):
    await db.po_requests.update_one({"id": po_id}, {"$set": {...}})
```

Any actor holding any portal token (including Field Leadership) could
cancel a PO mid-workflow. This was a real authority bypass even though
the UI did not surface it from the FL portal.

---

## 4 · Remediation (Surgical)

### 4.1 Frontend — capability-scoped rendering
1. **New** `frontend/src/lib/portalContext.js`
   * Tracks current portal in `sessionStorage.masci.portal-context`.
   * Each hub mount declares its context: `field-leadership`, `admin`,
     `pm`, `hr`, `safety`, `shop`.
2. **New** `frontend/src/lib/poCapabilities.js`
   * `getPoCapabilities()` returns an explicit per-capability bundle
     (`po.approve`, `po.reject`, `po.clarify`, `po.issue_number`,
     `po.set_approved_amount`, `po.close`, `po.cancel`,
     `po.request.create`, `po.request.view`,
     `po.request.receipt_upload`, `po.request.respond_clarify`).
   * Field Leadership context forces approver caps OFF regardless of
     coexisting tokens — the surgical fix.
3. **Modified** `frontend/src/pages/PoRequests.jsx`
   * Replaced `canApprove = isPm() || isHr() || isAdmin()` with
     `caps = getPoCapabilities()`.
   * Every approver button, Manual PO # input, Approved amount input,
     Cancel button, and Close button now reads from a specific
     capability flag.
4. **Modified** hub mounts wire `setPortalContext(...)`:
   * `pages/FieldLeadershipHub.jsx` → "field-leadership"
   * `pages/AdminHub.jsx` → "admin"
   * `pages/PmHub.jsx` → "pm"
   * `pages/HrHub.jsx` → "hr"

### 4.2 Backend — close `/cancel` leak
`backend/routes/po_requests.py` · `cancel_po()` now begins with:
```python
if not _can_approve(actor):
    raise HTTPException(403, "Not authorized to cancel POs")
```

---

## 5 · Verification

### Backend (10/10 PASS)
File: `backend/tests/pw_suite/test_trust_po1_backend_enforcement.py`

* `test_leadership_can_create_po_request` ✅
* `test_leadership_cannot_approve_po` ✅ (403)
* `test_leadership_cannot_reject_po` ✅ (403)
* `test_leadership_cannot_clarify_po` ✅ (403)
* `test_leadership_cannot_close_po` ✅ (403)
* `test_leadership_cannot_cancel_po` ✅ (403) — **new authority gate**
* `test_leadership_cannot_assign_manual_po_number_or_amount` ✅ (403)
* `test_admin_can_approve_po` ✅
* `test_admin_can_cancel_po` ✅
* `test_approval_task_assigned_to_pm_not_leadership` ✅

### Frontend (4/4 PASS)
File: `backend/tests/pw_suite/test_trust_po1_frontend_capability_scope.py`

* `test_admin_context_renders_approval_block` ✅
* `test_leadership_only_context_hides_approval_block` ✅
* `test_super_admin_in_fl_context_hides_approval_block` ✅
   ← **the surgical fix verified**
* `test_context_switch_admin_to_leadership_recomputes_caps` ✅

---

## 6 · Remaining Risks

| Risk | Mitigation |
|---|---|
| Operator deep-links to `/po-requests` BEFORE entering a hub → context = "unknown" | Capabilities default-conservative: submitter caps granted only if any token; approver caps require explicit approver portal context. |
| sessionStorage disabled (private browsing edge) | `setPortalContext` no-ops silently; `getPortalContext` returns "unknown"; conservative caps apply. |
| Future PO state-mutating endpoint added without `_can_approve` gate | Add to the backend enforcement test as a new probe. Pre-deploy gate `stage_sigma3_regression` runs the full `pw_suite/`. |
| Capability layer used as security rather than UX | Backend `_can_approve` remains the ground truth. UI capability is a TRUST surface, not a SECURITY surface. |

---

## 7 · Deploy Recommendation

* **Preview cutover**: GO (all gates green)
* **Production cutover**: gated on
  1. Preview validation pass (manual)
  2. Real Field Leadership iPad workflow exercise
  3. 72-hour preview observation window (no portal-context drift in `/api/draft-telemetry`)
* **Phase V (RFI) start**: cleared after production observation window.

---

## 8 · References

* `PO_ROLE_CAPABILITY_MATRIX.md`
* `PO_BACKEND_ENFORCEMENT_REPORT.md`
* `PO_FRONTEND_VISIBILITY_REPORT.md`
* `PO_NOTIFICATION_TARGETING_AUDIT.md`
* `PROCUREMENT_TRUST_REMEDIATION_PLAN.md`
* `PROCUREMENT_AUTHORITY_CERTIFICATION.md`
