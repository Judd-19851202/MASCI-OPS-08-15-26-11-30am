# PROCUREMENT AUTHORITY CERTIFICATION — TRUST-PO-1

Date: **2026-05-28**
Iteration: **TRUST-PO-1**
Status: **PREVIEW CERTIFIED** · awaits production cutover review

---

## Certification Statement

The MASCI Operational Hub procurement layer has been audited and
remediated against the trust-boundary contract approved by the
platform owner. As of the date above, the following certified
guarantees hold on the **preview environment**:

### Backend (10/10 regression PASS)

1. A valid Field Leadership token **CAN** create a PO request.
2. A valid Field Leadership token **CANNOT** approve a PO (403).
3. A valid Field Leadership token **CANNOT** reject a PO (403).
4. A valid Field Leadership token **CANNOT** request clarification
   on a PO as an approver (403).
5. A valid Field Leadership token **CANNOT** assign a manual PO
   number (403 on the approve endpoint).
6. A valid Field Leadership token **CANNOT** set the approved
   amount (403 on the approve endpoint).
7. A valid Field Leadership token **CANNOT** close a PO (403).
8. A valid Field Leadership token **CANNOT** cancel a PO (403)
   — newly enforced; the `/cancel` endpoint was the real backend
   authority bypass discovered during this audit.
9. A valid admin token **CAN** approve a PO.
10. A valid admin token **CAN** cancel a PO.
11. The approval task fan-out for a new PO is assigned to **role=pm**
    with HR as cc, **NEVER** to role=leadership.

### Frontend (4/4 regression PASS)

12. The PO Requests page rendered inside the **Admin portal context**
    surfaces the `data-testid="po-approval-block"` with Approve /
    Clarify / Reject buttons + Manual PO # + Approved amount inputs.
13. The PO Requests page rendered inside the **Field Leadership
    portal context** does **NOT** surface ANY approver control
    (`po-approval-block`, `po-approve-btn`, `po-reject-btn`,
    `po-clarify-btn`, `po-approval-manual`, `po-approval-amount`,
    `po-approval-notes`, `po-close-btn`, `po-cancel-btn`).
14. The PO Requests page rendered inside the Field Leadership portal
    context when the **operator ALSO holds an admin token** in
    browser storage does **NOT** surface approver controls.
    ← This is the surgical fix for the originally-reported field
    incident.
15. Switching portal context from Admin → Field Leadership during
    the same session recomputes the capability bundle on the next
    `/po-requests` mount; the approval block disappears.

### Notification Targeting (audited — no remediation required)

16. The `approval_needed` task is assigned to `role=pm` with
    `cc_roles=["hr"]`. Field Leadership is NOT in the recipient list.
17. The `clarification_needed` task is assigned to the requester's
    role (legitimate — they must respond).
18. The `receipt_missing` task is assigned to `role=leadership`
    (legitimate — they own receipt upload).
19. No new authority-leak notification path was found in the audit.

---

## Doctrine Locked

* **Field Leadership requests.** Submits, uploads receipts, responds
  to clarification.
* **PM / HR / Admin approve.** Approve, reject, clarify, set amount.
* **Admin issues + closes + cancels.** Manual PO number, close, cancel.
* **Super Admin in FL portal sees the FL view** — never the approver
  view — regardless of which tokens coexist in browser storage.
* **The backend remains the source of truth.** UI capability gating
  is a TRUST surface, not a SECURITY surface.

---

## Deploy Recommendation

* **Preview**: CERTIFIED.
* **Production**: PROCEED after the following gates clear:
  1. Operator-perspective manual sweep (15 min · admin + FL round-trip).
  2. Real iPad workflow exercise (one FL submission → PM approval →
     receipt upload).
  3. 72-hour preview observation window without any
     `po.authority_leak` telemetry or operator escalation.
  4. Telemetry-clean — `/api/draft-telemetry/recent` shows no
     `portal-context` drift events.
* **Phase V (RFI) MVP**: CLEARED to begin after the above completes.

---

## Audit Trail

* Primary diagnosis: `PROCUREMENT_AUTHORITY_AUDIT.md`
* Capability source-of-truth: `lib/poCapabilities.js`
* Portal-context source-of-truth: `lib/portalContext.js`
* Backend enforcement source-of-truth: `routes/po_requests.py`
  `_can_approve()`
* Test contracts:
  * `tests/pw_suite/test_trust_po1_backend_enforcement.py`
  * `tests/pw_suite/test_trust_po1_frontend_capability_scope.py`

---

## Sign-off Discipline

Future changes that touch ANY of the following MUST re-run the
TRUST-PO-1 regression suite **before** merge:
* `routes/po_requests.py`
* `lib/portalContext.js`
* `lib/poCapabilities.js`
* `pages/PoRequests.jsx`
* `pages/{Admin,Pm,Hr,FieldLeadership}Hub.jsx`
* Any new portal hub that should set `portal-context`

If any test in either TRUST-PO-1 test file fails, the change is
**not certifiable** until either (a) the test failure is understood
as an intentional contract change (in which case the test must be
updated in the same PR) or (b) the underlying defect is fixed.

---

## Operator-Visible Outcome

A Field Leadership operator now sees a procurement experience that
matches the platform's stated promise: they request, they upload
receipts, they respond to clarification. They do not see authority
that they do not hold. The "Authority & Visibility" banner now
operates in operational coherence with the rendered controls.

The platform feels:
* **calm** — no permission-denied toasts
* **predictable** — every control rendered is a control they can use
* **truthful** — the UI matches the actual workflow authority
* **recoverable** — switching portals re-derives the capability bundle
* **operationally trustworthy** — Field Leadership requests; PM /
  Admin / HR / Office issues, approves, and closes; Admin cancels.

Field Leadership requests. PM/Admin/Office approves/issues/closes.
The platform never implies authority where authority does not exist.

— TRUST-PO-1, certified
