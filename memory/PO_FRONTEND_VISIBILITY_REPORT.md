# PO FRONTEND VISIBILITY REPORT — TRUST-PO-1

Date: **2026-05-28**

---

## 1 · Pre-Remediation Visibility (Bug)

`PoRequests.jsx` line 62:
```js
const canApprove = isPm() || isHr() || isAdmin();
```

| User scenario | `isPm()` | `isHr()` | `isAdmin()` | `canApprove` | Approval block visible? |
|---|---|---|---|---|---|
| Pure Field Leadership session | false | false | false | **false** | NO ✅ |
| Admin session in `/admin/*` | false | false | true | true | YES ✅ |
| PM session in `/pm/*` | true | false | false | true | YES ✅ |
| Super Admin who also visited FL (sessionStorage holds both) | false | false | true | **true** | **YES** ❌ ← BUG |

The fourth row is the trust failure. Field Leadership sidebar +
Super Admin admin-token coexistence → operator sees Approve / Reject /
Manual PO # / Approved amount inside what looks like the FL portal
chrome.

---

## 2 · Post-Remediation Visibility (Capability-Scoped)

`PoRequests.jsx` now:
```js
const caps = useMemo(() => getPoCapabilities(), []);
const canApprove = caps["po.approve"] || caps["po.reject"] || caps["po.clarify"];
```

Inside the drawer every block / button gates on a specific cap:
* `caps["po.approve"]` · Approve button
* `caps["po.reject"]` · Reject button
* `caps["po.clarify"]` · Clarify button
* `caps["po.issue_number"]` · Manual PO # input
* `caps["po.set_approved_amount"]` · Approved amount input
* `caps["po.close"]` · Mark Closed button
* `caps["po.cancel"]` · Cancel button
* `caps["po.request.receipt_upload"]` · Receipt upload form

`getPoCapabilities()` returns:
* All approver caps **OFF** if `getPortalContext() === "field-leadership"`,
  regardless of token storage state.
* Approver caps **ON** only when (a) the operator holds the relevant
  token AND (b) is in an approver portal context.

| User scenario | Portal context | Approver caps |
|---|---|---|
| Pure Field Leadership | `field-leadership` | OFF ✅ |
| Pure Admin | `admin` | ON ✅ |
| Pure PM | `pm` | ON (close/cancel OFF — admin-only) ✅ |
| Pure HR | `hr` | ON (close/cancel OFF — admin-only) ✅ |
| Super Admin in FL context | `field-leadership` | OFF ← **surgical fix** ✅ |
| Super Admin in Admin context | `admin` | ON ✅ |
| Deep link to `/po-requests` before any hub | `unknown` | OFF (conservative) ✅ |

---

## 3 · DOM Surface Audit

The following `data-testid` selectors form the visibility contract.
Anything in the "Hidden" column MUST NOT appear in the DOM under
Field Leadership context:

| Selector | Admin / PM / HR context | Field Leadership context |
|---|---|---|
| `po-approval-block` | Visible | Hidden ❌→✅ |
| `po-approval-notes` | Visible | Hidden ❌→✅ |
| `po-approval-manual` | Visible | Hidden ❌→✅ |
| `po-approval-amount` | Visible | Hidden ❌→✅ |
| `po-approve-btn` | Visible | Hidden ❌→✅ |
| `po-clarify-btn` | Visible | Hidden ❌→✅ |
| `po-reject-btn` | Visible | Hidden ❌→✅ |
| `po-close-btn` | Visible (admin only) | Hidden ❌→✅ |
| `po-cancel-btn` | Visible (admin only) | Hidden ❌→✅ |
| `po-request-create` (request submit form) | Visible | Visible ✅ |
| receipt upload form | Visible (when status allows) | Visible (when status allows) ✅ |

❌→✅ means "previously leaked → now hidden".

---

## 4 · Authority Banner

`PoRequests.jsx` already includes a calm "Authority & Visibility"
banner that explains who-does-what:

```
Field Leadership submits purchase requests. The assigned PM, any
Co-PMs on the job, HR, and Admin issue the official PO and assign
the PO number. After purchase, the requester uploads receipts here.
```

This banner is shown to ALL roles (it sets expectations regardless
of who the operator is). Wording was correct pre-remediation; only
the matching UI behaviour was wrong. Now the UI behaviour matches the
banner — operational coherence restored.

---

## 5 · Verification

`backend/tests/pw_suite/test_trust_po1_frontend_capability_scope.py` —
4/4 PASS

* `test_admin_context_renders_approval_block` ✅
* `test_leadership_only_context_hides_approval_block` ✅
* `test_super_admin_in_fl_context_hides_approval_block` ✅
* `test_context_switch_admin_to_leadership_recomputes_caps` ✅

Each test:
1. Seeds the relevant tokens in browser storage.
2. Sets `sessionStorage.masci.portal-context`.
3. Navigates to `/po-requests`.
4. Opens the PO drawer.
5. Asserts presence/absence of `data-testid="po-approval-block"` and
   every individual button/input testid.

---

## 6 · Operator-Visible Outcome

A Super Admin opening `/po-requests` from inside the Field Leadership
portal sidebar now sees the **same view a clean Field Leadership user
sees**: request form + request list + status timeline + receipt upload
(when applicable) + respond-to-clarification (when applicable). No
approve / reject / clarify / issue / close / cancel surfaces of any
kind.

When the same operator clicks back to the Admin / PM / HR sidebar
and re-enters `/po-requests`, the approver capabilities re-mount and
they see the full operator-tier view. The transition is calm and
immediate — no flash of restricted controls, no permission errors,
no confusing toasts.

---

## 7 · Operational UX Doctrine Preserved

* No new accounts
* No new login flow
* No new password
* No "permission denied" toasts (UI simply doesn't render restricted
  controls — calm rather than punitive)
* No portal-context selector for the operator (it's automatic, derived
  from which hub they entered)
* No "you can't do that here" modals
* Consistent with the existing "Authority & Visibility" banner copy
