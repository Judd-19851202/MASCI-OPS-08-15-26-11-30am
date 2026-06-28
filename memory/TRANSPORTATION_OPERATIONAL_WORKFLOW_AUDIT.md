# Transportation Operational Workflow Audit

**Constitutional rule (Track 18.09C):** Any workflow entering Administration must be justified. Otherwise it is classified as friction.

For each operational workflow we counted clicks, workspace changes, portal changes, dead ends, permission walls, context switches, and required Administration transitions.

---

## 1. Dispatcher — Start of Day → Assign First Load

* **Entry:** `/sign-in` → multi-portal sign-in (dispatcher role).
* **Route:** `/sign-in` → `/dispatch-portal/board` → assign row.
* **Clicks:** 3 (sign in · workspace tile · assign).
* **Workspace changes:** 0.
* **Portal changes:** 0 (dispatch portal is the dispatcher's home).
* **Administration transitions required:** **0** ✅
* **Friction:** None.

## 2. Dispatcher — Driver Onboarding (open existing driver record)

* **Entry:** `/transportation-operations/drivers`.
* **Route:** `/transportation-operations/drivers` → click driver row → `/transportation-operations/drivers/:id`.
* **Clicks:** 2.
* **Administration transitions:** **0** ✅
* **Friction:** None.

## 3. Transportation Manager — Carrier Onboarding Review

* **Entry:** `/transportation-operations/carriers`.
* **Route:** carriers list → row → `CarrierWorkspace` (docs, drivers, audit timeline tabs).
* **Clicks:** 2.
* **Administration transitions:** **0** ✅
* **Friction:** None.

## 4. Fleet Manager — Truck Onboarding + Documents

* **Entry:** `/transportation-operations/trucks`.
* **Route:** trucks list → row → `TruckWorkspace` (documents tab).
* **Clicks:** 2.
* **Administration transitions:** **0** ✅
* **Friction:** None.

## 5. Orientation Coordinator — Orientation Center end-to-end

* **Entry:** `/transportation-operations/orientation`.
* **Route:** orientation center → candidate row → step.
* **Clicks:** 3.
* **Administration transitions:** **0** ✅
* **Friction:** None.

## 6. Compliance Coordinator — Document Review

* **Entry:** `/transportation-operations/compliance`.
* **Route:** compliance dashboard → expiring document → drawer review.
* **Clicks:** 2.
* **Administration transitions:** **0** ✅
* **Friction:** None.

## 7. Dispatcher — Assign Loads (full)

* **Entry:** `/dispatch-portal/board`.
* **Route:** dispatch board → row → assign drawer → confirm.
* **Clicks:** 3.
* **Administration transitions:** **0** ✅
* **Friction:** None.

## 8. Compliance Coordinator — Truck Readiness Review

* **Entry:** `/transportation-operations/trucks`.
* **Route:** trucks list → readiness chip → drill.
* **Clicks:** 2.
* **Administration transitions:** **0** ✅

## 9. Driver Coordinator — Driver Readiness Review

* **Entry:** `/transportation-operations/drivers`.
* **Route:** drivers list → readiness chip → drill.
* **Clicks:** 2.
* **Administration transitions:** **0** ✅

## 10. Carrier Coordinator — Carrier Readiness Review

* **Entry:** `/transportation-operations/carriers`.
* **Route:** carriers list → readiness chip → drill.
* **Clicks:** 2.
* **Administration transitions:** **0** ✅

## 11. Incident Handling

* **Entry:** Safety portal (`/safety-portal/*`) — incident is a Safety operational concern.
* **Route:** Safety portal → incident drawer.
* **Administration transitions:** **0** ✅
* **Note:** Safety is a separate operational workspace; Transportation Operations links to Safety where relevant via the shared `_dispatch_bridge.jsx` pattern.

## 12. End-of-Day Reconciliation (Dispatcher)

* **Entry:** `/dispatch-portal/haul-ledger`.
* **Route:** haul ledger → reconcile + export.
* **Administration transitions:** **0** ✅

---

## Workflow conclusion

**Across 12 operational workflows, zero require an Administration transition.** Every operational user can run the transportation business entirely inside Transportation Operations + Dispatch portal + (when relevant) Safety portal.

## Anti-pattern test — pre-18.09C

Before 18.09C, six compat redirects inside `TransportationApp` silently sent operational users to `/admin/transportation/...` URLs. **A dispatch-authenticated user hitting `/transportation-operations/fleet/trucks` was redirected to `/admin/transportation/trucks`, which they couldn't access.** That was a real Administration-transition forced on operational users via legacy URLs. **Closed this track.**

## Verdict

🟢 **Transportation Operations is a self-contained operational workspace.** Administration is required for **zero** operational workflows.
