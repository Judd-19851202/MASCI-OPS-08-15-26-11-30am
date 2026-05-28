# PROCUREMENT TRUST REMEDIATION PLAN — TRUST-PO-1

Date: **2026-05-28**
Status: **COMPLETED (preview)** · awaiting validation sweep

---

## 1 · Remediation Scope (Surgical)

* Close the UI authority leak in `/po-requests`.
* Close the `/cancel` backend authority leak.
* Add capability-scoped rendering as a doctrinal pattern for future
  shared portal pages.
* Add regression coverage so the leak cannot silently return.

**Out of scope** (per fork directive):
* Procurement workflow redesign
* Accounting integration changes
* Schema migrations
* Phase V RFI work

---

## 2 · Step-By-Step Execution Log

### Step 1 · Diagnosis (read-only)
* Read `frontend/src/pages/PoRequests.jsx` line 62: token-presence gate.
* Read `backend/routes/po_requests.py` line 311: `_can_approve()` is
  pm/hr/admin (good).
* Walked every state-mutating PO endpoint. Found `/cancel` open.
* Walked every `_fan_out_task` call site. Notification routing was
  already correct.
**Classification: UI authority leak (primary) + `/cancel` backend
authority leak (secondary). Notification routing CLEAN.**

### Step 2 · Architecture decision
Capability-scoped rendering via two new modules:
* `frontend/src/lib/portalContext.js` — portal context tracker
* `frontend/src/lib/poCapabilities.js` — capability bundle deriver

Doctrine: **portal context is the FIRST gate, token presence the SECOND**.

### Step 3 · Implementation
1. Created `portalContext.js` with `setPortalContext` / `getPortalContext`.
2. Created `poCapabilities.js` exporting `getPoCapabilities()`.
3. Modified `PoRequests.jsx`:
   - Replaced `canApprove = isPm() || isHr() || isAdmin()` with
     `caps = getPoCapabilities()`.
   - Gated every approver button, Manual PO #, Approved amount, Close,
     and Cancel control with its specific capability flag.
4. Wired `setPortalContext()` into hub mounts:
   - `FieldLeadershipHub.jsx` → "field-leadership"
   - `AdminHub.jsx` → "admin"
   - `PmHub.jsx` → "pm"
   - `HrHub.jsx` → "hr"
5. Hardened `cancel_po()` with `_can_approve(actor)` guard.
6. Added telemetry-quiet defaults so capability gating never logs an
   error or warning.

### Step 4 · Verification
* Backend regression: `test_trust_po1_backend_enforcement.py` · 10/10 PASS
* Frontend regression: `test_trust_po1_frontend_capability_scope.py` · 4/4 PASS
* Lint: ESLint + ruff clean
* Manual smoke screenshot: admin context shows approval block, FL
  context hides it — both confirmed visually.

### Step 5 · Documentation
* PROCUREMENT_AUTHORITY_AUDIT.md
* PO_ROLE_CAPABILITY_MATRIX.md
* PO_NOTIFICATION_TARGETING_AUDIT.md
* PO_BACKEND_ENFORCEMENT_REPORT.md
* PO_FRONTEND_VISIBILITY_REPORT.md
* PROCUREMENT_TRUST_REMEDIATION_PLAN.md (this document)
* PROCUREMENT_AUTHORITY_CERTIFICATION.md

---

## 3 · Files Touched

### Frontend
* `lib/portalContext.js` (NEW)
* `lib/poCapabilities.js` (NEW)
* `pages/PoRequests.jsx` (capability-scoped rendering)
* `pages/FieldLeadershipHub.jsx` (`setPortalContext("field-leadership")`)
* `pages/AdminHub.jsx` (`setPortalContext("admin")`)
* `pages/PmHub.jsx` (`setPortalContext("pm")`)
* `pages/HrHub.jsx` (`setPortalContext("hr")`)

### Backend
* `routes/po_requests.py` — `/cancel` 403 gate

### Tests
* `tests/pw_suite/test_trust_po1_backend_enforcement.py` (NEW · 10/10 PASS)
* `tests/pw_suite/test_trust_po1_frontend_capability_scope.py` (NEW · 4/4 PASS)

### Memory
* `memory/PROCUREMENT_AUTHORITY_AUDIT.md`
* `memory/PO_ROLE_CAPABILITY_MATRIX.md`
* `memory/PO_NOTIFICATION_TARGETING_AUDIT.md`
* `memory/PO_BACKEND_ENFORCEMENT_REPORT.md`
* `memory/PO_FRONTEND_VISIBILITY_REPORT.md`
* `memory/PROCUREMENT_TRUST_REMEDIATION_PLAN.md`
* `memory/PROCUREMENT_AUTHORITY_CERTIFICATION.md`

---

## 4 · Risk Register

| # | Risk | Mitigation | Owner |
|---|---|---|---|
| R1 | Future PO state-mutating endpoint added without `_can_approve` gate | Add to backend enforcement test as a new 403 probe before merge | Main agent / reviewer |
| R2 | Deep link to /po-requests sets portal-context="unknown" | Capabilities default-conservative; approver caps OFF until explicit approver context | Already implemented |
| R3 | sessionStorage disabled (private browsing edge) | setPortalContext silently no-ops; getPortalContext returns "unknown"; conservative caps apply | Already implemented |
| R4 | Capability layer treated as security | Backend `_can_approve` remains ground truth. UI is TRUST surface, not SECURITY surface | Doctrine documented in `poCapabilities.js` |
| R5 | New portal (e.g., Safety) gains PO-approver authority without updating capability gate | `KNOWN` portal set in `portalContext.js` MUST be extended in same PR | Documented at top of `portalContext.js` |

---

## 5 · Phase Gate

* Preview deploy: GO
* Production deploy: gated on
  1. ✅ Preview validation pass (manual operator-perspective check)
  2. ⏳ Real iPad workflow exercise (FL + Admin + PM round-trip)
  3. ⏳ 72-hour observation window
  4. ⏳ Telemetry-clean (no portal-context drift in
     `/api/draft-telemetry/recent`)
* Phase V (RFI) start: cleared after production observation window

---

## 6 · Doctrine Going Forward

**Every shared portal page MUST consult portal context as the first
capability gate**, not raw token presence.

When introducing a new state-mutating endpoint, the reviewer MUST:
1. Add `_can_<action>(actor)` gate explicitly.
2. Add a backend regression test that asserts 403 for non-allowed roles.
3. Add a corresponding capability flag if the action surfaces in UI.
4. Wire portal-context awareness into the page that renders the action.
