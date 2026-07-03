# TRACK 19.45B · Permission Certification

## Shop Intelligence
- **Registered role:** `safety_or_admin`
- **Rationale:** Safety already carries visibility into holds and
  equipment incidents. Admin retains system-wide access. Shop-scoped
  read-only tokens are not yet defined at the OI-engine level; when a
  dedicated shop portal token is added, we will migrate this role to
  `shop_safety_or_admin`. Until then, safety_or_admin is the safest
  gate that meets the "attention signal only" contract.
- **Preview:** `GET /api/operational-intelligence/shop_intelligence/preview`
  → safety or admin token required.
- **Dispatch:** `POST /api/operational-intelligence/shop_intelligence/dispatch`
  → safety or admin token required. Live send requires `dry_run=false`.

## Corporate Intelligence
- **Registered role:** `admin_only`
- **Rationale:** Corporate rollup contains cross-domain attention
  signals across every function (safety, HR, projects, PO). Only
  admin sees the full company view.
- **Preview:** `GET /api/operational-intelligence/corporate_intelligence/preview`
  → admin token required (returns JSON 403 for non-admin).
- **Dispatch:** `POST /api/operational-intelligence/corporate_intelligence/dispatch`
  → admin token required.

## Enforcement layer
Both products pass through the shared preview/dispatch route handler
in `operational_intelligence/routes.py`:
```
if p.permission_role == "admin_only" and not _is_admin_actor(actor):
    raise HTTPException(403, ...)
```
Any misconfigured token receives a JSON 401 / 403 (never HTML).

## No-Auto-Decision compliance
Both products explicitly refuse to determine fault, discipline,
compliance status, or liability. See the "No-Auto-Decision Notice"
section of each digest.
