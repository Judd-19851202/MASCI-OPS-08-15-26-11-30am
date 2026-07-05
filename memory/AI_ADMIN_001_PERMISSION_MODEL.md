# AI-ADMIN-001 · Permission Model

**Doctrine:** Admin AI Configuration is a super-admin surface. Only the
strict admin gate (`require_admin_strict`) may see or modify it.

---

## 1. Role matrix

| Actor                | Read config | Read tenants | Update tenant caps | Read audit | Provider probe |
| -------------------- | :---------: | :----------: | :----------------: | :--------: | :------------: |
| Super-admin          |     ✓       |      ✓       |         ✓          |     ✓      |       ✓        |
| Admin (via directory)|     ✓       |      ✓       |         ✓          |     ✓      |       ✓        |
| PM                   |     ✗       |      ✗       |         ✗          |     ✗      |       ✗        |
| HR                   |     ✗       |      ✗       |         ✗          |     ✗      |       ✗        |
| Shop / Mechanic      |     ✗       |      ✗       |         ✗          |     ✗      |       ✗        |
| Safety               |     ✗       |      ✗       |         ✗          |     ✗      |       ✗        |
| Dispatch             |     ✗       |      ✗       |         ✗          |     ✗      |       ✗        |
| Field / Field Leader |     ✗       |      ✗       |         ✗          |     ✗      |       ✗        |
| Unauthenticated      |     ✗       |      ✗       |         ✗          |     ✗      |       ✗        |

All ✗ rows return **401** at the API layer via `require_admin_strict`.

## 2. Gate implementation

- Backend: every route in `routes/ai_admin_config.py` declares
  `Depends(require_admin_strict)`. This is the same gate used for
  destructive backups, restore, and recovery.
- Frontend: the `/admin/ai-configuration` route is mounted inside
  the admin routing group (`A(<AdminAIConfiguration />)`). The
  admin auth wrapper redirects unauthenticated users to the Admin
  Sign In page and the API returns 401 on any direct call.

## 3. Cross-tenant safety

- Every read/write endpoint takes `{tenant_id}` in the path — there is
  no bulk-mutate endpoint that touches multiple tenants at once.
- Update handler snapshots `before_doc` via a `find_one({tenant_id: X})`
  and writes back with `update_one({tenant_id: X}, {...}, upsert=True)`.
- Regression lock: `test_update_is_tenant_isolated` proves modifying
  tenant "widgets" does not touch tenant "acme".

## 4. Secret exposure model

- **Never returned:** raw API key values in any endpoint response.
- **Never accepted:** raw API key values in any request body — the
  pydantic model has no key-string field; extras are dropped.
- **Boolean-only surfaces:** `providers[*].key_present`.
- Regression locks:
  - `test_status_endpoint_returns_no_raw_key_values`
  - `test_provider_test_endpoint_returns_booleans_only`
  - `test_update_writes_audit_entry_with_before_after_and_actor`
    (also asserts no `API_KEY` substring appears in the audit blob).

## 5. Denial telemetry

- 401s are handled by the standard admin gate, which routes them
  through `_record_access_denial(db, request, namespace="admin", ...)`
  — same as every other `/api/admin/*` endpoint. No new denial
  channel introduced.

## 6. Actor attribution

- The frontend can supply `X-Admin-Actor: <email>` to record the human
  identity making a change. When missing, the audit entry falls back to
  `"admin"` — never leaks internal token identifiers.

## 7. Field / PM UI leakage prevention

- No component in the field bundle (`NewDailyReport.jsx`, hub, kiosk
  entry) imports anything from `admin/AdminAIConfiguration.jsx`.
- The route is registered only inside the admin route group in
  `AppRoutes.jsx`.
- The nav entry appears only in the admin sidebar
  (`components/admin/sidebar/domainMap.js`, `components/AdminShell.jsx`)
  — not in `NavRail`, `FieldNav`, or PM/Shop/HR shells.
- Regression lock: `test_daily_report_submit_route_does_not_import_ai_admin_config`.

## 8. Future extension notes

If/when multi-tenant expands beyond MASCI, consider:

- Splitting `require_admin_strict` into `require_super_admin` +
  `require_tenant_admin` so a scoped tenant admin can flip their own
  tenant's flags without touching other tenants.
- Introducing `POST /api/admin/ai/tenants/{tenant_id}/audit`
  (currently GET-only) with an explicit "reason" field for
  compliance-grade change requests.

Both are out of scope for AI-ADMIN-001.
