TRANSPORTATION DRIVER + CARRIER PERMISSION MATRIX
==================================================

EFFECTIVE : Track 19.00 (2026-06-29)
DOCTRINE  : Visible = Usable. If Drivers / Carriers are visible inside
            Transportation Operations, dispatch must be able to do real
            work — no "go ask Administration" dead ends.

────────────────────────────────────────────────────────────────────────────
ROLES IN SCOPE
────────────────────────────────────────────────────────────────────────────
  · Super Admin / Administration
  · Dispatcher (any Transportation user with `X-Dispatch-Token`)
  · Human Resources
  · Safety
  · Field Leadership (read-only on driver qualification)
  · Public / carrier-driver / external users — no internal management

────────────────────────────────────────────────────────────────────────────
HR DRIVER QUALIFICATION (HR-owned)
────────────────────────────────────────────────────────────────────────────
| Action                                            | Admin | Dispatch | HR  | Safety | FL   |
|---------------------------------------------------|-------|----------|-----|--------|------|
| Read HR Driver Qualification Dashboard            | ✓     | ✓        | ✓   | ✓      | ✓    |
| Write HR CDL credential fields                    | ✓     | ✗        | ✓   | ✗      | ✗    |
| Set / clear `approved_company_driver`             | ✓     | ✗        | ✓   | ✗      | ✗    |
| Mark HR employee Active / Inactive                | ✓     | ✗        | ✓   | ✗      | ✗    |

────────────────────────────────────────────────────────────────────────────
TRANSPORTATION DRIVERS  (`transport_persons`)
────────────────────────────────────────────────────────────────────────────
| Endpoint                                                            | Admin | Dispatch | HR  | Safety | FL   |
|---------------------------------------------------------------------|-------|----------|-----|--------|------|
| GET    /api/admin/transportation/persons                            | ✓     | ✓        | ✗   | ✗      | ✗    |
| GET    /api/admin/transportation/persons/{pid}                      | ✓     | ✓        | ✗   | ✗      | ✗    |
| POST   /api/admin/transportation/persons                            | ✓     | ✓ (NEW)  | ✗   | ✗      | ✗    |
| PATCH  /api/admin/transportation/persons/{pid}                      | ✓     | ✓ (NEW)  | ✗   | ✗      | ✗    |
| POST   /api/admin/transportation/persons/link-from-hr               | ✓     | ✓ (NEW)  | ✗   | ✗      | ✗    |
| GET    /api/admin/transportation/eligible-hr-cdl-drivers            | ✓     | ✓ (NEW)  | ✗   | ✗      | ✗    |

(NEW) = permission opening introduced by Track 19.00.

HR identity fields surfaced in Transportation responses are READ-ONLY
projections. They do not round-trip writes to the HR `employees`
collection.

────────────────────────────────────────────────────────────────────────────
TRANSPORTATION CARRIERS  (`carriers`)
────────────────────────────────────────────────────────────────────────────
| Endpoint                                                | Admin | Dispatch | HR  | Safety | FL   |
|---------------------------------------------------------|-------|----------|-----|--------|------|
| GET    /api/admin/transportation/carriers               | ✓     | ✓        | ✗   | ✗      | ✗    |
| GET    /api/admin/transportation/carriers/{cid}         | ✓     | ✓        | ✗   | ✗      | ✗    |
| POST   /api/admin/transportation/carriers               | ✓     | ✓ (NEW)  | ✗   | ✗      | ✗    |
| PATCH  /api/admin/transportation/carriers/{cid}         | ✓     | ✓ (NEW)  | ✗   | ✗      | ✗    |

────────────────────────────────────────────────────────────────────────────
WHAT STAYS ADMIN-ONLY (NOT changed by Track 19.00)
────────────────────────────────────────────────────────────────────────────
  · `/api/admin/transportation/trucks` POST / PATCH — kept admin-only;
    Track 19.00 scope is drivers + carriers. Truck add/edit can be
    opened in a follow-on track if MASCI wants.
  · Transportation Intelligence admin analytics endpoints.
  · Email Pilot / Email Routing governance.
  · Automation Health admin endpoints.
  · HR sync governance.
  · Audit Timeline governance.

────────────────────────────────────────────────────────────────────────────
ANONYMOUS / UNAUTHENTICATED
────────────────────────────────────────────────────────────────────────────
All `/api/admin/transportation/*` endpoints (including the new
Track 19.00 ones) reject anonymous requests with HTTP 401 or 403.

────────────────────────────────────────────────────────────────────────────
WHY DISPATCHER CAN WRITE
────────────────────────────────────────────────────────────────────────────
Track 18.12C established the Visible = Usable doctrine. Operator
review confirmed (Track 19.00 scope approval): for the foreseeable
operating model, every Transportation Operations user IS a
transportation manager equivalent (the role is small and trusted).
Splitting "dispatcher" vs "transportation manager" right now would
slow the team down without preventing any concrete data risk.

If MASCI later needs tighter governance, a future track can introduce
a `transport_manager` portal token and re-narrow these endpoints to
`require_transport_manager_or_admin_dep` without breaking the URL
shape.
