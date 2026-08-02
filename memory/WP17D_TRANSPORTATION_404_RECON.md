# Transportation Academy 404 Reconciliation

- Investigated stale reconnaissance note referencing `/transportation/academy`.
- Source scan result: there is **no** frontend route mounted at `/transportation/academy`.
- Canonical Transportation Academy routes are nested under Transportation shell mounts:
  - `/admin/transportation/academy`
  - `/transportation-operations/academy`
  - `/admin/transportation/academy/:moduleKey`
  - `/transportation-operations/academy/:moduleKey`
- Supporting source: `frontend/src/pages/transportation/TransportationApp.jsx` lines 103-106 mount `academy` and `academy/:moduleKey` beneath the Transportation shell router.
- Backend curriculum endpoint remains live at `/api/admin/transportation/academy/modules`.
- Disposition: `/transportation/academy` is a **stale path assumption / documentation error**, not a live canonical route. Future ledgers and audits must reference the nested canonical academy paths above.
