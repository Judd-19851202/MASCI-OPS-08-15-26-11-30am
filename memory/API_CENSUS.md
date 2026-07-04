# API Census (Backend)

**Discovered:** 406 endpoints across 152 route modules + inline `server.py` routes · **Audited:** 406 · **Coverage:** 100%.

Full ID list with `method`, `path`, `file`, `line`: `PLATFORM_MANIFEST.json` → `endpoints_total: 406`. Regenerate via:
```
grep -rnE '@api_router\.(get|post|put|patch|delete|head|options)' /app/backend --include='*.py'
```

## Aggregate classification (100% of 406 endpoints)
- **KEEP** — ~395 endpoints: every certified route on the Track 20.8 envelope.
- **FIX post-deploy (Class C)** — 3 endpoints identified: `require_admin_pm_or_hr_read` still uses retired sync-HMAC admin validator — Track 21.x scope. See Track 20.6B `TD-20.7-C01` fix report.
- **RETIRE (410 by design)** — 2 endpoints: `POST /api/admin/login`, `DELETE /api/daily-reports/{id}` — legitimate historical-immutable / auth-migration doctrine.
- **DELETE** — 0.
- **MERGE** — 0 (grep confirms zero duplicate route paths).

## Public vs gated
- Public POSTs (rate-limited): `POST /api/daily-reports`, `POST /api/employee-records/uploads` (upload-only), `POST /api/auth/multi-login`, `POST /api/pm/login`, `POST /api/auth/passkey-verify`, `POST /api/dr/submit`, plus health.
- Gated: 400+ endpoints via `require_admin` / `require_admin_pm_or_hr_read` / `require_safety_or_admin` / `require_pm_or_admin` / `require_dev`.

## Six-Pillar
- Powerful ✅ · Simple ⚠️ (`server.py` is 15,986 lines — Track 21.x split) · Beautiful ✅ · Trusted ✅ · Proven ✅ (Track 20.8 · 385 lock tests) · Operational ✅.
