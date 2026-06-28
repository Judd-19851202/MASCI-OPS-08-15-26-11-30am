# Transportation Route Rehome Plan

**Constitutional rule (Track 18.09C):** Transportation Operations is the operational system of record.

## Scope of rehome — this track

| Route / Construct | Before | After | Reason |
|---|---|---|---|
| Compat redirects inside `TransportationApp.jsx` (6 redirects) | hardcoded `to="/admin/transportation/..."` | path-relative (`to="../documents"` etc. with `relative="path"`) | Dispatch-authenticated users on `/transportation-operations/fleet/trucks` were silently bounced into the admin shell. Operational pillar violated. **Closed.** |

That is the **complete operational rehome list** for 18.09C. No other route required a move per the audit findings.

## Routes intentionally NOT moved (with reasons)

| Route | Why preserved | Six-Pillar status |
|---|---|---|
| `/admin/transportation/*` → `AdminTransportation` | Admin-strict oversight doorway into the shared `TransportationApp` router. **Same source of truth** as `/transportation-operations/*`. | ✅ Trusted, Operational |
| `/transportation-operations/*` → `AdminTransportation` (TX gate) | Canonical operational entry point. Already in place since Track 18.00E-FIX. | ✅ |
| `/dispatch-portal/*` | Dispatch is its own operational system of record. Per `_dispatch_bridge.jsx`: *"Transportation Operations links into Dispatch — it never replaces it."* | ✅ |
| `/dr/*` | Driver-token-gated self-service surfaces. Already correctly owned. | ✅ |
| `/admin/dispatch` | Equipment availability/transfer/utilization. Operational users reach equivalent capability via `/dispatch-portal/*` and TX dispatch bridge. The `/admin/dispatch` route is the admin oversight variant. | ⚠️ SHARED |
| `/admin/people/drivers/:driverKey` → `AdminDriverIntel` | Admin oversight view of the **same** `DriverCommandProfile` component used at `/transportation-operations/drivers/:id`. | ✅ SHARED |
| `/admin/operations-events`, `/admin/operations-dashboard`, `/admin/compliance-findings`, `/admin/geofence-reconciliation` | Cross-portal governance / read-only telemetry. **Belongs in Administration.** | ✅ GOVERNANCE |

## Renames / cosmetic refactors — DEFERRED

* **`pages/AdminTransportation.jsx`** is a 9-line thin re-export of `transportation/TransportationApp`. Renaming the file would touch the import in `App.js` (one line) but provides zero operational value. **Defer cosmetic rename.**
* **`pages/admin/AdminDriverIntel.jsx`** filename retains "Admin" — semantically the file IS the admin oversight variant of the Driver Command Profile. The shared `DriverCommandProfile` component is the source of truth. **Keep filename.**
* **`pages/admin/AdminDispatch.jsx`** — historical 848-line admin-shell variant of equipment availability/transfer/utilization. Operational users do not depend on this surface (they use `/dispatch-portal/*`). Keep filename; document the SHARED classification.

## Deployment-gate wiring

* `scripts/deployment_gate.py` REGRESSION_FILES now includes:
  * `test_track_18_09c_transportation_ownership.py`

## Permission validation

* Auth helpers `A` (admin-strict) and `TX` (admin + dispatch token) unchanged.
* `/admin/transportation/*` still admin-strict.
* `/transportation-operations/*` still TX-gated.
* `/dispatch-portal/*` dispatch-token-gated unchanged.
* Driver-token unchanged.
* Audit trails unchanged.
* RBAC contracts unchanged.
* Backend collections unchanged.
* API contracts unchanged.

## Six-Pillar self-check for the redirect fix

* **Powerful** — Operational user can now navigate any legacy URL within `/transportation-operations/*` and stay in the operational shell. No new feature added.
* **Simple** — Six lines edited; one prop added (`relative="path"`).
* **Beautiful** — User never sees a flicker into the admin shell on a stale bookmark.
* **Trusted** — Auth gates unchanged. Admin bookmarks still resolve under the admin doorway.
* **Proven** — Locked by `test_track_18_09c_transportation_ownership::test_transportation_compat_redirects_are_path_relative`.
* **Operational** — Dispatch-authenticated user never bounces into Administration on a legacy redirect.
