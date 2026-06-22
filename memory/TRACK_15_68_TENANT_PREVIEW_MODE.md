# TRACK 15.68 · Tenant Preview Mode

_Status: ✅ SHIPPED_

## Backend
`GET /api/branding/current` accepts `X-Tenant-Preview` header. Preview/dev only — the endpoint reads `APP_ENV` and refuses the override when `APP_ENV=production`.

```python
if app_env != "production":
    preview_tk = (request.headers.get("X-Tenant-Preview") or "").strip().lower()
tk = preview_tk or _current_tenant_key()
```

## Frontend
`lib/BrandingProvider.jsx` reads `?tenantPreview=<key>` URL parameter (persisted in `sessionStorage`), sends it as `X-Tenant-Preview` header.

## Synthetic tenant seeded
Doc id `track_15_68_tenant_test_delete` in `db.tenant_branding`:
- company_name: "Customer #2 Construction LLC"
- platform_display_name: "Customer #2 Operations Platform"
- All contacts: `*@customer2.example`
- primary_color: `#0F766E`

## Proof
```bash
curl -H "X-Tenant-Preview: track_15_68_tenant_test_delete" \
  http://localhost:8001/api/branding/current
# → {"tenant_key":"track_15_68_tenant_test_delete",
#    "company_name":"Customer #2 Construction LLC",…}
```
**ZERO MASCI strings** in the response.

## Safety
- ✅ No writes to production tenant.
- ✅ No route mutation.
- ✅ No email send.
- ✅ Refused in `APP_ENV=production`.
- ✅ `sessionStorage`-scoped so refreshing the tab preserves preview; new tab resets to live tenant.

## Clear preview indicator (recommended next session)
Add a fixed top banner: "🟡 Previewing tenant: customer2" — not yet added.
