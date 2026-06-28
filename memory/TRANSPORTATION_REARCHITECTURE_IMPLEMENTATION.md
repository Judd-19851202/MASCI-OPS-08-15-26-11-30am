# Transportation Rearchitecture Implementation

**Track 18.09C** · Final implementation log for the Transportation Operations Ownership amendment.

## What shipped

### Concrete code change

**File:** `frontend/src/pages/transportation/TransportationApp.jsx`

**Change:** Six compatibility redirects switched from hardcoded `/admin/transportation/...` targets to path-relative targets with `relative="path"`. This preserves both doorways (`/admin/transportation/*` for admin oversight, `/transportation-operations/*` for dispatch-authenticated operational use) while keeping operational users inside the operational shell on legacy URL navigations.

**Before (excerpt):**
```jsx
<Route
  path="fleet/trucks"
  element={<Navigate to="/admin/transportation/trucks" replace />}
/>
```

**After:**
```jsx
<Route
  path="fleet/trucks"
  element={<Navigate to="../../trucks" replace relative="path" />}
/>
```

All six redirects (`compliance/documents`, `compliance/rate-schedules`, `fleet`, `fleet/trucks`, `fleet/inspections`, `administration/audit`) were normalized this way.

### Lock test

**File:** `backend/tests/test_track_18_09c_transportation_ownership.py`

New regression lock with assertions covering:
* The seven required deliverable documents exist.
* Every Transportation feature category appears in the ownership matrix.
* Every Administration page is classified.
* The six compat redirects in `TransportationApp.jsx` are path-relative.
* The legacy hardcoded `/admin/transportation/...` redirects are gone.
* The shared single-source-of-truth contract is intact (`AdminTransportation.jsx` is the thin re-export; `TransportationApp.jsx` is the real component).
* Both doorway routes exist in `App.js` (`/admin/transportation/*` admin-gated and `/transportation-operations/*` TX-gated).
* Dispatch portal routes (`/dispatch-portal/*`) preserved.
* Driver-token routes preserved.
* RBAC contracts intact (no `A` / `TX` / dispatch helpers removed).
* Permission validation: 18.07 design-system linter still passes after rehome.
* No new collections introduced.

### Deployment gate

`scripts/deployment_gate.py` updated to include the new lock file.

## What was preserved (the explicit "do not change" surface)

| Concern | Status |
|---|:---:|
| `/admin/transportation/*` admin-strict doorway | ✅ Preserved |
| `/transportation-operations/*` TX-gated doorway | ✅ Preserved |
| `/dispatch-portal/*` dispatch token gate | ✅ Preserved |
| `/dr/*` driver token gate | ✅ Preserved |
| Backend collections | ✅ Preserved |
| Backend endpoints | ✅ Preserved |
| Auth helpers (`A`, `AP`, `TX`) | ✅ Preserved |
| Audit trail | ✅ Preserved |
| RBAC | ✅ Preserved |

## What was deferred (with reasons)

| Item | Reason for defer |
|---|---|
| Rename `pages/AdminTransportation.jsx` → `pages/transportation/TransportationOperationsEntry.jsx` | Cosmetic rename of a 9-line re-export. Zero operational benefit. Would touch `App.js` import. Defer to a later cosmetic-cleanup track. |
| Rename `pages/admin/AdminDriverIntel.jsx` → e.g. `pages/admin/DriverCommandProfileOversight.jsx` | Cosmetic. File semantically IS the oversight view. Shared component `DriverCommandProfile` is the source of truth. |
| Move `pages/admin/AdminDispatch.jsx` to Transportation Operations | The 848-line admin-shell variant of equipment availability/transfer/utilization is **not** depended on by operational dispatchers (they use `/dispatch-portal/*`). It is admin oversight today. Re-classifying as SHARED is sufficient. |
| Add a Transportation Operations-native Driver Command Profile route | A canonical operational driver workspace already exists at `/transportation-operations/drivers/:id`. The admin variant is parallel oversight. |
| Move `/admin/training`, `/admin/equipment` to per-workspace ownership | These are cross-workspace (Training touches HR + Safety + Field Leadership; Equipment touches Shop + Transportation). SHARED classification is correct; no rehome needed. |

## Final architecture

```
/transportation-operations/*  ──┐
                                 ├──► pages/transportation/TransportationApp.jsx
/admin/transportation/*       ──┘     (single source of truth)
                                          │
                                          ▼
                                  All Transportation operational routes
                                  (dispatch bridge, live-operations, trucks,
                                  drivers, carriers, compliance, orientation,
                                  intelligence, command queue, reports, audit,
                                  documents, inspections, rate-schedules)

/dispatch-portal/*           ──► Dispatch system of record (unchanged)
/dr/*                        ──► Driver self-service (unchanged)
/admin/* (governance only)   ──► Administration governance surface (unchanged)
```

**One source of truth. Two doorways for Transportation. Dispatch separate. Driver separate. Administration governance-only.**

## Final certification

🟢 **GO.** Transportation Operations is a self-contained operational workspace. Administration is a true governance workspace. The Six Pillars are upheld.

The directive's central question — *Was Transportation built under Administration and surfaced through Transportation Operations?* — is answered: the **component was named `AdminTransportation` historically and re-exposed via Track 18.00E-FIX**, but the underlying router has lived in `pages/transportation/` from the start. Track 18.09C codifies that reality, closes the one concrete redirect defect, and documents every ownership decision so future work has a contract to follow.
